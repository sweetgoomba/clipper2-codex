# 밈 오버레이 구현 계획 1/3 — 카탈로그·디스크 캐시

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** 권리 승인된 밈 메타데이터를 Web API에서 페이지 단위로 제공하고, 로컬 Nest가 카드/오버레이 WebM을 무결성 검증 후 디스크에 캐시하여 localhost Range URL로 제공한다.

**Architecture:** Web API는 버전 관리 JSON을 읽고 검색·페이지네이션만 수행한다. 미디어 바이트는 CDN에서 직접 내려받는다. 로컬 Nest는 인증 토큰을 중계해 카탈로그를 받고, 파일은 part 파일로 스트리밍 다운로드한 뒤 size+SHA-256 검증과 atomic rename을 거쳐 CLIPPER_DATA_DIR에 보존한다. 기존 SourcesController의 Range 구현은 공용 helper로 추출하여 소스 스트림과 밈 스트림이 같은 코드를 직접 호출한다.

**Tech Stack:** NestJS 11, TypeScript, Jest, node:test, Node fetch/streams, FFmpeg, VP9 WebM

**Spec:** [밈 오버레이 플러그인 교차 레포 설계](./2026-08-20-meme-overlay-plugin-design.md) §5, §10, §11, §14

## Global Constraints

- 밈 미디어 파일은 Electron/Angular/Nest 배포 산출물에 포함하지 않는다.
- Web API 응답에는 CDN URL·size·SHA-256만 포함하고 파일 바이트를 프록시하지 않는다.
- 운영 카탈로그에는 rights.status가 approved인 항목만 노출한다. 제공된 Angry cat 파일은 기술 검증용이며 권리 승인 전 운영 JSON에 넣지 않는다.
- 로컬 캐시는 RAM 캐시가 아니라 CLIPPER_DATA_DIR/meme-assets 아래 디스크 캐시다.
- 다운로드는 전체 Buffer 적재 없이 스트림으로 기록한다.
- HTTPS와 MEME_ASSET_CDN_HOSTS allowlist를 모두 통과한 URL만 다운로드한다.
- 기존 SourcesController의 Range 수식·응답 코드를 복사하지 않는다. 공용 helper를 양쪽 controller가 호출한다.
- 플러그인 설치는 기존 InstalledVirtualWorkflowsRepository를 그대로 사용하며 별도 설치 저장소를 만들지 않는다.
- TDD 순서는 실패 테스트 → 최소 구현 → 대상 테스트 → 레포 전체 회귀다.
- 아래 checkpoint는 커밋 경계 제안일 뿐이다. 사용자가 명시적으로 요청하기 전에는 commit/push하지 않는다.

## 변경 레포

| 순서 | 레포 | 책임 |
|---|---|---|
| 1 | web/clipper_web_api | OpenAPI, 카탈로그 JSON/조회 API |
| 2 | desktop/clipper_nestjs | 플러그인 등록, Web API 중계, 다운로드·캐시·Range |
| 3 | desktop/clipper_python | 개발자용 WebM 전처리 스크립트와 검증 테스트 |
| 4 | desktop/clipper_electron | 번들에 밈 파일이 들어가지 않는지 smoke check만 |

---

## Task 1: API 계약을 OpenAPI에 먼저 고정

**Files**

- Modify: web/clipper_web_api/docs/api/openapi.yaml

**Produces**

- GET /meme-assets?page=1&limit=12&q=
- GET /meme-assets/{assetId}?version=v1
- MemeAssetFile, MemeAsset, MemeAssetPage schemas

- [ ] **Step 1: schemas를 추가한다.**

~~~yaml
MemeAssetFile:
  type: object
  required: [url, mimeType, sizeBytes, sha256]
  properties:
    url: { type: string, format: uri }
    mimeType: { type: string, const: video/webm }
    sizeBytes: { type: integer, minimum: 1 }
    sha256: { type: string, pattern: '^[a-f0-9]{64}$' }

MemeAsset:
  type: object
  required: [id, version, name, tags, durationMs, width, height, hasAudio, cardPreview, overlay]
  properties:
    id: { type: string, pattern: '^[a-z0-9][a-z0-9-]{1,63}$' }
    version: { type: string, pattern: '^v[1-9][0-9]*$' }
    name: { type: string }
    tags: { type: array, items: { type: string } }
    durationMs: { type: integer, minimum: 1 }
    width: { type: integer, minimum: 1 }
    height: { type: integer, minimum: 1 }
    hasAudio: { type: boolean }
    cardPreview: { $ref: '#/components/schemas/MemeAssetFile' }
    overlay: { $ref: '#/components/schemas/MemeAssetFile' }
~~~

- [ ] **Step 2: 두 path를 bearerAuth로 보호하고 page 기본값 1, limit 기본값/최댓값 12로 명시한다.**
- [ ] **Step 3: 문서 정합성을 확인한다.**

Run: npm run build

Working directory: web/clipper_web_api

Expected: exit 0. OpenAPI 편집은 컴파일 대상이 아니므로 뒤의 controller 테스트가 실제 계약을 검증한다.

## Task 2: Web API의 정적 카탈로그 저장소

**Files**

- Create: web/clipper_web_api/src/modules/meme-assets/domain/meme-asset.model.ts
- Create: web/clipper_web_api/src/modules/meme-assets/infrastructure/meme-assets.catalog.json
- Create: web/clipper_web_api/src/modules/meme-assets/infrastructure/json-meme-assets.repository.ts
- Create: web/clipper_web_api/src/modules/meme-assets/infrastructure/json-meme-assets.repository.spec.ts
- Modify: web/clipper_web_api/nest-cli.json

**Produces**

~~~ts
export type MemeAssetRightsStatus = 'approved' | 'pending' | 'rejected';

export interface StoredMemeAsset extends MemeAsset {
  rights: {
    status: MemeAssetRightsStatus;
    source: string;
    checkedAt?: string;
  };
  visible: boolean;
}

export abstract class MemeAssetsRepository {
  abstract list(input: { page: number; limit: number; q?: string }): MemeAssetPage;
  abstract find(id: string, version?: string): MemeAsset | null;
}
~~~

- [ ] **Step 1: repository spec를 작성한다.**

Test cases:

- approved+visible만 목록에 노출
- pending/rejected/hidden 제외
- 이름·태그에 대해 대소문자 무시 검색
- page/limit과 total/hasNext 계산
- find(id, version)는 숨겨진 구버전도 반환하지만 rights approved가 아니면 반환하지 않음
- 응답 객체에 rights/source 내부 필드가 없음

- [ ] **Step 2: 실패를 확인한다.**

Run: npm test -- --runInBand src/modules/meme-assets/infrastructure/json-meme-assets.repository.spec.ts

Expected: FAIL — module not found.

- [ ] **Step 3: JSON import와 repository를 구현한다.**

운영 JSON의 스키마 버전은 meme-asset-catalog.v1로 고정한다. 코드 저장소에는 권리 검증이 끝난 메타데이터만 추가한다. 테스트 fixture는 spec 내부에 주입하고 운영 JSON과 섞지 않는다.

- [ ] **Step 4: nest-cli.json assets에 modules/meme-assets/infrastructure/*.json을 등록한다. build 뒤 dist에도 catalog JSON이 있어야 한다.**

- [ ] **Step 5: 대상 테스트를 통과시킨다.**

Expected: PASS.

- [ ] **Checkpoint:** Web API catalog domain/repository review.

## Task 3: Web API 조회 controller

**Files**

- Create: web/clipper_web_api/src/modules/meme-assets/application/meme-assets.service.ts
- Create: web/clipper_web_api/src/modules/meme-assets/presentation/dto/list-meme-assets-query.dto.ts
- Create: web/clipper_web_api/src/modules/meme-assets/presentation/dto/get-meme-asset-query.dto.ts
- Create: web/clipper_web_api/src/modules/meme-assets/presentation/meme-assets.controller.ts
- Create: web/clipper_web_api/src/modules/meme-assets/presentation/meme-assets.controller.spec.ts
- Create: web/clipper_web_api/src/modules/meme-assets/meme-assets.module.ts
- Modify: web/clipper_web_api/src/app.module.ts

**Consumes:** MemeAssetsRepository

- [ ] **Step 1: controller spec를 작성한다.**

Assertions:

- controller class에 JwtAuthGuard가 적용됨
- ValidationPipe whitelist+transform가 적용됨
- page=0, limit=13은 validation error
- GET list가 service.list를 정확한 숫자 인자로 호출
- 없는 asset/version은 404
- malformed assetId/version은 실제 HTTP 400이며 repository lookup 전에 거부

- [ ] **Step 2: 실패를 확인한다.**

Run: npm test -- --runInBand src/modules/meme-assets/presentation/meme-assets.controller.spec.ts

Expected: FAIL — controller/module missing.

- [ ] **Step 3: DTO와 controller를 구현한다.**

~~~ts
@Controller('meme-assets')
@UseGuards(JwtAuthGuard)
@UsePipes(new ValidationPipe({ whitelist: true, transform: true }))
export class MemeAssetsController {
  @Get()
  list(@Query() query: ListMemeAssetsQueryDto): MemeAssetPage;

  @Get(':assetId')
  get(@Param('assetId') assetId: string, @Query() query: GetMemeAssetQueryDto): MemeAsset;
}
~~~

- [ ] **Step 4: module을 AppModule에 등록한다.**
- [ ] **Step 5: 대상 테스트와 전체 Web API 회귀를 실행한다.**

Run:

~~~sh
npm test -- --runInBand src/modules/meme-assets
npm test -- --runInBand
npm run build
~~~

Expected: all PASS, build exit 0.

- [ ] **Checkpoint:** Web API contract complete.

## Task 4: 개발자용 에셋 전처리 도구

**Files**

- Create: desktop/clipper_python/scripts/prepare_meme_asset.py
- Create: desktop/clipper_python/tests/test_prepare_meme_asset.py
- Modify: desktop/clipper_python/.gitignore

**Input used for manual verification**

- /Users/jina/Downloads/Angry cat green screen 1.mp4

**Produces outside git**

~~~text
.local/meme-assets/<asset-id>/<version>/
  card-preview.webm
  overlay.webm
  catalog-entry.json
~~~

- [ ] **Step 1: command-builder unit tests를 쓴다.**

Assertions:

- overlay command uses chromakey, format=yuva420p, libvpx-vp9, auto-alt-ref=0, Opus audio
- card command uses no audio and scales the short edge to at most 240px
- catalog entry contains actual byte size, lowercase SHA-256, ffprobe duration/width/height/hasAudio
- output directory exists 오류 대신 명시적 overwrite flag가 필요

- [ ] **Step 2: 실패를 확인한다.**

Run: uv run pytest tests/test_prepare_meme_asset.py -q

Expected: FAIL — script module missing.

- [ ] **Step 3: subprocess argument array만 만드는 순수 함수와 실행 경계를 나눠 구현한다.**

CLI:

~~~sh
uv run python scripts/prepare_meme_asset.py \
  --input "/Users/jina/Downloads/Angry cat green screen 1.mp4" \
  --asset-id angry-cat \
  --version v1 \
  --name "Angry cat" \
  --tag cat --tag angry --tag 화남 \
  --output .local/meme-assets
~~~

초기 chroma key 기본값은 0x00FF00, similarity 0.18, blend 0.08로 두고 CLI에서 조정 가능하게 한다. 실제 샘플 가장자리 확인 후 값만 조정할 수 있으며 런타임 계약은 변하지 않는다.

- [ ] **Step 4: unit test를 통과시킨다.**
- [ ] **Step 5: 제공 샘플로 수동 생성하고 ffprobe로 alpha/audio를 확인한다.**

Expected:

- card-preview.webm: VP9 alpha, no audio
- overlay.webm: VP9 alpha, Opus audio가 원본에 있을 때 유지
- 두 파일 모두 git untracked 목록에 나타나지 않음

- [ ] **Checkpoint:** authoring tool review. 생성된 미디어는 운영 권리 승인 및 CDN 업로드 전까지 로컬에만 둔다.

## Task 5: 공용 Range 파일 응답 추출

**Files**

- Create: desktop/clipper_nestjs/src/core/http/range-file-response.ts
- Create: desktop/clipper_nestjs/test/range-file-response.test.js
- Modify: desktop/clipper_nestjs/src/modules/sources/presentation/sources.controller.ts
- Modify: desktop/clipper_nestjs/test/sources-controller.test.js
- Modify: desktop/clipper_nestjs/test/sources-stream.test.js

**Produces**

~~~ts
export interface RangeFileDescriptor {
  absolutePath: string;
  size: number;
  contentType: string;
}

export function resolveByteRange(
  rangeHeader: string | undefined,
  size: number,
): ResolvedByteRange | null;

export function streamRangeFile(
  file: RangeFileDescriptor,
  request: IncomingMessage,
  response: ServerResponse,
): void;
~~~

- [ ] **Step 1: 현재 sources Range 동작을 characterization test로 고정한다.**

Cases: full 200, explicit/open/suffix 206, malformed/unsatisfiable 416, zero-byte 200, stream error 500, client close destroys stream.

- [ ] **Step 2: 현재 테스트가 PASS인지 확인한다.**

Run: npm run build && node --test test/sources-controller.test.js test/sources-stream.test.js

- [ ] **Step 3: helper test를 먼저 추가하고 sources controller가 helper 호출을 기대하도록 바꾼다.**
- [ ] **Step 4: controller 안의 resolveByteRange와 stream response 코드를 공용 파일로 이동한다. 복사본을 남기지 않는다.**
- [ ] **Step 5: 대상 테스트를 통과시킨다.**

Expected: 기존 source stream 응답 계약이 byte-for-byte 같은 header/status 의미를 유지한다.

- [ ] **Checkpoint:** shared Range seam review.

## Task 6: 로컬 카탈로그 client와 디스크 캐시

**Files**

- Create: desktop/clipper_nestjs/src/modules/meme-assets/domain/meme-asset.model.ts
- Create: desktop/clipper_nestjs/src/modules/meme-assets/application/meme-catalog.service.ts
- Create: desktop/clipper_nestjs/src/modules/meme-assets/application/meme-asset-cache.service.ts
- Create: desktop/clipper_nestjs/src/modules/meme-assets/infrastructure/meme-catalog-cache.repository.ts
- Create: desktop/clipper_nestjs/src/modules/meme-assets/infrastructure/meme-asset-downloader.ts
- Create: desktop/clipper_nestjs/test/meme-catalog-service.test.js
- Create: desktop/clipper_nestjs/test/meme-asset-cache.test.js

**Cache key**

~~~text
<assetId>/<version>/<variant>
variant = card | overlay
~~~

**Public application API**

~~~ts
prepareCatalogPage(
  query: { page: number; limit: number; q?: string },
  auth: AuthContext,
): Promise<LocalMemeAssetPage>;

prepareOverlay(
  assetId: string,
  version: string,
  auth: AuthContext,
): Promise<PreparedMemeOverlay>;

resolveCachedFile(
  assetId: string,
  version: string,
  variant: 'card' | 'overlay',
): Promise<RangeFileDescriptor>;
~~~

- [ ] **Step 1: catalog service 실패 테스트를 쓴다.**

Assertions:

- accessToken을 WebApiClient.getJson에 전달
- 첫 페이지 item의 card variant를 concurrency 3으로 준비
- 모든 card 준비 시도를 끝내고 원래 순서를 유지하며, ready 항목은 cardStreamPath, failed 항목은 stable cardErrorCode를 반환
- 일부 card만 실패하면 페이지를 유지하고, 비어 있지 않은 페이지에서 ready가 0개일 때만 meme_catalog_unavailable
- catalog-cache.json은 성공한 원격 응답 뒤에만 atomic replace
- 원격 실패 시 저장된 metadata+검증된 card 파일만 반환
- 원격/로컬 둘 다 없으면 meme_catalog_unavailable
- overlay prepare의 Web API unreachable/timeout 시 저장 metadata+검증된 overlay만 다운로드 없이 cacheHit=true로 재사용

- [ ] **Step 2: asset cache 실패 테스트를 쓴다.**

Assertions:

- HTTPS가 아니거나 allowlist 밖 host 거부
- allowlist는 exact HTTPS authority이며 비기본 port는 명시 항목만 허용, credentials 거부, signed query 허용
- header/body 전체가 MEME_ASSET_DOWNLOAD_TIMEOUT_MS를 넘으면 abort하고 cache/in-flight 상태 정리
- Content-Length가 선언 크기보다 크면 중단
- 수신 byte count/sha256 mismatch면 part 삭제, 최종 파일 없음
- 성공 시 part에서 최종 경로로 rename
- 같은 key 동시 요청은 fetch 1회
- 유효한 기존 파일은 fetch 없이 cacheHit=true
- 파일을 readFile Buffer로 읽지 않고 pipeline로 기록

- [ ] **Step 3: 실패를 확인한다.**

Run:

~~~sh
npm run build
node --test test/meme-catalog-service.test.js test/meme-asset-cache.test.js
~~~

Expected: FAIL — modules missing.

- [ ] **Step 4: downloader/cache/repository/service 순으로 최소 구현한다.**

Config:

- MEME_ASSET_CDN_HOSTS: comma-separated exact host allowlist
- MEME_ASSET_DOWNLOAD_CONCURRENCY: default 3
- MEME_ASSET_DOWNLOAD_TIMEOUT_MS: default 60000
- MEME_ASSET_MAX_CARD_BYTES: default 2 MiB
- MEME_ASSET_MAX_OVERLAY_BYTES: default 32 MiB

Path segments는 정규식으로 검증하고 외부 입력을 join에 그대로 넣지 않는다. metadata.json도 최종 파일과 같은 검증 결과를 기록한다.

- [ ] **Step 5: 대상 테스트를 통과시킨다.**
- [ ] **Checkpoint:** cache/download integrity review.

## Task 7: 로컬 API와 가상 플러그인 등록

**Files**

- Create: desktop/clipper_nestjs/src/modules/meme-assets/presentation/dto/meme-assets.dto.ts
- Create: desktop/clipper_nestjs/src/modules/meme-assets/presentation/meme-assets.controller.ts
- Create: desktop/clipper_nestjs/src/modules/meme-assets/meme-assets.module.ts
- Create: desktop/clipper_nestjs/test/meme-assets-controller.test.js
- Modify: desktop/clipper_nestjs/src/app.module.ts
- Modify: desktop/clipper_nestjs/src/modules/plugins/domain/plugin-catalog.ts
- Modify: desktop/clipper_nestjs/test/plugin-catalog.test.js
- Modify: desktop/clipper_nestjs/test/installed-virtual-workflows-repository.test.js

**Endpoints**

- GET /meme-overlay/catalog
- POST /meme-overlay/assets/:assetId/prepare
- GET /meme-overlay/assets/:assetId/stream

- [ ] **Step 1: controller와 plugin catalog 실패 테스트를 작성한다.**

Assertions:

- catalog/prepare는 AuthContextService로 인증하고 application service에 auth 전달
- stream은 캐시 파일만 열며 외부 URL을 받지 않음
- stream은 공용 streamRangeFile helper 호출
- invalid id/version/variant는 400
- meme_overlay는 runtimeKind virtual_workflow, installGated true
- provides는 workflow.meme_overlay, requires는 project.manifest
- 설치/제거가 기존 JSON 저장소에서 왕복

- [ ] **Step 2: 실패를 확인한다.**
- [ ] **Step 3: DTO/controller/module/catalog 항목을 구현한다.**
- [ ] **Step 4: 대상 테스트와 전체 Nest 회귀를 실행한다.**

Run:

~~~sh
npm run build
node --test test/meme-*.test.js test/range-file-response.test.js test/plugin-catalog.test.js test/installed-virtual-workflows-repository.test.js
node --test test/*.test.js
~~~

Expected: all PASS.

## Task 8: 패키징·수동 API 검증

**Files**

- No production code expected in desktop/clipper_electron

- [ ] Web API를 test catalog fixture와 함께 띄우고 GET /meme-assets 인증/페이지 응답을 확인한다.
- [ ] 로컬 Nest GET /meme-overlay/catalog 첫 호출에서 card 파일이 디스크에 생기고 spinner 소비에 필요한 응답이 완료 뒤 반환되는지 확인한다.
- [ ] 같은 호출의 두 번째 요청이 네트워크 없이 cache hit인지 확인한다.
- [ ] Range bytes=0-99가 206, 올바른 Content-Range/Length인지 확인한다.
- [ ] overlay prepare 전에는 overlay 파일이 없고, POST prepare 뒤에만 생성되는지 확인한다.
- [ ] npm run bundle 후 dist/bundled 안에 card-preview.webm/overlay.webm이 없는지 확인한다.
- [ ] Electron package 파일 목록에도 밈 미디어가 없는지 확인한다.

## Plan 1 완료 기준

- Web API가 승인된 메타데이터만 페이지/검색/버전 조회한다.
- 로컬 Nest가 첫 페이지 card만 선준비하고 overlay는 선택할 때만 다운로드한다.
- 파일은 디스크 캐시되며 size+SHA-256을 통과한 것만 stream된다.
- 배경 source와 meme stream이 동일 Range helper를 직접 호출한다.
- meme_overlay 설치 상태가 기존 가상 플러그인 저장소에서 관리된다.
- Electron 설치 파일 크기는 밈 카탈로그 수와 무관하다.
- Plan 2가 LocalMemeAssetPage와 PreparedMemeOverlay 계약만 소비하면 된다.
