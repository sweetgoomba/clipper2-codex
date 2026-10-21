# W14 — 고정된 안무 메인 얼굴의 표본 선택·세 모델 비교

작성: 2026-10-14. 상태: **제한된 실험 완료, 제품 적용·모델 교체 미채택**.

## 쉽게 요약

- 같은 메인 인물 구간에서도 어떤 시점의 얼굴을 비교하느냐가 결과에 영향을 준다.
- 선명도와 크기로 고르면 비교 가능한 얼굴이 80→89개로 늘었다. 표본 수는 각각99개로 같았다.
- SFace의 멤버 배정은36개 범위 중8→13개로 늘었지만, 기존 하니 배정 하나가 보류로 바뀌었다. 선명한 얼굴로 전부 바꾸는 안은 바로 적용할 수 없다.
- 기존 표본을 유지하고 새 얼굴을 보충하는 후속 계산에서는15개 배정, 기존8개는 모두 유지됐다. **표본이99→156개로 증가한 별도 분석**이고, 추가7개 모두 정답이라고 확인한 결과는 아니다.
- AuraFace/Intel0095로 교체할 근거는 이번에도 얻지 못했다. 혜인의 어려운 사례도 여전히 미해결이다.
- 지금 사용자에게 작은 얼굴을 다시 라벨링하도록 요구하지 않는다. 다음 평가에서는 원본 움직임과 선택된 메인 위치를 함께 확인할 수 있는 구간을 우선하고, 명확한 근거가 없는 얼굴에 억지로 이름을 붙이지 않는다.

## 1. 승인된 범위와 보존

직전 사용자의 ‘진행해줘’에 따라 고정된 W13 메인 출력에서 얼굴 수집→동일 입력 모델 비교→멤버/클립/원본 근거 화면까지 수행했다. 기존 평가 경로 개선이며 새 제품 아키텍처·모델 설치·다운로드·유료API·몸 모델 추론은 없다.

W14 Python worktree branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e` 및 개별 코드 hash를 사용했다. 기존 dirty pyproject/uv.lock/core/evaluation은 보존했고, 제품 코드·공통 core·W13 main/mapping/crop·다른 형제 repo를 수정하지 않았다. commit/push/merge·새 채팅 생성·다른 채팅 메시지 없음.

[사전 실행 계획](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/docs/superpowers/plans/2026-10-14-main-face-quality-sampling.md)

## 2. 입력과 실험 고정

W13 완료 결과 `single-gaps-35/revision-a`의 observed frames·segments와 실제 pose를 W14 출력에 복사하고 해시로 고정했다. 이후 W13 변경과 무관한 snapshot이다. 이전27번과 구간 분할이 다르므로27→35 숫자 차이를 W14 개선으로 해석하지 않는다.

- 원본: `/Users/jina/project/adlight/.worktrees/w13-review-scenes-20261001/runtime-preview/sources/youtube/yFTAYXDTjqI/source.mp4`
- SHA-256: `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`
- 원본1920×1012, fps60000/1001. 검출 전320px 축소 없음.
- 전체62구간 중 single34 + joint1(두 명)을36개의 segment×main 범위로 평가. group/unknown에는 이 실험에서 이름을 새로 붙이지 않는다.
- 고정된 메인 관측:649원본프레임 /678 main관측. 원본5.739~105.305초 내 해당 메인 시점들; 정확한 전체 시각은 manifest.scopes에 포함.
- source_track_runs 보존: 같은 몸으로 이어진35→38,68→69를 각각 원래run으로 유지해 짧은run도 수집 기회를 보장했다. 새로운 메인 추적을 하지 않았다.
- 저장된 recovered/joint_context/candidate_bridge 실제 관측만 원래 pose에 보충했다. 없던 몸이나 얼굴을 만들지 않았다.
- GT: 기존135개 답변 원문 hash `684cbd4d1a40904e64b43b9b9efeeaad52a94e7dafebee1a7ecfd2f4399b2aec`. 정확한frame+유일한IoU≥.5로35얼굴과 연결했고, 그중 등록 멤버 이름이 있는34얼굴을 인식 지표에 사용했다. 이 중 식별가능 yes는28개. 구간 전체 GT가 아니다.
- 등록 사진23장, 기존 모델별 참조 cache·거리/margin 기준 고정. 모델 점수나 GT로 표본 선택 금지.

[실행 전 manifest](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-quality-v1/manifest.json), [추론 전 표본 선택 manifest](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-quality-v1/selection.json)

Manifest SHA: `d07cb5ec4d795a4de283263ded1a5ed677b366ccfd7ada453b63500e7d290e5b`

Selection SHA: `e54923532f58b56057c1cda8818afca2bd94034f9e56e601aaa2a74bd80c454b`

## 3. 비교한 방법

### 1차: 같은 표본 예산99개

A. 각 track run 처음·중간·끝 최대3시점. 짧으면 있는 시점만 사용.

B. 각 run을 시간순3개 구획으로 나눈 뒤 각 구획에서 얼굴 화질 점수가 가장 높은 시점을 선택. 점수는 얼굴 내부80%의64×64 gray Laplacian 분산 log1p × min(원본 얼굴 가로,64)/64. 기존 몸↔얼굴 연결과 유효5점이 있는 표본을 우선한다. 이 점수가 인식에 더 유리하다는 보장은 실험 전 두지 않았다.

두 조건의 합집합 + GT 연결용 진단 얼굴을 고정한 뒤 세 모델 모두158얼굴을 처리했다. 실패23개도 결과181행에 남겼다. GT 연결용 추가 얼굴은 구간 투표에 추가하지 않았다.

### 후속: 기존 표본 + 보완 표본156개

1차에서 하니 회귀를 확인한 뒤 저장된 개별 얼굴 판정만 합쳐 계산했다. 기존 얼굴을 보존하고 화질 표본을 추가하되 같은 관측은 중복으로 세지 않는다. 서로 다른 멤버로 확정된 근거가 충돌하면 보류한다. 문턱 완화·모델 추론·새 GT 사용 없음.

**표본 예산이 크며 사후 분석이다.** 앞의 같은예산 비교나 새로운 독립 평가로 소개하지 않는다. [재현 코드](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/evaluation/segment_review/supplement_quality.py), [전체 판정](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-quality-v1/supplement-replay.json).

기존 pooled 결합 후보도 raw실행 결과에 보존했지만 이번 주 비교/화면/결론은 개별얼굴 확정근거의 합의만 사용한다. pooled 정책 유효성을 새로 입증한 결과가 아니다.

## 4. 실제 결과

### 얼굴을 확보한 정도

678관측 중 연결된 유효 얼굴596, 얼굴 연결 불가51, 연결 모호30, 특징점 품질 검증 실패1. 연결 실패 원인은 메인 머리 근처 얼굴 없음41, 머리 위치 신뢰 부족10, 다른 사람 머리와 경합30이다. 모델 미검출과 연결 모호를 같은 미매칭으로 숨기지 않았다.

선택99슬롯 중 인식 가능한 입력은 시간순80→화질89. 원본 얼굴 가로 중앙값36.49→38.58px. 크게 선명한 얼굴이 새로 생긴 것은 아니다.

### 최종 멤버 배정 수 — 정답 수 아님

| 모델 | 시간순99표본 | 화질99표본 | 후속 보완156표본 |
|---|---:|---:|---:|
| SFace | 8/36 | 13/36 | 15/36 |
| AuraFace-v1 | 4/36 | 7/36 | 11/36 |
| Intel0095 | 5/36 | 3/36 | 8/36 |

SFace에서 기존얼굴 답변이 연결된11범위의 ‘부분 정답과 판정 일치’는3→6→7범위다. 기존8개 배정은 후속안15개에서 모두 같은 이름으로 유지됐다. 추가7개 중4개는 범위 안의 일부 사용자 답변과 일치하며, 나머지3개는 연결된 멤버 정답이 없다. 전체구간 정확도로 환산하지 않는다.

### 동일한 GT34얼굴의 인식 비교

| 모델 | 올바르게 배정 | 다른 멤버로 배정 | 보류 |
|---|---:|---:|---:|
| SFace | 9 | 0 | 25 |
| AuraFace-v1 | 8 | 0 | 26 |
| Intel0095 | 1 | 1 | 32 |

이34얼굴은 앞서 평가한 같은 얼굴과 겹치는 재현 지표다. 새 독립 검증34개로 세지 않는다. 혜인10얼굴의 올바른 확정은 모두0이며, Intel의 혜인→해린 개별 오배정1개가 다시 나타났다. 그 클립 전체는 보류다. 임베딩 비교·실행 오류는0.

## 5. 확인한 실패와 의미

1. **28.762–34.167초 / 화면 클립22, s0035-p0**: 시간순은 하니, 화질만 쓰면 보류. 화질 표본3개의 점수1위는 모두하니지만 1·2위 차이가 `.1456/.0839/.1116`이고 고정문턱`.1353`을 통과한 표본이1개뿐이다. 크기·선명도 개선이 다른 멤버와의 구별력 개선을 보장하지 않는 실제 사례다. 보완안에서는 기존의 유효근거를 유지해 하니로 남는다.
2. **52.719–53.387초 / 클립27, s0045-p0**: 시간순은 유효근거1개, 화질선택은 해린 확정2개 확보하여 보류→해린. 일부 기존 답변과 일치하지만 구간 전체독립GT는 아니다.
3. **57.257–63.063초 / 클립29, s0047-p0**: 일부 혜인답변이 연결된 구간. 화질선택에서도 가까운 후보가 다니엘/혜인/하니/민지로 흔들리며 전체보류다. 다른 시점의 이름을 GT가 있는 얼굴에 덮어쓰지 않는다. 이 범위의 실제 선택 메인이 전체시간 같은 인물인지와 얼굴연결/인식 중 어느 단계가 남은 혼동 원인인지는 미확인이다.

SFace **화질 단독 조건**의 보류23개를 단계별로 나누면: 메인 관측 자체1시점뿐5개, 연결된 유효얼굴2개미만4개, 얼굴은2개이상 있으나 인식근거부족14개다. 후속15배정안이나 세모델 전체통계가 아니다. [상세](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-quality-v1/failure-location.json).

## 6. 실행·검증 증거

- 기존 YuNet649회. SFace/Aura/Intel각158회, 인식합계474회. 새모델0/설치0/몸추론0.
- Mac Apple M4·CPU 1thread·batch1. Python3.11.12, OpenCV4.13.0.92, ORT1.24.4, OpenVINO2026.4.1. 기존평가venv 그대로.
- 검출49.07초/피크389.9MiB. 인식전체 SFace6.37초/328.6MiB, Aura15.29초/1065.9MiB, Intel5.75초/282.3MiB. 이 수치는 같은Mac의 해당평가프로세스이며 제품전체처리시간이나 Windows수치가 아니다.
- 단계마다300초·RSS4GiB, 검출700/인식각300회·총출력500MiB 제한. 모두상한내. 실제평가폴더약178MiB(문서전186,143,782bytes).
- 최초 sandbox에서ps사용이 막혔으나 자식추론 시작전 실패. 감시권한으로 재실행; 이 사전실패는 ML실행횟수에 포함하지 않는다. 제한없는재시도/자동반복없음.
- 평가/core테스트183개 통과(0.50초). JS syntax검사 통과. 새구간adapter·추적run보존·공동인물분리·GT비사용·짧은run기회·중복pose검증 포함. 전체제품테스트/빌드 결과가 아니다.
- 개별후보거리2,370개·동일입력181행×3·기본구간판정216개 독립검산. 최대거리차1.20e-7미만.
- 입력해시·정확한모델5파일hash·고정두조건선택재현·원본crop동일성 검증.
- 독립코드리뷰 및 후속보완재집계에서중요오류없음. 실패위치통계의 model/variant표시를 명확히 보완했다.
- 브라우저에서멤버·클립·원본1920폭영상실제재생, 구간끝정지, 선택얼굴전환, 빈혜인목록재생비활성, 오류로그없음 확인. 문서/UI검증은실제인물정답검증을대신하지않는다.

[수치 검산](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-quality-v1/verification.json) · [실행 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-quality-v1/summary.json) · [독립 리뷰](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/main-face-quality-v1/independent-review.md)

## 7. 화면 사용

[비교화면](http://127.0.0.1:58261/main-face-quality-v1/index.html). 기본 SFace / 기존+보완. 왼쪽멤버를누르면오른쪽클립목록이바뀌고, 클립을누르면중앙의원본메인몸·얼굴위치와두선택표본이표시된다. ‘클립재생’은해당원본구간을재생하고, 얼굴카드선택은해당시점의정지근거를보여준다. 세모델의배정은시험결과이며이름이붙었다고정답이보장되지않는다. 자료는읽기전용, 새정답입력요구없음.

## 8. 결정·미검증·다음 일

- **모델선택:** SFace비교기준유지. 신규교체미채택. 모델선택완료/얼굴매칭해결로표현하지않는다.
- **수집안:** 선명한얼굴로기존표본을전면교체하는안미채택. 기존근거를유지하고보완수집하는안을다음평가후보로둔다. 표본수가증가한효과를명시한다.
- **다음우선작업:** 보완안에서남은21범위중식별가능한메인얼굴이있는범위를먼저분리하고, 특히57–63초에서선택몸↔얼굴↔실제멤버의불일치를시점별로확인한다. 고정된메인출력을준비한별도촬영영상에서같은보완수집안을재검증한다. 작은흐린배경얼굴추가라벨링을성공기준으로쓰지않는다.
- **필요한입력:** 기존부분GT로알수없는범위의선택메인정답/동일인연속성, 별도영상의고정main출력과대표적식별가능정답. 아직이를확보했다고주장하지않는다. 이번단계에서사용자추가작업없음.
- **아직안한것:** 독립전체구간정확도·새영상일반화·혜인문제해결·제3후속안의prospective검증·Windows배포/Mac깨끗한설치·제품통합/과금/UI본앱연결.

## 9. W13 소유권·호환 인계

W14는평가코드/공통facecore, W13은main/segment/body/mapping/crop및제품소비adapter소유유지. 이번35snapshot소비는새공개계약상호승인이나제품수락을뜻하지않는다.

- `source_track_runs`와실제observed `main_bboxes`를함께읽어야한다. `role`만지속되고실제관측이없는시점은얼굴검출근거로만들지않는다.
- joint가상ID는별도scope로유지. 같은얼굴을동시두메인에중복배정하지않는다.
- 같은bbox의동일pose는중복제거, 좌표는같고키포인트가다르면모호함을남긴다.
- 연결된bodyrun이물리적으로동일인이라는보장과실제shot경계는W13출력/계약에서별도확인이필요하다. GT를전파하지않는다.
- 인계순서: W14공개API·fixture → W13scope/시간/좌표/실패compatibility → 소비adapter·선택venv/모델준비 → Macarm64/Windowsx64설치검증 → 합의후merge. 현재merge/배포승인없음.
