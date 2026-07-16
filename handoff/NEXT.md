# Next Handoff

최신 갱신: 2026-07-16 KST

이 문서는 다음 세션이 가장 먼저 읽는 압축 인계문이다. 긴 과거 인계는 [archive/2026/05/next-session-prompt-legacy.md](archive/2026/05/next-session-prompt-legacy.md)에 보관한다.

## Active Handoff: 2026-07-16 AI 숏폼 디렉터 Remotion PoC 결과와 production gate

상세 기록:

- `.codex/records/sessions/2026/07/16.md`
- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PLUGIN_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_VIRA_EVIDENCE_POLICY_AND_STRATEGY_INPUT_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_GROUNDED_CONTENT_STRATEGY_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_GROUNDED_CONTENT_STRATEGY_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_NATIVE_VIDEO_PLAN_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_45S_EVAL_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_45S_EVAL_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_PACK_RESOLUTION_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROJECT_ARTIFACT_BINDING_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_ASSET_ACQUISITION_AND_MANUAL_REPLACEMENT_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_REPRESENTATIVE_ASSET_ACCEPTANCE_AND_PRODUCTION_READINESS_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_SUPERTONIC_TTS_TIMING_ALIGNMENT_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_SUPERTONIC_TTS_TIMING_ALIGNMENT_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_NARRATION_AUDIO_MATERIALIZATION_AND_REGENERATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_NARRATION_AUDIO_MATERIALIZATION_AND_REGENERATION_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_RECIPE_COMPILER_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_RECIPE_COMPILER_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_PROGRAMMATIC_MOTION_AND_DETERMINISTIC_PREVIEW_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_DIAGRAM_STEP_COPY_OWNERSHIP_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_DIAGRAM_STEP_COPY_OWNERSHIP_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_INPUT_REVALIDATION_AND_STAGING_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_INPUT_REVALIDATION_AND_STAGING_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ADAPTER_AND_OPERATION_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ADAPTER_AND_OPERATION_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_CONFORMANCE_AND_BENCHMARK_ACCEPTANCE_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_CONFORMANCE_AND_BENCHMARK_ACCEPTANCE_IMPLEMENTATION_PLAN_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ROLE_ALLOCATION_AND_FIRST_POC_DECISION_2026-07-16.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDERER_ROLE_ALLOCATION_AND_FIRST_POC_IMPLEMENTATION_PLAN_2026-07-16.md`

초기 legacy adapter 문서는 이력만 보존하며 superseded 상태다.

- `.codex/design/SHORTFORM_VIDEO_PLAN_FOUNDATION_DESIGN_2026-07-16.md`
- `.codex/design/SHORTFORM_VIDEO_PLAN_FOUNDATION_IMPLEMENTATION_PLAN_2026-07-16.md`

### 현재 결정

- 기존 `프롬프트로 숏폼 제작(shortform_prompt)` 플러그인은 변경하지 않는다.
- 새 품질 파이프라인은 독립 `shortform_director` / `AI 숏폼 디렉터` 플러그인에서 만든다.
- 새 플러그인은 legacy clips를 backfill하지 않고 `PlanningContext + native VideoPlan`을 처음부터 소유한다.
- `VideoPlan`은 creative planning IR, 기존 `render-recipe.v1`은 실행 IR로 역할을 분리한다.
- 실제 `/Users/jina/project/vira` 현재 코드를 정본으로 삼고 PDF는 방향 참고 자료로만 쓴다.
- `vira-evidence.v1`은 current/lab/on-demand/legacy lifecycle을 분리하고 surface-lifecycle 조합을 runtime에서 검증한다.
- 현재 Vira에는 Clipper exporter/API가 없으므로 네트워크나 DB 직접 연동은 하지 않았다.
- production renderer와 image/video provider는 아직 미정이다.
- renderer는 상호 배타적인 단일 선택이 아니라 범용 합성, 전문 도식 materialization, 최종 media 처리 역할로 나눈다.
- 범용 합성은 Remotion을 첫 비프로덕션 PoC로 검증하고 Motion Canvas는 packaging/license/quality gate 실패 시 두 번째 후보로 둔다.
- 기존 app-managed FFmpeg/ffprobe는 최종 probe, thumbnail과 필요한 mux/normalize 역할을 유지한다.
- `diagram.sequence-card.v1` 같은 간단한 programmatic motion은 메인 합성기가 직접 구현한다.
- Manim은 final render 중 즉석 호출하지 않고 복잡한 기술·수학 도식을 checksummed artifact로 먼저 materialize한 뒤 immutable stage에 넣는 전문 renderer 후보로 둔다.
- 첫 PoC에서는 Angular에 React/Remotion Player를 넣지 않고 같은 RenderRecipe/motion 계약을 Angular preview와 Remotion final/still render가 각각 소비한다.
- Remotion source/runtime은 Nest `ncc` bundle과 분리하고 production runtime의 자동 browser/native binary download를 허용하지 않는다.
- Remotion production 후보 승격 전 company license, packaged binary size, supported macOS 범위와 Windows x64를 확인해야 한다.
- isolated Remotion `4.0.489`/React `19.2.7` representative harness는 구현됐고 automated conformance 7개가 모두 pass했다.
- raw Remotion video는 41.2초였지만 AAC/container가 41.258667초여서 조건부 FFmpeg audio trim/remux가 실제로 필요했다.
- 최종 MP4는 41.2초, 30fps, 1080×1920, H.264/AAC이며 progress와 AbortSignal cancel도 실제 render에서 검증했다.
- visual renderer spot check는 통과했지만 synthetic media라 manual 7축은 pending이고 production adapter는 여전히 0개다.
- `VideoPlan + AssetPack + narrationAudio`는 strict gate 뒤 기존 `render-recipe.v1`로 결정적으로 컴파일한다.
- Director recipe는 `shortform.director.hybrid.v1` identity와 `shortform-director-composition.v1` layer metadata를 사용한다.
- 기존 renderer가 새 recipe를 자동 claim하지 않도록 `shortformTemplateModel`과 legacy provenance를 넣지 않는다.
- compile endpoint는 owner-scoped read-only preview이며 project/file/operation/render 상태를 변경하지 않는다.
- `diagram.sequence-card.v1`은 `shortform-director-programmatic-motion.v1` normalized motion 계약을 갖는다.
- motion sampler는 start/reveal/hold/exit/end 5개 reference frame을 결정적으로 만든다.
- Angular preview는 RenderRecipe overlay의 동일 motion 값을 소비하며 별도 preview API나 영상 파일을 만들지 않는다.
- diagram Layer `content`는 sequence-card headline, `programmaticPayload`는 `context/evidence/action` exact copy를 소유한다.
- web strict draft는 diagram payload object와 non-diagram null을 필수로 생성·검증한다.
- renderer/compiler/Angular preview는 VideoPlan authored copy를 그대로 소비하며 새 광고 문구를 만들지 않는다.
- `상황 → 확인 → 행동`은 payload가 없는 기존 저장 plan에만 적용되는 compiler compatibility fallback이다.
- `planning-context.v2`는 BrandProfile, expanded CampaignBrief, SourcePack claim/provenance를 소유한다.
- `ContentStrategy`의 Vira 직접 인용은 candidate evidence로 제한하고 context-only/excluded를 분리한다.
- LLM 전략 생성은 기존 `/llm/script`와 분리된 web API endpoint와 별도 operation을 사용한다.
- 사용자가 고른 matrix entry와 연결 hypothesis만 native VideoPlan 입력으로 사용한다.
- LLM 생성 직후 `VideoPlan` timeline은 absolute ms, 0-based contiguous Scene/Beat/Shot이며 timing은 `estimated`다.
- 현재 Supertonic은 word/sentence timestamp를 반환하지 않고 WAV 경로만 반환하며 Nest가 전체 duration/checksum을 측정한다.
- cue별 artifact/checksum/text fingerprint/duration exact set이 유효할 때만 plan을 `tts_aligned`로 재배치한다.
- 순수 TTS alignment fallback은 원본 estimated plan을 변경하지 않는다.
- `tts-timing-alignment.v1`은 voice/speed 재생성의 누적 오차를 막기 위해 compact estimated timing baseline을 보존한다.
- `narration-audio-pack.v1`은 현재 VideoPlan에 연결된 Supertonic voice/speed와 cue별 materialized WAV metadata를 저장한다.
- 나레이션 project JSON에는 파일 경로/URL/provider raw payload/credential을 저장하지 않는다.
- cue 합성은 순차 실행하고 전체 성공 뒤 project를 한 번 저장한다. 일부 실패 시 새 파일을 제거하고 이전 project/generation을 유지한다.
- 나레이션 재생성은 직전 aligned timing이 아니라 저장된 estimated baseline에서 다시 시작한다.
- TTS provider는 기존 공용 Supertonic으로 고정했으며 별도 operation charge는 없다.
- Layer는 실제 provider/artifact가 아니라 `owned|source|search|generated-*|programmatic|unresolved` 계획 전략만 갖는다.
- product/evidence visual에는 생성형 route를 금지하고 diagram/text는 programmatic으로 제한한다.
- 품질 자동화의 첫 단계는 45초 합성 기준편과 `structural_proxy` evaluator이며 production 생성 gate가 아니다.
- 자동 평가는 blocking/warning과 측정값만 만들고 임의의 100점 총점은 만들지 않는다.
- source faithfulness, hook strength, script/visual/motion/mobile 품질은 rendered sample의 수동 검토 축으로 남긴다.
- `asset-pack.v1`은 VideoPlan visual layer의 requirement, AssetRef, binding과 렌더 준비도를 별도 snapshot으로 소유한다.
- `resolved`는 준비 완료, `missing`은 route는 있으나 실제 ref가 없음, `unresolved`는 route 자체가 미정이라는 뜻이다.
- AssetRef는 URL/파일 경로가 아니라 project-scoped `(projectId, artifactId)` locator, origin, provenance, rights, availability 메타데이터를 갖는다.
- production 입력의 첫 범위로 같은 사용자의 로컬 `owned/source` ProjectManifest artifact를 연결할 수 있다.
- `search|generated-image|generated-video` route에는 provider-neutral acquisition 상태 계약을 두되 실제 provider 실행은 아직 없다.
- search/generated layer는 로컬 owned/source project artifact로 명시적 manual replacement가 가능하다.
- planned origin binding과 manual replacement binding을 구분하며 수동 대체를 해제해도 원 acquisition 상태를 보존한다.
- `asset-production-readiness.v1`은 local resolution, provider outstanding, retryable, blocking 상태를 별도 gate로 계산한다.
- readiness는 `empty|ready|waiting|blocked`이며 `renderable`은 모든 visual requirement가 해결된 ready에서만 true다.
- remote provider 결과와 render artifact는 아직 후보가 아니며 provider는 미정이다.
- 새 project-artifact binding은 artifact kind/media type/size/checksum의 `project-artifact-snapshot.v1`을 AssetRef에 저장한다.
- snapshot 없는 기존 AssetRef는 manifest metadata 또는 현재 content checksum으로 render-input staging할 수 있다.
- `POST .../:projectId/render-input-stage`는 current project를 다시 compile한 뒤 exact visual/TTS 파일을 재검증하고 immutable local stage로 고정한다.
- stage id는 project/recipe/input checksum snapshot에 결정적으로 묶이며 같은 snapshot은 기존 stage를 재사용한다.
- stage public contract에는 path/URL/internal filename/provider/model/credential이 없고 project JSON도 변경하지 않는다.
- Angular의 `렌더 입력 고정`은 recipe 확인 뒤에만 보이며 과금·renderer·provider·queue를 실행하지 않는다.
- private stage manifest는 checksum으로 봉인된 exact RenderRecipe를 함께 보관한다.
- private execution bundle은 recipe와 sourceId/stagedInputId metadata를 갖고 staged absolute path는 `resolveInput(sourceId)` 호출에서만 해소한다.
- Director renderer adapter는 original ProjectManifest/source path가 아니라 execution bundle만 소비한다.
- Director adapter registry는 claim/availability/explicit id를 검증하되 production adapter는 0개이고 generic VideoRenderProvider를 자동 포함하지 않는다.
- future JobsService params는 path/raw recipe 대신 opaque stage/recipe checksum reference만 저장한다.
- stage retention class는 active job, retry source, completed source로만 고정했으며 기간/삭제 worker는 아직 없다.
- adapter가 없으므로 render operation API/Angular render controls/queue executor는 아직 추가하지 않았다.
- private execution bundle에서 deterministic renderer conformance profile과 canonical staged-input fingerprint를 만든다.
- profile은 representative output/timeline counts, required capability와 sequence-card 5개 semantic state checksum을 가진다.
- candidate benchmark는 revision/environment/elapsed/output bytes/optional peak RSS를 기록하지만 performance threshold나 순위에는 쓰지 않는다.
- 자동 gate 뒤 기존 manual 7축 exact all-pass만 최종 accepted이며 평균·가중치·100점 총점은 없다.

### 구현 상태

```text
desktop/clipper_angular
  branch: feat/shortform-director-foundation
  pushed HEAD: bfaf720 feat(shortform-director): add director workflow UI
  upstream: origin/feat/shortform-director-foundation exact sync
  branch divergence: origin/dev 대비 feature 1 commit / dev 5 commits
  working tree: clean

desktop/clipper_nestjs
  branch: feat/shortform-director-foundation
  pushed commits:
    - 9eb8994 feat(shortform-director): add native planning and render foundation
    - b72e74c feat(shortform-director): add isolated Remotion render PoC
  upstream: origin/feat/shortform-director-foundation exact sync
  branch divergence: origin/dev 대비 feature 2 commits / dev 2 commits
  working tree: clean

web/clipper_web_api
  branch: feat/shortform-director-foundation
  pushed HEAD: 5a8424b feat(shortform-director): add grounded planning APIs
  upstream: origin/feat/shortform-director-foundation exact sync
  branch divergence: origin/dev 대비 feature 1 commit / dev 0 commits
  working tree: clean

.codex
  branch: main
  design/session/handoff commit: 6a389a3 docs(shortform-director): record hybrid renderer design and PoC
  final closure record: current main HEAD
  upstream: origin/main exact sync after closure push
  working tree: clean after closure

/Users/jina/project/vira
  branch: main
  HEAD at audit: 2f1d1fd
  read-only audit
```

현재 구현된 흐름:

```text
Plugin Store 설치
  → /shortform/director
  → campaign prompt + BrandProfile + expanded CampaignBrief + SourcePack claims
  → optional vira-evidence.v1 JSON paste
     + lab/legacy explicit opt-in
  → POST /projects/shortform-director/projects
  → Vira envelope + current payload validation
  → candidate/context_only/excluded admission
  → owner-scoped dedicated JSON store
  → PlanningContext v2 + contentStrategy:null + empty native VideoPlan
  → shortform_director.strategy 10 credit quote/confirm
  → web API strict structured ContentStrategy
  → candidate evidence/source claim reference 이중 검증
  → ContentStrategy 저장 + matrix 표시
  → matrix entry 선택 + shortform_director.video_plan 10 credit quote/confirm
  → web API strict video-plan-draft.v1
  → absolute timeline/grounding/hook/CTA/asset route 이중 검증
  → server provenance + narration cue 조립
  → native VideoPlan + AssetPack 저장
  → hierarchy + 에셋 준비도 요약

오프라인 품질 회귀
  → Vira-shaped synthetic evidence + 승인 claim 2개
  → 45초 expected ContentStrategy/VideoPlan
  → 기존 admission/contract validator
  → video-plan-quality-report.v1
     ├─ blocking 8개
     ├─ warning 4개 + structural metrics
     └─ manual_review_required 7개 축

에셋 readiness
  → VideoPlan visual layer만 requirement로 변환
  → programmatic: resolved
  → owned/source/search/generated + ref 없음: missing
  → unresolved strategy: unresolved
  → Angular에서 준비/필요/방식 미정과 pending 위치 표시
  → owned/source pending layer에서 프로젝트 에셋 선택
  → 권리 확인 + server-side 소유권/파일/origin 재검증
  → AssetRef/binding 저장 + readiness 재계산
  → 연결된 ref 표시/해제
  → search/generated layer별 provider-neutral AssetAcquisition 생성
     ├─ not_requested / queued / running
     └─ succeeded / failed / cancelled
  → 실제 provider control 없이 현재 상태 표시
  → image/video compatibility에 맞는 로컬 project artifact 수동 대체
  → manual-replacement binding 표시, 해제 시 acquisition 상태 복원
  → 대표 45초 AssetPack acceptance
     ├─ programmatic 1
     ├─ planned local 7
     ├─ manual replacement 1
     └─ provider required 1
  → asset-production-readiness.v1
     ├─ ready
     ├─ waiting
     └─ blocked
  → Angular에서 해결/로컬/Provider/차단 summary 표시

Director narration lifecycle
  → Supertonic voice / supported speed 선택
  → cue별 WAV 순차 합성
  → owner/project hash namespace에 opaque artifact materialization
  → path/URL 없이 size/checksum/duration/provider metadata만 project에 저장
  → exact-set validation
  → compact estimated timing baseline 보존
  → Scene/Beat/Shot/Layer deterministic reflow
  → 45,000ms estimated → 41,200ms tts_aligned
  → 전체 성공 뒤 narration-audio-pack.v1과 project 1회 저장
  → voice/speed 재생성은 estimated baseline 복원 후 새 generation 생성
  → 성공 뒤 이전 generation 파일 정리
  → partial failure는 새 파일 정리 + 이전 project/generation 보존
  → 기존 AssetPack binding/acquisition/readiness 보존
  → Angular에서 음성/속도, 생성·재생성, ready cue와 timing 상태 표시

Director RenderRecipe compile preview
  → tts_aligned VideoPlan + renderable AssetPack + ready narration exact set
  → timeline hierarchy/containment + current AssetPack recompute 검증
  → existing render-recipe.v1
     ├─ external visual timeline 9
     ├─ programmatic/text overlay 11
     ├─ TTS audio track 7
     ├─ caption item 7
     └─ composition Layer metadata 20
  → GET /projects/shortform-director/projects/:projectId/render-recipe
  → project 저장/파일 쓰기/operation charge/renderer 호출 없음
  → Angular에서 준비 조건이 맞을 때만 실행 레시피 확인
  → renderer 미선정 · 렌더는 실행하지 않음

Director render input staging
  → current project strict recompile
  → RenderRecipe sourceAssetIds exact visual set
     ├─ ProjectManifest owner/artifact/local access 재검증
     ├─ AssetRef media kind 재검증
     └─ bound snapshot | manifest metadata | current content checksum
  → TTS audio track exact narration set
     └─ narration pack + timing measurement + actual WAV checksum
  → temporary directory copy
  → copied size/checksum 재검증
  → immutable ready stage rename
  → opaque stage/input id + visual/narration/byte summary만 응답
  → project 저장/operation charge/renderer/provider/queue 없음

Director private render execution foundation
  → private stage manifest에서 exact recipe checksum 재검증
  → recipe visual/TTS source exact set과 staged input exact set 검증
  → shortform-director-render-execution-bundle.v1
     ├─ public-safe stage/recipe/input metadata
     └─ resolveInput(sourceId)만 private staged path 반환
  → Director-only renderer adapter registry
     ├─ explicit id / claim / availability
     └─ production adapter 0개
  → shortform-director-render-job-reference.v1
     └─ project/stage/recipe/checksum/adapter id only
  → Jobs status retention class
     ├─ active-job
     ├─ retry-source
     └─ completed-source
  → 실제 renderer/queue/API/UI/cleanup 없음

Director renderer conformance foundation
  → private execution bundle metadata only
  → deterministic profile id + input fingerprint
  → representative expected contract
     ├─ 41.2s / 30fps / 1080×1920
     ├─ staged input 13
     ├─ visual item 9 / TTS 7 / subtitle 7
     ├─ overlay 11 / composition layer 20
     └─ sequence-card checkpoint 5
  → required provider-neutral capability ids
  → future candidate observed report
     ├─ exact staged input consumption
     ├─ output probe + one-frame duration tolerance
     ├─ timeline/motion conformance
     └─ raw benchmark metadata, no ranking
  → automated gate + manual 7-axis exact review
  → production adapter/API/UI 실행 없음

Renderer 역할 분담 결정
  → main compositor first PoC: Remotion
  → main compositor fallback: Motion Canvas
  → final probe/thumbnail/mux: app-managed FFmpeg/ffprobe
  → simple sequence-card: main compositor native motion
  → future complex diagram
     ├─ Manim or specialist materializer
     ├─ checksummed project artifact
     └─ immutable stage input
  → production renderer registration은 계속 0개

Isolated Remotion representative PoC
  → nested private package
     ├─ Remotion 4.0.489
     └─ React/React DOM 19.2.7
  → synthetic staged input exact 13
  → 5 checkpoint still
  → 41.2s full raw MP4
  → ffprobe
     ├─ video 41.2s
     └─ AAC/container 41.258667s
  → one-frame tolerance 초과
  → conditional FFmpeg finalization
     ├─ video stream copy
     ├─ audio 41.2s trim/re-encode
     └─ remux
  → final 41.2s MP4/H.264/AAC
  → automated conformance 7/7 pass
  → manual 7축 pending
  → AbortSignal cancel 2% smoke pass

Programmatic motion preview
  → VideoPlan diagram Layer
     ├─ content: headline
     └─ programmaticPayload: context/evidence/action exact copy
  → diagram.sequence-card.v1 overlay
  → normalized stage + enter/hold/exit sampler
  → 5개 deterministic reference frame
  → RenderRecipe params.programmaticMotion
  → Angular 9:16 frame inspector
     ├─ 시작
     ├─ 공개
     ├─ 유지
     ├─ 퇴장
     └─ 끝
  → canvas/video/audio/autoplay/render 없음
```

- 이번 Director 작업에서 기존 Angular shortform feature, Nest shortform/shortform-core, web API shortform-script 경로 working-tree 변경은 0이다.
- remote `origin/dev` 전진으로 현재 feature branch에는 Angular 기준 dev 5커밋, Nest 기준 dev 2커밋이 아직 들어오지 않았으며 merge/rebase하지 않았다.
- current Vira 코드 모양의 합성 active/lab/on-demand fixture 3종을 추가했다.
- desktop Nest director 83/83 통과.
- Director와 기존 generic renderer registry boundary 회귀 합계 84/84 통과.
- web API 전체 80 suite 431/431 통과.
- Angular director feature 30/30 통과.
- Angular 전체 1,535/1,535 통과.
- 세 저장소 build 통과, web API 새 production source ESLint clean.
- Vira exporter/API, 새 upload/URL ingestion, search/generation, production renderer/queue는 구현하지 않았다.
- `shortform_director.strategy`와 `shortform_director.video_plan`은 각각 10 credit 초기 policy지만 migration은 실행하지 않았다.
- duplicate normalized hook, prohibited expression, VideoPlan grounding coverage를 deterministic validator로 검사한다.
- 전략 재생성 성공 시 이전 VideoPlan은 empty plan으로 무효화한다.
- 대표 fixture는 45,000ms, 5 scene, 7 beat, 10 shot, 20 layer이며 narration은 공백 제외 225자/초당 5자다.
- 품질 evaluator는 grounding, 첫 3초 hook, CTA, 서사, visual coverage, asset authenticity, 금지 표현, disclosure를 blocking으로 검사한다.
- narration density, shot pacing, text readability, unresolved asset은 warning이며 `passed`를 false로 만들지 않는다.
- hook 지연, grounding 누락, 생성형 product, narration 과밀, unresolved asset mutation 회귀가 통과한다.
- evaluator는 순수 domain 객체로만 추가했고 generation service, operation billing, web API, Angular UI에는 연결하지 않았다.
- 대표 plan은 visual requirement 10개 중 programmatic diagram 1개 resolved, 실제 ref가 필요한 9개 missing, route unresolved 0개다.
- AssetPack resolver는 origin/media/availability/rights/ref 존재를 검증하고 reason을 보존한다.
- 새 project와 전략 재생성은 empty AssetPack, 새 VideoPlan은 동일 plan id의 AssetPack을 저장한다.
- assetPack 없는 저장 JSON은 read 시 메모리에서만 hydration하고 디스크를 rewrite하지 않는다.
- Angular는 owned/source planned binding과 search/generated manual replacement에 lazy project asset picker, 권리 확인, 연결/해제를 제공한다.
- search/generated acquisition 상태는 보이지만 provider 실행·재시도·render control은 없다.
- candidate API는 path/URL/uri를 반환하지 않으며 binding 시점에 project ownership과 로컬 파일 존재를 다시 확인한다.
- 같은 project artifact를 여러 layer가 하나의 deterministic AssetRef로 공유하고 마지막 binding 해제 때 정리한다.
- AssetPack은 search/generated layer에 deterministic acquisition을 만들고 구형 JSON의 acquisitions/binding mode를 read-only hydration한다.
- 수동 대체는 `manual-replacement`와 `manual_replacement_ready`로 식별하며 원 acquisition 이력을 삭제하지 않는다.
- 대표 acceptance는 visual 10개 중 9개 해결, local 8개, provider-required 1개로 waiting이다.
- 마지막 search layer까지 수동 대체하면 10/10 ready와 `renderable: true`가 된다.
- non-retryable failure, succeeded-without-binding, invalid local binding과 unresolved strategy는 blocked다.
- production readiness도 구형 JSON read 시 메모리에서 재계산하며 read만으로 rewrite하지 않는다.
- TTS alignment는 `trim + NFC + SHA-256` narration fingerprint와 lowercase SHA-256 audio checksum을 검증한다.
- Shot은 기존 duration 비율로, Layer는 Shot 상대 구간으로 재배치하며 id/order/copy/grounding/asset strategy는 바꾸지 않는다.
- aligned plan JSON과 timing metadata는 read-only hydration에서 보존되고 visual AssetPack은 같은 layer id로 유지된다.
- Director 전용 preset/synthesis/file API, audio materialization, voice/speed 재생성 lifecycle을 구현했다.
- storage는 `CLIPPER_DATA_DIR/shortform-director/narration-audio` 아래 owner/project hash namespace를 사용한다.
- legacy project의 narrationAudio는 read-only hydration으로 empty pack을 보강하며 read만으로 파일을 rewrite하지 않는다.
- 실제 Supertonic 모델 실행은 하지 않았고 fake provider/file fixture로 순차·atomic·cleanup 경계를 검증했다.
- Director compiler는 대표 41.2초 snapshot을 visual 9, programmatic/text 11, TTS 7, caption 7의 기존 RenderRecipe로 만든다.
- 같은 project snapshot은 같은 recipe를 만들고 path/URL/provider raw payload/credential은 포함하지 않는다.
- compile 준비 실패는 HTTP 400이며 preview는 project에 저장하지 않는다.
- Angular는 recipe summary만 메모리에 보관하고 project mutation 뒤 무효화한다.
- sequence-card motion은 normalized geometry, cubic-out stagger와 소수점 4자리 frame state를 갖는다.
- 대표 diagram은 6.9초이며 start/reveal/hold/exit/end reference frame을 recipe에 포함한다.
- Angular는 기본 hold frame과 5개 frame 선택을 제공하고 exact opacity/translate/scale을 DOM에 적용한다.
- motion 계약에는 color/font/path/URL/provider/model/credential이 없다.
- 대표 diagram authored copy는 RenderRecipe motion과 Angular preview까지 그대로 보존된다.
- 새 diagram draft의 payload 누락·잘못된 step order·중복/prohibited copy와 non-diagram payload를 거부한다.
- malformed stored payload는 compile error이며, payload가 아예 없는 legacy plan만 generic fallback을 쓴다.
- staging은 representative ready project의 unique visual 6개와 narration 7개, 총 13개를 immutable copy로 고정한다.
- changed/missing/remote/wrong-kind visual, bound snapshot mismatch, narration checksum mismatch는 renderer 전에 차단한다.
- partial copy 실패는 ready stage를 남기지 않으며 source 변경 뒤에도 기존 staged copy는 바뀌지 않는다.
- project mutation 또는 recipe 재확인 뒤 Angular의 stage preview는 recipe preview와 함께 무효화된다.
- stage hydration은 exact recipe checksum, staged bytes와 visual/TTS input exact set을 다시 검증한다.
- sourceId resolver만 private absolute path를 반환하고 bundle/job reference JSON에는 path/URL/raw provider payload가 없다.
- production Director adapter token은 빈 배열이고 기존 generic renderer 회귀가 통과했다.
- queue/retry/cancel persistence는 새로 만들지 않고 future JobsService executor가 소유하도록 경계만 고정했다.
- representative conformance profile은 path resolve 없이 stage/recipe/input metadata만 소비한다.
- profile은 staged image/video/WAV, layered timeline, subtitle, text overlay, sequence-card motion, MP4/H.264/AAC, progress/cancel capability를 요구한다.
- output duration tolerance는 한 frame이고 raw benchmark metric은 자동 성능 합격이나 순위에 쓰지 않는다.
- 자동 통과 뒤 manual 7축 exact all-pass만 accepted이며 malformed/incomplete review는 accepted가 아니다.
- Remotion/Motion Canvas/FFmpeg/Manim을 current Angular/Nest/Electron/Python packaging과 공식 문서 기준으로 비교했다.
- Remotion은 layered media/text/caption과 Node progress/cancel API 적합성 때문에 첫 PoC 후보가 됐다.
- Motion Canvas는 vector diagram 강점이 있지만 Vite/browser runtime과 newer FFmpeg exporter의 packaged automation 경로를 추가 검증해야 한다.
- current simplified FFmpeg provider는 arbitrary composition layer와 sequence-card motion을 지원하지 않으므로 main compositor가 아니라 final media 역할로 고정했다.
- Manim 결과는 final adapter 내부에서 즉석 생성하지 않고 future asset materialization과 staging을 거쳐야 한다.
- nested Remotion dependency, representative projection/composition, full render, progress/cancel와 conformance report harness를 구현했다.
- raw AAC padding이 한 frame tolerance를 넘는 경우만 FFmpeg가 video copy + audio trim/re-encode + remux한다.
- representative automated result는 7/7 pass, elapsed 74,257ms, final output 8,082,314 bytes다.
- checkpoint 5개와 timeline spot frame에서 Korean clipping, safe-zone과 sequence-card state 파손은 보이지 않았다.
- synthetic media이므로 manual 7축은 pending이고 production accepted가 아니다.
- nested install tree 약 270MB, macOS arm64 compositor 약 17MB, development composition bundle 약 20MB로 관찰됐다.
- composition bundle cache/reuse, child-process RSS와 Electron packaging은 아직 하지 않았다.
- 실제 OpenAI provider 호출은 하지 않았다.
- 사용자 명시 요청 뒤 Angular/NestJS/web API 구현을 각각 `feat/shortform-director-foundation`에 커밋·push했다.
- Angular `bfaf720`, NestJS `9eb8994`와 `b72e74c`, web API `5a8424b`가 각 upstream feature branch와 exact sync다.
- `.codex`의 전체 설계·세션·handoff 기록은 `6a389a3`으로 `main`에 커밋·push했고, 이 최종 정합성 보정도 `.codex/main` current HEAD로 마감한다.
- dev merge/rebase, PR 생성, deploy, DB 초기화/migration 실행, runner/dev server/Electron 조작은 하지 않았다.

### 다음 우선순위

1. grounded ContentStrategy/native VideoPlan/eval/AssetPack/narration/RenderRecipe/motion preview와 두 10 credit 초기 policy를 리뷰한다.
2. 구현된 immutable stage/private execution bundle/adapter registry/conformance profile diff를 리뷰한다.
3. 구현된 isolated Remotion harness와 조건부 FFmpeg finalization diff를 리뷰한다.
4. source revision fingerprint 기반 composition bundle cache/reuse와 Chrome/compositor child tree peak RSS를 추가한다.
5. 실제 representative asset/audio로 full MP4와 5개 checkpoint still의 manual 7축을 검토한다.
6. Electron `extraResources` packaged smoke, offline startup, Windows x64와 supported macOS 범위를 검증한다.
7. Remotion license/Automator 비용과 packaging/quality gate 뒤에만 production adapter 후보로 승격하고, 실패 시 Motion Canvas PoC를 진행한다.
8. 선택 뒤 JobsService executor, output materialization과 render operation API/Angular queue UX를 구현한다.
9. stage retention 기간/GC policy를 별도 결정한다.
10. 실제 acquisition adapter operation/materialization과 provider benchmark를 별도 진행한다.
11. complex technical diagram 요구가 생기면 Manim 선행 materialization 계약과 PoC를 별도로 설계한다.
12. 실제 Vira exporter/API snapshot identity/auth 계약은 manual handoff 검증 뒤 별도로 설계한다.

### 안전 경계

- `.codex`는 `main`에서만 작업한다.
- 실제 cookie/env/JWT/provider secret은 출력·문서화·커밋하지 않는다.
- `clipper_docs`에는 아직 추가하지 않는다.
- commit/push/deploy/DB/runner/dev server/Electron 조작은 사용자 요청 전 수행하지 않는다.

## Previous Handoff: 2026-07-15 Shortform Source Images, Dev Integration, And Quality Direction

상세 기록:

- `.codex/records/sessions/2026/07/15.md`
- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- 이전 YouTube 상세: `.codex/records/sessions/2026/07/14.md`

### dev 통합 상태

- 8개 코드 저장소의 `dev`를 최신화했다.
- `feature/youtube-auth-diagnostics`가 있던 Angular, Electron, NestJS, web_api는 `merge/youtube-auth-diagnostics-into-dev-20260715`를 거쳐 `dev`에 통합했다.
- YouTube feature 병합 충돌은 없었다.
- 병합 HEAD:
  - `desktop/clipper_angular`: `9236798`
  - `desktop/clipper_electron`: `a77c57a`
  - `desktop/clipper_nestjs`: `f1e7d63`
  - `web/clipper_web_api`: `c1c9b31`
- 2026-07-14까지 작업한 YouTube 인증·다운로드 안정화, packaged Python 3.11 bootstrap, Dialog Highlight 413 수정이 현재 `dev`에 포함돼 있다.

### 숏폼 원본 이미지 기능

- URL 방식과 paste 방식의 원본 이미지를 에셋 교체 dialog의 `원본 이미지` 탭에서 표시한다.
- 선택한 원본 이미지는 기존 remote import/replace 경로를 사용해 클립 에셋으로 교체된다.
- paste HTML에서 중복 없는 HTTP(S) 이미지 URL을 추출하고 `data:`/`blob:` URL은 제외한다.
- NestJS는 paste의 원본 이미지를 project source에 저장하고 자동 클립 생성에서 media search보다 우선 사용한다.
- 사용자가 실제 제품 흐름을 수동 테스트해 정상 동작을 확인했다.

기능 브랜치와 커밋:

```text
feature/shortform-generation-plugin-fixes-and-updates

desktop/clipper_angular
  6fa73fa feat(shortform): add original image asset picker
  593e2e8 fix(shortform): hide unused creation controls
  904a1f8 Merge branch 'feature/shortform-generation-plugin-fixes-and-updates' into dev

desktop/clipper_nestjs
  45a0d1f fix(shortform): reuse pasted source images
  4e3adab Merge branch 'feature/shortform-generation-plugin-fixes-and-updates' into dev
```

### 숏폼 UI 정리

- 클립 생성 진행 모달의 동작 없는 닫기 아이콘과 관련 Material icon 의존성·스타일을 제거했다.
- 실제 숏폼 제작 페이지의 prompt mode 언어 선택 UI를 HTML 주석 처리했다.
- 내부 기본 언어값과 생성 요청의 language 데이터는 유지했다.

### 검증 상태

- Angular 원본 이미지 관련 focused tests: 97 passed.
- Angular build: passed.
- NestJS build: passed.
- paste 원본 이미지 생성 테스트 격리 실행: passed.
- 클립 생성 overlay focused test: 1 passed.
- legacy input panel focused tests: 16 passed.
- 관련 `git diff --check`: passed.
- Angular 전체 suite는 1,410/1,505 후 기존 TemplateBuilder timeout/browser disconnect로 종료됐지만 해당 spec 단독 실행은 76 passed였다.
- NestJS 기존 전체 generation-assets test file에는 constructor fixture 선행 실패가 있고 새 테스트 단독 실행은 통과했다.

### Clipper Studio 소개 문서

- 영문 elevator pitch와 프로젝트 소개 Markdown을 작성했다.
- 파일: `/Users/jina/project/adlight/CLIPPER_STUDIO_ABOUT.md`
- 루트는 git 저장소가 아니므로 이 파일은 commit 대상이 아니다.

### NotebookLM/Vira 기반 품질 고도화 방향 — 2026-07-15 PDF 기준 기록

> 아래 Vira 항목은 당시 PDF 기준의 이력이다. 현재 판단은 Active Handoff와 `.codex/design/VIRA_CURRENT_CODE_AUDIT_AND_CLIPPER_EVIDENCE_HANDOFF_2026-07-16.md`를 우선한다.

확인한 내부 자료:

- `/Users/jina/project/adlight/vira/vira-deck.pdf`
- `/Users/jina/project/adlight/vira/vira-IR_20260616 (3).pdf`

당시 이해:

- 목표는 NotebookLM 복제가 아니라 source grounding, AI creative director와 timeline orchestration을 Clipper의 마케팅·대량 생성 목적에 맞게 적용하는 것이다.
- Vira는 16개 마케팅 포맷/5개 그룹, 첫 3초·훅, 급상승 이상치, 키워드 추세와 단일 영상 8차원 분석·재현 레시피를 Clipper 입력으로 제공할 수 있다.
- 제품 루프는 Vira 진단 → Clipper 제작 → ViewX 측정 → 다음 진단·제작 환류다.
- 사용자 prompt 하나를 확장하는 수준이 아니라 BrandProfile, CampaignBrief, SourcePack, MarketContext와 ContentStrategy를 구조화한다.
- 한 번에 영상 하나가 아니라 포맷 × 훅 × 타깃 × 소구점 × CTA 조합의 content matrix로 수십·수백 개의 변형을 만든다.
- 영상 전체에 검색 에셋 또는 생성 에셋 한 방식을 강제하지 않고 Shot/Beat별 hybrid routing을 사용한다.
- 실제 사람·제품·증거는 실제/원본/검색 에셋, 추상 개념·분위기는 생성 이미지·영상, 비교·관계·숫자는 프로그램 모션과 도식을 우선한다.
- 렌더 모델은 `VideoPlan → Scene → Beat → Shot → Layer` 시간 기반 IR을 검토한다. 기존 clip은 편집 호환 단위로 남길 수 있다.
- Supertonic은 유지한다. 범용 timeline renderer는 Remotion/Motion Canvas, 특화 도식은 Manim, 반복 모션은 SVG/Lottie/Rive, 최종 encode/mux/audio mix는 FFmpeg를 우선 비교한다.

NotebookLM 사실 경계:

- 공식 자료로 Short가 약 60초·현재 영어 전용임을 확인했다.
- 일반 Video Overview의 Nano Banana contextual illustration과 Cinematic의 Gemini 3/Nano Banana Pro/Veo 3 creative-director 구조는 Google이 공개했다.
- Stable Video Diffusion, SDXL, Manim, Remotion, ChatTTS, ElevenLabs, Suno/Udio와 구체적인 FFmpeg 방식은 NotebookLM 내부 스택으로 확인되지 않았다. 재현 후보이지 확정 사실이 아니다.
- source grounding도 환각을 완전히 제거하지 않으므로 claim provenance와 품질 검증이 필요하다.

### 다음 기술 작업 우선순위

1. 현재 prompt shortform의 Angular/NestJS/Python/FFmpeg 호출·데이터·렌더 경계를 실제 코드로 감사한다.
2. 대표 source pack과 45~60초 PoC 한 편의 품질 기준을 정한다.
3. 기존 clip model compatibility와 새 timeline IR 도입 선택지를 비교한다.
4. Remotion, Motion Canvas, Manim, SVG/Lottie/Rive의 역할과 packaged 제약을 조사한다.
5. 최신 open/commercial image·video generation 모델의 품질·비용·latency·license matrix를 공식 자료 기준으로 만든다.
6. Vira → Clipper 최소 structured handoff schema를 정의한다.

### 기존 YouTube 후속 QA

- 연령 제한, YouTube Premium, anti-bot/추가 로그인 오류
- 수정 빌드의 완전히 빈 clean userData packaged 최초 실행
- 플러그인별 venv 또는 모델 설치 중단·손상 복구
- 인터넷 단절/package 설치 실패 시 다시 시도·앱 종료 흐름
- Windows packaged app의 cookie/EJS/metadata/download 전체 검증
- 필요 시 PO Token, 720p 및 AV1/VP9 fallback, offline wheel, `unhandled:` 명칭 분리
- Electron 업그레이드와 macOS Touch ID/Windows Hello passkey 지원

### 종료 시점 repo 상태

```text
desktop/clipper_angular   dev   clean, origin/dev 동기화, HEAD 904a1f8
desktop/clipper_electron  dev   clean, origin/dev 동기화, HEAD a77c57a
desktop/clipper_nestjs    dev   clean, origin/dev 동기화, HEAD 4e3adab
desktop/clipper_python    dev   clean, origin/dev 동기화, HEAD fdb14f4
web/clipper_web_api       dev   clean, origin/dev 동기화, HEAD c1c9b31
web/clipper_web_admin     dev   clean, origin/dev 동기화, HEAD 70cd4c8
web/clipper_web_client    dev   clean, origin/dev 동기화, HEAD 802ca57
web/clipper_infra         dev   clean, origin/dev 동기화, HEAD d10d54e
.codex                    main  dirty: 2026-07-15 session/design/handoff 문서, commit/push 안 함
```

### Next Session Prompt

```text
Using Superpowers.

작업 위치는 /Users/jina/project/adlight 입니다. 한국어로 답변해줘.

이전 세션에서 모든 코드 저장소를 dev 최신 상태로 맞추고 YouTube feature를 dev에 통합했다. 이어서 숏폼 URL/paste 원본 이미지를 자동 클립 생성과 에셋 교체 dialog에서 재사용하도록 구현·검증하고 Angular/NestJS dev에 병합했다. NotebookLM Short/Cinematic Video Overview와 Vira 자료를 바탕으로 프롬프트 숏폼 품질 고도화 및 하이브리드 생성 파이프라인의 초기 방향도 정리했다.

먼저 다음 문서를 읽어줘.

- .codex/AGENTS.md
- .codex/handoff/NEXT.md
- .codex/records/sessions/2026/07/15.md
- .codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md
- .codex/records/sessions/2026/07/14.md

Vira 자료가 필요하면 다음 PDF를 읽어줘.

- vira/vira-deck.pdf
- vira/vira-IR_20260616 (3).pdf

그다음 아래 저장소의 git status, 현재 브랜치, 최근 log와 upstream 동기화 상태를 확인해줘.

- desktop/clipper_angular
- desktop/clipper_electron
- desktop/clipper_nestjs
- desktop/clipper_python
- web/clipper_web_api
- web/clipper_web_admin
- web/clipper_web_client
- web/clipper_infra
- .codex

예상 상태는 모든 코드 저장소가 dev clean 및 origin/dev 동기화이고, .codex는 main에서 2026-07-15 session/design/handoff 문서만 dirty 상태다. 예상과 다른 변경은 revert/reset하지 말고 먼저 보고해.

다음 큰 작업은 현재 프롬프트 숏폼 생성 파이프라인을 코드 기준으로 감사하고, Vira-grounded input과 VideoPlan/Scene/Beat/Shot/Layer 기반 hybrid rendering architecture를 구체화하는 것이다. 아직 renderer나 image/video provider는 확정하지 않았다.

중요:

- .codex는 반드시 main에서만 작업해.
- 실제 cookie, env 값, JWT key, provider secret을 출력·문서화·커밋하지 마.
- clipper_docs에는 아직 문서를 추가하지 마.
- 커밋/푸시/배포/DB 초기화/runner 재시작은 내가 명시적으로 요청할 때만 해.
- 개발 서버나 Electron 앱도 내가 요청하기 전에는 실행하거나 종료하지 마.
- 상태 확인이 끝날 때까지 코드를 수정하지 마.

먼저 문서와 저장소 상태만 확인해서 보고한 다음 다음 지시를 기다려줘.
```

## Previous Handoff: 2026-07-14 YouTube Source Hardening And Packaged QA

상세 기록:

- `.codex/records/sessions/2026/07/14.md`
- `.codex/design/YOUTUBE_AUTH_DEBUG_TOOL_DESIGN_2026-07-13.md`
- `.codex/design/YOUTUBE_AUTH_DEBUG_TOOL_IMPLEMENTATION_PLAN_2026-07-13.md`
- `.codex/design/ELECTRON_YOUTUBE_PASSKEY_SUPPORT_REVIEW_2026-07-14.md`
- `.codex/design/PASSKEY_DEEP_DIVE_2026-07-14.md`

현재 구현/QA 상태:

- 실제 하이라이트 YouTube 경로는 공개 영상은 익명으로 먼저 확인하고, 인증 오류일 때 Electron 내장 로그인에서 내보낸 관리 쿠키 파일로 재시도한다.
- 채널 멤버십 필요와 일반 로그인 필요를 분리했고, Clipper Studio 로그인과 영상용 YouTube 계정이 별개임을 제품 UI에서 안내한다.
- 현재 Electron 35 영상용 로그인 창은 패스키 로그인을 지원하지 않는다. YouTube 로그인 액션이 있는 제품 오류에 `다른 방법 시도`를 눌러 비밀번호·2단계 인증 등을 사용하라는 안내를 표시한다.
- 대사/안무 하이라이트의 YouTube URL 입력에서 Enter를 누르면 각 화면의 영상 불러오기/아티스트 감지 액션을 실행한다.
- 영상용 계정 변경 전후 진단 결과와 개발용 계정 이메일 표시는 YouTube 디버그 페이지에만 유지한다. 제품 로그에는 계정 이메일을 기록하지 않는다.
- 성공 metadata의 `availability`, `ageLimit`, `formatCount`는 디버그 UI에 공개 상태·연령 제한·포맷 수로 구조화해 표시한다.
- 새 userData의 관리 쿠키 파일과 Electron 영상용 인증 세션은 비어 있다. 공개 영상 익명 실행은 쿠키를 만들지 않고, Electron 영상용 로그인 창을 닫을 때만 해당 세션을 Netscape 관리 파일로 내보낸다.
- YouTube가 같은 멤버십 영상에 간헐적으로 `Video unavailable. This video is not available`을 반환하는 현상을 실제 패키지 앱에서 확인했다.
- `unknown` yt-dlp 오류에는 URL/이메일/로컬 경로/쿠키/토큰/서명 값을 제거한 `providerErrorSummary`와 `providerErrorFingerprint`를 기록한다.
- 위 일반 `UNPLAYABLE` 계열이 metadata 단계에서 나오면 1초 뒤 같은 인증 전략으로 1회만 재확인한다. 구체적인 멤버십/비공개/연령 사유는 두 번째 실제 응답으로만 결정하며 추정하지 않는다.
- 다운로드의 `media_access_forbidden`은 동일한 품질 선택식을 유지한 채 새 미디어 주소를 얻도록 1초/3초 간격으로 최대 2회 재시도한다.
- Dialog Highlight web_api 413은 중복 LLM payload를 제거해 실제 실패 프로젝트의 요청을 약 172KB에서 약 13KB로 줄였고, web_api JSON limit도 1MB로 명시했다.
- YouTube 구조화 로그에는 영상 식별용 정규 `sourceUrl`만 기록한다. 공유 URL 쿼리, 서명된 미디어/provider URL, 쿠키, 이메일, 토큰은 기록하지 않는다.
- macOS 기본 앱 메뉴를 복원해 `Cmd+Q`를 정상화했고, macOS 앱 종료와 Windows/Linux 창 닫기에 취소가 기본인 네이티브 종료 확인을 연결했다. 확인 후 자식 runtime을 정리하며 OS session end에서는 확인을 생략한다.
- packaged 온라인 bootstrap은 시스템 Python을 사용하지 않고 uv 관리 Python 3.11을 명시적으로 설치한다. base와 플러그인별 venv 모두 `--python 3.11 --managed-python`을 사용한다.
- Python 3.9 또는 실행 불가능한 base venv는 앱 소유 경로만 재생성하고, Python 3.11은 정상이나 yt-dlp/EJS가 빠진 경우에는 패키지 설치만 재실행한다. 모든 검증 성공 후에만 marker를 기록한다.
- 필수 runtime 준비 실패 시 앱 진입을 차단한다. 네이티브 모달의 `로컬 파일로 계속` 경로는 제품 요구사항에서 제거했고 `다시 시도`/`앱 종료`만 제공한다.

macOS packaged 수동 QA:

- 멤버십 미보유/보유 계정 전환에 따라 동일 영상의 실패/성공과 실제 사용 계정 표시가 기대대로 동작했다.
- 전체 초기화 후 멤버십 영상이 `members_only`로 안정적으로 분류되는 것을 확인했다. 새 일반 `UNPLAYABLE` 내부 재확인은 수동 재현하지 못했으며 자동 테스트로만 검증했다. 같은 현상이 다시 발생할 때 trace로 확인한다.
- 이전 공개 영상 download 403 사례는 재검증 시 오류 없이 성공해 재시도 분기를 수동 재현하지 못했다. 다음 실제 403 발생 시 trace로 검증한다.
- 2026-07-14 16:49에 web_api 413으로 실패했던 동일 YouTube URL의 Dialog Highlight 작업을 19:39에 다시 실행해 성공했다. 보관함 결과와 추출 클립을 확인했고 눈에 띄는 품질 저하는 없었다.
- 비공개 영상은 권한 안내가 정확히 표시됐다. 해당 영상을 소유한 영상용 YouTube 계정으로 로그인한 뒤 metadata와 Dialog Highlight 전체 작업이 성공했다.
- 새 `test1` macOS 사용자 첫 실행에서 기존 base venv 명령이 Command Line Tools Python 3.9.6을 선택해 Python 3.10 이상인 yt-dlp 요구사항을 만족하지 못하는 배포 차단 버그를 재현했다.
- 수정 후 임시 clean HOME에서 앱 내장 uv가 CPython 3.11.14를 다운로드하고 yt-dlp 2026.7.4/EJS 0.8.0을 설치하는 것을 확인했다. 임시 Python 3.9 venv도 3.11.14로 재생성됐다.
- 새 패키지를 실제 `test1` 계정에서 실행해 기존 Python 3.9.6 부분 설치를 감지하고 CPython 3.11.14로 재생성한 뒤 yt-dlp 2026.07.04/EJS 0.8.0을 준비해 정상 진입하는 것을 확인했다.
- 같은 userData로 두 번째 실행했을 때 runtime 검사는 약 222ms 만에 `check.started`에서 `check.ready`로 끝났고 Python 다운로드, base venv 재생성, yt-dlp/EJS 재설치가 반복되지 않았다.
- 두 번째 실행 중 최초 생성된 `clipper_video_render` 플러그인 venv도 관리 CPython 3.11.14를 사용해 26개 패키지를 정상 설치했다. 플러그인별 중단·손상 복구 검증은 별도 보류다.

외부 브라우저 쿠키의 현재 제품 경계:

- YouTube 디버그 페이지는 명시적인 `browser: chrome` 등 외부 브라우저 쿠키 진단을 제공한다.
- 현재 packaged 하이라이트 제품 경로는 외부 Chrome 쿠키를 기본 사용하지 않는다. Electron은 관리 쿠키 파일 경로만 NestJS에 명시적으로 전달하며, 실행 중 진단도 `cookiesFromBrowser=미설정`, `autoBrowserCookies=꺼짐`이었다.
- `CLIPPER_YTDLP_COOKIES_FROM_BROWSER`/`CLIPPER_YTDLP_AUTO_BROWSER_COOKIES`로 선택적으로 켤 수 있는 기반 코드는 있지만 현재 제품 기본 UX/설정은 아니다. 따라서 외부 Chrome 쿠키 성공 경로는 출시 필수 QA에서 제외하고 선택 기능을 실제 채택할 때 검증한다.

패스키 관련 현재 결정:

- Electron `35.7.0`은 이번 작업에서 변경하지 않는다.
- 패스키 지원은 Electron 업그레이드, `app.configureWebAuthn()`, macOS 서명 entitlement, macOS/Windows packaged QA가 함께 필요하므로 별도 작업으로 보류한다.
- 개발·CI Node와 Electron 내장 Node는 별도이지만 완전히 무관하지 않다. Electron 40 이상으로 올릴 때는 Node 22 빌드/테스트 경로와 Electron 내장 Node 24 main/preload/utility/yt-dlp EJS 경로를 모두 검증한다.
- 현재 제품 우회 안내와 재개 조건은 `.codex/design/ELECTRON_YOUTUBE_PASSKEY_SUPPORT_REVIEW_2026-07-14.md`를 기준으로 한다.
- 패스키의 역사, FIDO2/WebAuthn 구조, 종류, macOS·Windows·Android 동작, 보안 효과와 한계는 `.codex/design/PASSKEY_DEEP_DIVE_2026-07-14.md`에 별도 학습 문서로 정리했다.

추후 검증으로 명시적으로 보류:

- 연령 제한, YouTube Premium, anti-bot/추가 로그인 오류
- 수정 빌드의 완전히 비어 있는 clean userData packaged 최초 설치 경로. 실제 `test1` 검증은 수정 전 빌드가 만든 Python 3.9 부분 설치를 수정 빌드가 복구하는 경로였고, clean 경로의 동일한 uv 명령은 격리 자동 검증까지만 완료했다.
- 플러그인별 venv 또는 모델 설치가 중단·손상된 상태의 복구
- 오프라인/패키지 설치 실패 시 `다시 시도`/`앱 종료` packaged 수동 QA
- Windows packaged app 전체 cookie/EJS/metadata/download 검증

추후 필요성에 따라 구현할 항목:

- PO Token 도입
- 720p 품질 fallback
- AV1/VP9 명시적 fallback
- 오프라인 wheel 앱 내장
- 전역 예외 로그의 `unhandled:` 명칭을 예상된 HTTP 실패와 진짜 미처리 예외로 분리

현재 repo 상태:

```text
desktop/clipper_angular   feature/youtube-auth-diagnostics  clean, origin 동기화
desktop/clipper_electron  feature/youtube-auth-diagnostics  clean, origin 동기화
desktop/clipper_nestjs    feature/youtube-auth-diagnostics  clean, origin 동기화
desktop/clipper_python    dev                               clean
web/clipper_web_api       feature/youtube-auth-diagnostics  clean, origin 동기화
web/clipper_web_admin     dev                               clean
web/clipper_web_client    dev                               clean
web/clipper_infra         dev                               clean
.codex                    main                              clean, origin 동기화
```

이번 세션 커밋:

- `desktop/clipper_angular`: `77b4ce4`, `af07d62`, `06c3098`, `03d07ba`
- `desktop/clipper_electron`: `fb60b95`, `70d3374`, `fbf860e`, `756be44`, `97ab0f3`, `6f694df`
- `desktop/clipper_nestjs`: `cf8cb52`, `83f322e`, `b49815f`, `89a6f39`
- `web/clipper_web_api`: `b593062`
- `.codex`: `7877237`, `dae4665`와 이 세션 최종 문서 커밋

위 코드 커밋과 `.codex` 문서는 각 원격 feature 브랜치 및 `.codex/main`에 push했다. deploy/DB 초기화/runner 재시작은 수행하지 않았다. 실제 cookie/env/key/provider secret은 출력·문서화·커밋하지 않았다. `clipper_docs`에는 추가하지 않았다.

### Next Session Prompt

```text
Using Superpowers.

작업 위치는 /Users/jina/project/adlight 입니다. 한국어로 답변해줘.

이전 세션에서 Clipper Studio의 YouTube 인증·다운로드 안정화, macOS packaged QA, Python 3.11 runtime bootstrap 복구, Electron 패스키 검토와 문서화를 완료했다. 모든 변경사항은 저장소별 feature 브랜치와 .codex/main에 commit/push된 상태다.

먼저 다음 문서를 읽고 현재 상태를 정확히 이어받아줘.

- .codex/AGENTS.md
- .codex/handoff/NEXT.md
- .codex/records/sessions/2026/07/14.md
- .codex/design/YOUTUBE_AUTH_DEBUG_TOOL_DESIGN_2026-07-13.md
- .codex/design/YOUTUBE_AUTH_DEBUG_TOOL_IMPLEMENTATION_PLAN_2026-07-13.md
- .codex/design/ELECTRON_YOUTUBE_PASSKEY_SUPPORT_REVIEW_2026-07-14.md
- .codex/design/PASSKEY_DEEP_DIVE_2026-07-14.md

그다음 아래 저장소의 git status, 현재 브랜치, 최근 log와 upstream 동기화 상태를 확인해줘.

- desktop/clipper_angular
- desktop/clipper_electron
- desktop/clipper_nestjs
- desktop/clipper_python
- web/clipper_web_api
- web/clipper_web_admin
- web/clipper_web_client
- web/clipper_infra
- .codex

현재 예상 상태:

- desktop/clipper_angular: feature/youtube-auth-diagnostics, clean, origin 동기화
- desktop/clipper_electron: feature/youtube-auth-diagnostics, clean, origin 동기화
- desktop/clipper_nestjs: feature/youtube-auth-diagnostics, clean, origin 동기화
- web/clipper_web_api: feature/youtube-auth-diagnostics, clean, origin 동기화
- desktop/clipper_python: dev, clean
- web/clipper_web_admin: dev, clean
- web/clipper_web_client: dev, clean
- web/clipper_infra: dev, clean
- .codex: main, clean, origin 동기화

현재 구현된 주요 내용:

- 공개 YouTube 영상은 익명으로 먼저 처리하고 인증 오류일 때만 Electron 영상용 로그인에서 생성한 관리 쿠키로 재시도한다.
- 일반 로그인, 채널 멤버십, 비공개, 연령 확인, Premium, anti-bot 오류를 분리해 사용자 안내와 영상용 계정 선택 액션을 제공한다.
- YouTube 인증 디버그 페이지에서 runtime, 쿠키, 계정 전환 전후 인증 상태, 인증 전략별 metadata/download를 확인할 수 있다.
- 일반 UNPLAYABLE metadata 응답은 1초 뒤 같은 전략으로 1회 재확인하고, download 403은 새 미디어 주소를 얻어 1초/3초 간격으로 최대 2회 재시도한다.
- YouTube 주요 과정은 구조화 로그에 남기며 이메일, 쿠키, 토큰, 서명된 미디어 URL은 기록하지 않는다.
- Dialog Highlight web_api 413 문제는 중복 payload 제거와 1MB JSON limit 명시로 수정됐다.
- packaged 최초 실행은 시스템 Python 대신 uv 관리 Python 3.11을 준비하고, 잘못되거나 부분 설치된 app-owned venv와 yt-dlp/EJS를 복구한다.
- 대사/안무 하이라이트의 YouTube URL 입력에서 Enter로 실행할 수 있다.
- macOS Cmd+Q와 Windows/Linux 창 닫기에 종료 확인을 표시한다.
- 현재 Electron 35 영상용 로그인 창에서는 패스키가 진행되지 않을 수 있어 `다른 방법 시도` 후 비밀번호·2단계 인증을 사용하도록 안내한다. Electron 업그레이드와 실제 패스키 지원은 별도 작업으로 보류했다.

macOS packaged에서 확인된 내용:

- 멤버십 미보유/보유 영상용 계정 전환에 따른 동일 영상 실패/성공
- 비공개 영상 권한 안내, 권한 보유 계정 로그인 후 metadata와 Dialog Highlight 성공
- 이전 web_api 413 실패 영상의 재실행 성공과 결과 품질 확인
- 새 macOS test1 사용자에서 기존 Python 3.9 부분 설치를 감지해 관리 Python 3.11.14로 복구하고 정상 진입
- 같은 userData의 두 번째 실행에서 runtime 준비를 재사용하고 불필요한 재설치를 하지 않음

추후 검증으로 남긴 항목:

- 연령 제한, YouTube Premium, anti-bot/추가 로그인 오류
- 수정 빌드의 완전히 비어 있는 clean userData packaged 최초 실행
- 플러그인별 venv 또는 모델 설치가 중단·손상된 상태의 복구
- 인터넷 단절 또는 package 설치 실패 시 다시 시도/앱 종료 흐름
- Windows packaged app의 cookie/EJS/metadata/download 전체 검증

필요성에 따라 나중에 구현할 항목:

- PO Token
- 720p 품질 fallback
- AV1/VP9 명시적 fallback
- 오프라인 wheel 앱 내장
- 전역 예외 로그의 `unhandled:` 명칭 분리
- Electron 업그레이드와 macOS Touch ID/Windows Hello 패스키 지원

중요:

- 예상과 다른 dirty 변경이 있으면 임의로 revert/reset하지 말고 먼저 보고해.
- .codex는 반드시 main 브랜치에서만 작업해.
- 실제 쿠키, env 값, JWT key, provider secret을 출력·문서화·커밋하지 마.
- clipper_docs에는 아직 문서를 추가하지 마.
- 커밋/푸시/배포/DB 초기화/runner 재시작은 내가 명시적으로 요청할 때만 해.
- 개발 서버나 Electron 앱도 내가 요청하기 전에는 실행하거나 종료하지 마.
- TypeORM multi-DB, raw API response, NestJS feature layer와 상대 import, Angular 4파일 분리와 Material token 규칙을 지켜.
- 상태 확인이 끝날 때까지 코드를 수정하지 마.

먼저 문서와 저장소 상태만 확인해서 보고한 다음, 내가 다음 작업을 지시할 때까지 기다려줘.
```

## Previous Handoff: 2026-07-13 YouTube Auth Diagnostics And Packaged Runtime

상세 기록:

- `.codex/records/sessions/2026/07/13.md`
- `.codex/design/YOUTUBE_AUTH_DEBUG_TOOL_DESIGN_2026-07-13.md`
- `.codex/design/YOUTUBE_AUTH_DEBUG_TOOL_IMPLEMENTATION_PLAN_2026-07-13.md`

현재 상태:

- 개발자 모드의 `YouTube 디버그` 페이지를 `디버그 로그` 바로 위에 추가했다.
- Electron 쿠키 파일/내장 세션 상태·삭제·전체 초기화·위치 열기, 내장/외부 로그인, 네 인증 전략, metadata/download 분리 진단을 구현했다.
- `clipper_nestjs`는 실제 `SourceService` yt-dlp 실행 경로를 재사용하는 raw diagnostic API를 제공한다.
- packaged local-api build는 `resources/auth/user-jwt-public.local.pem`을 선택하고 package 내부에는 안정적인 `auth/user-jwt-public.pem` 이름으로 포함한다.
- Electron은 `35.7.0`으로 고정했고 내장 Node.js `22.16.0`을 확인했다.
- 관리 venv는 `yt-dlp[default]>=2025.12.8`을 설치하며 기존 venv는 EJS marker가 없으면 다음 package app 실행에서 보강한다.
- 자동 검증은 Angular/NestJS 관련 test/build, Electron build 및 전체 133 tests까지 통과했다.

macOS packaged local-api 수동 결과:

- 전체 초기화 + 인증 없음 + 기본 공개 URL metadata 성공
- 같은 조건 실제 download 성공: 종료 코드 0, 약 3.9초, 약 97.6 MB
- 회원 전용 영상 `k_TGyt6E29w`는 종료 코드 1과 `Join this channel` 오류로 실패해 접근 제한 재현
- `Made for Kids` 공개 영상은 metadata/download 모두 성공했으며 기대 동작

확인된 누락과 다음 우선순위:

1. `authRequired`가 `Join this channel`/`members-only`를 분류하지 못한다. 로그인 필요와 멤버십 entitlement 필요를 구분해야 한다.
2. 성공 metadata의 `availability`, `age_limit`, format count를 구조화해 raw JSON 검색 없이 확인할 수 있게 한다.
3. 멤버 권한 계정으로 Electron 내장 로그인 + 관리 쿠키, 외부 로그인 + browser cookie 성공 경로를 확인한다.
4. 연령 제한, private/premium, IP·guest session 기반 anti-bot 오류를 별도로 검증한다.
5. 신규 설치/업데이트 시 관리 venv bootstrap이 오프라인에서 실패할 때 앱 진입 차단, 명확한 원인 안내, 재시도, 부분 설치 복구가 구현됐는지 감사한다.
6. Windows packaged app에서 동일한 cookie/EJS/metadata/download 동작을 스모크한다.

현재 repo 상태:

```text
desktop/clipper_angular   dev...origin/dev  dirty
desktop/clipper_electron  dev...origin/dev  dirty
desktop/clipper_nestjs    dev...origin/dev  dirty
desktop/clipper_python    dev...origin/dev  clean
web/clipper_web_api       dev...origin/dev  clean
web/clipper_web_admin     dev...origin/dev  clean
web/clipper_web_client    dev...origin/dev  clean
web/clipper_infra         dev...origin/dev  clean
.codex                    main...origin/main dirty
```

변경사항은 아직 commit/push하지 않았다. dirty worktree를 revert/reset하지 말고 현재 변경을 이어서 사용한다. secret-bearing 파일, 실제 cookie/env/key 값은 출력·문서화·커밋하지 않는다. `clipper_docs`에는 아직 추가하지 않는다.

## Previous Handoff: 2026-07-10 Dev Merge, Release, Download, Packaging Follow-up

이 섹션은 2026-07-10 당시 기준이다. 현재 작업 기준은 위 2026-07-13 handoff이며, 아래 2026-07-07 auth/session/license/provider 섹션은 상세 설계/이력으로만 본다.

auth/session/license/credit/provider routing 구현은 dev merge 후 통합 정리까지 진행됐다. 이후 release/version 운영을 다시 이어서 dev 환경에서 앱 identity를 `Clipper Studio` 기준으로 정리했고, release DB를 dev 한정으로 reset해 0.0.1부터 다시 시작했다.

secret-bearing 파일이나 env 값은 절대 출력하거나 커밋하지 않는다. `clipper_docs`에는 아직 추가하지 말고, 설계/운영 변경은 `.codex` 문서에만 반영한다.

현재 세션 요약:

- `.codex/records/sessions/2026/07/10.md`
- `.codex/design/RELEASE_VERSION_STATUS_2026-07-10.md`
- `.codex/operations/env-runtime/records/2026/07/10-auth-runtime-env.md`
- `.codex/operations/env-runtime/records/2026/07/10-dev-deploy-notes.md`
- `.codex/operations/windows-packaging/records/2026/07/10-windows-runner-dev-release.md`

현재 코드 repo 상태:

- `desktop/clipper_angular`, `desktop/clipper_electron`, `desktop/clipper_nestjs`, `desktop/clipper_python`, `web/clipper_web_api`, `web/clipper_web_admin`, `web/clipper_web_client`, `web/clipper_infra` 모두 `dev...origin/dev` clean 상태로 확인했다.
- 마지막 주요 커밋:
  - `web/clipper_web_api`: `6d39cac fix: expose public download manifest`
  - `web/clipper_web_admin`: `415b723 fix: improve release detail modal spacing`
  - `web/clipper_web_client`: `8efca4b feat: split landing download actions`
  - `web/clipper_infra`: `d10d54e test: update release runner app identity fixture`
  - `desktop/clipper_electron`: `8eb9ed0 chore: rename packaged app to Clipper Studio`
  - `desktop/clipper_nestjs`: `0a42a0b chore: align runtime app name with Clipper Studio`
  - `desktop/clipper_angular`: `612e0b2 chore: update desktop UI app name`
  - `desktop/clipper_python`: `fdb14f4 docs: clarify python credential boundary`

즉시 확인할 운영 항목:

1. m2-stage에 `web_api` 최신 dev를 배포한 뒤 `GET /downloads/latest`가 stable Windows artifact를 반환하는지 확인한다.
2. m2-stage에 `web_client` 최신 dev를 배포한 뒤 `https://dev.clipperstudio.ai` Windows 버튼이 installer URL로 이동하는지 확인한다.
3. web_admin release console에서 0.0.1 stable target과 public download manifest가 같은 artifact를 가리키는지 확인한다.
4. Windows runner PC에서 runner container health와 token/start-token alignment를 다음 remote build 전에 확인한다.
5. Mac download는 아직 준비중 상태로 둔다.

남은 큰 작업:

- admin permission guard 세분화: `/operators`, API key 수정/삭제, release publish 등 민감 admin API를 role/status 기반으로 보호한다.
- operator role/status DB schema와 guard를 더 엄격하게 정리한다.
- provider credential rotation 운영 검증을 계속한다.
- session/device 개인정보 보관 기간, 삭제/탈퇴 시 처리 정책, 보안 로그 보관 정책은 별도 정책 결정 후 구현한다.
- cross-repo plugin metadata SoT는 아직 미결정이다.

### Next Session Prompt

```text
Using Superpowers.

작업 위치는 /Users/jina/project/adlight 입니다. 한국어로 답변해줘.

먼저 아래 문서를 읽고 현재 상태를 파악해줘.
- .codex/AGENTS.md
- .codex/handoff/NEXT.md
- .codex/design/AUTH_SESSION_LICENSE_PROVIDER_TARGET_DESIGN_2026-07-07.md
- .codex/design/AUTH_SESSION_LICENSE_PROVIDER_REMAINING_PHASES_2026-07-08.md
- .codex/design/RELEASE_VERSION_STATUS_2026-07-10.md
- .codex/operations/env-runtime/records/2026/07/10-auth-runtime-env.md
- .codex/operations/env-runtime/records/2026/07/10-dev-deploy-notes.md
- .codex/operations/windows-packaging/records/2026/07/10-windows-runner-dev-release.md
- .codex/records/sessions/2026/07/10.md
- .codex/records/sessions/2026/07/07.md

이번 세션은 dev merge 이후 운영/배포 follow-up을 이어서 진행한다.
secret-bearing 파일이나 env 값은 절대 출력하거나 커밋하지 마.
clipper_docs에는 아직 문서를 추가하지 말고, 설계 변경은 .codex 문서에만 반영해.

먼저 모든 관련 repo의 git status/log를 확인해줘.
현재 기준 브랜치는 각 repo `dev`다. 새 작업이 필요하면 dev 최신에서 feature branch를 별도로 만들고 진행해.

대상 repo:
  desktop/clipper_angular
  desktop/clipper_electron
  desktop/clipper_nestjs
  desktop/clipper_python
  web/clipper_web_api
  web/clipper_web_admin
  web/clipper_web_client
  web/clipper_infra

주의:
- dirty worktree가 있으면 임의로 revert/reset하지 말고 먼저 보고해.
- 실제 구현은 작은 phase별 커밋으로 나눈다.
- TypeORM multi-DB, raw API response, NestJS feature layer 규칙, 상대 import, Angular 4파일 분리/Material token 규칙을 지킨다.

우선 m2-stage에 `web_api`와 `web_client` 최신 dev를 배포하고, `GET /downloads/latest`와 landing Windows 다운로드 버튼을 검증해줘. 그 다음 admin permission guard/operator role-status 정리 또는 provider credential rotation 운영 검증 중 우선순위를 확인하고 진행해줘.
```

## Historical Handoff: 2026-07-07 Auth/Session/License/Provider Implementation Entry

이 섹션은 구현 이력으로 남긴다. 현재 다음 작업 기준은 위 2026-07-10 Active Handoff다.

### 2026-07-07 설계 결정 요약

채택:

```text
short-lived JWT access token
+ long-lived opaque refresh token
+ server-side session table
+ refresh token rotation
+ desktop one-time code exchange
```

인증/세션:

- Google OAuth 단독 로그인 유지
- 앱 메인 화면 진입 전 로그인 필요
- desktop deep link는 `clipper://auth/callback?token=<JWT>`가 아니라 `clipper://auth/callback?code=<one-time-code>`
- web_api가 one-time code를 교환해 access/refresh token을 발급
- access token은 RS256 JWT
- refresh token은 opaque random string
- refresh token 원문은 클라이언트에만 저장, 서버 DB에는 hash 저장
- Electron은 token bundle을 `safeStorage`로 저장
- local browser dev는 별도 dev fallback 허용 가능
- user JWT와 operator JWT는 audience/type/session 정책을 분리
- 2026-07-09 follow-up에서 `JWT_SECRET` user/operator fallback은 제거됐다. user JWT는 `USER_JWT_PRIVATE_KEY`/`USER_JWT_PUBLIC_KEY`, operator/admin JWT는 `OPERATOR_JWT_PRIVATE_KEY`/`OPERATOR_JWT_PUBLIC_KEY` 또는 `OPERATOR_JWT_SECRET`을 사용한다.

local NestJS:

- local NestJS는 최종 auth truth가 아니다.
- local NestJS는 JWT public key PEM으로 access token을 1차 검증한다.
- public key는 secret이 아니며 MVP에서는 앱 resource PEM으로 포함한다.
- 최종 session revoke/license/credit/operation 판단은 web_api가 한다.
- refresh token과 provider key는 local NestJS/Python plugin에 넘기지 않는다.

이용권:

- 한 user의 active license는 최대 1개
- active license가 있으면 새 승인 license는 queued
- credit 소진 시 active license는 active_depleted
- queued license는 자동 시작하지 않는다.
- 사용자가 "다음 이용권 시작"을 눌러야 queued license가 active 된다.
- 기존 credit/기간 흡수/병합 없음
- MVP에서 credit top-up은 만들지 않음

operation/credit:

- 크레딧 차감 단위는 provider API 호출이 아니라 사용자-facing 제품 operation이다.
- billing strategy MVP는 `charge_then_refund`
- 제품 시작 시 차감, local job 성공 시 유지, 실패 시 refund ledger 생성
- 멀티 디바이스 초과 차감은 web_api `/operations/start` transaction/lock으로 막는다.
- stale running operation은 MVP에서 자동 환불보다 admin review가 안전하다.

operation_policies:

- `operation_key`를 안정 식별자로 사용한다. 예: `dance_highlight.extract`
- DB 내부 id는 코드에서 직접 참조하지 않는다.
- `operation_id`, `execution_mode`, `enabled` 기반 설계는 MVP에서 제거했다.
- `billing_strategy`, `operation_run.status`, `credit_ledger.type`, `provider_scope`는 enum으로 관리한다.
- `OPERATION_DEFINITIONS` code registry + 명시적 seed/upsert로 row를 생성한다.
- seed는 `ON CONFLICT (operation_key) DO NOTHING` 원칙으로 기존 관리자 수정값을 덮어쓰지 않는다.
- 관리자 CRUD는 Read + 제한적 Update만 허용한다.
- Create/Delete는 일반 관리자 CRUD로 열지 않는다.

플러그인 스토어:

- MVP에서 플랜별 플러그인 노출/잠금/상위 플랜 유도 정책은 제외한다.
- MVP에서 플러그인 스토어 목록은 web_api DB가 아니라 로컬 앱 manifest/catalog/Angular visible list 기준으로 유지한다.
- web_api는 "플러그인 카드를 보여줄지"가 아니라 "실제 제품 실행을 허용할지"를 판단한다.
- desktop UI plugin/navigation metadata SoT는 현재 `desktop/clipper_angular/src/core/navigation/app-navigation-metadata.ts`다.
- cross-repo plugin metadata SoT는 아직 미결정이다. `desktop/clipper_nestjs` plugin catalog, `desktop/clipper_python/plugins/*/manifest.json`, Angular navigation metadata 사이에 `displayName`/`description` drift 가능성이 남아 있다.
- `shortform_url`, `shortform_paste`, `shortform_prompt`, `variation` 같은 virtual workflow는 Python manifest가 없어서 NestJS catalog와 Angular metadata 중복이 특히 남는다. 다음 설계에서 shared JSON/catalog, generated adapter, 또는 drift validate script 중 하나를 결정한다.
- repo/build boundary가 섞이므로 Angular TS 파일을 NestJS에서 직접 import하거나 NestJS TS 파일을 Angular에서 직접 import하는 방식은 현재 채택하지 않는다.
- 하이라이트 진입 화면은 `app-page contentAlign="center"`를 사용한다. 로컬 파일 입력도 YouTube와 동일하게 `영상 확인` 화면을 먼저 거친 뒤, 확인 버튼에서만 크레딧 확인 모달을 띄운다. 확인 카드 back wording은 `다시 선택`이다.

provider:

- provider key는 설치형 앱에 넣지 않는다.
- provider credential은 DB 암호화 저장 중심으로 통일한다.
- OpenAI env fallback은 제거됐다. OpenAI runtime은 DB credential이 없으면 `not_configured`로 실패한다.
- provider endpoint는 user JWT + operationRunId 소유권 + provider scope enum을 확인한다.
- provider_usage 신규 기록/관리자 조회는 2026-07-09 보류로 전환했다. provider endpoint는 owner/scope authz만 유지하고, 사용자 크레딧 원장은 `credit_ledger`만 사용한다.

### 구현 진행 현황 (2026-07-08 KST)

작업 브랜치:

```text
feature/auth-session-license-provider-20260707
```

완료:

```text
Phase 1: web_api session/refresh/desktop exchange
  web/clipper_web_api
    04d5c2e feat(auth): add session token service
    11844cf feat(auth): persist user sessions
    9aba1ea feat(auth): sign user session tokens
    3a2a340 feat(auth): add desktop session endpoints

Phase 2: Electron token store/deep link
  desktop/clipper_electron
    d7408b3 feat(auth): exchange desktop login codes
    b989d39 chore(auth): include public key resource path
  desktop/clipper_angular
    6c62b42 fix(auth): align deep link payload type

Phase 3: Angular auth refresh layer
  desktop/clipper_electron
    70e207f feat(auth): refresh desktop token bundles
  desktop/clipper_angular
    051306f feat(auth): refresh access tokens

Phase 4: local NestJS JWT prefilter and user token relay
  desktop/clipper_nestjs
    e33baf6 feat(auth): verify local user access tokens
  desktop/clipper_angular
    c2e2838 feat(auth): attach user token to local api
  desktop/clipper_electron
    cdcd8b8 chore(auth): pass public key path to local api

Phase 5a: web_api operation policy/ledger foundation
  web/clipper_web_api
    91257f0 feat(operations): add billable operation ledger

Phase 5b-1: shortform.create operationRunId authz and reporting
  web/clipper_web_api
    72953c4 feat(operations): authorize script generation runs
  desktop/clipper_nestjs
    4db3593 feat(shortform): report billable operation runs

Phase 5b-2: provider usage and dialog_highlight.extract operationRunId authz/reporting
  web/clipper_web_api
    7ea3014 feat(operations): record script provider usage
    f31591d feat(dialog): authorize provider llm runs
  desktop/clipper_nestjs
    2619e8e feat(dialog): report billable llm operation runs

Phase 5b-3: dance_highlight.extract workflow operation reporting
  desktop/clipper_nestjs
    f6acb38 feat(dance): report billable workflow runs

Phase 5b-4a: media.search provider operation context/authz transition
  desktop/clipper_nestjs
    41ddb34 feat(media): relay operation context to search provider
  web/clipper_web_api
    ce81289 feat(media): authorize operation search usage

Phase 6: license one-active/queue/depleted lifecycle
  web/clipper_web_api
    4b89ec6 feat(billing): add queued license lifecycle

Phase 7-1: OpenAI provider credential DB resolver
  web/clipper_web_api
    78907c6 feat(providers): resolve OpenAI credentials from database

Phase 7-2: provider credential admin API/source-status
  web/clipper_web_api
    93ea025 feat(providers): expose credential sources in admin api
  web/clipper_web_admin
    df5d6f2 feat(admin): display provider credential sources

Phase 7-3: OpenAI credential admin create/edit UI
  web/clipper_web_admin
    79a631c feat(admin): manage OpenAI provider credentials

Phase 7-4: Naver provider_credentials migration
  web/clipper_web_api
    d7797d1 feat(providers): migrate Naver keys to provider credentials

Phase 7-5: OpenAI env fallback opt-in cleanup
  web/clipper_web_api
    5e14ae9 feat(providers): gate OpenAI env fallback

Phase 7-6: legacy Naver key runtime cleanup
  web/clipper_web_api
    c246366 chore(providers): remove legacy Naver key runtime

Phase 7-7: OpenAI runtime credential status API
  web/clipper_web_api
    4501b36 feat(providers): expose OpenAI runtime status

Phase 7-8: OpenAI runtime status admin UI
  web/clipper_web_admin
    a1f8ba4 feat(admin): show OpenAI runtime status

Phase 7-9: Naver runtime credential status
  web/clipper_web_api
    9191dab feat(providers): expose Naver runtime status
    6313ef1 fix(providers): type Naver credential client id column
  web/clipper_web_admin
    961f18c feat(admin): show Naver runtime status
```

Phase 3 구현 메모:

- Electron main에 `clipper:auth:refreshToken` IPC를 추가하고 refresh token rotation 응답의 새 token bundle을 저장한다.
- Angular `AuthBackend`/bridge에 `refreshToken()`을 추가했다.
- `AuthStore.loadSession()`은 exp 임박 access JWT를 proactive refresh하고, `/me` 401에는 refresh single-flight 후 한 번 retry한다.
- refresh token 원문은 Angular로 전달하지 않고 Electron main token bundle 저장소 안에만 둔다.

Phase 4 구현 메모:

- local NestJS `CLIPPER_AUTH_MODE=jwt`에서 user access JWT를 RS256/public key로 1차 검증한다.
- 검증 claim은 `iss=clipper-web-api`, `aud=clipper-user`, `typ=user`, `sub`, `sid`, `exp`를 확인한다.
- public key는 `CLIPPER_AUTH_JWT_PUBLIC_KEY`, `USER_JWT_PUBLIC_KEY`, `CLIPPER_AUTH_JWT_PUBLIC_KEY_PATH` 순으로 읽고 캐시한다.
- `web/clipper_web_api` commit `5bcefbf`에서 `USER_JWT_PRIVATE_KEY`가 설정된 경우 user JWT 서명이 module-level `JWT_SECRET`보다 private key를 우선 사용하도록 고쳤다. 후속으로 operator/admin JWT도 별도 key/secret으로 분리하고 legacy `JWT_SECRET` fallback을 제거해야 한다.
- Angular는 local NestJS `/v1/*` 요청에만 user bearer token을 붙인다. web_api `/me`/auth 요청에는 붙이지 않는다.
- Angular WebSocket은 access token을 URL query가 아니라 `Sec-WebSocket-Protocol`의 `clipper.jwt.<token>`로 전달한다.
- local NestJS `AuthContext`는 검증된 `sessionId`와 `accessToken`을 보존해 web_api 호출에 relay할 수 있다.
- `WebApiClient.postJson()`은 per-request bearer relay를 지원한다.
- Shortform web_api script generator는 현재 user bearer token을 `/llm/script` 호출에 relay한다.
- Electron은 bundled local NestJS 시작 env에 packaged public key path 기본값을 주입한다. `CLIPPER_AUTH_MODE=jwt`를 강제하지는 않는다.
Phase 5a 구현 메모:

- `modules/operations` feature를 추가했다.
- admin DB migration `1783500000000-CreateOperationLedger`가 `operation_policies`, `operation_runs`, `credit_ledger`, `provider_usage`를 만든다.
- `operation_billing_strategy`, `operation_run_status`, `credit_ledger_type`, `credit_ledger_reason`, `provider_scope` enum을 추가했다.
- `provider_scopes`는 제품 operation별 허용 provider scope 배열로 JSONB 저장한다.
- 기본 operation definitions는 user-facing 제품 단위만 seed한다: `shortform.create`, `dialog_highlight.extract`, `dance_highlight.extract`.
- provider call 단위인 `media.search`는 operation policy로 seed하지 않는다.
- `OperationPolicySeeder`는 app boot 시 `ON CONFLICT (operation_key) DO NOTHING`으로 없는 row만 seed한다.
- `/operations/:operationKey/quote`, `/operations/start`, `/operations/:runId/succeed`, `/operations/:runId/fail`를 추가했다.
- `/operations/start`는 active license bucket을 `pessimistic_write`로 잠그고 charge ledger를 남긴다.
- `/operations/:runId/fail`은 charge ledger 기준으로 refund ledger를 남기고 `tokens_used`를 되돌린다.
- OpenAPI raw response 계약을 `docs/api/openapi.yaml`에 추가했다.

Phase 5b-1 구현 메모:

- web_api `/llm/script`에 user JWT guard를 적용했다.
- `/llm/script` request DTO에 `operationRunId`를 필수로 추가했다.
- `/llm/script`는 `OperationsService.authorizeProviderUse(userId, operationRunId, 'openai')`를 통과해야 provider 호출을 수행한다.
- `/llm/script` 성공 시 `provider_usage`에 `openai` 사용 기록을 남긴다.
- OpenAPI에 `/llm/script` provider-backed endpoint 계약을 추가했다.
- local NestJS에 `WebApiOperationRunService`를 추가했다.
- local shortform clip generation은 bearer token이 있을 때 `/operations/start`로 `shortform.create` run을 만들고, `/llm/script`에 `operationRunId`를 전달한다.
- local shortform generation 성공 시 `/operations/:runId/succeed`, 생성 중 오류 시 `/operations/:runId/fail`을 호출한다.
- operation reporting 실패는 원래 생성 결과/오류를 가리지 않도록 warn 로그만 남긴다.

Phase 5b-2 구현 메모:

- web_api `OperationsService.recordProviderUsage()`와 TypeORM repository 저장 경로를 추가했다.
- web_api `/dialog-highlight/llm`에 user JWT guard를 적용했다.
- `/dialog-highlight/llm` request DTO에 `operationRunId`를 필수로 추가했다.
- `/dialog-highlight/llm`은 `OperationsService.authorizeProviderUse(userId, operationRunId, 'openai')`를 통과해야 provider 호출을 수행한다.
- `/dialog-highlight/llm` 성공 시 `provider_usage`에 `openai` 사용 기록을 남긴다. metadata에는 endpoint와 dialog LLM operation명을 남긴다.
- OpenAPI에 `/dialog-highlight/llm` provider-backed raw response 계약을 추가했다.
- local NestJS `WorkflowRunContext`에 auth context를 추가하고, `JobQueueEntry`를 통해 in-memory로 access token을 전달한다. job snapshot에는 access token을 저장하지 않는다.
- local dialog workflow는 bearer token이 있을 때 `/operations/start`로 `dialog_highlight.extract` run을 만들고, 모든 dialog LLM web_api 호출에 같은 `operationRunId`와 bearer token을 전달한다.
- local dialog workflow 완료 시 `/operations/:runId/succeed`, provider/workflow 오류 시 `/operations/:runId/fail`을 호출한다.
- dialog operation reporting 실패는 원래 workflow 결과/오류를 가리지 않도록 warn 로그만 남긴다.

Phase 5b-3 구현 메모:

- local NestJS `JobsService`에 `dance_highlight -> dance_highlight.extract` billable workflow mapping을 추가했다.
- `dance_highlight` workflow job은 caller bearer token이 있을 때 `/operations/start`로 `dance_highlight.extract` run을 만든다.
- workflow가 `completed`로 끝나면 `/operations/:runId/succeed`, `failed`/기타 terminal 상태면 `/operations/:runId/fail`을 호출한다.
- job snapshot에는 access token을 저장하지 않는 기존 Phase 5b-2 원칙을 유지한다.
- `dialog_highlight`와 `shortform.create`는 이미 각각 executor/service 내부에서 reporting하므로 JobsService generic mapping에 넣지 않았다.

Phase 5b-4a 구현 메모:

- local shortform 자동 생성 미디어 검색은 `shortform.create` operation run이 있을 때 remote media provider 호출에 caller bearer token과 `operationRunId`를 전달한다.
- local `RemoteProxyClipperStudioImageSearchProvider`는 caller bearer token을 `Authorization: Bearer ...`로 우선 사용하고, body에 `operationRunId`를 포함한다.
- web_api `/media/search`는 transition 호환을 위해 optional user JWT guard를 사용한다.
- `/media/search` body에 `operationRunId`가 있으면 `OperationsService.authorizeProviderUse(userId, runId, 'naver_image')`를 통과한 뒤 Naver 검색을 실행하고, 성공 시 `provider_usage`를 기록한다.
- `/media/search` body에 `operationRunId`가 없으면 기존 setup/manual 호출 호환을 위해 검색을 허용한다. 이는 dance setup 단계가 아직 제품 operation run 전에도 검색을 수행할 수 있기 때문이다.
- provider 호출 단위인 `media.search`는 별도 operation policy로 추가하지 않았다.
- `/llm/variation` provider routing은 이번 범위에서 의도적으로 skip한다. Variation 기능/UX와 과금 기준을 먼저 파악해야 하므로, 임의로 `variation.generate` 같은 billable operation을 추가하지 않는다.
- 이 skip은 known deferred gap이다. 따라서 "모든 provider endpoint가 user JWT + operationRunId로 전환됨"이라고 표현하지 않는다.

Phase 6 구현 메모:

- `licenses.status` enum을 추가했다: `queued`, `active`, `active_depleted`, `expired`, `depleted`, `cancelled`.
- 기존 license row는 migration에서 만료/소진 여부에 따라 `expired`, `active_depleted`, `active`로 backfill한다.
- `starts_at`/`expires_at`는 queued license를 위해 nullable로 변경했다.
- 운영자 승인 시 현재 active/active_depleted license가 남아 있으면 새 license는 `queued`로 생성한다.
- 현재 active license 조회/operation charge/legacy consume은 `active` 상태의 license만 차감 대상으로 사용한다.
- credit이 0이 되면 license는 `active_depleted`가 된다. 실패 refund로 credit이 복구되면 유효기간 내에서는 다시 `active`가 된다.
- `GET /licenses/current`는 현재 started license만 잔액으로 계산하고, queued summary를 함께 반환한다.
- `POST /licenses/queued/start`를 추가했다. remaining credit이 있는 active license나 running refundable operation이 있으면 409를 반환한다.
- queued start 시 기존 depleted/expired started license를 종료 상태로 확정하고, 첫 queued license에 `startsAt`/`expiresAt`를 설정해 active로 전환한다.
- OpenAPI raw response 계약에 license lifecycle 상태와 queued start endpoint를 반영했다.

Phase 7-1 구현 메모:

- admin DB에 `provider_credentials` 테이블을 추가했다.
- `ProviderCredentialsModule`과 `OpenAiCredentialService`를 추가했다.
- OpenAI credential resolver는 active DB credential만 복호화해서 사용한다. DB credential이 없으면 `not_configured`로 실패하며 env fallback은 없다.
- DB credential 복호화 실패/빈 secret/미설정은 secret 원문 없이 503으로 매핑한다.
- `shortform.create` `/llm/script`와 `dialog_highlight.extract` `/dialog-highlight/llm` 경로가 새 resolver를 통해 OpenAI bearer key를 가져온다.
- 기존 Naver `naver_search_keys` rotation 모델은 아직 그대로 유지한다.
- `/llm/variation` provider routing/과금 정책은 여전히 defer 상태다. 이번 슬라이스는 variation provider routing을 건드리지 않았다.

Phase 7-2 구현 메모:

- web_api 기존 `/admin/api-keys` surface를 유지하면서 Naver legacy key와 OpenAI provider credential을 함께 반환한다.
- Naver 응답은 기존 `clientId`, `secretMasked`, `dailyUsed`, `dailyLimit`, `priority` shape를 유지하고, `provider='naver'`, `source='database'`, `maskedKey`를 추가했다.
- OpenAI DB credential 응답은 `provider='openai'`, `source='database'`, `maskedKey`, `status`, `priority`를 반환한다. secret 원문/암호문은 반환하지 않는다.
- active OpenAI DB credential이 없으면 OpenAI row를 반환하지 않는다. `env:openai` synthetic row는 제거됐다.
- `/admin/api-keys` create/update/delete/activate가 `provider='openai'` DB credential도 처리한다. active 전환 시 같은 provider의 기존 active DB credential은 standby로 내린다.
- web_admin API key 화면은 provider-aware response를 매핑하고 OpenAI source를 표시한다.
- 기존 Naver `naver_search_keys` rotation 모델은 아직 유지했다.

Phase 7-3 구현 메모:

- web_admin OpenAI section에 DB credential 추가/수정 form을 연결했다.
- OpenAI credential 생성은 `/admin/api-keys`에 `provider='openai'`, `label`, `secret`, `priority`를 보낸다.
- OpenAI credential 수정은 `label`, `priority`를 보내고, secret input이 비어 있으면 기존 secret 유지를 위해 `secret` field를 보내지 않는다.
- OpenAI DB row는 활성전환/수정/삭제 액션을 제공한다.
- OpenAI env fallback synthetic row와 `env에서 관리` 표시는 제거됐다.
- web_admin mock API도 OpenAI create response를 provider-aware shape로 반환한다.
- 기존 Naver create/edit/test UI는 변경하지 않았다.
- secret 원문은 목록 응답/화면에 표시하지 않는다.
- 기존 Naver `naver_search_keys` rotation 모델은 아직 유지했다.

Phase 7-4 구현 메모:

- `provider_credentials`에 Naver rotation/search에 필요한 nullable metadata 컬럼을 추가했다: `client_id`, `daily_used`, `daily_limit`, `usage_date`.
- admin migration `1783800000000-AddNaverProviderCredentialMetadata`는 기존 `naver_search_keys.client_secret_enc` 암호문을 복호화하지 않고 그대로 `provider_credentials.secret_enc`로 복사한다.
- migration은 `naver_search_keys` row를 `provider='naver'`로 backfill한다.
- 여러 active legacy row가 있거나 이미 active Naver provider credential이 있으면 `provider_credentials`의 one-active unique index 충돌을 피하도록 legacy active row를 standby로 강등한다.
- `ProviderBackedApiKeysRepository`를 추가했고, Nest `ApiKeysRepository` injection을 기존 `TypeOrmApiKeysRepository`에서 provider-backed adapter로 전환했다.
- Search/rotation service의 `NaverSearchKey` 계약은 유지했다. 따라서 `/media/search`, `/admin/api-keys/test`, daily limit/rotation 경로는 provider-backed repository를 통해 동작한다.
- `ApiKeysService.list()`는 provider repository에서 Naver row를 직접 provider view로 중복 표시하지 않고, Naver row는 adapter가 반환한 legacy-compatible view로만 표시한다.
- 기존 `naver_search_keys` table/entity/repository는 migration source와 rollback context로 남아 있다. 이번 슬라이스에서는 drop하지 않았다.
- OpenAI env fallback은 2026-07-09 follow-up에서 제거됐다.

Phase 7-5 구현 메모:

- OpenAI env fallback은 2026-07-09 follow-up에서 완전 제거됐다.
- `OpenAiCredentialService`는 더 이상 `OPENAI_API_KEY` 또는 `OPENAI_API_KEY_ENV_FALLBACK_ENABLED`를 runtime credential 결정에 사용하지 않는다.
- `/admin/api-keys` env synthetic row도 제거됐다.
- active DB credential이 있으면 DB credential을 사용하고, 없으면 provider call은 secret 원문 없이 503으로 실패한다.

Phase 7-6 구현 메모:

- 더 이상 런타임에서 쓰지 않는 `NaverSearchKeyEntity`와 `TypeOrmApiKeysRepository`를 삭제했다.
- admin TypeORM datasource entities에서 `NaverSearchKeyEntity` 등록을 제거했다.
- `ApiKeysRepository` runtime injection은 Phase 7-4의 `ProviderBackedApiKeysRepository` 유지다.
- `naver_search_keys` table을 생성하는 historical migration과 provider_credentials backfill migration의 raw SQL 참조는 보존했다.
- 이번 슬라이스는 table drop migration을 추가하지 않았다. 실제 운영 DB migration/rollback 안전성을 확인한 뒤 별도 슬라이스에서 판단한다.
- `rg "NaverSearchKeyEntity|TypeOrmApiKeysRepository" src`는 결과가 없어야 한다.

Phase 7-7 구현 메모:

- `OpenAiCredentialService.inspectRuntime()`을 추가했다.
- 새 admin endpoint는 `GET /admin/api-keys/providers/openai/runtime-status`다.
- 응답은 secret 원문/암호문을 반환하지 않는다.
- 응답 shape는 `provider`, `ready`, `source`, 선택적 `activeCredentialId`, 선택적 `reason`이다.
- `source='database'`이면 active DB credential을 복호화 시도해 ready 여부를 판단한다.
- `source='env'`는 더 이상 나오지 않는다.
- `source='none'`, `reason='not_configured'`이면 active DB credential이 없다는 뜻이다.
- 실제 OpenAI provider 호출은 하지 않는다. 운영 검증 endpoint는 비용/외부 의존성 없이 runtime credential 선택 상태를 확인하는 용도다.

Phase 7-8 구현 메모:

- web_admin API models에 `OpenAiRuntimeStatus`를 추가했다.
- `ApiKeysApiService.getOpenAiRuntimeStatus()`가 `GET /admin/api-keys/providers/openai/runtime-status`를 호출한다.
- API key 화면 OpenAI section 상단에 runtime strip을 추가했다.
- runtime strip은 `Runtime`, status chip, DB/none source만 표시한다.
- mock API도 OpenAI DB credential 상태만 반환한다.
- secret 원문/암호문은 화면에 표시하지 않는다.
- 실제 OpenAI 호출/테스트 버튼은 추가하지 않았다.

Phase 7-9 구현 메모:

- web_api에 `GET /admin/api-keys/providers/naver/runtime-status`를 추가했다.
- `RotationService.previewRuntime()`은 DB mutation이나 실제 Naver provider 호출 없이 현재 사용할 후보 credential과 usable/exhausted/disabled count를 계산한다.
- `SearchService.inspectRuntime()`은 후보 credential 복호화 가능 여부만 확인하고 secret 원문/암호문을 반환하지 않는다.
- 응답 shape는 `provider`, `ready`, `source`, `usableCredentialCount`, `exhaustedCredentialCount`, `disabledCredentialCount`, 선택적 `activeCredentialId`, 선택적 `reason`이다.
- web_admin API key 화면 Naver section 상단에 runtime strip을 추가했다.
- runtime strip은 status chip과 `사용 가능/소진/제외` count 및 선택적 activeCredentialId만 표시한다.
- 실제 Naver 검색 호출은 추가하지 않았다. 기존 `테스트 검색` 버튼이 실제 provider 호출 검증 경로로 남아 있다.
- 로컬 admin DB migration smoke 중 `ProviderCredentialEntity.clientId` nullable union 컬럼의 TypeORM inferred type이 `Object`가 되어 Postgres metadata validation이 실패하는 문제가 발견되어, `client_id` column type을 `varchar`로 명시했다.

다음 구현 진입점:

```text
Phase 9 provider credential 운영 hardening
```

2026-07-09 현재 Phase 8C operation policy admin MVP는 완료됐다.
`web_api`는 `/admin/operation-policies` list/update를 제공하고, `web_admin`은 `/operation-policies`의 `크레딧 정책` 화면에서 `creditCost`만 수정한다.
`enabled`, `updatedBy`, 변경 이력/audit은 후속 phase로 남아 있다.

2026-07-09 현재 Phase 8E external API usage log는 보류로 전환했다.
사용자 결정에 따라 API/provider usage 기록은 일단 필요하지 않다고 보고, `web_admin`의 `API 사용` nav/route/page/service/mock을 제거했다.
`web_api`도 `GET /admin/provider-usage`, `OperationsService.recordProviderUsage/listProviderUsage`, TypeORM provider_usage repository/entity 등록, `/media/search`/`/llm/script`/`/dialog-highlight/llm`의 provider usage 기록 호출을 제거했다.
초기 operation ledger migration에서는 더 이상 `provider_usage`를 만들지 않고, 이미 적용된 DB는 `DropProviderUsage1784700000000` migration으로 `provider_usage` table과 `provider_scope` type을 제거한다. 신규 runtime 기록/조회는 없다.
provider credential delete는 API usage log 제거와 무관하게 hard delete가 아니라 `deleted_at` soft delete를 유지한다. `disabled`는 재활성화 가능한 제외 상태이고, delete는 운영 목록/runtime candidate/rotation에서 제외되는 soft-deleted 상태다.
2026-07-09 현재 Phase 8D follow-up도 완료됐다.
`web_api`는 `credit_ledger.balance_after` snapshot column을 추가했고, 새 charge/refund ledger row에 작업 처리 후 최종 잔여 credit을 저장한다. 기존 과거 row는 `balance_after=null`로 둔다.
`GET /operations/ledger`와 `GET /admin/members/:userId/credit-ledger`는 `from`, `to`, `type=charge|refund` filter를 지원한다. date-only filter는 KST 날짜 경계로 해석한다.
`web_client` `/app/credits`와 `web_admin` `/members` credit ledger drawer에는 시작일/종료일/유형 필터와 `처리 후 잔여` column이 추가됐다.

Variation 과금 정책은 2026-07-09에 확정됐다.
차감 지점은 `영상 생성` 또는 `변형하고 영상까지` 버튼이며, 생성 영상 1개당 20 credits다. 예: 원본 1개 + 변형 19개로 총 20개 영상이 생성되면 400 credits.
2026-07-09 현재 Phase 8J Variation render billing 첫 구현도 완료됐다.
`web_api`는 `variation.render` operation policy와 `per_generated_video` pricing unit을 추가했고, `generatedVideoCount`로 quote/start 비용을 계산한다.
`desktop_angular`는 `영상 생성`/`변형하고 영상까지`에서 실제 생성 영상 수로 quote/confirm을 띄우고, 차감 후 snackbar를 표시한다.
`desktop_nestjs`는 Variation render queue submission 전에 `/operations/start`를 호출하고, submission 성공/실패를 succeed/fail로 보고한다.
`web_admin` `/operation-policies`는 `베리에이션 영상 생성`, `생성 영상 1개당` 단위를 표시한다.
2026-07-09 현재 Phase 8J queue submission 이후 개별 render job 실패 부분 환불도 완료됐다.
`web_api`는 `POST /operations/:runId/refund`와 `credit_ledger.reference_key` idempotency column/index를 추가했다.
`desktop_nestjs`는 Variation batch record에 billing snapshot을 저장하고, failed item을 감지하면 `variation.render:<batchId>:<jobId>` reference key로 실패 job 1개당 `variation.render` 단가를 부분 환불 보고한다.
`operation_runs.status`는 queue submission 성공 기준 `succeeded`를 유지하고 `refundedCredits`만 누적 증가한다.
`/llm/variation`은 AI copy preview 성격으로 보고 provider usage 기록 전환은 이번 범위에서 제외한다.

2026-07-09 현재 Phase 8G operator/admin auth hardening 첫 구현이 완료됐다.
admin DB에 `operator_sessions` table을 추가했고, operator refresh token은 원문 저장 없이 hash만 저장하며 refresh 시 rotation한다.
`/admin/auth/login`은 access/refresh token bundle과 `sid`가 포함된 operator access JWT를 발급한다.
`/admin/auth/refresh`, `/admin/auth/logout`, `/admin/auth/sessions`, `DELETE /admin/auth/sessions/:id`를 추가했다.
`OperatorJwtStrategy`는 `typ='operator'`, `sid`, active `operator_sessions` row를 확인한다.
`web_admin`은 admin refresh token을 저장하고 일반 admin API 401에서 refresh 1회 후 원 요청을 재시도한다.
2026-07-09 follow-up에서 `operators.role`/`operators.status` DB column을 추가했고, operator auth/JWT validate는 payload role이 아니라 DB role/status를 기준으로 판단한다.
inactive operator는 login/refresh/JWT validate를 통과하지 못한다.
`/operators`는 super-admin 전용 route/API가 됐고, `내 로그인 세션`은 header profile menu의 `로그인 세션` action에서 `/operator-sessions`로 이동해 확인한다.
operator seed는 `OPERATOR_SEED_EMAIL`/`OPERATOR_SEED_PASSWORD` 계정을 `super-admin`/`active`로 보장한다.
일반 관리자 seed가 필요하면 `OPERATOR_SEED_OPERATOR_EMAIL`/`OPERATOR_SEED_OPERATOR_PASSWORD`를 추가로 설정하면 같은 seed script가 `operator`/`active` 계정을 생성 또는 보정한다.
user JWT는 `USER_JWT_PRIVATE_KEY`/`USER_JWT_PUBLIC_KEY` 또는 `USER_JWT_PRIVATE_KEY_PATH`/`USER_JWT_PUBLIC_KEY_PATH`가 없으면 발급/검증하지 않는다.
operator/admin JWT는 `OPERATOR_JWT_PRIVATE_KEY`/`OPERATOR_JWT_PUBLIC_KEY`, 해당 `*_PATH`, `OPERATOR_JWT_SECRET`, 또는 `OPERATOR_JWT_SECRET_PATH` 없이는 발급/검증하지 않는다.
local/dev의 권장 위치는 gitignore된 `web/clipper_web_api/.secrets/`이며, `.env`에는 secret 값 대신 path를 둔다.
2026-07-09 중단 지점:
`web_api`, `web_admin`, `.codex`에 operator role/status, super-admin 제한, operator session page 분리, optional regular operator seed 문서화 변경이 남아 있으며 커밋/푸시 대상이다.
로컬 admin DB에는 예전 seed 계정인 `admin@example.local`이 남아 있어 운영자 목록이 3개로 보일 수 있다. 운영 DB 정책은 삭제보다 `inactive` 처리를 우선 검토한다.
남은 Phase 8G 후속은 API key write/release write/operation policy write 같은 민감 admin endpoint permission guard, operator invite/deactivate write API 실제 구현, 일반 operator 권한 smoke, 실제 local/staging login smoke다.

2026-07-09 현재 Phase 9 provider credential rotation 첫 hardening을 진행했다.
Naver credential 모델은 `active` 1개와 `standby` 여러 개를 전제로 한다. `standby`는 자동 rotation 후보이고, `active`가 daily limit에 도달하거나 Naver 429를 받으면 `exhausted`로 내려간 뒤 사용 가능한 `standby` 중 priority가 가장 빠른 키가 `active`로 승격된다.
수동 전환은 별도 `다음 키로 전환` 버튼을 두지 않고, 기존 row별 `활성` action으로 처리한다. 이 버튼은 운영자가 특정 `standby` 키를 직접 골라 현재 active로 올리는 manual failover다.
`disabled`는 runtime/rotation 후보에서 제외되며, admin UI에서는 직접 활성화하지 않고 먼저 Naver `대기`로 `standby` 상태에 되돌린다. active/standby 키는 `제외` 버튼으로 `disabled` 처리할 수 있다.
Naver 자동 rotation은 한도에 도달한 standby를 후보에서 제외하도록 보강했다.
Naver active 키를 `제외`하거나 `standby`로 내릴 때 active 0개 상태가 생기지 않도록 web_api에서 guard한다. 사용 가능한 standby가 있으면 같은 요청 안에서 즉시 active로 승격하고, 없으면 요청을 거부한다.
2026-07-09 follow-up에서 OpenAI는 Naver식 rotation 대상이 아니라 단일 DB key 모델로 정리했다. OpenAI DB credential은 최대 1개만 허용하고, label은 `OpenAI API Key`, status는 `active`, priority는 `0`으로 고정한다. OpenAI 키가 이미 있으면 admin UI의 `+ 키 추가` 버튼은 숨긴다.
Naver runtime status는 후보 credential status를 응답한다. active 후보면 `DB credential 준비됨`, active 없이 standby 후보만 있으면 admin UI에서 `대기 키 자동 승격 가능` warn 상태로 표시한다.
OpenAI는 Naver와 같은 quota rotation을 적용하지 않는다. admin UI의 OpenAI row에는 `수정`, `삭제`, `테스트`만 남기고 `활성`/`제외`/`대기` 상태 작업은 표시하지 않는다.
2026-07-09 follow-up에서 admin API key page 작업 UX를 정리했다. Naver의 `테스트`는 별도 column으로 두고, `작업` column은 `수정`, `삭제`, `...`만 노출한다. `활성`, `제외`, `대기`는 Naver `...` menu 안에 있고, 삭제/상태 변경은 browser confirm이 아니라 admin modal로 확인한다. OpenAI DB credential test도 추가했으며, OpenAI API 연결 결과는 `ok`, HTTP status, safe error code만 표시한다. OpenAI masked key column은 prefix 일부와 suffix 4자만 표시하고, secret/암호문/raw credential UUID는 표시하지 않는다.
2026-07-09 follow-up에서 OpenAI env fallback을 완전 제거했다. `OpenAiCredentialService`, `ScriptService`, `DialogHighlightLlmService`, `VariationService`는 더 이상 `OPENAI_API_KEY`를 runtime credential로 읽지 않고, admin API key UI도 `source='env'`/fallback 표시를 제거했다.

### 권장 구현 순서

큰 작업이므로 한 번에 끝내려고 하지 말고 phase별로 나눈다.

```text
Phase 0
  dev 최신화, 새 브랜치 생성, repo별 현재 테스트 명령 확인

Phase 1: web_api session/refresh/desktop exchange
  user_sessions table
  desktop_auth_codes table
  RS256 access JWT 발급/검증
  refresh token hash 저장/rotation
  /auth/desktop/exchange
  /auth/refresh
  /auth/logout
  /auth/sessions 최소 구현

Phase 2: Electron token store/deep link
  deep link token -> code 변경
  exchange API 호출
  auth.bin token bundle 저장
  safeStorage production fallback 정책 정리
  local NestJS public key PEM app resource 포함

Phase 3: Angular auth refresh layer
  access token proactive/reactive refresh
  single-flight refresh
  /me restore 개선
  logout/relogin branch 처리

Phase 4: local NestJS JWT prefilter and user token relay
  protected product start route Authorization 수신
  JWT public key PEM load/cache
  RS256/aud/iss/typ/exp 1차 검증
  WebApiClient Bearer relay
  @BillableOperation(operationKey) 또는 동등 interceptor

Phase 5: web_api operation policy/ledger/provider authz
  operation_policies table
  enum 관리
  OPERATION_DEFINITIONS seed/upsert
  /operations/:operationKey/quote
  /operations/start
  /operations/:runId/succeed
  /operations/:runId/fail
  operation_runs/credit_ledger/provider_usage
  provider endpoints user JWT + operationRunId 보호

Phase 6: license one-active/queue/depleted 정리
  active_depleted
  queued user-start endpoint
  자동 queued activation 제거

Phase 7: provider credential 통합
  Naver 중심 key 모델을 provider_credentials로 일반화
  OpenAI DB encrypted credential
  admin API key page source/status 정리
```

### 2026-07-07 구현 진입 판단

현재 대화 컨텍스트가 길어졌다. 실제 구현은 새 세션에서 시작하는 것이 안전하다.

이 세션에서 한 일:

- auth/session/license/provider target design을 `.codex/design/AUTH_SESSION_LICENSE_PROVIDER_TARGET_DESIGN_2026-07-07.md`에 정리
- operation policy를 `operation_key`, enum, code registry + seed/upsert 방식으로 정리
- 플랜별 플러그인 노출/잠금은 MVP 제외로 결정
- 플러그인 스토어 목록은 로컬 앱 기준 유지로 결정
- 이 `NEXT.md`를 다음 세션용 구현 진입 handoff로 갱신

## Previous Handoff: 2026-07-03 Installed App Integration

이 섹션은 이전 기준이다. 설치형 앱 integration 상세 이력으로만 본다.

Release/version-management work is still paused. The current priority is installed desktop app correctness, local/manual verification, and then Windows packaged verification. Do not resume 0.0.4 stable publish or updater detection until the installed app behavior below is accepted.

### Next Session Prompt

```text
Using Superpowers.

작업 위치는 /Users/jina/project/adlight 입니다. 한국어로 답변해줘.

먼저 .codex/handoff/NEXT.md, .codex/records/sessions/2026/07/02.md, .codex/records/sessions/2026/07/03.md 를 읽고 현재 상태를 파악해줘.
이번 세션은 설치형 앱 완성/검증을 우선하며, release/version publish 작업은 아직 재개하지 마.
secret-bearing 파일이나 env 값은 절대 출력하거나 커밋하지 마.

현재 app repo들은 integration/plugin-runtime-isolation-review2-20260703 브랜치에 있고 원격에 push되어 있다.
.codex는 git 연결/푸시 없이 로컬 문서 컨텍스트로만 사용 중이다.

먼저 각 repo의 git status/log를 확인하고, 아래 우선순위대로 진행해줘:
1. Mac mini에서 최신 packaged app/local-api 빌드로 fresh manual smoke
2. Windows test PC에서 reset-windows.ps1 fix 단독 확인 후 원격 web_api 기준 packaged smoke
3. 남은 TODO 중 높은 우선순위부터 처리
4. Mac/Windows 설치형 앱 smoke가 승인되기 전까지 release/version publish는 재개하지 않기
```

### Current Branch/Commit State

These are the current integration branch heads as of the latest session update. They have been pushed.

```text
desktop/clipper_angular:  integration/plugin-runtime-isolation-review2-20260703 @ 376e4f3 Enable opening Variation from plugin store
desktop/clipper_nestjs:   integration/plugin-runtime-isolation-review2-20260703 @ 3655c12 Cover packaged BGM lookup from resources root
desktop/clipper_electron: integration/plugin-runtime-isolation-review2-20260703 @ 079cef8 Merge feature/plugin-runtime-isolation into dev
desktop/clipper_python:   integration/plugin-runtime-isolation-review2-20260703 @ dec0286 Merge feature/plugin-runtime-isolation into dev
web/clipper_web_api:      integration/plugin-runtime-isolation-review2-20260703 @ 46cf304 Merge feature/plugin-runtime-isolation into dev
```

Recent 2026-07-03 follow-up fixes on the integration branch:

```text
desktop/clipper_angular:
  5564501 Fix virtual workflow install after ffmpeg consent
  a643353 Sync selected plugin detail after install
  376e4f3 Enable opening Variation from plugin store

desktop/clipper_nestjs:
  c54cb8b Fix packaged shortform BGM asset lookup
  3655c12 Cover packaged BGM lookup from resources root
```

See `.codex/records/sessions/2026/07/03.md` for the complete session record.

Latest feature-branch commits now pushed:

```text
desktop/clipper_angular:
  3b11280 fix(auth): keep newer desktop session
  c7db2e4 fix(shell): remove native navigation tooltips
  ab68b2e fix(store): block concurrent plugin installs
  ca71561 fix(shortform): polish clip generation defaults
  eb767a2 fix(template-builder): render default template thumbnails

desktop/clipper_nestjs:
  26ba140 fix(plugins): gate runtime on asset install state
  9b475cf feat(dialog): run LLM stages through web api
  e7f9441 feat(shortform): use web api and Supertonic providers
  19015ee fix(errors): classify provider and YouTube failures
  4abd210 chore(env): remove deprecated .env.packaged file
  3133015 feat(template-builder): add default shortform template

desktop/clipper_python:
  4405cad fix(tts): preserve pitch for playback speed

desktop/clipper_electron:
  df952b1 fix(auth): redact desktop login tokens
  ebe4cae fix(runtime): reset plugin asset state locally
  d8e6cba feat(build): add local API packaged app build

web/clipper_web_api:
  c4d9779 fix(auth): show desktop login completion page
  5c8f96f feat(desktop): allow local provider proxy calls
  9532093 fix(dialog): log LLM calls and extend timeout
```

Do not push any of these directly to `dev`. Push feature branches only, unless the user explicitly changes the release plan.

`desktop/clipper_angular` and `desktop/clipper_nestjs` also have pushed helper branches named
`fix/default-template-thumbnails`; those commits were fast-forward merged back into
`feature/plugin-runtime-isolation`.

### Session Flow Summary

1. Started from the previous release handoff: `release-platform-integration` had been merged/pushed to latest `dev`; Windows runner had confirmed release `0.0.4 build 10` build/sign/S3 upload/report success; `stable` still pointed at build 9; stable publish/update detection remained.
2. Release work was paused after a Windows installed-app failure: S3-downloaded `clipperstudio Setup 0.0.3` launched with no visible window.
3. Helped bootstrap the separate Windows PC: Codex CLI path issue was resolved, repos were to be cloned under `C:\Users\metabuzz_jmj\Desktop\project\clipper`, and the Windows diagnosis session was instructed.
4. Windows diagnosis found the first-run app window was blocked by packaged startup `ensureVenv()`:
   - startup sync pulled in the full Python workspace;
   - `dance_highlight -> insightface==0.7.3` attempted a Windows source build;
   - the PC had no MSVC Build Tools;
   - `main.ts` opened the window only after `ensureVenv()`, so users saw no app window.
5. We decided not to require MSVC Build Tools from users. The direction became proper runtime isolation plus Windows-safe Dance dependencies.
6. InsightFace commercial/distribution risk and Windows wheel risk were investigated. The Dance path moved to OpenCV YuNet/SFace instead of `insightface`.
7. Dance Highlight was changed and tested:
   - startup venv no longer installs every plugin dependency before app window open;
   - Dance face matching moved to OpenCV YuNet/SFace;
   - Mac unit/e2e pipeline tests passed;
   - user manually confirmed Dance install/model flow and project generation.
8. Dance result quality issues were found:
   - some members appeared with 0 clips while anonymous clusters held their clips;
   - manual anonymous-cluster-to-member mapping was added;
   - member profile/exclusion direction was discussed for retired or irrelevant members;
   - segment face sampling was improved by selecting more/better frames per segment.
9. Windows manual build from the feature branch succeeded. The app launched and Dance plugin worked, but new installed-app issues were discovered.
10. Windows edit-page issue was fixed:
    - rendered result could choose a render/output project id instead of source project id;
    - edit routing now resolves the original source project from metadata/manifest/source asset metadata.
11. ffmpeg/ffprobe readiness behavior was corrected:
    - no silent auto-download;
    - packaged UI should require explicit consent/install flow;
    - old copy that suggested restarting the app was considered misleading.
12. Plugin install state was corrected:
    - reset app data should show model-backed plugins as uninstalled;
    - local/devapp NestJS now checks real model asset presence rather than only plugin manifests;
    - Electron devapp model-download IPC also checks real files;
    - reset scripts were added for macOS and Windows.
13. Plugin Store concurrent install was blocked:
    - only one plugin install flow can run at a time;
    - this prevents shared download/install state from being reset by a second click.
14. Secretless provider routing became the main architecture:
    - desktop should not carry provider secrets in packaged resources;
    - Dance member image search routes through `web_api`;
    - prompt shortform script generation routes through `web_api`;
    - Dialog Highlight LLM stages route through `web_api`;
    - local unauthenticated desktop access is temporary until auth/token design lands.
15. Dialog Highlight pipeline was split:
    - Python performs media stages only;
    - local NestJS orchestrates stages;
    - web_api owns LLM provider calls and credentials.
16. Dialog Highlight timeout/logging was fixed:
    - desktop NestJS `WebApiClient` timeout was too short and mislabeled as `web_api is unreachable`;
    - Dialog calls now use longer per-request timeout;
    - web_api OpenAI Responses timeout was extended;
    - web_api logs request/completion/failure for Dialog LLM operations without logging prompts/payloads;
    - user confirmed a full Dialog Highlight run reached and completed all LLM stages.
17. Prompt shortform was routed and fixed:
    - script generation calls web_api/OpenAI;
    - TTS must use embedded Supertonic, not Naver Clova;
    - Supertonic fast speed no longer passes speed into model synthesis directly;
    - plugin synthesizes at stable model speed `1.0` then applies pitch-preserving playback-speed post-processing;
    - default clip/TTS speed is now `1.2`.
18. Electron/auth fixes were added:
    - local dev auth can target local `CLIPPER_WEB_API_BASE_URL`;
    - deep-link token logs are redacted;
    - stale `/me` validation should not clear a newer desktop session;
    - web_api desktop OAuth callback shows a completion page and should not leave a confusing "back to app" button.
19. Angular/UI fixes were added:
    - removed unwanted native tooltip text from shell navigation;
    - removed Material progress bar from the clip generation modal where custom stage imagery is used.
20. All app repos were committed in related groups. No push was performed after the latest commit batch.
21. Packaged-app build config was clarified:
    - default packaged mac arm64 build uses deployed web_api;
    - new `desktop/clipper_electron` command `npm run build:app:mac:arm64:local-api` builds a packaged app that points at local `http://127.0.0.1:3000`;
    - build-time runtime config was verified without printing secret env values.
22. `desktop/clipper_nestjs/.env.packaged` was removed from git tracking with `git rm --cached`; secret-bearing env files remain untracked.
23. Template Builder default shortform template was added:
    - empty local template store now exposes one read-only built-in shortform template;
    - default template uses the same baseline as "새 템플릿 만들기";
    - read-only delete is blocked by existing readonly checks;
    - template badges such as `사용자 템플릿` were removed from builder cards.
24. Default template thumbnail behavior was corrected:
    - Template Builder gallery captures the live preview DOM for the built-in default card thumbnail;
    - no fake SVG thumbnail is used;
    - object URLs are cleaned up.
25. Live preview thumbnail capture was hardened:
    - while `phone-canvas` is captured, preview-grid scrollbars are hidden so small Electron windows do not bake scrollbars into card thumbnails.
26. Shortform production template selector now receives an actual default builder thumbnail:
    - `TemplateBuilderPublishedPresetSource` emits `preview.remoteImageUrl` for the default shortform template;
    - a browser-rendered `default-shortform.png` asset is bundled and served via `template-presets/template-builder/assets/:fileName`;
    - packaged asset path resolution was verified.
27. Windows local-api smoke reached app launch but was stopped before manual UI smoke:
    - app repos were pulled to `feature/plugin-runtime-isolation`;
    - `web/clipper_web_api` was bootstrapped locally and `/health` returned 200;
    - Windows local-api Electron build produced `dist-app\win-unpacked` after a manual no-sign electron-builder rerun;
    - app logs showed packaged NestJS ready and ffmpeg/ffprobe missing, with no silent media-tool download;
    - updater check started automatically and logged missing `app-update.yml`, so smoke was stopped to respect the no-updater condition.
28. Electron local-api smoke build was fixed after that Windows finding:
    - `build:app:win:x64:local-api` now writes runtime config with `autoUpdateDisabled: true`;
    - packaged runtime config maps that to `CLIPPER_AUTO_UPDATE_DISABLED=1` for updater setup;
    - Windows local-api `--dir` builds add `--config.win.signAndEditExecutable=false` to avoid winCodeSign/symlink failures during smoke builds.
29. Windows local-api smoke was later paused as a private-only debug path, not a team/public README path:
    - the separate Windows Codex session pulled `desktop/clipper_electron @ a9cf9c1`;
    - local `web/clipper_web_api` was running and `/health` returned 200 with user/admin/release DB ok;
    - env file presence and forbidden packaged provider-secret key names were checked without printing values;
    - `scripts\reset-windows.ps1 -ConfirmReset` stopped at `Stopping Clipper2 and managed plugin processes...`;
    - likely cause: `Stop-ProcessByCommandLinePattern 'clipper_electron'` matched the PowerShell command line that was running the reset script from a `clipper_electron` path and killed its own shell;
    - `Clipper2.exe` was not launched, so updater behavior and UI smoke were not checked in that run;
    - public `desktop/clipper_electron/README.md` local-api/no-sign Windows guidance was removed afterward. Keep this context in `.codex` only.
30. The Windows reset self-kill risk was fixed in `desktop/clipper_electron`:
    - `reset-windows.ps1` now protects the current PowerShell `$PID` from command-line pattern kills;
    - the broad `clipper_electron` command-line kill was replaced with a narrower dev Electron executable path pattern;
    - static regression coverage was added in `test/reset-windows-script.test.js`;
    - macOS verification ran `npm test` and `git diff --check`, but actual PowerShell execution still needs a Windows PC.

### Verification Already Run

```text
desktop/clipper_electron:
  npm run build && npm test
  -> 65 tests passed

  latest Windows local-api smoke fix:
  npm run build
  node --test test/build-runtime-config.test.mjs
  node --test test/packaged-runtime-config.test.js
  npm test
  -> build passed; focused tests passed; 78 tests passed

desktop/clipper_python:
  uv run --with pytest --with httpx --package clipper-plugin-tts-supertonic python -m pytest tests/test_tts_supertonic_synthesis.py tests/test_tts_supertonic_route.py tests/test_tts_supertonic_runtime.py -q
  -> 10 tests passed

web/clipper_web_api:
  npm test -- --runInBand src/modules/dialog-highlight/presentation/dialog-highlight-llm.controller.spec.ts src/modules/dialog-highlight/application/dialog-highlight-llm.service.spec.ts src/modules/auth/presentation/auth.controller.spec.ts src/modules/api-keys/presentation/media-search.controller.spec.ts src/modules/shortform-script/presentation/script.controller.spec.ts
  npm run build
  -> 5 suites / 15 tests passed, build passed

desktop/clipper_nestjs:
  npm run build
  node --test test/web-api-client.test.js test/dialog-highlight-web-api-client.test.js test/dialog-highlight-workflow-executor.test.js test/dialog-highlight-python-stage-runner.test.js test/error-code.test.js test/job-failure-event.test.js test/local-plugin-host-install-state.test.js test/clipper-studio-script-generator.test.js test/shortform-script-generator-wiring.test.js test/shortform-clip-generation-events.test.ts test/shortform-project-generation-assets.test.js test/shortform-tts-provider.test.js
  -> 74 tests passed

desktop/clipper_angular:
  ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/shortform/pages/shortform-workflow-style.spec.ts --include src/features/shortform/components/workflow/shortform-legacy-style-panel/shortform-legacy-style-panel.component.spec.ts --include src/features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component.spec.ts
  npm run build
  -> 68 tests passed, build passed

Latest Template Builder/default-template verification:

desktop/clipper_electron:
  npm run build:app:mac:arm64:local-api
  node scripts/assert-no-packaged-secrets.mjs ...
  packaged runtime config check
  -> build passed, packaged secret guard passed, runtime_config=local-api

desktop/clipper_nestjs:
  npm run build
  node --test test/template-builder-api.test.js test/template-builder-preset-source.test.js test/template-builder-shortform-preset-source.test.js test/simplified-shortform-template-preset-source.test.js
  packaged asset resolution check for default-shortform.png
  -> 14 tests passed, packaged_asset_resolution=ok

desktop/clipper_angular:
  ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadlessNoSandbox --include src/features/template-builder/pages/template-builder-page/template-builder-page.component.spec.ts
  ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadlessNoSandbox --include src/features/template-builder/components/template-family-card/template-family-card.component.spec.ts --include src/features/template-builder/components/template-family-gallery/template-family-gallery.component.spec.ts --include src/features/template-builder/pages/template-builder-redesign-preview/template-builder-redesign-preview.component.spec.ts --include src/features/template-builder/pages/template-builder-page/template-builder-page.component.spec.ts
  ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadlessNoSandbox --include src/features/shortform/services/shortform-project.service.spec.ts --include src/features/shortform/components/template/shortform-template-selector/shortform-template-selector.component.spec.ts
  ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadlessNoSandbox
  npm run build -- --progress=false
  -> 75 success, 87 success, 13 success, 809 success, build passed
```

Resolved verification caveat:

- `desktop/clipper_nestjs` `node --test test/shortform-project-api.test.js` now configures a mock `CLIPPER_WEB_API_BASE_URL` through the test harness and passes.

### Immediate Next Priorities

1. Re-decide the Windows test PC verification path after pulling feature branches:
   - use project root `C:\Users\metabuzz_jmj\Desktop\project\clipper`;
   - pull all repos on `feature/plugin-runtime-isolation`;
   - default assumption after the latest user decision: Windows should not run a local web_api/local-api smoke path unless explicitly requested as private debugging;
   - prefer a normal deployed-web_api packaged-app verification path once the user chooses the exact Windows build/run method;
- reset runtime data with the updated `reset-windows.ps1`, then confirm on Windows that the PowerShell session survives the reset;
   - verify first launch, login, plugin installs, prompt shortform, Dialog Highlight, Dance Highlight, edit pages, and secret/log hygiene.
2. Finish auth/security/provider-routing follow-ups:
   - replace temporary unauthenticated local desktop access to web_api endpoints with proper desktop auth/service token design;
   - keep the no-fallback provider policy;
   - verify local/dev/prod web_api base URL behavior and error classification.
3. Do not resume release/stable publish work until Windows installed-app smoke is accepted.

Mac packaged-app smoke and ffmpeg/ffprobe consent/install-state flow were user-confirmed done on 2026-07-02.

### Carry-Forward TODOs

#### Release / Version Management

- `0.0.4` stable publish is still not done.
- Installed app `electron-updater` update detection from the previous stable target still needs verification.
- Windows runner build/sign/S3 upload/report should be repeated from the accepted feature branch after installed app smoke passes.
- Release Console follow-ups remain:
  - publish confirmation/authz details;
  - artifact/stable target UX;
  - release-runner status polish.
- Web client download page follow-ups remain.

#### Cross-Repo Push / Branch Hygiene

- Confirm all five app repos are on `feature/plugin-runtime-isolation`.
- Do not push these commits to `dev` directly.
- `.codex` is a separate repo; documentation commits must stay separate from app repo commits.
- Several local feature branches are ahead of origin; before any future release/dev merge, re-check all repo status/logs and push only approved feature branches.
- Optional cleanup later: decide whether to delete pushed helper branches such as `fix/default-template-thumbnails` after they are no longer needed.

#### Mac / Windows Manual Verification

- Mac fresh-reset packaged-app smoke is user-confirmed done.
- Windows test PC local-api unpacked smoke is paused and should not be treated as the default team/public path.
- The latest Windows attempt stopped during `reset-windows.ps1 -ConfirmReset` because the `clipper_electron` command-line kill pattern likely matched the reset-running PowerShell session itself; the script has since been narrowed, but actual Windows execution still needs confirmation.
- Windows manual verification should use a deployed-web_api packaged-app path once the user confirms the exact build/run method.
- Windows runner PC packaged build/sign/S3 workflow is still needed after manual behavior is accepted.
- Secret/log checks for the Mac smoke were user-confirmed done; repeat on Windows packaged smoke.

Template Builder/default template, Dance Highlight active smoke, Prompt Shortform/TTS, plugin reset state, plugin asset persistence, render timing, and ffmpeg/ffprobe consent/install-state flow were user-confirmed done during TODO review.

#### Dialog Highlight

- Mac packaged-app Dialog Highlight rerun was user-confirmed done after:
  - desktop NestJS sentence-split batching with adjacent context shots;
  - target-only merge so context shot results are not saved as final `llm_sentences`;
  - web_api OpenAI Responses JSON mode;
  - web_api prompt labels for `CONTEXT` vs `TARGET` shots.
- The observed failure was `sentence_split` timing out in local web_api after 180000ms. The failing artifact had about 663s duration, 256 STT segments, 171 non-empty shots, and about 4k shot text chars; content was not printed.

#### Prompt Shortform / TTS

- Do not reintroduce Naver Clova or any fallback TTS provider for installed app shortform.

Prompt Shortform/TTS generation, default `ttsSpeed: 1.2`, wav edge clipping, speed pitch preservation, and final render timing were user-confirmed done during TODO review.

#### Plugin Store / Runtime Assets

Plugin Store concurrent install block, reset script removal scope, fresh-reset model-backed plugin `미설치` state, Dialog/Dance asset persistence across restart, and ffmpeg/ffprobe consent/install-state flow were user-confirmed done during TODO review.

#### Auth / Security / Provider Routing

- Temporary unauthenticated local desktop access to web_api endpoints must be replaced by proper desktop auth/service token once auth/permissions design lands.
- Keep current no-fallback policy:
  - Dance image search through web_api only;
  - prompt script generation through web_api only;
  - Dialog LLM through web_api only;
  - no direct desktop OpenAI/Naver provider fallback.
- Verify local/dev/prod base URL configuration:
  - desktop devapp should use local web_api when configured;
  - packaged builds should use the intended environment URL;
  - errors should clearly distinguish missing config, unreachable api, provider failure, and timeout.

#### Documentation / Test Hygiene

- `NEXT.md` now treats this top `Active Handoff` section as the only current TODO source; lower sections are historical snapshots only.
- stdout/log/control-event contract is documented in `.codex/design/DESKTOP_STDOUT_AND_CONTROL_EVENT_CONTRACT_2026-07-02.md`.
- `.codex/todos/2026-07-01-desktop-stdout-event-contract.md` is marked documented, with only a long-term physical channel separation follow-up.
- Full Angular suite passed in the latest documented run (`809 success`); rerun relevant suites before treating future failures as regressions.

## Historical Handoff Snapshots (Reference Only)

The sections below are retained for detailed history. They are not the source of current TODOs,
branch heads, or next-session priorities. Use the top `Active Handoff` section above for current
state.

### 2026-07-02 Desktop Secretless Provider Routing / Dialog Pipeline Current Handoff

Release/version-management work is still paused. The current priority is installed desktop app correctness.

Current pushed feature branch heads:

```text
web/clipper_web_api:       c0f54bf feat: add dialog highlight llm endpoint
desktop/clipper_nestjs:    4def63c feat: orchestrate dialog highlight in nestjs
desktop/clipper_python:    d5b24d8 refactor: remove direct dialog llm provider calls
desktop/clipper_electron:  cd798ba build: reject packaged provider secrets
desktop/clipper_angular:   7c77745 feat: map provider routing errors
```

Feature branch commits not yet in `origin/dev`:

```text
web/clipper_web_api:
  c0f54bf feat: add dialog highlight llm endpoint

desktop/clipper_nestjs:
  45df395 feat: add desktop web api client
  e2436ae refactor: route dance image search through web api
  f91c4ee feat: add dialog highlight web api client
  4def63c feat: orchestrate dialog highlight in nestjs

desktop/clipper_python:
  fe223e3 feat: make dance face matching Windows-safe
  1cea9ee feat: add dialog highlight stage contracts
  665c173 refactor: extract dialog media analysis stage
  f8e49e3 refactor: split dialog highlight media stages
  d5b24d8 refactor: remove direct dialog llm provider calls

desktop/clipper_electron:
  bc69b54 fix: isolate packaged plugin virtualenvs
  cd798ba build: reject packaged provider secrets

desktop/clipper_angular:
  adef4f8 fix: route shortform edits to source project
  b581987 fix: require consent for packaged media tools
  934c7df fix: keep plugin install state pending
  7c77745 feat: map provider routing errors
```

Branch/push state:

- All five active repos are on `feature/plugin-runtime-isolation` and match their origin tracking branch:
  - `web/clipper_web_api`
  - `desktop/clipper_nestjs`
  - `desktop/clipper_python`
  - `desktop/clipper_electron`
  - `desktop/clipper_angular`
- `desktop/clipper_nestjs` had already been pushed from another session/PC.
- `web/clipper_web_api` briefly had `c0f54bf` on local `dev`; it was moved to `feature/plugin-runtime-isolation`, pushed there, and local `dev` was reset to `origin/dev @ 51e51ce`.
- Do not push these plugin-runtime-isolation commits directly to `dev`.

Completed architecture changes:

- Packaged app startup venv was split from plugin-specific venv work:
  - startup sync no longer installs every plugin dependency before opening the app window.
  - packaged plugins use isolated virtualenvs/install state instead of blocking first launch on heavy optional dependencies.
- Dance Highlight face matching is Windows-safe:
  - removed the direct `insightface` dependency from the dance plugin path.
  - OpenCV/ONNX-based face model loading and clustering tests were added.
  - segment face sampling/mapping was improved to reduce anonymous or zero-clip member results.
- Shortform edit routing now prefers the source project id from render result metadata/manifest/source asset metadata, fixing Windows packaged edit pages that opened with clips/settings missing.
- Packaged media tool readiness now requires consent:
  - ffmpeg/ffprobe should not be silently auto-downloaded.
  - the UI should remain in a consent/install-required state until the user approves media tool setup.
- Plugin store install state stays pending until install completion, instead of showing installed before the final completion event/snackbar.
- Dance member image search now routes through `web_api`; desktop direct Naver/Kakao fallback is removed.
- Dialog Highlight is now staged:
  - local NestJS orchestrates.
  - Python performs media stages only.
  - web_api owns LLM provider calls and credentials.
- Dialog Python no-stage execution no longer runs the legacy monolithic OpenAI path.
- Dialog Python package no longer imports/depends on OpenAI and no longer reads provider env names.
- Packaged Electron build guard rejects forbidden provider secret key names in packaged resources/env files.
- Angular maps provider routing machine codes to Korean user-facing messages.

Additional local changes after the pushed feature heads above:

- `desktop/clipper_nestjs` fixes devapp/local Plugin Store install-state drift:
  - `LocalPluginHost` now checks actual model files instead of treating plugin manifest discovery as installed.
  - Stale `.ready` markers no longer make model-backed plugins look installed when model files are missing.
  - `CLIPPER_ELECTRON_USER_DATA_DIR` can override the inferred Electron `Clipper2` userData path for tests/unusual local setups.
  - New regression: `test/local-plugin-host-install-state.test.js`.
- `desktop/clipper_electron` fixes devapp Plugin Store install button flow:
  - `modelDownload.modelsNeeded()` now reports actual model-file state in devapp too.
  - Dev plugin processes use `uv run --project <clipper_python>` with Electron userData as `cwd`, so downloaded model assets land where install-state checks look.
  - New regression: `test/model-download-info.test.mjs`; `test/plugin-process-packaged-paths.test.js` covers dev plugin `cwd`.
- `desktop/clipper_electron` now includes fresh-reset scripts:
  - `scripts/reset-macos.sh`
  - `scripts/reset-windows.ps1`
  - Scope includes packaged Electron app data, downloaded ffmpeg/ffprobe, plugin model markers/files, HuggingFace cache by default, repo-local Dance model artifacts, and local NestJS `.clipper_data`.
  - The scripts also stop the default local NestJS devapp listener on port `9019` and any `NEST_PORT` declared in local Nest env files.
  - The first reset script missed `desktop/clipper_nestjs/.clipper_data`, which is why old project library entries could survive in devapp.
- `web/clipper_web_api` local Dance image search 401 fix:
  - `POST /media/search` no longer uses `MediaSearchServiceTokenGuard` while desktop auth/token wiring is intentionally deferred.
  - Added `media-search.controller.spec.ts` to prevent reintroducing this guard before the auth design lands.
- `desktop/clipper_nestjs` local Dance image search 503 diagnostics:
  - `WebApiClient` now preserves non-2xx web_api response details in `WebApiProviderError.message`.
  - This distinguishes missing usable `naver_search_keys` rows from `API_KEY_ENC_SECRET` decrypt failures.
- `desktop/clipper_python` YouTube ingest fix:
  - `yt-dlp` lock updated from `2026.3.17` to `2026.6.9`.
  - The failed Dance URL `CHp0Kaidr14` was verified with the updated tool:
    - `uv run python -m yt_dlp --version` -> `2026.06.09`
    - format probe passed without 403.
    - small 360p download probe to `/private/tmp` passed without 403.
- `desktop/clipper_nestjs` YouTube/web_api failure classification:
  - YouTube `HTTP Error 403: Forbidden` download failures now map to `AUTH_REQUIRED` instead of disappearing behind generic `validation`.
  - Source ingest recognizes YouTube 403 as an auth-required case.
  - `WebApiNotConfiguredError`, `WebApiProviderError`, and `WebApiUnreachableError` now classify as `dependency`.
  - Stable web_api error `code` values (`web_api_not_configured`, `web_api_unreachable`, `provider_failed`) are propagated to job failure events.
- `desktop/clipper_angular` job failure headline fix:
  - Existing failed jobs with raw `yt-dlp ... HTTP Error 403: Forbidden` in `detail` now display the YouTube login/download problem instead of only `입력을 다시 확인해주세요`.
- Shortform prompt clip generation secretless routing:
  - `desktop/clipper_nestjs` now injects `WebApiClipperStudioScriptGenerator` for `ClipperStudioScriptGenerator`.
  - Shortform script generation calls `web_api` `POST /llm/script` through `WebApiClient`.
  - Desktop ShortformModule no longer registers the local OpenAI/Ollama/remote_proxy script providers in its execution path.
  - `web/clipper_web_api` `POST /llm/script` no longer requires `ScriptServiceTokenGuard` while desktop auth/token wiring is deferred.
  - Existing web_api `.env` has `OPENAI_API_KEY` configured (presence only verified; value was not printed).
- These changes are local working-tree changes unless committed later. They are not included in the pushed feature head list above.

Local verification completed:

```text
web/clipper_web_api:
  npm test -- dialog-highlight-llm.service.spec.ts --runInBand  # pass, 4
  npm test -- search.service.spec.ts --runInBand                # pass, 6
  npm run build                                                 # pass

desktop/clipper_nestjs:
  npm run build                                                 # pass
  node --test web-api/dance/dialog/workflow focused tests        # pass, 46

desktop/clipper_python:
  uv run --package clipper-plugin-dialog-highlight python -m pytest dialog focused tests -q  # pass, 17
  forbidden provider source scan under dialog_highlight package  # no matches

desktop/clipper_electron:
  npm test -- test/packaged-secret-scan.test.js                  # pass, 58
  npm run build                                                  # pass

desktop/clipper_angular:
  npm test -- --watch=false --include src/core/errors/error-catalog.spec.ts  # pass, 12
  npm run build                                                              # pass
```

Additional local verification after the devapp Plugin Store install-state fix:

```text
desktop/clipper_nestjs:
  npm run build  # pass
  node --test test/local-plugin-host-install-state.test.js test/local-plugin-host-exit-listener.test.js test/plugin-host-module-wiring.test.js test/workflow-executor-registry.test.js test/dialog-highlight-workflow-executor.test.js test/plugins-service-runtime-diagnostics.test.js  # pass, 27

desktop/clipper_electron:
  npm run build  # pass
  node --test test/model-download-info.test.mjs test/plugin-install-state.test.mjs test/plugin-process-packaged-paths.test.js test/plugin-manager-plugin-venv.test.js test/plugin-manager-exit-listener.test.js  # pass, 11

web/clipper_web_api:
  npm test -- media-search.controller.spec.ts media-search-service-token.guard.spec.ts search.service.spec.ts --runInBand  # pass, 11
  npm run build  # pass

desktop/clipper_nestjs:
  npm run build && node --test test/web-api-client.test.js  # pass, 7
  npm run build && node --test test/error-code.test.js test/job-failure-event.test.js test/web-api-client.test.js test/dialog-highlight-web-api-client.test.js  # pass, 23

desktop/clipper_angular:
  npm test -- --watch=false --browsers=ChromeHeadless --include src/core/errors/job-failure-headline.spec.ts --include src/core/errors/error-catalog.spec.ts  # pass, 17

desktop/clipper_python:
  uv sync --all-packages  # pass, local venv now has yt-dlp 2026.06.09
  uv run python -m yt_dlp --version  # 2026.06.09
  uv run python -m yt_dlp --simulate --skip-download --no-playlist -F <Dance failed YouTube URL>  # pass
  uv run python -m yt_dlp --no-playlist --force-overwrites -f 18 -o /private/tmp/clipper-ytdlp-probe.%(ext)s <Dance failed YouTube URL>  # pass

web/clipper_web_api local runtime:
  npm run start:dev  # running locally on port 3000 after sandbox-escalated start
  curl -sS http://127.0.0.1:3000/health  # user/release/admin db all ok
  curl -sS -X POST http://127.0.0.1:3000/media/search ...  # pass, usable Naver key row present

web/clipper_web_api:
  npm run build  # pass
  npm test -- script.controller.spec.ts script-service-token.guard.spec.ts script.service.spec.ts --runInBand  # pass, 22

desktop/clipper_nestjs:
  npm run build && node --test test/shortform-script-generator-wiring.test.js test/web-api-client.test.js test/clipper-studio-script-generator.test.js test/shortform-project-generation-assets.test.js  # pass, 24

runtime smoke:
  curl -sS -o /tmp/clipper-llm-script-empty-body.json -w "%{http_code}" -X POST http://127.0.0.1:3000/llm/script -H 'Content-Type: application/json' -d '{}'  # 400, proves no service-token 401
  curl -sS http://127.0.0.1:9019/v1/health  # ok
```

Manual installed-app verification still needed on macOS and Windows after pulling these commits:

1. Fresh reset and first launch opens a window.
2. ffmpeg/ffprobe consent flow is visible and does not require app restart.
3. Plugin Store install state shows model-backed plugins as uninstalled after fresh reset and remains pending until the install really completes.
4. Dance Highlight installs/runs on Windows without requiring MSVC Build Tools.
5. Dance result member list/anonymous cluster assignment still needs quality spot-checks with known sample videos.
6. Shortform project edit opens the original project clips/settings on Windows packaged builds.
7. Dance image search succeeds only through configured/reachable web_api.
8. Dialog Highlight succeeds without desktop-bundled OpenAI key when web_api is configured.
9. Missing/unreachable web_api/provider configuration shows clear provider routing errors.
10. Packaged env/resource files contain no forbidden provider key names.
11. Windows runner/manual packaged build/sign/upload should be resumed only after installed app behavior is accepted.

Fresh reset commands:

```powershell
cd C:\path\to\project\desktop\clipper_electron
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\reset-windows.ps1 -ConfirmReset
```

```bash
cd /Users/jina/project/adlight/desktop/clipper_electron
scripts/reset-macos.sh --yes
```

Detailed session record: `.codex/records/sessions/2026/07/02.md`.

## 2026-06-30 Release Platform Integration Current Handoff

현재 기준 브랜치:

```text
web/clipper_infra:       dev @ 6b2b6fb
web/clipper_web_api:     dev @ 51e51ce
web/clipper_web_admin:   dev @ 6c0dfc7
desktop/clipper_electron: dev @ 47358cd
desktop/clipper_angular: dev @ 460211e
desktop/clipper_nestjs:  dev @ c524646
desktop/clipper_python:  dev @ e34cdbc
clipper_docs:            main @ 9a244d6
```

중요 전제:

- Mac mini 로컬에서는 코드/문서 수정과 단위 테스트/web build만 수행한다.
- Windows container 실행/빌드/서명/S3 검증은 Windows new runner PC에서 수행한다.
- release integration feature branch는 최신 `dev`에 병합/푸시됐다.
- runner PC, m2-stage, m2-db는 `dev` 기준으로 다시 맞췄다.
- secret-bearing 파일과 env 값은 출력/커밋하지 않는다.

이번 세션에 추가로 완료/검증된 것:

- Windows dev S3 upload mode end-to-end 검증 완료.
- runner installer version이 release payload version을 따르도록 검증.
  - 예: release `0.0.3` -> `clipperstudio Setup 0.0.3.exe`.
- Windows runner에서 build 9 성공:
  - code signing 성공.
  - Authenticode 검증 성공.
  - S3 upload 성공:
    `s3://clipperstudio/dev/windows/0.0.3/build-9/clipperstudio Setup 0.0.3.exe`.
  - API report success:
    `2510ff8f-a4eb-4f9b-906e-c5b46adff026`.
- Admin `정식 배포` 버튼으로 build 9 Windows artifact를 stable target에 publish.
- B' update-feed 방식 검증 완료.
  - S3에는 `latest.yml`을 올리지 않는다.
  - API가 stable target/artifact metadata로 `latest.yml`을 동적 생성한다.
  - 확인 URL:
    `https://dev-api.clipperstudio.ai/releases/updates/stable/windows/x64/latest.yml`
    -> `200`.
  - feed가 가리키는 S3 installer URL도 `200`.
- `release_artifacts.sha512` migration registration/API validation/runner report 보강.
- `API_KEY_ENC_SECRET`이 API container로 전달되도록 compose 보강.
- `admin.datasource.ts`가 `CLIPPER_ADMIN_DATABASE_*` split env를 쓰도록 수정.
- Windows runner runtime 검증 중 발생한 운영 이슈 처리:
  - runner token pair 불일치로 source snapshot 401 발생 -> runner env token 정합 필요 확인.
  - `CLIPPER_RELEASE_API_BASE_URL=http://localhost:3000` 오설정 -> runner report 실패 원인 확인.
  - `electron-updater` dependency missing -> Windows runner workspace에서 `install-windows-deps.ps1` 재실행 필요 확인.
- build 8은 실패 report가 API에 못 들어가 `building`으로 남았고, 수동 runner report로 `blocked/failed` 처리 완료.
- `feature/release-platform-integration`을 최신 `dev`에 병합/푸시 완료.
  - 병합/푸시 repo:
    `web/clipper_infra`, `web/clipper_web_api`, `web/clipper_web_admin`,
    `desktop/clipper_electron`.
  - `desktop/clipper_angular`, `desktop/clipper_nestjs`, `desktop/clipper_python`은
    feature와 `dev`가 동일해서 병합 커밋이 필요 없었다.
- `dev` merge 후 `web/clipper_infra/apps/compose.yml`에 `API_KEY_ENC_SECRET`
  중복 mapping이 생겨 m2-stage compose config가 실패했다.
  - root cause: 최신 `dev`와 feature 양쪽에서 같은 env key를 다른 위치에 추가한 merge 결과.
  - fix: 중복된 두 번째 mapping 제거.
  - `web/clipper_infra` fix commit: `6b2b6fb`.
  - 검증: `docker compose --env-file env/stack.dev.env.example -f apps/compose.yml config --quiet`,
    `node --test runner/*.test.mjs runner/windows/*.test.mjs` 통과.
- m2-stage는 `dev @ 6b2b6fb`로 pull 후 API/Admin 재배포 완료.
- m2-db는 `clipper_infra`만 `dev @ 6b2b6fb`로 fast-forward pull 완료.
  - DB containers는 재기동하지 않았다.
  - `clipper-db-admin-dev`, `clipper-db-user-dev`, `clipper-db-release-dev` 모두 `Up`/`healthy`.
- Windows runner PC도 `dev` 기준으로 다시 맞추고 runner container 기준 검증을 이어갔다.
- release `0.0.4`, build 10 Windows artifact build/sign/upload 성공.
  - block map 생성:
    `C:\runner-output\dist-app\clipperstudio Setup 0.0.4.exe.blockmap`.
  - code signing 성공.
  - Authenticode 검증 성공.
  - S3 upload 성공:
    `s3://clipperstudio/dev/windows/0.0.4/build-10/clipperstudio Setup 0.0.4.exe`.
  - API report success:
    `09180076-9dc4-4d7c-9629-69edeba0e174`.

현재 dev release DB에서 검증된 핵심 상태:

```text
Build 8: windows x64 failed, build blocked
Build 9: windows x64 succeeded/uploaded/signed, build published
Build 10: windows x64 succeeded/uploaded/signed
stable/windows/x64 target -> build 9 artifact
```

새로 문서화한 follow-up:

- `clipper_docs/todos/2026-06-30-release-console-followups.md`
  - 설치 파일 표 정렬/페이징/저장 위치/시도 열/publish 버튼 피드백.
  - `/versions` 내부 섹션 라우팅.
  - 릴리즈 준비 폼 레이아웃/릴리즈 노트 표시 정책.
  - Coordinator 버튼 정렬과 macOS runner 상태 오표시.
  - 이벤트 탭 페이징과 event coverage 확장.
  - `clipper_web_client` 다운로드 페이지를 정식 배포된 Windows artifact에 연결.
  - 다운로드 버튼을 Windows/Mac으로 분리하고, Mac은 당분간 출시 준비중 상태로 표시.
- 기존 publish authz/confirmation 후속:
  `clipper_docs/todos/2026-06-30-release-publish-authz-confirmation.md`.

남은 주요 TODO:

1. `desktop/clipper_electron/scripts/build-app.mjs --output-dir` 공식 지원.
   - 현재 runner는 `electron-builder.yml` 임시 rewrite로 output dir을 바꾼다.
2. runner output cleanup 정책.
   - `C:\runner-output\dist-app`, `C:\runner-output\signed` 정리/보존 기준 결정.
3. 실제 installer 실행/update detection 테스트.
   - 현재 `0.0.3` stable feed와 S3 다운로드는 검증됨.
   - `0.0.4` Windows artifact build/sign/S3 upload까지 완료됨.
   - 다음에는 `0.0.4` publish 후 설치된 앱의 electron-updater 감지까지 별도 검증 필요.
4. `clipper_web_client` 다운로드 페이지 연결.
   - 정식 배포된 stable Windows artifact가 다운로드되게 연결한다.
   - 다운로드 버튼은 Windows/Mac으로 분리한다.
   - Mac은 당분간 출시 준비중 메시지만 표시하고, macOS runner/build 구현과 연결하지 않는다.
5. macOS runner 구현은 당분간 비범위.
   - Windows runner만으로 출시한다.
   - 단, Admin/API에서 macOS runner가 없는 상태를 `online`으로 표시하는 문제는 고친다.
6. QA/approval/publish flow 운영화.
   - publish confirmation/authz는 별도 TODO 문서에 있음.
7. Admin release console UX 정리.
   - 상세 항목은 release-console follow-up TODO 참조.
8. dev release DB 테스트 데이터 정리 여부 결정.
9. Windows runner 운영화.
   - startup/restart policy, health monitoring, firewall/LAN 접근 정책.

다음 세션 시작 문구:

```text
Using Superpowers.

작업 위치는 /Users/jina/project/adlight 입니다. 한국어로 답변해줘.

먼저 .codex/handoff/NEXT.md 와 .codex/records/sessions/2026/06/30.md 를 읽고
현재 상태를 파악해줘.

release-platform-integration 작업은 최신 dev에 merge/push 되었고,
runner PC / m2-stage / m2-db도 dev 기준으로 다시 맞춰져 있어.
Windows runner 기준 release 0.0.4 build 10은 build/sign/S3 upload/report success까지
확인됐어. stable target은 마지막 문서 기준 build 9를 가리키고 있고,
0.0.4 stable publish와 설치된 앱의 electron-updater update detection 검증은 아직 남아 있어.

이번 세션은 Mac mini 로컬에서 코드/문서 수정과 로컬 테스트를 진행하고,
Windows container 실행/빌드/서명/S3 검증은 Windows runner PC에서 수행해야 한다는
전제로 진행해줘.

secret-bearing 파일이나 env 값은 절대 출력하거나 커밋하지 마.
NEXT.md의 남은 TODO를 기준으로, 0.0.4 publish/update detection 검증과
release console / web client download page 후속 작업부터 차근차근 진행하자.
```

## 2026-06-30 02:56 Release Runner Current Handoff

2026-06-29부터 2026-06-30 새벽까지 진행한 release management runtime /
direct Windows runner 작업은 `dev`에 병합되고 m2-stage, Windows runner PC,
m2-db checkout까지 `dev` 기준으로 맞춰졌다.

중요 전제:

- 다음 작업은 새 feature branch에서 시작한다.
- `main`은 건드리지 않는다.
- Windows container 실행/빌드/서명/S3 검증은 Windows new runner PC에서 수행한다.
- Mac에서는 코드 수정과 단위 테스트/web build까지만 한다.
- secret-bearing 파일과 env 값은 출력/커밋하지 않는다.

현재 `dev` HEAD:

```text
web/clipper_infra:     75e1307 Merge remote-tracking branch 'origin/feat/release-management-runtime' into dev
web/clipper_web_api:   5b40558 Merge remote-tracking branch 'origin/feat/release-management-runtime' into dev
web/clipper_web_admin: 125fa3a Merge remote-tracking branch 'origin/feat/release-management-runtime' into dev
```

이번 세션에 완료/검증된 것:

- Admin `Windows 빌드 시작` -> `clipper_web_api` -> Windows runner container
  `/jobs/start` direct start flow 구현.
- runner job claim polling 제거. 브라우저가 runner를 직접 호출하지 않는다.
- source snapshot capture도 Windows runner container에서 수행.
- Windows runner container가 checkout/build/sign/report 수행.
- `CLIPPER_RELEASE_SKIP_UPLOAD=1` dry-run일 때 artifact status는 `local_verified`.
- Admin은 `local_verified`를 `로컬 검증 완료`, build `ready`를 `QA 대기`로 표시.
- Coordinator `Windows 빌드 시작` 버튼은 요청 중 spinner/disabled와 성공/실패 feedback 표시.
- Windows runner container에서 `npm run build:app:win:x64`, SSL.com CodeSignTool signing,
  Authenticode `Valid`, API report success까지 검증.
- artifact key collision 해결. 새 key는
  `clipper2/dev/windows/<release-version>/build-<build-number>/<file>` 형태.
- infra README/runbook에 m2-stage/Windows runner 명령과 env file 위치 문서화.

검증 결과:

```text
web/clipper_infra:
  node --test runner/*.test.mjs runner/windows/*.test.mjs
  21 pass, 1 skip

web/clipper_web_api:
  npm test -- --runInBand
  93 pass
  npm run build
  pass

web/clipper_web_admin:
  ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless
  61 success
  npm run build
  pass
```

배포/서버 상태:

- m2-stage:
  - `/Users/metabuzz/Desktop/project/clipper2`
  - `clipper_infra`, `clipper_web_api`, `clipper_web_admin` 모두 `dev`.
  - `./scripts/deploy-dev.sh api`, `./scripts/deploy-dev.sh admin` 완료.
  - `https://dev-api.clipperstudio.ai/health` 정상.
- Windows runner PC:
  - `C:\Users\Metabuzz00\Desktop\project\clipper`
  - `web\clipper_infra`는 `dev`.
  - `sync-windows-workspace.ps1 -Branch dev`로 desktop repos와 `clipper_web_api` sync 완료.
  - Docker image rebuild 완료.
  - Build 4 report success:
    `df48e154-3cc0-4662-81c9-1a2bbfc381a9`.
- m2-db:
  - `/Users/metabuzz/Desktop/project/clipper2/clipper_infra`
  - `dev...origin/dev`.
  - `clipper-db-admin-dev`, `clipper-db-user-dev`, `clipper-db-release-dev` 모두 healthy.
  - DB containers는 재기동하지 않았다.

release DB 현재 테스트 기록:

```text
Build 4: windows x64 succeeded, local_verified, signed
Build 3: windows x64 succeeded, local_verified, signed
Build 2: windows x64 failed
Build 1: windows x64 succeeded, local_verified, signed
```

Build 3/4는 새 S3 key 구조를 사용한다. Build 1은 이전 dry-run key 구조가 남아 있지만
테스트 기록으로 보존했다.

다음 세션 우선순위:

1. S3 upload mode 전환.
   - Windows runner 실행에서 `CLIPPER_RELEASE_SKIP_UPLOAD=1` 제거.
   - AWS secret은 `C:\secure\clipper-aws.env` 같은 mounted env file 사용.
   - 실제 S3 upload 후 API artifact status `uploaded`, `uploaded_at` populated 확인.
   - Admin 설치 파일 다운로드/public URL 동작 확인.
2. `desktop/clipper_electron/scripts/build-app.mjs` output dir 공식 지원.
   - 예: `node scripts/build-app.mjs win32 x64 --output-dir C:\runner-output\dist-app`.
   - 현재 runner의 `electron-builder.yml` 임시 수정 우회를 제거한다.
3. runner output cleanup 정책 추가.
   - job 시작 전 `C:\runner-output\dist-app`, `C:\runner-output\signed` 정리.
   - upload 성공 후 container 내부 산출물 보존/삭제 정책 결정.
4. artifact download/install verification flow 정리.
   - Admin 설치 파일 화면 다운로드 확인.
   - client page 다운로드 연결 필요 범위 결정.
5. macOS runner 상태 표시 정정.
   - 현재 방침: macOS runner 구현은 당분간 비범위이며 Windows runner만으로 출시한다.
   - 단, macOS runner가 없는데 `online`으로 표시되는 문제는 Admin/API에서 고친다.
6. QA/approval/publish flow 보강.
   - QA 대기 -> 승인 -> target promotion/stable publish 운영 흐름 연결.
7. dev release DB 테스트 데이터 정리 여부 결정.
   - Build 2 failed 기록과 Build 1 old key 구조는 테스트 흔적이다.
8. runner 운영화.
   - Windows startup/restart policy, health monitoring, firewall/LAN 접근 정책.
9. `feat/release-management-runtime` branch 정리 여부 확인.
   - 이미 `dev`에 merge됐다.
   - 삭제는 사용자 확인 후에만 진행한다.

상세 세션 기록:

- [records/sessions/2026/06/29.md](../records/sessions/2026/06/29.md)
- [records/sessions/2026/06/30.md](../records/sessions/2026/06/30.md)

## Historical Context: 2026-06-29 Release Management Runtime / Windows Runner Handoff

이 섹션은 2026-06-29 당시 상태 기록이다. 2026-06-30 현재 상태는 위
`2026-06-30 02:56 Release Runner Current Handoff` 섹션이 우선한다.

2026-06-29 당시 진행 중인 작업은 관리자 버전관리 페이지와 release runner runtime이었다.

활성 브랜치:

```text
web/clipper_web_admin: feat/release-management-runtime
  HEAD: 7b9a21e feat: connect version console to release runtime

web/clipper_web_api: feat/release-management-runtime
  HEAD: 86289a0 feat: add release management runtime

web/clipper_infra: feat/release-management-runtime
  HEAD: 2d61769 fix: allow node 22 for windows runner
```

`dev`/`main`은 건드리지 않는다. 세 repo 모두 local/origin 같은 브랜치 상태로 확인됐다.

관리자 UI 상태:

- `/versions` 콘솔형 UI로 통합.
- `/versions2` 제거.
- 좌측 메뉴: 개요, 릴리즈, 빌드, 설치 파일, 배포 타겟, Coordinator, 이벤트.
- 중복 최근 이벤트 블럭 제거. 이벤트 메뉴에서만 노출.
- 소스 스냅샷 상세는 릴리즈 row click 모달.
- snapshot pin 버튼 loading/disabled feedback 추가.
- 릴리즈 discard 기능 추가.
- 새 릴리즈 준비 version validation 추가. `0.0.1` stable semver만 허용, branch name은 현재 자유 입력.
- `아티팩트`는 `설치 파일`로 변경.
- `Version Console` 메뉴 문구 제거.

API/runtime 상태:

- `web/clipper_web_api`에 release management runtime과 runner claim/report endpoint 추가.
- build 상태 갱신은 초기에는 page refresh 기준이다. polling/SSE/WebSocket은 사용자 요청으로 제외했다.
- 현재 `web/clipper_infra/runner/release-runner.mjs`는 runner가 API에서 job을 claim하는 pull 방식이다.
- 사용자는 pull vs push 방식은 더 고민하겠다고 했다. 다음 구현에서 네트워크 흐름을 바꾸기 전에 다시 합의한다.

Windows runner 검증 상태:

- 이전 Windows Home/Core PC는 Windows containers 불가라 Docker runner 후보에서 제외.
- 검증 성공 PC:

```text
OS: Windows 10 Pro 19045
Workspace: C:\Users\Metabuzz00\Desktop\project\clipper
CodeSignTool: C:\tools\CodeSignTool-v1.3.2-windows
Docker image baseline: mcr.microsoft.com/windows/servercore:ltsc2019
Node: v22.22.2
```

- Docker Windows engine 전환 성공: `docker info --format '{{.OSType}}' => windows`.
- `servercore:ltsc2019` Hyper-V isolation container 실행 성공.
- host smoke build 성공:

```text
C:\Users\Metabuzz00\Desktop\project\clipper\desktop\clipper_electron\dist-app\Clipper2 Setup 0.0.1.exe
```

- Docker container 안에서 CodeSignTool help/sign help 성공.
- Docker container 안에서 실제 SSL.com signing 성공.
- `Get-AuthenticodeSignature` 결과 `Status: Valid`, signer `METABUZZ Co.,Ltd`, timestamp present.

관련 문서:

- [../operations/windows-packaging/release-runner-docker-codesign-2026-06-29.md](../operations/windows-packaging/release-runner-docker-codesign-2026-06-29.md)
- [../records/sessions/2026/06/29.md](../records/sessions/2026/06/29.md)

비밀값 주의:

- `/Users/jina/project/adlight/sign-and-publish.js`는 기존 runner PC에서 복사한 secret-bearing 파일이다.
- `/Users/jina/project/adlight/code_signing_tool-2025-11-03.log`도 credential ID/signature material이 있으므로 커밋하지 않는다.
- `/Users/jina/project/adlight/docker-codesign-help-command.txt`와 `docker-codesign-sign-command.txt`는 명령만 있고 secret은 없다.

다음 작업:

1. `web/clipper_infra`에 Windows runner Dockerfile 추가. base는 `servercore:ltsc2019`.
2. container entrypoint 추가.
3. `sign-windows-artifact.ps1` 같은 signing helper 추가:
   - mounted CodeSignTool을 writable path로 copy.
   - artifact sign.
   - Authenticode status verify.
   - invalid signature면 fail.
4. release runner build flow에서 `npm run build:app:win:x64` 후 signing 실행.
5. `signatureStatus=signed`는 verification pass 후에만 report.
6. secret storage 방식 결정:
   - local env file,
   - Windows Credential Manager,
   - mounted secret file,
   - other secret manager.
7. 관리자 UI `빌드 시작`부터 runner claim/build/sign/report까지 end-to-end 검증.

## 2026-06-23 Repo Layout And Dev State

`/Users/jina/project/adlight` 루트 자체는 git repo가 아니다. 현재 active app repo는
8개이며 모두 `dev` 브랜치를 기본 작업 브랜치로 사용한다. 작업은 각 repo에서 새 브랜치를
만들고 검증 후 `dev`에 merge하는 방식이다.

```text
desktop/
  clipper_angular/
  clipper_nestjs/
  clipper_python/
  clipper_electron/

web/
  clipper_infra/
  clipper_web_client/
  clipper_web_api/
  clipper_web_admin/

legacy/
  adlight_python/
  adlight_angular/
  adlight_nestjs/
```

`.codex`는 별도 문서 repo다. 앱 코드 repo 변경과 `.codex` 문서 변경은 같은 commit에
섞지 않는다. 과거 기록에는 경로 이동 전의 `/Users/jina/project/adlight/clipper_*`
절대 경로가 남아 있을 수 있지만, 새 작업에서는 `desktop/*`, `web/*`, `legacy/*` 경로를
기준으로 한다.

2026-06-23 fetch 후 8개 active repo 상태:

```text
desktop/clipper_angular:   dev...origin/dev, clean
  bdf3434 refactor(angular): move provideDanceApi to dance-highlight.providers.ts (match tts pattern)

desktop/clipper_nestjs:    dev...origin/dev, clean
  886a5de chore(deps): upgrade NestJS 10→11 (Express 5), align with clipper_web_api

desktop/clipper_python:    dev...origin/dev, clean
  0314baf Merge branch 'dev' into feature/cross-process-logging

desktop/clipper_electron:  dev...origin/dev, clean
  e839aca feat(nest-manager): update data directory path for korean_artists.json to match bundle layout

web/clipper_infra:         dev...origin/dev, clean
  b9dfcdf feat: add Google OAuth and JWT configuration to environment files

web/clipper_web_client:    dev...origin/dev, clean
  87abf16 feat(scripts): add cache cleaning scripts to package.json

web/clipper_web_api:       dev...origin/dev, has untracked env/local.dev.env
  c8be471 docs: reference shared NestJS structure standard (ADR-0007), align layering rule

web/clipper_web_admin:     dev...origin/dev, clean
  d1aa4f5 build(package.json): add clean scripts for cache and dist removal
```

주의:

- `web/clipper_web_api/env/local.dev.env`는 local secret env 후보이므로 값을 출력하지 않는다.
  현재 repo의 `.gitignore`에는 `env/`가 없어 미추적 파일로 보인다.
- 여러 repo의 `origin/HEAD`가 아직 `dev`가 아닌 과거 기본 브랜치를 가리킨다.
  실제 작업 기준은 `origin/dev`다.
- 일부 `origin/main`에는 dev에 없는 오래된 README/scaffold commit이 남아 있다. 현재
  사용자가 확정한 기본 브랜치는 `dev`다.

## 2026-06-26 Desktop Plugin Runtime Work Merged To Dev

`desktop/*` 4개 repo의 `feature/plugin-runtime-memory-management` 작업은 최신 `origin/dev`
위 merge-test 브랜치에서 충돌 해결과 검증을 마친 뒤 `dev`에 반영됐다.

현재 desktop 원본 checkout 상태:

```text
desktop/clipper_angular:
  branch: dev
  state: dev...origin/dev, clean
  HEAD: 9f141e8 Merge feature/plugin-runtime-memory-management into dev merge-test
  parents: de7848e origin/dev before merge, 3f247d3 feature branch

desktop/clipper_electron:
  branch: dev
  state: dev...origin/dev, clean
  HEAD: 559673d Merge feature/plugin-runtime-memory-management into dev merge-test
  parents: 3f94f18 origin/dev before merge, d1a9ab0 feature branch

desktop/clipper_nestjs:
  branch: dev
  state: dev...origin/dev, clean
  HEAD: 5f5fb1a Merge feature/plugin-runtime-memory-management into dev merge-test
  parents: f2bcc8f origin/dev before merge, 4436c4b feature branch

desktop/clipper_python:
  branch: dev
  state: dev...origin/dev, clean
  HEAD: e34cdbc Merge feature/plugin-runtime-memory-management into dev merge-test
  parents: 90f89d1 origin/dev before merge, ec5ff36 feature branch
```

중요:

- 이 세션에서는 `git push`를 하지 않았다.
- merge 직전 `git fetch origin` 후 `origin/dev`가 이미 위 merge commit들을 가리키고 있었다.
  따라서 로컬 `dev`는 `pull --ff-only origin dev`로 fast-forward만 했다.
- 임시 merge-test worktree는 `/private/tmp/adlight-merge-check/plugin-runtime-memory-management-20260626-latest`
  아래에 detached HEAD 상태로 남겨뒀다.
- merge-test 브랜치명은 `merge-test/plugin-runtime-memory-management-into-dev-20260626`였다.

충돌 해결 기준:

- Angular는 최신 `origin/dev`의 one-component-per-dir 구조를 따랐다.
  `template-builder-page`는 `src/features/template-builder/pages/template-builder-page/` 하위 경로가 정본이다.
- Angular Template Builder의 logo/admin/official remnants는 feature branch 기준으로 제거 상태를 유지했다.
  `logoImageUploadRequest`, `logoText`, `adminPassword`, `systemTemplateEditMode`,
  `handleRegisterOfficial` 검색 결과는 merge-test 검증 당시 0건이었다.
- Angular dashboard spec은 최신 dev의 runtime confirmation/admission 테스트와 feature branch의
  lifecycle diagnostics 테스트를 함께 유지했다.
- NestJS `tts-plugin.client.ts`는 최신 dev의 `withTraceHeader()`와 feature branch의
  `PythonRuntimeLifecyclePolicy` lifecycle hook을 함께 유지했다.
- Electron/Python은 merge conflict 없이 자동 merge됐다.

최종 검증:

```text
Node: /Users/jina/.nvm/versions/node/v22.22.2/bin/node

desktop/clipper_angular:
  npm run build pass
  targeted Karma tests => TOTAL: 237 SUCCESS

desktop/clipper_electron:
  npm run build pass
  targeted node tests => 4/4 pass
  npm run build:app:mac:arm64 pass

desktop/clipper_nestjs:
  npm run build pass
  targeted node tests => 13/13 pass

desktop/clipper_python:
  uv run --with pytest python -m pytest tests/test_template_builder_text_renderer.py -q
  => 8 passed

all desktop repos:
  git diff --check pass
```

Electron packaged build note:

- `desktop/clipper_electron npm run build:app:mac:arm64`는 내부에서
  `desktop/clipper_angular npm run build:packaged -- --progress=false`를 먼저 실행한다.
- 최신 Angular `origin/dev`는 `pretendard`, `material-symbols` CSS를 `angular.json` global styles에 추가했다.
- 원본 checkout 전환 직후 `desktop/clipper_angular/node_modules`에 이 두 패키지가 없어 packaged build가 실패했다.
- `desktop/clipper_angular`에서 Node v22.22.2로 `npm install --prefer-offline` 실행 후 `added 2 packages`가 나왔고,
  Angular packaged build와 Electron mac arm64 packaged build가 모두 통과했다.

## 2026-06-26 App Version / Release Policy

관련 문서:

- [../design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md](../design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md)

확정 방향:

- 관리자 버전 관리는 `/versions` 방식, 즉 공통 product version + OS별 artifact 방식으로 확정한다.
- `/versions2`의 macOS/Windows 독립 버전 스트림은 채택하지 않는다.
- macOS/Windows user-facing version은 항상 하나로 관리한다. Windows-only fix여도 다음 공통 patch version으로 올린다.
- stable publish는 필수 OS/arch artifact가 모두 build/sign/notarize/verify된 뒤에만 가능하다.
- build/release는 수동 PC 접속 명령이 아니라 관리자 화면 또는 release coordinator의 단일 명령으로 Windows runner와 macOS runner에 동시에 job을 보내는 방향이다.
- macOS signing/notarization은 일반 Linux Docker로 처리할 수 없고 macOS host/keychain/Apple credential이 필요하다.

Release coordinator 배치:

- 본체는 `web/clipper_web_api`의 release module에 둔다. release DB, build job 상태, publish/pull/rollback, download/update target의 SoT다.
- `web/clipper_web_admin`은 operator UI다. release 생성, build 생성, artifact/log 확인, stable promote, pull/rollback을 제공한다.
- `web/clipper_infra`는 runner 설치/운영, S3 prefix, signing/notarization secret, runbook/compose를 담당한다. release 상태의 정본을 갖지 않는다.
- `desktop/clipper_electron`은 실제 packaging script와 release metadata 주입을 담당한다.

DB 모델 변경:

- `release_versions`는 `2.5.1` 같은 제품 버전 단위다. 여기에 `build_number`를 직접 두지 않는다.
- `release_builds`를 별도로 둔다. `build_number`, `display_version`, `artifact_version`, build source snapshot, build status를 가진다.
- `release_artifacts`는 OS/arch 설치 파일 단위이고 `release_build_id`를 참조한다.
- `release_artifact_attempts`는 같은 artifact job을 재시도한 이력을 저장한다.
- stable로 publish되는 macOS/Windows artifact는 같은 `release_build` 아래에 묶이고 같은 build number를 공유한다.
- `build_number`는 release coordinator가 발급하는 전역 단조 증가 번호이며 제품 버전마다 1부터 다시 시작하지 않는다.

코드 배포와 앱 릴리즈:

- web repo의 `prod` deploy는 실제 prod container/page/API를 바꾸는 운영 배포다.
- desktop repo의 `prod` branch에 코드가 있다고 해서 사용자가 바로 app update를 받는 것은 아니다.
- desktop stable release는 build/sign/notarize/upload/QA/manual promote 후 `release_download_targets`와 `release_update_targets`가 바뀔 때 사용자에게 반영된다.
- 성공 artifact는 S3에 올라갈 수 있지만, target pointer에 연결되기 전까지 사용자에게 배포된 것이 아니다.

Desktop branch/tag 정책:

- 기본 환경 브랜치는 `dev`, `stage`, `prod`를 유지한다.
- `release/<version>`은 필요할 때만 만드는 desktop 안정화 브랜치다. 환경 브랜치가 아니라 특정 버전 RC/QA 작업대다.
- QA가 며칠 이상 걸리거나 다음 기능 개발이 stage에 병행되면 desktop 4개 repo에 `release/2.5.0` 같은 브랜치를 만든다.
- stable release마다 desktop 4개 repo 모두에 annotated tag, 예: `v2.5.0`, 를 찍는 방식을 기본으로 한다.
- source snapshot은 계속 필요하다. tag는 git 이름표이고, snapshot은 release DB에 남는 multi-repo commit/tag 조합 기록이다.
- 같은 commit에 `v2.5.0`, `v2.5.1`처럼 여러 tag가 붙을 수 있다. 변경 없는 repo가 여러 제품 release에 포함된 정상 상황이다.

채널/브랜치 기준:

```text
dev -> alpha
stage or release/<version> -> rc
production/release tag -> stable 후보, 수동 publish 승인 후 stable
```

`beta`는 지금 당장 필수 채널이 아니다. 외부 베타 프로그램이 필요해질 때 추가한다.

버전/상태 기준:

- SemVer: `MAJOR.MINOR.PATCH`.
- `MAJOR`: 호환성 파괴, 큰 migration, 런타임 호환 정책 변경.
- `MINOR`: 기존 호환성을 유지하는 사용자 기능/플러그인/workflow 추가.
- `PATCH`: 버그 수정, 설치/서명/공증 수정, 보안 patch, OS-only hotfix.
- `stable`: 현재 일반 사용자에게 배포 중인 정식 버전.
- `superseded`: 정상적으로 더 새 stable에 의해 대체된 과거 버전.
- `pulled`: 한때 배포됐지만 문제로 다운로드/auto update 대상에서 내려진 버전.

Rollback 정책:

- 다운로드/auto update target rollback과 설치된 앱 downgrade를 구분한다.
- 일반 정책은 설치된 앱을 낮은 버전으로 내리지 않는다.
- 문제 release는 `pulled`로 표시하고 신규 다운로드 target을 마지막 정상 artifact로 임시 변경할 수 있다.
- 이미 문제 버전을 설치한 사용자는 `2.4.3 -> 2.4.1` downgrade가 아니라 `2.4.4` 같은 더 높은 patch release로 복구한다.
- 공통 product version은 유지하되, no-op OS artifact는 platform/arch별 `auto_update_enabled=false` 같은 예외로 업데이트 알림을 숨길 수 있다. 단, 코드/데이터/보안/호환성 변화가 없는 경우에만 허용한다.

## 2026-06-23 Plugin Runtime Memory Management Handoff

관련 문서:

- [../design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md](../design/PLUGIN_RUNTIME_MEMORY_MANAGEMENT_2026-06-23.md)
- [../standards/GIT_COMMIT_MESSAGE_POLICY.md](../standards/GIT_COMMIT_MESSAGE_POLICY.md)

현재 branch/commit:

```text
desktop/clipper_nestjs:
  branch: feature/plugin-runtime-memory-management
  pushed HEAD: a978ea7 feat(plugin-runtime): add Python runtime lifecycle policy
  also contains: dded94b chore(template-builder): remove legacy template families and S3 storage

desktop/clipper_angular:
  branch: feature/plugin-runtime-memory-management
  pushed HEAD: 652bc44 chore(template-builder): remove legacy template builder UI paths

desktop/clipper_python:
  branch: feature/plugin-runtime-memory-management
  pushed HEAD: 84a1d44 chore(clipper1): remove legacy template assets

desktop/clipper_electron:
  branch: feature/plugin-runtime-memory-management
  HEAD: e839aca feat(nest-manager): update data directory path for korean_artists.json to match bundle layout
  이번 plugin runtime memory management 커밋 없음
```

중요: plugin/runtime memory management는 완료가 아니라 초기 구현 상태다. 사용자는 아직 실제 앱에서
검증하지 않았다.

NestJS에 구현된 것:

- `PythonRuntimeLifecyclePolicy` 추가.
- `PYTHON_RUNTIME_LIFECYCLE_OPTIONS` DI token으로 env 기반 설정 주입.
- `CLIPPER_PLUGIN_RUNTIME_EXCLUSIVE_GROUP`, `CLIPPER_PLUGIN_RUNTIME_IDLE_SHUTDOWN_MS`,
  `CLIPPER_PLUGIN_RUNTIME_HEALTH_TIMEOUT_MS` 지원.
- Python workflow executor가 실행 전 idle exclusive peer를 종료하고, 실행 후 idle stop을 예약한다.
- `/health`에서 `active_jobs` 또는 `activeJobs`가 0일 때만 `safeToEvictWhenIdle` plugin을 종료한다.

검증된 것:

```text
desktop/clipper_nestjs npm run build
desktop/clipper_nestjs node --test test/python-runtime-lifecycle-policy.test.js
desktop/clipper_nestjs node --test test/*.test.js
desktop/clipper_nestjs git diff --check
```

결과:

- build pass
- lifecycle policy test 3/3 pass
- 전체 Node test 148/148 pass
- diff check pass

다음 세션 첫 확인:

1. 실제 local/devapp/packaged runtime에서 `dance_highlight`, `dialog_highlight`,
   `clipper1_video_render`를 연달아 실행해 idle peer process가 종료되는지 확인한다.
2. 각 Python plugin `/health` payload가 `active_jobs` 또는 `activeJobs`를 정확히 제공하는지 확인한다.
3. heavy plugin manifest에 `resourceProfile.idlePolicy.safeToEvictWhenIdle === true`가 설정되어 있는지 확인한다.
4. Electron packaged mode에서 `PluginHost.stop()`이 child process를 실제 종료하는지 확인한다.
5. 부족하면 Electron/Python/NestJS lifecycle 개선을 추가 구현한다.

커밋 메시지는 반드시 Conventional Commit 형식을 따른다. type 없는 `Add ...`, `Remove ...`,
`Update ...` 메시지는 금지한다.

원격에 남아 있는 dev 미병합 작업 후보:

```text
desktop/clipper_angular:
  origin/feature/variation-v2
    - variation 화면, asset folder/BASE card/clip/sound/BGM/render button UI

desktop/clipper_nestjs:
  origin/feature/variation-v2
    - variation asset folder repository/API/render service
  origin/docs/readme-run-instructions
    - README run instructions only

desktop/clipper_electron:
  origin/feat/logs-ipc
    - clipperBridge.logs openFolder/readAll IPC and sample logs seed script
  origin/feature/variation-v2
    - folder/file selection and fs.listMediaFiles/getPathForFile/openFiles IPC

web/clipper_web_api:
  origin/feat/google-auth
    - ancestry상 dev 미병합으로 보이나 dev 대비 file diff는 비어 있음. 내용은 dev에 흡수된 것으로 보인다.
```

최근 dev에 들어간 큰 흐름:

- `desktop/clipper_angular`: structure cleanup, component-per-folder/spec backfill,
  feature barrel 제거, shared test fake 정리.
- `desktop/clipper_nestjs`: 4-layer structure unification, 이후 NestJS 11 / Express 5 upgrade.
- `desktop/clipper_python`: cross-process logging trace context work가 dev와 합쳐진 상태.
- `desktop/clipper_electron`: cross-process logging, desktop-login merge, bundle data path fix.
- `web/clipper_*`: billing/admin/auth/dev-login, mockup/admin docs, cache clean scripts,
  structure standard alignment.

다음 작업 우선순위는 여전히 plugin/runtime process memory pressure and lifecycle cleanup이다.
단, NestJS에는 위 초기 구현이 들어간 상태이므로 다음 세션은 구현 완료로 가정하지 말고
실제 runtime 관찰과 gap 확인부터 시작한다.

## 2026-06-24 Plugin Runtime Lifecycle Verification

2026-06-24에 local/devapp/packaged runtime에서 실제 Python plugin process lifecycle을 확인하고
부족한 stop 경로를 보강했다.

현재 branch/commit:

```text
desktop/clipper_nestjs:
  branch: feature/plugin-runtime-memory-management
  HEAD: 78d80e8 fix(plugin-runtime): clean up health wait exit listeners
  previous listener cleanup target commit: d8d8f82 fix(template-builder): remove official template DB integration
  previous lifecycle/cancel commit: a2efd95 fix(plugin-runtime): stop managed runtime on cancelled jobs
  previous cancel/lifecycle diagnostics commit: a5a6003 feat(plugin-runtime): expose lifecycle diagnostics and pressure cleanup
  previous retry commit: 11979f3 fix(plugin-runtime): retry idle stop after active jobs finish
  previous TTS lifecycle commit: ef1b23a fix(plugin-runtime): include TTS runtime in lifecycle policy
  previous stop commit: fbf7b41 fix(plugin-runtime): gracefully stop local Python runtime
  previous lifecycle commit: a978ea7 feat(plugin-runtime): add Python runtime lifecycle policy

desktop/clipper_electron:
  branch: feature/plugin-runtime-memory-management
  HEAD: d1a9ab0 fix(plugin-runtime): clean up health wait exit listeners
  previous listener cleanup target commit: 1ea4234 fix(template-builder): remove official DB packaging gate
  previous test script commit: abafc4c test(electron): run node tests with file globs
  previous stop commit: b18f424 fix(plugin-runtime): gracefully stop Electron-hosted Python runtime

desktop/clipper_angular:
  branch: feature/plugin-runtime-memory-management
  HEAD: 3d4c231 test(template-builder): align specs with current ratios
  previous dashboard lifecycle UI commit: 1460727 feat(plugin-runtime): show lifecycle diagnostics on dashboard
  previous cleanup commit: 652bc44 chore(template-builder): remove legacy template builder UI paths

desktop/clipper_python:
  branch: feature/plugin-runtime-memory-management
  HEAD: 84a1d44 chore(clipper1): remove legacy template assets
```

확인한 것:

- `clipper1_video_render` actual runtime smoke에서 `/health.active_jobs === 0` 확인.
- `dance_highlight`, `dialog_highlight`, `tts_supertonic` actual sequential smoke를 local/devapp/packaged mode에서 확인.
- `dance_highlight`, `dialog_highlight` actual job 중 `/health.active_jobs > 0`을 관찰했고, job 종료 후 `0`으로 돌아오는 것을 확인.
- local mode에서 job 완료 후 idle stop이 Python `/shutdown`을 호출하고 process가 exit code 0으로 종료됨.
- devapp mode에서 동일하게 idle stop 후 child process가 실제 종료됨.
- rebuilt packaged Electron app에서 idle stop과 explicit `POST /plugins/:name/stop` 모두 Python `/shutdown`을 거쳐
  child process가 exit code 0으로 종료됨.
- Electron packaged bridge `PluginHost.stop()` 경로는
  Electron bridge -> bundled NestJS `LocalPluginManager.stop()` -> Python `/shutdown` -> process exit까지 확인됨.
- `tts_supertonic`은 기존 default lifecycle group 밖이라 heavy peer와 함께 남는 gap이 있었고,
  `ef1b23a`에서 default group에 포함하고 `TtsPluginClient`가 lifecycle policy를 거치도록 수정함.
- packaged cancel probe에서 NestJS job cancel은 즉시 `cancelled`가 되지만 Python `/health.active_jobs`가
  잠시 1로 남는 것을 확인했다. 기존 idle stop timer는 이 시점에 한 번만 확인하고 끝날 수 있어,
  장시간 cancelled job 이후 process가 유휴로 남을 수 있었다.

구현한 것:

- NestJS `LocalPluginProcess.stop()`이 SIGTERM 전에 Python plugin `/shutdown`을 먼저 요청한다.
- Electron main `PluginProcess.stop()`도 동일하게 `/shutdown`을 먼저 요청한다.
- `/shutdown` 실패 또는 timeout 시 SIGTERM, 이후 SIGKILL까지 기다리고, SIGKILL 후에도 종료되지 않으면 error를 던진다.
- 두 repo 모두 stop helper 단위 테스트를 추가했다.
- NestJS default Python runtime exclusive group에 `tts_supertonic`을 추가했다.
- `TtsPluginClient`가 synthesis 전 `prepareForRun()`, 완료 후 `scheduleIdleStop()`을 호출한다.
- `11979f3`에서 scheduled idle stop이 `/health.active_jobs > 0` 때문에 stop하지 못한 경우,
  plugin이 여전히 running이고 `safeToEvictWhenIdle`이면 같은 idle delay로 재확인하도록 수정했다.
- `abafc4c`에서 Electron test script를 Node 22 호환 glob 실행으로 고정했다.
- `a5a6003`에서 `/v1/plugins`와 `/v1/plugins/:name/status`의 Python plugin status에
  `runtimeHealth.activeJobs`와 lifecycle metadata를 포함하도록 확장했다.
- `a5a6003`에서 heavy Python plugin 시작 전 projected memory headroom이 낮으면
  Electron/NestJS resource snapshot의 plugin RSS를 보고 idle safe-to-evict runtime을 RSS 큰 순서로 정리한다.
  `/health.active_jobs > 0`인 runtime은 정리하지 않는다.
- `1460727`에서 dashboard plugin row가 runtime active job 수, 다음 idle cleanup 확인 시간,
  마지막 종료 코드, exclusive-group 기반 자동 정리 설명을 표시하도록 수정했다.
- `a2efd95`에서 NestJS job cancel 후 host-owned, safe-to-evict Python runtime을 즉시 stop하도록 수정했다.
  external/static runtime host는 그대로 둔다.
- `3d4c231`에서 current ratio policy(`16:9`, `4:3`, `1:1`, shortform `1:1`/`4:3`)에 맞게
  TemplateBuilder Karma spec 기대값을 정리했다.
- `d8d8f82`에서 NestJS Template Builder official DB/Postgres/S3 registry integration remnants를 제거했다.
  Template Builder family list는 local JSON store만 사용한다.
- `1ea4234`에서 Electron packaged build의 `CLIPPER2_TEMPLATE_DB_*` env gate를 제거했다.

검증:

```text
desktop/clipper_electron npm run build
desktop/clipper_electron node --test test/child-process-stop.test.js
desktop/clipper_electron node --test test/*.js test/*.mjs
desktop/clipper_electron nvm use 22 && npm test
desktop/clipper_electron git diff --check

desktop/clipper_nestjs npm run build
desktop/clipper_nestjs node --test test/local-plugin-process-stop.test.js
desktop/clipper_nestjs node --test test/*.test.js
desktop/clipper_nestjs git diff --check

desktop/clipper_angular ./node_modules/.bin/tsc -p tsconfig.app.json --noEmit
desktop/clipper_angular ./node_modules/.bin/tsc -p tsconfig.spec.json --noEmit
desktop/clipper_angular ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/shell/dashboard/dashboard.component.spec.ts
desktop/clipper_angular CI=1 npm run build:packaged -- --progress=false
desktop/clipper_angular git diff --check

desktop/clipper_electron npm run build:app:mac:arm64
desktop/clipper_electron npx electron-builder --mac --arm64 --publish never
actual sequential smoke:
  local:    dance_highlight -> dialog_highlight -> clipper1_video_render -> tts_supertonic -> dance_highlight
  devapp:   dance_highlight -> dialog_highlight -> clipper1_video_render -> tts_supertonic -> dance_highlight
  packaged: dance_highlight -> dialog_highlight -> clipper1_video_render -> tts_supertonic -> dance_highlight
rebuilt packaged app smoke:
  idle stop: clipper1_video_render PID terminated, lastExitCode=0
  explicit stop: clipper1_video_render PID terminated, lastExitCode=0

real full pipeline output smoke:
  input:
    dance_highlight: YouTube CHp0Kaidr14, downloaded as /tmp/clipper-youtube-real-input/CHp0Kaidr14.mp4
    dialog_highlight: YouTube ulQr-_f3DG8, downloaded as /tmp/clipper-youtube-real-input/ulQr-_f3DG8.mp4
  command:
    CLIPPER_E2E_DANCE_VIDEO=/tmp/clipper-youtube-real-input/CHp0Kaidr14.mp4
    CLIPPER_E2E_DIALOG_VIDEO=/tmp/clipper-youtube-real-input/ulQr-_f3DG8.mp4
    CLIPPER_E2E_OUTPUT_ROOT=/tmp/clipper-youtube-real-output-with-llm
    uv run --extra test pytest tests/e2e/test_real_pipeline.py -v -s
  result:
    2 passed in 242.54s
    dialog output includes /tmp/clipper-youtube-real-output-with-llm/dialog/json/manifest.json
    dance output includes /tmp/clipper-youtube-real-output-with-llm/dance/json/dance_meta.json and montage mp4 files

packaged normal-video memory lifecycle probe:
  sequence:
    cycle 1: dance_highlight full pipeline -> dialog_highlight full pipeline -> tts_supertonic generate
    cycle 2: dance_highlight full pipeline -> dialog_highlight full pipeline -> tts_supertonic generate
  app:
    dist-app/mac-arm64/Clipper2.app/Contents/MacOS/Clipper2
    packaged NestJS API: http://127.0.0.1:60929/v1
  input:
    dance_highlight: /tmp/clipper-youtube-real-input/CHp0Kaidr14.mp4
    dialog_highlight: /tmp/clipper-youtube-real-input/ulQr-_f3DG8.mp4
  output:
    /tmp/clipper-packaged-memory-probe-2026-06-24T04-02-46-162Z
    summary: /tmp/clipper-packaged-memory-probe-2026-06-24T04-02-46-162Z/memory-probe-summary.json
  result:
    completed=6, failures=0
    max plugin process count=1
    final running plugins=none
    final plugin process count=0
    max sampled relevant RSS=3386 MB
    dance pids: 82940, 86976; max sampled RSS=2996 MB; active_jobs observed 1 -> 0
    dialog pids: 84373, 88382; max sampled RSS=1553 MB; active_jobs observed 1 -> 0
    tts pids: 86854, 90612; max sampled RSS=562 MB
    all observed peer evictions exited with lastExitCode=0
    generated cycle-1/cycle-2 dance_meta.json and dialog manifest.json

packaged cancel/error/idle probe:
  app:
    existing packaged Clipper2 primary instance
    packaged NestJS API: http://127.0.0.1:62052/v1
  summary:
    /tmp/clipper-packaged-cancel-error-idle-2026-06-24T04-21-42-900Z/cancel-error-idle-summary.json
  result:
    missing source file and corrupt mp4 fail in NestJS validation before plugin start
    TTS idle reuse window: same PID reused within 30s, stopped after the 60s idle window with lastExitCode=0
    dance cancel: NestJS job became cancelled immediately, Python active_jobs stayed 1 until worker finished, then stopped with lastExitCode=0
    output-root error probe started dance_highlight PID 6054, failed inside plugin with read-only filesystem error,
      then /health.active_jobs returned 0 and idle stop terminated the process with lastExitCode=0

Node/test baseline:
  desktop/clipper_electron/.nvmrc is 22
  final Electron verification used Node v22.22.2
  npm test now runs node --test "test/*.js" "test/*.mjs" and passes 23/23
  desktop/clipper_nestjs final build/test verification also used Node v22.22.2

dashboard inventory and gap:
  /dashboard refreshes plugin status, resource snapshot, and jobs every 3s
  resource panel shows memory percent/used/total, CPU load/cores, OS/arch,
    tracked process count, GPU/VRAM summary, and per-process PID/RSS/CPU rows
  plugin panel shows runtime plugin rows, install/start/stop actions, port/runtime age,
    accelerator labels, resource warnings, estimated RAM/VRAM, PID/RSS/CPU when running,
    lastError on error, and a bulk "stop evictable runtimes" action
  idle cleanup label now prefers Python plugin /health.active_jobs over NestJS app job count
  plugin rows show scheduled cleanup countdown, lastExitCode, and exclusive-group peer eviction explanation

packaged app smoke after a5a6003/1460727:
  built:
    dist-app/mac-arm64/Clipper2.app
    dist-app/Clipper2-0.0.1-arm64.dmg
  API:
    http://127.0.0.1:64942/v1
  checked:
    GET /v1/plugins returned Python plugin status.lifecycle.safeToEvictWhenIdle=true
    GET /v1/plugins returned participatesInExclusiveGroup=true and the default exclusive group
    packaged app shutdown closed NestJS with exit code 0

final follow-up after a2efd95/3d4c231:
  NestJS Node v22.22.2:
    npm run build pass
    node --test test/python-runtime-lifecycle-policy.test.js 8/8 pass
    node --test test/*.test.js 157/157 pass
    npm run bundle pass
    git diff --check pass before commit
  Angular Node v22.22.2:
    ./node_modules/.bin/tsc -p tsconfig.app.json --noEmit pass
    ./node_modules/.bin/tsc -p tsconfig.spec.json --noEmit pass
    ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless 638/638 pass
    CI=1 npm run build:packaged -- --progress=false pass
    git diff --check pass before commit
  Electron Node v22.22.2:
    npm run build pass
    npm test 23/23 pass
    CI=1 npm run build:app:mac:arm64 rebuilt Angular/NestJS/Electron and packaged .app,
      then failed only at GitHub publish because GH_TOKEN is not set
    npx electron-builder --mac --arm64 --publish never pass
  packaged cancel/error/idle probe:
    app API: http://127.0.0.1:51660/v1
    summary: /tmp/clipper-packaged-cancel-error-idle-2026-06-24T05-44-04-496Z/cancel-error-idle-summary.json
    completed=3, failures=0
    error path stayed stopped after NestJS validation failure
    TTS reused PID 4968 inside the 30s idle window and stopped after the idle window
    dance cancel observed active_jobs=1 before cancel, job became cancelled, and after DELETE
      dance_highlight was already stopped; observedActiveAfterCancel=null, stoppedWithin100s=true
  packaged normal-video memory lifecycle probe:
    app API: http://127.0.0.1:51660/v1
    summary: /tmp/clipper-packaged-memory-probe-2026-06-24T05-46-03-415Z/memory-probe-summary.json
    completed=6, failures=0, sampleCount=81
    max plugin process count=1
    final running plugins=none
    final plugin process count=0
    max sampled relevant RSS=2833 MB
    max sampled plugin RSS: dance_highlight=2462 MB, dialog_highlight=1543 MB, tts_supertonic=563 MB
    active job values stayed within expected 0/1 samples; activeMismatchCount=0
  process cleanup:
    after packaged app shutdown, pgrep found no Clipper2/dance_highlight/dialog_highlight/tts_supertonic/clipper1_video_render processes
  known verification note:
    The default shell still resolves `node` to v24.3.0. Final verification evidence above used PATH-pinned Node v22.22.2.
    Direct `ng` invocations without the Node 22 PATH are not valid evidence for this branch.
```

Template Builder packaged-store follow-up from the same session:

```text
problem:
  packaged Template Builder page returned 500 for /v1/template-builder/families because official Template DB remnants
  still existed after the product decision to remove official DB/S3 registry paths.

code fixes:
  desktop/clipper_nestjs d8d8f82
    removed official DB repository/provider/Postgres adapter/env requirement
    added no-official-DB regression test
  desktop/clipper_electron 1ea4234
    removed CLIPPER2_TEMPLATE_DB_* packaged build gate
    added build-script regression test

branch consolidation:
  fix/template-builder-packaged-store was fast-forward merged into feature/plugin-runtime-memory-management
  in desktop/clipper_nestjs and desktop/clipper_electron.
  dev/main were not touched.

current push state:
  desktop/clipper_nestjs feature/plugin-runtime-memory-management is ahead of origin by 1
  desktop/clipper_electron feature/plugin-runtime-memory-management is ahead of origin by 1
  desktop/clipper_angular and desktop/clipper_python are clean and aligned with origin feature branch
```

Template Builder local user-data repair:

```text
root cause:
  API delete removes template-assets/<familyId>. JSON-only restore made five visible shortform templates point to
  missing card thumbnail PNGs and missing uploaded font files.

backup:
  ~/Library/Application Support/Clipper2/templates/template-builder.backup-before-font-thumbnail-repair-2026-06-24T08-04-00-605Z.json

repair:
  restored/generated 5 card thumbnail PNG files at the existing cardThumbnailUri paths
  copied 7 missing uploaded font files back into template-assets
  removed 36 legacy clipperstudio.s3 font references
  mapped JalnanGothic to local asset files
  mapped legacy Pretendard URLs to bundled template-builder/fonts/Pretendard-SemiBold.otf

packaged verification:
  GET /v1/template-builder/families => 200
  5 visible shortform families
  thumbnails: 5/5 image/png 200
  font endpoints: 35/35 200
  legacy S3 font refs: 0
  non-Pretendard preview text artifacts: 17/17 rendered, bad frame count 0
```

Template Builder preview-artifact MaxListeners follow-up:

```text
Resolved the Electron packaged Template Builder preview-artifact smoke warning:

  MaxListenersExceededWarning: Possible EventEmitter memory leak detected.
  11 exit listeners added to [ChildProcess]. MaxListeners is 10.

Root cause:
  waitForHealthOrDeath() attached a one-shot ChildProcess exit listener before polling /health.
  When /health succeeded, the process stayed alive and the exit listener was never removed.
  Repeated ensureStarted() calls against the same live clipper1_video_render worker accumulated listeners.

Fix:
  desktop/clipper_electron d1a9ab0
    PluginProcess.onceExited() now returns a cleanup function.
    LocalPluginManager.waitForHealthOrDeath() calls cleanup when health wait settles.
    Added test/plugin-manager-exit-listener.test.js.

  desktop/clipper_nestjs 78d80e8
    LocalPluginProcess.onceExited() now returns a cleanup function.
    LocalPluginHost.waitForHealthOrDeath() calls cleanup when health wait settles.
    Added test/local-plugin-host-exit-listener.test.js.

Verification:
  Node v22.22.2 was PATH-pinned for all commands.
  Electron targeted warning-as-error repro => exit listeners 0.
  NestJS targeted warning-as-error repro => exit listeners 0.
  Electron npm test => 25/25 pass.
  Electron targeted lifecycle tests => 3/3 pass.
  NestJS targeted lifecycle/template-artifact tests escalated => 15/15 pass.
  Electron npm run build pass.
  NestJS npm run build pass.
  Electron/NestJS git diff --check pass.
  Electron npm run build:app:mac:arm64 pass when rerun escalated.

Known unrelated test issue:
  NestJS full node --test test/*.test.js:
    sandbox run failed on listen EPERM.
    escalated run reached 153/158 pass.
    five failures are repeatable shortform-project-api dry-run render job timeouts.
    The same file fails the same five cases when run alone escalated, so track separately from listener cleanup.
```

## 2026-06-23 Web Admin App Version Management Notes

`web/clipper_web_admin`에서 앱 버전 관리 mock 화면을 검토했다.

```text
branch: feat/admin-version-management-ui
commit: f04230a feat: add admin version management mock screens
```

현재 볼 수 있는 화면:

- `/versions`: 공통 앱 release + OS별 artifact 방식
- `/versions2`: macOS/Windows 독립 release stream 비교안

관련 설계 문서:

- [../design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md](../design/APP_VERSION_MANAGEMENT_APPROACHES_2026-06-23.md)

핵심 판단:

- 최종 방식은 아직 확정하지 않는다.
- 현재 Clipper는 공통 Electron 앱/공통 desktop repo 묶음이므로 `/versions`가 기본 후보에 가깝다.
- 그러나 Windows는 코드서명 준비가 되어 있고 macOS는 아직 공증/서명 준비가 안 되어 `xattr` 수동 안내가 필요한 상태라, OS별 배포 현실을 보면 `/versions2`가 더 자연스럽게 느껴지는 이유도 타당하다.
- 다음 설계에서는 “제품 버전”과 “실제 배포 artifact”를 분리해서 본다.
- DB/API는 release보다 artifact를 더 진실에 가까운 단위로 보고, `release_download_targets.current_artifact_id`가 artifact를 직접 가리키는 구조를 우선 검토한다.

## 2026-06-19 Current Focus

4개 레포의 사용자 작업은 현재 원격 `dev`에 들어간 상태다. PR 단계는 생략했다.
세션 마지막에 4개 레포 모두 로컬 branch를 `dev`로 체크아웃하고 `origin/dev`까지
fast-forward했으며, 확인용 `.worktrees/origin-dev-20260619` worktree도 제거했다.

다음 세션의 첫 작업은 최신 `dev` 기준 새 브랜치를 만들고, 여러 plugin/runtime을
연달아 실행할 때 메모리가 부족해져 앱이 종료되거나 다른 앱까지 freeze되는 문제를
완화하는 것이다. 먼저 Electron/NestJS/Python/Angular 전체의 plugin/runtime/worker
process lifecycle을 조사하고, idle process cleanup 또는 exclusive plugin group 정책을
설계한 뒤 사용자 승인 후 구현한다.

먼저 읽을 문서:

- [../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)
- [../design/TEMPLATE_BUILDER_SIMPLIFICATION_IMPLEMENTATION_PLAN_2026-06-15.md](../design/TEMPLATE_BUILDER_SIMPLIFICATION_IMPLEMENTATION_PLAN_2026-06-15.md)
- [../design/ANGULAR_DEV_STRUCTURE_REFACTOR_ANALYSIS_2026-06-19.md](../design/ANGULAR_DEV_STRUCTURE_REFACTOR_ANALYSIS_2026-06-19.md)
- [../records/sessions/2026/06/19.md](../records/sessions/2026/06/19.md)
- [../records/sessions/2026/06/18.md](../records/sessions/2026/06/18.md)
- [../records/sessions/2026/06/17.md](../records/sessions/2026/06/17.md)
- [../records/sessions/2026/06/16.md](../records/sessions/2026/06/16.md)
- [../records/sessions/2026/06/15.md](../records/sessions/2026/06/15.md)

현재 app/code commit:

```text
clipper_angular:  96cd2f1 test: cover failed highlight project cards
clipper_electron: 25ac58f Merge branch 'feature/windows-packaging' into merge/dev-selected-20260619
clipper_nestjs:   d8260fc test: remove archived template builder API tests
clipper_python:   4922c5c Merge branch 'feature/windows-packaging' into merge/dev-selected-20260619
```

최신 follow-up:

```text
clipper_angular:  96cd2f1 test: cover failed highlight project cards
clipper_electron: 25ac58f Merge branch 'feature/windows-packaging' into merge/dev-selected-20260619
clipper_nestjs:   d8260fc test: remove archived template builder API tests
clipper_python:   4922c5c Merge branch 'feature/windows-packaging' into merge/dev-selected-20260619
```

## Current Open Work Queue

2026-06-24 기준 현재 남은 작업이다.

1. Push 또는 merge 판단
   - `desktop/clipper_electron` `feature/plugin-runtime-memory-management`는
     `origin/feature/plugin-runtime-memory-management` 대비 ahead 1:
     `d1a9ab0 fix(plugin-runtime): clean up health wait exit listeners`.
   - `desktop/clipper_nestjs` `feature/plugin-runtime-memory-management`는
     `origin/feature/plugin-runtime-memory-management` 대비 ahead 1:
     `78d80e8 fix(plugin-runtime): clean up health wait exit listeners`.
   - `dev`/`main` merge는 아직 하지 않았다.

2. Shortform render dry-run test timeout 확인
   - NestJS full test escalated run에서 `test/shortform-project-api.test.js` 5개가
     `pipeline job did not finish`로 timeout.
   - 같은 file 단독 escalated 실행에서도 같은 5개가 재현됨.
   - job은 `render_prepare_pending=false` 이후 `running`에 머무는 상태로 보였고,
     listener cleanup과는 별도 worker/job completion issue로 분리한다.

3. Project-first / Plugin / Queue 전체 정리
   - 상세 기준은 아래 `Project-First / Plugin / Queue Status`와
     `PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md`,
     `PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md`를 따른다.
   - 현재 ID 구조:
     `shortform_project_*`는 편집 원본 project,
     `shortform_*`는 promoted/completed render project,
     `shortform_render_*`는 queue job,
     `source.shortform_project_*`는 completed manifest의 source asset id다.
   - `promotedProjectId`는 원본 shortform project에서 보관함 project id로 가는 연결고리다.
3. 작업 보관함 non-shortform project detail flow
   - 2026-06-17에 `/projects` completed shortform card는 오른쪽 inline detail panel 대신
     hover action overlay + `편집`/`재생`으로 바뀌었다.
   - 2026-06-18 `clipper_angular` `a7a1211`에서 non-shortform 완료 카드에 직접 `재생`을 붙인
     잘못된 변경(`60a0b83`)을 되돌렸다.
   - 2026-06-18 `clipper_angular` `92a54b9`에서 non-shortform 완료 카드는 `결과 보기` 액션으로
     `/projects/:projectId` 상세 라우트에 진입한다.
   - 2026-06-18 `clipper_angular` `5fa436c`에서 상세 라우트 내부를 이전 오른쪽 inline
     detail panel과 같은 header/source/result-section 래퍼 및 스타일로 복원했다.
   - 2026-06-18 `clipper_angular` `fb03b92`에서 새 상세 라우트가 전역 `.projects-page`
     result 스타일을 받지 못하던 문제를 고쳤다. `.projects-detail-page`에도 `shorts-frame`,
     clip row, info panel 공통 스타일을 적용하고, panel 폭을 예전 오른쪽 inline panel에 가까운
     1022px로 제한했다.
   - 상세 라우트는 일단 기존 `DialogResultDetailComponent`/`DanceResultDetailComponent`와
     이전 inline panel UI를 그대로 사용한다. 나중에 UI 구성은 별도 정리한다.
4. 작업 보관함 completed card UI redesign
   - 2026-06-18 `clipper_angular` `fd6e55a`에서 completed card hover overlay action을 제거하고,
     카드 하단에 항상 보이는 action button 영역을 둔다.
   - completed project card thumbnail은 card kind별로 나눈다. shortform은 최종 render에서 저장하는
     `main_thumbnail.jpg`를 우선 사용하고 9:16 output thumbnail frame을 유지한다.
   - source-video 계열 non-shortform은 input longform/source thumbnail을 우선 사용하고 16:9
     source thumbnail frame을 쓴다. source thumbnail이 없을 때만 completed result clip/render
     thumbnail으로 fallback한다.
   - 2026-06-18 `clipper_angular` `b399f18`에서 card metadata를 정리했다.
     shortform은 input mode, clip count, duration, template snapshot display name을 표시하고,
     non-shortform은 completed result clips 기준 clip count/duration을 표시한다.
   - 2026-06-18 `clipper_angular` `2e3a8b5`에서 사용자 확인 후 card layout을 다시 정리했다.
     모든 thumbnail은 카드 내부 높이를 채우는 9:16 영역으로 표시하고, duration은 thumbnail 우하단
     badge로 겹쳐 표시한다. card chip에서는 source mode, clip count, template name을 제거했다.
     shortform plugin label은 `URL로 숏폼 제작`/`붙여넣기로 숏폼 제작`/`프롬프트로 숏폼 제작`으로
     표시한다.
   - 2026-06-18 `clipper_angular` `cb8598e`에서 plugin/workflow kind line을 thumbnail/content grid
     안이 아니라 card 최상단 전체 폭 row로 이동했다.
   - 2026-06-18 `clipper_angular` `e757fe9`에서 plugin/workflow kind line을 card 상단 banner처럼
     보이도록 배경, 하단 border, card padding을 덮는 negative margin을 적용했다.
   - 2026-06-18 `clipper_angular` `c50093d`에서 위 strip-style banner는 되돌리고,
     plugin/workflow title text 자체만 `완료`/`실패` status와 같은 pill badge 스타일로 바꿨다.
   - 2026-06-18 `clipper_angular` `2cc5919`에서 사용자 확인 후 pill badge도 제거했다.
     최종 kind line은 card 최상단 전체 폭 row 위치를 유지하되, banner/pill이 아닌 plain text 스타일이다.
   - 2026-06-18 `clipper_angular` `48c1342`에서 archive page 용어를 `작업 보관함`/`완료된 작업`에서
     `프로젝트 보관함`/`프로젝트 내역`으로 바꿨고, completed/history 영역을 감싸던 outer
     border/background/padding panel을 제거했다. 큐 문맥의 `작업` 용어와 개별 project card border는 유지한다.
   - 2026-06-18 `clipper_angular` `3be569d`에서 archive card view model에
     `cardKind`(`shortform-output`/`source-video-output`)를 추가했다. shortform card는 기존
     portrait output thumbnail layout을 유지하고, source-video card는 landscape input source
     thumbnail layout을 사용한다.
   - 2026-06-18 `clipper_angular` `54b419b`에서 `프로젝트 내역`을 `cardKind + pluginLabel`
     섹션으로 나눴다. shortform 섹션은 좁고 긴 portrait card grid를 쓰고, 카드 내 `재생`/`편집`
     버튼을 제거했다. shortform card title은 render/project title fallback보다 render manifest의
     `mainTitle1 + mainTitle2`를 우선 표시한다. source-video card는 landscape source thumbnail
     아래 input video title을 최대 2줄로 표시한다.
   - 2026-06-18 `clipper_angular` `f9c90c3`에서 section heading을 `프로젝트`로 줄이고 font size를
     키웠으며, `완료 상태만 보기` 버튼을 제거했다. plugin section heading도 키우고 `(count)`를 붙인다.
     shortform URL/paste/prompt project는 더 이상 mode별 섹션으로 나누지 않고 `클리퍼` 섹션 하나로
     묶는다.
   - 2026-06-18 후속 정정에서 `clipper_studio` project를 숨기는 필터 방식은 제거했다. 대신
     Angular의 `clipper-studio` project client/query 코드와 NestJS의 `/projects/clipper-studio...`
     project API/DTO/service/module registration을 삭제했다. shortform 생성/렌더가 재사용 중인 legacy-named
     low-level provider 파일은 기능 의존성 때문에 유지한다.
   - 실제 앱 내부 저장소 `/Users/jina/Library/Application Support/Clipper2/projects/projects.json`에서도
     `clipper_studio_*` project 13개와 matching outputRoot directory 13개를 삭제했다.
   - 2026-06-18 후속 `clipper_angular`에서 project card 자체 border/background/padding을 제거했다.
     카드 내부 plugin name top row도 제거해 thumbnail이 바로 맨 위에 온다. Clipper card는 thumbnail/date만,
     source-video/highlight card는 thumbnail/source-video-title/date만 표시한다. `완료` status,
     `history-title`, `history-footer`, `history-card-actions`는 card에서 제거했다.
   - plugin별 project section은 grid가 아니라 한 줄 horizontal scroll row로 표시하고, plugin section
     사이에는 full-width divider line을 둔다. `source-video-title`은 정확히 2줄 높이로 고정하고 긴 제목은
     ellipsis 처리한다.
   - 2026-06-18 후속 `clipper_angular`에서 메인 `/projects`는 plugin section별 최신 10개만 표시하고,
     초과분이 있으면 row 오른쪽에 `더보기 +N` 카드가 생긴다. `더보기`는
     `/projects/history/:sectionKey`로 이동해 해당 plugin section 전체를 보여준다. 이 route는
     `projects/:projectId`보다 먼저 선언한다. 전용 history page는 queue를 숨기고 section 전체 목록만
     보여준다.
   - 같은 후속에서 Clipper card width를 키워 portrait thumbnail 높이를 늘렸고, Clipper row gap,
     thumbnail-date gap, date center alignment를 조정했다.
   - 2026-06-18 후속 `clipper_angular`에서 row 직접 scrollbar를 숨기고, section 양옆 `<`/`>` 버튼으로
     `scrollBy` 이동하게 바꿨다. divider line 색은 더 진하게 조정했다. duration badge는 `12s`가 아니라
     `00:12` timecode 형식이고, source-video/highlight card는 input source video duration을 우선 표시한다.
     card cursor는 pointer이며 duration pill 배경은 더 투명하게 조정했다.
   - 2026-06-18 후속 `clipper_angular`에서 row `<`/`>` 버튼을 layout column이 아니라 row 위에 겹치는
     absolute overlay로 바꿨다. 최신 항목을 보고 있는 시작 위치에서는 `<`를 숨기고, 마지막 project까지
     보이는 끝 위치에서는 `>`를 숨긴다. 버튼 이동량은 기존 640px에서 `max(960px, row width 90%)`로 키웠다.
   - 2026-06-18 후속 `clipper_angular`에서 실행 큐 job이 `completed`로 완료 목록에 들어오면 메인
     `/projects`에서 해당 `cardKind + pluginLabel` plugin row로 세로 스크롤 이동한다. 해당 row 내부도
     `scrollTo({ left: 0 })`로 최신 project card가 보이게 되돌린다. `/projects/history/:sectionKey`
     전체보기 페이지에서는 자동 reveal을 하지 않는다.
   - 2026-06-18 후속 정정으로 완료 job 최신순 입력 때문에 방금 완료된 plugin section이 맨 위로
     재배치되던 문제를 막았다. `/projects` plugin section 순서는 `클리퍼`, `대사 하이라이트`,
     `안무 하이라이트`로 고정하고, 완료 reveal은 순서를 바꾸지 않고 해당 section 위치로만 세로 스크롤한다.
   - 2026-06-18 후속 정정으로 실행 큐 expanded 상태의 `queue-shell` padding은 제거했다. shell padding은
     `queue-bar`와 `queue-popover` 사이를 갈라 보이게 하고, popover padding 증가는 내부 padding 경계에
     glow가 생겨 보이게 하므로 사용하지 않는다. `queue-popover`는 기본 padding `16px`를 유지하고
     `overflow: visible`로 둔다. 하단 glow는 pseudo-element가 아니라 expanded `queue-popover` 자체의
     `border-bottom-color`와 `box-shadow`로 직접 강조한다.
5. 남은 renderer/app QA와 cleanup
   - packaged app에서 Template Builder custom preset end-to-end render QA.
   - video/thumbnail/manifest/artifact path가 앱 재시작 후에도 열리는지 검증.
   - Python worker lifecycle: dev/packaged start/stop, port/baseUrl, event delivery,
     output_root access.
   - 더 이상 쓰지 않는 `VideoRenderJobsService`/old render provider path 제거 전 grep.
6. Preview/URL/fixture follow-up
   - Angular current branch preview snapshot export test 2개 실패는 별도 Angular 작업으로 남김.
   - URL extractor selector edge case와 실제 URL QA 보강.
   - 구형 21개 Clipper1 golden/baseline fixture는 현재 shortform 생성 경로가 아니므로
     후순위/별도 경로로 유지한다.

2026-06-17 shortform render queue follow-up:

- `숏폼 생성하기`는 더 이상 console payload 출력이나 별도
  `VideoRenderJobsService` synthetic completed project 경로를 사용하지 않는다.
- Angular는 현재 shortform edit state를 저장한 뒤 render API 응답의 job id로
  `/projects?plugin=clipper1_video_render&job=...` 이동한다. backend가 먼저 job을
  reserve하므로 사용자는 `/projects`에서 즉시 `렌더 준비 중` 큐 항목을 본다.
- NestJS shortform render API는 먼저 `JobsService.reserve()`로
  `clipper1_video_render` waiting job을 만들고, asset/manifest/recipe/legacy payload
  preparation이 끝난 뒤 `JobsService.activateReserved()`로 같은 jobId를 실행 큐에 넣는다.
- `/projects` 완료 항목은 `JobsService` 완료 이벤트 이후
  `ProjectsService.recordCompletedJob()`에서만 생성된다.
- job result와 completed project result에는 `render_manifest`를 `manifest`로
  보존한다.
- `clipper1_video_render` worker는 존재하지만 adlight_python `VideoService.py`의
  완전 parity 포팅은 아니다. 현재 경로는 기존 Python plugin worker/local adapter를
  일반 작업 큐에 연결한 상태다.
- simplified shortform template은 Clipper1 legacy payload로 직접 render하지 않는다.
  실제 render path는 legacy Clipper1 또는 Template Builder custom preset 기준이다.
- 2026-06-17 추가 수정으로 Template Builder shortform render의 최종 output contract는
  Python worker와 Nest manifest 모두 1080x1920으로 고정됐다. `contents_ratio`는
  content area 높이/비율 의미로만 유지한다.
- 구형 21개 Clipper1 baseline template은 현재 Clipper2 shortform 생성의 실사용 기준이
  아니다. 다음 renderer 작업은 `mainTitleLine1`, `mainTitleLine2`, clip subtitle
  1/2줄, layout/background layer, content area, image/GIF/video media 경로를 기준으로
  진행한다.
- 2026-06-17 follow-up `clipper_python` `9396094`에서
  `local_render_adapter.py`는 유지하고 VideoService parity checklist 기준으로
  Template Builder 실사용 path gap을 보정했다. payload 구조는 바꾸지 않았다.
- 2026-06-17 follow-up `clipper_nestjs` `6e98b15`에서 shortform render API는
  heavy asset/manifest/legacy payload preparation 전에 `/jobs` record를 먼저 만들고
  `렌더 준비 중`으로 큐에 즉시 표시한다. 준비가 끝나면 같은 jobId를 activate해
  Python worker를 실행한다.
- 2026-06-17 follow-up `clipper_python` `d30fc35`에서
  `clipper1_video_render` progress message를 한국어로 바꿨다. `Rendering clip 1/N`의
  `N`은 user-facing shortform clip 수가 아니라 recipe timeline item/media slot 수이므로
  `렌더 세그먼트 1/N 처리 중`으로 표시한다.
- 2026-06-17 follow-up `clipper_angular` `4dffe76`에서 `/projects` 완료 영역은
  오른쪽 상세 패널 대신 큰 project card grid를 사용한다. Shortform 완료 카드 클릭은
  레거시 Clipper1처럼 action overlay를 띄우고, `편집` 버튼만
  `/shortform/<mode>?project=<shortformProjectId>`로 이동해
  `ShortformWorkflowPageComponent`가 input/clips/styles/templates를 복원한다.
  `재생` 버튼은 완료 output video overlay를 연다.
- 2026-06-17 follow-up `clipper_nestjs` `ec50176`에서 실제 render media가
  remote URL artifact일 때 seed placeholder로 대체되던 문제를 고쳤다. Python worker는
  remote asset staging을 지원하므로 shortform render manifest/legacy payload는 실제
  clip media URL을 유지한다. 또한 `bgm.bright` 같은 UI catalog id를
  `artifact.clipper-studio.bgm.legacy.bright` 같은 renderable BGM artifact id로 정규화해
  BGM 선택 시 render preparation이 실패하지 않게 했다.
- 2026-06-17 follow-up `clipper_angular` `0c4fb15`에서 완료 shortform card action
  overlay는 selected state가 아니라 hover/focus-within으로 보인다. 완료 이벤트가 카드를
  자동 선택하던 동작도 제거했다.
- 2026-06-17 follow-up `clipper_nestjs` `af8e838`에서 Template Builder shortform
  published preset이 legacy render mapper에 필요한 `templateBuilderRenderContract`,
  `templateBuilderLayers`, `templateBuilderContentArea`, `templateBuilderOutputSize`를
  `defaultParams`에 포함하도록 고쳤다. 또한 shortform recipe의 `main_title1`,
  `main_title2` overlay role을 legacy `project.main_title_check/main_title1/main_title2`
  payload로 매핑한다. 실제 완료 job `shortform_render_1781704268262` recipe를 새 코드로
  다시 매핑하면 content area는 `y=456,height=1080`, layout layer는 `#0017c7`,
  main title 두 줄은 보존된다.
- 2026-06-17 follow-up `clipper_python` `8a5436d`에서 Template Builder contract render
  test가 ffmpeg output frame을 추출해 background color와 content area media pixel을
  확인한다. renderer production code 변경은 없다.
- 2026-06-18 follow-up에서 app ffmpeg/ffprobe env contract를 정리했다.
  packaged 앱 전용 설치 경로는 `userData/bin/ffmpeg`, `userData/bin/ffprobe`이고,
  런타임 표준 env는 `FFMPEG_BIN`, `FFPROBE_BIN`이다.
  `clipper_electron` `d461dfd`는 NestJS/Python runtime에 이 경로를 주입하고 NestJS
  preflight에서 `ensureFfmpeg()`를 보장한다. `clipper_nestjs` `b4739c6`은 TTS
  ffprobe, source ingest, NestJS ffmpeg executor가 표준 env만 보게 했고,
  `clipper_python` `c2e54c7`은 Python plugin 직접 lookup을 표준 env로 통일했다.
- 2026-06-18 URL clip generation QA에서 사용자가 본 500은 같은 running endpoint
  재호출 시 201 Created로 성공했고, `shortform_project_1781746600126`에 clips 8개가
  저장됐다. 첫 500 stack은 앱 데이터 로그에 없었다. `clipper_nestjs` `095e61d`에서
  `generateClips()`의 provider/network plain `Error`를 `ServiceUnavailableException`으로
  매핑해 외부 provider transient failure가 generic 500으로 보이지 않게 했다.
- 2026-06-18 follow-up `clipper_python` `d743cdd`에서 마지막 TTS tail이 잘리는 문제를
  고쳤다. 원인은 auto zoom/pan frame count floor로 segment video가 payload duration보다
  짧아질 수 있는 점, AAC concat demuxer `-c copy`의 timestamp/tail 손실 가능성, 최종 mux
  `-shortest`였다. frame count는 `ceil(duration * 30)`, TTS/BGM concat은 filter concat
  re-encode, final mux는 no `-shortest`로 바꿨다.
- 같은 `clipper_python` `d743cdd`에서 세 번째 Template Builder outline subtitle이 실제
  render에서 사라지던 문제를 고쳤다. `subtitleText.box.enabled=false`이고
  `subtitleBox.visible=false`인 no-box caption template을 1px fallback으로 처리하던 것이
  원인이며, 이제 visible `subtitleText` layer height/style을 fallback으로 사용한다.
- 2026-06-18 follow-up `clipper_angular` `184c96f`에서 shortform browser preview의 caption
  outline을 fill text 뒤 pseudo layer로 그린다. 굵은 `-webkit-text-stroke`를 실제 fill
  text에 직접 적용해 흰색 글자가 거의 오렌지색처럼 보이던 문제를 막았다.
- 2026-06-18 follow-up `clipper_angular` `38c41b6`과 `clipper_nestjs` `4d5aa36`에서
  보관함 완료 카드의 `편집`이 붙여넣기 프로젝트를 `/shortform/prompt`로 열던 문제를
  고쳤다. 원본 shortform project는 `source.mode=paste`였지만 render manifest
  `detail.input.mode`가 `editor`로 저장돼 Angular가 prompt fallback을 탔다. 새 manifest는
  `paste`를 그대로 저장하고, 기존 완료 기록은 Angular가 `sourceAssets.metadata.sourceMode`
  fallback으로 `/shortform/paste?project=...`를 선택한다.
- 2026-06-18 follow-up `clipper_angular` `5175a9d`에서 caption outline preview를 다시
  고쳤다. `::before` pseudo layer + `-webkit-text-stroke` 방식은 여전히 윤곽선 색이 흰색
  fill을 덮어 보일 수 있어 제거했고, caption line text 자체의 여러 방향 `text-shadow`로
  outline을 근사한다. shadow는 fill 뒤에 그려져 흰 글자를 덮지 않는다.
- 2026-06-18 follow-up `clipper_angular` `37dea74`에서 Template Builder 자막 공통 스타일
  적용 시 `fontSize * lineHeight`, outline, shadow, box border를 반영한 최소 높이를
  계산해 `subtitleText.height`와 `subtitleText.box.height`를 같이 키운다. 기존 높이가
  더 크면 줄이지 않는다.
- 2026-06-18 follow-up `clipper_python` `5eda200`에서 이미 작게 저장된 템플릿도 최종
  subtitle artifact/render에서 잘리지 않도록 renderer가 저장된 box height와 계산된 최소
  line box height 중 큰 값을 사용한다.
- 2026-06-18 follow-up `clipper_nestjs` `0c78413`과 `clipper_angular` `e850888`에서
  shortform project가 선택 당시 `templateVersionSnapshot`을 저장하고, 편집 재진입 preview와
  render recipe가 최신 Template Builder catalog보다 snapshot preset/runtimeSpec을 우선 사용하도록
  바꿨다. 신규 project는 생성/선택 시점의 최신 catalog preset을 새 snapshot으로 캡처한다.
- 2026-06-18 follow-up `clipper_nestjs` `5c7112b`과 `clipper_angular` `b1b7a34`에서
  snapshot preview와 최신 template thumbnail이 다르게 보일 때 사용자에게 생성 당시 템플릿으로
  preview 중임을 안내하고, 원하면 같은 template id의 최신 catalog preset으로 snapshot을 갱신하는
  `현재 템플릿 적용` action을 추가했다. Template selector 목록 자체는 최신 catalog 상태를 유지한다.
- 2026-06-18 follow-up `clipper_nestjs` `1740bd7`에서 shortform render 준비 중 선택된
  원격 clip media만 output root 아래 `draft/assets/remote`로 materialize한 뒤 Python worker
  payload/manifest에 local source-file로 넘기도록 바꿨다. 선택되지 않은 후보 asset은 다운로드하지
  않는다. 선택 asset 다운로드가 실패하면 remote-url artifact를 넘기지 않고 기존 asset preparer가
  만든 local fallback media를 사용한다. 또한 Python worker job이 failed/cancelled로 끝나면 원본
  `shortform_project_*`의 status/lastError도 failed로 동기화한다.
- 2026-06-18 follow-up `clipper_nestjs` `3165b79`과 `clipper_angular` `e3b6f32`에서
  stale template snapshot 안내 오탐을 고쳤다. 기존에는 snapshot runtimeSpec과 최신 runtimeSpec의
  JSON 차이만으로 안내를 띄워, 템플릿 수정 후 새로 생성한 프로젝트도 안내가 뜰 수 있었다. 이제
  Template Builder preset catalog가 `updatedAt`을 내려주고, Angular는 최신 template `updatedAt`이
  project snapshot `capturedAt`보다 늦고 runtimeSpec도 다를 때만 안내를 띄운다.

검증 결과:

```text
clipper_angular:
- npm run build
- ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/shell/projects/projects-history-list.component.spec.ts --include=src/shell/projects/projects.component.spec.ts --include=src/app/app.routes.spec.ts
  11 SUCCESS
- git diff --check
- ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/shortform/pages/shortform-workflow.store.spec.ts
  9 SUCCESS
- ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/shortform/pages/shortform-workflow-page.component.spec.ts --include=src/features/shortform/services/shortform-project.service.spec.ts
  68 SUCCESS
- ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts
  72 SUCCESS
- ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/features/shortform/components/preview/shortform-browser-timeline-preview.component.spec.ts
  18 SUCCESS
- ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include=src/shell/projects/projects.component.spec.ts --include=src/shell/projects/projects-history-list.component.spec.ts
  3 SUCCESS
- npm run build
- git diff --check

clipper_nestjs:
- npm run build
- node --test test/template-builder-shortform-preset-source.test.js
  2 pass
- node --test test/template-builder-shortform-preset-source.test.js test/shortform-project-generation-assets.test.js test/simplified-shortform-render-recipe-provider.test.js
  19 pass
- node --test test/shortform-project-generation-assets.test.js test/shortform-project-api.test.js
  18 pass
- node --test test/shortform-project-generation-assets.test.js test/shortform-project-api.test.js test/simplified-shortform-render-recipe-provider.test.js
  27 pass
- node --test test/shortform-project-api.test.js test/shortform-project-generation-assets.test.js test/shortform-tts-provider.test.js
  19 pass
- node --test test/shortform-tts-provider.test.js test/shortform-project-generation-assets.test.js test/workflow-executor-registry.test.js test/simplified-shortform-local-ffmpeg-render-provider.test.js
  11 pass
- node --test test/shortform-project-api.test.js
  10 pass
- node --test test/template-builder-shortform-preset-source.test.js
  2 pass
- node --test test/template-builder-render-payload.test.js
  13 pass
- node --test test/simplified-shortform-render-recipe-provider.test.js
  2 pass
- node --test test/*.test.js
  120 passed, 24 failed. Remaining failures are existing Template Builder
  official DB configuration failures (`Template Builder official DB is not
  configured`), not the shortform render payload path.
- git diff --check

clipper_electron:
- npm run build
- git diff --check

clipper_python:
- uv run pytest tests/test_template_builder_subtitle_artifacts.py -q
  4 passed
- uv run pytest tests/test_clipper1_video_render_template_styles.py -q
  31 passed
- uv run pytest tests/test_clipper1_video_render_text_artifact_job.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_frame_artifacts.py -q
  9 passed
- uv run pytest tests/test_clipper1_video_render_contract.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_motion.py tests/test_clipper1_video_render_template_styles.py -q
  72 passed
- Actual latest outline payload subtitle artifact:
  image_size=(877, 171), alpha_bbox=(10, 8, 867, 171)
- uv run pytest tests/test_template_builder_video_frame_extraction.py tests/test_clipper1_video_render_contract.py::test_local_render_adapter_uses_standard_ffmpeg_env tests/test_clipper1_video_render_media_looping.py -q
  30 passed
- uv run pytest tests/test_clipper1_video_render_contract.py -q
  6 passed
- uv run pytest tests/test_clipper1_video_render_remote_assets.py::test_render_execute_stages_remote_media_layout_logo_tts_and_bgm -q
- uv run pytest tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_contract.py tests/test_clipper1_video_render_text_artifact_job.py -q
  19 passed
- uv run pytest tests/test_clipper1_video_render_contract.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_remote_assets.py tests/test_clipper1_video_render_motion.py tests/test_clipper1_video_render_uploaded_fonts.py tests/test_clipper1_video_render_text_artifact_job.py tests/test_clipper1_video_render_template_styles.py tests/test_template_builder_text_artifacts.py tests/test_template_builder_subtitle_artifacts.py tests/test_template_builder_frame_artifacts.py tests/test_template_builder_text_preview_artifact_export_script.py -q
  91 passed
- uv run pytest -q
  170 passed, 4 skipped, 2 failed. Remaining failures are the old
  `test_clipper1_video_render_golden_frames.py` and
  `test_clipper2_template_baseline_frames.py` fixture comparisons, which are
  not the current Template Builder shortform path.
- uv run pytest -q --ignore=tests/test_clipper1_video_render_golden_frames.py --ignore=tests/test_clipper2_template_baseline_frames.py
  168 passed, 4 skipped
```

## 2026-06-17 Video Render Logic Status

이번 세션에서 한 일:

- `clipper_python` `LocalRenderAdapter.render()`가 `recipe.output.width/height`를
  최종 canvas로 쓰던 문제를 고쳤다. 최종 mp4는 항상 1080x1920이다.
- `clipper_python` `9396094`에서 adapter 삭제 대신 유지/정렬 방식을 택했다.
  `VideoService.py` 함수 기준으로 실제 Template Builder shortform path에 걸리는
  gap을 좁혔다.
- `clipper_nestjs` shortform render manifest `outputs[0].width/height`도 항상
  1080x1920으로 기록한다.
- Template Builder contract payload에서 image/GIF/video media가 content area에 들어가고
  main title 1/2, subtitle 1/2줄, layout layer와 함께 1080x1920으로 render되는
  Python contract test를 추가했다.
- Template Builder shortform preset/mapper contract bug를 수정했다. 이전 실제 job은
  `shortformTemplateRuntimeSpec`에는 올바른 `content y=456`, title/caption 좌표,
  `#0017c7` layout layer가 있었지만 legacy payload의 `template_settings`가 `{}`이고
  `project.main_title_check`가 `false`라 Python worker가 흰 배경/상단 content로 렌더했다.
  새 shortform render job은 preset defaultParams와 mapper에서 contract/layers/title role을
  보존한다.
- Template Builder `contentArea` geometry를 `template_settings`가 없을 때 fallback으로
  사용하고, 명시적인 `contents_area_y_offset: 0`은 보존한다.
- `mainTitleLine2`만 있는 경우에도 legacy text image overlay와 ASS event 경로가
  렌더된다.
- TTS summary는 silence placeholder가 아니라 실제 `tts_url`이 있는 clip 수만 센다.
- Template Builder text artifact에서 `box.sizing`이 누락된 enabled box는 fixed layer
  box로 정규화해 artifact PNG size와 metadata frame을 계약 레이어 박스에 맞춘다.
- 잘못 들어갔던 구형 `project.sub_title` y-offset 수정과 `clipper2_template_baseline`
  PNG 갱신은 제거했다.

명확히 아닌 것:

- `adlight_python/app/services/VideoService.py` 전체를 그대로 포팅한 상태가 아니다.
- 현재는 기존 `clipper1_video_render/local_render_adapter.py`의 구현을 실제 Clipper2
  Template Builder shortform contract에 맞춰 보정하고 테스트로 고정한 상태다.

VideoService parity checklist 상태:

- `create_video`: adapter `render()`가 output path/thumbnail/progress/result summary를
  담당한다. final canvas는 1080x1920 고정이다.
- `_process_clips`: adapter는 clip별 segment render 후 concat한다. image/GIF/video
  media type tests가 있다.
- `_create_video_from_image`: image cover, auto zoom/pan, explicit none effect tests가
  있다.
- `_convert_gif_to_video` / `_process_video_clip`: GIF/video는 `-stream_loop -1`,
  blur background, centered contain foreground 경로를 테스트한다.
- `_create_final_video`: segment concat, final layout overlay, x264 final options,
  TTS/BGM mux 경로를 테스트한다.
- `_generate_subtitle_images`: Template Builder subtitle artifact와 legacy subtitle text
  image overlay tests가 있다.
- `_download_tts` / `_concatenate_audios`: adapter는 remote/local audio resolve,
  clip silence fill, concat, BGM loop/volume, mix summary를 테스트한다.
- `_generate_thumbnail`: render 결과 thumbnail path를 만들며 execute contract/remote
  render tests가 검증한다.

남은 renderer 작업:

- 실제 packaged app에서 Template Builder custom preset으로 end-to-end render QA:
  `숏폼 생성하기` -> `/projects` running -> Python worker render -> completed project 재열기.
- Angular current branch의 Node preview snapshot export tests는 현재 7 passed, 2 failed
  상태다. 실패는 Python 변경 없이도 재현되는 Angular preview fixture 기대값 차이
  (`top: 109.2` vs `0`, style-heavy background transparent)라 별도 Angular 작업으로 본다.
- 구형 21개 Clipper1 golden/baseline fixture는 현 shortform path가 아니므로 이번 parity
  작업에서 갱신하지 않는다.

## Project-First / Plugin / Queue Status

진행된 것:

- shortform render submit path는 기존 `/jobs` queue로 들어간다. 2026-06-17
  `6e98b15` 이후 heavy render preparation 전에 job을 reserve하므로 큐가 즉시 보인다.
- render 요청 시점에 synthetic completed project를 만드는 경로는 제거했다.
- 완료 project 기록은 job completion 이후 `ProjectsService.recordCompletedJob()`에서만
  생성되는 방향으로 맞췄다.
- Angular `숏폼 생성하기`는 render API 호출 후 작업 보관함 페이지
  `/projects?plugin=clipper1_video_render&job=...`로 이동한다.
- Angular `/projects` completed shortform card는 action overlay를 제공한다.
  2026-06-17 `0c4fb15` 이후 action overlay는 클릭 선택이 아니라 hover/focus-within으로
  표시된다. `편집`은 `ShortformWorkflowPageComponent`를 `?project=`로 복원 진입시키고,
  `재생`은 completed output video overlay를 연다. 오른쪽 inline detail panel은
  completed card grid 경로에서 제거했다.
- job result와 completed project result에 `render_manifest`/`manifest`가 남도록 했다.

아직 남은 큰 작업:

- Shortform template snapshot/version snapshot:
  shortform project는 현재 `renderSettings.templateId`만 저장하므로, Template Builder
  최신본이 수정되면 예전 project의 편집 preview가 output 영상과 달라질 수 있다.
  원본 project에 template snapshot/version snapshot을 저장하고 편집 화면이 이를 우선
  사용하게 한다.
- Project-first 데이터 모델 정리:
  draft shortform, promoted project, render job, completed artifact 사이 ownership를
  명확히 분리한다. 현재 `shortform_project_*`는 편집 원본, `shortform_*`는
  promoted/completed render project, `shortform_render_*`는 job, `promotedProjectId`는
  원본에서 promoted project로 가는 연결고리다.
- Plugin contract 정리:
  `clipper1_video_render` input/output schema, artifact path contract, env/runtime contract,
  cancellation/progress/error contract를 문서화하고 코드에 고정한다.
- Queue UI/상태 정리:
  queued/running/completed/failed/cancelled 전환, retry/cancel, completed job list 이동,
  project detail 재열기 동작을 실제 앱에서 QA한다.
- 작업 보관함 non-shortform project detail flow:
  shortform 완료 card는 `편집`/`재생` action overlay를 갖는다. non-shortform 완료 card에 직접
  `재생`을 붙였던 `clipper_angular` `60a0b83`은 `a7a1211`로 되돌렸다. `92a54b9` 이후
  non-shortform 완료 card는 `결과 보기`로 `/projects/:projectId` 상세 라우트에 진입하고, 상세 라우트는
  기존 dialog/dance result detail 컴포넌트를 그대로 사용한다.
- 작업 보관함 completed card UI redesign:
  thumbnail을 9:16 기본 비율로 바꾸고, shortform은 render thumbnail을 사용한다.
  non-shortform thumbnail 정책과 card에 표시할 metadata/title/status/action 배치를 다시
  설계한다.
- Python worker lifecycle 정리:
  devapp/packaged에서 worker start/stop, port/baseUrl, job event delivery,
  output_root 접근 권한을 확인한다.
- Render artifact persistence 정리:
  mp4/thumbnail/tts/media asset 경로가 local app storage 기준으로 재열기 가능한지 확인한다.
- 2026-06-18 audit: 기존 `VideoRenderJobsService`는 shortform render path에서는 더 이상
  사용되지 않지만, generic project output render API
  `/projects/:projectId/outputs/:outputId/render-jobs`와 Angular
  `ProjectHistoryService.startVideoRenderJob()`에 아직 연결돼 있어 즉시 삭제 대상이 아니다.
  `clipper_nestjs` `audit/old-render-path-cleanup`에서 shortform render가 old
  `render-jobs/render-jobs.json` store를 만들지 않는 회귀 테스트를 추가했다. 다음 단계에서
  이 generic output render API를 `/jobs`로 통합할지, non-shortform detail flow와 함께
  유지할지 결정해야 한다.
- 2026-06-18 추가 audit에서 generic project output render API가 `workflow.shortform` manifest를
  받으면 old `VideoRenderJobsService`로 넘기지 않고 400을 반환하도록 막았다. Shortform 재렌더는
  `/projects/shortform/projects/:projectId/render-jobs` -> `/jobs` queue path만 사용해야 한다.
- 2026-06-18 Angular audit에서 generic output render 버튼을 담고 있던
  `ProjectsDetailPanelComponent`는 현재 `projects.component.html`에서 더 이상 렌더되지 않는
  죽은 UI로 확인되어 삭제했다. `ProjectHistoryService.*VideoRenderJob*` 메서드와 NestJS generic
  output render API는 아직 남아 있으며, 다음 cleanup은 `ProjectsComponent` 내부의 detail/render
  context dead state와 service 메서드 제거 가능성을 별도로 봐야 한다.
- 2026-06-18 추가 Angular cleanup `clipper_angular` `36ca7fc`에서 `ProjectsComponent`의
  generic video render provider/job polling, start/cancel action, selected output state를 제거했다.
  `ProjectHistoryService`의 unused `listVideoRenderProviders()`, `startVideoRenderJob()`,
  `listVideoRenderJobs()`, `cancelVideoRenderJob()` 클라이언트 메서드와 관련 타입도 제거했다.
  이제 Angular `src/test`에는 old `VideoRenderJobsService` API caller가 남아 있지 않다.
- 2026-06-18 추가 NestJS cleanup `clipper_nestjs` `a5dbe9a`에서 generic project output render API를
  제거했다.
  - 제거된 route: `GET /projects/:projectId/outputs/:outputId/render-providers`,
    `POST /projects/:projectId/outputs/:outputId/render-jobs`,
    `GET /projects/:projectId/render-jobs`,
    `GET /projects/:projectId/render-jobs/:renderJobId`,
    `DELETE /projects/:projectId/render-jobs/:renderJobId`
  - `ProjectsService`의 matching public methods와 old render job result를 Clipper Studio manifest에
    반영하던 helper도 제거했다.
  - `clipper_nestjs` `7f0320d`에서 persisted `VideoRenderJobsService`,
    `VideoRenderJobRepository`, `video-render-job.dto`도 제거했다.
  - `VideoRenderProviderRegistry`와 provider classes는 아직 남아 있다. 이 registry는
    `TemplateBuilderSampleRenderService`가 sample render provider resolution에 사용 중이고,
    simplified/template-builder render provider tests도 직접 검증하므로 이번 cleanup 대상에서 제외했다.
- 2026-06-18 `clipper_nestjs` `4dfe604`에서 `VideoRenderProviderRegistry`의 남은 역할을
  "persisted render jobs"가 아니라 "render recipe provider resolution"으로 고정했다.
  - 새 `test/render-provider-registry-boundary.test.js`는 registry가 project-manifest barrel에 남고,
    removed `VideoRenderJobsService`는 export되지 않으며, registry error wording이
    `render recipe provider` 기준임을 검증한다.
  - `TemplateBuilderSampleRenderService`의 sample render provider resolution 경로는 유지한다.
- completed job이 "완료된 작업" 목록으로 이동하고, 다시 열었을 때 video/thumbnail/manifest가
  유효한지 end-to-end 검증한다.

2026-06-17 shortform 제작 페이지 리팩토링은 app repo에 커밋됐다. 새 Markdown 작업
계획 문서는 코드 repo에서 제거하고 `.codex/records/worklog/2026/06/`로 옮겼다.
앞으로 새 Markdown 문서는 `.codex` repo 안에만 만든다.

2026-06-17 NestJS paste plugin copy 수정도 커밋됐다. `shortform_paste` 설명에서
`현재 준비 중입니다.`를 제거했고, `test/plugin-catalog.test.js` 회귀 테스트를
추가했다.

URL로 숏폼 제작 백엔드 1차 이식도 완료됐다. 이전 NestJS는 URL project creation만
저장하고 clip generation 때 URL 문자열을 그대로 LLM prompt로 넘겼다. 이제
`ShortformUrlContentExtractor` provider가 URL 본문/이미지를 추출하고,
`generateClips()`가 URL mode일 때 parsed content를 prompt로 쓰며 원본 이미지를 clip
media로 우선 배정한다. 지원 대상은 Naver Blog, Tistory, Brunch, generic/news HTML
fallback이다. 다음 우선순위는 실제 앱/실 URL QA와 selector edge case 보강이다.

검증 결과:

```text
clipper_angular:
- ./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/**/*.spec.ts'
  TOTAL: 137 SUCCESS
- npm run build
- git diff --check

clipper_nestjs:
- npm run build
- node test/plugin-catalog.test.js
- node test/shortform-project-generation-assets.test.js
- node test/shortform-url-content-extractor.test.js
- node test/shortform-project-api.test.js
- git diff --check
```

2026-06-16 shortform browser timeline preview engine 1차 구현과 packaged app
hardening은 app repo에 커밋/푸시됐다. 다음 세션은 먼저 pull/status로 push 상태와
로컬 dirty 여부를 확인한다.

문서 repo는 이 handoff update 커밋이 shortform browser preview hardening,
packaged app font/BGM asset loading fix, 검증 결과를 기록한다.

완료된 것:

- 기존 full Template Builder 보존용 archive branch 생성 완료.
- `ShortformProject.mainTitle1/mainTitle2` 저장/응답 반영 완료.
- shortform 제작 페이지의 `레이아웃` 섹션을 `템플릿` 섹션으로 변경.
- ratio 버튼과 title visibility checkbox 제거.
- 템플릿 picker를 horizontal thumbnail strip + 더보기 modal 구조로 변경.
- 템플릿 thumbnail은 임시 PNG 파일 asset으로 제공하며 9:16 shortform card
  비율로 생성.
- 오른쪽 템플릿 섹션이 패널 밖으로 넓어지던 레이아웃 버그 수정.
- 새 shortform payload/render path에서는 `sub_title`, `bottom_title`,
  `logo`를 사용하지 않고 `main_title1`, `main_title2`, `caption`만 사용.
- 임시 simplified shortform template preset/catalog/render baseline 추가.
- Template Builder simplification plan Task 1 완료:
  backend `ShortformTemplateRuntimeSpec` contract 추가.
- Task 2 완료: backend Template Builder shortform mode 추가.
  shortform family는 `1:1` 또는 `4:3` 단일 ratio만 만들고, legacy roles는
  runtime spec에 노출하지 않는다.
- Task 3 완료: Builder-created shortform templates를
  `template_builder.custom` preset source로 노출.
  preset은 `clip_media`, `main_title1`, `main_title2`, `caption`, `bgm`만
  사용하고 Builder card thumbnail을 preview image로 쓴다.
- Task 4 완료: Angular shortform catalog가 `template_builder.custom`을 먼저
  로드하고, 없을 때만 `shortform.simplified`로 fallback한다.
  `ShortformTemplateCatalogItem.runtimeSpec` 매핑과 shallow validation도
  추가했다.
- Task 5 완료: Angular Template Builder active UI를 shortform 단일 ratio
  flow로 단순화했다. create/clone은 `workflowKind: 'shortform'`를 보내고,
  editor는 content area/layout/main title 1/main title 2/caption만 보여준다.
- Task 6 완료: Template Builder card thumbnail capture를 9:16 shortform card
  이미지로 고정했다. fallback canvas는 360x640이고, layout/content/main
  title 1/main title 2/caption만 그린다.
- Task 7 focused verification 완료:
  NestJS build/focused Node tests, Angular focused Karma tests, Angular build,
  양쪽 `git diff --check`가 통과했다.
- Follow-up blocker fix 완료: Builder `template-builder.v1` shortform preset이
  backend shortform recipe path를 타고 shortform render provider로 resolve되도록
  수정했다.
- Follow-up UI fix 완료: active `/templates` 페이지가 backend legacy/system
  Template Builder family를 그대로 보여주지 않도록 `workflowKind:
  shortform` family만 표시한다. legacy-only 상태에서는 shortform 전용 empty
  state와 `새 템플릿` CTA를 보여준다. 새 템플릿 모달의 `1:1` / `4:3`
  선택은 `aria-pressed`와 active styling으로 즉시 구분된다. Shortform editor의
  사용자 표시 role은 main title 1/main title 2/caption만 남는다.
- Follow-up thumbnail/capture hardening 완료: `/templates`는
  `window.clipperBridge.capture`가 없는 localhost browser/dev-server 환경에서
  새 템플릿 생성과 편집 시작/저장을 막는다. 편집 도중 저장만 막히지 않도록
  생성/편집 진입 버튼도 disabled 된다. 생성/편집 시 카드 썸네일은 fallback
  canvas가 아니라 왼쪽 preview frame `.template-workspace__preview-cell
  .phone-canvas`를 캡쳐한다. Electron packaged app이 hidden/CDP 상태라
  `requestAnimationFrame`이 멈춰도 80ms paint fallback으로 썸네일 캡쳐/업로드가
  진행된다.
- 2026-06-16 browser timeline preview engine 1차 구현 완료:
  Angular production page가 정적 composition box 대신
  `ShortformBrowserTimelinePreviewComponent`를 사용한다. 브라우저에서 clips,
  narration/TTS, BGM, media, main title 1/2, caption을 timeline으로 조합해
  재생/정지/seek한다. 실제 FFmpeg preview 파일은 만들지 않는다.
- 2026-06-16 Template Builder template parity 수정 완료:
  shortform 제작 페이지는 `template_builder.custom`만 로드하고
  `shortform.simplified` fallback을 더 이상 호출하지 않는다. 빌더 목록이 비면
  제작 페이지 템플릿 목록도 비어 있고, draft/new template도 보존한다.
  thumbnail/sample render가 아직 없는 새 draft는 1:1/4:3 fallback card로 표시한다.
- 2026-06-16 runtime/preview spec 수정 완료:
  backend `ShortformTemplateRuntimeSpec.canvas`는 1080x1920 9:16이고,
  원래 Builder canvas는 `templateCanvas`, portrait 안 배치 영역은
  `templateFrame`으로 보존한다. region 좌표와 font/padding/border/outline/shadow
  값은 9:16 canvas 기준으로 변환된다. Angular preview도 해당 spec을 기준으로
  위치/폰트/색상/테두리/외곽선/그림자를 반영한다.
- 2026-06-16 preview media 품질 수정 완료:
  preview와 clip thumbnail 후보 모두 이미지/비디오 `contentUrl`을 먼저 쓰고,
  실패한 URL은 `thumbnailUrl`로 fallback한다.
- 2026-06-16 packaged app preview hardening 완료:
  preview font URL은 app data absolute path가 아니라
  `template-assets/...` relative URI를 사용한다. `/v1/template-builder/assets/file`
  endpoint는 font content type과 missing local asset 404를 처리한다.
  Electron renderer의 `Origin: file://` font request를 local API CORS에서 허용한다.
  이 변경으로 preview font가 packaged app에서 적용된다.
- 2026-06-16 browser preview playback/style polish 완료:
  seek bar는 `현재 시간 / 총 시간` 표시로 바뀌었고 total duration은 TTS duration
  pre-measurement로 고정된다. clip/project/TTS update 중 preview는 멈추고 0초로
  reset된다. caption은 줄 단위 box로 그리며 template line gap을 반영한다.
  BGM `선택 안 함`, BGM/voice sample과 preview playback 상호 배제, TTS regeneration
  spinner/status, clip order 보존, clip duration label 갱신을 반영했다.
- 2026-06-16 debugging 문서 추가 완료:
  `records/worklog/2026/06/shortform-browser-preview-debugging-2026-06-16.md`에 symptoms,
  root causes, debugging evidence, solution, verification, operational notes를 정리했다.

중요한 현재 판단:

- 정적 composition box는 browser timeline preview component로 교체됐다.
- 현재 preview는 1차 browser engine이다. render-engine pixel parity가 아니라
  편집 중 interactive preview가 목표다.
- Template Builder 단순화와 Builder-created template catalog 연결은 진행됐다.
- 최종 cross-repo review에서 blocking gap이 발견됐고 수정했다:
  Angular는 `template_builder.custom` Builder preset을 먼저 노출하고,
  NestJS preset은 `shortformTemplateModel: 'template-builder.v1'`를 내보내지만,
  backend `RenderRecipeProvider`와 shortform render providers가 `simplified.v1`만
  처리하던 문제였다. `0ce6b27`에서 공통 supported shortform template model
  판정으로 `simplified.v1` / `template-builder.v1`를 같이 처리한다.
- 이제 다음 우선순위는 실제 앱에서 Template Builder -> shortform production page
  왕복 QA와 남은 preview visual parity polish다.
- packaged app preview font 500의 최종 원인은 CORS였다. Origin 없이 호출하면 200,
  `Origin: file://`로 호출하면 500이었고, 새 bundle에서는
  `Access-Control-Allow-Origin: file://`와 함께 font file이 200으로 내려온다.
- BGM은 명시적으로 `선택 안 함`을 선택할 수 있어야 하고, 이 상태에서는 preview와
  최종 render 모두 BGM을 생략한다.
- Template Builder 페이지는 packaged Electron 앱 기준으로 생성/썸네일 저장까지
  확인됐다. localhost browser에서는 썸네일 캡쳐 bridge가 없으므로 생성/편집이
  제한되는 것이 의도된 동작이다.

다음 실행:

- `TEMPLATE_BUILDER_SIMPLIFICATION_IMPLEMENTATION_PLAN_2026-06-15.md`는
  완료된 Builder simplification 기록으로 본다.
- 다음 코드는 browser timeline preview hardening 이후 남은 앱 동작 QA와 visual
  parity 보정이다.
- 먼저 `clipper_angular`, `clipper_nestjs`의 branch/status를 확인한다.
- packaged/local 환경에서 Template Builder 새 템플릿 생성 -> 편집/저장 ->
  shortform 제작 페이지 템플릿 목록 반영 -> 클립 생성 -> preview 재생까지 확인한다.
- 문제가 보이면 browser preview component, runtime spec projection, local asset
  resolver를 우선 보정한다.
- 시작 전에 `clipper_angular`가 `6143003`, `clipper_nestjs`가 `bbc00f6` 이상인지
  확인한다.
- Project-first / Plugin / Queue cleanup은 아직 시작하지 않는다.

다음 세션 시작 프롬프트:

```text
Using Superpowers.

먼저 .codex/README.md, .codex/handoff/NEXT.md,
.codex/design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md,
.codex/design/TEMPLATE_BUILDER_SIMPLIFICATION_IMPLEMENTATION_PLAN_2026-06-15.md,
.codex/records/sessions/2026/06/16.md를 읽고 현재 상태 파악해.

Project-first / Plugin / Queue 정리는 아직 시작하지 마.
최근 커밋된 shortform browser timeline preview hardening을 이어서
검증/폴리시해줘. 우선 git status와 최신 커밋을 확인하고, 가능하면 로컬 앱에서
Template Builder 새 템플릿 생성/편집/저장 -> shortform 제작 페이지 템플릿 목록
반영 -> 클립 생성 -> 9:16 browser preview 재생/seek/스타일 반영/원본 이미지 품질을
확인해. 발견한 문제는 작게 수정하고 테스트/빌드까지 돌려줘.
```

## 2026-06-12 Clipper2 Modal Inventory

Clipper2 앱 전체의 모달/오버레이 사용처를 조사했고, 현재는 추가 교체를 진행하지 않기로 했다. 나중에 공통 모달로 교체할 때는 아래 문서를 먼저 본다.

- [../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md](../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md)

현재 판단:

- 이미 생성된 숏폼 클립 재생성 확인은 shared confirmation modal 사용 대상으로 남긴다.
- 바로 교체하기 좋은 후보는 Template Builder의 native `window.confirm` dirty-cancel prompt와 템플릿 삭제 확인이다.
- Dashboard admission dialog는 detail rows/badge가 있어 shared modal 확장 후 검토한다.
- ffmpeg/model consent, 숏폼 생성 진행, 템플릿 샘플 렌더, 프로젝트/이미지 preview, 입력 form overlays는 단순 confirmation modal로 교체하지 않는다.

## 2026-06-12 Template Simplification Decision

숏폼 제작 페이지의 템플릿/레이아웃 작업에 들어가기 전, Template Builder와 shortform template 사용 방향이 크게 바뀌었다.

먼저 읽을 문서:

- [../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)

확정 기준:

- 기존 full Template Builder 구현은 단순화 작업 전 archive branch로 보존한다.
- active branch에서는 기존 Template Builder를 simplified model로 직접 교체한다. product-visible full Template Builder route를 병행 유지하지 않는다.
- 새 템플릿은 `main_title1`, `main_title2`, `caption`만 사용한다.
- `sub_title`, `bottom_title`, `logo`는 새 템플릿/숏폼 제작 flow에서 제거한다.
- 메인타이틀은 두 줄 구조를 유지한다.
- 템플릿 하나는 ratio 하나만 가진다. 허용 ratio는 `1:1`, `4:3`이다.
- 기존 official legacy 템플릿은 새 숏폼 제작 템플릿 목록에서 사용하지 않는다.
- 숏폼 제작 페이지의 `레이아웃` 섹션은 `템플릿`으로 바꾸고, ratio 선택과 타이틀 체크박스는 제거한다.
- 선택한 템플릿의 ratio가 preview와 최종 render payload/recipe를 결정한다.
- 새 preview는 legacy still preview가 아니라 timeline preview여야 한다. 재생/seek, TTS, BGM, media, main title lines, caption overlay가 필요하다.
- 브라우저 preview만으로 FFmpeg/Python 최종 렌더와 pixel-identical 보장은 불가능하다. 빠른 interactive preview와 render-engine confirmation preview를 분리하는 hybrid 방향을 기준으로 한다.

## 2026-06-11 Latest Product Terminology Decision

2026-06-10의 `workspace -> project` 정정 이후, 2026-06-11에 사용자-facing 제품 용어 기준을 다시 확정했다.

먼저 읽을 문서:

- [../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md)
- [../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md)

확정 기준:

- 유저가 알아야 하는 핵심 개념은 `플러그인`과 `프로젝트` 두 개다.
- 플러그인은 스토어에 보이는 설치/실행 단위다.
- `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 독립된 사용자 플러그인이다. 하나의 shortform 플러그인 안의 입력 모드로 취급하지 않는다.
- 프로젝트는 플러그인을 열어 사용자가 만들기 시작한 작업물이다.
- 큐에 들어가는 사용자 단위도 프로젝트이고, 완료 후 보관함/프로젝트 페이지에 남는 단위도 프로젝트다.
- `workflow`, `job`, `pipeline`, `runtime`, `worker`는 유저에게 노출하지 않는다. 기존 코드와 기술 문서에서 현재 구현을 설명할 때만 쓴다.
- `Plugin catalog`는 개발자 입장에서 플러그인 목록의 원본 데이터/registry를 뜻한다. 사용자 플러그인 목록과 숨김 runtime worker 목록을 분리해야 한다.
- `clipper1_video_render`는 유저가 직접 여는 플러그인이 아니라 숏폼 플러그인들이 의존하는 hidden `RuntimeWorker`다.
- `task`라는 단어는 신규 제품/문서 용어로 쓰지 않는다. 내부 실행 기록은 `ProjectRun`, worker 원본 진행은 `RuntimeProgress`, 사용자 표시 진행은 `ProjectProgress`/`ProgressStep`으로 구분한다.
- 하이라이트 분석 진행 단계는 유저에게 자세히 보여줄 수 있다. 예: `문장 위치를 영상과 맞추고 있습니다`.
- 숏폼/ffmpeg 렌더 세부 단계는 유저에게 그대로 보여주지 않는다. `영상 생성 중`, `영상 생성 완료`, `영상 생성 실패`처럼 단순화한다.
- 목표 구조는 `/jobs` 중심이 아니라 Project-first다: `Project 생성 -> ProjectRun 생성 -> 큐 대기/실행 -> 같은 Project 상태/결과 갱신`.
- 기존 `/jobs`, `VideoRenderJob`, Python runtime `/jobs`는 당장 삭제하지 않고 compatibility/internal 실행 계층으로 다룬다.
- Project-first 구현 계획은 Project-first facade를 추가하는 방식이다. 전역 `WorkflowExecutor` rename이나 `/jobs` 삭제는 첫 구현 범위가 아니다.
- 단, Project-first / Plugin / Queue 모델 변경은 아직 시작하지 않았다. 현재 진행 순서는 먼저 shortform legacy UI/pre-render parity를 끝내고, 그 다음에 Project-first / Plugin / Queue 정리를 시작하는 것이다.

2026-06-10 기준 주요 repo 확인:

```text
.codex:           clipper1-input-workflow-docs @ 77dcb9c docs(shortform): add phase 3 session handoff
clipper_angular:  work/clipper1-input-workflow-split @ 993efb2 refactor(shortform): use project terminology
clipper_nestjs:   work/clipper1-input-workflow-split @ 8ac76d5 refactor(shortform): rename workspace state to project
clipper_python:   main @ 535131c Render sample images as cover
clipper_electron: main @ f701677 Revert "Update electron builder"
```

2026-06-11 `.codex` 문서 작업 시작 시 기존 `implementation/*` 삭제 상태가 이미 있었다. 이 삭제들은 이번 용어 문서 작업에서 만든 변경이 아니므로 임의 복구하지 않는다.

2026-06-11 후속 shortform legacy parity 구현 이후 로컬 확인 기준:

```text
clipper_angular:  work/clipper1-input-workflow-split @ 8d9d0a5 Fix shortform legacy font sizing
clipper_nestjs:   work/clipper1-input-workflow-split @ 06e3123 Implement shortform clip generation providers
.codex:           clipper1-input-workflow-docs @ 3594f97 Merge branch 'project-first-plugin-queue-docs' into clipper1-input-workflow-docs
```

`clipper_angular`와 `clipper_nestjs`는 이 확인 시점에 working tree가 clean이고 tracking branch 대비 ahead 표시가 없었다. `.codex`는 이 문서 갱신 전까지 clean이었다.

## Current Execution Order

현재 합의된 작업 순서:

1. 숏폼 제작 레거시 UI/pre-render parity 먼저 완료.
   - 기준: `work/clipper1-input-workflow-split`
   - 유지: 세 shortform 플러그인 분리, `workspace -> project` 정정, 현재 NestJS shortform API
   - 목표: `adlight_angular` 레거시 UI/스타일/영상 생성 전 동작과 동일하게 맞추기
   - 금지: 큐/프로젝트/잡 모델 대수술, render/queue 연결, `/projects` navigation
2. 그 다음 Project-first / Plugin / Queue / terminology 정리.
   - 큐에 들어가는 유저 단위를 Project로 정리
   - `/projects`, `/jobs`, `VideoRenderJob`, plugin catalog, ProjectRun, ProjectProgress 정리
   - Angular Project card와 archive/queue 표시 모델 정리

2번은 아직 구현하지 않았다. 현재 작성된 Project-first 문서는 다음 단계 계획서이며 완료 기록이 아니다.

## 2026-06-11 Shortform Legacy Port State

이번 세션에서 완료/반영된 것:

- `.worktrees` 임시 작업 공간은 필요한 변경 반영 후 제거했다.
- `clipper_nestjs/.clipper_data/`는 로컬 NestJS runtime data로 확인했고 gitignore에 추가했다. packaged app runtime data는 macOS 기준 `/Users/jina/Library/Application Support/Clipper2` 아래에 저장되는 것이 기준이다.
- `shortform_url`, `shortform_paste`, `shortform_prompt`는 계속 별도 user-visible plugin이다.
- Shortform editor는 Clipper2 shell 안에서 열리며, 왼쪽 Clipper2 sidebar가 유지된다.
- Plugin Store는 카드 클릭 후 오른쪽 detail panel에서 플러그인을 여는 기존 Clipper2 동작으로 복구했다.
- Legacy Clipper1 shortform UI/assets/styles를 Clipper2 shortform editor에 가져왔다.
- Legacy reset/common/edit CSS가 Store/Dashboard/Projects/Template Builder에 영향을 주지 않도록 shortform editor scope로 분리했다.
- Legacy `.actions` CSS와 Store detail action 영역 충돌을 수정했다.
- Clip drag/drop, subtitle drag/drop, subtitle hover action 잔상 개선, clip drag 중 scrollbar 생김 방지를 반영했다.
- Shortform clip-generation modal은 NestJS WebSocket event로 갱신한다. Clipper2 pre-render clip generation은 SSE를 쓰지 않는다.
- NestJS shortform clip generation은 normal path에서 고정 dummy data를 쓰지 않고 configured LLM script provider, Naver Clova TTS, Naver image search를 사용한다.
- `숏폼 생성하기`는 아직 Phase 1 boundary 그대로다. legacy video-create payload를 console log만 하고 render/queue/navigation은 호출하지 않는다.
- Shortform left panel font-size 깨짐은 scoped px CSS variables로 수정했다. legacy global `html { font-size: 62.5%; }` reset은 재도입하지 않았다.

검증 완료:

- Angular focused tests passed.
- Angular build passed.
- NestJS build passed.
- NestJS shortform/WebSocket event tests passed.
- Browser computed style check: shortform left panel tab `16px`, input `13px`, button `16px`, root `html` `16px`.

알려진 gap:

- Full Angular suite에는 기존 Template Builder snapshot 계열 실패가 남아 있었다. `layoutImage` undefined 관련으로, 이번 shortform parity 작업 범위에서는 수정하지 않았다.

다음에 우선 볼 것:

- 실제 브라우저/Electron에서 Plugin Store -> shortform plugin 선택 -> detail panel -> 열기 플로우를 세 플러그인 모두 확인한다.
- URL/prompt/paste 입력, clip-generation modal stage progression, generated clip card, thumbnail fallback, TTS/BGM controls, title/logo/style controls, preview panel을 legacy `adlight_angular` 기준으로 비교한다.
- 모달 첫 단계는 `텍스트 분석`부터 켜져야 한다. 이후 단계는 backend WebSocket event로 진행되어야 한다.
- `숏폼 생성하기`는 계속 log-only인지 확인한다. render/video/queue request와 `/projects` navigation이 있으면 Phase 1 scope violation이다.
- local/devapp/packaged mode별 LLM/Naver Clova TTS/Naver image env 로딩을 정리하고, 누락 시 앱에서 이해 가능한 에러를 보여주도록 개선한다.
- packaged app에서 runtime data path, bundled env, WebSocket delivery, provider availability를 별도로 검증한다.
- UI/pre-render parity가 사용자에게 승인된 뒤에만 Project-first / Plugin / Queue 정리를 시작한다. 실제 video generation과 queue/archive 연동은 그 다음 단계로 다룬다.

## 먼저 읽기

1. [../README.md](../README.md)
2. [../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md)
3. [../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md](../design/PLUGIN_PROJECT_QUEUE_PROJECT_FIRST_IMPLEMENTATION_PLAN_2026-06-11.md)
4. [../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md](../design/TEMPLATE_SIMPLIFICATION_AND_SHORTFORM_PREVIEW_2026-06-12.md)
5. [../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md](../design/CLIPPER2_MODAL_USAGE_INVENTORY_2026-06-12.md)
6. [../README.ARCHITECTURE.md](../README.ARCHITECTURE.md)
7. [../README.RUNTIME.md](../README.RUNTIME.md)
8. [../README.OPERATIONS.md](../README.OPERATIONS.md)
9. [../operations/env-runtime/README.md](../operations/env-runtime/README.md)
10. [../operations/windows-packaging/README.md](../operations/windows-packaging/README.md)
11. [../features/template-builder/README.md](../features/template-builder/README.md)
12. [../features/dance-highlight/README.md](../features/dance-highlight/README.md)
13. [../features/clipper-studio/README.md](../features/clipper-studio/README.md)
14. [../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port.md](../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port.md)
15. [../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port-plan.md](../features/clipper-studio/records/2026/06/11-shortform-legacy-parity-port-plan.md)
16. [../design/TEAM_ARCHITECTURE_OVERVIEW.md](../design/TEAM_ARCHITECTURE_OVERVIEW.md)
17. [../design/TEAM_DEVELOPMENT_GUIDE.md](../design/TEAM_DEVELOPMENT_GUIDE.md)
18. [../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](../design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)
19. [../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](../design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)
20. [../design/CLIPPER2_INFRA_EASY_GUIDE.md](../design/CLIPPER2_INFRA_EASY_GUIDE.md)
21. [../design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md](../design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md)
22. [../design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md](../design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md)
23. [../records/sessions/2026/06/12.md](../records/sessions/2026/06/12.md)
24. [../records/sessions/2026/06/11.md](../records/sessions/2026/06/11.md)
25. [../records/sessions/2026/06/08.md](../records/sessions/2026/06/08.md)
26. [../records/sessions/2026/06/05.md](../records/sessions/2026/06/05.md)
27. [../records/sessions/2026/06/02.md](../records/sessions/2026/06/02.md)
28. [../records/sessions/2026/06/04.md](../records/sessions/2026/06/04.md)
29. [../records/sessions/2026/05/29.md](../records/sessions/2026/05/29.md)
30. [../records/sessions/2026/05/27.md](../records/sessions/2026/05/27.md)

## Historical Repo Heads

최신 2026-06-10 repo 기준은 위 `2026-06-11 Latest Product Terminology Decision` 섹션을 우선한다. 아래 내용은 과거 세션 기록이다.

2026-06-11 로컬 세션에서 직접 재확인한 기준:

```text
clipper_angular: work/clipper1-input-workflow-split @ 993efb2 refactor(shortform): use project terminology
clipper_nestjs:  work/clipper1-input-workflow-split @ 8ac76d5 refactor(shortform): rename workspace state to project
```

위 두 브랜치가 shortform plugin split과 최근 project terminology 정정을 포함하는 현재 기준이다. `feature/initial-scaffold`로 돌아가면 필요한 변경이 너무 많이 사라진다.

2026-06-04 로컬 세션에서 문서 수정 전에 직접 재확인한 이전 기준:

```text
clipper_angular:  main @ 70d6e58 Improve template sample render flow
clipper_nestjs:   design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch
clipper_python:   main @ 535131c Render sample images as cover
clipper_electron: main @ f701677 Revert "Update electron builder"
clipper2-codex:   workflow-executor-design @ 31e2ce0 docs: document Clipper infra initial setup (문서 수정 전 기준)
```

세션 시작 시 반드시 각 repo에서 `git status -sb`와 `git log -1 --oneline`을 다시 확인한다. `.codex`는 별도 git repo다.

2026-06-02 기준 추가 확인:

```text
clipper_infra:      feature/infra-initial-setup @ 8226879 feat: add Clipper infra initial setup
clipper_web_admin:  main, no commits yet; origin/main gone
clipper_web_api:    main, no commits yet; origin/main gone
clipper_web_client: main, no commits yet; origin/main gone
```

`clipper_web_admin`, `clipper_web_api`, `clipper_web_client` 3개 repo는 생성/클론만 된 상태로 확인됐다. `git log -1 --oneline`은 첫 커밋이 없어 실패하는 것이 정상이다.

2026-06-04 로컬 세션에서도 위 앱 repo/infra repo 상태를 재확인했다. `clipper_web_admin`, `clipper_web_api`, `clipper_web_client`는 여전히 첫 커밋이 없다.

2026-06-05 기준 추가 확인:

```text
clipper_infra:      feature/infra-initial-setup @ 49faa91 feat: split Clipper DB stack into user admin release
clipper_web_admin:  main @ fef456a feat: add minimal web admin scaffold
clipper_web_api:    main @ ec13be7 feat: add minimal web API scaffold
clipper_web_client: main @ 791c935 feat: add minimal web client scaffold
```

위 4개 repo는 commit/push 완료됐다. `.codex`의 이전 문서 commit `e09fa2e docs: record Clipper web scaffold and DB split`은 사용자가 직접 push했다.

2026-06-08 기준 추가 확인:

```text
.codex:             workflow-executor-design, contains m2-stage dev deploy documentation; verify latest with git log -1
clipper_infra:      feature/infra-initial-setup @ decdfa0 docs: document Clipper dev server-side deployment
clipper_web_admin:  origin/main @ e21cabe fix: include Angular zone polyfill
clipper_web_api:    origin/main @ 8386865 feat: verify database connections in health checks
clipper_web_client: origin/main @ e2102db fix: include Angular zone polyfill
```

위 5개 repo의 2026-06-08 변경은 commit/push 완료됐다. 이후 m2-stage 서버
세션 시작 당시에는 `/Users/metabuzz/Desktop/project/clipper2` 아래에
`clipper_infra`만 있었고 그 repo도 최신이 아니었다. 그 서버 세션에서
`clipper_infra` pull과 `clipper_web_client`, `clipper_web_admin`,
`clipper_web_api` sibling clone이 완료됐다.

이후 m2-stage 서버 세션에서 위 배치 작업과 real dev service 배포가 완료됐다.
`clipper_web_client`와 `clipper_web_admin`은 Angular blank screen 원인이던
`zone.js` polyfill 누락을 각각 `e2102db`, `e21cabe`로 수정했고, 두 commit
모두 `origin/main`에 push 완료된 것을 로컬에서 `git fetch` 후 확인했다.
`clipper_web_api`는 이후 `8386865`에서 `/healthz`와 `/v1/health`가 세 DB에
`SELECT 1`을 실행하는 readiness check를 갖게 됐다. 이 API commit은
m2-stage에 재배포됐고 dev API health에서 `userConnected`, `adminConnected`,
`releaseConnected`가 모두 `true`로 확인됐다.

DBeaver 관련 주의:

- 사용자가 로컬 Mac mini에서 `192.168.0.7:55203` DBeaver test connection과
  `nc -vz 192.168.0.7 55203`을 시도했지만 timeout이었다.
- 이는 password 문제가 아니라 로컬 Mac mini에서 m2-db LAN IP/port로 TCP
  도달이 안 되는 문제다.
- m2-stage에서는 DB 접근이 되고, dev API health도 세 DB connected를
  확인했다.
- 이후 사용자는 dohit과 같은 편의성을 위해 Clipper dev DB만 임시로 ipTIME
  WAN port forwarding 방식으로 열기로 결정했다.
- 임시 포워딩 규칙:
  - `clipper_dev_user_db` TCP `55203` -> `192.168.0.7:55203`
  - `clipper_dev_admin_db` TCP `55213` -> `192.168.0.7:55213`
  - `clipper_dev_release_db` TCP `55223` -> `192.168.0.7:55223`
- 로컬 DBeaver/로컬 `clipper_web_api`는 `metabuzz.iptime.org:55203/55213/55223`을 사용한다.
- 사용자가 로컬 Mac mini에서 `nc -vz metabuzz.iptime.org 55203/55213/55223`
  성공을 확인했고, 로컬 DBeaver에서도 3개 DB 모두 연결 완료했다.
- 이 방식은 나중에 VPN/SSH tunnel로 교체한다. stage/prod DB ports는 WAN에 열지 않는다.

2026-06-08 세션 마무리 기준 추가 변경:

```text
clipper_infra:      feature/infra-initial-setup @ f0cb1f1 fix: use per-database password envs
clipper_web_admin:  origin/main @ db26f4d chore: move local admin port to 4701
clipper_web_api:    origin/main @ 0eab250 fix: require per-database passwords
clipper_web_client: origin/main @ 7bdaeae chore: move local web port to 4700
.codex:             workflow-executor-design, verify latest with git log -1
```

- 로컬 개발 포트는 web `4700`, admin `4701`, API `43203`이다.
- API DB env는 URL 3개 방식에서 split 변수 방식으로 바뀌었다.
- app DB password는 DB별 변수로 관리한다:
  - local API: `USER_DATABASE_PASSWORD`, `ADMIN_DATABASE_PASSWORD`, `RELEASE_DATABASE_PASSWORD`
  - m2-stage app env: `CLIPPER_USER_DATABASE_PASSWORD`, `CLIPPER_ADMIN_DATABASE_PASSWORD`, `CLIPPER_RELEASE_DATABASE_PASSWORD`
- `CLIPPER_DATABASE_PASSWORD` 하나짜리 공통 password 변수는 default/example shape에서 제거됐다.
- `clipper_infra/scripts/deploy-dev.sh`는 이제 실행 초기에 `clipper_infra`를 pull하고, infra가 업데이트되면 새 스크립트로 다시 실행한다.
- m2-stage의 실제 `clipper_infra/env/stack.dev.env`는 git-tracked 파일이 아니므로 직접 per-DB password split 변수 형식으로 바꿔야 한다. secret 값은 채팅/로그에 출력하지 않는다.

### Main Branch Consolidation Notes

아래는 2026-05-29 main branch consolidation 당시의 히스토리 설명이다. 2026-06-02 직접 확인 기준으로 `clipper_python`은 `main...origin/main` ahead/behind가 `0/0`이다.

- `clipper_nestjs`
  - 로컬 `main`을 `feature/windows-packaging`에서 생성했다.
  - `feature/windows-packaging`는 로컬 `feature/initial-scaffold`의 추가 3커밋을 포함한다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이다.
- `clipper_electron`
  - 로컬 `main`을 `feature/windows-packaging`에서 생성했다.
  - `feature/windows-packaging`는 로컬 `feature/initial-scaffold`의 추가 1커밋을 포함한다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이다.
- `clipper_angular`
  - 로컬 `main`을 `feature/initial-scaffold`에서 생성했다.
  - 현재 `main`과 `feature/initial-scaffold`는 같은 commit이다.
- `clipper_python`
  - 기존 `main`은 `origin/main`의 `1e94974 Initial commit`에 머물러 있었다.
  - 로컬 `main`을 `feature/windows-packaging`까지 fast-forward했다.
  - 현재 `main`과 `feature/windows-packaging`는 같은 commit이고, `feature/plugin-architecture` 변경도 포함한다.
  - 그래서 `git status -sb`는 `main...origin/main [ahead 103]`로 보인다.
  - 이 `ahead 103`은 미커밋 변경이나 파일 103개가 아니라, `origin/main..main` 범위의 103개 commit이다.
  - Sync/push하면 그동안 feature 브랜치에 쌓인 Python plugin architecture, render worker, Template Builder fixture/render, env/windows packaging 관련 이력이 `origin/main`으로 올라간다.

## Active Decisions

- 사용자-facing 핵심 개념은 `플러그인`과 `프로젝트`다.
- `shortform_prompt`, `shortform_url`, `shortform_paste`는 각각 독립된 사용자 플러그인이다.
- 큐/보관함의 사용자 단위는 Project다. `/jobs`, `VideoRenderJob`, Python runtime `/jobs`는 내부 실행/호환 계층으로 취급한다.
- 하이라이트 분석 단계 메시지는 유저에게 보여줄 수 있지만, 숏폼/ffmpeg 렌더 세부 메시지는 `영상 생성 중`으로 단순화한다.
- Shortform production의 현재 1차 작업은 strict legacy parity port다.
- `shortform_url`, `shortform_paste`, `shortform_prompt`는 별도 user-visible plugin으로 유지한다.
- 레거시 Clipper shortform UI/스타일/영상 생성 전 동작은 `adlight_angular`와 완전히 동일해야 한다. 차이는 버그다.
- 1차 작업에서 `숏폼 생성하기` 버튼은 legacy `adlight_python` video-create payload를 console log만 한다.
- 1차 작업에서 ffmpeg 호출, render job 생성, queue insertion, `/projects` navigation은 금지다.
- 실행 모드는 `local`, `devapp`, `packaged`.
- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- real `.env.<mode>` 파일에 optional blank placeholder를 넣지 않는다.
- plugin별 고정 포트는 사용하지 않는다.
- Angular는 plugin URL/port를 몰라야 하고 NestJS API만 호출한다.
- Windows packaged build 중 PowerToys `Command Palette`를 끈다.
- `win.asar: false`, electron-builder retry, build script lock handling을 EBUSY 우회로 다시 넣지 않는다.
- Template Builder는 ffmpeg/ffprobe ready 이후에 본 UI를 시작한다.
- Template Builder sample render는 Angular 버튼/UI, NestJS recipe/assets, Python ffmpeg renderer가 함께 동작한다.
- 샘플 렌더의 콘텐츠 이미지는 콘텐츠 영역을 `cover` 방식으로 꽉 채운다. 빈 여백을 만들지 않고 넘친 부분을 중앙 crop한다.
- root `README.*.md`는 정해진 top-level guide만 둔다.
  - 현재 root README guide: `README.ARCHITECTURE.md`, `README.RUNTIME.md`, `README.FRONTEND.md`, `README.OPERATIONS.md`, `README.DOCS.md`.
  - 팀 설명용/심화 분석 문서는 `design/` 또는 domain folder 아래에 둔다.

## Last Completed Work

- 팀원 온보딩/Notion import용 개발 가이드를 추가했다.
  - `.codex/design/TEAM_DEVELOPMENT_GUIDE.md`
  - 구조, repo별 책임, `local`/`devapp`/`packaged` 실행 방법, branch 운영, env 첨부 섹션을 한 문서에 정리했다.
  - 명령어는 팀원이 각자 `PROJECT_ROOT`를 지정해 실행할 수 있게 작성했다.
- NestJS-native workflow도 Plugin Store/job history/start-stop 모델에 통합하기 위한 설계를 추가했다.
  - `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`
  - 쉬운 standalone 설명 문서로 `.codex/design/WORKFLOW_PLUGIN_JOB_EASY_EXPLANATION.md`도 추가됐다.
  - 이 쉬운 설명 문서는 전체 문서 인덱스나 다음 세션 필수 읽기 목록에 넣지 않아도 된다.
  - 현재 Python runtime plugin 중심 구조의 한계를 정리했다.
  - `WorkflowExecutor`, executor registry, Python adapter, NestJS-native ffmpeg executor 방향을 정의했다.
  - 작업 브랜치:
    - `.codex`: `workflow-executor-design`
    - `clipper_nestjs`: `design/workflow-executor`
- `clipper_nestjs` `design/workflow-executor`에서 WorkflowExecutor 초기 구현을 진행했다.
  - commit: `ceaa6ab Add workflow executor runtime dispatch`
  - `src/workflows/`에 executor interface, registry, Python adapter, virtual workflow executor, `simple_ffmpeg_transform` NestJS-native executor를 추가했다.
  - `JobsService`는 `PluginHost` 직접 호출 대신 `WorkflowExecutorRegistry`로 dispatch한다.
  - `PluginsService`는 Python, NestJS-native, virtual workflow를 registry 기반 list/status/start/stop으로 통합한다.
  - `PluginManifestView.runtimeKind`를 추가하고 기존 catalog/local manifests에 runtime kind를 명시했다.
  - 검증:
    - `clipper_nestjs npm run build`: passed.
    - `clipper_nestjs npm run bundle`: passed.
    - `clipper_nestjs node --test test/workflow-executor-registry.test.js`: passed (`2 passed`).
    - `simple_ffmpeg_transform` direct executor start smoke: passed locally with `runtimeState=running`.
    - `clipper_nestjs git diff --check`: passed.
- WorkflowExecutor 기준을 기존 아키텍처 문서들에도 반영했다.
  - `README.ARCHITECTURE.md`, `README.RUNTIME.md`
  - `design/TEAM_ARCHITECTURE_OVERVIEW.md`
  - `design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`
  - `design/TEAM_DEVELOPMENT_GUIDE.md`
  - `design/BACKEND_ROLE_SPLIT_CURRENT.md`
  - `design/NESTJS_CONTROL_PLANE_REDESIGN.md`
  - `design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
  - `design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
  - `design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
  - `design/CLIPPER2_NEXT_ARCHITECTURE_PLAN.md`
  - `design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
  - `operations/env-runtime/README.md`
- 로컬 앱 repo의 최종 작업 상태를 `main` 브랜치로 모았다.
  - 코드 내용은 새로 수정하지 않았다.
  - `clipper_nestjs`, `clipper_electron`, `clipper_angular`는 없던 로컬 `main`을 생성했다.
  - `clipper_python`은 기존 로컬 `main`을 `feature/windows-packaging`로 fast-forward했다.
  - branch 포함 관계 확인:
    - `clipper_nestjs`: `feature/windows-packaging`가 `feature/initial-scaffold`를 포함.
    - `clipper_electron`: `feature/windows-packaging`가 `feature/initial-scaffold`를 포함.
    - `clipper_python`: `feature/windows-packaging`가 `feature/plugin-architecture`와 기존 `main`을 포함.
  - 원격에는 아직 push하지 않았다.
- Template Builder sample render UX와 렌더 동작을 수정했다.
  - `clipper_angular` `70d6e58 Improve template sample render flow`
    - 상단 `샘플 렌더` 버튼은 결과 화면을 여는 역할만 한다.
    - 실제 최초 렌더/재렌더는 화면 안의 `렌더 시작` 버튼이 담당한다.
    - 샘플 렌더 화면에는 "이 화면을 닫아도 진행 중인 샘플 렌더는 계속 진행됩니다." 안내를 둔다.
    - 샘플 렌더는 가능한 네 비율을 모두 순차 렌더한다.
    - 플레이어는 shorts 비율로 표시한다.
    - 샘플 렌더 UI를 inspector에서 page header/overlay로 이동했다.
    - 편집 저장 시 사용자 템플릿 카드 썸네일은 저장 당시 선택 ratio를 사용한다.
    - 공식 템플릿 등록 직전에는 4:3 기준 카드 썸네일을 다시 생성한다.
  - `clipper_nestjs` `73c2519 Stage template sample media`
    - 샘플 렌더용 기본 콘텐츠 이미지를 `src/projects/assets/template-builder/sample-media.jpg`로 stage한다.
    - 해당 파일이 없으면 기존 generated PNG fallback을 쓴다.
    - 단색 `layoutImage`도 render layout layer로 전달해 content 영역 밖 흰 배경 문제를 보정했다.
  - `clipper_python` `535131c Render sample images as cover`
    - `effects: [{ type: "none" }]`을 실제로 존중해 자동 팬/줌을 끈다.
    - 샘플/정지 이미지 기본 렌더를 `contain + pad`가 아니라 `cover + crop`으로 변경했다.
    - 콘텐츠 영역을 꽉 채우고 넘친 부분은 중앙 crop한다.
- 검증:
  - `clipper_angular`: targeted tests `220 SUCCESS`, page-only `60 SUCCESS`, `npm run build` passed, `git diff --check` passed.
  - `clipper_nestjs`: `npm run build` passed, render payload targeted tests passed, sample render targeted tests passed, `git diff --check` passed.
  - `clipper_python`: `uv run pytest tests/test_clipper1_video_render_media_looping.py -q` passed (`27 passed`), `git diff --check` passed.
- main branch consolidation 직후 앱 코드 repo는 위 커밋들까지 clean 상태였다. 이후 `clipper_nestjs` `design/workflow-executor`의 WorkflowExecutor 구현은 `ceaa6ab`로 커밋 완료했다.
- 2026-06-02에는 dohit 인프라 참고 문서 3개를 읽고 Clipper2 설치형 앱 인프라를 이해하기 위한 문서를 시작했다.
  - 참고 문서:
    - `/Users/jina/project/dohit-infra/.codex/dohit-infra-easy-guide.md`
    - `/Users/jina/project/dohit-infra/.codex/dohit-infra-technical-guide.md`
    - `/Users/jina/project/dohit-infra/.codex/clipper-infra-recommendations.md`
  - 이해용/기술 문서:
    - `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`
    - `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`
  - 원칙:
    - dohit은 웹 리워드 서비스라 web/API 서버가 서비스 본체다.
    - Clipper2는 설치형 Electron 앱이라 서버는 다운로드 페이지, 설치파일 저장소, 업데이트 정보, 계정/API/관리자 기능을 담당한다.
    - Electron 설치파일은 Docker infra 서버가 아니라 self-hosted CI runner에서 빌드한다.
    - Windows 설치형 빌드는 code signing 인증서가 설치된 사무실 Windows PC self-hosted runner에서 수행한다.
    - macOS 설치형 빌드는 별도 Mac mini self-hosted runner에서 수행하는 방향이다.
    - 코드 push/main merge만으로 설치파일 release가 되면 안 된다.
    - Windows release는 Windows PC runner에서 `npm run build:app:win:x64`, macOS release는 Mac mini runner에서 `npm run build:app:mac:arm64` 같은 명시적 release build trigger로 실행한다.
    - Windows/macOS release와 version/update metadata는 플랫폼별로 따로 관리한다.
    - 설치파일 저장소는 기존처럼 S3를 유지한다.
    - dev/stage/prod 3환경을 설계한다.
    - stage/prod는 web/API 배포뿐 아니라 stage/prod 설치파일과 update feed를 나누는 문제다.
    - 3대 Mac mini 기본 배치는 proxy/prod app, dev/stage app, DB/backup/monitor다.
    - 문서는 `clipper_infra` repo가 아니라 `.codex`에 둔다.
    - `clipper_infra`에는 2026-06-02 초기 compose/env/runbook 구성을 생성했다.
    - 실제 IP, 도메인, S3 bucket, image tag, DB password는 아직 placeholder다.
    - 검증: dev/stage/prod app compose config, DB compose config, release metadata JSON, monitor JSON passed.
- 2026-06-04에는 다음 실제 서버 세션의 접속지와 첫 환경을 정했다.
  - 첫 서버 Codex 세션은 `m2-proxy`에서 read-only inventory/preflight로 진행했다.
  - 첫 실제 Clipper 배포 대상 환경은 `dev`다.
  - `stage`는 dev health와 DB/backup/proxy route 확인 뒤 진행한다.
  - `prod`는 stage 검증과 release/update feed 정책 확정 전에는 건드리지 않는다.
  - `m2-proxy`는 `192.168.0.2`, NPM은 `/Users/metabeojeu/Desktop/infra/proxy-server`에서 실행 중이다.
  - `m2-stage` 후보는 `192.168.0.23`, `m2-db` 후보는 `192.168.0.7`이다.
  - NPM active dohit route는 access list 없이 설정되어 있고, NPM admin `81`은 `0.0.0.0`에 bind되어 있으므로 ipTIME에서 WAN 공개 여부를 확인해야 한다.
  - Clipper 예약 port는 m2-proxy/m2-stage/m2-db 후보에서 충돌이 확인되지 않았다.
  - `m2-db` preflight도 완료됐다.
  - `m2-db`는 `192.168.0.7`, dohit DB compose는 `/Users/metabuzz/Desktop/project/dohit-infra/database/postgres/docker-compose.yml`이다.
  - dohit DB `55101/55102/55103`은 `0.0.0.0`에 bind되어 있고, 기존 Clipper DB 예약 port `55201/55202/55203`은 충돌이 없다.
  - 2026-06-05 기준 목표 DB 모델은 user/admin/release split이다.
    - user DB ports: dev `55203`, stage `55201`, prod `55202`
    - admin DB ports: dev `55213`, stage `55211`, prod `55212`
    - release DB ports: dev `55223`, stage `55221`, prod `55222`
  - Clipper dev DB는 `CLIPPER_DB_BIND_HOST=192.168.0.7`, source allow `192.168.0.23 -> 192.168.0.7:55203/55213/55223` 방향이 권장된다.
  - `m2-stage` preflight도 완료됐다.
  - `m2-stage`는 `192.168.0.23`, dohit dev/stage compose roots are `/Users/metabuzz/Desktop/project/dohit-infra-dev` and `/Users/metabuzz/Desktop/project/dohit-infra-stg`.
  - dohit dev/stage app ports `42103/43103/42101/43101` are in use, while Clipper app 예약 port `42201/42202/42203`, `42301/42302/42303`, `43201/43202/43203` are free.
  - Split dev DB deployment is complete on m2-db:
    - `clipper-db-user-dev` healthy on `192.168.0.7:55203`
    - `clipper-db-admin-dev` healthy on `192.168.0.7:55213`
    - `clipper-db-release-dev` healthy on `192.168.0.7:55223`
  - m2-stage network verification to all three dev DB ports succeeded.
  - User said not to spend time on dev DB password rotation for this deployment session. Do not print secrets in chat/logs.
  - Clipper web/admin/API Angular 19/NestJS corrections are committed and pushed.
  - m2-stage `stack.dev.env` was created server-locally from `stack.dev.env.example`; secrets were not printed.
  - Real web/admin/API dev services are deployed and healthy on m2-stage.
  - `clipper_infra/runbooks/deploy-db.md` documents deploying the dev DB stack with `docker compose --env-file ../env/db.dev.env -f compose.yml up -d`.
  - `clipperstudio.ai` authoritative DNS is Cloudflare (`adele.ns.cloudflare.com`, `owen.ns.cloudflare.com`), while Hosting.KR is the registrar.
  - m2-proxy/office WAN IPv4 is `112.169.113.138`, but ipTIME reports it as dynamic DHCP.
  - ipTIME DDNS `metabuzz.iptime.org` points to `112.169.113.138`.
  - ipTIME forwards `80/443` to m2-proxy `192.168.0.2`; router remote management is not configured.
  - Existing WAN forwards `55101/55102/55103` go to dohit DB on `192.168.0.7`.
  - Later decision: add temporary WAN forwarding for Clipper dev DB ports `55203/55213/55223` only. Do not add Clipper stage/prod DB ports `55201/55202/55211/55212/55221/55222` to WAN forwarding.
  - Legacy records `api.clipperstudio.ai -> 3.34.33.3` and `demo.clipperstudio.ai -> 121.138.93.3` must not be changed until legacy cutover.
  - Clipper dev records should be `dev.clipperstudio.ai`, `dev-admin.clipperstudio.ai`, `dev-api.clipperstudio.ai`, initially DNS-only.
  - Because the WAN IP is dynamic, prefer Cloudflare CNAME records to `metabuzz.iptime.org`; A records to `112.169.113.138` are acceptable only while the WAN IP remains unchanged.
  - The three dev CNAME records have been created and verified with `dig`; each resolves through `metabuzz.iptime.org` to `112.169.113.138`.
  - Temporary `nginx:alpine` containers on m2-stage verified `42203/42303/43203`.
  - NPM dev proxy hosts were added and external HTTPS checks returned `HTTP/2 200` for all three dev domains.
  - Observed `strict-transport-security: max-age=63072000; preload`; user decided to keep HSTS enabled for dev.
  - Prod web/download target is `clipperstudio.ai`/`www.clipperstudio.ai` after replacing the current Cloudflare Pages holding page.
  - `api.clipperstudio.ai` moves to Clipper2 prod API only after legacy Clipper is retired or cutover is approved.
  - `clipper_infra/proxy/routes.md` and `env/stack.*.env.example` were updated locally to use `clipperstudio.ai` domains and known server LAN IPs.
  - Next step is Clipper web client/admin/API scaffold and dev Docker image preparation.
  - 기록: `.codex/records/sessions/2026/06/04.md`

## Next Work

1. 세션 시작 시 `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python`의 `git status -sb`, `git log -1 --oneline`을 확인한다.
2. 현재 작업 branch 상태를 먼저 정리한다.
   - `.codex`: `workflow-executor-design`, 이번 문서 커밋 이후 clean이어야 한다.
   - `clipper_nestjs`: `design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch`, clean.
   - 앱 코드 변경과 `.codex` 문서 변경은 별도 commit으로 관리한다.
3. WorkflowExecutor 후속 확인:
   - Python plugin job regression smoke.
   - `simple_ffmpeg_transform` local/devapp/packaged smoke.
   - packaged Electron에서 NestJS-native ffmpeg path env 표준 확정.
   - 필요한 경우 Angular Plugin Store/job start UI에서 `runtimeKind` 표시/버튼 정책 연결.
4. Clipper2 dev/stage/prod 인프라 구현을 이어간다.
   - 먼저 `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`와 `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`를 읽는다.
   - `m2-proxy` read-only preflight는 완료됐다.
   - `m2-db` read-only preflight는 완료됐다.
   - `m2-stage` read-only preflight는 완료됐다.
   - Split dev DBs are deployed and healthy:
     - `clipper-db-user-dev` on `192.168.0.7:55203`
     - `clipper-db-admin-dev` on `192.168.0.7:55213`
     - `clipper-db-release-dev` on `192.168.0.7:55223`
     - DB Compose projects are environment-scoped: `clipper-db-dev`, `clipper-db-stage`, and optional self-hosted `clipper-db-prod`.
     - Prod DB can also be an external PostgreSQL service; in that case DB Compose is not used for prod and app env DB URLs point to the external DB endpoints.
     - DB containers create Postgres databases/users and persistent Docker volumes, not app tables. Tables come from app migrations/seed scripts.
     - `55201/55202/55211/55212/55221/55222` remain closed until stage/prod are ready.
     - m2-stage `nc` verification to `55203/55213/55223` succeeded.
     - User said not to spend time on dev DB password rotation for this deployment session. Do not print secrets in chat/logs.
   - Cloudflare dev route DNS is created.
     - `dev.clipperstudio.ai` CNAME `metabuzz.iptime.org`
     - `dev-admin.clipperstudio.ai` CNAME `metabuzz.iptime.org`
     - `dev-api.clipperstudio.ai` CNAME `metabuzz.iptime.org`
     - legacy `api.clipperstudio.ai`와 `demo.clipperstudio.ai`는 건드리지 않는다.
   - NPM dev proxy hosts are already created.
     - `dev.clipperstudio.ai` -> `192.168.0.23:42203`
     - `dev-admin.clipperstudio.ai` -> `192.168.0.23:42303`
     - `dev-api.clipperstudio.ai` -> `192.168.0.23:43203`
     - HSTS is enabled for dev by user decision.
     - User reported the temporary nginx test containers have already been removed.
     - Public dev domains now route to real m2-stage dev services.
   - 2026-06-08 dev app deployment strategy decision:
     - Use server-side build on m2-stage.
     - Do not use GHCR/registry push for this first dev deployment.
     - Expected m2-stage layout:
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_infra`
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_web_client`
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_web_admin`
       - `/Users/metabuzz/Desktop/project/clipper2/clipper_web_api`
     - App repos are siblings of `clipper_infra`, not ignored subdirectories inside infra.
   - `clipper_web_api`, `clipper_web_client`, and `clipper_web_admin` 2026-06-08 framework corrections are committed and pushed.
     - `clipper_web_client`: Angular 19 placeholder app, Docker image serves Angular build output with Nginx, latest `origin/main` `7bdaeae chore: move local web port to 4700`.
     - `clipper_web_admin`: Angular 19 placeholder app, Docker image serves Angular build output with Nginx, latest `origin/main` `db26f4d chore: move local admin port to 4701`.
     - `clipper_web_api`: NestJS scaffold with `/healthz`, `/v1/health`, `/v1/info`, and `/v1/releases/latest` 501 placeholder. Latest `origin/main` `0eab250 fix: require per-database passwords` verifies all three PostgreSQL connections with `SELECT 1` and uses per-DB password env variables.
     - m2-stage repo layout is complete under `/Users/metabuzz/Desktop/project/clipper2`.
     - m2-stage server-local `env/stack.dev.env` exists.
     - Real dev services are deployed with server-side built local images.
     - Final containers:
       - `clipper-web-client-dev` healthy on `192.168.0.23:42203->80`
       - `clipper-web-admin-dev` healthy on `192.168.0.23:42303->80`
       - `clipper-web-api-dev` healthy on `192.168.0.23:43203->43203`
     - Final public checks:
       - `https://dev.clipperstudio.ai` shows `C / CLIPPER2 WEB / Coming Soon`
       - `https://dev-admin.clipperstudio.ai` shows `A / CLIPPER2 ADMIN / Coming Soon`
       - `https://dev-api.clipperstudio.ai/v1/health` returns API health JSON
   - 첫 실제 배포 환경 `dev`는 완료됐다. `stage`는 dev app 기능/migration 흐름 확인 후, `prod`는 stage 검증과 승인 후 진행한다.
   - 실제 도메인, 서버 IP, proxy, dev DB 접속정보는 dev 기준 반영됐다. S3 bucket/prefix와 release artifact/update feed 연동은 아직 남았다.
   - dev `stack.dev.env`는 m2-stage에 생성 완료됐다. stage/prod env는 아직 아니다.
   - DB env files are split by environment: `db.dev.env`, `db.stage.env`, and optional `db.prod.local.env`.
   - backup worker는 아직 README placeholder만 있으므로 실제 backup image/script를 결정해야 한다.
   - Detailed session design doc: `.codex/design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md`
5. Clipper2 web/API 후속 구현을 진행한다.
   - 먼저 m2-stage에서 `clipper_infra`를 최신화하고 실제 `env/stack.dev.env`를 per-DB password split 변수 형식으로 수정한다.
   - 그 다음 `./scripts/deploy-dev.sh all`로 최신 infra/app image를 재배포하고 health/browser smoke를 확인한다.
   - `clipper_web_api` migration tooling 결정.
   - user/admin/release DB 첫 schema migration 작성.
   - `/v1/releases/latest` 실제 release metadata 구현.
   - client download/login/signup 실제 페이지 merge 시 dev 배포 반영.
   - admin 운영 기능 범위 결정.
6. Template Builder sample render smoke를 다시 할 경우 아래를 확인한다.
   - 새 템플릿 생성 후 단색/이미지 layout 변경 저장.
   - 샘플 렌더 화면 열기와 `렌더 시작`.
   - 네 비율 모두 생성.
   - 콘텐츠 이미지가 각 ratio의 content area를 빈 여백 없이 꽉 채우는지.
   - content area 밖 layout image 또는 단색 background가 흰색으로 빠지지 않는지.
   - 화면을 닫아도 렌더 진행이 계속되는지.
   - 공식 템플릿 등록 후 카드 썸네일이 4:3 기준인지.
7. Windows packaged smoke가 필요하면 기존 운영 문서 기준을 따른다.
   - PowerToys `Command Palette` off.
   - `.env.local` packaged read/copy 금지.
   - plugin별 env port 나열 금지.

## Next Session Prompt

```text
Using Superpowers.

지금 세션은 Clipper dev web/admin/API 배포 완료 이후의 후속 작업이다.
먼저 아래 상태를 기준으로 현재 repo/server 상태를 확인해줘.

배포 완료된 m2-stage layout:

/Users/metabuzz/Desktop/project/clipper2/
  clipper_infra/
  clipper_web_client/
  clipper_web_admin/
  clipper_web_api/

현재 기준:
- dev 배포 방식은 server-side build다. GHCR/registry push 방식은 이번 dev 배포에 쓰지 않았다.
- app repo 3개는 clipper_infra와 sibling이다.
- m2-stage `clipper_infra/env/stack.dev.env`는 생성되어 있고 secret 값은 채팅/로그에 출력하지 않는다.
- latest pushed commits:
  - clipper_infra: feature/infra-initial-setup @ f0cb1f1
  - clipper_web_client: main @ 7bdaeae
  - clipper_web_admin: main @ db26f4d
  - clipper_web_api: main @ 0eab250
- clipper_web_client는 Angular 19 placeholder app이고 `zone.js` polyfill 포함 상태여야 한다.
- clipper_web_admin은 Angular 19 placeholder app이고 `zone.js` polyfill 포함 상태여야 한다.
- clipper_web_api는 NestJS scaffold이고 `/healthz`, `/v1/health`에서 세 DB에 `SELECT 1`을 실행한다.
- clipper_web_api DB env는 URL 방식이 아니라 split 변수 방식이다.
- m2-stage `stack.dev.env`는 반드시 DB별 password 변수를 사용해야 한다:
  - `CLIPPER_USER_DATABASE_PASSWORD`
  - `CLIPPER_ADMIN_DATABASE_PASSWORD`
  - `CLIPPER_RELEASE_DATABASE_PASSWORD`
- `CLIPPER_DATABASE_PASSWORD` 하나짜리 공통 password 변수는 쓰지 않는다.
- Angular web/admin Docker image는 Angular build output을 컨테이너 내부 Nginx로 서빙한다.
- API Docker image는 Node/NestJS runtime이고 Nginx를 포함하지 않는다.
- m2-db dev DB 3개는 이미 배포 완료:
  - user DB: 192.168.0.7:55203
  - admin DB: 192.168.0.7:55213
  - release DB: 192.168.0.7:55223
- DB password rotate는 이번 세션에서 신경쓰지 않는다. 다만 secret 값은 채팅/로그에 출력하지 않는다.
- DBeaver로 DB를 볼 때 로컬 Mac mini에서 `192.168.0.7:55203` timeout이면 password 문제가 아니라 네트워크 도달성 문제다.
- 권장 DB GUI 접근은 m2-stage 안에서 DBeaver를 실행하는 방식이다. 로컬 DBeaver는 VPN/SSH tunnel 없이는 안 될 수 있다.
- legacy api.clipperstudio.ai, demo.clipperstudio.ai는 건드리지 않는다.
- dohit 관련 파일/컨테이너/포트는 건드리지 않는다.
- Clipper dev DB 포트 `55203/55213/55223`은 임시로 ipTIME 포트포워딩을 사용한다. stage/prod DB 포트는 WAN 공개하지 않는다.

해야 할 일:
1. `.codex/handoff/NEXT.md`, `.codex/records/sessions/2026/06/08.md`,
   `.codex/design/CLIPPER_DEV_TEAM_GUIDE.md`,
   `.codex/design/CLIPPER2_DEV_DEPLOYMENT_NOTION.md`를 먼저 읽는다.
2. m2-stage에서 아래를 먼저 실행해 `clipper_infra`를 최신화한다:
   - `cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra`
   - `git status --short --branch`
   - `git pull --ff-only origin feature/infra-initial-setup`
3. m2-stage의 실제 secret 파일을 확인하되 secret 값은 출력하지 않는다:
   - `/Users/metabuzz/Desktop/project/clipper2/clipper_infra/env/stack.dev.env`
   - 기존 `CLIPPER_*_DATABASE_URL` 또는 `CLIPPER_DATABASE_PASSWORD`가 있으면 제거하고 per-DB password split 변수로 바꾼다.
4. 관련 repo의 상태를 확인한다:
   - clipper_infra
   - clipper_web_client
   - clipper_web_admin
   - clipper_web_api
5. `./scripts/deploy-dev.sh all`을 실행해 최신 image/service를 재배포한다.
6. dev service health/browser smoke를 재확인한다:
   - https://dev.clipperstudio.ai
   - https://dev-admin.clipperstudio.ai
   - https://dev-api.clipperstudio.ai/v1/health
7. 다음 구현 단계는 infra wiring이 아니라 app 기능이다:
   - clipper_web_api migration tooling 결정
   - user/admin/release DB schema 첫 migration 작성
   - `/v1/releases/latest` 실제 release metadata 구현
   - client download/login/signup 실제 페이지 merge 시 배포 반영 방식 정리
   - admin 운영 기능 범위 결정
8. stage/prod 배포는 dev 기능과 migration 흐름이 정해진 뒤 진행한다.

문서 기준:
- if available, read clipper_infra/runbooks/deploy-dev.md,
  clipper_infra/apps/compose.yml, clipper_infra/apps/compose.dev.yml,
  clipper_infra/env/stack.dev.env.example first.
- Do not touch dohit containers/files/ports.
```

## Legacy Local Session Prompt

```text
Using Superpowers.

먼저 `/Users/jina/project/adlight/.codex`가 별도 git repo라는 점을 기준으로 아래 문서를 순서대로 읽고 현재 상태를 파악해줘.

1. `.codex/README.md`
2. `.codex/handoff/NEXT.md`
3. `.codex/README.ARCHITECTURE.md`
4. `.codex/README.RUNTIME.md`
5. `.codex/README.OPERATIONS.md`
6. `.codex/operations/env-runtime/README.md`
7. `.codex/operations/windows-packaging/README.md`
8. `.codex/features/template-builder/README.md`
9. `.codex/features/dance-highlight/README.md`
10. `.codex/design/TEAM_ARCHITECTURE_OVERVIEW.md`
11. `.codex/design/TEAM_DEVELOPMENT_GUIDE.md`
12. `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`
13. `.codex/design/PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md`
14. `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`
15. `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`
16. `.codex/design/CLIPPER2_WEB_DB_SPLIT_AND_DEV_DEPLOYMENT.md`
17. `.codex/records/sessions/2026/06/05.md`
18. `.codex/records/sessions/2026/06/02.md`
19. `.codex/records/sessions/2026/06/04.md`
20. `.codex/records/sessions/2026/05/29.md`
21. `.codex/records/sessions/2026/05/27.md`

현재 repo HEAD는 세션 시작 시 직접 `git status -sb`와 `git log -1 --oneline`으로 재확인한다.

현재 기준:
- `clipper_angular`: `main @ 70d6e58 Improve template sample render flow`
- `clipper_nestjs`: `design/workflow-executor @ ceaa6ab Add workflow executor runtime dispatch`
- `clipper_python`: `main @ 535131c Render sample images as cover`
- `clipper_electron`: `main @ f701677 Revert "Update electron builder"`
- `.codex`: `workflow-executor-design`, 2026-06-05 Clipper web DB split/session closeout docs 포함. 세션 시작 시 `git log -1 --oneline`으로 직접 재확인.
- `clipper_infra`: `feature/infra-initial-setup @ 49faa91 feat: split Clipper DB stack into user admin release`
- `clipper_web_admin`: `main @ fef456a feat: add minimal web admin scaffold`
- `clipper_web_api`: `main @ ec13be7 feat: add minimal web API scaffold`
- `clipper_web_client`: `main @ 791c935 feat: add minimal web client scaffold`

다음에 할 일:
1. `.codex`, `clipper_nestjs`, `clipper_electron`, `clipper_angular`, `clipper_python` 상태를 확인한다.
2. WorkflowExecutor 작업 branch들을 먼저 확인한다.
   - `.codex`: `workflow-executor-design`, clean after this documentation commit.
   - `clipper_nestjs`: `design/workflow-executor @ ceaa6ab`, clean.
   - 앱 코드 변경과 `.codex` 문서 변경은 별도 commit으로 관리한다.
3. WorkflowExecutor 후속 확인을 진행한다.
   - Python plugin job regression smoke.
   - `simple_ffmpeg_transform` local/devapp/packaged smoke.
   - packaged Electron에서 NestJS-native ffmpeg path env 표준 확정.
   - Angular Plugin Store/job UI에서 `runtimeKind` 표시/버튼 정책이 필요한지 검토한다.
4. Clipper2 dev/stage/prod 인프라 구현을 이어간다.
   - `.codex/design/CLIPPER2_INFRA_EASY_GUIDE.md`
   - `.codex/design/CLIPPER2_INFRA_TECHNICAL_GUIDE.md`
   - dohit 참고 문서 3개:
     - `/Users/jina/project/dohit-infra/.codex/dohit-infra-easy-guide.md`
     - `/Users/jina/project/dohit-infra/.codex/dohit-infra-technical-guide.md`
     - `/Users/jina/project/dohit-infra/.codex/clipper-infra-recommendations.md`
   - dohit은 웹 리워드 서비스이고, Clipper2는 설치형 Electron 앱이라는 차이를 먼저 맞춘다.
   - Windows installer는 사무실 Windows PC runner, macOS installer는 Mac mini runner, 설치파일 저장소는 S3라는 현재 전제를 유지한다.
   - 코드 push/main merge를 설치파일 release trigger로 삼지 않는다.
   - 플랫폼별 명시적 release build trigger와 release metadata 구조를 먼저 정한다.
   - dev/stage/prod 3환경을 기준으로 서버/컨테이너/DB/release/update feed 구조를 정한다.
   - `clipper_infra`에는 초기 compose/env/runbook 구성이 있다.
   - `m2-proxy`, `m2-db`, `m2-stage` preflight는 완료됐다.
   - `clipper-db-dev`도 m2-db에서 배포 완료됐고, m2-stage에서 `192.168.0.7:55203/55213/55223` 접근 확인이 끝났다.
   - dev Cloudflare DNS와 NPM dev proxy hosts도 완료됐다. 사용자는 임시 `nginx:alpine` 컨테이너를 이미 제거했다고 보고했다.
   - 2026-06-08 Angular 19/NestJS 전환 변경은 commit/push 완료됐다. m2-stage에서 `clipper_infra`를 pull하고 app repo 3개를 clone한 뒤 server-side build로 real dev service를 배포한다.
   - 첫 실제 Clipper 배포 환경은 `dev`다. `stage`는 dev 확인 후, `prod`는 stage 검증과 승인 후 진행한다.
   - 사용자가 dev DB password rotate는 이번 배포 세션에서 신경쓰지 말라고 했다. secret 값은 채팅/로그에 출력하지 않는다.
   - 서버 IP, 도메인, proxy, secret 주입, DB/백업 경로를 실제 값으로 채운다.
5. 사용자가 요청하면 로컬 main들을 repo별로 push한다.
6. Template Builder sample render 관련 후속 버그가 입력되면 아래 전제를 유지한다.
   - 샘플 렌더 UI는 Angular, recipe/assets는 NestJS, 실제 MP4 합성은 Python renderer가 담당한다.
   - 샘플 이미지는 콘텐츠 영역을 `cover + center crop`으로 꽉 채워야 한다.
   - layout image/단색 background는 content area 밖에서 흰색으로 빠지면 안 된다.
   - 공식 등록 전 카드 썸네일은 4:3 기준이어야 한다.
7. 새 분석 문서는 `.codex/design/` 아래에 둔다.

주의:
- `.codex`는 별도 git repo다.
- 앱 코드 repo 변경과 `.codex` 문서 변경을 같은 커밋에 섞지 않는다.
- `.env.local`을 packaged에서 읽거나 복사하는 방향은 금지다.
- plugin별 env 포트 나열 방식은 금지다.
- Windows build 중 PowerToys `Command Palette`를 끈다.
```

## Notes

- `.codex`는 별도 git repo다. 문서 변경은 `.codex`에서 commit/push한다.
- 앱 코드 repo 변경과 `.codex` 문서 변경은 같은 커밋에 섞지 않는다.
- 과거 경로를 이관할 때는 `git mv`를 우선 사용하고, 링크 확인은 `rg`로 한다.
- root `README.*.md`를 새로 늘리지 않는다. cross-cutting design 문서는 `design/`, feature 문서는 `features/<feature>/`, operations 문서는 `operations/<domain>/` 아래에 둔다.

## Current Shortform Installed-App State

- Prompt shortform script generation is routed through `desktop/clipper_nestjs -> web/clipper_web_api -> OpenAI`.
- Prompt shortform TTS is not routed through `web_api`.
- Installed-app TTS must use embedded `tts_supertonic`.
- `desktop/clipper_nestjs` shortform TTS now defaults to:
  - provider: `tts.supertone`
  - speaker: `F2`
  - speed: `1`
  - artifact format: `.wav` / `audio/wav`
- Naver Clova is no longer wired as a shortform TTS provider and no Clova fallback/migration path should be added.
- Supertonic TTS speed follow-up:
  - Root cause of "TTS sounds cut/too short" was Clova-era default speed `1.6` plus Angular default helper preferring `1.6`/`1.4` over provider preset defaults.
  - The installed app now uses Supertonic for shortform TTS.
  - User-facing shortform clip generation playback speed now defaults to `1.2`.
    - Nest project default render settings: `ttsSpeed: 1.2`.
    - Supertonic shortform preset default: `speed.default: 1.2`.
    - Angular style helpers and legacy style panel prefer `1.2` when supported.
  - A second root cause was confirmed for deliberate fast-speed regeneration:
    - passing user speed directly into Supertonic model synthesis can lose beginning/end speech content at faster speeds.
    - `tts_supertonic` now always calls the Supertonic model with stable speed `1.0` and applies requested playback speed as pitch-preserving wav post-processing.
    - The first simple-resampling post-processing attempt was rejected because it raised voice pitch at faster speeds; it has been replaced with a numpy phase-vocoder time-stretch path.
    - This avoids requiring FFmpeg or extra runtime consent for TTS regeneration.
  - Previously generated projects/wav files keep their old speed; retest with a newly generated project after restarting services.
- Before manual prompt shortform retest, reset local app/runtime data so previously created projects with old `tts.naver_clova` render settings do not affect the result.
- Verification already run:
  - `desktop/clipper_nestjs`: `npm run build && node --test test/shortform-project-generation-assets.test.js test/shortform-tts-provider.test.js test/shortform-script-generator-wiring.test.js`
  - `desktop/clipper_nestjs`: `node --test --test-name-pattern "shortform style catalogs expose BGM and TTS presets" test/shortform-project-api.test.js`
  - `desktop/clipper_nestjs`: `npm run build`
  - `desktop/clipper_nestjs`: `node --test test/shortform-tts-provider.test.js`
  - `desktop/clipper_nestjs`: `node --test test/shortform-project-generation-assets.test.js`
  - `desktop/clipper_angular`: `./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/shortform/pages/shortform-workflow-style.spec.ts`
  - `desktop/clipper_angular`: `npm run build`
  - `desktop/clipper_nestjs`: `npm run build && node --test test/shortform-tts-provider.test.js test/shortform-project-generation-assets.test.js` -> 17 passed after the `1.2` default update.
  - `desktop/clipper_angular`: `./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/features/shortform/pages/shortform-workflow-style.spec.ts --include src/features/shortform/components/workflow/shortform-legacy-style-panel/shortform-legacy-style-panel.component.spec.ts --include src/features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component.spec.ts` -> 68 passed after the `1.2` default update.
  - `desktop/clipper_angular`: `npm run build` passed after the `1.2` default update.
  - `desktop/clipper_python`: `uv run --with pytest --with httpx --package clipper-plugin-tts-supertonic python -m pytest tests/test_tts_supertonic_synthesis.py tests/test_tts_supertonic_route.py tests/test_tts_supertonic_runtime.py -q` -> 10 passed
  - Runtime smoke: `GET /v1/projects/shortform/tts/presets?locale=ko-KR` returned 10 `tts.supertone` presets.
- Known gap:
  - `desktop/clipper_nestjs`: `node --test test/shortform-project-api.test.js` currently fails because that test harness does not configure/mock `CLIPPER_WEB_API_BASE_URL`.
  - Do not interpret this as a TTS speed regression; it is a web_api-only media/LLM test-harness follow-up.

## Current Dialog Highlight web_api State

- `clipper_web_api` health was verified alive on `127.0.0.1:3000`.
- `clipper_nestjs` health was verified alive on `127.0.0.1:9019`.
- A live NestJS dance endpoint using the same `WebApiClient` successfully reached web_api.
- Dialog Highlight failure `web_api is unreachable` was caused by the desktop `WebApiClient` 30s timeout being too short for LLM steps and being reported as generic unreachable.
- Follow-up failure `web_api request failed: HTTP 502: provider_failed: OpenAI Responses request failed: The operation was aborted due to timeout` proved the request reached web_api, but web_api's own OpenAI Responses call timed out.
- `desktop/clipper_nestjs` now has:
  - per-request `WebApiClient.postJson(..., { timeoutMs })`;
  - `WebApiTimeoutError` with code `web_api_timeout`;
  - Dialog Highlight web_api calls defaulting to `240000ms`;
  - optional override `DIALOG_HIGHLIGHT_WEB_API_TIMEOUT_MS`.
- `web/clipper_web_api` Dialog Highlight LLM calls now have:
  - OpenAI Responses default timeout `180000ms`;
  - timeout-specific provider message `provider_failed: OpenAI Responses request timed out after <ms>ms`.
- `web/clipper_web_api` Dialog Highlight LLM route now logs request lifecycle at the controller boundary:
  - request start: `dialog_highlight.llm request requestId=<id> operation=<operation> locale=<locale>`;
  - completion: `dialog_highlight.llm completed requestId=<id> operation=<operation> elapsedMs=<ms>`;
  - failure: `dialog_highlight.llm failed requestId=<id> operation=<operation> status=<httpStatus> elapsedMs=<ms> message=<error>`;
  - request input/prompt payload is intentionally not logged.
- Verification:
  - `desktop/clipper_nestjs`: `npm run build && node --test test/web-api-client.test.js test/dialog-highlight-web-api-client.test.js test/dialog-highlight-workflow-executor.test.js test/error-code.test.js` -> 39 passed.
  - `web/clipper_web_api`: `npm test -- --runInBand src/modules/dialog-highlight/presentation/dialog-highlight-llm.controller.spec.ts src/modules/dialog-highlight/application/dialog-highlight-llm.service.spec.ts` -> 8 passed.
  - `web/clipper_web_api`: `npm run build` passed.
- Manual retest requires restarting `clipper_nestjs`/Electron; the running PID from before this change still has the old 30s timeout code.

## Current Plugin Store Install State

- Plugin Store now blocks concurrent plugin installs in `desktop/clipper_angular`.
- The root cause was that a second install click could reset shared `ModelDownloadService`/`FfmpegDownloadService` state while the first plugin install was still running.
- Current behavior:
  - only one plugin install flow can run at a time.
  - selecting/navigating to another plugin is still allowed.
  - another uninstalled plugin's install button is disabled with `다른 플러그인 설치 중`.
  - repeated install clicks during the active flow do not reset model/ffmpeg install state.
- Verification already run:
  - `desktop/clipper_angular`: `./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless --include src/shell/store/store/store.component.spec.ts --include src/shell/store/plugin-detail/plugin-detail.component.spec.ts`
- Manual retest:
  - reset app data.
  - start Dialog Highlight install.
  - before it finishes, select Dance Highlight.
  - expected: Dance install is disabled until Dialog install completes, then Dance can be installed normally.

## Current Shortform Packaged-App Follow-up

- During packaged local-api testing, the user found that editing a successfully generated paste shortform project did not restore the original pasted editor contents.
- Root cause:
  - `ShortformWorkflowPageComponent` restored `project.source.html` into the paste input state.
  - `ShortformLegacyInputPanelComponent` rendered a raw `contenteditable` div but never synchronized that restored state back into the editor DOM.
- Fix:
  - `desktop/clipper_angular` now syncs saved paste HTML into the paste editor DOM when the current DOM differs from restored input state.
  - The sync is guarded by normalized equality so normal typing does not rewrite the editor on every change.
- The user also saw intermittent shortform render failures:
  - `Shortform render requires a legacy Clipper1 or Template Builder template preset`
  - failed jobs had a selected Template Builder template id, but no render manifest because render prepare failed before activation.
- Root cause:
  - `RenderRecipeProvider` could build a snapshot-backed Template Builder recipe, but `LegacyClipper1RenderPayloadMapper` re-required the template from the live catalog and ignored the already-built recipe params when catalog lookup was unavailable.
  - Later prompt runs could succeed when that live catalog path happened to be available; it was not specific to URL/prompt/paste input mode.
- Fix:
  - `desktop/clipper_nestjs` legacy render payload mapper now falls back to Template Builder params already present in the render recipe when catalog lookup is unavailable.
- Verification:
  - `desktop/clipper_angular`: shortform legacy input panel spec -> 13 success.
  - `desktop/clipper_angular`: shortform workflow page spec -> 60 success.
  - `desktop/clipper_angular`: `npm run build -- --progress=false` -> pass.
  - `desktop/clipper_nestjs`: `node --test test/simplified-shortform-render-recipe-provider.test.js test/template-builder-render-payload.test.js` -> 17 passed.
  - `desktop/clipper_nestjs`: `npm run build` -> pass.
  - `desktop/clipper_electron`: `npm run build:app:mac:arm64:local-api` -> pass.
  - `desktop/clipper_electron`: `node scripts/assert-no-packaged-secrets.mjs` -> pass.
  - Packaged runtime config was checked by key/host classification only; the local-api build uses a loopback web_api base URL.
- Manual retest target:
  - Restart/reopen the rebuilt packaged app.
  - Open an existing paste shortform project and confirm pasted text/images appear in the editor.
  - Re-run URL/prompt/paste shortform render with the selected Template Builder default template.
- Latest paste clip-generation follow-up:
  - User saw `POST /v1/projects/shortform/projects/<id>/clips` return 503 with traces `0a1165a0` and then `e7bcd083`.
  - Root cause from packaged NestJS log:
    - `0a1165a0`: `web_api` returned 502 because OpenAI `llm.script` output was invalid JSON.
    - `e7bcd083`: after adding JSON output format directly to the primary request, OpenAI returned HTTP 400.
    - The pasted source content and env values were not printed.
  - Fix:
    - `web/clipper_web_api` keeps `web_search_preview` on the primary shortform script generation request.
    - The primary web-search request does not combine `web_search_preview` with `text: { format: { type: "json_object" } }`.
    - If the primary web-search response is malformed JSON, `web_api` sends a second no-tools JSON repair request with `text: { format: { type: "json_object" } }`.
    - Existing strict JSON parsing and `clips[]` validation remain in place.
  - Verification:
    - `web/clipper_web_api`: shortform script spec -> 19 passed.
    - `web/clipper_web_api`: shortform script + Dialog Highlight specs -> 29 passed.
    - `web/clipper_web_api`: `npm run build` -> pass.
  - Manual retest note:
    - If local `web/clipper_web_api npm run start:dev` does not auto-reload, restart it before retrying paste clip generation.
- Latest media-search follow-up:
  - User saw `POST /v1/projects/shortform/projects/<id>/clips` return 502 with trace `61075652`.
  - Root cause from packaged NestJS log:
    - script generation and Supertonic TTS had already succeeded.
    - generated image search failed at `media.search.remote_proxy.image` because remote media.search provider returned HTTP 502.
  - Fix:
    - automatic shortform clip generation now treats generated media search provider failure as non-fatal.
    - if a generated image search provider fails, the clip is still created with TTS/narration and an empty media pool/slots.
    - missing media search provider configuration still remains fatal.
    - manual per-clip media search/import APIs still surface search errors.
  - Verification:
    - `desktop/clipper_nestjs`: focused generated media provider failure test -> passed.
    - `desktop/clipper_nestjs`: shortform generation assets + media search routing tests -> 18 passed.
    - `desktop/clipper_nestjs`: `npm run build` -> pass.
    - `desktop/clipper_electron`: `npm run build:app:mac:arm64:local-api` -> pass.
    - `desktop/clipper_electron`: packaged secret guard -> pass.
    - Packaged runtime config loopback check -> pass.
  - Manual retest note:
    - Reopen the rebuilt packaged app from `desktop/clipper_electron/dist-app/mac-arm64/Clipper2.app`.

## Current Shortform TTS Playback Auth Fix

- User live-tested Electron devapp login and prompt shortform clip generation successfully.
- TTS synthesis itself succeeded; `clipper_nestjs` log showed Supertonic `/tts` calls returning 200 and WAV artifacts being saved.
- Playback failure root cause:
  - browser media requests for `tts/<artifactId>/file` do not carry Angular/Electron bearer headers.
  - with `CLIPPER_AUTH_MODE=jwt`, local NestJS rejected those `<audio>`/metadata requests with `Missing bearer token`.
- Fix in progress/completed:
  - `desktop/clipper_nestjs` now issues short-lived opaque `mediaToken` tickets for shortform TTS file URLs.
  - tickets are local process-memory mappings of owner/project/artifact/expiry only; JWT/access token/provider key material is not placed in URLs.
  - TTS file endpoint keeps bearer auth when Authorization is present and falls back to ticket resolver when no bearer can be attached.
  - transient `ttsAudioUrl` values are stripped before project persistence and regenerated for list/get/update/media-edit responses.
  - `desktop/clipper_angular` preserves `mediaToken` when rewriting saved TTS URLs to the current backend port.
- Verification run:
  - `desktop/clipper_nestjs`: `node --test test/shortform-tts-file-ticket.test.js` -> 2 passed.
  - `desktop/clipper_nestjs`: `npm run build` -> pass.
  - `desktop/clipper_nestjs`: `git diff --check` -> pass.
  - `desktop/clipper_angular`: focused shortform project service spec -> 10 passed.
  - `desktop/clipper_angular`: `npm run build` -> pass.
  - `desktop/clipper_angular`: `git diff --check` -> pass.
- Manual retest needed:
  - restart `desktop/clipper_nestjs` devapp so it runs the new ticket code.
  - reload/restart Electron renderer so Angular runs the new URL preservation code.
  - create or open a shortform project with TTS and confirm audio preview plays without `Missing bearer token`.

## Current Project Artifact Playback Auth Fix

- User confirmed shortform TTS preview now plays in Electron devapp.
- Follow-up issue:
  - after clicking `숏폼 생성하기`, the render job completed and appeared in project history.
  - project thumbnail was blank and generated video would not play.
  - `clipper_nestjs` logged `Missing bearer token` for:
    - `GET /v1/projects/<projectId>/file?path=renders%2Fmain_thumbnail.jpg`
    - `GET /v1/projects/<projectId>/file?path=renders%2Fmain.mp4`
- Root cause:
  - render itself completed.
  - project artifact thumbnail/video are loaded by browser `<img>`/`<video>`, which cannot attach Angular bearer headers.
  - `ProjectsController.getFile()` previously required bearer auth unconditionally.
- Fix:
  - `desktop/clipper_nestjs` now exposes `POST /v1/projects/:projectId/file-tickets` for authenticated renderer requests.
  - local NestJS issues short-lived opaque media tokens for specific project file paths.
  - `GET /v1/projects/:projectId/file` keeps bearer auth when Authorization is present and falls back to media token validation when bearer cannot be attached.
  - `desktop/clipper_angular` caches project file media tokens during project refresh/getByJob/detail/manifest loads.
  - `ProjectHistoryService.projectFileUrl()` appends cached `mediaToken` to thumbnail/video URLs when available.
  - tokens do not contain JWT/access token/provider key material and are stored only in local process memory on the server side.
- Follow-up fix:
  - stored shortform render metadata can contain both absolute `video_path`/`thumbnail_path` and relative `video_relative_path`/`thumbnail_relative_path`.
  - Angular now sends only project-relative paths to `/file-tickets`.
  - local NestJS skips invalid project file paths in a batch ticket request instead of failing tokens for otherwise valid paths.
  - Angular no longer returns tokenless `/projects/:projectId/file` URLs while a media ticket is not cached yet, preventing one-off unauthorized thumbnail requests during project archive refresh.
- Verification run:
  - `desktop/clipper_nestjs`: `node --test test/project-file-media-ticket.test.js test/shortform-tts-file-ticket.test.js test/project-output-render-path.test.js test/variation-batch-retry-zip.test.js` -> 38 passed after the absolute-path follow-up.
  - `desktop/clipper_nestjs`: `npm run build` -> pass.
  - `desktop/clipper_angular`: focused `project-history` + `projects` specs -> 20 passed.
  - `desktop/clipper_angular`: `npm run build` -> pass.
- Manual retest result:
  - User restarted the devapp flow and confirmed completed shortform output appears in project history.
  - User confirmed project thumbnail renders and generated MP4 playback works.
  - User then smoke-tested Dance Highlight end-to-end:
    - web_api routed Naver image search through DB provider credentials.
    - plugin pipeline completed, project queue/job flow completed, and output was added to completed projects.
    - project archive thumbnail, project detail thumbnails, and video playback all rendered.
  - No provider secret/env values or raw API keys were recorded.

## Current Dialog Highlight Install State Fix

- User observed Dialog Highlight install staying in progress without a completion state.
- After app restart, the plugin incorrectly appeared as `설치됨`.
- Running the plugin then failed at startup:
  - project queue stayed around pipeline start.
  - plugin dashboard showed `오류`.
  - local NestJS reported `Plugin on port 54800 did not become healthy within 60s`.
- Root cause:
  - model-backed plugin install state treated HuggingFace/model files as the source of truth.
  - Electron and local NestJS auto-restored `.ready` markers when files existed.
  - Dialog Highlight model files/cache can exist even when the plugin never reached `/health`.
- Fix:
  - `desktop/clipper_electron` now writes a JSON ready marker only after plugin startup health check succeeds.
  - `desktop/clipper_electron` install-state check now requires both model files and a validated JSON ready marker for model-backed plugins.
  - `desktop/clipper_nestjs` uses the same validated marker rule and no longer auto-restores `.ready` from files alone.
  - legacy timestamp-only `.ready` markers are treated as invalid, so old partial installs are not shown as installed.
  - local plugin startup timeout is configurable through `CLIPPER_PLUGIN_START_TIMEOUT_MS` and defaults to 300000 ms instead of the prior hard-coded 60 s.
- Verification run:
  - `desktop/clipper_electron`: `node --test test/plugin-install-state.test.mjs` -> 7 passed.
  - `desktop/clipper_electron`: `node --test test/model-download-info.test.mjs` -> passed.
  - `desktop/clipper_electron`: `npm test` -> 100 passed.
  - `desktop/clipper_electron`: `npm run build` -> pass.
  - `desktop/clipper_electron`: `git diff --check` -> pass.
  - `desktop/clipper_nestjs`: related plugin install/runtime tests -> 15 passed.
  - `desktop/clipper_nestjs`: `npm run build` -> pass.
  - `desktop/clipper_nestjs`: `git diff --check` -> pass.
- Manual retest needed:
  - restart local NestJS and Electron devapp after rebuilding.
  - Dialog Highlight should no longer show `설치됨` from an old timestamp marker.
  - reinstall/start should only mark installed after the plugin becomes healthy.
- Follow-up:
  - User reset app data and intentionally quit during Dialog Highlight `faster-whisper-small` download.
  - HuggingFace cache contained only a `*.incomplete` blob, but the install modal reported `faster-whisper-small` as already installed.
  - Electron and local NestJS now ignore `*.incomplete` and zero-byte HF blobs when deciding model presence.
  - Verification: Electron full test suite passed 102 tests; NestJS related plugin tests passed 16 tests.
- Follow-up:
  - User retried Dialog Highlight install and observed the download UI staying at 0% for a long time.
  - Electron logs showed HuggingFace HEAD and Xet read-token requests but no `download_progress` event.
  - Local Xet logs and HF cache showed the `.incomplete` file growing/reconstructing, so the transfer was active while `tqdm_class` progress was not emitted.
  - `desktop/clipper_python` now polls the HuggingFace `.incomplete` blob size during dialog model prefetch and emits monotonic progress for Xet/native transfer paths.
  - Verification: isolated dialog HF progress regression test passed; ruff passed; py_compile passed; `git diff --check` passed.
  - Broader dialog pytest commands were attempted but the current `uv` test runner environment lacked or mismatched Python 3.11 binary dependencies (`numpy`, `uvicorn`/`pydantic_core`), so those commands were not usable as signal for this code change.
- Follow-up:
  - User observed Dialog Highlight hanging after `faster-whisper-small` small files downloaded.
  - HF cache inspection showed `config.json`, `tokenizer.json`, and `vocabulary.txt` snapshot links existed, but `model.bin` snapshot link did not.
  - A previous full-size `model.bin` `.incomplete` blob remained from the interrupted Xet transfer.
  - The next run held/updated the HF lock but did not turn the stale `.incomplete` into a final snapshot file.
  - `desktop/clipper_python` now removes orphan complete-size `.incomplete` blobs before prefetch when the expected snapshot file is missing.
  - Smaller partial `.incomplete` blobs are preserved for normal resume/progress.
  - Verification: dialog HF progress tests passed 2 tests; ruff passed; py_compile passed; `git diff --check` passed.
- Follow-up:
  - User still saw `faster-whisper-small` as `이미 설치됨` while `model.bin` snapshot was missing.
  - Root cause: Electron/local NestJS still accepted any non-incomplete HF blob as model presence, so metadata blobs (`config.json`, `tokenizer.json`, `vocabulary.txt`) made the model look installed.
  - Electron/local NestJS now require model-specific snapshot filenames for HF model presence and no longer use generic `blobs/` fallback.
  - Verification: Electron full test suite passed 103 tests; NestJS related plugin tests passed 17 tests; builds/diff checks passed.
- Follow-up:
  - User retried Dialog Highlight download with `HF_TOKEN`; unauthenticated HF warning disappeared, but download still stalled after HEAD.
  - Root cause 1: `desktop/clipper_python` prefetch trusted `snapshot_download(..., local_files_only=True)` even when the snapshot only had metadata files and the expected large file (`model.bin`) was missing.
  - Fix: prefetch now verifies the expected large snapshot filename before returning, removes stale complete-size `.incomplete`, and passes `HF_TOKEN`/`HUGGINGFACE_HUB_TOKEN` explicitly to HuggingFace calls when present.
  - Commit: `desktop/clipper_python` `b3828a6 fix(dialog): require large hf model snapshot`.
  - Verification: `uv run pytest tests/test_dialog_hf_progress.py -q` -> 4 passed; ruff, py_compile, `git diff --check` passed.
- Follow-up:
  - User still saw the dialog download stall around the large model file.
  - Local inspection showed old dialog Python processes still holding the HuggingFace `model.bin` lock. They were terminated, and the lock owner cleared.
  - New Xet logs then showed the transfer path receiving repeated HuggingFace CDN range `500` responses, while `HF_TOKEN`/CAS token refresh was successful. This was not an auth failure.
  - Fix: Dialog Highlight now disables `hf-xet` by default at package import time and again before model prefetch, so the model download uses the standard HuggingFace HTTP path.
  - Commit: `desktop/clipper_python` `cf09810 fix(dialog): disable unstable hf xet downloads`.
  - Verification: `uv run pytest tests/test_dialog_hf_progress.py -q` -> 6 passed; ruff, py_compile, `git diff --check` passed.
  - Manual retest needed: fully restart Electron/local NestJS so no old Python plugin process remains, then retry Dialog Highlight install/download.
- Follow-up:
  - User confirmed Dialog Highlight install completion snackbar appeared, but Plugin Store still displayed `미설치`/`설치하기`.
  - Root cause: HuggingFace snapshot files are symlinks to `blobs/`, but Electron/local NestJS install-state checks only accepted `Dirent.isFile()`. The validated ready marker and model blobs existed, but `model.bin`/OpenCLIP snapshot symlinks were treated as missing.
  - Fix: Electron/local NestJS install-state now accepts snapshot symlinks and verifies the symlink target with `statSync(...).size > 0`.
  - Commits:
    - `desktop/clipper_nestjs` `d270cd0 fix(plugins): detect hf snapshot symlinks`
    - `desktop/clipper_electron` `dc5ced7 fix(plugins): detect hf snapshot symlinks`
  - Verification:
    - `desktop/clipper_nestjs`: symlink RED test failed before fix, related plugin tests -> 18 passed, build/diff check passed.
    - `desktop/clipper_electron`: symlink RED test failed before fix, `npm test` -> 104 passed, build/diff check passed.
    - Live local NestJS status after fix: `GET /v1/plugins/dialog_highlight/status` returned `installState: installed`.
- Follow-up:
  - User confirmed Plugin Store updated to installed, but clicking the Dialog Highlight sidebar entry still opened the AI model needed modal.
  - Root cause: Angular readiness still called Electron `modelDownload.modelsNeeded()` for `pluginModel` requirements even when `PluginStatusService` already had the plugin marked `installed`. If Electron IPC/renderer state was stale, it could re-open the model consent modal despite backend install state being installed.
  - Fix: `desktop/clipper_angular` readiness skips model consent checks for already-installed plugins and resets stale consent/error prompts for the same plugin before continuing to warmup.
  - Commit: `desktop/clipper_angular` `cf2defb fix(readiness): skip model prompt for installed plugins`.
  - Verification: readiness RED tests failed before fix, focused readiness test -> 7 passed, dialog setup test -> 15 passed, `npm run build`/`git diff --check` passed.

### Follow-up: manual operation smoke and DB audit

- User confirmed Electron devapp login and real product smoke results:
  - Shortform prompt flow succeeded: clip generation, TTS preview audio, render queue/completion, archive thumbnail, and video playback.
  - Dance Highlight succeeded end-to-end: pipeline, queue/completed project, archive/detail thumbnails, and videos.
  - Dialog Highlight succeeded end-to-end after install-state/readiness fixes: pipeline, queue/completed project, archive/detail thumbnails, and videos.
- DB audit for recent 24h operation/credit/provider records:
  - `operation_runs` and `credit_ledger` matched; anomaly query returned 0 rows.
  - failed `dialog_highlight.extract` run refunded the full charged credits.
  - succeeded `shortform.create`, `dance_highlight.extract`, and `dialog_highlight.extract` runs charged expected credits.
  - `provider_usage` recorded OpenAI usage for shortform/dialog runs.
  - `dance_highlight.extract` had 0 provider_usage rows even though setup-time Naver image search occurred. This remains a known transition gap because current Dance reference image search can occur before the billable workflow run exists.
- Follow-up policy note:
  - Do not force setup-time Dance reference search into `dance_highlight.extract` without UX/policy design.
  - Future phase should decide whether Dance reference search becomes part of an explicit preflight/quote flow, a free setup provider action with audit-only tracking, or a search step moved after `/operations/start`.

### Follow-up: Settings page license/credit summary

- User found the Settings page license/credit rows were hardcoded dummy values.
- Fix:
  - `web/clipper_web_api` keeps `tokenBalance` compatibility and adds `creditBalance`, `creditAllowance`, and `creditsUsed` to `GET /licenses/current`.
  - `desktop/clipper_nestjs` adds `GET /v1/licenses/current` as a thin authenticated proxy to web_api `GET /licenses/current`.
  - `desktop/clipper_angular` Settings page uses `SettingsAccountService` and replaces hardcoded `무료 플랜`, `460 / 500`, and fixed progress with live license summary state.
- Verification:
  - `web/clipper_web_api`: `npm test -- licenses.service.spec.ts licenses.controller.spec.ts --runInBand` -> 8 passed; `npm run build` -> passed.
  - `desktop/clipper_nestjs`: RED tests confirmed missing `WebApiClient.getJson` and missing local license proxy; `node --test test/web-api-client.test.js test/license-current-proxy.test.js` -> 13 passed; `npm run build` -> passed.
  - `desktop/clipper_angular`: RED tests confirmed missing settings account service; focused settings specs -> 10 passed; `npm run build` -> passed.
- Follow-up UI polish:
  - Settings credit bar was replaced with a custom segmented credit meter so total track, remaining credits, and used credits are visually distinct.
  - The meter includes `사용 N` legend text and progressbar aria attributes.
  - Verification: RED settings component test failed before fix; focused settings component spec -> 10 passed; `npm run build` and `git diff --check` passed.
  - User noted the used segment was still too close to the track/background color.
  - Follow-up fix increased the used segment contrast with warning-colored fill, stripe overlay, and a divider; the legend dot now matches the stronger used color.
  - Verification: focused settings component spec -> 11 passed; `npm run build` and `git diff --check` passed.
- Follow-up: Settings "이용권 신청" button
  - User observed the button did nothing.
  - Root cause: `desktop/clipper_angular` rendered the button without a click handler; `web/clipper_web_client` also did not preserve `/app/purchase` through the web login callback when the browser was not already logged in.
  - Fix:
    - `desktop/clipper_electron` exposes a narrow `external.openWebClientPath(path)` bridge and only accepts relative web-client paths.
    - Electron maps local web_api (`localhost`/`127.0.0.1`) to local web client `http://localhost:4201`, and maps dev/stage/prod API domains to the matching web client origins. `CLIPPER_WEB_CLIENT_BASE_URL` can override the derived origin.
    - `desktop/clipper_angular` Settings opens `/app/purchase` through the Electron bridge, with a local browser fallback.
    - `web/clipper_web_client` carries `returnUrl=/app/purchase` through Google login and returns to it after callback.
  - Commits:
    - `desktop/clipper_electron` `91691ec feat(external): open web client purchase links`
    - `desktop/clipper_angular` `82b01f5 feat(settings): open license purchase page`
    - `web/clipper_web_client` `d522f88 fix(auth): preserve purchase return url`
  - Verification:
    - `desktop/clipper_electron`: RED module-missing test failed before fix; `npm test` -> 107 passed; `npm run build` passed.
    - `desktop/clipper_angular`: RED settings spec failed because bridge was not called; focused settings spec -> 12 passed; `npm run build` passed.
    - `web/clipper_web_client`: RED auth-api export missing before fix; focused auth/login/callback specs -> 5 passed; `npm run build` passed.
    - `web/clipper_web_client` full `ng test` still has an unrelated existing timeout in `mockApiInterceptor returns mock current license for GET /licenses/current`; the same spec fails when run alone.
- Follow-up: queued license visibility
  - User clarified `/admin/approvals` can stay request-approval oriented; it does not need to show active vs queued lifecycle.
  - Root causes:
    - `web/clipper_web_client` history labels did not include the `queued` display status, so queued licenses appeared with a blank status.
    - `desktop/clipper_angular` Settings showed only the active/current plan and did not expose queued license count/details or a purchase-history link.
    - `web/clipper_web_api` `GET /licenses/current` exposed only queued count/next id, not enough detail for Settings to show multiple queued license names.
  - Fix:
    - `web/clipper_web_api` adds `queuedLicenses[]` with plan name and credit summary to current license.
    - `web/clipper_web_client` history maps `queued` to `시작 대기` and keeps lifecycle statuses typed.
    - `desktop/clipper_angular` Settings shows `시작 대기 N개 · ...` under the active plan and adds a `구매 내역` button opening `/app/history`.
  - Commits:
    - `web/clipper_web_api` `646d13d feat(billing): expose queued license summaries`
    - `web/clipper_web_client` `cee0da3 fix(history): label queued license requests`
    - `desktop/clipper_angular` `2999873 feat(settings): show queued licenses`
  - Verification:
    - `web/clipper_web_api`: RED queuedLicenses assertion failed before fix; `npm test -- licenses.service.spec.ts licenses.controller.spec.ts --runInBand` -> 8 passed; `npm run build` passed.
    - `web/clipper_web_client`: RED queued status type/label failed before fix; focused history/auth specs -> 3 passed; `npm run build` passed.
    - `desktop/clipper_angular`: RED queuedLicenses type/history button tests failed before fix; focused settings specs -> 15 passed; `npm run build` passed.
    - `git diff --check` passed in all three repos.
- Follow-up: admin API key Runtime detail internal id
  - User noticed an extra trailing string in `web_admin /api-keys` Runtime detail after Naver/OpenAI status counts.
  - Root cause: the trailing value was `activeCredentialId`, an internal provider credential UUID, not the API key/secret. `web_admin` appended it in `openAiRuntimeDetail`/`naverRuntimeDetail`.
  - Fix: `web/clipper_web_admin` no longer displays `activeCredentialId` in Runtime detail. API/runtime logic was not changed.
  - Commit: `web/clipper_web_admin` `d7df31e fix(api-keys): hide runtime credential ids`.
  - Verification: RED runtime detail spec failed before fix; focused api-keys component spec -> 13 passed; `npm run build` and `git diff --check` passed.
- Follow-up: web session/device privacy hardening
  - User requested login device implementation, privacy-policy content notes, admin raw IP/device id hiding, later retention/deletion TODOs, and log redaction for token/refresh token/provider key/local paths.
  - Fix:
    - `web/clipper_web_api` web Google callback now creates a `user_sessions` row and issues a `sid` access JWT.
    - web refresh token is kept out of URL/localStorage and sent only as an HttpOnly cookie.
    - `/auth/refresh` supports both desktop body refresh token and web HttpOnly cookie refresh.
    - `/auth/sessions` returns current-session marker and privacy-preserving device metadata (`clientKind`, browser/OS names, masked IP) without refresh hash/IP hash/raw IP.
    - `DELETE /auth/sessions/:id` revokes only another session owned by the current user.
    - user DB migration adds `client_kind`, `browser_name`, `os_name`, `ip_masked`, `ip_hash`.
    - `web/clipper_web_client /app/account` shows real login devices and supports remote logout for non-current sessions.
    - Electron and local NestJS JSON logs redact token, refresh token, provider key shapes, and local absolute paths.
    - Electron auth token-store no longer logs the local auth bundle path.
    - `.codex/design/AUTH_SESSION_LICENSE_PROVIDER_TARGET_DESIGN_2026-07-07.md` now includes privacy-policy draft items, admin raw-value hiding rules, and next-phase retention/deletion TODOs.
  - Next:
    - Decide session/device retention period.
    - Decide deletion/account-withdrawal handling for session/device/security logs.
    - Add credit ledger user/admin views with session/device attribution.
    - Add admin external API usage log view; provider calls remain audit logs, not extra credit billing units.
  - Documentation:
    - Detailed current-state and remaining-phase checklist is in `.codex/design/AUTH_SESSION_LICENSE_PROVIDER_REMAINING_PHASES_2026-07-08.md`.
    - It includes the user-added gaps: charge confirmation UX, operation policy admin, credit ledger history, external API usage log, video-duration pricing, session/device privacy retention/deletion, JWT fallback cleanup, provider credential operation checks, and `/llm/variation` deferral.
