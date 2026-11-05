#!/usr/bin/env python3
"""Clipper GPU 시험 키트 — 모델 4개를 CPU와 이 PC에서 쓸 수 있는 GPU 실행기로 각각 돌려
속도와 결과 일치도(CPU 대비)를 results/ 에 남긴다. numpy·onnxruntime만 있으면 돈다.

  python run_kit.py --label directml     (run.bat이 대신 부른다)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import onnxruntime as ort

KIT = Path(__file__).resolve().parent
SKIP_PROVIDERS = {"CPUExecutionProvider", "AzureExecutionProvider"}
WARMUP = 3
MAX_DML_ADAPTERS = 4


def system_info() -> dict:
    info = {"platform": platform.platform(), "python": sys.version.split()[0], "onnxruntime": ort.__version__,
            "available_providers": ort.get_available_providers()}
    if sys.platform == "win32":
        query = ("Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,AdapterRAM | ConvertTo-Json; "
                 "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json")
        info["windows_hw"] = _run(["powershell", "-NoProfile", "-Command", query])
    elif sys.platform == "darwin":
        info["mac_hw"] = _run(["sysctl", "-n", "machdep.cpu.brand_string", "hw.physicalcpu", "hw.memsize"])
    if hasattr(ort, "get_ep_devices"):
        try:  # 장치 metadata(Windows: 어댑터 번호·설명 등)로 DirectML 장치 번호가 어느 그래픽인지 맞춰 본다
            info["ep_devices"] = [{"ep": d.ep_name, "ep_vendor": d.ep_vendor, "type": str(d.device.type),
                                   "vendor": d.device.vendor, "vendor_id": hex(d.device.vendor_id),
                                   "device_id": hex(d.device.device_id), "metadata": dict(d.device.metadata)}
                                  for d in ort.get_ep_devices()]
        except Exception as error:  # Windows ML 설치 상태에 따라 실패할 수 있다 — 그 자체가 기록할 정보
            info["ep_devices_error"] = repr(error)
    return info


def dml_adapters(probe_model: Path) -> list[str]:
    """DirectML은 기본으로 0번 그래픽 장치(주 모니터가 붙은 쪽 — 노트북이면 보통 내장 그래픽)를 쓴다.
    내장+외장이 함께 있는 PC에서 어느 쪽을 쟀는지 헷갈리지 않게 장치 번호마다 따로 잰다.
    없는 번호와 소프트웨어 장치(Microsoft Basic Render Driver)는 세션 생성이 실패하면서 끝난다."""
    found = []
    for device_id in range(MAX_DML_ADAPTERS):
        try:
            session = ort.InferenceSession(str(probe_model), providers=[("DmlExecutionProvider", {"device_id": str(device_id)})],
                                           enable_fallback=0)
        except Exception:
            break
        if session.get_providers()[0] != "DmlExecutionProvider":
            break
        found.append(f"DmlExecutionProvider:{device_id}")
    return found


def _run(command: list[str]) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as error:
        return f"실패: {error!r}"


def register_winml_providers(info: dict) -> list[str]:
    """Windows ML 실행기 목록(제조사별 GPU 실행기)을 받아 ONNX Runtime에 등록한다 — 시험용.

    Microsoft 문서(new-windows-ml/register-execution-providers)의 Python 절차를 따른다. 문서에 빠진
    부트스트랩 호출은 추정이라, 단계마다 실패를 그대로 기록하고 계속한다(키트 본 시험에는 영향 없음).
    """
    log = info.setdefault("winml_catalog", {})
    try:
        from winui3.microsoft.windows.applicationmodel.dynamicdependency import bootstrap
        bootstrap.initialize(options=bootstrap.InitializeOptions.ON_NO_MATCH_SHOW_UI).__enter__()
        log["bootstrap"] = "ok"
    except Exception as error:
        log["bootstrap"] = repr(error)
    registered = []
    try:
        import winui3.microsoft.windows.ai.machinelearning as winml
        catalog = winml.ExecutionProviderCatalog.get_default()
        log["providers"] = []
        for provider in catalog.find_all_providers():
            row = {"name": provider.name, "ready_state": str(provider.ready_state)}
            try:
                result = provider.ensure_ready_async().get()
                row["ensure_ready"] = str(result.status)
                if result.status == winml.ExecutionProviderReadyResultState.SUCCESS:
                    ort.register_execution_provider_library(provider.name, provider.library_path)
                    registered.append(provider.name)
                    row["registered"] = True
            except Exception as error:
                row["error"] = repr(error)
            log["providers"].append(row)
    except Exception as error:
        log["catalog_error"] = repr(error)
    return registered


def make_session(path: Path, provider: str) -> tuple[ort.InferenceSession, float]:
    options = ort.SessionOptions()
    if provider.startswith("DmlExecutionProvider"):  # DirectML 문서 요구사항
        options.enable_mem_pattern = False
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    # GPU 쪽은 실패하면 CPU로 몰래 넘어가지 않게 한다 — 넘어가면 CPU 시간을 GPU 시간으로 잘못 적는다
    fallback = int(provider == "CPUExecutionProvider")
    started = time.perf_counter()
    if provider.startswith("winml:"):  # Windows ML로 등록한 실행기는 장치 목록으로 붙인다
        devices = [d for d in ort.get_ep_devices() if d.ep_name == provider[len("winml:"):]]
        options.add_provider_for_devices(devices, {})
        session = ort.InferenceSession(str(path), sess_options=options, enable_fallback=fallback)
    elif provider == "auto:PREFER_GPU":
        options.set_provider_selection_policy(ort.OrtExecutionProviderDevicePolicy.PREFER_GPU)
        session = ort.InferenceSession(str(path), sess_options=options, enable_fallback=fallback)
    elif provider.startswith("DmlExecutionProvider:"):
        dml = ("DmlExecutionProvider", {"device_id": provider.split(":")[1]})
        session = ort.InferenceSession(str(path), sess_options=options, providers=[dml, "CPUExecutionProvider"],
                                       enable_fallback=fallback)
    else:
        providers = [provider] if provider == "CPUExecutionProvider" else [provider, "CPUExecutionProvider"]
        session = ort.InferenceSession(str(path), sess_options=options, providers=providers, enable_fallback=fallback)
    return session, time.perf_counter() - started


def run_all(session: ort.InferenceSession, inputs: np.ndarray, runs: int, batch: int = 1) -> tuple[list, dict]:
    name = session.get_inputs()[0].name
    batches = [inputs[i:i + batch] for i in range(0, len(inputs) - batch + 1, batch)]
    started = time.perf_counter()
    first = session.run(None, {name: batches[0]})
    first_ms = (time.perf_counter() - started) * 1000
    for i in range(WARMUP):
        session.run(None, {name: batches[i % len(batches)]})
    times = []
    for i in range(runs):
        started = time.perf_counter()
        session.run(None, {name: batches[i % len(batches)]})
        times.append((time.perf_counter() - started) * 1000)
    outputs = [session.run(None, {name: b}) for b in batches] if batch == 1 else []
    per_item = np.array(times) / batch
    return outputs, {"first_run_ms": round(first_ms, 1), "median_ms_per_item": round(float(np.median(per_item)), 2),
                     "p90_ms_per_item": round(float(np.percentile(per_item, 90)), 2), "batch": batch}


def compare(kind: str, cpu: list, other: list) -> dict:
    if kind == "embedding":
        a = np.concatenate([o[0] for o in cpu]); b = np.concatenate([o[0] for o in other])
        cos = np.sum(a * b, 1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
        return {"cosine_min": round(float(cos.min()), 5), "cosine_median": round(float(np.median(cos)), 5)}
    if kind == "yolo":  # 플러그인과 같은 기준(NMS 뒤 사람 수)으로 본다 — 안무 conf .25, 인물 conf .1, 둘 다 iou .7
        row, ious = {}, []
        for label, conf in (("dance", 0.25), ("person", 0.1)):
            same = 0
            for (a,), (b,) in zip(cpu, other):
                pa, pb = _people(a[0], conf), _people(b[0], conf)
                same += int(len(pa) == len(pb))
                ious += [max((_iou(x, y) for y in pb), default=0.0) for x in pa]
            row[f"same_people_{label}"] = f"{same}/{len(cpu)}"
        row["matched_box_iou_min"] = round(float(min(ious)), 4) if ious else None
        return row
    if kind == "yunet":  # 원시 출력 상대오차는 0에 가까운 obj 값 때문에 부풀려진다 → 실제 판정(얼굴 점수)으로 본다
        same_count, diffs = 0, []
        for a, b in zip(cpu, other):
            sa, sb = _yunet_scores(a), _yunet_scores(b)
            same_count += int((sa > 0.6).sum() == (sb > 0.6).sum())
            diffs.append(float(np.abs(sa - sb).max()))
        return {"same_face_count": f"{same_count}/{len(cpu)}", "face_score_max_diff": round(max(diffs), 4)}
    errors = [float(np.abs(x - y).max() / (np.abs(x).max() + 1e-9)) for a, b in zip(cpu, other) for x, y in zip(a, b)]
    return {"max_relative_error": round(max(errors), 5)}


def _yunet_scores(outputs: list) -> np.ndarray:  # 출력 순서: cls_8·16·32, obj_8·16·32, bbox…, kps…
    cls, obj = outputs[0:3], outputs[3:6]
    return np.concatenate([np.sqrt(np.clip(c * o, 0, 1)).ravel() for c, o in zip(cls, obj)])


def _people(pred: np.ndarray, conf: float, iou: float = 0.7) -> list[np.ndarray]:
    """YOLO 원시 출력(56×8400) → 점수 순 NMS 뒤 사람 상자(cx, cy, w, h). ultralytics NMS와 같은 규칙."""
    keep = pred[4] > conf
    boxes, scores = pred[:4, keep].T, pred[4, keep]
    picked: list[np.ndarray] = []
    for i in scores.argsort()[::-1]:
        if all(_iou(boxes[i], other) <= iou for other in picked):
            picked.append(boxes[i])
    return picked


def _iou(a: np.ndarray, b: np.ndarray) -> float:  # cx, cy, w, h
    ax1, ay1, ax2, ay2 = a[0] - a[2] / 2, a[1] - a[3] / 2, a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1, bx2, by2 = b[0] - b[2] / 2, b[1] - b[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2
    inter = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    return inter / ((ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter + 1e-9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--winml-catalog", action="store_true", help="Windows ML 제조사 실행기를 받아 등록해 함께 시험")
    args = parser.parse_args()

    manifest = json.loads((KIT / "models" / "manifest.json").read_text(encoding="utf-8"))
    samples = np.load(KIT / "samples.npz")
    info = {}
    registered = register_winml_providers(info) if args.winml_catalog else []
    info.update(system_info())
    gpu_providers = [p for p in ort.get_available_providers() if p not in SKIP_PROVIDERS]
    if "DmlExecutionProvider" in gpu_providers:  # 그래픽 장치마다 따로 — 못 찾으면 원래 이름으로 남겨 실패를 기록한다
        probe = min((KIT / "models" / e["file"] for e in manifest.values()), key=lambda p: p.stat().st_size)
        at = gpu_providers.index("DmlExecutionProvider")
        gpu_providers[at:at + 1] = dml_adapters(probe) or ["DmlExecutionProvider"]
    gpu_providers += [f"winml:{name}" for name in registered]
    if hasattr(ort, "OrtExecutionProviderDevicePolicy"):
        gpu_providers.append("auto:PREFER_GPU")
    print(f"[{args.label}] onnxruntime {ort.__version__} · 시험할 GPU 실행기: {gpu_providers or '없음'}", flush=True)

    results = {"label": args.label, "system": info, "models": {}}
    for name, entry in manifest.items():
        path, inputs, kind = KIT / "models" / entry["file"], samples[entry["samples"]], entry["kind"]
        rows = {}
        print(f"  {name} ({'·'.join(entry['used_by'])}) CPU ...", flush=True)
        cpu_session, load_s = make_session(path, "CPUExecutionProvider")
        cpu_outputs, timing = run_all(cpu_session, inputs, args.runs)
        rows["CPU"] = {"load_s": round(load_s, 2), **timing}
        for provider in gpu_providers:
            print(f"  {name} {provider} ...", flush=True)
            try:
                session, load_s = make_session(path, provider)
                outputs, timing = run_all(session, inputs, args.runs)
                rows[provider] = {"load_s": round(load_s, 2), "providers_used": session.get_providers(), **timing,
                                  "speedup_vs_cpu": round(rows["CPU"]["median_ms_per_item"] / timing["median_ms_per_item"], 2),
                                  **compare(kind, cpu_outputs, outputs)}
                if kind == "embedding" and len(inputs) >= 8:
                    rows[provider]["batch8"] = run_all(session, inputs, max(4, args.runs // 4), batch=8)[1]
            except Exception as error:
                rows[provider] = {"error": repr(error), "trace": traceback.format_exc(limit=3)}
        if kind == "embedding" and len(inputs) >= 8:
            rows["CPU"]["batch8"] = run_all(cpu_session, inputs, max(4, args.runs // 4), batch=8)[1]
        results["models"][name] = {"used_by": entry["used_by"], "rows": rows}

    out_dir = KIT / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    (out_dir / f"{args.label}-{stamp}.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"Clipper GPU 시험 결과 — {args.label} — {stamp}", f"onnxruntime {ort.__version__}", ""]
    for name, model in results["models"].items():
        lines.append(f"[{name}] ({'·'.join(model['used_by'])})")
        for provider, row in model["rows"].items():
            if "error" in row:
                lines.append(f"  {provider:28s} 실패: {row['error'][:150]}")
                continue
            extra = {k: v for k, v in row.items() if k in ("speedup_vs_cpu", "cosine_min", "same_people_dance",
                                                            "same_people_person", "matched_box_iou_min", "same_face_count",
                                                            "face_score_max_diff", "max_relative_error")}
            lines.append(f"  {provider:28s} {row['median_ms_per_item']:8.1f}ms/장  첫 실행 {row['first_run_ms']:.0f}ms  {extra}")
        lines.append("")
    (out_dir / f"{args.label}-{stamp}.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"결과 저장: {out_dir}")


if __name__ == "__main__":
    main()
