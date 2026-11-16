# 메일 발송 기능 세션 종합 기록·배포 인계

작성일: 2026-11-10, 한국 시간 기준. 대상 대화: 2026-11-06부터 이어진 Clipper 메일 설계·구현·통합·개발 배포 세션.

## 1. 현재 상태 — 이 문서를 우선한다

**API·관리자·고객 웹·인프라 변경은 커밋하고 원격 `dev`에 반영했다. 사용자는 최신 개발서버 배포를 완료했다고 보고했다. 운영 AWS의 SES·SNS·IAM 리소스는 생성했지만, 이번 메일 기능의 운영 배포는 아직 하지 않았다.**

| 구분 | 현재 상태 | 확인 근거와 한계 |
|---|---|---|
| 제품 소스 4개 repo | 로컬 `dev`와 로컬 추적 참조 `origin/dev` 일치, 모두 clean | 문서화 시점 Git 재조회. 실제 푸시는 단계별 결과 파일의 원격 SHA 검증 기록 |
| 개발서버 | 최신 변경 재배포 완료 | 사용자의 마지막 보고. 이번 문서화 중 서버 접속·배포 SHA·health 재조회는 하지 않음 |
| 개발 SES | 전용 키·구성 세트·SNS 연결 후 발송 사용 | 사용자가 전용 키 설정, SNS 확인됨, 테스트·웰컴·구독 결제 메일 수신을 확인 |
| 운영 AWS | 운영용 SES/SNS/IAM 생성 완료 보고 | 사용자 보고. 실제 정책 JSON·구독·환경변수·실행 역할 사용 여부는 미조회 |
| 운영 애플리케이션·DB | 이번 기능 배포·마이그레이션 전 | 기존 서비스가 없다는 뜻이 아니라, 이번 세션의 메일 변경이 아직 운영 미배포라는 뜻 |
| `.codex` 문서 | 이번 종합 기록으로 정리 | 문서 커밋·푸시는 이번 요청에 포함하지 않음 |

이전 문서의 “미커밋”, “19개 후보”, “자동 이벤트 미연결”, “문의·운영자 메일도 SES로 이전”은 각 단계의 과거 상태다. 현재 범위 판단과 다음 운영 준비에는 이 문서와 [현재 메일 색인](../../../README.md)을 사용한다. 아래에 기록한 사용자 실행 작업과 에이전트 실행 작업은 구분한다.

## 2. 확정 범위와 주요 결정의 변화

- 발신자는 최종 **`Clipper <clipper@metabuzz.co.kr>`**. 초기 `contact@metabuzz.co.kr` 발신안은 폐기했다. `strategy@metabuzz.co.kr` 수신 여부 조사는 사용자 지시로 범위에서 제외했다.
- 새 자동 발송은 SES 공통 큐에 연결했다. 기존 홈페이지 문의를 회사에 전달하는 메일과 운영자 초대·비밀번호 재설정은 **Resend를 유지**한다. 초기 로컬 SES 이전 변경은 최신 범위에 맞춰 기존 Resend 연결로 복원했다.
- 탈퇴 완료는 다른 팀원이 구현한 기존 발송 시점을 유지하며 공통 SES 큐에 연결했다. 기존 Resend 탈퇴 경로와 이중 발송하지 않는다.
- 자동 이벤트는 아래 **10개**로 확정했다. 휴면 전환·휴면 해지 2개는 이번 출시에서 제외했다. 연간 갱신 사전 안내, 결제 실패로 구독 종료, 구독 해지 예약 완료도 보내지 않는다.
- 최초 구독·갱신·플랜 변경·충전을 한 이벤트 안의 탭으로 묶던 안은 최종 폐기하고, 각각 독립 이벤트로 분리했다. 별도 “최초 유료 구독 계약 확인”도 추가하지 않는다.
- 앱 소식 기능과 연결하지 않는다. 별도 오픈소스 에디터 도입은 보류했다.
- 수동 메일은 광고/서비스 안내를 구분하는 기반을 구현했으나, **현재 실제 화면의 ‘메일 작성’ 버튼은 새 UI 검토를 위해 비활성화**했다. 임시 저장·즉시/예약·취소 API가 있다는 사실과 운영자가 현재 새 메일을 작성할 수 있다는 것은 구분한다.
- 갱신 실패의 상세 사유를 **대시보드에 추가 표시**하는 작업은 사용자 지시로 보류했다. 자동 메일의 실패 사유는 기존 회원용 코드 변환 문구를 재사용한다.
- 날짜·시간은 한국 시간의 분 단위로 표시한다. 초와 각 값 옆의 반복 `(KST)`는 넣지 않는다.

## 3. 구현한 기능

### 3.1 관리자 메일 발송

- 공통 탭은 **발송 현황 / 자동 발송 설정 / 공통 디자인**이다. 중간의 2탭 설정 허브·발송 전후 분리 안은 최종 적용하지 않았다.
- 기존 앱의 탭·폼·모달·드로어·테마를 재사용한다. 상태명에 SES 같은 공급자 이름을 노출하지 않고 접수/전달 상태를 구분한다.
- 발송 목록에서 수신자별 결과, 제목·본문 미리보기, 취소 가능한 건의 취소, 페이지 이동을 제공한다.
- ‘상세 보기’는 새 페이지 대신 **기존 목록 위 오른쪽 드로어**를 연다. 목록 페이지를 유지하고 닫기·Escape 뒤 목록과 초점을 복구한다. 기존 상세 query URL도 드로어로 호환한다. 닫힌 패널이나 이전 요청의 늦은 응답이 새 상세를 덮지 않도록 처리했다.
- 메뉴를 배포 그룹에서 **고객 그룹의 프로모션 다음**으로 옮겼다. 실제 카테고리 이름은 ‘고객’이며, 기존 회원 관련 항목이 포함된 그룹이다. 권한은 기존 `mail.read`를 유지한다.
- 자동 이벤트 그리드, 오른쪽 제목·본문 편집 패널, 실제 저장·버전 충돌 처리, 예시 미리보기와 조건별 생략 설명을 구현했다. 메타정보 순서는 발송 조건·시점 → 수신 대상 → 자동발송 토글이다.
- 패널 제목·본문 소제목과 placeholder를 보완했다. 별도 ‘새로 고침’ 및 제대로 행 편집이 되지 않던 고정 3행 ‘표 삽입’ 컨트롤을 제거했다. 기존 HTML 표를 포함한 확정 템플릿은 렌더링·미리보기할 수 있다. 외부 편집기 라이브러리는 도입하지 않았다.
- 편집 본문에는 `{{회원명}}`, `{{가입이메일}}` 같은 변수만 넣고 김클리퍼·예시 이메일은 미리보기에서만 치환한다.
- 자동 메일 제목에는 미리보기와 실제 전송 모두 **`[Clipper] `를 정확히 한 번** 붙인다. 이미 붙은 대소문자 혼용·반복 접두사는 정규화하고, 접두사를 포함한 200자 제한과 빈 제목 검증을 유지한다. 기존 대기 건도 발송 시 적용한다. 수동 메일 제목은 이 변경 대상이 아니다.

### 3.2 공통 디자인과 본문

- 기본 로고는 확정 PNG를 API 소스에 포함해 CID 인라인 첨부한다. 기본 너비 212px, 왼쪽 정렬, 상하좌우 여백 24px이다.
- 기본 상단 `#131316`, 하단 `#f2f2f2`, 하단 글자 `#303030`. 크기·정렬·여백·색상·하단 문구와 링크 편집, 저장 후 재조회와 미리보기를 연결했다.
- 불필요한 상단 문구 및 별도 회사명·주소·연락처 입력 블록을 제거하고 하단 문구에 모았다. 기본 하단의 이메일을 자동 mailto 링크로 만들지 않는다.

```text
문의: contact@metabuzz.co.kr · 070-4616-5610
주식회사 메타버즈 · 서울특별시 강남구 역삼로25길 7 · 사업자등록번호 548-88-02172
```

- 미리보기 문서와 iframe의 배경은 흰색이다. 공통 디자인의 “본문 영역입니다.” 샘플 높이 약 182.375px는 실제 메일에 주입하지 않는다. 실제 본문은 내용에 맞는 높이이며, 메일 앱의 다크 모드 표시까지 강제하지 않는다.
- iframe 높이를 내용·이미지 로드·줄바꿈에 맞춰 갱신해 과한 빈 공간을 없앴다.
- 웰컴·구독 결제·갱신·플랜 변경·충전의 ‘고객지원’ 안내는 홈페이지 **문의하기** 링크로 바꿨다. 탈퇴 완료의 기존 확정 문구는 유지했다. 운영 저장 템플릿을 일괄 덮어쓰는 DB 작업은 하지 않았다.
- 홈페이지 문의 접수 안내에는 문의 유형·접수일·답변 이메일 표와 별도 인용 상자로 감싼 문의 내용을 담는다.
- 플랜 변경은 기존 이용권 종료와 새 이용 기간 시작을 안내한다. 지급 크레딧을 ‘추가 지급’, ‘이번 지급’이라고 부르지 않는다.

### 3.3 회원 광고 수신 동의

- 가입 화면의 선택 체크박스는 기본 OFF다. 설명은 해당 선택 영역 바로 아래에만 표시한다.
- 가입 API의 `marketingEmail`을 사용자 DB의 `user_email_preferences`에 저장하고, `user_email_preference_events`에 변경 출처·이력을 남긴다.
- 계정 설정의 조회·변경 API는 같은 저장값을 사용한다. 변경 시 기존 공통 확인 모달을 열고, 확인한 뒤에만 저장한다. 취소·닫기·Escape는 변경하지 않으며 저장 실패 시 기존 값으로 복원한다.
- **기존 회원에게 광고 동의를 자동 부여하지 않는다.** `users` 컬럼 추가가 아니라 별도 설정 테이블이다. 기본값 false, 행이 없으면 미동의로 처리하며 true로 만드는 backfill은 없다.
- 광고는 명시적으로 동의한 발송 가능 회원 전체를 대상으로 한다. 예약 확정 대상 저장 후 실제 발송 전 동의·탈퇴·차단을 재확인한다. 예약 후 신규 가입자는 이미 확정한 수신자 목록에 자동 추가하지 않는다.
- 광고 수신거부 링크와 설정 변경을 연결했다. 필수 서비스 안내는 광고 수신 동의와 구분한다.

### 3.4 발송 큐·작업·결과 수집

- 이벤트별 제목·본문·활성 상태·수정 버전, 공통 디자인, 수신자별 발송 상태와 결과를 저장한다.
- 이벤트 종류와 원본 업무 ID 조합으로 중복 등록을 막는다. 결제/환불 등 관리자 DB의 업무 변경과 큐 등록은 해당 트랜잭션으로 함께 저장한다. 사용자 DB와 관리자 DB가 분산 트랜잭션이라는 뜻은 아니다.
- 메일은 업무 응답 중 외부 SES 전송 완료까지 기다리는 방식이 아니라, 저장된 작업을 발송 워커가 처리한다.
- 편집된 잘못된 메일 내용은 확인 가능한 실패 결과로 기록해 이미 성공한 혜택 지급을 되돌리지 않게 했다. DB 등록 자체가 실패한 경우에는 해당 트랜잭션·기존 업무 복구 흐름이 적용된다.
- 발송 직전 수신 가능 여부와 갱신 실패 통지의 주문·회차·현재 상태·유예 종료 시각을 다시 검사한다. 결제 해결 뒤 낡은 실패 메일을 보내지 않도록 했다.
- 전송 시작 전 장애는 복구하되, 이미 청구/전송을 시작했고 결과가 불명확한 건을 무조건 다시 보내지 않는다. 취소와 처리 완료, 늦은 결과의 경합을 보완했다.
- SNS 서명과 허용 토픽 ARN을 검사하고 구독 확인 요청을 자동 처리한다. SNS의 text/plain JSON도 처리한다. 전달·반송·스팸 신고 결과를 반영하고 영구 반송/신고 주소를 제외한다.
- 탈퇴 메일의 임시 원본 이메일은 기존 24시간 기한을 유지한다. 종료 결과나 기한 도달 시 정리하며, 워커가 꺼져 있어도 개인정보 정리 작업은 별도로 실행한다. 정리 후 피드백 때문에 주소를 다시 저장하지 않는다.
- 문의는 기존 Resend 전달 성공 뒤 접수 안내를 등록한다. 전달 성공 후 큐 등록만 실패하면 저장한 접수 작업으로 복구한다. submission ID·내용 지문으로 재제출을 구분하고, 동일 문의의 회사 전달·접수 안내 중복을 막는다.
- 기존 후보 이벤트 행은 무작정 삭제하지 않고 catalog version으로 구분한다. 확정 기본 템플릿을 사용하다 관리자가 다시 저장하면 현 버전으로 기록한다.

### 3.5 환불·플랜 변경 정책과 결제 관련 UI

- 구독 환불 신청 시 기존 플랜 변경 예약이 있으면 취소될 것을 먼저 알리고, 환불 접수와 예약 취소를 같은 잠금·트랜잭션 안에서 처리한다. 확인창을 연 뒤 예약이 바뀌면 오래된 확인으로 취소하지 않도록 재검증한다.
- 환불 승인 대기 중에는 새 플랜 변경·변경 예약을 API와 고객 화면에서 차단한다. 이미 외부 결제가 진행된 건의 정산·복구를 잘못 막지 않도록 구분했다.
- 추가 크레딧 구매 환불은 구독 플랜 변경을 막지 않는다. 크레딧 사용은 계속 허용하며, 사용하면 환불이 불가능해지는 기존 조건은 유지한다.
- 확정 문구: **“이후 환불 신청을 취소하거나 환불 신청이 승인되지 않더라도, 취소된 플랜 변경 예약은 자동으로 복원되지 않아요.”**
- 어렵고 불필요하다고 지적한 ‘예약 취소는 구독 해지가 아니며 자동 갱신은 유지’ 문단은 제거했다. 접수/회수 안내 문체를 다른 본문과 맞췄고 ‘운영팀’ 표현을 제거했다.
- 관리자 `/product-policies?tab=renewal`은 기존 input·버튼 디자인을 유지하면서 조작을 막았다. 숫자 변경·추가·삭제·유예기간 수정은 불가하며, 입력 색은 기존 디자인을 유지한다.
- 고객 결제 내역 하단의 **‘환불 신청 상태 새로고침’ 버튼만 제거**했다. 30초 자동 갱신, 행별 오류 시 ‘다시 확인’, 신청 후 갱신, ‘더 보기’는 유지한다.
- 별도 결제 장애 조사 채팅의 재시도·구독 종료·대시보드 변경은 뒤에 통합했다. 그 구현의 작성 주체와 검증 범위는 §6에서 구분한다.

## 4. 확정 자동 이벤트 10개와 실제 연결 지점

아래는 메일이 생성되는 업무 시점이다. DB 저장 뒤 별도 발송 작업이 처리하므로 메일 수신 시각과 업무 완료 시각은 같다고 보장하지 않는다. 코드 연결 완료와 실제 모든 업무의 개발서버 E2E 완료도 구분한다.

| ID | 관리자 이벤트명 | 그리드의 발송 조건·시점 | 실제 업무 기준 |
|---|---|---|---|
| welcome | 웰컴 메일 | 회원가입 완료 시 | 신규 회원의 가입 혜택 처리에서 무료체험·가입 프로모션 크레딧 지급 결과가 확정될 때 등록. 로그인 화면 전환 자체를 트리거로 삼지 않음 |
| payment-initial | 구독 결제 | 구독 결제 완료 시 | 실제 결제 승인과 해당 이용권·구독·크레딧 반영이 모두 성공한 결제의 지급 완료 저장 시 등록 |
| payment-renewal | 구독 갱신 | 갱신 결제 완료 시 | 갱신 결제 승인과 갱신 이용 기간·크레딧 반영 완료 시. 별도 결제 완료 메일을 중복 추가하지 않음 |
| payment-upgrade | 플랜 변경 | 플랜 변경 결제 완료 시 | 변경 결제 및 새 플랜 반영 완료 시. 예약만 만들었을 때 보내지 않음 |
| payment-topup | 크레딧 충전 | 크레딧 충전 결제 완료 시 | 충전 결제 승인과 구매 크레딧 지급 완료 시 |
| failure-first | 갱신 결제 실패 안내 | 갱신 결제 첫 실패 시 | 정기 갱신의 첫 예정 결제가 실패해 실패 기록·다음 자동 재시도·유예 종료 상태를 저장할 때. 신규 구매 실패나 수동 재결제 실패는 제외 |
| failure-next | 갱신 결제 실패 최종 안내 | 마지막 자동 재시도 실패 시 | 예정된 자동 재시도를 소모하고 남은 재시도 시각이 없는 실패를 저장할 때. 현재 고정 정책의 마지막 재시도에 해당 |
| inquiry | 문의 접수 안내 | 문의 접수 완료 시 | 기존 Resend 문의 전달이 성공한 뒤 등록. 문의 본문을 포함하며 실패한 전달이나 스팸 방어로 접수하지 않은 요청은 완료로 안내하지 않음 |
| refund | 환불 접수 안내 | 환불 신청 접수 시 | 환불 신청 저장 및 필요한 기존 플랜 변경 예약 취소가 같은 트랜잭션에서 완료될 때 |
| withdrawal | 탈퇴 완료 안내 | 회원 탈퇴 완료 시 | 다른 팀원의 기존 탈퇴 후속 처리 중 메일 발송 단계 유지. 탈퇴/개인정보 정리·로그인 종료의 선행 조건을 유지하고 그 자리에서 SES 큐에 등록 |

탈퇴는 기존 구현처럼 카드 정보 삭제의 재시도가 남아 있더라도 기존 선행 단계가 완료되면 메일 단계로 진행할 수 있다. 모든 외부 후속 작업이 끝나야만 발송한다는 새 조건을 붙이지 않았다.

갱신 정책은 현재 D0 최초 실패 → D+1 재시도 → D+2 마지막 재시도 → D+3 이용 정지다. 예를 들어 11월 9일 14:30 갱신 기준이라면 10일·11일 14:30 재시도, 12일 14:30 정지 예정이다. 실제 스케줄러 처리는 예정 시각 이후 순차 실행된다. 최초 실패와 최종 실패만 통지하고 중간 재시도 실패마다 통지하지 않는다. 마지막 여부를 다음 재시도 존재 여부로 판단하는 연결은 있으나, 정책 변경과 모든 미래 예외를 검증했다는 뜻은 아니다. 사용자 지시로 관리자 정책 수정 UI도 잠갔다.

실패 메일에는 저장된 오류 코드를 기존 회원용 문구로 바꾼 실패 사유, 재시도/정지 예정 시각, 자동 재시도를 기다리지 않고 대시보드에서 직접 결제할 수 있다는 안내를 담는다. `~요` 문체를 맞추려 별도 실패 사유 변환표를 중복 생성하지 않았다.

**제목·본문 전체, 사용 변수, 조건별 생략은 [확정 기본 템플릿 스냅샷](2026-11-10-automatic-mail-template-snapshot.md)에 수록했다.** 기본 소스를 추출한 문서이며 개발/운영 DB에 관리자가 저장한 편집본을 읽어온 결과는 아니다.

결제 4종은 코드에서 실제 paid + 지급 성공 상태만 등록한다. 잔액 부족, 결제 실패, 승인 후 지급 반영 대기 상태에서는 결제 성공 안내를 보내지 않는다. 무료체험·프로모션 미지급, 환불 종류, 탈퇴 시 구독/카드/크레딧/기기 여부에 따른 생략은 스냅샷의 조건과 렌더러가 처리한다. 다음 결제 시각이 없는 경우의 행 생략은 현재 확정 기본 템플릿의 별도 조건으로 구현하지 않았으므로, 과거 제안을 현재 동작으로 해석하지 않는다.

## 5. 환경별 메일 링크 수정

사용자가 개발서버 구독 결제 메일의 ‘결제 내역 확인하기’가 운영으로 열리는 것을 발견했다. 기본 템플릿의 하드코딩 URL이 원인이었다.

- 기존 `WEB_BASE_URL`을 사용해 Clipper 자사 웹 링크의 origin을 해당 발송 환경으로 맞춘다.
- `clipperstudio.ai`, `www.clipperstudio.ai`, `dev.clipperstudio.ai`의 링크만 대상이며 경로·query·hash를 보존한다. 외부 사이트·유사 도메인·mailto·일반 텍스트와 로고 주소는 바꾸지 않는다.
- 새 자동 메일, 저장된 편집 본문, 공통 하단 HTML/링크, 미리보기 및 기존 대기 메일의 실제 전송에도 적용한다.
- 개발은 `https://dev.clipperstudio.ai/my/payment-history`, 운영은 `https://clipperstudio.ai/my/payment-history`, 로컬은 설정한 로컬 웹으로 연결한다.
- 추가 환경변수나 DB 마이그레이션은 없다. 개발/운영 배포 사전 검사는 기존 `WEB_BASE_URL`을 검사한다. 설정이 비어 있으면 원래 href가 유지되므로 올바른 환경변수가 있어야 한다.
- 이미 받은 이메일은 소급 변경되지 않는다. 새로 생성/발송한 메일로 확인해야 한다.

## 6. Git·보존·커밋·병합·푸시 이력

### 6.1 작업 보존과 최신 원격 dev 맞추기

초기 작업은 오래된 로컬 dev의 미커밋 변경이었다. 당시 API는 원격보다 67개, 관리자 21개, 고객 웹 49개, 인프라 15개 커밋 뒤였다. 사용자 승인으로 최신 원격 dev를 맞추기 전에 tracked/untracked 파일, 삭제 정보, 원래 HEAD, patch와 SHA256 manifest를 백업했다.

원본 밖에서 파일별 3-way 대조·통합을 준비하고, 각 로컬 dev를 지정 origin/dev로 fast-forward한 뒤 로컬 작업을 미스테이징 상태로 복원했다. ignored 실제 환경파일·기존 DB는 수정하지 않았다. 최신 탈퇴 방어·환불 권한·계정 탈퇴 진입과 로컬 메일·환불 예약 취소를 함께 보존했다. 검토에서 발견한 탈퇴 회원의 발송 대상 제외 누락도 회귀 테스트 후 수정했다.

이 단계에서는 커밋·푸시하지 않았다. 이후 사용자가 각각 기능 브랜치 커밋 → 통합 테스트 → dev 병합 → dev 푸시를 명시적으로 승인했다. 초반의 금지 지시와 이후 실행 승인을 시점별로 구분한다.

### 6.2 최초 기능 및 메일 통합

네 repo 공통 기능 브랜치: **`feat/mail-delivery-261109`**. 원격 최신 dev에서 테스트한 관리형 워크트리 브랜치: **`integration/mail-delivery-261109`**.

| repo | 메일 기능 최초 커밋 | 원격 기준 dev | 메일 통합 merge 커밋 |
|---|---|---|---|
| API | `548e3cfb5e09b047bce9bcc3d4549c68a94fd540` | `c85fd18cccfb75e8f288ca964fbaf2979adb6b7c` | `e8ddd7b12c3e56c237d05401ce8e182fbcde158b` |
| Admin | `7cbee18d756d9b65a1efa6fb7ed57287ed1b96c2` | `bb2bca7270f565df890cdb8b35cff2cb96f8c62b` | `381533c5d231379de16d2990cec15cbc294ad228` |
| Client | `7d3954dec38371c72bb288bbbff6fdf4b6e2ac47` | `9b7165bd463213f66a35a9d575d1cf32300ff912` | `70c4af7a20182f61a3ef351d52a4f3e718dc2aca` |
| Infra | `66e2b81df5da02a811ac9851396f23dac5a35fad` | `1141985cdc5462f36af9034b28f9bf1b1c04ec22` | `78f5509690cb8d7be9052cad8bc0875403556652` |

위 메일 통합 테스트는 네 저장소 모두 충돌 없이 끝났다.

처음에는 `--no-commit --no-ff`로 병합 테스트만 했고, 추가 승인 뒤 merge 커밋을 만들고 원본 로컬 dev를 fast-forward했다. 당시 원격 푸시는 보류했다. 관리자에만 배포 번들에서 목업/리뷰를 빼는 추가 수정을 통합 merge에 포함했다. 최초 feature 커밋에 그 수정이 이미 있었다고 해석하지 않는다.

### 6.3 다른 결제 채팅과 합친 뒤 dev 푸시

**‘Clipper AWS 갱신 결제 재시도 장애 조사’ 채팅**에서 `integration/payment-operations-20261109`에 결제 변경과 위 메일 merge를 통합·검증했다. 이 세션은 전달받은 검증 트리와 SHA를 확인하고 실제 dev에 fast-forward한 뒤 푸시했다.

| repo | 다른 결제 채팅의 기능 커밋 | 결제+메일 통합 후 dev로 푸시한 커밋 |
|---|---|---|
| API | `400937f695d4b61d07933e27deaf778c3bb00dd8` | `3fda70f5081a52d3cda2a09132f3f72e3c216da9` |
| Admin | `5dd01d1406cf98676ae72b8b36506693b8734996` | `2a65cf763483f748baac088854dd7fbf68b372cd` |
| Client | `625b74c8636295b0a659b83faf99a9dbc12aca06` | `a32f8ef29aefc3c2e4d4f05483cf475775bb50f5` |
| Infra | 별도 결제 기능 변경 없음 | `78f5509690cb8d7be9052cad8bc0875403556652` |

결제 통합 시 충돌 해결과 결합 회귀 테스트는 다른 채팅에서 수행했다. 구독 현재 상태/종료 정보·갱신 생성자/메일 연결·환불/클라이언트 응답 경합을 함께 보존했다. 이 세션에서 결제 장애 조사 자체를 새로 구현했다고 기록하지 않는다. 인프라도 사용자 재지시 뒤 dev 반영·푸시에 포함했다. 이 과정에서 force push나 운영 배포는 하지 않았다.

### 6.4 dev 반영 후 추가 수정

| 작업 브랜치 | repo | 커밋 | 변경 |
|---|---|---|---|
| `fix/ses-dedicated-credentials-261110` | API | `c322d2695b3a4c230e4c3a644ac50a963e732915` | SES 자격 증명을 S3 키와 분리 |
| 같은 이름 | Infra | `50b2038c97afea62bf75603feb33efbbf876c5d8` | compose·환경 예시·기존 dev 런북에 전용 키 전달 |
| `fix/automatic-mail-subject-prefix-261110` | API | `fc904f2c4f169dcf005fa483f4db0bd2f03ce3be` | 자동 메일 `[Clipper] ` 접두사 |
| `fix/mail-activity-detail-panel-261110` | Admin | `97c1cd9d6064e215cee7f6e8e7f94f929811027c` | 발송 상세 드로어·고객 카테고리 이동 |
| `fix/mail-environment-links-261110` | API | `130c81e8e2fd3e7759072be6ba22fb269c5f128b` | WEB_BASE_URL 기반 링크 변환 |
| `fix/remove-refund-status-refresh-button-261110` | Client | `93fb968c038b6d75e57b6028c2e56a1b62498b8e` | 결제 내역 하단 수동 새로고침 버튼 제거 |

위 후속 수정은 검증 후 각각 로컬 dev에 fast-forward하고 `origin/dev`에 푸시했다. 작업/통합 브랜치와 관리형 워크트리는 보존했다. 이 문서화 작업에서는 새 커밋·푸시·병합·태그를 만들지 않았다.

### 6.5 문서화 시점 최종 Git

| repo | 최종 로컬 dev = origin/dev 추적 SHA | 작업 폴더 |
|---|---|---|
| clipper_web_api | `130c81e8e2fd3e7759072be6ba22fb269c5f128b` | dev, clean |
| clipper_web_admin | `97c1cd9d6064e215cee7f6e8e7f94f929811027c` | dev, clean |
| clipper_web_client | `93fb968c038b6d75e57b6028c2e56a1b62498b8e` | dev, clean |
| clipper_infra | `50b2038c97afea62bf75603feb33efbbf876c5d8` | dev, clean |

모든 커밋의 부모·작성 시각·첫 부모 대비 변경 파일 목록과 원본 결과 파일 해시는 [Git/근거 JSON](2026-11-10-mail-session-evidence.json)에 기록했다. `origin/dev` 비교는 이번에 로컬 추적 참조를 읽은 결과이고, 실제 원격 일치 확인은 각 푸시 당시 기록에 있다.

## 7. 배포 번들에서 목업 데이터 제외

최초 관리자 prod 빌드가 1MB 오류 한도를 약 4.88KB 초과했다. 정확한 원격 dev 기준 빌드는 962.21KB로 통과했고, 새 메일 목업을 정적 목록에 연결하며 예시 데이터가 초기 번들로 들어간 것이 원인이었다.

- `angular.json`에서 dev/prod만 mock interceptor와 root routes를 빌드 시 교체한다.
- `mock-api.disabled.ts`는 mock handler/data import 없이 실제 HTTP를 통과시킨다.
- `app.routes.deploy.ts`는 기존 로그인/초대/재설정/포털과 인증 보호를 유지하고 리뷰·샘플을 import하지 않는다.
- local/mock의 리뷰 경로는 유지한다. 단순 지연 로딩만으로 해결한 것이 아니다.
- stats.json에서 mock handler·mock-data·review component가 빠진 것을 확인했다. 파일 치환 때문에 원래 interceptor 경로명이 보여도 실제 내용은 233바이트 대체 코드다.
- 메일 통합 후 799.74KB, 결제 결합 후 799.45KB, 최신 관리자 수정 후 799.44KB로 통과했다. 500KB 경고는 남고 1MB 오류 한도는 넘지 않는다. 고객 웹 최신 prod는 533.53KB로 기존 500KB 경고가 남는다.

## 8. DB 마이그레이션과 개발 배포

| DB | 이번 메일 기능에 포함한 migration |
|---|---|
| user | `1794180000000-CreateEmailPreferences.ts` |
| admin | `1794180000000-CreateManualMail.ts` |
| admin | `1794180100000-CreateMailEventTemplates.ts` |
| admin | `1794180200000-ConnectAutomaticMail.ts` |
| admin | `1794180300000-AutomaticInquiryReceipts.ts` |

DataSource에 등록했다. 가입 동의 설정·변경 이력, 메일 작업/수신자/결과/공통 설정, 이벤트 템플릿 및 자동 연결, 문의 접수 복구 저장이 포함된다. 기존 회원을 광고 동의 ON으로 바꾸지 않는다. 전용 키·제목 접두사·드로어/메뉴·환경 링크·버튼 제거 후속에는 새 migration이 없다.

개발서버의 사용자 실행 경로는 `/Users/metabuzz/Desktop/project/clipper2/clipper_infra`다. 최초 안내는 새 이미지 준비 → API 중지 → user/admin/release의 미적용 migration → 새 서비스 시작 순서였다.

```sh
cd /Users/metabuzz/Desktop/project/clipper2/clipper_infra
./scripts/deploy-dev.sh all --build-only
docker compose --project-name clipper-dev --env-file env/stack.dev.env -f apps/compose.yml -f apps/compose.dev.yml stop api
./scripts/migrate-db.sh dev
./scripts/deploy-dev.sh all --start-only
```

이 코드는 **개발서버에서 사용자가 수행한 배포 흐름 기록**이며 지금 다시 실행하라는 뜻이 아니다. migration 스크립트는 추가 확인 문구 입력을 요구할 수 있다. 초기 복사 명령의 `#` 주석이 interactive zsh에서 명령으로 처리되어 `command not found: #`로 중단됐고, 주석 없는 명령으로 안내를 정정했다. 사용자는 이후 배포 완료를 보고했다.

SES 전용 키 추가 뒤 사용자가 개발 env에 값을 직접 입력하고 API를 재배포했으며 두 항목이 모두 설정됐다고 확인했다. 마지막 링크/버튼 수정까지 다시 배포했다고 보고했다. 에이전트가 원격 서버에 접속해 해당 배포나 영구 DB migration을 실행한 것은 아니다. 실제 배포 이미지 revision·health·각 migration 적용 목록은 이번 문서화에서 별도 조회하지 않았다.

## 9. AWS SES·SNS·IAM와 환경변수

### 9.1 공통 계정·인증·권한

- AWS 계정 `327655937726`, 서울 `ap-northeast-2`.
- 도메인 identity: `arn:aws:ses:ap-northeast-2:327655937726:identity/metabuzz.co.kr`.
- 사용자가 제공한 콘솔에서 도메인 확인됨, Easy DKIM 성공/활성, RSA2048을 확인했다. custom MAIL FROM은 미설정이었다. 이번 기능 때문에 회사 공용 도메인/기존 ViewX 발송 설정을 교체하지 않았다.
- 관리형 정책 `ClipperSesSendEmail`을 `ses:FromAddress=clipper@metabuzz.co.kr`로 수정했다. 사용자가 연결 엔터티 `clipper-ses-prod` IAM 사용자와 `clipper-prod-app-role` 역할을 확인했다.
- 발송 action은 `ses:SendEmail`, 도메인 identity 및 실제 사용할 구성 세트 ARN 권한을 맞춘다. dev/prod 구성 세트를 각각 허용하는 정책 수정을 안내했다. 현재 실제 AWS JSON은 문서화 중 다시 조회하지 않았다.
- repo 예시 정책/운영 env에는 초기 `clipper-mail` 이름이 남아 있다. **실제 운영 적용에는 아래 `clipper-mail-prod` 이름을 사용해야 하며 예시를 그대로 복사하면 안 된다.** 기존 다른 서비스나 기존 구성 세트 권한을 임의로 제거하지 않는다.

### 9.2 S3와 SES 키 분리

기존 `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`는 기본 소재 S3 업로드용이었다. 새 SES 키를 만들 때 설명 태그 `clipper-dev-ses-mail`을 사용하도록 안내했다. 사용자가 키를 발급하고 비공개 dev env에 입력했다. 실제 키 값은 받거나 문서에 저장하지 않았다.

| 값 | 동작 |
|---|---|
| `MAIL_SES_ACCESS_KEY_ID` + `MAIL_SES_SECRET_ACCESS_KEY` 둘 다 있음 | SES SDK에 전용 자격 증명을 명시적으로 전달 |
| 둘 다 없음 | AWS SDK 기본 credential chain 사용 |
| 하나만 있음 | 잘못된 설정으로 API 시작 실패. 비밀값은 오류에 출력하지 않음 |
| 기존 `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` | S3 기존 설정 유지. SES가 기본 chain을 사용할 때에는 이 env 키가 EC2 역할보다 먼저 선택될 수 있음 |

따라서 운영 역할에 정책이 붙어 있다는 사실만으로 실제 API가 그 역할을 사용한다고 단정할 수 없다. 전용 MAIL_SES 키 여부, generic AWS 키 여부, 실행 역할 연결을 배포 시 함께 확인해야 한다.

### 9.3 개발/운영 리소스 대응

| 항목 | 개발: 연결·발송 사용 | 운영: 생성만 완료 보고 |
|---|---|---|
| SES 구성 세트 | `clipper-mail-dev` | `clipper-mail-prod` |
| SES 이벤트 대상 이름 | `clipper-mail-dev-feedback` | `clipper-mail-prod-feedback` |
| SNS Standard 토픽 | `clipper-mail-dev-events` | `clipper-mail-prod-events` |
| SNS ARN | `arn:aws:sns:ap-northeast-2:327655937726:clipper-mail-dev-events` | `arn:aws:sns:ap-northeast-2:327655937726:clipper-mail-prod-events` |
| HTTPS 피드백 URL | `https://dev-api.clipperstudio.ai/mail/feedback` | 배포 후 `https://api.clipperstudio.ai/mail/feedback` |
| 웹 링크 origin | `https://dev.clipperstudio.ai` | `https://clipperstudio.ai` |
| SNS 구독 상태 | 사용자가 ‘확인됨’을 제시 | 코드 미배포. 구독 생성/확인 완료로 기록하지 않음 |

선택한 이벤트는 콘솔의 **전달 / 하드 바운스 / 수신 거부**다. 여기서 ‘수신 거부’는 `Complaint`(스팸 신고)를 뜻하며, `Subscription`(구독 기본 설정 변경) 이벤트와 다르다. SNS Raw message delivery는 끈다.

토픽 정책에는 `ses.amazonaws.com`의 `sns:Publish`를 허용하고 `AWS:SourceAccount=327655937726`, SourceArn을 환경별 `arn:aws:ses:ap-northeast-2:327655937726:configuration-set/clipper-mail-{dev|prod}`로 제한하도록 안내했다.

개발에서 확인된 HTTPS 구독 ARN:

```text
arn:aws:sns:ap-northeast-2:327655937726:clipper-mail-dev-events:60c30fb1-1aec-4802-89d6-104c1394182d
```

### 9.4 env 설정값 대응 — 비밀값 제외

| 환경변수 | 개발 | 운영 준비값 |
|---|---|---|
| `MAIL_SES_REGION` | `ap-northeast-2` | 동일 |
| `MAIL_FROM_EMAIL` | `Clipper <clipper@metabuzz.co.kr>` | 동일 |
| `MAIL_SES_CONFIGURATION_SET` | `clipper-mail-dev` | `clipper-mail-prod` |
| `MAIL_PUBLIC_API_URL` | `https://dev-api.clipperstudio.ai` | `https://api.clipperstudio.ai` |
| `WEB_BASE_URL` | `https://dev.clipperstudio.ai` | `https://clipperstudio.ai` |
| `MAIL_SNS_TOPIC_ARNS` | 위 dev 토픽 ARN | 위 prod 토픽 ARN |
| `MAIL_UNSUBSCRIBE_SECRET` | 개발용 안정적인 비밀값 | 운영용 별도 안정적인 비밀값; 운영 인스턴스 간 동일하게 유지 |
| `MAIL_SES_ACCESS_KEY_ID` / `MAIL_SES_SECRET_ACCESS_KEY` | 사용자 입력 완료 보고 | 운영 auth 방식 결정 후 입력하거나 둘 다 생략해 역할 사용 |
| `MAIL_WORKER_ENABLED` | 초기 false로 준비 후 실제 발송 사용 | 배포·대기열·테스트 준비 전 false 유지 |
| `MAIL_SEND_INTERVAL_MS` | `1000` | 초기 `1000` |

`MAIL_UNSUBSCRIBE_SECRET`을 바꾸면 기존 메일 수신거부 링크가 무효화될 수 있으므로 계속 보존한다. env 파일·키·Google/Toss 토큰·실제 비밀번호는 이 기록에 포함하지 않는다. Resend를 유지하므로 `RESEND_API_KEY`, `INQUIRY_FROM_EMAIL`, `INQUIRY_TO_EMAIL`도 임의로 제거하지 않는다. 문의 수신 주소는 기존 설정을 유지하며 이 문서화에서 실제 값은 조회하지 않았다.

### 9.5 개발에서 실제 확인한 것

- 개발 SNS 목록에서 위 구독이 확인됨인 것을 사용자가 제시했다.
- 사용자가 직접 실행한 SES 전송 테스트를 본인 메일함에서 수신했다. 그 테스트는 transport 직접 호출이라 관리자 캠페인 목록에 일반 발송 기록을 만드는 테스트는 아니다.
- 사용자가 새 가입 후 웰컴 메일을 수신했다.
- 사용자가 구독 구매 후 구독 결제 완료 메일을 수신했다. 그 메일의 운영 링크 문제를 발견했고 §5의 수정으로 원인을 해결했다.
- 접두사·환경 링크 수정 후 최신 배포 완료는 보고했지만, **수정 후 새 메일의 제목/링크 및 관리자 전달 완료 결과를 다시 수신 확인했다는 보고는 아직 없다.**
- 나머지 자동 이벤트 모두에 대해 개발서버의 실제 업무 → 한 건 등록 → 실제 수신 → SNS 결과 반영을 끝냈다고 기록하지 않는다. 그 전체 업무 흐름 검증은 앞서 사용자 지시로 보류했다.

SES 발신 권한/도메인 인증은 실제 수신 메일함 생성과 별개다. `clipper@metabuzz.co.kr`의 수신함/별칭이나 답장 경로가 생성됐는지는 이 작업에서 확인하지 않았다.

## 10. 개발 회원 초기화 작업 기록

사용자는 개발 회원 `wlsdk318@gmail.com`을 가입 전 상태로 초기화하는 명령을 요청하고 직접 실행했다. 당시 대상 UUID는 `57ecd1b2-e41d-4ed3-92da-1017c5cd8765`다.

- 에이전트는 개발/운영 DB에 직접 접속하지 않았다. 대상·dev DB명·포트·실행 환경을 제한한 일회성 스크립트를 준비하고 격리된 로컬 PostgreSQL에서 검증했다.
- 사용자가 제시한 사전 조회에는 사용자 DB의 consent 3, session 8, desktop auth code 4건, 관리자 DB의 주문 3, 구독 2, 이용권 2, credit grant 3, ledger 7, access event 3, operation 3, 환불 신청/사례 각 1건 등이 있었다.
- API 중지 후 대상 연결 하위 기록부터 삭제하고 마지막에 users를 지운다. 순환 참조·환불 항목·정산/혜택/작업·메일/SNS 기록 및 가입 재판정에 영향을 줄 수 있는 탈퇴 식별값을 처리하도록 구성했다. 다른 회원·정책·상품·운영자 데이터는 유지한다.
- 실제 user/admin schema migration을 적용한 격리 DB에서 강제 실패 롤백, 정상 삭제, 다른 회원과 무관한 행의 checksum 보존을 확인했다. 두 DB는 분산 원자적 commit이 아니므로 admin commit 후 user commit 실패 가능성은 별도로 구분했다.
- 사용자는 `user.user_consents: 3건 삭제`, `user.users: 1건 삭제`, **‘초기화 완료: 대상 회원 및 연결 기록 없음’**, API 컨테이너 재기동 결과를 제시했다.
- 이후 재가입해 웰컴 메일을 받았으므로 위 UUID는 **옛 계정**이다. 이 스크립트를 현재 재가입 계정에도 그대로 반복 실행할 수 있다고 해석하지 않는다.
- 이 작업은 실제 PG 환불·카드 승인 취소, 받은 메일 삭제, Google 자체 계정/동의 삭제가 아니다. 원격 전체 DB를 초기화하거나 truncate하지 않았다.

스크립트·fixture·검증 로그·결과는 §13의 `dev-member-reset-261110`에 보관했다. 파괴적 명령 전문을 일반 운영 배포 절차에 섞지 않는다.

## 11. 검증 이력과 한계

테스트 수는 각 단계의 기준 코드가 다르므로 누적 합산하지 않는다. 환경 조건으로 제외된 테스트를 통과로 계산하지 않는다. 이번 문서화에서는 제품 테스트를 다시 돌리지 않고 아래 저장된 결과를 확인했다.

| 단계 | 결과 |
|---|---|
| 초기 수동 메일 구현 | API 5,330 / Admin 2,872 / Client 665 통과, 별도 DB 15. 제품 빌드와 브라우저 검증. 당시 기록은 초기 문서에 보존 |
| 최신 dev 보존 통합 | API 6,098 이후 최종 변경 subset·DB 보완, Admin 3,002 / Client 881, 격리 PG 117 통과 |
| 자동 10종·공통 디자인·가입 최종 feature | API 6,164 통과·491 제외·snapshot 5, Admin 3,013, Client 887 |
| 메일 integration | API 6,164, Admin 3,013 + 배포 라우트 2, Client 887, PG 6 suites/165. API·Admin prod/dev/mock·Client prod 빌드 |
| 다른 결제 채팅의 결합 검증 | API 6,224 통과·550 제외·snapshot 5, Admin 3,080, Client 905, PG 13 suites/268, 제품 3개 빌드 |
| SES 키 분리 | 새 credential 테스트 4, mail subset 10, API 전체 6,228 통과·550 제외·snapshot 5, 인프라 테스트 36 및 compose, API 빌드 |
| 자동 제목 접두사 | API 전체 6,235 통과·550 제외·snapshot 5, 빌드 |
| 발송 상세 드로어·메뉴 | Admin 전체 3,084, prod 빌드, 실제 브라우저 드로어·수신자·미리보기·Escape/초점 확인 |
| 환경 링크 최신 API | mail 6 suites/45, API 전체 6,242 통과·550 제외·snapshot 5, 빌드 |
| 새로고침 버튼 제거 최신 Client | 결제 내역 관련 33, prod 빌드, 실제 앱 페이지의 버튼 제거 확인. 이 한 줄 수정 뒤 Client 전체 905를 재실행했다고 주장하지 않음 |

기록된 검증 명령의 기본 형태는 API `npm test -- --runInBand`, 제품 빌드 `npm run build`, 관리자/고객 웹의 `ng test --watch=false --browsers=ChromeHeadless` 및 해당 Angular prod/dev/mock 구성 빌드다. 환경 선택형 PostgreSQL 스위트는 별도 격리 DB 설정으로 실행했다. 정확한 대상·환경·전체 출력은 §13의 단계별 로그를 기준으로 하며, 이번 문서화에서 이 명령들을 재실행하지 않았다.

광고 동의는 실제 로컬 웹→실제 API→독립 DB로 가입 동의/미동의, 가입 혜택 완료, 마이페이지 표시, 확인 전 미저장, 취소/Escape, ON/OFF 저장, 새로고침 유지까지 검증했다. Google 실인증 단계만 로컬 전용 가입 대기표로 대체했고 이후 경로는 실제 구현이었다. 외부 발송 워커·실제 자격 증명은 없이 검증했다.

공통 디자인은 실제 로컬 DB에 색상 저장·재조회, 로고 212px 로드, 미리보기 본문 182.37px, iframe 여백 제거를 확인했다. automatic editor 일부 브라우저 검토는 mock API를 사용했으며 실제 저장 계약은 별도 PG 테스트로 확인했다.

코드 검토에서 확인한 주요 경합·개인정보 문제는 실패 테스트로 재현 후 수정했다. 문의 재제출/복구, 무효 템플릿과 지급 완료, 탈퇴 주소 정리 100행 이후 진행, 해결된 실패 알림 제외, 플랜 변경의 실제 새 이용 기간, 대상 상품·재시도 시각, 환불 잠금·단일 pool 등을 검증했다.

결제 통합 PG의 첫 267/268 결과는 기존 데드락 테스트가 특정 트랜잭션만 victim이 된다고 가정한 문제였다. 다른 채팅에서 두 가능한 victim의 rollback/완료를 검사하게 고친 뒤 268/268을 통과했다. 이 때문에 운영 잠금 동작 자체를 변경했다고 기록하지 않는다.

전체 TypeScript 테스트 파일까지 포함한 광범위 타입 검사에는 기존 부채가 있었고 제품용 source build는 통과했다. 기존 Angular 초기 번들 경고도 남는다. 테스트/브라우저 결과는 운영의 실제 외부 메일 수신이나 모든 사업 이벤트 E2E를 대신하지 않는다.

## 12. 남은 작업과 보류

### 운영 배포 때 할 일 — 이번 문서화에서는 실행하지 않음

1. 배포할 검증 revision과 운영 AWS 대상 인스턴스를 정한다. 현재 사용자 보고는 리소스 생성까지만이며 운영 코드/DB 적용은 아직이다.
2. 운영 env의 구성 세트 `clipper-mail-prod`, prod SNS ARN, API/web URL, unsubscribe secret 및 실제 자격 증명 선택을 맞춘다. repo의 초기 `clipper-mail` 예시와 혼동하지 않는다.
3. 실제 발송 주체에 identity/구성 세트/발신 주소 권한이 적용되는지 확인한다. generic S3 키가 SES의 실행 역할을 가리지 않는지도 확인한다.
4. `MAIL_WORKER_ENABLED=false`로 코드·DB migration·API/웹을 배포할 절차를 준비한다. 위 Mac mini용 dev 명령을 AWS 운영 명령으로 그대로 사용하지 않는다. 기존 AWS 전용 배포 스크립트/런북을 다시 읽고 실제 환경에 맞춘다.
5. 새 코드가 서비스된 뒤 prod HTTPS SNS 구독을 만들거나 재확인하고 ‘확인됨’을 확인한다. 이벤트 대상·토픽 정책·허용 ARN을 함께 점검한다.
6. 대기/예약 건과 이벤트 활성 상태를 확인한다. 워커가 꺼져 있어도 업무에서 메일이 등록될 수 있으므로, 켜는 순간 기존 건이 처리될 수 있다. 탈퇴 임시 수신자는 기한 정책도 확인한다.
7. 범위를 제한한 내부 검증에서 발신자·접두사·운영 링크·공통 디자인·SNS 결과를 확인하고, 승인한 시점에 발송 워커를 활성화한다. 이 순서는 향후 작업이며 현재 운영 발송 가능 확인 완료가 아니다.

### 보류·이번 출시 제외 항목

| 항목 | 상태 |
|---|---|
| 나머지 자동 이벤트의 실제 업무 전체 흐름·외부 수신 테스트 | 사용자 지시로 보류. welcome/최초 구독 수신만 별도 사용자 확인 있음 |
| 수정 후 새 메일의 접두사·개발 링크·발송 결과 재확인 | 최신 배포 뒤 후속 확인 필요 |
| 수동 ‘메일 작성’ 화면 최종 UI와 활성화 | 별도 채팅에서 검토. 현재 버튼 disabled, 외부 에디터 보류 |
| 기존 문의 전달·운영자 초대/재설정 Resend 이전 | SES 자동 체계 이후 나중에 진행하기로 함 |
| 대시보드의 상세 갱신 실패 사유 추가 표시 | 문서로만 보존, 구현 보류 |
| 휴면 2종·해지 예약 완료·실패로 종료·연간 갱신 사전 안내 | 이번 이벤트 목록에서 제외 |
| S3 메일 로고 업로드/관리 체계 | 새로 도입하지 않음. 기본 CID 로고 사용 |

다른 결제 채팅과의 통합은 처음에 보류했지만 이후 실제 dev 병합·푸시까지 끝났으므로 더 이상 미통합 TODO로 두지 않는다.

## 13. 파일·근거·백업 인덱스

### 실제 코드의 주요 위치

- API 메일: [mail 모듈](/Users/jina/project/adlight/web/clipper_web_api/src/modules/mail), [업무 연결](/Users/jina/project/adlight/web/clipper_web_api/src/modules/mail-events), [SES sender/설정](/Users/jina/project/adlight/web/clipper_web_api/src/core/mail), [OpenAPI](/Users/jina/project/adlight/web/clipper_web_api/docs/api/openapi.yaml).
- 기본 문구: [mail-event-templates.ts](/Users/jina/project/adlight/web/clipper_web_api/src/modules/mail/domain/mail-event-templates.ts), [치환/생략](/Users/jina/project/adlight/web/clipper_web_api/src/modules/mail/domain/automatic-mail-content.ts), [공통 HTML/링크/제목](/Users/jina/project/adlight/web/clipper_web_api/src/modules/mail/domain/mail-content.ts).
- 관리자: [메일 페이지](/Users/jina/project/adlight/web/clipper_web_admin/src/app/features/portal/mail), [메뉴](/Users/jina/project/adlight/web/clipper_web_admin/src/app/shared/layout/nav-items.ts), [배포 라우트](/Users/jina/project/adlight/web/clipper_web_admin/src/app/app.routes.deploy.ts), [빌드 설정](/Users/jina/project/adlight/web/clipper_web_admin/angular.json).
- 고객 웹: [고객 소스](/Users/jina/project/adlight/web/clipper_web_client/src/app). 정확한 최초 feature/후속 변경 파일은 아래 JSON의 repo별 commit 파일 목록에 수록했다.
- 인프라: [compose](/Users/jina/project/adlight/web/clipper_infra/apps/compose.yml), [개발 env 예시](/Users/jina/project/adlight/web/clipper_infra/env/stack.dev.env.example), [운영 env 예시](/Users/jina/project/adlight/web/clipper_infra/env/stack.prod.env.example), [개발 배포](/Users/jina/project/adlight/web/clipper_infra/runbooks/deploy-dev.md), [migration 스크립트](/Users/jina/project/adlight/web/clipper_infra/scripts/migrate-db.sh).

### 백업·단계별 결과

- [최신 dev 보존 통합](/Users/jina/project/adlight/.local-backups/mail-before-dev-20261110-031543/reconcile/progress.md).
- [자동 연결 구현·검토](/Users/jina/project/adlight/.local-backups/mail-automatic-20261110/progress.md), [광고 동의 로컬 E2E](/Users/jina/project/adlight/.local-backups/mail-automatic-20261110/consent-e2e.md), [공통 디자인 검증](/Users/jina/project/adlight/.local-backups/mail-common-design-20261110/result.md).
- [커밋 전 파일 manifest](/Users/jina/project/adlight/.local-backups/mail-before-commit-261109-lkex95vl/manifest.json), [메일 통합 보고](/Users/jina/project/adlight/.local-backups/mail-integration-261109/report.md).
- [다른 결제 채팅 통합 보고](/Users/jina/.codex/visualizations/2026/11/09/01a1bea6-b00b-7493-aa45-fc5085a7c809/payment-integration-push-20261110/report.txt).
- [dev 반영/푸시 확인](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/dev-payment-mail-merge-20261110.json).
- [전용 키](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/ses-dedicated-credentials-261110/result.json), [접두사](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/automatic-subject-prefix-261110.json), [드로어](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/mail-detail-drawer-261110/result.json), [환경 링크/버튼](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/mail-env-links-refund-refresh-261110/result.json).
- [회원 초기화 검증 결과](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/dev-member-reset-261110/result.json), [격리 fixture 검증 로그](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/dev-member-reset-261110/validation.log).

위 단계별 JSON의 `serverDeployed:false`나 보고서의 ‘미커밋/미푸시’는 **파일 작성 당시 관찰값**이다. 뒤의 사용자 배포 보고나 실제 dev 푸시를 취소하는 뜻이 아니다. 이 문서의 최신 상태 표와 시점별 Git 이력을 함께 읽는다.

### 워크트리·로컬 환경 인계

- 원본 소스: `/Users/jina/project/adlight/web/{clipper_web_api,clipper_web_admin,clipper_web_client,clipper_infra}`. 현재 4개 dev clean.
- 관리형 워크트리: `/Users/jina/.codex/worktrees/mail-integration-{api,admin,client,infra}-261109/<repo>`에 보존했다. 현재 infra 채팅 cwd도 그중 하나다. 후속 fix branch 이름은 §6.4를 따른다.
- 로컬 실 API/광고 동의 검토는 3000·고객 웹4201·실관리자4207·전용 DB55448을 사용했다. 초기 별도 환경은 API3000/관리자4202/DB55449/로컬메일함4555였고, 다른 결제 채팅은 API4340/관리자3310/고객3311/DB55441을 사용했다. 이들은 시점별 관찰이며 현재 실행 보장이 아니다.
- 임시 회귀 DB55439와 회원 초기화 검증 DB55459는 검증 후 종료했다. 다른 채팅의 DB·컨테이너·사용자 데이터는 임의로 정리하지 않는다. 로컬 프로세스가 필요하면 현재 포트/소유권부터 다시 확인한다.
- 사용자 요청으로 별도 메일 작성 UI 검토 채팅 `01a1c19d-2bb3-7ff0-8e83-d701d9cd6402`를 만들었다. 그 채팅의 검토 파일은 임의로 삭제하지 않는다. 본 세션의 구현 완료와 해당 화면 최종 확정은 구분한다.

## 14. 이번 문서화 자체의 변경 범위

이 종합 문서, 기본 템플릿 스냅샷, Git/근거 JSON, 메일 README 색인, 날짜별 세션/월별 로그를 추가했다. 초기 메일 문서 상단에는 현재 기록 링크와 과거 스냅샷임을 표시했다. 루트 README와 다음 세션 인계에는 이 문서로 가는 링크를 추가했다.

기존 `.codex`의 AGENTS·README.FRONTEND·UI 목업 가이드·환불 정책 문서 등 다른 미커밋 변경은 보존한다. 제품 소스, 실제 env/자격 증명, AWS 리소스, 개발/운영 DB, 배포 상태는 이 문서화 작업에서 변경하지 않는다. 문서도 새로 커밋·푸시하지 않는다.


## 2026-11-10 추가: 환불 대기 버튼·결제 대기 표시·마이페이지 목업

개발계정의 실제 자동 메일 테스트 중 사용자가 다음 UI 변경을 요청했다. 메일 자동발송 시나리오와 별개로 진행했으며 새 결제·환불·탈퇴를 에이전트가 실행하지 않았다.

### 제품 코드에 반영한 로컬 변경

- 환불 승인 대기 중에는 비활성화된 ‘변경 가능한 요금제 보기’를 제거하고 같은 자리·공통 버튼 스타일의 ‘환불 신청 확인’ 링크를 표시한다. 기존 안내 문단 안 텍스트 링크는 제거하며 경로는 /my/payment-history다.
- 플랜 변경 결제 확인창이 클릭 직후 닫힌 뒤 API 완료까지 아무 피드백이 없던 원인은 ConfirmDialog가 afterClosed를 먼저 완료한 뒤 결제 요청을 시작하는 순서였다. 지연 자체가 PG/서버 중 어디에서 발생했는지는 서버 로그로 조사하지 않았다.
- 선택적으로 제공하는 ConfirmDialogData.confirmAction과 pendingText로 해당 확인창을 요청·화면 갱신 완료까지 유지한다. 처리 중 안내, 중복 확인 차단, 버튼·동의 체크 비활성화, Escape/바깥 클릭 차단을 적용한다. 기존 일반 확인창은 boolean 결과를 유지한다. 503 불확실 결과 안내·자동 재시도 금지·파괴 후 늦은 응답 보호·자신이 연 모달 정리를 유지한다. 닫힘 애니메이션 동안도 중복 잠금을 유지한다.
- 완료 후 페이지 하단에 추가하던 기존 카드/메시지는 제품 코드에서 아직 교체하지 않았다. 아래 3안의 사용자 선택 후 반영한다.
- 계정 설정 3개 소제목은 모두 h3였으나 이메일 수신 설정에 크기/두께 지정이 없어 기본 h3 크기가 적용됐다. 별도 공통 제목 컴포넌트는 없었다. account 폴더의 공통 SCSS partial을 두 컴포넌트에서 가져와 15px/600으로 맞췄다. 기존 카드 간격은 유지한다.
- 대시보드 이용 정보의 Pro/정기구독/월간 값은 같은 30px·줄높이36px로 맞췄다.

### 검토 전용 화면

Clipper UI_MOCKUP_PLAYBOOK을 읽고 실제 AppComponent·PortalLayout·Dashboard·PaymentHistory·Account·공통 Material 모달과 테마를 재사용했다. 별도 Angular 엔트리 src/plan-change-review-main.ts 및 tsconfig.plan-change-review.json으로 샘플 API만 공급하고 다른 HTTP 요청은 차단한다. 실제 제품 라우트/엔트리에는 연결하지 않았고 배포 번들에 리뷰 문자열이 없음을 확인했다.

- 요금제 선택 4안: A 비교표660px, B 목록640px, C 선택 후 확인600px, D 상위 플랜 카드720px. 월간/연간 전환은 모두 중앙에 배치하고 각 버튼은 약132×40px다.
- 완료 안내 3안: A 중앙 모달500px, B 오른쪽 결과 패널440px, C 기존 구독 정보 안의 완료 안내. 목업에서는 기존 하단 완료 카드를 제거한 상태로 비교한다.
- 결제 내역 2안: A 한 줄 말줄임+전체 번호 복사, B 두 줄 표시+전체 번호 복사. 실제 PaymentHistoryComponent를 사용하며, 긴 번호에 의해 컬럼이 커지지 않도록 리뷰 범위에서 fixed table layout을 적용한다. 상품 컬럼은 검증 뷰포트에서 약234px. 원문 title·복사 동작 유지. 제품 그리드는 아직 변경하지 않는다.
- 글자 크기 수정 확인 2화면: 실제 Dashboard·Account. 브라우저 computedStyle에서 값3개30px/36px, 제목3개15px/600 일치 확인.

검토 링크: http://127.0.0.1:4226/#picker . 페이지 상단에서 요금제 선택/완료 안내/결제 내역/글자 크기를 고른다. 각 안의 버튼은 확대해서 보여주고, ‘원본 크기로 열기’로 단독 화면을 연다. iframe 원본1487×1058을 고정하고 바깥 transform으로만 확대한다. 최대600%, 최저배율은 해당 그룹 전체 보기다. 목업 가격/주문번호는 샘플이며 실제 결제는 발생하지 않는다.

산출물: /Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/plan-change-review-261110 . 로컬 서버는 포트4226, 빌드는 /private/tmp/clipper-plan-change-review-build/browser다. 검토 브라우저 탭은 deliverable로 유지했다. 사진은 실제 브라우저 캡처이며 UI 자체는 실제 DOM이다.

### 검증과 Git 상태

- 전체 클라이언트 ChromeHeadless911개 통과, prod/review 빌드 통과, diff --check 통과. 기존 초기 번들500kB 기준 초과 경고(533.53kB)는 남는다.
- 실제 Material overlay를 사용하는 대기 응답 회귀 테스트를 먼저 실패시킨 뒤 수정했다. 지연 중 상태/버튼/동의/중복·성공·503·화면 파괴·기존 일반 확인창 호환을 검증했다.
- 독립 읽기 전용 검토 /root/review_inquiry_from에서 actionable finding 없음. 다른 보조 작업자는 결제 그리드 목업과 계정 제목을 각각 분리 작업했다.
- 로컬 브라우저에서 6초 모의 결제 동안 같은 확인창의 처리 중 안내와 비활성 버튼을 확인하고, 완료 모달 연결과 하단 중복 카드 없음도 확인했다. 월간·연간 전환, 에셋, 모달 배경, 폭, 복사, 메뉴 선택을 확인했다.
- 이 UI 작업은 모두 클라이언트 작업트리의 미커밋 변경이다. 커밋·병합·푸시·원격 배포·DB 변경·AWS 변경은 하지 않았다. 앞서 noreply 문의 발신 분리 dev 커밋/API6da3ebf·infra88b3760의 완료 상태와 혼동하지 않는다.


## 2026-11-10 승인 후 구현 계획: 완료 A·결제 내역 A

사용자는 완료 안내 A(중앙 모달), 결제 내역 A(한 줄 말줄임+전체 주문번호 복사)를 제품에 구현하도록 확정했다. 요금제 선택 모달 4안은 보류하므로 기존 제품 선택 UI를 유지한다. 기존 미커밋 환불 버튼·처리 중 안내·폰트 변경도 보존한다.

1. 완료 안내: 실제 결제/구독 응답의 변경 전후 상품·결제 금액·새 이용 기간·다음 결제·월 지급 크레딧을 받는 전용 완료 모달을 추가한다. 확인창의 비동기 처리·닫힘이 끝난 뒤 성공한 즉시 변경에만 한 번 열고, 하단 성공 카드/중복 완료 메시지를 제거한다. 취소·예약·실패·503 불확실 응답에는 성공 모달을 열지 않는다. 날짜/시간은 기존 분 단위 표시 기준이며 샘플 값을 제품에 넣지 않는다.
2. 결제 내역: 실제 테이블에 폭 제한과 한 줄 말줄임을 반영하고, 원문 툴팁/전체 번호 복사/복사 성공·실패 접근성 안내를 추가한다. 기존 모바일 카드 배치는 유지한다. 리뷰 A는 실제 제품 컴포넌트를 재사용하도록 중복 장식을 제거한다.
3. 각 작업의 실패 테스트→구현→관련 검증 후 전체 클라이언트 브라우저 테스트·prod/review 빌드·독립 검토·브라우저 실물 확인을 수행한다. 커밋·병합·푸시·배포는 이번 지시 범위에 추가하지 않는다.


### 완료 A·결제 내역 A 실제 구현 결과

- 전용 PlanChangeCompleteDialogComponent를 Dashboard 아래에 구현했다. 변경 전 상품과 confirm 응답의 상품명·결제 금액·월 크레딧·새 이용기간·다음 결제시각을 사용한다. 마이페이지 재조회 결과가 응답보다 늦거나 실패해도 거래 응답 스냅샷으로 표시한다. 재조회 실패 시 결제 성공을 실패로 바꾸지 않고 모달에도 주의를 표시한다.
- 기존 비동기 확인창이 닫힌 후 즉시 변경+결제 정보가 있는 성공에만 완료 모달을 연다. 취소·예약·unchanged·실패·503에는 완료 모달이 없다. 화면 이탈 시 열린 완료 모달도 정리한다. ‘결제 내역 보기’는 모달을 닫고 /my/payment-history로 이동한다.
- 하단의 완료 카드와 즉시 결제 중복 성공 메시지·전용 CSS·더 이상 제품에서 사용하지 않는 완료 카드용 signal을 제거했다. 예약/다른 구독 업무의 기존 메시지는 유지한다.
- 실제 PaymentHistoryComponent에 fixed table layout과 열별 폭을 적용하고 주문번호를 한 줄 말줄임 처리했다. 원문 DOM·title은 유지하며 MatIconButton으로 전체 번호를 복사한다. 성공/실패를 행별 aria-live로 안내하고, 같은 행 복사 중에는 중복 호출을 막는다. 다른 행의 복사는 독립적이다. 기존 모바일 카드 배치를 유지한다.
- 리뷰 A는 이제 장식을 덧붙이는 복제품이 아닌 실제 완료 모달/실제 결제내역 표를 그대로 사용한다. 리뷰에 ‘적용 화면’ 그룹을 추가했다. 요금제 선택 4안은 보류 상태로 리뷰에만 남고 제품의 기존820px 선택 모달은 유지됨을 브라우저에서 확인했다.
- 최종 전체 ChromeHeadless915/915 통과, prod 및 review 빌드 통과, diff check 통과. 기존 번들 예산 경고533.53kB는 동일하다. 배포 JS에 리뷰 fixture 마커가 없는 것도 확인했다.
- 독립 검토의 P3(같은 행 복사 응답 역전)를 per-row copying 잠금으로 수정했고 지연 Promise 성공/실패 회귀 테스트로 red→green 검증했다. 최종 검토에서 남은 actionable finding 없음.
- 로컬 브라우저에서 실제 기존 요금제 선택→동의→처리 중→완료 모달1개→결제내역 이동을 검증했다. 이 흐름은 샘플 PG 응답만 사용했으며 실제 결제·서버·DB 변경은 없다. 하단 완료 카드0개, 실제 표의 복사 버튼은3행에3개로 중복 없이 표시되고 원문 복사가 동작했다.
- 검토 링크 http://127.0.0.1:4226/#applied . 실제 완료 화면 캡처는 산출물의 implemented-complete-a.png다. 아직 모든 UI 변경은 로컬 미커밋이며 병합·푸시·배포하지 않았다.


### 2026-11-10 클라이언트 UI 수정 dev 커밋·푸시 완료

사용자가 ‘이것들 최신 원격 dev에 커밋 푸시’하도록 지시했다. 원격을 fetch/pull하여 dev가 작업 기준93fb968c038b6d75e57b6028c2e56a1b62498b8e와 같음을 확인했다. 기존 미커밋/리뷰 파일30개와 patch를 client-dev-ui-merge-261110/before에 백업하고 SHA256 manifest를 저장했다.

- 로컬 기능 브랜치 codex/mypage-payment-ui-261110에 실제 제품20파일만 커밋: 0cbb55f72005abe681150b7019d82a17b7df36f9, `fix(mypage): improve plan change feedback and payment history`.
- 커밋 트리4d87b982c8524d8d055997ac845af4206843d795. 최신 dev에 fast-forward로 반영하고 origin/dev에 일반 push 성공. git ls-remote로 동일SHA 확인. 원본 dev 체크아웃은 깨끗하다. 충돌/force push 없음.
- 포함: 환불 대기 버튼 교체, 결제 처리 중 확인창 유지·중복 차단, 완료 A 중앙 모달과 하단 카드 제거, 결제내역 A 폭 제한·말줄임·원문 복사, 계정 제목 공통15px/600, 이용 정보 값30px.
- 보류한 요금제 선택 모달의 ng-template은 기존dev와 문자열 동일을 확인했다. 검토용 sample/별도 엔트리/tsconfig는 커밋에서 제외하고 로컬 보존했다. 실제 prod JS에서 리뷰 fixture marker가 없음을 확인했다. 30개 작업 파일 전체가 백업manifest와 동일해 유실 없음을 확인했다.
- 커밋 직전 전체 ChromeHeadless915/915와 prod 빌드·diff check 통과. 이전 최종 독립 검토 내용과 동일한 소스이며 병합 트리가 테스트한 커밋 트리와 같다. 기존 번들 예산 경고533.53kB는 남는다.
- 서버 배포·DB·환경변수·AWS 변경은 하지 않았다. 이번 작업의 서버 반영은 사용자 소유의 클라이언트 배포이며, API/admin/infra 재배포나 DB migration이 필요한 변경은 없다.


### 2026-11-10 개발 갱신 메일 테스트와 테스트 일정 정합성 수정

사용자가 개발 계정 wlsdk318@gmail.com으로 구독 환불을 취소하고, 일회성 도구로 최초 갱신 실패·첫 자동 재시도 실패·마지막 자동 재시도 실패를 실행했다. 최초 안내1통, 중간 안내0통, 최종 안내1통을 확인했다. 이어 직접 재결제했고 26,900원 결제 완료·구독 active·신규 정기 크레딧5,000·갱신 완료 메일1통을 확인했다. Chrome 실제 화면에서 자동 갱신 중, 다음 결제2026-12-10 18:16, 총 크레딧10,800을 읽었다.

브라우저 확인 중 메일의 크레딧 사용 기한18:16과 실제 신규 크레딧 기한14:56의 차이를 발견했다. 원인은 이 세션에서 만든 테스트 도구가 구독 기준만 앞당기면서 크레딧 기준과 이전 기간 크레딧 만료를 함께 맞추지 않은 데 있다. 사용자가 정리를 지시했다.

제품 코드·정책은 유지하고 일회성 도구를 수정했다. 기존 기준 시각을 보존하고 기간만 단축하며 이전 기간 정기 크레딧을 만료시킨다. 현재 개발 계정 전용 원자적 정리 도구도 작성했다. 신규 크레딧 기한을 이미 보낸 메일의12월10일18:16에 맞추고, 이전 기간5,000을 만료로 제외하여 예상 잔액5,800으로 정리한다. 수량·원장·결제·메일은 새로 만들거나 변경하지 않는다.

격리 DB에서 원본 도구의 불일치를 실제 서비스와 가짜 PG 응답으로 재현했다. 정리 검증5개 통과(조회 무변경·사용 후 차단·원자성·기한/잔액 일치·다른 지급 건 및 건수 보존·재실행 무변경). 수정 도구로 실패3단계→직접 재결제→실제 월 정기 지급을 다시 실행해 메일/실제 기한이 일치했다. 외부 PG·SES 요청 없이 검증했다.

산출물: /Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/dev-renewal-mail-test-261110/credit-repair/. README와 실행 도구, 검증 코드·로그를 보존했다. 실제 개발 DB 적용은 사용자 실행을 기다린다. 운영 접근·커밋·푸시·병합 없음. 탈퇴 테스트는 정리 결과 대조 뒤 진행한다.


### 2026-11-10 크레딧 테스트 데이터 정리 개발 적용 확인

사용자가 정리 파일 apply를 실행했고 changes=3, spendableCredits=5800, creditExpiresAt=2026-12-10T09:16:46.306Z를 전달했다. Chrome 개발 계정 크레딧 화면을 실제 새로고침하여 무료체험400·정기구독5,000·추가충전400 합계5,800, 신규 정기 크레딧 기한12월10일18:16, 기존 Pro5,000 만료(11월10일18:16)를 확인했다. 신규 크레딧 기한은 이미 수신한 갱신 완료 메일과 일치한다. 결제 내역의 26,900원 갱신 완료 기록도 그대로다. 추가충전400/5,900원 환불 신청이 승인 대기로 남아 있다. 취소·탈퇴는 브라우저에서 실행하지 않았다.


### 2026-11-10 개발 자동 메일 수신 테스트: 탈퇴 완료까지 확인

사용자가 마지막 탈퇴 절차를 실행하고 `[Clipper] 클리퍼 회원 탈퇴가 완료됐어요` 메일을 전달했다. 탈퇴 번호WD-YRKP6Q, 마스킹 이메일wl***@gmail.com, Pro 월간 종료, 남은5,800크레딧 소멸, 등록 카드 끝자리076*의 자동 결제 중단·정보 삭제 처리 안내, 로그인 기기1대 로그아웃이 표시됐다. 이는 직전 개발 계정의 상품·크레딧·카드와 일치한다. Chrome의 기존 개발 클라이언트 탭이 로그인 화면(dev.clipperstudio.ai/login?returnUrl=%2F)으로 이동한 것을 직접 확인했다. 재로그인·재가입·추가 데이터 변경은 하지 않았다.

이번 개발 환경의 이벤트별 실제 메일 수신 확인 범위는 웰컴·구독 결제·크레딧 충전·플랜 변경·문의 접수·환불 접수(추가크레딧/구독/예약취소 분기)·최초 갱신 실패·최종 갱신 실패·직접 재결제에 따른 구독 갱신·탈퇴 완료다. 첫 자동 재시도 실패에는 추가 메일이 등록되지 않은 것도 확인했다. 사용자가 앞서 완료했다고 알린 항목과 직접 대조한 후속 항목을 합친 결과이며, 모든 항목을 새로 독립 실행한 것으로 표현하지 않는다.

주의할 검증 한계: 갱신 실패·재시도는 해당 개발 계정의 일정을 앞당기고 기존 서비스의 scheduled 경로를 일회성 호출했다. D+1/D+2의 실제24시간 대기와 스케줄러의 자동 실행을 끝까지 관찰한 검증은 아니다. 실제 카드 결제 거절 사유는 테스트 키의 지정 거절 코드로 재현했다. 운영 배포·운영 SES 검증은 이번 테스트에서 수행하지 않았다. 탈퇴 후 DB·PG의 후속 정리 결과는 별도 조회하지 않았으며 이번에 확인한 것은 수신 메일 내용과 실제 로그아웃 화면이다.


### 2026-11-10 결제 내역 컬럼·환불 버튼 통일 (로컬 미커밋)

사용자가 컬럼 병합 대신 기존7개 컬럼을 유지하고 `결제 상태 → 영수증 → 환불 상태 → 환불 신청` 순서로 바꾸도록 지시했다. 원격dev fetch 결과ca84dd2와 같은 기준에서 기존 분리 클라이언트 작업 폴더를 사용했다.

- 실제 결제내역 컴포넌트 HTML: 관리→환불 신청, 헤더와 행의 영수증/환불상태 순서 교체, 모바일data-label 동일 변경.
- 신청/취소 모두 matButton=outlined와 동일 클래스 사용. 취소 버튼/확인 모달은 ‘환불 신청 취소’, 두 버튼의 처리 중 문구는 ‘처리 중’. 별도 그라데이션 취소 버튼 CSS 제거. 공통 Material 토큰으로 두 버튼 좌우 여백12px를 맞추고 긴 취소 문구에 맞게 마지막 컬럼18%, 상품 컬럼24.5%로 조정했다.
- 기존 DOM 테스트에서 순서/문구를 먼저 바꿔 실패3개를 확인했다. 구현 뒤800px 폭 가로 넘침1건이 잡혀 버튼 공통 여백/작업 컬럼 폭을 조정했다. 최종 결제내역37/37, dev build, 별도 리뷰 build, diff check 통과. 기존 초기 번들 예산 경고는 남는다. 제품 번들에서 검토용 환불 샘플 marker가 없음을 확인했다.
- 실제 앱의 기존 로컬 리뷰 엔트리에서 샘플 환불 가능·승인 대기 행으로 검증했다. 브라우저에서 버튼 높이40px/글자14px/여백12px 일치·넘침 없음, 요청한 컬럼 순서, 모바일 배치, 취소 확인 모달의 문구를 확인했다. 실계정·결제·환불 API는 호출하지 않았다.
- 화면: /Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/refund-columns-261110/desktop.png 및 mobile.png. 로컬 검토 탭은4226의 실제 결제내역 컴포넌트를 사용한다.
- 제품 변경은payment-history.component의html/scss/ts와기존spec 총4개 미커밋이다. 별도 리뷰 fixture는 기존 untracked 검토 파일 안에서만 변경했으며 기존 버전은 /private/tmp/clipper-payment-grid-review-before-refund-ui.ts에 보존했다. 커밋·푸시·병합·서버 배포·DB/env 변경은 하지 않았다.


### 2026-11-10 환불 버튼 최종 스타일: 채워진 버튼

사용자가 아웃라인 대신 채워진 버튼을 명시했다. 두 환불 작업 버튼을 모두 matButton=filled로 바꾸고 동일한 filled-horizontal-padding12px 토큰을 적용했다. 컬럼 순서·문구는 유지했다. 결제내역37/37, dev/review 빌드와diff check 통과. 로컬 실제 컴포넌트에서 두 채워진 버튼을 눈으로 확인했고 desktop-filled.png에 보존했다. 최종스타일은 filled이며 앞선 outlined 설명을 대체한다. 기존4파일 미커밋 상태 유지, 커밋·푸시·배포 없음.


### 2026-11-10 결제 내역 환불 UI dev 커밋·원격 푸시 완료

사용자의 원격dev 푸시 지시에 따라 실제 제품4파일만 codex/mypage-payment-ui-261110에 커밋했다. 커밋 e2443cf73b5b26ec37633146a1de73c86c9030eb (`fix(payment-history): clarify refund actions and unify buttons`), 부모ca84dd2. 원본 클라이언트dev에 fast-forward로 반영하고 origin/dev에 일반push했으며 ls-remote로 같은SHA를 확인했다. 충돌·force push 없음.

최종 소스로 결제내역37/37와dev build를 다시 통과했다. 기존 초기 번들 예산 경고533.65kB/500kB는 유지된다. 제품 번들에서 검토용 환불 샘플이 없음을 확인했다. 제품 및 검토14파일을 refund-columns-261110/commit-backup에 백업했고 작업 후SHA256 일치로 보존을 확인했다. 검토용 파일은 기존 분리 작업 폴더에 untracked로 남겨 두었다. 원본dev는 깨끗하다. 서버 배포·DB/env 변경은 하지 않았다.


### 2026-11-10 세션 미커밋·미병합 점검

사용자 요청으로4제품 저장소의origin/dev를새로fetch하고 원본dev/이세션관리형worktree/status·브랜치 ancestry를조회했다. API6da3ebf, Client e2443cf, Admin e89a8d1, Infra88b3760에서 원본dev와origin/dev가모두일치했다. 세션관련17개작업/통합브랜치는전부origin/dev의ancestor이며dev에없는커밋0개다. 기록한커밋26개도존재하는해당저장소에서모두origin/dev포함을확인했다.

4관리형worktree모두tracked/staged변경0개. 클라이언트관리형worktree에는실제앱리뷰용10개파일이untracked로남아있다. .codex/features/mail의기록·인계·README등14파일은문서저장소에서untracked이며문서커밋은아직하지않았다. 원본어드민에는별도메일작성/메일관리목업28파일이untracked로있다. 모두제품코드와분리해서보존했고이번확인에서수정·삭제·커밋·병합·푸시하지않았다. Git바깥의visualizations목업·스크린샷·테스트/정리도구·로그/백업도보존돼있다. 실제제품기능의누락된미커밋수정이나미병합커밋은발견되지않았다.

상세증거: /Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/refund-columns-261110/session-uncommitted-audit.json. 마지막클라이언트UI e2443cf의개발서버배포완료는사용자에게아직보고받지못했다.
