# W14 신규 인물 하이라이트 — 목적·MVP·계약·검증 제안

2026-09-30 KST. **Superpowers architectural brainstorming의 검토용 제안**이다. 사용자 검토와 선택을 거친 승인 스펙·구현 계획이 아니다. 제품 코드, ML 추론, 모델 다운로드, 유료 API, Build5, fetch, commit/push/merge/deploy는 수행하지 않았다. 9/29 [종합 인계](29-pipeline-design-handoff.md) §2의 SHA는 fetch로 보증된 최신 원격이 아니다.

## 1. 사용 목적과 성공 기준

사용자가 밝힌 목표는 **참조 이미지를 미리 고르지 않고, 한 영상에서 같은 사람이 등장한 구간을 묶어 찾아보고 수정한 뒤 내보내는 것**이다. 배경과 잠깐 지나간 사람까지 *검출된 모든 인물 그룹*을 기본 목록에 표시한다는 결정은 확정이다. 실명 식별이나 얼굴=화자 판정은 기본 기능이 아니다.

제안하는 1차 이용 상황은 2~3명이 반복 등장하는 인터뷰·토크의 편집 재료 수집이다. **10/1 사용자 확인: 주요·배경·단역 인물 및 등장 구간의 누락 최소화와 서로 다른 인물의 오합침 최소화는 둘 다 중요하다.** 두 지표를 동등한 1차 성공 기준으로 따로 보고, 한쪽의 개선으로 다른 쪽의 악화를 상쇄해 단일 점수로 합격시키지 않는다. 한 사람의 과도한 분리, 사용자의 탐색·수정 시간, 요청한 경계·소리·선택 파일의 정확성은 별도로 평가한다. 불확실한 검출은 결과에서 빼거나 무리하게 합치지 않고 확인 필요 상태로 보존해 두 기준 사이의 선택을 사용자에게 드러낸다. 구체적인 허용 수치는 GT와 평가 범위가 확정된 뒤 합의하며, 그 전에는 어느 지표가 성공했다고 선언하지 않는다. “흥미로운 쇼츠 자동 완성”은 목표로 약속하지 않는다.

| 첫 대상 | 얻는 가치 | 품질 위험 / 출시 판단 |
| --- | --- | --- |
| 인터뷰·토크, 소수 반복 인물 | 재등장 검색과 카드 수정이 비교적 쉬움 | 화면 밖 발화, 진행자/게스트 동시 출연, 짧은 배경 등장도 평가 |
| 드라마·예능 | cut마다 재등장하는 인물 찾기 | 분장·각도·가림·빠른 cut, 높은 false split/merge; 별도 비교군 |
| 행사·거리·브이로그 | 많은 사람 중 원하는 등장 장면 탐색 | 작고 짧은 얼굴, 움직이는 카메라, 군중·동시 출연; 초기 보장 확대 전에 평가 |

## 2. 접근 3개와 첫 버전 권고

| 접근 | 장점 | 비용·오류 | W14 제안 |
| --- | --- | --- | --- |
| 참조 없는 face-only 익명 grouping | 원본만 선택하면 Person 1/2…과 확인 필요 카드 생성 | 얼굴 없는 구간, 측·후면, 작은 얼굴에 취약; 수동 수정 필요 | **MVP 기준**. 인물명은 영상 내부 익명 label이며 첫 등장순 표기 |
| 결과 뒤 선택적 참조 이미지 검색 | 이미 알고 있는 대상의 카드/구간 검색이 쉬움 | 이미지 준비, open-set 거절·다른 영상 참조 권리·오인식 평가 필요 | 별도 후속 옵션. 기본 분석의 전제나 실명 DB 검색이 아님 |
| face+body ReID/화자 fusion | 얼굴이 사라진 일부 구간의 coverage 가능 | 새 모델/weights·동기화·얼굴과 발화자 불일치·배경 오합침, 추가 비용 | 첫 버전 제외. 얼굴=화자 자동 등식 금지 |

첫 품질 샘플은 로컬 원본 3개×각 120초 이하(합계 6분 이하)다. 제품 입력 상한(길이·해상도·동시 인물 수)은 자원 실측 후 별도 결정한다. **모델 검출/샘플링 실패는 결과 숨김과 다르다.** 낮은 품질이나 단 한 번 등장했다는 이유로 이미 검출된 관측을 자동 숨기거나 제외하지 않는다. 확인 필요 카드는 자동 그룹 판정 실패 관측의 임시 보관 장소다. 소프트 필터, 최소 시간·반복·크기 표시 제한은 후속이다.

## 3. MVP 사용자 흐름과 보장 범위

1. 현행 앱의 YouTube URL/로컬 파일 입력과 영상 확인 UI를 사용한다. 확인 후 분석 작업을 홈 작업 큐에 추가하고 `/projects`로 이동한다. 대기·실행은 홈에서 계속 진행되며 완료 카드의 `결과 보기`로 상세 화면에 들어간다. 완료 후 대표 얼굴 카드, 익명 label, source 등장 시간/장면 수, 확인 필요 표식을 **전부** 첫 등장순으로 보여준다. 얼굴 crop을 카드에 쓸 수 없으면 원본 frame placeholder와 실패 이유를 보여준다.
2. 카드를 열면 해당 사람의 등장 interval 및 장면 목록을 원본 source 시각으로 표시하고 원본 seek preview로 검토한다. 한 scene/shot에 여러 그룹이 함께 속할 수 있다. 목록은 생성된 MP4를 요구하지 않는다.
3. 관측/등장 구간을 다른 그룹 또는 새 그룹으로 재배정하고, 그룹을 병합하며, 이름·대표 이미지 변경, 명시적 제외·복원을 제공한다. 단일 occurrence에서 tracking이 바뀌면 source 경계에서 둘로 나누고 각 절반을 재배정하는 최소 보정안을 포함한다. 모든 변경은 자동 결과 위의 edit overlay로 남기고 원판을 보존한다.
4. 인물 행의 다운로드 아이콘은 그 인물의 제외되지 않은 모든 클립을 ZIP으로, 클립 행의 아이콘은 해당 구간 하나를 MP4로 받는 직접 행동으로 제안한다. 전체 헤더의 모든 클립 다운로드도 별도로 둔다. 실제 export job에서 예상 길이·중복·소리·과금 여부를 언제 확인할지는 계약으로 정해야 한다. 분석 중 모든 clip을 미리 생성하지 않는 경로를 우선 제안한다.
5. 임의의 여러 클립을 고르는 체크박스는 결과 목업에서 제거했다. 사용자는 **선택 구간을 이어 붙인 MP4를 만들지 않는다**고 확인했다. 임의 다중 선택도 첫 MVP UI에는 없다. 템플릿/BGM/자동 타이틀/crop은 첫 버전 범위 밖이다.

10/1 UI 검토 방향: 결과는 현행 안무·대사 상세 화면의 열 카드 패턴을 따라 **왼쪽 인물 목록, 중앙 해당 인물 클립, 오른쪽 원본 미리보기·장면 수정**의 작업 영역으로 구성한다. 진입/큐/완료/결과를 한 화면의 단계 탭으로 만들지 않는다. 플레이어 바로 아래에는 보기/편집에 **하나의 동일한 구간 타임라인**을 사용한다. 기본 결과에서 선택 구간과 경계 위치를 보면서 그 구간만 재생하거나 그 안에서 재생 위치를 옮길 수 있고, 시작·끝 핸들은 조절할 수 없다. `구간 편집`을 누른 동안만 같은 타임라인의 시작·끝 핸들이 활성화되며 읽기 전용 시각·길이와 저장·취소·원래 경계 동작을 제공한다. 별도의 이동 막대는 두지 않는다. 숫자 직접 입력칸은 인물 결과 목업에서 제외한다. 현행 `clip-trimmer`의 핸들 조작을 참고하지만 숫자 입력도 있는 컴포넌트를 그대로 복사하는 결정은 아니다. 최소 길이·줌 폭·스냅·키보드 조작은 구현 스펙 전 검토가 필요하다. 이는 검토 중인 UI 방향이며 구현 승인이나 UX 검증 결과가 아니다.

추가 UI 결정: 안무 결과의 인물 행과 대사 결과의 클립 행에서 쓰는 **행 버튼과 형제인 hover 다운로드 아이콘** 패턴을 따른다. 인물 행은 그 인물 클립 전체 ZIP, 클립 행은 해당 클립 MP4다. 클립 목록 체크박스와 선택 내보내기 하단 영역은 목업에서 제거한다. 키보드 포커스·터치에서도 다운로드 버튼을 볼 수 있어야 한다. 기존 안무 클립 행 자체에는 현재 다운로드 아이콘이 없으므로 인물 행과 대사 클립 행을 각각 참고했다. 이후 사용자는 이 목업을 확인하고 이어 붙이는 기능은 없다고 명시했다. 임의 다중 선택은 첫 MVP UI에서 제외한다.

얼굴이 없는 동안은 **같은 shot의 이미 얼굴로 확인된 track**을 짧게 유지하는 후보만 둔다(초안 TTL 최대 1초, 불확실 표식; GT로 조정). shot cut에서는 motion track을 종료한다. 재등장은 같은 embedding 공간의 appearance cluster로 연결하되 확신이 없으면 새 확인 필요 그룹을 보존한다. 얼굴이 한 번도 검출되지 않은 사람, 프레임 샘플 사이에만 지나간 사람, 완전히 가려진 몸만 보이는 사람은 face-only MVP의 발견 보장 밖이며 평가에서 누락으로 기록한다. 한 화면의 서로 다른 두 얼굴은 동일 track ID를 공유할 수 없고, 동시에 존재하는 track끼리 자동 동일 PersonGroup으로 합치지 않는 cannot-link 제약을 둔다. 단역도 표시하지만 정확한 실명·발화자·완전한 전신 추적은 보장하지 않는다.

## 4. 다중 인물 분석과 artifact v1 제안

경로: **source/shot 인덱스 → 일정 간격 frame의 모든 유효 얼굴 검출 → shot-local 다중 track(한 frame에서 1:1 assignment) → 얼굴 정렬·품질·embedding → 영상 단위 constrained cluster → group별 appearance interval → scene 다대다 관계**. 분석 cadence는 표시 필터와 별개이며 P3의 짧은 등장 누락률을 기준으로 고정한다. 초기 후보 5fps는 실행·정확도 검증 전 값이다. 현재 안무의 ROI 최고 점수 얼굴 반환 함수와 `TrackAssigner.assign(t, bbox)`는 각각 하나의 ROI·하나의 main 입력용이므로 다중 얼굴 detector/tracker 구현으로 간주하지 않는다.

`person_highlight_analysis_v1` sidecar 후보:

| 엔터티 | 필수 필드 / 의미 |
| --- | --- |
| `Analysis` | schemaVersion, analysisId, source SHA-256·stream ID·duration·rotation, model/config hash, analyzer version, sampling cadence, createdAt, failure summary |
| `FaceObservation` | analysis 범위에서 유일한 observationId, frame source PTS/timebase, shotId, pixel `xyxy` bbox·5 landmarks·검출 score, embeddingRef 또는 실패 코드, 품질 근거·후보 frameRef |
| `FaceTrack` | shot 범위 trackId, observationIds, `[startMs,endMs)`·연결 상태·대표 embeddingRef. shot을 넘는 track ID 재사용 금지 |
| `PersonGroup` | 안정적 UUID, 자동 label, trackIds, representativeObservationId, 확인 필요 이유, cluster evidence. 번호/cluster label은 영속 ID가 아님 |
| `Scene` / `ScenePerson` | sceneId·source `[startMs,endMs)`, `{sceneId, groupId, appearanceIds, trackIds, evidence}`. 동일 scene의 다중 group 허용 |
| `Appearance` | appearanceId, groupId, sceneId, source `[startMs,endMs)`, source face evidence, `uncertain`/`face_visible` 등 상태. 선택·재배정·경계 편집의 최소 단위 |
| `ReviewDraft` | analysisId, 단조 증가 editRevision, rename/merge/reassign/split/exclude/restore/representativeOverride, edit transaction·이전 값·stale 여부 |

검출 score가 임계 미달이면 `not_detected` 또는 `below_detector_threshold`로 집계한다. bbox가 검출됐지만 정렬/임베딩/군집에 실패한 것은 **관측 및 확인 필요 임시 그룹으로 보존**한다. `unknown`은 하나의 공유 실체 ID가 아니라 각 관측/track의 미확정 상태다. 단일 얼굴이 여러 PersonGroup에 동시에 자동 배정되지 않는다. UI에서 사용자가 제외한 것은 edit overlay의 `excluded`이며 모델 미검출과 혼동하지 않는다.

대표 이미지는 얼굴 crop 자체의 선명도, 가림/landmark 신뢰도, 원본에서의 얼굴 크기, 그룹 centroid 거리의 다기준 순위로 고른다. 전부 기록해 근거를 설명하며 저품질 후보도 카드 노출 자체를 막지 않는다. 사용자 선택 `representativeOverride`는 자동 재순위와 분리해 보존한다. 재분석으로 observation이 달라지면 이전 asset와 선택을 그대로 임의 새 관측에 붙이지 않고 `stale` 검토 상태로 둔다.

## 5. 앱 계약과 export 제안

현행 Nest `ProjectClipItem.personId`는 하나이고 `ProjectDetail.category`는 person을 모르며, 숏폼 origin은 dance/dialog만 허용한다. `/projects/:projectId/zip`은 전체/`personId`만 받는다. 새 분석 draft를 현행 `ProjectSnapshot.status='completed'`에 억지로 넣지 않는다. 신규 읽기 계약은 `GET analysis/{id}`의 group/scene/appearance 및 원본 ticket, 편집 계약은 `PATCH review-draft/{id}`의 expected editRevision과 **한 번의 원자 저장**, 출력 계약은 `POST exports`의 selected appearance + edited source bounds + output mode를 권한다. 실제 URL·DTO 이름은 선택 스펙에서 확정한다. 사용자 수정의 재시작 보존에는 revision CAS와 crash-safe 저장이 필요하다. 현재 `JsonProjectRepository.upsert()`의 직접 writeFile만으로는 이를 보장할 수 없다.

`ExportSelection`은 `appearanceId`, `[editedStartMs,editedEndMs)` (source 기준), request order를 갖는다. 클립 행은 항목 하나, 인물 행은 해당 그룹의 제외되지 않은 항목 전체, 전체 헤더는 전체 그룹의 대상 항목을 서버 요청에 명시적으로 전달한다. 서버는 source 범위·권한·분석/편집 revision과 구간 길이를 검증한 후 export plan을 반환한다. 같은 edited interval이 여러 인물/scene에서 선택돼도 **정확히 같은** `(sourceHash, streamId, editedStartMs, editedEndMs, outputSettingsHash)`는 MP4를 한 번만 생성하고 ZIP에도 한 번 넣으며 manifest에 모든 선택·group 출처를 남긴다. sceneId가 같아도 편집 경계가 다르면 **각각 보존**한다. 서로 겹치지만 경계가 다른 interval은 자동 union하지 않는다. union은 UI에서 명시적으로 선택하는 후속 옵션이다. 캐시 키에는 codec/profile/audio/rotation까지 포함한다. ZIP은 기존 `personId` 쿼리를 확장한 것으로 오인하지 않도록 선택 목록을 서버 본문으로 전달한다.

기본 MP4는 원본 비율, 원본 소리 유지, 고정 crop/BGM/타이틀 없음. source seek preview와 실제 MP4의 경계 차이를 검증하며 keyframe copy가 경계를 어기면 재인코딩한다. export 요청의 계획/확인 화면이 필요할 경우 출력 unique 구간의 총 길이와 중복 제거 전 대상 수를 함께 보여준다. 이어 붙인 단일 MP4 경로는 만들지 않는다. ZIP 항목은 source 첫 등장순으로 나열하고, 정확히 동일한 edited interval은 한 번, 겹친 다른 구간은 각각 유지한다. 입력·개별/ZIP의 허용 총 길이는 실측과 가격 계약 전에는 제품 정책으로 단정하지 않는다.

분석과 export는 별도 `AnalysisJob → ReviewDraft → ExportJob`로 모델링한다. 리뷰 준비 시점, 첫 MP4, 전체 ZIP 준비 시점을 별도 측정한다. export plan에 예상 길이·파일 수·비용 quote와 동일 revision/idempotency key를 묶는다. 기존 과금 operation map에는 person이 없으므로 무료라고 가정하거나 dance key를 재사용하지 않는다. 과금이 필요하면 Web API에 신규 operation/권한/quote·ledger·환불 계약을 **별도 scope**로 승인하고 quote 확인 전 실행하지 않는다. 취소는 queued/실행 중을 구분해 worker/ffmpeg 중단과 `.part` 정리까지 확인하고, 완료된 동일 hash 파일만 재개에 재사용한다. edit/analysis revision이 바뀐 **export plan**은 다시 검증한다. 다만 source bytes·편집 경계·출력 설정이 정확히 같은 완료 MP4 blob은 새 plan에서 안전하게 재사용할 수 있다. source 또는 output setting이 바뀌면 blob 재사용을 금지한다. 실패·취소·재개와 크레딧 정산은 서버 확인 상태를 기준으로 멱등화하며 실제 가격·환불 규칙은 미결정이다. 원본은 draft/export가 참조하는 동안 hash를 검증하며 보존 기간은 사용자 정책 입력이 필요하다.

## 6. Superpowers 다음 gate와 작업 공간

이 문서는 초기 검토용 접근·계약 제안이다. 두 1차 성공 기준과 이어 붙인 MP4 제외, 직접 다운로드 UI를 확인했다. [10/1 W14 서면 MVP 설계](../../../../../../docs/superpowers/specs/2026-10-01-person-highlight-mvp-design.md)를 리뷰한 뒤 `writing-plans` 계획 → 계획 리뷰·실행 방식 선택 순서로 간다. 과금/원본 보존 정책, 실제 평가 입력, W13 공통 계약 상호 확인은 실행 전 gate다. 공통 패키지 계약+관측 adapter를 먼저 독립 slice로, 제품 UI·export 계약은 뒤의 slice로 나누는 것이 충돌·검증 비용을 줄인다.

제품 구현을 시작할 때에만 실제 대상 Python/Nest/Angular, 등록·모델 준비가 필요한 Electron, 새 과금/권한이 필요한 Web API의 **각 최신 `origin/dev`를 fetch 확인한 새 브랜치·격리 worktree**를 만든다. 공통 root 아래 형제 경로를 유지한다. 현재 원본 checkout과 다른 세션 미커밋 변경을 건드리지 않는다. 9/29 SHA는 조사 기준일 뿐 최신 보증이 아니다.

## 7. 관측·검증과 아직 없는 근거

[W14 실행 전 manifest 초안](30-w14-evaluation-manifest.yaml)에 입력 3개×120초·GT 항목·최대 3 face-only 추론 및 동일 embedding의 grouping 기준 1개 대조(최대 6조건 결과)·자원 중단 조건·지표 정의를 적었다. **정확한 입력 경로/hash/라벨/실제 설치 모델 hash/실행 위치가 비어 있으므로 ML은 실행할 수 없다.** 9/29 로컬 짧은 세로 영상은 원본·GT·평가 적합성이 확인되지 않아 자동 채택하지 않았다.

이번 검증은 위 9개 인계 파일, 9/30 W13 문서, 현재 로컬 Python/Nest/Angular/Electron/Web API 소스와 Git 상태의 읽기 전용 대조, OpenCV/InsightFace/ByteTrack 공식 자료 재조회다. 성능·정확도·Mac/Windows parity·사용자 UX·과금은 측정하지 않았다. 최신 로컬 HEAD는 Python `4778295`, Nest `c8b8b07`, Angular `5570f8ca`(기존 타 세션 문서 수정 있음), Electron `9d5ea55`, Web API `1feac57`이며 fetch하지 않았다. `.codex`에는 여러 세션의 기존 미커밋 문서가 있어 이 W14 관련 문서만 추가/갱신한다.
