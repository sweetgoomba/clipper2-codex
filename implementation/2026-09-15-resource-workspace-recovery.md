# CPU·리소스 작업 공간 복구 — 2026-09-15

## 후속: 복구 브랜치 원격 보존 및 워크트리 제거

2026-09-15 사용자 요청에 따라 복구50파일을 4개 저장소에서 커밋·푸시하고 원격 SHA 일치를 확인했다. 미커밋/ignored 파일이 없음을 확인한 뒤 `git worktree remove`로 복구 워크트리4개 및 빈 상위 폴더를 제거했다. 로컬/원격 `recovery/resource-safety-20260915` 브랜치는 유지한다. 통합 브랜치와 원본 작업 공간은 변경하지 않았다. 테스트·빌드·배포 미실행. 아래 복구 폴더 존재 상태는 과거 기록이다.

- clipper_electron: `c7fd58496f38aef4323319a340e63a1ddfe642de`
- clipper_angular: `db719e963f8aa1b1fb515db60a52974d48a3bba6`
- clipper_nestjs: `0aad9ed6dcd06aa2996697a389309327b8f2e1e9`
- clipper_python: `a867a2dbd8f9d43029ac5edd04e5c0fcfe1bcd9b`

상태: 복구 완료, 앱 저장소의 수정은 미커밋·미푸시·미배포. 새 integration 병합은 미실행.

보관 정본: `patches/2026-09-10-windows-owned-process-tree/manifest.json`의 CPU + R1~R4/watchdog/UI + R5 누적 패치. 이전 CPU/안전성 패치를 중복 적용하지 않았다.

공통 복구 브랜치: `recovery/resource-safety-20260915`. 위치: `/Users/jina/project/adlight/.worktrees/resource-safety-recovery-20260915/desktop/`의 형제 저장소4개. 별도 linked worktree이며 원본 작업 파일은 변경하지 않았다.

| 저장소 | 기준 커밋 | 복원 파일 수 |
|---|---|---:|
| clipper_electron | a34a39d510bca51bf8b3e527d433ff9112c686fc | 8 |
| clipper_angular | c8b186770ae6f77294a2a1689226834f05a8944a | 7 |
| clipper_nestjs | 780128a069c38a9df6438cc64d79f7a2e42bc1ea | 30 |
| clipper_python | 260751d2fa5be8a5a9cd8e346c60ba22d1512ed9 | 5 |

검증: 패치4개 SHA-256이 manifest와 일치. 기준 커밋 clean 상태에서 apply --check --whitespace=error 후 적용. 전체 변경 경로가 manifest50파일과 정확히 일치. 기존 임시 작업본50파일과 byte 동일. HEAD는 기준 커밋이며 stage된 파일0. 원본 desktop4개의 branch/HEAD/status/tracked diff 불변 확인.

이번에는 의존성 설치·테스트·빌드·ML 실행을 하지 않았다. 기존 모의검증 기록을 재실행한 것으로 취급하지 않는다. Windows 실기·Build5 전체QA HOLD 유지.

기존 `/private/tmp/clipper-resource-dashboard-review/`의 손상된 Git 메타데이터는 수정/삭제하지 않았다. 앞으로의 통합 기준 작업본은 위 새 경로다. 다음 단계는 최신 dev에 맞춘 병합안 갱신이며 이 복구 자체가 병합 승인이나 배포가 아니다.
