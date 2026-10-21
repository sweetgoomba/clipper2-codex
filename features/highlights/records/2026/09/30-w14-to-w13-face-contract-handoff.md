# W14 → W13 공통 얼굴 계약·파일 소유권 인계

## 2026-10-15 시험 빌드 통합 — W13 소비자에게 남기는 현재 계약

사용자가 이 세션의 얼굴 매칭을 직접 빌드·재실행해 확인하겠다고 지시해 W14가 최초 Dance adapter 연결까지 수행했다. Python 병합 테스트 브랜치 `test/dance-highlight-merge-20261015` HEAD `e636a5f`, Electron 같은 이름의 별도 브랜치 HEAD `b162592`가 빌드 입력이다. W14 격리 feature에서 core 0.2.0/adapter/테스트를 먼저 고정하고 Python에 merge한 뒤, Electron의 Dance 전용 비편집 venv 재설치·core source fingerprint를 merge했다. 다른 세션의 Angular/Nest와 W13 평가 노트북은 수정하지 않았다.

공개 `clipper_face_core` API는 Dance `Segment`/`person_id`/UI/job 타입을 받지 않는다. Dance adapter는 기존 YuNet/SFace 128D·alignCrop·float32 L2 공간과 참조 이미지 SHA/크기, 영상 SHA/파생 초/구간 범위/모델·config SHA를 제공한다. 메인 구간의 최다 얼굴 클러스터 표본만 참조와 비교하고, 상충한 멤버 근거를 보류하며 서로 다른 클러스터의 동일 멤버 매칭에 기존 추가 거리 조건을 적용한다. 얼굴이 메인 몸 ROI에서 선택됐다는 것은 **Dance의 가정**이고 독립적인 얼굴 소유 정답이 아니다. 구간/메인 선정·track/crop과 `person_id` 단일 소유 계약은 이번에 변경하지 않았다.

W14의 공통 core·임베딩 공간/출처 계약 초기 소유, W13의 메인 몸·컷·track·선택 얼굴 ROI/mapping/crop·이후 Dance 소비자 소유를 유지한다. W13이 이 브랜치와 결합할 때 Python `e636a5f`의 `pipeline.py`/`reference_matcher.py`를 기준으로 변경하고 core 공개 입력을 Dance 타입에 종속시키지 않는다. 소비자 호환 검사는 병합 트리 Dance+core **115 통과**, Electron 선택 venv **12 통과**, 실제 옵션 오프라인 wheel 설치/import, 안무 로컬 API smoke **4 통과·1 skip**이다. 실제 설치형 앱 빌드, 새 클립의 정답/오확정/미매칭, Mac arm64·Windows x64 패키징은 아직 미검증이다. 신규 얼굴 모델·참조 추가·시간 전파는 포함하지 않았다. W13의 별도 수락을 주장하지 않으며, 이번 사용자 요청으로 W14가 통합한 사실을 이 문서에 인계한다.

## 2026-10-14 얼굴 근거 회귀 입력과 소비 gate

[W14 회귀 결과](../10/14-w14-face-evidence-regression-result.md)에서 직접 얼굴 정답34+23과 등록 외5를 별도 촬영·모델·gallery별로 재계산했다. 확인된 다른 촬영 참조8장을 더하면 뉴진스 SFace와 AuraFace 모두 정답2개 회복과 기존 정답1개 보류가 함께 생겨 무손실 gate에 실패했다. 위험 run의 SFace 하니확정3은 보류로 바뀌지만 그 주변8얼굴의 직접 사용자 GT는 없다. 얼굴 연결 `confirmed`와 원본 시각 연속성을 신원 정답으로 승격하지 않는다. 모델 간 거리/문턱/참조 cache는 혼용하지 않는다.

W14는 [해시 고정 평가 입력·결과·26항목 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/face-evidence-regression-v1/decision.md)와 공통 얼굴 공개 API를 소유한다. W13은 안정된 main 몸, 실제 shot cut/track 교대/구간, mapping/crop, Dance 제품 adapter를 소유한다. W13 소비 시 같은 source hash·time base·bbox 좌표·관측/몸경로 ID·실패 상태·모델 공간을 대조하고 기존 소비자 compatibility를 통과시킨다. 이어 선택 venv/모델 준비와 Mac arm64/Windows x64 설치 검증 후 합의된 merge 순서를 따른다. 이번 평가는 제품/core/W13 코드 변경, W13 새 수락, 모델 전환 승인이 아니다.

## 2026-10-14 시간 이웃 규칙 반례의 W13 소비 조건

[실패 위치와 출처별 점수](../10/14-w14-temporal-cross-video-stress-result.md#후속-원인-분리-잘못된-확정-근거가-먼저-있었다). 4K SFace/등록23참조의 `s0043-p0-r1`에서 59.593/59.660/59.860초 얼굴은 시간 규칙 적용 전부터 하니 확정이었고, 보류8시점에 같은 이름을 전파하는 것은 위험했다. 직접 사용자 라벨4시점은 혜인이나 중간8시점의 직접 GT는 없다. 몸 track ID가 68→69로 바뀐 사실과 원본의 동일 출연자 시각 연속성을 모두 보존한다. 별도 화질·모델 비교의 gallery 지문이 다르므로 거리/threshold를 합치지 않는다.

W14는 이 위험 run·원본 프레임·정확한 얼굴 라벨/미라벨 구분·source/model/gallery/policy 지문을 평가 회귀 입력으로 소유한다. W13은 안정된 main 몸, shot cut, 실제 track 교대, 구간 경계와 선택 crop의 대응을 소유한다. 소비 계약에서 **연결 확정(`confirmed`)을 신원 정답으로 승격하지 않고**, 보류 얼굴을 시간상 근처 확정 이름으로 자동 채우지 않는다. 새 후보는 직접 라벨이 있는 얼굴의 정답 회복/오확정/미매칭과 실제 컷·교대/동시 출연/등록 외 인물 대조를 통과한 뒤에만 제품 적용을 논의한다. 이번에는 W13 파일 변경, 새 상호 수락, 공통 공개 API/제품 adapter/선택 의존성 변경, 병합이 없었다. 계약 상호확인 → 소비자 compatibility test → 선택 venv/모델 준비 → Mac arm64/Windows x64 설치 검증 → 합의 merge 순서를 유지한다.

## 2026-10-14 SeetaFace6 일반형 실제 비교 — 제품 연결 보류

[실제 결과와 검산](../10/14-w14-seeta-normal-comparison-result.md) · [메인/얼굴/모델 비교 화면](http://127.0.0.1:53320/seeta-normal-v1/index.html). 사용자의 제한 실행 승인을 받아 공식 CSTA와 고정 ONNX를 확보하고 출처·SHA-256·입출력을 확인했다. 같은 원본 프레임·YuNet 얼굴 상자와 5점·참조 사진 23장·W13 메인/몸 경로/구간을 유지하고 일반형에 필요한 정렬·전후처리만 달리했다. 모델 호출 503회, 새 추론 오류 0건, 독립 계산 검산 34,078개 차이 0이다.

식별 가능한 안무 얼굴 28개에서 정답은 SFace 15개, AuraFace 17개, 일반형 19개다. 다른 두 영상의 식별 가능한 19개에서는 15개, 17개, 13개다. 일반형은 뒤 자료에서 SFace보다 2개 적어 사전 기준에 실패했다. 제품은 SFace를 유지하고 AuraFace는 비교 후보로 남긴다. 원본 CSTA와 제3자 ONNX의 수치는 두 입력에서 일치했지만, 네이티브 TenniS 샘플러와 Mac·Windows 설치 앱 실행은 미검증이다. 안무 34개 라벨은 개발 자료와 동일 프레임이고 두 추가 영상도 이미 본 회귀 자료다. 35개 대상의 이름 수를 전체 구간 정확도로 해석하지 않는다.

W14는 공통 얼굴 API·검증 입력·격리 평가, W13은 메인 몸·경로·구간·멤버 연결·crop·제품 adapter를 계속 소유한다. 새 일반형의 원본/변환 SHA, single 256 정렬, 248 BGR 입력, 제곱근/L2와 거리 기준은 별도 embedding 공간·참조 캐시 키로 분리했다. 공개 API와 제품 adapter, 선택 의존성은 바꾸지 않았다. 유효 후보가 다시 생기면 계약 확인 → 기존 소비자 호환성 검증 → 선택 가상환경과 모델 준비 → Apple Silicon / Windows x64 설치 검증 → 합의한 순서의 병합을 따른다. Mac Intel은 대상이 아니다. W13의 새 수락, 다른 채팅 발신, 커밋·푸시·병합은 없었다. 다음 검증은 독립 영상의 식별 가능한 메인 얼굴·몸 경로·구간 정답을 고정하는 것이다. 아래의 승인 대기 항목은 이전 상태다.


## 2026-10-14 SeetaFace6 일반형 실행 전 범위 준비

[조사·구체적 실행안](../10/14-w14-standard-recognition-probe-preflight.md). Light 미채택을 유지하며 별도 일반형ResNet-50 가중치를 후보로 제시했다. 공식 원본ZIP301,479,618bytes+ONNX102,530,399bytes, 합계약404MB/상한450MiB, 총600forward·20분·4GiB, 기존ORTCPU/추가설치0. 사용자에게 이 범위 승인을 요청했으며 아직 가중치 다운로드·ML0이다. 제품SFace유지/Aura비교유지·품질개선미완료.

일반형은single256정렬→중앙248BGR float32(외부/255없음)→1024출력→sqrt1회/L2로 Light와 다르다. 공식sqrt(x)와wrapper sqrt(max(0,x)) 차이를 확인해 실제출력/원본비교gate를 넣었다. 현재는소스/메타데이터명세이며binary/두OS실행확인아님. 원본픽셀·YuNet5점에서참조/query재정렬,새space/cache/threshold격리. 같은35대상/37run합의를유지한다.

관련입력88hash·문서18hash확인. 모델선정에서는성능주장/라이선스표시/미확인권한을구분;PETALface약861MB와추가IQA/CPU변환부담으로보류. native34개발중복·추가영상회귀자료한계보존. 유효결과인경우에만독립자료/배포검증으로진행. W14 API/fixture/평가와W13 main/몸/구간/mapping/crop/제품adapter소유유지;계약확인→호환검증→선택venv/모델준비→Macarm64/Windowsx64→합의merge. 새W13수락·다른채팅발신·제품/core수정0. 얼굴정답/export재요청없음. 아래는이전이력이다.

## 2026-10-14 SeetaFace6 Light 비교 완료 — 제품 미채택

[실제 결과·파일·검증·한계](../10/14-w14-seeta-light-comparison-result.md), [같은 메인/얼굴 비교](http://127.0.0.1:58261/seeta-light-v1/index.html). 사용자 계속 진행 승인으로 이전 대기 해소. 공식 CSTA와 제3자 ONNX 원본 연결·전처리·변환 수치 대조 후 총503 forward, 추가 설치0. 안무34 얼굴 정답/오류/보류는 SFace18/0/16, Aura19/0/15, Seeta3/1/30; 추가 식별가능19 정답은15/17/12. **이번 Seeta 경로 미채택, 제품 SFace 유지, Aura 비교 후보 유지**다. 모든 Seeta 모델을 배제한 결론은 아니다.

61.6616초 혜인→하니 오류는59.4594–63.063초 몸 경로의 하니 합의로 이어졌고 기존 혜인 정답4지점과 모순된다. 전체 구간은 앞 경로 근거 부족으로 보류여서 내부 오류가 가려진다. 얼굴·몸 경로·구간 지표를 분리할 계약을 유지한다. native34는 개발과 같은 프레임/인물, 추가2영상도 재사용 자료여서 독립 정확도 증거가 아니다.

원 worker는 ML 후 baseline 오류명 집계에서 exit1. 원 log/정책/특징을 보존하고 후처리만 수정했으며 추가 ML0이다. 독립 감사34,078숫자 차이0,605입력hash 보존, 실제 UI 필터/재생을 확인했다. native TenniS sampler, Windows x64/깨끗한 Mac arm64 패키징은 미검증. 제품 품질 개선 완료나 배포 승인으로 읽지 않는다.

W14 공통 API/fixture/평가, W13 main/몸/구간/mapping/crop/제품 adapter 소유 유지. 이번 공개 API·core·제품·선택 의존성 변경0. Seeta 모델/전처리/정렬/거리/참조 cache는 기존 embedding 공간과 격리했다. 향후 유효 후보에 한해 계약 확인 → 소비자 compatibility test → 선택 venv·모델 준비 → Mac arm64/Windows x64 패키징 → 합의 merge 순서. Mac Intel 제외. 새 W13 수락·다른 채팅 발신·commit/push/merge 없음. 사용자 정답/export 재요청 없음. 아래는 이전 이력이다.

## 2026-10-14 다음 인식 후보 준비 — SeetaFace6 Light 조건부 검토

[조사 근거와 실행 범위](../10/14-w14-next-recognition-candidate-preflight.md). 다른 학습 가중치와 작은 파일의 비교 가치를 검토했다. 최신/우수 모델로 입증된 것은 아니다. 공식 CSTA와 제3자 ONNX의 출처·정확한 파일 조건·전처리·변환 검증을 통과한 경우에만 기존 격리 ORT CPU 환경에서 비교하는 범위를 사용자에게 제시했다. 약 10MB, 총 forward 600회·20분·4GiB, 새 설치·제품 적용 제외. 현재 승인 답변 대기다. 얼굴 이름·export 요청은 없다.

실제 수행은 소스/문서 10개와 기존 입력 54개 hash 확인이며 새 모델 다운로드·ML·제품 변경은 0이다. 기존 평가 34장은 개발 프레임과 중복, 추가 두 영상도 이미 노출된 회귀 자료다. 이 자료에서 좋아져도 독립 평가/두 OS 패키징 전에 제품 모델을 바꾸지 않는다.

W14 평가·공통 API/fixture / W13 main·몸·구간·mapping·crop·제품 adapter 소유를 유지한다. core 공개 API 변경은 필요하다고 확인되지 않았다. 채택 시 계약 확인 → 소비자 호환 검증 → 선택 환경·모델 준비 → Mac arm64·Windows x64 → 합의 merge 순서를 유지한다. 다른 채팅 발신·새 W13 수락·commit/push 없음.

## 2026-10-14 가까운참조2장 정책 — 현재입력 검증 후 미채택

[실제 결과·반례·검증](../10/14-w14-two-reference-transfer-result.md). 이전gallery-diagnosis의모델별best_two/centroid wrong_budget0기준을고정전이;새튜닝없음. native34/34가개발라벨과정확프레임중복이므로개발입력재평가이며새holdout아님. 추가2source도이미살펴본자료. 집계+각자threshold의결합정책비교.

SFace native18→20이나기존하니/별도main해린손실·scope2손실/2추가;Aura native19→21이나추가식별가능19 17→15·다니엘오확정유지. 알려진run/scope모순0이어도개별얼굴오류가보류에숨음. 문턱완화시혜인→하니강제수락반례(Aura직접,SFace개발정답51보존조건·반례identifiable null)를검산. **후보미채택·동일점수문턱반복조정종료·제품SFace유지**. 새ML0·1548판정/6860거리·140scope/148run독립검산·현재추가사용자조작없음.

W14평가/API,W13 main/몸/구간/mapping/crop/adapter소유와기존호환/merge순서유지. core/공개API/제품/의존성/사용자정답·편집수정0. 새W13수락/다른채팅발신/commit/push/merge없음. 다음은새인식근거/후보의배포조건·독립평가설계이며현재결과를제품개선완료로읽지않음.

## 2026-10-14 정렬 회귀의 참조/인식 원인 분리 — 제품 보류 유지

[실제 결과·후속](../10/14-w14-alignment-error-attribution.md). 같은 저장4공간에서 1548판정/6860거리 재현. Aura0009 해린95/140초는 개별참조1위 해린/평균1위 혜인, 다니엘25.759초는 두정렬·23개 단일제외에서도 해린1위. 최근접1장 대조는 추가식별가능19의1위17→19이나 native34 29→27·별도main2 1→0이라 미채택. **1위수는 threshold 적용정답수가 아님.** 새ML0·220순위/366기하독립검산·기존viewer에사진/거리근거 추가. 제품개선완료/모델채택 아님·현재추가사용자조작없음.

다음은 원래YuNet고정+복수참조지지 후보를 기존평균과 비교하고 모델별 기준을 개발자료에서 정할 예정. 이미 본3영상은 회귀평가로 기록,새독립holdout으로 부르지 않음. 특정참조삭제/정답별최적모델선택/빈관측을타인근거화 금지. W14 API/평가, W13 main/몸/구간/mapping/crop/adapter소유·기존compatibility/merge순서유지. 이번 core/API/제품/의존성/W13수정0·정답/편집/참조보존·새수락/채팅발신/commit/push없음.

## 2026-10-14 자동5점 0009 정렬 — 일부 회복·제품 전면 적용 보류

[실제 결과·계약·검증](../10/14-w14-auto-landmark-0009-result.md). 같은40B/35대상/37경로/353관측과원래23참조,추가34. 0009(BGR48/OpenVINO CPU)로참조와query5점만재생성하고새space분리;SFace/Aura가중치·policy·합의고정. Aura대상13→16(기존13유지,57–63혜인회복),nativeGT34정답19→21이나추가식별가능19정답17→15·25.759다니엘→해린오류유지. SFace native18→15·추가15→14. **일괄정렬/제품모델교체보류**. 새ML1098·오류0/upstream44보존·62tests·88hash·독립3430거리/70scope/74run검산·UI. 현재추가사용자입력없음.

W14평가/API/fixture, W13main/몸/구간/mapping/crop/제품adapter소유유지. 이번0009는artifact전용;core/publicAPI/제품/선택의존성/SDK시작경로변경0. 임베딩공간·참조cache는정렬/전처리hash로분리,기존기준은통제진단일뿐새제품threshold아님. 실패/연결보류/비얼굴/신원불명은별도기록. 공개API에Dance객체추가없음. 소비계약상호확인→source/time/좌표/scope/failure/space호환→선택venv·모델준비→Macarm64/Windowsx64패키징→합의merge순서. 새W13수락/채팅발신/commit/push/merge없음.

## 2026-10-14 시간순 점수 결합 — 새 오배정으로 제품 미채택

[실제 결과·검증·반례](../10/14-w14-sequence-score-diagnostic-result.md). 고정40B/35대상/37몸경로/353관측에 원래23참조의 SFace 점수만 사용. 시간0.25초칸+후보별중앙값+상태전환비용의 단일 평가정책에서 배정16→14,해린1추가/기존3손실. clip43 뒤 경로가 하니로 잘못 확정되어 기존혜인GT4개와 모순. 전체클립은보류라최종scope모순0만으로안전판정금지. run단위GT34는20/0/14→22/4/8(일치/모순/보류). 실제과거전환7중1단일배정/6보류,전환검출0;102초경계삭제stress만전환검출. 현재/과거source·space·gallery·policy분리,GT전파없음. 새25초다니엘유지/105초해린미해결. 145tests·14hash·독립DP검산200·새ML0·제품미채택·추가사용자입력없음.

W14평가/API/fixture, W13main/몸/구간/mapping/crop/제품adapter 소유 유지. 이 시간정책은 artifact 전용이며 public API/core/제품/의존성변경0. 시간칸은 통계적독립성보증아님,관측칸수는승자지지칸수와다름. 같은trackID/연속몸이 잘못된얼굴점수를 정답으로만들지않음. 후속회귀에혜인오배정4/기존정답손실/실제전환누락을고정. 계약상호확인→consumer호환→선택venv/모델준비→Macarm64/Windowsx64→합의merge순서유지. 새W13수락/채팅발신/commit/push없음.

## 2026-10-14 사용자 메인 정답2건 — 참조보충/교차모델 veto 미채택

[결과·실제검증·남은작업](../10/14-w14-confirmed-main-errors-and-opposition-result.md). 사용자가105.105초 해린/25.759초 다니엘을 확인. source-main exact2개로 기록하고 기존34얼굴GT/주변/whole-clip로 전파하지 않음. s0058하니 배정은 확인시점과 모순,1544해린은 기존연결근거에서 오판정. 모델반대시보류는 SFace16→14/Aura15→12·다니엘/혜인 근거까지손실·1544오류잔존으로 미채택. 같은 gallery 문턱강화도 기존정답 손실반례 확인. 120tests·15+3hash·독립검산/UI·새ML0. 답변대기해소·제품개선/교체완료아님.
W14 평가/API/fixture, W13 main/몸/구간/mapping/crop/제품adapter 소유. core/API/제품/의존성변경0. 계약상호확인→consumer호환→선택venv/모델준비→Macarm64/Windowsx64→합의merge 유지. 반대모델거리/embedding혼합금지, 단순1위/미관측을타인근거로승격금지. 새W13수락/채팅발신/commit/push 없음. 아래 답변대기는 이전이력이다.

## 2026-10-14 신규 배정의 원본·단일 참조 민감도 — 제품 보류 유지

[결과·실제검증·미확인](../10/14-w14-reference-continuity-and-sensitivity-result.md). 고정40B의101crop/33원본을 확인. s0043는 보라메인 연속/기존혜인GT9, s0058는 같은초록메인이나 SFace해린/Aura하니 충돌·GT없음. 25초 해린2는 같은노란메인 얼굴 선택 상태의 인식판정 흔들림 근거. 연결/main 오류로 단정하지 않음.
추가8참조 하나씩제외(기준선포함9×2)에서 s0043/s0058배정은 특정사진에 의존. 우수사후조건은 채택하지 않음. 706기준선재현·113/83입력hash·109tests·독립감사·새ML0. GT34/제품/core/W13변경0. 현재질문은105.1초초록/25.76초노란메인의 이름2개; 새GT0, 답변대기.
W14평가/API/fixture, W13main/몸/구간/mapping/crop/제품adapter 소유와 기존 merge/compatibility 순서 유지. 이번 audit는 제품연결/새W13수락 아님. 사용자 답변을 받은 후 오배정 여부를 별도 기록하고 후속 개선 범위를 정한다.

## 2026-10-14 교차 영상 참조 보충 — 평가후보·제품 미채택

[결과·검증·한계](../10/14-w14-cross-video-reference-append-result.md) · [전후 비교](http://127.0.0.1:58261/face-reference-comparison-v1/index.html).
고정40B/353저장관측, 원래23참조+다른영상 사용자확인8개. query 영상 전체를 추가참조에서 제외. 참조만보충시 기존민지정답1손실; 원래확정도보존/충돌유지하는 별도평가에서 GT34 SFace18→20/Aura19→21·오확정0·기존정답손실0. 메인배정16→16/13→15·기존배정손실/개명0. Aura s0043혜인·s0058하니 추가이나 클립전체GT없음. 25초대충돌지속. 별도문턱검증/독립main평가 없이 제품교체하지 않음.
두 gallery fingerprint를 별도 보존한 평가 전용 schema이며 core ReferenceMatch/동일gallery 검사/공개API는 변경하지 않았다. W14평가/API/fixture, W13main/몸/구간/mapping/crop/제품adapter 소유 유지. 계약확인→소비호환→선택venv/모델준비→Macarm64/Windowsx64→합의merge 순서. W13새수락/다른세션코드변경/채팅발신/commit/push 없음.
새ML0·774기존판정재현·109tests·독립감사·원본UI검증. 초안invalid-veto 오류는 보존/수정했고 사유를 기록. 다음은 신규 배정 근거/25초대 잔여충돌과 별도영상 적용 검증. 현재사용자추가입력없음.

## 2026-10-14 현재 유지40B 소비자 연결 — 제품 모델교체 보류

[결과·실제검증·한계](../10/14-w14-current-dance-face-comparison-result.md) · [클립 비교](http://127.0.0.1:58261/dance-main-comparison-v1/index.html).
W13 40B 스냅샷58구간/35대상/37run을 읽기 소비. exact frame/body+동일pose pool로 기존353관측 재사용, 중복127제거/현행군무1제외. 공통모듈 rebind 후706얼굴판정재현. SFace16/Aura13배정, GT34얼굴정답18/19·오확정0. 새ML0·29tests·독립리뷰/UI; 전체구간정확도/제품승인아님. Aura우선시험 결과로 단순교체 보류. 현재 입력에없는332시점 새추론없음.
W14 평가/API/fixture, W13 main/몸/구간/mapping/crop/제품adapter 소유 유지. 기존 core/공개API 변경0. 계약상호확인→source/time/coords/scope/failure 호환→선택venv/consumer→Macarm64/Windowsx64→합의merge. 이번결과는W13 새수락이나프로덕션연결아님. 다른세션파일변경/채팅발신/commit/push없음.
다음은 순간충돌25.759/25.826초 및57~59초 무확정의 입력/인식/합의원인에한정. 단순다수결/threshold완화/다른경로이름전파는채택하지않음. 사용자추가입력현재없음.

## 2026-10-14 W14 추가12얼굴 정답 수신 — Aura 연결시험 우선

[결과·근거·한계](../10/14-w14-holdout-clear-face-comparison-result.md) · [비교화면](http://127.0.0.1:58261/holdout-clear-results-v1/index.html).
사용자12/12식별가능·멤버5명포함. 기존36저장예측채점: SFace10/0/2, Aura12/0/0, Intel9/0/3(정답/오확정/보류). 기존22포함식별가능19는15/17/12정답·오확정0. 새ML0·80tests·180거리/36판정/12집계검산·독립리뷰/UI.
다음안무main연결시험은Aura우선/SFace대조. 선명얼굴선별·같은두영상·혜인/민지각1개이므로제품교체/원래혜인난구간해결아님. 이번입력에W13main/track/구간없음; 얼굴GT를mainGT로전파금지. 사용자추가입력요구없음.
W14평가/API/fixture, W13main/몸/구간/mapping/crop/제품adapter소유. core/API/제품소비adapter는불변. sourcehash·시간·좌표·scope·실패호환을고정한소비평가→선택venv→Macarm64/Windowsx64→합의merge유지. 새W13수락/채팅발신/commit/push아님.

## 2026-10-14 W14 추가영상 얼굴12개 준비 — main/구간 평가 아님

[실행·검증·한계](../10/14-w14-holdout-clear-face-preparation.md) · [사용자 얼굴확인](http://127.0.0.1:58261/holdout-clear-review-v1/index.html).
기존두영상4분/240프레임·1080검출 보존,새YuNet232회.48후보 가시성 점검→28→12확인자료,모델점수로선택하지않음·제품필터아님. 기존23참조/3모델/정렬/threshold고정각12추론36성공. GT대기·정확도없음,144tests·180거리/36판정검산·QA/사용자export격리·독립리뷰. 이전22답변 별도원문hash보존,새12export와자동병합하지않음.
두source에 저장된W13main/track/segment없음. 사용자가 답할 것은 얼굴이름/식별가능 여부12개이며 finalclipGT아님. 향후sourcehash/시간/좌표가일치하는 고정W13출력+선택인물GT로 제품연결을평가해야함. 최신W13평가·모델교체·제품적용아님.
공통core/API/제품adapter불변. W14평가/API/fixture, W13main/몸/구간/mapping/crop/소비adapter소유. 계약상호확인→시간/좌표/scope/실패호환→선택venv/소비adapter→Macarm64/Windowsx64→합의merge 유지. 채팅발신·새상호수락·commit/push없음.

## 2026-10-14 W14 수동 위치점 진단 — 제품 미채택

[결과·실행·한계](../10/14-w14-manual-landmark-diagnosis-result.md) · [원본 위치/전후 입력](http://127.0.0.1:58261/manual-landmark-v1/index.html).
같은12GT얼굴에서 정답확정 SFace4→4/Aura5→7/Intel3→2,오확정0. Aura 새혜인확정도 ±2px20조건 중10보류로 불안정.
수동추정55점/가림5점유지이며 전문가GT/자동정확도 아님. 새인식136회(최종112+보존초안24),204tests·560거리/112판정/36증거쌍 검산·독립리뷰/UI.
모델/등록23사진/정렬공식/threshold 고정. embedding공간은같고 query geometry/config/adapter/evidence/cache key는분리.
정렬공식/template를 바꾸면 별도 공간/참조재생성 여부를 검토해야 한다. 수동 위치점을 자동 검출 결과처럼 캐시하지 않는다.
공개 API/core/제품adapter는불변. 다음은추가영상 식별가능 메인얼굴과자동경로 비교;명확하지않은 배경 라벨추가는우선하지않음.
W14평가/API/fixture, W13main/몸/구간/mapping/crop/제품adapter소유. 계약상호확인→시간/좌표/scope/실패호환→선택venv/소비adapter→Macarm64/Windowsx64→합의merge 유지.
최신W13평가·새상호수락·제품적용·채팅발신·commit/push아님.


## 2026-10-14 W14 혜인 참조 평균/개별 사진 진단

[결과·검증·한계](../10/14-w14-hyein-reference-attribution-result.md) · [실제 얼굴과 등록 사진](http://127.0.0.1:58261/hyein-reference-v1/index.html). W13-35 고정 native4K 특징354관측/34멤버GT를 재계산했다. 앞 혜인5개 점수1위 정답은 평균→최근접 SFace2→1/Aura4→2/Intel0→0; 단순 참조변경 미채택. 앞33은27인식+6연결보류, SFace 후보차이 제거는2정답+2오확정. 새ML0·192tests·37,779거리/1,443원본match 검산·독립리뷰/UI. 제품 전체suite는 평가venv의 clipper_video_render 누락으로 수집불가.

공통 core/공개API/소비adapter 변경 없음. 순위 비교에 기존 평균용 threshold를 재사용하지 않았다. W14 평가/API/fixture와 W13 main/몸/구간/mapping/crop/제품adapter 소유권 유지. 다음은 정확한 얼굴 위치점 오차/정렬 영향 진단. 기존 계약상호확인→시간·좌표·scope·실패호환→선택venv/소비adapter→Macarm64/Windowsx64→합의merge 순서 유지. 최신 W13 평가·수락·제품적용·채팅발신 아님.


## 2026-10-14 W14 경로별 표본 보충 — 제품 정책 미채택

[실제 비교·근거·한계](../10/14-w14-per-run-face-topup-result.md) · [회복/충돌 비교](http://127.0.0.1:58261/run-topup-v1/index.html). 고정 W13-35의 저장5범위/7경로/238관측에서 기존3개를 보존해6→9로 보충했다. 시간대별 SFace 다니엘·민지와 Intel 민지가 회복됐지만 SFace 기존 간격 선택보다 최고 결과가 좋아진 것은 아니다.9개 추가회복0, 모든 제한 SFace 선택이 전체의 하니 반대판정1개를 놓쳐 제품정책 미채택. 혜인 앞33표본도3모델확정0. 새ML0·180tests·3,135거리/252경로/180비교 검산·독립리뷰/UI확인. 제품 전체suite는 평가venv의 clipper_video_render 누락으로 수집불가. 다음은 남은 인식실패/충돌 분리; 사용자필수입력없음.

표본 보충은 공개 얼굴 API에 넣지 않고 소비자의 비용/정확도 정책으로 둔다. 기존 실패/반대 근거를 보존하고, 관측 없음과 타인 지지를 구분한다. 공통 core/공개계약/제품/W13 파일 무변경. W14는 평가/API/fixture, W13은 main/몸/구간/mapping/crop/제품adapter 소유. 계약상호확인→시간/좌표/scope/실패호환→선택venv/소비adapter→Macarm64/Windowsx64→합의merge 순서 유지. 이번은 W13 수락·제품적용이나 채팅 발신이 아니다.


## 2026-10-14 W14 몸 경로별 소비 계약 구현·비교

[결과·실제검증·한계](../10/14-w14-run-scoped-face-contract-result.md) · [구간 이름 근거 비교](http://127.0.0.1:58261/run-scope-contract-v1/index.html). 고정 W13-35의 저장 얼굴로 몸 경로별 합의를 구현했다. 뒤쪽 얼굴 근거로 앞 경로까지 이름을 채우지 않고, 빈 경로/실패/다른 멤버 근거를 보존한다. 339비교 중4개는 전체이름→확인필요; 뒤혜인근거는 유지. 희소 SFace 다니엘 추가보류1도 있어 정확도개선/제품채택을 뜻하지 않는다. 새ML0·기존match1,443개재현·거리6,300/경로363검산·165tests·독립리뷰·원본UI확인. 다음은 경로별 표본보완과 잔여충돌/인식실패 분리. 사용자필수입력없음·제품/core/W13보존.

계약 상세/fixture는 W14 Python worktree `evaluation/segment_review/RUN_SCOPE_CONTRACT.md`, `run_scoped_matching.py`, `test_run_scoped_matching.py`. W14는 평가/API/fixture, W13은 main/몸/구간/mapping/crop/제품adapter 소유. 공개 core는 그대로이며 BodyRun을 공개 API에 추가하지 않음. 원래→경로scope fingerprint 대응·빈 예정경로·관측없음/충돌분리·참여자별scope 필수. 같은trackID는 동일인 보증 아님. 계약상호확인→좌표/시간/scope/실패호환→W13소비adapter/선택venv→Macarm64/Windowsx64→합의merge 순서유지. 새 W13 수락/제품적용/채팅발신 없음.

## 2026-10-14 W14 시간순 근거 진단 — 충돌·무근거 경로 분리

[결과·실행·한계](../10/14-w14-temporal-face-evidence-result.md) · [시간순 얼굴/메인 비교](http://127.0.0.1:58261/face-temporal-evidence-v1/index.html). 고정 W13-35의 5범위/238시점을 기존3모델로 채웠다. Aura25.759/25.826초 연속 해린판정과 같은 몸의 이동 근거, 혜인 앞경로33확정0/뒤경로28확정을 분리했다. 단순LK는 실제전환에서 근거부족이므로 미채택. 새검출99+인식294, 관련109tests·3,135거리/21경로/237관계 검산·독립리뷰·원본UI확인. 전체suite는 평가venv의 clipper_video_render 누락으로 수집불가. 전체정확도/제품적용 미완료. 다음은 구간과 몸경로별 근거를 분리하는 소비scope 계약. 사용자 추가조작 없음·제품/core/W13 보존.

공통 core는 소비자가 동일인이라고 선언한 scope를 합의한다. 합쳐진 안무 구간에 얼굴 무근거 경로가 있으면 다른 경로의 이름으로 자동 채우지 않는 계약이 필요하다. 같은 track ID도 동일인 보증은 아니며, ID 변경도 타인 보증은 아니다. W14 평가/API/fixture, W13 main/몸/구간/mapping/crop·소비adapter 소유와 기존 merge 순서를 유지한다. 이번 결과는 W13 수락이나 제품적용 승인이 아니다.

## 2026-10-14 W14 입력 안정성 규칙 검증 — 단순 제외 미채택

[결과·반례·재현](../10/14-w14-face-input-stability-result.md) · [규칙 비교 화면](http://127.0.0.1:58261/face-input-stability-v1/index.html). 저장두입력에서‘양쪽확정’은Aura혜인구간을회복하지만이미알아본타인근거도지움(Aura19인위적조합/민지얼굴1개,식별가능만15). 충돌보존은이위험을막지만원래구간보류;1위일치도해결미완료. 식별가능28얼굴의동일인/타인거리가겹쳐단일거리기준도불충분. 새ML0·71tests·1458조합/1308범위/38052control/2208거리검산·독립리뷰·완전재현. 다음은고정메인경로안의시간적얼굴근거와실제타인전환구별. 사용자필수입력없음·제품/core/W13보존.

소유권유지: W14평가/API/fixture, W13main/mapping/crop/소비adapter. 입력불일치로보류하더라도원래반대멤버근거를지우지않는계약이필요하다는검사결과다. 새API수락·제품적용아님. 기존compatibility→선택venv/adapter→양OS→합의merge순서유지.

## 2026-10-14 W14 얼굴 위치·정렬 민감성 비교 — 전면 적용 미채택

[실행·수치·남은 작업](../10/14-w14-native-face-conflict-result.md) · [전후 얼굴·클립 비교](http://127.0.0.1:58261/native-face-input-v1/index.html). 같은4K픽셀에서YuNet 위치/5점만재검출. GT34 정답 SFace16→18/Aura18→19/Intel7→10·오확정0, 다만Aura기본구간15→14와연결4손실.57–63초Aura28:1충돌→혜인28만이나58.125초는해린1위유지·경계값보류여서인식해결아님.25.759초새해린충돌도공개. 새검출214/인식633,62tests·3165거리/327판정·독립리뷰·원본재생확인. 전체품질/제품적용미완료;다음은입력불안정성과실제타인혼입을구분하는검증. 사용자필수추가입력없음. W13-35고정snapshot·core/제품/W13보존.

소유권/merge순서 유지: W14공통API·평가/fixture → 시간·좌표·실패/scope compatibility → W13소비adapter·선택venv/모델준비 → Macarm64/Windowsx64 → 합의merge. 이실험은제품소비요청/새상호수락아님.

## 2026-10-14 W14 4K 얼굴 간격 선택 — 혜인 구간 회복 후보

[결과·검증·한계](../10/14-w14-native-face-sampling-result.md) · [멤버/클립 비교](http://127.0.0.1:58261/native-face-sampling-v1/index.html). 같은 4K 입력·모델·99슬롯에서 간격 선택을 비교했다. SFace 배정14→16, Aura14→15이며 기존 배정을 유지했고, Intel9→7로 회귀했다. Aura의57–63초 구간은 혜인 근거2개로 배정되지만 직접GT가 없는 표본이며, 전체얼굴 진단에서는 혜인28/해린1 충돌로 보류된다. 부분GT와 전체구간 정답을 구분하며 모델교체·제품통합은 미완료다. 새516추론·91tests·3,225거리/324구간검산·독립리뷰·원본재생 확인. W13-35 고정입력, 제품/core/W13 보존. 사용자 필수 추가입력 없음.

W14는 공통 API/평가/fixture, W13은 main·몸/구간·mapping/crop·소비 adapter 소유를 유지한다. 이번 선택정책은 평가 전용이고 공통 API/제품 소비 변경 요청이 아니다. source/hash·시간/축별좌표·실패/scope compatibility → 선택venv/소비adapter → Macarm64/Windowsx64 → 합의 merge 순서 유지. 신규 상호수락 없음.

## 2026-10-14 W14 57–63초 진단·실제4K 원본 비교

[원인·실행·한계](../10/14-w14-main-face-native-source-diagnosis.md) · [비교 화면](http://127.0.0.1:58261/native-source-faces-v1/index.html). 같은GT34얼굴에서 기존1080→실제4K 정답 SFace9→16/Aura8→18/Intel1→7,4K오배정0. SFace기존정답2개미매칭회귀,Aura기존8보존. 단순확대대조·3모델각86추론·1290거리검산·119tests·독립리뷰·원본재생확인. 문제의혜인9는SFace0→0/Aura0→3/Intel0→0; Aura정답3시점이자동선택에없어구간미매칭유지. W13-35고정입력·메인/소비코드보존. 고화질입력+표본선택을후속우선,모델교체/제품통합은미완료. 현재추가사용자입력없음.

W14평가/API와W13main/mapping/crop소유권유지. 서로다른해상도source를연결할때source hash·실제크기·PTS·축별bbox/landmark변환을검증하는fixture가필요하다. 분석source와preview/exportsource를분리표시하고자동교체하지않는다. Nest최고화질의H.264우선은조사근거이며이번수정/merge없음. 기존공통API→compatibility→선택venv/소비adapter→양OS설치검증→합의merge순서유지. 새상호수락아님.

## 2026-10-14 W14 안무35 고정·얼굴 선택 비교 및 보완안

[실제 실행·결과·미검증](../10/14-w14-main-face-quality-sampling-result.md) · [멤버/클립 비교](http://127.0.0.1:58261/main-face-quality-v1/index.html). 649프레임/678메인관측을기존YuNet으로검출,3모델각158얼굴비교. 같은99표본에서사용가능얼굴80→89, SFace범위배정8→13이나하니회귀1로전면교체미채택. 기존+보완156표본의사후계산은15배정·기존8보존(추가7전체정답미확인). 동일GT34개정답9/8/1·오배정0/0/1, 혜인정답0으로모델교체/제품적용미채택. 183tests·2370거리/216기본판정검산·독립리뷰·원본재생UI확인. W13 snapshot35/read-only, 공통core/제품/다른세션보존. 다음은보완안잔여21범위의명확한메인얼굴과57–63초연결·인식실패분리, 별도영상고정main/구간GT검증. 현재사용자추가입력요구없음.

W14평가/API소유, W13main/mapping/crop/소비adapter소유유지. source_track_runs+실제observed boxes소비, joint분리·실제pose보충fixture준비. bodyrun동일인/실제shot보장미확인. 공개계약/fixture→시간·좌표·scope·실패compatibility→선택venv/소비adapter→Macarm64/Windowsx64→합의merge순서유지. 새상호수락·배포승인아님.


## 2026-10-14 W14 종합 정리 — 후속 실험 전 문서화

[전체 이력·현재 계약/통합 경계](../10/14-w14-face-matching-work-summary-and-decision-status.md). 모델별 실제 실행/조사만 한 후보, Person 시기부터 공통 얼굴 모듈·안무 매칭까지의 실험·성과·기각 이유·남은 검증을 종합했다. 공통 core 0.2와 평가 adapter 구현은 있으나 **전체 안무 구간 매칭 품질 개선·제품 통합·최종 모델 선택은 미완료**다. YuNet/SFace는 당분간 비교 기준으로 유지하고 Aura/Intel0095/기존 ArcFace의 제품 교체는 채택하지 않는다. 최근 식별어려운 7개 전부 보류는 인식 개선이 아니며, 다음은 고정된 W13 메인에 연결된 식별가능 얼굴·구간 정답을 우선 확보해 비교한다. 기존 사용자 답변과 결과는 보존하며 이번에는 새 ML·모델 설치·제품 코드 변경 없이 문서만 정리했다.

W14는 공통 얼굴 API·평가·fixture, W13은 main/구간/몸·기존 mapping/crop·제품 소비 adapter를 소유한다. W14가 소비한 iteration27은 고정 snapshot이며 이후 W13 결과를 평가했다고 해석하지 않는다. 공개 계약/fixture → 동일인 범위·실패·시간/좌표 compatibility → 소비 adapter/선택 venv·모델 준비 → Mac arm64/Windows x64 설치 검증 → 합의한 병합 순서 유지. 이번은 새 소비 계약 수락·제품 이식 요청이나 배포 승인 기록이 아니다.


## 2026-10-14 추가 답변7개 수신·22개 통합 비교 완료

[결과·검증](../10/14-w14-holdout-coverage-comparison-result.md). 사용자7/7원문·provenance 검증, 기존15보존. 추가멤버4/등록외3은모두식별어려움이며 기존3모델각7회(총21회)로비교했다. 새7개모두보류, 전체멤버11개 시험배정정답 SFace5/Aura5/Intel3·오배정0·보류6/6/8. 식별가능7개는5/5/3정답, 등록외5모두보류. 수동영상참조최근접8/3/7로교체근거없음·미채택. 34tests/330+1533거리/독립리뷰·UI확인. 혜인GT0/식별가능하니0, 전체구간·패키징미검증. 현재사용자추가입력없음. 제품/core/W13불변. 아래7답변0·대기항목은이전준비이력이다.

W14평가/공통API·fixture, W13main/mapping/crop소유유지. 공개계약·fixture→scope/실패compatibility→소비adapter/선택venv→Mac arm64/Windows x64→합의merge순서유지. 이번은소비계약/제품통합변경없음.


## 2026-10-14 특징 구별 진단·추가7개 — 소비 변경 없음

[근거·미검증·입력대기](../10/14-w14-face-separation-and-coverage-result.md). W14평가산출물만추가. 저장3모델최근접진단은수동참조정보포함,최신34정답25/24/26으로교체미채택. 47,790거리/38hash/독립리뷰·UI확인. 기존추가영상15GT에없는7검출얼굴을별도확인준비(정답0,ML0);사용자확인후평가전용으로사용. main선정/물리적scope전체GT아님.

public core/API/SDK/W13 main·mapping·crop·adapter불변. W14공개계약/fixture→W13scope·실패compatibility→소비adapter/선택venv→Mac arm64/Windows x64패키징→합의merge순서유지. 추가영상혜인·하니GT/unknown거부·최종scope·제품통합은여전히미검증.

## 2026-10-14 참조 영향 진단 — 변경 소비 요청 없음

[실제 비교·미채택](../10/14-w14-reference-domain-diagnosis-result.md). W13 iteration27에서이미고정한선택얼굴/SFace특징재사용,새ML0. 자동영상참조는혜인0개·최신34오확정3,수동GT참조도오확정1/추가영상악화로미채택. 단순margin제거도오확정3. 178tests/4,185거리/21gallery/20hash·독립리뷰/UI확인.

W14평가helper/리포트/기록만변경; public core/기본SDK/W13 main·mapping·crop·adapter무변경. 기존얼굴GT를scope전체로전파하지않음. W14공개계약/fixture→W13동일인scope·실패compatibility→소비adapter/선택venv→Mac arm64/Windows x64→합의merge순서유지. 새상호승인/제품통합완료아님. 혜인분리·별도calibration/평가·최신upstream소비는남아있음.

## 2026-10-14 동일 iteration27 메인 얼굴·세 인식 모델 비교

[실행·검산·교체미채택](../10/14-w14-latest-main-model-comparison-result.md). W13 메인/선택얼굴129·참조23·42범위 고정. SFace캐시/Aura129/Intel129새추론, 얼굴연결보류32보존. 연결된34얼굴 정답확정9/8/1·오확정0/0/1, 혜인정답확정모두0. Intel 혜인→해린은개별얼굴오류이며구간전체는보류. 전체42범위배정은기존→결합 SFace12→18/Aura8→11/Intel6→7이나전체범위GT아님·미채택.

W14평가adapter/검산/리포트만수정,public core/기본SDK/W13 main·mapping·crop·제품adapter불변. 170tests/189hash/2,045거리/126정책·독립리뷰검산누락1수정. 원래선택얼굴/사용자GT/다른모델공간혼용없음. W14공개계약/fixture→W13동일인scope·실패compatibility→소비adapter/선택venv→Mac/Windows패키징→합의한merge순서유지. 이번에새계약상호수용·제품통합완료를뜻하지않음. 최신upstream변화/전체구간GT·혜인/하니독립평가/Windows미검증.

## 2026-10-14 최신 W13 iteration27 소비 평가 연결

[실제 연결·검산·미채택](../10/14-w14-latest-dance-face-pipeline-result.md). W13 iteration27 combined frames/segments + 동일pose cache 읽기전용.70구간→42 segment×main범위,joint2scope/group·unknown이름없음,다른구간같은track숫자합침없음. 실제shot/물리적동일인보증아님.

YuNet158/SFace129회,새자세추론0.개별12/결합18배정이나추가6개GT없음·부분GT14범위7일치/7보류동일로미채택. 기존얼굴GT는정확한frame/위치만연결,main/전체scope truth전파없음.111tests/47hash/690거리/129픽셀/42정책검산.

W14평가adapter/리포트만변경,publiccore/W13 main·mapping·crop·adapter불변. 저장출력연결완료,제품통합/전체정확도/Windows미검증. W14공개계약/fixture→W13동일인scope·실패compatibility→W13adapter/선택venv→병합순서유지. 신규6배정정답/혜인분리력/shot·track계약이남음.

## 2026-10-14 새 영상 사용자 정답 및 인식 비교

[실행·검산·선택얼굴 결과](../10/14-w14-holdout-recognition-result.md). 사용자15GT(멤버7/등록외2/불명5/비얼굴1) 수신, source/PTS/bbox/ID 검증. 모든15개를 SFace/Aura/Intel 각1회 추론하고 기존 개발자료의 모델별 centroid 거부 기준을 고정했다. 시험배정 정답5/5/3, 보류2/2/4·오배정0. 7멤버만으로 전체 품질/낮은FAR 보장 불가, 혜인GT0. 신규모델교체·제품 적용 없음.

W14 평가파일만 추가했으며 public core/API와 W13 main/track/구간/crop 소비자는 그대로다. 얼굴GT를 메인선정GT/동일인track 전체로 전파하지 않는다. W14 공개 계약/fixture → 최신 W13 source·동일인 scope·실패 상태 compatibility → W13 adapter/venv 검증 → 병합 순서를 유지한다. 이번39tests/225거리 재현은 최신 안무 최종분류 호환성/정확도 보장이 아니다. 최신 W13 출력 결합·Windows 패키징 미검증.

## 2026-10-14 새 영상 얼굴 정답 준비

[고정 입력·실제 검출·확인 화면](../10/14-w14-holdout-face-review-preparation.md). 새 두 영상의 8프레임에서 YuNet 22검출/첫 사용자 확인 15개를 준비했다. 새 인식 추론과 사용자 GT는 0이며, 이 자료는 W13 메인 선택의 정답이 아니다. 얼굴 ID/source hash/PTS/bbox와 등록 외/판단 어려움/얼굴 아님/식별 여부를 보존한다. QA export는 사용자 GT와 origin/pathname으로 분리했다. 미검출·검출 오탐도 인식 거부와 분리한다.

이번 소유 범위는 W14 평가 코드/화면뿐이다. 공통 API 및 W13 main/track/구간/crop 소비 코드 변경 없음. W14 공개 계약/fixture → 최신 W13 동일인 scope·얼굴 연결·실패 상태 compatibility → W13 adapter/venv 검증·병합 순서 유지. 새 영상의 최신 W13 출력 결합과 Windows 실기는 미검증이다. 사용자 얼굴 정답을 track/구간 전체에 전파하지 않는다.

## 2026-10-14 입력 해상도·정렬 대조 — 소비 코드 변경 없음

동일SFace/선택얼굴/128사용자GT에서기존93정답→참조42px91/두눈정렬81. 식별가능102기준82→80/72이며회귀3/12개로둘다미채택. 참조42px는기존산출물재사용,두눈정렬은참조23+query128모두동일변환으로151새추론. [범위·근거·검산·후속](../10/14-w14-face-input-ablation-result.md). 기본5점경로유지. W13main/track/구간과공통API에변경없으며실험config/cache를소비adapter에넣지않는다. W14→compatibility fixture→W13merge순서유지. 새두영상의고정메인출력/얼굴GT·통합검증미확보. 이번26tests/1,920거리·151행렬검증은안무최종정확도보장이아니다.

## 2026-10-14 참조·원본입력 진단 후속

[9조건·151원본 재현·GTscope감사](../10/14-w14-gallery-diagnosis-and-input-replay.md). SFace 참조2장방식은기존정답4회귀·혜인개선없어미채택. 저장특징151/표시얼굴128개원본재현확인. 사용자GT의23개segment/track중6개에둘이상의선택얼굴정답이있음(clip2/2,3/3,8/9,9/12,16/20,16/19). 몸추적/얼굴연결중어디에서대상이바뀌었는지는단정하지않음. 같은track이라는이유로얼굴GT/identity전파금지유지. W13 코드/공통API/병합순서불변, W14 후속은입력전처리분리대조.

## 2026-10-14 사용자 선택 얼굴GT 수신

[수신·대조·실제 한계](../10/14-w14-user-face-labels-and-candidate-scores.md). 기존선택얼굴에 대한 사용자135기록/멤버128개 확보, main구간GT로 전파하지 않음. 식별가능102개 점수1위 SFace82/Aura73/Intel67로 신규모델 단순교체 미채택. 기준선도 혜인/해린 혼동이 남음. 새ML/공통API/제품/W13변경0. 관측/track/구간 경계·소유권·merge순서 불변. 독립영상과 최종구간 매칭평가는 미완료.

## 2026-10-14 후보 비교 UI 후속

[사용 안내·재생 검증](../10/14-w14-candidate-review-playback-fix.md). 평가 정답/모델 목록 구분, 최초19얼굴 안내, SVG static박스 숨김/구간 재재생/미디어 복구만 수정했다. saved body_box는 한 시점이며 연속 추적 결과로 표시하지 않는다. 공통 API·W13 소비자·모델 결과·파일 소유권·merge 순서 불변. 새ML0/사용자GT0. 검은 화면은 reload 복구 확인, 브라우저 내부 원인 미확정.

## 2026-10-14 후속 — 승인된 격리 후보 실행

[실행·파일·화면·한계](../10/14-w14-candidate-runtime-and-face-review.md). W14 기존worktree의 `evaluation/candidate_comparison`에만adapter 추가, core/SDK/plugin/기존venv·lock/W13변경 없음. AuraFace ORT/0095 OpenVINO Apple M4 CPU 각smoke1+본426성공(참조23/얼굴403),3정렬오류/36미검출/9연결보류 보존. SFace는406캐시. 6,060거리 재검산과116관련테스트, GT노출이력 수정검증 수행. 영상정확도/threshold/구간최종분류 미확정. 0095는모델문서정렬, 기본OpenVINO import telemetry를 제품시 반드시 제어. 평가full은공식CI옵트아웃확인. ORT선택wheel macOS14+이나제품OS정책상향안아님;Windows미검증.

새2영상1080p hash/240actualPTS preview 확보,얼굴ML0. 이 영상의 최신W13메인/track/source계약은아직없다. 처음요청할GT는기존클립별선택얼굴19개이며main구간전체재라벨링이아니다. W14공통인식API/manifest/선택의존성확정→W13 adapter compatibility·실기→병합순서유지. 공개API승격·제품통합·새세션·세션메시지없음. 아래 설계단계의다운로드/ML0은당시이력이며현재상태는이후속기록을따른다.

## 2026-10-14 신규 인식 후보 비교 설계 인계

후속: 두 공개 페이지를 직접 확인해 각30~60/80~110/125~155/165~195초를 평가 창으로 선정했다. [준비 기록](../10/14-w14-holdout-input-preparation.md). 새 영상의 W13 메인/track 출력은 아직 고정되지 않았으며, 단일 얼굴 인식 시험을 전체 안무 분류 성능으로 계산하지 않는다. 원본 PTS/hash/GT와 소비 계약은 실행 전 잠금 대상이다. 다운로드/ML/코드 수정 없음.

사용자가 추가 평가 영상 `J9DlrnNlgfE`(백댄서 다수), `6bVUjsUi9sw`(멤버5명)를 제공했다. 두 영상은 기준 튜닝에 사용하지 않는 독립 평가 후보이며 각120초 이하를 제안한다. W13 선택 메인 얼굴의 분류와 별도 등록 외 얼굴 거부 시험을 구분한다. 실제 촬영/참조 중복·평가 구간·GT·최신 W13 출력 계약은 미확정이며 영상 다운로드/추론은 시작하지 않았다. 사용자에게 추가 영상을 더 요청할 필요는 없다.

[실행 전 시험안](../10/14-w14-recognition-candidate-evaluation-design.md): SFace 대조군에 AuraFace-v1/face-reidentification-retail-0095 후보를 두며 0009 정렬은 별도 후속이다. 이번은 조사·문서 갱신만, 다운로드/설치/추론/제품·평가 코드 수정0. macOS는 Apple Silicon arm64만 지원한다.

W14는 기존 저장 관측의 bbox/5점과 얼굴 선택을 고정해 인식 모델 효과부터 비교한다. 현재 공개 OpenCV backend는 검출/특징 추출이 결합돼 있으므로 관측/인식 adapter 분리는 후속 설계 대상이며 이미 구현됐다고 가정하지 않는다. 기존 gallery/match/consensus·provenance 계약은 재사용한다. W13의 main/몸 추적/구간/crop 소유와 기존 파일을 유지한다.

사용자 시간대 main 정답은 실제 선택 얼굴 정답이 아니다. W13 최신 출력과 결합할 때 source/code/model SHA, 얼굴 소유 상태, 동일인 scope와 전환/실패 의미를 고정해야 한다. 옛 MoveNet 20구간의 7범위 수동 감사표를 최신 W13 자동 규칙으로 이식하지 않는다. 순서는 W14 공통 API/입력 fixture → W13 최신 출력 compatibility → W13 소비 adapter/venv 검증. 후보 선택이나 이 문서가 W13의 신규 adapter 계약 수락·제품 채택을 의미하지 않는다.

## 2026-10-14 W14 동일인 범위 계약·판정 규칙 미채택 인계

저장된 옛 MoveNet512 메인20구간/451몸 표본 감사에서 클립2/3/8/9/16의7범위는 같은track ID 안에서 다른 몸으로 바뀐다. IoU 유일 최고 연결도 클립2의 노란옷→보라색옷 전환을 통과했다. **동일 시점의 얼굴↔선택 몸 연결과 여러 시점의 동일인 연속성은 별도 계약이다.** 이는 최신W13 오류 판정이나 메인으로 누가 적합한지의 GT 채점이 아니다.

W13 소비자는 main 역할/segment ID와 물리적 동일인 scope를 구분하고 전환·연결불확실·관측실패 근거를 전달해야 한다. W14는 단순track번호만으로 같은 사람이라고 가정해 얼굴을 평균/다수결로 합치지 않는다. 평가용 수동7범위 차단표는 자동전환 탐지나 제품 예외처리가 아니다. 공통 query/match DTO·core는 이번에 변경하지 않았다.

점수차이+시간지지 평가 wrapper를 같은저장406얼굴에 대조했으나 ArcFace 클립10 혜인→보류 회귀로 **채택하지 않는다**. SFace10→12/ArcFace10→6은 정확도 아님. 새ML0.107관련통과,651회귀통과/3skip/11모델부팅제외,참조230/query8,120거리·96track/80segment 검산. [실제 증거·한계·v5](../10/14-w14-margin-consensus-and-scope-audit.md).

소유: W14 `evaluation/segment_review`의 감사/consensus 대조/fixture/UI, W13 main/추적/구간/crop·제품 adapter 유지. merge 순서: W14 공개 API/fixture → 최신 W13의 동일인 scope·소유권·실패 상태 compatibility → W13 소비. 최신 출력 연결/호환 검증·상호 새 계약 수용·merge 미완료. 기존 소유권을 덮어쓰지 않으며 다른 세션 메시지/새 세션 생성0.

## 2026-10-14 W14 실제 표본 수집 재평가 인계

저장된20구간과 W13 메인/몸/pose는 보존하고 평가 adapter의 경로별 얼굴 수집을 수정했다. 클립19 끝에만 붙은 추적24는 `[start,end)` 밖이므로 합의 대상에서 제외한다. 클립20 끝 기록도 제외하지만 안쪽 추적24는 유지한다. 공통 core가 모든 bboxes를 자동으로 같은 사람이라고 취급하지 않도록 소비자에서 유효 경로/scope를 지정해야 한다. 같은 경로·원본frame 중복 표 금지, 첫/중간/끝 실제 몸 기록을 포함하며 reserve는 identity 점수가 아닌 연결 얼굴 부족으로만 실행한다.

W14 소유: `evaluation/segment_review/sampling.py`, `coverage_replay.py`, 평가 테스트/검산/UI. W13 main/구간/몸/crop 및 제품 파일 변경 없음. core 공개 API도 이번에는 변경 없음. 기존240시점 보존+새211시점,24실제 경로 미수집0. SFace/ArcFace 개별 공간 유지, 관련90통과·4,060거리/40구간 검산 일치. 표본 보충 후 새 충돌이 있어 제품 적용 불가. 최신 W13과 병합/적용 전 half-open/경계 record/동일인 scope 계약과 기존 matcher 호환 검증 필요. merge는 미실행이며 다른 세션 메시지·새 세션 생성 없음. [실제 실행·한계·전후 화면](../10/14-w14-track-sampling-replay.md).

**10/14 실패 원인 인계:** W14 평가의 구간 전체 최대12표본 수집이3/19의 짧은 추적 경로를 누락하지만 최종 구간은 모든 경로의 합의를 요구하는 불일치 확인.19번은 한 경로 다니엘 지지9개/다른 경로 표본0개로 보류. 이는 모델 정확도로만 설명하면 안 된다.169/221 ArcFace 미매칭·14/18의 최소지지 부족도 분리했다. [근거·후속](../10/14-w14-poor-result-diagnosis.md). W13 코드/구간을 수정하거나 미관측 경로를 같은 사람으로 선언하지 않았다. 파일 소유·merge 순서 유지.

**10/13 기존 ArcFace 격리 대조:** 같은20구간·221얼굴·23참조로 SFace와 로컬 ArcFace를 각각 public gallery/match/consensus API에 넣었다. ArcFace512D/SFace128D·참조/cache/threshold/space fingerprint 분리. SFace 입력 확대 대안은 실패, ArcFace는 클립10 혜인 개발사례를 해결했으나 이름11→9·미매칭3개여서 제품 후보일 뿐이다. [사전 hash·기준 선택 순서·별도 재검산·화면](../10/13-w14-input-path-audit-and-arcface-dance-replay.md). W13의 최신 main/구간을 재실행하지 않았고 파일/core/adapter 변경0. **실험 runner/모델/기준을 바로 소비하지 않는다.** W14 API→독립 품질/compatibility fixture→W13 main/mapping/crop 소비 순서 유지. 선택 얼굴 identity GT와 latest W13/Windows/optional backend·venv/Electron 검증이 남는다.

**10/13 참조 gallery 후속:** 같은 YuNet/SFace·23참조의 선택/정렬을 다시 확인하고 저장 특징 차이0을 재현했다. 동일221개 query·20구간으로 참조 평균/최근접/두사진평균과42px 참조6조건 대조했으나 클립10 혜인 확정0.42px 평균은 하니로 오분류해 미채택. public core/gallery/match 정책과 W13 adapter는 변경하지 않았다. [실행·한계·화면](../10/13-w14-reference-gallery-audit-and-score-controls.md). W13은 이번 실험용 scoring/scale 코드를 소비하지 않는다. W14 공통경로→fixture→W13 main/mapping/crop 소비 순서와 소유권 유지, 최신 W13 통합 검증은 여전히 남음.

**10/13 최신 소비 실험:** W14 격리 평가 adapter가 저장된 선택 몸의 pose 코 위치로 얼굴 소유를 판정하고, public `match_reference`/`combine_reference_matches`에 각 표본을 전달한다. 추적 평균으로 충돌을 숨기던 경로를 수정. W13 파일/메인/구간/제품 adapter는 무변경. 입력소유 근거·얼굴별 비교·충돌 상태 계약을 유지한다. same-model 새특징24개 재평가에서 클립10 하니→확인필요, 혜인 정답 확정은 미해결이며 제품 채택 근거가 아니다. [결과·검증·제약](../10/13-w14-owned-face-consensus-replay.md). core→fixture→W13 소비 순서 유지, 최신 W13 연결은 남음.

**10/13 클립10 후속:** 사용자 확인으로 선택 인물 혜인→새 하니는 오매칭 악화 사례다. 기존 ROI 최고 검출점수 선택에서 옆 얼굴1개가 들어갔고, 그 표본 제외 후에도 하니가 근소하게 앞선다. 트랙 평균 하나를 core에 넘기는 현 비교 adapter는 표본별 충돌을 숨긴다. `all_tracks_agree`는 표본 합의를 뜻하지 않는다. 후속 소비는 실제 얼굴/몸 연결 근거와 표본별 비교·충돌을 전달해야 하며, main GT와 identity GT를 계속 구분한다. [저장 특징 진단](../10/13-w14-clip10-selected-face-mismatch.md). W13 파일/실제 결과 변경 없음.

**10/13 최신 비교 계약:** 사용자 요청으로 `selected-main segment/bbox/track`을 고정한 동일 구간 전후 비교를 구현했다.97개 실제 얼굴 표본→저장 평균20개 동일, 기존 clustering/mapping/구간 결과 재현, 새 구간9개 변경이며 품질 개선 판정은 하지 않았다. desired-main GT와 selected-face identity GT를 혼용하지 않는다. 복수track을 같은 사람으로 자동 선언하지 않고 구간 adapter에서 불일치·부분 매칭을 확인 필요로 보존한다. [실행·화면·정확한 소유 경계](../10/13-w14-fixed-dance-segment-face-comparison.md). 기존 W13 코드는 격리 복사해서 읽었고 제품 파일은 수정하지 않았다. 최신 W13 메인/군무 결과에 대한 실행은 아직 아니다. core→호환 fixture→W13 adapter 소비 순서와 파일 소유를 유지한다.

**10/13 사용자 증거 요청 후 보완:** [원본과 기존/새 분류 비교](../10/13-w14-face-matching-visual-comparison.md)를 제공했다. 저장512의18시점 이름 일치3→7, 저장256은5→4로 악화도 있다. 이전 구간 최종 이름 vs 새 개별 얼굴 이름의 서로 다른 집계 단위이며,512의 일치1개는 정답 몸과 위치가 다르다. 전체 pipeline 개선을 주장하거나 새 policy를 자동 채택하지 않는다. 코드/호환 테스트 통과와 실제 오배정 감소를 분리한다.

**10/13 구현 인계 갱신:** 사용자 Native 실행 승인 후 `clipper_face_core` **0.2.0 구현·격리 검증 완료**. `build_gallery`, `match_reference`, `combine_reference_matches` 및 provenance DTO/선택 OpenCV import/플러그인 비종속 예제를 제공한다. 새 checkout은 `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python`, branch `feature/shared-reference-face-matching-20261013`, fetch base `47782953228861f4bdbdc135265d067c2a826b0e`다. **미커밋이므로 HEAD만 전달하면 변경이 빠진다.** [실제 결과·코드 hash·적용 순서](../10/13-w14-shared-reference-matching-implementation.md). core/replay73개·donor호환27개·확대617개 통과(모델부팅11개 제외·3skip), 리뷰 Important3건 수정. 새 계약 W13 수용·제품 adapter/venv·Electron 연결 완료는 아직 아니다.

**2026-10-13 방향 전환 당시 인계(보존 이력):** 사용자 결정으로 W14는 Person 자체 기능/여러 품질 실험을 보류하고 **안무에서 선택된 참조 멤버와 영상 속 얼굴의 매칭 품질 및 공통화**를 먼저 맡는다. W13은 메인 선택·추적·구간/군무/복수 메인·crop, Dance adapter 소비/통합을 계속 맡는다. W13은 10/1 파일 소유 경계를 이미 수용했지만 API 고정·Dance 이식은 미완료다. 현재 `clipper_face_core` 0.1.0은 W14 미커밋 시험판에서 Person만 사용하고, 참조 이미지 평균/멤버 배정은 Dance 내부에 남아 있다. [현재 코드 상태·보존 범위·평가 방향](../10/13-w14-face-matching-priority-reset.md)을 우선 읽는다. 실제 공통 매칭 엔진 이식 완료나 안무 정확도 개선으로 해석하지 않는다.

**10/13 진단·새 계약 제안:** 기존 YuNet/SFace와 참조23사진·원본18프레임×3 ROI로 대상 얼굴 선택/개별 참조 비교/후단 배정을 분리했다. 참조 내부 23/23 일관성, 정답 몸 ROI 14/18 라벨 일치(다른 라벨2·미배정2), 옆 얼굴 선택 및 올바른 해린 특징의 전역 군집 후 하니 배정 사례를 확인했다. 최근접만 적용하는 저장 대조는 조건별 개선/악화가 섞여 미채택했다. [실제 진단·실패 시도·자원·한계](../10/13-w14-dance-face-matching-baseline.md), [서면 설계안](/Users/jina/project/adlight/docs/superpowers/specs/2026-10-13-shared-reference-face-matching-design.md). 새 제안에서 **참조 갤러리/거리·순위/모호·미배정/표본 충돌 계산은 W14 공통 API**, 대상 사람·선택 얼굴의 연결 정보/track·구간과 제품 반영은 W13 adapter 경계다. 아래 옛 문서의 '멤버 참조 mapping은 소비자 소유'는 표시 이름·구간 적용 정책을 뜻하도록 새 API에서 구체화한다. 새 설계의 W13 수용/실제 이식은 아직 확인하지 않았다. 공통 fixture/API → W14 격리 대조 → W13 소비 호환 순서이며 W13 코드·프로젝트 결과는 수정하지 않았다.

아래는 2026-09-30 당시 제안과 이후 진행 이력이다. 최초 작성 당시에는 W13 상호 확인 대기였으며 [10/1 소비자 검토](../10/01-w13-face-core-consumer-contract-review.md)에서 파일 소유 경계를 수용했다. [W14 MVP·artifact 제안](30-w14-person-highlight-design-proposal.md)과 [W13 9/30 설계](30-w13-investigation-evaluation-design.md)를 함께 본다.

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


**10/14 새 촬영 영상의 메인 정답 확인 인계:** W14는 Clipper Studio Dev의 `5j-yYbdOrzE` 원본 SHA `bb15d1bad1542fb7ec4bfbf968d60639b22beb66ab34a8e3139b553ae8166133`와 9/18 저장 안무 메타 SHA `3b9b0e4fdbaac39db8b900b225fb0d4464397728c6722e19c267be25d3bb50ae`의 18개 기존 메인 구간·참조 21장을 고정해 예측 비노출 확인 화면을 준비했다. [입력·실제 검증·한계](../10/14-w14-independent-dance-review-preparation.md). 이 메타는 구간별 이름만 있고 메인 bbox·track이 없으며 최신 W13 40B 출력도 아니다. W14의 사람별 정답이 들어온 뒤 W13 소유 최신 메인 경로/시점/몸 좌표를 같은 원본 SHA에 대해 별도로 확보해야 얼굴 선택·몸 연결·인식 거부를 구분할 수 있다. 이번 단계의 새 포즈/얼굴 추론, W13 adapter·제품 변경은 0회다. W14 공통 API/평가 소유, W13 메인/track/소비자 소유와 공개 DTO 확정 → W13 compatibility test → 병합 순서는 유지한다. 기존 SFace와 AuraFace의 모델·전처리 해시·참조 cache·threshold는 분리하고, 새 영상 정답으로 기준을 사후 조정하지 않는다.

**10/14 사용자 교체 입력과 W14 선행 산출물:** 위 릴레이 영상은 구간 내 메인 교체·중앙 중첩 때문에 평가 입력에서 철회됐다. 사용자가 지정한 일반 무대 [M2 ANTIFRAGILE](https://www.youtube.com/watch?v=p_XdZdg9oGc)의 새 원본 SHA `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`을 기준으로 한다. W14는 원본 `frame_index=0,12,…,13236`의 YuNet 후보 3,450개를 저장하고, 그 후보와 기존 참조 21장의 SFace 128D 특징 및 `(3450,21)` 원시 cosine 점수를 준비했다. [입력/PTS·원본 파일](../10/14-w14-antifragile-input-preflight.md), [관측](../10/14-w14-antifragile-face-observations.md), [특징·참조 선택·검산](../10/14-w14-antifragile-sface-features.md)에 SHA/계획/상한/실제 결과가 있다. 다중 상자 참조 3장의 주 얼굴은 W14가 원본을 직접 보고 명시적으로 선택했다. **영상 얼굴을 멤버로 배정한 결과는 아직 없다.** W13은 같은 source SHA·frame index/PTS·1920×1080 좌표계의 메인 몸 bbox/track, 역할(메인/공동/군무/없음), 교대/구간 경계를 W13 소유 평가 출력으로 제공해야 한다. 기존 릴레이 메타·옛 W13 2,002프레임 결과는 새 영상의 메인 정답이 아니다. 한 시점의 얼굴 여러 개 중 메인 몸에 연결할 얼굴이 모호하면 강제 선택하지 않고 별도 실패 상태로 둔다. W14는 그 결과를 받은 뒤 SFace 대조군과 후보 모델을 **각각 다른 embedding 공간/전처리/cache/threshold**에서 비교한다. 현재 독립 새 영상 GT·W13 출력·Dance adapter compatibility/Windows/제품 통합은 미검증이며 W14 평가 코드는 제품/core/W13 파일을 수정하지 않았다. 기존 `W14 공개 DTO 고정 → W13 compatibility fixture/실기 → 병합` 소유·순서는 유지한다.

**10/14 ANTIFRAGILE 사용자 얼굴 신원 확인 후 계약 정정:** 위 “멤버 배정 아직 없음”은 당시 준비 상태다. W13 69번의 같은 source SHA/프레임에서 `single` 몸 선택과 W14의 얼굴 위치 연결이 모두 확정된 시점 20개를 모델 이름을 보지 않고 선정한 뒤 사용자가 **표시된 얼굴 사진** 18개의 멤버와 식별 어려움 2개를 확인했다. 이는 몸이 올바른 안무 메인이라는 라벨이나 전체 구간 정답이 아니다. W14의 별도 평가에서 기존 SFace는 식별 가능 얼굴14/18 정답·오배정0, frozen Seeta 제한 보충은16/18 정답·오배정0(추가 홍은채 2장), Seeta 전면 교체는13/18이다. [고정 계획·20장 전 결과·선정 편향](../10/14-w14-independent-face-fallback-replay.md). 20장의 얼굴 가로 중앙값199.5px는 연결된 전체 435시점 중앙값123px보다 커 **작은 얼굴 일반화가 미검증**이다. SFace accepted 보존, association invalid에서 fallback 금지, SFace/Seeta 별도 embedding·alignment·cache·threshold 규칙을 유지한다. W13 소비자에게 이 20개 얼굴 이름을 69번 또는 미래 구간 전체의 메인 정답으로 전파하지 않는다. W13의 안정된 메인/교대/경계 산출물이 나오면 같은 source SHA·time base·bbox 좌표/track ID·선택 얼굴 ID/상태를 연결해 클립 수준 검증을 별도로 진행한다. 공통 API·W13 Dance adapter/main/mapping/crop과 설치 앱은 미변경이고 기존 파일 소유 및 DTO→compatibility fixture/실기→병합 순서도 유지한다.

**10/14 작은 얼굴·`shared_head_candidate` 전수 후속:** 동일 source/face 관측·W13 69번 pose/후보 계약·W14 adapter hash를 고정한 [평가 기록](../10/14-w14-antifragile-small-face-and-head-link-audit.md)을 추가했다. `single` 522시점 중 얼굴 연결 확정 435, `shared_head_candidate` 보류 53, 연결 실패 34다. 연결된 얼굴 가로 `<90px` 149시점에서 기존 SFace는 36개만 확정했고, `90–159px` 160시점 중 80개, `≥160px` 126시점 중 84개를 확정했다. **신원 라벨 없는 배정 처리율**이며 작은 얼굴 정확도가 아니다. 작은 원본 얼굴 13장의 사용자 신원/식별 불가 라벨은 별도 요청 상태다. 53개 보류에만 적용할 읽기 전용 규칙을 사전 잠그고 원본을 전수 검토한 결과, 35개 후보 중 한 화면 판독과 명확히 같은 얼굴 행은 33개, 2개는 불확실했다. 규칙의 제품 적용은 보류한다. W13은 `ambiguous`를 다른 멤버의 증거로 바꾸거나 얼굴 없는 34시점을 자동 신원 배정하지 않아야 한다. W14의 얼굴 ID 후보·실패 상태는 source SHA/frame index/PTS/time base, 원본 pixel bbox, W13 선택 body/pose track/version과 함께 전달하고, 멤버 점수와 adapter 단계는 분리해야 한다. 다른 촬영 영상의 독립 몸↔얼굴 GT 및 동시 출연 오연결 fixture가 호환 gate다. W13 메인·구간 GT 없이는 이 얼굴 단위 수치를 클립 정확도로 쓰지 않는다. **소유·병합 순서는 그대로:** W14 공통 얼굴 공개 DTO 초기 소유 → W13 Dance adapter/main/mapping/crop 소비자 fixture·실기 검증 → 병합. 제품 파일·기존 캐시/threshold 변경 없음.

**10/14 연결 실패 34시점의 원본 전수 판독 추가:** [같은 기록의 실패 분해](../10/14-w14-antifragile-small-face-and-head-link-audit.md#얼굴-연결-실패-34시점-검출과-몸-머리-위치의-분리). YuNet은 이 원본의 1920×1080 전체 입력·score 0.60으로 실행됐다. 34개 중 선택 몸 얼굴이 원본에서 보이지만 해당 얼굴 상자가 없는 사례는 11, 얼굴 상자는 있으나 W14 머리 조건이 거부한 사례는 2(U07 `unreliable_main_head`, U18 `no_face_at_main_head`), 얼굴이 안 보이거나 식별 불가 17, 한 화면 판독 불확실 4다. 이는 단일 검토자 진단이며 W13 메인·얼굴 신원 GT가 아니다. W13 소비 계약에서 `no_face_detection`/`no_face_at_main_head`/`unreliable_main_head`를 단순 `unmatched_identity`와 구별해야 한다. 보이지 않는 몸의 신원을 다른 검출 얼굴로 자동 채우지 않는다. 검출 누락은 후보 검출기/조건의 별도 GT 비교로, 머리 위치 거부는 다른 영상의 동시 출연 오연결 fixture로 검증한다. W13 파일·제품 API 수정은 없고 위 소유권·merge 순서를 유지한다.

**10/14 동일 검출기 문턱 시험 인계:** 위 34개 실패 시점에 저장 0.60을 기준으로 동일 YuNet 모델/1920×1080에서 0.45·0.30을 각각34회 더 돌렸다. 선택 얼굴이 보이지만 검출되지 않았던 11시점 중 새 얼굴 상자는 각각 2·4시점에만 생겼고, 선택 얼굴이 안 보이는 17시점에는 새 상자가 16·44개 생겼다. 새 상자에는 다른 실제 얼굴과 손·무대 배경 비얼굴이 섞여 있다. [계획·68회 결과·상자 판독·감사](../10/14-w14-antifragile-small-face-and-head-link-audit.md#동일-yunet의-점수-기준만-낮춘-격리-진단). **전역 YuNet 문턱 완화는 미채택**이고 W13 adapter가 보류/미검출을 신원으로 임의 변환해서는 안 된다. 작은 얼굴 인식 보충, 검출 누락, 몸↔얼굴 연결은 서로 다른 실패 단계와 별도 fixture/모델 공간으로 평가한다. 제품 설정·공통 API·W13 파일 변경 없음.

**10/14 시간 이웃 확정 얼굴의 반례 인계:** W14의 ANTIFRAGILE S02/S06 사후 후보 규칙을 다른 뉴진스 개발자료 35 scope/37 run/353 저장 SFace 얼굴에 그대로 재생했다. 34개 직접 사용자 얼굴 라벨에서는 정답18→23/신규 오확정0이지만 `s0043-p0-r1`에서 앞뒤 혜인 직접 라벨과 시각적으로 이어지는 보라색 출연자의 중간 얼굴8개에 하니 후보가 생겼다(중간8개의 직접 GT 없음). 7개 과거 시각적 몸 track 교대 중4경로에도 후보18개가 생겼으나 신원 GT는 없다. **같은 몸 ID·같은 run·짧은 시간·주변 얼굴 두 표도 동일인 보장 아님; 확정 얼굴도 틀릴 수 있다.** [반례·원본·직접 라벨과 시각 추정의 구분](../10/14-w14-temporal-cross-video-stress-result.md)을 W13 호환 회귀의 안전성 입력으로 보존한다. W13은 보류 얼굴을 인접 확정 이름으로 자동 채우지 않고, 얼굴/몸 연결·shot cut/교대·서로 다른 멤버의 동시 출연·등록 외 인물 근거를 별도 상태로 소비해야 한다. 이번 규칙은 평가 전용이며 제품/core/W13 수정·통합 승인 없음. 공개 DTO/실패 상태 고정 → W13 adapter fixture·실기 → 병합 순서 유지.
