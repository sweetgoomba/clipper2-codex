# 정식 PG 로컬 통합 — 저장소별 병합 제안

> 병합 전 제안을 보존한 역사 기록이다. 이후 승인된 병합·수정은 진행됐으며 현재 상태는 [최신 수정 결과](2026-09-17-archive-refund-fix-result.md)와 [커밋 정리안](2026-09-17-integration-commit-proposal.md)을 따른다. 아래 승인 전 표현은 당시 상태다.

기준일: **2026-09-17 KST**

상태: **읽기 전용 비교 완료 / semantic 결합안 사용자 승인 / 실제 전체 병합 승인 전**

이 문서는 최신 `origin/dev`, `origin/integration/main-unification-20260911`, Electron 앱 이름 브랜치를 실제 Git 객체로 비교한 병합 제안이다. 이 문서 작성은 병합·rebase·cherry-pick·파일 복사·push 승인이 아니다.

## 공통 작업 공간 제안

- 기준 ref: 각 저장소의 아래 표에 고정한 최신 `origin/dev` SHA
- 새 로컬 브랜치: `integration/dev-pg-local-validation-20260917`
- 별도 worktree 루트: `.worktrees/dev-pg-local-validation-20260917/`
- 병합 방식: 승인 후 각 저장소에서 `origin/dev`로 새 worktree/branch를 만들고 `origin/integration/main-unification-20260911`을 `--no-ff`로 병합한다.
- Electron은 위 병합을 별도 checkpoint로 확인한 뒤 `feature/app-window-name-20260915`를 두 번째 `--no-ff` 병합으로 가져온다.
- 자동 fast-forward가 가능한 저장소도 감사 경계를 남기기 위해 `--no-ff`를 권장한다. 사용자 승인 없이는 실행하지 않는다.
- 원본 8개 checkout의 `dev`, 원격 `main/dev`, 다른 worktree는 변경하지 않는다.
- push·배포·서버 접속은 하지 않는다.

## Git 기준과 정확한 범위

`integration only`는 고정된 두 HEAD 사이에서 `git rev-list origin/dev..origin/integration/main-unification-20260911`로 계산한 실제 커밋 수다.

| 저장소 | 기준 `origin/dev` | 가져올 integration HEAD | 정확한 integration-only 범위 | dev only / integration only | 자동 merge-tree |
|---|---|---|---|---:|---|
| Angular | `98d449584055b324f223678f058e255c7d464c80` | `f7bcaddebdf56f8e834c564355368a8c75e8680f` | `98d44958..f7bcadde` | 44 / 10 | textual conflict 없음 |
| Electron | `0b43737ca22fe0bf48ea46a73fcf95068cf538f5` | `b698014a2ebba5bd22a12199b35d23c68682bd7b` | `0b43737c..b698014a` | 0 / 10 | textual conflict 없음 |
| NestJS | `4c32e03c327003e85ec5da248e362d4e85b49fb7` | `da3b7f2fe3404100250cfc660fdf3e855dad00ae` | `4c32e03c..da3b7f2f` | 17 / 9 | textual conflict 없음 |
| Python | `88b1da277922cc5734a3e72e32425aa4054fa158` | `ae0a6fd532f4b2d962918a47588f3bb86c7084c9` | `88b1da27..ae0a6fd5` | 0 / 1 | textual conflict 없음 |
| Infra | `6cc7a3796409b931b7e13240826496fd3e8f5b73` | `948e8a12c7549fd418a066f672d2cb50af5dd808` | `6cc7a379..948e8a12` | 0 / 16 | textual conflict 없음 |
| Web Admin | `beda584fde924a9a97aa69f1856cbddafe69c94c` | `dade0ee63c2ab1f2461da693eccf1d36200ce705` | `beda584f..dade0ee6` | 0 / 42 | textual conflict 없음 |
| Web API | `fdd0cb6bf1d5a46edc90f683ffdb2c737d2812b6` | `31e014b6182a93b12a3899fd49cfc821269c28f2` | `fdd0cb6b..31e014b6` | 0 / 167 | textual conflict 없음 |
| Web Client | `4b361efc742db797e85848c5aea90eb1736194c5` | `4d95a963cde6f4e4067244c6cc8c148bb66709ce` | `4b361efc..4d95a963` | 0 / 57 | textual conflict 없음 |

Angular의 공통 조상은 `019687d973bf988f85beee7a3756ec97a7d2d7df`, NestJS의 공통 조상은 `e99b3962956343eb9272f7e9d4869f472d8ab180`이다. 두 저장소만 최신 dev와 integration이 그 조상 이후 갈라졌고, 나머지 6개는 최신 `origin/dev`가 integration의 조상이다.

Electron 앱 이름 작업의 정확한 추가 범위는 다음과 같다.

- integration 기준: `b698014a2ebba5bd22a12199b35d23c68682bd7b`
- feature HEAD: `7aed9f666d26b55c22307c7a77df82751cb0e8b5`
- 범위: `b698014a..7aed9f6` 두 커밋
  - `99444d8dd40ab198c8664aecf7959a637cc8b3ec` — `feat: distinguish desktop app display names`
  - `7aed9f666d26b55c22307c7a77df82751cb0e8b5` — `fix: distinguish desktop package names by environment`
- author/committer identity: `metabuzz-jinahan <jinahan@metabuzz.co.kr>`
- worktree 상태: clean, push되지 않음
- 최신 Electron dev에 feature 전체를 합친 `merge-tree`도 textual conflict 없음

## 1. Angular

### 이미 dev에 포함된 변경

- Variation v2 효과음을 과거 클립별 `sfxIds` 풀에서 `slots.sfx`와 `sfxEnabled` 모델로 옮긴 최신 편집 모델.
- Variation 프로젝트·결과 영상 삭제 UX와 보관함 카드 갱신.
- 최신 프로젝트 목록, Shortform Director, 댓글 오버레이와 기타 dev 변경 44커밋.

### 새로 들어오는 변경

- access/credit 조회와 사용 내역 UI, 공통 과금 확인창 `OperationChargeGuardService`.
- Shortform/Dance/Dialog/Variation 유료 작업 견적 확인 경로와 Variation 실제 차감액·차감 후 잔액 표시.
- 선택 저장이 끝난 뒤 정확한 Variation 영상 수로 견적을 여는 동기화.
- 요금제 목적지를 `/pricing`으로 변경하고 Naver 연구 사용량과 일반 크레딧 내역을 분리.
- 런타임 앱 이름 표시와 Windows CPU 정보 표시.

### 양쪽이 같은 파일을 수정한 지점

자동 병합은 되지만 아래 5파일은 의미 검토 대상이다.

- `src/features/variation-v2/pages/v2-variation-list/v2-variation-list.component.spec.ts`
  - dev: 최신 Variation 선택·삭제/SFX 동작에 맞춘 테스트.
  - integration: 과금 확인, 확인 취소, 저장 완료 후 견적, 차감 결과 안내 테스트.
  - 결합: 두 테스트 군을 모두 유지한다.
- `src/features/variation-v2/services/variation-v2-api.ts`
  - dev: `deleteVideos()` 추가.
  - integration: 렌더 응답의 `billing` 추가.
  - 결합: 삭제 API와 billing 응답을 모두 유지한다.
- `src/features/variation-v2/state/variation-v2.store.ts`
  - dev: `slots.sfx`, `sfxEnabled`, 프로젝트 삭제 동작.
  - integration: `lastRenderBilling`, `waitForPendingWrites()`.
  - 결합: 최신 dev 모델을 정본으로 두고 billing 상태와 저장 대기만 더한다.
- `src/shell/projects/projects/projects.component.ts` 및 spec
  - dev: Variation 카드 삭제 시 영상과 프로젝트를 안전한 순서로 함께 삭제.
  - integration: 요금제 링크 `/pricing`, 앱 이름 중립 문구.
  - 결합: dev 삭제 semantics를 그대로 유지하고 PG 링크/문구만 합친다.

### 병합 뒤 수정할 부분

- `CurrentLicenseSummary/currentLicense/_license`, queued/expired license UI를 제거하고 access·credit 원형 모델로 이름과 상태를 정리한다. integration 병합만으로 사라지지 않는다.
- 모든 사용자 `다시 시도/다시 만들기`가 새 견적·확인 뒤 새 attempt로 가는지 보장한다.
- Variation의 성공 토스트·잔액 refresh는 실제 terminal 과금 결과와 일치하게 바꾼다. 큐 제출만으로 성공 확정하지 않는다.

### 사용자 영향과 검증

- 사용자는 작업 전에 크레딧 금액을 보고 취소할 수 있고, 승인하면 실제 차감·잔액을 확인한다.
- 최신 Variation 효과음/삭제 기능은 유지된다.
- 검증: Angular build, 관련 unit test, 잘못된 access/credit 응답, 확인 취소, 저장 직후 견적, 실패/환급 후 잔액 refresh.

## 2. Electron

### 이미 dev에 포함된 변경

- 현재 dev Electron 기준 전체. integration과 갈라진 dev-only 커밋은 없다.

### integration에서 들어오는 변경

- dev/prod 실행 모드별 Web API 설정 전달.
- 운영 app identity, protocol, cache/port, Windows 설치·프로세스 검사 격리.
- 빌드 임시 산출물 정리 재시도, Windows CPU 사용량 수집.
- dev와 운영이 같은 PC에서 공존할 때 프로세스·캐시·포트를 잘못 공유하지 않도록 하는 경계.

### 앱 이름 feature에서 들어오는 변경

- 운영 표시명, macOS `.app`, DMG, Windows installer: `Clipper Studio`.
- 개발 표시명, macOS `.app`, DMG, Windows installer: `Clipper Studio (dev)`.
- 유지되는 identity:
  - dev `appId=ai.clipperstudio.desktop`, 운영 `appId=ai.clipperstudio.app`
  - dev protocol `clipper`, 운영 protocol `clipperstudio`
  - dev data path `Clipper Studio`, 운영 data path `Clipper`
  - 기존 cache/port/update 구조
- macOS safeStorage/Keychain 복호화가 표시명 변경으로 실패할 경우 1회 재로그인을 허용한다. 자동 Keychain migration은 하지 않는다.
- 과거 개발 앱 `Clipper Studio.app`과 새 `Clipper Studio (dev).app`은 파일명이 달라 공존할 수 있지만 같은 dev data path와 identity를 사용하므로 번갈아 실행하는 사용 방식은 지원하지 않는다.

### 예상 충돌과 검증

- textual conflict 없음. 의미상 위험은 builder 문자열 치환이 appId/protocol/data path까지 잘못 바꾸는지 여부다.
- 생성된 dev/prod builder config를 snapshot으로 검사하고 mac `.app`/DMG 이름, Windows installer 이름을 확인한다.
- 로그인 복호화 실패가 크래시·반복 prompt 없이 로그아웃으로 끝나며 재로그인 후 유지되는지 확인한다.
- utility Nest와 하위 Python/ffmpeg process tree의 정상/강제 종료를 fixture로 검증한다. 실제 ML 실행은 HOLD다.

## 3. NestJS

### 이미 dev에 포함된 변경

- 최신 렌더·프로젝트·Variation SFX 모델, 보관함/삭제, Shortform Director 및 dev 17커밋.

### 새로 들어오는 변경

- Web API access/credit proxy와 operation quote/start/evidence/succeed/fail client.
- Shortform, Dance, Dialog Highlight, Variation 과금 연결.
- Variation 영상별 부분 성공 정산, 준비 실패 환급 후보.
- Naver credential 분리, resource ownership/lifecycle 보완.

### 같은 파일의 의미 결합

- 실제 겹침은 `test/variation-v2-render-service.test.js` 한 파일이다.
  - dev: `slots.sfx.volume` fixture로 변경.
  - integration: Variation 과금 start/evidence/succeed/fail 테스트 178줄 추가.
  - 자동 결과는 최신 SFX fixture와 과금 테스트를 모두 유지한다.

### integration 그대로 유지하지 않고 수정할 부분

- 현재 Variation 테스트는 queue 제출을 곧 `succeed`로 본다. 실제 렌더 terminal 성공에서만 성공 확정하고 실패·취소는 환급하도록 바꾼다.
- Shortform watcher, Dance `JobsService`, Dialog executor `finally`, Variation 서비스에 흩어진 종결을 구성 기반 공통 attempt coordinator/finalizer로 모은다.
- `waiting`을 `preparing | queued | starting | running | completed | failed | cancelled` enum으로 직접 확장하고 `render_prepare_pending`을 신규 정본에서 제거한다.
- Shortform/Variation/댓글 오버레이/영상 랭킹의 reserve/prepare/retry 상태를 같은 상태 기계로 연결한다. 무료 기능 두 개에는 billing coordinator를 붙이지 않는다.
- 실패/환급 뒤 사용자 재시도는 과거 operation을 재사용하지 않고 새 quote/confirmation/attempt로 보낸다.
- 로컬 attempt metadata와 durable terminal outbox를 project/job 삭제 가능 데이터와 분리한다. 미종결은 해결까지 보존하고 서버 종결 확인 항목·tombstone은 30일 뒤 정리한다.
- access/credit proxy 응답을 runtime validation/projector로 검증하고 제거된 독립 `refund()` client 메서드를 삭제한다.
- Shortform 최종 렌더 전 TTS/media 완전성 preflight를 추가하고 sample/silent/fallback TTS로 누락을 숨기는 경로를 제거한다. 정상 `legacy-bgm.*` ID와 MP3는 이름 때문에 바꾸지 않는다.

### 사용자 영향과 검증

- 어느 유료 플러그인이든 같은 견적·확인·차감·성공/환급·재시도 규칙을 사용한다.
- 앱/네트워크 장애 뒤 terminal 보고가 outbox로 재전송되고 중복 환급되지 않는다.
- 검증: unit/contract test, fake child와 짧은 ffmpeg, 앱 종료/네트워크 단절/응답 유실, 사용자 삭제와 billing tombstone 분리. 실제 ML HOLD 유지.

## 4. Python

### 들어오는 변경

- plugin SDK와 TTS Supertonic의 resource/process 안전성 보완 및 대응 테스트.
- 최신 dev와 integration의 코드 충돌은 없다.

### 유지·수정 기준

- 기존 렌더 결과와 plugin 계약은 유지한다.
- 상위 Nest/Python 종료 때 하위 ffmpeg/process group이 남는지 먼저 fixture로 증명한다. 증명되지 않은 경로만 최소 수정한다.
- 실제 ML 모델 실행은 하지 않고 단위 테스트와 짧은 subprocess fixture까지만 실행한다.

## 5. Infra

### 들어오는 변경

- 로컬 dev와 운영 빌드 분리, Web Admin/Client prod configuration.
- API migration runner를 runtime image에 포함하고 명시적으로 실행하는 배포 구조.
- Toss PG 환경·runbook, Windows production runner/source/dependency 격리.
- guarded production test-payment reset과 이후 DB recreation 문서 이력.

### 유지·수정 기준과 영향

- build/deploy 격리와 migration runner는 유지한다.
- 운영 DB 전체 재생성 절차는 개발 DB 전환에 사용하지 않는다.
- 개발 DB는 사용자/auth를 보존하고 금융 데이터만 승인된 범위로 정리하는 별도 runbook을 만든다.
- 서버 명령은 이 저장소에서 실행하지 않는다. 로컬 compose와 clone rehearsal 명령만 계획에 포함한다.

## 6. Web Admin

### 들어오는 변경

- PG payment/subscription/refund/access/credit 운영 화면.
- operation recovery와 payment fulfillment recovery, evidence 기반 수동 확정.
- 회원별 잔액·grant·ledger·결제 연결, 테스트 영수증과 실패 세부 정보.
- 최신 dev의 API key/Naver/진단 화면을 보존한 통합 결과.

### 유지·수정 기준과 영향

- evidence 없이 성공/실패를 임의 확정하지 않는 수동 recovery를 마지막 안전망으로 유지한다.
- 자동 outbox/reconciliation이 판정할 수 없는 건만 Admin으로 보낸다.
- 접근·크레딧·환불 UI가 실제 Web API 상태/권한과 일치하는지 계약 테스트와 build로 검증한다.

## 7. Web API

### 들어오는 변경

- Toss 정식 PG 결제, billing key, 구독·변경·해지·top-up·환불·recovery.
- access grant, credit grant/ledger, operation definition/run/evidence/recovery.
- 상품 카탈로그, 고객/관리자 API, 결제·크레딧 표시명과 history filter.
- migration runner와 다수 admin/user migration.
- 최신 dev의 Naver/진단 기능을 보존한 통합 결과.

### integration 그대로 유지하지 않고 수정할 부분

- operation start DTO에 stable client attempt/idempotency key를 추가하고 DB unique constraint로 같은 logical attempt의 중복 차감을 막는다.
- `succeed/fail` terminal replay가 같은 run에 멱등임을 계약 테스트로 고정한다.
- 필요 최소한의 operation 상태/evidence 조회 계약을 추가해 Desktop이 outbox 결과를 확인할 수 있게 하되 프로젝트·미디어는 서버로 올리지 않는다.
- active access가 없어도 남은 추가구매 크레딧으로 작업 가능하다는 계약과 모든 현행 tier의 `entitlement_mode=all`을 테스트로 고정한다.
- 기존 개발 사용자/auth는 보존하고 구·신 금융 상태를 정리하는 개발 전환 전용 inventory/reset SQL을 별도로 만든다. live provider 거래 의심 행이 있으면 중단한다.

### 위험과 검증

- migration 수가 많고 금융 FK가 연결돼 있으므로 로컬 빈 DB → 기존-schema DB → 개발 DB dump clone 순서로 검증한다.
- forward migration 뒤 rollback은 down migration에 의존하지 않고 사전 dump restore로 리허설한다.
- payment provider 실호출 없이 fixture/mock/테스트키 범위의 contract/e2e만 수행한다.

## 8. Web Client

### 들어오는 변경

- 고객 pricing, 구독 checkout/동의, billing key 등록, top-up, 결제/크레딧 history.
- 구독 변경·해지와 예약 변경 확인, 실패·환불 안내.
- `/my` 포털 경로, desktop handoff/download/auth callback, prod build config.
- 최신 dev와 textual/semantic overlap 없음.

### 사용자 영향과 검증

- 사용자가 웹에서 요금제를 확인·구독·변경·해지하고 크레딧을 추가 구매하며 내역을 확인한다.
- checkout은 명시적 결제 동의 뒤에만 생성되어야 한다.
- Angular build/unit test와 API contract fixture로 성공·실패·취소·환불·예약 변경을 검증한다.

## 병합 뒤 공통 구현 순서

1. 8개 병합 결과의 build와 기존 targeted test로 baseline 확인.
2. Angular의 옛 license adapter 제거와 runtime 계약 정리.
3. Web API operation start idempotency/DB migration/contract test.
4. Desktop Nest 공통 attempt metadata, terminal outbox, finalizer, retry 경계.
5. job status enum과 네 reserve/prepare 경로 전환.
6. Shortform authoritative preflight와 암묵 fallback 제거.
7. Electron/Nest/Python process-tree 종료 보장과 재시작 reconciliation.
8. 앱 이름 패키징·재로그인 검증.
9. 별도 로컬 DB에서 migration과 웹/API/설치형 앱 검증.
10. 개발 DB dump 복제본에서 데이터 전환·dump restore rollback 리허설.

각 단계는 테스트 실패나 새 의미상 충돌이 승인 범위를 벗어나면 중단하고 다시 설명한다.

## 승인 전 현재 결론

- 현재 Git 기준 textual conflict는 8개 저장소 모두 없다.
- 의미상 결합 검토가 필요한 것은 Angular 5파일과 Nest 테스트 1파일이며, 사용자는 최신 dev 기능과 integration PG 기능을 모두 유지하는 위 권장 결합안을 승인했다.
- Electron 앱 이름 worktree에서 TypeScript build와 builder config/package name/identity/data-path 관련 targeted test를 새로 실행해 71 PASS, 0 FAIL을 확인했다. 실제 `.app`·DMG·Windows installer 산출물 생성은 병합된 최종 소스에서 다시 검증한다.
- 자동 병합 성공은 기능 완성을 뜻하지 않는다. integration의 과금 terminal 경계, 재시도, outbox, idempotency, 상태 enum, Shortform preflight, license adapter는 승인 후 별도 구현해야 한다.
- 커밋·merge·push·deploy는 아직 0건이다.
