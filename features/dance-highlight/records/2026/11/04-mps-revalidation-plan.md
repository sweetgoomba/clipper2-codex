# MPS 복구 후 통합 앱 재검증 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 공통 가속 담당 세션에서 MPS 시작 실패를 해결한 최신 원격 dev를 원본 저장소에서 빌드하고, 같은 세 YouTube 영상의 실제 GPU 사용·시간·품질을 검증한다.

**Architecture:** MPS 근본 원인과 공통 런타임 수정은 기존 「하이라이트 GPU·ONNX 전환 및 Windows 시험 도구 감사」 세션이 소유한다. 이 세션은 증거 전달·수정 결과 검토·원본 dev 빌드·제품 앱 실측을 소유한다. 기존 품질 변경과 원래 결과·교정본을 보존한다.

**Tech Stack:** Electron/Nest/Angular, Python/PyTorch MPS/공통 accelerators, 기존 앱 UI와 저장 진단 JSON.

**Spec:** 사용자 2026-11-04 후속 지시와 [직전 통합 dev 실측](04-quality-dev-merge-and-app-results.md).

## Global Constraints

- 추가 고비용 SAM/mask/joint 몸 추적 OFF.
- 인물 하이라이트 분류·구간 정책 및 검증된 안무 품질 정책 보존.
- 앱 빌드는 세션 작업트리가 아닌 원본 desktop 저장소 dev에서 수행.
- 입력은 기존 YouTube URL3개와 동일 대표 이미지. 크레딧 사용은 기존 사용자 승인 유지.
- GPU 이름/제공자만으로 성공 판정 금지. 실제 GPU 추론과 CPU 재분석 여부를 확인.
- 측정 중 대량 테스트·다른 모델 벤치·추가 빌드 금지. 원본 프로젝트와 교정본 덮어쓰기 금지.

## Review Focus

- 메모리 부족·adapter busy·identity·실제 backend 오류가 같은 사유로 뭉개지지 않아야 한다: 담당 세션의 재현/회귀 검사 확인.
- admission을 우회해 GPU 성공을 위장하지 않아야 한다: 담당 세션의 안전 여유·실제 압력 테스트 확인.
- 포맷/실행기 변경이 얼굴·메인·구간 품질을 흔들지 않아야 한다: 전후 실제 입력/대표 이미지·타임라인 비교.
- 예전 venv/패키지 소스가 실행되면 안 된다: 빌드160개 및 실행 모듈50개씩 해시 대조.
- GPU 실패를 숨긴 CPU 결과를 속도 성과로 보고하지 않아야 한다: 각 job의 attempt/fallback/models와 실제 실행 증거 확인.

### Task 1: 공통 담당 세션의 원인·수정 회수

- [x] 사용자 지시·실측3개·진단 소실 경로·메모리 가설과 한계·보호 범위를 전달.
- [x] wait_threads cursor를 사용해 진척/완료를 읽는다. 최종 원인과 실제 GPU 검증·회귀 결과·원격 dev SHA를 검토한다.
- [x] 확정 근거가 부족하면 같은 담당 세션에 구체 확인을 이어 요청한다. GPU 구현을 여기서 중복하지 않는다.

### Task 2: 원본 dev 동기화와 빌드

- [x] desktop 네 저장소 branch/status/HEAD와 원격 dev를 확인한다. 로컬 변경을 보존하며 dev를 fast-forward한다.
- [x] Python9a9a940 품질 조상, Angular4150871c 지도 복구, 몸 추적 OFF가 유지되는지 diff로 확인한다.
- [x] 원본 Electron에서 Node24.19 PATH로 npm run build:app:mac:arm64:local-api를 실행한다. 종료0과 패키지 소스 일치를 확인한다.
- [x] 기존 앱을 정상 종료한 뒤 기본 dist-app의 새 앱을 실행한다. 로그인·API·실행 코드 확인.

### Task 3: 제품 앱 세 YouTube 실행

- [x] MMN https://youtu.be/BZDZBUyaJbA, ANT https://youtu.be/p_XdZdg9oGc, NEON https://youtu.be/93j1fDGi_-8 를 동일 대표 이미지로 정상 UI 실행한다.
- [x] 신규3개 job ID를 evidence/state.json after_jobs에 기록한다. 큐 제외 startedAt→finishedAt과 실제 가속 진단을 수집한다.
- [x] 3개 모두 완료하고, 성공한 GPU 추론 증거/CPU 재분석 유무/몸 추적OFF를 확인한다. 실패하면 완료로 보고하지 않고 담당 세션과 원인을 해결한다.

### Task 4: 품질·시간 비교와 기록

- [x] 입력 소스·대표 이미지 해시, packaged/source/runtime 모듈 해시를 대조한다.
- [x] 14개 사용자 확인 구간과 MMN50.673단체→50.834허윤진/102.99홍은채, ANT64초 지원suffix·171초 미확인 경계, NEON78초시리·150/183초단체를 비교한다.
- [x] 전체/멤버 1초 미만·미확인·멤버별 개수·중첩·타임라인 차이를 계산하고 차이가 정확도 개선인지 별도 판단한다.
- [x] 전후3개 절대 시간과 합계, 실제 GPU/CPU 및 남은 문제를 새 기록에 정리하고 feature README를 갱신한다.

### Task 5: 정밀도 후속 진단의 우선순위 조정

- [x] 같은 입력·코드·실제 MPS 완료 상태에서 ANT9.9098–10.276933초가 사용자 확인 김채원에서 미확인으로 바뀐 것을 기록했다.
- [x] 담당 세션의 읽기 검토로 FP32/FP16 차이와 좌표·얼굴 근거 전파를 확인했다. 정밀도 단독 인과는 미확정이다.
- [x] 더 최근 실제 사용자 메시지(`01a1a270-caed-71c1-865a-75f5cf117c33`)의 “기존 품질과 완전히 같지 않아도 돼. 지금 가장 중요한건 실행 시간을 단축시키는거라고”를 확인하고 계획에 반영했다.
- [x] 작은 차이만으로 정밀도 수정·전체3영상 추가 재실행을 완료 조건으로 붙이지 않는다. 최종3영상 GPU·시간·품질 근거를 기존 GPU 담당 세션에 전달했다.
- [x] 원본8개 최신dev Mac/Windows 새 빌드와 큰 CPU 병목 개선은 새 사용자 요청을 받은 담당 세션이 일원화한다. root는 중복 빌드·모델 시험을 진행하지 않는다.

정밀도 영향 분리와 품질 회귀는 여전히 남은 과제이며 해결됐다고 표시하지 않는다. [직접 지시와 조정 근거](04-mps-revalidation-evidence/latest-user-priority.json). 요청한 MPS 시작 복구·원본dev 빌드·동일3영상 실제 사용/시간 재검증은 완료했다. [최종 결과](04-mps-revalidation-results.md).
