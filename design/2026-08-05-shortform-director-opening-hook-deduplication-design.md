# Shortform Director Opening Hook Deduplication Design

## Goal

새로 생성하는 스토리보드의 첫 장면에서 선택된 영상 후보의 훅과 이를 바꿔 말한 문장이 연속으로 반복되지 않게 한다.

## Confirmed root cause

`video-plan` LLM은 선택 후보의 `candidate.hook`을 그대로 복사하지 않고 문장부호를 바꾸거나 의미가 비슷한 문장으로 다시 쓸 수 있다.

Desktop compiler는 첫 장면 내레이션에 `candidate.hook`의 정규화된 정확 문자열이 없으면 훅을 앞에 추가한다. 이 검사는 의미 동등성을 판단하지 않으므로 다음 두 입력 모두 최종 결과에서 중복된다.

- 문장부호만 다른 훅
- 같은 질문을 다른 표현으로 바꿔 쓴 훅

첫 화면 text layer도 같은 접두 추가 함수를 사용해 `candidate.hook + 첫 onScreenText` 형태의 어색한 문구를 만들 수 있다.

## Decision

첫 장면의 훅은 후보 선택 결과를 단일 출처로 사용한다.

- 첫 장면 spoken narration은 `candidate.hook`과 정확히 같아야 한다.
- 첫 장면 primary text layer도 `candidate.hook`과 정확히 같아야 한다.
- LLM이 반환한 `scenes[0].narration`이나 첫 `onScreenText`가 훅을 바꿔 말하더라도 컴파일 결과에 덧붙이지 않는다.
- 두 번째 장면부터는 기존 LLM 내레이션과 화면 텍스트를 그대로 사용한다.
- 마지막 CTA 처리와 다른 장면의 required-copy 처리는 이번 변경 범위에 포함하지 않는다.

Web API의 `video-plan` system prompt도 첫 장면의 `scenes[0].narration`을 `candidate.hook`과 정확히 같게 만들고, 훅을 바로 뒤에서 바꿔 말하거나 반복하지 않도록 명시한다. Compiler가 최종 불변식을 보장하고 prompt는 불필요한 출력 낭비를 줄인다.

## Data flow

```text
selected candidate.hook
  ├─ video-plan prompt: scene 0 narration은 이 훅 한 번만
  └─ Desktop compiler
       ├─ narration cue 0 = candidate.hook
       └─ primary text layer 0 = candidate.hook
```

## Compatibility

- 기존 저장 artifact와 완성된 프로젝트는 변경하거나 마이그레이션하지 않는다.
- 새로 생성하거나 다시 생성한 스토리보드부터 적용한다.
- schema와 HTTP API는 바뀌지 않는다.
- prompt template version은 새 동작을 구분하도록 올린다.

## Verification

- 문장부호만 다른 LLM 훅을 입력해도 첫 narration cue가 정확한 후보 훅 한 문장인지 검사한다.
- 의미가 비슷하지만 다른 표현의 LLM 훅을 입력해도 같은 결과인지 검사한다.
- 첫 primary text layer가 후보 훅 뒤에 LLM 텍스트를 붙이지 않는지 검사한다.
- 두 번째 장면 이후 내레이션은 바뀌지 않는지 검사한다.
- Web API prompt가 첫 장면 exact-hook 및 no-restatement 계약을 명시하는지 검사한다.
- 외부 LLM이나 유료 영상 공급자는 호출하지 않는다.
