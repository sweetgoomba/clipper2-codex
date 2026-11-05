# 하이라이트 자동 가속 구현 기록 — 2026-11-03

**공통 기반과 CPU 복구 엔진을 1차 구현했다. 전체 자동 가속 기능은 아직 미완료이며, 새 GPU 기본값은 활성화하지 않았다.**

지원 범위는 Apple Silicon native macOS와 Windows x64다. Intel Mac과 Windows ARM은 제외한다. 기존 모델, 전후처리, 임계값과 하이라이트 품질 기준은 그대로 유지했다.

## 작업 위치와 원본 보존

| 저장소 | 작업트리 | 브랜치 |
|---|---|---|
| Python | `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103` | `codex/highlight-acceleration-20261103` |
| Nest | `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103` | `codex/highlight-artifact-recovery-20261103` |

Python base는 `4b54bced17e13aadbeb97be75259b7f7213a9b24`, Nest base는 `e4e1fcf5d37bdbbd2c0c00a9f558b052c2d55f7f`다.

원래 Python checkout의 dirty patch와 untracked 소스를 먼저 보존하고 작업트리에 재현했다. 대형 모델은 해시로 기록했다. 원본의 변경 파일·모델 120개를 다시 검사했으며 시작 시점과 해시가 모두 같다. 원래 Nest checkout에도 코드 변경을 하지 않았다.

commit, push, 앱 재시작, 원래 가상환경의 설치·동기화는 하지 않았다. 기존 Python interpreter를 사용하되 import 경로를 작업트리로 지정했다.

## 구현한 동작

### 모델 계약과 자동 선택 기반

`clipper_accelerators` 경량 workspace package를 만들고 세 하이라이트 플러그인의 의존에 추가했다. package 자체 import는 torch·ORT·OpenCV·Whisper를 로드하지 않는다.

- 활성 모델 6개(YOLO pose, YuNet, AuraFace, SFace, CLIP, Whisper small)와 비활성 SAM2·OCR를 구분한다.
- 모델·pack·정밀도·shape·batch·전처리·인증·OS·아키텍처·장치·드라이버·정책 버전을 식별한다.
- 알 수 없는 장치나 드라이버, 미설치 pack, 인증 범위 밖 입력은 자동 선택 후보에서 제외한다. 새 경로의 CPU 기준도 인증이 필요하다.
- 검증 순서는 fixture 해시 확인 → 현재 CPU와 승인 출력 비교 → GPU 후보와 승인 출력 및 현재 CPU 비교다.
- 유휴 측정 예산은 총 120초, 영상 후보당 30초, 음성 후보당 60초다. 한 profile에서 CPU와 최대 2개 GPU를 평가하고 다음 회차에 나머지 후보를 순환한다.
- 영상은 품질 입력 24개·warmup 3회·성능 측정 30회, 음성은 입력 3개·3회 반복을 사용한다. 취소되거나 끝나지 않은 측정은 선택 자료로 사용하지 않는다.
- 로드·컴파일 시간을 포함한 예상 작업시간이 10% 이상 줄고 p90이 기준의 1.05배 이하일 때만 전환한다. 작업 크기 미상, 부족한 측정, 품질 실패는 전환하지 않는다.
- 캐시는 원자적으로 기록하며 프로세스 간 key별 잠금으로 동시 변경을 보존한다. 결정적 실패는 같은 환경 key에서 격리하고, OOM은 해당 job에만 적용한다.

실제 idle scheduler, 모델별 session adapter, host의 자원 승인·lease 연결은 남아 있다. 현재 catalogue의 pack·certificate는 비어 있으며 허위 `enabled` 항목은 없다.

### 격리 실행과 CPU 복구

- 인증된 loopback과 binary IPC로 Python 3.11 추론 worker를 호출한다. pickle은 사용하지 않고 header 64KiB·tensor 합계 64MiB를 제한한다.
- job·epoch·request ID, dtype과 shape를 확인한다. session 호출은 직렬화하며 부분 frame, 막힌 전송, 응답 timeout을 부모의 기한으로 제한한다.
- 모델 해시를 검사하고 명시한 EP가 설치·선택됐는지 확인한다. GPU load는 lease 식별자가 없으면 거부한다. 실제 host lease 검증과 연산별 EP 배정 인증은 후속 작업이다.
- DirectML의 sequential 실행과 memory pattern 제한은 [공식 문서](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html)를 반영했다.
- POSIX에서 부모가 사라지면 worker의 PID와 PGID가 같은지 확인한 후 자기 프로세스 그룹만 종료한다. Windows는 기존 SDK의 kill-on-close Job Object 경로를 재사용한다.
- `run_with_cpu_recovery`는 명시적인 backend 오류에 한해 분석 단위 전체를 CPU로 한 번 재실행한다. 참여 모델 전체를 CPU 계획으로 교체하고, 새 epoch를 만들며, 기존 worker의 종료를 확인한 뒤 시작한다.
- 취소·입력 오류·일반 파일/ffmpeg 오류는 엔진을 바꾸어 재시도하지 않는다. CPU도 실패하면 두 원인을 보존하고 종료한다.
- `AttemptOutput`에 명시한 산출물만 시도별 디렉터리에 쓰고, project revision을 확인한 원자적 pointer 갱신으로 공개한다. 실패한 시도는 공개하지 않고 이전 성공 결과를 유지한다.

한계: POSIX 내부 watchdog만으로 GIL을 영구 점유하거나 OS에서 정지된 worker의 부모 사망까지 보장하지는 않는다. host의 프로세스 소유권·lease 연결과 실제 Windows 검증이 제품 전환 전에 필요하다.

### 결과 읽기 연결

Nest의 `LocalArtifactStorage`와 대사 workflow, Python의 대사 후보 생성·렌더 읽기가 committed pointer를 해석하도록 연결했다. 기존 프로젝트는 기존 경로를 계속 읽는다. Windows 역슬래시 상대경로는 storage 경계에서 정규화하며 외부 경로 이탈은 거부한다.

`stage_paths` 같은 쓰기 경로는 기존 논리 경로를 유지한다. 읽을 때만 확정된 세대로 해석하여 후속 LLM·렌더 단계가 이미 성공한 세대 파일을 덮어쓰지 않게 했다. 제어된 workflow 시험에서는 LLM 중복 호출이 없었다.

**세 플러그인의 실제 모델 추론 전체를 새 복구 wrapper로 전환한 상태는 아니다.**

## 품질 검증 범위

새 비교기는 pose·face 수치, embedding cosine, 음성 text·timing과 최종 의미 출력을 함께 확인한다. 빈 기준, NaN·Infinity, 누락 fixture를 PASS로 보지 않는다. snapshot·qualification CLI는 원본 golden을 수정하지 않는다.

첨부된 네 모델을 새 worker에서 실제 CPU로 실행하고 동일 ORT 1.31.0 직접 실행과 비교했다.

| 모델 | 입력 수 | 출력 tensor 수 | 최대 절대차 |
|---|---:|---:|---:|
| YOLO pose | 24 | 24 | 0 |
| YuNet | 24 | 288 | 0 |
| AuraFace | 30 | 30 | 0 |
| CLIP visual | 24 | 24 | 0 |

총 102개 입력과 366개 출력 tensor가 bit 단위로 같았고 모든 worker의 종료를 확인했다. **CPU 전달·격리 실행 검증이며, PyTorch→ONNX 변환 품질·최종 하이라이트 품질·GPU 속도 인증은 아니다.**

기존 사용자 검토 안무 fixture 3종과 첨부 Windows 결과의 해시를 `corpus-inventory.json`에 기록했다. 여섯 모델·세 플러그인을 포괄하는 CPU·기존 가속 golden, 배포 가능한 local fixture, 실장비 검증표가 완성되지 않아 release 품질 gate는 BLOCKED다. 개인 영상·참조 얼굴은 배포 fixture로 복사하지 않았다.

## 독립 리뷰와 수정

새 context의 read-only reviewer 한 명이 이번 변경만 검토했다. Critical 0개, Important 3개, Minor 0개였다.

1. Windows 상대경로 거부: 역슬래시 경로와 legacy·committed 읽기 시험으로 재현한 뒤 storage 정규화로 수정했다.
2. 동시 cache 쓰기가 다른 프로세스의 실패 기록을 덮는 문제: 실제 multiprocessing으로 재현하고 key별 OS file lock으로 수정했다. 동시 OOM job 기록도 보존한다.
3. 부모 종료 뒤 worker의 자식 프로세스가 남는 문제: 실제 하위 프로세스와 중단된 backend 호출로 재현한 뒤 소유 그룹 종료로 수정했다.

전체 Nest 시험에서 발견한 생성자 fixture 순서도 수정했다. 추가 품질 점검에서는 빈·비유한 의미 출력과 `True`/`1`의 잘못된 동등 판정을 네 개의 실패 시험으로 재현한 뒤 수정했다. 수정 후 전체 회귀를 재실행했다.

## 설계 대비 남은 작업

| 단계 | 현재 상태와 남은 작업 |
|---|---|
| T01 품질 기준 | 비교·snapshot·BLOCKED 보고 도구 구현. 전체 golden·배포 fixture·manifest schema 필요 |
| T02 계약 | 기본 식별자·registry·package 구현. 완전한 pack/IO/support manifest와 공유 계약 fixture 필요 |
| T03 환경 | 정규화·adapter 매핑 검사 구현. native DXGI·Apple probe와 Electron 연결 필요 |
| T04 pack | 미구현: 정확한 호환 lock, build·install·rollback |
| T05 worker | ONNX 격리·IPC·종료 구현, CPU 실모델 검증. native GPU·Windows·host 소유권 연결 필요 |
| T06 자원 조정 | 미구현: host lease, CPU admission, heartbeat bridge |
| T07 선택 | 선택·제한 측정·cache 구현. 모델 adapter와 idle 실행 연결 필요 |
| T08 복구 | 공통 복구·atomic commit·결과 읽기 구현. 실제 plugin 실행·상태 초기화 연결 필요 |
| T09–T12 모델 연결 | 미구현: 동일 전후처리를 사용하는 pose·face·CLIP·Whisper adapter와 인증된 CPU 기준 |
| T13–T15 배포 | 미구현: optional vendor, 설정·진단 UI, 실장비 release 검증 |

다음 순서는 native 환경·pack 소유권·resource lease → 모델별 adapter와 CPU golden → plugin 전체 복구 연결 → 장비별 품질·속도 검증이다. 품질·소유권 gate가 없는 GPU 경로를 활성화하지 않는다.

## 구현 중 판단

- native worktree 도구가 중첩 repository를 거부하고 상위 workspace는 Git repo가 아니어서 수동 Git worktree를 사용했다. 원본 dirty 변경을 재현했으며 merge·commit은 하지 않았다.
- 여러 repo와 T번호 계획을 기록하기 위해 skill의 단일 repo helper 대신 private JSONL ledger를 사용했다. 부분 구현·검증·제약을 남겨 다음 작업자가 완료 범위를 오해하지 않게 했다.
- 사용자 요청대로 실사용 GPU 활성화보다 공통 기반·CPU 복구 검증을 먼저 진행했다. 따라서 이번 변경으로 앱의 실사용 GPU 선택이 바뀌었다고 주장할 수 없다.
- 단일 모델 대신 `AnalysisContext` 전체를 복구한다. 일부 모델만 CPU로 바꾸어 결과가 혼합되는 위험을 막기 위한 결정이다.
- `AttemptOutput`의 명시적 산출물 목록과 읽기·쓰기 경로 분리를 사용했다. 소비자가 누락되면 이전 결과를 읽을 수 있으므로 실제 plugin 전환 전에 추가 검증이 필요하다.
- pack·model 계약은 현재 기반 구현에 필요한 식별자 부분을 먼저 만들었다. 설치·호환성 계약의 완성을 대체하지 않는다.
- standalone Nest 작업트리의 시험을 위해 선언된 번들 폰트를 build output에, 기존 ignored 환경 fixture를 작업트리에 복사했다. 제품 build 코드·golden·원본 설정은 바꾸지 않았다.
- 리뷰가 판단을 유보한 corpus·native probe·pack·lease·GPU 배정·모델 adapter·실제 plugin 복구·UI·실장비 배포는 위 표에 미완료로 남겼다. 기존 dirty 변경 자체는 이번 리뷰에서 제외했다.

## 검증 결과와 증거

- Python 전체: **3,049 passed, 6 failed, 7 skipped**. 실패 6개는 시작 전 baseline과 같은 렌더링 golden·전환 시험이며 새 실패는 없다. golden은 수정하지 않았다.
- Nest 전체: **5,246 passed, 0 failed, 9 skipped**. TypeScript build와 두 저장소의 `git diff --check`도 통과했다.
- 새 worker의 첨부 모델 CPU 비교: **102개 입력·366개 출력 tensor 모두 동일**, 최대 절대차 0, worker 종료 확인.
- 원본 dirty 파일·모델 **120개 해시 일치**. 실제 영상 E2E 등 빠진 장비·영상 검증은 PASS로 처리하지 않았다.

Python의 기존 실패 6개:

- `tests/test_annotation_layer_renderer.py::test_counter_formats_value_and_matches_goldens`
- `tests/test_annotation_layer_renderer.py::test_chip_tones_and_badge_goldens`
- `tests/test_annotation_layer_renderer.py::test_arrow_goldens`
- `tests/test_annotation_layer_renderer.py::test_arrow_target_above_golden`
- `tests/test_annotation_layer_renderer.py::test_layer_without_area_or_zone_tops_is_byte_identical_to_before`
- `tests/test_clipper_video_render_ranking_transitions.py::test_real_render_list_holds_still_through_transitions_and_switches_at_handoff[fadeblack]`

재현 명령(Python은 작업트리의 `.implementation-evidence/run_tests.py` 사용):

```text
UV_NO_SYNC=1 UV_PROJECT_ENVIRONMENT=/Users/jina/project/adlight/desktop/clipper_python/.venv python3 .implementation-evidence/run_tests.py -q
npm run build
node --test test/*.test.js
```

loopback·실제 자식 프로세스 시험은 허용된 로컬 실행 권한으로 실행했다. Nest의 standalone build에는 별도로 기록한 기존 폰트·환경 fixture를 준비했다.

두 작업트리의 `.implementation-evidence/`에 상세 기록이 있다. Python의 `implementation.patch`는 원래 dirty 상태와 이번 변경 사이의 차이만 담는다. 다음 증거도 함께 보존한다.

- `original-baseline/baseline.json`: 소스·모델·corpus의 해시와 기존 diff.
- `original-checkout-preservation.json`: 원본 120개 파일 보존 검사.
- `cpu-model-transport.json`: 첨부 네 모델의 CPU 직접 실행과 worker 비교.
- `corpus-inventory.json`: 기존 품질 자료와 아직 부족한 release 증거.
- `progress.jsonl`: 단계별 진행·검증·판단 기록.
