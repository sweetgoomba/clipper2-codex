# W14 인물 하이라이트 MVP 설계

> **2026-10-26 문서 이관 안내:** 인물 하이라이트의 초기 제품 계약이다. face-only 분석·등장 구간 생성 가정은 [10/19 연속 등장·얼굴/몸 근거 설계](../../../../../design/2026-10-19-person-highlight-continuity-design.md)로 갱신됐다. [후속 구현 계획](../../../../../implementation/2026-10-20-person-highlight-implementation-plan.md) 및 [10/23 기능·공통 모델 체크포인트](23-person-highlight-checkpoint-and-shared-face-model.md)를 함께 읽으며, 아래 실행 전 상태와 gate는 10/1 당시 기록으로 보존한다.

2026-10-01 KST · **서면 설계 검토본**. 사용자가 확인한 결과 목업과 “이어 붙인 MP4 없음” 결정을 반영했다. 제품 코드·새 ML 추론·모델 다운로드·과금 호출은 이 문서 작성으로 시작되지 않는다. [W14 조사와 근거](../09/30-w14-person-highlight-design-proposal.md), [W13 공통 계약 인계](../09/30-w14-to-w13-face-contract-handoff.md), [평가 준비안](../09/30-w14-evaluation-manifest.yaml)을 따른다.

## 1. 목적과 선택 범위

영상만 입력하면 같은 사람이 등장한 source 구간을 익명 그룹으로 찾아보고, 틀린 결과를 고친 뒤 클립을 받는다. 첫 사용 상황은 소수 인물이 반복 등장하는 인터뷰·토크다. 드라마·예능의 빠른 cut/분장과 행사·거리·브이로그의 작고 짧은 얼굴은 비교 평가 대상으로 두고 같은 품질을 보장하지 않는다.

**확인된 방향:** 사전 참조 이미지 없이 Person 1/2…로 묶는다. 배경·잠깐 지나간 사람을 포함해 검출된 모든 그룹을 기본 목록에 표시한다. 불확실한 관측도 고유 ID의 `확인 필요` 결과로 남긴다. 인물·등장 구간 누락과 서로 다른 사람의 오합침을 동등한 1차 기준으로 각각 평가한다. 한쪽 개선으로 다른 쪽 악화를 상쇄하지 않는다.

**첫 MVP의 출력:** 인물 카드의 다운로드 아이콘은 그 인물의 제외되지 않은 클립 전체 ZIP, 클립 행의 아이콘은 해당 edited source 구간의 MP4, 화면 상단은 모든 클립 ZIP이다. 임의 다중 선택 체크박스와 선택 내보내기 하단 영역은 없다. 사용자가 **이어 붙인 단일 MP4는 만들지 않는다**고 결정했다. 쇼츠 제작·템플릿·BGM·자동 타이틀·crop, 실명 식별, 얼굴=화자 판정, body ReID/화자 fusion, 선택적 참조 이미지 검색은 이 MVP 범위가 아니다. 공통 얼굴 모듈은 특정 두 플러그인 전용으로 제한하지 않는다.

## 2. 사용자 흐름과 UI 상태

현행 앱의 YouTube URL/로컬 파일 선택 → 영상 확인 → 홈 작업 큐 등록을 사용한다. 분석이 끝나기 전 결과 페이지를 만들지 않는다. 대기·실행 상태는 홈에 남고 완료 카드의 `결과 보기`로 들어간다. 결과 페이지는 기존 안무·대사 상세의 열 카드 패턴을 따라 왼쪽 인물, 중앙 그 인물의 클립, 오른쪽 원본 preview와 수정 영역으로 구성한다. 앱 사이드바나 단계 탭을 결과 목업 안에 다시 그리지 않는다.

- 인물 카드는 대표 얼굴, 익명 이름, 등장 수/시간과 확인 필요 여부를 보여준다. 자동 배경 숨김·soft filter·시간/반복/크기 표시 제한은 없다. 대표 얼굴이 없으면 원본 frame placeholder와 실패 이유를 보여준다.
- 인물 선택 시 그 사람의 등장 interval/장면 목록을 source 시각으로 표시한다. 한 Scene에 여러 그룹이 있으면 각 그룹 목록에 그 Scene이 나타난다. 클립 선택은 오른쪽 원본을 그 구간으로 seek한다.
- 플레이어 아래는 보기·편집 공통 타임라인 하나다. 기본 상태는 선택 구간만 재생하고 구간 안에서 seek할 수 있으며 양끝 핸들은 움직일 수 없다. `구간 편집` 중에만 같은 핸들이 활성화된다. 경계 시각은 읽기 전용, 저장/취소/원래 경계를 제공하고 숫자 직접 입력은 없다.
- 이름·대표 이미지 변경, 등장 구간 재배정/새 그룹, 그룹 병합, 제외/복원, track이 한 occurrence 안에서 바뀐 경우의 구간 분할을 수정 동작으로 둔다. 자동 결과는 보존하고 사용자 변경을 별도 revision으로 저장한다. 서로 다른 사람이 동시 출연한 그룹의 수동 병합은 충돌을 경고한다.
- 인물 행의 ZIP 아이콘은 현행 안무 결과의 인물 행, 클립 행의 MP4 아이콘은 현행 대사 결과의 클립 행을 따른다. 각 아이콘은 행 선택 버튼의 형제여서 다운로드 클릭이 인물/클립 선택을 바꾸지 않는다. hover·키보드 focus·터치에서 접근 가능하다. 제외된 클립은 직접 다운로드 대상에서 빠지고 복원 뒤 다시 들어온다.

화면의 다운로드 아이콘은 요청 시작점이다. 캐시된 파일이면 다운로드를 제공하고, 새 인코딩이 필요하면 export job의 대기·실행·완료·실패 상태를 기존 작업 큐 흐름에 연결한다. 유료 작업 정책이 정해지면 비용/권한 확인 뒤에만 job을 제출한다. 아이콘 클릭만으로 조용히 과금하지 않는다. 목업은 실제 파일·대기 시간을 구현한 증거가 아니다.

## 3. 분석 경로와 보장 한계

원본 source/stream hash와 PTS를 고정하고 shot을 나눈다. 선택한 분석 cadence로 각 frame의 **모든 유효 얼굴**을 검출·정렬·품질 기록·embedding한다. shot 안에서 frame당 1:1 assignment로 여러 track을 만들고, shot을 넘는 재등장은 같은 embedding 공간의 영상 단위 constrained cluster로 연결한다. 동시 출연한 서로 다른 두 얼굴의 track은 자동 병합할 수 없는 `cannot-link` 관계다. 그룹에서 appearance interval과 Scene↔PersonGroup 다대다 관계를 파생한다. ROI 최고 점수 얼굴 하나와 main 한 명용 현행 Dance `TrackAssigner`를 다중 인물 tracker로 재사용하지 않는다.

같은 shot에서 이미 얼굴로 확인된 track의 짧은 무얼굴 gap만 유지 후보로 삼는다. 1초 TTL과 5 fps는 **평가 전 후보값**이며 성공 보장이 아니다. shot cut에서 motion track은 종료하고 embedding cluster로만 재등장을 연결한다. 얼굴이 한 번도 검출되지 않은 사람, 샘플 사이에만 지나간 사람, 완전히 가려져 몸만 보이는 사람은 face-only MVP의 자동 발견 보장 밖이다. 검출 실패는 평가상 누락으로 기록한다. 반면 검출된 얼굴의 정렬/embedding/군집 실패는 버리지 않고 별도의 확인 필요 카드와 실패 이유로 보존한다. 단순 저품질·짧은 등장만으로 자동 숨기지 않는다.

대표 후보 순위는 선명도, 가림/landmark 신뢰도, 얼굴 크기, 그룹 centroid 근접도를 함께 사용하고 근거를 보존한다. 사용자의 대표 이미지 override가 자동 재순위로 덮이지 않도록 한다. 재분석으로 observation ID가 바뀌면 override를 임의 새 얼굴에 붙이지 않고 `stale` 검토 대상으로 둔다.

## 4. 여러 플러그인이 쓰는 얼굴 API

Python workspace에 독립 `clipper_face_core` 패키지를 두되 공개 입출력은 Dance segment, PersonGroup, UI/job 타입에 종속하지 않는다. 초기 공개 기능은 `detect_all(frame, frame_ref)`, `align_and_embed(frame, observation)`, `cosine_distance(a,b)`, `rank_representatives(observations, centroid)`와 versioned DTO다. 공통 패키지는 모든 얼굴 관측·정렬·embedding/거리·품질 근거와 대표 후보를 제공한다. shot tracking과 clustering의 계산 helper는 도메인 중립일 때만 공통으로 올리고, 임계값·main/member mapping·scene·카드·job·과금 정책은 소비자가 소유한다.

| 계약 | v1 의미 |
| --- | --- |
| `FrameRef` | `sourceSha256`, stream index, 원본 PTS 정수와 rational time base, 파생 `timeMs`, frame width/height/rotation. bbox 기준은 회전 적용 display frame. |
| `FaceObservation` | analysis revision 안에서 유일한 observation ID/schema version, shot ID, display frame의 pixel `xyxy`, 같은 frame 크기에서 파생한 normalized `xyxy`, 5 landmarks, 검출 score, 품질 항목, embedding ref 또는 명시적 실패 상태. |
| `FaceTrack` | `{shotId, trackId}` 유일 키, 관측 ID 목록, source `[startMs,endMs)`, gap/validity. shot을 넘겨 track ID를 재사용하지 않음. |
| `Embedding` | float32 L2 normalized vector의 ref, dimension, recognizer weight SHA·정렬/전처리·정규화/거리 규칙을 포함한 `embeddingSpaceId`, backend/library version. 민감 벡터는 일반 로그에 기록하지 않음. |
| `ModelRef/ConfigRef` | detector/recognizer 파일별 SHA-256, 코드/adapter/config hash, device/backend. 관측 cache 키에 source+모델+설정+schema fingerprint 포함. |
| 실패 상태 | `decode_failed`, `model_unavailable`, `no_detection`, `below_detector_threshold`, `invalid_geometry`, `align_failed`, `embedding_failed`, `uncertain_group`. 미검출·결과 숨김·사용자 제외는 서로 다른 상태. |

`timeMs`는 source PTS에서 변환한다. frameIndex/fps로 원본 seek 시각을 대신하지 않는다. 서로 다른 `embeddingSpaceId`의 vector·centroid·cache·distance threshold를 섞지 않는다. 같은 weight라도 정렬/전처리/정규화가 바뀌면 호환성 평가 전에는 다른 공간이다. 모델/backend 교체는 명시적 adapter/config/schema 변경과 두 초기 소비자의 compatibility test 뒤에만 한다.

패키지 import는 모델 다운로드·초기화·외부 호출을 하지 않는다. 플러그인별 선택 의존성, venv, local 모델 준비와 SHA 검증을 유지하며 기본 SDK 시작에 ML을 강제하지 않는다. 9/30 공식 자료 조사상 OpenCV YuNet/SFace의 현행 CPU 경로가 첫 비교 기준이다. Mac/Windows 실기, weight 권리, CUDA custom build는 별도 검증 전 지원/상용 적합성을 선언하지 않는다. 새 모델 다운로드·외부 유료 API·Build5는 별도 범위다.

## 5. Person artifact와 수정 저장

`person_highlight_analysis_v1`은 source hash/stream/rotation·model/config/adapter hash·cadence·failure summary를 가진 불변 analysis와, observation/track/PersonGroup/Scene/Appearance를 가진다. `ScenePerson`은 `{sceneId, groupId, appearanceIds, trackIds, evidence}`의 다대다 연결이다. Appearance는 source `[startMs,endMs)`와 `face_visible`/`uncertain` 근거를 가진 수정·다운로드 최소 단위다. `unknown` 하나를 모든 미확정 사람의 공통 실체 ID로 쓰지 않는다. 자동 label 번호는 영속 ID가 아니라 첫 등장순 표시이며 그룹은 안정적 UUID를 가진다.

`ReviewDraft`는 analysis ID와 단조 증가 `editRevision`, rename/merge/reassign/split/exclude/restore/representativeOverride 및 edited bounds를 불변 analysis 위에 기록한다. 저장 요청은 expected revision을 받아 충돌이면 409와 최신 revision을 돌려준다. 한 수정 동작은 원자적으로 저장하고 crash 뒤 다시 열어도 보존한다. 현행 직접 `writeFile` 저장이 이 보장을 자동으로 제공한다고 가정하지 않는다. 분석을 다시 돌려 ID가 달라진 변경은 자동 무음 이식하지 않고 stale 검토로 노출한다.

Nest/Angular에서 현행 단일 `clip.personId`, dance/dialog 전용 category·shortform origin, 기존 전체/한 인물 ZIP API에 Person 결과를 억지로 끼워 넣지 않는다. 별도 analysis read, review draft write, export job 계약을 만들며 실제 route/DTO 이름은 구현 계획에서 repo 상태와 함께 확정한다. 필수 조회 값은 그룹/Scene/Appearance의 관계, source preview ticket, revision, 실패/불확실 상태다.

## 6. 다운로드와 작업 계약

클립 아이콘은 Appearance 하나의 edited source bounds를 MP4로 요청한다. 인물 아이콘은 해당 그룹의 제외되지 않은 Appearance 전체를 ZIP으로, 상단 버튼은 모든 그룹의 대상 Appearance를 ZIP으로 요청한다. source 원본 소리·비율을 유지하고 BGM/crop/타이틀은 적용하지 않는다. 중복 key는 `(sourceHash, streamId, editedStartMs, editedEndMs, outputSettingsHash)`다. 완전히 같은 편집 구간은 media blob과 전체 ZIP entry를 한 번만 만들되 manifest에 모든 Scene/PersonGroup 출처를 남긴다. 같은 scene ID라도 경계가 다르면 각각 남기고, 일부만 겹친 다른 구간은 자동 합치지 않는다. 인물 ZIP은 해당 그룹 항목만 포함한다. 전체 ZIP은 유일 media 파일과 그룹↔파일 매핑 manifest로 다대다 관계를 보존한다. **구간들을 이어 붙이는 MP4 경로는 없다.**

`ExportJob`은 analysis/edit revision, source/출력 hash, 요청 대상, 예상 파일 수·총 길이, 권한/quote 또는 무료 정책 결과, idempotency key를 고정한다. queued/running/completed/failed/canceled를 구분하고 `.part` 파일과 worker/ffmpeg를 취소 시 정리한다. 같은 입력·설정의 완료 blob만 재개에 재사용한다. 새 edit revision은 plan을 다시 검증하지만 동일 source bytes·경계·출력 설정의 완료 blob은 안전하게 재사용할 수 있다. keyframe copy가 선택 경계를 어기면 재인코딩하고 preview/source/export PTS를 비교한다. 사용자가 아이콘을 누른 즉시 파일이 없으면 완료 후 다운로드 가능 상태를 알린다.

과금 operation은 기존 dance key를 재사용하거나 무료라고 추정하지 않는다. 정책이 유료라면 신규 Web API entitlement/quote/ledger/취소·환불 계약을 따로 확정하고 사용자 확인 전에 분석/export를 유료 실행하지 않는다. 원본은 draft/export가 참조하는 동안 hash를 검사하며 보존 기간은 제품 정책으로 확정해야 한다. 이 두 정책은 출시 gate이며 본 설계가 임의 가격·기한을 만들지 않는다.

## 7. 검증과 실행 상한

실제 ML 전에 원본 절대 경로/SHA·source 구간, 익명 GT 사람/등장/배경/동시 출연, 모델 파일 SHA와 embedding space, 실행 SHA·OS/device, 횟수·시간·메모리·출력 위치를 manifest에 채운다. 첫 제안은 인터뷰, 재등장/동시 출연, 배경/단역 사례 3개×각 120초 이하(총 6분 이하)다. 다중 얼굴 평가 adapter가 준비된 뒤 face-only 관측 추론 각 1회, 합계 최대 3회다. 같은 관측/embedding에서 grouping 기준 **하나만** 바꿔 A/B 최대 6개 결과를 비교한다. soft-filter 대조는 하지 않는다. 새 모델·유료 API·Build5는 이 실행 범위에 없다.

사람/appearance interval recall(배경·단역 별도)과 false merge를 동등한 1차 축으로 각각 보고한다. pairwise 및 B-cubed precision/recall/F1, false split, 동시 출연 cannot-link 위반, uncertain coverage를 분리한다. 대표 이미지의 선명도·가림·크기/동일 인물 적합성, 사용자의 탐색 시간·수정 횟수, exact 중복 제거/다른 경계 보존/원본 소리/수정 영속성은 별도 평가다. 보수적 미합침으로 생기는 false split도 숨기지 않는다. GT가 없으므로 숫자 목표와 실제 성능은 아직 주장하지 않는다.

최소 계약 검증은 두 얼굴 frame→서로 다른 관측/track, 같은 Scene의 두 group, shot cut/재등장, 배경 단일 관측 카드, unknown 보존, edit revision 409/재시작 보존, 사용자 대표 override, 동일 interval dedup·다른 경계 보존·겹침 미합침, 다운로드 아이콘 클릭이 행 선택을 바꾸지 않는지, 키보드/터치 접근, 기존 Dance/Dialog 회귀다. 오류 상태에서 원본·수정·완료된 파일을 잃지 않는지도 확인한다.

## 8. 구현 분할과 선행 gate

1. **W14 공통 경로:** Python 독립 face core DTO/API와 fixture, plugin 선택 의존성 경계. W13이 공개 타입과 파일 소유를 검토한다.
2. **W14 Person 분석:** 다중 얼굴 관측→shot-local track→cannot-link cluster→Appearance/Scene 다대다 artifact와 평가 adapter. GT/모델/자원 manifest 없이 실제 추론을 하지 않는다.
3. **W14 결과·수정·출력:** Nest analysis/review/export job·Angular 결과 화면과 기존 입력/홈 큐 연결. Electron plugin 등록·공통 소스 fingerprint와 모델 준비는 W13과 단일 파일 소유자를 합의한 뒤 수정한다. Web API는 신규 과금/권한 정책이 실제 선택될 때만 범위에 넣는다.
4. **W13 Dance 소비:** W13이 기존 ROI/main/mapping/crop adapter를 소유한다. W14는 이를 임의 변경하지 않는다. core 준비→W13 호환 fixture→Dance 소비→Person 연결 순으로 merge하며 공통 파일 병렬 수정을 피한다.

제품 코드를 고칠 때에만 대상 각 repo의 최신 `origin/dev`를 fetch해 새 브랜치·격리 worktree를 만들고 형제 repo와 다른 세션의 미커밋 변경을 보존한다. 9/29 조사 SHA를 최신 원격으로 간주하지 않는다. 이 프로젝트 루트는 Git 저장소가 아니므로 이 설계 문서를 여기서 commit할 수 없다.

**서면 검토 뒤에도 남는 실행/출시 gate:** W13의 공통 API·파일 소유 상호 확인, 정확한 GT 원본/라벨과 모델 실제 SHA·실행 환경, 과금/권한과 원본 보존 정책, Mac/Windows·weight 권리·자원 상한 확인. 이들이 없으면 해당 실행·배포를 진행하지 않는다. 설계 검토 승인은 ML 성능이나 제품 출시 승인으로 확대하지 않는다.
