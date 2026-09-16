# 옛 PG 보완 워크트리 반영 대조

## 후속 실행 — 로컬 보존 완료, push 차단으로 제거 보류

사용자 “응” 승인 후 Nest `000414f3a0ce47b3461e007311d3d3296cd8dc22`(7파일), Web API `3c33268d2b512dc33bf8b94fc122afec1cba0315`(OpenAPI1파일)로 보존 커밋했다. 메시지에 과거 draft이며 현재 통합본으로 대체돼 재병합하지 말 것을 명시했다. 두 worktree 모두 tracked/untracked clean이다.

fresh 검증: 옛 Nest build + access-credit-proxy/jobs-commit-phase/variation-v2-render-service **108 PASS, 0 FAIL/SKIP** (`/private/tmp/pg-archive-old-nest.log`). OpenAPI는 설치된 js-yaml로 parse PASS(yaml 모듈은 없어 최초 검증 명령 실패 후 js-yaml 사용). ignored는 Nest dist/node_modules 및 빈 .clipper_data 인덱스3개, API dist/node_modules. lsof cwd 검색에서 대상 worktree 사용 프로세스 없음. 이를 모든 파일 핸들/세션 사용 부재의 증명으로 확대하지 않는다.

Electron feature `7aed9f6` push는 정확한 목적지 승인 부족으로 자동 권한 검토가 거절했다. 원격 integration `6766c06`과 feature의 조상 관계 및 고유 커밋0개를 확인해 새 코드 전송이 없음을 추가 설명했으나 재차 거절됐다. Nest/API 두 fix push도 각각 동일한 목적지/payload 승인 부족으로 거절됐다. 우회나 추가 재시도 없음. 원격 보존 조건이 충족되지 않아 **두 worktree 제거는 하지 않았다**. 통합/main/dev·앱 이름 worktree는 변경하지 않았다.

남은 전송 대상은 기존 GitHub OhMyMetabuzz/clipper_electron → feature/app-window-name-20260915 (`7aed9f6`), OhMyMetabuzz/clipper_nestjs → fix/pg-contract-and-render-refund-20260916 (`000414f`), OhMyMetabuzz/clipper_web_api → fix/credit-operation-contract-20260916 (`3c33268`). 정확한 코드/문서 전송 승인 또는 사용자 직접 push 후 SHA 확인 → 두 fix worktree만 제거 순서로 재개한다. 아래는 승인 전 조사 기록이다.

2026-09-17. 사용자 요청: 앱 이름 feature push, 두 fix 브랜치의 목적·통합 반영 여부·보존 후 worktree 제거 가능 여부 확인.

## 판정

- Electron `feature/app-window-name-20260915`: HEAD `7aed9f666d26b55c22307c7a77df82751cb0e8b5`, clean, 현재 통합 HEAD `6766c06`의 조상이다. 기존 origin `https://github.com/OhMyMetabuzz/clipper_electron.git`의 같은 feature 브랜치로 push를 시도했으나 자동 권한 검토가 정확한 목적지 승인 부족으로 실행을 거절했다. 원격 branch 조회는 없음이었다. 목적지 명시 승인 대기이며 push 완료로 기록하지 않는다.
- Nest `fix/pg-contract-and-render-refund-20260916`: HEAD `da3b7f2`, 미커밋7파일. access/credits JSON 런타임 검증, Variation 제출 직후 성공 처리 제거, 실제 성공/실패 종결, 큐 취소 환급, 재시도 새 차감과 tests의 초기 수정안이다.
- Web API `fix/credit-operation-contract-20260916`: HEAD `31e014b`, 미커밋 `docs/api/openapi.yaml` 1파일. 활성 구독/access가 없어도 남은 유효 크레딧으로 operation을 시작할 수 있다는 정책 문서 정정이다. 신규 top-up 구매에는 active access가 필요하다는 구분도 썼다.

두 fix 브랜치 모두 통합에 없는 고유 커밋은 0개이며 HEAD는 통합 조상이다. 그러나 미커밋8파일은 Git 병합 이력에 포함될 수 없다. 기능 의도는 통합 후 재구현돼 있으므로 “옛 수정 파일을 그대로 merge했다”는 설명은 틀리다.

## 현재 구현 근거

- Nest `b9f9ce7`: access/credit 검증을 공통 `web-api-response.projector`로 구현. 필드·enum·숫자·페이지 검증 및 extra 필드 제거 tests. 현재 credit ledger는 옛 수정안에 없는 `payment_refund_revoke`도 지원한다.
- Nest `f3edd21`, `644c0c0`, `fda1eda`: 공통 coordinator/finalizer/outbox와 새 attempt 재시도 및 재시작 복구로 초기 Variation 보완안을 대체했다. `watchVariationRenderJob`은 실제 terminal을 기다려 completed면 succeed, 실패/취소면 fail을 호출한다. job별 영속 연결·취소/삭제 환급 회귀가 있다. 기존 waiting/params 기반 특례를 그대로 다시 가져오면 후속 설계를 퇴행시킨다.
- Web API `7392147`: `/operations` 설명은 충분한 유효 크레딧이면 active access 불필요로 정정돼 있다. `/payments/topups/checkout`은 `NO_ACTIVE_ACCESS` 400을 명시한다. 옛 문구와 문자 단위 동일하지 않지만 정책 정정은 반영됐다.
- fresh 검증: 통합 Nest build + access-credit-proxy / variation-v2-render-service / variation-v2-initial-billing-restart.integration / variation-v2-retry-billing-restart.integration / billing-archive-cancellation / jobs-confirmed-billing 6 test 파일, **148 PASS / 0 FAIL / 0 SKIP**. 로그 `/private/tmp/pg-old-worktree-coverage.log`. 옛 워크트리 자체의 build/test 통과를 주장하지 않는다.

## 권장 정리와 승인 경계

두 fix 워크트리는 현 통합 구현을 위한 작업 공간으로 더 이상 필요하지 않다. 다만 기록 보존을 원하면 각 미커밋 변경만 archive/WIP 성격의 커밋으로 보존하고 기존 origin의 각각 같은 fix 브랜치로 push한 뒤, 원격 SHA 일치와 clean·ignored/untracked 산출물·사용 중 프로세스를 확인하여 해당 worktree만 제거할 수 있다. 브랜치/커밋은 유지하며 통합본에 재병합하지 않는다. 커밋·push·worktree 제거는 아직 승인받아 실행한 것이 아니다. 다른 작업 worktree와 원본은 보존한다.
