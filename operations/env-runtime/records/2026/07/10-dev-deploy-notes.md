# Dev Deploy Notes

작성일: 2026-07-10

이 문서는 2026-07-10 dev 배포 과정에서 확인한 m2-db/m2-stage/runner 운영 메모다. 실제 env 값, DB password, token 값, secret 파일 내용은 적지 않는다.

## 역할 분리

- m2-db: user/admin/release DB container가 실행되는 서버.
- m2-stage: web_api/web_client/web_admin Docker app stack을 실행하는 서버.
- Windows runner PC: Windows installer remote build/sign/upload runner.

## Secret Directory

Docker Desktop on macOS는 host file sharing 제한이 있다. `/opt/...` 같은 경로를 바로 compose mount하면 "path is not shared" 오류가 날 수 있다.

dev에서는 repo-local ignored secret directory를 사용해 compose mount가 가능하게 했다.

원칙:

- secret 값은 git에 올리지 않는다.
- secret 값은 문서에 적지 않는다.
- compose에는 container 내부 mount path만 노출한다.
- local host path는 환경마다 달라질 수 있으므로 장기 문서에 개인 절대경로를 고정하지 않는다.

## Release DB Reset

앱 identity를 개발 단계에서 새로 정리했기 때문에 dev release DB만 reset했다.

개념적 순서:

```text
1. m2-db에서 release DB container 상태 확인
2. release DB public schema reset
3. m2-stage web_api checkout을 dev 최신으로 확인
4. web_api에서 release migration 실행
5. m2-stage web_api 재배포
6. health check에서 user/admin/release DB 모두 ok 확인
```

주의:

- user/admin DB는 reset하지 않았다.
- release DB reset은 dev 한정 결정이다.
- prod에서는 기존 release/update path 보존 정책을 별도로 설계해야 한다.

## Web API Deploy

web_api 변경 후 m2-stage에서 수행할 개념적 순서:

```text
1. clipper_infra와 clipper_web_api가 origin/dev 최신인지 확인
2. 필요한 migration 실행
3. deploy-dev.sh api 실행
4. health endpoint 확인
5. 변경 endpoint 직접 확인
```

이번 세션에서 특히 확인해야 하는 endpoint:

```text
GET /downloads/latest
GET /releases/updates/stable/windows/x64/latest.yml
```

`/downloads/latest`는 web_client landing page 다운로드 버튼용이다. `/releases/updates/.../latest.yml`는 Electron auto-update feed용이다. 둘은 목적이 다르지만 stable Windows target에서는 같은 artifact를 가리켜야 한다.

## Web Client/Admin Deploy

web_client 변경 후:

```text
1. deploy-dev.sh client
2. https://dev.clipperstudio.ai 접속
3. Windows 다운로드 버튼 클릭
4. stable Windows artifact가 있으면 installer URL로 이동하는지 확인
5. Mac 버튼은 준비중 모달만 뜨는지 확인
```

web_admin 변경 후:

```text
1. deploy-dev.sh admin
2. /versions/releases release detail modal 확인
3. /versions/artifacts 정식 배포 modal과 저장 위치 표시 확인
4. /versions/targets stable target 확인
```

## Windows Runner Deploy/Health

runner PC에서 dev 최신 반영 후:

```text
1. infra dev pull
2. runner env preparation 실행
3. runner token/start-token이 m2-stage API env와 같은지 확인
4. runner container 재시작
5. runner /health 확인
```

주의:

- runner container가 workspace를 mount하고 있으면 `node_modules` native binaries가 lock될 수 있다.
- dependency 재설치나 cleanup 전에는 runner container를 중지한다.
- runner token 값은 문서나 로그에 남기지 않는다.

## 다음 배포 전 체크리스트

```text
1. web_api dev에 public download endpoint 커밋이 포함되어 있는가
2. web_client dev에 Windows/Mac split download CTA 커밋이 포함되어 있는가
3. web_admin dev에 release detail/artifact publish UI 커밋이 포함되어 있는가
4. m2-stage API health가 user/admin/release DB ok를 반환하는가
5. /downloads/latest가 404가 아닌 manifest를 반환하는가
6. stable Windows target이 존재하는가
7. Windows runner container가 healthy인가
```
