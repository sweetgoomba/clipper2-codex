# 고객 결제 차단 안내·관리자 표 갱신 배포

2026-09-10 사용자 `배포해` 요청에 따른 두 검증 완료 수정의 배포 준비. 이 문서를 이전 미커밋 표기보다 우선한다.

## 배포할 커밋

- Customer aa26eed1b5937fb31dbeb4bb85e8a43f910aa7ff: 이용권 충돌 전용 안내, /my 이동, 카드 등록 버튼 제거 및 재요청 차단. checkout ts/html/spec 3개, 34줄 추가/2줄 삭제. 전체266테스트 및 prod빌드 통과.
- Admin 3747eb0189c071f0fe5f8e9c0b2f4c5268350cfa: 수동 작업 성공 후 getMember 재조회로 상단 크레딧 지급표 갱신. member-detail ts/spec 2개, 43줄 추가/1줄 삭제. 전체401테스트 및 prod빌드 통과(기존 번들 경고).
- 두 커밋은 isolated checkout에서 생성. 원본 공유 미커밋 변경 보존. API/DB 변경 없음. 영문 지급사유 표시 추가 수정은 이번 범위에 포함하지 않음. Build5 QA 대기·플러그인 검증 보류 유지.

## 푸시 상태 — 사용자 명시적 승인 후 완료

- 읽기 전용 ls-remote: Customer integration/toss-payments-pg-20260903=b5dc7976199cc309b25971e56aec84cdd45ac1d9, Admin release/pg-expiry-20260910=597c5b61bbe5e6ef4fe0a1fc21542a73d0e7b5cb. 각각 새 커밋의 직전 기준과 일치.
- 목적지: https://github.com/OhMyMetabuzz/clipper_web_client.git 의 integration/toss-payments-pg-20260903, https://github.com/OhMyMetabuzz/clipper_web_admin.git 의 release/pg-expiry-20260910.
- Customer 일반 push 시도는 실행 전 자동 승인 검토에서 거절. 사유: 배포 요청은 있으나 외부 GitHub 저장소로 사설 소스를 전송하는 목적지/payload에 명시적 승인이 부족함. Admin push는 아직 시도하지 않음. 우회하지 않고 위 두 목적지 및 커밋의 명시적 승인 요청.
- 후속 사용자 `승인함`으로 두 목적지/커밋 푸시·배포 명시 승인. Customer b5dc797→aa26eed 및 Admin597c5b6→3747eb0 일반 push 성공. ls-remote로 각 전체 SHA 일치 확인 완료. 위 거절/미시도 표기는 승인 전 이력이다.
- 운영 빌드/컨테이너 교체 미실행. 마지막 사용자 확인 운영은 API3299a73/Admin597c5b6/Customerb5dc797.
- 다음은 m4-prod 기존 스크립트 admin/web build-only → 이미지 SHA 확인 → start-only/HTTP 확인 → 사용자 UI 확인 순서. 운영 서버 명령은 기존 방식대로 사용자 실행 결과를 받아 확인한다.

## 운영 이미지 빌드 완료 — 컨테이너 교체 대기

- 사용자 m4-prod 출력으로 admin/web build-only 성공 확인. Admin image revision3747eb0189c071f0fe5f8e9c0b2f4c5268350cfa, Customer image revisionaa26eed1b5937fb31dbeb4bb85e8a43f910aa7ff 모두 예상과 일치.
- 두 빌드 모두 애플리케이션/DB 변경 없음 출력 확인. 실행 컨테이너 교체 및 HTTP/UI 확인은 아직 완료하지 않았다.
- 다음은 이미지 SHA 재검증 후 Admin start-only/상태·HTTP 확인 → Customer start-only/상태·HTTP 확인. API/DB 및 Build5 QA·플러그인 보류 유지.

## 운영 컨테이너 교체 완료 — 실제 화면 확인 대기

- 사용자 m4-prod 실행 결과: clipper-web-admin-prod running/restarts0/revision3747eb0189c071f0fe5f8e9c0b2f4c5268350cfa, Admin HTTP200 확인.
- clipper-web-client-prod running/restarts0/revisionaa26eed1b5937fb31dbeb4bb85e8a43f910aa7ff, Customer HTTP200 확인.
- 두 start-only 모두 DB migrations 미실행 출력 확인. API는 이번 배포 대상이 아니며 마지막 확인3299a73 유지. 이번에 API health를 재조회했다고 기록하지 않는다.
- 다음 UI 확인: 한진아 wlsdk318 계정의 관리자 Basic 이용권 보유 상태에서 고객 화면 강력 새로고침 후 /pricing → 월간 Basic → 동의/카드 등록 버튼1회. 전용 이용권 충돌 안내와 /my 링크, 카드 등록 버튼 제거 및 카드창 미열림 확인 대기.
- Admin 자동 갱신 운영 검증은 다음 필요한 관리자 이용권 수동 작업에서 상단 지급표/하단 잔액이 새로고침 없이 일치하는지 확인한다. 완료된 수동 크레딧 지급·회수 테스트를 반복하지 않는다.

## 고객 안내 운영 확인 및 버튼 스타일 후속 — 로컬 수정 완료

- 사용자 `응 확인했어`로 aa26eed 배포 후 이용권 충돌 안내 확인. 추가로 마이페이지 이동 버튼 스타일 이상 및 이 경우 요금 페이지 복귀 링크 숨김 요청.
- Chrome 실제 렌더 회귀 테스트에서 링크 버튼 content-box 폭 계산으로 본문280px일 때320px, 680px일 때720px로 각각40px 넘는 문제 재현. 좌우20px padding이 width100% 바깥에 추가된 원인 확인.
- checkout-action에 box-sizing:border-box 적용. access-conflict 상태에서만 하단 pricing-link를 렌더하지 않도록 변경. 다른 오류 화면의 요금 페이지 링크 유지 검증.
- 기존 테스트에 좁은/넓은 본문 폭 및 링크 노출 조건 검증 추가, 수정 전 실패/수정 후 전체266개 통과. prod빌드 및 git diff --check 통과.
- isolated Customer aa26eed 기반 html/scss/spec 3파일 미커밋·미푸시·미배포. 운영은 Customeraa26eed/Admin3747eb0 유지. 이 후속 스타일 변경은 아직 운영 검증 완료로 계산하지 않는다.

## 버튼 스타일 후속 배포 준비 — GitHub 푸시 완료

- 후속 사용자 `배포해` 요청으로 Customer 8c723c32c1bcacf17860e423950deb9ba11d6c3d 커밋 생성. html/scss/spec 3파일, 15줄 추가/1줄 삭제. 위 미커밋 표기는 이전 이력.
- GitHub OhMyMetabuzz/clipper_web_client의 integration/toss-payments-pg-20260903에 aa26eed→8c723c3 일반 push 성공. ls-remote 전체 SHA 일치 확인.
- 검증한 코드 추가 변경 없음: 전체266테스트/prod빌드 통과 및 diff --check 확인. 원본 공유 미커밋 보존.
- 다음은 m4-prod web build-only/이미지 SHA 확인 → web start-only/HTTP 및 실행 SHA 확인 → 사용자 버튼 폭/복귀 링크 숨김 확인. 이번 후속은 고객 웹만 대상이며 아직 운영 실행 버전은 aa26eed다.

- 사용자 후속 출력: web build-only를 두 번 실행했으며 모두 성공, 이미지 revision8c723c32c1bcacf17860e423950deb9ba11d6c3d 일치. 두 번 모두 애플리케이션/DB 변경 없음. 추가 빌드 불필요, web start-only/실행 상태·HTTP 확인 대기.

## 버튼 스타일 후속 운영 배포 완료 — 화면 확인 대기

- 사용자 start-only 출력: clipper-web-client-prod running/restarts0/revision8c723c32c1bcacf17860e423950deb9ba11d6c3d, Customer HTTP200 확인. DB migrations 미실행 확인.
- 최신 운영 사용자 확인값: Customer8c723c3/Admin3747eb0/API3299a73. 이번에는 Customer만 교체했으며 Admin/API 재조회는 하지 않음.
- 실제 화면 확인은 한진아 계정에서 고객 요금 페이지 강력 새로고침 후 동일 이용권 충돌 안내로 진입하여 마이페이지 버튼 폭 정상 및 요금 페이지 복귀 링크 숨김 확인 대기. Admin 자동 갱신 및 남은 이용권 운영 테스트는 별도 유지.

## 최종 사용자 화면 확인 완료

- 사용자 `확인 완료`로 8c723c3 운영 화면의 마이페이지 이동 버튼 폭 정상 및 요금 페이지 복귀 링크 숨김 확인. 앞서 확인한 이용권 충돌 안내와 함께 이번 Customer 안내·스타일 수정은 구현/테스트/푸시/배포/사용자 화면 확인까지 완료.
- 완료된 결제 안내 및 수동 크레딧 지급·회수 테스트를 반복하지 않는다. Admin 수동 작업 후 상단 자동 갱신 운영 확인, 관리자 이용권 기간·등급 변경·회수 및 사용분 환불 차단 검증은 별도 남음. Build5 QA 대기·플러그인 검증 보류 및 공유 미커밋 보존 유지.
