# W01 — 대사 하이라이트 개선

최종 확인: 2026-09-29 KST. 상태: **W12 현행·팀원 diff·OCR 경로 조사 확보 / 실제 평가·선택 개선 대기**.

[전체 현황](../WORKBOARD.md) · [하이라이트 전체 조사](highlight-overview.md) · [새 세션 프롬프트](../prompts/2026-09-29-new-sessions.md)

## 이번 사용자 요구

- [ ] 민준님이 무엇을 바꿨는지 commit/date/diff·현행 동작으로 확인한다.
- [ ] 사용 기술·모델·파이프라인의 현재 구조부터 파악한다.
- [ ] 타이틀 퀄리티, STT 퀄리티, 후보/경계/요약 등 내부 로직 개선 후보를 비교한다.
- [ ] 모델이 오래됐을 것이라는 가설을 확인한다. 최신 후보를 공식 문서/논문/모델 카드의 성능·상업 이용 조건·시간·비용·자원으로 비교한 뒤 교체 여부를 정한다.
- [ ] OCR 비활성화 상태/이유와 관련 설정·실행 경로를 확인한다.
- [ ] OCR을 켰을 때 추가 리소스/시간과 출력 품질 향상 정도를 같은 입력에서 측정한다. 무조건 활성화하지 않는다.

## 기존 근거・작업 공간

[9/4 전체 감사](../../main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md) §13 개선 후보·§14 작업 공간을 과거 기준선으로 활용한다.

과거 `.worktrees/dialog-highlight-overhaul-20260904`의 5repo/`feature/dialog-highlight-overhaul-20260904`는 준비 당시 기준이다. 9/15 조사에는 준비 이후 고유 개선 커밋이 없었다. **현재 dev의 팀원 변경이 없다는 뜻이 아니며**, 이번 문서 갱신에서 해당 공간의 현재 HEAD/clean/포함 여부를 다시 조사하지 않았다.

읽기 전용 조사는 최신 dev에서 시작하고 실제 개선은 필요한 Python/Nest/Angular 및 기타 repo의 최신 origin/dev 기반 새 브랜치·격리 worktree로 진행한다.

## 다음 행동・완료 기준

W12의 전체 구조/팀원 diff/측정 계획을 받는다 → 동일 입력의 STT·타이틀·후보·OCR 기준 결과를 측정 → 병목/오류에 맞는 후보 비교 → 선택한 개선만 구현 → 전후 품질/시간/자원/비용을 기록한다.

기존 감사의 warmup/실제 load, 긴 영상 waveform/mel/STT 메모리, LLM retry/checkpoint/비용, 후보 점수·경계·진행/실패 UX도 현행에 남는지 확인한다. CPU·리소스 안전성 구현과 중복 구현하지 않는다.

## 제약・검증 상태

이번에는 코드 조사 일부와 문서 정리만 했으며 대사 ML/모델 비교·OCR 평가·Build5를 실행하지 않았다. 과거 실제 ML HOLD는 해당 세션에서 사용자가 지정한 입력/평가 범위와 대조한다. 형제 Desktop 경로 구조를 유지한다.

## W12 현행 delta와 평가 인계

[종합 조사 §3·7–8](../../features/highlights/records/2026/09/29-pipeline-design-handoff.md) · [파일·함수·민준님 SHA·감사 대조](../../features/highlights/records/2026/09/29-dialog-code-history.md) · [공식 최신 모델·교체 제약](../../features/highlights/records/2026/09/29-official-model-candidates.md) · [새 대사 세션 프롬프트](../prompts/2026-09-29-highlight-sessions.md).

- 9/18 곽민준 Python 49838e0/8bc9501은 제목 번인→원본 비율 clip+타이틀 데이터, Web API af664d7은 overlay_title·나열형 제목 repair를 추가했다. Nest/Angular raw clip 백필·상태·숏폼 생성/재편집도 현행에 있다.
- 기본은 faster-whisper small/OpenCLIP 분석과 Nest staged workflow, Web API gpt-5-mini Responses다. Python 직접 LLM 경로·다른 기능의 Gemini를 현행으로 읽지 않는다. 환경 override/서버 실제 모델은 확인하지 않았다.
- 9/4 감사의 원본 전체 timeline trim 설명은 당시 코드에도 맞지 않은 오기다. 현행은 추출 clip 내부 trim이며 원본 구간 밖 경계 확장은 별도 기능이다. Angular preview/quote → durable job·operation start → 큐 → runtime lease → Nest 실제 source ingest이며 과금 뒤 ingest가 진행된다.
- EasyOCR는 RUN_OCR=False·CUDA gate·optional dependency 부재. 상수만 켜면 Mac/packaged에서 동작한다고 가정하지 않는다. 초기화/seek/decode·text merge·evidence/token·오인식 효과를 OFF/ON으로 분리한다.
- warmup/load, 장편 waveform/mel/word/librosa, retry·artifact resume 부재·내부 title repair 호출수/credit, cancel의 실제 STT/ffmpeg 중지까지 현행 잔여 검증 항목을 상세 감사에 기록했다.
- 평가 제안: 3개×180초 이하, STT small3pass+후보 하나3pass, OCR 최대540프레임, 고정된12후보·12타이틀의 batch 비교. repair/retry 포함24provider calls·총$2 중 먼저 도달하는 상한은 제안이며 현재 승인된 예산이 아니다. 정확한 입력/라벨/device/실행 범위 확정 전 ML·download·유료 호출·Build5를 실행하지 않았다.

## 9/29 제목 변경 전후 후속 근거

[9/18 제목 지시문·조건부 보정 전후](../../features/highlights/records/2026/09/29-title-change-detail.md). 이전/이후 prompt 규칙·입출력·repair 한계와 raw clip/제목 데이터 분리를 구분한다. 실제 제목 품질 A/B는 미실행이다.
