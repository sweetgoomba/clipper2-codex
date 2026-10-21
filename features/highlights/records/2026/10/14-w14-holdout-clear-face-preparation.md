# W14 추가 영상: 더 선명한 얼굴 12개 확인 준비 및 세 모델 비공개 비교

## 결론과 다음 행동

현재 안무 매칭 모델 교체/제품 적용은 미완료다. 앞서 새 두 영상에서 받은22답변은 식별가능 멤버7개뿐이며 혜인0·식별가능 하니0이었다. 작은·흐린 얼굴이나 배경 인물만 더 확인하는 것은 현재의 인식 개선 질문을 해결하지 못한다.

이번에는 같은 두 영상의 미리 고정한4분 범위에서 **더 크고 실제 얼굴이 보이는 후보12개(영상당6개)**를 마련했다. 기존 SFace/AuraFace-v1/Intel0095로 각12번, 총36번 추론을 마쳤지만 사용자 정답은 아직0개다. 화면에는 예측을 노출하지 않았다. 모델 성능 향상이나 우승 모델을 주장하지 않는다.

[얼굴12개 확인 화면](http://127.0.0.1:58261/holdout-clear-review-v1/index.html)에서 멤버 이름 → 얼굴 사진 자체의 식별가능 여부 → 다음 얼굴을 선택한 뒤 내보낸다. 전체 구간의 메인 댄서를 다시 지정하는 요청은 아니다. 파일명은 `clipper-holdout-clear-face-labels.json`이다.

답변 수신 후 원문 보존/검증 → 이미 저장한36결과와 연결 → 모델별 정답확정·오확정·거부·멤버별 분모 비교 순서로 진행한다. 이전22답변은 별도 영수증으로 보존됐으며 새 export에 합쳐져 있지 않다. 통합 집계 시 ID 중복을 검사해야 한다. 판정 기준을 이12개에 맞춰 튜닝하지 않는다.

## 실제 범위와 입력

- 평가 worktree: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python`
- HEAD `47782953228861f4bdbdc135265d067c2a826b0e` + 입력 manifest의 파일별hash. 기존 worktree 재사용, origin/dev 새 기준으로 제품 개발을 시작한 것이 아님.
- 출력: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-clear-faces-v1`
- 입력 영상은 기존1920×1080 파일2개. 새 다운로드·의존성 설치·유료API·pose/body/메인 추론·Build5 없음.
- 각각30–59/80–109/125–154/165–194초의 네30초 창, 1Hz120프레임씩 총240. 전체영상 실행 아님. `holdout-frames.json`의 frame_index/PTS/time_base=1/30000 고정.
- OMG(`6bVUjsUi9sw`) SHA `0e778c49ecb3325e1fe507d7179f5e5b638686896fbd5c3bc07fd03027f63f63`
- Super Shy(`J9DlrnNlgfE`) SHA `fa434d6d1d62c19fd75f606b70fd158a943fcbdfd1fe91778ef784e4ca149cc0`
- 이전8프레임/22검출은 원본 crop 픽셀 동일성 확인 후 재사용. 추가 YuNet232회, 전체1080검출 보존. 유효얼굴 없는4프레임·invalid0을 따로 기록. 모든 누락률 평가를 완료한 뜻은 아님.
- YuNet1920×1080 native BGR, score0.6/NMS0.3/topK5000. 몸/팔 오검출도 전체 결과에서 삭제하지 않음.
- OS/device/versions: macOS27 arm64 Apple M4, Python3.11.12, OpenCV4.13.0.92, NumPy2.4.4, ORT1.24.4, OpenVINO2026.4.1; CPU1thread/batch1.
- 검출 한도232회/300초/4GiB/200MiB. 실제 supervisor23.323초·479,969,280bytes RSS, exit0.
- 인식 한도 모델당12회/120초/4GiB, 전체100MiB 출력. 기존 등록사진23장과 모델별 참조cache/embedding공간/전처리/template/threshold를 유지했다. 수동 위치점 보정 없음.

## 왜 확인 목록을 다시 골랐나

자동 크기/선명도 선택12개에 팔·몸 오검출과 큰 흔들림이 포함됐다. 큰 bbox나 Laplacian 점수만으로 유용한 얼굴이라고 할 수 없었다.

전체1080검출 → 각 영상/창의 크기80px·눈간24px·5점기하/시간조건을 통과한 상위6개씩48후보를 시각 점검 → 얼굴이 보이는28개 → 기존 선택 규칙(6/source, 최대2/window, 최소8초간격)으로12개를 정했다. 기존 확인 프레임 ±1.01초는 중복 확인을 막기 위해 제외했다.

48개 중20개는 심한 흐림/가림/몸·팔 오검출 등의 이유로 **이번 수동 확인 요청에서만** 제외했다. `visual-screening.json`은 assistant의 얼굴 가시성 판단이며 멤버 정답/전문가GT가 아니다. 모든 ID/crop hash/제외 이유와 자동 최초12개는 보존했다. 이름 예측을 보고 선택하지 않았다. Person 제품의 배경 숨김/soft filter 정책을 만든 것이 아니다.

최종 원본 bbox 폭 약201–393px. 사용자가 실제 식별가능 여부를 최종 답한다. 다섯 멤버를 모두 포함했는지는 아직 모른다. 이전과 같은 영상에서 큰 얼굴을 의도적으로 고른 진단자료이므로 새 독립 holdout/무편향 전체성능 분모가 아니다.

## 검증 및 실행 결과

- 새/기존 관련144tests 통과: `evaluation/holdout_expansion evaluation/candidate_comparison evaluation/native_sampling`.
- 신규 선택5tests 및 신규 importer8tests는 실패→수정→통과 확인. QA/다른페이지/다른manifest/일부응답/원본frame변조를 거부한다.
- 기존 제품 전체suite는 평가venv의 `clipper_video_render` 누락으로 수집불가였으며 이번에는 새 설치나 무관한 전체 재실행을 하지 않았다.144는 제품 전체suite 통과가 아님.
- 세 모델 각각12/12 embedding 성공. 점수180개·판정36개를 저장벡터에서 float64로 독립 재계산, 최대거리오차 8.52e-08.36회 원본 crop 픽셀 동일성 확인. 추론실패0은 정확도100%를 뜻하지 않는다.
- SFace worker1.100초/peak516,767,744bytes; Aura2.140초/871,366,656bytes; Intel1.538초/375,128,064bytes. 각12얼굴의 모델로딩/디코딩 포함 측정이며 일반 배포 성능 보증 아님. warm forward+L2 p50은13.52/72.04/6.56ms, n=11씩뿐.
- 독립 리뷰에서 selection 재현/기존labelhash/36실행/QA격리/예측 미노출 확인, actionable blocker없음. 이전22개는 아직 새 export에 합쳐지지 않았다는 점 기록.
- 실제브라우저 QA: 얼굴아님→다른응답 수정시 quality초기화,12개 이동/완료,새로고침 유지,내보내기 확인. 브라우저 download-event wait는 timeout였으나 실제 `/Users/jina/Downloads/clipper-holdout-clear-qa-labels.json` 저장과12/12내용 확인; QAorigin/path로 importer거부. 자동화 입력은 모두 QA의 ‘판단어려움/no’로 실제 정답 아님.
- 실제 사용자 index는0/12미입력, 다른storage/path/파일명 사용. 기존답변과 사용자페이지storage를 덮어쓰지 않았다. screenshots/QA원문/검산 영수증 보존.

## 고정 증거

- 검출 계획SHA `1879b944bed9706296b90e56adbfe1556b3be37a21799a2d2792d45bdcd88cad`
- review manifestSHA `441378025b10c22f4a0b56a59153d24972caf56b5c60a95c50bd1f8e2015d7f8`
- recognition manifestSHA `32fe3c9a1c368e19adc04cabae5506912d028f0edc1079cbae50129f2fbdc504`
- `plan.json`, `result.json`, `screening-pool.json`, `visual-screening.json`, `review-manifest.json`, `review-data.json`, `recognition/manifest.json`, 모델별 `result.json`·vectors·aligned입력·supervisor, `audit.json`.
- 이전15답변SHA `ea75e27a332057a5003b80341d683049cbbb6d9b3f60556f560859f9768db0be`, 추가7답변SHA `ff0e6a091cb8f862f24644eb6a679b0f44bdc434309cdcb1549a1b027a00d5aa` 재확인.

## 남은 범위 / W13 계약

이 두 입력에는 저장된 안무 메인/몸경로/구간 출력이 없다. 따라서 이번 얼굴을 ‘안무가 고른 메인의 얼굴’이라 부르거나 얼굴GT를 최종클립GT로 전파하면 안 된다. 기존 W13-35 진단과도 별도다. 원본 PTS는 manifest 산술/디코더 frame-index로 확인했으며 독립packet PTS검증은 아니다.

1. 사용자12답변을 수신한 뒤 같은 고정 모델/기준으로 비교한다. 잘못된 멤버 확정과 식별가능 얼굴 거부를 나누고 멤버 분모 부족을 표시한다.
2. 실제 안무제품 검증에는 source hash가 일치하는 W13의 고정 main/track/구간 출력 및 그 선택 인물의 정답이 필요하다. 현 단계에서 최신W13품질 향상/제품통합/모델교체를 선언하지 않는다.
3. Windows x64/패키징/독립 촬영 검증은 미완료. Mac Intel 제외. 기존제품 YuNet+SFace 대조군 유지.
4. W14는 평가·공통 API·fixture, W13은 main/몸/구간/mapping/crop/소비adapter 소유. 이번 core/publicAPI/제품adapter/W13코드 변경없음. 계약상호확인→시간/좌표/scope/실패호환→선택venv/소비adapter→Macarm64/Windowsx64→합의merge 순서 유지. 새상호수락/채팅발신/commit/push 아님.
