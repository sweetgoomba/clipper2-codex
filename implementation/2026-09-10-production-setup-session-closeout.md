# 운영 구축 잔여 작업 — 세션 정리 및 인계

**후속 현재 상태:** [9/10 전체 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md)를 우선한다. 웹 후속 배포 및 Windows 설치 충돌·동시 로그인 확인이 이 문서 이후 진행됐다. 현재 설치0.0.3.7의 CPU 표시 확인과 Build/artifact 출처 대조를 구분한다. Build5 전체 QA·실제 플러그인 실행 HOLD는 유지하며, 현재 대시보드 코드·모의 리소스 검토는 [별도 검토](./2026-09-10-plugin-resource-management-review.md)를 따른다.

기준: 2026-09-10, 사용자 요청으로 플러그인 작업 검증을 보류하고 세션 정리.

후속 PG 세션 기록과 대조: 웹 배포는 이후 API ab86b3d / Admin 8980eab / Customer b5dc797로 통합·배포됐다고 사용자 실행 증거가 기록돼 있다. 네이버 관리자 migration 및 용도 저장도 후속 수행됐다. API 원격 ab86b3d가 이 세션의 8e1ce22·06316a4와 PG 923c9cb를 모두 보존하는 것은 별도 Git 조회로 확인했다. 제공자 키 소실 조사는 사용자의 “운영에 아직 등록하지 않았던 것으로 판단” 정정으로 종료됐다는 후속 기록을 따른다. 아래 미통합/키 미확정 설명은 당시 이력이며 최신 웹 상태와 남은 UI 검증은 [PG 인수인계](2026-09-10-pg-session-closeout.md) 상단을 우선한다. Windows Build 5 QA/플러그인 보류 상태는 유지한다.

이 문서는 9/9~9/10 대화와 사용자가 전달한 서버 실행 결과를 종합한 최신 상태다. 과거 진행 로그의 “미배포/미검증”은 당시 상태이며, 현재 상태는 아래를 우선한다. 서버를 문서 작성 시점에 다시 조회한 것은 아니다. 비밀 값은 기록하지 않는다.

## 1. 목표와 최종 도달 지점

목표는 TASKS 5의 **운영 구축 잔여 작업 진행**이었다. 특히 개발 환경과 분리된 Windows 운영 앱/runner를 구성하고, 관리자 빌드 요청부터 서명·S3 업로드·결과 보고·설치·로그인까지 연결했다.

**도달 지점: 운영 Admin의 Build 5가 서명된 Windows 설치파일을 S3에 업로드했고, 다운로드한 파일의 서명 및 설치 후 로그인 유지가 확인됐다.** 새 로그인 연결도 사용자 응답을 성공으로 해석해 진행했으나, 엄밀한 확인이 필요하면 다음 QA에서 명시적으로 재확인한다.

**운영 구축 전체 완료 또는 정식 출시 완료는 아니다.** Build 5는 QA 대기다. 플러그인 실행 검증은 사용자가 보류했다. QA 승인, 정식 공개, Customer 공개 다운로드, 실제 자동 업데이트는 수행하지 않았다.

## 2. 완료·부분 완료·보류 현황

| 범위 | 이번 세션 결과 | 남은 부분 |
|---|---|---|
| 운영 desktop 식별/분리 | appId, 이름, 프로토콜, 데이터·모델 캐시·플러그인 포트 분리 구현 및 패키지 검사 | 개발판과 실제 동시 실행, OS 자격증명 저장소 등 전체 분리 QA |
| Windows 운영 runner | 별도 작업 경로·컨테이너·포트·env, 빌드·서명·호스트 보관·S3 업로드 | 재생성 시 Git 신뢰 경로 자동 등록, 장기 디스크 정리·재부팅 복구 |
| 관리자 연계 | 소스 스냅샷 고정, 요청 인증, 결과 보고, 실패/성공 표시 확인 | QA 승인·정식 배포 절차 |
| 설치/인증 | Build 5 다운로드, Valid 서명, 설치 후 로그인 유지 | 플러그인 기능, 신규 설치/공존/자동 업데이트 QA |
| 네이버/크레딧 | 검색·데이터랩 사용량 분리, 작업 차감·실패 반환 및 표시 개선 | 운영 최신 API 반영 여부와 실제 플러그인 재검증 |
| 월 지급 영문 문구 | 운영 PG 브랜치에 통합·배포, health 및 사용자 과거 내역 한국어 표시 확인 | 완료 |
| 운영 키 관리 | 운영 DB provider_credentials가 빈 상태인 것 확인 | 원인 미확정, 사용자 재등록 완료/테스트 여부 미확인 |
| 나머지 운영 기반 | 조사와 정리 | 모니터링·알림, 백업/복원, 정전/재부팅, 보안 운영, Google/Toss live 전환 |

개발 서버/DB 전환은 보류했다. Mac 공개 다운로드는 “준비 중” 유지이며 Mac 공개·자동빌드·업데이트는 이번 완료 범위가 아니다. PG 테스트/실거래 검증은 별도 작업의 정본을 따른다.

## 3. 구축된 환경

### Windows

- 호스트: Metabuzz00, IP `192.168.0.14`, Docker context `desktop-windows`.
- 기존 개발 runner: `clipper-windows-release-runner`, 호스트 포트 `19029`. 운영용과 분리 유지.
- 운영 workspace: `C:\clipper-prod`.
- 운영 runner: `clipper-windows-release-runner-prod`, 호스트 `19030` → 컨테이너 `19029`, Hyper-V, 메모리 8GB.
- 최종 확인 컨테이너: `961773bf7c6a`.
- 최종 이미지: `11c0d8fc13f361cb01392bd9727db34e0b3438aab967ab68f6ce19d491cb5c30`。
- 운영 runner env: `C:\clipper-prod\web\clipper_infra\runner\env\release-runner.prod.env`.
- 내부 작업: `C:\runner-work`; 최종 보관: `C:\runner-output\artifacts` → 호스트 `C:\clipper-prod\runner-output\artifacts`.
- 최종 설정 확인: `skipUpload=false`, S3 bucket `clipperstudio`, prefix `prod/windows`, AWS 인증 정보 존재.
- CodeSignTool 및 GitHub/AWS/서명 자격증명 파일은 별도 경로에서 주입. 비밀 값은 문서에 저장하지 않음.

### 운영 API Mac

- 호스트: m4-prod Mac mini, IP `192.168.0.47`.
- Infra: `/Users/m4-prod/Documents/projects/clipperstudio/clipper_infra`.
- Compose: 프로젝트 `clipper-prod`, 서비스 `api`, 컨테이너 `clipper-web-api-prod`.
- 운영 설정 파일: `env/stack.prod.env`.
- 로그인 반환 주소: `clipperstudio://auth/callback`.
- runner 시작 URL: `http://192.168.0.14:19030/jobs/start`.
- snapshot URL: `http://192.168.0.14:19030/source-snapshots/capture`.
- 시작 요청용 토큰과 결과 보고용 토큰을 구분해 연결. snapshot HTTP 200, 보고 토큰 해시 일치, 실제 빌드 보고 수신 확인.
- 설정 변경 때 기존 API 이미지를 유지하고 API 서비스만 재생성, Healthy 확인. 당시 이미지 ID는 `87aa6b2014d651147333585abe017792fa8428191e9849637e5c8acbda26ef1d`. 이후 다른 작업의 배포 여부까지 보장하는 현재값은 아님.

### 운영 앱

- appId: `ai.clipperstudio.app`; 앱 이름·데이터 폴더: `Clipper`.
- 로그인 프로토콜: `clipperstudio`.
- API: `https://api.clipperstudio.ai`; runtime identity: `production`.
- 설치 경로: `C:\Users\Metabuzz00\AppData\Local\Programs\Clipper\Clipper.exe`.
- 운영 데이터: `%APPDATA%\Clipper`; 모델/관련 캐시는 운영 userData 아래 분리.
- 운영 플러그인 포트 범위: `55000–55199`. 당시 사용/제외 범위 충돌 없음 확인.
- 운영 JWT 공개키와 API 공개키의 해시 일치 확인. 개인키는 앱에 복사하지 않음.

## 4. 소스 및 주요 변경

Windows의 다섯 저장소는 `integration/toss-payments-pg-20260909`로 정렬했다. Python도 dev와 같은 커밋에서 해당 브랜치를 만들어 관리자 소스 브랜치를 일관되게 사용했다. Infra는 `integration/toss-payments-pg-20260903`이다.

| 저장소 | 검증 빌드의 고정 커밋 |
|---|---|
| clipper_angular | `7ae7366d51a997ee009f73a825467db061daca2b` |
| clipper_nestjs | `780128a069c38a9df6438cc64d79f7a2e42bc1ea` |
| clipper_python | `260751d2fa5be8a5a9cd8e346c60ba22d1512ed9` |
| clipper_electron | `dd4e9d67d85f3da18b6a3a107c06987c67da46d0` |
| clipper_web_api | `3b6d68d7e2179a2508c1a3bcca09d02dc094ae2b` |

API 소스가 스냅샷에 포함된 것과 그 API 이미지가 운영 서버에 배포된 것은 별개다.

주요 커밋:

- Electron `aecc30e`: 일시적 빌드 출력 삭제 실패 재시도.
- Electron `4c60f1e`: 운영 식별자·로그인 프로토콜 분리.
- Electron `dd4e9d6`: 운영 모델 캐시·플러그인 포트 분리.
- Infra `262c4ff`: 운영 runner 옵션/경로 보호.
- Infra `c784afe`: 설치파일 빌드·서명을 컨테이너 내부에서 수행하고 완성본을 호스트로 보관.
- Infra `f948922`: 소스와 node_modules도 작업별 컨테이너 내부 경로로 격리.

## 5. Windows 빌드 오류: 원인과 해결

### 5.1 NSIS 설치파일 생성이 파일 잠금에서 멈춤

증상: 공유 출력 경로에서 `output file is locked for writing ... waiting for unlock` 발생. 설치 EXE가 약 294KB의 중간 상태로 남았다.

관찰: 호스트의 `vmwp.exe`가 해당 EXE 핸들을 보유했고 빌드 Node만 종료해도 잠금이 유지됐다. 특정 백신이 원인이라는 증거는 없었다. Hyper-V 내부의 정확한 잠금 발생 원인은 확정하지 못했다.

우회 검증: 컨테이너 내부 `C:\installer-local-check`로 출력 위치를 바꾸자 NSIS 설치파일과 blockmap 생성이 완료됐다.

구조 개선: `c784afe`에서 작업별 내부 폴더에서 빌드·서명을 완료한 뒤 최종 EXE만 호스트 보관 폴더에 복사한다. 원본/복사본 크기·SHA256·SHA512를 대조하고 불일치/복사 실패 시 업로드 및 성공 보고를 막는다. 서명 전 latest.yml/blockmap을 서명본 배포에 재사용하지 않는다.

### 5.2 npm ci가 esbuild.exe 삭제 권한 오류로 실패

증상: Build 1에서 공유 소스의 `node_modules/@esbuild/win32-x64/esbuild.exe` unlink가 `EPERM`, errno -4048로 실패. 표시된 종료 코드 `4294963248`은 이 실패와 연결된 값이었다.

관찰: 컨테이너에 esbuild 프로세스가 없는데도 호스트 vmwp.exe가 해당 파일 핸들을 보유했다. 단순 관리자 권한 부족으로 단정할 수 없었다.

해결: `f948922`에서 각 작업의 내부 sources로 다섯 저장소를 `--no-hardlinks --no-checkout` 복제하고 스냅샷 SHA를 checkout한다. npm ci 및 빌드가 모두 내부에서 실행된다. 호스트 node_modules나 미커밋 파일을 복사하지 않는다.

별도 복사 허용 입력은 Nest/Python `.env.packaged`, JWT 공개키, Windows uv 실행파일 네 가지다. 입력 누락은 의존성 설치 전에 실패시킨다.

결과: Windows 테스트 7/7 통과. 같은 컨테이너에서 Build 3·4 연속 성공, Build 5 업로드 성공. 공유 파일 잠금은 이 검증에서 재발하지 않았다.

### 5.3 로컬 Git clone의 dubious ownership

원인: 호스트 저장소 소유자 SID와 ContainerAdministrator SID가 달라 Git이 거부했다. 컨테이너 재생성 시 글로벌 신뢰 경로 설정도 없어졌다.

초기 source root 등록은 일반 fetch에 도움이 됐지만 로컬 clone은 `.git` 경로를 추가로 검사했다. 슬래시로만 표기한 `.git` 경로 등록은 이 환경에서 해결하지 못했다.

해결: 다섯 저장소에 일반 root와 **오류에 출력된 정확한 혼합 경로**를 각각 등록했다. 예:

```text
C:/workspace/clipper/desktop/clipper_angular
C:\workspace\clipper\desktop\clipper_angular/.git
```

이후 ls-remote, 실제 clone/checkout, 입력 파일 준비가 성공했다. 와일드카드 전체 신뢰는 사용하지 않았다. **재생성 후 자동 등록은 아직 미구현이며 다음 작업에서 보완해야 한다.**

### 5.4 실행 중 Hyper-V 컨테이너 docker cp 실패

명시적 오류: `filesystem operations against a running Hyper-V container are not supported`.

해결: docker exec로 컨테이너 내부 Copy-Item을 실행해 bind mount로 내보냈다. 실제 복사본 해시/서명을 확인했다. 컨테이너 삭제로 내부 결과물을 잃기 전에 최종 파일 보관이 필요하다.

### 5.5 기타 구축 중 오류

| 증상 | 원인/관찰 | 대응 |
|---|---|---|
| Electron ENOTEMPTY 정리 실패 | 출력 디렉터리 삭제 중 일시적 실패 | 출력 정리 재시도 구현 후 로컬 빌드 성공 |
| Node 검사 코드 SyntaxError | PowerShell → native 명령 인자 전달 중 따옴표 소실 | here-string을 표준입력으로 전달하거나 EncodedCommand 사용 |
| ASAR에 main.js가 없다는 검사 오류 | 목록에는 실제 파일 존재; Windows 추출 경로 구분자 문제 | 경로 정규화 후 추출, 패키지 코드와 컴파일 결과 일치 확인 |
| 앱 응답 없음 | Esc로 터미널 선택 해제 후 브라우저 표시/앱 응답 회복 | 터미널 선택 상태 영향으로 추정, 앱 고유 교착으로 확정하지 않음 |
| 로그인 반환 후 401 | 코드 교환 거부; 지연 후 재시도 성공 | 코드 만료 가능성, 확정 원인 아님. 새 로그인으로 성공 |
| 운영 업데이트 latest.yml 404 | 당시 공개된 운영 업데이트 산출물 없음 | 공개 전 상태와 구분. 자동 업데이트 기능을 껐다는 뜻은 아님 |
| docker stop: No such container | 해당 시점 prod 컨테이너가 목록에 없음 | context/컨테이너/이미지 조회 후 운영 컨테이너만 생성; 소실 원인 단정 안 함 |
| AWS ListObjectsV2 AccessDenied | uploader 정책에 s3:ListBucket 없음 | 목록 권한을 추가하지 않고 PutObject 허용 범위 확인, Build 5 실제 업로드 성공 |
| SKIP_UPLOAD가 1과 0으로 중복 | env에 기존 줄 대신 새 줄 추가 | 실행값 false 확인, 파일은 0 한 줄로 정리 안내; 실제 중복 제거 재조회는 안 함 |
| Build 5인데 전달 링크 build-3 | 전달된 링크와 runner 로그 불일치 | 새 확인에서 Admin build-5와 로그 build-5 일치; UI 결함으로 확정하지 않음 |

## 6. 빌드와 배포 검증 증거

릴리즈 `0.0.1`, 스냅샷 `snapshot-20260909T210055Z`.

| 빌드 | 표시 버전 | 결과 |
|---|---|---|
| 1 | 0.0.1.1 | 차단: 공유 node_modules esbuild.exe EPERM |
| 2 | 0.0.1.2 | 차단: 로컬 clone 소유권 검사 |
| 3 | 0.0.1.3 | QA 대기 / Windows 로컬 검증 완료 |
| 4 | 0.0.1.4 | QA 대기 / Windows 로컬 검증 완료、3과 연속 검증 |
| 5 | 0.0.1.5 | QA 대기 / Windows 업로드됨、서명 완료 |

Build 5:

- S3: `prod/windows/0.0.1/build-5/clipperstudio Setup 0.0.1.exe`.
- runner 보고 job ID: `e1320707-205d-4557-9d4e-a28e7eb1ae43`.
- 다운로드 파일 SHA256: `7DDE536A1A5AE9172D43745DE50C3B6168BE47A3D8EB1DA145D8A9160D2D9C7D`.
- 관리자 표시 축약 해시와 일치. 전체 기대 해시를 별도 API로 받아 비교한 것은 아님.
- Authenticode `Valid`, 서명자 `Meta Buzz Co., Ltd.`.
- 설치 후 로그인 유지 확인. 실제 플러그인 작업은 보류.
- UI의 산출물 버전은 0.0.1.5지만 파일명/패키징 로그 버전은 0.0.1이다. 이를 자동 업데이트 버전 증가가 검증된 것으로 해석하면 안 된다. 공개 전 버전 정책/업데이트 시나리오 확인 필요.

S3 업로드는 정식 공개 승인과 다르다. 다만 S3 URL의 외부 접근 가능성은 버킷 정책에 달려 있으므로 “미승인이어서 파일이 비공개”라고 보장하지 않는다.

## 7. 네이버·크레딧 및 추가 발견

- 네이버 검색과 데이터랩 사용량/가능 API/기본·대기 키 표시를 분리했다. 사용자 조사 실행 후 검색과 데이터랩 계수가 각각 증가한 것을 확인했다.
- 안무 하이라이트 준비 실패 시 크레딧 차감/반환 내역 누락을 수정했다. 사용자 화면에서 -150/+150 내역 확인.
- operation 식별자가 그대로 보이는 내역을 한국어 작업명과 사용/반환 문구로 표시했다. 조회 실패도 후속 수정 후 사용자 정상 표시 확인. 관련 소스는 Angular/Nest/API 고정 커밋에 포함된다.
- 월 지급 `monthly access credit grant`는 조회 표시명 변환에서 빠져 있었다. API의 `credit-ledger-display.ts`에 “월 정기 크레딧 지급”, `one-time free trial`에 “최초 무료 체험 크레딧 지급”을 추가했다. 원장 원문/금액은 변경하지 않고 기존 내역에도 읽을 때 적용한다. 관련 테스트 18개 통과.
- 후속 승인으로 운영 반영 완료. 최초 로컬 수정은 통합 브랜치의 06316a4로 push했으나, 운영 서버는 별도 release/pg-expiry-20260910의 923c9cb를 사용 중이었고 기존 한국어 표시 처리도 없었다. 운영 PG 변경을 보존한 별도 worktree에서 크레딧 표시 관련 6개 파일만 통합해 8e1ce22afee89ca134131cd71c23cd27f6e0f580으로 같은 운영 브랜치에 push했다. 네이버 변경/마이그레이션은 제외했다. 관련 155개 테스트와 API 빌드 통과, OpenAPI 수정 후 계약 테스트 60개 재통과.
- 사용자가 m4-prod에서 api --build-only 후 --start-only로 배포했다. HTTP 200 및 user/release/admin DB 모두 ok 확인. 이어 기존 01:02·02:06 지급 내역이 “월 정기 크레딧 지급”으로 표시되고 환불/구독 변경 내역도 조회되는 것을 사용자 확인했다. DB 마이그레이션과 데스크톱 재빌드는 수행하지 않았다.
- 사용자 운영 관리자에서 Gemini·YouTube 등 키가 모두 0개로 보였다. 운영 API 연결 DB `clipper_admin_prod`에서 provider_credentials 제공자별 count 조회가 `[]`였다. **해당 테이블이 비었다는 사실만 확인**했으며 네이버의 별도 저장소를 포함해 모든 저장 데이터를 검사한 것은 아니다.
- 후속 사용자 정정: 운영 관리자에 아직 키를 등록하지 않았던 것으로 판단해 소실 조사 불필요하다고 명시했다. 이 건은 장애 원인 조사에서 제외한다. 실제 키 등록·테스트는 필요할 때 별도 진행한다.

## 8. 남은 작업과 다음 세션 순서

1. 사용자가 원할 때 provider 키 재등록/테스트 상태 확인 후 Windows Build 5 플러그인 실제 실행 QA를 재개한다. 성공·실패 시 크레딧 내역도 함께 확인한다.
2. 월 지급 한국어 표시 운영 반영은 후속 작업으로 완료했다. 향후 브랜치 통합 시 운영 브랜치 8e1ce22와 통합 브랜치 06316a4의 관계를 유지한다.
3. runner Git safe.directory 등록을 재생성 시 자동화하고 실제 재생성 회귀 검증을 한다. 내부 작업 폴더의 보관/정리 정책도 정한다.
4. Build 5 QA, 신규 설치/기존 설치 갱신/개발판 공존 검증, 설치파일 실제 버전 및 자동 업데이트 증가 규칙을 확인한다.
5. 승인 후에만 정식 배포와 Customer Windows 다운로드 연결, 실제 자동 업데이트를 검증한다. Mac은 준비 중 유지한다.
6. 모니터링·알림, 백업 및 복원 실습, 정전·재부팅 후 복구, DB 접근·로그·비밀 관리, Google/Toss 운영 전환 조건을 마무리한다.
7. 최종 branch/PR와 Infra 문서·작업 기록을 선택적으로 정리한다. 개발 서버/DB 전환과 실결제는 별도 승인 범위다.

이번 종료 요청에 따라 위 검증/배포는 추가 실행하지 않는다. Build 5 QA 대기와 플러그인 검증 보류 상태를 유지한다.

## 9. 참고 파일

- 시간순 상세 기록: `2026-09-09-production-setup-log.md` (같은 폴더).
- 전체 작업 범위: `TASKS.md`의 5번. 부분 검증을 전체 완료로 체크하지 않는다.
- runner 설계/사용 문서: `web/clipper_infra/runner/windows/production-artifact-storage.md`.
- 구현: `web/clipper_infra/runner/release-runner.mjs`, `runner/windows/run-windows-runner-container.ps1`.
- 월 지급 표시 수정: `web/clipper_web_api/src/modules/credits/domain/credit-ledger-display.ts` 및 `.spec.ts`.
