# Documentation Structure

이 저장소는 active 기준 문서와 날짜별 기록을 분리한다.

## Rule

- 현재 기준 문서: 날짜 없는 `README.md` 또는 domain `README.md`.
- 날짜별 작업 기록: `records/YYYY/MM/` 아래.
- 다음 세션 인계: `handoff/NEXT.md`.
- 긴 과거 인계문: `handoff/archive/YYYY/MM/`.
- 세션 로그: `records/sessions/YYYY/MM/DD.md`.
- 월별 작업 로그: `records/worklog/YYYY/MM.md`.

## Where To Add New Documents

- 새 Markdown 문서는 기본적으로 이 `.codex` repo 안에만 만든다. 이 규칙은 프로젝트 루트 `/Users/jina/project/adlight`에서 작업할 때도 적용한다.
- Superpowers 등의 `docs/superpowers/specs/`, `docs/superpowers/plans/`는 기본 경로 예시다. 사용자 지정 문서 저장소인 `.codex`와 아래 domain 분류가 우선하며, 이를 위해 루트 `docs/` 아래에 새 설계·계획·병합 기록을 만들지 않는다.
- `clipper_angular`, `clipper_nestjs`, `adlight_python` 같은 코드 repo에는 새 `*.md`
  문서나 작업 계획 문서를 추가하지 않는다. 기존 tracked README류를 수정해야 하는
  명시적 이유가 있을 때만 해당 repo 안에서 수정한다.
- Feature-specific work:
  - `features/<feature>/records/YYYY/MM/`
- Build/runtime work:
  - `operations/<domain>/records/YYYY/MM/`
- Cross-cutting architecture:
  - root `README.ARCHITECTURE.md` 요약 후 필요하면 `design/` 또는 domain records.
- One-session summary:
  - `records/sessions/YYYY/MM/DD.md`

## Migration Rule

기존 문서는 한 번에 모두 옮기지 않는다. 새 domain README를 먼저 만들고, 자주 읽는 문서부터 `git mv`로 이관한다. 다른 저장소나 Git 비관리 경로에서 가져오는 문서는 원본 경로·hash와 새 경로를 이관 기록에 남긴다.

이관할 때는 들어오는 링크와 문서 내부 상대 링크를 함께 바꾸고, 폐기·대체된 계획에는 후속 문서를 연결한다. hash로 봉인한 증거 사본·manifest의 `original_path`·과거 실행 원장은 당시 원본을 유지하고, 별도의 경로 대응표와 새 정본 링크를 제공한다. 다른 worktree의 사본은 해당 브랜치에서 별도로 반영한다.

[2026-10-26 루트 docs 이관: 위치 대응표·보존 범위](records/2026/10/26-root-docs-relocation.md). 사용자 요청으로 제외한 루트 `docs/tips`는 이 이관 대상이 아니다.

이관 후에는 다음을 확인한다.

```bash
git status -sb
rg -n "old/path/or/file.md" .
```

## Ignored Data

`imports/`는 legacy asset과 DB backup 성격이므로 git에서 추적하지 않는다.
