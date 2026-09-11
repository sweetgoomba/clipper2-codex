# 2026-09-09 운영 구축 세션 B 기록

## 세션 종료 상태 — 2026-09-10

- 후속 사용자 승인 작업 완료: 운영 PG 브랜치 release/pg-expiry-20260910의 923c9cb를 보존하고 크레딧 한국어 표시만 8e1ce22로 통합·push. 관련 155 tests/API build PASS. m4-prod api 이미지 빌드/교체 후 HTTP200, user/release/admin DB ok. 사용자 기존 01:02·02:06 내역의 “월 정기 크레딧 지급” 표시 확인. 월 지급 문구 운영 반영 대기는 해소됨. 네이버 변경/DB migration/desktop 재빌드는 포함하지 않음.

최신 종합 상태는 [운영 구축 세션 정리](2026-09-10-production-setup-session-closeout.md)를 따른다. 아래 시간순 기록의 미검증/미배포 문구는 당시 상태다.

- Build 5는 S3 prod/windows/0.0.1/build-5 업로드 및 API 결과 보고 성공, QA 대기. 다운로드한 설치파일 Authenticode Valid(Meta Buzz), 설치 후 로그인 유지 확인.
- 컨테이너 961773bf7c6a에서 skipUpload=false, AWS 인증 정보 존재, 5개 Git 경로 접근 확인. 플러그인 QA는 사용자 요청으로 보류하고 문서화로 세션 종료.
- 월 지급/무료 체험 영문 원장 표시를 한국어 표시명으로 변환하는 로컬 API 변경 2개 파일, 관련 테스트 18 PASS. 운영 배포 미수행.
- 운영 DB clipper_admin_prod의 provider_credentials 조회 결과 빈 테이블 확인. 소실 원인은 미확정이며 사용자는 재등록 선택, 완료 보고는 없음.
- 정식 공개/QA 승인/Customer 공개 다운로드/실제 자동 업데이트는 미수행. 잔여 운영 구축 전체를 완료로 보지 않는다.

## 2026-09-10 Windows 설치 검증 및 runner 출력 경로 조사 추가

- 2026-09-10 13:09 후속 검증(사용자 보고): 소스/의존성 내부 격리 f948922 push 및 Windows 반영. 이미지 11c0d8fc13f3, 운영 컨테이너 85d315d08411. Windows 테스트 7/7 PASS. Build 2는 로컬 clone의 .git 소유권 검사로 차단됨. slash-only safe.directory 추가로는 해결되지 않았고, Git 오류에 표시된 혼합 경로 C:\workspace\clipper\desktop\clipper_angular/.git 형식으로 5개를 등록한 뒤 실제 clone/checkout 및 필수 입력 준비 성공. 다음 재생성에도 이 정확한 등록이 필요하며 자동화 보완 미완료.
- 2026-09-10 13:05/13:09 Admin 실제 연속 빌드(사용자 보고): 같은 컨테이너를 재시작하지 않고 Build 3(0.0.1.3), Build 4(0.0.1.4) 모두 QA 대기 / Windows 로컬 검증 완료. 실제 내부 소스 준비→npm ci→빌드/서명→호스트 보관→API 성공 결과 보고→Admin 표시 확인. 이번 두 번에서 esbuild.exe 및 NSIS 공유 파일 잠금 재발 없음. S3 업로드 차단 유지, QA 승인/정식 공개/자동 업데이트 미수행. 이 후속 결과가 앞선 성공 보고 미검증 및 연속 빌드 대기 기록을 갱신함.

- 후속 연결/배포(사용자 실행): 운영 API runner start/snapshot URL과 요청/결과 보고 토큰 적용 후 같은 이미지로 API만 재생성, Healthy. API→runner snapshot HTTP200 확인, 결과 보고 토큰은 SHA256 비교로 일치 확인. PG 진행 중단 조율 승인 후 수행.
- 후속 Admin 검증: 0.0.1 검증용 릴리스 생성 및 snapshot-20260909T210055Z 고정. Admin 요청 Build 1(0.0.1.1)이 Angular npm ci의 esbuild.exe unlink EPERM으로 차단됨. API가 실패 결과를 수신해 화면에 표시한 것은 확인, 성공 결과 보고는 아직 미검증. 컨테이너에 esbuild 프로세스 없음, 호스트 vmwp.exe PID7344가 운영 공유 폴더 esbuild.exe 핸들 보유. 원인 추정은 공유 파일 잠금 잔류이며 내부 원인 확정 아님.
- 추가 로컬 구현(설계 승인): 운영 작업 내부 sources에 5개 Git 저장소를 하드링크 없이 clone하고 고정 SHA checkout. 호스트 checkout/의존성은 변경하지 않음. .env.packaged 2개, 공개키, Windows uv만 별도 복사. npm ci부터 내부 소스에서 진행, 기존 개발 모드는 유지. 로컬 전체 runner 테스트 42개 중 41 PASS/1 SKIP/0 FAIL. 실제 Git fixture로 고정 커밋/호스트 미커밋 보존/의존성 및 .env.local 비복사/입력 누락 실패와 내부 cwd 연결 검증. 아직 추가 변경 commit/push/Windows 적용 없음. 동일 컨테이너 두 번 연속 실제 빌드 검증 필요.

- 후속 배포: 사용자 명시 승인으로 Infra c784afe를 integration/toss-payments-pg-20260903에 push. Windows pull 및 운영 이미지 6b0a40f546887bdc83bba5b3aa1d58c30fa918a6e5d65387067a50483066bd4c 빌드, 운영 컨테이너 73f2ac99d1a0 재생성. 개발 runner 계속 실행 확인. WORK_ROOT=C:\runner-work, ARCHIVE_ROOT=C:\runner-output\artifacts, skipUpload=true 및 health 정상. 새 컨테이너에 5개 소스 safe.directory 재등록.
- 후속 구축 검증: Windows local-artifact 테스트 5/5 PASS. 원본 5개 브랜치 clean 및 동결 커밋 Angular7ae7366d/Nest780128a0/Python260751d2/Electrondd4e9d67/API3b6d68d7 확인 후 runReleaseJob 실제 빌드 수행. 결과 보고 주소만 컨테이너 내부 임시 HTTP 수신기로 대체, S3 업로드 차단. 운영 API Release 등록 없음. Angular/Nest/Electron/NSIS/외부 서명/호스트 복사/해시 비교 모두 성공, 이전 파일 잠금 미발생.
- 후속 결과물 검증(사용자 출력): C:\clipper-prod\runner-output\artifacts\de8f3773f0fe35af-attempt-1-RElA31\clipperstudio Setup 0.0.1.exe SHA256=8745536975b94b37b04e21e67aba07b7e5f5c1e6035ec0e6235ef021d4478070. 호스트 Authenticode Valid, 서명자 Meta Buzz Co., Ltd. 확인. 이 자동 빌드 결과물의 추가 설치/업데이트는 아직 미검증(이전 수동 빌드 설치 검증과 구분).

- 로컬 구현(사용자 설계 승인 후): 운영 Windows 실행 스크립트만 WORK_ROOT/ARCHIVE_ROOT를 활성화. runner는 작업마다 별도 내부 폴더에서 제작/서명하고 최종 EXE를 호스트 보관 폴더로 배타적 복사 후 크기/SHA256/SHA512 검증. 실패 시 업로드/성공 보고 차단. 개발 기본 동작 유지. 내부 결과는 진단 목적으로 남기며 자동 삭제하지 않음.
- 로컬 검증: runner 및 Windows script 테스트 40개 중 39 PASS, 1 SKIP(실제 Windows 실행 검증 제외), 0 FAIL. 새 테스트는 작업별 고유 경로, 기본 동작 보존, 복사/해시 오류 및 업로드/보고 연결 검증. diff check PASS. Windows Hyper-V에서 수정된 자동 작업 실행은 아직 하지 않음. 이미지 빌드/컨테이너 재생성, commit/push 없음. 다른 세션 runbooks 변경 보존. 사용 설명은 runner/windows/production-artifact-storage.md에 별도 기록.

- 배포(사용자 실행): 운영 API DESKTOP_REDIRECT를 clipperstudio://auth/callback으로 변경하고 API만 재생성. 이미지 sha256:87aa6b2014d651147333585abe017792fa8428191e9849637e5c8acbda26ef1d 유지, Healthy 및 적용값 확인. PG 키/웹훅/DB 변경 없음.
- 설치검증(사용자 보고): Windows 운영 앱 로그인 및 재실행 로그인 유지 성공. 최초 401은 재시도 후 해소됐으며 코드 만료 추정(확정 아님). PowerShell 선택 해제 후 응답 없음 해소. 기존 Clipper2 경로는 비어 있고 HKCU/HKLM 설치 등록 조회 결과 없어 개발 앱 동시 실행 검증 보류.
- 구축(사용자 실행): Hyper-V 공유 출력 경로에서 NSIS 중간 EXE 잠금 발생. 호스트 핸들 vmwp.exe, 빌드 Node 종료 후에도 잠금 지속. 컨테이너 내부 C:\installer-local-check로 출력 위치를 바꿔 설치 EXE 및 blockmap 생성 성공. 구체적 잠금 원인 미확정.
- 구축(사용자 실행): 실행 중 Hyper-V 컨테이너 docker cp 실패. docker exec 내부 Copy-Item으로 공유 폴더에 복사 성공. 미서명 EXE 193283947 bytes, SHA256 83AC8764728B4F7CAE05E2443728D1A67C997FD850E290AC5D3EA8876E778D70, 원본/복사본 일치. 코드서명 후 별도 폴더로 복사, 해시 일치 및 호스트 Authenticode Valid, Meta Buzz Co., Ltd. 확인. 미서명본 latest.yml/blockmap은 서명본 배포에 재사용하지 않음. S3 업로드/공개 없음.
- 설치검증(사용자 보고): 서명된 설치파일 설치 후 로그인 유지. 실행 파일과 clipperstudio 프로토콜 모두 C:\Users\Metabuzz00\AppData\Local\Programs\Clipper\Clipper.exe를 가리킴. 실제 자동 업데이트/개발판 동시 실행/Admin→runner→S3→Customer 경로 미검증.
- 로컬 조사: Infra runner 소스는 변경 전 clean이며 별도 미커밋 운영 runbook들 보존. run-windows-runner-container.ps1이 출력/서명 경로를 C:\runner-output\dist-app 및 signed로 지정하고 release-runner.mjs가 그 위치에서 직접 패키징/서명. 운영만 내부 작업 경로에서 완성 후 호스트 보관 경로로 복사하도록 분리하는 변경 검토 중. 아직 구현/배포하지 않음.

시작: 2026-09-09 11:02 KST. 원본 `web/*`, `desktop/*` 기준. TASKS 5 중 개발 전환 제외.

## 경계와 기록 원칙

- PG 계정·주문·환불·크레딧, 개발 앱·runner·데이터·캐시, `.integration-clones` 변경 금지.
- 서버 명령은 장비·경로·영향을 설명하고 사용자 직접 한 단계씩 실행.
- 앱 식별자, live 키·거래·정식 공개는 별도 승인. 공용 서비스 재시작/배포·복원·키/웹훅 변경은 PG 세션과 시간 조율.
- 수정 직전 diff 확인. 기존 ahead/dirty 변경은 보존하며 commit/push하지 않는다.
- 로컬 조사/구축, 배포, 설치검증을 각각 기록한다. 과거 서버 결과는 현재 재검증으로 세지 않는다.

## 1. 시작 Git 스냅샷 — 로컬 조회

| 원본 repo | branch | HEAD | 시작 상태 |
| --- | --- | --- | --- |
| Customer | integration/toss-payments-pg-20260903 | 888c2b9 | clean, 추적 upstream 차이 없음 |
| Admin | 동일 | fb3e532 | clean, 추적 upstream 차이 없음 |
| API | 동일 | 2710301 | clean, 추적 upstream 차이 없음 |
| Infra | 동일 | 088e520 | 기존 수정 2 + 신규 3 문서 |
| desktop Angular | 동일 | 7f34704b | clean, upstream 없음 |
| desktop NestJS | 동일 | 19c667e | clean, upstream 없음 |
| desktop Electron | 동일 | dbf55c8 | clean, upstream 없음 |
| desktop Python | merge/meme-overlay-into-dev | f8274ac | clean, 추적 upstream 차이 없음 |
| .codex | main | 40beeda | 기존 ahead 25, 기존 수정 4 + 신규 7 문서 |

원격 최신 상태 및 서버 실행 revision은 이 표만으로 확인되지 않는다.
Infra 보존 대상: deploy-prod.md, recreate-prod-databases.md, production-console-settings.md, production-deployment-team-guide.md, production-setup-history-20260908.md.
.codex 보존 대상은 시작 `git status --short` 기준 TASKS/WORKLOG/기존 main 기록 및 기존 신규 문서 전체.

## 2. TASKS 5 분류

| 담당 항목 | 진행 가능 | 결정 필요 | 별도 승인 필요 |
| --- | --- | --- | --- |
| desktop 분리 | 코드·빌드 설정·경로·JWT·로그인·업데이트 조사 | 이름/아이콘 및 고정 식별자·경로·포트 | appId/protocol 등 식별자 적용 |
| runner 분리 | 현재 구현·예제·테스트·원격 소스 확인 | 장비/포트/작업·output/S3/Release 값 | 공용 서비스 영향 시 시간 조율 후 사용자 실행 |
| 설치 E2E | 검증 매트릭스·소스 SHA 준비 | 운영 식별자와 서명/배포 대상 | 운영 설치파일 게시·기존 설치에 영향 있는 작업 |
| 지속운영 | 모니터/백업/복원/접근·로그 정책 조사 및 체크리스트 | 알림 수신자·담당자·보존/RPO/RTO·접근 경로 | 서비스 재시작·호스트 재부팅·실DB 복원·비밀 교체 |
| Google/Toss 준비 | 누락된 콘솔 증거·담당/정책 정리 | 게시 상태/소유자/지원메일·계약/심사/MID·테스트데이터 정책 | 실제 게시·키/웹훅 변경·데이터 정리 |
| 라이브/공개 | PG 세션 결과와 연결한 전환 조건 | 승인자·실거래 범위·중지/복구 기준 | live 키 전환·실결제/취소·정식 공개 |
| 통합/문서 | 원격 조회·통합 계획·Infra 5문서 검토 | 저장소별 최종 후보/PR·공유 담당 | 명시 범위를 넘는 commit/push/merge/외부 전송 |

개발 전환·개발 DB 복제/migration/데이터 정리는 이 세션의 진행 대상이 아니다.

## 3. 로컬 조사·구축

- 시작 문서와 미커밋 TASKS, desktop 식별자 결정 대기 기록, Infra 팀 매뉴얼/콘솔 문서 확인.
- 식별자 문서의 `ai.clipperstudio.app`, `clipperstudio://`는 후보이며 확정값 아님.
- 상세 코드 조사와 로컬 검증 진행 중.

## 4. 배포

이 세션의 서버 실행·배포·재시작·S3 게시 없음.

## 5. 설치검증

이 세션의 Windows/macOS 설치·실행·공존·업데이트 검증 없음.

## 6. 결정 및 다음 단계

사용자 추가 답변: 결정권자 최종 답변은 아직 없음. **아이콘 동일 사용, 운영 이름은 일단 Clipper라고 가정하고 진행**.
이는 잠정 설계 전제이며 `productName`/appId/protocol/Keychain/userData 적용 승인이 아니다.

### 6.1 desktop 분리 조사 결과

| 대상 | 코드에서 확인한 현재 값/동작 | 남은 조치 |
| --- | --- | --- |
| 이름/설치 | productName `Clipper Studio`, appId `ai.clipperstudio.desktop`, package `clipper-electron`, Win exe/Mac app 기본명 Clipper Studio | 기존 개발판 유지. 운영 Clipper 전용 빌드 설정은 승인 후 |
| 아이콘 | mac `icon-mac.png`, Windows `icon.ico` | 동일 사용이라는 잠정 전제 기록; 파일 수정 없음 |
| protocol | builder·Electron 등록/argv 검사가 `clipper`; API 기본 DESKTOP_REDIRECT도 `clipper://auth/callback` | 운영 scheme 승인 후 builder/runtime/API를 함께 반영. API 재시작 PG 일정 조율 |
| API | 기존 Electron 로그인·업데이트 fallback은 dev-api; 일반 runtime config는 비어 있었음 | 이번 명시적 API 입력 구현. 실제 운영 runner 주입/산출물 검사 남음 |
| Nest remote | 현재 로컬 `.env.packaged`는 dev-api와 script/variation/media-search endpoint | 실제 파일 변경 없음. 새 운영 프로필에서 public config만 생성 |
| JWT | builder는 resources/auth/user-jwt-public.pem을 generated/auth에 복사. Windows prepare는 제공된 key가 없으면 기존 key 존재만 확인 | 운영 서버 공개키 fingerprint와 운영 빌드 공개키 일치 확인. 개인키 복사/키 재생성 금지 |
| userData/토큰 | app.getPath(userData), auth.bin safeStorage, 별도 prod setName/setPath 없음 | 운영 고정 경로와 내부 이름을 ready/lock/암호화 초기화 전에 적용; 기존 데이터 이전 금지 |
| Keychain | 명시적인 운영 내부 이름 분리 없음 | 운영 내부 이름 승인 및 실제 Mac 저장/복호화/양쪽 로그인 독립 검증 |
| 모델·캐시 | 일부 userData/plugin_models, YOLO; HF는 기본 ~/.cache/huggingface/hub, 환경 override 지원 | 운영 전용 HF_HOME 등을 모델 존재검사·다운로드·폴더열기·Python 자식 모두에 전달. 공용 캐시 이동/삭제 금지 |
| 포트 | Nest 9019, plugins 54800–54999; Nest loopback bind | 운영 Nest/플러그인 범위 확정 후 launcher 포함 전달·점유 시 동작 검증 |
| 업데이트 | API feed stable/{windows,x64 또는 macos,arm64}; 이번 explicit config에서 API origin 일치 | 실제 서명된 N→N+1 업데이트·중단/재시도·개발판 무영향 검증 |

근거: Electron `electron-builder.yml`, `scripts/build-runtime-config.mjs`, `src/main/main.ts`,
`auth/{api-base,deeplink,token-store,google-login}.ts`, `config/{bundled-env-provider,packaged-runtime-config}.ts`,
`plugin/plugin-install-state.ts`, `backend/nest-process.ts`, Nest `src/main.ts`,
Python `plugins/dialog_highlight/dialog_highlight/services/pipeline/orchestrator.py`.
선택 provider endpoint(예: 별도 TTS/image provider)와 uv/torch/임시폴더 전체는 추가 inventory가 필요하다.
API 주소 1개 통일만으로 모든 외부 provider·JWT·캐시 분리를 완료로 표시하지 않는다.

### 6.2 구체적인 선택안 — 아직 적용 안 함

| 결정 | 선택 A | 선택 B | 영향/권장 방향 |
| --- | --- | --- | --- |
| 운영 고정 식별자 | 과거 후보 `ai.clipperstudio.app` + `clipperstudio://` | 환경을 드러내는 `ai.clipperstudio.production` + `clipper-prod://` | 모두 미승인 후보. A는 외부 이름이 자연스럽고 B는 팀의 환경 구분이 쉬움. 기존 `ai.clipperstudio.desktop`/`clipper://`는 개발판 유지 |
| 운영 내부 이름/경로 | `Clipper`, 기본 userData의 Clipper 경로 | 표시명 Clipper, 고정 내부 이름/경로 `Clipper Production` | A는 간단, B는 향후 표시명 변경과 분리하기 쉬움. Keychain·바로가기·uninstaller·updater cache까지 한 세트로 승인 |
| desktop 포트 | 별도 고정값 후보 Nest 9020, plugins 55000–55199 | 동적 할당과 URL 전달 강화 | 우선 A가 현재 구조 변경이 작음. 장비 점유 확인 후 확정; 지금 미적용 |
| Windows runner 장비 | storage에 운영 전용 workspace/컨테이너 추가 | 별도 Windows 장비 | A는 비용 적지만 CPU/RAM/디스크/동시 빌드 경합. 기존 runner 8GB 설정 고려해 여유 확인 후 선택 |
| Windows 분리값 | 후보 container/image `clipper-windows-release-runner-prod`, host 19030→container 19029, `C:\clipper-prod` | 장비 확정 후 다른 경로/포트 | 후보일 뿐. 실제 개발 mount와 중첩·junction 공유가 없어야 함. prod output와 env/Git/AWS 권한도 별도 |
| Mac runner | PG 웹/API와 다른 서명 가능한 Mac | m4-prod에 별도 작업경로와 빌드 시간대 | 전용 Mac 권장. m4-prod 빌드는 PG 서비스 자원 경합 때문에 사전 조율 필요 |
| S3 | 기존 bucket 내부 prod 전용 prefix와 IAM scope | 운영 전용 bucket | A는 단순, B는 접근/보존 권한을 독립하기 쉬움. 현재 실제 bucket/prefix 확인 전 결정 보류 |

### 6.3 runner 조사 — 현재 그대로 운영 시작 금지

- `run-windows-runner-container.ps1`: 환경과 무관하게 기본 이름 `clipper-windows-release-runner`, 고정 `19029:19029`; 동명 기존 컨테이너가 있으면 `docker rm -f`. `-Environment prod`만 추가하면 개발판 보존을 보장하지 못한다.
- `start-windows-runner-container.ps1`: `git pull --ff-only origin dev`를 수행하고 준비 스크립트로 workspace env를 수정한다. 낮은 단계의 ContainerName/ImageName도 wrapper에서 전달하지 않는다.
- prepare는 같은 workspace의 Nest/Python `.env.packaged`와 Electron 공개키를 사용/수정한다. 운영은 별도 workspace 필요. repoRoot 예제의 현재 개발 원본 경로를 실제 운영 값으로 사용 금지.
- output `C:\runner-output\dist-app`, signed `C:\runner-output\signed`는 컨테이너 내부 경로이며 현재 host 영속 mount 없음. 동일 경로라도 별도 컨테이너면 분리되지만 제거 시 미업로드 증거가 사라질 수 있음. 작업 로그·output 보존 정책 필요.
- API prod 예제 S3 `clipper-release/clipper2/prod`, runner prod 예제 `clipperstudio/prod/macos`가 다르다. 실제 저장값은 미확인. runner는 prefix 아래 version/build-number를 추가한다. bucket/prefix와 Release report/public URL을 실값으로 대조해야 함.
- start token(API→runner)과 report token(runner→API)은 양 끝 일치 및 dev/prod 차등 필요. 비밀값은 비교 결과만 기록하고 출력하지 않는다.
- source snapshot은 Angular/Nest/Python/Electron/Web API 5개 repo에서 동일 sourceBranch를 조회. branch는 환경 선택값이 아니다.
- runner 테스트 34개 중 33 PASS, Windows PowerShell 실제 실행 1 SKIP. 소스 snapshot·가짜 빌드/report 테스트이며 Docker 이미지/설치파일 빌드 성공이 아니다.
- 첫 제한 실행은 localhost `listen EPERM`으로 실패. 실제 외부 접속 없는 임시 fixture/localhost 테스트임을 확인하고 승인된 권한으로 재실행하여 위 결과 확보. 운영 호출 없음.

### 6.4 Mac 전체 경로의 별도 미구현

후속 사용자 결정(7절): **이번에는 Windows만 제공하고 Mac 다운로드는 준비 중으로 유지**한다. 아래는 조사 이력이며 현재 Mac 공개/빌드/업데이트 구현할 일 목록이 아니다.

- Web API `releases.service.ts`는 Windows job에만 runner start 호출을 보낸다. Mac 자동 dispatch 완료로 볼 수 없다.
- runner build matrix Mac 대상은 arm64이고 일반 미서명 명령을 사용. mac artifact는 실제 서명 검사 없이 env의 signatureStatus를 반환하므로 `signed` metadata만 신뢰하면 안 된다.
- Electron mac target은 DMG, runner는 DMG 1개를 업로드, API feed도 같은 artifact URL을 사용한다. 설치된 electron-updater MacUpdater는 ZIP을 선택하고 dmg/pkg를 제외한다.
- Mac 자동 업데이트 ZIP이 필요하다는 것은 [electron-builder v26 공식 문서](https://www.electron.build/v26/docs/features/auto-update/)와도 일치한다. DMG 다운로드와 ZIP 업데이트 artifact를 구분하는 Release 모델/API 경로 설계 필요.
- Customer `download.component.ts`는 Windows manifest만 다운로드하며 Mac은 준비 중 안내. PG 세션과 공유하는 Customer/API 파일이므로 이 세션에서는 수정하지 않았다. 변경 전 대상/범위 공지 및 조율 필요.
- Mac x64 지원은 제품/runner 대상 결정 필요. 현재 arm64 runner 경로를 x64 검증으로 확대하지 않는다.

### 6.5 설치·공존·업데이트 검증표 — 전부 미실행

1. 승인한 5 repo SHA, Infra SHA, 공개키 fingerprint, API origin, 이름/식별자, env 변수명, artifact hash/서명/버전을 빌드 기록에 고정.
2. 운영 Admin의 build 생성 → 운영 runner만 시작 → 운영 S3 경로 upload → 운영 Release DB report를 연결. dev runner/DB/S3 경로에 새 작업 없는지 대조. 빌드 성공과 stable 게시를 분리.
3. signed Windows exe 및 notarized Mac dmg/ZIP 검증. 다운로드 파일 SHA256/SHA512와 Release 기록 비교.
4. 기존 개발판/샘플 프로젝트가 있는 Windows·Mac에서 설치 전 앱/프로토콜/경로/로그인 상태를 기록. 운영판 추가 설치 후 두 앱 동시 실행, 각 API 로그인, 새 프로젝트와 모델 전용 경로, 포트/캐시 분리 확인.
5. 운영 N→N+1 업데이트, 재실행 후 프로젝트/설정/로그인 유지 및 개발판 버전 불변 확인. 업데이트 중단·재시도, 오래된 설치와의 호환성 확인.
6. 한쪽 제거가 다른 쪽의 scheme/설정/데이터에 영향을 주지 않는지 폐기 가능한 검증용 프로필에서 확인. 직원의 실제 개발 설치를 삭제 대상으로 삼지 않는다.
7. 실제 크레딧 차감/작업이 필요한 E2E는 PG 세션과 전용 계정·예상 변동을 먼저 합의. 현재 PG 테스트 계정으로 실행하지 않는다.

### 6.6 지속운영 준비와 남은 결정

- monitor는 m4-prod에서 기존 실행(9/8 증거). repo 예제는 dev target만 있고 README의 DB 호스트/레거시 도메인 설명은 현재 토폴로지와 다르다. 실제 targets/state는 미확인이고 복사/덮어쓰기 금지.
- 로컬 monitor 순수 테스트 6 PASS. Slack 메시지 발송·실제 장애 유도 없음.
- 운영 target 후보는 Customer/Admin HTTPS와 API HTTPS(health body db.user/admin/release 모두 ok), DB 55202/55212/55222, 백업 신선도. m4-prod monitor의 `host.docker.internal`을 m2-db 주소로 오인하지 않는다.
- 알림 채널/당번·대체 담당/응답시간 결정 필요. 알림 확인은 전용 시험 target에서 down/recovery를 유도하고 승인된 수신자에게 전달. 서비스 실제 중지로 시험하지 않는다.
- monitor와 웹/API가 같은 m4-prod/사무실에 있으면 호스트·전원·인터넷 전체 장애를 스스로 알리기 어렵다. 외부 HTTPS 감시와 수신 경로 후보를 팀과 결정.
- repo에는 백업 신선도 검사기가 있으나 운영 백업 생성 스케줄·성공 증거는 미확인. 최신 dump mtime 검사만으로 복원 가능성은 증명되지 않으며 현재 검사기는 0바이트도 통과 가능.
- 백업 정책 후보: 매일 암호화 logical dump + 별도 장비/NAS 복제, 일 7/주 4 보존; 더 짧은 허용 손실시간이 필요하면 WAL/PITR 검토. **주기/보존/RPO/RTO는 미확정**이며 실제 시간 목표는 팀 결정.
- 복원 리허설은 별도 승인된 격리 DB/볼륨/포트에 수행. 운영 DB 덮어쓰기·개발 DB 복제 작업 아님. 복원 앱은 PG worker/웹훅/이메일/runner 외부 연결을 차단한 후 schema/건수/관계·업무 복구를 확인. 이 세션에서 DB 생성/복원 없음.
- User/Admin/Release 3 DB의 백업 시점 차이와 외부 Toss/S3 상태를 함께 고려. dump 3개가 각각 성공했다는 것만으로 업무적으로 동일 시점이라는 보장은 없음.
- 앱/DB/monitor Compose는 restart unless-stopped. OS 전원 복구·Docker 시작·FileVault 로그인·mount 준비까지 보장하지 않는다. 장비별 UPS/자동 전원복구/OS 로그인/Docker 자동시작 확인 → DB/NPM/API/웹/runner 순서 점검 → 업무 복구는 PG 시간 조율 후 사용자 실행.
- DB 외부 포워딩은 기존 기록상 존재. 현 출발지 제한·TLS·VPN/SSH tunnel·읽기전용 계정을 확인한 뒤 팀 정책 결정. 임의 포트 폐쇄/DB 권한 변경 없음.
- 로그: callback query/토큰/키 원문 수집 금지. NPM 실제 access_log 설정, Docker rotation/보존·용량 알림 확인 필요. env 600/secret dir 권한과 소유자, 키 백업·복구 담당·교체 절차를 기록하되 비밀값은 문서에 저장하지 않음.

### 6.7 Google·Toss 및 라이브 전환 조건

Google 운영 프로젝트 ID/소유자·대체 소유자, 지원메일 수신/담당, 브랜딩 이름·homepage/privacy URL,
authorized domain, OAuth client/callback, audience/게시 상태/검증 상태/scopes를 콘솔에서 읽기 전용 확인할 필요가 있다.
운영 로그인 성공을 브랜드 검증/일반 사용자 공개 완료로 대체하지 않는다.
[Google 공식 브랜드 검증 안내](https://developers.google.com/identity/verification/authentication-verification)의 정보 항목을 준비하되 콘솔 제출/게시/클라이언트 삭제는 실행하지 않는다.

Toss 계약/카드사 심사·자동결제 계약 상태, Widget/Billing 각각 MID와 TEST/live 키 세트 연결,
기능별 허용 결제수단, 환불·정산·고객지원 담당, 테스트데이터 보존/구분 정책을 확인한다.
[Toss API 키 공식 안내](https://docs.tosspayments.com/reference/using-api/api-keys) 기준으로 서로 다른 키 세트를 혼용하지 않는다.
MID/계약 실제 상태는 이번 세션에서 확인되지 않았다. 키 값 출력·교체·웹훅 변경 없음.

전환 승인 자료: PG 세션 TASKS 4의 미해결/제외 사유·증거, desktop/runner E2E,
지속운영·백업복원 증거, Google/Toss 담당자 확인, 테스트 기록 처리 정책,
정확한 릴리스 SHA·아티팩트·실거래 계정/금액/취소 조건·시간대·실행자·중지 기준.
그 자료를 바탕으로 **키 전환 → 한정된 실결제/취소 → 정식 공개를 각각 별도 승인**받는다.
전환 실패 시 무조건 TEST키로 덮어쓰거나 DB를 되돌리는 식의 롤백은 금지. 진행 중 live 거래 정합성/웹훅·환불 처리를 보존하는 중지·복구 절차를 먼저 확정한다.
테스트데이터는 현재 보존. 운영 DB 재초기화·개발 DB 복제·옛 PG 기록 자동삭제는 계획에 포함하지 않는다.

### 6.8 원격 상태 및 통합 계획

2026-09-09 로컬 `git ls-remote --heads origin ...` 성공 결과. fetch/checkout/push 없음.
최초 샌드박스 DNS 실패 후 승인된 네트워크 읽기로 확인했다.

| desktop repo | origin dev | origin main | 현재 로컬 통합 branch의 원격 |
| --- | --- | --- | --- |
| Angular | 6a5d882 | d2f2475 | 없음 |
| Electron | 768b876 | df36a6e | 없음 |
| NestJS | ef18951 | ad719ca | 없음 |
| Python | 9f6cb5e | cf77448 | integration branch 없음; 현재 merge/meme-overlay-into-dev의 원격 f8274ac는 로컬과 일치 |

통합 순서: PG 세션 결과/SHA 확보 → 원본 dirty 변경의 소유자 확인 → repo별 diff/원격 ancestry 재검토
→ 5 repo 공통 sourceBranch 및 각 SHA 확정 → 필요한 변경만 선택 commit/push/PR
→ 소스 snapshot 고정 → 운영 runner isolated build/검증 → 별도 게시.
장기 운영 main은 기존 결정이지만 오늘 main으로 자동 merge/checkout하지 않는다.
최신 원격 dev와 로컬 후보 간 ancestry는 이번 ls-remote만으로 판단하지 않았다. 후속 fetch가 필요하다.
.codex ahead 25 및 기존 Infra 문서 5개를 이번 코드 변경과 묶지 않는다. 기존 문서 작성자 검토 후 파일/문단 단위 공유 범위를 확정한다.

### 6.9 Infra 문서 5개 검토 결과 — 원문 보존

| 문서 | 이번 검토 / 팀 공유 전 보완 |
| --- | --- |
| deploy-prod.md | 현재 직접 Docker build와 팀 매뉴얼로 안내됨. 이 문서의 배포 안내를 desktop runner에 확대하지 않음 |
| production-deployment-team-guide.md | 장비/현재 upstream/선택 배포/별도 migration/secret 보호 정리됨. 실제 반복 배포와 롤백 증거·운영 당번·동시 실행 조율 필요 |
| production-console-settings.md | 확인값/미확인값 구분 적절. 운영 Google 지원메일/owner·게시/MID/NPM 로그·DB 외부 접속 정책 증거 보완 |
| production-setup-history-20260908.md | 과거 수행 증거로 보존. 초기 키 생성/DB 생성 명령은 오늘 실행할 지시가 아님. runner placeholder 수정은 연결 검증 증거가 아님 |
| recreate-prod-databases.md | 9/8 일회성 파괴적 이력으로만 참조. 복원/평소 배포/관리자 추가에 전체 절차를 복사하지 않음 |

9/7 callback 설계의 개발 우선 배포/미구축 proxy/옛 `/app` 경로는 과거 내용이다.
9/8 closeout·현재 원본·사용자 이번 범위를 우선하며 개발 전환 계획을 되살리지 않는다.

### 6.10 이번 로컬 구현·검증 결과

- Electron에 선택 입력 `CLIPPER_DESKTOP_API_BASE_URL` 지원. HTTPS origin만 허용, 빈 값/HTTP/credentials/path/query/fragment와 local-api 동시 입력 거부.
- 명시 runtime config가 로그인 API 및 기본 API·script/variation/media-search·업데이트 feed에 전달. 이전 shell/bundled URL보다 우선. 입력 없는 개발 기본값 보존.
- 변경: `scripts/build-runtime-config.mjs`, `src/main/auth/api-base.ts`, `src/main/config/packaged-runtime-config.ts`, 관련 기존/신규 테스트, README. 그 외 web/API/runner 실행 코드와 실제 env 미변경.
- TDD: 신규 5 테스트에서 변경 전 4 FAIL/1 PASS 확인 → 구현 후 관련 7파일 65 PASS.
- Node v24.19.0, Electron TypeScript 전체 컴파일 PASS. 출력은 `/private/tmp/clipper-prod-electron-20260909/dist-electron` 사용. 원본 dist-electron/개발 앱 userData/모델 캐시 미수정.
- runner baseline 33 PASS/Windows 실행 1 SKIP, monitor 6 PASS. 실제 컨테이너 빌드·공개 S3·운영 API/PG 호출 없음.
- `git diff --check` Electron/Infra/.codex 통과. 마지막 Electron TypeScript `--noEmit --incremental false`도 PASS.
- Superpowers requesting-code-review에 따른 독립 읽기 전용 코드 리뷰: 해당 5 코드/테스트 파일에 조치가 필요한 정확성·회귀 결함 없음. 리뷰어 관련 43 tests 재확인 PASS. 전체 운영 준비/설치파일 동작의 증거로 확대하지 않음.
- runner 새 env 입력 전달, 공개키·식별자·포트·캐시 분리, 최종 app packaging은 아직 미완료. 이번 변경을 운영 전체 구축 완료로 취급하지 않는다.

### 6.11 세션 조율 및 사용자 첫 서버 단계

PG 세션 A의 전용 로그가 생성된 것을 확인했다. 최신 기록상 운영 화면/revision 결과 대기이며 서비스 변경 없음.
이 세션은 Customer/API/PG 상태를 변경하지 않았고 공용 서비스 재시작·키 변경 요청도 하지 않았다.
TASKS는 수정 직전 다시 읽고 5번에만 이 기록 링크를 추가한다.

다음 사용자 실행은 **storage Windows PowerShell, 경로 무관, 읽기 전용**:

```powershell
hostname
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

실행/중지/삭제/빌드/env 출력 없음. 장비와 실제 runner 이름·포트를 확인한 후에만
다음 단계로 해당 컨테이너 mount/workspace·자원·버전 정보를 필요한 필드만 조회하도록 안내한다.

## 7. 후속 요청 — 최신 dev 통합 및 Windows 운영 범위 정정

사용자 요청: desktop 최신 dev를 바탕으로 복제/분리한 새 integration 브랜치에 PG 작업 통합.
원본 8 repo의 실제 로컬/원격 상태를 확인. runner node_modules 관련 이력 및 Windows 자동업데이트 조사.
운영도 Windows 다운로드만 제공, Mac 버튼은 준비 중 유지. 같은 Windows PC에 개발/운영 runner 컨테이너 분리.
이 지시는 이전 Mac 전체 경로 구현 계획보다 우선한다. Mac 공개/자동빌드/업데이트 구현은 지금 진행하지 않는다.

### 실행 계획과 경계

- [x] 원본 상태와 GitHub 브랜치 읽기 전용 조회. 정확한 기존 이름은 `integration/toss-payments-pg-20260903`이며 `payment` 단수 이름은 조회된 8 repo에 없음.
- [x] desktop 4개 `origin/dev`만 fetch. 기존 checkout/dirty와 기존 PG worktree 보존.
- [x] 각 로컬 dev가 fast-forward 가능하고 다른 worktree에 체크아웃되지 않은 것을 확인한 뒤 최신화.
- [x] `.worktrees/production-pg-refresh-20260909/desktop/<repo>`에 최신 dev 기반 `integration/toss-payments-pg-20260909`를 생성. 사용자 요청한 복제 작업공간이며 기존 `.integration-clones`와 무관.
- [x] Angular/Nest/Electron에 기존 PG 후보를 merge. Angular 충돌은 최신 UI/입력 변경과 PG 과금/접근 동작을 모두 보존하여 해결.
- [x] Python: 사용자 **최신 dev만 사용** 결정. 밈 오버레이 3개 커밋 미통합, 기존 원본 branch는 그대로 보존.
- [x] 기존 Electron의 이번 세션 미커밋 API 설정 패치를 별도로 보존하고 새 후보에도 적용. 원본 파일은 유지. 기존 ahead/다른 세션 변경과 묶지 않음.
- [x] 새 작업공간에서 컴파일·관련 테스트·merge ancestry 확인. 요청된 merge에 필요한 로컬 merge commit만 생성, 원격 push/서비스 배포는 하지 않음.
- [x] runner/업데이트 조사와 사용자 결정 반영, TASKS 5만 갱신.

작업공간 상위 adlight는 Git 저장소가 아니며 `.worktrees`는 각 원본 repo 밖에 있어 원본에 stage될 수 없다.
명시적인 복제 작업공간 요청에 따라 using-git-worktrees 적용. 현재 task를 다른 task로 옮기는 native 도구는 이 작업과 맞지 않아 git worktree 사용.
이번 통합은 Git 소스 최신화이며 개발 서버·개발 DB·개발 데이터 전환이 아니다.

### 새 조회 시점의 원본/원격

| repo | 원본 checkout HEAD | 기존 PG 통합 branch GitHub | 조회한 최신 dev |
| --- | --- | --- | --- |
| desktop Angular | 7f34704b, PG integration | 없음 | aee3580c |
| desktop NestJS | 19c667e, PG integration | 없음 | 8ae0952 |
| desktop Electron | dbf55c8, PG integration + 이 세션 미커밋 6파일 | 없음 | 747ad7e |
| desktop Python | f8274ac, merge/meme-overlay-into-dev | 로컬에도 없음/원격에도 없음 | 9f6cb5e |
| web Customer | 888c2b9 | 있음, 888c2b9 일치 | 4b361ef |
| web Admin | fb3e532 | 있음, fb3e532 일치 | eae522f |
| web API | 2710301 | 있음, 2710301 일치 | 557da3f |
| web Infra | 088e520 + 기존 5문서 | 있음, 088e520 일치 | 4d32022 |

이전 조사 후 dev가 추가 이동했으므로 위 SHA를 이번 통합 시작점으로 고정한다.
기존 후보에 없는 dev 커밋: Angular 87/Nest 48/Electron 15/Python 42 (merge commit 포함).
반대쪽 unique: Angular 6/Nest 6/Electron 2/Python 3. Git merge-tree 사전 확인은 원본 checkout을 변경하지 않았으며 Angular 3파일/Python 4파일 충돌, Nest/Electron 자동 병합 가능.

### 7.1 새 desktop 통합 결과 — 2026-09-09 13:22 KST 기준

로컬 앱 사용자 확인 후 문구/링크 수정: 사용자가 앱 기동·로그인·Trial 400 크레딧 표시 성공을 확인했다. 원본 Angular의 settings-account.service에서 trial tier 표시를 `무료 체험`, 기존 `one-time free trial` 표시를 `최초 무료 체험 크레딧 지급`으로 번역하며 저장 reason/DB는 유지했다. 설정 링크를 `/my/credits`, `/my/payment-history`로 수정했다. `요금제 보기`는 원래 `/pricing` 의도였으나 Customer sanitizeWebReturnPath가 bare pricing을 거부하여 `/my`로 돌리던 문제를 정확한 `/pricing` 경로만 허용하도록 수정했다. Nest plugin-catalog URL 입력 설명에서 `현재 준비 중입니다.`만 삭제했다. 수정 전 회귀 테스트 실패 확인 후 Angular 26/26, Customer auth/handoff 21/21 PASS, diff check PASS. 빌드된 앱 재생성/설치 확인은 사용자 다음 실행 단계이며 commit/push/배포 없음.

Naver 키 관리 읽기 전용 조사: 저장/선택은 단일 Naver pool이며 capability별 권한 필드 없음. Director 테스트는 선택 키로 News GET `/v1/search/news.json`(sim/display1)와 DataLab POST `/v1/datalab/search`(최근 7일, 입력 키워드 1그룹)를 순차 호출한다. 이미지 테스트는 GET `/v1/search/image`(display4). 실제 Director 주제 조사에서 News 및 조건부 DataLab을 사용하며 동일 승인 credential id/revision을 공유한다. 콘티 생성은 저장된 조사 근거와 OpenAI를 사용한다. 제안은 자격증명 1회 저장 + 이미지/뉴스/DataLab 각각 기능 배정·개별 테스트·상태 + 기능별 키 선택/승인 스냅샷 분리다. Admin/API의 Naver 코드는 아직 수정하지 않았고 실제 제공업체 테스트 요청도 실행하지 않았다.

로컬 PG DB 마이그레이션 사용자 실행 완료: `.env.local`을 명시한 명령의 출력에서 admin은 `LocalizeCreditProductNames1788900000000`까지, user는 9개(`CreateUserOnboardingJobs1788200000000`까지), release는 2개(`AddReleaseArtifactSha5121782790000000`까지) 모두 성공 확인. 기존 DB는 대상이 아니다. 다음 단계는 dotenv preload로 PG 전용 설정을 읽고 로컬 Web API를 시작하는 사용자 실행 안내이며, API 기동/로그인/설치 기능 검증은 아직 미확인이다.

로컬 PG DB 후속: 사용자 실행 결과 전용 컨테이너 3개 Healthy 확인. 기존 `.env`를 보존하고 ignored `.env.local`을 새로 생성(0600)했다. example 기본값과 기존 로컬 설정을 바탕으로 DB를 127.0.0.1:56433/56434/56435에 고정, WEB_BASE_URL=4201, 로컬 전용 HMAC/암호화 비밀값을 생성했다. Slack webhook 및 Windows runner 원격 실행 주소/토큰은 새 환경파일에서 비웠다. Toss 설정에 비TEST 키가 있으면 생성하지 않도록 검사했으며 기존 키는 비어 있어 PG 테스트 키 준비가 추가로 필요하다. dotenv preload/override로 선택 파일을 명시하는 방식을 확인했고 주소·포트만 출력하여 전용 DB 선택을 검증했다. API build PASS. 마이그레이션은 실행하지 않았으며 관리자 DB부터 사용자 직접 실행 안내 단계다.

후속 로컬 테스트 준비: 사용자가 Mac mini 로컬 PG 테스트용 DB 분리를 요청했다. 기존 개발 DB 포트 5433/5434/5435 및 환불 E2E DB 55433/55434/55435는 보존한다. 사용자가 lsof로 56433/56434/56435에 LISTEN 출력이 없음을 확인했다. Web API에 새 `docker-compose.pg-local.yml`만 추가하여 프로젝트 `clipper-pg-local-20260909`, loopback 포트 56433/56434/56435, 전용 named volume 3개를 정의했다. `docker compose ... config --quiet` 성공. 구축: 구성 파일만 준비, 기존 .env/DB 수정 및 마이그레이션 없음. 배포/컨테이너 실행: 사용자 실행 안내 단계이며 아직 실행 결과 없음. 설치검증: 미실행. 이는 로컬 PG 테스트 준비이며 개발 서버·개발 DB 전환 작업은 아니다.

후속 사용자 승인에 따른 원본 전환 완료: Angular `57873881`, NestJS `a673ee9`, Electron `81a028f`는 원본 경로에서 `integration/toss-payments-pg-20260909`를 사용한다. 이 3개의 별도 통합 worktree는 파일을 보존한 채 detached HEAD로 전환했다. Web 4개는 사용자의 정정에 따라 기존 `integration/toss-payments-pg-20260903`을 유지하며 Infra 미커밋 문서도 유지했다.

Electron API 수정 6파일은 `81a028f3d20e3aaad31f13730acbb9e820754a84`로 커밋했다. 직전 TypeScript build 및 관련 시험 9/9 PASS. 원본/통합 worktree의 6파일이 동일함을 확인하고 원본 변경을 stash `c6cc910f3f5aeac5f2e2e9048b17889412c7b6fd`에 추가 백업한 뒤 전환했다. 최종 원본 파일은 커밋된 파일과 동일하며 중복 stash는 재적용/삭제하지 않았다.

Python 원본은 이번 fetch에서 새로 확인된 최신 `origin/dev`인 `260751d`까지 fast-forward하여 `dev`로 전환했다. Python 별도 통합 worktree/브랜치는 이전 `9f6cb5e`로 남아 있으므로 원본 최신 dev와 구분한다. 추가 Python 커밋의 기능 시험은 이번 checkout 작업에서 실행하지 않았다.

구축/소스 전환: 최종 원본 desktop 4개 작업 상태 clean 확인. 기존 의존성·캐시 재설치/삭제 없음. 배포: push·서버 실행·재시작·키/DB 변경 없음. 설치검증: 이번 작업에서는 실행하지 않음. 아래 표는 최초 통합 당시 기록이다.

공통 branch: `integration/toss-payments-pg-20260909`, 경로: `/Users/jina/project/adlight/.worktrees/production-pg-refresh-20260909/desktop/<repo>`.
원본 repo에서 관리하는 새 linked worktree다. 별도 원격 repository/새 GitHub branch를 만들지는 않았다.
최종 commit 전 `ls-remote`를 다시 확인해 아래 dev SHA에 추가 이동이 없음을 확인했다.

| repo | 최신 dev 기준 SHA | 새 integration SHA | 내용 |
| --- | --- | --- | --- |
| clipper_angular | aee3580c | 57873881 | 최신 dev + 기존 PG 7f34704b, 충돌 3파일 해결 |
| clipper_nestjs | 8ae0952 | a673ee9 | 최신 dev + 기존 PG 19c667e 자동 병합 |
| clipper_electron | 747ad7e | 26d442f | 최신 dev + 기존 PG dbf55c8 자동 병합; 이번 세션 API 수정은 별도 미커밋 |
| clipper_python | 9f6cb5e | 9f6cb5e | 사용자 결정대로 최신 dev와 동일, merge 불필요 |

각 로컬 dev ref = origin/dev. 새 Angular/Nest/Electron merge commit은 첫 부모가 최신 dev, 둘째 부모가 기존 PG integration이다.
`merge-base --is-ancestor`로 최신 dev와 기존 PG 모두 포함됨을 확인했다. 이전 integration ref와 원본 checkout HEAD는 변경하지 않았다.
원본 Electron 미커밋 6파일과 새 worktree의 같은 6파일은 현재 동일하며, 사용자 승인 없이 한쪽만 commit/push하거나 서로 덮어쓰지 않는다.
미커밋 패치 백업 `/private/tmp/clipper-pg-refresh-20260909/electron-session.patch` 및 신규 테스트 복사본은 임시 자료다. 원본과 새 worktree 파일이 지속 작업 근거다.
새 브랜치 4개는 로컬에만 있다. Web API/Infra 등 4개 웹 repo에는 새 20260909 branch를 만들거나 dev를 merge하지 않았다.
따라서 5 repo 공통 sourceBranch를 요구하는 실제 runner build는 웹 API의 같은 branch 준비와 선택 commit/push 확인 후 진행해야 한다.

### 7.2 충돌 해결과 로컬 검증

Angular 충돌 3파일:
- storyboard-scene-list.component.html: 폐기한 이미지 검색 안내를 다시 추가하지 않음.
- v2-variation-list.component.ts: 최신 AppErrorBanner import와 PG OperationChargeGuardService 동시 유지.
- settings.component.html: 최신 matButton 표현과 PG 요금제/결제/크레딧 문구·출처 표시 유지.

별도 리뷰에서 Angular의 충돌 해결 3파일 및 Nest jobs/variation/dialog 자동 병합을 양 부모와 비교했다.
최신 입력 검증·폰트 해석·텔레메트리와 PG evidence/과금/실패복구가 함께 남아 있고, 조치가 필요한 병합 유발 결함을 발견하지 못했다.

| 검증 | 결과 및 한계 |
| --- | --- |
| Angular packaged build / 전체 spec 타입검사 | PASS. 새 worktree 산출물만 생성 |
| Angular 선택 ChromeHeadless | 1068 PASS; PG 수정 spec·storyboard·variation·IME/forms·font 포함. 전체 suite는 아님 |
| Angular SCSS | 6 PASS |
| Nest TypeScript / ncc bundle+assets | PASS |
| Nest 전체 node:test | 2285 중 2284 PASS, ignored `.env.packaged` 부재로 1 FAIL. 임시 테스트 env 준비 후 해당 파일 2/2 PASS. 전체 재실행으로 기록하지 않음 |
| Electron 전체 node:test (PG merge, API 미커밋 복사 전) | 406 중 405 PASS, fresh staged resources 시험의 generated 자료 부재로 1 FAIL. 새 Angular/Nest 빌드+임시 테스트 config/public key 준비 후 해당 파일 7/7 PASS |
| Electron API 미커밋 복사 후 | TypeScript PASS; API 설정/로그인/업데이트/handoff/telemetry 관련 77 PASS |
| Python 최신 dev 선택 테스트 | TTS 묵음·폰트·render contract 34 PASS. 원본 venv의 패키지를 재설치하지 않고 새 소스 PYTHONPATH로 실행 |
| Git | unmerged entry 없음, staged/working diff whitespace 검사 PASS, ancestry 확인 |

첫 Angular 명령은 해당 디렉터리 셸의 Node24.3.0이 CLI 요구사항에 못 미쳐 거부되어 절대경로 Node24.19.0로 고정했다.
이후 sandbox 내부 Angular build는 exit134/빈 로그였으나 동일 명령의 sandbox 외부 실행은 성공. 소스 우회 수정 없음.
Nest 표적 시험은 localhost listen EPERM 한 건이었으며, localhost 시험을 허용한 전체 실행에서 그 시험은 통과했다.
Nest 새 worktree만 lockfile npm ci --ignore-scripts로 설치(fontkit 포함). 기존 node_modules는 변경하지 않음.
Angular/Electron은 lockfile 일치한 원본 의존성을 초기에 읽기용 symlink로 사용했고 최종에는 별도 APFS 복사본으로 분리했다. 두 node_modules가 symlink가 아닌 독립 디렉터리임을 확인했다. 기존 개발 캐시·의존성 변경 없음.
임시 `.env.packaged`, generated runtime config 및 무작위 시험 공개키는 시험 후 삭제했다. 실제 운영/개발 secret·JWT key를 복사하지 않았다.
이 검증은 소스 통합/로컬 빌드 검증이다. Windows exe 생성·서명·S3 upload·운영 설치·실제 결제/환불 확인이 아니다.

로그는 `/private/tmp/clipper-pg-refresh-20260909/`의 angular-merged-tests.log, angular-merged-build-escalated.log,
nest-all-tests.log, nest-bundle.log, electron-all-tests.log, electron-session-reapplied-tests.log, python-dev-tests.log 참조.

### 7.3 컨테이너 재생성과 node_modules — 이력 확인

- `9ffc6f0` (2026-07-06 10:38): `--rm` 일회성 runner를 `-d --restart unless-stopped` 상시 runner로 변경. 시작 스크립트 재실행 시 기존 컨테이너 제거/재생성이 추가됨.
- `6d2f8a4` (같은 날 11:10): 오래된 node_modules 문제를 막기 위해 매 작업에서 소스 checkout 후 Angular/Nest/Electron `npm ci` 추가.
- `3515402` (2026-08-11): Node22→24 이미지 변경. 이때는 이미지 빌드/컨테이너 재생성 및 새 Node 기준 의존성 재설치가 모두 관련됨.

현재 작업 순서: 상시 runner가 Admin 요청 수신 → 소스 SHA checkout → npm ci → 설치파일 build/sign/upload/report → 다음 요청 대기.
**매 빌드 후 컨테이너를 삭제할 필요가 없으며 현재 job 처리도 그렇게 하지 않는다.**
시작 wrapper 재실행은 별개로 컨테이너를 재생성한다. `-SkipBuildImage`도 이미지 빌드만 생략하며 재생성은 생략하지 않는다.
호스트에 mount한 소스/node_modules는 컨테이너를 삭제해도 남는다. 의존성 정리는 npm ci가 담당한다.
Node/runner 코드를 포함한 이미지 변경, 실행 env/포트/mount/메모리 변경에는 컨테이너 재생성이 필요하다.

근거: Infra `runner/release-runner.mjs` checkoutSourceSnapshot/buildSourceDependencyInstallPlan/runReleaseJob,
`runner/release-runner-server.mjs` activeJobId/job endpoint,
`runner/windows/{run-windows-runner-container.ps1,start-windows-runner-container.ps1,Dockerfile}`.

### 7.4 같은 PC의 개발/운영 runner — 사용자 결정

별도 Windows PC 선택은 더 이상 미정사항이 아니다. **같은 storage PC에 dev/prod 컨테이너를 각각 둔다.**
개발 컨테이너/작업폴더 유지, 운영용 이름·host port·host workspace·환경파일·S3 경로를 별도로 둔다.
컨테이너 내부 경로/포트는 같아도 되지만 host workspace를 공유하면 checkout/npm ci/env가 충돌한다.
툴체인이 같으면 Docker image 자체는 공유 가능하다. 환경을 나누기 위해 반드시 이미지까지 두 벌이어야 하는 것은 아니다.
현재 wrapper의 기본 이름/고정 host port는 아직 개선하지 않았다. storage 조회 결과로 기존 경로와 포트를 확인한 후 prod 입력/실행 절차를 완성한다.

### 7.5 Windows 다운로드·자동업데이트와 Mac 정책

**사용자 설명:** 현재 개발 웹 Windows 버튼은 정식배포된 설치파일을 내려받고 Mac 버튼은 준비 중이다.
**사용자 결정:** 운영도 동일하게 Windows 다운로드만 제공하고 Mac은 준비 중 유지. Mac 공개·원격 자동빌드 구현은 지금 하지 않음.
현재 Customer 코드의 Mac 클릭은 항상 준비 중을 표시하므로 UI 변경은 필요 없음. API는 Mac artifact도 지원하지만 이것이 Mac 게시 승인은 아니며 운영 Mac target에 publish하지 않는다.

Windows 자동업데이트 코드 조사:
- 패키징 앱은 기본적으로 autoDownload=true와 checkForUpdatesAndNotify 실행.
- unpackaged 개발 실행은 제외. `CLIPPER_AUTO_UPDATE_DISABLED=1` 또는 `CLIPPER_DISABLE_AUTO_UPDATE=1`이면 비활성.
- `e75a96e` (2026-07-02)는 **--local-api 빌드만** autoUpdateDisabled=true로 만든 변경.
- Windows remote runner는 일반 `build:app:win:x64`를 호출하며 local-api 옵션을 넣지 않음.
- 원본 로컬 generated config는 local-api/autoUpdateDisabled=true였다. 이는 마지막 로컬 생성물의 상태일 뿐 실제 원격 Windows 설치본 증거가 아님.
- API Release target의 auto_update_enabled 및 current artifact 상태에 따라 feed가 제공된다. 현재 운영/개발 DB 실값은 조회하지 않았음.
- 중요: 현재 수동 다운로드 manifest와 업데이트 feed가 모두 findPublishedArtifactForUpdate를 사용한다. DB에서 auto_update_enabled=false로 바꾸면 수동 다운로드도 사라질 수 있다. 다운로드 유지+자동업데이트만 차단하려면 소비 경로를 분리하거나 앱 측 disable을 검토해야 한다. 이번 조사에서 설정을 변경하지 않음.

현재 설치된 Windows 앱의 resources/packaged-runtime-config.json에서 autoUpdateDisabled/buildInfo만 확인하고,
실행 환경의 위 두 disable flag 및 Release DB target의 channel/platform/arch/auto_update_enabled/current artifact 존재 여부를 읽기 전용으로 대조해야 실제 상태를 확정할 수 있다.
앱 설정/DB/env 전체를 출력하지 않고, 서버 명령은 사용자 직접 한 단계씩 실행한다.

## 8. 2026-09-10 네이버 사용 API 분리 구현

사용자가 확인한 로컬 UI 시안의 실제 적용을 승인했다. 승인 용어는 `사용 API`, 두 권한은 `검색` 및 `데이터랩(검색어트렌드)`다. 이미지/뉴스는 동일 검색 권한이며 테스트만 별개로 표시한다. 미사용 데이터랩 badge는 목록에 표시하지 않는다.

계획: `/Users/jina/project/adlight/.preview/naver-api-ui/implementation-plan.md`. 원본 Web API/Admin 및 desktop Nest/Angular에서 구현한다. 현재 다른 세션의 payment-reconciliation/payment-webhook 수정과 Admin members/detail 수정이 존재하며 보존한다. 기존 desktop settings 및 plugin-catalog 문구 수정도 보존한다.

구축: 권한 저장/마이그레이션, 기능별 키 선택·한도, 개별 테스트, Admin UI, desktop 조사 승인 연결을 구현 중이다. API watch가 켜져 있으면 마이그레이션 전 컬럼 오류가 발생할 수 있어 사용자에게 로컬 API만 종료하도록 안내했다.

배포: 실제 DB migration·외부 Naver 요청·서비스 재시작·commit/push 없음. 설치검증: 구현 후 사용자 rebuild와 로컬 기능 확인 필요.

### 2026-09-10 추가 UI 확인

- 구축/소스 게시: Windows 사용자 확인에서55000–55199 LISTEN 없음, IPv4 TCP 제외 범위와 겹침 없음. 안내한 후속 절차에 따라 Electron 캐시·포트 분리5파일을 dd4e9d6으로 커밋·푸시. 직전 tsc 및 전체419 tests PASS, 원본 clean/origin0/0. 배포: 소스 게시까지이며 Windows fetch·재컴파일·재패키징 필요. 실제 앱 실행/모델 다운로드/공존 검증 및 운영 API 변경 없음.

- 구축(운영 캐시/포트 분리, 사용자 승인 후 로컬 구현): production identity일 때 userData/cache 아래 HuggingFace(HF_HOME/HF_HUB_CACHE/HUGGINGFACE_HUB_CACHE), Torch, uv, XDG 캐시를 지정. 부팅 초기 process.env 및 provider 병합 후 자식 프로세스 env에 모두 적용해 기존 번들·사용자 설정의 개발 캐시 경로를 덮도록 함. 플러그인 포트 후보55000–55199 적용, 개발 기본값 유지. 모델 폴더 열기는 모델 존재 검사와 같은 경로 resolver 사용. 캐시 복사/이동/삭제 없음. TypeScript 및 표적8 tests PASS, 전체 회귀 실행 결과 별도 확인. 배포: 미커밋/미푸시/Windows 미반영. 설치검증: 앱 미실행, Windows 포트 사용·예약 범위 확인 필요.

- 구축/소스 게시: 사용자 승인 후 Electron 운영 식별자 분리 10파일을 4c60f1e로 커밋하고 integration/toss-payments-pg-20260909에 푸시 완료. 직전 TypeScript 컴파일 및 전체416 tests PASS. 원본 clean, origin과0/0 확인. Windows 사용자 ClipperDataExists/clipperstudio HKCU/HKLM 모두False 확인. 배포/설치검증: Windows 소스 수신·prod opt-in·재빌드는 아직 대기, 운영 API/서비스 변경 없음.

- 운영 식별자 사용자 승인: appId ai.clipperstudio.app, 표시 이름/데이터 폴더 Clipper, protocol clipperstudio 확정. 기존 개발 기본값 유지. 구축(로컬 구현): CLIPPER_DESKTOP_ENVIRONMENT=prod와 운영 API 주소를 함께 지정한 빌드에서만 identity=production을 저장하고 별도 전체 builder 설정을 생성. extends 방식은 protocol 배열이 병합되어 기존 clipper까지 등록되는 것을 실제 config loader로 발견하여 사용하지 않음. 생성 설정에서 appId/productName/package name/protocol을 교체. 시작 시 로그·단일 인스턴스 락보다 먼저 userData/sessionData를 appData/Clipper로 지정하고 AppUserModelId 설정. protocol 등록/argv/open-url 처리는 선택한 scheme만 수용. 자동 업데이트 차단 추가 없음. 배포: 미커밋/미푸시, Windows 기존 검사 결과물에는 아직 미반영. 설치검증: 미실행. 다음 필수 확인은 실제 장비의 기존 Clipper 폴더 유무, 변경 소스 게시·운영 env opt-in·재빌드, 운영 API DESKTOP_REDIRECT 별도 조율. 모델 공용 캐시/플러그인 포트/실기 Keychain 공존 검증은 이 식별자 수정으로 완료되지 않음.

- 구축/빌드검증(Windows 사용자 실행): npm ci 세 저장소 완료(취약점/설치 스크립트 승인 경고 남음), Angular packaged/Nest ncc 및 assets 복사/Electron tsc 성공. uv 다운로드·Windows 배치, 운영 runtime config/공개키 생성·금지 비밀값 검사 완료. electron-builder --win --x64 --dir --config.win.signAndEditExecutable=false로 C:\clipper-prod\runner-output\package-check\win-unpacked 생성. 표준입력 Node 검사에서 필수파일/운영 API URL/공개키 지문 모두PASS. 최초 node -e 검사는 PowerShell 인수 따옴표 소실로 실패했고 표준입력 방식으로 해소. 배포: 서명/설치파일/업로드/정식 공개 없음. 설치검증: 앱 미실행. 현재 결과물은 기존 Clipper Studio/appId/protocol 값을 사용하는 검사용 앱 폴더이며 운영·개발 공존 설정 완료 아님.

- 구축(Windows 사용자 확인): 운영 공개키 저장 및 DER SHA256 df87c1dd85ca85dcc0a3cd00b532a931db32418831e3f73fc4b05f3479d7f49d 일치. 운영 workspace Nest/Python .env.packaged 생성. runner prod env에 CLIPPER_DESKTOP_API_BASE_URL=https://api.clipperstudio.ai 추가 후 idle 확인/운영 runner만 제거·재생성(id 9fc154afa75c). safe.directory 다섯 경로 재등록 후 별도 -e 없이 runtimeConfigForBuild가 운영 API 주소를 반환하는 것을 사용자 확인. 자동 업데이트 차단 변경 없음. 운영 Release targets 조회 [] / 운영 feed404, 개발 feed200 및 0.0.30 확인. 배포: runner 환경 반영만 완료, 운영 API/DB/설치파일 배포 없음. 설치검증: 없음. 다음은 운영 workspace의 npm ci이며 appId/protocol·데이터/포트 공존 승인·검증은 여전히 남아 있음.

- 업데이트 조사(사용자 요청, 차단 구현 없음): Electron은 packaged 실행 시 업데이트 확인/자동 다운로드하며 설치된 electron-updater의 autoInstallOnAppQuit 기본값 true를 변경하지 않음(Windows 종료 시 설치 시도 가능). API findPublishedArtifactForUpdate는 target.currentArtifactId와 autoUpdateEnabled가 모두 있어야 feed를 제공하며 없으면404. 따라서 앱 자체 차단 추가 전 운영/개발 feed 실제 응답 확인 필요. 운영 Windows feed 경로 /releases/updates/stable/windows/x64/latest.yml. 현재 서버 target 설정값/실제 업데이트 설치는 미검증.

- 구축(Windows 사용자 실행 결과): Git fetch의 dubious ownership 확인. 운영 runner 컨테이너 안의 다섯 저장소만 safe.directory에 등록한 뒤 source snapshot 조회 성공. Angular 7ae7366d / Nest 780128a0 / Python 260751d2 / Electron aecc30e1 / API 3b6d68d7 확인. GitHub 인증과 각 브랜치 조회까지 검증됨. 컨테이너 재생성 시 safe.directory 재등록 절차는 남은 작업. 배포/설치검증: 앱 빌드·서명·업로드·API 재시작 없음.

- 구축(사용자 Windows 실행): 운영 runner clipper-windows-release-runner-prod 생성(id 143544f8203c), prod 이미지/독립 workspace C:\clipper-prod/output C:\clipper-prod\runner-output, 19030→19029, 8g, SkipBuildImage/DryRun 적용. 기존 인증 파일 변수명 점검에서 API/S3 경로 override 없음 확인. 운영 API 컨테이너에서 http://192.168.0.14:19030/health HTTP200/ok=true/activeJobId=null 사용자 확인. 배포: runner 실행까지이며 앱 빌드·서명·S3 게시·운영 API 설정/재시작은 미실행. 설치검증: 미실행. 다음은 runner 내부 GitHub 인증으로 다섯 저장소의 20260909 source snapshot 조회 검증.

- 구축/소스 게시: 사용자 승인에 따라 Web API 3b6d68d(37파일), Admin cafebe3(22파일), Customer ae75f51(3파일)를 각각 원본 integration/toss-payments-pg-20260903에 커밋·푸시. API에 동일 3b6d68d의 integration/toss-payments-pg-20260909도 추가·원격 게시. Mac 원본 브랜치는 세 저장소 모두 20260903 유지. 임시 소스 복사본에서 커밋 대상만 검증(API 191 tests+build, Admin119 tests+build, Customer11 tests+build/spec typecheck PASS). Admin 오래된 테스트 기대값 ‘대기’를 승인된 ‘검색 대기 키’로 수정 후 재검증. 같은 파일의 PG 결제/환불/만료/지급내역 추가 변경은 index 단위로 제외했고 원본 파일 내용 보존을 hash로 확인. 로컬 DB compose 파일은 미커밋 유지. 배포: 서버/DB migration/재시작/S3 게시 없음. 설치검증: 없음. Windows Web API를 새 20260909/3b6d68d로 fetch/switch하는 사용자 단계가 다음.

- 구축: 사용자 요청으로 runner 저장소별 브랜치 설정 제안은 철회. Python 기존 로컬 integration/toss-payments-pg-20260909(별도 worktree, clean, dev 대비 추가 커밋 없음)를 9f6cb5e→260751d로 fast-forward하고 원격 신규 게시 완료. 원격 dev도 260751d임을 조회 확인. 원본 Python 경로는 dev 유지. 새 코드 수정/병합 커밋 없음. Windows는 fetch/switch 필요. Web API의 20260903 브랜치 차이는 아직 미해결. 배포/설치검증: 없음.

- 구축(Windows 사용자 확인): C:\clipper-prod\desktop의 네 저장소 복제 및 git status/log 확인 완료. Angular 7ae7366d / NestJS 780128a / Electron aecc30e는 integration/toss-payments-pg-20260909, Python 260751d는 dev이며 모두 변경 파일 없음. 배포: 없음. 설치검증: 운영 Windows 앱 빌드·설치 아직 미실행. Web API 원본의 Naver/크레딧 표시 수정은 여전히 미커밋으로 확인. runner의 source snapshot은 현재 모든 저장소에 동일 sourceBranch를 fetch하므로 저장소별 브랜치가 다른 현재 구성에 대한 처리 보완이 빌드 전 필요.

- desktop 선택 commit/push: 사용자 dmd(한영 전환 ‘응’) 승인으로 Angular12/Nest11/Electron1 파일만 각 원본 20260909 통합 브랜치에 커밋. Angular7ae7366d, Nest780128a, Electrona ecc30e(정확 SHA: aecc30e). 세 브랜치 origin 신규 게시/upstream 설정 완료, 기존 최신dev·PG통합 커밋 포함. Python/web/Infra/.codex 커밋·푸시 대상 제외. 커밋 전 재검증 Angular86/Nest114/Electron7 tests PASS, Angular app/spec typecheck/Nest build/Electron tsc PASS. 이는 소스 게시이며 운영 API/앱 배포 아님.
- 운영 연결 준비 사용자 확인: 운영 API runner start/snapshot URL 및 양방향 토큰 모두 미설정. Windows192.168.0.14, m4-prod route192.168.0.0/24→en0 확인(포트 접속 성공 아님). Windows prod env 신규 생성, bucket clipperstudio/prefix prod/windows, API https://api.clipperstudio.ai, 내부포트19029, SKIP_UPLOAD=1. 사용자 토큰 생성/ACL 명령 PASS 확인. 토큰은 파일에만 저장되고 운영 API 적용·재시작 없음. 다음은 env를 전달한 네트워크 차단 임시 이미지에서 설정 파싱 검사이며 아직 상시 runner 실행하지 않음.
- S3 조사: Windows dev runner 실제 bucket clipperstudio/prefix dev/windows/public base https://clipperstudio.s3.ap-northeast-2.amazonaws.com 확인. 운영 API 컨테이너 S3 관련3환경변수 미설정 사용자 확인. 소스 확인 결과 API는 이 변수를 읽지 않고 runner report의 artifact bucket/key/publicUrl을 Release DB에 저장하므로 API S3 환경변수 추가 불필요. prod/windows는 운영 runner prefix 후보이며 AWS 권한/실제 게시 검증 전. 다음은 운영 API의 runner start/snapshot URL 및 양방향 토큰 설정 여부(값 비출력) 조회.
- 사용자 Windows 이미지 검증 완료: prod 이미지5abb98bdc74c 빌드/태그 성공(캐시 재사용), 네트워크·mount·포트 없는 임시 컨테이너에서 Node v24.19.0/Git2.45.2.windows.1/AWS CLI2.36.20 실행 확인. 임시 컨테이너 --rm 종료. 운영 상시 runner/앱 빌드/서명/S3 업로드는 아직 미실행. 다음은 기존 dev runner의 S3 bucket/prefix/public URL 공개 설정만 선별 조회해 prod 경로 결정을 준비.
- Windows 후속 사용자 검증: 262c4ff fast-forward 수신, 변경 PowerShell3파일 ParseFile 모두PASS, Assert-ProductionRunnerOptions 지정 prod값 실행PASS. 실제 Docker 컨테이너는 아직 생성하지 않음. Dockerfile 확인: runner JS/entrypoint/sign helper 및 Node/Git/AWS 도구 이미지이며 desktop 소스/키 없이 별도 prod 태그 빌드 가능. 다음 단계는 사용자 Windows에서 운영 이미지 빌드(앱 빌드·S3 게시 아님).
- 사용자 yes 승인으로 Infra runner 4파일만 commit/push 완료: 262c4ff, integration/toss-payments-pg-20260903, 원격088e520→262c4ff. 스테이징 목록4파일 확인 및 구조테스트17 PASS/Windows1 SKIP 재확인. 기존 운영 문서2수정/3미추적 그대로 보존, .codex 포함 안 함. 이는 소스 전송이며 Windows 설치·컨테이너 실행·서비스 배포 아님. 다음 사용자 단계는 C:\clipper-prod\web\clipper_infra에서 해당 branch fast-forward pull 후 PowerShell 문법 확인.
- Windows 사용자 조회/준비 확인: 개발 container/image clipper-windows-release-runner, host19029→19029, Hyper-V, memory8589934592(8GiB), restart unless-stopped. RW source C:\Users\Metabuzz00\Desktop\project\clipper→C:\workspace\clipper, CodeSignTool RO mount. RAM31.9GiB/free24.8GiB/C空171.8GiB. C:\clipper-prod 및19030 미사용 확인 후 폴더 생성, web\clipper_infra 088e520/integration/toss-payments-pg-20260903 clean clone 사용자 확인.
- runner 로컬 구현: run/start wrapper에 HostPort/OutputRoot 및 이름 전달 추가. prod는 명시 workspace/분리 이름·포트/출력 경로 요구, 기본 dev값 거부. prod Infra 자동 dev pull 생략, 기존 prod 컨테이너 자동 rm 거부, 결과를 host bind로 보존 가능. 실제 env/S3/소스 branch/app identity는 아직 준비·검증 필요. 현재 선택안 container/image clipper-windows-release-runner-prod, host19030→19029, workspace C:\clipper-prod, output C:\clipper-prod\runner-output.
- 검증: Windows 스크립트 정적/구조 테스트17 PASS/Windows 전용1 SKIP, diff check PASS. Windows PowerShell 문법/실행·Docker build는 미검증. 운영 생성/기존 개발 변경 없음. 배포: Windows clone은 수정 이전088e520. 로컬 Infra runner4파일만 전송할 방법/선택 커밋·푸시 확인 필요; 기존 운영 문서 변경은 별도 보존.
- 사용자 확인: 원장 조회 오류 수정 후 내역 정상 표시. 스토리보드 새 조사 성공, clipperstudio 검색 7→17(+10)/DataLab 1→2(+1), 검색 대기 키 3 유지. 정상 실행 경로의 용도 분리 확인이며 한도 소진·자동 전환 검증은 아님.
- 운영 Windows runner 분리 재개: 같은 Windows PC의 별도 dev/prod 컨테이너 원칙 유지. 원본 Infra runner 스크립트/현재 diff 재확인, 기존 운영 문서 수정 보존. 사용자에게 Windows PowerShell docker ps 읽기 전용 조회부터 안내. 컨테이너 생성·중지·배포 없음.
- 원장 한국어 표시 후 조회 실패 보완: 신규 JOIN에서 operation_runs.user_id(uuid)와 credit_ledger_entries.user_id(varchar36)를 직접 비교한 결함 확인(마이그레이션·Entity 근거). run.user_id::text 비교로 수정, 사용자 소유권 조건 유지. 쿼리 회귀 테스트 실패 확인 후 관련 29 tests PASS. 최초 모의 테스트는 실제 PostgreSQL 타입 검사를 하지 않아 놓쳤음. 실제 DB 쿼리/데이터 수정 없음, 사용자 로컬 API 반영 후 조회 확인 대기. 앱 재빌드 불필요.
- 크레딧 내역 한국어 표시 승인/구현: URL·붙여넣기·프롬프트 숏폼 제작, 대사/안무 하이라이트, 배리에이션 6종에 ‘크레딧 사용/반환’ 표시. 원장 조회에서 같은 사용자 operation_runs LEFT JOIN으로 과거 반환에도 작업명 제공. 원문 reason/금액/원장 불변, displayName/displayDescription 선택 필드 추가. 알려진 취소 사유는 취소 반환, 그 외 실패 반환 설명. 미확인 과거 작업은 일반 한국어 제목. 앱 설정·홈, Customer 크레딧, Admin 회원 원장 연결. 다른 PG 세션 변경을 보존해 조회/표시만 수정. 별도 migration/DB수정/PG실행/운영배포 없음.
- 검증: API 4 suites/49 tests 및 build PASS, desktop Angular app/spec typecheck와 표시 7 tests PASS, Customer build/13 tests PASS, Admin build PASS. Admin 기존 테스트의 내부 코드 노출 기대 1건을 한국어 및 원문 비노출 검증으로 갱신해 재검증. 로컬 API 변경 반영 및 앱 재빌드 후 기존 기록으로 사용자 확인 필요(새 작업 실행 불필요).
- 사용자 재빌드 Step3 실패: Electron dist-app 정리 rmSync에서 ENOTEMPTY. 조회 시 중복 build-app/electron-builder 프로세스 없음. 생성 출력 정리에 maxRetries 5/retryDelay 200ms 적용; 지속 실패는 계속 build 중단. 실제 폴더 재생성 원인은 미확정. 프로젝트/userData 수동 삭제 없음, 배포/설치 없음. 기존 출력 정리 테스트 2개 통과; 첫 전체 실행에서 선행 빌드 중단으로 dist-electron이 없어 1개 실패하여 TypeScript 컴파일 후 재검증.
- 로컬 사용자 검증: 안무하이라이트 멤버 이미지 검색 후 clipperstudio 검색 3→6, DataLab 1 유지, 검색 대기 키 3 유지. 해당 실행의 Naver 용도별 선택·카운터 확인.
- 안무하이라이트 크레딧 수정: 영상 준비가 과금 시작보다 먼저 실행되어 YouTube 로그인 필요 오류 시 차감/반환 자체가 호출되지 않는 경로 확인. JobsService에서 차감을 영상 준비 직전으로 이동하고 준비 이후 조기 취소 경로에 반환 처리 추가. 큐 대기 중에는 차감하지 않고 작업 시작 시 차감. 과거 실행의 DB 원장을 변경하거나 합성하지 않음.
- 검증: 준비 실패/취소/잔액 부족 회귀 테스트가 기존 코드에서 실패함을 확인한 뒤 수정. desktop 작업 수명주기 관련 31 tests PASS 및 TypeScript 컴파일 PASS. API operations/credit-grants 기존 2 suites/41 tests PASS(격리 테스트, 실제 DB/PG 호출 없음). 앱 재빌드 후 사용자 실화면 -150/+150 및 최종 잔액 재확인 대기. 다른 세션 API 크레딧 repository/결제 변경 보존. 배포/설치 없음.
- 추가 간격 요청: Naver 상태 카드 내부 gap 3px, heading 아래 추가 margin 3px, 설명 paragraph margin 0으로 조정(제목→상세 6px, 상세→설명 3px). 검색 권한 있는 standby 키는 ‘검색 대기 키’로 명시. 데이터랩 미사용과 검색 대기 상태는 독립이며 선택 정책 변경 없음. 배포/설치 변경 없음.
- 후속 요청: usage-bar 마크업/스타일 제거, 상태별 DB·사용 가능·소진·제외 상세 글자 12px로 축소. DataLab도 DB 키 준비 상태에서는 ‘DB credential 준비됨’과 정상 색상으로 통일. 이는 외부 연결 테스트 성공 표시가 아니라 사용 가능한 DB 키 존재 표시이며 선택 정책은 그대로 유지. 배포/설치 변경 없음.
- 사용자 확인: AddNaverUsageApis 마이그레이션 성공, API 재시작 및 사용 API 저장 후 목록 배지 표시 확인.
- 구축: Naver 테스트 버튼의 disabled 조건은 있었지만 시각 스타일이 누락되어 opacity/cursor 추가. 검색·데이터랩 상태를 동일 너비 2열로 배치(좁은 화면 1열), 배지 간격 추가, 오늘 사용량 정렬, 작업 버튼을 표 셀 내부 flex로 옮겨 행 높이 깨짐 수정. 데이터랩의 자동 승격 문구를 사용 가능으로 수정하고 각 카드에 선택 규칙 설명. 백엔드 선택 정책 변경 없음.
- 검증: ChromeHeadless 관련 78 tests PASS. 미선택 API 클릭 차단/opacity/cursor, 카드 너비·위치, 배지 gap, 작업 셀 높이 검증 포함. Admin local build PASS, diff check PASS. 사용자 로그인 화면 자체의 육안 확인은 이번 검증에 포함하지 않음.
- 배포: 없음. DB/외부 API 호출/운영 서비스 변경 없음. 설치검증: desktop 재설치 불필요; 실행 중인 로컬 Admin 화면 새로고침으로 확인.

### 8.1 구현 및 검증 결과

- API: `usageApis` 저장/검증/응답, 기존 Naver 행 빈 배열(설정 필요), Search/DataLab 선택·한도·사용량 분리. News 및 DataLab 테스트는 source를 명시해 각각 실행하며 성공 호출을 해당 API 사용량에 기록한다. 승인 revision에 사용 API를 포함한다. `1789000000000-AddNaverUsageApis` 마이그레이션을 등록하고 OpenAPI 갱신. 실제 DB에는 미적용.
- Admin: 네이버 API / 사용 API 용어, 선택한 badge만 표시, 이미지·뉴스·DataLab 세 행의 개별 테스트와 결과 유지, 검색어 변경 시 이전 결과 초기화. 사용량·준비 상태를 Search/DataLab로 나눔. 미설정 키는 설정 필요. 검색 활성화는 `검색 기본 키로 지정`이며 검색 권한 없는 키에는 노출/허용하지 않는다. DataLab은 별도 우선순위 선택이다.
- Desktop: 연구 preflight 및 실제 수집의 Search/DataLab 승인 id/revision 분리, 누락 시 검색 키로 대체하지 않음. 승인 버전 `research-grounded-discovery-cost-2026-09-10.v2`, 화면은 네이버 검색/네이버 데이터랩 표시. 앱 반영은 사용자 rebuild 필요.
- 검증: API build 및 관련 26 suites/240 tests PASS, OpenAPI 4 suites/17 tests 별도 PASS. Admin 관련 ChromeHeadless 96 tests, spec typecheck, local build PASS. Desktop Nest build, 관련 108 tests 및 HTTP 경계 5 tests PASS. Desktop Angular app/spec typecheck 및 preflight UI 2 tests PASS. 최종 diff check 통과.
- 검토: API/Desktop 계약 일치 확인. 독립 리뷰의 활성화 의미 혼동 지적을 검색 전용 동작/명칭으로 해소하고 회귀 테스트 추가. 검색의 활성화/소진이 DataLab 우선순위 선택에 영향을 주지 않도록 유지한다.
- 다른 세션의 payment-reconciliation/payment-webhook 및 members/detail 변경, 이전 settings/plugin-catalog 변경 보존. 비밀값/계정/PG 거래/기존 DB 변경 없음. 카운터는 기존 read/modify/write 및 UTC 날짜 경계를 유지하며 원자성 변경은 범위에 넣지 않았다.
- 사용자 다음 단계: 현재 `.env.local` admin 목적지가 127.0.0.1:56433/clipper_admin임을 읽기 전용 확인했다. 로컬 API 중지 상태에서 이 파일을 명시해 admin migration 실행, 이후 API 재시작 및 기존 키 사용 API 설정. 이 단계는 아직 사용자 실행 대기다.
- 최종 보완: 활성 검색 키에서 search 용도를 제거하면 검색 가능한 대체 키로 전환하며, 대체 키가 없으면 변경 전 거부하는 기존 정책 유지. 관련 추가 회귀 2개 포함 API 표적 35 tests 및 재빌드 PASS. Admin의 활성 상태 표시도 search 포함 여부에 따라 검색 기본 키/사용 가능/설정 필요로 구분, 표적 7 tests PASS. 독립 리뷰 재확인 결과 기존 활성화 의미 문제 해소, 추가 지적 없음. 위 전체 테스트 수는 전체 실행 당시 수치이며 마지막 표적 재검증을 전체 재실행으로 계산하지 않는다.
