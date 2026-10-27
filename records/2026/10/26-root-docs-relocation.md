# 2026-10-26 — 루트 docs 문서의 .codex 이관

2026-10-26 KST. 사용자가 이동 전 조사 결과를 확인한 뒤 `진행해줘`라고 지시해 루트 `docs/merge`와 `docs/superpowers`의 Markdown 6개를 `.codex`로 이관했다. `docs/tips`는 명시적으로 제외했다.

## 이동 경로와 원본 지문

아래 hash는 상태 안내·후속 링크·상대 링크를 수정하기 **전**의 원본 바이트를 나타낸다. 새 정본은 이동 후 탐색을 위한 수정이 있으므로 봉인 사본의 hash와 같아야 하는 파일이 아니다. 파일명은 유지했다.

| 이전 위치 — adlight 루트 기준 | 새 정본 — .codex 기준 | 이동 전 SHA-256 |
|---|---|---|
| `docs/merge/plugin-runtime-isolation-dev-merge-20260703.md` | [operations/env-runtime/records/2026/07/plugin-runtime-isolation-dev-merge-20260703.md](../../../operations/env-runtime/records/2026/07/plugin-runtime-isolation-dev-merge-20260703.md) | `a49a389d2a4d0ba444762bbbd0adc3cf2a8c70a72bc457af4ab9588ff017ed33` |
| `docs/superpowers/plans/2026-08-06-shortform-director-candidate-return-and-storyboard-resume.md` | [features/shortform-director/records/2026/08/2026-08-06-shortform-director-candidate-return-and-storyboard-resume.md](../../../features/shortform-director/records/2026/08/2026-08-06-shortform-director-candidate-return-and-storyboard-resume.md) | `334a894d6c6237ec5240c6410e58abd9ae13243e9a1d635e35a70fbad9010ad4` |
| `docs/superpowers/specs/2026-10-01-person-highlight-mvp-design.md` | [features/highlights/records/2026/10/2026-10-01-person-highlight-mvp-design.md](../../../features/highlights/records/2026/10/2026-10-01-person-highlight-mvp-design.md) | `2a98cd80ea2a04d55d26f4e88694bf40606dddfa376fad91eb37713aebfc8273` |
| `docs/superpowers/specs/2026-10-13-shared-reference-face-matching-design.md` | [features/highlights/records/2026/10/2026-10-13-shared-reference-face-matching-design.md](../../../features/highlights/records/2026/10/2026-10-13-shared-reference-face-matching-design.md) | `74863491f6ccfe0e626eb0a9f2306192b2568a111a6ff174e2a6b7bdd49158d4` |
| `docs/superpowers/plans/2026-10-13-shared-reference-face-matching.md` | [features/highlights/records/2026/10/2026-10-13-shared-reference-face-matching.md](../../../features/highlights/records/2026/10/2026-10-13-shared-reference-face-matching.md) | `6c2e84bbec1d282c861df5d8e29fbd68da519c589e41eea5eaeb3f7b3d9c841e` |
| `docs/superpowers/plans/2026-10-14-isolated-face-candidate-comparison.md` | [features/highlights/records/2026/10/2026-10-14-isolated-face-candidate-comparison.md](../../../features/highlights/records/2026/10/2026-10-14-isolated-face-candidate-comparison.md) | `94b66c0807629457da4f9f2482fd25c3c8253800b0cc6ecd368c70334b253cb0` |

## 생성 원인과 재발 방지

- 파일시스템 기준 루트 `docs`와 `merge`는 2026-07-03 00:35 KST, `superpowers`는 2026-08-06 10:34 KST에 생겼다.
- `.codex/README.DOCS.md`의 새 Markdown 저장 위치 규칙은 2026-06-17 Git 이력 `0c353b7`에도 존재했다.
- 10/13 작업 로그에는 brainstorming의 `docs/superpowers/specs/`와 writing-plans의 `docs/superpowers/plans/` 기본 경로를 읽고 루트에 문서를 생성한 기록이 있다. writing-plans의 사용자 경로 우선 문구도 있었으나 적용하지 않았다.
- 10/14 실행 원장에는 다중 저장소 루트라는 이유로 계획을 Git 루트 밖에 둔 판단이 있다. 별도 문서 저장소 `.codex`를 고려하지 않은 위치 선택이었다.
- 7/3·8/6 문서의 원본 생성 대화는 조사 중 찾지 못했다. 그 두 건의 세부 판단 동기는 확정하지 않았다.
- [문서 규칙](../../../README.DOCS.md)과 [Codex 적용 메모](../../../AGENTS.md)에 사용자 지정 `.codex` 위치와 domain 분류가 스킬 기본 경로보다 우선함을 명시했다.

## 수정한 참조와 이력 관계

이관 전 현재 `.codex` 문서 9개에 있던 12곳의 참조와 이동 문서 내부 상대 링크 5개를 새 위치로 바꿨다. 현재 문서의 새 참조는 `.codex` 안에서 해석되는 상대 링크를 사용한다. 역사적 코드 예제·실행 작업 디렉터리는 문서 링크 이관을 이유로 재작성하지 않았다.

- [handoff/tasks/person-highlight.md](../../../handoff/tasks/person-highlight.md)
- [implementation/2026-10-20-person-highlight-implementation-plan.md](../../../implementation/2026-10-20-person-highlight-implementation-plan.md)
- [records/sessions/2026/10/01.md](../../sessions/2026/10/01.md)
- [design/2026-10-19-person-highlight-continuity-design.md](../../../design/2026-10-19-person-highlight-continuity-design.md)
- [features/highlights/records/2026/09/30-w14-to-w13-face-contract-handoff.md](../../../features/highlights/records/2026/09/30-w14-to-w13-face-contract-handoff.md)
- [features/highlights/records/2026/09/30-w14-person-highlight-design-proposal.md](../../../features/highlights/records/2026/09/30-w14-person-highlight-design-proposal.md)
- [features/highlights/records/2026/10/13-w14-dance-face-matching-baseline.md](../../../features/highlights/records/2026/10/13-w14-dance-face-matching-baseline.md)
- [features/highlights/records/2026/10/13-w14-shared-reference-matching-implementation.md](../../../features/highlights/records/2026/10/13-w14-shared-reference-matching-implementation.md)
- [features/highlights/records/2026/10/13-w14-shared-reference-matching-plan.md](../../../features/highlights/records/2026/10/13-w14-shared-reference-matching-plan.md)

- 7/3 상세 병합 기록은 1차 이력으로 표시하고 같은 날 `review2` 세션 기록과 양방향으로 연결했다.
- 8/6 계획의 스크롤 복원 철회, 10/1 face-only 가정의 10/19 설계 대체, 10/13·14 계획의 실행 결과와 후속 모델 결정을 연결했다.
- [하이라이트 색인](../../../features/highlights/README.md), [숏폼 디렉터 색인](../../../features/shortform-director/README.md), [런타임 색인](../../../operations/env-runtime/README.md), 루트 README·Records·NEXT를 갱신했다.

## 보존 사본과 옛 링크의 읽는 법

이관 전 파일명을 참조하던 69개 보존/별도 작업 파일은 바이트를 변경하지 않았다.

- `.codex/features/highlights/records/2026/10/evidence/13-w14-shared-reference-matching/`의 관련 6파일: 문서 사본 3개, manifest, archive script, 실행 원장. 설계와 상세 계획 사본 2개는 이동 전 정본과 바이트가 같았다. manifest의 `original_path`, `sha256`은 당시 출처를 뜻한다.
- 얼굴 비교 `evaluation-output`의 문서 사본 56파일.
- 기존 Python worktree의 `.superpowers/sdd` 원장·archive script 3파일.
- 별도 `dance-image-search-notes-20261014/.codex` 작업 공간의 문서 4파일. 해당 브랜치의 이력이며 이번 현재 문서 저장소 수정 범위에 포함하지 않았다.

이 자료의 옛 `docs/` 링크는 위 이동 대응표를 통해 새 정본을 찾는다. 보존본을 현재 경로로 일괄 치환하지 않았으며 루트에 호환 symlink·중복 정본을 남기지 않았다. 당시 archive script는 과거 실행 증거이므로 현재 경로에서 재실행할 도구로 취급하지 않는다. 새 보관 작업은 새 정본 위치를 입력으로 사용한다.

## 검증 결과

- 정본 6개를 새 위치에서 확인했고, 이전 정본 경로와 빈 `merge`·`superpowers` 디렉터리 4개를 제거했다. 루트 `docs`의 일반 하위 폴더는 `tips`만 남았다.
- 변경/추가한 문서 28개의 로컬 Markdown 링크 456곳이 모두 존재하는 경로를 가리켰다. 깨진 링크 0건이며 기존의 무관한 문서를 일괄 수정하지 않았다.
- 옛 정본 경로는 이 대응표와 명시적으로 보존한 자료 외의 현재 `.codex` Markdown에 남아 있지 않음을 확인했다.
- `docs/tips` 파일 5개와 위 보존/별도 작업 파일 69개의 SHA-256이 이동 전과 같았다.
- 증거 manifest의 entries 72개 모두 보관 파일 hash와 일치했다.
- Git 추적 문서의 `git diff --check`가 통과했다. 앱 코드 변경·실행·모델 추론·커밋·푸시는 수행하지 않았다.
