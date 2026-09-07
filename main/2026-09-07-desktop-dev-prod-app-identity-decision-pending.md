# 데스크톱 개발판·운영판 이름과 앱 분리 — 결정 대기 기록

작성일: 2026-09-07

상태: 이름·아이콘은 결정권자 답변 대기. 아래 운영 설정은 검토 후보이며 확정값이나 구현 완료 내역이 아니다.

## 1. 현재 멈추는 이유와 사용자 의도

사용자는 결정권자에게 다음 내용을 문의했다.

> 클리퍼 앱 아이콘 이미지랑 앱 이름(Clipper Studio) 현재 개발버전에서 사용 중인 것들 운영버전에서도 그대로 쓰면 될까요?

결정권자는 운영판 이름을 `Clipper`로 할지 기존 `Clipper Studio`로 할지 결정한 후 알려주기로 했다. 아이콘 재사용 여부도 아직 확정하지 않았다.

현재 개발판은 개발팀과 회사의 다른 팀들이 이미 사용하고 있고, 이 앱을 기준으로 QA가 진행 중이다. 같은 Windows PC와 Mac에 운영판도 함께 설치할 예정이다.

사용자의 우선순위는 다음과 같다.

- 기존 개발판의 설정과 동작을 최대한 유지한다.
- 기존 개발판의 프로젝트·설정·로그인 정보·로그·캐시·모델 등 데이터를 옮기거나 초기화하는 일을 피한다.
- 기존 개발판과 새 운영판이 서로의 설치·데이터·로그인 연결·업데이트에 영향을 주지 않도록 한다.
- 직원들에게 별도 이전 스크립트를 실행하게 하는 방안은 현재 진행안으로 채택하지 않는다.
- 이름 문제는 답변을 받을 때까지 보류하고, 원래 진행하던 운영 인프라 준비를 계속한다.

과거에 논의한 “기존 개발판의 이름과 경로를 운영판에 넘기고 개발 데이터를 새 경로로 이동”하는 방식은 현재 실행 계획이 아니다. 그 논의를 근거로 데이터 이전 스크립트나 개발판 변경을 임의로 구현하지 않는다.

## 2. 기존 개발판에서 확인한 값

| 항목 | 현재 값 |
| --- | --- |
| 제품명 `productName` | `Clipper Studio` |
| 앱 식별자 `appId` | `ai.clipperstudio.desktop` |
| 내부 패키지 이름 | `clipper-electron` |
| Electron 내부 이름 | 별도 변경이 없다면 `Clipper Studio` |
| Windows 실행파일 | `Clipper Studio.exe` |
| Mac 앱 파일 | `Clipper Studio.app` |
| Windows 기본 데이터 폴더 | `%APPDATA%\Clipper Studio` |
| macOS 기본 데이터 폴더 | `~/Library/Application Support/Clipper Studio` |
| 앱을 여는 주소 | `clipper://` |

아이콘 파일은 Electron 빌드 설정에서 macOS `icon-mac.png`, Windows `icon.ico`를 사용한다. 운영판에서 그대로 사용할지는 결정 대기다.

이름과 경로는 코드의 기본값 기준이다. 사용자가 설치 폴더를 직접 선택한 경우와 이전 버전의 잔여 파일까지 모든 직원 PC에서 조사한 것은 아니다.

## 3. 운영판의 두 가지 후보

다음 표는 두 이름 모두 실현할 수 있음을 보여주는 예시다. 최종 식별자·실행파일·저장 경로까지 확정한 것으로 읽지 않는다.

| 항목 | 후보 A: 운영판 이름 `Clipper` | 후보 B: 운영판 이름 `Clipper Studio` |
| --- | --- | --- |
| 제품명 `productName` | `Clipper` | `Clipper Studio` |
| 앱 식별자 후보 | `ai.clipperstudio.app` | `ai.clipperstudio.app` |
| 내부 패키지 이름 후보 | `clipper-app` | `clipper-app` |
| Electron 내부 이름 후보 | `Clipper` | `Clipper` — 제품명과 따로 설정 |
| Windows 실행파일 후보 | `Clipper.exe` | `Clipper.exe` — 제품명과 따로 설정 |
| Mac 앱 파일 후보 | `Clipper.app` | `Clipper.app` — 제품명과 따로 설정 |
| Windows 데이터 폴더 후보 | `%APPDATA%\Clipper` | `%APPDATA%\Clipper` |
| macOS 데이터 폴더 후보 | `~/Library/Application Support/Clipper` | `~/Library/Application Support/Clipper` |
| 운영 로그인 연결 주소 후보 | `clipperstudio://` | `clipperstudio://` |

- 후보 A는 직원들이 이름만 보고 두 앱을 구별하기 쉽다.
- 후보 B는 운영판에서도 기존 브랜드명을 그대로 사용할 수 있다. 대신 설치 파일명·바로가기·아이콘 등에서 구별 방법을 마련해야 한다. 같은 폴더에 같은 이름의 `.app`이나 바로가기를 만들면 안 된다.
- `.desktop`과 `.app`이라는 appId 접미사에는 기술적 우열이 없다. 현재 서비스 도메인 `clipperstudio.ai`를 바탕으로 고유하고 지속적인 식별자를 정하면 된다. 제품명을 `Clipper`로 정해도 appId에서 `studio`를 지울 필요는 없다.
- 표시 이름이 같아도 앱 식별자·실행파일·데이터·로그인 연결이 분리되면 별개의 앱으로 만들 수 있다. 현재 코드가 이미 그렇게 동작하는 것은 아니다.

## 4. 로그인 연결 주소에 대한 현재 권장안

기존 개발판의 `clipper://`는 유지하고 운영판만 `clipperstudio://`를 사용하도록 하는 안을 우선 검토한다. 이것도 최종 설정 승인을 대신하지 않는다.

- 개발 API의 로그인 완료 주소: `clipper://auth/callback`
- 운영 API의 로그인 완료 주소 후보: `clipperstudio://auth/callback`
- 이 주소는 인터넷 도메인이 아니라 OS에 등록하는 앱 열기 주소다. 새 DNS나 서브도메인은 필요하지 않다.
- 제품명 `Clipper`와 프로토콜 `clipperstudio`는 단어가 달라도 사용할 수 있다.

현재 개발판은 실행할 때 `clipper`를 기본 연결 앱으로 등록하고, Windows에서 받는 URL도 `clipper://`로 찾는다. 운영판은 설치 설정과 실행 중 등록·수신 코드 모두 자신의 프로토콜만 사용하도록 바꿔야 한다. Web API의 `DESKTOP_REDIRECT`도 같은 환경의 프로토콜과 일치해야 한다.

이전에 논의한 “개발판을 `clipper-dev://`로 바꾸고 운영판에 `clipper://`를 넘기는 안”은 기존 개발판과 개발 API를 함께 전환해야 한다. 업데이트하지 않은 구버전이 옛 주소를 다시 등록할 수 있으므로, 기존 개발판을 최대한 유지한다는 현재 우선순위에서는 채택하지 않은 대안으로 남긴다.

## 5. 제품명과 함께 확인해야 할 분리 항목

이름이나 아이콘만 달리해서는 개발·운영 분리가 끝나지 않는다. 최종 이름 결정 후 구현·검증할 항목은 다음과 같다.

- 앱 식별자와 Windows 설치·삭제 식별값, 기본 설치 위치, 실행파일, Mac 앱 파일, 바로가기.
- `userData`, 브라우저 세션 저장소, 로그, 캐시, 모델, Python 실행환경과 다운로드 파일의 저장 위치.
- Mac Keychain의 로그인 암호화 저장 이름. `productName`과 appId만 보고 분리됐다고 판단하지 않는다.
- API 주소, JWT 공개키, 로그인 연결 주소, 자동 업데이트 조회 주소와 업데이트 캐시.
- 빌드 환경별 S3 저장 위치, Release DB, runner의 작업·출력 폴더.
- 두 앱이 동시에 실행할 때 사용하는 로컬 서버·플러그인 포트와 프로세스 종료 범위.

현재 내부 패키지 이름으로 업데이트 캐시 이름이 만들어진다. 운영판의 내부 패키지 이름을 따로 정하면 이 캐시도 분리할 수 있다.

제품명을 둘 다 `Clipper Studio`로 사용할 때는 Electron 내부 이름을 운영판용으로 분리하는 방안을 검증한다. 현재 앱 정보 화면은 `app.getName()`을 사용하므로 내부 이름과 표시 이름을 분리하는 경우 이 화면도 표시 이름을 사용하게 맞춰야 한다.

### Hugging Face 모델과 외부 파일

Hugging Face 캐시에는 실제 다운로드한 모델 파일도 들어 있다. 현재 대사 하이라이트의 faster-whisper/OpenCLIP 모델은 기본적으로 사용자 홈의 `.cache/huggingface/hub`에 있고, 일부 다른 모델은 앱 데이터 폴더에 있다.

기존 개발판의 공용 캐시는 유지하고 운영판이 전용 모델 저장 위치를 사용하게 하는 안을 검토한다. 다른 프로그램도 사용할 수 있는 공용 Hugging Face 폴더 전체를 옮기거나 삭제하지 않는다. 모델 다운로드·존재 확인·폴더 열기 기능이 모두 같은 운영판 전용 경로를 따라야 한다.

외부 프로젝트 폴더 동시 사용은 대화에서 설명한 조건부 위험이다. 현재 모든 플러그인이 외부 프로젝트 폴더를 직접 열어 수정하는 기능을 갖췄다고 확인한 것은 아니다. 실제로 같은 외부 파일을 두 앱이 수정하는 경로가 있는지 먼저 확인하며, 별도 동시 실행 차단 기능을 이번 문서만으로 추가하지 않는다.

## 6. 운영 배포 후 제품명을 변경하는 경우

`productName`은 나중에 변경할 수 있지만, 기본 설정에서는 실행파일·Mac 앱 파일·데이터 폴더·일부 로그와 암호화 저장 이름까지 영향을 받을 수 있다.

- 데이터 폴더가 바뀌면 기존 파일은 남아 있어도 새 앱이 빈 폴더를 읽어 프로젝트가 사라진 것처럼 보일 수 있다.
- 실행파일·앱 파일 이름이 바뀌면 바로가기와 자동 업데이트가 예전 위치를 가리키거나 앱이 중복으로 남을 수 있다.
- Mac은 Electron 내부 앱 이름으로 Keychain 저장 이름을 구성한다. 데이터 폴더를 유지해도 기존 로그인 정보의 복호화가 보장되지는 않는다.
- appId, 내부 패키지 이름, 저장 경로, 내부 이름, 프로토콜처럼 계속 유지할 값을 표시 이름과 구분해서 설계한다.
- 표시 이름을 바꾼 버전은 기존 운영판에서 실제로 업데이트해 프로젝트·설정·로그인·바로가기·업데이트가 이어지는지 Windows와 Mac에서 확인한다.

“제품명 한 줄만 바꾸면 아무 영향이 없다”거나 “제품명은 배포 후 절대로 못 바꾼다”는 설명은 둘 다 맞지 않는다.

## 7. 결정이 오면 재개할 작업

1. 운영판의 최종 표시 이름과 아이콘 재사용 여부를 기록한다.
2. 그 결정에 맞춰 운영판의 고정 식별자·저장 경로·로그인 연결·바로가기 구분을 확정한다.
3. 기존 개발판을 변경하지 않는 범위를 우선으로 빌드·실행 설정을 구현한다.
4. 기존 개발판이 설치되고 데이터가 있는 Windows/Mac에 운영판을 추가 설치해 확인한다.
5. 두 앱의 재실행, 로그인, 업데이트, 한쪽 삭제가 다른 쪽의 연결과 데이터를 건드리지 않는지 검증한다.

이번 정리에서는 앱 설정·아이콘·사용자 데이터·서버를 변경하지 않는다. 결정권자에게 추가 메시지를 보내거나 답변을 자동 감시하지 않는다. 사용자가 결정 결과를 전달하면 이 기록에서 이어간다.

## 8. 지금 이어갈 운영 인프라 작업

- 장비별 조사 결과는 [운영 인프라 조사 로그](./2026-09-07-toss-payments-pg-production-infrastructure-discovery-log.md)에 있다.
- 웹/API·runner 환경 분리와 PG 콜백은 [서버 콜백·웹훅 설계](./2026-09-07-toss-payments-pg-server-callback-webhook-design.md)를 참고한다.
- `m2-db`는 DB, `m2-proxy`는 프록시, `m2-stage`는 현재 개발 웹/API, `m4-prod`는 새 운영 웹/API 담당이다. `storage`는 Windows 빌드 runner 장비다.
- 운영 웹/API는 `m4-prod`에서 직접 빌드하는 방식이며, 장기 운영 브랜치는 `main`이다. 통합 테스트 브랜치 이름을 운영 브랜치로 확정하지 않는다.
- 다음 준비 대상은 개발·운영 배포 명령의 사용법 통일, migration 명령 분리, 웹 빌드의 API 주소 분리, 실제 장비 구성에 맞춘 Compose와 운영 DB 설정 절차다.
- 이름 결정은 웹/API·DB·프록시 준비를 막지 않는다. 최종 운영 데스크톱 설치파일의 배포는 이름 결정과 환경 분리 검증 후에 진행한다.
- 서버 명령은 사용자가 직접 실행한다. 기존 개발 DB의 파괴적 변경은 지금 진행하지 않으며, 적용 직전에 `m2-db` 로컬 백업과 복원본 검증을 거치는 사용자 방침을 유지한다.

## 9. 코드와 공식 자료

- `/Users/jina/project/adlight/desktop/clipper_electron/electron-builder.yml`
- `/Users/jina/project/adlight/desktop/clipper_electron/package.json`
- `/Users/jina/project/adlight/desktop/clipper_electron/src/main/auth/deeplink.ts`
- `/Users/jina/project/adlight/desktop/clipper_electron/src/main/auth/token-store.ts`
- `/Users/jina/project/adlight/desktop/clipper_electron/src/main/app-info/app-info.ts`
- `/Users/jina/project/adlight/desktop/clipper_electron/src/main/plugin/plugin-install-state.ts`
- `/Users/jina/project/adlight/desktop/clipper_electron/src/main/model-download-ipc.ts`
- `/Users/jina/project/adlight/web/clipper_web_api/src/modules/auth/presentation/auth.controller.ts`
- [Electron 내부 이름 변경](https://www.electronjs.org/docs/latest/api/app#appsetnamename)
- [Electron 저장 경로 지정](https://www.electronjs.org/docs/latest/api/app#appsetpathname-path)
- [Electron 43.3.0의 Mac Keychain 이름 구성](https://github.com/electron/electron/blob/v43.3.0/shell/browser/electron_browser_main_parts.cc#L478)
- [electron-builder Windows 앱 식별값](https://www.electron.build/v26/docs/nsis/#guid-vs-application-name)
