# AI 숏폼 디렉터 — 프로젝트 artifact 연결 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_DESIGN_2026-07-16.md`

## 목적

`AssetPack` foundation은 어떤 visual layer에 실제 에셋이 부족한지 계산하지만, 사용자가 이미 만든 프로젝트의 로컬 원본·보유 에셋을 연결할 방법은 아직 없다. 이번 단계는 provider나 renderer를 고르기 전에 다음 흐름을 완성한다.

```text
사용자 소유 ProjectManifest
  ├─ source.image / source.video
  └─ local-user media.image / media.video
                 ↓ 소유권·종류·파일 존재 검증
      sanitized asset candidates
                 ↓ 사용 권리 확인
        layer ↔ AssetRef binding
                 ↓
        AssetPack readiness 재계산
```

기존 `shortform_prompt` API, 데이터 모델, UI와 렌더 흐름은 변경하지 않는다. 새 기능은 `shortform_director` 전용 API와 UI 안에서만 동작한다.

## 감사 결과와 식별자

기존 `ProjectManifest`의 `artifact.id`는 전역 식별자가 아니라 `manifest.projectId` 안에서만 유일하다. 따라서 저장할 안정 식별자는 단일 `artifactId`가 아니라 다음 locator다.

```ts
interface ProjectArtifactLocatorV1 {
  kind: 'project-artifact';
  projectId: string;
  artifactId: string;
}
```

`AssetRef`에는 URL이나 로컬 경로를 복사하지 않는다. 프로젝트가 저장하는 것은 locator와 표시용 label, origin, media kind, provenance, 권리·가용성 snapshot뿐이다.

## 이번 단계에서 허용하는 후보

후보는 현재 인증 사용자가 소유한 기존 completed project의 `ProjectManifest`에서만 찾는다.

| origin | 허용 artifact | 추가 조건 |
|---|---|---|
| `source` | `source.image`, `source.video` | 로컬 `source-file` 또는 `project-file`이며 실제 파일이 존재 |
| `owned` | `media.image`, `media.video` | provider가 `media.local_user.file` 또는 `media.local_user.file_path`이고 실제 로컬 파일이 존재 |

다음 항목은 이번 단계에서 제외한다.

- `remote-url`
- 검색 provider 결과
- 생성 이미지·영상
- `render.video`, `render.thumbnail`
- audio, text, transcript, template, recipe
- 파일 존재를 로컬에서 검증할 수 없는 artifact

`project-file`은 기존 `ProjectsService.resolveProjectFile()`로 프로젝트 root 경계를 포함해 검증한다. `source-file`은 manifest의 owned project 경계를 먼저 검증한 뒤, 절대 로컬 경로가 실제 일반 파일이고 읽기 가능한지만 확인한다. 이 단계는 파일 내용을 읽거나 복사하지 않는다.

## 후보 응답

UI에는 path, URL, uri, checksum을 노출하지 않는다.

```ts
interface ShortformDirectorAssetCandidateV1 {
  schemaVersion: 'asset-candidate.v1';
  sourceProjectId: string;
  sourceProjectTitle: string;
  artifactId: string;
  label: string;
  mediaKind: 'image' | 'video';
  artifactKind: 'source.image' | 'source.video' | 'media.image' | 'media.video';
  allowedOrigins: Array<'owned' | 'source'>;
}
```

label은 artifact metadata의 명시적 label, 연결된 source asset의 label, media kind 기본 label 순으로 만든다. 파일 basename을 fallback으로 쓰지 않아 로컬 경로 일부가 새 API에 새지 않게 한다.

## AssetRef 계약 변경

foundation에서 임시로 두었던 단일 `artifactId`를 project-scoped locator로 교체한다.

```ts
interface AssetRefV1 {
  schemaVersion: 'asset-ref.v1';
  id: string;
  mediaKind: 'image' | 'video';
  origin: 'owned' | 'source' | 'search' | 'generated-image' | 'generated-video';
  locator: ProjectArtifactLocatorV1;
  label: string;
  sourceProjectTitle?: string;
  provenance: {
    kind: 'user_provided' | 'source_evidence' | 'search_result' | 'generated';
    sourceRef?: string;
  };
  rights: { status: 'cleared' | 'unknown' };
  availability: 'available' | 'missing';
}
```

AssetRef ID는 `(origin, sourceProjectId, artifactId)`의 결정적 hash로 만든다. 같은 artifact를 여러 layer에서 선택하면 하나의 AssetRef를 공유하며 binding만 늘어난다.

## API

```text
GET    /projects/shortform-director/projects/:projectId/asset-candidates
PUT    /projects/shortform-director/projects/:projectId/asset-bindings/:layerId
DELETE /projects/shortform-director/projects/:projectId/asset-bindings/:layerId
```

PUT body:

```json
{
  "sourceProjectId": "project-id",
  "artifactId": "artifact-id",
  "rightsConfirmed": true
}
```

서버 처리:

1. director project 소유권을 확인한다.
2. 현재 VideoPlan에서 `layerId`를 찾는다.
3. visual layer이며 `assetStrategy`가 `owned` 또는 `source`인지 확인한다.
4. source project 소유권과 manifest artifact를 확인한다.
5. artifact origin/media/local availability를 서버에서 다시 계산한다.
6. `rightsConfirmed === true`를 요구한다.
7. AssetRef와 binding을 upsert하고 orphan ref를 제거한다.
8. `buildAssetPack()`으로 준비도를 재계산하고 project를 저장한다.

DELETE는 해당 layer binding을 제거하고 다른 layer가 사용하지 않는 AssetRef를 정리한 뒤 준비도를 다시 계산한다.

local artifact 연결·해제는 provider 호출이나 유료 연산이 아니므로 operation billing confirmation을 붙이지 않는다.

## UX

pending requirement 중 `owned`와 `source`만 “에셋 선택”을 제공한다.

```text
[제품 · 보유 에셋] 장면 2 · 비트 1 · 샷 1
브랜드가 제공할 실제 제품 이미지

  프로젝트 에셋 선택 [▼]
  ☑ 이 에셋을 영상에 사용할 권한을 확인했습니다
  [연결]
```

- picker를 열 때 후보를 lazy load한다.
- layer strategy와 맞는 후보만 표시한다.
- 후보가 없으면 “사용 가능한 로컬 보유/원본 에셋이 없습니다”를 표시한다.
- 연결된 requirement는 label과 source project title을 보여주고 “연결 해제”를 제공한다.
- `search`, `generated-*`, `unresolved`에는 아직 실행 버튼을 만들지 않는다.
- render, preview, provider/model selector는 추가하지 않는다.

## 안전성과 정합성

- 클라이언트가 보낸 origin, media kind, label, path를 신뢰하지 않는다.
- 후보 조회와 binding 시점 모두 소유권과 파일 상태를 검증한다.
- API 응답과 director JSON에 path/URL을 저장하지 않는다.
- source project나 파일이 나중에 사라질 수 있으므로 이 단계의 `available`은 연결 시점 snapshot이다. 렌더 compiler 단계에서도 locator 재검증이 필요하다.
- VideoPlan 재생성 시 기존 AssetPack 초기화 정책은 유지한다. 의미가 달라진 layer에 binding을 자동 승계하지 않는다.

## 수용 기준

1. 후보 ID는 `(sourceProjectId, artifactId)` 쌍으로 구분된다.
2. 같은 사용자가 소유하고 로컬에서 검증 가능한 owned/source visual artifact만 후보가 된다.
3. 후보 응답과 저장 JSON에 path/URL/uri가 포함되지 않는다.
4. 권리 확인 없이 연결할 수 없다.
5. layer strategy와 origin이 다르면 연결할 수 없다.
6. 연결 후 해당 requirement가 resolved가 되고, 해제 후 missing으로 돌아간다.
7. 같은 artifact를 여러 layer가 공유할 수 있고 orphan ref는 해제 시 정리된다.
8. Angular에서 후보 선택, 권리 확인, 연결, 해제가 가능하다.
9. 검색·생성·render/provider 기능은 추가하지 않는다.
10. 기존 `shortform_prompt` 경로는 `origin/dev` 대비 변경이 없다.

## 비범위

- 새 파일 upload 또는 URL paste
- remote URL liveness 확인
- search/image/video generation provider
- renderer/compiler/RenderRecipe/preview
- license 자동 판별
- source artifact 복사·materialization
- web API 변경, DB migration, server/Electron 실행
- commit, push, deploy

## 2026-07-16 구현 결과

NestJS `shortform_director` 전용 경계에 다음을 구현했다.

- owner-scoped completed ProjectManifest 후보 조회
- project-scoped locator와 sanitized candidate 응답
- source-file/project-file 로컬 존재 검증
- 권리 확인과 layer origin 재검증
- deterministic AssetRef 공유, binding 교체·해제, orphan ref 정리
- binding 변경 뒤 AssetPack readiness 재계산

Angular에는 owned/source pending layer만 여는 lazy picker, 권리 확인, 연결, 연결된 label/project title 표시와 해제를 추가했다. search/generated/unresolved에는 provider나 실행 control을 추가하지 않았다.

검증:

- Nest director 33/33 통과, TypeScript build 통과
- Angular director 16/16 통과, production build 통과
- path/URL/uri 비노출 회귀 통과
- 기존 Angular/Nest/web API shortform 경로 `origin/dev` 대비 diff 0
- provider 호출, operation billing, server/Electron, migration, commit/push/deploy 없음
