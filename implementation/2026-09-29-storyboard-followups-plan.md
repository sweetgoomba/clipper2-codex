# 스토리보드 후속 수정 실행 계획

> For agentic workers: use Superpowers TDD, systematic-debugging and verification-before-completion. Continue within the user's authorized scope; no commit/push/merge/deploy.

Goal: W07 전체 요구를 최신 dev와 대조하고 입력/선택 오류, 프로필 관리·표시·원장 누락을 고치며 측정 가능한 성능 근거를 남긴다.

Spec: `.codex/handoff/tasks/storyboard.md` 및 Angular `docs/superpowers/specs/2026-09-21-storyboard-v2-ui-refinement-design.md` D6–D13, §5. 기존 v2 수량·프로필당 한 배치·검증·복구·정산 계약 유지.

## 제약·검토 초점

- profile delete는 batch lock(영구 수정 잠금)과 별개의 busy 판정. 실행/시작 복구/정산 대기는 삭제 차단, 완료 산출물·snapshot·legacy 데이터는 보존.
- 한글 composition 중 Enter, 마지막 목적 해제, custom 입력 전환, saving 중 이벤트를 검사.
- 순차 삭제 중 일부 실패·화면 이탈·재시도·실행 상태 전환을 검사.
- 기존 JobHistoryService의 진행률만 사용. checkpoint 저장/재시도 횟수 및 원장 수량 정산 불변.
- 실제 AI/과금 실행 없음. 실공급자 지연과 fixture/local 측정은 분리.

## 작업

- [x] 1. 폼 오류 RED→GREEN: `operating-profile-form` 실제 Material 칩 클릭과 composition 이벤트 순서로 빈 목적 시 disabled·save 미발행, 완료 한글 태그·payload 확인. 공용 imeEnter 사용, 로컬 composition lifecycle 방어.
- [x] 2. Nest 관리·레거시: profiles service/repository/controller DELETE(204, owner, busy 409) 및 crash-safe 저장. legacyCompletedCount/잠금·legacy PDF export 제거, preflight 400. 실제 임시 JSON 저장·복구·batch 보존 테스트.
- [x] 3. FE 관리·표시: profile gateway deleteProfile(id):Promise<void>; 선택 모드·전체 선택·확인1회·순차 삭제·실패 선택 유지. legacy route/viewer 제거·변환 CTA, 완료 편집 비활성+이유, 진행 미터/결과 CTA, 카드 설정 정렬·반응형. JobHistory jobs 연결·정리 및 완료 후 quiet reload 회귀.
- [x] 4. 진행 메시지: discovery/pipeline callbacks를 executor publishProgress에 전달. 조사 0.05–0.10, 이후 작성/완료 상태. 저장/취소 경계 유지 및 callback 회귀.
- [x] 5. 원장·성능: read-time operation display 명칭 수정(역사 차감/환급도 동일). 성공/실패/재시도 대기 단계 시간 로그(내용/키 제외), fixture/local benchmark 전후. 독립호출/캐시/모델 후보의 품질·비용·취소/복구/정산 위험 검토 후 근거 있는 변경만 적용.
- [x] 6. 검증: Angular 관련 Karma·AOT·스타일, Nest shortform/storyboard/billing/jobs build+tests, Web credits/inference/operations tests+build. 브라우저 fixture에서 저장 payload·삭제·다크/라이트·좁은 화면·실시간 진행 검사. 독립 diff 검토, 중요 발견 RED→GREEN.
- [x] 7. 기록: `.codex` 카드/보드/9월29일 세션·구현/측정 보고서 갱신. 다른 세션 충돌 경로 및 기준 SHA, 실행환경, 검증 한계, 남은 실기 명시.

## 기준·협업

Branch `feat/storyboard-followups-20260929`: Angular 797782e8, Nest 824a7a9f, Web API 31f4482 (fetch 2026-09-29).
Root implements FE. Backend agent owns Nest profile/legacy/progress. Performance agent owns Web ledger and Nest retry timing only; pipeline/discovery writes are backend-owned.
Existing overlaps: W10 common forms/UI/credit; W11 shell/projects; TC4 core logging/jobs (no new menu); dialog-highlight Web inference/operations/credits. Existing checkouts/worktrees unchanged.

## 실행 기록

- Baseline Angular form: 21/21 PASS. Node executable must explicitly be v24.19.0 (npm/npx can select v24.3.0); Karma/Chrome requires local-test sandbox escalation.
- Legacy policy clarification: retain all historical disk data, even when deleting a profile. D7/D12 forbid automatic destructive cleanup; UI no longer reads legacy results.

## 최종 결과·남은 실기

2026-09-29 최종 Angular 전체5395/5395, SCSS6/6, local AOT PASS; Nest build와875/875 PASS; Web 관련503 PASS/build PASS, 전체의 기존7개 실패는 원본 동일 재현. Browser fixture 입력/저장/삭제/보존/다크·라이트4폭 PASS. 독립 리뷰 확인창 대상 expansion과 in-flight cancel 계측 누락은 RED→GREEN·재검토 완료.

삭제 확인 전에 ID/보존 수 고정; 개별 busy 재검사 유지. 설정 삭제는 durable tombstone이며 역사 원본 보존. legacy viewer/라우트/PDF/잠금 철거, settingsV2 전환 CTA와400. 진행률은 JobHistory 단일 원본. 원장 read-time 표시만 추가. 목록 obsolete I/O 제거 및 feature timing 추가, provider 병렬화/모델 변경은 근거 부족으로 적용하지 않음.

- [ ] 실제 공급자의 같은 입력·수량·모델·retry/cold-warm 조건 전후 시간/품질/비용/정산 비교.
- [ ] macOS 물리 한글 키보드/Electron 설치형 IME, 전체 패키징과 실제 서버/DB/과금 실기.

브랜치/worktree와 미커밋 변경 보존. 원본3repo dev·clean·0/0. commit/push/merge/deploy/DB 실행 없음. 상세는 .codex/implementation/2026-09-29-storyboard-followups-verification.md 및 diagnostics/2026-09-29-storyboard-performance.md.
