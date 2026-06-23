# Git Commit Message Policy

작성일: 2026-06-23

모든 앱 repo와 `.codex` repo의 커밋 메시지는 Conventional Commit 형식을 따른다.

## Required Format

```text
<type>(<scope>): <summary>
```

`scope`가 정말 불필요한 문서/잡무 커밋만 예외적으로 생략할 수 있다.

예:

```text
feat(plugin-runtime): add Python runtime lifecycle policy
fix(template-builder): preserve preview text scale
chore(template-builder): remove legacy template families
docs(handoff): record plugin runtime memory work
test(plugin-runtime): cover idle peer eviction
```

## Allowed Types

- `feat`: 사용자/시스템 기능 추가
- `fix`: 버그 수정
- `refactor`: 동작 의도 변경 없는 구조 개선
- `test`: 테스트 추가/수정
- `docs`: 문서 변경
- `chore`: 빌드, 설정, 의존성, 데이터 정리 등
- `build`: 빌드 시스템 변경
- `ci`: CI 변경
- `perf`: 성능 개선
- `revert`: 이전 커밋 되돌림

## Hard Rules

- 커밋 전 메시지가 이 형식인지 먼저 확인한다.
- `Add ...`, `Remove ...`, `Update ...`, `Fix ...`처럼 type 없는 메시지는 금지한다.
- 원격에 올라간 커밋 메시지를 잘못 작성했으면, 사용자가 허용한 경우에만
  `--force-with-lease`로 안전하게 고친다.
- 앱 코드 repo 변경과 `.codex` 문서 변경은 별도 커밋으로 관리한다.
- 커밋 전에는 해당 변경 범위에 맞는 fresh 검증 명령을 실행하고 결과를 확인한다.
