# 개발서버 정식 PG 전환 실행 기록

실행일: 2026-09-18 KST
cutover ID: `dev-pg-20260918-035446`
상태: **Gate A–G 및 사용자 smoke PASS / 개발 DB·서비스 정식 PG 전환 완료 / rollback 미사용 / 후속 Web cache 보완 배포·사용자 재확인 완료**

에이전트는 서버에 접속하지 않았다. 아래 명령과 결과 확인은 사용자가 `m2-stage`에서 수행했다.

## Gate A-1 — 현재 source와 실행 image 기록

결과: **PASS**

| repo | branch/upstream | HEAD |
|---|---|---|
| `clipper_infra` | `dev` / `origin/dev` | `6cc7a3796409b931b7e13240826496fd3e8f5b73` |
| `clipper_web_client` | `dev` / `origin/dev` | `4b361efc742db797e85848c5aea90eb1736194c5` |
| `clipper_web_admin` | `dev` / `origin/dev` | `beda584fde924a9a97aa69f1856cbddafe69c94c` |
| `clipper_web_api` | `dev` / `origin/dev` | `fdd0cb6bf1d5a46edc90f683ffdb2c737d2812b6` |

- 네 origin URL은 모두 `https://github.com/OhMyMetabuzz/<repo>.git`과 일치했다.
- `git status --short --branch`에는 branch/upstream 줄 외의 변경 파일이 없었다.
- 백업 경로: `/Users/metabuzz/clipper-backups/dev-pg-20260918-035446`.

| 실행 컨테이너 | 기존 image ID | revision label |
|---|---|---|
| `clipper-web-client-dev` | `sha256:da9c6d0810a178f00e47bf59b6f7ffa882fe8d43baf0c732b5ac5495db110d4a` | 비어 있음 |
| `clipper-web-admin-dev` | `sha256:6d73ecc5c3a138878be986302e4345eda2033e2c9dc64da24f34f93cbd293f91` | 비어 있음 |
| `clipper-web-api-dev` | `sha256:f23eca69f8930daf8287aa3f24170f2681392bc6adb5a72616b8b4e2c64d8310` | 비어 있음 |

기존 image의 revision label 부재는 이 단계의 blocker가 아니다. Gate A-3에서 정확한 실행 image ID를 rollback tag와 tar로 보존한다. Gate B에서 새 image는 기대 source SHA의 revision label을 가져야 한다.

## Gate A-2 — env·secret 보존

결과: **PASS**

- cutover ID: `dev-pg-20260918-035446` 일치.
- `stack.dev.env` 원본과 백업 SHA256 일치.
- `web-api-dev-secrets.tar` archive 읽기 검증 통과.
- 백업 `stack.dev.env`: 3.4K, mode `600`.
- 백업 secret archive: 14K, mode `600`.
- `config-sha256.txt`와 `config-modes.txt`에는 hash·경로·mode만 기록하며 secret 값은 출력하지 않았다.
- 백업 경로: `/Users/metabuzz/clipper-backups/dev-pg-20260918-035446`.

## Gate A-3 — 기존 실행 image 보존

결과: **PASS**

- Gate A-1에서 기록한 세 실행 image ID가 tag 직전에도 동일함을 확인했다.
- `clipper-web-client:rollback-dev-pg-20260918-035446`, `clipper-web-admin:rollback-dev-pg-20260918-035446`, `clipper-web-api:rollback-dev-pg-20260918-035446`가 각각 기존 실행 image ID를 가리킨다.
- 세 image를 `/Users/metabuzz/clipper-backups/dev-pg-20260918-035446/dev-app-images.tar`로 저장했다.
- archive 크기: 116M, mode `600`, tar 읽기 검증 PASS.
- archive SHA256: `689b36b17e5b75768bf403fb957c8970417d0567fd21c17e5ecaa176c7fb9658`.
- 저장 전 사용 가능 공간 71GiB였으며 Docker prune은 하지 않았다.

Gate A 종료 시점에도 기존 세 컨테이너는 계속 실행 중이다. DB dump·migration과 새 image build/start는 아직 수행하지 않았다.

## Gate B 사전 원격 재확인 — 중단

사용자가 실제 개발서버는 계속 `dev`를 기준으로 운영해야 하지 않는지 질문했다. 검토 결과 이 판단이 맞다. 검증 SHA를 고정하기 위해 서버를 integration branch로 직접 전환하는 기존 초안은 임시 후보 검증에는 가능하지만, 실제 dev cutover 후 팀 기준 branch와 서버 branch가 달라지는 문제가 있다. 따라서 Gate B를 실행하지 않고 8개 원격의 최신 `origin/dev`와 integration을 다시 비교했다.

- Electron/Nest/Python/Infra/Web Admin/Web API/Web Client 7개는 최신 `origin/dev`가 integration HEAD의 조상이며 fast-forward 가능하다.
- Angular `origin/dev`는 `7c04e14e712d08b2f43f92d645674ed1011d480a`로 새로 이동했다.
- Angular merge base는 `98d449584055b324f223678f058e255c7d464c80`이다.
- Angular는 dev-only 15 commits(페이지 가이드 시트), integration-only 17 commits(PG/환급/독립 개발판/템플릿 보완)로 분기됐다.
- 양쪽 변경 파일의 교집합은 0개이고 `git merge-tree`에 실제 conflict marker는 없었다. 다만 dev의 공통 page/page-header layout과 integration의 여러 화면이 런타임에서 결합되므로 full test/build 및 화면 의미 검증이 필요하다.

권장안은 Angular integration에 최신 dev를 먼저 merge·검증하고, 그 최종 integration HEAD를 포함해 8개 `dev`를 승인 후 fast-forward하는 것이다. 그 뒤 m2-stage는 branch를 바꾸지 않고 계속 `dev`에서 정확한 SHA를 pull/build한다.

## Angular 최신 dev 로컬 병합·검증

사용자가 Angular의 로컬 병합과 전체 검증만 명시적으로 승인했다. 원격 push, 다른 저장소의 `dev` 반영, 서버 작업은 승인 범위가 아니므로 실행하지 않았다.

- 기준 branch: `integration/dev-pg-local-validation-20260917`
- 병합 전 HEAD: `19b407a7a6de56d7a43428f688e3e4e7258fdc8d`
- 가져온 최신 `origin/dev`: `7c04e14e712d08b2f43f92d645674ed1011d480a`
- 로컬 merge commit: `4c7993cdcbece0b07aa21afd7d90d1f1c5d48316`
- merge parent: `19b407a7` + `7c04e14e`
- 자동 Git conflict: 없음
- 의미상 결합: integration의 PG/환급/독립 개발판/템플릿 보완 위에 dev의 공통 page/page-header 가이드 시트가 추가됨. 병합으로 들어온 파일은 22개, 양쪽 변경 파일 교집합은 0개였다.
- `git diff --check 19b407a7..4c7993cd`: PASS
- 스타일 계약: 6/6 PASS
- `CI=1 npm run build:devapp` (project `.nvmrc` Node 24): PASS
- 일반 로컬 `npm run build:devapp`: Angular persistent cache의 LMDB native addon(`node.napi.glibc.node`)에서 macOS native crash. `CI=1`로 persistent cache를 끄면 같은 source build가 통과했다. source 오류로 은폐하지 않고 로컬 도구 환경 이슈로 기록한다.
- 첫 Angular 전체 테스트: 4,540개 중 4,539 PASS, 1 FAIL. Node 22와 project Node 24에서 같은 1건이 재현됐다.
- 실패: `ProductionPageComponent keeps the storyboard after copy failure and announces the retryable message` (`production-page.component.spec.ts:71–84`). 실패 테스트가 clipboard failure를 stub하지 않아 전체 suite에서는 실제 `navigator.clipboard` 성공 경로로 들어갔다. 단독 실행은 4/4 PASS라 실행 순서·환경 의존성도 확인했다.
- 해당 component/spec는 merge에서 변경되지 않았고 `origin/dev`에도 같은 코드가 있다. 문제 라인은 2026-08-25 `ee7b536d`에서 유입됐다. 사용자 승인 후 제품 코드는 건드리지 않고 해당 spec에 `clipboard.copy() -> { copied: false, reason: 'clipboard-failed' }`를 명시했다.
- 수정 후 대상 spec: 4/4 PASS.
- 수정 후 전체 Angular: 4,540/4,540 PASS.
- 수정 후 스타일 계약: 6/6 PASS.
- 수정 후 `CI=1 npm run build:devapp`: PASS.
- 테스트 보완 commit: `9dc31ec15da498fcd231132395491b0ffff9f500` (`test: isolate storyboard clipboard failure`).
- `origin/integration/dev-pg-local-validation-20260917`에 push했고 fetch 후 로컬·원격 SHA가 모두 `9dc31ec15da498fcd231132395491b0ffff9f500`임을 확인했다.

따라서 Angular 통합 검증과 통합 branch 보존은 완료됐다. 이 시점의 다음 단계는 8개 저장소의 최신 원격 상태를 다시 fetch하고, 최종 integration 결과를 각 `dev`에 반영하는 정확한 범위·SHA를 제시해 다시 승인받는 것이었다. 실제 개발서버는 integration branch를 직접 배포하지 않고, 최종 승인된 통합 결과를 `dev`에 반영한 뒤 서버가 계속 `dev`를 pull하도록 한다.

## 8개 원격 dev fast-forward

사용자에게 저장소별 출발 SHA, 목표 SHA, commit 범위, 기능 영향, 검증 결과를 제시하고 명시적 승인을 받은 뒤 실행했다. push 직전 8개 `origin/dev`가 승인된 출발 SHA와 일치하고, 각 dev가 목표 integration의 조상이며, 작업 폴더가 clean임을 다시 확인했다. force push는 사용하지 않았다.

| repo | 이전 `origin/dev` | 새 `origin/dev` |
|---|---|---|
| Angular | `7c04e14e712d08b2f43f92d645674ed1011d480a` | `9dc31ec15da498fcd231132395491b0ffff9f500` |
| Electron | `0b43737ca22fe0bf48ea46a73fcf95068cf538f5` | `d95c05058439a8be5c08d34ee3cb9890b2005b35` |
| NestJS | `4c32e03c327003e85ec5da248e362d4e85b49fb7` | `884fa8bc7abf5d802a142c918568d8e606041900` |
| Python | `88b1da277922cc5734a3e72e32425aa4054fa158` | `60417ce865499df519971650a43a7ca1a82d9867` |
| Infra | `6cc7a3796409b931b7e13240826496fd3e8f5b73` | `f0af3f52be99ed19b6594f25ac81ba2375ec3a05` |
| Web Admin | `beda584fde924a9a97aa69f1856cbddafe69c94c` | `01d0b93ad3c4b6803060c919ebd80d9ae656c142` |
| Web API | `fdd0cb6bf1d5a46edc90f683ffdb2c737d2812b6` | `fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f` |
| Web Client | `4b361efc742db797e85848c5aea90eb1736194c5` | `a4bc54b5852e82d0699f63e6198d409746dd0ee0` |

8개 push가 모두 성공했고, 이후 각 GitHub origin에 `git ls-remote refs/heads/dev`를 실행해 목표 SHA 8개가 모두 정확히 일치함을 확인했다. 저장소 내부 `.github/workflows`는 없으므로 이 push로 repo-defined 자동 배포는 실행되지 않았다. m2-stage source checkout, image build, 서비스 중단, DB migration은 여전히 실행하지 않았다. Gate B 런북은 integration branch가 아니라 `dev`와 위 고정 SHA를 사용하도록 갱신했다.

## 변경 상태

- 서버 접속 주체: 사용자.
- 서비스 중단: 0건.
- 실제 개발 DB 조회·변경: 0건.
- 새 image build·배포: 0건.
- 로컬 commit: Angular merge `4c7993cd`, 테스트 보완 `9dc31ec1`.
- push: Angular integration branch 1건, 8repo 원격 `dev` fast-forward 8건.

위 변경 상태는 Gate B 재개 전 체크포인트다. 이후 실제 전환 결과는 아래가 최신 정본이다.

## Gate B — 환경 계약 확인과 image 사전 빌드

결과: **PASS**

- `TOSS_PAYMENTS_REVIEW_MODE`를 제거했다.
- Widget/Billing test key 4개와 `TOSS_PAYMENTS_RETURN_BASE_URL`, `WEB_BASE_URL`, `API_KEY_ENC_SECRET`의 존재를 값 노출 없이 확인했다.
- 새 서버 전용 `TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET`, `DESKTOP_AUTH_TARGET`, `DESKTOP_RELEASE_TARGET`을 추가했다.
- 설정 변경 전 `stack.dev.env.before-formal-pg`를 남겼고 Toss 환경 preflight가 통과했다.
- 고정 source revision은 Infra `f0af3f52`, Web Client `a4bc54b5`, Web Admin `01d0b93a`, Web API `fe58b650`이었다.
- 새 image를 build-only로 만들었고 이 시점에는 기존 실행 컨테이너 image가 바뀌지 않았음을 확인했다.

| image | 사전 빌드 image ID | revision |
|---|---|---|
| Web Client | `sha256:77aeb1b415c974cac115a228bb37ee38fdaf90c3906dd5f16da80f5928ead865` | `a4bc54b5852e82d0699f63e6198d409746dd0ee0` |
| Web Admin | `sha256:f57763f95c86e777a371674cd43227c377c7a44b9d1029f35131f156913aeb85` | `01d0b93ad3c4b6803060c919ebd80d9ae656c142` |
| Web API | `sha256:6b0354dc7a4b13a718ca0a6717cb46e118871967a232e88aa52836b65e331254` | `fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f` |

## Gate C — 개발 서비스 쓰기 정지

결과: **PASS**

- 기존 Web Client/Admin/API 세 컨테이너가 모두 `running`임을 확인한 뒤 중지했다.
- 세 컨테이너는 각각 Gate A에서 기록한 옛 image ID로 `exited` 상태가 됐다.
- 같은 서버의 ViewX, Coldmail, Dohit 컨테이너는 중지하지 않았다.

## Gate D — 최종 DB dump·보존 기준·정책 조사

결과: **PASS**

- User/Admin/Release DB의 외부 연결이 각각 0개임을 재확인했다.
- 최종 dump를 `/Users/metabuzz/clipper-backups/dev-pg-20260918-035446`에 생성했다.
- dump archive 자체 검사는 세 파일 모두 `OK`였고, 사용자가 m2-stage 백업 위치로도 전달했다.

| dump | SHA256 |
|---|---|
| `user.dump` | `aacbeccd07ff623f81d32f816f840a33d199a4ce0f99eb8064f11fcbc5d1e401` |
| `admin.dump` | `47bd9428f5c730ab59e8a2e090ef7c5be40768e5faf8e4a2d71cf3cceb8fc92d` |
| `release.dump` | `291f57e80eaab80f7082051d6da82011af3558b13be3ab4368aa09392495e98d` |

보존 대상의 migration 전 count와 ID 집합 hash를 기록했다. 핵심 결과는 User `users=20`, `user_sessions=162`, `desktop_auth_codes=161`, `shortform_projects=1481`; Admin `operators=3`, `operator_sessions=26`, `provider_credentials=7`, `desktop_error_reports=22`, `desktop_sessions=7`; Release `release_versions=33`, `release_builds=51`, `release_artifacts=33`, `release_events=134`였다. Gate F에서 같은 파일과 `diff -u`로 비교했다.

정책 조사 결과:

- 옛 finance 테이블은 `licenses=24`, `purchase_requests=35`, `plans=4`, `credit_ledger=253`, `operation_runs=210`, `payment_orders=37`, `payment_events=49`였다.
- 옛 payment order 37건 중 `checkout_ready=27`, `failed=1`, `paid/TEST=9`였으며 보존할 LIVE 결제는 발견되지 않았다.
- 새 `user_access_grants`, `credit_grants`, `credit_ledger_entries`, `user_free_trials`, `subscriptions`, `user_onboarding_jobs`는 migration 전 존재하지 않았다.

## Gate E — 실제 migration

결과: **PASS**

- 사용자 승인 후 Infra의 `scripts/migrate-db.sh dev`로 User → Admin → Release 순서 migration을 실행했다.
- 같은 명령을 한 번 더 실행해 pending migration이 없는 no-op 재실행을 확인했다.
- 최신 migration은 User `AddDesktopLoginBinding1789600000000`, Admin `NormalizeAllTierPluginEntitlements1789300000000`, Release `AddArtifactDesktopProfile1789600000000`이었다.

## Gate F — migration 직후 DB 검증

결과: **PASS**

- Gate D의 User/Admin/Release 보존 snapshot과 migration 후 snapshot 세 쌍의 `diff -u`가 모두 비어 있었다.
- 옛 finance 테이블은 제거됐고 새 finance 테이블 8개는 서비스 시작 전 모두 0건이었다.
- `trial`, `basic`, `pro`, `business`는 모두 `entitlement_mode=all`; 저장된 개별 entitlement row는 0건이었다.
- operation catalog는 Shortform URL/Paste/Prompt 각 50, Dance 50, Dialog 50, Variation 20 크레딧이며 모두 `charge_then_refund`였다.
- `user_onboarding_jobs`는 서비스 시작 전 0건이었다.

## Gate G — 새 서비스 시작·외부 smoke

결과: **PASS**

- Web Client/Admin/API가 Gate B image로 시작했고 revision label을 확인했다.
- 첫 `/health` 요청은 API가 막 올라오는 순간의 `Empty reply from server`였으나, 컨테이너 상태·로그를 확인하고 재시도한 뒤 정상 응답을 확인했다.
- 외부 HTTPS `dev.clipperstudio.ai`, `dev-admin.clipperstudio.ai`, `dev-api.clipperstudio.ai`는 모두 HTTP 200/TLS 성공이었다.
- Catalog의 Basic/Pro/Business가 모두 여섯 plugin(`dance_highlight`, `dialog_highlight`, `shortform_paste`, `shortform_prompt`, `shortform_url`, `variation`)을 반환했다.
- 기존 사용자는 이메일이 보존됐고 활성 이용권 없음, 사용 가능 크레딧 0, 무료 체험 비소급을 확인했다.
- 신규 테스트 사용자는 Trial/400크레딧/30일을 한 번만 받았고 재로그인 뒤 중복 지급되지 않았다. DB에는 onboarding job 1건 `completed`, trial 1건, grant 1건, ledger grant `+400` 1건만 존재했다.
- Customer Web/Admin 주요 화면, 요금제 3종, 개발판의 이용 관리·크레딧 내역 링크, Google 로그인, 계정/access/credit 표시를 사용자 확인했다.
- 개발판 build와 실행, `clipperstudio-dev` 로그인 복귀, 운영 protocol 비점유, 필수 템플릿 import 및 중복 건너뜀을 확인했다.
- Toss checkout 사전 화면과 test key mode를 확인했지만 카드 등록/실제 결제·webhook은 실행하지 않았다.

## Smoke 중 발견한 Web SPA cache 결함과 최소 보완

첫 Customer Web 접속에서 이전 `index.html`이 이미 제거된 `chunk-6N5722P4.js`를 요청했다. 서버의 SPA fallback이 누락 JS 요청에도 HTML을 200으로 반환해 브라우저가 MIME 오류로 중단됐다. 강력 새로고침 뒤 로그인은 정상 동작했고, `/auth/refresh`의 401 `missing refresh token`은 로그인 전 기대 응답으로 원인이 아니었다.

사용자가 선택한 최소 범위로 Customer/Admin 컨테이너 내부 Nginx만 보완했다.

- `index.html`: `Cache-Control: no-store, no-cache, must-revalidate`
- 실제 JS/CSS: `Cache-Control: public, max-age=31536000, immutable`
- 없는 JS/CSS: SPA HTML fallback 대신 HTTP 404
- API, DB, 외부 m2-proxy/DNS/Nginx Proxy Manager: 변경 없음

TDD와 실제 Nginx HTTP 검증 후 다음 커밋을 `dev`와 integration branch 양쪽에 push하고 Web Client/Admin만 다시 배포했다.

| 서비스 | commit/revision | 최종 실행 image ID |
|---|---|---|
| Web Client | `72829210ecbe2d56b61bfc132f2b6e7e886b933a` | `sha256:2d31f80faef29e1be451f168d86cbf9bdfbd361aed5a243402bd20ee89f63815` |
| Web Admin | `583c6f2373cddf51ae24cefe528f4a9d4eb4b671` | `sha256:33117d9f093c2fe78ad50291948b2deb2c28fd127b6cd448209b84d45955a0c3` |
| Web API | `fe58b6504c024fa94f3ab67e5a3f027b8d75ba0f` | `sha256:6b0354dc7a4b13a718ca0a6717cb46e118871967a232e88aa52836b65e331254` |

자동 검증은 Customer 285/285, Admin 571/571, 두 build, Nginx 계약 테스트 각 3/3 및 격리 Nginx HTTP 검사를 통과했다. 배포 뒤 외부 HTTPS에서도 index/SPA route의 no-store, 실제 JS의 immutable, 누락 JS의 404를 확인했다. 사용자는 일반 새로고침, 로그인, 메뉴 이동을 다시 확인했다.

## 최종 판정과 남은 범위

- 개발서버 정식 PG schema/source/service 전환은 완료됐고 rollback은 사용하지 않았다.
- 보존 대상 데이터의 행 수와 ID 집합은 migration 전후 동일했다.
- 실제 카드 등록·결제·구독·webhook과 유료 plugin의 실차감/환급 end-to-end는 별도 승인 전까지 수행하지 않는다.
- 실제 ML plugin 실행과 Build 5 전체 QA는 HOLD다.
- Windows 설치형 실기는 Windows 장비에서 별도로 수행한다.
- macOS 자동 업데이트는 현재 비활성 상태를 유지한다.
- 배포 시 이미 열린 옛 탭은 한 번의 일반 새로고침이 필요할 수 있다. 미저장 입력을 임의로 날리지 않기 위해 자동 강제 reload는 이번 최소 수정에 포함하지 않았다.
- 전용 30–60분 로그 관찰 결과는 아직 별도 기록하지 않았다. 다음 재개 시 API 오류·onboarding 재시도·결제/operation 이상 징후를 값 노출 없이 확인한다.
