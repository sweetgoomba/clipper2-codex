# Windows Runner Dev Release Record

작성일: 2026-07-10

이 문서는 dev Windows release runner와 0.0.1 dev release 검증 기록이다. secret-bearing token 값, signing credential 값, private key 값은 기록하지 않는다.

## 배경

앱 identity를 `Clipper Studio` 기준으로 정리하면서 dev release DB를 초기화하고 Windows installer를 0.0.1부터 다시 생성했다.

관련 변경:

- product name: `Clipper Studio`
- appId: 공식 도메인 기반 desktop namespace
- packaged app info endpoint 추가
- Settings 앱 정보 live metadata 표시
- packaged local NestJS JWT auth/resource path 정리

## Runner 준비 절차 요약

Windows runner PC에서 필요한 준비:

```text
1. repo들을 dev 최신으로 fast-forward pull
2. user-jwt-public.pem을 runner workspace의 electron packaged resource 위치에 설치
3. release-runner env 파일을 준비
4. runner token과 runner start token을 m2-stage API env와 일치시킴
5. npm dependencies 설치
6. Windows smoke build 실행
7. runner container 실행
8. m2-stage에서 runner health 확인
```

주의:

- public key는 secret이 아니지만 private key와 혼동하지 않는다.
- token 실제 값은 문서화하지 않는다.
- runner env는 git에 올리지 않는다.

## Token mismatch 이슈

source snapshot 고정 요청에서 runner가 401을 반환했다.

원인:

- m2-stage API가 runner에 보낸 start token과 Windows runner env의 start token이 달랐다.
- runner 준비 스크립트를 실행할 때 token 인자를 명시하지 않아 기존값/기본값이 남을 수 있었다.

조치:

- runner 준비 스크립트에서 runner token과 runner start token을 명시적으로 전달하도록 정리했다.
- runner start script가 env 준비 단계를 포함하도록 보강했다.
- token 값 자체는 기록하지 않는다.

## Node modules EPERM 이슈

Windows runner PC에서 `npm ci` 또는 `node_modules` 삭제 중 EPERM이 발생했다.

관찰:

- `esbuild.exe`, native `.node` 파일 등이 locked 상태였다.
- node/electron/editor process를 종료해도 일부 lock이 유지됐다.
- 실행 중인 Windows runner container가 workspace를 mount하고 파일을 잡고 있었다.

조치:

```text
1. release runner container 중지
2. release runner container 삭제
3. node_modules 제거
4. dependencies 재설치
5. smoke build 재실행
6. runner container 재시작
```

후속 주의:

- dependency reinstall이나 workspace cleanup 전에는 runner container가 실행 중인지 확인한다.
- runner container가 실행 중이면 workspace native binaries가 locked 될 수 있다.

## Build/Upload/Auto-update 검증

검증한 흐름:

```text
1. web_admin release 생성
2. source snapshot 고정
3. Windows 원격 빌드 시작
4. runner가 dev repos를 snapshot commit으로 checkout
5. Windows installer build
6. signing
7. S3 upload
8. release job success report
9. artifact 정식 배포 target 지정
10. Windows app에서 auto-update 알림/설치 확인
```

0.0.7 dev 설치본에서 0.0.8 dev 업데이트가 감지되고, Windows 알림 및 UAC 이후 새 앱이 실행되는 것을 확인했다. 이후 app identity 변경으로 dev release DB를 reset하고 0.0.1부터 다시 시작했다.

## Packaged JWT auth 검증 메모

Windows packaged app에서 Settings/license/ledger API가 401/500으로 실패한 적이 있다.

원인:

- packaged local NestJS env에 `jwt` auth mode/public key path가 제대로 들어가지 않았다.
- installer 안에는 user JWT public key resource가 있었지만 local NestJS가 그 경로를 사용하지 않았다.

조치:

- Windows runner env preparation에서 packaged local NestJS auth mode와 public key path를 생성하도록 수정했다.
- packaged app 설치 후 Settings에서 license/current와 credit ledger가 정상 로드되는 것을 확인했다.

## 남은 작업

- 다음 remote Windows build 전 runner container health 확인
- runner env와 m2-stage API env token alignment 확인
- macOS packaged release flow는 아직 준비중
- release DB reset은 dev 한정 결정으로 유지
