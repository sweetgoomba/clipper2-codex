# Clipper2 인프라 쉬운 설명

작성일: 2026-06-02

## 한 줄 요약

Clipper2는 설치형 Electron 앱이다. 그래서 서버는 앱을 직접 실행하는 곳이 아니라, 설치파일 다운로드, 업데이트 정보, 계정/API, 관리자 화면, DB, 모니터링을 운영하는 곳이다.

2026-06-02 기준으로 `clipper_infra`에는 dev/stage/prod 초기 구성을 만들었다. 실제 IP, 도메인, S3 bucket, image tag, DB password 같은 운영 값은 아직 placeholder다.

전체 구조는 이렇게 보면 된다.

```text
개발팀 로컬 PC
  -> 코드 작성과 로컬 테스트

Windows PC runner
  -> Windows 설치파일 빌드와 코드서명

Mac mini runner
  -> macOS 설치파일 빌드와 서명/notarization

S3
  -> 빌드된 설치파일 보관

3대 Mac mini 서버
  -> dev/stage/prod web/API/admin/DB/proxy/monitor 운영
```

## dohit과 가장 큰 차이

dohit은 웹 리워드 서비스다.

```text
사용자 브라우저
  -> dohit web 서버
  -> dohit API 서버
  -> DB 서버
```

사용자는 서버에 배포된 웹 화면 자체를 사용한다. 그래서 dohit의 `web + api`가 서비스 본체다.

Clipper2는 다르다.

```text
사용자 PC
  -> Clipper2 설치형 앱 실행

서버
  -> 다운로드 페이지
  -> 최신 버전 정보
  -> 설치파일 링크
  -> 계정/라이선스/API
  -> 관리자 화면
```

Clipper2의 제품 본체는 사용자의 PC에서 실행된다. 서버의 `web + api`는 제품을 배포하고 운영하기 위한 관문이다.

## 전체 구조도

```text
[개발팀 개인 로컬]
  기능 개발 / 버그 수정 / 로컬 테스트
        |
        v
[GitHub repo]
  코드 push / merge
  release build trigger
        |
        v
[CI/CD controller]
  push/merge는 검사만 실행
  명시적 release trigger만 runner에 빌드 지시
        |
        +-----------------------------+
        |                             |
        v                             v
[사무실 Windows PC runner]       [Mac mini runner]
  npm run build:app:win:x64       npm run build:app:mac:arm64
  Windows code signing            macOS signing/notarization
        |                             |
        +--------------+--------------+
                       |
                       v
                     [S3]
         dev/stage/prod 설치파일 보관
                       |
                       v
             [release metadata]
        플랫폼별 최신 버전과 다운로드 URL
                       |
        +--------------+--------------+--------------+
        |                             |              |
        v                             v              v
 [dev 다운로드 페이지]        [stage 다운로드 페이지]  [prod 다운로드 페이지]
  개발팀 내부용                 출시 후보 검증용       실제 사용자용
```

## 3대 Mac mini 서버 역할

현재 3대 Mac mini를 운영 서버로 쓴다면 추천 기본 구조는 다음이다.

```text
Mac mini 1: proxy/prod 서버
  - 외부 도메인 진입점
  - prod web client
  - prod admin web
  - prod API

Mac mini 2: dev/stage 서버
  - dev web client
  - dev admin web
  - dev API
  - stage web client
  - stage admin web
  - stage API

Mac mini 3: DB/backup/monitor 서버
  - dev DB
  - stage DB
  - prod DB
  - DB backup
  - health monitor
```

이 구조는 dohit의 3대 분리 방식과 비슷하지만, Clipper는 설치파일 build runner가 별도로 있다는 점이 다르다.

## dev, stage, prod 차이

### dev

개발팀 공용 실험 환경이다.

```text
dev
  - 개발 중인 기능을 빠르게 올려보는 곳
  - 깨져도 비교적 괜찮은 곳
  - dev DB는 reset 가능
  - dev 설치파일과 dev update feed 사용
  - 외부 사용자에게 공개하지 않음
```

### stage

출시 후보 검증 환경이다.

```text
stage
  - prod에 내보내기 전 최종 검증
  - 가능한 prod와 비슷하게 유지
  - stage DB는 함부로 reset하지 않음
  - stage 설치파일과 stage update feed 사용
  - 팀원/QA/내부 사용자 검증용
```

### prod

실제 사용자 환경이다.

```text
prod
  - 실제 사용자가 보는 다운로드 페이지
  - 실제 사용자 API
  - prod DB
  - prod 설치파일과 prod update feed
  - 배포는 수동 승인 또는 release 승인 후 진행
```

## 각 환경에 떠야 하는 web/API 컨테이너

각 환경마다 web client, admin web, API가 한 묶음이다.

```text
dev
  - clipper-web-client-dev
  - clipper-web-admin-dev
  - clipper-web-api-dev

stage
  - clipper-web-client-stage
  - clipper-web-admin-stage
  - clipper-web-api-stage

prod
  - clipper-web-client-prod
  - clipper-web-admin-prod
  - clipper-web-api-prod
```

각 역할은 다음처럼 이해하면 된다.

```text
web client
  - 사용자가 보는 다운로드/제품 페이지
  - OS별 설치파일 다운로드 버튼
  - 릴리즈 노트

admin web
  - 내부 운영자가 보는 관리자 페이지
  - release 등록/비활성화
  - 설치파일 링크 확인
  - 사용자/라이선스/운영 데이터 관리

API
  - 최신 버전 정보 제공
  - S3 설치파일 URL 제공
  - update feed 제공
  - 계정/라이선스/관리자 기능 제공
```

## DB 컨테이너

DB는 환경별로 분리한다.

```text
DB/backup/monitor 서버
  - clipper-db-dev
  - clipper-db-stage
  - clipper-db-prod
  - clipper-backup-dev
  - clipper-backup-stage
  - clipper-backup-prod
  - clipper-health-monitor
```

DB를 하나로 합치지 않는 이유는 간단하다.

```text
dev DB
  - 개발 중 실험과 reset 가능

stage DB
  - 출시 후보 검증용 데이터

prod DB
  - 실제 사용자 데이터
```

세 DB가 섞이면 dev 실험이 prod 데이터에 영향을 줄 수 있다. 그래서 컨테이너, DB 이름, volume, backup을 분리한다.

## 설치파일 빌드는 서버에서 하지 않는다

설치파일은 Docker 서버에서 만들지 않는다. 각 runner에서 만든다.

```text
Windows 설치파일
  - 사무실 Windows PC runner
  - npm run build:app:win:x64
  - Windows code signing
  - S3 업로드

macOS 설치파일
  - Mac mini runner
  - npm run build:app:mac:arm64
  - signing/notarization
  - S3 업로드
```

서버는 이미 S3에 올라간 파일을 다운로드 페이지와 update feed에서 보여준다.

## push와 release는 다르다

코드를 push하거나 main에 merge했다고 설치파일이 release되면 안 된다.

```text
코드 push/main merge
  - test/build check
  - 코드 공유
  - 설치파일 release 없음
  - S3 업로드 없음
```

설치파일 release는 명시적인 trigger로 실행한다.

```text
Windows dev release trigger
  -> Windows PC runner
  -> npm run build:app:win:x64
  -> S3 dev/windows 업로드
  -> dev windows release metadata 갱신

macOS stage release trigger
  -> Mac mini runner
  -> npm run build:app:mac:arm64
  -> S3 stage/macos 업로드
  -> stage macos release metadata 갱신
```

## Windows와 macOS release는 따로 관리한다

Windows와 macOS는 빌드 컴퓨터, 빌드 명령, 서명 방식이 다르다.

```text
Windows
  - runner: 사무실 Windows PC
  - command: npm run build:app:win:x64
  - signing: Windows code signing

macOS
  - runner: Mac mini runner
  - command: npm run build:app:mac:arm64
  - signing: macOS signing/notarization
```

그래서 release metadata도 플랫폼별로 관리한다.

```text
stage release metadata
  windows-x64:
    version: 0.9.12
    s3_url: s3://.../stage/windows/Clipper2-0.9.12.exe

  macos-arm64:
    version: 0.9.10
    s3_url: s3://.../stage/macos/Clipper2-0.9.10-arm64.dmg
```

제품 정책상 버전 번호를 맞출 수는 있다. 하지만 인프라 관점에서는 Windows release와 macOS release가 독립적으로 성공/실패한다고 봐야 한다.

## S3 경로는 환경과 플랫폼으로 나눈다

기존 S3를 유지한다면 경로는 이렇게 나누는 것이 이해하기 쉽다.

```text
s3://clipper-release/dev/windows/...
s3://clipper-release/dev/macos/...

s3://clipper-release/stage/windows/...
s3://clipper-release/stage/macos/...

s3://clipper-release/prod/windows/...
s3://clipper-release/prod/macos/...
```

다운로드 페이지는 S3를 직접 뒤지는 것이 아니라 API나 release metadata를 통해 최신 파일 URL을 받는다.

## 환경별 흐름

### dev release

```text
개발팀이 빠르게 내부 테스트하고 싶을 때
  -> dev release trigger 실행
  -> Windows/Mac runner가 필요한 플랫폼만 빌드
  -> S3 dev 경로 업로드
  -> dev 다운로드 페이지에서 다운로드
  -> 개발팀 테스트
```

### stage release

```text
출시 후보를 검증하고 싶을 때
  -> stage release trigger 실행
  -> Windows/Mac runner가 설치파일 빌드/서명
  -> S3 stage 경로 업로드
  -> stage release metadata/update feed 갱신
  -> 팀원/QA가 stage 설치파일로 검증
```

### prod release

```text
stage 검증 완료
  -> prod release 승인
  -> stage에서 검증한 파일을 prod로 promote하거나 prod release build 실행
  -> S3 prod 경로 업로드
  -> prod release metadata/update feed 갱신
  -> 실제 사용자가 prod 다운로드 페이지에서 다운로드
```

1차 출시에서는 prod release를 자동으로 열어두기보다 stage 검증 후 수동 승인으로 올리는 편이 안전하다.

## 추천 컨테이너 배치

```text
Mac mini 1: proxy/prod
  - edge proxy
  - clipper-web-client-prod
  - clipper-web-admin-prod
  - clipper-web-api-prod

Mac mini 2: dev/stage
  - clipper-web-client-dev
  - clipper-web-admin-dev
  - clipper-web-api-dev
  - clipper-web-client-stage
  - clipper-web-admin-stage
  - clipper-web-api-stage

Mac mini 3: DB/backup/monitor
  - clipper-db-dev
  - clipper-db-stage
  - clipper-db-prod
  - clipper-backup-dev
  - clipper-backup-stage
  - clipper-backup-prod
  - clipper-health-monitor
```

## 처음 만들 때 중요한 순서

1. 도메인과 서버 IP를 확정한다.
2. S3 bucket/prefix를 실제 값으로 확정한다.
3. release metadata를 DB에 둘지 manifest 파일로 둘지 정한다.
4. `clipper_infra/env/*.env.example`을 서버별 실제 env 파일로 복사하고 값을 채운다.
5. DB 서버에서 `db/compose.yml`을 배포한다.
6. dev web/API/admin부터 Docker 배포한다.
7. stage web/API/admin을 Docker 배포한다.
8. Windows PC runner에서 `npm run build:app:win:x64` release trigger를 붙인다.
9. Mac mini runner에서 `npm run build:app:mac:arm64` release trigger를 붙인다.
10. prod web/API/admin은 stage가 안정된 뒤 열어도 된다.

## 기억할 기준

```text
운영 서버
  - web/API/admin/DB/proxy/monitor가 계속 떠 있는 곳

CI runner
  - 설치파일을 빌드하고 서명하는 컴퓨터

S3
  - 빌드된 설치파일을 보관하는 곳

release metadata/update feed
  - 최신 버전과 설치파일 URL을 알려주는 정보
```

Clipper2 인프라는 dohit처럼 web/API만 띄우면 끝나는 구조가 아니다. web/API 서버 위에 설치형 앱 release, 플랫폼별 빌드 runner, S3, update feed가 함께 붙는 구조다.
