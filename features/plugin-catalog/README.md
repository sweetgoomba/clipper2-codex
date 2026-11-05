# 요금제별 플러그인과 카탈로그 동기화

[11/03 최종 배지·여섯 저장소 dev 반영 결과](../plugin-catalog/records/2026/11/03-store-plan-badges-dev-merge.md).

현재 기준: **2026-11-03 KST**. [세션 종합](../../records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md).

## W19 구현: 요금제별 허용과 공통 표시/실행

- 관리자 /plans의 단일 관리 모달에서 Free/Basic/Pro/Business 등 전체 등급을 비교한다. 하위 자동 포함 정책은 전역 ON/OFF이고 모달 밖에서도 상태를 표시한다.
- ON 체크는 상위로, 해제는 하위로 전파한다. 잠금 UI는 제거했고 정책 토글/안내는 sticky다. OFF는 독립 선택이다.
- 전역 정책과 허용 목록은 하나의 트랜잭션으로 저장하고 revision 충돌을 검사한다. 새 등급/순위 변경도 같은 정책을 준수한다.
- 회원 웹 `/#price`·`/pricing` 공통4카드의 가격/혜택/허용 플러그인은 실제 API 설정을 사용한다. 요금제별 조합을 화면에 별도 하드코딩하지 않는다.
- 앱의 스토어 표시·설치·준비는 허용하고 실제 권한이 필요한 실행에서 현재 등급/크레딧을 검사한다. Free는 잔액·가입 혜택 만료와 독립한 기본 상태다.
- 변경 이력은 요금제·플러그인의 실제 허용 전후로 표시하며 새 이름 스냅샷/기존 원본 보존을 적용한다.

[일괄 설정·저장 구조·검증](records/2026/11/02-plan-plugin-settings-implementation.md) · [최신 양방향 조작·고정 영역](records/2026/11/03-plan-plugin-bidirectional-selection.md) · [변경 이력 표시](records/2026/11/03-readable-plugin-audit.md). 현재 작업 브랜치 커밋·푸시 및 원격 dev 통합 완료다. 실제 서버 배포 확인은 별도다.

## W18 후속: 전체 목록 동기화와 운영 관리

사용자가 전체 카탈로그 동기화를 이번 세션에서 제외했다. 개발 등록 목록 전송/자동 감지, 관리자 카테고리 CRUD·순서·배정, 스토어 표시 순서, 설정 대기/공개, 전역 긴급 중지는 제품에 구현되지 않았다. 과거 임시 HTTP/PostgreSQL 실험을 제품 배포 자동화 완료로 취급하지 않는다.

사이드바의 카테고리 내부 설치 순서·회원 즐겨찾기 순서는 기존대로 유지한다. 긴급 중지 시 등급별 허용 설정을 보존해야 한다. 구체적인 동기화 정본/배포 절차/실행 중 작업·오프라인/캐시 처리는 재개 시 설계한다.

[W18 작업카드](../../handoff/tasks/plugin-catalog-sync.md) · [논의·보류 이력](records/2026/10/29-admin-store-sync-discussion-and-deferral.md) · [후속 TODO](../../todos/2026-10-29-plugin-catalog-admin-store-sync.md). W19가 구현됐다고 W18 전체가 완료된 것은 아니며, W18이 보류라고 W19까지 미구현인 것도 아니다.
