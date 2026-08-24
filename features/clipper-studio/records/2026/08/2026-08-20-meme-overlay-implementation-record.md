# 밈 오버레이 구현 기록

> 설계일: 2026-08-20
> 구현 완료: 2026-08-24
> 상태: Plan 1·2·3 완료, 검증 완료, push·merge 전
> 기준 설계: [밈 오버레이 플러그인 설계](../../../../../design/2026-08-20-meme-overlay-plugin-design.md)

## 1. 결과

밈 오버레이 MVP의 카탈로그·로컬 캐시, Angular 편집기와 실시간 프리뷰, Nest 렌더 제출과 프로젝트 매니페스트, Python FFmpeg 영상·오디오 합성, 보관함 저장·다시 열기·재편집을 구현했다.

기존 댓글 오버레이와 영상 랭킹의 공용 source ingest, Range 응답, project manifest, RenderRecipe, payload mapper, 작업 큐를 재사용했다. 렌더 예약·제출·실패 rollback은 `VideoRenderService.reserveAndSubmit` 한 곳으로 모았고 댓글·랭킹·베리에이션도 이 경계를 사용한다.

## 2. 레포별 커밋

- `clipper_web_api`: `eab77ea1b56b7762d956567b99662cb771f1905f` — Plan 1 카탈로그 API
- `clipper_nestjs`: `2c60b6d` — Plan 1 캐시·로컬 API, `4e09f9f4e7bccf6c85cca35e6740f0ea8f6353ff` — Plan 3 렌더·매니페스트·공용 제출 경계
- `clipper_python`: `4a58972` — Plan 1 투명 밈 제작 도구, `01f9d961cb235146ed147e515311905ab8113078` — Plan 3 FFmpeg 영상·오디오 합성
- `clipper_angular`: `e5528e9` — Plan 2 편집기·프리뷰, `f330d588c75a56d16b83b9e2a57665a5d3cdc627` — Plan 3 제출·영속화·재편집
- `clipper_electron`: `d686393` — worktree `.git` metadata가 Python 패키지 리소스에 포함되지 않도록 보강

모든 커밋은 `feat/meme-overlay` 작업트리에만 있고 push·merge하지 않았다.

## 3. 최종 런타임 계약

### 카탈로그와 캐시

- Web API: `GET /meme-assets`, `GET /meme-assets/:assetId?version=...`
- 로컬 준비/스트림: `/v1/meme-overlay/catalog`, `/v1/meme-overlay/assets/:assetId/prepare`, `/v1/meme-overlay/assets/:assetId/stream`
- 캐시 키: `assetId/version/variant`, variant는 `card` 또는 `overlay`
- 원격/저장 metadata 모두 요청한 asset ID와 version이 정확히 일치해야 캐시에 들어간다.
- HTTPS, 명시 CDN host allowlist, byte limit, SHA-256을 모두 통과한 파일만 atomic rename으로 확정한다.

### 렌더와 프로젝트

- 제출: `POST /v1/meme-overlay/render`
- 출력: `output.meme_overlay.render.main` → `renders/meme_overlay.mp4`
- payload: `meme_overlays[]`에 media URL, source/timeline 구간, 1080×1920 기준 normalized transform, audio, z-index를 전달한다.
- Python은 배경 체인을 만든 뒤 투명 VP9 밈을 z-order대로 합성하고, 배경 원본 오디오와 음소거되지 않은 밈 오디오를 `amix normalize=0`과 limiter로 합친다.
- `meme_overlays`가 없으면 기존 FFmpeg command path와 receipt 형태를 유지한다.
- 편집 스키마 `meme-overlay-project.v1`은 source path/label/duration/dimensions와 instance ID, asset ID/version/name, source/timeline 구간, transform, audio, z-index만 저장한다.
- 보관함의 밈 카드 편집 링크는 `/meme-overlay?project=<projectId>`이며, 다시 열 때 source를 복원하고 고유 asset ID/version만 준비한다.

## 4. 운영 설정

| 설정 | 기본값/의미 |
|---|---|
| `MEME_ASSET_CDN_HOSTS` | 기본값 없음. HTTPS URL의 정확한 `host[:port]` 쉼표 목록. 운영 카탈로그 CDN을 반드시 명시한다. |
| `MEME_ASSET_DOWNLOAD_CONCURRENCY` | `3` |
| `MEME_ASSET_DOWNLOAD_TIMEOUT_MS` | `60000` |
| `MEME_ASSET_MAX_CARD_BYTES` | `2097152` (2 MiB) |
| `MEME_ASSET_MAX_OVERLAY_BYTES` | `33554432` (32 MiB) |

로컬 검증용 3개 밈은 운영 카탈로그에 넣지 않았다. 앱 패키지에도 card/overlay WebM을 포함하지 않는다.

## 5. 자동 검증

- NestJS focused 회귀: 코드 리뷰 보완 테스트 28/28 통과
- NestJS 전체: 991/991 통과
- NestJS TypeScript build와 `ncc` bundle 통과
- Python 전체: 489 통과, 환경 의존 5 skip
- Python Ruff 전체 대상 통과, 신규 `meme_overlays.py` mypy 통과
- Python packaged worker smoke: `clipper_video_render` 1 통과
- Angular focused 회귀: 28/28 통과
- Angular 전체: 2776/2776 통과
- Angular SCSS class 검증: 6/6 통과
- Angular production/packaged build 통과
- Electron 테스트: 211/211 통과, TypeScript 검사 통과
- 전 레포 `git diff --check` 통과

Python 전체 mypy에는 밈 변경과 무관한 기존 12개 파일의 오류 31건이 남아 있다. 신규 밈 모듈의 targeted mypy는 오류가 없다.

## 6. 실제 렌더·재편집 E2E

- 8초 360×640 H.264/AAC 배경과 두 밈 인스턴스로 실제 Nest → Python 렌더를 실행했다.
- 결과는 8초 1080×1920 H.264, stereo AAC MP4였고 receipt에서 배경 오디오, 밈 오디오 1개, 오버레이 2개를 확인했다. muted 인스턴스는 오디오에 들어가지 않았다.
- 같은 시각의 Angular `<video>` CSS 프리뷰와 MP4 추출 프레임은 SSIM `0.981479`, PSNR `36.847 dB`였다.
- 카드 Range는 206/100 bytes, 결과물 Range는 206/1024 bytes로 확인했다.
- 첫 overlay 준비는 cache miss, 두 번째는 cache hit였고 fixture 서버에는 overlay GET이 정확히 한 번 들어왔다.
- overlay 캐시를 비운 offline 재편집은 `503 meme_asset_network_required`, online retry는 정확한 `angry-cat@v1`과 SHA-256을 다시 받았다.
- 저장된 source와 두 instance의 timing, transform, audio, z-index를 다시 열어 동일하게 복원했다.

## 7. 패키지 smoke

- macOS arm64 unpacked 앱을 빌드하고 패키지 리소스에 Angular renderer, Nest bundle, Python worker가 포함된 것을 확인했다.
- 패키지 안에는 `card-preview.webm`, `overlay.webm`, Python worktree `.git` metadata가 없었다.
- 격리한 packaged userData에서 앱을 실행해 bundled Nest → Electron plugin host → packaged Python worker 렌더를 완료했다.
- 패키지 결과물 Range 206/512 bytes와 packaged font/resource 경로를 확인했다.
- 격리 userData에는 사용자 설치 도구인 FFmpeg가 없어서 첫 시도가 실패했고, 시스템 FFmpeg를 격리 경로에 연결한 뒤 정상 완료했다. 제품의 기존 사용자 도구 준비 정책은 변경하지 않았다.

## 8. 보존 확인

- `/Users/jina/Library/Application Support/Clipper Studio/meme-assets/`의 로컬 카탈로그와 테스트 밈 3개는 삭제·수정하지 않았다.
- 운영 카탈로그에 로컬 테스트 밈을 추가하지 않았다.
- Angular의 기존 `package-lock.json` 변경은 스테이징·커밋하지 않고 그대로 남겼다.
- Web API에는 Plan 3 추가 변경이 없고, Electron에는 Python worktree metadata 제외 보강만 있다.
- `clipper_docs`는 수정하지 않았다.
