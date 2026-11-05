# 스토어 사용 가능 요금제 배지 및 W19 dev 통합 계획

목표: 현재 사용할 수 없는 플러그인의 카드에 필요한 요금제를 간결하게 표시하고 상세에서 사용 가능 요금제를 안내한 뒤, 승인된 세션 전체 제품 변경을 최신 원격 dev에 통합한다.

설계: 공개 /catalog의 실제 활성 등급/upgradeRank/entitlementMode/pluginKeys를 기존 WebApiClient로 읽어 로컬 Nest의 GET /access/plugin-plans로 최소 투영한다. 서버 계약·실행 허용 판정은 변경하지 않는다. 같은 표시 helper와 배지 컴포넌트를 카드와 모달에서 재사용한다.

표시 규칙: 가능한 등급이 최상위까지 연속일 때만 Pro 이상 등으로 줄인다. 한 등급만 가능하면 Business. Free부터 모두 가능하면 무료 요금제 이상. OFF에서 Basic/Business만 가능하면 두 배지를 각각 표시한다. 카드에는 executionAllowed===false인 경우만 표시하고 모달에는 사용 가능 요금제 항목을 항상 표시한다. 이름/허용 조합은 하드코딩하지 않으며 기존 시맨틱 색 토큰으로 Free/Basic/Pro/Business를 구별한다. 조회 지연/실패/허용 등급 없음도 정확히 구분하고 설치·바로가기 동작은 유지한다.

범위 제외: W18 전체 카탈로그 동기화, 100원 최소 청구 업그레이드 처리, DB 초기화, 다른 세션/원본 checkout 변경. 기존 전용 워크트리와 로컬 테스트 환경 유지. 커밋·푸시·원격 dev 병합은 사용자가 이번 요청으로 승인했다.

- [x] 테스트: 연속/불연속/Free/단일/없음·현재 허용 시 카드 숨김·모달/설치 유지·실제 API 투영/실패.
- [x] 최소 구현: Nest AccessService/Controller, 앱의 표시 모델·조회 서비스·공통 배지·카드/상세/스토어 연결.
- [x] 관련 검사, 여섯 저장소 전체 회귀·빌드와 스타일 검사. 실화면 다크/라이트 확인.
- [x] 코드 리뷰 지적 확인/수정. 비밀값/빌드 산출물/로컬 프로필이 커밋에 섞이지 않는지 확인.
- [x] 각 작업 브랜치 커밋·푸시, 최신 dev와 사전 충돌 검사. 충돌 시 사용자에게 대상/해결 방향 공유.
- [x] 원본 checkout을 건드리지 않고 dev 통합 결과 검증·푸시, 원격 SHA와 조상 관계 확인. 환경/worktree 유지, .codex 병합 기록·WORKBOARD 갱신.

검증 대상: desktop/clipper_angular의 store/helper/service/component spec 및 test:styles, desktop/clipper_nestjs의 access-credit-proxy와 전체 node:test. Web API 전체 Jest/실제 PostgreSQL 통합, 회원·관리자 전체 Karma/build, Electron 전체 node:test/build. Karma는 저장소 간에도 순서대로 실행해 실행 중 Chrome/포트 충돌을 피한다. 로그는 /private/tmp/w19-final-20261103-*에 보존한다.

완료 결과는 [최종 기록](03-store-plan-badges-dev-merge.md)을 따른다. 전체 Nest의 기존 macOS 오류1건은 사용자 지시로 W20 별도 이관했다. 이 예외를 해결/전체 통과로 주장하지 않는다.
