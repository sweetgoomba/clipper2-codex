# 하이라이트 idle 교정과 후보 순환 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. 기존 승인 설계의 T08/T14 미연결 경로를 구현한다. 사용자 지시로 추가 승인 질문 없이 끝까지 실행하며 커밋하지 않는다.

**Goal:** 실제 앱이 foreground 작업을 우선하고, idle에서만 최대 120초/후보 2개씩 교정하며 GPU/실행기별 결과를 저장·순환하고 다음 분석 단위에만 선택을 적용한다.

**Architecture:** Electron이 idle owned process와 foreground admission을 소유한다. Python은 기존 calibrate의 품질/예산 정책을 실제 session/fixture/지속 queue에 연결한다. 준비된 immutable runtime 목록을 열거하고 각 backend의 실제 adapter index를 사용한다. 기존 명시 기기 시험에서 원래 CPU 입력/출력을 로컬 한정·크기 제한·hash 봉인해 교정 프로필로 수집한다. release fixture/catalog가 공급되면 동일 경로로 인증 교정을 수행하며, 개발 기기 시험의 성공은 release 권한을 만들지 않는다.

**Tech Stack:** 현재 Electron/Node TypeScript, NestJS, Angular, Python3.11/기존 worker protocol.

**Spec:** `/Users/jina/project/adlight/.codex/operations/accelerators/records/2026/11/03-highlight-auto-acceleration-design.md` §idle/선택/인증/결과 보존.

## Global Constraints

- Apple Silicon Mac / Windows x64, 기존 네 분리 작업 트리 재사용. 원본 desktop/공유 venv/실행 중 앱/작업 중 변경을 수정·재설치·종료하지 않음.
- 모델 가중치·전후처리·임계값·샘플링·Whisper small/beam5/VADoff/word timestamps 유지. 신규 release 인증/허용 오차 완화 금지.
- User job은 idle 종료 확인 후 시작. 실패/취소 partial row를 complete로 쓰지 않음. 선택은 다음 unit부터 고정.
- 120초 회차, 시각 후보30초/음성60초, CPU+후보 최대2개, 나머지 GPU/runtime/workload 순환 cursor 지속. 실패/timeout=deferred/실패 기록; 0ms 합격 금지.
- optional 패키지 자동 설치 금지. 준비된 호환 immutable runtime들만 후보. 새 Windows CUDA 등은 hash lock과 명시 준비로만 설치.

## Interfaces

- 준비된 inventory: `home/active-runtimes.json`: `{schema:1,runtimes:[{...기존 ready active-runtime row}]}`. legacy `active-runtime.json` 호환 유지.
- Idle CLI: `python -m clipper_accelerators.idle --home HOME --plugin PLUGIN --budget 120`. 한 회차만 실행, owned parent가 foreground 시 process tree 종료. runtime worker와 모든 자손의 종료 확인 필요.
- Python queue/status: `home/idle/PLUGIN/status.json`, `{schema:1,state,pending:boolean,...}`. 새 프로필/계속할 후보가 있으면 pending=true. profile/입력/expected/환경/pack/candidate별 hash를 고정하고 cursor와 완결 측정 row를 원자 저장.
- Electron foreground: `POST /accelerators/foreground` begin `{action:'begin',plugin,job_id}` → `{lease_id}`; end `{action:'end',lease_id}`. begin은 idle 종료 확인 뒤 반환. 같은 job 중복/동시 begin과 cleanup 실패를 시험.
- Electron idle: `GET /accelerators/idle`, `POST /accelerators/idle` `{plugin}` 재교정 예약. runtime 상태에도 idle 상태를 포함. CPU 설정은 해당 plugin 교정 중단/보류.
- N 실제 factory/LocalPluginJobRunner는 foreground begin을 runtime 준비보다 먼저, end를 모든 성공/실패/취소 finally에서 호출. headless/bridge unavailable 정책은 CPU 안전 경로 유지, cleanup 거절은 무시하지 않음.

## Review Focus

1. 새 사용자 분석과 idle 시작이 경합해도 foreground 승리; CPU/worker 메모리가 남으면 admission 거절.
2. 다른 어댑터·같은 모델·동일 runtime/서로 다른 runtime별 cache가 섞이지 않음; driver/build/power 변경 재교정.
3. 24 distinct 시각 /3 distinct 음성 부족·손상·fixture 과대·불완결 결과는 완료/인증으로 둔갑하지 않음.
4. 재시작/취소/후속 failure가 기존 complete row와 committed 프로젝트 결과를 손상하지 않음.
5. idle 결과가 실제 다음 ModelGate/Whisper 선택까지 연결되고 실행 중 unit은 변경하지 않음.

## Tasks

### T1 Python 실제 교정·다중 후보
- [x] 기존 calibration/runtime/assets/adapters와 실제 tests를 읽고 실패하는 연결 회귀 작성·RED 저장.
- [x] hash 봉인된 로컬 fixture 수집, 실제 ONNX/CT2 세션, 준비 runtime×adapter 열거, 지속 순환/결과/재교정 구현. 기존 calibrate 사용/개선하되 production caller 없는 함수를 완료로 세지 않음.
- [x] user test와 release 승인 교정을 구분하고 다음 unit의 실제 선택 연결. 품질·시간·취소·손상·fallback 회귀 GREEN.

### T2 Electron idle 소유권과 runtime inventory
- [x] owned idle→foreground 선점/동시 요청/종료 실패/재시작/CPU 설정 RED 작성.
- [x] 실제 main/bridge에 timer, status, begin/end, shutdown, runtime inventory 연결. native process/worker 종료 확인.
- [x] read-only startup와 명시 runtime 준비 정책, 기존 GPU lease 회귀 GREEN.

### T3 NestJS 실제 foreground 연결과 설정 화면
- [x] 실제 factory/runner가 runtime 이전 begin, 완료/실패/취소 end하며 cleanup 거절을 무시하지 않는 RED.
- [x] bridge/API 연결 및 UI에 idle 예약/진행/보류/잔여 후보/자동 적용 승인 구분. 새 UX/구조를 만들기보다 기존 카드 확장.
- [x] 실제 request/WebSocket 경로와 Chrome UI 회귀 GREEN.

### T4 통합·전달
- [x] 세 도메인 code review와 실제 연결 검증, 추가 결함 RED→GREEN. 전체 Python/N/E 및 A 집중/스타일 검증.
- [x] 실제 CPU/가능한 로컬 idle smoke; 실제 GPU/다양한 corpus는 사용자 검증으로 명시.
- [x] 원본/진행 중 변경/모델 hash 보존 확인. Mac arm64 패키지와 Windows 소스/lock/안내 갱신·해시 검증.
- [x] 독립 최종 검토를 받고 지적 수정. 구현 보고서/증거/제한과 빌드 산출물 제공.

## 최종 증거

구현/검증 완료: `03-highlight-idle-rotation-implementation.md`, `03-highlight-idle-rotation-validation.json`. Mac arm64 DMG/ZIP 생성, Windows x64 소스 ZIP 4,934개 파일의 현재 소스 SHA 일치. 실기기 품질·속도·GPU 고장 매트릭스는 사용자 시험 범위이며 release 인증서를 새로 만들지 않았다.

## 독립 재검증 후속 교정 — 완료

- [x] A01 동일 FP16 raw 경계 유휴 replay와 CPU 선택 연결, 원래 foreground 결과 보존.
- [x] A02 CPU·incumbent·후보 예산 accounting/deadline 통합, 실제 소유 CPU/GPU 역할 hang 종료 회귀.
- [x] N01 승인된 다른 native adapter 실제 YOLO/CLIP owned factory/lease/정밀도/인증 연결과 엄격한 native evidence 판정. 기본 benchmark CLI의 native 전체 인수 범위는 별도 근거 없으면 BLOCKED로 명시.
- [x] N02 지정 전달 JSON을 같은 build_id로 갱신하고 실제 SHA/크기/현재 source4936개 재검사.
- [x] N03 저장 실패 뒤 실제 설정 재조회, N04 .git 파일/pytest·ruff cache 패키징 제외. native MPS 장치 표시도 교정.
- [x] 독립 검토16파일 SHA 일치, Python3379통과/기존실패6/skip5, Electron1904, Angular53/스타일21. Nest 소스 변경 없음/직전5292검사 유지.
- [x] Mac 새 DMG/ZIP 및 Windows 직접 빌드용 소스 ZIP 생성, 801개 실행 코드·자산 일치와 개인/개발 자료 제외, 기존18사용자파일·10모델 SHA 보존.

최신 보고서: `03-highlight-idle-rotation-reaudit-remediation.md`. 검증: `03-highlight-idle-rotation-validation.json`. build_id: `highlight-idle-reaudit-ba5b9bb9f46f517e`. 원 독립 감사·재검증 보고서와 재현 증거는 수정하지 않았다.
