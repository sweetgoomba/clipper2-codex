# Mac 하이라이트 가속 사용과 검증 절차

2026년 11월 4일 Python 17259bc·Electron 849a51b의 Apple Silicon Mac 구현을 설명한다. [모델별 상태](../README.md)와 [실측 결과](../records/2026/11/04-mac-remaining-models-speed-results.md)를 함께 읽는다. 이 문서화 과정에서 새 모델 실행·빌드·성능 시험은 하지 않았다.

## 앱에서 사용하는 방법

설정 → 분석 가속은 기존 설정 페이지에 추가된 기능이다. 안무·인물·대사 각각의 이 기기 실행 방식을 정하며 서버 설정과는 별개다.

| 조작 | 실제 의미 | 적용 |
|---|---|---|
| 자동 | 환경·준비 상태·품질·속도·메모리에 맞는 경로 선택 | 다음 분석. 모든 모델 GPU 강제 아님 |
| CPU | 해당 플러그인 CPU 실행, 유휴 가속 비교 보류 | 다음 분석 |
| 추가 실행기 준비 | 호환 별도 실행기 패키지 다운로드·설치 | 준비 후 시험/선택 |
| 이 기기 시험 | 다음 분석에서 CPU와 후보 비교, 성공한 자료를 로컬 유휴 비교에 사용 | 다음 분석. CPU 비교 때문에 더 오래 걸릴 수 있음 |
| 유휴 검사 다시 예약 | 유효한 저장 자료로 남은 후보 순환 검사 예약 | 사용자 작업이 없을 때 |
| 실행 기록 | 실제 선택·거절·보류·품질·속도·복구 확인 | 실행 후 |

평소 속도를 볼 때는 자동으로 분석한다. CPU 기준을 함께 실행한 이 기기 시험과 일반 자동 분석 시간을 같은 조건으로 비교하지 않는다. 설정은 플러그인별이며 실행 중 모델을 중간 교체하지 않는다. 이 문서화에서는 사용자의 설정을 바꾸지 않았다.

추가 팩 준비와 기본 Mac 얼굴 후보는 별도 경로다. 기본 후보는 플러그인에 설치된 고정 ONNX/ORT와 호스트 조건을 쓴다. 추가 실행기 준비를 모든 기본 얼굴 가속의 필수 활성화 버튼으로 설명하지 않는다.

문구 정본은 [설정 카드 HTML](/Users/jina/project/adlight/desktop/clipper_angular/src/shell/settings/acceleration-settings-card/acceleration-settings-card.component.html), 저장 정본은 [Electron settings.ts](/Users/jina/project/adlight/desktop/clipper_electron/src/main/accelerators/settings.ts)다. 새 기본 얼굴 사유 코드 일부는 한국어로 번역되지 않아 원문으로 보일 수 있다.

## 기본 Mac 얼굴 후보의 선택

소유된 분석·자동 모드·Darwin arm64·CoreML 제공·검증한 원본·변환기·충분한 작업량·메모리 승인이 전제다. ORT 1.31.0/ONNX 1.20.1을 확인하며 미확인 모델·버전을 임의로 변환하지 않는다. 이 기본 경로는 범용 팩의 승인 조건을 해제하지 않는다.

| 모델 | 입력과 수치 검사 | 선택 기준 |
|---|---|---|
| AuraFace | 최초 실제 얼굴+가로/세로 반전 3입력, 512차원·유한·유효 norm, cosine≥0.9995, norm 비율 차이≤2% | 실제 CoreML 노드, 후보 median<CPU median×0.8 |
| SFace | 기존 alignCrop·112×112 uint8·RGB blob·128차원, cosine≥0.99999, norm 비율 차이≤0.1% | 원본 FP32, 같은 속도/노드 기준 |
| YuNet | 명시 source 크기+가로/세로 반전, 기존 pad32/decode/NMS, 같은 배열 모양, allclose rtol=1e-5·atol=0.001 | 원본 FP32, 같은 속도/노드 기준 |

AuraFace/SFace는 계획량이 없거나 128 미만이면 변환·시험을 생략한다. YuNet도 source 크기와 pose 계획 128 이상이 필요하다. 다른 크기 ROI는 기존 CPU다. CoreML 노드 할당은 물리 GPU 단독 실행과 동의어가 아니다.

원본 파일을 덮어쓰지 않고 accelerator cache의 native-coreml 아래에 hash별 파생물을 저장한다. 기본 home은 ~/.cache/clipper/accelerators이며 환경에 따라 달라질 수 있다.

| 모델 | 고정 원본 SHA256 | 파생 |
|---|---|---|
| AuraFace | a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60 | batch 1·내부 FP16/입출력 FP32, a97695fbb8785013af24264fe235cb8bcffca8de77d56a47b3cc0e787608757c |
| SFace | 0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79 | FP32, ae6a6ac44d2bdc87924e75fb23d8212430dd24f037f5e035c21deff99afc8b61 |
| YuNet | 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4 | 크기에 따라 다름. 측정한 1920×1080 pad32는 617ecfe0499f6294124a92707c1deae7d0e975ce31691e680a82f0c0a88994b7 |

## 단계별 메모리 수명

1. 원래 YOLO MPS로 초기 자세 분석.
2. 동기화·모델 파괴·weakref 소멸·프로세스 MPS 할당 0 확인 후 해당 모델 예약만 반환.
3. AuraFace CPU 비교 후 소유 CPU 세션 해제, 승인 후 CoreML 선택. YuNet은 원본 크기만 선택.
4. 메인 선택 종료 시 YuNet CoreML 세션·해당 예약 해제.
5. 원경 자세 확인 시 동일 YOLO 재생성, 완료 뒤 다시 해제.
6. 기존 얼굴·구간 조립을 같은 판정·샘플링·가중치로 계속.

새 호스트의 CLIPPER_ACCELERATOR_NATIVE_RELEASE=1 지원이 없으면 기존 수명을 유지한다. CPU/Windows/routed YOLO worker는 이 MPS 해제 대상이 아니다. /unreserve-native는 인증된 native 소유자·활성 worker 없음·유효 반환량을 검사한다. ACK 전 예약 유지, lease 독점·향후 메모리 admission 한도 유지다.

Made My Night에서 MPS 할당 34,124,800·34,384,896바이트가 각각 0이 됐고 반환 HTTP 200을 확인했다. SFace는 당시 총 요청 1,079,002,652바이트가 허용 897,232,896바이트보다 커서 CPU를 유지했다. 장치가 지원하더라도 동시 모델 메모리가 선택을 제한한다.

## CPU 복구와 결과 공개

| 상황 | 처리 |
|---|---|
| 첫 후보 품질·속도·메모리 거절 | GPU 결과 공개 전 원본 CPU로 계속 |
| 선택한 GPU의 늦은 오류·비정상 출력 | BackendFailure gpu=true, 분석 단위를 새 CPU 실행으로 한 번 재분석 |
| CPU 재분석도 실패 | 오류 반환, 이전 성공 결과 유지 |
| 취소·입력 오류·원본 CPU 오류 | GPU 성공/복구로 오인하지 않음 |
| 자식 종료 미확인 | cleanup_pending/busy 유지, 새 작업·유휴 검사 성공 처리 안 함 |

안무는 해당 영상 분석 전체를 다시 계산한다. 인물·대사는 시각/음성/stage 경계를 따르며 다른 성공 stage·서버 LLM·과금을 무조건 반복하는 기능은 아니다. 임시 결과는 성공 후 artifact revision으로 원자 공개한다. GPU 중간 특징과 새 CPU gallery를 섞지 않는다.

원본·참조·프로젝트를 지우거나 사용자 삭제를 취소하는 기능이 아니다. [visual_unit.py](/Users/jina/project/adlight/desktop/clipper_python/clipper_accelerators/clipper_accelerators/visual_unit.py)와 [대사 transactional_stages.py](/Users/jina/project/adlight/desktop/clipper_python/plugins/dialog_highlight/dialog_highlight/services/transactional_stages.py)가 복구 단위의 코드 정본이다.

## 진단에서 확인하는 항목

| 항목 | 해석 |
|---|---|
| acceleration.cpu_reanalysis/attempt/fallback_reason/fallback_error | 전체 CPU 재시도 여부·원인 |
| acceleration_models.models | model_id/selected_backend/reason/calls. 실행기 설치만으로 실제 GPU 실행 단정 안 함 |
| profile_verified/provider_node_counts/graph_execution | 실제 CoreML 로컬 실행 증거 |
| YuNet execution_counts/execution_seconds | CPU ROI/CoreML 원본프레임 실행량 분리 |
| cpu_reference_released/accelerator_released/reservation_released | 후보 비교와 단계 종료의 수명 |
| trial_failure.details.admission | pressure/budget/requested/source 등 실제 거절 |
| meta.diagnostics.performance.stage_seconds | 상위/하위 중첩을 고려한 단계 비용 |

결과 revision에 연결된 acceleration JSON을 우선한다. 인물의 기존 성능 요약 face_provider=CPUExecutionProvider는 고정 문자열이라 실제 AuraFace CPU/GPU 판정 근거로 삼지 않는다. 인물 YuNet은 source 크기 준비 미연결이라는 제한도 함께 읽는다.

## 남은 CPU 병목과 채택하지 않은 후보

YuNet CPU ROI는 실제 입력에서 동적 CoreML이 더 느려 유지했다. SFace CoreML은 단독에서 빨랐으나 전체 메모리 한도를 넘었다. Whisper는 현재 구현이 MPS 요청을 CPU int8로 바꾼다. CLIP은 기존 MPS가 있지만 이번 안무에는 호출되지 않았다.

남은 상위 비용은 YOLO 62.945초·메인 선택 73.555초·구간 27.514초·얼굴 추출 33.258초·인물 묶기 42.379초다. secondary_faces 24.658초는 인물 묶기 안의 하위 시간이라 중복 합산하지 않는다.

CPU 스레드 제한·dynamic YuNet CoreML·FP16 YuNet/SFace·확인되지 않은 하드웨어 디코드는 속도나 품질 때문에 채택하지 않았다. 후속은 준비·전송·postprocess와 동시 peak를 먼저 측정하며, 프레임·참조·threshold·품질 규칙을 줄여 속도를 맞추지 않는다.

## 저장된 결과를 모델 실행 없이 비교

[문서화 보충 증거](../records/2026/11/04-mac-acceleration-documentation-evidence/)에 baseline/final의 lists/config/stats/acceleration view와 원본 파일 SHA가 있다. 새 ML 실행이 아니다. 다음 명령은 저장된 63행 전체를 대조한다.

    python3 - <<'PY'
    from pathlib import Path
    import json
    root = Path('/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/04-mac-acceleration-documentation-evidence')
    before = json.loads((root / 'baseline-result-view.json').read_text())
    after = json.loads((root / 'final-result-view.json').read_text())
    for key in ('lists', 'config', 'stats'):
        assert before['meta'][key] == after['meta'][key], key
    assert after['acceleration']['cpu_reanalysis'] is False
    assert {key: len(value) for key, value in after['meta']['lists'].items()} == {'main': 49, 'group': 14}
    print('PASS: lists/config/stats identical, CPU reanalysis false')
    PY

기존 57개 증거와 manifest는 바꾸지 않았다. [실측 로그](../records/2026/11/04-mac-remaining-models-speed-results-evidence/single-phased-final.log)와 [모델·단계 비교](../records/2026/11/04-mac-remaining-models-speed-results-evidence/single-phased-comparison.json)를 함께 읽는다.

## 테스트 재현

개발 의존성이 설치된 기존 venv·Node 24.19를 쓴다. 다음은 기록한 검증 범위다.

    cd /Users/jina/project/adlight/desktop/clipper_python
    CLIPPER_MPS_TEST_ROOT=/Users/jina/project/adlight/desktop/clipper_python \
      .venv/bin/python /Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/04-mac-acceleration-documentation-evidence/pytest-run.py \
      -q clipper_accelerators/tests clipper_face_core/tests tests/test_dance*.py plugins/person_highlight/tests

기록 결과는 2,073개 통과/54.80초다. runner 환경변수는 검사할 소스 경로 지정이며 제품 인증·메모리·소유권 우회가 아니다.

    cd /Users/jina/project/adlight/desktop/clipper_electron
    npm run build
    node --test --test-concurrency=4 'test/*.js' 'test/*.mjs'

기록 결과는 1,977개 통과/34.812초다. 첫 기본 동시 실행의 EPERM/Node IPC 실패와 단독 20개 통과도 보존했다. 소스 SHA가 달라졌으면 테스트 수를 과거 값에 맞추지 말고 현재 커밋·결과를 별도로 남긴다.

핵심 회귀는 Python test_native_face_coreml.py/test_native_yunet.py/test_native_sface.py/test_phase_model_release.py와 Electron accelerator-admission-memory.test.js다. test_late_face_failure_reaches_visual_unit_cpu_reanalysis_and_revision은 실제 바깥 복구 경계·CPU 재분석·revision까지 확인한다.

## 전체 영상 속도 재측정

영상은 Made My Night 하나다. SHA는 3400a0f3d21399609c54b38884d0208bf28e2541e10d450c5135306deba2e363,155.038초/1920×1080/59.94fps다. [입력 manifest](../records/2026/11/04-mac-remaining-models-speed-results-evidence/mmn-inputs.json)에 참조 31장의 SHA와 순서가 있다.

1. baseline Python a73593a, final 17259bc/Electron 849a51b를 별도 소스로 고정한다. final worktree에서 baseline harness만 실행하면 과거 소스가 복원되지 않는다.
2. 현재 사용자 분석·다른 측정·빌드를 확인한다. 앱 종료가 필요하면 현재 사용자 작업과 허락 범위를 확인한다. 문서화 요청으로 앱을 종료하지 않았다.
3. [run_final.py](../records/2026/11/04-mac-remaining-models-speed-results-evidence/run_final.py)·[CJS](../records/2026/11/04-mac-remaining-models-speed-results-evidence/run_final.cjs)는 당시 절대경로가 고정된 재현 원본이다. 별도 scratch 사본에서 source root·venv·compiled Electron host를 맞춘다.
4. scratch/output_root/job_id/log/result/selection hook 경로를 전부 새 실행 전용으로 바꾼다. frozen-params의 입력경로·hash를 검증한다. 사용자 프로젝트·이전 성공 경로를 쓰지 않는다.
5. CJS가 실제 호스트·새 token을 만든 뒤 Python을 실행한다. 기존 실행이 끝나기 전에 다시 시작하지 않는다. hook은 진단용이며 판정 출력을 바꾸지 않는다.
6. wall time과 내부 elapsed를 구분하고 stage/model 시간·전체 목록·config·stats·CPU 재분석을 함께 비교한다. 다른 모델 조합·메모리 압력·중복 실행·cold compile은 별도로 기록한다.

이것은 실제 owned 실행/메모리 코드를 사용한 오프라인 검증이다. UI 새 분석 제출과 같은 작업 ID·과금 흐름을 측정한 것은 아니다. 취소는 소유 부모의 정상 취소 경로로 수행하고 다른 Python/Node를 임의 종료하지 않는다.

## 원본 dev Mac 빌드와 적용

Node 24.19와 형제 저장소 구조에서 사용자가 요청한 명령이다.

    cd /Users/jina/project/adlight/desktop/clipper_electron
    npm run build:app:mac:arm64:local-api

먼저 원본의 미커밋 변경·HEAD·실제 서버 dev를 읽고 다른 작업을 보존한다. 캐시나 비교 앱이 보인다고 reset/clean하지 않는다. API health는 연결 검사이며 최신 DB 스키마·모든 기능 검증을 대신하지 않는다.

앱은 dist-app/mac-arm64/Clipper Studio (dev).app, local-api 패키지 주소는 http://127.0.0.1:3000, 업데이트는 OFF다. local-api 플래그 없는 dev/Windows 빌드가 같은 주소라고 가정하지 않는다. 개발 서버 배포는 하지 않았다.

검증 순서: runtime config → Python 파일 SHA → app.asar lease SHA → 실제 plugin fingerprint·설치 모듈 SHA → 앱 시작·안무 화면 → dynamic Nest/API health. Nest 52454는 당시 할당값이며 다음 실행의 고정 포트가 아니다.

ensurePluginVenv가 source fingerprint를 비교해 네 로컬 패키지를 갱신한다. 빌드 성공만으로 기존 venv 최신성을 보장하지 않아 설치 모듈도 대조했다. marker만 편집해 업데이트를 건너뛰지 않는다.

## 보존과 복귀

직전 기본 앱은 Electron .tmp/mac-before-remaining-face-20261104에 보존됐다. 더 이전 dist-app-dance-dev-baseline-20261103과 dist-app-dance-quality-integrated-20261103에는 파일/링크 858·870개, Python coreml-cache에는 38개가 존재했다. .git/info/exclude로 안 보여도 삭제된 것이 아니다.

문제가 발생하면 해당 플러그인의 CPU 설정으로 다음 새 분석을 비교하고 오류와 revision을 남긴다. 다른 앱 사본과 결과를 교차 사용하지 않는다. 원본 모델·참조·프로젝트·개인 교정 자료 삭제를 해결 절차로 삼지 않는다. 원격 dev 되돌리기·서버 배포·사용자 데이터 삭제는 이 문서의 자동 단계가 아니다.
