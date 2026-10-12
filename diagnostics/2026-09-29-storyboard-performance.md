# 스토리보드 원장·성능 근거 (2026-09-29)

## 최신 재감사 — 실제 단계 표본 및 적용 상태

이번 사용자 질문으로 코드/실행 서버/새로 남은 실로그를 재확인했다. [요구별 현재 상태](../implementation/2026-09-29-storyboard-status-audit.md). 아래 기존 조사는 초기 시점의 이력이며 당시의 “단계 비중 미확인”은 이번 단일 표본으로 일부 해소했다. 생성 시간 단축·동일 조건 전후 검증은 여전히 미완료다.

원장 표시 소스는 구현됐고 이번 재검증2 suites19 tests통과. 하지만 localhost3000(PID11863)는 원본 `/Users/jina/project/adlight/web/clipper_web_api`에서 실행 중이고 그 source/dist에는 새 표시 map이 없다. **실행 서버 적용 미완료**다. 최신 테스트 앱은 Web API를 포함하지 않는다.

새 AI 호출 없이 이미 저장된 앱 로그의 allowlisted 시간 필드를 집계했다. 성공 job의2026-09-29 21:08:19~21:12:13 KST 실행 시간은233926ms(약3분54초). 같은 실행 시간대 batch의 단계별 attempt 합은229315ms다. 시간대가 일치하는 단일 표본이고 서로 다른 과거 작업과 전후 비교하지 않았다.

| 단계 | 실행 attempt 수 | 누적 ms | stage attempt 합 중 비중 |
| --- | ---: | ---: | ---: |
| 검색(source) | 12 | 1961 | 0.9% |
| 검색어 계획(실패2회 포함) | 3 | 11272 | 4.9% |
| 트렌드 평가 | 1 | 1542 | 0.7% |
| 초기 조사자료 정규화 | 1 | 16320 | 7.1% |
| 최종 조사자료 정규화 | 1 | 23676 | 10.3% |
| 주제 선정 | 1 | 8709 | 3.8% |
| 시나리오 후보 | 2 | 23385 | 10.2% |
| 본문 구성(editorial) | 4 | 43930 | 19.2% |
| 소재 결정(materials) | 4 | 98520 | 43.0% |

이 표본에서는 소재 결정이 가장 크고 본문 구성·두 정규화 단계가 다음이다. 검색 API12회는1961ms(Trends573, news1262, Datalab124)로 주요 지연이 아니다. 재시도 실제 대기는501+1007=1508ms. 체크포인트 실행(load54/attempts24/reserve348/save1607ms) 및 큐 wait1ms, 문서 save194ms도 관측했다. document save에 내부 load가 포함되고 source fetch는 source stage와 겹치므로 중복 합산하지 않는다.

stage elapsed는 Web API 왕복/응답 검증 포함, provider 자체 추론 시간만을 뜻하지 않는다. job elapsed는 큐 실행 이후이며 사용자 클릭부터 전체 대기 시간을 뜻하지 않는다. 이번 한 건을 전체 생성이나 특정 모델의 평균으로 일반화하지 않는다.

우선 검토 후보는 독립된 스토리보드 각각의 editorial→materials 묶음에 제한 동시성을 주는 것이다. 같은 묶음 안의 두 단계는 receipt/hash를 위해 순차 유지해야 한다. in-flight 취소/재개/checkpoint/완료 수량 정산·중복 비용 보호와 같은 조건 전후 평가를 갖춘 실제 구현은 아직 없다.

이번 감사는 외부 웹 검색 없이 코드·기존 실로그·오프라인 harness를 사용했다. 오프라인 재측정 exit0 및 진행 관련27/27통과. 안전한 집계와 테스트 로그는 `/Users/jina/project/adlight/output/storyboard/2026-09-29/status-audit-*`에 있다. product source변경/서버재시작/DB수정/새유료AI/배포없음.

## 초기 조사 기록

## 범위와 기준

- Web 기준 `31f4482`, Nest 기준 `824a7a9f`; 실제 AI·외부 네트워크·DB 실행 없이 소스, 기존 로그, 오프라인 fixture만 조사했다.
- 원장: `shortform_director.generate` → `shortform_director` 플러그인, operation 표시명 `스토리보드 생성`. 기존 read-time credit 표시 map에 이 operation이 빠져 있어 `작업 크레딧 사용` fallback이 나왔다.
- 수정: 기존 charge reason `operation:shortform_director.generate`와 run join을 사용하여 `스토리보드 생성 · 크레딧 사용/반환`으로 표시한다. 저장 reason, delta, 수량 과금, 부분 환급, 정산 데이터는 그대로다.

## 실제 로컬 로그에서 측정한 것

안전한 필드만 추출했다. 경로: `/Users/jina/Library/Application Support/Clipper Studio Dev/logs/nest.jsonl`. 작업 내용·프로필·프롬프트·키를 읽어 출력하지 않았다.

| UTC 시작 | UTC 완료 | 기록된 elapsedMs | 결과 |
| --- | --- | ---: | --- |
| 2026-09-29 05:58:09.815 | 2026-09-29 06:08:20.378 | 610563 | job.succeeded |
| 2026-09-29 07:09:41.691 | 2026-09-29 07:12:04.119 | 142428 | job.succeeded |

- 첫 작업에는 `discovery:queries`의 `research_query_plan_invalid` 1차 validation 실패 경고가 있다.
- 두 번째 작업에는 같은 validation 실패 경고 1차/2차가 있다. 두 경고 간 실제 간격은 4074ms다. 여기에는 500ms retry wait와 다음 실행/저장 등이 섞여 있어 provider latency로 단정할 수 없다.
- 위 elapsedMs는 queue에서 잡을 실행하기 시작한 뒤의 시간이다. 생성 요청·preflight·과금·queue 대기 전체 사용자 시간과 같지 않다. 성공 이벤트만으로 모든 요청 슬롯이 완성됐다고 단정할 수 없다.
- 기존 성공 stage, 검색, 저장별 duration과 요청/완료 개수가 없다. 두 작업의 총시간 차이를 특정 model·단계·수량으로 설명할 근거가 없다. `Library/Logs/Clipper Studio`와 `Clipper Studio (dev)`의 nest 로그에는 storyboard.stage 사건이 없었다.
- 이전 `output/.../nest-tests.log`의 ms는 테스트/fixture 실행 시간이다. 실공급자 속도 근거로 사용하지 않았다.

## 코드상 순차 경계 (관측된 병목과 구별)

`StoryboardBatchPreflight.prepare`는 profile snapshot/credentials를 이미 병렬로 읽는다. 실행 시 credential preflight를 다시 한다.

`StoryboardBatchDiscovery.discover` 순서:

1. Trends RSS → query-plan → 계획된 Naver 검색을 한 개씩 수행 → trend relevance.
2. 최근 근거가 없으면 broaden query-plan → 추가 검색.
3. initial normalization → grounded follow-up 검색 → 필요할 때 Datalab → final normalization → 근거 checkpoint.

`StoryboardBatchPipeline.run` 순서:

1. discovery → topics (수량 부족/오류가 공유하는 durable 3-call budget).
2. 각 topic의 candidates → 해당 topic의 각 candidate editorial → materials → immutable document 저장.
3. 다음 topic로 진행. 마지막으로 persisted document를 복구·계수하여 서버 수량 정산.

추가 시도 없는 정상 경로의 AI 호출 수는 `4 + 1 + topicCount + 2 × requestedStoryboardCount`다. 예를 들어 3×5면 38회, 5×10이면 110회다. 이는 코드상 호출 수이며 위 실로그의 작업 수량이나 실제 provider 지연 측정값이 아니다. 검색은 최대 10개의 Naver query와 Trends/Datalab 호출이 있고 stage별 retry가 가능하다.

Default 모델은 query/trend/normalization에 `gpt-5.4-nano`, topics/candidates/editorial/materials에 `gpt-5.6-luna`다. Web inference의 HTTP timeout은 180000ms, desktop wrapper의 기본 timeout은 200000ms, source provider의 기본 timeout은 8000ms다. Timeout이 실제 발생했다는 증거는 이번 로그에 없다.

Storage는 stage attempt 예약을 먼저 쓰고, provider 결과를 immutable artifact로 쓴 다음 manifest에 붙인다. 원자적 JSON 갱신과 artifact registry의 직렬 write queue가 있어 storage 비용이 있을 수 있지만 이번 로그로 그 비중을 측정할 수 없다. 성공한 discovery는 full audit의 latencyMs를 checkpoint에 갖지만 production stage는 output만 저장한다. Web audit latencyMs는 provider HTTP/body read 시간을 측정하며 credential/receipt/desktop storage/queue 시간을 포함하지 않는다.

## 새 계측과 오프라인 harness

`storyboard-stage-retry.ts`에 내용 없는 timing 사건을 추가했다:

- `storyboard.stage.succeeded`: batchId/stageKey/attempt/elapsedMs.
- `storyboard.stage.cancelled`: in-flight 요청이 취소로 reject됐을 때 batchId/stageKey/attempt/elapsedMs. 기존 signal.throwIfAborted 전에 기록하며 원래 signal.reason을 그대로 throw한다.
- `storyboard.stage.failed`: 동일 실행 elapsedMs + 기존 allowlist failure/status/code 진단.
- `storyboard.stage.retry_wait`: 계획 waitMs, 실제 elapsedMs, completed/cancelled/failed 상태.
- `storyboard.checkpoint.storage`: load/save/attempts/reserve, execution elapsedMs, 같은 stage queue waitMs, succeeded/failed/aborted 상태.
- `storyboard.document.storage`: load/save, inclusive execution elapsedMs, succeeded/failed/aborted 상태. save에 포함된 nested load는 별도 event라 두 값을 중복 합산하면 안 된다.
- `storyboard.source.fetch` (백엔드 담당자): source kind/stage hash, httpStatus, elapsedMs, succeeded/failed/cancelled 상태. checkpoint 재사용에는 fetch가 발생하지 않아 이 사건을 추가로 내지 않는다.

stage 실행 elapsedMs는 attempt 저장 뒤에 시작한다. Web API 왕복·응답 projection·stage validation을 포함하며 model 추론만의 시간이 아니다. beforeAttempt/checkpoint 저장은 포함하지 않고 추가 storage 사건으로 관측한다. logger 또는 진단 생성 실패는 삼킨다. retry budget, beforeAttempt 저장 순서, 반환 값/원래 error, 취소와 정산 경로를 변경하지 않는다. source stage는 source kind/hash stageKey로 실행 시간이 찍힌다. job queue·정산·provider/server credential/receipt 세부 분해는 후속 실제 구간 계측이 필요하다.

재현: Nest build 뒤 `node scripts/storyboard-stage-timing-benchmark.js`. baseline TS를 git `824a7a9f`에서 메모리로 컴파일하며 외부 요청을 하지 않는다. fake provider 및 fake wait에 수동 clock을 쓰고 실제 retry helper를 전후 실행한다. 11ms attempt 저장, provider 37/23/40ms, wait 500/1000ms + 7ms의 fixture 비용을 사용한다. 이 값들은 실공급자 예측치가 아니다.

| fixture | provider/예약 횟수 전후 | 논리 ms 전후 | 전후 결과 |
| --- | --- | ---: | --- |
| 첫 성공 | 1 / 1 | 51 | success |
| 1회 실패 후 성공 | 2 / 2 | 589 | success |
| 3회 실패 | 3 / 3 | 1667 | failed |
| retry wait 중 취소 | 1 / 1 | 40 | cancelled |
| 2회 예약 후 재개 | 1 / 1 | 51 | success |

5개 fixture 전후 실행에서 위 값과 결과가 모두 일치했다. 1회 실패→성공의 changed 기록은 실패 실행37ms / retry wait507ms(계획500ms) / 성공 실행23ms이며 두 번의 예약11ms는 execution timing 밖이다. 취소 fixture는 wait9ms 뒤 원래 취소 error를 유지했다. 타이밍 추가는 속도 최적화가 아니라 관측 가능성 개선이다. 정상 provider 호출 수와 fixture 논리시간이 동일하다. 실행 raw JSON은 `PERF-BENCHMARK.json`에 저장했다.

Profile list도 baseline/changed의 실제 Service·Lock를 synthetic 저장소 port로 실행했다. 각 profile에 4개 legacy run(2개 document run×2 refs + 2개 project-backed run×1 metadata ref)을 제공했다. 벽시계 latency나 사용자 데이터는 사용하지 않았다.

| profile 개수 | legacy runs.list 전후 | artifacts.readJson 전후 | projects.get 전후 | profile repo.list 전후 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1 → 0 | 6 → 0 | 2 → 0 | 1 → 1 |
| 20 | 20 → 0 | 120 → 0 | 40 → 0 | 1 → 1 |
| 100 | 100 → 0 | 600 → 0 | 200 → 0 | 1 → 1 |

반환 profile 개수는 전후1/20/100으로 동일했다. 20-profile fixture에서 obsolete legacy reads180회, 100-profile fixture에서900회를 제거했다. 백엔드 담당자의 legacy 표시 제거는 이 구간의 I/O 횟수를 줄인다. 파일 크기·디스크 cache·실제 profile/run 수에 따라 지연 효과가 달라져 실사용 ms 개선으로 환산하지 않았다.

Document store 전후 fixture에서는 storage 호출 횟수와 저장 output byte-order SHA-256도 동일했다:

| 시나리오 | get/write/register/find/read (전후 동일) | artifacts/completed (전후 동일) |
| --- | --- | --- |
| 저장·idempotent 재저장·읽기 | 5/1/1/1/2 | 1/1 |
| 취소 후 저장 거부 | 3/0/0/2/0 | 0/0 |
| artifact 저장 후 manifest 중단·읽기 복구 | 3/2/1/2/1 | 1/1 |

성공/복구 모두 저장 output SHA-256 `f2e0e64fe7d67e56c39b97db2c6051d1ee11377c24720db20ea28abce9254574`가 전후 일치했다. retry fixture의 성공 출력 hash도 일치했다. storage timing unit fixture는 load20ms + 뒤에 queued attempts wait20ms/실행7ms, document inclusive save21ms/안쪽 load5ms를 독립 기대값으로 확인했다. 원래 error와 logger 실패를 삼키는 계약은 유지했다. Unit test에서 raw fixture JSON key order와 parser가 정규화한 order의 해시가 달라 처음 한 번 실패했으며, 내용 비교용 assertion은 sorted-key canonical hash로 고쳤다. production parser/storage는 변경하지 않았다.

## 최적화 후보와 보호할 계약

- Trends fetch와 query-plan은 독립 입력이다. Trends relevance와 계획된 news 검색도 독립적이다. 단일 news 목록과 normalized follow-up news/Datalab은 입력 의존성을 확인한 뒤 제한적 병렬화 후보가 된다.
- 다만 `collected.push`가 응답 완료순서에 따라 바뀌면 `naver-X-Y` 근거 ID, normalization 입력, editorial request hash가 바뀔 수 있다. 시작순서대로 결과를 합치고 기존 checkpoint key와 회복 lineage를 보존해야 한다.
- baseline source fetch client는 AbortSignal을 지원하지만 collector의 trends/news/Datalab 메서드가 batch signal을 전달하지 않았다. 백엔드 담당자는 이 메서드의 optional signal을 추가해 batch 호출에만 전달하고 기존 호출자는 그대로 뒀다. desktop 요청 취소가 Web provider까지 끝내는 계약은 현재 inference controller/transport에 없다. 병렬화 전에 이를 검증해야 한다.
- 서로 다른 slot의 editorial→materials chain은 병렬 후보다. 같은 slot의 editorial과 materials는 서버 verified receipt와 editorial hash를 공유하여 반드시 순차다. 같은 slot을 중복 실행하면 서버 receipt 저장 전에 provider 중복 비용이 생길 수 있다.
- 병렬 작업이 남아 있는 상태에서 정산하면 늦게 저장되는 완료 산출물이 환급과 어긋난다. cancellation 후 모든 in-flight 작업이 정리된 다음 durable documents를 복구·계수하고 단 한 번 immutable settlement를 보내는 계약이 필요하다.
- 현재 completed checkpoint/document 재사용은 이미 구현돼 있다. 결과 재생과 retry가 함께 3회 durable budget을 사용한다. 모델 교체나 두 normalization 합치기는 품질·근거·비용 비교 없이 적용하지 않았다.

## 검증 기록

- Web credit-ledger-display RED: 신규 두 테스트가 fallback `작업 크레딧 사용`으로 실패 → 수정 후 16/16 GREEN.
- Web credits/operations/inference: 33 suites, 503 tests GREEN. Web build GREEN.
- 전체 Web unit suite: 277 suites pass / 2 fail / 5 skip, 2959 tests pass / 7 fail / 21 skip. 두 실패 suite를 원래 checkout에서 재실행하여 동일한 기존 7개 실패(43 pass)를 확인했다. 기존 expected registered plugins에 `shortform_director`가 빠져 있으며 이번 read-time 원장 수정과 별개다. 해당 파일은 변경하지 않았다.
  - `ProductCatalogService`: `tierById derives all-mode plugins and preserves allowlist plugins`; `publicCatalog derives every registered plugin for an all-mode tier instead of exposing stale rows`; `adminCatalog derives all-mode plugins while preserving allowlist tiers`; `does not persist a plugin allowlist for an all-mode tier`; `clears persisted plugin rows when a tier changes to all mode`.
  - `EffectiveAccessService.resolve`: `prefers active subscription access over a usable trial`; `prefers active admin_plan access over a usable trial`.
- Nest timing RED: 3개 신규 테스트가 누락된 elapsed/success/wait 진단으로 실패(6/9 pass) → backend 담당자 build exit0 뒤 9/9 GREEN.
- Storage timing RED: 신규2개 테스트가 사건 누락으로 실패(6/8 pass). 최신 build 뒤 retry/checkpoints/document store/settlement/pipeline/실디스크2회 재시작26/26 GREEN. 취소가 완료 문서를 보존하고 추가 stage를 막으며 부분/전체 환급과 서버 확인 계약이 통과했다.
- Offline stage/profile benchmark: exit0, 5개 retry/cancel/restart fixture invariants와1/20/100 profile operation counts 모두 확인. Node v24.3.0, fake clocks/providers, 외부 호출 없음.
- 실제 공급자 stage 속도 비교, 사용자 시작부터 완료까지 queue/전송/저장 분해, 품질/model 변경 비교는 수행하지 않았다.

## 리뷰 후 취소 계측 보완

기존 catch가 timing log보다 먼저 signal.throwIfAborted를 호출하여 in-flight 취소 실행의 elapsed event가 빠졌다. 신규 회귀가 이벤트 없음으로 RED(9/10 pass)를 재현했다. 안전한 `storyboard.stage.cancelled` event 한 줄을 abort throw 앞에 추가했다.

fake 실행25ms / 예약11ms fixture에서 실행 elapsed25ms를 확인했다. signal.reason의 object identity, provider1회·예약1회·retry wait0회, logger 예외가 발생해도 같은 abort reason 유지, provider rejection 내용/abort reason 비노출을 확인했다. 이후 최신 build exit0와 timing/executor/pipeline/settlement/job 취소 통합26/26 GREEN, 해당 diff whitespace check GREEN. 정산/취소 로직과 durable attempt budget은 바꾸지 않았다. shared `.codex`는 수정하지 않았다.

참고: backend 담당자의 이전 coordinated build와 broad suite는874/874 GREEN이었다. 위 취소 계측 보완 뒤에는 요청된 좁은 timing/cancel/settlement 통합 범위26개를 다시 실행했다.
