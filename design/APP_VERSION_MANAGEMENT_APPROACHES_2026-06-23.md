# 앱 버전 관리 방식 비교: versions vs versions2

작성일: 2026-06-23

이 문서는 관리자 앱 버전 관리 화면의 두 가지 설계안을 비교한다.

- `/versions`: 공통 앱 릴리즈 + OS별 설치 파일 방식
- `/versions2`: macOS/Windows 독립 버전 스트림 방식

현재 두 화면은 API 없이 프론트엔드 mock data로만 동작한다. 이후 실제 구현 시 데이터는 `release` database에 저장하는 전제를 둔다.

2026-06-23 추가 검토 기준: 아직 최종 확정은 보류한다. 현재 Clipper는 공통 제품 버전에 가까워 `/versions`가 기본 후보지만, macOS/Windows의 배포 준비도와 OS별 구현/버그 차이를 보면 `/versions2`가 더 자연스럽게 느껴지는 지점도 있다. 따라서 다음 설계 단계에서는 “공통 제품 버전”과 “OS별 artifact 배포 현실”을 분리해서 판단한다.

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
- 실제 배포 가능 여부는 artifact로 판단해야 한다.
- source snapshot의 1차 진실은 release가 아니라 artifact에 둔다.
- 다운로드 target은 release가 아니라 artifact를 직접 가리켜야 한다.

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
  - version, build_number, source_branch, git_tag, release_notes, status
- `release_artifacts`
  - release_version_id, platform, arch, file_name, s3_key, sha256, signature_status, build_runner, status
- `artifact_source_revisions`
  - release_artifact_id, repo, role, commit_sha, branch, summary
- `release_download_targets`
  - channel, platform, arch, current_artifact_id, rollback_artifact_id

`release_version`은 공통 릴리즈 단위이고, `release_artifact`가 macOS/Windows 설치 파일 단위다. source snapshot은 artifact 단위에 둔다. 같은 `2.4.1` release 아래에서도 macOS artifact와 Windows artifact가 서로 다른 commit 묶음으로 만들어질 수 있기 때문이다.

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

## 현재 프로젝트에 대한 판단

현재 Clipper 구조만 보면 `/versions` 방식이 기본 모델 후보에 더 가깝다.

이유는 다음과 같다.

- desktop 4개 repo가 공통 코드베이스를 이룬다.
- 다운로드 화면은 OS 감지 후 현재 지정된 OS별 설치 파일을 내려주면 된다.
- Electron 자동 업데이트도 “현재 다운로드 대상 artifact”를 기준으로 판단하면 된다.
- 운영자가 당장 필요한 작업은 설치 파일 업로드, 검증 상태 확인, 현재 다운로드 지정, 롤백이다.
- 고객에게는 공통 앱 버전 체계가 더 이해하기 쉽다.

하지만 현재 macOS와 Windows의 배포 준비도는 이미 다르다. Windows는 코드서명 준비가 되어 있고, macOS는 아직 공증/서명 플로우가 준비되지 않아 사용자가 `xattr` 명령어를 직접 실행해야 하는 상황이다. 이 차이는 `/versions2`가 더 자연스럽게 느껴지는 타당한 이유다.

따라서 다음 상황이 반복되거나 장기화되면 `/versions2` 방식으로 전환하거나, `/versions` 안에 OS별 artifact state를 더 강하게 노출해야 한다.

- Mac과 Windows의 버전 번호가 장기간 따로 움직인다.
- 한 기능이 OS별로 다른 버전에 들어가는 일이 자주 생긴다.
- OS별 QA 결과가 릴리즈 의사결정의 핵심이 된다.
- 고객 지원 문서가 OS별 버전을 따로 안내하기 시작한다.
- macOS만 `xattr` 안내/공증 미완료/제한 배포 상태가 계속 유지된다.

---

## 권장안

처음 실제 DB/API를 만들 때는 `/versions` 모델을 기준 후보로 두되, 최종 확정은 보류한다.

구체적으로는 다음 방향이 좋다.

1. 공통 `release_versions`를 둔다.
2. OS별 설치 파일은 `release_artifacts`로 분리한다.
3. 현재 다운로드 대상은 `release_download_targets`가 artifact를 가리키게 한다.
4. source snapshot은 `artifact_source_revisions`에 artifact 단위로 저장한다.
5. 강제 업데이트 기준은 당장 넣지 않는다.
6. Electron 자동 업데이트는 current artifact 또는 rollback artifact pointer를 기준으로 동작하게 한다.

이렇게 시작하면 UI는 `/versions`처럼 단순하게 유지하면서도 DB의 진실은 artifact 중심으로 남길 수 있다. 나중에 OS별 독립성이 커졌을 때 `/versions2` 모델로 확장하기도 쉽다.

확장 신호는 다음 중 하나다.

- 같은 공통 버전 안에서 OS별 기능 차이를 설명하는 일이 많아진다.
- artifact별 source snapshot이 release 공통 snapshot과 자주 달라진다.
- “Mac 최신 버전”과 “Windows 최신 버전”을 서로 다른 버전 체계로 공개해야 한다.

그 전까지는 `/versions2`를 비교안/검토용 화면으로 두고, 실제 구현은 artifact 중심 `/versions` 구조를 우선 검토하는 것이 유지보수 비용이 낮다. 단, macOS 공증/서명 준비가 늦어져 OS별 배포 흐름이 계속 벌어지면 `/versions2`를 메인 모델로 승격하는 판단을 다시 한다.
