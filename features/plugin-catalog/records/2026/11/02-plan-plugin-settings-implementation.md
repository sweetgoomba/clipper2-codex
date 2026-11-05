# 요금제별 플러그인 일괄 관리 적용

**현재 체크 조작은 [2026-11-03 양방향 연동](03-plan-plugin-bidirectional-selection.md)으로 변경되었습니다. 아래 잠금 방식은 최초 적용 당시의 기록입니다.**

2026-11-02. 사용자 승인 목업을 실제 관리자와 API에 적용했다.

## 사용자 동작

- 실제 URL: http://localhost:4242/plans
- 요금제 등급 카드의 관리 버튼 하나로 큰 공통 모달을 연다. 기존 등급별 ‘허용 플러그인’ 버튼과 개별 편집 창은 제거했다.
- 관리 버튼 옆에 저장된 ‘하위 플러그인 자동 포함: 켜짐/꺼짐’을 한 번만 표시한다.
- Free부터 업그레이드 순위에 따라 등급을 나란히 비교한다. 추가 등급도 같은 줄에 표시하고 필요하면 가로로 스크롤한다.
- 등급·플러그인 이름과 체크는 실제 catalog API 데이터이다. 별도의 권한 하드코딩은 없다.
- ON: Free를 포함한 하위 등급의 선택은 모든 상위 등급에 포함하고 체크를 잠근다. OFF: 현재 체크를 유지하고 등급별 독립 선택을 허용한다.
- 변경 없음은 저장 비활성화. 저장 시 기존 공통 확인창으로 정책과 등급별 개수를 확인한다. 저장 중 입력·중복 저장·닫기를 막는다.
- 취소/닫기는 저장하지 않는다. 확인창만 취소하면 편집 초안은 유지한다. 서버 오류 시 초안과 오류 사유를 남긴다.
- 다른 관리자가 먼저 변경했다면 오래된 초안의 전체 저장을 거절하고 최신 설정을 다시 불러오도록 안내한다.

## 서버와 저장 구조

- AdminCatalog 응답에 pluginSettings { includeLowerTierPlugins, revision }을 추가했다.
- PUT /admin/catalog/plugin-settings: includeLowerTierPlugins, revision, tiers[{tierId,pluginKeys}]. catalog.read + catalog.write 권한이 필요하다.
- catalog_plugin_settings singleton에 공통 정책과 revision을 저장한다. 해당 정책·전체 등급별 allowlist는 하나의 트랜잭션에서 저장한다.
- PostgreSQL advisory 잠금으로 권한 변경을 직렬화하고, catalog 조회는 공유 잠금으로 정책·목록을 일관되게 읽는다. 일괄 저장 중 등급 추가/순위 변경도 충돌하지 않게 한다.
- 서버는 현재 등급 ID 집합, 중복/누락/알 수 없는 등급, 등록된 플러그인, ON 포함 관계, 최신 revision을 다시 검사한다.
- 기존 개별 권한 API와 등급 순위 변경도 공통 정책을 준수하고 revision을 갱신한다.
- 새 등급은 allowlist로 생성한다. ON이면 하위 선택을 상속하고 OFF면 별도 선택을 시작한다. 하위 포함을 깨는 순위 변경은 거절한다.
- 기존 공개 요금제 카드와 서버 실행 권한 검사는 같은 plan_plugin_entitlements를 읽으므로 OFF 독립 설정도 일치한다.
- 감사 작업 ‘요금제별 플러그인 설정 변경’과 변경 전후 정책·목록을 기록한다.
- 실제 화면과 개발용 목업은 동일한 공통 PlanPluginEditorComponent를 재사용한다.

## 마이그레이션과 데이터 보존

- admin migration: 1793664100000-CatalogPluginSettings.
- 기본 정책은 ON이다. 기존 허용을 삭제하지 않고 필요한 하위 플러그인만 상위 등급에 추가한다. 기존 all 모드는 마이그레이션에서 보존한다.
- 실제 편집 저장은 체크한 현재 목록을 allowlist로 확정한다. 새 플러그인이 등록됐을 때 임의로 자동 허용하는 별도 정책은 추가하지 않았다.
- down은 공통 설정 테이블만 제거하고 이후 운영자가 편집했을 수 있는 허용 목록을 삭제하지 않는다.
- 세션 전용 PostgreSQL15438의 clipper_promo_admin만 백업 후 migration을 적용했다. 백업은 전용 runtime/backups/before-plugin-settings-2026-11-02T141617555Z/admin.dump (0600)이다.
- 실제 브라우저 QA는 확인창·편집 취소까지 진행하여 기존 정책/체크를 변경하지 않았다. 실제 DB 테스트의 임시 설정·추가 등급은 모두 롤백했다.

## 검증 결과

- API 전체: 470 suites / 5,131 tests 통과, 기존 108 tests skip. 권한 경로 목록도 신규 PUT을 포함한다.
- Admin 전체: 2,723 tests 통과. 최종 등급 안내/접근성 ID 변경 후 공통 편집기 3 tests도 재통과했다.
- 실제 PostgreSQL 통합 16 checks: OFF 독립 저장, ON 강제, stale revision 거절, 서버 실행 권한·공개 catalog 일치, 신규 등급 상속, 실패 시 전체 롤백.
- API/Admin build, check:colors, 두 저장소 git diff --check 통과.
- 실제 /plans에서 단일 버튼/공통 배지/서버 목록/체크 잠금/변경 없음/확인창 취소·전체 취소를 확인했다.
- 별도 읽기 전용 코드 리뷰에서 신규 등급 all 충돌, stale 저장, 중첩 배열 DTO, 추가 등급 줄바꿈 4건을 발견·수정하고 재검토했다. 새 중요 문제 없음.

## 로컬 적용

- API4340 PID81887 health 정상. Admin4242 정적 번들 갱신. Client4241·설치형 앱·다른 작업 환경은 재시작/초기화하지 않았다.
- 기존 W19 브랜치 feat/signup-credit-promotion-free-20261102에서 작업했다. 커밋·푸시·원격 배포는 하지 않았다.
- W18 앱 스토어/웹 플러그인 목록 동기화 작업은 계속 별도 후속 범위이다.

[실제 상품 페이지](02-plan-plugin-settings-applied-page.png) · [실제 편집 모달](02-plan-plugin-settings-applied-modal.png)

## 후속 UI 수정: Free 고정 상태와 등급 입력칸 높이

사용자 요청으로 Free의 비활성 토글을 제거하고 공통 상태 칩 ‘항상 활성’로 표시했다. 서버의 Free 필수 정책은 유지한다. 등급 수정 창은 grid의 기본 stretch 때문에 유효일수의 안내 문구 높이까지 옆 순위 입력 테두리가 늘어나던 문제였다. plans__form에 align-items:start를 적용하여 두 테두리의 상단·높이를 맞췄다. 실제 브라우저에서 수정 전 유효일수 약52px/순위 약73px, 수정 후 둘 다 약52px이고 상단도 동일함을 확인했다. 안내 문구는 그대로 남겼다. 상품 화면75 tests·build·check:colors·diff 확인 통과. 관리자4242 번들만 갱신했고 API/DB는 변경하지 않았다.

[Free 항상 활성](02-free-always-active-status.png) · [등급 수정 입력칸 정렬](02-plan-tier-fields-aligned.png)
