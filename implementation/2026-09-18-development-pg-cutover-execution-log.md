# 개발서버 정식 PG 전환 실행 기록

실행일: 2026-09-18 KST
cutover ID: `dev-pg-20260918-035446`
상태: **Gate A 전체 PASS / 8repo dev fast-forward·원격 SHA 확인 완료 / Gate B 재개 승인 전 / 실제 서비스 중단·DB 변경·배포 없음**

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
