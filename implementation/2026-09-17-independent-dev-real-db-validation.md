# 독립 개발판 — 승인된 로컬 실제 PostgreSQL 검증 결과

날짜: 2026-09-17 KST. 사용자는 새 DB 3개 생성/migration/자동 검증에 동의했고, 실행 장비가 **본인 로컬 Mac**임을 확인한 뒤 재승인했다. [대상·영향 사전 설명](2026-09-17-independent-dev-release-validation.md#후속-실제-로컬-db-검증안--승인-대기)을 실행했다. 개발/운영 서버가 아니다.

## 결과

- 새 컨테이너 3개와 각각의 전용 named volume을 생성했다. 기존 컨테이너·볼륨·데이터를 재사용하지 않았다.
- 새 빈 DB의 실제 migration chain 실행 성공. 최초 User/Release 새 nullable migration 적용 전에 합성 옛 형식 행을 넣고 적용 후 보존을 확인했다.
- 실제 TypeORM repository/AuthSessionService와 PostgreSQL을 사용하는 검증 **최종 9 PASS / 0 FAIL / 0 SKIP**. Web API `npm run build` PASS.
- 이번 turn 제품 구현 코드 변경 없음. API 저장소에 재실행 가능한 opt-in 테스트 `test/independent-desktop-db.test.mjs` 추가, `.codex` 인계 갱신. 모두 미커밋.
- 실제 `.env`/`.env.local` 변경·앱 재패키징/기동·Google 로그인·원격 API/runner/업로드·commit/push/merge/deploy 없음.

## 생성한 대상과 종료 상태

| 컨테이너 | loopback 포트 | DB | 완료 migration 수 | 종료 상태 |
|---|---|---|---:|---|
| clipper-identity-check-20260917-admin | 58433 | clipper_identity_admin | 64 | Exited (0) |
| clipper-identity-check-20260917-release | 58434 | clipper_identity_release | 3 | Exited (0) |
| 같은 Release 컨테이너 | 58434 | clipper_identity_release_prod_test | 3 | 위와 같음 |
| clipper-identity-check-20260917-user | 58435 | clipper_identity_user | 10 | Exited (0) |

`prod_test`는 로컬 합성 production profile 검증 DB이며 원격 운영 DB가 아니다. PostgreSQL 16 로컬 arm64 이미지 사용(pull 없음), 각 컨테이너 메모리 512 MiB·CPU 1 한도, 자동 restart 설정 없음. 각 볼륨 이름은 컨테이너 이름 뒤 `-data`; 삭제하지 않았다. `clipper.task=identity-check-20260917` 라벨과 실제 마운트/포트 일치를 확인 후 이번 3개만 정상 중지했다.

기존 dev 5433/5434/5435, 오늘 로그인 검증 57433/57434/57435 및 다른 프로젝트 DB는 전후 실행 상태 유지. 그 DB에 SQL 접속하거나 데이터를 바꾸지 않았다. 중지돼 있던 9/9 DB도 그대로 뒀다.

## 실제 검증한 내용

1. **스키마 이행·반복 실행:** 새 로그인 binding 컬럼/릴리스 profile 컬럼 이전의 합성 user/code/artifact가 유지되고 nullable 값은 null. 전체 migration 재실행은 빈 결과, pending 없음. 첫 실행과 이미 적용된 DB의 재실행을 로그에서 구분한다. 기존 개발 DB 복제본의 데이터 전환 리허설을 대체하지 않는다.
2. **로그인 1회 소비:** 실제 AuthSessionService + TypeORM User/AuthCode/Session 저장소 + 테스트 전용 임시 RSA 키. 잘못된 target/requestId/verifier는 거부하고 code를 소비하지 않는다. 동일 정상 코드 12개 동시 교환 중 정확히 1개 성공·11개 거부, 실제 session 행 1개, 이후 재사용 거부. Google 브라우저 OAuth 테스트는 아니다.
3. **최초 동시 게시:** 같은 dev/windows/x64 대상으로 서로 다른 artifact를 동시 게시해 target이 하나만 생기고 current/rollback 두 포인터에 두 artifact가 보존된다.
4. **오게시·잘못된 복원 거절:** dev→stable 또는 production profile→dev 요청을 거부하고 DB target/build를 변경하지 않는다. 잘못된 rollback profile 역시 포인터를 바꾸지 않는다.
5. **feed 분리:** 동일 DB에 유효한 production stable feed가 실제 존재할 때도, dev의 profile 불일치/빈 current target은 stable로 fallback하지 않는다.
6. **운영 후보 승격:** 별도 로컬 prod_test DB에서 production rc artifact를 stable에 게시하고 release 상태/피드를 확인했다. null-profile 옛 이력은 재게시 불가.
7. **동시 rollback/게시:** 가능한 두 직렬 실행 결과 중 하나만 남는지 검사해 중간/혼합 포인터가 남지 않음을 확인했다.
8. **Mac HOLD:** Mac과 Windows target 분리, 새 Mac target의 autoUpdateEnabled=false 및 업데이트 조회 없음.
9. **오류 원자성·runner 보고:** fixture DB에만 임시 트리거를 설치해 target 갱신 후 build UPDATE를 실패시켰고 target/build rollback 확인. 트리거/함수는 finally에서 제거했다. runner profile 불일치 보고는 job/build/artifact/attempt 성공 상태를 쓰지 않으며, 올바른 보고는 검증 profile과 ready/succeeded 상태를 저장한다.

위 항목은 Node 테스트 9개로 묶어 실행한다. 개별 성공은 해당 fixture/동시 요청 실행에 대한 증거이며 모든 운영 부하·장애 조합을 증명하는 것은 아니다.

## 재실행 안전장치·발견 사항

- 명시적 `CLIPPER_IDENTITY_DB_CHECK=20260917` 없으면 DB module import/접속 전에 실패한다. opt-in 미지정 실행이 의도한 오류로 종료되는 것도 확인했다.
- `DOTENV_CONFIG_PATH=/dev/null`; DB별 host/port/name/user/password를 테스트 프로세스에 고정한다. 초기화 직전 allowlist 확인, 연결 후 current_database/current_user 확인. HTTP fetch는 기본 거부한다. JWT는 테스트에서 생성한 임시 키이며 실제 secret을 사용하지 않는다.
- 첫 실행은 **8 PASS**. 이후 반복 실행에서 고정 `s3_key='fixture'`가 기존 fixture와 충돌해 hook이 실패했다. 제품 오류가 아닌 테스트 seed 문제로 확인하고 실행별 UUID로 변경했다. 당시 오류는 도구 출력에 남아 있으며 원인과 수정 내용을 이 절에 기록한다. final 로그 파일은 최종 성공 결과로 갱신됐다.
- 독립 리뷰: 마이그레이션 최초 적용과 재실행의 증거 구분, `beforeTargets[0]` 대신 명시적 dev/windows/x64 선택, 실제 stable target을 둔 fallback 검사 보완. 보완 후 재리뷰에서 추가 Critical/Important 없음. 리뷰어는 코드·로그를 읽었고 SQL/테스트 실행은 주 에이전트가 수행했다.
- 재실행은 전용 fixture DB에 합성 행을 추가하고 일부 fixture target/artifact를 정리한다. 새 DB를 앱의 실사용 데이터 저장소로 간주하거나 일반 환경에 이 테스트를 연결하면 안 된다. 테스트 suite를 동시에 여러 프로세스로 실행하지 않는다.

로그:

- 최초 새 DB 적용·8 PASS: `/tmp/clipper-identity-real-db-20260917.log`
- seed 수정 후 반복 검증: `/tmp/clipper-identity-real-db-repeat-20260917.log`
- 최종 9 PASS: `/tmp/clipper-identity-real-db-20260917-final.log`
- opt-in 차단: `/tmp/clipper-identity-db-optin-guard-20260917.log`

## 남은 순서

1. 실제 앱 실기용 로컬 API 환경을 정한다. 오늘 사용자가 로그인한 5743x DB는 이번에도 수정하지 않았다. 새 로그인 컬럼·DESKTOP_AUTH_TARGET을 적용하지 않은 기존 실행환경에서 새 앱 로그인이 검증됐다고 주장하지 않는다. `.env` 수정/실기 데이터 연결 범위를 설명한 뒤 진행한다.
2. 새 독립 개발판을 다시 패키징하고 실제 Google 로그인, 옛/새 개발판 및 운영판 동시 실행·프로토콜·데이터·로그인 복귀 분리를 검증한다. 실제 Google 계정 선택/동의는 사용자가 수행한다.
3. **필수:** 옛 배포 앱 `.cliptpl` 내보내기 → 새 빈 데이터 앱 가져오기, 자산/폰트/레이아웃 및 편집 재열기. 다른 로컬 자료 이관은 선택.
4. Windows 실제 EXE 설치/registry/업데이트·삭제 격리는 사용자 장비에서. Mac 공개/자동빌드/자동업데이트·ZIP, 실제 ML/Build5 전체 QA HOLD 유지.
5. PG 로컬 실기 후 개발 DB 복제본 리허설과 개발서버 전환 계획 승인을 별도로 진행한다. 서버 직접 접속 금지.

주간 한도 마지막 조회 잔여 **95%**. reset credit 미사용. commit/push/deploy 없음.
