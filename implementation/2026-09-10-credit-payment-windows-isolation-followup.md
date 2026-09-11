# 크레딧 표시 공통화·결제내역 필터·Windows 설치 충돌 후속

2026-09-10. 사용자 요청에 따라 사용분 환불 차단 검증보다 먼저 진행. 아래 초기 로컬 수정 상태보다 문서 마지막 배포 준비 기록을 우선한다. 마지막 운영 확인은 API3299a73/Admin3747eb0/Customer8c723c3. 공유 원본 변경, Build5 QA 대기·플러그인 검증 보류 유지.

## 1. 크레딧 사유 공통화

- 원인: API 원장 조회는 creditLedgerDisplay를 사용하지만 Admin 수동 지급표는 원문 reason을 표시. Customer는 원장 페이지에서 지급 사유를 찾아 일부 영어를 자체 변환하고 있었다.
- API creditGrantDisplayReason을 원장·Admin 지급표·회원 상세·Customer 지급 내역의 공통 표시 함수로 사용. 조회 응답에 displayReason을 추가하고 OpenAPI/양쪽 웹 모델·표시를 반영. 고객은 원장 페이지에 지급행이 없어도 같은 사유를 표시한다.
- 저장된 reason은 수정하지 않는다. 운영자가 입력한 사유는 operatorId를 통해 보존하며 알려진 시스템 지급 사유만 번역. 원장 조회는 동일 사용자 지급분을 조인하여 입력 출처를 확인한다.
- monthly access credit grant → 월 정기 크레딧 지급, one-time free trial → 최초 무료 체험 크레딧 지급. 과거 추가 크레딧 상품명 포함 사유도 같은 기존 변환 경로를 공유한다. 결제 상품 스냅샷 전체 이름 변경은 이번 변경과 별도.

## 2. 결제내역 카테고리 및 영수증

- 카테고리: 전체/구독 시작/구독 갱신/요금제 상향/추가 크레딧. GET /payments/history의 optional purpose를 DTO에서 검증하고 사용자 조건과 함께 SQL 페이지 조회 전에 적용한다.
- 필터 변경은 기존 요청 취소/행·커서 초기화. 더 보기에도 선택값 유지. 빠르게 바꿔도 이전 응답이 섞이지 않는 테스트 포함.
- 영수증의 원래 목적은 토스 Payment.receipt.url의 매출전표 연결. 공급자 응답은 dashboard-sandbox.tosspayments.com을 허용하지만 기존 API 조회/웹은 dashboard.tosspayments.com만 허용하는 불일치를 발견했다.
- API는 safeTossReceiptUrl로 공급자·주문 조회·회원/고객 내역 URL 검증을 통합. 두 공식 HTTPS 호스트만 허용하며 credentials/포트/외부 호스트 차단 유지. Customer/Admin의 검증도 두 호스트로 맞춤.
- 고객 영수증 URL이 없으면 기존 — 대신 제공 안 됨 표시. 해당 운영 주문의 raw receipt_url을 아직 읽지 않았으므로 모든 빈 영수증의 원인을 이 문제로 확정하지 않는다.
- 참고: https://docs.tosspayments.com/guides/v2/learn/payment-results 및 https://docs.tosspayments.com/reference . 테스트 URL 생성 여부와 실제 영수증 데이터 제공 여부를 구분한다.

## 3. Windows 설치 충돌

- 사용자: 개발판 Clipper Studio 실행 중 운영판 Clipper 설치 시 실행 중 안내 발생. OK를 누르지 않고 취소했으며 개발판은 계속 실행 중. 두 설치 파일의 이름/버전 및 실제 설치 경로는 사용자가 추후 확인 예정.
- 설치 중인 electron-builder NSIS의 탐지/종료 양쪽이 Path.StartsWith('$INSTDIR', 'CurrentCultureIgnoreCase') 사용. 기본 폴더가 …\\Clipper / …\\Clipper Studio이면 접두사가 겹쳐 재현되는 코드 결함 확인. 사용자 실제 산출물과의 대조는 아직 필요하다.
- 별도 Electron checkout에서 현재 의존성의 탐지·종료·재시도 매크로를 추출해 NSIS customCheckAppRunning으로 연결. 두 경로 모두 디렉터리 끝 구분자까지 비교하며 OrdinalIgnoreCase 적용. 경로는 환경변수 데이터로 전달하여 작은따옴표 등 사용자 경로의 코드 삽입 방지. PowerShell 불가 시 기존 정확한 실행파일명 비교 유지. 의존성 원본은 수정하지 않으며 예상 템플릿 변경 시 빌드를 중단해 재검토한다.
- 향후 개발판/운영판 Windows 설치·제거 모두에 적용. 앱 ID·제품명·업데이트 식별자·프로토콜·userData는 변경하지 않아 기존 데이터 위치를 보존한다.
- 런타임 코드에서 운영판은 ai.clipperstudio.app/Clipper/clipperstudio, 개발판은 ai.clipperstudio.desktop/Clipper Studio/clipper, 운영 userData/sessionData 설정 후 singleton lock, 캐시 경로/플러그인 포트 범위 분리 확인. 실제 Windows 동시 실행 증명과 구분한다.
- 기존 설치 파일 자체는 수정되지 않는다. 새 후보 빌드 후 개발판 실행 상태에서 설치/동시 실행/프로토콜·로그인·포트/업데이트·제거의 상호 간섭을 Windows에서 확인해야 한다. 현재 새 산출물 빌드·게시나 원격 프로세스 종료를 수행하지 않음.

## 검증과 작업 위치

- API 전체2503통과/21skip, 빌드 통과. SQL alias 정리 후 관련3테스트 추가 통과. Customer 전체270통과/빌드 통과. Admin 전체402통과/빌드 통과(기존567.26kB 번들 경고). git diff --check 통과.
- Electron TypeScript 빌드 통과. 전체420통과/1실패: 별도 checkout에 sibling renderer/Nest 패키징 산출물이 없어 기존 staged-resource 테스트 실패. 테스트를 끄거나 가짜 fixture를 넣지 않았다. 관련 분리 테스트48개 통과.
- node scripts/verify-nsis-process-check.mjs로 실제 NSIS 설치 및 제거 매크로 각각 warnings-as-errors 컴파일 통과. 생성한 실행 파일은 실행하지 않고 제거한다. 실제 Windows 설치·동시 실행 검증은 미완료.
- 웹 isolated base: /private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn 의 clipper_web_api/admin/client. Electron isolated: /private/tmp/clipper-isolation-fix-electron. Electron 상세는 그 checkout의 docs/superpowers/reviews/2026-09-10-windows-installation-isolation.md.
- 웹 배포 시 API를 먼저 반영한 후 두 웹 반영. 새 필터/표시 필드는 이전 API로는 동작하지 않는다. DB migration은 없다. Windows 수정은 기존 runner 후보 빌드와 별도 실기 검증 후 배포한다.

## 배포 요청 후 커밋 완료 — GitHub 전송 차단 당시 이력

- 사용자 요청: 웹 배포 후 직접 관리자에서 0.0.2 새 릴리즈를 만들고 빌드·정식 배포 버전 지정, 문제가 발생했던 Windows PC의 고객 다운로드 경로로 설치·동시 실행 재시험. 이 요청으로 커밋과 배포 진행을 승인한 상태다. 정식 릴리즈 생성/지정은 사용자가 수행한다.
- 4개 isolated checkout에서 다음 커밋 생성. node_modules 심볼릭 링크는 커밋하지 않음. 원본 API8/Admin7/Customer10 tracked 변경과 Infra 공유 변경 보존, 원본 Electron clean 유지.

| 대상 | 커밋 | 목적지 | 브랜치 |
|---|---|---|---|
| API | e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5 | https://github.com/OhMyMetabuzz/clipper_web_api.git | release/pg-expiry-20260910 |
| Admin | 59b7903b3810afd3f7cc2dd35266617e25511ec1 | https://github.com/OhMyMetabuzz/clipper_web_admin.git | release/pg-expiry-20260910 |
| Customer | 05121731b603a1251e4b61b7cdef14a94031d43a | https://github.com/OhMyMetabuzz/clipper_web_client.git | integration/toss-payments-pg-20260903 |
| Electron | 2d492fee3284263a2207a8a76d11aa035d01d9b0 | https://github.com/OhMyMetabuzz/clipper_electron.git | integration/toss-payments-pg-20260909 |

- Electron 일반 push는 샌드박스 DNS 실패 후 승인 검토 요청. 자동 승인 검토가 실행 전 거절: 사설 소스를 전송하는 정확한 저장소·브랜치·커밋에 대한 명시적 승인 부족 및 저장소 소유/공개 상태 미확인. 우회하지 않음. 다른 3개 push도 아직 미실행. 4개 정확한 목적지·커밋에 대한 승인 요청으로 정리.
- API 배포 직전 전체 테스트는 로컬 포트 sandbox EPERM으로 실패하여 허용된 환경에서 다시 실행, 2503통과/21skip 및 빌드 통과 확인. Electron 관련48테스트/TypeScript빌드/설치·제거 NSIS 컴파일 재확인 통과. 미사용 테스트 import 제거 후 신규2테스트 재통과. Admin402/Customer270 및 prod빌드의 이전 검증 이후 기능 변경 없음.
- 원격 ls-remote 확인: 4개 배포 기준 HEAD는 각각3299a73/3747eb0/8c723c3/dd4e9d6으로 변경 전 기준과 일치. 강제 push 없이 각각 일반 fast-forward push 예정.
- Windows 새 릴리즈 소스 브랜치: integration/toss-payments-pg-20260909. runner captureSourceSnapshot은 각 저장소의 origin 브랜치를 fetch하여 SHA를 고정한다. 새 소스 스냅샷의 Electron이2d492fee…인지 확인해야 한다. 0.0.2는 관리자 입력을 runner가 package.json/lock 버전에 적용하므로 저장소 package 버전을 별도 수정할 필요 없음.
- 나머지 해당 소스 브랜치 원격 SHA는 기존 Build5와 동일: Angular7ae7366/Nest780128a/Python260751d/API3b6d68d. 릴리즈 스냅샷에 포함되는 API 소스는 운영 API 이미지 배포 브랜치와 별개다.
- 푸시 후 m4-prod 기존 경로에서 API/Admin/Customer 각각 build-only → 예상 이미지 SHA 확인 → API start-only 및 DB3항목 health → Admin/Customer start-only/HTTP·컨테이너 revision 확인 순서. 서버 접근은 이전처럼 사용자가 명령 실행. 운영 교체·DB 변경·새 Windows 빌드·정식 지정은 아직 수행하지 않았다.

### 푸시 완료 후 사용할 m4-prod 이미지 빌드 명령

아래 명령은 후속 사용자 명시적 승인 및 4개 푸시 완료 후 실행 가능하다. 세 이미지 빌드만 하며 실행 컨테이너와 DB는 변경하지 않는다.

```bash
bash <<'SH'
set -euo pipefail
cd /Users/m4-prod/Documents/projects/clipperstudio/clipper_infra
test "$(git -C ../clipper_web_api branch --show-current)" = "release/pg-expiry-20260910"
test "$(git -C ../clipper_web_admin branch --show-current)" = "release/pg-expiry-20260910"
test "$(git -C ../clipper_web_client branch --show-current)" = "integration/toss-payments-pg-20260903"
./scripts/deploy-prod.sh api --build-only
./scripts/deploy-prod.sh admin --build-only
./scripts/deploy-prod.sh web --build-only
test "$(docker image inspect clipper-web-api:prod --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5"
test "$(docker image inspect clipper-web-admin:prod --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "59b7903b3810afd3f7cc2dd35266617e25511ec1"
test "$(docker image inspect clipper-web-client:prod --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "05121731b603a1251e4b61b7cdef14a94031d43a"
docker image inspect clipper-web-api:prod clipper-web-admin:prod clipper-web-client:prod --format '{{index .RepoTags 0}} revision={{index .Config.Labels "org.opencontainers.image.revision"}}'
SH
```

## 후속 명시적 승인 후 GitHub 푸시 완료

- 사용자 `승인했어`로 위4개 저장소·브랜치·커밋의 정확한 전송 승인. 자동 검토 거절은 해결되었고 추가 승인 대기가 아니다.
- 일반 push 모두 성공: API3299a73→e0e5b35, Admin3747eb0→59b7903, Customer8c723c3→0512173, Electrondd4e9d6→2d492fe. 각 ls-remote로 표의 전체SHA와 일치 확인.
- 푸시 직전4개 checkout의 HEAD 및 tracked clean 확인. API/Electron의 untracked node_modules 링크는 미포함. 원본 공유 변경 유지.
- m4-prod 웹 이미지 빌드·컨테이너 교체는 아직 실행하지 않았다. 다음은 위build-only 명령의 사용자 출력 확인 후 API health를 확인하며 API→Admin→Customer start-only 순서로 진행.
- 새0.0.2 릴리즈는 사용자 진행 예정. 소스 브랜치 integration/toss-payments-pg-20260909에서 새 스냅샷을 고정하고 Electron2d492fee3284263a2207a8a76d11aa035d01d9b0 포함을 확인. Windows 실기 설치/동시실행 미완료, 기존Build5 QA·플러그인 검증 보류 유지.

## m4-prod 이미지 빌드 완료 — 실행 컨테이너 교체 대기

- 사용자 출력으로 세 build-only 성공 확인. 이미지 SHA는 API e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5, Admin59b7903b3810afd3f7cc2dd35266617e25511ec1, Customer05121731b603a1251e4b61b7cdef14a94031d43a로 모두 예상과 일치.
- 세 빌드 모두 `No application or DB changes performed` 출력. 중복 빌드 불필요. 실행 컨테이너 교체와 배포 후 health/UI 확인은 아직 미완료.
- 다음은 API 이미지 SHA 재확인 후 api start-only, /health HTTP200·status ok·user/release/admin DB ok 및 실행 revision/running/restarts0 확인. 이후 Admin/Customer를 순서대로 교체한다. 새0.0.2 빌드·정식지정·Windows 실기검증은 별도 대기.

## API 운영 교체 완료 — Admin/Customer 교체 대기

- 사용자 m4-prod 출력으로 api start-only 완료 확인. DB migrations 미실행.
- clipper-web-api-prod running/restarts0/revisione0e5b356017cc55ea2d4f3e19ecd549bb802b5f5. 컨테이너 내부 /health HTTP200/status ok/service clipper_web_api, user/release/admin DB 모두 ok.
- Admin59b7903/Customer0512173 이미지는 준비됐으며 실행 컨테이너는 아직 교체 대기. 다음은 각 이미지 SHA 확인 후 Admin start-only/HTTP·실행SHA 확인 → Customer start-only/HTTP·실행SHA 확인.
- Windows0.0.2 새 스냅샷·빌드·정식지정 및 실기 설치/동시실행 검증은 미완료. Build5 QA·플러그인 검증 보류 유지.

## 웹3종 운영 배포 완료 — 화면 확인 및 Windows0.0.2 대기

- 사용자 m4-prod 출력: clipper-web-admin-prod running/restarts0/revision59b7903b3810afd3f7cc2dd35266617e25511ec1, admin HTTP200. clipper-web-client-prod running/restarts0/revision05121731b603a1251e4b61b7cdef14a94031d43a, web HTTP200. 두 start-only 모두 DB migrations 미실행.
- 앞선 API e0e5b35 운영교체/HTTP200·DB3항목ok와 합쳐 웹3종 배포 완료. 표시 사유 공통화·카테고리 필터·실제 영수증 링크의 배포 후 화면 확인은 별도 미완료다.
- 사용자 다음 진행: Admin /versions/releases에서 버전0.0.2/소스브랜치integration/toss-payments-pg-20260909로 새 릴리즈 준비 → 새 소스 스냅샷 고정 → 해당 릴리즈 행을 눌러 릴리즈 상세의 소스 스냅샷에서 Electron2d492fee3284263a2207a8a76d11aa035d01d9b0 확인 → /versions/coordinator의 대상 버전0.0.2 확인 후 Windows 빌드 시작 → /versions/artifacts에서 생성된0.0.2 Windows x64 파일과 상태/서명 확인 후 정식 배포 지정 → /versions/targets의 Windows 지정 확인 → 문제가 발생했던 PC의 https://clipperstudio.ai/에서 새 파일 다운로드 및 개발판 실행 상태에서 설치·동시실행 확인.
- 실제0.0.2 스냅샷/빌드/서명/정식지정/다운로드/Windows 설치결과는 아직 제공받지 않았다. 원본 공유 미커밋 및 기존Build5 QA·플러그인 검증 보류 유지.

## 사용자 Windows 설치·동시 실행 확인 — 운영판 로그인 전

- 사용자가 후속 Windows 설치에서 개발판 종료 안내가 사라졌고 설치 후 두 앱이 동시에 실행됨을 명시적으로 확인했다. 기존 Clipper Studio는 metabuzz2023@gmail.com 로그인 상태로 계속 실행 중이며, 운영판 Clipper는 로그인 화면이다.
- 설치 과정에서 개발판 프로세스 종료/로그인 해제 없이 공존하는 흐름은 사용자 실기 확인 완료. 두 앱 모두 로그인한 후의 세션 유지, 업데이트/제거 상호 간섭 및 플러그인 동작은 별도 미검증. 실제 설치파일명/Build 번호/파일 버전·고정 SHA 증거는 아직 전달되지 않아0.0.2 계획과의 산출물 대조는 남겨둔다.
- 동일 계정 운영판 로그인 질문에 인증 정책 읽기 전용 확인: Electron 운영 identity는 userData/sessionData와 auth.bin 저장 경로 및 로그인 프로토콜을 분리하고 운영 API override를 적용. 개발 기본 API는 dev-api.clipperstudio.ai. API createSessionBundle은 동일 API의 동일 user·deviceLabel/clientKind/platform 세션만 same_device_login으로 회수하며 다른 기기 전체를 로그아웃시키지 않는다.
- 기대 동작: 개발/운영이 각자의 API·DB를 사용하는 정상 구성에서는 같은 Google 이메일로 양쪽 로그인 가능, 개발 세션 유지 및 운영 세션 별도 발급. 기존 개발 설치 파일의 실제 API override는 확인하지 않았으므로, 만약 같은 운영 API/동일 기기를 공유한다면 기존 세션 회수 가능성은 있다. 운영판 로그인 후 개발판에서 계정 정보를 다시 조회하여 로그인 유지 여부를 확인할 단계다.
- 이 확인은 기존Build5 전체QA 완료나 플러그인 검증 재개를 뜻하지 않는다. 두 보류 유지.

## 사용자 동일 계정 동시 로그인 유지 확인

- 후속 사용자 명시 확인: 개발판과 운영판 모두 metabuzz2023@gmail.com으로 동시에 로그인되며 양쪽 로그인 유지. 앞선 운영판 로그인 전/동시 로그인 미확인 표기는 이전 단계 이력이다.
- 이번 신규 설치 흐름에서 개발판 종료 안내 제거, 두 앱 동시 실행, 기존 개발판 로그인 보존, 같은 계정의 양쪽 로그인 유지까지 사용자 확인 완료. 업데이트/제거 및 플러그인 검증까지 완료했다고 확장하지 않는다.
- 앞선 같은 서버·같은 PC 세션 설명은 하나의 인증 서버/세션 저장소에서 같은 사용자·기기 메타데이터에 해당하는 이전 세션을 새 로그인으로 교체하는 정책을 설명한 것. 구 개발판의 실제 API override를 확인하지 못한 상태에서 조건부로 언급했으며, 현재 사용자 실기 결과에서 로그인 충돌이 발견된 것은 아니다. API 주소·DB 분리 자체를 원격 재조회했다고 기록하지 않는다.
