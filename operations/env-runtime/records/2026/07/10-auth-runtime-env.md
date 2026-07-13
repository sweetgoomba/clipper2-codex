# Auth Runtime Env And Secret Boundary

작성일: 2026-07-10

이 문서는 devapp/packaged/local API 실행과 JWT/provider credential 경계를 정리한다. secret-bearing 값, private key 원문, token 원문, env 실제 값은 적지 않는다.

## Boundary

### web_api

web_api는 인증과 provider credential의 authoritative boundary다.

- user access JWT를 signing한다.
- user JWT private key를 가진다.
- user JWT public key를 제공/배포할 수 있다.
- operator/admin JWT signing material을 가진다.
- provider credential DB를 읽고 decrypt한다.
- OpenAI/Naver provider runtime은 DB credential만 사용한다.

주의:

- OpenAI env fallback은 제거됐다.
- provider key를 desktop/electron/local NestJS/Python plugin env에 두지 않는다.
- operator/admin JWT와 user JWT는 audience/type/session 정책을 분리한다.

### desktop_electron

Electron은 native adapter와 packaged process host다.

- user refresh token bundle은 safe storage에 저장한다.
- provider key는 갖지 않는다.
- packaged app에는 user JWT public key PEM resource를 포함할 수 있다.
- public key는 secret이 아니지만, private key와 같은 디렉터리나 secret bundle로 취급하지 않는다.

### desktop_nestjs

local NestJS는 최종 auth truth가 아니다.

- local API ingress에서 user access JWT를 public key로 1차 검증한다.
- session revoke/license/credit/operation 판단은 web_api로 relay한다.
- refresh token은 local NestJS로 넘기지 않는다.
- provider credential은 local NestJS/Python plugin으로 넘기지 않는다.

## Mode별 Env 원칙

### devapp

devapp은 repo-local ignored env를 사용한다.

필요한 값의 종류:

- local NestJS auth mode
- local NestJS가 읽을 user JWT public key path
- web_api base URL

주의:

- 경로 원문은 팀/머신마다 달라질 수 있으므로 문서에 개인 절대경로를 고정하지 않는다.
- devapp 실행 명령에 긴 env prefix를 붙이는 방식보다 ignored env 파일에 넣는 방식을 우선한다.

### packaged

packaged 앱은 packaged resource와 packaged env를 사용한다.

필요한 값의 종류:

- local NestJS auth mode
- packaged resource 기준 user JWT public key path
- web_api base URL

Windows runner packaging에서는 public key resource가 반드시 설치되어 있어야 한다. 이 파일이 없거나 packaged env가 `jwt` mode를 지정하지 않으면 local API가 web user token을 검증하지 못하고 Settings/license/ledger API가 실패할 수 있다.

### local web_api

local web_api는 ignored `.env`와 ignored secret directory를 사용한다.

필요한 값의 종류:

- user JWT private/public key path 또는 값
- operator/admin JWT secret 또는 key path
- DB 연결 env
- OAuth env
- provider credential encryption material

실제 값은 문서화하지 않는다.

## HF Token 결정

HF token 관련 env는 이번 정리에서 desktop runtime 문서/파일에서 제거하는 방향으로 결정했다.

배경:

- provider credential 정책의 핵심은 외부 API key를 desktop/local plugin에 두지 않는 것이다.
- HuggingFace model download token은 provider 과금 key와 성격이 다르지만, 현재 제품 runtime 필수 credential로 고정하지 않았다.
- dialog/dance model download는 unauthenticated 또는 별도 운영 방식으로 정리한다.

후속 정책이 바뀌면 별도 문서에서 token 목적, 저장 위치, 배포 방식, 사용자 고지 여부를 다시 결정한다.

## Public Key 이름

팀 내 명칭은 `user-jwt-public.pem`으로 통일한다.

이름 원칙:

- `user-jwt-public.pem`: user access JWT 검증용 public key
- user JWT private key: web_api 전용, packaged app에 포함 금지
- operator/admin signing material: admin/operator JWT 전용, desktop app에 포함 금지

## 배포 전 확인

packaged 앱 또는 runner 준비 전 확인한다.

```text
1. web_api가 user JWT signing material을 읽을 수 있는가
2. web_api가 operator/admin JWT signing material을 읽을 수 있는가
3. packaged app resource에 user-jwt-public.pem이 포함되는가
4. local NestJS packaged env가 jwt mode와 public key path를 지정하는가
5. web_api base URL이 dev/stage/prod 목표 환경에 맞는가
6. provider key가 desktop/local env에 남아 있지 않은가
```
