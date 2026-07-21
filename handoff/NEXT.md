# Next Handoff

최신 갱신: 2026-07-21 KST

이 문서는 다음 세션의 활성 인계만 담는다. 상세 수행 내용은
`../records/sessions/2026/07/21.md`, 과거 전체 인계는
`archive/2026/07/next-handoff-through-2026-07-20.md`에 있다.

## 현재 목표

AI 숏폼 디렉터가 기존 `프롬프트로 영상생성`보다 실제로 더 좋은 숏폼을 만들기 위해 어떤
입력과 편집 판단 구조가 필요한지 검증한다.

현재 단계에서는 production 구현과 UI 확정을 서두르지 않는다. 네 가지 대표 사례에서 입력
조합별 Content Opportunity, Director Brief, 대사와 storyboard 품질을 비교하고 효과가 있는
정보만 남긴 뒤 UI와 구현으로 이동한다.

기존 `shortform_prompt` 플러그인은 수정하지 않는다.

## 먼저 읽을 문서

1. `.codex/AGENTS.md`
2. `.codex/records/sessions/2026/07/21.md`
3. `.codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_ARCHITECTURE_AND_DIRECTOR_BRIEF_DESIGN_2026-07-21.md`
4. `.codex/design/SHORTFORM_DIRECTOR_PERSISTENT_CONTENT_OPERATIONS_AND_VIRA_INTEGRATION_DESIGN_2026-07-21.md`
5. `.codex/mockups/shortform-director-content-operations-v2/index.html`

기존 구현과 Vira 상세가 필요할 때만 다음을 추가로 읽는다.

- `.codex/records/sessions/2026/07/16.md`
- `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_FREE_COMMERCIAL_RENDERER_AND_OS_DECISION_2026-07-20.md`

## 현재 제품 결정

```text
운영 프로필
  → 콘텐츠 프로젝트
  → 콘텐츠 트랙
  → Episode Research Pack
  → Content Opportunity
  → Director Brief
  → 영상 아이디어 / VideoPlan
  → 제작 실행
  → 결과와 피드백
```

- 운영 프로필·프로젝트·트랙·아이디어 보관·제작은 Clipper가 소유한다.
- 입력은 목적과 Vira에 한정하지 않는다. 공식 source, 시청자 질문, 창작 레퍼런스, 과거
  성과·편집 피드백과 제작 가능성을 함께 검증한다.
- Vira는 시장 수집·원본 영상·snapshot·성장점수·상세 분석의 source of truth다.
- Clipper는 Vira 분석 화면을 복제하지 않고 생성에 사용한 evidence snapshot만 보관한다.
- 관측 사실, 공식 사실, 시청자 반응, AI 기획 해석과 가설을 구분한다.
- 입력 단계부터 beat별 visual intent와 asset intent를 기록해 향후 생성형 영상·도식 renderer
  개선으로 연결한다.
- 사용자 직접 입력은 최소화하고 저장 기본값, source 추가, 연결, 추천 확인과 행동 학습을
  우선한다.

Vira 감사 기준은 `main@2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4`다. 활성 Market/Tmarket
계열과 등록 해제된 legacy Viral Intelligence를 구분한다. Vira는 구현 단계 전까지 read-only다.

## 다음 작업

1. 다음 네 유형에서 실제 주제와 source pack 후보를 정한다.
   - 브랜드 없는 트렌드 큐레이션
   - 특정 제품을 포함한 시장 정보
   - 인물·아이돌 상시 콘텐츠
   - 일반 유튜버의 전문 지식 설명
2. 같은 주제에 대해 `prompt only → 프로필 → 공식 source → 시청자 질문 → Vira → 레퍼런스
   → 과거 피드백` 순으로 입력을 추가하는 비교 실험을 설계한다.
3. 구체성, 새로움, 시청자 관련성, 근거 정확성, 훅·payoff, 시각화와 제작 가능성 rubric을
   확정한다.
4. 첫 비교 결과로 필요 없는 필드를 제거하고 Project Memory, Research Pack, Opportunity,
   Director Brief의 최소 경계를 정한다.
5. 사용자 승인 후 V2 목업을 다시 수정한다. 그 전에는 production 구현으로 이동하지 않는다.

## 보류 중인 실제 E2E

- Veo quota 재확인
- 에셋 자동 준비의 owned 부재 시 search 자동 전환
- RenderRecipe → immutable staging → Motion Canvas MP4 저장
- 결과 영상과 자동 선택 에셋 품질 검토

실제 provider 호출 전에 사용자에게 알린다.

## 저장소 기준점

| 저장소 | branch | expected HEAD |
|---|---|---|
| `desktop/clipper_angular` | `feat/shortform-director-foundation` | `c93be51` |
| `desktop/clipper_nestjs` | `feat/shortform-director-foundation` | `d27db82` |
| `desktop/clipper_electron` | `dev` | `ddf70dc` |
| `web/clipper_web_api` | `feat/shortform-director-foundation` | `480bc30` |
| `web/clipper_web_admin` | `feat/shortform-director-foundation` | `8a3333f` |
| `.codex` | `main` | 이 NEXT를 포함한 pushed handoff commit |

시작할 때 branch, `git status`, upstream 동기화와 최근 log를 확인한다. 예상 밖 변경은
reset/revert하지 말고 먼저 보고한다. `legacy/adlight_python/fastapi_server.spec`의 기존 변경은
이번 작업과 무관하므로 보존한다.

## 안전 경계

- 기존 `shortform_prompt` 플러그인을 수정하지 않는다.
- `/Users/jina/project/vira`는 구현 단계 전까지 read-only다.
- 실제 키, JWT, cookie와 env 값을 출력·문서화하지 않는다.
- 새 문서는 `.codex`에만 작성한다.
- 실제 provider 호출 전에는 사용자에게 알린다.
- 커밋·push·PR·배포·migration·서버 재시작·앱 실행은 사용자가 명시할 때만 한다.

## 다음 세션용 프롬프트

```text
Using Superpowers.

작업 위치는 /Users/jina/project/adlight 입니다. 한국어로 답변해줘.

먼저 다음 문서를 읽고 AI 숏폼 디렉터의 품질 입력 아키텍처 작업을 이어받아줘.

- .codex/AGENTS.md
- .codex/handoff/NEXT.md
- .codex/records/sessions/2026/07/21.md
- .codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_ARCHITECTURE_AND_DIRECTOR_BRIEF_DESIGN_2026-07-21.md
- .codex/design/SHORTFORM_DIRECTOR_PERSISTENT_CONTENT_OPERATIONS_AND_VIRA_INTEGRATION_DESIGN_2026-07-21.md

먼저 NEXT.md의 기준점에 따라 각 저장소의 branch, git status, upstream 동기화 상태와 최근
log를 확인해줘. 예상 밖 변경은 reset/revert하지 말고 먼저 보고하고,
legacy/adlight_python/fastapi_server.spec의 기존 변경은 보존해.

이번 세션에서는 production 구현이나 목업 수정부터 시작하지 말고, 품질 입력 아키텍처를
검증할 네 가지 실제 주제와 source pack, 입력 조합 비교 실험, 평가 rubric을 먼저 구체화해줘.
Vira는 read-only로 다루고 실제 provider 호출 전에는 나에게 알려줘. 커밋·push·PR·배포·
migration·서버 재시작·앱 실행은 내가 명시적으로 요청할 때만 해.
```
