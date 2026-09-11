# TEST PG 세션 종료 및 다음 작업 인계

## 새 세션 읽기 안내 — 병렬 운영 구축 세션 검토

**최신 정본:** [9/10 현재 상태·Git·배포 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md)를 먼저 읽는다. APIe0e5b35/Admincd3a306/Customer4d95a96 배포 및 최신 두 웹 UI 확인 완료. Windows 현재 설치0.0.3.7의 CPU 표시도 사용자 확인. 아래 ab86/8980/b5를 최신으로 부르는 문장과 Customer 미배포·키조사 미해결 결론은 과거 통합 시점 기록이다. 공유 원본 변경은 이미 배포된 통합 스냅샷과 재대조했으며 상세 잔여를 새 감사에 분리했다.

후속 업데이트: [Admin 표시 수정·운영 확인 기록](2026-09-10-admin-display-followup.md)을 먼저 대조한다. API9b1b395/Adminfa7e67a 후속 배포·health 및 취소 TEST 구독/무료체험 관리 화면, Customer 과거 지급사유 한글 표시 확인 완료. 아래ab86b3d/8980eab는 직전 배포 이력이며 Customer b5dc797은 유지된다.

이 문서를 시작점으로 사용하되, [운영 구축 종료문서](2026-09-10-production-setup-session-closeout.md)와 [TASKS](TASKS.md)도 함께 읽는다. Windows runner 오류 원인·수정, Build 5 검증 범위, 재생성 후 Git 경로 등록 등은 운영 구축 종료문서가 상세 정본이다.

- 최신 웹 배포 상태는 아래 **후속 통합 완료 / 사용자 실행으로 확인한 운영 반영 결과**를 우선한다: API ab86b3d, Admin 8980eab, Customer b5dc797. 서버에 현재 재접속해 확인한 값이 아니라 사용자 실행 증거의 마지막 확인값이므로 작업 재개 시 재조회한다.
- 아래 1·4·5·8절 중 “API 8e1ce22가 최신”, “Customer 미배포”, “네이버 미통합”, “키 소실 조사 미해결” 및 그와 연결된 TODO는 **후속 통합 전 이력**이다. 현재 작업으로 그대로 반복하지 않는다. Customer 일부 화면은 후속 사용자 확인됐고 링크/필터 동작 등 남은 범위만 구분한다.
- 키 소실 조사는 사용자 정정으로 종료됐다는 후속 PG 기록을 따른다. 운영 구축 종료문서의 빈 테이블/원인 미확정 기록은 당시 관찰이다.
- 운영 구축 세션에서 원격 API 이력을 별도로 검토했다: ab86b3d의 부모는 8e1ce22와 06316a4이며, 923c9cb와 3b6d68d도 조상이다. 월 지급·무료 체험 한국어 표시 코드가 유지된다. 이 확인은 전체 기능 E2E나 현재 서버 상태 검증을 뜻하지 않는다.
- Build 5는 QA 대기, 플러그인 QA는 사용자 보류다. 새 세션 시작만으로 공개·QA 승인·보류 검증 재개가 승인된 것으로 간주하지 않는다.
- 원본 M표시는 통합 후에도 남을 수 있다. 현재 diff와 통합 커밋을 대조한 후 처리하며 reset/stash/중복 커밋을 자동 실행하지 않는다.

기준: 2026-09-10. 과거 로그의 ‘미배포/대기/다음’보다 이 문서의 현재 상태를 우선한다. 상세 증거: [기능 테스트 기록](2026-09-09-pg-functional-test-log.md). 전체 체크리스트: [TASKS](TASKS.md).

## 후속 통합 완료 — 이전 미커밋/미푸시 설명보다 우선

사용자가 브랜치 통합과 Customer 변경의 즉시 진행을 요청해 다음을 완료했다. **아래 3커밋은 사용자 실행 결과로 운영 배포·revision·running/restarts0·HTTP200까지 확인됐다. 새 화면 기능 확인은 남았다.**

| 저장소 | 푸시 완료 커밋 | 브랜치 | 검증 |
|---|---|---|---|
| API | `ab86b3d3ad930abd5b62b6c86289042ab4522ad8` | release/pg-expiry-20260910 | 전체 2486 통과/16 skip, 빌드 통과 |
| Admin | `8980eab6378f81dcca8b272fe9d1d86cd902612a` | release/pg-expiry-20260910 | 전체394 통과, 빌드 통과; 초기번들566.39kB 경고 |
| Customer | `b5dc7976199cc309b25971e56aec84cdd45ac1d9` | integration/toss-payments-pg-20260903 | 전체265 통과, 빌드 통과 |

- API/Admin은 기존 release와 integration 양쪽 부모를 보존하는 merge 커밋이다. 크레딧 표시를 양쪽에서 다른 위치에 추가해 OpenAPI 중복 key가 발생했으며, 계약 테스트가 검출해 단일 선언으로 수정했다. PG 수정과 네이버 기능 모두 포함한다.
- Customer는 지급일시/사유/결제링크/회수유형/만료안내, 월간탭 비활성, 갱신 실패 안내와 기존 `/pricing` 로그인 복귀 허용 변경을 포함했다.
- 원본 API/Admin의 추적 미커밋과 통합 결과를 대조했다. API OpenAPI 중복 표시 선언 정리를 제외하면 일치했다. untracked compose는 제외했다. 공유 원본 작업트리는 변경하지 않았으므로 M표시는 남지만 위 원격 커밋에 해당 변경이 포함된다. 원본 checkout 정리는 별도이며 reset/stash 미실행.
- 작업 디렉터리: `/private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn`. 원본 node_modules만 링크해 사용했다. 디스크 부족으로 중단된 검증은 이전 임시 Angular 캐시만 정리한 후 재실행해 통과했다.
- 사용자 정정: 제공자 키는 운영 관리자에 아직 등록하지 않았던 것으로 판단해 **소실 원인 조사 종료**. 아래 과거 미확정 기록을 현재 장애로 취급하지 않는다.

### 운영 반영 순서

1. m4-prod API/Admin checkout은 release, Customer는 integration인지 확인하고 각 build-only 실행. 예상 이미지 revision은 위 3개다.
2. API 시작 전에 관리자 DB의 pending migration을 점검한다. 새 `AddNaverUsageApis1789000000000`은 provider_credentials에 nullable 4컬럼 및 CHECK를 추가하고 기존 naver 행의 사용 API를 빈 배열, datalab 카운터를 0으로 초기화한다. 기존 네이버 키는 새 UI에서 search/datalab 용도를 선택해야 한다.
3. 기존 migrate-db.sh는 user/admin/release의 모든 pending migration을 실행하므로 목록/백업 확인 없이 곧바로 실행하지 않는다. 운영 schema와 migration 적용 기록을 읽기 전용으로 확인한 후 필요한 관리자 migration을 적용한다.
4. API start-only 및 health/DB 확인 → Admin/Customer start-only → revision/HTTP/강력 새로고침/UI 확인. 기존 redirect/runner/token 설정 보존.

### 사용자 실행으로 확인한 운영 반영 결과

- 2026-09-10 14:22 KST 사전 조회: 네이버 새 컬럼0개, 마지막 migration1788900000000, naver 키2개.
- 단일 트랜잭션 SQL로 AddNaverUsageApis1789000000000와 같은 DDL/UPDATE 및 migration 기록을 적용해 COMMIT. UPDATE2, 키2개 유지. 전체 migration runner는 실행하지 않았다.
- API ab86b3d 재시작 직후 HTTP000/connection reset이 있었으나 후속 조회 running/restarts0, HTTP200 및 user/release/admin 모두ok.
- Admin8980eab 및 Customer b5dc797 running/restarts0와 각각 HTTP200 확인.
- 사용자 네이버 용도 저장 완료 보고. 실제 검색/데이터랩 호출 성공은 별도 미검증.
- 사용자 Customer 화면으로 지급일시KST·지급사유·결제내역 링크 표시·만료/회수 합계 제외 안내·결제 환불 회수 유형과 필터 표시 확인. 총4800=무료400+추가4400 유지. 링크 이동/필터 동작 자체는 별도 미검증.
- 과거 지급 사유 `추가 크레딧 구매: 400 Credits` 1건은 영어 상품명 그대로 표시됨. 과거 원문 표시 개선 잔여로 기록하며 원장 데이터는 변경하지 않는다.
- 남음: redirect/runner/token의 재배포 후 별도 확인, 연간 월간탭 비활성 및 재시도 실패문구의 운영 화면 검증. 붙여넣은 텍스트만으로 반응형 레이아웃을 검증한 것은 아니다.


## 조사 범위와 한계

- 사용자 서버 실행 결과, 전체 대화와 테스트 로그, TASKS, 원본 API/Admin/Customer의 git status·diff·log·릴리스 차이를 대조했다. 종료 정리 시 git ls-remote로 원격 최신 해시도 읽었다.
- 운영 서버는 정리 시 다시 접속하지 않았다. 운영 버전은 사용자 실행 결과와 이후 사용자가 전달한 병렬 운영 구축 세션의 배포 보고를 구분해 기록한다.
- TEST PG 범위다. 실제 live 결제·정식 출시·전체 예외 검증 완료가 아니다. 시간압축 검증을 실제 한 달/1·2·3일 경과 또는 동시성 검증으로 확대하지 않는다.
- 이번 정리에서 서버·DB·결제·소스 브랜치 변경 없음. env/비밀 값 미조회·미기록.

## 1. 배포와 원격 현황

| 저장소 | 이 세션 마지막 운영 확인 | 종료 정리 시 원격 최신 | 의미 |
|---|---|---|---|
| API | PG 직접 확인 `923c9cbf224ac5ed08eac3af276e718c5c9dac80`; 이후 운영 구축 보고 `8e1ce22afee89ca134131cd71c23cd27f6e0f580` 배포·HTTP200·DB3항목ok·한국어 표시 확인 | release `8e1ce22afee89ca134131cd71c23cd27f6e0f580`; integration `06316a41828af5508b0ebe679aae3bf661119908` | PG 수정 위에 원장 한글화 추가 배포됨. 후속 배포 증거는 사용자가 전달한 다른 세션 보고이며 서버 재조회는 안 함 |
| Admin | `62a56690b338567aa8882e6b7aabb523d2db2df0`, running/restarts0/HTTP200 | release 동일; integration `cafebe3778e86a9e4537d1aae8a4b8497e24f6f1` | 이번 수정 배포·전액환불 안내 화면 확인 완료 |
| Customer | `888c2b96d818857306e9376c3436563c394971b1`가 이 세션 마지막 확인 | integration `ae75f51a79c103e0063cc383a2184218c164764a` | 이번 세션 Customer 배포 없음. 별도 원격 커밋 및 로컬 미커밋 변경 존재 |

release는 `release/pg-expiry-20260910`, integration은 `integration/toss-payments-pg-20260903`이다. m4 API/Admin checkout은 사용자 확인 당시 release였다. 로컬 원본 checkout은 integration이며 공유 변경을 보존했다.

**주의:** 로컬 API release 포인터는923c9cb, 원격은8e1ce22다. 다음 build-only는 최신 upstream을 당기므로 923c9cb만 빌드한다고 가정하지 말 것. 강제 푸시 금지.

## 2. 완료한 TEST 검증

| 범위 | 결과 | 검증 한계 |
|---|---|---|
| 추가 구매 | 400/5,900원·4,000/29,900원 주문/지급/원장/30일기한/Toss조회 대조 | 모든 결제수단 E2E 아님 |
| 미사용 추가구매 환불 | 5,900원 전액취소·400회수1건·다른잔액 보존 | 사용량·부분환불 실제 데이터 별도 |
| 미사용 월간 환불 | 10,900원 취소·구독/권한종료·1000회수1건·빌링키삭제 | 실패복구 매트릭스 별도 |
| 하향 예약·갱신 | Pro→Basic 예약/미동의차단/취소/재예약·압축갱신5,900원·Basic400 지급 | 실제 월경과·중복/실패 조합 별도 |
| Basic 월간→연간 | 차액52,906원·기존400회수/새400지급·연간기간/청구일 대조 | Business월간24,006원은 견적/만료, 결제성공 아님 |
| 연간 월별 지급 | 압축경계 후 기존400만료·새400원장1건·추가청구없음 | 실제월경과·강제중복·동시성 별도 |
| 연간 월별지급 후 환불 | 52,906원 취소·월별400회수1건·만료 첫달400기록 유지·구독/키삭제·총4800 | 압축된 지급 상태 기준 |
| 취소 웹훅 멱등 | 같은 전송2회 inbox1건/시각불변·다른전송ID 처리 후 금액/원장불변 | 모든 이벤트 동시성 아님 |
| 주문 미도착 웹훅 | 1/4/16/64분 재시도 후 manual_review/RETRY_EXHAUSTED | 재시도 후 성공복구 별도 |
| 옛 상향 취소웹훅 | 목적불일치 manual_review 1건 재큐잉→processed·72017환불/원장2건·합계0 유지 | 새 환불 실행 안 함 |
| 신규 연간 취소웹훅 | CANCELED/processed·오류없음/retry0 | 기존 목적불일치 재현 안 됨 |
| A12 수동 갱신복구 | TEST거절→유예→설정제거→동일주문5900성공·active·800 | 다른 PG오류 별도 |
| A13 자동재시도/유예 | 실패2회·index2/retryNULL·최종stopped/access ended·무료400 | 압축 검증; 만료코드 수정 후 유예경로 실환경 재현 별도 |
| 수정후 자동만료 | 신규 Basic취소예약·경계압축→subscription/access ended·credit expired 자동처리 | 해지예약 경로만 통과 |
| 완료환불 재접수 UI | 전액5900/잔액0·추가환불없음·회수완료 정확히 표시 | 부분환불 테스트가 아님 |

## 3. 코드 수정과 배포

- API `88ae3f1`: 상향결제 one_time/billing 웹훅 분류, 특정 TEST구독·회원·금액·1시간 범위 실패 주입.
- API `8acbb90`: 확정 카드거절 후 provider 주문미존재 확인 시 새 청구 멱등키. 기존 주문/지급 식별자 보존. 실제 복구 확인.
- API `37cdcdb`: 자연종료/이미 종료된 경로의 크레딧 만료처리 보완. 원장·만료 잔여량 보존.
- Admin `c319249`, `b3492e2`: 상하단 지급표 만료시간 반영·회수 분류·환불 원장 유형.
- Admin `4367fa8`: 접수 성공 후 새 환불 상세 자동이동. 테스트38건/배포 확인. **새 환불 실행으로 운영 이동 검증은 아직 안 함.**
- API `923c9cb`, Admin `62a5669`: 전액/부분/미확인 분리·환불완료금액·추가처리없음 안내·상품별 설명. 정확한 release코드에서 API95/Admin41테스트·두 build 통과. Admin 초기번들565.90kB/500kB 경고 남음.
- 강력 새로고침 후 최신 전액환불 화면 확인. 캐시의 정확한 계층과 배포 캐시정책은 미조사.

## 4. 미커밋·미푸시·미배포 감사

### API 원본

미커밋8파일: OpenAPI, access-grants 서비스/테스트, monthly-credit-grant 서비스/테스트, refund-eligibility 서비스/테스트, payments-openapi-contract 테스트.
이 세션의 해당 변경은 별도 release커밋으로 이미 배포됐다. **M표시가 곧 미배포는 아니다.** 원본 integration에 반영/정리하는 작업은 남음. reset 금지.

untracked `docker-compose.pg-local.yml`은 이번 배포에 넣지 않았다. 출처/사용 의도는 확정하지 않았으므로 삭제·커밋 전 별도 확인.

### Admin 원본

미커밋7파일: models, member-detail html/ts/spec, refund-workbench html/ts/spec. 이번 PG수정은 release에 포함됐다. 다만 member-detail 원장의 displayName/displayDescription 표시와 테스트는 release와 추가 차이가 있다. 이는 integration 원장표시 작업과 연결되며 release62a5669에는 없다.

integration `cafebe3`의 Naver키 UI·원장표시 기능도 별도 작업이다. API 의존·migration 범위를 검토한 후 통합해야 한다.

### Customer: 실제 미완료 로컬 수정

미커밋10파일. 이번 PG세션에서 commit/push/배포하지 않음.

| 파일 묶음 | 내용 | 남은 작업 |
|---|---|---|
| credits.component html/ts/scss/spec, models | 지급일시KST·사유·결제내역 링크·만료/회수 합계제외 안내·모바일·환불회수유형/필터·월별지급한글 | 최신 코드 검증·분리커밋·push·Customer배포·실제화면 |
| dashboard.component html/ts/spec | 연간 이용중 월간탭 비활성 표시·수동재시도 실패문구 | 동일 절차 |
| auth-api.service ts/spec | `/pricing` 로그인 returnPath허용 | 다른작업 변경으로 별도 확인 |

지급사유/결제링크는 로드된 지급 원장에서 찾는다. 페이지 단위 로딩 때문에 모든 지급건의 연결정보가 항상 보장되지는 않는 제한이 있다.

원격 Customer `ae75f51` 원장한글화와 API release `8e1ce22` 원장한글화는 이미 푸시된 별도 커밋이다. API는 운영 구축 세션의 배포 완료 보고를 받았다. Customer 배포 여부는 미확인이다.

**이 세션에서 만든 release커밋 중 미푸시인 것은 없다.** 하지만 원본 integration/release 통합·중복패치 정리와 위 Customer 변경이 남음. 작업트리 삭제나 중복 cherry-pick 금지.

## 5. 다음 세션 TODO

1. 다음 배포 전에 현재 서버 revision/원격 최신 읽기 전용 확인. API8e1ce22를 보존하고 Customer ae75f51 배포 여부 확인. 운영 구축 세션에서 추가한 redirect/runner 설정도 비밀 값 출력 없이 보존 확인.
2. Customer 로컬 변경을 다른작업과 분리해 최신 테스트 후 커밋/배포. 과거 테스트만 믿고 공유HEAD 전체 배포 금지.
3. 환불 상세 자동이동은 다음 필요한 TEST환불 때 확인. 이미 완료한 주문 재환불 금지.
4. 실제 부분환불·사용량있는 충전/연간·환불 실패/내부복구·권한별 차단. d8782ce3는 전액환불 건이었다.
5. 수정 만료코드의 past_due 유예종료 재현·동시 worker/중복실행·재기동 복구. 자연월/일 경계 별도.
6. 종료 Admin의 ‘해지 예약’ 잔존 문구, 종료시각 —, 수동이용권관리 빈 등급/상태·‘결제 구독’ 사유 정합성 검토. 관찰만 했고 미수정.
7. 만료 원장/이용권 종료 감사이력 정책 확인. 화면에는 지급만 보였음. expire원장/종료이벤트 생성 여부와 필요성은 미확정. 임의 원장 추가 금지.
8. 카드변경 이전키 정리/다음청구 새키사용, 실패·연체·취소, 금지 요금제 조합 남은 검증.
9. 웹훅 MID/키별·옛ngrok등록 정리,콜백/지급 동시성·복구,환불 중 자연종료 경합.
10. TEST 실패 override 파일 정리 여부 확인. 실행중 설정은 제거 확인했으나 `/tmp/clipper-pg-a12-failure.override.json`, `/tmp/clipper-pg-a13-failure.override.json` 삭제는 미실행. 재적용 금지.
11. 전체 branch/PR 통합과 공유 변경 정리,빌드 용량 경고·캐시정책 점검.

## 6. 계정/데이터 마지막 확인

### 메타버즈

- `metabuzz2023@gmail.com`, user `f47e0e29-217d-40e7-bc66-b22bf4c58c72`: Trial/총4800=무료400+추가4400.
- sub `89ba75e8-111b-4935-a131-069eddc4e3b4`: canceled/청구·retryNULL/빌링키삭제succeeded.
- annual order `21a547f3-3f79-437d-8530-dcba03bba8fa`, case `4caa171c-43f8-414f-ae9c-8e54d984dee6`:52906환불 completed/completed.
- 취소inbox `6461a476-cd6e-421e-9765-95e321874ffd`:processed/retry0.
- 옛 복구inbox `778c9ef6-554a-43c2-8316-fac26393491f`:processed/72017환불 불변.
- 완료환불 안내대상 order `d8782ce3-60b9-451d-866a-903994a32f44`:5900전액환불, grant `5193342b-8226-4f73-bb56-293a45d0b839` 회수.

### 한진아

- `wlsdk318@gmail.com`, user `9e7035f5-9b99-4ac1-88b5-c654133725f3`:마지막 Trial/무료400.
- 실패/복구 sub `be09b51b-4a00-4df9-a9b7-9ba74ae6c5a5`:stopped.
- 후속 만료회귀 sub `65a5a240-573e-466b-accc-f6b3e28fb201`:ended; grant `c6d4a96f-1e6a-4fae-b76f-f4b32a87154e`:expired.
- 실패order `e8309db5-0c68-492d-b811-0eca90eddaeb`:failed/REJECT_CARD_PAYMENT.

합성inbox `41151647-ec2b-40ec-8853-7e55bce8ef40`은 의도한 manual_review/WEBHOOK_RETRY_EXHAUSTED 종료상태. 무조건 재큐잉하지 말 것.
과거 일부 active/기한경과 지급건은 승인된 단일행 SQL로 expired 정리했음. 자동처리 검증과 구분한다.

## 7. 범위 밖 보류와 실행 원칙

[별도 운영구축 종료문서](2026-09-10-production-setup-session-closeout.md)의 Windows Build5 QA·플러그인 보류/Mac준비중/개발DB보류/모니터·백업복구/정식키·심사·실결제승인 항목은 이 PG세션에서 완료하지 않았다. 이후 배포 변화는 담당 작업 기록과 재대조한다.

가상계좌는 현재 TEST창에 없어 입금/만료 E2E 제외일 뿐 기능통과가 아님. 정책·약관/FAQ·전략팀 전달·live키·정식공개 별도.

- 서버명령은 사용자 실행: m4-prod 앱배포, m2-db READ ONLY 조회. 이 문서는 실행승인이 아니다.
- 배포스크립트 `/Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/scripts/deploy-prod.sh`.
- build-only는 upstream fast-forward+이미지빌드; start-only는 선택컨테이너 교체; migrations는 별도.
- TEST회원/주문/이전상태 가드 없는 DB변경 금지. 완료환불 재실행 금지. 개발초기화/live키/desktop 변경 범위 아님.
- `.codex`를 앱 소스push에 섞지 말 것. env·토큰 원문 기록 금지.

## 8. 병렬 운영 구축 세션 대조 결과

사용자가 전달한 운영 구축 종료 보고와 실제 로컬 Git 커밋을 대조했다.

- `git merge-base --is-ancestor 923c9cb 8e1ce22` 성공. 8e1ce22는 PG 환불 수정 이후의 자손으로, 기존 만료·환불 커밋을 보존한다.
- `923c9cb..8e1ce22`는 보고와 일치하는 크레딧 표시 관련 6파일, 114추가/6삭제다. 조회 SELECT의 동일 사용자 operation_runs JOIN, 선택 응답 필드 2개와 한국어 표시 함수/테스트만 추가된다. 이 차이에 마이그레이션·DB 쓰기·결제/환불/만료 로직 변경은 없다. OpenAPI의 PG 환불 수정도 유지된다.
- integration의 네이버 변경 전체가 release에 합쳐진 것은 아니다. 두 브랜치에는 같은 표시 기능의 별도 구현 이력이 있으므로 향후 내용 기준으로 통합해야 한다.
- 원본 API 미커밋 8파일과 untracked compose는 그대로다. PG 변경이 release에 이미 존재하므로 원본 M표시를 미배포로 오인해 다시 통째로 커밋하지 않는다. Admin/Customer 잔여 변경은 4절 참조.
- 공통 API 컨테이너는 양쪽 세션이 재생성했다. 코드 덮어쓰기 증거는 없지만 당시 요청 중단/설정 교체 여부까지 Git으로 입증할 수는 없다. 다음 배포 시 `DESKTOP_REDIRECT=clipperstudio://auth/callback`, runner `192.168.0.14:19030`, 요청/보고 토큰의 존재·일치 여부를 값 노출 없이 확인한다. 실패 주입 설정 제거도 유지한다.
- provider_credentials 빈 테이블 원인은 **미확정**이다. PG 로그 및 전달받은 DB 작업에서 해당 테이블 DELETE/TRUNCATE/DROP 기록은 발견하지 못했다. PG의 특정 구독 빌링키 삭제와 외부 제공자 키 저장소는 구분해야 한다. 기록 부재가 삭제 미발생의 증명은 아니며, DB 전체 감사로그/접속·복원 이력을 확인하지 않았으므로 특정 세션 탓으로 단정하지 않는다. 사용자 선택인 재등록의 완료 여부도 미확인이다.
- 운영 구축 보고의 테스트155건/계약60건/빌드 통과는 해당 세션 검증 결과다. 이번 문서 대조에서 테스트를 재실행하지 않았다.

결론: 확인한 Git 변경에서는 병렬 작업으로 PG 코드가 유실된 증거가 없다. 미해결은 브랜치 통합·미커밋 정리, Customer 미배포 변경, 제공자 키 재등록/원인, 공유 API 설정 보존 및 남은 E2E 검증이다. Windows Build5 QA와 플러그인 보류는 다른 세션의 잔여 작업으로 유지한다.
