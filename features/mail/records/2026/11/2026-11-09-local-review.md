# 메일 기능 로컬 실행 환경

> **2026-11-10 현재 기준:** 이 문서는 초기 단계의 과거 기록입니다. 현재 10개 자동 이벤트는 실제 연결·dev 반영을 완료했고, 문의 전달·운영자 초대/재설정은 Resend를 유지합니다. 사용자는 최신 개발 배포 완료, 운영 SES/SNS/IAM 생성만 완료를 보고했습니다. [종합 기록](2026-11-10-mail-session-summary.md)과 [현재 색인](../../../README.md)을 먼저 확인하세요. 아래 초기 리소스 이름·배포 지침·미커밋/미연결 상태를 현재 기준으로 실행하지 마세요.

## 실행 중인 주소

- 시작 페이지와 받은 메일함: http://localhost:4555
- 관리자 웹: http://localhost:4202/mail
- 고객 웹: http://localhost:4201
- 고객 계정 테스트 로그인: http://localhost:4555/open/client
- 신규 가입/선택 동의 확인: http://localhost:4555/open/signup
- API 상태: http://localhost:3000/health
- 관리자 계정: admin@clipper.test / ClipperLocal!2026 (이 로컬 DB 전용)
- 고객 계정: member@clipper.test (위 테스트 로그인 링크로 접속)

관리자·고객 웹 모두 local 설정(useMocks=false)으로 실행한다. 실제 API와 신규 PostgreSQL에 데이터를 저장한다. 메일은 AWS SDK의 AWS_ENDPOINT_URL을 http://127.0.0.1:4555로 지정해 이 컴퓨터의 받은 메일함에만 저장한다. 로컬 받은 메일함은 SES API 요청 형식을 받고 응답하므로 실제 작성/확정/작업 큐/SDK 경로를 검토할 수 있다. 실제 AWS 발송 권한·DKIM·외부 수신함 도달은 이 환경의 검증 대상이 아니다.

## 새 로컬 DB

- PostgreSQL 15, host 127.0.0.1, port 55449, user clipper_mail_local
- DB: clipper_mail_local_user / clipper_mail_local_admin / clipper_mail_local_release
- 데이터 폴더: /private/tmp/clipper-mail-local-pg
- 기존 DB나 운영 데이터는 사용하지 않았다. 전체 마이그레이션 적용 완료(관리자 116개 포함).
- 테스트 회원 5명, Basic 구독/Pro 해지 예약 예시, 공통 디자인, 작성 예시 2개를 넣었다. 실제 검증 과정에서 새 가입 회원과 발송·취소 기록도 추가됐다.

## 로컬 실행 파일

환경파일과 개발용 서명 키: /private/tmp/clipper-mail-local/ (서버 비밀 파일은 0600).

DB가 꺼졌다면:

```sh
/opt/homebrew/opt/postgresql@15/bin/pg_ctl -D /private/tmp/clipper-mail-local-pg -l /private/tmp/clipper-mail-local-pg.log -o '-h 127.0.0.1 -p 55449 -k /private/tmp' start
```

각 서비스를 다시 띄울 때 별도 터미널에서 실행한다(이미 실행 중이면 중복 실행하지 않는다).

```sh
node /private/tmp/clipper-mail-local/run.mjs api
node /private/tmp/clipper-mail-local/run.mjs client
node /private/tmp/clipper-mail-local/run.mjs admin
node /private/tmp/clipper-mail-local/run.mjs sink
```

첫 초기화 파일 prepare-env.mjs는 서명 키를 새로 만들므로 재시작 때 다시 실행하지 않는다. 실행 파일과 DB는 임시 폴더에 있으므로 시스템에서 임시 파일을 정리하면 재구성이 필요하다.

로그: /private/tmp/clipper-mail-local-api.log, -client.log, -admin.log, -mailbox.log. HTTP/브라우저 검증 결과: /private/tmp/clipper-mail-local-check.log, /private/tmp/clipper-mail-local-browser.log.

## 분기 기준 확인

새 기능 브랜치를 만들지 않았으며 기존 각 로컬 dev 체크아웃의 미커밋 변경이다. 2026-11-09 원격 fetch 후 비교:

| repo | 작업 기준 로컬 HEAD | 최신 origin/dev | 뒤처진 커밋 |
| --- | --- | --- | --- |
| API | 7922d050 | c85fd18c | 67 |
| 고객 웹 | ea1b985 | 9b7165b | 49 |
| 관리자 웹 | 13b0568 | bb2bca7 | 21 |
| 인프라 | fe24f61 | 1141985 | 15 |

원격 변경은 병합하지 않았다. 기존 작업을 보존한 상태로 현재 메일 구현을 띄웠다. 최신 원격에 추가된 탈퇴·운영 화면 등과의 통합 검증은 별도 필요하다.

## 검증 결과

- 실제 로컬 API: 관리자 인증/권한, 요금제·구독 상태 수신 대상, 일반/광고 메일 발송과 로컬 수신, 광고 동의 대상 제한, 제목 광고 표시, 예약 취소, 수신거부, 가입 동의 저장 확인.
- 브라우저: 관리자 로그인→작성→미리보기→확인창 취소/확정→발송 내역, 예약/취소, 공통 디자인, 고객 계정 토글 저장, 선택 동의 미체크 시 가입 가능, 체크 후 실제 가입 완료와 계정 설정 반영 확인.
- localhost 수신거부 링크를 위해 NODE_ENV=development에서만 HTTP loopback 주소를 허용. 운영은 HTTPS 조건 유지. 관련 회귀 테스트 후 API 전체 5,331개 통과(기존 환경 선택형 190개 제외).
- 운영 AWS/IAM/환경변수/DB/배포는 수정하지 않았고 실제 외부 메일을 보내지 않았다.

## 메일 화면 보완

- [자동 발송 설정](http://localhost:4202/mail?tab=automatic): 19개 이벤트와 오른쪽 편집 패널. 본문/제목 저장과 미리보기만 연결되어 있으며 실제 이벤트 발송은 미연결이다. 관리자 DB migration `1794180100000-CreateMailEventTemplates` 추가 적용.
- 세 번째 탭 [공통 디자인](http://localhost:4202/mail?tab=design): 로고 업로드와 너비 슬라이더, 정렬/여백/배경색, 하단 문구 내 링크, 변경 즉시 미리보기. 저장한 로고는 SES SDK에 CID 인라인 첨부로 전달되며 로컬 메일함에서도 표시한다.
- 가입 설명 문구를 선택 체크 항목 안으로 이동. 실제 브라우저에서 한 번만 표시되며 체크 항목 아래에 정렬됨을 확인했다.
- 추가 검증 스크립트: `/private/tmp/clipper-mail-local/correction-browser-check.mjs`, `check-corrected-mail.mjs`. 별도 PostgreSQL 테스트 16개 통과 후 테스트 서버55439 종료; 리뷰용55449 유지.
