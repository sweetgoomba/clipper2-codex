# Next Handoff

최신 갱신: 2026-07-24 KST

이 문서는 다음 세션의 활성 인계만 담는다. 상세 수행 내용은
`../records/sessions/2026/07/24.md`, 이전 설계 맥락은
`../records/sessions/2026/07/21.md`, 과거 전체 인계는
`archive/2026/07/next-handoff-through-2026-07-20.md`에 있다.

## 현재 목표

AI 숏폼 디렉터의 품질 입력 아키텍처 중 실제 market signal인 `V` 축을 어떤 대표
YouTube Shorts corpus로 검증할지 결정한다.

현재 Vira 서비스와 DB는 개발 중이며 소량의 테스트 데이터만 있어 품질 판단 자료로 쓸 수
없다. 다음 세션에서는 production 구현이나 기존 DB 조회를 시작하지 않고, 먼저 corpus
목적·수집 코드 위치·keyword discovery·coverage gate·snapshot 기간을 결정한다.

기존 `shortform_prompt` 플러그인은 수정하지 않는다.

## 먼저 읽을 문서

1. `.codex/AGENTS.md`
2. `.codex/records/sessions/2026/07/24.md`
3. `.codex/design/SHORTFORM_DIRECTOR_VIRA_VALIDATION_CORPUS_OPTIONS_2026-07-24.md`
4. `.codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_VALIDATION_PROTOCOL_2026-07-24.md`
5. `.codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_VALIDATION_EXECUTION_PLAN_2026-07-24.md`

제품 배경과 기존 UI가 필요할 때만 다음을 추가로 읽는다.

- `.codex/records/sessions/2026/07/21.md`
- `.codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_ARCHITECTURE_AND_DIRECTOR_BRIEF_DESIGN_2026-07-21.md`
- `.codex/design/SHORTFORM_DIRECTOR_PERSISTENT_CONTENT_OPERATIONS_AND_VIRA_INTEGRATION_DESIGN_2026-07-21.md`
- `.codex/mockups/shortform-director-content-operations-v2/index.html`
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
- 장기적으로 Vira는 시장 수집·snapshot·성장 관측·상세 분석의 source of truth가 된다.
  현재 서비스와 테스트 DB가 이미 이 역할을 충족한다고 가정하지 않는다.
- Clipper는 Vira 분석 화면을 복제하지 않고 생성에 사용한 evidence snapshot만 보관한다.
- 관측 사실, 공식 사실, 시청자 반응, AI 기획 해석과 가설을 구분한다.
- 입력 단계부터 beat별 visual intent와 asset intent를 기록해 향후 생성형 영상·도식 renderer
  개선으로 연결한다.
- 사용자 직접 입력은 최소화하고 저장 기본값, source 추가, 연결, 추천 확인과 행동 학습을
  우선한다.

2026-07-24 확인한 Vira checkout은
`main@5267ac0bcc6bde9020bd35f67e27dc375d0a00ef`, clean이다. 기존 상세 감사 기준
`2f1d1fdc291c3ccc67d60dc18614fcf41e6e69a4` 이후 새 commit은 이번 세션에서 재감사하지
않았다.

현재 코드에는 yt-dlp 기반 `shorts_*`와 YouTube Data API 기반 `intel_market_*` 두 수집
계열이 있다. 기존 DB는 대표 corpus가 아니므로 조회하지 않는다. 다음 설계가 승인될 때까지
Vira는 read-only이며 branch/worktree도 만들지 않는다.

## 2026-07-24 완료 범위

- 품질 입력 validation protocol과 implementation plan 작성
- 네 사례의 32개 JSON pack materialization과 4/4 seal
- contract, root containment, digest와 atomic sealer
- Vira read-only wrapper와 normalizer의 offline fixture 검증
- security, malformed input, nullable metric과 four-case rollback review 수정
- 전체 offline test `38/38` 통과
- 독립 Task 1~3 spec/quality review 승인
- 실제 Vira DB, psql, YouTube API, yt-dlp와 생성 provider 호출 `0`
- production 코드·목업·DB·API 변경 없음

실제 네 case의 Vira 상태는 모두 `provider_not_called`, evidence 0개다. 이를
`insufficient`로 바꾸지 않는다.

## 다음 작업

1. corpus 목적을 고른다.
   - 광고 제작과 연결되는 업종 중심
   - 한국 YouTube Shorts 전체 트렌드
2. 수집 코드 위치를 고른다.
   - Vira feature branch/worktree + 운영 RDS와 분리된 local experiment Postgres
   - `.codex` 또는 별도 연구 저장소의 독립 collector
3. YouTube API data 보관·표시 범위와 현재 정책 적합성을 확인한다.
4. 분야별 현재 query 후보 생성 방식과 coverage gate를 확정한다.
5. panel 규모와 수집일·1일·3일·7일 snapshot 일정을 확정한다.
6. 승인된 설계를 새 문서로 기록한 뒤 implementation plan을 만든다.
7. 그 뒤에만 Vira branch, local DB, API 수집과 `V` condition matrix를 구현한다.

현재 네 주제는 `P/S/A/R` pack과 평가 fixture로는 사용할 수 있지만 최신 Vira collection
seed로 확정된 것이 아니다. `V` 축은 최근 30일 coverage, 채널 다양성과 반복 snapshot이
있는 주제로 다시 선택한다.

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
| `/Users/jina/project/vira` | `main` | `5267ac0bcc6bde9020bd35f67e27dc375d0a00ef` |
| `.codex` | `main` | 이 NEXT를 포함한 pushed handoff commit |

시작할 때 branch, `git status`, upstream 동기화와 최근 log를 확인한다. 예상 밖 변경은
reset/revert하지 말고 먼저 보고한다. `legacy/adlight_python/fastapi_server.spec`의 기존 변경은
이번 작업과 무관하므로 보존한다.

## 안전 경계

- 기존 `shortform_prompt` 플러그인을 수정하지 않는다.
- 현재 Vira DB를 quality-input evidence source로 조회하지 않는다.
- `/Users/jina/project/vira`는 새 설계와 사용자 승인 전까지 read-only다.
- Vira branch/worktree, migration, local DB, YouTube API, yt-dlp와 provider 호출은 각각
  사용자 승인 전에 실행하지 않는다.
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
- .codex/records/sessions/2026/07/24.md
- .codex/design/SHORTFORM_DIRECTOR_VIRA_VALIDATION_CORPUS_OPTIONS_2026-07-24.md
- .codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_VALIDATION_PROTOCOL_2026-07-24.md
- .codex/design/SHORTFORM_DIRECTOR_QUALITY_INPUT_VALIDATION_EXECUTION_PLAN_2026-07-24.md

먼저 NEXT.md의 기준점에 따라 각 저장소의 branch, git status, upstream 동기화 상태와 최근
log를 확인해줘. 예상 밖 변경은 reset/revert하지 말고 먼저 보고하고,
legacy/adlight_python/fastapi_server.spec의 기존 변경은 보존해.

현재 Vira 서비스와 DB는 개발 중이고 소량의 테스트 데이터만 있으므로 기존 DB를 조회해
품질을 판단하지 마. 기존 네 주제도 Vira collection seed로 확정하지 마.

Superpowers brainstorming으로 먼저 다음 설계를 이어가줘.

1. 광고 제작 업종 중심 corpus와 한국 Shorts 전체 트렌드 corpus의 trade-off
2. Vira feature branch + 격리 local DB와 독립 collector의 trade-off
3. 현재 keyword 후보 발굴, coverage gate, panel 규모와 반복 snapshot 기간
4. YouTube Data API를 기본으로 하고 yt-dlp를 제한적으로 사용할 경계
5. V 축 준비 전 P/S/A/R/F 실험을 어디까지 진행할지

한 번에 한 질문씩 확인하고 설계를 승인받기 전에는 구현하지 마. Vira branch/worktree,
DB, API, yt-dlp, provider, migration, 서버·앱 실행도 내가 명시적으로 승인할 때만 해.
커밋·push·PR·배포도 내가 명시적으로 요청할 때만 해.
```
