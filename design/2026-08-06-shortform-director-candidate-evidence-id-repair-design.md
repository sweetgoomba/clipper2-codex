# Shortform Director 후보 근거 ID 계약 복구 설계

상태: 관련 범위 구현 및 자동화 검증 완료

## 문제

후보 생성용 grounded context에는 사람이 검증한 시장 근거 식별자인
`sourceItemId`와 로컬 추적용 `artifactId`,
`normalizationArtifactId`가 함께 들어간다. 현재 candidate prompt는
`candidates[].evidenceIds`가 어느 필드를 사용해야 하는지 명시하지 않는다.

실패 실행 `run.director.d844e75c1ba949f88fb520cf658b4eec`에서는 세 번의
LLM 호출이 모두 정상 응답했지만, 모델이 모든 후보의 `evidenceIds`에
`artifact.director.*`를 넣었다. Desktop validator는 `sourceItemId`만 허용하므로
모든 후보가 `unknown-evidence`로 거절되었고, 세 번의 동일한 재시도 뒤
`SHORTFORM_DIRECTOR_CANDIDATE_GENERATION_FAILED`가 반환되었다.

## 목표

- LLM이 `evidenceIds`에 `marketEvidence[].sourceItemId`만 쓰도록 입력과
  prompt 계약을 일치시킨다.
- 로컬 artifact lineage는 삭제하지 않고 candidate-generation-input artifact에
  계속 보존한다.
- 검증 실패 뒤 같은 실수를 반복하지 않도록 다음 호출에 제한된 교정 정보를 준다.
- 기존 저장 데이터의 candidate prompt v1·v2는 읽을 수 있게 유지한다.
- 유료 provider 호출 없이 자동화 테스트로 회귀를 검증한다.

## 설계

### 1. 로컬 lineage와 provider 입력을 분리한다

`GroundedCandidateGenerationContextV1`은 로컬 정본이다. 이 객체는 기존처럼
`candidate-generation-input` artifact와 lineage 계산에 사용한다.

provider에 보내는 candidate inference envelope에는 별도 projection을 사용한다.
projection은 근거의 실제 내용과 모델이 출력해도 되는 공개 ID를 유지하고 아래
내부 lineage 필드를 제거한다.

- market evidence: `artifactId`, `normalizationArtifactId`
- audience signal: `artifactId`, `sourceArtifactIds`,
  `sourceComments[].artifactId`
- reference pattern: `artifactId`, `analysisSources[].artifactId`,
  `analysisSources[].runId`

`sourceItemId`, audience signal `id`, reference pattern `id`, 설명·요약·지표·
분석 내용은 유지한다. 따라서 모델은 근거를 읽을 수 있지만 내부 artifact ID를
정답으로 착각할 수 없다.

### 2. candidate prompt를 v3로 올린다

Web API candidate prompt는 다음 매핑을 명시한다.

- `candidates[].evidenceIds`:
  `groundedContext.marketEvidence[].sourceItemId`만 허용
- `candidates[].audienceSignalIds`:
  `groundedContext.audienceSignals[].id`만 허용
- `candidates[].referencePatternIds`:
  `groundedContext.referencePatterns[].id`만 허용
- artifact ID, normalization artifact ID, run ID 등 내부 lineage ID 금지
- `correction`이 있으면 허용 ID와 이전 검증 실패 종류를 반영

버전은 `shortform-director.candidate-generation.v3`이다. Desktop runtime
projector는 v3를 현재 계약으로 처리하면서 v1·v2도 읽기 호환한다.

### 3. 재시도에 제한된 교정 정보를 추가한다

첫 호출의 `correction`은 `null`이다. 후보 검증 후 최소 개수를 채우지 못하면
다음 envelope에 아래 정보만 넣는다.

- 고유한 검증 issue 코드
- 허용 가능한 evidence, audience signal, reference pattern ID 목록

거절된 후보의 제목·hook·본문은 다시 보내지 않는다. 이미 통과한 후보만 기존처럼
`existingCandidates`에 포함한다. 교정 정보는 grounded context에서 파생되므로
새로운 외부 데이터나 비밀을 추가하지 않는다.

preflight의 최대 재시도 크기와 비용 추정에는 가능한 모든 검증 issue와 허용 ID
목록을 포함한 envelope를 사용한다. 실제 재시도 입력이 승인 당시 계산한 최대
입력 크기를 넘지 않게 한다.

## 오류 처리

provider 응답 자체가 잘못되었거나 audit digest가 어긋나는 경우의 기존 fail-closed
동작은 유지한다. 세 번의 bounded call 뒤에도 최소 10개를 얻지 못하면 기존
validation failure로 종료한다.

이 수정은 잘못된 artifact ID를 `sourceItemId`로 자동 변환하지 않는다. 서로 다른
ID를 추측해 치환하면 잘못된 근거를 붙일 수 있기 때문이다.

## 테스트

- Web API prompt 테스트로 v3와 정확한 ID 매핑·금지 규칙·correction 규칙을 검증한다.
- Desktop 통합 테스트에서 provider 입력에는 artifact ID가 없고, 로컬 입력
  artifact에는 lineage ID가 남는지 검증한다.
- 첫 응답이 artifact ID를 사용해 `unknown-evidence`가 난 뒤 두 번째 요청에
  교정 정보가 포함되고, 허용 source ID를 사용한 응답이 성공하는 흐름을 검증한다.
- runtime status projector가 candidate v1·v2·v3를 모두 수용하는지 검증한다.
- Desktop은 `npm run build` 뒤 영향 테스트를 `node --test`로 실행한다.

## 범위 밖

- 기존 실패 실행의 자동 재개
- provider 유료 E2E 호출
- 후보 개수 또는 다양성 정책 변경
- validator가 artifact ID를 허용하도록 완화하는 변경
- 사용자 앱 패키징 빌드

## 구현 검증

2026-08-06에 다음 검증을 완료했다.

- Web API Shortform Director inference: 10 suites, 324 tests 통과
- Web API `npm run build` 통과
- Desktop Nest 관련 계약: 70 tests 통과
- Desktop Nest `npm run build` 통과
- `git diff --check` 통과

유료 provider E2E와 사용자 앱 패키징 빌드는 실행하지 않았다.

저장소 전체 회귀는 이 변경과 무관한 기존 fixture 실패 때문에 green이 아니다.
Web API 전체 테스트는 126 suites 중 124 suites, 1,038 tests 중 1,036 tests가
통과했고, 현재 시각에 만료된 2026-08-06 session fixture를 사용하는 auth 테스트
2개가 실패했다. Desktop 전체 테스트에도 기존 shortform-project 인증 fixture,
preview·variation TTS mock, media paging, 기본 TTS preset 관련 실패가 남아 있다.
이 문서의 변경 대상인 candidate generation과 runtime contract 테스트는 모두 통과했다.
