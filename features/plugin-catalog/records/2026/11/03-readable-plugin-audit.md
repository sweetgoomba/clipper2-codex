# 플러그인 설정 변경 이력의 읽기 쉬운 표시

2026-11-03. 사용자가 /change-history의 플러그인 설정 변경 전후에 tierId/pluginKeys JSON이 출력되는 문제를 수정하도록 요청했다.

## 최종 화면

- 목록은 같은 변경을 한 등급들을 묶어 ‘Free·Basic·Pro: 스토리보드 허용 해제’처럼 요약한다. 변경 그룹이 많으면 일부와 나머지 건수를 표시한다.
- 상세는 변경된 조합만 ‘Free · 스토리보드 | 허용 | 허용 안 함’처럼 한 행씩 보여준다. 변하지 않은14개 허용 목록을 통째로 나열하지 않는다.
- 공통 자동 포함 정책 변경은 ‘하위 플러그인 자동 포함 | 켜짐 | 꺼짐’으로 표시한다.
- 기존 공통 변경 이력 목록과 상세 전후 표를 그대로 재사용한다.

## 원본과 이름 보존

- 기존 audit detail.changes는 그대로 유지하며, 읽기 응답에 displayChanges/displaySummary만 추가한다. 기존 기록의 내용·날짜를 다시 저장하거나 수정하지 않는다.
- 새 플러그인 설정 변경 기록에는 pluginSettingsLabels 스냅샷을 보존한다. 요금제 이름은 저장 트랜잭션에서 확보하고 플러그인 이름은 기존 CATALOG_PLUGIN_PRESENTATION을 재사용한다.
- 새 기록은 이후 이름이 바뀌거나 등급이 삭제돼도 당시 표시 이름을 유지한다.
- 이미 존재한 기록에는 당시 이름이 없으므로 현재 plan_tiers에서 관련 이름을 한 번에 조회한다. 과거 허용 여부는 원본 전후 값에서만 계산한다. 현재 허용 목록으로 이력을 대체하지 않는다.
- 삭제되었거나 확인할 수 없는 이름은 한국어 누락 안내를 사용한다. 표시 표에 UUID/기계 키/JSON을 대체 출력하지 않는다.
- 조회 투영은 admin-audit의 별도 catalog-plugin-audit-presentation 모듈에 모았다. 관련 없는 action과 기존 읽기 권한·운영자 정보 처리는 유지한다.

## 검증

- 기존 API/화면에서 표시 값 누락/JSON 출력 테스트가 실패하는 것을 먼저 확인했다.
- API 관련31 suites/315 tests, 관리자 변경 이력 관련79 tests 통과. API/Admin build, check:colors, 양쪽 diff 검사 통과.
- 이름 스냅샷 보존, 과거 기록 일괄 이름 조회, 삭제된 등급/플러그인, 추가/해제, 정책 변경, 변하지 않은 항목·순서 변경, 다른 action 보존을 확인했다.
- 읽기 전용 코드 리뷰에서 새 중요 문제 없음.
- 실제 세션 DB의 플러그인 변경 기록1건을 조회했으며, 조회 전후 원본 detail의 MD5가 동일함을 확인했다. 쓰기·마이그레이션은 하지 않았다.
- 실제 /change-history의 2026-11-03 01:40:10 기록을 열어 읽기 쉬운18행이 나오고, 표 안에 tierId/pluginKeys/shortform_director/JSON 괄호가 없음을 확인했다.

## 로컬 적용

- API4340 최신 PID37139 health 정상. Admin4242 번들을 갱신했다. Client4241·설치형 앱·다른 작업 환경은 유지했다.
- feat/signup-credit-promotion-free-20261102 작업, 미커밋·미푸시.
- 원본 데이터·허용 설정 변경, DB 초기화, 원격 배포 없음.

[개선된 목록 요약](03-readable-plugin-audit-list.png) · [개선된 상세 전후 표](03-readable-plugin-audit-detail.png)
