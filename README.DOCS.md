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

- Feature-specific work:
  - `features/<feature>/records/YYYY/MM/`
- Build/runtime work:
  - `operations/<domain>/records/YYYY/MM/`
- Cross-cutting architecture:
  - root `README.ARCHITECTURE.md` 요약 후 필요하면 `design/` 또는 domain records.
- One-session summary:
  - `records/sessions/YYYY/MM/DD.md`

## Migration Rule

기존 문서는 한 번에 모두 옮기지 않는다. 새 domain README를 먼저 만들고, 자주 읽는 문서부터 `git mv`로 이관한다.

이관 후에는 다음을 확인한다.

```bash
git status -sb
rg -n "old/path/or/file.md" .
```

## Ignored Data

`imports/`는 legacy asset과 DB backup 성격이므로 git에서 추적하지 않는다.
