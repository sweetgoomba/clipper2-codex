# 앱 버전 관리 정책: 공통 제품 버전 + OS별 artifact

작성일: 2026-06-23
업데이트: 2026-06-26

이 문서는 관리자 앱 버전 관리 화면의 두 가지 설계안을 비교하고, 2026-06-26 확정된 정책을 기록한다.

- `/versions`: 공통 앱 릴리즈 + OS별 설치 파일 방식
- `/versions2`: macOS/Windows 독립 버전 스트림 방식

현재 두 화면은 API 없이 프론트엔드 mock data로만 동작한다. 이후 실제 구현 시 데이터는 `release` database에 저장하는 전제를 둔다.

2026-06-26 결정: **1번 방식(`/versions`)을 제품 정책으로 확정한다.** Clipper 앱의 user-facing version은 macOS와 Windows에서 항상 동일하게 관리한다. Windows-only 수정이어도 macOS artifact의 앱 버전도 함께 올린다. 이유는 OS별 독립 버전 스트림보다 공통 제품 버전 하나가 운영 엔트로피를 낮추고, admin/지원/릴리즈 노트/자동 업데이트 정책을 단순하게 유지하기 때문이다.

확정된 핵심 정책:

- 제품 버전은 하나다. 예: `2.5.0`.
- macOS/Windows artifact는 같은 `2.5.0` release 아래에 묶인다.
- Windows-only hotfix도 다음 공통 버전으로 올린다. 예: `2.5.1` macOS artifact도 함께 생성한다.
- stable 채널 publish는 필수 OS/arch artifact가 모두 성공하고 검증된 뒤에만 가능하다.
- OS별 artifact 상태, 서명/공증, checksum, runner, build log는 artifact 단위로 관리한다.
- `/versions2`는 독립 버전 스트림 정책으로는 채택하지 않는다. 다만 artifact 상태를 OS별로 강하게 보여주는 UI 감각은 `/versions` 화면 안에서 흡수할 수 있다.

---

## 공통 전제

데스크톱 앱 릴리즈는 단순히 `2.4.1` 같은 버전 번호만 저장하면 부족하다. 실제 운영에서 중요한 것은 다음 정보다.

- 어떤 설치 파일이 현재 다운로드 대상인지
- 문제가 생겼을 때 어떤 설치 파일로 롤백할 수 있는지
- 해당 설치 파일이 어떤 소스 코드 commit 묶음으로 만들어졌는지
- 앱 실행 중 호출하는 `clipper_web_api`와 호환되는지
- macOS/Windows 설치 파일이 각각 서명 또는 공증 완료 상태인지
- runner가 어떤 PC에서 어떤 job으로 빌드했는지
- S3에 올라간 파일의 key, checksum, size가 무엇인지

스냅샷에 포함하는 repo는 다음으로 좁힌다.

- 빌드 소스: `clipper_angular`, `clipper_nestjs`, `clipper_python`, `clipper_electron`
- 런타임 API: `clipper_web_api`

다음 repo는 앱 릴리즈 스냅샷에서 제외한다.

- 배포 인프라: `clipper_infra`
- 관리 화면: `clipper_web_admin`
- 다운로드 화면: `clipper_web_client`

Electron 자동 업데이트는 별도의 “n 미만 강제 업데이트” 정책 없이, 현재 다운로드 대상으로 지정된 설치 파일 또는 롤백 지정 파일을 기준으로 최신 대상 여부를 판단하는 방향을 기본으로 둔다.

핵심 원칙:

- 제품/기능 묶음은 release로 표현할 수 있다.
- 실제 build 시도는 release와 분리해서 표현해야 한다.
- 실제 배포 가능 여부는 artifact로 판단해야 한다.
- source snapshot의 목표값은 release에 둔다. build와 artifact에는 실제 checkout 증거와 release snapshot 일치 여부를 둔다.
- 다운로드 target은 release가 아니라 artifact를 직접 가리켜야 한다.
- stable release는 필수 artifact 전체가 준비되기 전까지 current target으로 승격하지 않는다.

---

## 방식 A: `/versions`

### 개념

하나의 앱 릴리즈 버전을 중심으로 보고, 그 아래에 OS별 설치 파일을 붙이는 방식이다.

예를 들어 `2.4.1`이라는 앱 릴리즈가 있고, 그 릴리즈에 다음 설치 파일이 연결된다.

- macOS arm64 dmg
- Windows x64 exe

버전 번호와 릴리즈 노트는 공통으로 관리한다. 설치 파일은 OS별로 별도 관리한다.

### 데이터 구조 감각

핵심 테이블을 만든다면 다음 형태에 가깝다.

- `release_versions`
  - version, channel_policy, source_branch, git_tag, release_notes, status, source_snapshot_id
- `release_builds`
  - release_version_id, build_number, channel, display_version, artifact_version, source_snapshot_id, status, started_at, finished_at
- `release_source_revisions`
  - release_version_id, repo, role, commit_sha, branch, summary
- `release_artifacts`
  - release_version_id, release_build_id, platform, arch, file_name, s3_key, sha256, signature_status, build_runner, status
- `release_artifact_attempts`
  - release_artifact_id, attempt_number, build_runner, status, started_at, finished_at, log_s3_key, error_summary
- `artifact_source_revisions`
  - release_artifact_id, repo, role, commit_sha, branch, summary, matches_release_snapshot
- `release_download_targets`
  - channel, platform, arch, current_artifact_id, rollback_artifact_id

`release_version`은 `2.5.1` 같은 공통 제품 버전 단위다. `release_build`는 그 제품 버전을 실제로 빌드하기 위해
공통 build number를 발급받은 build set이다. 같은 `2.5.1`이라도 build `449`, `450`, `451`처럼 여러 build set을 만들 수 있다.
`release_artifact`는 특정 build에서 나온 macOS/Windows 설치 파일 단위다.
`release_artifact_attempt`는 같은 artifact job을 재시도한 기록이다.

`release_builds.build_number`는 release coordinator가 발급하는 전역 단조 증가 번호로 둔다. 제품 버전마다
1부터 다시 시작하지 않는다. stable로 publish되는 macOS/Windows artifact는 같은 `release_build` 아래에
묶이고, 따라서 같은 build number를 공유한다.

예:

```text
release_version: 2.5.1
release_build: build_number 451
  display_version: 2.5.1
  artifact_version: 2.5.1.451
  macOS arm64 artifact: verified
  Windows x64 artifact: verified
```

같은 build에서 Windows runner가 일시 실패해 재시도하는 경우, source snapshot과 build config가 같다면
새 `release_build`를 만들지 않고 같은 artifact의 attempt를 추가한다. source snapshot, build config,
packaging metadata가 바뀌면 새 `release_build`와 새 build number를 만든다.

source snapshot은 release 단위에서 "목표 snapshot"으로 먼저 고정할 수 있고, build 단위에도 실제 build에
사용한 snapshot을 저장한다. artifact source snapshot은 각 runner가 실제로 어떤 commit을 checkout했는지
증거로 저장하며, stable publish 조건에서는 원칙적으로 release/build snapshot과 일치해야 한다. 예외적인
재빌드가 필요할 때만 artifact snapshot이 달라질 수 있고, 이 경우에는 별도 사유와 승인 기록이 필요하다.

### 장점

- 사람이 이해하기 쉽다. “이번 앱 버전은 2.4.1이고, Mac/Windows 설치 파일이 각각 있다”는 모델이다.
- 기능 릴리즈 노트가 중복되지 않는다.
- 같은 기능 묶음을 여러 OS에 배포하는 일반적인 앱 릴리즈 흐름과 잘 맞는다.
- 버전 번호 관리가 단순하다.
- 다운로드 페이지는 OS 감지 후 해당 OS의 current artifact만 내려주면 된다.
- 롤백도 OS별 artifact pointer만 바꾸면 된다.
- macOS/Windows가 같은 기능 묶음을 공유한다는 운영 판단을 표현하기 좋다.

### 단점

- 같은 버전 번호라도 OS별 빌드 상태가 다를 수 있다.
- Windows 빌드만 실패했는데 공통 릴리즈는 이미 만들어진 상태가 될 수 있다.
- OS별로 기능 포함 시점이 자주 갈라지면 “2.4.1인데 Mac에는 있고 Windows에는 없는 기능” 같은 설명이 필요해진다.
- OS별 테스트/승인 상태를 artifact 단위로 더 꼼꼼히 표시해야 한다.

### 적합한 경우

다음 조건이면 `/versions` 방식이 더 적합하다.

- macOS와 Windows가 대체로 같은 기능 세트를 같은 버전 번호로 배포한다.
- OS별 빌드 타이밍은 조금 달라도 최종 릴리즈 단위는 하나로 보고 싶다.
- 제품/고객 커뮤니케이션에서 “앱 버전 2.4.1”처럼 공통 버전 번호를 쓰고 싶다.
- 기능 릴리즈 노트를 한 번만 작성하고 OS별 설치 파일만 분리하고 싶다.
- OS별 차이는 주로 설치 파일, 서명/공증, runner, checksum, 다운로드 pointer 수준이다.
- 운영자가 “현재 정식 다운로드 Mac/Windows가 각각 무엇인지”를 빠르게 바꾸는 것이 핵심이다.

### 주의할 점

이 방식을 쓰더라도 artifact 상태는 OS별로 분리해야 한다. 공통 release가 `published`라고 해서 macOS와 Windows artifact가 모두 정상이라는 뜻으로 처리하면 안 된다.

예를 들어 `2.4.1` release 아래에서 macOS artifact는 `검증 완료`, Windows artifact는 `업로드됨` 또는 `검증 실패`일 수 있다. 다운로드 대상으로 지정할 수 있는 조건은 release가 아니라 artifact의 검증 상태를 기준으로 봐야 한다.

artifact 중심 `/versions`는 다음처럼 보아야 한다.

```text
Release 2.4.1
  Windows artifact
    status: verified
    signature: signed
    current target: yes

  macOS artifact
    status: limited or blocked
    signature/notarization: missing
    current target: no, beta, or internal only
    note: xattr 수동 실행 안내 필요
```

즉 `/versions`를 쓴다는 것은 macOS와 Windows를 같은 상태로 취급한다는 뜻이 아니다. 공통 제품 버전은 유지하되, OS별 설치 파일의 상태와 배포 가능 여부는 독립적으로 판단한다는 뜻이다.

---

## 방식 B: `/versions2`

### 개념

macOS와 Windows를 각각 독립적인 버전 스트림으로 보는 방식이다.

예를 들어 다음처럼 서로 다른 버전 흐름을 가진다.

- macOS: Mac 2.4.3
- Windows: Win 1.9.8

각 OS 버전은 독립적으로 현재 다운로드 대상, 롤백 대상, 릴리즈 노트, source snapshot을 가진다.

### 데이터 구조 감각

핵심 테이블을 만든다면 다음 형태에 가깝다.

- `os_release_streams`
  - platform, arch, current_release_id, rollback_release_id
- `os_releases`
  - platform, arch, version_label, version_value, release_notes, built_at, state
- `os_release_source_revisions`
  - os_release_id, repo, role, commit_sha, summary
- `os_release_artifacts`
  - os_release_id, file_name, s3_key, sha256, signature_status, build_runner, status

이 모델에서는 macOS 릴리즈와 Windows 릴리즈가 같은 버전 번호를 공유할 필요가 없다.

### 장점

- OS별 현실을 가장 정확하게 표현한다.
- macOS는 배포 가능하지만 Windows는 아직 테스트 중인 상황을 자연스럽게 다룰 수 있다.
- GPU 가속, 파일 권한, 설치 방식, 서명/공증처럼 OS별 차이가 큰 기능을 관리하기 쉽다.
- 같은 기능이 Mac에는 먼저 들어가고 Windows에는 나중에 들어가는 상황을 숨기지 않는다.
- OS별 담당자/runner/검증 플로우가 독립적인 조직에 맞다.

### 단점

- 운영자가 이해해야 할 정보가 많아진다.
- 릴리즈 노트와 기능 포함 여부 관리가 중복되기 쉽다.
- 고객에게 보이는 버전 체계가 복잡해질 수 있다.
- “기능 A가 어느 OS의 몇 버전에 들어갔는가”를 별도 매핑으로 관리해야 한다.
- 공통 코드베이스를 쓰는데 버전 스트림을 완전히 분리하면, 실제 코드 provenance를 더 엄격히 기록해야 한다.

### 적합한 경우

다음 조건이면 `/versions2` 방식이 더 적합하다.

- macOS와 Windows의 배포 주기가 자주 다르다.
- 같은 기능이 OS별로 다른 시점에 들어가는 일이 많다.
- OS별 버그와 테스트 실패가 잦고, 한쪽 OS 때문에 다른쪽 OS 배포를 막고 싶지 않다.
- Mac runner와 Windows runner의 빌드/검증/서명 플로우가 실질적으로 독립되어 있다.
- 고객에게도 OS별 버전 번호가 달라도 괜찮다.
- 기능 포함 여부를 OS별로 명시적으로 추적할 운영 여력이 있다.
- macOS는 아직 공증/서명 준비가 되지 않아 `xattr` 수동 안내가 필요하고, Windows는 코드서명 완료 상태처럼 OS별 배포 품질 차이가 장기간 유지된다.

### 주의할 점

이 방식에서는 “버전 번호”보다 “source snapshot”이 더 중요하다. 예를 들어 Windows `1.9.8`이 macOS `2.4.3`보다 낮은 숫자라고 해서 더 오래된 코드라고 단정하면 안 된다.

각 OS 릴리즈마다 다음을 반드시 저장해야 한다.

- desktop 4개 repo commit
- `clipper_web_api` 호환 commit 또는 API 계약 버전
- build runner
- artifact checksum
- 현재 다운로드 대상 여부
- 롤백 후보

---

## 핵심 비교

| 비교 항목 | `/versions` | `/versions2` |
|---|---|---|
| 기준 단위 | 공통 앱 릴리즈 | OS별 릴리즈 스트림 |
| 버전 번호 | 공통 버전 중심 | macOS/Windows 독립 |
| 설치 파일 | 한 릴리즈 아래 OS별 artifact | OS별 release가 artifact 보유 |
| 릴리즈 노트 | 공통 작성 | OS별 작성 |
| 기능 포함 여부 | 공통 기능 묶음 중심 | OS별 포함 버전 추적 필요 |
| 롤백 | OS별 artifact pointer 변경 | OS별 current release 변경 |
| 운영 복잡도 | 낮음 | 높음 |
| 현실 표현력 | 보통 | 높음 |
| 고객 커뮤니케이션 | 단순 | 복잡할 수 있음 |
| 추천 기본값 | 대부분의 제품에 적합 | OS별 배포가 실제로 독립일 때 적합 |

---

## 상황별 선택 기준

### `/versions`가 더 적합한 경우

공통 코드베이스에서 하나의 제품 버전을 만들고, macOS/Windows 설치 파일은 그 버전의 산출물로 관리하는 경우다.

예시는 다음과 같다.

- 제품 릴리즈 공지가 “Clipper 2.4.1 배포”처럼 나간다.
- Mac과 Windows가 거의 같은 기능을 제공한다.
- Windows 빌드만 늦어져도 최종적으로는 같은 `2.4.1` 범주에 묶고 싶다.
- 고객 지원이 “현재 최신 버전은 2.4.1입니다”라고 안내하길 원한다.
- 관리 화면에서 가장 중요한 작업이 “Mac current artifact 변경”, “Windows current artifact 변경”, “롤백”이다.

이 경우 DB는 공통 `release_versions`와 OS별 `release_artifacts`를 분리하는 것이 좋다.

### `/versions2`가 더 적합한 경우

OS별로 제품의 배포 흐름이 사실상 따로 움직이는 경우다.

예시는 다음과 같다.

- Mac은 매주 배포하지만 Windows는 2~3주에 한 번 배포한다.
- Windows 전용 GPU 버그 때문에 Windows 릴리즈가 자주 밀린다.
- Mac에는 이미 기능 A가 들어갔지만 Windows에는 아직 빼야 하는 일이 자주 있다.
- 고객 지원도 “Mac 최신은 2.4.3, Windows 최신은 1.9.8”처럼 OS별로 안내할 수 있다.
- OS별 QA/승인/릴리즈 담당이 다르다.

이 경우 OS별 release stream이 더 정직하다. 다만 기능 포함 여부와 source snapshot을 더 엄격히 기록해야 한다.

---

## 현재 프로젝트에 대한 확정 판단

현재 Clipper는 `/versions` 방식을 제품 정책으로 확정한다.

이유는 다음과 같다.

- desktop 4개 repo가 공통 코드베이스를 이룬다.
- 다운로드 화면은 OS 감지 후 현재 지정된 OS별 설치 파일을 내려주면 된다.
- Electron 자동 업데이트도 “현재 다운로드 대상 artifact”를 기준으로 판단하면 된다.
- 운영자가 당장 필요한 작업은 설치 파일 업로드, 검증 상태 확인, 현재 다운로드 지정, 롤백이다.
- 고객 지원과 릴리즈 노트는 “현재 최신 버전은 2.5.0”처럼 단일 버전을 기준으로 할 수 있다.
- OS별 독립 버전 스트림은 시간이 지날수록 예외, 문서, QA, 자동 업데이트 정책의 엔트로피를 높인다.

macOS와 Windows의 배포 준비도는 현재 다르다. Windows는 코드서명 전용 runner PC가 있고, macOS는 아직 별도 코드서명/공증 runner가 없다. 이 차이는 artifact 상태로 표현한다. 버전 스트림을 분리하는 이유로 사용하지 않는다.

예:

```text
Release 2.5.0
  macOS arm64 artifact
    status: built / signed / notarized / verified
  Windows x64 artifact
    status: built / signed / verified
```

Windows-only bug fix도 다음처럼 처리한다.

```text
기존 stable:
  macOS 2.5.0
  Windows 2.5.0

Windows installer bug fix:
  새 release 2.5.1 생성
  macOS 2.5.1 artifact 재빌드 또는 재패키징
  Windows 2.5.1 artifact 빌드
  둘 다 성공하면 stable current를 2.5.1로 승격
```

---

## 권장안

실제 DB/API는 `/versions` 모델을 기준으로 만든다.

구체적으로는 다음 방향이 좋다.

1. 공통 `release_versions`를 둔다.
2. 실제 build 시도는 `release_builds`로 분리한다.
3. OS별 설치 파일은 `release_artifacts`로 분리하고, 반드시 `release_build_id`를 갖게 한다.
4. OS별 build job 재시도 이력은 `release_artifact_attempts`에 저장한다.
5. 현재 다운로드 대상은 `release_download_targets`가 artifact를 가리키게 한다. 단, stable current 승격은 release/build/artifact 전체 검증을 통과해야 한다.
6. source snapshot은 `release_source_revisions`에 release 목표값으로 고정하고, `release_builds`와 `artifact_source_revisions`에는 실제 build/runner checkout 증거를 저장한다.
7. 강제 업데이트 기준은 release 또는 channel policy로 둔다. OS별 강제 업데이트 예외가 필요하면 artifact policy로 보완한다.
8. Electron 자동 업데이트는 current artifact 또는 rollback artifact pointer를 기준으로 동작하게 한다.

이렇게 하면 UI는 `/versions`처럼 단순하게 유지하면서도 DB의 진실은 artifact 중심으로 남길 수 있다.

`/versions2` 모델은 더 이상 메인 후보가 아니다. 다음과 같은 정보는 `/versions` 내부의 artifact 상태로 흡수한다.

- OS별 빌드 성공/실패
- OS별 코드서명/공증 상태
- OS별 QA 결과
- OS별 rollback artifact
- OS별 build runner/log/checksum

따라서 `/versions2`는 비교안/검토용 화면으로만 본다. 실제 구현은 artifact 중심 `/versions` 구조로 진행한다.

---

## 빌드와 릴리즈 운영 방향

현재는 사람이 각 빌드 PC에 직접 접속해서 명령을 실행한다.

```text
Windows build PC:
  npm run build:app:win:x64

Mac 개발자/빌드 PC:
  npm run build:app:mac:arm64
```

출시 준비 단계에서는 이 수동 운영을 끝내야 한다. 관리자 화면 또는 별도 release control plane에서 한 번의 명령으로 공통 버전 release를 생성하고, 필수 빌드 PC에 동시에 build job을 보내야 한다.

목표 흐름:

```text
Admin /versions
  -> "Build & Release 2.5.0" 클릭

clipper_web_api or release coordinator
  -> release 2.5.0 draft 생성
  -> release_build 생성
  -> build_number 발급
  -> build source snapshot 고정
  -> Windows runner에 build job 전송
  -> macOS runner에 build job 전송

Windows runner
  -> checkout source snapshot
  -> npm run build:app:win:x64
  -> code signing
  -> artifact upload
  -> checksum/log/status report

macOS runner
  -> checkout source snapshot
  -> npm run build:app:mac:arm64
  -> code signing/notarization
  -> artifact upload
  -> checksum/log/status report

release coordinator
  -> 필수 artifact 모두 success/verified 확인
  -> release build 2.5.0.<build_number> publish 가능 상태로 전환
  -> stable download/update target 갱신
```

stable 채널에서는 둘 중 하나만 성공한 상태로 버전이 올라가면 안 된다. 예를 들어 Windows artifact가 성공하고 macOS artifact가 실패하면 `2.5.0`은 draft 또는 blocked 상태로 남고, 사용자 다운로드/auto update target은 기존 stable을 유지한다.

```text
Release 2.5.0
  Build 451
    Windows x64: success
    macOS arm64: failed
  release status: blocked
  stable current: still 2.4.0
```

## Build runner 요구사항

### Windows runner

현재 Windows 전용 build PC가 있고 코드서명이 설치되어 있다. 이 PC는 release runner로 승격할 수 있다.

필요한 역할:

- release coordinator에서 build job 수신
- 지정된 repo/branch/commit checkout
- Node 22 고정
- Windows build preflight 실행
- `npm run build:app:win:x64` 실행
- 코드서명 적용
- artifact, checksum, build log 업로드
- 성공/실패 상태 report

### macOS runner

현재는 팀원 각자의 macOS 개발 머신에서 macOS installer를 빌드한다. 출시 준비 전에는 별도 macOS build PC, 예를 들면 Mac mini, 를 준비하는 것이 맞다.

필요한 역할:

- release coordinator에서 build job 수신
- 지정된 repo/branch/commit checkout
- Node 22 고정
- `npm run build:app:mac:arm64` 실행
- Apple Developer code signing
- notarization
- staple 검증
- artifact, checksum, build log 업로드
- 성공/실패 상태 report

주의: macOS 앱 build/sign/notarization은 일반 Linux Docker container에서 처리할 수 없다. macOS host, keychain, Apple signing credential이 필요하다. 따라서 "Docker container로 job을 전달"한다는 표현은 runner 격리/실행 인터페이스로는 사용할 수 있지만, 실제 macOS signing은 macOS host runner 또는 macOS에서 검증된 runner 환경이 맡아야 한다.

## Release 상태 모델

초안 상태는 다음처럼 둔다.

```text
release_versions.status
  draft       제품 버전 record 생성됨
  locked      release notes/source policy가 고정되어 build 생성 가능
  blocked     publish 가능한 build가 없거나 운영자가 배포를 막음
  retired     더 이상 새 build를 만들지 않는 과거 release version
```

build 상태는 release version이 아니라 `release_builds`에 둔다.

```text
release_builds.status
  queued      build job 생성됨
  building    하나 이상의 artifact build 진행 중
  blocked     필수 artifact 중 실패가 있음
  ready       필수 artifact가 모두 verified이고 publish 가능
  published   download/update target에 반영된 build
  failed      build attempt 실패
  superseded  같은 release version의 더 새 build로 대체됨
```

artifact 상태는 별도로 둔다.

```text
release_artifacts.status
  queued
  building
  built
  signing
  notarizing
  verified
  failed
```

artifact attempt 상태는 재시도 이력을 보존하기 위해 별도로 둔다.

```text
release_artifact_attempts.status
  queued
  building
  signing
  notarizing
  uploaded
  verified
  failed
  cancelled
```

운영 UI에서는 release의 배포 상태를 다음처럼 더 세밀하게 표시한다.

```text
release_versions.distribution_status
  draft       아직 준비 중
  candidate   publish 가능한 build가 있지만 아직 stable은 아님
  stable      현재 일반 사용자에게 배포 중인 정식 버전
  superseded  정상적으로 더 새 stable에 의해 대체된 과거 버전
  pulled      한때 배포됐지만 문제로 배포 대상에서 내려진 버전
  blocked     운영자가 배포를 막았거나 publish 가능한 build가 없음
  archived    더 이상 운영하지 않는 과거 버전
```

`stable`은 "현재 stable 채널의 active version"이라는 운영 상태다. `superseded`는 정상적인 구버전이고,
`pulled`는 문제 때문에 신규 다운로드와 자동 업데이트 대상에서 제거된 버전이다. `pulled`라고 해서
S3 artifact나 source snapshot을 삭제한다는 뜻은 아니다. 감사, 재현, 긴급 분석을 위해 파일과 기록은 남긴다.
`building`, `verified`, `failed`처럼 실제 build 진행과 검증을 나타내는 상태는 `release_builds`와
`release_artifacts`에서 판단하고, version 목록 UI는 그 상태를 요약해서 보여준다.

publish 조건:

- release version이 확정되어 있다.
- publish 대상 release build가 확정되어 있다.
- release build의 build number가 확정되어 있다.
- 필수 platform/arch artifact가 모두 존재한다.
- 필수 artifact가 모두 `verified`다.
- release/build source snapshot과 각 artifact의 실제 checkout snapshot이 저장되어 있고, 필수 artifact가 release/build snapshot과 일치한다.
- 각 artifact의 checksum, file size, build log가 저장되어 있다.
- stable current target 갱신이 원자적으로 처리된다.

## Auto update 방향

Electron auto update는 OS별 artifact를 내려받아야 하지만, 버전 판단은 공통 product version을 기준으로 한다.

예:

```text
client platform = windows x64
current version = 2.4.0
server stable release = 2.5.0
target artifact = release 2.5.0 / build 451 / windows x64
```

macOS client도 같은 stable release version을 본다.

```text
client platform = macos arm64
current version = 2.4.0
server stable release = 2.5.0
target artifact = release 2.5.0 / build 451 / macos arm64
```

즉 OS별 artifact는 다르지만, user-facing latest version은 하나다.

## 브랜치, 채널, 버전 표기 정책

채널은 "이 빌드가 누구에게 배포되는가"를 나타낸다. 버전 번호 자체가 아니라 배포 통로다.

권장 채널:

```text
alpha   개발팀 내부 확인용. 깨질 수 있는 개발 빌드.
beta    일부 외부/확장 테스트 사용자용. 현재는 필수 채널이 아님.
rc      release candidate. 문제가 없으면 그대로 stable로 승격할 출시 후보.
stable  일반 사용자에게 배포되는 정식 채널.
```

Clipper의 기본 매핑은 다음으로 둔다.

```text
dev branch
  -> alpha
  -> 개발팀 내부 확인용 build

stage branch 또는 release/<version> branch
  -> rc
  -> 출시 직전 QA/스테이징 검수용 build

production/release tag
  -> stable 후보
  -> 필수 artifact 검증과 수동 publish 승인 후 stable
```

브랜치가 곧 채널이라는 뜻은 아니다. 정확히는 release coordinator/CI가 "어떤 브랜치 또는 tag에서 나온
빌드를 어떤 채널로 publish할 수 있는가"를 제한한다는 뜻이다. 예를 들어 `dev`에서 만든 build는
`alpha`로만 publish할 수 있고, `stable`에는 직접 publish할 수 없게 막는다.

`stage = beta`보다 `stage = rc`가 더 정확하다. `beta`는 아직 실험/피드백 성격이 강한 테스트판이고,
`stage`는 보통 "문제 없으면 출시한다"는 최종 검수 단계다. 따라서 현재 Clipper에는 `beta`를 필수로
두지 않고, 나중에 외부 베타 프로그램이 필요해지면 추가한다.

저장 필드는 다음처럼 분리한다.

```text
productVersion: 2.5.0
channel: alpha | beta | rc | stable
displayVersion: 2.5.0-alpha.12 | 2.5.0-rc.1 | 2.5.0
buildNumber: release coordinator가 부여하는 전역 단조 증가 build 번호
artifactVersion: 실제 Electron packaging 도구와 OS metadata에 들어가는 버전 문자열
```

Electron packaging/updater/native OS metadata가 prerelease suffix를 어디까지 허용하는지는 별도 검증이 필요하다.
그래서 UI/DB의 `displayVersion`과 실제 packaging의 `artifactVersion`을 분리할 수 있게 둔다.

SemVer 기준:

```text
MAJOR.MINOR.PATCH
2    .5    .1
```

- `MAJOR`: 프로젝트/템플릿/플러그인 호환성 파괴, 큰 로컬 데이터 migration, 런타임 호환 정책 변경.
- `MINOR`: 기존 호환성을 유지하는 사용자 기능 추가, 새 플러그인, 새 workflow, 관리자 기능 추가.
- `PATCH`: 버그 수정, 설치/서명/공증 수정, 보안 patch, OS-only hotfix, 기능 의미 변화가 없는 수정.

예시:

```text
현재 stable: 2.4.1
새 기능 개발: 2.5.0-alpha.1, 2.5.0-alpha.2
출시 후보: 2.5.0-rc.1, 2.5.0-rc.2
정식 배포: 2.5.0
정식 배포 후 Windows-only bug fix: 2.5.1-rc.1 -> 2.5.1
```

## Rollback / Pull 정책

롤백은 두 종류로 나눠서 생각한다.

```text
1. 신규 다운로드/업데이트 target을 되돌리는 운영 롤백
2. 이미 설치된 앱을 낮은 버전으로 내리는 다운그레이드
```

Clipper의 기본 정책은 1번만 일반 운영 기능으로 둔다. 2번은 기본 정책으로 삼지 않는다.

예를 들어 `2.4.3`에 문제가 있고 아직 수정 버전이 없다면:

```text
2.4.3 문제 발견
  -> 2.4.3을 stable target에서 제거
  -> 2.4.3 상태를 pulled로 표시
  -> 신규 다운로드 target은 마지막 정상 artifact, 예: 2.4.1, 로 임시 변경
  -> 이미 2.4.3을 설치한 사용자는 자동 다운그레이드하지 않음
  -> 2.4.4 긴급 수정 release를 준비
```

`2.4.4`가 준비되면:

```text
2.4.4 필수 artifact build/sign/notarize/verify 완료
  -> 다운로드 페이지 target을 2.4.4로 변경
  -> auto update target을 2.4.4로 변경
  -> 2.4.1 사용자도 2.4.4로 업데이트 가능
  -> 2.4.3 사용자도 2.4.4로 업데이트 가능
```

즉 `2.4.1`로 되돌리는 것은 `2.4.4`가 아직 없을 때 문제 있는 `2.4.3` 신규 유입을 막는 임시 조치다.
`2.4.4`가 준비된 뒤에는 다운로드 페이지와 auto update target 모두 `2.4.4`가 되는 것이 맞다.

이미 설치된 앱을 `2.4.3 -> 2.4.1`처럼 낮추는 방식은 일반 정책으로 두지 않는다. 이유는 `2.4.3` 실행 중
로컬 데이터, 설정 파일, 캐시, 프로젝트 파일, sidecar schema가 변경됐을 수 있기 때문이다. 낮은 버전의 앱이
그 데이터를 읽지 못하면 더 큰 장애가 된다. 복구는 보통 "낮은 버전으로 후퇴"가 아니라 `2.4.4` 같은 더 높은
patch 버전으로 전진해서 한다.

S3에 과거 설치파일이 남아 있더라도, 사용자에게 보이는 것은 파일 존재 여부가 아니라 release target pointer다.
S3 artifact는 보존하고, 다운로드/auto update는 DB의 current target이 어떤 artifact를 가리키는지로 결정한다.
과거 source snapshot으로 재빌드할 수도 있지만, 롤백에는 기존 검증 artifact를 다시 가리키는 것이 더 정확하다.
재빌드는 artifact가 손상됐거나 서명/공증/metadata 재생성이 필요한 경우의 fallback으로 본다.

## 플랫폼별 Auto Update Target

공통 제품 버전 정책을 쓰더라도, 자동 업데이트 target은 platform/arch artifact 단위로 제어할 수 있어야 한다.

예를 들어 stable이 `2.4.1`이고 Windows-only installer bug를 고쳐 `2.4.2`를 배포한다고 하자.

```text
Release 2.4.2
  Windows x64 artifact: 내용 변경 있음, auto_update_enabled = true
  macOS arm64 artifact: 버전만 맞춘 no-op artifact, auto_update_enabled = false 가능
```

이 경우 다운로드 페이지는 신규 macOS 사용자에게 `2.4.2` artifact를 줄 수 있지만, 이미 `2.4.1`을 쓰는
macOS 사용자에게는 굳이 업데이트 알림을 띄우지 않을 수 있다. 단, 이 예외는 macOS 쪽에 실제 코드/데이터/보안/
호환성 변화가 없을 때만 허용한다. 공통 runtime, 프로젝트 schema, 웹 API 호환성, 보안 수정이 얽힌 release라면
macOS도 update target을 올리는 것이 맞다.

필요한 데이터:

```text
release_download_targets
  channel
  platform
  arch
  current_artifact_id

release_update_targets
  channel
  platform
  arch
  current_artifact_id
  auto_update_enabled
  minimum_supported_version
  force_update_below_version
```

다운로드 target과 auto update target은 기본적으로 같게 두되, no-op artifact나 staged rollout 같은 예외를 위해
분리할 수 있게 설계한다.

## Release Coordinator 배치

release coordinator의 본체는 `clipper_web_api`에 둔다. `clipper_infra`는 runner, 네트워크, S3, secret,
compose 같은 운영 배치와 runbook을 담당하고, release 상태의 정본을 갖지 않는다.

역할 분담:

```text
web/clipper_web_api
  release coordinator 본체
  release DB 정본
  build job 생성/상태 관리
  runner polling API
  publish/pull/rollback 정책
  download/update target API

web/clipper_web_admin
  운영자 UI
  release 생성
  build 생성
  artifact 상태/로그 확인
  promote stable
  pull/rollback 실행

web/clipper_infra
  runner 설치/운영 문서
  S3 prefix/key naming
  signing/notarization secret 관리 방식
  deploy/runbook/compose

desktop/clipper_electron
  실제 app packaging script
  release metadata 주입
  electron-builder 설정

desktop/clipper_angular
desktop/clipper_nestjs
desktop/clipper_python
  source snapshot에 포함되는 build source
```

`clipper_infra`에 Docker service로 coordinator를 별도 구현하는 방식은 지금 단계의 기본안으로 두지 않는다.
release는 DB, admin API, operator audit, artifact target 갱신이 필요하므로 `clipper_web_api`의 `release`
module이 정본을 갖는 쪽이 단순하다. 나중에 build queue나 runner orchestration이 커지면 runner 전용 worker
service를 분리할 수 있지만, release record의 SoT는 계속 `clipper_web_api`에 둔다.

## 코드 배포와 앱 릴리즈 분리

웹 서비스의 `prod` 배포와 desktop app stable release는 다르다.

```text
web repo prod deploy
  -> prod web_client/admin/api container가 바뀜
  -> 실제 웹 사용자가 보는 서버/페이지가 바뀜

desktop app release
  -> installer artifact가 build/sign/notarize/upload됨
  -> release coordinator가 download/update target을 갱신함
  -> 그때 사용자가 새 설치파일 또는 auto update를 받음
```

따라서 운영 브랜치에 코드가 들어갔다고 해서 desktop installer를 자동으로 stable publish하면 안 된다.
운영 브랜치는 "릴리즈 가능한 소스 후보"일 뿐이고, 실제 사용자 배포는 build, 서명, 공증, checksum,
install smoke, QA, 수동 승인 후에만 한다.

권장 절차:

```text
1. dev에서 기능 개발
2. stage에서 통합 QA
3. 필요한 경우 desktop 4개 repo에 release/<version> 브랜치 생성
4. release coordinator에서 release version 생성
5. Build RC 실행
6. build_number 발급 및 source snapshot 고정
7. macOS/Windows runner가 같은 build set 아래 artifact 생성
8. 성공 artifact는 S3에 upload하고 DB에 기록
9. QA 실패 build도 DB에 남기고, 사용자의 download/update target에는 연결하지 않음
10. 최종 통과 build만 stable로 promote
```

빌드가 성공해 설치파일이 생성되면 S3에 upload할 수 있다. 그러나 S3에 파일이 있다는 뜻이 사용자에게
배포됐다는 뜻은 아니다. 사용자 배포 여부는 `release_download_targets`와 `release_update_targets`가 어떤
artifact를 가리키는지로 결정한다. 실패/QA 탈락 artifact는 retention policy로 일정 기간 뒤 정리하되,
build log/checksum/metadata는 더 오래 보관한다.

예:

```text
2.5.0 build 30
  compile 실패
  artifact 없음
  DB에 실패 로그만 남김

2.5.0 build 31
  macOS artifact upload 성공
  Windows signing 실패
  stable publish 불가

2.5.0 build 32
  macOS/Windows artifact upload 성공
  QA 실패
  S3에는 남지만 target에는 연결하지 않음

2.5.0 build 33
  macOS/Windows artifact upload 성공
  QA 통과
  stable로 promote
```

## Desktop 브랜치와 Release 브랜치

팀 환경 브랜치는 다음처럼 유지한다.

```text
dev    개발 환경
stage  스테이징 환경
prod   운영 환경 또는 운영 후보 기준
```

다만 desktop repo에서는 필요할 때 `release/<version>` 브랜치를 추가로 만들 수 있다. 이 브랜치는 네 번째
환경이 아니라 특정 버전을 안정화하기 위한 임시 작업대다.

```text
release/2.5.0
  2.5.0 출시 후보 고정
  rc build 생성
  QA 중 발견된 버그만 cherry-pick
  새 기능 추가 금지
```

release branch가 필요한 이유는 QA 중에도 `dev`나 `stage`에 다음 기능 작업이 들어갈 수 있기 때문이다.
`stage`가 다음 출시 후보 역할을 계속 맡으면, 2.5.0 QA 도중 2.6.0 기능이 섞여 다시 빌드되는 문제가 생길 수 있다.

권장 사용:

```text
작은 팀 / 단일 출시만 준비:
  dev -> stage -> prod + tag만으로 시작 가능

desktop 출시 안정화가 며칠 이상 걸리거나 다음 기능 개발이 병행됨:
  desktop 4개 repo에 release/<version> 생성
```

stable 배포의 최종 정본은 `prod` 브랜치 자체가 아니다. 최종 정본은 release coordinator DB의
source snapshot, build number, S3 artifact, download/update target이다. `prod` 브랜치는 현재 운영 기준을
따라가는 편의 포인터로만 본다.

## Git Tag와 Source Snapshot

Git tag는 특정 commit에 붙이는 고정 이름표다. stable release에는 annotated tag를 사용한다.

```sh
git tag -a v2.5.0 -m "Release 2.5.0"
git push origin v2.5.0
```

branch는 계속 움직이는 포인터이고, tag는 특정 release commit을 찾기 위한 고정 표식이다.

```text
prod branch
  오늘은 2.5.0 commit을 가리키고,
  다음 주에는 2.5.1 commit을 가리킬 수 있음

v2.5.0 tag
  2.5.0 stable release에 사용된 commit을 계속 가리킴
```

source snapshot은 tag를 대체하지 않는다. 둘 다 필요하다.

```text
tag
  Git repo 안에서 특정 commit에 붙이는 이름표

source snapshot
  release DB에 남기는 "이 release/build가 어떤 repo들의 어떤 commit/tag 조합으로 만들어졌는지" 기록
```

Clipper desktop은 multi-repo 제품이므로 source snapshot이 특히 중요하다.

```text
release_version: 2.5.0
release_build: 33

source_snapshot:
  clipper_angular:  commit/tag v2.5.0
  clipper_electron: commit/tag v2.5.0
  clipper_nestjs:   commit/tag v2.5.0
  clipper_python:   commit/tag v2.5.0
  clipper_web_api:  compatible commit or API contract version
```

같은 commit에 여러 tag가 붙을 수 있다. 예를 들어 `2.5.1`에서 Angular만 바뀌고 NestJS/Python/Electron은
그대로라면, 변경 없는 repo의 같은 commit에 `v2.5.0`과 `v2.5.1` tag가 둘 다 붙을 수 있다. 이는 정상이다.
"이 repo 코드가 두 번 바뀌었다"는 뜻이 아니라 "같은 repo commit이 두 제품 release에 포함됐다"는 뜻이다.

Clipper는 stable release마다 desktop 4개 repo 모두에 같은 tag명을 찍는 방식을 기본으로 둔다. 그래야
`v2.5.1` checkout 자동화와 사람이 보는 운영이 단순하다. 변경된 repo에만 tag를 찍고 나머지는 DB snapshot만
믿는 방식도 가능하지만, multi-repo checkout과 장애 분석이 더 번거로워진다.

## 남은 설계 항목

- build runner가 pull 방식으로 job을 가져갈지, web_api가 push 방식으로 전달할지
- runner 인증 방식
- build job 로그 streaming 방식
- artifact storage 위치와 key naming
- release 목표 source snapshot과 build 실제 source snapshot을 어느 시점에 lock할지
- git tag를 stable promote 직전/직후 어느 시점에 생성할지
- build 실패 후 retry 정책
- artifact retention policy
- macOS code signing/notarization credential 관리
- Windows code signing credential 관리
- `beta` 채널을 실제로 운영할지, 아니면 `alpha/rc/stable`만 먼저 구현할지
- auto update suppression을 어떤 UI/권한으로 허용할지
- pulled release를 사용자가 관리자 화면에서 어떻게 다시 확인/감사할지
- stable publish 전 수동 승인 단계를 둘지
