# 최신 원격 dev 기준 Mac arm64 로컬 API 재빌드

2026-11-04 KST. 사용자 요청에 따라 원본 8개 저장소의 현재 서버 dev SHA를 읽기 전용 `git ls-remote`로 재조회했다. 모두 dev이며 로컬 HEAD와 서버 dev가 일치했고, 추적 소스 변경도 없었다.

| 원본 저장소 | HEAD = 서버 dev |
|---|---|
| `web/clipper_web_client` | `aabcf3d4aa33a7da0795e7b141aee31da3ac2b71` |
| `web/clipper_web_api` | `197af457fc00517de11e0f89fbb7c78863ca897c` |
| `web/clipper_web_admin` | `13b0568df99c3e3c6f99374f329d8f9bccc7b6a7` |
| `web/clipper_infra` | `f304750c4d1d6277483ba71ce73f88baaf33fe80` |
| `desktop/clipper_nestjs` | `a5f8db6f795847f778e67810e35f5d1af83c7fd0` |
| `desktop/clipper_angular` | `7b559706cea07e21374592f3106c0503d7a93d34` |
| `desktop/clipper_python` | `a73593a2c6445bc87401eb4de30e9954ef2467ba` |
| `desktop/clipper_electron` | `6831d8de76d34bb6ae2523122e9c6271ba68d00f` |

## 빌드 결과

원본 `desktop/clipper_electron`에서 `npm run build:app:mac:arm64:local-api` 실행. Node v24.19.0으로 03:42:27~03:43:29 KST에 완료했고 exit code는 0이다. Angular packaged 빌드, Nest 번들, Electron TypeScript, uv 준비, darwin arm64 앱 패키징을 통과했다. `--dir --publish never` 개발 빌드이며 서명·배포는 수행하지 않았다.

첫 실행은 도구 실행 환경의 Node v24.3.0이 Angular 최소 버전에 미달해 Angular 시작 단계에서 중단됐다. 설치된 Node v24.19.0의 bin 경로를 명시해 같은 명령을 재실행했다. 소스나 의존성 버전 변경은 하지 않았다.

앱: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`

패키지 실제 설정:

- `identity=development`, `updateChannel=dev`
- `webApiBaseUrl=http://127.0.0.1:3000`
- `autoUpdateDisabled=true`

## 검증과 보존

- 빌드 후 8개 원본 HEAD는 시작 때와 동일하며 Git status는 전부 비어 있다.
- 패키지의 `native_face.py`, `face_adapter.py`, `auraface.py`는 원본과 SHA256가 모두 일치한다. 전체 모델·앱의 대규모 해시는 실행하지 않았다.
- CoreML 캐시와 비교용 Mac 앱 두 폴더는 경로·파일 크기·mtime·mode가 빌드 전과 동일하다. 파일을 삭제·이동하지 않았다.
- 소스와 공유 `.gitignore`는 변경하지 않았다. `.git/info/exclude`의 정확한 경로 3개가 계속 적용되고 있다.
- 저장소의 모델 캐시 `plugin_models/`가 새 앱에 복사되지 않았음을 확인했다.
- 03:43:40 KST 로컬 API `/health`는 HTTP 200, user/release/admin DB 모두 ok였다.
- 이번 요청 범위는 재빌드이므로 앱 실행과 기능별 UI smoke는 새로 하지 않았다. 개발 서버·프로덕션 배포도 하지 않았다.

같은 이름 JSON에 서버 SHA·빌드 종료 코드·패키지 설정·핵심 소스 해시·health·보존 검증을, 같은 이름 log에 실제 빌드 출력을 저장했다.
