# AI 숏폼 디렉터 시각 구성 품질 보완 설계

작성일: 2026-07-30 KST

관련 문서:

- `.codex/design/2026-07-27-shortform-director-quality-input-lineage-and-production-design.md`
- `.codex/design/SHORTFORM_DIRECTOR_DIAGRAM_STEP_COPY_OWNERSHIP_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PRODUCTION_MODEL_AND_SCENE_REVISION_DESIGN_2026-07-28.md`

## 1. 목적

실제 end-to-end 제작에 성공한 두 영상에서 확인된 다음 품질 결함을 고친다.

1. 장면 표현 방식을 선택한 내부 이유가 도식 headline으로 최종 영상에 노출된다.
2. 한 장면이 `실제 시각 소재`와 `화면 위 표현` 중 하나만 선택하므로 도식·문구만 있는 빈 장면이 만들어진다.
3. 실제 인물·아티스트·제품·사건 장면에서도 이미지 검색이 선택되지 않아 시각 파일 없이 렌더될 수 있다.
4. LLM이 비교·순서·수치 등 서로 다른 도식을 요청해도 모두 같은 3단계 sequence card로 변환된다.

목표는 모든 신규 제작 장면이 적합한 기본 시각 소재를 갖고, 자막·도식은 그 위의 표현 레이어로 동작하게 만드는 것이다.

## 2. 확인된 실제 결함

### 2.1 코딩 프로필 결과

- 전체 5개 장면 중 외부 시각 파일을 가진 장면은 1개였다.
- 나머지 4개 장면은 programmatic diagram 또는 그 fallback이었다.
- `decision.rationale`이 `VideoPlanLayer.content`가 된 뒤 RenderRecipe의 diagram `headline`으로 전달됐다.
- `programmaticBrief.labels`가 5개여도 앞의 3개만 sequence card에 사용됐다.
- `comparison`, `metric` 같은 primitive 선택값은 무시됐다.

### 2.2 엔터테인먼트 프로필 결과

- 전체 5개 장면에 내레이션 파일만 있었고 이미지·영상 입력은 0개였다.
- 장면 결정은 kinetic typography와 programmatic diagram만 선택했다.
- `image-search`가 선택되지 않았으므로 네이버 이미지 검색 API도 호출되지 않았다.
- 렌더러는 시각 파일이 0개인 계획도 기술적으로 성공 처리했다.

## 3. 핵심 결정

현재의 단일 `medium`을 다음 두 축으로 분리한다.

```text
장면
  ├─ 기본 시각 소재(base visual)
  │    ├─ official-source
  │    ├─ image-search
  │    ├─ generated-image
  │    └─ generated-video
  └─ 화면 위 표현(overlay)
       ├─ none
       ├─ kinetic-typography
       └─ programmatic-diagram
```

모든 신규 장면은 기본 시각 소재를 하나 가져야 한다. `none`은 overlay에만 허용하며 기본 시각 소재에는 허용하지 않는다.

이 설계는 기존 `video-plan.v1`의 다중 Layer 기능을 그대로 사용한다. 새 저장소나 새 프로젝트 스키마를 만들지 않는다.

## 4. 장면 미디어 결정 계약 v3

Web API의 `scene-media-decision` structured output을 다음 의미로 변경한다.

```ts
type SceneBaseMedium =
  | 'official-source'
  | 'image-search'
  | 'generated-image'
  | 'generated-video';

type SceneOverlayMode =
  | 'none'
  | 'kinetic-typography'
  | 'programmatic-diagram';

interface SceneMediaDecisionV3 {
  sceneIndex: number;
  baseMedium: SceneBaseMedium;
  overlayMode: SceneOverlayMode;
  rationale: string;
  factualRisk: 'low' | 'medium' | 'high';
  evidenceIds: string[];
  productionSourceIds: string[];
  searchBrief: string | null;
  generationBrief: string | null;
  programmaticBrief: {
    variant: 'comparison' | 'sequence' | 'loop' | 'metric';
    labels: string[];
    values: number[] | null;
  } | null;
}
```

조건:

- `baseMedium=image-search`일 때만 `searchBrief`가 필수다.
- `baseMedium=generated-image|generated-video`일 때만 `generationBrief`가 필수다.
- `overlayMode=programmatic-diagram`일 때만 `programmaticBrief`가 필수다.
- `factualRisk=high` 또는 `baseMedium=official-source`이면 연결된 `productionSourceIds`가 하나 이상 필요하다.
- `rationale`은 감사·근거 확인용이며 최종 화면 문구로 사용할 수 없다.
- 실제로 식별 가능한 현재 인물·아티스트·제품·사건은 `official-source` 또는 `image-search`를 선택한다.
- 생성 미디어는 개념·비유·촬영하기 어려운 연출에만 사용하며 사실 증거로 사용하지 않는다.

도식 데이터 조건:

| variant | labels | values |
|---|---:|---:|
| `comparison` | 정확히 2개 | `null` |
| `sequence` | 2~4개 | `null` |
| `loop` | 3~5개 | `null` |
| `metric` | 1~3개 | labels와 같은 개수 |

영상 전체 조건:

- programmatic diagram은 전체 장면 수의 `ceil(sceneCount / 3)`개를 넘지 않는다.
- programmatic diagram을 연속 두 장면에 배치하지 않는다.
- 모든 입력 장면에 정확히 하나의 결정이 있어야 한다.

## 5. 문구 소유권

내부 정보와 시청자용 정보를 다음처럼 분리한다.

```text
decision.rationale
  → LLM 선택 근거 artifact와 UI의 제작 정보에서만 확인
  → VideoPlan Layer.content 또는 RenderRecipe headline으로 전달 금지

scene.onScreenText[0] 또는 scene.claim
  → 시청자용 diagram headline

programmaticBrief.labels / values
  → 시청자용 diagram 본문
```

VideoPlan의 beat와 shot intent도 시청자에게 전달할 `scene.claim`을 사용한다. 매체 선택 이유를 장면 의미로 오인해 저장하지 않는다.

컴파일 회귀 테스트는 RenderRecipe의 모든 표시 문자열에 입력 `rationale`의 exact copy가 없음을 검증한다.

## 6. VideoPlan 컴파일

각 장면을 다음 순서의 Layer로 만든다.

1. 기본 시각 Layer
   - source, search, generated-image 또는 generated-video
   - 역할은 evidence, b-roll 또는 background
2. 선택적 diagram Layer
   - `overlayMode=programmatic-diagram`일 때만 추가
   - 외부 artifact가 없는 programmatic overlay
3. text Layer
   - `kinetic-typography`이면 kinetic text
   - 그 외에는 caption
   - 첫 장면의 hook과 마지막 장면의 CTA 보존

기본 시각 Layer가 없는 신규 v3 결정은 compile 전에 거부한다. 따라서 새 제작 계획에서는 시각 요구사항이 최소 장면 수만큼 생성된다.

기본 시각 에셋 준비가 실패하거나 binding이 없으면 기존 AssetPack readiness gate가 최종 렌더를 차단한다. 빈 화면으로 조용히 계속 진행하지 않는다.

## 7. 도식 계약

기존 저장 프로젝트의 `diagram.sequence-card.v1`은 호환성을 위해 유지한다.

신규 장면은 하나의 semantic card primitive와 명시적 variant를 사용한다.

```ts
interface DiagramSemanticCardContentV1 {
  schemaVersion: 'diagram-semantic-card-content.v1';
  primitive: 'diagram.semantic-card.v1';
  variant: 'comparison' | 'sequence' | 'loop' | 'metric';
  items: Array<{
    id: string;
    label: string;
    value?: number;
  }>;
}
```

RenderRecipe의 `programmaticMotion`도 동일한 variant와 exact label/value를 소유한다. 렌더러는 새 문구를 만들지 않는다.

Motion Canvas 레이아웃은 다음처럼 구분한다.

- `comparison`: 좌우 2열
- `sequence`: 번호와 연결선이 있는 순차 카드
- `loop`: 원형 또는 순환 연결 구조
- `metric`: 큰 수치와 짧은 라벨 중심의 지표 카드

variant별 진입 애니메이션은 동일한 deterministic stagger 기반을 공유할 수 있지만, 화면 배치는 실제로 달라야 한다.

## 8. 프롬프트와 결정 검증

프롬프트는 장면을 독립적으로만 판단하지 않고 영상 전체 결과도 함께 확인하도록 지시한다.

- 실존 대상이 등장하는 장면은 실제 시각 소재를 우선 검토
- 모든 장면에 base visual 필수
- diagram과 kinetic typography는 base visual을 대체하지 않고 overlay로 사용
- 같은 표현이 반복되지 않도록 전체 장면 배열 검토
- diagram 상한과 연속 배치 금지 준수

LLM 출력 뒤 Desktop compiler에서도 도식 상한과 연속 배치 금지를 다시 검증한다. 프롬프트 준수에만 의존하지 않는다.

## 9. 오류 처리

- v3 필드 누락 또는 조건 위반: Web API structured output validation 실패
- 장면 index 누락·중복: Desktop projection/compile 실패
- 도식 variant별 labels/values 위반: Web API와 Desktop 양쪽에서 실패
- 기본 시각 요구사항 누락: candidate plan compile 실패
- 에셋 검색·생성 실패 또는 binding 누락: AssetPack readiness에서 렌더 차단
- 지원하지 않는 semantic diagram: RenderRecipe compile 또는 renderer conformance에서 실패

실패를 generic dark background로 대체하지 않는다.

## 10. 호환성

- 기존 완료 영상과 기존 `video-plan.v1` JSON은 수정하지 않는다.
- 기존 `diagram.sequence-card.v1` renderer 경로는 유지한다.
- 신규 inference 응답과 신규 candidate plan만 v3 계약을 사용한다.
- 기존 프로젝트의 장면별 편집·revision 기록 구조는 유지한다.
- 새 결정을 적용해 다시 만들 때 조사와 후보 생성 결과는 재사용할 수 있다.

## 11. 구현 경계

변경 대상:

- `web/clipper_web_api`
  - scene media response schema
  - manual validator
  - prompt v3
  - 계약·transport 테스트
- `desktop/clipper_nestjs`
  - inference response projector
  - candidate plan compiler
  - semantic diagram domain/motion contract
  - RenderRecipe compiler
  - Motion Canvas projection·scene
  - readiness·conformance 회귀 테스트
- `desktop/clipper_angular`
  - 저장된 RenderRecipe 타입에 신규 semantic diagram union 반영
  - 기존 sequence preview를 깨지 않는 최소 호환 처리

이번 범위에서 하지 않는 것:

- 새 이미지·영상 provider 추가
- 기본 모델 변경
- 새 결제·크레딧 차감
- 기존 JSON 일괄 migration
- 프레임 단위 편집기
- 실제 provider 호출을 승인 없이 실행
- 기존 완료 영상 파일 삭제 또는 덮어쓰기

## 12. 인수 조건

1. `rationale` 문장이 diagram headline이나 최종 표시 문자열에 나타나지 않는다.
2. 신규 장면마다 source/search/generated 계열 기본 시각 Layer가 정확히 하나 이상 존재한다.
3. 도식과 kinetic text는 기본 시각 소재 위의 overlay로 컴파일된다.
4. 이미지 검색 장면은 실제 search requirement를 만들고, 준비 전에는 렌더 ready가 되지 않는다.
5. programmatic diagram은 상한을 넘거나 연속 배치되면 거부된다.
6. comparison, sequence, loop, metric이 서로 다른 Motion Canvas 레이아웃으로 렌더된다.
7. 기존 `diagram.sequence-card.v1` fixture와 저장 프로젝트 호환 테스트가 계속 통과한다.
8. Web API 전체 테스트·빌드와 Desktop Nest 관련 전체 테스트·빌드가 통과한다.
9. Angular 타입 검사·관련 컴포넌트 테스트·빌드가 통과한다.
10. 테스트는 실제 외부 provider를 호출하지 않으며, 라이브 재제작은 별도 비용 승인 뒤 수행한다.
