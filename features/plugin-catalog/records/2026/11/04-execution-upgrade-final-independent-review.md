# 구현 후 새 별도 세션 독립 검증

최신 결론: 처음 발견한 P2는 최소 수정 후 같은 별도 세션에서 해결을 재확인했다. 추가 확정 결함 없음. dev 병합·커밋·배포는 수행하지 않았다. 아래는 최신 재검증을 먼저, 최초 검증 기록을 뒤에 보존한다.

## 최신 수정 재검증

Adlight plugin execution upgrade — P2 최소 수정 독립 재검증
검증일: 2026-11-04 (Asia/Seoul)
판정: 앞선 독립 검증에서 지적한 P2는 해결됨. 이번 수정 범위에서 추가 확정 결함은 발견하지 못함.

검증 범위 및 동일성
- 제품 소스 수정은 explainer-flow.store.ts, 테스트 수정은 colocated explainer-flow.store.spec.ts 두 파일뿐임을 이전/v2 diff의 모든 diff --git block 비교로 확인했습니다. 앱의 나머지 tracked/untracked diff block은 동일했습니다.
- 나머지 세 저장소는 기존 전달 diff의 git apply --check --reverse가 계속 성공했습니다.
- 앱 최신 v2 패키지도 현재 파일에 reverse-check 성공했습니다.
- /tmp/adlight-plugin-final-verification-clipper_angular-v2.diff SHA256: a1928ccdf4a6c8d0f56e3ad43ac102eacb6870371d86547f91fb14f6e9d0878b
- 앱 git diff --check exit 0.
- 읽기 전용 검증을 유지했습니다. 소스/테스트/설정/브랜치 수정, commit/push/merge, 실제 회원/DB/PG/외부 생성 호출, 새 에이전트/채팅 생성, 타 세션 메시지 발송은 하지 않았습니다. /tmp 재검증 로그/스크립트/보고서만 작성했습니다.

수정의 타당성
- /Users/jina/project/adlight/desktop/clipper_angular/src/features/shortform/pages/shortform-explainer-page/explainer-flow.store.ts:938
  resumeAutopilot에서 stageHasNoNewWork(stage, true)로 자동 진행 문맥을 명시합니다.
- 같은 파일 :2000 및 :2014-2021
  직접 startKeyframes와 ingredient_review의 자동 이어가기는, ready keyframe 유지 후 pending 변화 그림만 새로 만드는 서버 규칙과 일치합니다. failed/missing/stale 변화 그림은 이 전환에서 생성하지 않으므로 단위 유료 quote로 차단하지 않습니다.
- keyframe_review/video_review의 자동 진행은 서버 missingPicturesStep/changeFramesToRedo가 failed/missing/stale 변화 그림을 개별 재생성할 수 있으므로 ready+assetId를 요구하는 별도 경로를 유지합니다. 이 유료 재시도를 무료로 잘못 분류하지 않습니다.
- 서버 근거 재확인:
  /Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/shortform/application/explainer-visuals.ts:158-168, :366-382
  /Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/shortform/application/explainer-edits.ts:40-42
  /Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/shortform/domain/explainer-autopilot.ts:52-63, :93-99
  /Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/shortform/application/explainer-autopilot.ts:323-337, :500-505
- 개별 makeChangeFrame/regenerateKeyframe/reviseKeyframe은 이 무료 전환 판정을 사용하지 않고 기존 charged:true -> fresh quote 경로를 유지합니다. pending 변화 그림도 계속 유료 판정입니다. 이번 수정으로 admission/차감/환불/실행 동의 로직은 바뀌지 않았습니다.

독립 실행 결과
1. 이전 독립 재현 스크립트 그대로 재실행: PASS, exit 0
   명령: /Users/jina/.nvm/versions/node/v22.22.3/bin/node /tmp/adlight-independent-zero-work-repro.cjs
   로그: /tmp/adlight-independent-fix-repro.log
   실제 결과:
   natural failed run: ingredient_review failed
   frontend stageHasNoNewWork(keyframes): true
   backend actual result: keyframe_review billing calls: [] image calls: 0
   따라서 원래 재현했던 앱/서버 무료 전환 불일치는 사라졌습니다.

2. 수정 대상 store Karma 스위트만 독립 실행: 282/282 SUCCESS, exit 0
   cwd: /Users/jina/project/adlight/desktop/clipper_angular
   명령: NG_BUILD_MAX_WORKERS=2 /Users/jina/.nvm/versions/node/v22.22.3/bin/node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless --include='src/features/shortform/pages/shortform-explainer-page/explainer-flow.store.spec.ts'
   로그: /tmp/adlight-independent-fix-tests.log
   localhost/Chrome가 필요한 mock 테스트만 승인된 환경에서 실행했습니다.
   PLUGIN_NOT_ALLOWED/INSUFFICIENT_CREDITS 양쪽의 직접/자동 무료 전환, 이후 단계 자동 유료 재시도, pending 변화 그림 대조, 개별 make/redo/revise 유료 대조를 포함한 새 회귀 9개를 읽고 독립 실행했습니다.

3. 추가 독립 상태 조합 대조: 18/18 PASS, exit 0
   명령: /Users/jina/.nvm/versions/node/v22.22.3/bin/node /tmp/adlight-independent-fix-matrix.cjs
   로그: /tmp/adlight-independent-fix-matrix.log
   현재 TS의 실제 판정 함수를 추출/변환하고 실제 compiled backend nextAutopilotStep/isChangeFramePending와 비교했습니다.
   조합: ingredient_review/keyframe_review/video_review x 변화 그림 missing/pending/failed/stale/ready-no-asset/ready-with-asset.
   모든 조합에서 즉시 무료 전환과 실제 유료 그림 retry 구분이 일치했습니다.

구현자 검사 증거와 한계
- 구현자의 /tmp/adlight-plugin-desktop-failed-change-full.log 끝의 10,769/10,769 SUCCESS를 직접 읽었습니다. 이전 전체 스위트 간헐 실패 이력은 기존 보고서에 남아 있습니다.
- 이번 독립 세션에서 전체 10,769 테스트와 build/types/styles를 중복 실행하지 않았습니다. 전체 테스트 green, focused362 및 packaged build/types/style21 결과는 구현자 증거이며, 독립 재실행 결과는 위 282개와 서버 재현/18조합입니다.
- 실제 PG/외부 생성/운영 DB/다중 계정 종단 간/앱 화면 시각 검증을 수행하지 않았습니다. 이전 독립 보고서의 일반 검증 한계는 계속 유효합니다.
- 실제 서버 재현과 상태 조합 검사는 기존 dist를 사용했고, 대상 서버 소스가 이전 snapshot과 동일함을 확인했습니다.

최종 결론
- 원래 P2를 해결하는 최소 수정으로 확인합니다. 유료 개별 재생성 및 이후 단계 자동 retry 경계를 훼손한 증거는 없습니다.
- 현재 재검증 범위에 남은 확정 결함은 없습니다. 이전 보고서의 “P2 미해결” 판정은 이번 수정 snapshot에서는 이 재검증 결론으로 대체됩니다.
- 이 세션에서는 병합/커밋/배포를 실행하지 않았습니다.


## 최초 구현 후 검증 (P2 수정 이전 이력)

Adlight plugin execution upgrade — 최종 working tree 독립 검증
검증일: 2026-11-04 (Asia/Seoul)
검증자: 별도 읽기 전용 검증 세션

판정
- 현재 상태를 요구사항 전체 충족/병합 준비 완료로 판정하지 않습니다. 확정 P2 1건이 남아 있습니다.
- P1은 발견하지 않았습니다. 아래 P2 외에는 이번 소스 추적과 대상 테스트에서 확정할 추가 결함을 찾지 못했습니다.
- 주요 권한 검사·기존 구독 변경·멱등 복구·동의 분리 경로는 확인했습니다. 모든 조합의 실제 운영 통합 검증을 했다는 뜻은 아닙니다.
- 코드/테스트/설정/문서/브랜치 수정, commit/push/merge, 실제 회원/DB/PG/외부 생성 호출을 하지 않았습니다. 추가 에이전트/채팅 생성과 타 세션 메시지 발송도 하지 않았습니다. /tmp 보고서·검증 로그·재현 스크립트만 작성했습니다.

확정 결함
[P2] 실패한 변화 그림 때문에 실제 생성량 0인 무료 장면 그림 단계 이동이 유료 견적으로 차단됨
- 변경 파일: /Users/jina/project/adlight/desktop/clipper_angular/src/features/shortform/pages/shortform-explainer-page/explainer-flow.store.ts:2015
- 호출 경로: 같은 파일 startStage:993 -> stageHasNoNewWork:2000 -> checkPermission:2024 -> allowQuote:2029.
- 조건: 프로젝트가 ingredient_review이고 모든 장면 keyframe은 ready + assetId이며, motion=video/videoMode=change 장면의 changeFrame이 failed. 잔액이 단위 그림 가격 미만이거나 현재 이용권에서 플러그인이 비허용이면 발생합니다.
- 이 상태는 인위적인 불가능 상태가 아닙니다. 기존 ready 장면들에 남은 pending 변화 그림만 생성하다 모두 실패하면, 서버가 변화 그림 failed를 저장하고 ingredient_review로 되돌립니다. 이 자연스러운 실패 흐름도 실제 compiled ExplainerService와 기존 mock fixture로 독립 재현했습니다.
- 서버의 startKeyframes는 ready keyframe은 유지하고 pending 변화 그림만 toMake에 셉니다. 따라서 위 상태는 toMake=0, billing.start 없이 keyframe_review로 이동합니다.
  서버 근거: /Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/shortform/application/explainer-visuals.ts:161-168 및 :366-382; /Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/shortform/application/explainer-edits.ts:40-42.
- 그러나 앱 :2015는 변화 그림이 없거나 stale이거나 ready+assetId일 때만 무료라고 판정합니다. failed는 false가 되어 :993의 단위 유료 quote를 실행하고, PLUGIN_NOT_ALLOWED/INSUFFICIENT_CREDITS이면 무료 단계 이동 API 자체를 부르지 않습니다. “만들 그림 0인 무료 전환을 유료 단위 견적으로 막으면 안 됨” 요구 위반입니다. resumeAutopilot의 같은 keyframes 무료 판정에도 영향을 줍니다.
- 최소 수정: 단계 이동/자동 진행에서 새로 생성할 대상의 판정을 서버의 withPendingKeyframes + isChangeFramePending와 일치시킵니다. 이미 ready인 장면의 failed 변화 그림을 이 단계가 새로 그리지 않는 한, 이 상태 때문에 단위 유료 quote로 차단하지 않아야 합니다. 개별 makeChangeFrame/재생성/요청 수정은 기존대로 유료 견적·서버 admission을 유지해야 합니다.
- 회귀검사: 자연 실패 후 ingredient_review + ready keyframes + failed changeFrame에서 비허용/잔액0 unit quote가 있어도 startKeyframes가 호출되고 keyframe_review로 무료 이동하는지, 같은 상태의 autopilot continuation도 가능한지 확인. pending 변화 그림은 계속 유료이며 개별 변화 그림 재생성은 계속 차단되는 대조 사례 유지.
- 독립 재현: /tmp/adlight-independent-zero-work-repro.cjs 및 /tmp/adlight-independent-zero-work-repro.log.
  실제 출력:
  natural failed run: ingredient_review failed
  frontend stageHasNoNewWork(keyframes): false
  backend actual result: keyframe_review billing calls: [] image calls: 0
- 재현 방식: /tmp 스크립트가 기존 서버 test helper를 사용해 실제 dist 서비스를 실행했습니다. 앱 private 판정 함수는 현재 TS 소스에서 추출하여 TypeScript로 변환해 동일 프로젝트에 적용했습니다. 앱 전체 UI 재현을 새로 수행한 것은 아닙니다.

검증 대상의 동일성
- 네 저장소 모두 feat/plugin-execution-upgrade 확인.
- 전달받은 manifest의 SHA256 네 항목 모두 실제 diff 파일과 일치:
  clipper_web_api e2932d5f10143eea2018757e21cd0125c50bcf2db606646475eb3fa86e9a5519
  clipper_web_client e682add1f41a521c46ba0bbe4c6316a29bd4ccae0c7509288db7782166725984
  clipper_nestjs 7cc75a56f385e20e34c46de9229bd08fdcdaaf013b2053311aaa0a77614cdb32
  clipper_angular 77541f03e2ace02d107407cf7244bec87c1c20576e64cf26926238041dc1b68a
- 네 저장소 각각 git apply --check --reverse <전달된 diff> 성공. 미추적 plugin-upgrade.service/interceptor 및 spec 네 파일까지 현재 작업 파일과 일치함을 확인.
- 종료 전 동일 검사 재실행도 모두 성공. 네 저장소 git diff --check 모두 exit 0.
- .codex/AGENTS.md 및 네 repo CLAUDE.md를 읽었으며, 현재 코드/실제 테스트를 기준으로 판단했습니다.

요구사항별 확인
1. 설치/진입, 권한 우선
- pluginInstalledGuard는 설치 상태만 검사하고 플러그인 이용 요금제를 검사하지 않습니다. Store 설치 경로도 이용권 안내와 설치 동작이 분리되어 있습니다.
- web API OperationsService.start는 새 attempt에 대해 resolveForExecution/유저 잠금으로 plugin 허용 여부를 확인한 뒤 run 생성/credits.consume을 수행합니다. PLUGIN_NOT_ALLOWED 응답은 pluginKey/operationKey를 포함합니다.
- quote는 effective access를 먼저 읽고 balance를 읽으며, 양쪽이 불충족일 때 PLUGIN_NOT_ALLOWED를 우선 반환합니다.
- desktop WebApiClient의 403 안전한 metadata 전달, 공통 guard/interceptor와 ErrorNotification 경로를 확인했습니다.

2. 웹 공유 요금제 카드와 정책
- 랜딩/요금제는 PricingCatalog/PlanCard/PricingCheckoutService를 공유합니다.
- effective access와 실제 subscription을 분리해 읽고 exact billingProductCode 현재 이용 중, scheduled target, rank 상향/하향 예약, 연간->월간 금지를 표시합니다.
- 선택 시 API를 다시 조회하여 변경/신규/관리 경로를 결정합니다. 서버의 classifySubscriptionPlanChange 정책(하향 scheduled, 연간->월간 forbidden)과 대조했습니다.
- /catalog/plugin-plans는 판매 상품 카탈로그와 별개로 활성 이용 등급을 반환합니다. /pricing?plugin은 정확한 허용 집합과 판매 상품이 없는 허용 등급을 안내합니다. 비연속 허용 집합과 “이상” suffix 판정의 기존 summarizePluginPlans도 읽었습니다.

3. 신규 구독과 기존 구독 변경
- Free/no access는 초기 checkout. active 유료 구독은 /my?changePlan=<선택 product>로 이동합니다.
- Dashboard finishLoad는 초기 projection 완료 후 access/subscription을 새로 읽고 기존 changePlan을 호출합니다. 기존 quote -> 명시 확인 dialog -> confirmSubscriptionPlanChange 순서를 유지하며 링크 자체로 confirm하지 않습니다.
- legacy /my/payment/checkout?product 진입 시 및 초기 결제 생성 직전 재검사하고, 계정 조회 실패 시 신규 결제로 빠지지 않습니다.
- promotion/admin_plan effective access는 active 유료 구독과 구분하여 관리로 보냅니다. 서버의 신규 checkout 최종 차단/중복 진행 차단 경로도 확인했습니다.

4. 앱 재시도와 설명형 숏폼/스토리보드
- 공통 charge guard는 매 시도 새 quote를 읽고 upgrade CTA 이후 false를 반환합니다. 스토리보드의 denied quote/403 구분, 수량 유지 재확인, 결과 불명 시 원 요청 ID 유지 경로를 확인했습니다.
- 설명형 최초/단계/개별 그림 재생성/요청 수정/변화 그림/장면 영상/영상 요청 수정/전체 영상에 fresh quote 경로가 있습니다. 실제 실행 admission은 서버에 남아 있습니다.
- 동기 403과 비동기 project/event/ingredient/keyframe/changeFrame/video 오류의 PLUGIN_NOT_ALLOWED marker를 공통 안내로 보냅니다. 저장된 과거 오류 signature 중복 억제와 fresh effective access가 이미 허용하는 경우 obsolete 안내 억제도 확인했습니다.
- 저장된 숫자-only legacy quote 호환은 서버 실행 admission을 대체하지 않습니다.

5. 과금 대기/멱등 복구/환불 및 무료 동작
- OperationsService.start의 기존 clientAttemptKey replay는 새 권한 admission보다 앞에 있어 다운그레이드 후에도 이미 승인된 running attempt를 반환하며 재차감하지 않습니다.
- BillableJobAttemptCoordinator는 응답 유실을 durable key로 복구하고 원래 실행하지 못한 attempt를 환불합니다. pending/ambiguous 구분과 terminal outbox를 읽었습니다. storyboard 기존 clientRequestId 재요청도 quote보다 먼저 반환됩니다.
- 설명형 서버 복구/settle/fail 경로, script/visual/video run 기록과 환불 유지 확인. 독립 recovery 대상 테스트 30개 통과.
- 무료 최종 render retry, 재료/장면 empty transition, 이미 완료된 영상 batch의 예외는 확인했습니다. 단, 확정 P2의 failed 변화 그림 상태는 이 예외 판정에서 누락됩니다.
- 개별 재생성은 batch 무료 예외를 사용하지 않고 계속 fresh quote를 검사합니다.

6. 실행 동의, 계정/복귀/캐시 경계
- upgrade는 실행 확인 서비스와 별도 MatDialog ref를 사용하고 afterDialogClose(false)를 전달합니다. 두 dialog의 겹치는 순서 양쪽 회귀 테스트가 독립 실행에서 통과했습니다.
- /pricing?plugin 복귀 경로의 클라이언트/웹 API sanitizer는 단일 bounded plugin 인자만 허용하며 duplicate/extra/hash/외부 경로를 거부합니다. 기존 Electron bridge가 상대 경로 query를 handoff URL의 returnUrl로 전달하는 경로도 읽었습니다. Electron 소스는 수정하지 않았습니다.
- PricingCheckoutService의 user identity effect/version은 로그인 복원/계정 변경 시 이전 access/subscription을 초기화하고 이전 refresh 응답을 버립니다. 창 focus/bfcache 재조회와 checkout 실행 전 재조회 확인.
- 여기까지는 소스/대상 테스트 확인이며, 실제 서로 다른 계정 로그인 전환과 운영 쿠키/딥링크의 종단 간 검증은 하지 않았습니다.

독립 실행 테스트 (전부 최종 working tree 대상)
A. 웹 API: 4 suites / 155 tests PASS, exit 0
- cwd: /Users/jina/project/adlight/web/clipper_web_api
- PATH=/Users/jina/.nvm/versions/node/v24.19.0/bin:$PATH npm test -- --runInBand --runTestsByPath src/modules/operations/application/operations.service.spec.ts src/modules/auth/application/web-return-url.spec.ts src/modules/payments/domain/subscription-plan-change-policy.spec.ts src/modules/operations/presentation/operations-openapi-contract.spec.ts
- 로그: /tmp/adlight-independent-web-api-tests.log

B. 로컬 API: 194 tests PASS, exit 0
- cwd: /Users/jina/project/adlight/desktop/clipper_nestjs
- PATH=/Users/jina/.nvm/versions/node/v22.22.3/bin:$PATH node --test test/explainer-script-stage.test.js test/explainer-video-stage.test.js test/explainer-visuals-stage.test.js test/storyboard-batch-service.test.js test/web-api-client.test.js
- 로그: /tmp/adlight-independent-local-api-tests.log
- 최초 sandbox 실행은 localhost listen EPERM으로 176 pass/18 fail이었음. 코드 실패로 분류하지 않았고 승인된 환경에서 동일 명령 재실행하여 194/194 통과. 외부 실서비스 호출 없음.

C. 로컬 과금 복구: 30 tests PASS, exit 0
- 같은 cwd/runtime, node --test test/billing-start-recovery.test.js test/billable-job-attempt-coordinator.test.js test/web-api-operation-run.test.js test/shortform-operation-run.test.js
- 로그: /tmp/adlight-independent-recovery-tests.log

D. 앱: 496 tests PASS, exit 0
- cwd: /Users/jina/project/adlight/desktop/clipper_angular
- NG_BUILD_MAX_WORKERS=2 /Users/jina/.nvm/versions/node/v22.22.3/bin/node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless --include='src/shared/operations/*upgrade*.spec.ts' --include='src/shared/operations/operation-charge-guard.service.spec.ts' --include='src/features/shortform/pages/shortform-explainer-page/explainer-flow.store.spec.ts' --include='src/features/template-builder/components/template-builder-editor/template-builder-editor.component.spec.ts'
- 로그: /tmp/adlight-independent-desktop-tests.log
- 승인된 테스트 환경 사용. 변경 기능과 알려진 실패 컴포넌트를 함께 포함. 전체 앱 스위트 재실행은 하지 않음.

E. 웹: 148 tests PASS, exit 0
- cwd: /Users/jina/project/adlight/web/clipper_web_client
- NG_BUILD_MAX_WORKERS=2 /Users/jina/.nvm/versions/node/v24.19.0/bin/node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless --include='src/app/features/public/pricing/pricing-checkout.service.spec.ts' --include='src/app/features/portal/dashboard/dashboard.component.spec.ts' --include='src/app/features/portal/payment-checkout/payment-checkout.component.spec.ts' --include='src/app/features/public/pricing/pricing.component.spec.ts'
- 로그: /tmp/adlight-independent-web-tests.log
- 앱 Karma 종료를 확인한 후 직렬 실행. 실제 결제 없음.

전체 앱 실패와 남은 검증 한계
- 구현자 최종 전체 앱 결과는 10,759 pass / 1 fail이며 이를 green으로 바꾸어 보고하지 않습니다.
- 실패 위치는 변경되지 않은 TemplateBuilderEditorComponent spec:1651, notify.calls.mostRecent().args입니다. 독립 실행에서는 해당 컴포넌트 스위트를 새 기능 스위트와 함께 포함해 496/496 통과했습니다.
- 소스상 handleAddBackgroundFile은 createBackgroundThumbnail(createImageBitmap/canvas.toBlob)를 await한 뒤 backgroundApi.add 실패를 거쳐 showToast를 호출합니다. 해당 spec의 flushUntil은 최대 20회 짧은 polling 뒤 조건 미충족도 그대로 반환합니다. notify spy 호출 자체가 없는 실패는 이 비동기 thumbnail 완료 전 단언과 부합합니다. 새 ErrorNotificationService의 plugin marker 분기는 showToast 호출 이후에만 실행되고 이 테스트의 500 'disk write failed'에는 해당하지 않습니다.
- 따라서 변경 feature가 이 실패를 일으켰다는 증거는 찾지 못했고, 문서에 기재된 기존 async flake와 일치합니다. 하지만 같은 전체 실행 조건에서 baseline A/B를 실행하지 않았으므로 변경과 완전히 무관함을 실험적으로 확정하지는 못합니다. 전체 스위트의 비결정성은 미해결입니다.
- 이전 Store 3px 레이아웃 및 다른 tiny PNG 업로드 실패는 구현자 보고만 참고했으며 이 세션에서 재현하지 않았습니다.
- 웹 build 512.08 kB / budget 500 kB, 12.08 kB 경고는 구현자 보고 기준이며 이 세션에서 build/baseline 크기 비교를 새로 하지 않았습니다. 회귀 유무는 미확인입니다.
- 실제 PG 차액 결제/즉시 구독 반영, 실제 회원/DB, 외부 그림·영상 생성, 앱->Electron->웹 handoff 전체와 다크/라이트 화면 시각 검증은 수행하지 않았습니다. Parent의 Playwright 결과는 독립 검증으로 재주장하지 않았습니다.
- 이미 생성된 final dist를 사용하는 로컬 node:test이며, 이 세션에서는 읽기 전용 범위에 맞춰 rebuild하지 않았습니다. 핵심 P2 서버 로직은 실제 src와 dist 양쪽의 결과를 대조했습니다.

다음 처리
- 위 P2를 주 세션에서 최소 수정하고 관련 회귀검사를 수행한 뒤 변경 범위를 재확인해야 합니다.
- 본 보고서는 현재 동결된 snapshot에 대한 검증 결과입니다. 수정 후 새 상태의 요구 충족/병합 판단을 대신하지 않습니다.


P2 수정 재검증 (2026-11-04)
앞선 확정 P2는 최신 v2 snapshot에서 해결됨을 독립 확인했습니다. 대상 store282/282 PASS, 기존 자연 실패 서버 재현에서 frontend true/backend keyframe_review/billing[]/image0, 상태18조합 서버 판정 일치. 수정 범위 추가 확정 결함 없음. 세부 증거/한계는 /tmp/adlight-plugin-postimplementation-fix-verification.txt 참조. 이전 P2 미해결 판정은 이 재검증 결과로 대체됩니다.
