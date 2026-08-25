# 밈 오버레이 플러그인 — 최종 세션 인수인계

> 작성일: 2026-08-25
> 상태: Plan 1·2·3 구현, 자동/수동 검증, 로컬 병합 브랜치 작성까지 완료
> 현재 통합 상태: 각 원본 저장소의 `dev`는 `origin/dev`와 동일. 밈 변경은 로컬 `merge/meme-overlay-into-dev`와 `feat/meme-overlay` 브랜치에만 보존됨. 원격 push 없음.
> 기준 문서: [교차 레포 설계](./2026-08-20-meme-overlay-plugin-design.md), [Plan 1](./2026-08-20-meme-overlay-plan-1-catalog-cache.md), [Plan 2](./2026-08-20-meme-overlay-plan-2-editor-preview.md), [Plan 3](./2026-08-20-meme-overlay-plan-3-render-integration.md), [2026-08-21 checkpoint](./2026-08-21-meme-overlay-checkpoint.md)

## 1. 이 세션의 목적과 완료 범위

이 세션은 Plan 1·2가 완료된 기존 작업트리에서 Plan 3 전체를 이어서 끝냈다. 새 작업트리나 Plan 1·2 구현을 만들지 않았고, 기존 설계의 재사용 경계를 유지했다.

완료 범위는 다음과 같다.

- 기존 render job의 reserve → submit → 실패 rollback을 공용 원자 연산으로 추출하고 댓글·랭킹·베리에이션이 함께 사용하도록 이관
- Nest의 밈 렌더 요청 DTO·도메인 검증·매니페스트·RenderRecipe·Python payload 연결
- Python/FFmpeg의 VP9 알파 밈 합성 및 밈 효과음/배경 원본 소리 믹싱
- Angular의 렌더 요청, 작업 상태 UX, 프로젝트 저장, 보관함 카드, 결과 다운로드, 다시 열기·재편집
- Electron 패키징 시 밈 작업트리의 `.git` 파일이 Python 리소스에 섞이지 않도록 제외
- 독립 로컬 앱 빌드와 수동 수용 테스트: 로그인, 카탈로그, 편집, `영상 생성`, 최종 영상 생성까지 확인

작업 결과는 기능적으로 완료됐지만, 아직 애플리케이션 저장소의 원격 `dev`에는 반영되지 않았다.

## 2. 구현 설계와 실제 변경

### 2.1 재사용 원칙의 실제 적용

기존 댓글 오버레이나 공용 모듈을 복제하지 않았다.

| 공용화/재사용 지점 | 실제 구현 |
|---|---|
| 렌더 잡 예약 | Nest `VideoRenderService.reserveAndSubmit`을 추가하고 댓글·랭킹·베리에이션·밈이 호출 |
| HTTP Range 파일 응답 | Nest `core/http/range-file-response.ts`로 좁게 추출; sources와 meme asset stream이 공유 |
| 영상 소스 인제스트 | Angular `VideoSourceIngestService`를 추가; 댓글·랭킹·밈이 `SourceInspectService`/URL 조립 사본 대신 사용 |
| 미리보기 geometry | Angular `shared/media-stage/normalized-rect.ts`를 추가; 댓글의 자유 resize와 밈의 등비 resize가 공통 순수 함수 사용 |
| transport UI | Angular `MediaTransportComponent`를 추가; 댓글·랭킹·밈 미리보기가 play/pause·scrub UI를 공유 |
| 렌더 파이프라인 | Python 기존 `LocalRenderAdapter`, `VideoRenderer`, `AudioMixer`, `filter_graph`를 확장; 별도 renderer를 만들지 않음 |

### 2.2 Web API — 운영 카탈로그

- `GET /meme-assets` 및 단일 asset 조회 계약을 OpenAPI에 추가했다.
- `MemeAssetsModule`이 버전 있는 JSON 카탈로그를 읽고 검색·페이지네이션·ID/version 검증을 제공한다.
- 추적되는 운영 카탈로그 `meme-assets.catalog.json`은 `assets: []` 상태를 유지한다. 로컬 기술 테스트 밈은 운영 카탈로그에 넣지 않았다.

### 2.3 NestJS — 캐시, 렌더와 프로젝트 매니페스트

- Web API 인증 중계, CDN allowlist/HTTPS 확인, 크기/SHA-256 검증, part file → atomic rename을 갖는 디스크 캐시를 구현했다.
- 로컬 밈 card/overlay 파일을 안전한 Range endpoint로 제공한다.
- `meme_overlay` 가상 워크플로와 `POST /v1/meme-overlay/render`를 등록했다.
- 서버가 asset ID/version, 밈 source/timeline 구간, 500ms 최소 길이, 1080×1920 경계, 최대 동시 2개, z-index를 독립 검증한다.
- 매니페스트에는 source·각 meme artifact·`meme-overlay-project.v1` 편집 snapshot을 저장하며, 로컬 cache 절대 경로나 localhost URL은 editState에 저장하지 않는다.
- RenderRecipe와 Clipper payload에 optional `meme_overlays`를 추가했다. 기존 workflow payload에 해당 필드가 없으면 기존 경로를 유지한다.

### 2.4 Python — 최종 FFmpeg 렌더

- `meme_overlays.py`로 payload 정규화 모델을 추가했다.
- 알파 WebM은 `libvpx-vp9` 입력으로 읽어 source trim, timeline PTS, 크기, 퍼센트 좌표, z-index 순서에 따라 합성한다.
- 밈이 하나도 없을 때에는 새 video input/filter/audio 명령을 만들지 않는다.
- 밈 오디오가 있으면 해당 source trim, timeline delay, volume/mute를 적용해 background/source/SFX mix에 합치고 limiter를 적용한다.
- 밈 배경은 댓글과 동일하게 contain + black letterbox 규칙을 적용한다.
- 개발자용 `prepare_meme_asset.py`는 투명 VP9 WebM과 card preview를 만드는 Plan 1 범위를 유지한다.

### 2.5 Angular — 편집, 렌더 UX, 결과물과 재편집

- `meme-overlay` feature에 라이브러리, 1~2 lane 타임라인, 9:16 video layer preview, transform/settings, 페이지/store/API를 구현했다.
- 로컬 파일 및 YouTube 소스를 기존 인제스트 경로로 받아 배경 stream으로 연결한다.
- 현재 playhead에 밈을 추가하고 source trim/timeline 이동, position/등비 resize, mute/volume, z-index, 삭제를 지원한다.
- 메인 preview는 배경 video 1개와 동시에 활성인 밈 video 최대 2개를 동기화한다.
- render 요청은 milliseconds 계약으로 정규화한다. 수동 테스트에서 발견된 API 400(입력 확인 snackbar) 원인은 seconds/ms 혼용이었고, `2b279f4d fix(meme-overlay): normalize render times to milliseconds`로 수정했다.
- project manifest를 저장하고 Projects 보관함에서 밈 카드/재생/다운로드/삭제/`/meme-overlay?project=...` 재편집 라우팅을 제공한다.
- `app.config.ts`는 dev의 `shortform_director` provider를 유지한 상태에서 밈 provider를 별도 추가했다.

### 2.6 Electron — 패키징 보호

- Python 리소스 staging이 worktree `.git` 파일을 포함하지 않도록 `electron-builder.yml`에 제외 규칙과 smoke test를 추가했다.
- 밈 미디어나 로컬 테스트 카탈로그는 Electron bundle에 넣지 않는다.

## 3. 수동 실행·수용 테스트 기록

별도의 로컬 API/Nest/Angular/Electron 실행 조합으로 앱을 빌드해 검증했다. 기존 원본 레포에서 이미 사용 중이던 포트와 겹치지 않도록 별도 포트/런타임을 사용했고, 테스트 종료 후 실행한 포트와 프로세스는 정리했다.

- Google 로그인에서 `redirect_uri_mismatch`가 발생한 것은 local app runtime의 OAuth redirect 설정 문제였으며, 로컬 테스트 구성에 맞춰 조정 후 로그인 가능 상태를 확인했다.
- 첫 `영상 생성` 시 `POST /v1/meme-overlay/render`가 400을 반환하고 입력 확인 snackbar를 띄운 문제를 발견했다.
- UI가 renderer에 보내는 시간 단위를 milliseconds로 일관되게 고친 뒤 재검증했다.
- 최종적으로 실제 앱에서 밈을 얹은 영상 생성이 성공하는 것까지 확인했다.

이 수동 테스트에서 비치명적인 UX 개선 후보는 보였지만, 크리티컬 문제는 남지 않았다. 별도 후속 이슈로 정리할 때까지 기능 완료 상태로 둔다.

## 4. 커밋과 로컬 브랜치 상태

### 4.1 기능 브랜치 커밋

| 저장소 | `feat/meme-overlay` 커밋 |
|---|---|
| `web/clipper_web_api` | `eab77ea feat: add meme asset catalog API` |
| `desktop/clipper_nestjs` | `2c60b6d feat: add meme asset cache and local endpoints` → `4e09f9f feat: integrate meme overlay render workflow` |
| `desktop/clipper_python` | `4a58972 feat: add transparent meme asset authoring` → `01f9d96 feat: render meme overlays with ffmpeg` |
| `desktop/clipper_angular` | `e5528e9 feat: add meme overlay editor preview` → `f330d58 feat: persist and reopen meme overlay projects` → `2b279f4d fix(meme-overlay): normalize render times to milliseconds` |
| `desktop/clipper_electron` | `d686393 fix: exclude worktree metadata from packaged Python` |

모든 feature branch는 로컬에만 있고 원격 push하지 않았다.

### 4.2 dev 우선 병합 감사와 병합 브랜치

최신 `origin/dev`를 기준으로 각 원본 저장소에서 로컬 `merge/meme-overlay-into-dev` 브랜치를 만들고 일반 3-way merge를 수행했다. `-X ours`/`-X theirs`를 사용하지 않았으며, 자동 병합된 기존 파일 변경도 밈 범위인지 별도로 감사했다.

감사 기준은 다음과 같다.

- 최신 dev의 기존 기능 변경은 유지한다.
- 밈 기능과 무관한 feature branch 변경이 dev의 기존 UI/동작을 바꾸면 dev를 우선한다.
- 밈의 직접 의존성인 좁은 공용화만 함께 수용한다.

발생한 충돌과 해소 결과:

| 저장소 | 파일 | dev 우선 해소 |
|---|---|---|
| Web API | `src/app.module.ts` | dev의 4개 Shortform Director module을 유지하고 `MemeAssetsModule`만 추가 |
| NestJS | `src/app.module.ts` | dev의 `ShortformDirectorModule`을 유지하고 `MemeAssetsModule`·`MemeOverlayRenderModule` 추가 |
| Angular | `src/app/app.config.ts` | dev의 Shortform Director pipeline provider를 유지하고 밈 provider를 별도 추가 |
| Angular | `src/core/navigation/app-navigation-metadata.spec.ts` | dev의 `shellPageIcon` import와 밈의 `PLUGIN_FEATURE_ORDER` import를 함께 유지 |
| Angular | `ranking-preview.component.spec.ts` | dev의 template background 회귀 테스트와 밈 공용 transport seek 테스트를 모두 보존 |

자동 병합된 기존 feature 변경도 검토했다. 댓글/랭킹의 source ingest, preview transport, geometry, Nest reserve-submit, Range response는 밈의 중복 방지 목적의 공용화이며 기존 기능의 동작 변경을 만들지 않는 것을 테스트로 확인했다. 밈과 무관한 버튼 색상·기능 정책 변경은 발견되지 않았다.

병합 브랜치의 최종 커밋은 다음과 같다.

| 저장소 | 로컬 브랜치 | 병합 커밋 |
|---|---|---|
| `web/clipper_web_api` | `merge/meme-overlay-into-dev` | `5e50065 Merge branch 'feat/meme-overlay' into merge/meme-overlay-into-dev` |
| `desktop/clipper_nestjs` | `merge/meme-overlay-into-dev` | `8e08828 Merge branch 'feat/meme-overlay' into merge/meme-overlay-into-dev` |
| `desktop/clipper_python` | `merge/meme-overlay-into-dev` | `f8274ac Merge branch 'feat/meme-overlay' into merge/meme-overlay-into-dev` |
| `desktop/clipper_angular` | `merge/meme-overlay-into-dev` | `6ce7deaa Merge branch 'feat/meme-overlay' into merge/meme-overlay-into-dev` |
| `desktop/clipper_electron` | `merge/meme-overlay-into-dev` | `3a2b16a Merge branch 'feat/meme-overlay' into merge/meme-overlay-into-dev` |

한때 이 병합 브랜치를 로컬 `dev`에 fast-forward했으나, 사용자의 지시에 따라 이후 각 `dev`를 정확히 `origin/dev`로 되돌렸다. 따라서 현재 `dev`에는 밈 변경이 없고, 위 merge branch만 통합 후보로 남아 있다. 이 작업 역시 원격에는 push하지 않았다.

## 5. 현재 작업트리·보존 상태

- 다섯 개의 `.worktrees/*-meme-overlay` worktree는 깨끗한 상태를 확인한 뒤 제거했다.
- 제거한 worktree의 `feat/meme-overlay` 브랜치는 모두 유지했다.
- 다섯 `merge/meme-overlay-into-dev` 브랜치도 모두 유지했다.
- 원본 저장소의 `dev`는 모두 clean이며 `origin/dev`와 일치한다.
- Angular의 기존 `package-lock.json` 변경은 밈 범위 밖이었다. 사용자 요청에 따라 worktree에서 버렸고 feature/merge branch 및 커밋에 포함하지 않았다.
- `clipper_docs`는 수정하지 않았다.
- `.codex`는 별도 Git 저장소다. 이 문서 외 다른 세션의 Toss/정책 문서를 수정하거나 스테이징하지 않는다.

## 6. 최종 검증

병합 충돌을 해소한 뒤 merge branch 기준으로 아래 검증을 실행했다.

| 저장소 | 검증 | 결과 |
|---|---|---|
| Web API | `npm run build`; 밈 asset Jest focused suite | build 통과, 4 suites / 19 tests 통과 |
| NestJS | `npm run build`; 밈·공용 render/Range/source focused `node --test` | build 통과, 125 tests 통과 |
| Python | Plan 3 밈 audio/model/overlay/authoring/contract/letterbox/source-audio pytest | 67 passed |
| Angular | Node `v22.22.3`의 `npm run build:local`; 밈·공용화 영향 Angular test | build 통과, Chrome 664 / 664 SUCCESS |
| Electron | `npm run build && npm test` | build 통과, 329 tests 통과 |

Web API와 Nest HTTP integration test는 제한된 sandbox에서 ephemeral listen 권한 때문에 처음 `EPERM`이 났다. 코드 실패가 아니며, 허용된 로컬 환경에서 다시 실행해 모두 통과했다.

Nest 전체 회귀에는 밈 이전부터 있던 `shortform-clip-generation-events` fixture/생성자 불일치 1건이 알려져 있다. 이번에는 밈 관련 focused suite와 build가 통과했고, 이 기존 실패를 고치거나 포함하지 않았다.

## 7. 로컬 테스트 자산·운영 분리

다음 경로의 로컬 카탈로그와 테스트 밈은 보존해야 한다.

```text
/Users/jina/Library/Application Support/Clipper Studio/meme-assets/
```

- `hitting-cat/v1`, `crunchy-cat/v1`, `angry-cat/v1`의 `card-preview.webm`, `overlay.webm`, cache metadata
- local catalog JSON

이는 기술 검증용 로컬 자산이며 Git 추적/앱 bundle/운영 카탈로그에 포함하지 않는다. 권리 승인과 CDN 게시가 별도 완료되기 전에는 운영 `meme-assets.catalog.json`에 추가하면 안 된다.

## 8. 다음 통합 작업자에게

1. 통합할 저장소에서 해당 `merge/meme-overlay-into-dev`를 기준으로 다시 최신 `origin/dev`와 차이를 확인한다. 현재 문서의 병합 commit은 로컬 branch에만 있다.
2. dev가 새로 전진했다면, 새 dev에서 새 merge branch를 만들고 이 문서의 dev 우선 기준으로 다시 merge/audit한다. 기존 merge branch를 무조건 fast-forward하지 않는다.
3. conflict가 발생하면 dev의 독립 기능을 먼저 보존하고 밈 관련 등록·좁은 공용화만 추가한다. 자동 병합된 기존 파일도 범위를 검사한다.
4. 현재와 같은 focused 검증을 다시 통과시킨 뒤에만 로컬 dev 또는 원격 통합 여부를 결정한다.
5. 통합/PR 전에는 feature branch와 merge branch를 push할지 사용자의 명시적 승인을 받는다.

## 9. 문서 변경 원칙

이 문서는 2026-08-25 세션 전용 기록이다. 후속 세션은 이 파일을 live scratchpad로 공유 편집하지 말고, 새 날짜/목적 파일을 만들거나 명시적 상태 변경이 있을 때만 짧은 후속 기록을 추가한다. `.codex`에서 `git add .`은 사용하지 말고 밈 문서의 정확한 경로만 stage한다.
