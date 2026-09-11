# 관리자 크레딧 수동 지급 검증 중 사유 누락 수정

최신 검증: [수동 회수 및 상단 지급표 갱신 누락](./2026-09-10-admin-manual-action-refresh-followup.md). 지급100→회수40→회수60/잔여0/원장순합0/회수버튼 제거·Admin/고객5800 복귀 확인 완료. 상단 자동 갱신 수정은 로컬401테스트/빌드 통과, 미배포. 다음은 별도 TEST 회원의 관리자 이용권 지급.

2026-09-10. [이전 상품·이력 수정](./2026-09-10-admin-catalog-audit-followup.md)은 배포·화면 확인 완료. 이번 사유 누락 수정은 **API3299a73 배포 및 기존 지급분 사유·원장·고객 잔액 실제 화면 확인 완료**다. 마지막 확인된 실행 버전은 API3299a73/Admin597c5b6/Customerb5dc797. 수동 회수·초과회수 차단은 다음 검증이다.

## 사용자 운영 관찰

- 활성 Pro 연간 회원, 지급 전5800=무료400+구독1000+추가4400.
- 사용자 수동 지급 후 2026-09-10 15:48 KST 관리자 조정100/사용0/잔여100/사용 가능, 만료2026-09-11 23:59 확인. 총5900=관리자 조정100+무료400+구독1000+추가4400.
- 구독 지급 행의 연결 주문은819c0785-1c61-40db-998b-d9d69b61226c. 구독 지급1000/잔여1000 유지. 새 주문의 PG/DB 대조 완료를 뜻하지 않는다.
- 관리자 수동 조정 가능 지급분의 사유 칸은 실제 화면도 비어 있다고 사용자 명시 확인. 입력 사유는 테스트 안내에서 `운영 검증 - 관리자 크레딧 수동 지급 100`으로 지정했다. 실제 DB 저장 내용은 아직 별도 조회하지 않았다.
- API3299a73 배포 후 사용자 화면: 기존15:48 관리자 조정100/100 행에 `운영 검증 - 관리자 크레딧 수동 지급 100` 표시 확인. 원장에도 같은 사유로 지급+100/처리 후 잔여100/지급ID307ff59f-9c95-4378-a956-0e61d2b7d96a가1건 표시됨. 재지급 없음.
- 고객 화면 사용자 확인: 총5900=관리자 조정100+무료체험400+정기구독1000+추가충전4400. 사유 조회 수정 및 지급·원장·고객 반영 확인 완료. 사유 미입력 버튼 차단·회수·초과회수 차단은 아직 미확인.
- 사유가 보이면서 과거02:06/01:00 월 지급 행의 원본 `monthly access credit grant` 영문 표시가 노출됨. 후속 표시 한글화 항목으로 기록한다. 감사 원본 변경이나 지금 즉시 재배포는 하지 않았으며 수동 테스트를 먼저 이어간다.

## 원인과 최소 수정

- AdminMemberAccessController.detail의 creditGrants가 CreditGrantsService.grants 고객용 projection을 호출해 reason/operatorId 등 관리자용 필드를 누락했다. Admin 모델/템플릿은 grant.reason을 요구하므로 실제 화면에서 빈칸이 된다.
- 지급 controller→service→repository에는 reason을 저장하고 원장에 기록하는 코드가 있다. 이번 원인 확인은 조회 경로의 재현 증거이며 사용자 실제 행의 reason DB값까지 확인한 것은 아니다.
- adminGrants에서 원본 지급 기록을 페이지 처리하여 관리자 응답에 반환하고, 고객 grants는 기존 필드만 투영하도록 유지했다. 인증 가드는 변경하지 않았다. OpenAPI의 기존 CreditGrant 계약을 사용하고 실제 모델의 기간/환불 nullable 필드4개를 optional로 보완했다.
- 실제 서비스와 관리자 controller를 연결한 회귀 테스트로 저장된 사유가 응답에서 빠지는 실패를 재현한 뒤 수정했다. 관리자 원본 필드 보존과 고객 응답에서 reason/operatorId/idempotencyKey 제외를 함께 확인한다. 지급/회수/DB migration 변경 없음. Admin 프런트 재배포 불필요.

## 검증·커밋·푸시

- 관련4개 suite88개 통과, 전체 API2495개 통과/21skip, build 성공. 기존 opt-in migration 테스트는 이번 실행에서도 skip이며 migration 변경 없음.
- API3299a73e612c26c695a2278953cb3665f8a38ac7, `fix(credits): preserve grant reasons in admin member queries`. 이전부터 사용한 별도 API checkout에서4파일만 커밋, node_modules는 제외. 공유 원본 미커밋 변경 보존.
- 푸시 직전 GitHub release/pg-expiry-20260910은 a0a78db로 기준과 일치함을 확인했다.
- 최초 푸시는 자동 승인 검토가 ‘이전 승인은 앞서 명시한 커밋에 한정되므로 새 payload에 대한 승인이 부족’하다는 이유로 실행 전 거절했다. 사용자에게3299a73과 GitHub 저장소·release 브랜치를 명시하여 승인을 요청했고, ‘진행해’ 응답으로 승인받아 재실행했다. 우회 없음.
- GitHub https://github.com/OhMyMetabuzz/clipper_web_api.git 의 release/pg-expiry-20260910으로 a0a78db→3299a73 일반 푸시 성공. ls-remote 전체 SHA3299a73e612c26c695a2278953cb3665f8a38ac7 일치 확인. 공유 원본에 푸시하지 않았다.
- 사용자 m4-prod build-only 완료 출력 및 이미지 revision3299a73e612c26c695a2278953cb3665f8a38ac7 일치 확인. 이 단계의 앱/DB 변경 없음.
- 사용자 m4-prod start-only 결과 clipper-web-api-prod running/restarts0/revision3299a73e612c26c695a2278953cb3665f8a38ac7, health HTTP200/status ok/user·release·admin DB 모두ok 확인. DB migration 재실행 없음. API 배포 완료.
- 다음은 위 지급ID의 수동 회수 모달에서 사유를 입력한 상태로101 입력 시 확인 비활성화 확인, 이어40으로 변경하여 부분 회수1회 검증이다. 사유 `운영 검증 - 관리자 크레딧 부분 회수 40`, 기대 총5860/관리자 조정60/지급100·잔여60/원장-40·처리후잔여60. 이후 남은60 회수로 기준5800 복귀 예정. 아직 회수 실행 결과는 미확인. 관리자 이용권은 별도 이용권 없는 TEST 회원에서 확인한다. 사용분 환불 차단 및 Build5/플러그인 보류는 유지.
