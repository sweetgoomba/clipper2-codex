# 운영 웹 4개 저장소 `main` 승격 (2026-10-08)

## 범위와 현재 상태

이 작업은 m4-prod의 `clipper_infra`, `clipper_web_api`, `clipper_web_client`, `clipper_web_admin`에만 해당한다. 관리자 버전관리의 Windows 설치 앱 릴리즈 스냅샷(Angular/Python/NestJS/Electron/API 5개 저장소)은 별개이며, 이번에는 만들거나 배포하지 않는다. 팀의 개발 `dev`·운영 `main` 정책에 맞춰, 10/8 운영 컨테이너에서 확인한 파일을 원격 `main`에 반영했다. **사용자가 m4-prod에서 네 저장소를 `main`으로 전환하고 세 이미지를 빌드·기동한 결과를 확인했다.** 이 환경에서 직접 서버에 접속하지 않았으며, 아래 서버 상태 판단은 사용자가 제공한 터미널 출력에 근거한다.

| 저장소 | m4-prod에서 확인한 기존 HEAD/브랜치 | 원격 `main` (푸시 후 재조회) |
| --- | --- | --- |
| `clipper_infra` | `3cf915d95f9979d952e487eaa0caa0216f09045b` / `feature/toss-live-cutover-20261007` | `3cf915d95f9979d952e487eaa0caa0216f09045b` |
| `clipper_web_api` | `c22d90f3a528864c48e56750744f91c0ed602333` / 같은 feature | `c6ef00b7998bd7bbe28269e42d51f879dc7dda67` |
| `clipper_web_client` | `a27c3460aa2e633cfa6a2ce135e07c0947a36d2d` / 같은 feature | `0053af89cdf9246f2fd6f3ab02065e079073716b` |
| `clipper_web_admin` | `8025bc2aa8312174163f5c573f196e55c0902dab` / `dev` | `5578040182b712d5d97688a521c078312abd284b` |

API·고객 웹·관리자의 이전 `main`은 운영 커밋과 공통 Git 조상이 없는 오래된 초기 이력이었다. 기존 `main`을 각각 두 번째 부모로 기록하는 병합 커밋을 **운영 커밋 위**에 만들었다. 각 병합 커밋의 파일 트리와 첫 번째 부모인 운영 커밋의 파일 트리가 동일함을 `git rev-parse HEAD^{tree}` 및 `git diff --quiet`로 확인했다. `dev` HEAD는 세 운영 feature 커밋의 조상이고, 관리자는 운영 커밋 자체가 `dev` HEAD다. 인프라는 원격 `main`이 없어서 기존 운영 커밋을 그대로 새 `main`으로 만들었다. 원본 개발 체크아웃·`dev`·feature 브랜치는 변경하지 않았다.

### 변경 전 `main`·`dev`·변경 후 `main` 비교

| 저장소 | 변경 전 `main` | 변경 당시·현재 원격 `dev` | 변경 후 `main`과 `dev`의 실제 파일 차이 |
| --- | --- | --- | --- |
| 인프라 | 원격 `main` 없음 | `d050195` (10/7) | `dev` 뒤 운영 전용 4커밋. 12파일, +393/−61줄 |
| API | `0eab250` (6/8), 16파일 | `1feac57` (9/30) | `dev` 뒤 운영 전용 4커밋. 23파일, +497/−39줄 |
| 고객 웹 | `7bdaea` (6/8), 15파일 | `bd8fd8d` (9/22) | `dev` 뒤 운영 전용 9커밋. 20파일, +461/−317줄 |
| 관리자 웹 | `db26f4d` (6/8), 15파일 | `8025bc2` (9/22) | 파일 차이 없음. 당시 운영 서버 자체가 `dev`의 `8025bc2`를 사용 중이었음 |

API·고객 웹·관리자의 **변경 전 `main`과 `dev`에는 공통 Git 조상이 없다**. 두 트리를 파일 기준으로 비교하면 각각 API 889파일, 고객 웹 161파일, 관리자 웹 284파일이 달랐다. 오래된 `main`을 그 자체로 운영 서버에 체크아웃했다면 현재 운영 앱의 대부분이 사라졌을 것이다.
변경 전 `main`에서 변경 후 `main`까지의 트리 차이는 각각 API 890파일(+164,321/−1,786줄), 고객 웹 161파일(+24,185/−11,421줄), 관리자 웹 284파일(+44,197/−11,439줄)이다. 이 큰 수치는 6월 초기 트리와 이미 운영 중이던 현대 트리의 차이이며, **이번 라이브 전용 변경량**은 표의 `dev` 대비 수치로 봐야 한다.

실제 명령은 운영 커밋을 첫 번째 부모로 체크아웃한 격리 worktree에서 `git merge --no-ff -s ours --allow-unrelated-histories origin/main`을 실행한 것이다. 여기서 `ours`는 **운영 커밋의 파일 내용**이다. 이 병합은 이전 `main`을 이력의 두 번째 부모로 연결하지만 그 파일을 자동으로 채택하거나 충돌별로 합치지 않는다. 따라서 새 `main`의 트리는 현재 운영 feature/`dev` 트리와 정확히 같고, 이전 `main` 전용 파일은 현재 트리에 없다. API의 `env/local.dev.env.example`, `scripts/start-local-dev.sh`, 구형 `src/app.controller.ts`·`src/config.ts`·`src/database-health.service.ts`, `test/server.test.js`; 고객/관리자 웹 각각의 `docker-entrypoint.d/40-write-runtime-env.sh`, `src/styles.css`가 그 예다. 이 파일들의 과거 내용은 두 번째 부모 커밋에서 계속 조회·복원 가능하지만, 필요하다면 별도 검토 후 새 변경으로 복원해야 한다. 이력만 보고 과거 `main`의 모든 파일이 합쳐졌다고 해석하면 안 된다.

인프라·API·고객 웹은 원격 `dev`가 운영 feature 커밋의 조상임을 확인했다(`dev...feature`의 dev 전용 커밋 0개). 운영 전용 변경은 각각 인프라의 Toss 라이브 키·배포 검증과 운영 절차 4커밋, API의 단건 키 분리·고객 이메일·승인 거절·미시작 주문 만료 4커밋, 고객 웹의 단건 결제창·로그인 복귀·이메일·카드 표시 등 9커밋이다. 고객 웹의 빈 구매자명 실험과 되돌리기는 커밋 이력에 둘 다 있으나 최종 파일에서는 되돌려졌다. 관리자는 별도 운영 전용 커밋이 없었다. **원격 `dev`를 푸시하거나 변경하지 않았고**, 이 세 저장소의 운영 전용 커밋도 아직 `dev`에 반영하지 않았다. 단, 이번 운영 feature 자체가 최신 `dev`를 포함하므로 새 `main`에도 그때까지의 `dev` 변경은 포함된다. 이는 `main` 승격 이전 운영 소스에도 이미 들어 있던 내용이다.

### 이전 `main` 전용 파일 10개 재검토 (10/8)

옛 API·고객 웹·관리자 웹 `main`의 전체 추적 파일과 새 `main`의 전체 추적 파일을 비교해, 새 트리에 없는 **10개 경로 모두**를 확인했다. 옛 파일 내용과 옛 Dockerfile/Angular 설정, 새 앱의 참조·빌드·운영 Compose를 대조했다.

| 이전 `main`에만 있는 파일 | 이전 역할 | 현재 운영 소스와 판정 |
| --- | --- | --- |
| API `env/local.dev.env.example` | 로컬 개발 DB·포트 예시. `DATABASE_HOST`, `USER_DATABASE_*` 등의 옛 변수 사용 | 현행 API `.env.example`과 `src/core/database/db-config.ts`는 `CLIPPER_*_DATABASE_*` 계약을 사용한다. 현행 운영 Compose도 같은 접두사를 주입한다. 운영 배포에 불필요하다. |
| API `scripts/start-local-dev.sh` | 위 옛 env 파일을 읽어 로컬에서 `npm run build && npm start` | 현행 `package.json`의 `start:dev`와 `.env.example`이 로컬 개발 경로이며, 운영 Dockerfile은 `node dist/main`으로 실행한다. 운영 배포에서 호출되지 않는다. |
| API `src/app.controller.ts` | 옛 `healthz`·`v1/health`, `v1/info`, 미구현 `v1/releases/latest`(501) | 현행 `AppModule`은 별도 `HealthModule`과 `ReleasesModule`을 연결한다. 운영 상태 확인은 `/health`, 다운로드 매니페스트는 `/downloads/latest` 등 현행 엔드포인트를 사용한다. 옛 `v1/info`와 두 옛 health 경로의 **동일한 URL은 보존하지 않았다**. 현재 저장소 호출처·운영 배포 절차에서 그 URL을 참조하지 않는다. |
| API `src/config.ts` | 위 옛 컨트롤러용 설정·응답 타입, 옛 DB 변수·URL 파서 | 현행 `ConfigModule`·`src/core/database/db-config.ts`가 설정을 처리한다. 현행 소스에서 옛 `readConfig`를 참조하지 않는다. |
| API `src/database-health.service.ts` | `pg.Pool`로 세 DB에 `SELECT 1` | 현행 `src/core/database/db-health.service.ts`가 TypeORM 데이터소스 세 개에 `SELECT 1`을 실행하고 `/health`에 `ok`/`down`을 반환한다. |
| API `test/server.test.js` | 옛 `dist/config`, `dist/database-health.service`, 옛 경로를 검사 | 현행 `package.json`은 `src/**/*.spec.ts`를 Jest로 실행한다. 현행 DB 설정·헬스·릴리즈·AppModule의 관련 4개 suite/11개 테스트를 별도로 실행해 모두 통과했다. 운영 Docker 런타임에도 이 테스트 파일은 포함되지 않는다. |
| 고객 웹 `docker-entrypoint.d/40-write-runtime-env.sh` | 옛 Dockerfile이 Nginx 시작 때 `runtime-config.js` 생성 | 옛 `index.html`·앱 소스에서도 생성된 `CLIPPER_CONFIG`를 읽는 참조가 없었다. 현행 Dockerfile은 이 스크립트를 복사하지 않고, `angular.json`의 `prod` 파일 교체로 `environment.prod.ts`의 API URL을 빌드에 넣는다. 현행 운영 Docker 이미지에서 API URL 존재·`runtime-config.js` 참조 부재를 확인했다. |
| 관리자 웹 `docker-entrypoint.d/40-write-runtime-env.sh` | 고객 웹과 동일한 옛 방식 | 관리자 웹도 현행 Dockerfile·`environment.prod.ts` 방식이며, 운영 Docker 이미지에서 같은 검사를 통과했다. |
| 고객 웹 `src/styles.css` | 옛 Angular의 전역 스타일 | 현행 `angular.json`은 `src/styles.scss`를 전역 스타일로 지정한다. 운영 Docker 빌드 통과. |
| 관리자 웹 `src/styles.css` | 옛 Angular의 전역 스타일 | 현행 `angular.json`은 `src/styles.scss`를 전역 스타일로 지정한다. 운영 Docker 빌드 통과. |

**판정:** 빠진 10개 파일 가운데 현재 운영 앱의 빌드·기동·정적 파일/API 호출 경로에 다시 넣어야 하는 파일은 확인되지 않았다. 현행 운영 Docker 빌드(API·고객·관리자), 정적 파일 검사, 관련 API 테스트 11개가 이 결론을 뒷받침한다. API Docker 이미지도 새 `main`에서 별도 임시 태그로 빌드해 통과했다. 옛 `v1/info` 같은 URL까지 과거 API 계약을 복원했다는 뜻은 아니다. 현재 코드 안의 소비자는 없고 기존 운영 커밋에도 없는 경로지만, 저장소 밖의 미확인 소비자가 있다면 별도 계약 검토가 필요하다. 이 감사는 `main`에 코드를 추가하지 않았으므로 새 `main`과 기존 운영 커밋의 파일 트리 동일성이 유지된다.

**기존 코드와 옛 초기 `main`의 다른 동작:** 옛 API `/healthz`는 DB가 하나라도 비정상이면 HTTP 503을 반환했지만, 현행 `/health`는 DB 항목에 `down`이 있어도 HTTP 200과 최상위 `status: ok`를 반환한다. 따라서 운영 검증은 HTTP 코드만 보지 말고 `db.user/release/admin`의 `ok`를 모두 검사해야 한다. 옛 Dockerfile의 자체 `HEALTHCHECK`와 API의 `USER node`도 현행 Dockerfile에는 없다. 고객·관리자 웹의 옛 `/healthz` Nginx 경로와 이미지 헬스체크 역시 현행 구성에는 없다. 이 차이는 이번 병합으로 발생한 것이 아니라 병합 전부터 운영 중인 소스의 차이다. 이전 파일을 통째로 복원할 근거는 아니지만, 헬스체크·컨테이너 권한 강화는 별도 개선 대상으로 남긴다.

## 검증 결과

- 인프라 `node --test scripts/deployment.test.mjs`: 24개 통과.
- API `npm run build`와 `docker build`(임시 감사 태그): 통과. 전체 Jest는 샌드박스 밖에서 다시 실행해 2,970개 통과, 21개 건너뜀, 8개 실패. 실패는 기존 소스와 동일한 트리에서 catalog plugin 목록 기대값 5개, subscription resume 1개, effective access 2개다. resume 테스트는 9/29의 시각을 인자로 주지만 현재 구현·mock은 DB/현재 시각(10/8)을 사용하여 취소 기한 경과로 거절한다. 나머지 7개는 새 `shortform_director` 플러그인이 현재 목록에 있으나 테스트 기대 목록에 없는 차이다. 이번 병합의 파일 변경으로 생긴 실패는 아니며 테스트/구현의 기대값 정합성은 후속 정리 대상이다.
- 고객 웹과 관리자 웹의 Angular 컴파일(`ngc --noEmit`): 각각 통과. macOS 로컬 `ng build`는 시작 직후 SIGABRT였으나, 실제 운영 Dockerfile로 `ANGULAR_CONFIGURATION=prod` 이미지를 각각 빌드해 통과했다. 두 Docker 빌드는 임시 검증 태그만 만들었으며 m4-prod 이미지는 아니다.
- 원격 네 `main`을 `git ls-remote`로 재조회해 표의 SHA와 일치함을 확인했다.

## m4-prod에서 실행·확인한 작업

사용자가 10/8 m4-prod에서 아래 1·2단계 스크립트를 차례로 실행했다. 출력상 사전 HEAD·깨끗한 작업 트리·원격 target·조상 관계 검사를 모두 통과했고, 네 저장소가 표의 `main` SHA를 출력했다. `all --build-only`로 세 이미지를 만들었으며 이미지 revision label 검사를 통과했다. 이때 배포 스크립트는 애플리케이션·DB 변경이 없다고 출력했다.

이후 API → 관리자 웹 → 고객 웹 순으로 기동했다. 내부 API `/health`는 `status: ok`와 `db.user/release/admin: ok`를 반환했다. 두 사이트의 HTTP 200 검사는 스크립트가 `set -eu` 상태에서 끝까지 실행돼 통과한 것으로 확인된다. 최종 실행 컨테이너 label은 API `c6ef00b7998bd7bbe28269e42d51f879dc7dda67`, 고객 웹 `0053af89cdf9246f2fd6f3ab02065e079073716b`, 관리자 웹 `5578040182b712d5d97688a521c078312abd284b`로 표의 `main`과 일치한다. **DB migration은 실행하지 않았다.** 이 출력으로 운영 웹 네 저장소의 `main` 전환·세 앱 재기동을 완료로 기록한다. Windows 설치 앱 빌드·검증은 별도 후속이다.

아래는 실행한 절차를 재현·감사할 수 있도록 보존한 기록이다.

1. 네 저장소의 현재 브랜치·HEAD·작업 트리 깨끗함을 확인한다. 표의 기존 HEAD와 하나라도 다르면 진행을 멈추고 변경 원인을 조사한다.
2. 네 원격 `main`을 fetch하고 표의 target SHA와 일치하는지 확인한다. 현재 운영 HEAD가 target의 조상인지 확인한다.
3. 네 저장소를 `main`으로 전환하고 `origin/main`을 upstream으로 설정한다. `git merge --ff-only origin/main` 후 표의 target SHA와 일치하는지 확인한다.
4. `/Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/scripts/deploy-prod.sh all --build-only`로 이미지 3개를 먼저 빌드한다. **DB migration은 실행하지 않는다.** 이미지 revision label이 표의 API/고객 웹/관리자 `main`과 일치하는지 확인한다.
5. `api --start-only` → 내부 API health 및 세 DB `ok` 확인 → `admin --start-only` → 관리자 사이트 200 확인 → `web --start-only` → 고객 사이트 200 확인 순서로 기동한다. 재기동 직후 API의 초기 연결 실패만으로 곧바로 실패를 판정하지 않고 health를 재시도한다. 최종 컨테이너 revision label과 `main` HEAD가 같아야 서버 전환 완료로 기록한다.

전환 전에 만든 운영 이미지 태그 `prod-<기존 SHA>`는 배포 스크립트가 남긴다. 새 이미지 기동에 문제가 있으면 각 서비스의 기존 SHA 태그를 확인한 뒤 해당 이미지로 되돌리고, 원인 조사 전 DB migration이나 롤백성 데이터 조작을 하지 않는다.

### 1단계: 브랜치 전환과 이미지 빌드 (서비스 재기동 없음)

m4-prod의 터미널에서 실행한다. 먼저 **모든 저장소**의 기존 HEAD·작업 트리·원격 target을 검증하며, 불일치하면 이미지 빌드 전에 중단한다.

```sh
/bin/sh <<'SH'
set -eu
root=/Users/m4-prod/Documents/projects/clipperstudio
check_repo() {
  repo_path="$root/$1"
  old_sha="$2"
  main_sha="$3"
  test -z "$(git -C "$repo_path" status --porcelain)"
  test "$(git -C "$repo_path" rev-parse HEAD)" = "$old_sha"
  git -C "$repo_path" fetch origin
  test "$(git -C "$repo_path" rev-parse refs/remotes/origin/main)" = "$main_sha"
  git -C "$repo_path" merge-base --is-ancestor "$old_sha" "$main_sha"
}
check_repo clipper_infra 3cf915d95f9979d952e487eaa0caa0216f09045b 3cf915d95f9979d952e487eaa0caa0216f09045b
check_repo clipper_web_api c22d90f3a528864c48e56750744f91c0ed602333 c6ef00b7998bd7bbe28269e42d51f879dc7dda67
check_repo clipper_web_client a27c3460aa2e633cfa6a2ce135e07c0947a36d2d 0053af89cdf9246f2fd6f3ab02065e079073716b
check_repo clipper_web_admin 8025bc2aa8312174163f5c573f196e55c0902dab 5578040182b712d5d97688a521c078312abd284b
switch_main() {
  repo_path="$root/$1"
  main_sha="$2"
  if git -C "$repo_path" show-ref --verify --quiet refs/heads/main; then
    git -C "$repo_path" switch main
  else
    git -C "$repo_path" switch --track -c main origin/main
  fi
  git -C "$repo_path" branch --set-upstream-to=origin/main main
  git -C "$repo_path" merge --ff-only origin/main
  test "$(git -C "$repo_path" rev-parse HEAD)" = "$main_sha"
  printf '%s main %s\n' "$1" "$main_sha"
}
switch_main clipper_infra 3cf915d95f9979d952e487eaa0caa0216f09045b
switch_main clipper_web_api c6ef00b7998bd7bbe28269e42d51f879dc7dda67
switch_main clipper_web_client 0053af89cdf9246f2fd6f3ab02065e079073716b
switch_main clipper_web_admin 5578040182b712d5d97688a521c078312abd284b
/bin/sh "$root/clipper_infra/scripts/deploy-prod.sh" all --build-only
test "$(docker image inspect clipper-web-api:prod --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = c6ef00b7998bd7bbe28269e42d51f879dc7dda67
test "$(docker image inspect clipper-web-client:prod --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = 0053af89cdf9246f2fd6f3ab02065e079073716b
test "$(docker image inspect clipper-web-admin:prod --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = 5578040182b712d5d97688a521c078312abd284b
printf 'All main branches and three built images verified. Running containers unchanged.\n'
SH
```

### 2단계: 서비스 전환과 상태 확인

1단계가 성공한 뒤에만 실행한다. API가 기동 직후 DB 연결을 설정하는 동안에는 health를 재시도한다.

```sh
/bin/sh <<'SH'
set -eu
deploy=/Users/m4-prod/Documents/projects/clipperstudio/clipper_infra/scripts/deploy-prod.sh
/bin/sh "$deploy" api --start-only
healthy=no
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
  health_payload=$(/usr/bin/curl --connect-timeout 3 --max-time 10 -fsS http://192.168.0.47:43202/health 2>/dev/null || true)
  if printf '%s' "$health_payload" | /usr/bin/grep -Eq '"user"[[:space:]]*:[[:space:]]*"ok"' &&
     printf '%s' "$health_payload" | /usr/bin/grep -Eq '"release"[[:space:]]*:[[:space:]]*"ok"' &&
     printf '%s' "$health_payload" | /usr/bin/grep -Eq '"admin"[[:space:]]*:[[:space:]]*"ok"'; then healthy=yes; break; fi
  sleep 5
done
test "$healthy" = yes
printf '%s\n' "$health_payload"
/bin/sh "$deploy" admin --start-only
test "$(/usr/bin/curl -L --connect-timeout 3 --max-time 10 -sS -o /dev/null -w '%{http_code}' https://admin.clipperstudio.ai/)" = 200
/bin/sh "$deploy" web --start-only
test "$(/usr/bin/curl -L --connect-timeout 3 --max-time 10 -sS -o /dev/null -w '%{http_code}' https://clipperstudio.ai/)" = 200
/usr/local/bin/docker inspect clipper-web-api-prod clipper-web-client-prod clipper-web-admin-prod --format '{{.Name}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
SH
```

API health 본문의 세 DB 항목이 모두 `ok`일 때만 위 절차가 다음 서비스로 진행한다. 마지막 Docker label 세 값이 표의 원격 `main`과 일치하는지 확인한 다음 서버 전환을 완료로 기록한다.
