# 원본 8개 저장소와 대량 변경 독립 확인

2026-11-04 KST. Git 상태 수집 2026-11-04T03:33:41.581768+09:00, 원격 서버 조회 2026-11-04T03:33:57.992957+09:00. 원본 경로의 실제 Git common directory는 각각 해당 폴더의 `.git`임을 확인했다. 다른 채팅의 worktree는 조사·수정하지 않았다.

## 결론

원본 8개 모두 `dev`이며 **HEAD = 로컬 origin/dev = 현재 서버 dev**다. 추적 파일 수정·추가·삭제·이름 변경·충돌은 모두 0개다. Electron 1,720개와 Python 38개는 현재도 그대로 있으며 **Git에 추가되지 않은 로컬 산출물**이다. 미완료 추적 소스 작업이나 병합 충돌은 없다.

미추적 파일은 dev를 최신으로 맞춰도 자동으로 사라지지 않는다. 이번 조사는 원본 소스·산출물·ignore 규칙·브랜치·Git index를 변경하지 않았다. 이 보고서와 JSON만 `.codex` operations 기록에 새로 작성했다.

## 원본 저장소별 현재 상태

`M/A/D`는 추적 파일 수정/추가/삭제다. 서버 SHA는 오래된 origin/dev에 의존하지 않고, 각 저장소에서 `git ls-remote --exit-code origin refs/heads/dev`로 직접 조회했다. 첫 sandbox 조회는 DNS 제한으로 실패했으며 네트워크 허용 후 8개 모두 exit 0이었다.

| 원본 경로 | 브랜치 | HEAD / origin/dev / 서버 dev (동일) | M/A/D | 미추적 | 무시된 경로 수 | 무시된 크기 MiB |
|---|---|---|---:|---:|---:|---:|
| `web/clipper_web_client` | dev | `aabcf3d4aa33` | 0/0/0 | 0 | 23,366 | 276.66 |
| `web/clipper_web_api` | dev | `197af457fc00` | 0/0/0 | 0 | 43,958 | 242.25 |
| `web/clipper_web_admin` | dev | `13b0568df99c` | 0/0/0 | 0 | 25,482 | 366.82 |
| `web/clipper_infra` | dev | `f304750c4d1d` | 0/0/0 | 0 | 527 | 26.96 |
| `desktop/clipper_nestjs` | dev | `a5f8db6f7958` | 0/0/0 | 0 | 31,606 | 1884.35 |
| `desktop/clipper_angular` | dev | `7b559706cea0` | 0/0/0 | 0 | 39,362 | 666.90 |
| `desktop/clipper_python` | dev | `a73593a2c644` | 0/0/0 | 38 | 41,288 | 1706.59 |
| `desktop/clipper_electron` | dev | `6831d8de76d3` | 0/0/0 | 1720 | 10,715 | 2274.61 |

원본 경로는 `/Users/jina/project/adlight/` 기준이다. 실제 관리 콘솔 폴더는 `web/clipper_web_admin`이다. 사용자가 부른 `clipper_wdb_admin`이라는 별도 원본 폴더는 이 목록에 없다. 전체 40자리 SHA·real path·Git common directory는 같은 이름 JSON에 있다.

무시된 파일까지 세면 모든 저장소에 의존성·빌드·캐시 등이 있다. 대표 경로:

- web client/admin: `node_modules/`, `.angular/`, `dist/`.
- web API: `node_modules/`, `dist/`, 로컬 설정 등.
- infra: `ops/`, `runner/` 등.
- Nest: `node_modules/`, `dist/`, `tools/`, `.clipper_data/` 등.
- Angular: `node_modules/`, `.angular/`, `dist/`, `out-tsc/` 등.
- Python: `.venv/`, `__pycache__/`, ONNX/PT 모델 등.
- Electron: `node_modules/`, `dist-app/`, `dist-electron/`, `.tmp/`, 빌드 캐시·실행 도구 등.

`.clipper_data/` 같은 사용자 데이터는 정리 대상으로 취급하지 않았고 내용을 읽거나 기록하지 않았다. 로컬 설정·인증 파일 내용도 출력하지 않았다. 무시된 파일 전체 목록은 개인 데이터 파일명 노출을 피하기 위해 JSON에 넣지 않고 최상위 경로별 개수·크기만 남겼다.

크기는 Git에 나열되는 각 경로의 `lstat().st_size` 합이다. 심볼릭 링크도 경로 하나로 세고 디렉터리 자체는 세지 않는다. 압축·하드링크·블록 할당을 반영한 물리 디스크 사용량은 아니다.

## Electron 1,720개의 정체

두 경로는 `desktop/clipper_electron/` 안에 있다. Git status는 전부 `??`이며 stage된 새 소스가 아니다.

| 경로 | 보이는 미추적 파일 | 해당 파일 크기 | 내부에서 별도로 무시된 파일 | 폴더 생성 시각 KST |
|---|---:|---:|---:|---|
| `dist-app-dance-dev-baseline-20261103/` | 852 | 415,995,554 bytes (396.72 MiB) | 6 (31,570 bytes) | 11-03 23:10:37 |
| `dist-app-dance-quality-integrated-20261103/` | 868 | 416,269,680 bytes (396.99 MiB) | 2 (682 bytes) | 11-03 23:26:45 |
| 합계 | **1,720** | **832,265,234 bytes (793.71 MiB)** | 8 (32,252 bytes) | |

각 폴더는 `mac-arm64/Clipper Studio (dev).app` 형태의 완성된 Mac 앱이다. 앱마다 Electron Frameworks 267개, uv 실행 파일 1개, `app.asar` 1개, Nest 번들 88개, renderer 142개가 있고, Python 사본은 baseline 345개 / integrated 361개다. 나머지는 아이콘·설정·빌더 출력 등이다. `.py`, `.js`, `.md`가 보여도 위치는 **과거 앱 내부의 복사본**이며 원본 형제 저장소 소스의 변경 목록이 아니다.

구조·이름·생성 시각은 11월 3일 비교용 앱 산출물이라는 설명과 일치한다. 파일 시스템만으로 당시 실행자나 정확한 복사/출력 명령까지 확정하지는 않는다. 현재 `electron-builder.yml`의 기본 출력은 `dist-app`이며, `extraResources`가 형제 Angular/Nest/Python 결과를 앱 내부로 복사한다. 비교 앱을 원본 Electron 아래 별도 이름으로 보존하면서 두 폴더가 원본 작업 폴더에 남은 것으로 판단한다.

표시 원인은 `.gitignore:3`이 `dist-app/`만 무시하고 **`dist-app-*` 전체를 무시하지 않기 때문**이다. 대표 파일의 `git check-ignore -v`는 exit 1이며, 현재 `dist-app/`는 exit 0이다. 내부 `.env.packaged`와 일부 `__pycache__`는 별도 규칙으로 무시돼 실제 전체 경로 수가 VSCode 숫자보다 조금 많다.

과거 앱 두 벌에는 새 `native_face.py`가 없으며, `face_adapter.py`·`auraface.py`는 현재 원본과 해시가 다르다. 11월 4일 개선 전 앱 사본이라는 맥락에서 자연스러운 차이다. 과거 앱 내부를 최신 소스와 같게 만들거나, 그 차이를 원본 미커밋 변경으로 계산할 이유는 없다. 필요한 작은 소스 3개만 비교했으며 전체 앱·모델 해싱은 하지 않았다.

보존 가치: 이전 동작·결과 비교와 재현용 기준 앱이다. 두 벌 모두 보존했고, 최신 확인에는 아래 `dist-app/` 앱을 사용한다.

## Python 38개의 정체

모두 `desktop/clipper_python/plugin_models/dance_highlight/coreml-cache/` 아래 `??` 파일이다.

| 하위 경로 | 개수 | 크기 | 수정 시각 KST |
|---|---:|---:|---|
| `a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60/…` | 19 | 522,357,267 bytes (498.16 MiB) | 11-02 21:55:37~39 |
| `opencv-v1/ae6a6ac44d2bdc87924e75fb23d8212430dd24f037f5e035c21deff99afc8b61/…` | 19 | 77,344,243 bytes (73.76 MiB) | 11-03 15:42:08 |
| 합계 | **38** | **599,701,510 bytes (571.92 MiB)** | |

구성은 `.mlmodel` 8개, `.bin` 20개, `Manifest.json` 4개, `.mil` 4개, `model.txt` 2개다. 모델 weight 변환본과 `compiled_model.mlmodelc/` 아래 컴파일 결과, 임시 파일·manifest다. `com.microsoft.OnnxRuntime` 및 dynamic/static MLProgram 구조와 작은 CoreML manifest를 확인했다. 첫 SHA는 현재 코드에 고정된 원본 AuraFace SHA와 같다. 두 번째는 OpenCV 계열 모델의 이전 변환 캐시로 보이며, 정확한 모델명 확정을 위해 큰 weight를 추가로 읽지는 않았다.

이전 CoreML 실행/시험이 원본 저장소의 모델 캐시 경로 아래 생성한 파생물이다. 정확한 당시 실행 명령은 이번 파일 조사만으로 확정하지 않는다. `.gitignore:35~36`은 `*.pt`, `*.onnx`를 제외하지만 이 캐시 경로와 `.mlmodel`, `.bin`, `.mil`, `.json`, `.txt`는 제외하지 않는다. `git check-ignore`도 캐시 경로는 exit 1, ONNX 경로는 exit 0이다.

이 38개는 Python 소스 변경이나 Git에서 받은 새 추적 모델이 아니다. 현재 새 `native_face.py`는 `assets.home()/native-coreml/<derived SHA>/`와 그 하위 `compiled/`를 사용한다. `assets.home()` 기본값은 `~/.cache/clipper/accelerators`이며 환경변수로 바뀔 수 있다. 오래된 저장소 내부 캐시와 이번 새 helper의 기본 캐시는 구분해야 한다.

보존 가치: 원본 모델·변환 환경이 있으면 재생성할 수 있으나, 과거 시험 재현과 초기 컴파일 비용 절감에 도움이 된다. 진행 중 측정과의 사용 관계를 바꾸지 않고 보존했다.

## 현재 Mac 빌드와 로컬 서비스

최신 앱: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`

폴더 생성 시각은 **11-04 03:18:52 KST**다. `dist-app/`는 ignore되어 VSCode의 1,720개에 포함되지 않는다.

- `package.json:18`은 요청한 `npm run build:app:mac:arm64:local-api`를 `node scripts/build-app.mjs darwin arm64 --local-api`로 연결한다.
- 기존 `04-face-coreml-speed-evidence/mac-build.log`에서 Angular → Nest → Electron → uv → darwin arm64 패키징 → `✓ Done. Artifacts in dist-app/` 완료 기록을 직접 확인했다. exit 0은 앞선 빌드 실행 기록이며 이번 조사는 새 빌드를 하지 않았다.
- 실제 패키지 설정은 `identity=development`, `updateChannel=dev`, `webApiBaseUrl=http://127.0.0.1:3000`, `autoUpdateDisabled=true`다.
- 새 패키지의 `native_face.py`, `face_adapter.py`, `auraface.py` **3개 모두 현재 원본과 SHA256가 일치**한다. 설치된 안무 venv의 `native_face.py`도 같은 SHA `452972a144345a833df40c5f3696f7e1badc72fffdc6b51acc5a57313b24f0d7`다. 전체 소스·모델 일치 검사로 확대 해석하지 않는다.
- **03:34:26 KST 현재** `http://127.0.0.1:3000/health`는 HTTP 200, `clipper_web_api=ok`, `user/release/admin` DB 모두 `ok`였다. API 전체 실행 revision은 health 응답만으로 확정할 수 없다.
- **03:34:44 KST 현재** Clipper 개발 앱 main/helper 실행 프로세스는 없었다. `9019/v1/health`는 connection refused였다. 패키지 앱 Nest는 `NestManager`가 동적 포트를 할당하며 9019는 개발 수동 실행용 fallback이므로, 이를 패키지 앱 장애로 단정하지 않는다.
- 기존 보고서의 앱 실행·로그인/안무 입력 화면·Nest 정상 확인은 **앞선 실행 시점의 smoke 결과**다. 현재 앱 실행 중이라는 뜻은 아니다. 병행 측정을 보호하기 위해 이번에는 앱이나 Nest를 새로 띄우지 않았다.
- `.tmp/latest-dev-build-20261104/windows-baseline/win-unpacked` 및 `previous-mac/Clipper Studio (dev).app`가 실제 존재한다. `.tmp/`는 ignore되어 1,720개에 포함되지 않는다.

## 안전한 정리 선택지 — 실행하지 않음

1. **지금은 그대로 보존:** 원본 소스는 깨끗하다. 최신 dev 확인이나 검토를 위해 이 산출물을 먼저 없앨 필요는 없다.
2. **보존하면서 로컬 표시만 줄이기:** `.git/info/exclude`에 두 비교 앱과 Python 캐시의 정확한 경로를 등록할 수 있다. 공유 소스는 바뀌지 않는다. 이번에는 등록하지 않았다.
3. **팀 공통 정책으로 제외:** 추적 `.gitignore`에 목적 경로를 추가하는 별도 변경을 할 수 있다. 이 선택은 실제 소스 변경·검토 대상이다. `*.bin`처럼 넓게 제외하기보다 목적 경로를 한정하는 편이 적절하다. 이번에는 수정하지 않았다.
4. **나중에 별도 보관 위치로 이동 또는 정리:** 진행 중 측정의 사용 여부와 재현·복구 근거를 먼저 확인한 뒤 선택한다. 이동·삭제·숨김, `reset/clean/stash`는 실행하지 않았다.

## 추가 작업 필요 여부

**대량 변경을 해결하기 위한 pull/merge/소스 복구/재빌드는 필요하지 않다.** 조사 시점의 원본 8개 HEAD는 서버 dev와 같다. 최신 로컬 Mac 앱은 이미 존재하며 사용자가 기능별 수동 점검을 이어갈 수 있다. 이 독립 조사는 전체 기능 회귀 시험이나 배포 승인까지 대신하지 않는다.

개발 서버·프로덕션 배포는 하지 않았다. 로컬 API 정상은 개발 서버가 최신이라는 증거가 아니다. 부모의 별도 worktree에서 진행 중인 Mac YuNet/SFace/남은 시간 개선과 별도 Windows 채팅은 건드리지 않았다. 이후 그 작업이 dev에 병합되면 새 revision으로 빌드할지는 별도 판단해야 한다.

증거: 같은 이름 JSON에 8개 Git 상태, 전체 미추적 경로·크기, ignore 최상위 집계, 서버 SHA, 최소 패키지 해시 비교, 현재 health·프로세스 결과가 있다. 앞선 빌드/화면 확인은 `operations/accelerators/records/2026/11/04-face-coreml-speed-results.md` 및 evidence 기록을 참조한다.
