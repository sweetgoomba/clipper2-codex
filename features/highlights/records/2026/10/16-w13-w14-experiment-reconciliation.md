# W13·W14 안무/인물 하이라이트 실험 회고와 다음 출발점 (2026-10-16)

## 이 기록의 범위와 판정 기준

고정 스레드 2 `안무 하이라이트`, 3 `인물 하이라이트`, 4 `안무 하이라이트 사용성 개선`, 5 `안무 하이라이트 사용성 개선 (2)`, 8 `안무·인물 얼굴 매칭 통합 빌드 준비`의 대화 전체를 다시 읽고, 남아 있는 기록·노트북·코드 작업 트리와 대조했다. 5번의 앞부분은 4번에서 이어받은 동일 대화이므로 중복 성과로 세지 않는다. Git 반영 여부의 기준은 10/16 새로 `git fetch origin dev`를 수행한 각 저장소의 `origin/dev`다. 저장소별 SHA와 미반영 작업 트리는 [전체 브랜치 감사](../../../../../handoff/2026-10-16-pinned-thread-dev-reconciliation.md)에 둔다.

이 문서에서 **평가**는 저장된 관측/얼굴 특징을 다시 계산하거나 새 모델을 국소 실행한 결과, **시험 앱**은 격리 작업 트리에서 실행·빌드한 결과, **dev**는 원격 Git 조상 관계가 확인된 코드다. 평가 숫자를 앱의 최종 클립 정확도 또는 대표님께 전달한 설치본의 정확도로 바꾸어 읽지 않는다. 대표님께 새 빌드를 전달했고 어느 정도 개선됐다는 피드백을 받았다는 것은 이번 사용자 보고다. 해당 설치본의 소스 SHA·원본 영상·채점표는 이 조사에서 확보하지 않았다.

## 결론부터: 현재 이어받을 기준

| 영역 | 확인된 결과 | 채택·검증 경계 |
|---|---|---|
| W13 자동 메인/군무 | MoveNet 256·512, YOLO26s, RTMO-s, RTMDet+RTMPose-m 및 시계열 규칙을 노트북에서 비교. 72번의 신규 화면 주목 후보 7구간은 사용자가 맞다고 봤으나, 추가 확인에서 15.816초 오선택과 149.883초 3인 공유 요구 확인 | **72번 제품 미채택.** 7구간 판정은 전체 영상 정확도나 실제 클립 품질의 근거가 아님 |
| W13 공유 클립 | 저장돼 있던 group MP4의 `함께 등장` 노출과 복수 인물 수동 배정이 별도 앱에서 검증됐고 후속 코드가 dev에 들어감 | 기존 클립의 노출·수동 귀속 개선. 새 영상의 자동 인물 판별·클립 경계 품질은 미검증 |
| W14 얼굴 | `clipper_face_core` 0.2.0과 Dance 참조 매칭 연결이 시험 빌드에 들어가고 이후 dev에 병합됨 | YuNet/SFace 기본 유지. 신규 모델, 참조 8장 추가, 시간 이웃 이름 전파는 회귀·오배정 위험으로 미채택. 통합만으로 얼굴 매칭률 향상을 주장할 수 없음 |
| Person 플러그인 | 10/1 시험 MVP로 37분 실영상 작업을 완료하고 과분리·짧은 장면·대표 얼굴 문제를 관찰 | 사용자 지시로 Person 개발은 보류하고 공통 얼굴 매칭을 안무에 우선 적용. MVP 작업 트리의 미커밋 소스는 별도 보존 |
| 10/15~16 통합 | W13 공유 클립과 W14 core를 합친 시험 checkout을 빌드·검증. 사용자 보고상 새 앱 배포와 부분적 개선 피드백 | 시험 트리의 이후 수동 클립 배정 UI/API, 메인 초점 분할, 긴 group 분할은 **dev에 없음**. 실제 설치본/원본별 정량 평가와 혼동하지 않음 |

## W13 노트북과 근거 파일

실제 노트북 폴더는 `.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/`이다. 10/16 로컬 확인 시 `w13_dance_human_review.ipynb` 1개와 iteration 노트북 70개, 합계 71개가 있다. 번호 33·47 파일은 없으며, 이를 누락된 실행 결과라고 추정하지 않는다. 이 폴더와 `output/`, 평가 보조 코드 상당수는 **untracked 또는 미커밋**이다. Jupyter URL `127.0.0.1`은 당시 열었던 화면 주소일 뿐 다음 세션에서 지속되는 링크가 아니다. 각 단계의 재현 조건·입력 해시·표본은 아래 원문 기록을 우선한다.

재개용 원본: [사용자 21행 정답 노트북](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_human_review.ipynb) · [09 전체 영상](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_09_full_video_review.ipynb) · [13 역할/구간](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_13_roles_and_segments.ipynb) · [55 움직임 이력](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_55_motion_history.ipynb) · [65B 군무](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_65_group_evidence.ipynb) · [69 새 영상](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_69_antifragile_full65b.ipynb) · [72 화면 주목](../../../../../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_72_stage_focus.ipynb).

| 시기/노트북 | 무엇을 배웠나 | 다음 단계에서의 사용법 |
|---|---|---|
| 10/1~2 기본·02~04, `w13_dance_human_review` | MoveNet 저장 pose와 현행 선택기 18개 표본의 `6/18`은 **기존 앱 YOLO 성능이 아니다**. 10/2 같은 영상의 새 결과는 사용자가 그룹 과다·선택 품질로 불합격 판정 | 원본 앱 결과와 평가용 모델·선택 규칙을 분리. [초기 비교](13-w13-user-truth-existing-output-comparison.md)와 [사용자 정답 대조](13-w13-truth-guided-iteration-1-2.md) 참조 |
| 05~12 | MoveNet 256/512, YOLO26s 실제 pose 비교와 저장 결과 선택기·시간 동작 비교. 사용자 21행 `confirmed` 정답표 기준 기존 앱 멤버 일치 36.68/82.50초·오배정 28.97초, MoveNet 후보 25.81초·54.19초. 겹치는 정답 행을 중복 시간으로 세던 31.47/56.69초 계산을 고쳤다 | 모델별 검출·선택·군무를 별도 지표로 사용. [모델 실제 비교](13-w13-yolo26s-pose-actual-comparison.md), [오선택 원인](13-w13-user-feedback-motion-group-diagnosis.md). 12번의 소표본 `18/18`도 전체 채택 근거가 아님 |
| 13~18 | 단독/공동/군무/보류를 분리하고 시간 안정화. 14번은 1초 미만 구간을 줄였으나 메인→군무 오판이 남음. 15~18은 단일 선택·역할 근거의 반례를 분리 | 짧은 조각 감소와 맞는 인물 선택을 같이 측정. [역할 구간](13-w13-role-segmentation-result.md), [안정화](13-w13-sequence-stability-result.md), [선택](13-w13-single-selection-result.md) |
| 19~55 | RTMO-s와 RTMDet+RTMPose-m을 비교하고 관절·검출·track 교체·컷·공동 시작/종료를 한 원인씩 시험. 많은 후보는 기존 정답 손실·짧은 조각·근거 혼합 때문에 미채택. 55번은 잘못 이어진 움직임 이력을 초기화해 특정 15초/80초 사례를 개선 | 성공 사례만 합쳐 새 정책으로 만들지 않는다. [55번 결과](14-w13-motion-history-reset-result.md), 각 번호의 `2026-10-14-w13-*-result.md`를 참조 |
| 56~65B | 실패 조건을 다시 대조. 64번 몸통 크기 대체는 메인→군무 오판 71→78로 악화. 65B의 공동 시작은 약 0.33초 회복하되 전체 제품 후보는 아님 | 비교용 고정 후보로만 보존. [65B 근거](14-w13-pose-group-evidence-result.md) |
| 66~69 | 새 르세라핌 ANTIFRAGILE 원본에서 RTMDet Nano+RTMPose-m 3,310시점, 이후 YOLO26s Pose 1회를 실제 실행. 69는 459역할 구간 중 1초 미만 401, 판단 보류 1,150시점 | 67은 옛 35번 규칙이므로 최신 65B 검증이라고 부르지 않는다. 69도 사람 정답표가 없어 정확도 미판정. [전체 실행](14-w13-antifragile-full65-result.md) |
| 70~71 | 69 보류 중 70은 일부 움직임 근거로 3구간/40시점 후보를 제시했고 사용자는 **3구간의 메인 몸 위치**를 확인. 71은 상반신 관측 170시점을 진단했지만 역할 변경 0 | 40시점을 정답 40개로 세지 않는다. 정지·클로즈업도 무대 주요 인물 후보에 포함한다는 새 요구는 후속 평가 계약에 반영. [70·71 결과](14-w13-antifragile-partial-motion-and-upper-body-result.md) |
| 72 | 69 보류 중 388시점(약 25.9초)에 화면 주목 몸 후보를 추가. 57개 변경 구간 중 52개는 기존 연장, 새 독립 5개는 0.34초 이하. 1.2초를 처음 넘긴 7구간은 사용자 긍정; 추가 5곳에서 15.816초 오선택·43.911초 정답·149.883초 3인 공유 요구 | **평가 전용·미채택.** 남은 50변경 구간, 정확한 클립 경계, 다른 촬영 일반화가 비어 있다. [72 감사](14-w13-stage-focus-72-cached-comparison.md), [후속 5곳](15-w13-stage-focus-five-review-and-shared-clips.md) |

노트북 운영 시행착오: 10/2 열린 Jupyter 파일을 외부에서 다시 써 `File Changed` 충돌이 났고, 이후 UI에서 실행·저장해 수습했다(2번 스레드). 다음 실험은 노트북·원본·output의 해시와 실행 코드 SHA를 고정하고, 열린 노트북 외부 수정을 피한다. `w13-dance-metadata-eval`의 미커밋 `pipeline.py`, `face_cluster.py`와 수십 평가 파일을 제품 코드로 일괄 포팅하지 않는다.

## W14 얼굴 실험과 기각 이유

W14의 주된 평가 자산은 `.ipynb`가 아니라 `.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python` 및 `.codex/features/highlights/records/2026/10/`의 평가 코드·JSON·HTML·기록이다. Person MVP는 `.worktrees/person-highlight-mvp-20261001/desktop/`의 네 저장소 미커밋 소스를 별도 보존한다.

| 시도 | 관측과 결정 |
|---|---|
| Person MVP | 실제 영상 37분 작업은 완료됐으나 동일인 과분리, 짧은 장면 과다, 흐린 대표 얼굴, 오검출이 나왔다. ArcFace는 독립 60초 오합침 14쌍을 해결하지 못했고 다른 드라마 SFace는 380쌍/26클립 중 22개가 3초 미만이었다. Person 제품 고도화는 보류. [시험 결과](01-w14-testable-mvp-implementation.md), [첫 피드백](01-w14-first-result-debug.md) |
| 공통 core·Dance adapter | `clipper_face_core` 0.2.0은 공통 얼굴 관측·참조 매칭의 계약을 만들었다. Dance의 메인 몸/얼굴 연결과 타인 충돌을 보수적으로 다룬다. 10/15 Python `e636a5f`, Electron `b162592` 시험 트리 연결 뒤 통합 시험 checkout을 거쳐 dev에 병합. [연결 범위](15-w14-today-build-scope.md), [통합 시험](15-w13-w14-test-build-integration.md) |
| ArcFace/AuraFace/Intel0095 | 특정 얼굴·4K 입력에서는 개선 사례가 있었지만, 다른 얼굴 손실·참조/정렬 민감성·몸 경로 충돌이 남아 제품 모델 교체 근거로 부족. 4K의 같은 34얼굴에서 SFace 9→16/Aura 8→18/Intel 1→7은 **입력 조건의 국소 비교**이며 전체 영상 성능이 아니다. [입력 원인](14-w14-main-face-native-source-diagnosis.md) |
| SeetaFace6 Light/일반형 | Light는 작은 얼굴 직접 라벨 12장에서 SFace 정답 7 대비 추가 회복 0. 일반형은 안무 28얼굴에서 19정답이지만 다른 두 영상 19얼굴에서는 13정답으로 떨어져 미채택. [작은 얼굴](14-w14-antifragile-small-face-and-head-link-audit.md), [일반형](14-w14-seeta-normal-comparison-result.md) |
| 참조 사진 8장·시간 이웃 전파 | 직접 GT34에서 사진 추가 시 SFace 18→19/Aura 19→20이나 **각각 기존 정답 1개를 보류**해 회귀 gate 실패. 시간 전파는 직접 GT34의 18→23 회복 후보와 함께, 직접 GT가 없는 연속 얼굴 8개에 하니 전파 위험을 만들었다. 8개를 확정 오답으로 세지 않지만 제품 적용은 차단. [회귀](14-w14-face-evidence-regression-result.md), [다른 촬영 반례](14-w14-temporal-cross-video-stress-result.md) |
| 르세라핌 새 촬영 | 1,104시점에서 W13 단독 몸 522, 얼굴 위치상 연결 435/모호 53/실패 34는 **몸↔얼굴 위치의 관측**이지 멤버 정답이 아니다. 큰 얼굴 직접 라벨 18개는 SFace 14→제한 Seeta 보충 16의 탐색 후보, 작은 얼굴 12개는 7→7. 새 촬영의 컷·교대·등록 외 인물까지 독립 라벨이 필요. [독립 재판정](14-w14-independent-face-fallback-replay.md) |

W14 10/14 당시 [종합 기록](14-w14-face-matching-work-summary-and-decision-status.md)은 이후 10/15 core 연결과 10/16 dev 병합 이전 스냅샷이다. 평가 모델, 참조 gallery fingerprint, 얼굴 선택, 입력 해상도가 다른 수치를 한 개선율로 합치지 않는다. 릴레이댄스 18구간은 한 구간 안에서 멤버가 교대해 단일 이름 정답 요청을 철회했다. 같은 메인 몸 경로와 컷 경계를 고정한 평가 입력이 먼저 필요하다.

## 통합·사용성 변경과 남은 작업

4·5번 스레드에서 한글 우선 아티스트 후보, 별칭/직접 입력과 카탈로그 검색, 게시형 외부 데이터 관리, 참조 사진 검사·중복 처리, 결과 원본 URL 복사, 화면 문구·배지를 작업별 브랜치로 만들고 통합했다. 최종 검색 정책은 한국 그룹(P495=Q884)·한국 국적 솔로(P27=Q884) 기본이다. 시험 중 전세계→한국/일본/미국→중국을 거쳐 최종 기준으로 좁혔다. `LOVE DIVE`의 `LOVE`가 별칭 `Love`인 다른 솔로 아티스트와 매칭되는 오탐은 원인만 확인됐고 수정 기록은 없다. 과거 수집본 `b7d77ef7-…`은 게시하지 않았고 누락 QID/다국어 라벨 검증 수정 뒤 재수집·게시 확인이 필요하다. 기존 사진 URL의 403 접근 거부와 네이버 이미지 키 미설정/소진 오류 구분도 후속이다. [Git 반영 표](../../../../../handoff/2026-10-16-pinned-thread-dev-reconciliation.md)와 [10/16 개발 서버 스냅샷](../../../../../records/2026/10/16-dev-merge-and-deployment-snapshot.md)을 함께 본다.

8번의 초기 동일 영상 결과는 기존과 같은 main 19개/group 1개였다. 시험 트리의 오프라인 재계산은 정답 시간 36.02→38.55초 후보를 만들었지만 혜인 자동 클립은 0개였다. 샘플 프레임 기준 group 후보 1→15개는 오검출 검토 전이며, 51.8초 group의 최대 8초 분할과 43개 중 미확인 17개 얼굴 재비교는 앱 새 분석/정량 개선이 확인되지 않았다. Python dev의 `6b655ad`는 군무 샘플 프레임 시간 계산을 별도 수정했지만 `max_clip_sec` 분할과 수동 멤버·장면종류 수정 UI/API는 시험 트리 미커밋 상태다. [시험 트리 후속 문서](../../../../../../.worktrees/dance-diagnostic-docs-20261016/clipper_docs/todos/2026-10-16-dance-result-trial-worktree-followups.md)는 별도 문서 브랜치 `922e153`에 있으며 `clipper_docs/main` 반영 전이다.

다음 품질 작업의 순서는 (1) 대표님께 전달한 빌드의 4개 desktop SHA와 입력 영상·결과를 고정, (2) W13 메인/군무/컷/공유 인물과 W14 얼굴 ID를 **서로 다른 정답**으로 라벨링, (3) 같은 입력에서 현재 dev와 한 후보씩 비교해 회복·기존 정답 손실·오배정·짧은 구간을 함께 집계, (4) 시험 트리 변경을 기능별로 선별·검증해 병합 판단, (5) 새 설치 앱에서 전 과정을 다시 실행하는 것이다. 단일 샘플의 긍정 피드백만으로 새 모델·문턱·후처리를 제품 기본값으로 채택하지 않는다.
