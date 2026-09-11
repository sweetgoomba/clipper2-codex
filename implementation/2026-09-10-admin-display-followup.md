# PG·운영 재확인 및 Admin 표시 수정 후속 기록

2026-09-10. PG/운영 구축 종료문서 이후의 후속 기록. **API9b1b395/Adminfa7e67a의 GitHub 푸시·운영 배포 및 아래 명시된 사용자 화면 확인까지 완료**했다. Customer는b5dc797 유지.

후속 추가 요청: [미사용 상품 정리·이용권 이력 표시](./2026-09-10-admin-catalog-audit-followup.md). 삭제 migration 운영 적용 및 APIa0a78db/Admin597c5b6 커밋·푸시·배포, HTTP/DB와 실제 상품 목록·회원 이력 사용자 확인 완료. 15:23 신규 구독 시작 이력이 있어 수동 테스트 전 현재 권한/잔액 재확인 대기다.

## 이번 대화에서 확인한 운영 상태

- 이번 표시 수정 배포 전 사용자 m4-prod 출력: API ab86b3d / Admin 8980eab / Customer b5dc797, 모두 running/restarts=0. API health HTTP200 및 user/release/admin DB 모두 ok.
- desktop redirect, Windows runner start/snapshot URL 모두 기대값 일치. API에서 runner health HTTP200/ok=true/activeJobId=null.
- API 요청·보고 토큰 존재. 사용자 m4-prod 및 Windows 실행 결과에서 요청 토큰 해시와 보고 토큰 해시 각각 일치. 토큰 원문은 출력/기록하지 않았다. 실행 프로세스에 대한 실제 빌드 인증 검증은 하지 않았다.
- API CLIPPER_PG_RENEWAL_FAILURE_* 변수 0개. m4-prod /tmp/clipper-pg-a12-failure.override.json 및 a13 파일은 존재하며 삭제/재적용하지 않았다.
- 사용자 Customer 확인: 결제내역 링크 이동, 결제 환불 회수 필터, 필터 초기화 모두 성공. 좁은 화면의 표시·필터 조작·표 스크롤도 가능. 잔액4800=무료체험400+추가충전4400 유지.

## 표시 수정과 푸시

사용자가 표시 문제 추가 점검 후 작업 단위별 커밋·일괄 푸시·배포 순서에 동의했다. 이전 통합 디렉터리 `/private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn`의 별도 API/Admin checkout에서 수정했다.

- API 6849d4f: 과거 추가구매400/1000/4000 Credits 사유의 displayName만 현재 한글 상품명으로 변환. 원장 reason/금액/결제연결 보존, 사용자 지정 문구 보존.
- API **9b1b3956672cac4a5272a30ad80334f86ad8d5bd**: AdminAccessCredit.access는 기존 EffectiveAccess 유지. 현재/예정 구독·관리자 지급기록을 nullable accessGrant 필드로 추가하고 OpenAPI 동기화. DB migration 없음.
- Admin **fa7e67a654c4570bd0a44c460b58cc2dc99cc8fc**: 잘못된 access 타입/사용 수정, 무료체험을 포함한 현재 유효 권한과 관리용 지급기록 구분. 관리 요청에 실제 지급기록 ID 사용. 종료/취소/중단 구독의 예약표시 숨김, 현재 구독 월 종료는 해당 없음. 관리자 사유 미기록을 결제 구독으로 표시하지 않음. mock도 실제 계약과 일치시킴.
- 두 저장소 모두 GitHub `release/pg-expiry-20260910`으로 일반 fast-forward 푸시 및 ls-remote 확인. 기존 통합·PG 커밋 보존.
- 최초 API push에서 임시 clone origin이 원본 로컬 repo여서 로컬 release 포인터가 이동했다. 즉시 compare-and-swap update-ref로 원래923c9cb로 복원하고, 명시적 GitHub URL로 정상 푸시했다. 원본 checkout/index/작업파일은 변경하지 않았다. 임시 clone origin은 로컬 경로이므로 다음 푸시도 대상 확인 필수.

## 검증과 한계

- 변경 전 테스트 통과, 회귀 테스트의 표시 누락/잘못된 예약 및 무료체험 표시 실패 확인 후 수정.
- 최종 API 전체2493통과/16skip, Admin 전체399통과. API 빌드 및 Admin prod 빌드 통과. Admin 초기번들567.14kB/500kB 경고 유지.
- API 전체 테스트 첫 실행은 샌드박스 listen EPERM으로 실패; 로컬 포트 허용 후 동일 전체 테스트 통과. Admin 빌드 첫 실행도 출력 없이134 종료 후 권한 재실행 통과.
- Angular ChromeHeadless 렌더·서비스·mock 테스트 통과. 배포 후 운영 사용자 확인은 아래 범위까지 완료.
- 현재 구독 월 종료 null은 종료 구독에 현재 혜택기간이 없어서 생기는 값이다. 실제 구독 종료시각을 추정하여 표시하거나 감사이력을 새로 만들지 않았다.

## 사용자 실행으로 확인한 후속 배포·화면 결과

- m4-prod build-only: API9b1b395/Adminfa7e67a image revision 일치.
- API start-only 후9b1b395/running/restarts0, HTTP200/status ok, user/release/admin DB 모두ok.
- Admin start-only 후fa7e67a/running/restarts0, 공개 HTTPS HTTP200. DB migration 및 Customer 재배포 없음.
- Customer: 사용자가 과거400 Credits 사유의 한글 표시와 잔액4800=무료400+추가4400 확인 항목에 확인 완료 응답.
- Admin 메타버즈 회원 상세 사용자 텍스트: Basic연간/취소/현재 구독 월 종료 해당 없음/다음 결제 중단됨/환불 완료. 해지 예약 및 예약 요금제 변경 항목 없음.
- 같은 화면: 현재 유효 권한 Trial·무료 체험, 관리할 구독·관리자 이용권이 없습니다. 관리자 이용권 지급 버튼 표시. 새 지급·결제·환불 실행 없음.
- 이 사용자 확인은 취소된 기존 TEST 구독과 무료체험 화면 범위다. 종료/중단 상태 및 예약 관리자 이용권의 모든 운영 시나리오를 확인한 것으로 확대하지 않는다.

## 다음 단계와 보류

1. 이번9b1b395 재배포 후 redirect/runner/token 설정과 실패주입 제거의 추가 재조회는 아직 하지 않음. 위 설정 확인은ab86b3d 배포 상태에서 수행한 결과다.
2. 연간 월간탭/갱신 실패문구, 남은 PG 예외·동시성·자연기간 검증은 별도 미완료. 환불 상세 자동이동은 다음 필요한 TEST환불 때 확인.
3. 만료원장·종료감사이력 정책 및 임시override파일 정리는 별도 남음. 실제 종료시각 추가 표시 미구현.
4. Build5 QA 대기, 플러그인 검증 보류, Mac 준비중, 개발DB전환·실결제·정식공개 보류 유지.

원본 API8수정+미추적compose, Admin7수정, Customer10수정 및 Infra 공유 변경은 그대로 보존했다. reset/stash/중복커밋 없음. 새 변경을 원본 M표시만 보고 중복 반영하지 말 것.
