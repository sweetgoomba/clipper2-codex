# W14 — 얼굴 특징 구별 진단·추가 영상 정답 보완

2026-10-14 KST. 사용자 계속 진행 승인 범위에서 저장 특징만 분석했다. **모델 교체·제품 적용은 아직 채택하지 않았다.** 참조를 사용자가 확인한 영상 얼굴로 바꿔도 세 모델 모두 일부 다른 멤버를 더 가깝게 찾는다. 다만 시간 제외 뒤 같은 멤버 참조가 부족한 조건도 있으므로 모델의 근본적 구별 불가능으로 단정하지 않는다.

- [실제 같은 멤버/다른 멤버 얼굴 비교](http://127.0.0.1:58261/face-separation-v1/index.html)
- [아직 답하지 않은 7개 확인](http://127.0.0.1:58261/holdout-coverage-v1/index.html)
- [질문·고정 조건](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-separation-v1/probe.md) / [실행 manifest](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-separation-v1/manifest.json) / [전체 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-separation-v1/result.json)
- [47,790거리 검산](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-separation-v1/verification.json) / [독립 리뷰](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-separation-v1/review.json)
- [추가7개 manifest](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-coverage-v1/manifest.json) / [화면·내보내기 검증](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-coverage-v1/ui-verification.json)

## 1. 실행과 비교 조건

기존 격리 worktree `shared-reference-face-matching-20261013`, branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e`. 이번 Python/JS는 evaluation-output 아래 재현용 진단 스크립트·보고서이며 제품 코드가 아니다. public core/API·기본SDK·W13 main/mapping/crop·제품adapter·기존dirty파일·GT/이전결과는 변경하지 않았다. 새ML/모델 다운로드/의존성 설치/API/Build5/commit/push/세션생성/다른채팅메시지0.

SFace2021dec128D, AuraFace glintr100512D, Intel0095 256D의 기존 캐시만 읽었다. 정확한 모델 weight hash/config/runtime provenance는 manifest의 model별 항목과 parent 최신모델비교 manifest에 보존. 캐시 공간을 혼합하지 않고 각각 float64 재정규화 후1-cosine을 검산했다. Apple M4/macOS27arm64/Python3.11.12/NumPy2.4.4. 새속도/RSS 벤치마크 아님.

원본 `yFTAYXDTjqI` SHA256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`,1920×1012. 기존 사용자135답변·W13iteration27에서 정답과위치연결한 최신161행·추가두영상15행을 각각 보존한다. 총311행×3모델은 서로 독립인933사례가 아니다. 최신 정답34는 얼굴 단위 부분GT이며 전체scope로 전파하지 않는다.

참조는 원본 영상의 사용자 known-member+identifiable=yes 얼굴만 쓴다. 인물/source/1초bucket마다 중앙에가까운1개,동률ID. 같은 영상 query의20초block±5초는 전부 제외; 추가영상의얼굴/답변은참조에들어가지않는다. 모든모델에동일한참조ID를사용하고누락feature는명시적실패. 기준값탐색·확정정책은없다. query정답은점수순위선정에쓰지않고후속genuine/impostor분리/채점에만쓴다.

각얼굴에같은멤버최소거리/다른멤버최소거리·실제ID/이미지·5멤버별참조수·전체거리를보존했다. tieε=1e-8. 추가 pair-ordering은각다른멤버에동일가중치를주는genuine/impostor거리순서비율(동점0.5)이며TAR/FAR가아니다. 등록사진23개는자기사진만제외한최근접·멤버평균일관성검사도했다.

manifest SHA256 `bd436038f3b287f6e64babb30222aae76b9385a327c651687d493ae9c89138f2`. 38input/code/brief hashes. 이번에는모델이아니라참조와최근접비교경로를함께바꾼진단이므로이전registered centroid와차이를모델교체효과로말하지않는다.

## 2. 실제 결과: 거리 1위 정답 수

**확정성공수가 아니며, 사람이 인물별 참조를 알려준 진단이다.**

| 자료 | SFace 등록평균→영상개별참조 | AuraFace 등록평균→영상개별참조 | Intel0095 등록평균→영상개별참조 |
|---|---:|---:|---:|
| 기존 멤버128얼굴 |93→108|85→100|75→96|
| 기존 식별가능102얼굴 |82→90|73→86|67→84|
| 최신 메인 멤버34얼굴 |28→25|21→24|18→26|
| 최신 식별가능28얼굴 |24→22|17→22|14→23|
| 추가영상 멤버7얼굴 |6→6|6→3|6→6|

Aura/Intel기존135행에는각정렬실패2개(멤버1/판단어려움1)가있으며제외해분모를줄이지않았다. 최신32얼굴연결보류도그대로남겼다. 등록외/비얼굴/판단어려움/미입력은멤버정답오답으로세지않는다. 새거부정책은없어등록외거부율은측정하지않았다.

최신혜인10얼굴은등록평균7/4/1→영상개별참조8/6/6으로일부회복했지만,하니7얼굴은6/7/6→3/4/6으로악화했다. 이결과로자동참조나새모델을선택하지않는다. 최신식별가능28중세모델공통정답18/공통오답2. 나머지는모델마다다르며앙상블규칙을추가하지않았다.

### 구체적인 혜인 사례

58.2582초는사용자혜인답변과연결된얼굴이지만세모델모두해린참조를더가깝게찾았다.

| 모델 | 같은멤버최근접(9.61초혜인) | 다른멤버최근접(19.42초해린) |
|---|---:|---:|
| SFace |0.554051|0.440680|
| AuraFace |0.593659|0.467717|
| Intel0095 |0.500194|0.312640|

이query는35~65초를제외해혜인참조2장만남고다른멤버는9~13장이다. 같은멤버의촬영조건/각도범위가충분하지않을수있다. 61.528초는세모델모두혜인을최근접으로찾지만제외범위55~85초/혜인참조7장으로구성이달라,둘의차이를얼굴선명도하나의인과효과라고해석하지않는다.

### 등록 사진 자체

등록23장의자기사진제외최근접일치:SFace22/Aura22/Intel23. 멤버별다른사진평균일치23/22/23. **혜인4장은두검사모두세모델에서같은멤버로일치**했다. 참조등록인물의진짜정답을새로확인한검사는아니며,사진을잘못등록했다는근거를얻지못했다는수준이다. SFace ref-12와Aura ref-06의최근접사진은다른멤버였지만자동삭제/재라벨하지않았다.

## 3. 다음 검증을 위한 미확인7개 준비

추가두영상의기존검출22개중처음크기별선택15개만사용자가답했다. 그답변의known7개에는혜인·하니가없었다. **남은7개모두**를예측점수없이별도화면에복사했다.2개는`6bVUjsUi9sw`95.028초,5개는`J9DlrnNlgfE`45.012초다. 새검출/인식0. 7개에혜인/하니가반드시있다는보장은없다.

기존15ID/GT와7ID는겹치지않고합집합22. source hash/frame/PTS/timebase/bbox/원본context/crop을그대로보존했다. 추가7개manifest SHA256 `0126230099ab5a474683ccdb03358a07e99b9eb75346f8723072c8ab344fd773`. 새출력/URL/storage key/파일명분리. 사용자답변현재0,QA7답변은`ui_qa_not_ground_truth`로별도표시하고절대평가에수입하지않는다.

사용자작업: 각7얼굴에서인물과식별가능여부선택→다음얼굴→확인내용내보내기. 출력파일`clipper-holdout-coverage-labels.json`. 메인댄서/구간정답작성아님. 이후답변을정확한manifest/ID/source/PTS/bbox/annotation_origin과대조해받고기존15개에추가한다. 이추가정답은평가에만쓰며기준보정/영상참조수집에넣지않는다. 새추론을실행한다면두단계입력manifest·7face×3기존모델·시간/메모리상한을먼저고정한다. 이미본두영상의프레임보완이므로새독립영상검증이라고부르지않는다.

## 4. 실제 검증·미검증·소유권

- 합성6tests RED→GREEN,최종6passed/0.07초. 참조제외·query정답비사용·없는멤버/feature·균등멤버pair비중·동점·등록외미채점검증. 기존holdout labels Node test1개(완료판정/비얼굴/identity전환/provenance/unknown키검사)통과. 제품전체회귀·ML부팅은이번에돌리지않았다.
- 독립검산47,790scalarcosine최대차1.2212453270876722e-15,38hashes,311행×3,23참조×3,63known/identifiable/member집계및모든other분모확인.
- 독립리뷰Critical/Important0. Minor표시문구1건(전체정렬실패와멤버실패분모혼동)은전체2/멤버1로명확히수정. 계산변경없음. 원래GT/상류정렬추론/제품준비는기존증거범위로두고새성공주장없음.
- CUA에서실패·성공얼굴사진,등록외2개,연결보류,빈필터확인. 보완화면은QA입력/새로고침보존/실제JSON내보내기1개·7개/사용자화면0개분리확인. 다운로드이벤트대기도구가한번timeout했으나브라우저내보내기는실행됐고실제Downloads JSON을검사했다. 원본작은얼굴은240px보기로확대표시하되모델입력/세부정보는변경없다.
- 보완7개준비는부모가검증했으며앞선독립리뷰의범위에는포함되지않았다. 원래사용자GT자체정확성·유효참조coverage의인과성·새촬영일반화·unknown거부·전체구간매칭·최신W13iteration27이후소비·Mac/Windows패키징은미검증.
- W14평가/공통face API·fixture소유, W13기존main/mapping/crop소유유지. W14공개계약/fixture→W13동일인scope·실패compatibility→소비adapter·선택venv→Mac arm64/Windows x64→합의merge순서유지. 제품통합·새상호계약승인을의미하지않는다.
