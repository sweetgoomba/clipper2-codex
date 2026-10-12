# W14 → W13 공통 얼굴 계약·파일 소유권 인계

2026-09-30 KST. **W14 제안, W13 상호 확인 대기.** [W14 MVP·artifact 제안](30-w14-person-highlight-design-proposal.md)과 [W13 9/30 설계](30-w13-investigation-evaluation-design.md)를 함께 본다. 제품 코드·모델·실행 환경은 수정하지 않았다.

## 1. 독립 패키지와 공개 표면

Python workspace에 `clipper_face_core/`라는 별도 workspace package를 두는 **경로 제안**이다. `clipper_plugin_sdk`의 필수 의존성에 ML을 넣지 않는다. Dance와 Person plugin이 각자 pyproject에서 선택 의존성으로 가져가고 각 plugin venv·모델 준비를 유지한다. 공개 API는 `detect_all(frame, frame_ref)`, `align_and_embed(frame, observation)`, `cosine_distance(a,b)`, `rank_representatives(observations, group_embedding)` 같은 작은 독립 기능과 versioned DTO를 우선한다. shot-local tracking과 영상 단위 clustering의 **계산 도구**는 공용 후보이나 threshold, main 선택, 멤버 참조 mapping, scene 정책, UI 표시, job/과금은 소비자가 소유한다. 공개 타입에 `DanceSegment`, `PersonGroup`, Angular/Nest UI·job 타입이나 소비자 이름 allowlist를 넣지 않는다.

| 공개 값 | v1 제안 규칙 |
| --- | --- |
| `FrameRef` | `sourceSha256`, streamIndex, 원본 `pts` 정수와 `timeBase={num,den}`, source-relative `timeMs`와 frame width/height/rotation. display-orientation 좌표인지 명시 |
| `FaceObservation` | analysis 범위 observationId/version, shotId, pixel `xyxy` bbox(회전 적용 display frame 기준), 같은 frame의 정규화 `xyxy` 파생값, 5 landmarks, detect score, 품질 근거, 상태/실패 코드 |
| `Track` | `{shotId, trackId}`가 유일 키, 관측 ID와 source `[startMs,endMs)`, gap·validity. 한 frame의 얼굴과 track은 1:1; shot cut에서 track 종료 |
| `Embedding` | float32 L2 정규화, dimension, `embeddingSpaceId`(recognizer weight hash+전처리/정렬 버전+output norm/거리 규칙), 모델 id·파일 SHA-256, backend/library version, source observation ID. 민감 벡터는 일반 로그에 기록하지 않음 |
| `ModelRef/ConfigRef` | detector/recognizer 파일별 SHA-256과 code/adapter version, detect/align/sample/config hash, device/backend. 캐시는 source+model+config+schema fingerprint로 범위화 |
| 실패/불확실 | `decode_failed`, `model_unavailable`, `no_detection`, `below_detector_threshold`, `align_failed`, `embedding_failed`, `invalid_geometry`, `uncertain_group`. 검출 후 embedding 실패를 관측 삭제로 바꾸지 않음 |

`timeMs`는 원본 source PTS를 공통으로 표시한 파생값이다. 일정 FPS를 가정해 frameIndex/fps로 원본 시각을 대체하지 않는다. `[startMs,endMs)`와 pixel bbox는 변환 규칙을 버전으로 고정한다. observation/track ID는 **analysis revision 내부에서만 안정적**이고 cluster 순번을 영속 group ID로 쓰지 않는다. backend가 바뀌면 embeddingSpaceId가 달라지고 이전 centroid·distance threshold·cache를 직접 비교/재사용하지 않는다. 같은 SFace weight라도 정렬/normalization이 바뀌면 호환성 평가 전에는 별도 공간이다.

모델 로드는 플러그인이 명시한 local file의 size+SHA 검증 후 지연 실행한다. 공용 패키지 import 자체는 모델 다운로드·초기화·외부 호출을 하지 않는다. `opencv-python` wheel은 CPU-only이므로 현행 YuNet/SFace CPU를 기준으로 하며 CUDA target은 별도 custom build·실기 검증 없이는 지원 표기로 쓰지 않는다. Windows 한글 user path의 `read_model_buffer()` 우회 이유를 유지한다. 모델·backend 교체는 adapter와 cache/schema 버전을 갱신하고 두 소비자의 compatibility tests를 통과한 뒤에만 배포한다.

## 2. 현행 코드와 소비자 경계

현재 Dance `FaceClusterService.get_face_embedding_candidate()`는 ROI의 최고 score 얼굴 하나만 반환한다. `batch_segment_embeddings()`는 main segment의 sampled bbox만 처리하고 2개 미만 표본의 track을 drop한다. `TrackAssigner.assign(t,bbox)`는 한 번에 bbox 하나만 받아 다중 검출의 one-to-one assignment를 보장하지 않는다. Person에서는 이 경로를 다중 얼굴 서비스로 이름만 바꾸지 않는다. Face core는 모든 검출·정렬·embedding과 공통 품질 근거를 주고, W14 Person adapter가 shot-local 다중 track·cannot-link cluster·appearance interval을 구현한다. W13 Dance adapter는 기존 ROI/main/mapping/crop 결과를 보존하면서 core 도입을 별도 호환 단계로 검토한다. Dance의 `FaceClusterService`를 즉시 삭제하거나 W14가 W13의 main 정책을 바꾸지 않는다.

Electron의 `computePluginSourceFingerprint()`는 현재 uv.lock·SDK·해당 plugin 소스만 해시한다. 새 workspace 공용 패키지의 pyproject/소스를 추가하지 않으면 core 변경 뒤 plugin venv 갱신이 누락될 수 있다. 따라서 등록/패키징 단계에서 **설치되는 workspace 의존성의 소스 fingerprint가 두 plugin의 marker에 반영되는지** 확인하고 Electron 변경의 단일 소유자를 지정해야 한다. `uv sync --package`가 공통 패키지를 실제로 포함하는지 Mac/Windows 각각 검사한다. 공용 API는 기본 SDK 시작 경로에 ML import를 추가하지 않는다.

## 3. 파일 소유·병합 순서 제안

| 파일/계약 | 초기 수정 소유 제안 | 소비·검증 |
| --- | --- | --- |
| `desktop/clipper_python/clipper_face_core/**`, workspace/lock, 공개 API·schema | **W14** | W13은 검토·호환 테스트 요구 제시; 향후 플러그인 이용 가능 |
| `plugins/person_highlight/**`, Person observation/track/group adapter | **W14** | W13은 읽기/계약 리뷰 |
| `plugins/dance_highlight/**`의 기존 `FaceClusterService`, main/reference mapping, crop | **W13** | W14 공용 API와 기존 결과 compatibility test |
| Nest Person analysis/edit/export 계약, Angular Person UI | **W14** (선택 scope 뒤) | W13의 기존 Dance DTO/UX 무변경 회귀 |
| Electron plugin 등록·venv fingerprint·model install | W14가 새 plugin/core 연결 초안, W13과 **단일 파일 소유자 합의 후** 수정 | Dance plugin 설치/모델 캐시 회귀 |
| Web API 새 operation/entitlement | 신규 과금이 선택된 경우 W14 | 기존 Dance/Dialog operation 회귀 |

병합 순서: **(1)** 이 계약을 W13이 확인하고 path/DTO·파일 소유권 고정 → **(2)** W14가 core 관측 API와 기존 Dance adapter의 비파괴 compatibility fixture를 단독 준비 → **(3)** W13이 Dance 소비를 자신의 branch에서 적용/검증 → **(4)** W14 Person adapter와 Nest/Angular 계약 → **(5)** Electron 등록/과금은 선택된 범위에서 필요한 순서로. 각 단계마다 최신 `origin/dev` 재확인·새 격리 worktree를 사용한다. 동일 공용 파일을 W13/W14가 병렬 수정하지 않는다. W13에서 먼저 merge될 변경이 있으면 W14가 그 SHA로 rebase/재검증하고, 반대 순서면 W13이 core SHA를 받아 compatibility tests를 돌린다. 실제 merge는 이번 인계에서 수행하지 않았다.

## 4. 최소 compatibility gate

1. **공용 package 무해성:** SDK만 import/시작할 때 OpenCV/ML import·모델 다운로드가 발생하지 않음. 각 plugin venv에서 package import 및 model hash mismatch 실패가 명확함.
2. **다중 검출:** 한 frame 두 얼굴이 두 observation/서로 다른 track이 되고 동시 출연 cannot-link가 유지됨. no face / blur / invalid bbox / decode 실패 상태가 artifact에 남음.
3. **Dance 회귀:** 같은 fixture의 기존 ROI 최고 score·L2 embedding/거리, main-only segment 처리, reference mapping/unknown, model hash·Windows Unicode path가 adapter 전후 의도대로 유지됨. threshold를 다른 embedding 공간에서 재사용하지 않음.
4. **Person 관계:** 동일 Scene의 A/B 다대다, shot cut 뒤 재등장, 배경 단일 관측 카드, false split/merge 수동 수정, 대표 이미지 override와 재시작 보존.
5. **Export/저장:** 기존 dance/dialog ZIP/shortform origin과 Person의 클립 MP4·인물 ZIP·전체 ZIP 직접 요청을 혼동하지 않음. 이어 붙인 MP4/임의 다중 선택 없음. edit revision 409/원자 저장, 동일 편집 interval 중복 0·같은 scene 다른 경계 보존·겹침 미합침, 취소/재개/원본 소리 검증.
6. **패키징:** Mac arm64·Windows x64 plugin venv 재설치 fingerprint와 모델 준비·취소, CPU 경로 실기. CUDA는 별도 설치/build와 실행 확인 전 미지원으로 표기.

## 5. 공식 자료 재확인 (2026-09-30)

- [OpenCV Zoo YuNet README](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/README.md): 해당 디렉터리 모든 파일 MIT. 새 `2026may` ONNX는 `2023mar`의 **dynamic-shape 재export**로 설명하며 OpenCV 5 엔진용이다. 최신 파일명만으로 검출 정확도 향상을 주장하지 않는다.
- [OpenCV Zoo SFace README](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md): 디렉터리 모든 파일 Apache-2.0 표기, 현행 `2021dec` weight 사용. [공식 데모](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/demo.py)는 CPU/CUDA target 선택을 보여주지만 [opencv-python 배포 README](https://github.com/opencv/opencv-python/blob/4.x/README.md)는 사전 빌드 wheel이 CPU-only라고 명시한다. 모델 문서 정확도를 사용자 영상 결과로 환산하지 않는다.
- [InsightFace 모델 규정](https://github.com/deepinsight/insightface/blob/master/python-package/docs/model_zoo.md): 코드 MIT와 제공 pretrained weights의 비상업 연구용 조건이 다르다. [runtime 문서](https://github.com/deepinsight/insightface/blob/master/python-package/docs/runtime.md)는 CPU, 별도 ONNX Runtime GPU 설치의 CUDA, 사용 가능 provider일 때 CoreML을 설명한다. CoreML은 MPS와 다르다. 상용 weight 허가 없이는 교체 후보 보류.
- [ByteTrack 원 제작자 repo/논문](https://github.com/FoundationVision/ByteTrack): MIT 코드를 공개하지만 기본 예제의 Windows/Mac 제품 지원이나 detector weight 권리를 보장하지 않는다. 첫 face-only 다중 track의 선택적 비교 후보이지 이미 적용된 현행 기술이 아니다.

이 자료는 공개 권리·실행 경로 확인이다. 실제 설치 모델 파일의 SHA, Mac/Windows plugin 실행, SFace weight의 학습 데이터 권리 근거와 사업 적용 검토는 배포 판단 전에 별도로 확정한다. W14/W13 쌍방의 API·파일 소유 동의는 아직 받지 않았다.

## 10/1 W14 성공 기준 추가

사용자가 인물·등장 구간 누락과 서로 다른 인물의 오합침을 **동등한 1차 기준**으로 확인했다. W13/W14 compatibility fixture에는 background/단역 발견과 동시 출연 cannot-link를 함께 넣고, 한쪽만 좋아지는 threshold 변경을 자동 채택하지 않는다. 이는 W13의 기존 main/reference mapping 정책을 변경한다는 뜻이 아니다.

## 10/1 W14 MVP 출력 결정

사용자는 확인한 결과 목업에서 인물 행의 전체 클립 ZIP, 클립 행의 개별 MP4, 상단 전체 다운로드를 원하며 체크박스를 제거했다. 이어 붙인 MP4는 **없다**고 명시했다. [W14 서면 설계](../../../../../../docs/superpowers/specs/2026-10-01-person-highlight-mvp-design.md)에 맞춰 Person export compatibility fixture를 직접 요청 3종으로 바꾼다. W13 기존 Dance adapter/ZIP 계약 변경을 뜻하지 않는다. 공통 API·파일 소유권의 W13 상호 확인은 여전히 필요하다.

## 10/1 W14 시험용 코드와 W13 확인 지점

사용자의 빠른 테스트 요청으로 W14가 `feature/person-highlight-mvp-20261001` 격리 worktree에서 `clipper_face_core/**`·workspace/lock·`plugins/person_highlight/**`의 초기 구현을 소유했다. Electron `plugin-venv.ts`에 **Person 환경만** 공통 패키지 source fingerprint를 추가했고 Dance의 기존 ROI/main/mapping/crop 경로는 건드리지 않았다. [패키지 공개 API·현재 한계](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/clipper_face_core/README.md)와 [실행 기록](../10/01-w14-testable-mvp-implementation.md)을 본다.

실제 v1 공개 필드는 제안 표보다 좁다. `FaceObservation`은 source-relative seconds/frame index 기반이며 원본 PTS rational, rotation, landmarks·품질 세부 항목은 아직 없다. `OpenCvFaceBackend.detect`는 모든 얼굴과 실패한 embedding 관측을 반환하고, Person adapter가 shot-local greedy 1:1 track과 frame 동시 출연 cannot-link cluster를 수행한다. model SHA는 SFace weight, config SHA는 backend/검출 설정을 포함하지만 detector 파일 SHA는 `ModelFiles` 검증 및 artifact 별도 필드로 남긴다. 영속 embedding cache는 없다. **W13이 공통 API로 Dance를 이식하기 전에** 이 빠진 프레임/embedding-space 계약과 모델·전처리 fingerprint를 함께 확정해야 한다.

W13에 요청할 compatibility gate: 같은 입력의 기존 Dance ROI 최고 score·main segment·member mapping/crop·unknown이 바뀌지 않는지, Person 공통 패키지 변경 때 Person venv만 재설치되는지, 기존 Dance ZIP/shortform origin이 변하지 않는지. 현재 W14는 Python 합성/가짜 detector·Nest/Angular/Electron 선택 테스트와 기존 weight SHA·backend 생성만 검증했다. W13의 branch·파일을 수정하거나 병합하지 않았다. **소유권/merge 순서 상호 확인은 아직 답변을 받지 않았다.** W14 변경이 먼저 합쳐지면 W13은 확정 SHA를 기준으로 adapter를 적용하고; W13 변경이 먼저 합쳐지면 W14가 최신 origin/dev로 재기준화해 compatibility test를 다시 실행한다.

10/1 개발 앱 검증에서 기존 Dance YuNet/SFace 파일이 존재해도 Person 전용 readiness marker가 없으면 Person만 `not_installed`가 되는 계약을 확인했다. Person은 모델 파일을 복사/삭제하지 않고 자체 marker와 venv를 관리한다. Electron Person 설치가 기존 파일로 건강 상태를 확인하고 marker를 작성한 뒤 Nest Person 시작/health가 통과했다. W13이 Dance adapter에 공용 패키지를 연결할 때도 두 plugin의 모델 파일 공유와 설치/준비 상태를 별도로 검사하는 회귀를 유지해야 한다. 실제 영상 추론과 Dance adapter compatibility 검증은 아직 하지 않았다.

10/1 사용자 시험의 진행 문구를 분리하면서 `group_observations(..., on_intervals_start=callback)` 선택 콜백을 공통 API에 추가했다. 이 콜백은 track clustering이 끝난 뒤 각 그룹의 `FaceInterval` 계산 **직전** 한 번 호출되고, 인자·반환값이 없다. Person adapter만 이를 사용해 `등장 구간 정리 중`을 보고한다. 기본값은 `None`으로 기존 Dance 경로·호출자 동작은 바뀌지 않는다. 관련 단위 테스트는 callback 시점과 Person 전체 문구 순서/진행률 단조 증가를 확인했으며 Person/core 합계 7개 통과했다. W13 소비 여부 및 공통 API 확정은 여전히 상호 확인 대기다.

## 10/1 첫 실영상 결과 후 공통 계약 변경

사용자 결과에서 단일 관측 Person 8의 중복 clip, 한 프레임의 중첩 얼굴 Person 5/6, 흐린 대표 얼굴을 확인했다. W14는 `FaceDetection.sharpness: float | None`과 `FaceObservation.sharpness: float | None`을 **끝에 추가한 선택 필드**로 제공한다. 기존 위치 인자/호출자는 그대로 동작한다. OpenCV backend는 Laplacian 기반 0–1 선명도 값을 전달하고, 공통 그룹 대표 선택은 이를 반영한다. 유효 embedding이 있어도 관측이 단 한 장인 그룹은 `needs_review`다. Person 쪽 shot 검출·중첩 box 제거·clip coalescing은 소비자 adapter 정책으로 두고 공통 API에는 넣지 않았다.

W13 compatibility gate에는 기본값 `sharpness=None`인 기존 fixture의 대표 선택/DTO 직렬화, 같은 프레임의 별개 두 얼굴 cannot-link, optional field를 무시하는 기존 Dance main/ROI/mapping/crop을 포함한다. W13 adapter 소유와 merge 순서는 위와 동일하며 상호 확인은 아직 없다. W14의 Python Person/core 14개 테스트는 통과했지만 Dance 실영상 호환, 새 코드의 37분 영상 정확도, Windows 실행은 미검증이다. [실제 결과와 수정 기록](../10/01-w14-first-result-debug.md).

같은 날 20초 통제 실행에서 작은 얼굴의 Laplacian 값이 비정상적으로 높아 대표 선택 시 80px 이하 bbox의 선명도 기여를 크기에 비례시켰다. 이는 **대표 후보 순위만** 바꾸며 embedding/threshold/cluster ID를 바꾸지 않는다. `sharpness=None` backend는 기존 `quality` fallback을 사용한다. Person adapter의 shot-bound clip padding은 공통 얼굴 모듈 밖에 있으며 W13 Dance 경로에 적용되지 않는다. 공통 Person/core 테스트 16개 통과, 기존 완료 결과의 20초 MP4/오디오 통제 실행은 [평가 기록](../10/01-w14-controlled-first-result-evaluation.md)에 있다. W13 실제 adapter 호환 검토와 파일 소유 상호 확인은 계속 대기다.

그 뒤 Person 전용 `ObservationTracker`에 같은 shot·단일 유효 얼굴·짧은 시간/공간 거리·동일 SFace embedding 공간의 보조 track 연결을 추가했다. 이 약한 연결은 공용 `FaceObservation.association_uncertain: bool = False` 선택 필드로 표시하고 공용 grouping은 해당 그룹을 `needs_review`로 남긴다. 기존 Dance tracker는 변경하지 않았고 선택 필드의 기본값으로 기존 호출을 보존한다. 저장 관측 20초 replay에서 출연자 A 11→7그룹, false merge 0, 약한 연결 6개 관측/확인 필요 8그룹이나 실제 새 추론/37분 호환은 미검증이다. W13이 이 tracking 규칙을 Dance main에 자동 적용해서는 안 되며, 공용 API 소유권·병합 순서 확인 상태는 앞과 같다.

대표와 교체 후보의 순서를 일치시키려고 공용 공개 함수 `rank_representatives(observations) -> list[observation_id]`를 추가했다. `group_observations`의 대표 선택과 Person 후보 생성이 이를 공유한다. 이 함수는 모델/config hash가 다른 embedding 혼합을 거부하고 job·UI 타입을 받지 않는다. W13이 소비할 필요는 없지만 기존 Dance import·main 선택 fixture와 API export 호환을 확인해야 한다. 최신 Person/core 22개 테스트와 Ruff/compileall 통과; 실제 Dance adapter 실행은 여전히 미검증이다.

공용 Nest YouTube source ingest도 W14 시험에서 메타데이터 정확성 결함이 확인돼, 다운로드 뒤 실제 파일 ffprobe의 width/height/duration을 `SourceAsset`에 우선 기록하게 수정했다. 1080p 요청 영상에서 공급자 1080p/실제 720p 불일치를 바로잡는 목적이며 probe 실패 시 종전 공급자 값을 사용한다. SourceAsset 필드·Dance 입력 경로의 타입은 그대로이고 관련 Nest 회귀 44개 통과. W13이 실제 YouTube 입력의 main/mapping/crop 연산에서 변경된 **실제 픽셀 치수**를 사용하는지 compatibility 확인이 필요하다. 기존 저장 작업에는 소급되지 않는다.

Nest Person 결과 계약의 후속 회귀: 수동 병합 뒤에도 기본 `Person N`은 원본 manifest 순번을 유지한다. 대표 그룹의 명시적 이름·대표 이미지가 우선하며, 없으면 병합된 그룹에 저장된 명시적 선택을 이어받고 각 그룹의 대표 이미지 후보를 합친다. W14가 Person 결과 빌더만 수정했고 Dance DTO/adapter나 공용 얼굴 API는 변경하지 않았다. Nest 빌드·관련 18개 테스트와 기존 554그룹 manifest의 읽기 전용 병합 dry run을 확인했다. W13에는 Dance 결과의 이름·대표 이미지 선택이 이 Person 전용 규칙으로 변경되지 않는지 기존 compatibility fixture 유지가 필요하다. 공통 얼굴 API·파일 소유권·merge 순서에 대한 W13의 상호 확인은 계속 대기 중이다.

W14의 추가 오프라인 검토에서 SFace 저장 embedding의 상호 최고 cosine·격차 조건으로 기존 Person 그룹을 합치는 방식도 37분 결과의 다른 두 여성과 방송 로고 오검출을 병합 후보로 제시했다. **공용 `group_observations` 기준이나 W13 Dance main/mapping에 이 후보를 적용하지 않는다.** 20초 자체 라벨만으로 안전성을 판단할 수 없으며 배경/단역·동시 출연 정답이 있는 별도 검증이 필요하다.

180–210초 Person 원본의 199.5초 실제 컷을 구형 밝기 전용 판정이 놓치면서 서로 다른 출연자·객석 여성을 같은 track/group에 넣은 사례를 확인했다. W14 Person adapter의 현행 색 분포 보강 컷 판정과 기존 저장 관측 replay는 이 false merge를 분리했으며, 14개 수동 keyframe 관측의 pairwise precision 0.667→1.000, recall 0.500 불변이다. 이 컷 판정은 Person 소비자 정책이고 공용 얼굴 DTO·W13 Dance shot/main 경로에는 적용하지 않았다. W13 호환 검사에는 기존 Dance 컷·main 선택의 불변과, 장차 공용 track/cluster를 소비할 때 **컷 경계 넘어 IoU만으로 다른 얼굴을 이어붙이지 않는지**를 포함한다. W14의 별도 관측에서 진짜 같은 사람의 인접 embedding cosine도 0.056까지 나와 전역 embedding 하한을 track guard로 즉시 채택하지 않았다. [재생 근거](../10/01-w14-controlled-first-result-evaluation.md).

원본 SHA로 먼저 정한 `[1140,1170)`초의 7개 프레임을 저장 결과를 보기 전 익명 라벨한 추가 점검에서는 명확한 얼굴 6개가 모두 저장 검출과 대응했지만 사람 아닌 음식·장식 검출 3개와 한 출연자의 2그룹 과분리가 있었다. 저장 관측 90개를 현행 Person 코드로 replay해도 2그룹은 유지된다. 공용 API/모델/threshold 또는 W13 Dance adapter 변경은 **없다**. W13은 기존 main/ROI 소비자 호환 확인을 계속 맡고, W14는 이 작은 자체 라벨을 공용 cluster 안전성 증거로 확대하지 않는다. 배경·연속 interval 및 별도 입력 검증, W13의 파일 소유·병합 순서 상호 확인은 여전히 남아 있다. [선택·GT·대조 근거](../10/01-w14-controlled-first-result-evaluation.md).

180–210초 전체 정수 초 30프레임 개발 라벨로 확장하니 구형 결과의 `person_001`은 심사위원 J1과 출연자 T1, `person_013`은 T1과 관객 B3를 섞었다. 현행 W14 **Person adapter 컷 판정**을 기존 box/embedding 90개에 적용한 replay에서는 두 오합침이 사라졌고 34개 라벨 pairwise precision/recall이 0.632/0.403→1.000/0.672였으나 T1은 3그룹, 배경 B6는 2그룹으로 남았다. 196초의 명확한 얼굴 미검출과 187/206초 유효하지 않은 얼굴 관측도 확인했다. W13 Dance main/cut/track 경로 또는 공용 얼굴 API에는 이 정책을 적용하지 않았다. W13 compatibility gate에는 같은 사람과 다른 사람의 **컷을 가로지르는 실제 영상 예시**를 각각 넣어, 단순 IoU 연결과 단순 전역 threshold 완화가 반대 오류를 만드는지 확인해야 한다. 1초 grid는 artifact를 본 뒤 만든 자체 라벨이고 연속 interval·새 추론 품질 증거가 아니다. [상세](../10/01-w14-controlled-first-result-evaluation.md).

37분 저장 관측 전체 replay에서 W14 Person adapter의 큰 밝기 변화 컷 규칙에 실제 컷과 동작 오검출이 섞인 것을 확인했다. 원본 1360.5초의 실제 다른 인물 컷은 색 분포 차이 0.276으로 낮아 `색차<0.28이면 무조건 이어붙임`은 위험하다. W14 전용 `_shot_changed`는 밝기 `>45`에서 색차 `>0.27`을 함께 요구하도록 바꾸고 199.5/1360.5초 실제 컷을 보존했다. 공용 `clipper_face_core` DTO·embedding/cluster threshold와 W13 Dance main/ROI/crop/shot 경로는 변경하지 않았다. 저장 관측 후보는 기존 554그룹/1,301클립 대비 534그룹/790클립이나 중앙 2초·동일인/배경 과분리·음식 오검출은 남는다. W13 compatibility에는 **실제 컷인데 같은 팔레트인 쌍(1360.5초)**과 **밝기 변화가 큰 연속 동작(599.5/1003초)**을 별개 회귀로 유지하되, W14 임계값을 Dance에 그대로 복사하지 않는다. Person/core 직접 실행 25개·Ruff/compileall 통과; Dance 실영상·Windows와 양측 API/파일 소유권·병합 순서 상호 확인은 여전히 남아 있다. [저장 관측 전체 replay](../10/01-w14-controlled-first-result-evaluation.md).

사용자 재시험을 위한 5 fps 조건부 평가안은 **W14 Person 실행 cadence만의 별도 제안**이며 공용 embedding 공간, `FaceObservation` 필드, W13 Dance cadence/main을 변경하지 않는다. 현재는 입력·GT·모델·코드 hash 검증만 했고, 초기 3/3 얼굴 추론 상한을 넘는 새 추론과 새 앱 프로젝트는 미승인·미실행이다. W13은 이 제안을 자신의 compatibility test 통과나 파일 소유권 상호 합의로 해석하지 않는다. [범위·상한](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-01-first-result-p2/additional-inference-scope-proposal.json).

## 10/1 위 조건부 범위 승인·실행 후 W13 인계

사용자가 추가 짧은 창 3회와 gate 통과 시 전체 1회를 승인했고 W14는 네 번 모두 상한 내 실행했다. W14 Person job 입력의 선택적 `sample_fps`를 **2 또는 5**로 검증해 `analyze_video`에 전달하고 출력 manifest에 실제 cadence를 기록한다. 기본값은 2이며 공용 `clipper_face_core` 공개 DTO/API, YuNet/SFace weight/config hash·embedding 공간, 영상 전체 cosine 0.55, W13 Dance main/ROI/mapping/crop·cadence는 바꾸지 않았다. 5 fps 전달 회귀 2개가 통과했고 실제 37분 결과 manifest가 `sample_fps=5`다. W13 compatibility test는 기본 2 fps Person 입력과 기존 Dance fixture 모두 유지하되, 공용 얼굴 공간/cache/threshold 혼용이 없는지 확인한다.

고정 180–210초 배경·동시 출연 개발 라벨 34관측에서 W14 5 fps의 pairwise precision/recall 1.000/0.882, 배경 B6 2→1그룹, 라벨 오합침 0으로 조건부 gate가 통과했다. 별도 전체 결과는 499그룹/811 MP4지만 중앙 2.2초·3초 미만 601개, 1140–1170초 A 2그룹과 음식 오검출이 지속된다. 이는 **W14 Person 후보의 제한된 실영상 결과**이며 공용 face clustering 또는 W13 Dance 호환·품질 승인으로 승격하지 않는다. 기존 554그룹 완료 카드와 사용자 편집 snapshot은 보존됐고 새 카드의 실제 Electron 홈·상세·원본 재생만 확인했다. Windows/패키징 및 W13 실제 adapter compatibility는 미검증, 공통 API 파일 소유권·merge 순서에 대한 W13의 상호 답변도 아직 없다. [실행·채점 근거](../10/01-w14-controlled-first-result-evaluation.md).

**후속 상호 확인 정정:** [W13의 10/1 소비자 검토](../10/01-w13-face-core-consumer-contract-review.md)가 W14의 공통 Python 파일 초기 소유, W13의 Dance adapter/main/참조 매핑/crop 소유 경계를 명시적으로 수용했다. 직전 문단의 “파일 소유권 답변 없음”은 그 검토 전 상태다. 공개 `FrameRef`/PTS·실패 이벤트·embedding 공간 지문·track ID 범위는 아직 제안 계약과 실제 API가 달라 고정 전이며, **W14 공통 API 고정 → W13 adapter 변경과 compatibility test → 병합** 순서는 제안으로 유지한다. W13의 실제 Dance 이식/회귀와 Windows·패키징, 두 브랜치 병합은 아직 실행하지 않았다. 새 5 fps 결과의 짧은 clip 601개 중 539개가 3초 미만 shot에 속한다는 W14 컷 재계산도 W13 Dance 컷 정책의 변경 근거로 사용하지 않는다. [재생·컷 검증](../10/01-w14-controlled-first-result-evaluation.md).

사용자는 W14의 **후속 얼굴 추론 횟수 제한을 해제**했다. 이는 W14 Person 평가 실행에 관한 결정이며 W13 Dance 모델/입력/adapter 변경, 공용 API 호환 승인, 새로운 embedding 모델의 다운로드나 혼합을 뜻하지 않는다. W14는 미사용 원본 창의 GT를 먼저 고정해 추가 진단한다. [후속 순서](../10/01-w14-controlled-first-result-evaluation.md).

**후속 진단 인계(10/1):** W14는 기존 YuNet/SFace 파일로 0.85와 0.82 detector config를 각각 **별도 SHA/격리 출력**에서 비교했다. 0.85는 개발 창의 확실한 얼굴 104개 중 1개, 0.82는 별도 미열람 창의 63개 중 2개를 놓쳐 둘 다 미채택이다. W14 Person의 현재 0.60 검출/0.55 전체 묶기, W13 Dance의 ROI/main/참조 mapping·crop 및 양쪽의 embedding cache/threshold는 바뀌지 않았다. 같은 사람의 분리 얼굴 cosine 일부(0.009–0.585)가 다른 사람의 범위(최대 0.443)와 겹쳐 전역 문턱 완화도 W13 소비 계약으로 제안하지 않는다. 이 수치는 같은 원본의 희소 라벨이며 공용 알고리즘 정확도/호환을 보장하지 않는다. 기존 W14 공통 파일 초기 소유·W13 Dance adapter/main/mapping/crop 소유, **W14 공개 DTO 고정 → W13 실제 compatibility fixture → 병합** 순서를 유지한다. 구조화 실패/PTS·FrameRef/embedding 공간 지문/track ID 범위와 Windows·plugin venv 실기 검증은 아직 남는다. [실행·GT·미검증](../10/01-w14-source-first-holdout-and-threshold-audit.md).

**ArcFace 격리 비교 인계(10/1):** W14는 사용자 승인 뒤 공식 ResNet100 ArcFace ONNX SHA-256 `f0a2e278b430372d308fef67c1aea308c2baf37f32e8908d9bfce035c26a3fb4`를 별도 평가 폴더에서만 사용했다. OpenCV DNN CPU 전처리/정렬 config SHA-256 `e43af94246ef297e484a05a6dcc8c1d79dea2abfa8ba05ebf7ceaede8ba42d74`의 **새 512차원 embedding 공간**이며 YuNet/SFace cache·centroid·threshold 0.55와 혼용하지 않는다. 150초/1,074 기존 관측의 개발/독립 비교에서 새 공간 기준 0.30은 기존과 같은 과분리 및 독립 I1 오합침 14쌍을 보여 gate 실패했다. ONNX Runtime 1.24.4의 첫 호출은 공식 모델 BN 형식 오류였고 OpenCV DNN만 시험됐으므로 W13 Dance backend 교체·호환 승인으로 간주하지 않는다. W14 공통 공개 API, W13 Dance adapter/main/mapping/crop, merge 순서는 변경 없음. 파일 소유권은 기존 상호 확인대로 W14 공통 초기 소유/W13 Dance 소비자 소유를 유지하며, 다음 호환 gate는 `model_sha256+config_sha256` 공간 분리와 동일 프레임 cannot-link, 기존 Dance fixture, 별도 Windows/패키징을 포함한다. [실제 수치·미검증](../10/01-w14-arcface-isolated-probe-result.md).

**별도 드라마 교차 점검 인계(10/1):** W14가 기존 로컬의 다른 영상 60초에서 원본 우선 익명 라벨 뒤 동일 YuNet 상자 278개를 SFace와 위 **고정 ArcFace 0.30**으로 비교했다. 드라마 희소 얼굴 45셀은 SFace의 다른 사람 오합침 380쌍·같은 사람 분리 120쌍에서 ArcFace 양쪽 0으로 개선됐지만, 앞선 방송 독립 창의 ArcFace 오합침 14쌍/과분리는 남는다. 서로 다른 영상에 대한 이 상반된 근거로 **W14 제품 default 또는 W13 Dance recognizer를 교체하지 않는다**. SFace 0.65로만 바꿔도 드라마 분리 190쌍·방송 독립 오합침 14쌍이라 공통 threshold 변경도 없다. 26클립 중 22개가 3초 미만인 드라마 컷 문제는 embedding 모델과 별개다. 비얼굴 바퀴·손 그룹과 흐린 대표도 남는다. 공용 DTO/API·소유권·merge 순서·W13 기존 main/ROI/mapping/crop에 실제 변경 없음. 다음 compatibility fixture는 두 영상의 **다른 사람/같은 사람 양방향 결과와 동시 출연·비얼굴**을 함께 포함해야 하며 ArcFace/SFace 공간별 모델·전처리 SHA·threshold/cache 분리를 유지한다. [원본 우선 입력·자원·희소 GT의 한계](../10/01-w14-second-video-source-first-and-fixed-arcface.md).

**대표 선명도 후보의 공통 파일 영향(10/1):** W14 격리 `clipper_face_core/OpenCvFaceBackend`가 출력하는 기존 선택 필드 `FaceDetection.sharpness`의 계산 범위만 bbox 전체→얼굴 안쪽 위쪽으로 바꿨다. DTO 필드/위치 인자 및 `quality`·YuNet/SFace weight·embedding은 그대로지만 새 backend ID/config SHA `bca4dc55a1ac77e4afdf34f5eeb7c31a9bb484d01022a80d5ce0d270e2cf4710`로 이전 결과와 구분한다. 같은 드라마 278관측 재추론에서 ID·상자·embedding·그룹·clip은 동일, 대표 2개 변경을 확인했다. W13이 기존 Dance adapter/main/mapping/crop을 소비할 때 `sharpness` 무시 경로와 선택 필드 허용을 fixture로 확인하고, W14 공개 config/API를 고정한 뒤 W13 이식→compatibility test→병합하는 기존 순서를 유지한다. **W13 Dance 실기 호환/Windows 패키징/전체 대표 품질은 아직 미검증**, 현재 설치 앱·기존 완료 카드에는 이 격리 후보가 적용되지 않았다. [TDD·실제 비교](../10/01-w14-second-video-source-first-and-fixed-arcface.md).

**10/2 얼굴 없는 구간 pose 기술 탐색의 계약 경계:** W14는 W13 Dance가 이미 보유한 로컬 `yolov8s-pose.pt`를 **격리 평가에서만** 사용했다. 원본 우선 7프레임/몸 위치 라벨과 106프레임 연속 표본에서 잘린 얼굴 몸 3/3, 음악 동시 5/5 두 프레임, 요리 출연자 14/14 몸 상자를 확인했지만 방송의 작은 배경 4명 중 3명은 pose box가 없었다. 요리 shot에는 얼굴 앵커가 전혀 없으므로 **몸 검출만으로 기존 Person ID에 연결할 수 없으며 사용자 결과가 아닌 내부 진단값**다. 37분 저장 얼굴 93개와 사후 중심점 대조에서는 상자 없음 12개, 2개 이상 1개여서 pose box를 FaceObservation 또는 PersonGroup ID로 직접 승격할 근거가 없다. **공용 얼굴 API/embedding 공간·threshold·W13 Dance main/ROI/mapping/crop·기존 사용자 결과는 수정하지 않았다.** 후속 선택적 body 관측은 W14 Person 소비 정책의 별도 입력/모호 상태로 설계해야 하고 기본 SDK 경로에 Ultralytics/PyTorch를 강제하지 않는다. Windows/CUDA/패키징, 독립 배경·연속 interval GT 및 W13 실제 adapter 회귀는 미확인이다. W14 공통 얼굴 파일 초기 소유, W13 Dance adapter 소유, **W14 공개 DTO 확정 → W13 fixture·실기 호환 → 병합** 순서를 유지한다. [잠금 입력·실제 검증·남은 gate](../10/02-w14-existing-pose-continuity-feasibility.md).

**10/2 원본 우선 연결 채점의 W13 경계:** 위 3/3은 검출 전용임을 후속 3×10초 원본 GT/기존 모델 60프레임으로 검증했다. 음악 95.1–97.6초 GT의 정지 좌표 오류 30지점은 사후 발견·무효 처리했으며, 유효 71지점에서 몸65·얼굴 인물 그룹 연결46, 흐린 배경 그룹0/5, 동시 전원 별도 그룹5/16화면이다. 얼굴 그룹 두 개가 **같은 shot의 한 body track**에 붙는 경우가 실제로 있었지만 이를 자동 합침하는 공통 API나 Dance main 정책으로 승격할 근거는 없다. W14 Person 선택 `BodyObservation/unknown/ambiguous` 설계 검토로만 보낸다. SFace 모델/config 공간과 YOLO 몸 track ID를 분리하며 공용 `FaceObservation`·Dance adapter/main/ROI/mapping/crop은 변경하지 않았다. W13 측 새 호환 검증에는 같은 몸 track에 얼굴 그룹이 분리되는 fixture, 흐린 배경 누락, 동시 다섯 명의 전원 group coverage와 다른 사람 cannot-link **양쪽**을 포함한다. 기존 소유권과 `W14 공개 DTO 확정 → W13 compatibility fixture/실기 → 병합` 순서는 유지, 실제 W13 호환·Windows/패키징·조직의 Ultralytics 계약 범위는 여전히 미검증이다. [라벨 오류를 포함한 실제 채점](../10/02-w14-independent-continuity-and-fusion-audit.md), [W13 YOLO 도입/사용권 이력](../10/01-w13-yolo-license-provenance.md).

**10/2 사용자 지적에 따른 문구 정정:** Dance와 Person은 하나의 앱·SaaS 내부 기능이다. 기존에 쓰는 동일 YOLO 모델을 Person에서 호출한다고 **플러그인별 새 허가나 별도 계약이 생긴다는 근거는 없다**. W13의 모델 도입/서비스 전체 사용 조건 기록은 남기되 이를 W14의 제품 적용 승인 gate로 중복 제시하지 않는다. 또한 **얼굴 연결 없이 검출된 몸 상자만의 `확인 필요/unknown` 인물 카드·클립을 만들자는 제안을 철회**한다. 몸 상자만으로 동일인을 판정할 수 없다. W14가 body를 다시 검토한다면 이미 얼굴로 확인한 사람의 **같은 편집 shot 안**에서 모호함 없는 몸 track을 따라 얼굴이 잠시 없는 등장 구간을 연장하는 내부 경로로 한정한다. 얼굴 앵커가 없거나 모호하면 Person 결과에 사용하지 않으며, 이번 드라마 배경 통행인 4개 몸 상자는 인물 그룹으로 연결되지 않았다.

**10/2 후속 모델 결정 인계:** 사용자가 이번 W14 격리 시험의 **YOLOv8 pose는 앞으로 사용할 수 없다**고 명시했다. W13 Dance는 교체 작업 중이나 대체 모델은 아직 미정이다. 위 YOLO 몸 관측·연결 수치는 과거 진단일 뿐 W14 Person 통합 후보나 W13 교체 모델의 성능 근거가 아니다. W14는 YOLO의 추가 추론/제품 연동을 중단하고, W13의 미래 모델을 자동으로 가져오지 않는다. 선택적 몸 관측/face↔body 소비 계약은 **사용 가능한 모델·독립 GT·동시 출연 오합침 검증**이 정해지면 다시 논의한다. 얼굴 공통 `FaceObservation`/embedding 공간·cache와 Dance adapter/main/ROI/mapping/crop의 경계는 그대로 유지한다. 파일 소유는 W14 공통 얼굴 경로 초기 작업, W13 기존 Dance adapter 소비자이며, `W14 공개 DTO 고정 → W13 compatibility fixture/실기 → 병합` 순서를 유지한다. 이번 정정은 문서만 수정했고 W13 실제 호환·Windows/패키징·새 모델의 정확도는 검증하지 않았다.

**10/2 W14 독립 후보 조사:** [인물용 몸 검출 후보·예외 설계](../10/02-w14-person-body-model-candidates-and-continuity-rules.md)는 Dance의 메인 댄서용 pose 모델 선택과 별개다. D-FINE/RF-DETR/RTMDet는 W14 검출기 **제안**이며 W13 adapter의 모델·가중치·공통 얼굴 API 계약을 바꾸지 않는다. 얼굴 앵커가 있는 같은 shot의 등장 연장/모호 상태는 Person 소비 규칙으로 두고, 추후 공용 파일 변경이 필요하면 기존 W14 DTO→W13 fixture→병합 순서를 따른다. 다운로드·실기·제품 적용 0건.
