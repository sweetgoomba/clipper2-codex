# Job 상태 모델과 Shortform 렌더 preflight 설계

> 설계 당시 기록이다. 옛 active queue 승계 거부 등 후속 사용자 결정과 구현은 [최신 수정 결과](2026-09-17-archive-refund-fix-result.md)를 우선한다. 아래 미구현·승인 전 표현은 현재 상태가 아니다.

상태: **설계 초안 / 구현·병합 승인 전**

기준일: 2026-09-16 KST

## 확정된 사용자 결정

- `waiting` 아래에 별도 `phase`를 두는 과도기안은 사용하지 않는다.
- `PipelineJobStatus` enum 자체를 `preparing | queued | starting | running | completed | failed | cancelled`로 확장한다.
- Shortform 최종 렌더는 크레딧 확인 전에 서버 preflight를 실행한다.
- preflight 실패 시 편집 화면에 머물며 차감·job 예약·보관함 이동을 하지 않는다.
- 줄별 TTS·미디어 누락이나 손상을 sample 음성, 무음, seed media로 숨기지 않는다.
- URL/paste/prompt는 이미 하나의 workflow를 공유하므로 세 Strategy 클래스로 나누지 않는다. 세 plugin/operation identity는 유지하되 mode mapping은 작은 중앙 descriptor/resolver로 유지한다.

이 결정은 코드 구현 또는 병합 승인이 아니다.

## Job 상태 정본

허용 전이는 다음으로 제한한다.

```text
preparing -> queued -> starting -> running -> completed
     |          |          |          |
     +----------+----------+----------+-> failed | cancelled
```

- `preparing`: persistent job은 생성됐지만 실행 입력/manifest/payload가 완성되지 않음. 실행 queue에는 없어야 한다.
- `queued`: 실행 입력이 완성됐고 in-memory queue에 등록됨.
- `starting`: queue가 claim했고 source/plugin/executor를 준비 중.
- `running`: executor가 실제 작업을 실행 중.
- terminal: `completed | failed | cancelled`.

강제 invariant:

- 새 reserve는 `preparing`으로 저장하고 API도 `preparing`을 반환한다.
- direct enqueue는 처음부터 `queued`로 저장한다.
- `activateReserved`는 payload 영속 저장 후 `preparing -> queued`를 원자적으로 수행하고 그 다음 queue에 등록한다. 실패 시 `queued`로 거짓 저장하지 않는다.
- queue claim만 `queued -> starting`을 수행한다.
- executor 준비 완료 뒤에만 `starting -> running`을 수행한다.
- 신규 코드는 `render_prepare_pending`, `queue.contains()` 또는 `clipper_payload` 존재 여부를 상태 판정의 정본으로 사용하지 않는다.
- `queue.contains()`는 invariant 검증/복구용일 뿐 domain phase 판정값이 아니다.

## 저장 데이터 migration

- job store schema를 v2로 올리되, 옛 개발 빌드의 active queue를 새 빌드에서 이어받지 않는다.
- 기존 terminal `completed | failed | cancelled` 이력은 그대로 보존한다.
- 기존 active `waiting | starting | running`은 과거 `preparing/queued`를 판별하거나 새 보관함의 `failed` 이력으로 변환하지 않고 v2 store에서 제거한다. 사용자 결정상 옛 queue 연속성과 중단 흔적 보존은 모두 지원 대상이 아니다.
- 개발 빌드 업데이트 전 active job 0건을 확인하고, 있으면 기존 빌드에서 완료 또는 취소하도록 rollout precondition을 둔다. 이는 old billing watcher/operation 연결이 메모리에만 있던 작업을 업데이트가 끊어 orphan operation으로 만드는 것을 막기 위한 것이다.
- 신규 snapshot에서는 `render_prepare_pending`을 제거한다. v1 active job 분류에조차 사용할 필요가 없으므로 migration/runtime 모두 이 필드를 읽지 않는다.
- v2 serializer는 params에 남아 있는 옛 `render_prepare_pending` 키를 제거하고 다시 쓰며, 신규 코드와 fixture에서 해당 키를 삭제한다.

## 상태별 동작

### 취소

- `preparing`: 준비용 AbortController로 다운로드/probe/manifest 조립을 중단하고 terminal `cancelled`로 전환한다.
- `queued`: queue에서 제거한 뒤 `cancelled`로 전환한다.
- `starting/running`: executor와 외부 plugin job을 취소한 뒤 `cancelled`로 전환한다.
- 공통 billing finalizer가 각 상태의 operation을 정확히 성공/실패·환급 처리한다.

### 재시도

- 준비 실패는 공통 retry가 feature preparation을 우회해 payload 없는 job을 직접 queue에 넣지 않는다. 새 attempt를 만든 뒤 해당 기능의 preparation callback을 실행한다.
- 유료 작업의 실행 실패도 같은 attempt coordinator를 통과한다. 실패·취소된 원시도는 전액 환급하고, 사용자가 `다시 시도/다시 만들기`를 누르면 현재 설정으로 새 견적과 확인창을 거친 뒤 새 attempt·operation·idempotency key로 다시 차감한다.
- 무료 작업은 billing attempt를 만들지 않지만 동일한 preparation/retry 상태 기계를 사용한다.
- Shortform/Variation/Dance/Dialog가 서로 다른 retry 과금 경로를 갖지 않게 하고, 댓글 오버레이·영상 랭킹도 준비 미완 재시도에서 같은 준비 callback 계약을 사용한다.

### reorder/list/metrics

- reorder는 `queued`에서만 허용한다.
- UI는 `preparing`에 queue 순번을 표시하지 않는다.
- preparation duration과 queue wait duration을 별도로 기록한다.
- timeout도 preparation과 queue wait에 별도 적용한다.

## Shortform 렌더 preflight

### 사용자 흐름

```text
숏폼 생성하기 클릭
-> 현재 편집 내용 저장
-> 서버 preflight
-> 실패: 편집 화면 유지 + 문제 clip/line과 해결 행동 표시
-> 성공: 크레딧 견적/확인
-> Nest startRender 내부에서 authoritative preflight 재확인
-> operation start + job 생성
-> 보관함 이동
```

UI preflight 뒤 파일이 바뀌는 경쟁조건을 막기 위해 `startRender`도 과금 전에 같은 validator를 다시 실행한다.

### 검사 항목과 기대 결과

1. `ttsArtifactId` 누락
   - 모든 비어 있지 않은 narration line에 ID가 있어야 한다.
   - 누락 시 해당 clip/line을 표시하고 렌더를 차단한다.
   - fallback TTS를 생성하거나 연결하지 않는다.
2. TTS 파일 누락
   - owner/project/artifact 관계로 실제 로컬 파일을 resolve하고 존재·읽기 가능 여부를 확인한다.
   - 누락 시 과금·job 생성 전에 차단한다.
3. TTS 파일 손상
   - 단순 파일 존재가 아니라 ffprobe 또는 실제 renderer와 같은 decoder로 유효 오디오·양의 duration을 확인한다.
   - probe 오류를 삼켜 stored duration으로 진행하지 않는다.
4. 대사 수정 뒤 재합성 실패
   - ID 없는 편집 상태를 UI에서 명확히 표시한다.
   - 최종 preflight가 다시 차단한다.
   - 이전 TTS를 새 대사에 재사용하지 않는다.
5. 새/빈 대사 줄
   - 빈 줄은 삭제 또는 입력을 요구하고 렌더 대상에서는 허용하지 않는다.
   - 비어 있지 않은 새 줄은 정상 TTS 생성 전까지 렌더 불가다.
6. media asset/slot 누락
   - 각 clip에 하나 이상의 선택 가능한 asset이 있고 media slot이 전체 clip duration을 연속으로 덮어야 한다.
   - 로컬 파일은 존재·읽기 가능해야 하고 원격 URL은 materialization 가능성을 검사한다.
   - seed image/placeholder로 대체하지 않는다.
7. preflight 뒤 I/O 실패
   - startRender가 과금 전에 authoritative validation을 반복한다.
   - 그 뒤 발생한 예측 불가능한 다운로드/디스크/renderer 실패는 공통 terminal finalizer가 환급한다.

### 오류 계약

구조화된 issue 목록을 반환한다. 최소 code 후보:

- `SHORTFORM_TTS_ID_MISSING`
- `SHORTFORM_TTS_FILE_MISSING`
- `SHORTFORM_TTS_INVALID`
- `SHORTFORM_NARRATION_EMPTY`
- `SHORTFORM_MEDIA_MISSING`
- `SHORTFORM_MEDIA_SLOT_INVALID`
- `SHORTFORM_MEDIA_UNAVAILABLE`

각 issue는 `clipId`, 선택적 `lineId/assetId`, 사용자 메시지와 권장 action을 포함한다.

## 제거/유지 범위

- 제거: per-clip fallback TTS, `CLIPPER_STUDIO_SEED_TTS`, sample TTS assets, silent WAV fallback, 참조 0 `prepareClipTts()`.
- preflight와 함께 제거: seed media/placeholder 대체 경로.
- 그대로 유지: 현재 BGM catalog가 사용하는 실제 MP3와 `legacy-bgm.*` identity. 이름 정리를 위한 rename/migration은 하지 않는다.
- 기능 검증 뒤 판단: seed layout/logo와 recipe provider 의존성. `legacy`라는 이름만으로 template migration을 만들지 않으며, 실제로 필요하면 그대로 유지하고 불필요하다고 입증된 경우에만 producer·consumer를 함께 제거한다.

## 검증 기준

- 위 7개 preflight 항목 각각 API unit/integration test.
- preflight 실패 시 quote/operation start/job reserve/router navigation 호출 0회.
- 정상 preflight 뒤에만 과금 확인창 표시.
- authoritative recheck 실패 시 차감 0회.
- 모든 job transition 허용/거부 table test.
- `preparing`은 queue에 없고 `queued`는 queue에 있다는 invariant test.
- cancel/retry/restart/migration/reorder가 새 enum만으로 올바른 경로를 선택하는 test.
- fallback TTS/media artifact가 정상 Shortform manifest에 0개임을 검증.

## 2026-09-17 전체 reserve 경로 재감사

최신 `origin/dev`에서 `VideoRenderService.reserve()`를 사용하는 기능은 Shortform과 Variation 외에도 댓글 오버레이와 영상 랭킹이 있다. 네 기능 모두 준비 중에는 `render_prepare_pending=true`를 저장하고 준비가 끝나면 `submitReserved()`를 호출한다. 그러나 현재 `RenderJobPreparerRegistry`에 등록되는 구현은 Variation뿐이다.

- Shortform: 준비 미완 실패 후 공통 재시도에서 preparer를 찾지 못한다.
- 댓글 오버레이: source probe 뒤 manifest/payload 제출이 실패해 준비 미완 job이 되면 같은 문제가 생긴다.
- 영상 랭킹: 여러 source 검사·manifest/payload 제출 실패 뒤 같은 문제가 생긴다.
- Variation: 유일하게 자체 preparer가 등록돼 있다.

따라서 status enum 전환과 preparation callback 설계는 네 렌더 경로 전체를 대상으로 한다. Shortform preflight의 TTS/media 완전성 검사는 Shortform 고유 요구지만, `preparing -> queued` 전이·취소·재시도 invariant는 공통 요구다.

## 확정된 재시작 정책

자동 재개에 job 파일 안의 로그인 토큰 추가 저장이 반드시 필요한 것은 아니다. 기존 암호화 로그인 세션이 복원된 뒤 authenticated client가 Nest에 현재 토큰을 다시 제공하고, 그때 recovery를 시작하는 설계도 가능하다. 토큰은 job/billing metadata에 넣지 않는다.

앱 종료 전 job이 로컬 디스크에는 active로 남더라도 실제 in-memory queue는 프로세스와 함께 사라진다. 시작 시 이를 방치하면 화면에는 영원히 대기 중인데 실행되지 않는 ghost job이 된다.

사용자는 현 통합에서 자동 재개하지 않기로 확정했다. 신규 `preparing | queued | starting | running` job은 `failed + JOB_INTERRUPTED_BY_APP_RESTART`로 종결하고, 연결된 operation을 정리한 뒤 사용자 명시적 재시도로 돌아간다. job/billing metadata에 로그인 토큰을 저장하지 않는다.

단, `starting/running`에서 앱이 종료됐을 때 별도 프로세스나 외부 실행이 늦게 성공할 가능성이 있는 경로는 먼저 실제 실행이 중단됐음을 확인하거나 결과 evidence를 대조해야 한다. 결과가 모호한데 즉시 환급하면 성공 결과와 환급이 함께 남을 수 있으므로, 이런 경우는 자동 환급하지 않고 Admin 수동 recovery의 마지막 안전망으로 보낸다. 이 안전조건은 자동 재개를 하지 않는다는 제품 결정과 양립한다.

### v1 job store migration과 compatibility 제거 기준

`render_prepare_pending`은 신규 domain field나 장기 호환 필드로 남기지 않으며, v1 JSON 판별에도 사용하지 않는다. 옛 active queue를 이어받지 않기로 했기 때문에 과거 `waiting`의 내부 단계를 알아낼 필요가 없다.

- TypeScript의 신규 `PipelineJobSnapshot`에는 이 필드가 없다.
- 신규 reserve/activate/retry/cancel 로직은 이 필드를 읽거나 쓰지 않는다.
- v2 JSON serializer는 이 필드를 출력하지 않는다.
- migration은 옛 active `waiting | starting | running`을 재실행하거나 terminal 이력으로 바꾸지 않고 제거한다. 원래 preparing/queued 단계도 보존하지 않는다.
- migration 완료 후 실제 v2 파일에는 옛 필드가 없어야 한다는 테스트를 둔다.
- 출시 전 통제된 개발 데이터 전환이 끝나 v1 직접 업그레이드 지원이 불필요하다고 확정되면 migration reader도 제거한다. 그 전까지는 한 파일의 versioned migrator와 fixture에만 격리한다.
