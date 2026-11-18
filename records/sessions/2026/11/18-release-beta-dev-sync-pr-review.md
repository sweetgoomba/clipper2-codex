# 11/18 `release/beta` → `dev` 동기화 PR 6건 검토

2026년 11월 18일(KST). `junjunjunjoon`이 오전 11시 28분에 올린 Clipper 동기화 PR 6건을 검토하고, 발견 사항을 작성자에게 공유했다. 사용자는 이를 참고 의견으로 전달하고 병합 및 수정 여부는 팀원에게 맡기기로 했다. 이 건은 문서와 댓글 공유로 마무리했다.

## 검토 범위와 전달 이력

| PR | 검토한 head |
|---|---|
| [Angular #19](https://github.com/OhMyMetabuzz/clipper_angular/pull/19) | `83c590d8` |
| [Electron #6](https://github.com/OhMyMetabuzz/clipper_electron/pull/6) | `64e852aa` |
| [데스크톱 Nest #20](https://github.com/OhMyMetabuzz/clipper_nestjs/pull/20) | `411515e5` |
| [웹 API #13](https://github.com/OhMyMetabuzz/clipper_web_api/pull/13) | `dd7d08c9` |
| [관리자 웹 #7](https://github.com/OhMyMetabuzz/clipper_web_admin/pull/7) | `b7c9c160` |
| [인프라 #1](https://github.com/OhMyMetabuzz/clipper_infra/pull/1) | `476e0d35` |

- 상세 검토를 `clipper_docs/main`에 직접 커밋하고 푸시했다. 원격 `main`의 `ba9e275` 반영을 확인했다. [팀 공유 문서](https://github.com/OhMyMetabuzz/clipper_docs/blob/ba9e275e837a6e584006eb73e8c55e2839065264/reviews/2026-11-18-release-beta-dev-sync-review.md) · [커밋](https://github.com/OhMyMetabuzz/clipper_docs/commit/ba9e275e837a6e584006eb73e8c55e2839065264)
- 사용자 요청에 따라 Nest #20의 대화 탭에 문서 링크를 포함한 일반 댓글 한 건을 게시했다. [게시한 댓글](https://github.com/OhMyMetabuzz/clipper_nestjs/pull/20#issuecomment-6971111189)

## 발견 사항과 검증

- 데스크톱 리모컨의 계정 전환 시 이전 작업 표시, 비활성 상태의 로컬 작업 재개, 렌더 체크포인트 저장 실패 후 재개 시 중복 과금 위험, 취소 전이 경합을 확인했다. Electron의 Windows 자동 실행과 연결 해제 후 창 복원은 실기기 확인이 필요하다.
- 리모컨이 꺼져 있어도 기존 회원 탈퇴는 새 user DB 테이블을 사용한다. 웹 API 배포 전에 마이그레이션을 적용하고, 관리자 웹은 웹 API 다음에 배포한다. 리모컨 활성화 전에는 운영 웹 API 두 인스턴스 사이의 작업 전달을 검증한다.
- 사무실 인프라의 Colima 신규 설치, JWT 키 마운트, UPS 복전 후 서비스 복구, Caddy 접근 로그를 검토했다. Git 이력에 남은 모니터 Slack 웹훅은 폐기·교체 대상으로 기록했다.
- 검토 시점에 6개 PR 모두 열려 있었고 머지 시뮬레이션은 충돌 없이 끝났다. 앱 5개 빌드, 웹 API 6,805개와 PostgreSQL 회원 탈퇴 46개 테스트, 데스크톱·관리자 웹 관련 460개와 인프라 63개 테스트가 통과했다. 가짜 폰과 렌더 어댑터의 리모컨 E2E는 15/15 통과했다. 실제 과금, S3·FCM, Windows와 사무실 UPS, 운영 다중 인스턴스 검증은 팀 공유 문서에 남겼다.
