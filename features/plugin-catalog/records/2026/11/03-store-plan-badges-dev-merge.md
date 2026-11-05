# W19 최종 요금제 배지 · 세션 전체 구현의 원격 dev 통합

완료: **2026-11-03 KST**. 사용자가 마지막 스토어 배지 수정을 요청하고 이번 세션 전체 구현의 최신 dev 병합을 승인했다. 관련6개 제품 저장소에 각각 커밋·작업 브랜치 푸시·원격 dev fast-forward 통합을 완료했다. **충돌0건, 원격 dev/작업 브랜치/검증한 HEAD 일치, 작업 폴더6개 clean**이다.

[세션 전체 범위](../../../../../records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md) · [현재 W19 카드](../../../../../handoff/tasks/signup-promotion-plan-entitlements.md) · [기계 판독용 커밋·트리·검사 결과](03-store-plan-badges-dev-merge-manifest.json) · [짧은 설계·진행 계획](03-store-plan-badges-dev-merge-plan.md)

## 1. 이번 마지막 수정

카드의 긴 ‘현재 이용권에서 실행 불가’와 상세의 ‘현재 이용권에서는 실행할 수 없습니다’ 문구를 사용 가능한 요금제 안내로 바꿨다.

| 상태/허용 목록 | 카드 | 상세 모달 |
| --- | --- | --- |
| 현재 회원이 실행 가능 | 요금제 배지 생략 | 사용 가능 요금제 표시 |
| Business만 허용 | Business 배지 | 사용 가능 요금제 · Business |
| Pro/Business 및 그 위의 모든 활성 등급 허용 | Pro 이상 | 사용 가능 요금제 · Pro 이상 |
| Free부터 모든 활성 등급 허용 | 현재 Free도 허용되므로 카드에 생략 | 무료 요금제 이상 |
| 자동 포함 OFF, Basic/Business만 허용 | Basic와 Business 개별 배지 | 동일한 개별 배지 |
| 조회 지연/실패/허용 등급 없음 | 해당 상태 안내 | 조회 상태와 허용 등급 없음을 구분 |

‘이상’은 upgradeRank 기준으로 **그 등급부터 모든 상위 활성 등급이 빠짐없이 허용**된 경우에만 쓴다. 회사가 추가한 등급/이름도 같은 규칙을 따른다. 단일 최상위면 ‘이상’을 붙이지 않는다. Free는 안내에서 ‘무료 요금제’로 표시한다.

색은 전용 시맨틱 토큰을 사용한다. Free는 중립색, Basic은 파랑, Pro는 초록, Business는 보라다. 카드/모달은 같은 helper·배지 컴포넌트를 재사용한다. 이번 UI 때문에 설치/바로가기/편집을 차단하지 않으며 실제 실행의 서버 권한 검사는 유지한다.

## 2. 실제 데이터 연결과 검토 보완

- Web API `GET /catalog/plugin-plans`: 활성 요금제의 이름·코드·순위·entitlementMode·pluginKeys·isActive만 공개한다. 기존 catalog의 정규화 함수와 설정 스냅샷 잠금을 재사용한다. OpenAPI 계약을 추가했다.
- Nest `GET /access/plugin-plans`: 기존 WebApiClient로 위 공개 경로를 읽고 최소 필드를 검증·투영한다. 환경별 API URL/인증/오류 처리는 기존 연결을 따른다.
- 앱 PluginPlanAccessService가 스토어 진입 시 읽고 겹친 요청을 합친다. 서버의 등급 허용 조합과 이름을 사용하며 플러그인별 최소 등급을 앱에 하드코딩하지 않는다.
- 기존 `/catalog`는 판매 상품이 없는 유료 등급을 제외하므로 그대로 배지 데이터로 쓰면 안 됐다. 예: Basic/Business 허용, Pro 비허용인데 Pro 상품 판매를 중지하면 ‘Basic 이상’으로 잘못 표시된다. 새 읽기 경로는 **판매 상품과 독립된 모든 활성 등급**을 포함하여 해결했다. 가격 카드의 기존 판매 목록은 바꾸지 않았다.
- 실제 검사에서 카드/모달 입력 연결 실수와 Material의 옛 `--mdc-chip-*` 토큰 사용도 재현·수정했다. 현재 `--mat-chip-*` 토큰을 사용하며 실제 글자색을 두 스킴에서 검사한다. 변수 선언만 다른데 글자는 같은 문제를 놓치지 않도록 검사했다.

이는 W19 허용 설정/안내 보완이다. W18의 앱 스토어 전체 목록 동기화·분류·공개·전역 중지를 구현한 것은 아니다.

## 3. 원격 반영 결과

공통 작업 브랜치: `feat/signup-credit-promotion-free-20261102`.

| 저장소 | 병합 직전 원격 dev | 작업 커밋 = 반영 후 원격 dev | 작업 폴더 |
| --- | --- | --- | --- |
| `web/clipper_web_api` | `64919db3` | `6e1d001c` | clean |
| `web/clipper_web_admin` | `3435f2a3` | `e84d531a` | clean |
| `web/clipper_web_client` | `c0719ac8` | `50779ad0` | clean |
| `desktop/clipper_angular` | `9dd1550e` | `222ef59a` | clean |
| `desktop/clipper_nestjs` | `7f57ff1b` | `f2cc17a9` | clean |
| `desktop/clipper_electron` | `99be6e09` | `8e70e99b` | clean |

각 저장소에서 최신 dev를 다시 fetch했고 관계는 원격 dev가 현재 브랜치보다1커밋 뒤인 상태였다. 작업 브랜치를 먼저 푸시한 뒤 **검증한 동일 커밋으로 dev를 fast-forward**했다. 강제 푸시·불필요한 빈 병합 커밋 없이 반영했다. `git ls-remote --heads`로 두 원격 참조를 독립 확인하고 현재 HEAD/트리·조상 관계·clean 상태를 확인했다.

추가 충돌 해결이나 병합 중 소스 변경이 없으므로 아래 검증한 트리와 실제 원격 dev 트리가 동일하다. 원본 체크아웃은 전환/정리하지 않았고 사용 중인 세션 worktree·로컬 환경을 유지한다. 초기 이용권/레퍼럴 구현을 보존한 각 로컬 `archive/promotion-access-referral-20261102`도 유지한다.

## 4. 이번 최종 검증

| 검사 | 결과 |
| --- | --- |
| Web API 전체 Jest | 471 suites / **5,142 통과**, 109 opt-in/기존 제외, 0실패. snapshot5통과 |
| 실제 PostgreSQL 가입/혜택/권한 통합 | **39/39 통과**. 새 일회용15439, user/admin migration 및 동시성/복구/코드별 상한/조건/만료/유효기간 변경/판매 중지 등급 보존 |
| 관리자 전체 ChromeHeadless | **2,728/2,728 통과** |
| 회원 웹 전체 ChromeHeadless | **591/591 통과** |
| 앱 전체 ChromeHeadless | **10,656/10,656 통과**, 스타일21/21통과 |
| Electron 전체 Node24.19 | **1,913/1,913 통과** |
| 데스크톱 Nest 전체 Node24.19 | **5,290 통과 / 기존 macOS 소유권 종료 시험1실패**. 사용자 승인으로 W20 별도 이관, 이번 변경으로 해결됐다고 보고하지 않음 |
| API/관리자/회원/App/Nest/Electron 빌드 | 모두 통과. mac-arm64 local-api 앱 패키징도 통과 |
| 색상/공백/계약 | 관리자 직접 색상 검사·앱 스타일 가드·6개 diff check 통과. OpenAPI 신규 경로 시험 통과 |
| 검토 | 새 배지 데이터 누락/입력 연결 지적 수정 후 재검토에서 중요 미해결 없음. 기존 macOS 문제는 별도 항목 |

관련169개 및 API catalog94개 같은 집중 수치는 전체와 겹치므로 합산하지 않는다. 별도 PostgreSQL39개는 기본 opt-in 제외에 포함돼 따로 실행한 것이다. 실제 토스 결제망 검증이 아니다.

실제 DB 시험에서 예전 ‘Free 제외 유료 계층’ 초기 조건이 새 전역 포함 정책과 맞지 않아 실패했다. Free 및 상위 등급의 초기 허용 목록만 최신 정책에 맞춰 바로잡았고, 동시 편집/하위 포함 거절/이미 인정한 실행의 복구 단언은 유지했다. 새 판매 중지 회귀의 실제 DB 컬럼명과 상수 import 오류도 최종39개 통과 전에 수정했다. 제품 권한 검사를 느슨하게 바꾸지 않았다.

초기 API 전체 재실행의 설정 컨트롤러401 한 건은 같은 소스의 단독43개와 최종 전체5,142개에서 통과했다. Node22에서 옛 timer 시험 취소가 있어 기존 앱 빌드 환경인 Node24.19로 재검증했으며 Electron은 전부 통과했다. Nest의 POSIX identity 실패는 반복 재현돼 별도 이관했다. 최소 환경의 추가 시도는 ffmpeg PATH 누락까지 있어 성공 근거로 사용하지 않는다.

로그 접두어는 `/private/tmp/w19-final-20261103-`이며 `{api-tests.json,api-tests.log,api-build.log,signup-postgres.log,admin-tests.log,admin-build.log,client-tests.log,client-build.log,app-tests.log,app-styles.log,app-build.log,nest-tests-node24.log,nest-build.log,electron-tests-node24.log,electron-build.log,local-app-package.log}`를 참조한다. 실패/RED·보완 실행도 같은 접두어로 보존했다. 기존 FE 번들 예산 경고와 pg 동시 query의 향후 deprecation 경고는 남는다.

## 5. 기존 macOS 오류: 사용자 승인에 따라 별도 세션

전체 검증에서 기존 dev와 같은 OwnedChildProcessRegistry가 Darwin의 transient 시작 메타데이터 때문에 같은 프로세스를 다르게 해석하는 오류를 확인했다. 사용자에게 분리 여부를 물었고 **‘별도 기록하고 새로운 세션을 열어 원인 분석·해결’** 지시를 받았다. 이 사용자의 판단에 따라 기존 실패를 명시한 채 W19 변경만 통합했다. 해당 소스/시험을 이번 제품 커밋에서 변경하지 않았다.

- 새 세션: **macOS 보조 프로세스 종료 오류 수정**
- threadId: `01a19dcf-acaf-7371-9d72-58b3fce5f985`, host local.
- 생성/초기 인계 후 별도 세션이 같은 실패를 재현하고 수정 작업에 착수한 것을 확인했다. 그 작업을 이 세션의 완료로 주장하지 않는다.
- [W20 작업카드](../../../../../handoff/tasks/macos-owned-child-identity.md) · [원인·재현·안전 경계](../../../../../operations/env-runtime/records/2026/11/03-macos-owned-child-identity-investigation-handoff.md).

100원 최소 카드 청구액의 업그레이드 예약 문제도 기존 사용자 지시대로 다른 세션 담당이며 수정하지 않았다.

## 6. 로컬 적용과 보존

API4340은 이 세션 PID를 확인한 후에만 재시작했고 최신PID50850의 health와 새 요금제 조회200을 확인했다. 사용자 DB15438은 초기화/변경하지 않았고 별도 QA15439만 시험 후 컨테이너/임시 볼륨을 정리했다. 웹4241/4242와 다른 세션 서버/앱은 종료하지 않았다.

새 local-api 앱은 `desktop/clipper_electron/dist-app-w19-final/mac-arm64/Clipper Studio Local - promo-signup-20261102.app`에 별도 빌드했다. API4340·동일 세션 프로필·자동 업데이트 꺼짐을 산출물에서 확인했다. 이 산출물 경로는 Git 로컬 exclude에만 추가해 제품 커밋에 포함하지 않았다.

최초 기존 앱 종료는 자동 승인 검토가 작업 손실 가능성으로 거절해 유지했다. 이후 사용자가 ‘기존 앱 종료 해도 돼’라고 명시 승인해 새 앱을 실행했다. 최종 renderer 교체 후 앱 View 메뉴 Force Reload로 실제 새 번들을 확인했다. 회원/크레딧/프로모션 테스트 데이터와 로그인 프로필은 보존됐다.

실제 앱에서 허용 카드의 배지 생략과 Basic 이상/Pro 이상/Business, 상세의 ‘사용 가능 요금제 · Business’ 보라 배지와 설치 버튼 유지까지 확인했다. 다크 실화면과 두 스킴 실제 계산색 단위검사를 구분한다.

이번 완료는 **원격 dev 반영**이다. 공유 dev/운영 서버의 실제 배포·마이그레이션/worker 교체 완료나 실결제 승인을 확인한 것은 아니다. 배포 순서는 기존 W19 구현 기록을 따른다. `.codex` 문서 자체는 이번 요청으로 커밋·푸시하지 않았고 다른 세션 문서와 섞지 않았다.
