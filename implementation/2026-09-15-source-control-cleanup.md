# Source Control 실제 정리 완료 — 2026-09-15

사용자가 승인한 정리 4단계 실행 결과. 9월11일 inventory의 폴더 보존/미커밋 현황보다 이 기록을 우선한다. 새 main/integration 통합은 아직 실행하지 않았다.

## 완료

- `.integration-clones/toss-payments-pg-20260903/` 별도 복제본7개 제거. 각 clone의 로컬 브랜치와 HEAD가 최신 원격 운영 브랜치 이력에 포함됨을 확인했다. 미커밋0. Nest 로컬 데이터는 압축 보존했다.
- `.worktrees/production-pg-refresh-20260909/desktop/` 연결 worktree4개 제거. HEAD의 운영 이력 포함과 미커밋0 확인. 원본 브랜치와 원격 브랜치는 삭제하지 않았다.
- 대사 하이라이트5개 worktree의 원격 추적을 같은 이름 `origin/feature/dialog-highlight-overhaul-20260904`로 연결했다. HEAD 불변, 원격과0/0, 미커밋0. origin/dev를 합치지 않았다.
- 밈 worktree는 9568f436/clean으로 그대로다.
- 원본 웹의 24개 tracked 수정파일은 운영에 포함된 checkpoint와 byte 동일함을 재확인했다(Admin7/Client10/API7). API OpenAPI1개는 선언 위치와 displayName 설명 범위만 차이이며 운영본이 system grants까지 더 넓게 설명하므로 운영본을 유지했다.
- 원본 Admin/API는 기존 release/pg-expiry-20260910을 최신 원격으로 전진시켜 전환했다. Client는 기존 integration20260903을 최신 원격으로 전진했다. 새로운 merge commit이나 dev 통합은 없다.
- 원본 tracked 중복 변경은 해소했고, Infra5문서와 API 로컬 compose1은 그대로 남겼다. API .env/.env.local/compose는 전환 전후 해시 동일함을 확인했다.

## 원본8개 최종 상태

| 저장소 | 브랜치 | HEAD | 미커밋 파일 수 |
|---|---|---|---:|
| clipper_infra | integration/toss-payments-pg-20260903 | f948922c | 5 |
| clipper_web_client | integration/toss-payments-pg-20260903 | 4d95a963 | 0 |
| clipper_web_api | release/pg-expiry-20260910 | e0e5b356 | 1 |
| clipper_web_admin | release/pg-expiry-20260910 | cd3a3069 | 0 |
| clipper_angular | integration/toss-payments-pg-20260909 | 7ae7366d | 0 |
| clipper_python | dev | 260751d2 | 0 |
| clipper_nestjs | integration/toss-payments-pg-20260909 | 780128a0 | 0 |
| clipper_electron | integration/toss-payments-pg-20260909 | dd4e9d67 | 0 |

## 보존/남은 작업

- 로컬 백업 `.worktree-archives/2026-09-15-cleanup-preserved.tar.gz`(0600): 정리 전 웹 원본 변경파일·binary diff, 제거한 Nest 작업폴더의 로컬 데이터, 상태와 SHA-256 manifest. 모든 파일을 압축파일에서 다시 읽어 해시 검증. 원격 업로드 안 함.
- CPU/R1~R5 누적50파일은 이번 작업에서 수정하지 않았다. 이전 턴에 임시 Git 메타데이터 손상이 확인됐으므로 향후 별도 clean checkout에서 패치 복구/대조가 필요하다. 실제 ML/Windows 및 Build5 전체QA HOLD 유지.
- 이번 fetch에서 dev가 9월11일 이후 추가 이동했다. 기존 main 병합안의 dev SHA/충돌 예상은 실행 전 갱신해야 한다. 운영 기준 SHA는 이전 감사와 동일했다.
- 이미 사라진 6월 임시 worktree 등록 및 별도 과거 API tmp worktree는 이번 11폴더 제거 범위 밖이며 prune/제거하지 않았다.
- 테스트·빌드·신규 코드 커밋·push·배포·DB 실행 없음. 이번 기록은 미커밋 문서이며 이전 .codex 665f560 푸시 완료와 구분한다.
