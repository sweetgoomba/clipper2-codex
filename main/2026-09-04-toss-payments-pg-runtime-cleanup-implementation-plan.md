# TossPayments PG 런타임 정리 구현 계획

> 이 문서는 `integration/toss-payments-pg-20260903` 브랜치에서 실행할 작업을 기록한다. 실제 개발
> DB·서버에는 적용하지 않는다. 각 단계는 실패하는 테스트를 먼저 만들고, 최소 수정으로 통과시킨 뒤
> 작은 checkpoint commit으로 남긴다.

**실행 결과:** 아래 1~8단계를 모두 원본 저장소의 integration 브랜치에서 완료했다. 실제 개발 DB,
5433/5434/5435 DB, 서버에는 아무 변경도 하지 않았다.

**목표:** 현재 쓰지 않는 참고 영상 분석 등록과 스토리보드 이미지 검색 계획을 실제 실행 경로에서
제거하고, PG 전환 시 옛 개발용 이용권·크레딧·작업 기록을 의도대로 초기화하는 release candidate를
만든다.

**작업 장소:** 아래 원본 저장소에 checkout된 `integration/toss-payments-pg-20260903` 브랜치만
수정한다. `.integration-clones`와 기존 PG worktree는 건드리지 않는다.

**데이터 원칙:** 사용자 계정은 남긴다. 옛 요금제, 구매 신청, 이용권, 남은 크레딧, 유효기간,
차감·환급 기록과 과거 `operation_runs`는 새 PG 구조로 옮기지 않고 모두 초기화한다. 기존 사용자에게
무료체험이나 이용권을 소급 지급하지 않는다. 기존 사용자는 Customer 사이트에서 Toss 테스트 결제를
완료해 새 이용권과 첫 크레딧을 받아야 한다. 새 사용자만 정상 신규가입 흐름에서 무료체험을 받는다.

---

## 1. Web API: 과거 작업 실행 기록 초기화 migration

**수정 파일**

- 추가: `web/clipper_web_api/src/core/database/migrations/admin/1786850000000-ResetLegacyOperationHistory.spec.ts`
- 추가: `web/clipper_web_api/src/core/database/migrations/admin/1786850000000-ResetLegacyOperationHistory.ts`
- 수정: `web/clipper_web_api/src/core/database/admin.datasource.ts`
- 수정: `web/clipper_web_api/src/core/database/admin.datasource.spec.ts`

**쉽게 설명하면**

옛 이용권과 크레딧 장부를 없애면서 과거 플러그인 실행 기록만 남기는 것은 앞뒤가 맞지 않는다.
그래서 과거 `operation_runs`를 전부 비운다. 실행 기록을 가리키는 복구 기록
`operation_resolution_events`를 먼저 비워야 외래키 오류가 나지 않는다. 작업 종류별 현재 가격·차감
설정인 `operation_policies`는 지금 쓰는 여섯 종류만 남기고 폐기된 종류만 지운다.

남길 작업 종류:

- `shortform_url.create`
- `shortform_paste.create`
- `shortform_prompt.create`
- `dialog_highlight.extract`
- `dance_highlight.extract`
- `variation.render`

**TDD 순서**

1. migration SQL 순서를 검사하는 테스트를 먼저 추가한다.
2. 새 migration이 아직 없어서 테스트가 실패하는 것을 확인한다.
3. 자식 복구 기록 → 과거 실행 기록 → 폐기된 정책 순서로 삭제하는 migration을 구현한다.
4. datasource 목록에서 `DropLegacyBilling1786800000000` 다음,
   `CreateOperationEvidence1786900000000` 전에 등록한다.
5. migration 단독 테스트와 datasource 테스트를 통과시킨다.
6. 폐기 가능한 빈 PostgreSQL DB와 구형 fixture 복제본에서만 전체 migration을 재검증한다.

**검증 명령**

- `npm test -- --runInBand src/core/database/migrations/admin/1786850000000-ResetLegacyOperationHistory.spec.ts`
- `npm test -- --runInBand src/core/database/admin.datasource.spec.ts`
- `npm run build`

**Checkpoint commit:** `feat: reset legacy operation history for PG launch`

## 2. Web API: 현재 쓰지 않는 참고 영상 분석 API 비활성화

**수정 파일**

- 수정: `web/clipper_web_api/src/app.module.ts`
- 수정: `web/clipper_web_api/src/app.module.spec.ts`
- 수정: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/presentation/shortform-director-reference-analysis.controller.spec.ts`
- 수정: `web/clipper_web_api/src/modules/shortform-director-reference-analysis/presentation/shortform-director-reference-analysis.openapi.spec.ts`
- 수정: `web/clipper_web_api/docs/api/openapi.yaml`

**쉽게 설명하면**

참고 영상 분석 코드는 나중에 별도 플러그인으로 다시 쓸 수 있으므로 소스와 DB migration은 보존한다.
다만 지금 스토리보드가 쓰지 않으므로 서버 시작 목록에서 빼고, 현재 사용할 수 있는 API처럼 보이지
않도록 OpenAPI의 `/shortform-director/reference-video-analyses` 설명도 제거한다.

**TDD 순서**

1. AppModule과 OpenAPI에 해당 모듈·경로가 없어야 한다는 테스트로 먼저 바꾼다.
2. 기존 등록 때문에 테스트가 실패하는 것을 확인한다.
3. AppModule import를 제거하고 OpenAPI의 전용 route/schema만 제거한다.
4. 참고 분석 소스, 단위 테스트, `ReferenceAnalysisReplayEntity`,
   `1785400000000-CreateReferenceAnalysisReplays`는 그대로 남았는지 확인한다.

**검증 명령**

- `npm test -- --runInBand src/app.module.spec.ts src/modules/shortform-director-reference-analysis/presentation/shortform-director-reference-analysis.controller.spec.ts src/modules/shortform-director-reference-analysis/presentation/shortform-director-reference-analysis.openapi.spec.ts`
- `npm test -- --runInBand src/modules/shortform-director-reference-analysis`
- `npm run build`

**Checkpoint commit:** `refactor: disable unused reference analysis route`

## 3. Web API: 스토리보드의 오래된 이미지 검색 계획 제거

**수정 파일**

- 수정: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- 수정: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- 수정: `web/clipper_web_api/src/modules/shortform-director-inference/infrastructure/openai-shortform-director-inference.transport.spec.ts`
- 수정: `web/clipper_web_api/docs/api/openapi.yaml`

**쉽게 설명하면**

스토리보드는 더 이상 이미지를 검색하지 않는다. 그런데 생성 결과 형식에는 아직
`imageSearchPlan`이라는 옛 항목이 필수로 남아 있다. 이 항목과 검사 규칙, OpenAPI 설명을 제거한다.
다른 플러그인이 실제로 쓰는 공용 `/media/search`와 Naver 자격증명 코드는 삭제하지 않는다.

**TDD 순서**

1. `imageSearchPlan` 없는 스토리보드 결과가 유효하고, 오래된 필드가 계약에 포함되지 않아야 한다는
   테스트를 먼저 작성한다.
2. 현재 필수 검증 때문에 실패하는 것을 확인한다.
3. 타입, JSON schema, validator, redaction에서 스토리보드 전용 필드를 제거한다.
4. OpenAPI와 전송 계층 fixture를 같은 계약으로 맞춘다.
5. `/media/search`와 이를 쓰는 하이라이트·일반 숏폼 코드는 그대로인지 검색으로 확인한다.

**검증 명령**

- `npm test -- --runInBand src/modules/shortform-director-inference`
- `npm test -- --runInBand src/modules/media-search`
- `npm run build`

**Checkpoint commit:** `refactor: remove storyboard image search plan contract`

## 4. Desktop NestJS: 스토리보드 내부 모델에서 이미지 검색 계획 제거

**수정 파일**

- 수정: `desktop/clipper_nestjs/src/modules/shortform-director/domain/storyboard-document.ts`
- 수정: `desktop/clipper_nestjs/src/modules/shortform-director/domain/storyboard-quality-report.ts`
- 수정: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-storyboard.assembler.ts`
- 수정: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-storyboard.validator.ts`
- 수정: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-storyboard-recovery.ts`
- 수정: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-storyboard-read.adapter.ts`
- 수정: 관련 `desktop/clipper_nestjs/test/shortform-director-*.test.js` 여섯 개

**쉽게 설명하면**

Web API가 더 이상 보내지 않는 `imageSearchPlan`을 데스크톱 서버도 읽거나, 검사하거나, 실패 복구 때
가짜로 만들지 않게 한다. 기존 프로젝트 문서에 그 항목이 남아 있어도 다른 필요한 장면 정보는 계속
읽을 수 있어야 한다. 공용 미디어 검색 기능은 유지한다.

**TDD 순서**

1. 새 계약 fixture와 기존 문서 호환 테스트를 먼저 수정해 실패를 확인한다.
2. 타입·parser·assembler·validator·recovery·read adapter에서 해당 필드만 제거한다.
3. build 후 관련 Node 테스트를 실행한다.

**검증 명령**

- `npm run build`
- `node --test test/shortform-director-candidate-production.test.js test/shortform-director-run-recovery.test.js test/shortform-director-storyboard-assembler.test.js test/shortform-director-storyboard-read-adapter.test.js test/shortform-director-storyboard-validator.test.js test/shortform-director-web-api-clients.test.js`

**Checkpoint commit:** `refactor: remove storyboard image search plan handling`

## 5. Desktop Angular: 화면·복사 기능에서 이미지 검색 계획 제거

**수정 파일**

- 수정: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-storyboard.ts`
- 수정: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-storyboard.spec.ts`
- 수정: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.html`
- 수정: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.ts`
- 수정: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
- 수정: `desktop/clipper_angular/src/features/shortform-director/services/storyboard-clipboard.service.ts`
- 수정: `desktop/clipper_angular/src/features/shortform-director/services/storyboard-clipboard.service.spec.ts`
- 수정: `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-production.fixtures.ts`

**쉽게 설명하면**

스토리보드 화면의 “이미지 검색 가이드”와 검색어 복사 기능을 제거하고, 화면 모델도 새 Web API 계약과
맞춘다. 장면 설명, 내레이션, 소스 힌트 등 현재 쓰는 정보는 그대로 둔다.

**TDD 순서**

1. 모델과 클립보드 테스트를 새 계약으로 먼저 바꾸고 현재 코드에서 실패하는 것을 확인한다.
2. 모델·화면·클립보드에서 검색 계획 전용 코드만 제거한다.
3. 관련 Karma 테스트와 전체 Angular build를 실행한다.

**검증 명령**

- `npm test -- --watch=false --browsers=ChromeHeadless --include='src/features/shortform-director/models/shortform-director-storyboard.spec.ts' --include='src/features/shortform-director/services/storyboard-clipboard.service.spec.ts'`
- `npm run build`

**Checkpoint commit:** `refactor: remove storyboard image search UI`

## 6. Desktop NestJS: 최신 베리에이션 v2에 PG 과금 옮기기

**쉽게 설명하면**

최신 `dev`가 베리에이션 v1을 완전히 삭제했는데, 예전 PG 과금 코드는 그 v1에만 붙어 있었다. v1을
되살리지 않고 현재 v2의 영상 만들기에 과금을 연결한다. v2는 여러 영상 중 일부만 실패할 수 있으므로
영상마다 과금 기록을 하나씩 만들어 실패한 영상만 환급한다.

**TDD 순서**

1. 선택한 영상 수만큼 과금 기록이 생기는 테스트를 먼저 추가한다.
2. 일부 영상만 실패할 때 그 영상만 환급되는 테스트를 추가한다.
3. 과금 시작, 프로젝트 잠금, 잡 예약 중 실패하면 앞서 시작한 과금이 모두 환급되는지 검사한다.
4. 취소된 영상 환급, 재시작용 과금 ID 저장, bearer token 미저장을 검사한다.
5. 현재 v2 렌더 서비스에만 구현하고 삭제된 v1 파일은 그대로 삭제한다.

**검증 결과**

- 관련 과금·베리에이션 검사 331/331 통과
- 전체 NestJS 검사 2,116/2,116 통과
- `npm run build` 성공

**Checkpoint commit:** `19c667e merge: refresh NestJS integration from latest dev`

## 7. Desktop Angular: 베리에이션 v2 크레딧 확인과 결과 안내

**쉽게 설명하면**

사용자가 영상 만들기를 누르면 현재 체크된 영상 수로 예상 차감액을 먼저 보여 준다. 취소하면 아무
작업도 시작하지 않는다. 진행하면 NestJS가 돌려준 실제 총 차감액과 차감 직후 잔액을 안내한다.

**TDD 순서**

1. 선택 영상 수가 견적 요청에 들어가는 테스트를 먼저 추가한다.
2. 확인창 취소 시 렌더 요청·프로젝트 잠금·화면 이동이 없어야 한다는 테스트를 추가한다.
3. 방금 체크 해제한 저장이 끝난 뒤의 정확한 개수로 견적을 내는지 검사한다.
4. 성공 안내에 실제 차감액과 잔액이 표시되는지 검사한다.
5. 현재 베리에이션 v2 화면과 store에만 최소 구현한다.

**검증 결과**

- 베리에이션 v2와 공용 과금 확인 검사 550/550 통과
- 전체 Angular 검사 3,913/3,913 통과
- `npm run build` 성공
- 테스트 중에만 끈 Angular CLI cache 설정은 원복했고 commit에 포함하지 않음

**Checkpoint commit:** `7f34704b feat: forward-port variation v2 PG billing`

## 8. 최종 교차 검증과 문서화

1. 세 저장소에서 `imageSearchPlan`과 참고 분석의 활성 등록이 사라졌는지 검색한다.
2. 공용 `/media/search`와 실제 사용처가 남아 있는지 확인한다.
3. Web API 전체 test/build, NestJS 전체 test/build, Angular 전체 test/build를 새로 실행한다.
4. 빈 폐기 DB와 구형 fixture DB에서 migration 결과를 확인한다.
5. `.codex/main/2026-09-03-toss-payments-pg-release-candidate-integration-log.md`에 저장소별로
   충돌 원인, 보존 기능, 해결 방식, 테스트, 남은 위험을 갱신한다.
6. `.codex` 문서도 별도 checkpoint commit으로 남긴다.
7. `dev` merge, 서버 배포, 실제 개발 DB migration은 하지 않는다.
