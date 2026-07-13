# Release/Version Status

작성일: 2026-07-10

이 문서는 dev release/version 운영 상태와 이번 세션의 결정 사항을 정리한다.

## 현재 기준

dev 환경에서는 앱 identity 변경 이후 release DB를 reset하고 `0.0.1`부터 다시 시작했다.

이 결정은 아직 외부 출시 전, 내부 dev 검증 단계였기 때문에 허용했다. 실제 사용자에게 배포된 prod 환경에서는 같은 방식으로 release DB를 reset하지 않는다.

## App Identity

현재 앱 identity 기준:

- 제품명: `Clipper Studio`
- appId: 공식 도메인 기반 desktop namespace
- runtime data path: `Clipper Studio` 기준
- About 메뉴와 Settings 앱 정보는 package/build metadata를 표시한다.

주의:

- appId를 바꾸면 OS와 installer/update system이 기존 dev 앱과 다른 앱으로 볼 수 있다.
- 기존 dev 설치본 auto-update 경로와 충돌할 수 있으므로, 이번 reset은 dev 전용 결정이다.

## Release DB Reset

dev release DB는 `0.0.1`부터 다시 시작하기 위해 reset했다.

수행한 개념적 순서:

```text
1. m2-db release DB public schema reset
2. web_api release migration 재적용
3. m2-stage web_api 배포
4. web_admin release 생성
5. source snapshot 고정
6. Windows remote build
7. artifact upload
8. artifact stable target publish
```

실제 DB credential/env 값은 문서화하지 않는다.

## Release Console UI

web_admin release console에서 정리한 내용:

- releases list에서 release notes를 별도 column으로 분리
- row click 시 release detail modal 표시
- release detail modal에 release notes/source snapshot/runtime API 정보를 함께 표시
- release detail modal spacing, section divider, transparent scroll track 정리
- artifacts table에서 저장 위치를 storage provider/bucket 관점으로 표시
- 정식 배포 action은 native confirm이 아니라 admin modal로 확인
- 이미 stable target인 artifact는 "정식 배포 버전"으로 표시

## Public Download

web_client landing download 정책:

- Windows 다운로드 버튼은 public manifest를 조회한다.
- stable Windows artifact가 있으면 다운로드를 시작한다.
- artifact가 없거나 조회 실패 시 준비중 모달을 표시한다.
- Mac 다운로드 버튼은 현재 준비중 모달만 표시한다.
- OS auto-detect 단일 다운로드 버튼은 제거했다.

web_api public endpoint:

```text
GET /downloads/latest
```

응답 개념:

```json
{
  "version": "0.0.1",
  "releasedAt": "...",
  "artifacts": [
    {
      "os": "windows",
      "arch": "x64",
      "url": "...",
      "size": 0,
      "sha256": "..."
    }
  ]
}
```

이 endpoint는 release stable target에 연결된 artifact를 공개 다운로드용 manifest로 변환한다.

## Electron Auto-update

Electron auto-update feed는 별도 endpoint를 사용한다.

```text
GET /releases/updates/stable/windows/x64/latest.yml
```

이번 세션에서 확인한 점:

- update feed는 stable Windows artifact를 정상 반환했다.
- public landing download endpoint는 처음에 없어서 `/downloads/latest`가 404였다.
- 따라서 landing download failure의 root cause는 release target 데이터가 아니라 public manifest endpoint 누락이었다.

## 다음 확인 사항

1. m2-stage web_api 배포 후 `/downloads/latest`가 stable Windows artifact를 반환하는지 확인한다.
2. web_client 배포 후 `https://dev.clipperstudio.ai` Windows 버튼이 바로 installer URL로 이동하는지 확인한다.
3. web_admin artifact stable target과 public download manifest가 같은 artifact를 가리키는지 확인한다.
4. macOS artifact 정책이 정해질 때까지 Mac 버튼은 준비중 상태로 둔다.
