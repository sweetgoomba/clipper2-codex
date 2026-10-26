# 프로모션·결제 감사 수정 — 원격 dev 병합

완료: **2026-10-26 KST**. 사용자 요청에 따라 세 제품 저장소의 감사 수정 브랜치를 커밋·푸시하고 최신 원격 `dev`에 병합·푸시했다. 추가 요청한 관리자 `fix/member-promotion-access-summary-20261023`도 함께 병합했다.

[수정 내용·범위](2026-10-23-billing-promotion-audit-fixes-result.md) · [기준 감사](2026-10-23-billing-promotion-baseline-audit.md) · [W17](../handoff/tasks/festival-voucher.md)

## 원격 반영 결과

공통 수정 브랜치: `fix/billing-promotion-audit-20261023`.

| 저장소 | 수정 커밋 | 최종 원격 dev | 병합 전 최신 원격 dev |
|---|---|---|---|
| clipper_web_api | `3f0374493038f2c3003faea220dcc6d5bb6c8622` | `2ac17a94a0a6b58ef04a2c82bb17eb21d92385d8` | `db0ca363366765147d08fa12d698b7857f536149` |
| clipper_web_client | `dd915055d67e10cad011cf4143c104381bdf9907` | `90f17e370adacd9ea7b6ab78c44b02f00fff11e3` | `fbd457314982350da159e5ab1fb386074626bcc9` |
| clipper_web_admin | `0de7a88c5e79f2ea283542be0faa6d5eaa0e0640` | `4e2fbe664dd277a09e0301a18c9a041bd1bef7a3` | `090d4e7003517e8cb79adbad27d6c42520fa2421` |

각 저장소에서 새 fetch를 수행했고 병합 직전 원격 dev가 감사 수정의 기준과 같음을 확인했다. 수정 커밋을 해당 브랜치로 먼저 푸시하고, 원격 dev 기준의 분리된 HEAD에서 `--no-ff` 병합을 만들었다. 강제 푸시 없이 `HEAD:refs/heads/dev`로 반영했다. 푸시 후 `git ls-remote --heads`로 위 원격 SHA를 직접 확인했다.

관리자 추가 브랜치의 `ae9b15daa8f5d4a375178b8bb7422affb44597f9`는 중간 병합 `ae8b73e845fd3fdf62470183ccbffb7ac24f7856`을 통해 최종 dev에 포함됐다. `git merge-base --is-ancestor`로 이 커밋과 감사 수정 커밋이 모두 최종 dev의 조상임을 확인했다.

## 충돌과 해결

API·회원 웹은 충돌이 없었다. 관리자는 두 수정 브랜치가 같은 회원 상세 표시 코드를 변경하여 다음 두 파일에 충돌이 있었다. 병합 전에 사용자에게 알렸다.

- `src/app/features/portal/members/detail/member-detail.component.ts`
- `src/app/features/portal/members/detail/member-detail.component.spec.ts`

기존 `ae9b15d`는 구독 없음/pending에서 활성 프로모션을 우선한다. 감사 수정은 같은 동작에 canceled/ended/stopped와 공통 selector를 추가한 것이다. 해당 두 파일에는 감사 수정의 확장된 구현/회귀 검사를 유지했다. 타입·프로모션 라벨은 동일했고, 기존 브랜치의 `asBackendAccessSource('promotion')` 검증도 자동 병합으로 보존했다.

병합 결과와 감사 수정 커밋의 차이는 이 기존 API 타입 테스트의 assertion 한 줄뿐이다. 미해결 충돌 0건, `git diff --cached --check` 통과 후 관리자 전체 테스트와 빌드를 재실행하고 병합 커밋을 확정했다.

## 이번 턴의 재검증

| 검사 | 결과 |
|---|---|
| API 전체 Jest | 430 suites / **4,490 tests 통과**, snapshots 5 통과; 기존 opt-in 등 69 tests 제외 |
| 실제 PostgreSQL 별도 검사 | 5 suites / **48 tests 통과** (위 기본 제외 중 48개) |
| 회원 웹 전체 ChromeHeadless | **513/513 통과** |
| 관리자 감사 수정 전체 ChromeHeadless | **2,393/2,393 통과** |
| 관리자 두 브랜치 병합 결과 전체 ChromeHeadless | **2,393/2,393 통과** |
| API·회원·관리자 빌드 | 모두 통과; 관리자 병합 후에도 재빌드 통과 |
| Git 충돌·공백 검사 | 미해결 충돌 0, diff check 통과 |

API와 회원 웹의 병합 커밋 소스 트리는 이번 턴에 검사한 수정 커밋과 정확히 같음을 `git diff --exit-code` 및 tree SHA로 확인했다. API tree `7a1b3fbf42db45b49276b4023240c4932129946a`, 회원 tree `85960212cc05942fccd16a55a94b56caa99b3da5`다. 관리자에서는 충돌 해결 후의 소스를 다시 검사했다. 겹치는 검사 수치를 합산하지 않는다.

로그는 `/private/tmp/billing-merge-20261026-{api-tests,postgres-tests,client-tests,admin-tests,admin-integrated-tests,api-build,client-build,admin-build,admin-integrated-build}.log`에 있다. API Node 22.22.3, 웹 Node 24.19.0/ChromeHeadless를 사용했다. 웹 번들 경고(회원 503.64kB, 관리자 860.44kB)는 기존과 동일하며 두 빌드는 성공했다.

## 작업 폴더·환경

- 세 작업 트리 `.worktrees/billing-promotion-audit-20261023/web/{clipper_web_api,clipper_web_client,clipper_web_admin}`를 보존했다. 병합 후 공통 수정 브랜치로 돌아왔으며 모두 미커밋 변경이 없다. 각 수정 브랜치는 원격에 유지한다.
- 원본 저장소의 branch/checkout은 전환하거나 최신화하지 않았다. 원본 API의 `.env.example`, `auth.controller.ts` 변경 2개는 전후 diff SHA256 `f931c32358486ebc7d839759d83c91914de243f9b03691c4b64f417e4b39e2cd`로 동일함을 확인했다.
- 검증 전용 PostgreSQL만 잠시 기동했다. 생성한 `billing_test_*` DB 0건을 확인하고 정상 종료했다. 기존 DB·Docker·앱 서버는 변경하지 않았다.
- 실제 Toss 승인/청구/환불 및 서버 배포 완료 여부는 이번에 검증하지 않았다. 원격 dev 반영과 실행 중인 서버의 배포 확인은 구분한다.
- `.codex` 병합 기록과 WORKBOARD는 갱신했으며, 다른 세션의 문서 변경을 커밋에 섞지 않았다. 이번 커밋·푸시 대상은 위 제품 브랜치들이다.
