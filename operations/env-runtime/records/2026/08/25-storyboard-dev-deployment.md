# Storyboard 개발 서버 배포 기록

작성일: 2026-08-25 KST

## 범위

- `clipper_web_api` `dev`
- `clipper_web_admin` `dev`
- user DB와 admin DB의 미적용 migration

실행 서버의 저장소 배치는 `/Users/metabuzz/Desktop/project/clipper2` 기준이다. 실제 DB
비밀번호, 토큰, 키와 env 파일 내용은 이 문서에 기록하지 않는다.

## 1. 소스 최신화

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
git switch dev
git pull --ff-only origin dev

git -C ../clipper_web_api switch dev
git -C ../clipper_web_api pull --ff-only origin dev

git -C ../clipper_web_admin switch dev
git -C ../clipper_web_admin pull --ff-only origin dev
```

## 2. 새 API 이미지 빌드

migration 확인과 실행에는 새 API 코드가 들어 있는 같은 이미지를 사용한다.

```sh
cd /Users/metabuzz/Desktop/project/clipper2
docker build -t clipper-web-api:dev clipper_web_api
```

## 3. 대상 DB와 미적용 migration 확인

아래 확인 결과는 각각 `clipper_user_dev`, `clipper_admin_dev`였고 둘 다
`hasPendingMigrations: true`였다.

```sh
docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  run --rm --no-deps api \
  node --input-type=module -e "const module = await import('./dist/core/database/user.datasource.js'); const ds = module.default?.default ?? module.default; await ds.initialize(); const [{ database_name }] = await ds.query('SELECT current_database() AS database_name'); console.log({ database_name, hasPendingMigrations: await ds.showMigrations() }); await ds.destroy();"

docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  run --rm --no-deps api \
  node --input-type=module -e "const module = await import('./dist/core/database/admin.datasource.js'); const ds = module.default?.default ?? module.default; await ds.initialize(); const [{ database_name }] = await ds.query('SELECT current_database() AS database_name'); console.log({ database_name, hasPendingMigrations: await ds.showMigrations() }); await ds.destroy();"
```

DB 이름이 예상과 다르면 중단하고 env와 compose 대상을 먼저 확인한다.

## 4. API 중지 및 migration 적용

API만 잠시 중지한 뒤 user DB와 admin DB에 각각 migration을 적용했다. 어느 migration이라도
실패하면 API를 다시 올리기 전에 원인을 확인한다.

```sh
docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  stop api

docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  run --rm --no-deps api \
  node --input-type=module -e "const module = await import('./dist/core/database/user.datasource.js'); const ds = module.default?.default ?? module.default; await ds.initialize(); const migrations = await ds.runMigrations({ transaction: 'each' }); console.log(migrations.length ? migrations.map(({ name }) => name).join('\n') : 'No pending migrations.'); await ds.destroy();"

docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  run --rm --no-deps api \
  node --input-type=module -e "const module = await import('./dist/core/database/admin.datasource.js'); const ds = module.default?.default ?? module.default; await ds.initialize(); const migrations = await ds.runMigrations({ transaction: 'each' }); console.log(migrations.length ? migrations.map(({ name }) => name).join('\n') : 'No pending migrations.'); await ds.destroy();"
```

실제 적용된 user DB migration:

- `CreateReferenceAnalysisReplays1785400000000`
- `CreateShortformDirectorAiVideoJobs1786000000000`
- `CreateShortformDirectorAiImageJobs1786100000000`
- `DropShortformDirectorGeneratedMediaJobs1787800000000`

실제 적용된 admin DB migration:

- `SeedShortformDirectorStrategyOperationPolicy1785100000000`
- `SeedShortformDirectorVideoPlanOperationPolicy1785200000000`
- `RetireShortformDirectorCreditPolicies1785300000000`

생성 후 제거되는 작업 테이블 이름이 함께 보이는 것은 누적 migration 이력을 순서대로
적용했기 때문이다. 최종 스키마는 마지막 제거 migration까지 반영된 상태다.

## 5. API 재기동

```sh
docker compose \
  --env-file clipper_infra/env/stack.dev.env \
  -f clipper_infra/apps/compose.yml \
  -f clipper_infra/apps/compose.dev.yml \
  up -d --force-recreate api
```

## 6. 관리자 웹 배포

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
./scripts/deploy-dev.sh admin
```

스크립트가 infra와 admin 저장소를 최신화하고 `clipper-web-admin:dev` 이미지를 빌드한 뒤
`web-admin` 컨테이너를 재생성했다.

## 7. 외부 확인

```sh
curl -fsS https://dev-api.clipperstudio.ai/health
curl -fsSI https://dev-admin.clipperstudio.ai
```

확인 결과:

- API: `status: ok`, `service: clipper_web_api`
- DB: user/release/admin 모두 `ok`
- 관리자 웹: HTTP/2 200

## 다음 배포 시 주의

- `deploy-dev.sh`는 application migration을 자동 실행하지 않는다.
- 먼저 새 API 이미지를 빌드해야 그 버전에 포함된 datasource와 migration을 확인할 수 있다.
- user DB와 admin DB를 각각 확인한다. 한쪽만 실행하지 않는다.
- 대상 DB 이름을 확인하고 API를 중지한 뒤 migration을 적용한다.
- migration 실패 시 최종 `up`을 실행하지 않는다.
- 적용 후 API health와 관리자 웹 응답을 모두 확인한다.
