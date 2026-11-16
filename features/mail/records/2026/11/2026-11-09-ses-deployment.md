# 클리퍼 메일 기능 적용 안내

> **2026-11-10 현재 기준:** 이 문서는 초기 단계의 과거 기록입니다. 현재 10개 자동 이벤트는 실제 연결·dev 반영을 완료했고, 문의 전달·운영자 초대/재설정은 Resend를 유지합니다. 사용자는 최신 개발 배포 완료, 운영 SES/SNS/IAM 생성만 완료를 보고했습니다. [종합 기록](2026-11-10-mail-session-summary.md)과 [현재 색인](../../../README.md)을 먼저 확인하세요. 아래 초기 리소스 이름·배포 지침·미커밋/미연결 상태를 현재 기준으로 실행하지 마세요.

현재 변경은 로컬 개발 코드다. 운영 배포·운영 DB 변경·실제 회원 발송은 실행하지 않았다. 자동 발송 이벤트의 업무 연결과 외부 에디터 도입은 제외했다.

## 1. 기존 IAM 정책 수정

1. AWS 콘솔에서 IAM → 정책(Policies)을 연다.
2. `ClipperSesSendEmail`을 검색하고 정책 이름을 누른다.
3. 권한(Permissions) → 편집(Edit) → JSON을 누른다.
4. 아래 파일의 JSON으로 교체한다. 발신 주소를 contact에서 clipper로 바꾸고, 이번 발송 결과 수집에 사용할 `clipper-mail` 구성 세트 권한도 포함한다.
   - [적용할 JSON](/Users/jina/project/adlight/web/clipper_infra/env/clipper-ses-send-email.policy.json)
5. 다음(Next) → 변경 사항 저장(Save changes)을 누른다. 새 버전이 기본 버전으로 저장됐는지 확인한다.
6. `연결된 엔터티(Entities attached)`에서 기존 사용자 `clipper-ses-prod`에 연결된 상태를 확인한다. 정책을 고치면 연결된 사용자·역할에 적용되므로 액세스 키를 다시 만들 필요가 없다.
7. AWS 운영 서버는 EC2 → 인스턴스 → 대상 인스턴스 → 보안(Security)에서 현재 IAM 역할을 확인하고 역할 이름을 누른다. IAM 역할 화면 → 권한 추가(Add permissions) → 정책 연결(Attach policies) → `ClipperSesSendEmail` 검색·선택 → 권한 추가를 누른다. 두 운영 인스턴스가 서로 다른 역할이면 각각 연결한다. 기존 역할의 S3 등 권한은 유지한다.

코드가 AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY 환경변수를 받고 있다면 SDK는 역할보다 그 키를 먼저 사용한다. 그 경우 실제 사용하는 IAM 사용자에 정책을 연결하거나, 기존 S3 권한까지 실행 역할에 반영한 뒤 키 환경변수를 제거하는 배포가 필요하다. 현재 운영 자격 증명은 이 작업에서 조회·변경하지 않았다. 회사 외부 서버는 기존에 발급한 사용자 키를 서버 비밀 환경변수로 사용하면 된다.

서울 리전 metabuzz.co.kr 도메인이 이미 확인됨 상태이므로 이 변경을 위해 도메인을 다시 인증하거나 contact용 DNS를 바꿀 필요는 없다. SES 발신 주소는 수신 메일함 생성과 별개다. clipper@ 주소로 답장을 받으려면 회사 메일 서비스에 실제 수신함/별칭이 있어야 한다.

## 2. 발송 결과 수집 연결

1. 서울 리전 SES → 구성 세트(Configuration sets) → 생성 → 이름 `clipper-mail`.
2. 구성 세트의 이벤트 대상(Event destinations) → 대상 추가(Add destination).
3. Delivery, Bounce, Complaint 이벤트를 선택하고 SNS 대상으로 연결한다. 클리퍼 전용 토픽 `clipper-mail-events`를 사용한다.
4. SNS 토픽 권한은 `ses.amazonaws.com` 서비스의 Publish만 허용하고 SourceAccount를 회사 계정 `327655937726`, SourceArn을 `arn:aws:ses:ap-northeast-2:327655937726:configuration-set/clipper-mail`로 제한한다. 콘솔이 자동으로 구성한 정책도 이 범위를 확인한다.
5. SNS 구독은 HTTPS, 엔드포인트는 `https://api.clipperstudio.ai/mail/feedback`. Raw message delivery는 켜지 않는다. 코드가 허용 토픽과 SNS 서명을 검증한 뒤 구독 확인을 처리한다.
6. 토픽 ARN을 MAIL_SNS_TOPIC_ARNS에, 구성 세트 이름을 MAIL_SES_CONFIGURATION_SET에 넣는다. 알림 엔드포인트는 실제 코드 배포 후 연결한다.

## 3. 서버 환경변수

`clipper_infra/env/stack.prod.env` 및 API 컨테이너에 아래 설정을 반영한다. 예시는 `stack.prod.env.example`, 전달은 `apps/compose.yml`에 추가해 두었다.

MAIL_SES_REGION=ap-northeast-2
MAIL_FROM_EMAIL=Clipper <clipper@metabuzz.co.kr>
MAIL_SES_CONFIGURATION_SET=clipper-mail
MAIL_PUBLIC_API_URL=https://api.clipperstudio.ai
WEB_BASE_URL=https://clipperstudio.ai
MAIL_UNSUBSCRIBE_SECRET=<동일하게 유지할 무작위 32자 이상>
MAIL_SNS_TOPIC_ARNS=arn:aws:sns:ap-northeast-2:327655937726:clipper-mail-events
MAIL_WORKER_ENABLED=false
MAIL_SEND_INTERVAL_MS=1000
INQUIRY_TO_EMAIL=<기존 문의 수신 주소 유지>


MAIL_UNSUBSCRIBE_SECRET은 모든 서버에서 같은 값을 사용하고 계속 보존한다. 바꾸면 이전 메일에 포함된 수신거부 링크를 검증하지 못한다. 키·서명 비밀값은 관리자 브라우저에 전달하지 않는다.

## 4. 배포 순서

1. 위 IAM/SES/SNS 설정과 배포 환경변수를 준비한다. MAIL_WORKER_ENABLED=false 상태를 유지한다.
2. 회원 DB에 `1794180000000-CreateEmailPreferences`, 관리자 DB에 `1794180000000-CreateManualMail` 마이그레이션을 적용한다. 실제 적용은 기존 AWS 배포 스크립트의 `--migrate user,admin` 경로를 사용한다.
3. API와 관리자 웹·고객 웹을 함께 배포한다. 예: 기존 `scripts/deploy-aws-prod.sh --key <PEM 경로> --service all --branch <검증한 브랜치> --migrate user,admin`. 이 문서의 예시 명령은 실행하지 않았다.
4. SES/SNS 연결을 마무리하고 관리자 공통 디자인에 로고·하단 문구·회사 주소·연락처를 저장한다.
5. 검증용 회원만 직접 선택하여 내부 테스트 메일의 미리보기·수신·반송 상태를 확인한다. 광고 메일은 가입 동의·계정 설정·수신거부를 모두 확인한다.
6. 즉시/예약 발송을 사용할 때 MAIL_WORKER_ENABLED=true로 전환하고 API를 재시작한다. 테스트 발송도 작업 활성화가 필요하므로 활성화 전 대기/예약 건을 확인한다.
7. 기존 문의·운영자 초대·비밀번호 재설정도 SES로 보내므로 전환 배포 전에 발신 권한을 먼저 준비한다. 문의 받는 주소와 문의자 Reply-To, 기존 초대/재설정 링크 생성·유효기간은 유지한다. 더는 사용하지 않는 Resend 키는 전환 검증 후 폐기한다.

## 동작 기준

- 광고는 발송 확정 시 동의한 회원을 대상으로 저장하고, 실제 발송 직전에 동의·탈퇴·차단 상태를 다시 확인한다. 예약 후 새로 가입한 회원은 이미 확정한 예약 건에 추가하지 않는다.
- 필수 서비스 안내는 광고 동의 여부와 별개지만 존재하지 않는 주소의 영구 반송·스팸 신고는 발송 제외한다.
- 서버 장애 전 전송을 시작하지 않은 건은 복구하고, 이미 전송을 시작했으나 결과를 모르는 건은 확인 필요로 남긴다. 불명확한 결과를 자동 재전송하지 않는다.
- 접수 완료는 SES가 요청을 접수한 상태, 전달 완료는 상대 메일 서버가 전달을 받은 상태다. 실제 받은 편지함/열람 여부까지 보증하지 않는다.
- 자동 발송 19개 후보의 선정·본문 확정·업무별 트리거 연결은 이번 변경에 포함하지 않는다. 결제 재시도 조사와 이번 수동 발송 개발은 별개로 진행할 수 있다.

## 참고
- [AWS IAM 정책 편집](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-edit-console.html)
- [SES v2 발송 권한과 리소스](https://docs.aws.amazon.com/service-authorization/latest/reference/list_sesv2.html)
- [SES 구성 세트](https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html)
- [SES SNS 이벤트 형식](https://docs.aws.amazon.com/ses/latest/dg/event-publishing-retrieving-sns-contents.html)
- [SNS 서명 검증](https://docs.aws.amazon.com/sns/latest/dg/sns-verify-signature-of-message-verify-message-signature.html)
