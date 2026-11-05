# Mac 얼굴 분석 추가 가속 결과

2026년 11월 4일. Made My Night 안무 하이라이트를 기존과 같은 영상·참조 사진 31장·설정으로 비교했다. 전체 실행은 334.958초에서 266.034초로 20.58% 단축됐다. 최종 63개 하이라이트의 시작·종료·인물·썸네일 상대 경로와 설정·집계가 완전히 일치했다. 새 실행에는 전체 CPU 재분석이 없었다.

이번 전체 성능 검증 범위는 안무 하이라이트 하나다. 인물·대사의 모든 모델을 GPU로 바꿨다는 의미는 아니다. Windows 조합 비교·빌드는 별도 채팅에서 계속한다.

## 확인한 병목과 적용한 변경

YuNet 얼굴 검출이 누적 104.721초를 사용했다. 6,555개 요청에는 원본 1920×1080 프레임 3,167건과 크기가 계속 달라지는 얼굴 영역이 섞여 있었다. 캐시를 제외한 원본 프레임이 주요 비용이었다.

원본 FP32 YuNet의 입력·출력 shape만 고정하여 동일한 padding·pixel·decode·threshold·NMS를 유지하는 CoreML 경로를 추가했다. 원본 크기 프레임에만 적용하고, 다른 크기의 영역은 기존 OpenCV CPU로 처리한다. 동적 shape CoreML은 실제 샘플에서 더 느렸으므로 적용하지 않았다. FP16 YuNet은 최대 좌표 차이 약 1.84pixel이 나와 채택하지 않았다.

자세 분석이 끝난 뒤 원래 YOLO MPS 모델을 파괴하고 동기화·캐시 반환·실제 할당량 0을 확인한 후 그 모델의 예약량만 호스트에 반환한다. 나중의 원경 자세 확인은 같은 모델·설정으로 다시 생성한다. 메인 선택이 끝나면 더 이상 필요 없는 원본 크기 YuNet 세션도 해제한다. 모델 예약을 반환해도 lease 독점·소유권·향후 메모리 승인 한도는 유지한다.

AuraFace는 CPU 비교 출력을 독립 배열로 복사하고 CPU 가중치를 해제한 뒤 GPU를 승인받는다. 후보를 거절하면 GPU 후보를 먼저 파괴한 후 원본 CPU 세션을 다시 만든다. 공유·외부 소유 CPU factory는 임의로 해제하지 않는다.

SFace도 원본 FP32 가중치·OpenCV 정렬을 유지한 CoreML 후보를 구현했다. 실제 얼굴 crop 비교와 속도 검사·실행 노드 확인을 통과해야 선택한다. 이번 전체 실행에서는 동시 메모리 예약이 1,079,002,652byte로 당시 허용량 897,232,896byte를 초과하여 원본 CPU를 유지했다. 가속 실패 후 결과를 섞지 않으며, 선택된 GPU의 나중 실패는 기존 전체 CPU 재분석 경계로 전달한다.

## Made My Night 전체 측정

| 단계 | 변경 전 초 | 변경 후 초 |
|---|---:|---:|
| YOLO 자세 분석 | 75.237 | 62.945 |
| 메인 인물 선택 | 118.110 | 73.555 |
| 장면·구간 구성 | 28.758 | 27.514 |
| 얼굴 특징 추출 | 34.608 | 33.258 |
| 인물 묶기·교차 확인 | 47.125 | 42.379 |
| 메인 썸네일 | 8.977 | 7.466 |
| 단체 썸네일 | 5.261 | 5.018 |

상위 단계 시간에는 중첩 작업이 있으므로 하위 항목과 중복 합산하지 않는다. YOLO 연산 자체는 이번에 바꾸지 않았으며 그 시간 차이까지 YuNet 코드의 효과로 해석하지 않는다. 주요 직접 개선은 얼굴 검출 누적 104.721초 → 65.404초와 메인 인물 선택 단계다.

실행기 내부 동일 경계 비교는 333.575초 → 264.990초로 20.56% 단축이다. 위 전체 wall time에는 참조 입력 준비 등이 더 포함된다. 이전 AuraFace 개선 직후 327.616초 결과와도 최종 목록이 같다.

측정은 사용자 허락을 받아 Clipper 앱을 닫고 별도 빌드·모델 측정을 중지한 조건에서 수행했다. 잘못 겹쳐 실행된 중간 두 건은 부모에서 취소해 자식까지 종료했고 속도·품질 결론에서 제외했다. 마지막 단독 실행만 최종 수치에 사용했다. 앱을 다시 연 뒤 관측한 메모리는 normal, 예산 1,026,973,695byte였고 얼굴 두 모델의 예약량 857,138,640byte보다 컸다. 이는 재기동 상태의 관측이며, 앱을 연 상태에서 전체 시간을 다시 측정한 결과는 아니다.

## 실제 모델 실행과 품질

| 모델 | 마지막 전체 실행 |
|---|---|
| YOLO Pose | 기존 PyTorch MPS, 2,459회 |
| AuraFace | CoreML/CPU 혼합 graph, 요청 4,603회 |
| YuNet | 원본 크기 CoreML 2,275회·CPU 영역 3,389회 |
| SFace | 원본 OpenCV CPU 3,925회, 메모리 승인 거절 |
| Whisper·CLIP | 이번 안무 작업에서 호출되지 않음 |

CoreML 노드 실행을 ORT profile로 확인했다. MLComputeUnits ALL이므로 이 기록을 모든 연산의 물리 GPU 실행 증명으로 확대하지 않는다.

최종 main 49개·group 14개, 설정·집계와 구간별 인물 배정까지 일치했다. 최종 목록의 정규 JSON SHA256는 20e815c03c379b28af5b8e76031cb09db917037f2814fd82c46055fae6ce8d0d다. 영상 해시는 3400a0f3d21399609c54b38884d0208bf28e2541e10d450c5135306deba2e363이고 참조 사진 31장은 기존 입력 manifest와 대조했다. 판정 threshold·분석 간격·영상 해상도·얼굴 정렬·클립 품질 규칙을 바꾸지 않았다.

두 자세 분석 단계에서 MPS 할당이 각각 34,124,800 → 0byte, 34,384,896 → 0byte로 내려갔고 예약 반환 HTTP 200을 확인했다. YuNet 세션 반환도 200이었다. 원본 영상 영역에서 생긴 아주 작은 FP32 좌표 차이로 AuraFace 캐시 miss가 8건 늘었지만 최종 목록·집계는 같다.

원본 FP32 SFace 샘플 비교에서 OpenCV median 5.640ms, ORT CPU 3.639ms, CoreML 2.987ms였다. FP16 CoreML은 1.428ms였지만 더 엄격한 FP32 품질 기준을 유지해 채택하지 않았다. 이 소규모 측정값을 전체 인물/대사 플러그인의 속도로 해석하지 않는다.

## 아직 CPU인 작업과 플러그인 범위

안무에서 크기가 다른 얼굴 영역의 YuNet과 메모리가 부족한 SFace가 CPU로 남았다. 이 둘의 강제 GPU 실행은 이번 장치의 속도·메모리 측정에 맞지 않는다. SFace CoreML 경로는 여유가 있는 조건에서 실행 전 품질·속도 비교 후 사용할 수 있다.

공통 AuraFace helper는 인물 하이라이트에도 연결돼 있다. 다만 이번에 전체 인물 작업을 추가 측정하지 않았으며, 인물의 YuNet에는 source 크기 준비가 연결되지 않아 새 정적 크기 후보가 자동 적용되지 않는다. 인물 app의 기존 성능 요약 face_provider 문자열은 CPU로 고정돼 있어 실제 실행 판단은 acceleration 모델 진단으로 해야 한다.

대사의 CLIP은 기존 OpenCLIP/PyTorch MPS 경로를 사용할 수 있다. 인물·대사의 Whisper는 현재 faster-whisper/CTranslate2 CPU int8 경로다. Mac MPS를 받으면 CPU로 바꾸는 코드가 유지되어 있다. 이 후속 작업에서 Whisper를 새 구현으로 교체하지 않았고, 안무 속도 개선을 그 모델들의 성능 검증으로 보고하지 않는다. 영상 디코드도 이번 실측에서 실제 하드웨어 디코드가 확인되지 않아 바꾸지 않았다.

## 재현과 회귀 검증

- Python: 공통 가속·공통 얼굴·안무·인물 2,073개 통과, 54.80초.
- Electron: 전체 1,977개 통과, test concurrency 4, 34.812초.
- 첫 기본 동시 실행에서는 기존 소유 프로세스 종료 시험의 EPERM과 Node 테스트 IPC 역직렬화 오류가 나왔다. 해당 파일 20개 검증은 개별 재실행에서 통과했고, 전체를 제한된 동시성으로 다시 실행해 1,977개 모두 통과했다. 이 재실행 사이 제품 코드를 바꾸지 않았다. 최초 실패 로그도 보존했다.
- Ruff 변경 helper·테스트·pose/face runtime 통과, 두 저장소 diff check 통과.
- 독립 읽기 전용 검토에서 source hash와 소비 bytes 불일치, 얼굴 호출 중복 집계, 거절 후보 생존 중 CPU 재생성, SFace 첫 비표준 crop 이후 CPU/GPU 혼합 가능성을 지적받아 red/green 검증으로 수정했다. 마지막 weakref/실제 할당 확인 후 추가 치명·중요 발견 없음.
- 기존 전체 CPU 복구·취소·결과 revision 회귀도 위 테스트에 포함된다. 시험에서 GPU 늦은 실패를 강제로 만들었을 때 CPU 재분석 경계로 전달되는지 검증한다.

전체 실행 harness·고정 입력·비교 스크립트·원본 shape profile·모델별 실측·red/green·최종 로그를 evidence 폴더에 보존했다. run_final은 실제 Electron AcceleratorLeases와 앱 venv 의존성에 검증한 Python 소스를 연결한다. 해당 절대 경로가 존재하는 동일 Mac에서 재현하며, 원격 dev의 아래 커밋과 patch로 소스를 복원할 수 있다. 호스트 token은 실행 시 새로 생성하며 기록하지 않는다.

## dev와 새 Mac 앱

- Python dev: 17259bcf1c7c466cd7108e04a25250172dd28151.
- Electron dev: 849a51b7906f84054e1a55d02da45bfa3768be6f.
- 원본 8개 저장소에서 branch dev·실제 원격 dev SHA 일치·추적 소스 변경 0을 다시 확인했다. 다른 채팅의 변경을 reset/stash/clean하지 않았다.
- 원본 Electron에서 npm run build:app:mac:arm64:local-api 실행 exit 0.
- 앱: /Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app.
- 패키지 webApiBaseUrl=http://127.0.0.1:3000, autoUpdateDisabled=true.
- 변경 Python 파일 10개 패키지 SHA 일치, Electron 예약 반환 코드 app.asar SHA 일치.
- 실제 ensurePluginVenv 업데이트로 기존 안무 venv의 로컬 패키지 4개 갱신. source fingerprint와 설치 모듈 7개 SHA 일치.
- 앱을 다시 열어 안무 URL 입력 화면을 확인했다. 로컬 API 3000 health와 새 앱 Nest 52454/v1/health HTTP 200.
- 사용자 본인이 삭제한 프로젝트 상태는 그대로 유지했으며 이전 결과를 앱에 다시 추가하지 않았다.
- 개발/운영 서버 배포는 하지 않았다. Windows 채팅에는 두 커밋과 측정 완료·빌드 제한 해제를 전달했다.

직전 기본 Mac 앱은 Electron의 .tmp/mac-before-remaining-face-20261104에 별도로 보존했다. 이전 비교 앱 2개와 Python CoreML 캐시도 실제 파일/링크 수 858·870·38로 그대로 존재한다. 최종 Git 미추적 목록은 0개이며 해당 경로의 .git/info/exclude 규칙이 이미 적용돼 있음을 확인했다. 이 가속 구현 작업에서는 그 규칙을 추가하거나 산출물을 삭제하지 않았다.

[원본 8개 저장소 독립 조사](/Users/jina/project/adlight/.codex/operations/env-runtime/records/2026/11/04-original-eight-repositories-independent-audit.md)는 조사 시점의 Electron 1,720개와 Python 38개가 원본 소스 수정이 아닌 이전 앱·캐시라는 근거를 담고 있다.
