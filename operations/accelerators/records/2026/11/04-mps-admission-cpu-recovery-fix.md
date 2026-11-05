# MPS 시작 거절 원인과 CPU 복구 진단 수정

2026년 11월 4일 KST. 실제 YOLO와 원본 영상 한 프레임으로 MPS 추론 전 메모리 예약 거절을 재현했고, macOS 공유 메모리 검사와 거절 진단 전달을 수정해 원격 dev에 반영했다. 기존 안무 품질 정책과 SAM OFF는 유지했다. 앱 재빌드와 같은 세 영상 전체 재측정은 요청을 전달한 무대 하이라이트 채팅에서 이어간다.

## 원격 dev

| 저장소 | 검증한 기준 | 반영한 커밋 |
|---|---|---|
| Python | `9a9a940801f03c5a37e8a5897a474e5bb14bb7fd` | `5d565dfa96c1fa3bd6a4b94e9dc96110088f0dab` |
| Electron | `febb1670a56efc2348ad42f2b48ca4f30b74f7a7` | `6831d8de76d34bb6ae2523122e9c6271ba68d00f` |

일반 푸시 후 `git ls-remote origin refs/heads/dev`로 두 서버 SHA의 일치를 확인했다. Electron 검증 중 추가된 `8afb508`과 병합 커밋 `febb167`의 로컬 실행 경로·프로세스 정리 변경도 포함했다. Nest와 Angular는 이번 수정 대상이 아니다.

## 확인한 실패 원인

기존 Electron 검사는 모든 운영체제에서 `os.freemem() × 0.7`만 사용했다. macOS에서 캐시로 쓰다가 회수할 수 있는 메모리는 예산에 반영되지 않았다. 네이티브 모델은 첫 추론 전에 이 검사에 예약을 요청하므로, 이 단계가 거절되면 MPS 추론을 한 번도 하지 않고 CPU 재분석으로 넘어갔다.

Made My Night 원본 50초 프레임, 1920×1080, 기존 `yolov8s-pose.pt`, FP32, 입력 크기 640으로 짧게 재현했다. 실제 요청량은 **302,892,000바이트**, 검사에서 읽은 여유 메모리는 **258,195,456바이트**였다. 호스트가 `/acquire`에 **HTTP 409 `memory_admission_deferred`**를 반환했고, 성공한 추론은 **0회**였다. 작은 MPS 행렬 연산은 여유 메모리가 더 많은 별도 시점에 성공했으므로, 이 Mac의 MPS 자체가 지원되지 않는 상황은 아니었다.

과거 세 영상의 최초 거절 응답은 보존되지 않았다. 따라서 이번에 재현한 원인을 과거 세 작업의 최초 원인으로 소급 확정하지 않는다. 같은 실패가 다시 발생하면 아래 진단으로 구분할 수 있다.

## 수정 내용

- macOS에서는 운영체제의 VM 통계와 압력 상태를 함께 읽는다. 현재 free 값과 VM free 값 중 작은 값에, file-backed·purgeable 중 큰 풀의 절반만 더한다. 풀을 합산하지 않아 중복 계산 가능성도 줄였다. 여기서 512MiB를 남기고 정상 상태에서는 70%, 경고 상태에서는 50%를 예약 예산으로 삼는다. 위험 상태·조회 실패·해석 불가·오래된 관측은 거절한다. 이 비율은 앱의 보수적인 예약 정책이며 OS가 보장하는 할당량은 아니다.
- inactive·speculative·compressed·전체 RAM을 가용 예산에 더하지 않는다. 공유 메모리의 회수 가능 풀과 압력은 [Apple XNU 설명](https://github.com/apple-oss-distributions/xnu/blob/main/doc/vm/memorystatus_notify.md)을 참고했다. sysctl의 `1/2/4`는 내부 압력 enum 대신 사용자 공간 알림 값으로 해석하며 [XNU 변환 구현](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_memorystatus_notify.c)을 확인했다.
- 모든 어댑터의 기존 예약을 호스트 예산에 합산하고, 예약 증가도 다시 검사한다. 비동기 관측을 기다린 뒤 소유권·동시 예약 상태를 적용해 중복 승인을 방지한다. Windows의 host free 70%와 전용 GPU free 70% 제한은 유지한다.
- `memory_admission_deferred`, `adapter_busy`, 소유권·실행기·lease 오류의 상태와 안전한 판단 수치를 허용목록으로 보존한다. HTTP 응답 본문 읽기는 제한하고 토큰·헤더·전체 환경은 복사하지 않는다.
- 진단을 Python 자식 프로세스 응답에서 부모로 전달하고, CPU 재분석의 최종 `acceleration.fallback_error`와 같은 revision의 `json/acceleration.json`에 남긴다. 기존 `fallback_reason` 분류, 취소, 종료 확인, 한 번의 CPU 재시도 계약은 유지한다.

새 ONNX 후보 승인이나 품질 인증을 발급하지 않았다. 기존 네이티브 MPS 경로의 자원 검사 수정이며, 안무 메인·이름·구간 조립 정책과 모델 정밀도는 변경하지 않았다.

## 실제 MPS 실행과 프로브 비용

수정한 호스트와 앱의 `PoseEngine`을 실제 자식 프로세스로 연결했다. 단일 프레임 확인에서는 MPS 추론 2회가 성공했고, 모델 파라미터 장치는 `mps:0`, GPU 할당은 약 48MB였다. CPU와 MPS가 각각 5명을 검출했고 대응 박스 최소 IoU는 **0.9999992847**이었다. 이때 관측은 free 약 83MiB, file-backed 약 3.56GiB, 정상 압력이었으며 계산된 예약 예산 약 977MiB 안에서 약 289MiB 요청을 허용했다.

추가 요청에 따라 같은 프레임으로 연속 MPS 추론 **24회**도 확인했다.

| 관측 | 실제 결과 |
|---|---|
| MPS 추론 | 24회 성공, 모델 장치 `mps:0` |
| 최초 추론 | 약 1,013.9ms |
| 이후 23회 중앙값 | 약 29.36ms/회 |
| `vm_stat` 실행 | 최초 예약에서 1회, 약 1.27ms |
| 압력 sysctl 실행 | 최초 예약에서 1회, 약 1.39ms |
| 호스트 요청 | acquire 1회, register-native 1회, heartbeat 1회, release 1회 |
| 프레임별 추가 메모리 프로브 | 0회 |

두 메모리 프로브는 병렬 실행하므로 각 시간을 더해 지연으로 해석하지 않는다. `operation_reservation`과 `admit`는 매 호출에 들어가지만, 같은 모델의 예약량이 늘지 않으면 로컬 예약 확인만 수행한다. 호스트 메모리 프로브는 최초 acquire와 실제 reserve 증가에만 연결돼 있다. heartbeat에서는 프로브를 실행하지 않는다. heartbeat 관측을 위한 4.2초 대기는 추론 시간 통계에서 제외했다.

이 검사는 같은 한 프레임의 반복 실행이며 전영상 하이라이트 품질 인증이나 CPU 대비 속도 비교가 아니다. 원래 NativeRecord의 `provider_only`와 `profile_verified=false`는 보수적으로 유지했다. 위 GPU 실행 증거는 별도 계측한 실제 모델 장치·메모리 할당·추론 완료에서 확인한 것으로, 그 필드를 강제로 승인 상태로 바꾸지 않았다.

## 회귀 검증과 독립 검토

- Electron: Node 24.19 빌드 성공, 최신 dev 위 전체 **1,975개 통과**. 메모리·압력·동시 예약·Windows 제한·소유권 집중 검사 **13개 통과**.
- Python: 전체 **3,382개 통과, 5개 건너뜀, 기존 렌더링 6개 실패**. 복구·취소·예약 정책 집중 검사 **30개 통과**, Ruff와 공백 검사 통과.
- 실제 로컬 HTTP 거절이 자식 프로세스를 지나도 사유·상태·관측을 보존하고, Dance와 Person의 새 CPU 프로세스 결과 및 진단이 같은 artifact revision으로 게시되는지 검사했다. 거절 원인·프로세스 전달·최종 결과 검사는 수정 전 6개가 실패하는 것을 확인한 뒤 통과시켰다.
- 독립 검토에서 압력 문자열 객체 조회가 상속 속성을 허용할 수 있다는 문제 1건을 재현했다. `constructor`, `toString`, `__proto__`, `01`, `1e0`를 거절하는 회귀 검사를 추가하고 명시적인 값 비교로 수정했다. 검토자가 해결을 다시 확인했다.
- 초기 전체 검사에는 임시 실행기의 spawn 재귀 문제와 Node 버전·형제 빌드 입력 누락이 있었다. 표준 pytest 실행과 실제 빌드 Node 및 입력 사본으로 바로잡은 뒤 위 최종 수치를 얻었다. 이 실행 환경 문제를 제품 수정에 섞지 않았다.

남은 렌더링 실패 6개는 수정 전 원본 dev에서도 해당 항목만 다시 실행해 동일하게 재현했다.

1. `test_counter_formats_value_and_matches_goldens`
2. `test_chip_tones_and_badge_goldens`
3. `test_arrow_goldens`
4. `test_arrow_target_above_golden`
5. `test_layer_without_area_or_zone_tops_is_byte_identical_to_before`
6. `test_real_render_list_holds_still_through_transitions_and_switches_at_handoff[fadeblack]`

Windows 실기기 실행과 같은 세 영상 전체의 GPU 사용·품질·시간은 후속 앱 실측 범위다.

## 보존과 재현 자료

원본 네 저장소의 추적 파일 **4,955개와 HEAD가 모두 그대로임**을 다시 확인했다. Python 기준 dev 대비 모든 플러그인, 공유 얼굴·음성 코어, SDK 소스 차이는 없다. 원본 앱·프로젝트·교정본·생성 CoreML 캐시를 교체하거나 삭제하지 않았다.

[검증 JSON](04-mps-admission-cpu-recovery-fix.json)에 커밋·관측·로그 SHA·원본 보존 결과를 남겼다. [증거 폴더](04-mps-admission-evidence/)에는 재현 전후 JSON, 연속 실행 계측, 테스트 로그와 실행 보조 스크립트가 있다. 수정 전·후 Electron 호스트 모듈도 사본으로 보존했다. 실행 보조 스크립트는 기록된 Python 작업 트리와 사용자 원본 영상·모델 경로를 사용하므로 해당 경로와 SHA를 먼저 확인한다.

최종 앱 재빌드에는 Python `5d565df`와 Electron `6831d8d` 또는 그 후손을 사용한다. 기존 세 영상과 대표 이미지를 유지해 실제 GPU 추론 증거와 CPU 복구 여부, 시작부터 완료까지 시간, 하이라이트 품질을 다시 확인한다.
