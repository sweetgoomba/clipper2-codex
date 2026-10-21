# W14 — 추가 7개 답변 수신 및 두 영상 22개 얼굴 비교

2026-10-14 KST. 사용자 “내보냈어” 후 기존 승인된 얼굴 매칭 비교를 이어갔다. **답변 반영·비교는 완료했으나, 제품 매칭 품질 개선을 완료한 것은 아니다. 이번에도 모델 교체를 채택하지 않았다.**

- [통합 22개 비교 화면](http://127.0.0.1:58261/holdout-results-v2/index.html)
- [실제 입력·상한 manifest](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-coverage-comparison-v1/manifest.json)
- [전체 점수·답변·이전/추가 분리 집계](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-coverage-comparison-v1/combined.json)
- [독립 거리 검산](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-coverage-comparison-v1/verification.json)
- [브라우저 검증](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-coverage-comparison-v1/ui-verification.json)

## 1. 사용자 답변과 입력 보존

`/Users/jina/Downloads/clipper-holdout-coverage-labels.json`의 7/7 답변을 받았다. `annotation_origin=user_review`, 해당 화면 경로, manifest, 전체 ID와 canonical source hash/frame/PTS/time base/bbox/landmarks를 검증했다. QA 내보내기는 수입하지 않았다. 기존 validator 재사용 시에는 새 화면 경로를 먼저 엄격히 검사하고 복사본의 경로만 기존 경로로 변환했다. 원문 바이트는 별도 파일에 그대로 보존했다.

- 새 답변 SHA256: `ff0e6a091cb8f862f24644eb6a679b0f44bdc434309cdcb1549a1b027a00d5aa`.
- 검토 manifest SHA256: `0126230099ab5a474683ccdb03358a07e99b9eb75346f8723072c8ab344fd773`.
- 새 답변: 하니 2 / 다니엘 1 / 해린 1 / 등록 외 3. **7개 모두 identifiable=no**를 그대로 유지했다. 인물 이름을 답한 것과 얼굴 crop 자체가 식별 가능한지는 별개다.
- 이전 15개와 ID 중복 없음. 합계 22개: 이름이 있는 멤버 11, 등록 외 5, 판단 어려움 5, 얼굴 아님 1. 멤버 11개 중 identifiable=yes는 기존의 7개다. 혜인 정답은 0, 하니 2개는 모두 identifiable=no다.
- 새 7개는 기존 검출 결과의 남은 얼굴이며 새 무작위/독립 촬영 표본이 아니다. 두 영상의 고정 8프레임, 총 22검출을 모두 보존했다. 얼굴 미검출 1프레임도 별도 기록했다.

## 2. 실행 조건 및 실제 사용

기존 격리 worktree `shared-reference-face-matching-20261013`, Python branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e`에서 진행했다. 새 코드는 evaluation-output의 재현용 스크립트뿐이다. 제품/public core/SDK/W13 main·mapping·crop/기존 repo dirty 파일을 수정하지 않았다. 다운로드·설치·유료API·Build5·commit/push·다른 채팅 메시지·새 작업 세션 0.

같은 모델/23참조/모델별 전처리와 embedding 공간/기존 개발 거리·margin 기준을 그대로 복사했다. 답변을 실행 선택·모델 입력·참조 수집·기준 튜닝에 쓰지 않고 7개 모두 실행했다. 기존 15개 결과는 재추론하지 않았다.

| 모델 | 파일·공간 | 추가 실행 |
|---|---|---:|
| SFace2021dec | 기존 OpenCV DNN CPU, 128D | 7 |
| AuraFace-v1 glintr100 | 기존 ONNX Runtime CPU, 512D | 7 |
| Intel0095 FP32 XML/BIN | 기존 OpenVINO CPU, 256D | 7 |

정확한 각 weight hash·reference cache·정렬/전처리 config는 manifest에서 이전 실행과 완전히 동일한지 확인했다. 원본은 각각 1920×1080, 원래 source frame과 검토용 crop의 픽셀 동일성을 매 입력 확인했다. 모델용 정렬 이미지는 별도로 저장했다.

- 실행 manifest: `f0f898096ad22a38f004a17377165eb57992cda8f4827d8824954fb099aa8bf1`, 고정 입력83개.
- CPU Apple M4, macOS27 arm64, Python3.11.12; OpenCV4.13.0, NumPy2.4.4, ORT1.24.4, OpenVINO2026.4.1. 기존 환경 그대로.
- 모델별 상한: 7회,180초,4GiB RSS; 순차 CPU1thread/batch1, 전체 출력100MB. 신규 인식21회 모두 성공, 신규검출/참조추론0, 정렬/추론오류0. 재시도 없음.
- 첫 sandbox 실행은 ps 사전 확인에서 막혀 ML 시작 전 종료했다. 메모리 감시 권한을 포함한 scoped escalation 후 동일 상한으로 실행했다. 준비 단계의 opencv-python-headless metadata 가정은 실제 설치된 opencv-python으로 정정한 후 manifest를 고정했다. 패키지 변경 없음.

추가7개 실행의 첫 추론 / 나머지6 p50·p95(ms), peakRSS(MiB):

| 모델 | 첫 추론 | warm p50 / p95 | peak RSS |
|---|---:|---:|---:|
| SFace |27.5|13.2 / 14.1|486.8|
| AuraFace |152.8|68.0 / 83.3|831.1|
| Intel0095 |9.2|6.2 / 6.4|367.6|

모델 실행+출력 정규화만의 참고값이며 decoding/정렬 제외. 이전15개와 섞어 하나의 지연시간 분포로 만들지 않았다. Windows·앱 전체 성능 아님.

## 3. 실제 결과와 해석

### 기존 시험 기준 적용 — 이름이 있는 11개

| 모델 | 점수1위 정답 | 올바른 배정 | 잘못된 배정 | 보류 |
|---|---:|---:|---:|---:|
| SFace |7/11|5|0|6|
| AuraFace |7/11|5|0|6|
| Intel0095 |7/11|3|0|8|

식별 가능하다고 답한 기존7개만 보면 SFace/Aura는5정답·2보류, Intel은3정답·4보류다. 추가 멤버4개는 모델별 점수1위 정답1/4이고 모두보류였다. 추가 등록외3개도 모두보류, 기존 포함 등록외5개 모두보류. 판단어려움5·비얼굴1도 이름 배정0.

**새7개에서 틀린 이름을 확정하지 않았지만 인식에 성공한 멤버가 늘지는 않았다.** 보류를 정답 인식으로 세지 않는다. 식별어려움4의 보류와 식별가능7의 보류를 구분해야 한다. 개발에서 정한 거부 기준을 바꾸지 않았으며, 등록외5만으로 낮은 FAR를 주장하지 않는다.

### 이전 원본 영상의 수동 참조 진단 재사용

앞서 고정한 원본 영상의 user-confirmed/identifiable=yes 얼굴을 인물별·1초별로 고른 개별 참조와 비교했다. 이번 두 영상의 22개 답변은 참조에 한 개도 추가하지 않았다. 이전15개 진단 결과는 그대로 보존하고 새7개만 같은 방법으로 계산했다. 새 ML은 없다.

| 모델 | 등록사진 평균 최근접 | 수동 영상 개별 최근접 |
|---|---:|---:|
| SFace |7/11|8/11|
| AuraFace |7/11|3/11|
| Intel0095 |7/11|7/11|

참조자료와 평균/개별 비교법이 동시에 달라지는 원인 진단이다. 자동 성능/제품 제안/확정 성공 수가 아니며 영상참조의 거부 기준도 정하지 않았다. 참조만 바꿔서 일관되게 개선되는 근거가 없다.

## 4. 검증과 남은 일

- import boundary8tests RED→GREEN, 기존 holdout/adapter/report 포함34tests 통과.
- 기존·새83입력 hash 확인, 기존15행과 결과/진단 보존, 세 모델 space/config/reference/policy 불변.
- centroid330거리 scalar 검산 최대차8.958733532793417e-08; 새 영상참조1,533거리 최대차5.551115123125783e-16; 순위/거부 사유/전체 분모 확인.
- 브라우저에서 요약표·하니16/다니엘17/등록외19·원본/정렬 이미지·거리 펼치기·이전/다음/요약 복귀 확인. 사용자 정답 폼/저장값은 수정하지 않았다.
- 제품 전체회귀·배포모델 부팅·Mac/Windows패키징·전체 안무 구간 품질은 이번 범위에서 미검증이다.

현재 사용자가 다시 입력할 작업은 없다. 이 평가자료를 새 기준의 튜닝 데이터로 재사용하지 않는다. 향후 개선은 W13이 선택한 동일한 메인 범위 내 얼굴 입력 확보/선명한 시점 선택의 통제 비교가 후보이며, 기존 첫·중간·끝/표본누락 수정과 구별해야 한다. 이번 결과만으로 그 개선 방향의 성능을 입증한 것은 아니다. 혜인·하니의 식별 가능한 별도 촬영 정답과 최종 구간 검증은 여전히 부족하다.

## 5. W13 공통 계약·소유권

W14는 공통 얼굴 API/평가/fixture, W13은 기존 main/mapping/crop/소비adapter 소유를 유지한다. 제품 소비 변경 요청은 없다. W14공개계약·fixture→W13동일인scope/실패compatibility→소비adapter·선택venv→Mac arm64/Windows x64패키징→합의merge 순서를 유지한다. 새 모델·임베딩·cache·threshold를 서로 섞지 않았으며 이번 결과를 상호계약 승인이나 통합 완료로 간주하지 않는다.

## 6. 독립 리뷰

Critical/Important0, 진단 보고서로 적합 판정. 83/51/38 input hashes, 원문 bytes, 7원본 crop/PTS, 330+1533거리, 판정·분모, 기존15 보존,34tests를 독립 확인했다. Minor1: 계획의 이전15/추가7 별도 결과표는 HTML에서 별도 표로 구현하지 않고 서술/통합표/원문JSON에 남겼다. 표시 개선은 후속으로 남긴다.

리뷰가 판단하지 않은 항목: 브라우저는 부모가 검증; 인물정답 자체는 사용자답변 유지; 실제ML 재실행/역사적 호출 수 전체 관찰은 하지 않고 저장로그·호출상한·결과를 검증; 제품채택/FAR/일반화/Windows/전체안무구간은 주장하지 않음; 기존pyproject/uv.lock 변경의 시점은 부모의 시작status와 작업범위로 보존하되 독립리뷰가 시작diff까지 비교한 것은 아님. 해당 범위를 넘겨 해석하면 품질/변경 소유권을 잘못 설명할 위험이 있다.
