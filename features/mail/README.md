# 메일 발송 — 현재 기준

**개발 배포 확인(사용자 제공 출력 기준, 2026-11-10):** API revision `fadabc0`, 메일 env 파일/컨테이너 일치, 문의 전환 migration·신규 컬럼 2/2, 기존 문의 확인 대기 0건, 외부 `/health` 및 user/release/admin DB 모두 OK를 사용자가 확인했다. 에이전트의 서버 접속이나 독립 HTTP 점검은 없었다. 전환된 내부 메일의 실제 수신과 운영 배포는 아직 확인되지 않았다. [배포 결과·근거](records/2026/11/2026-11-10-ses-dev-merge-and-env.md)의 마지막 절을 우선한다.

**최신 Git 반영(2026-11-10):** Resend→SES 전환을 API `fadabc0`, 인프라 `724185f`로 커밋하여 각 dev에 fast-forward 병합·원격 푸시했다. 로컬·원격 SHA 일치와 검증된 tree 일치를 확인했다. 서버 배포·env 수정·실제 DB migration은 사용자가 수행할 예정이며 에이전트는 실행하지 않았다. [env 정리·개발 배포 명령·통합 검증 기록](records/2026/11/2026-11-10-ses-dev-merge-and-env.md)을 우선한다. 아래 미커밋 표시는 당시 상태의 기록이다.

**최신 후속 상태(2026-11-10):** 관리자 수정11파일을 `e89a8d1`로 커밋하고 로컬 dev에 fast-forward했다. **원격 dev 푸시 완료**이며 로컬/원격이 일치한다. 사용자가 직접 개발 배포 후 관리자 컨테이너 revision=e89a8d1을 확인했다. 화면·HTTP health의 별도 검증과 운영 배포는 이 기록에 포함하지 않는다. 전체3,100개·prod build·리뷰/목업 배포 번들 제외 검증 통과. 별도 작성 세션 파일15개 및 .codex 미커밋 문서는 보존했다. [상세 기록](records/2026/11/2026-11-10-mail-preview-detail-and-compose-handoff.md)의 마지막 절을 우선한다.


**진행 중인 후속 작업 — 미커밋:** 사용자 요청으로 문의 전달·운영자 초대/재초대·비밀번호 재설정의 Resend→SES 전환을 API/인프라 `feat/resend-to-ses-261110`에서 구현했다. 내부 메일은 관리자 발송 현황에서 제외하며 주소는 env 전용이다. 문의 재시도 만료 결과 구분과 중복 방지를 보완했고, 로컬 API 6,283개·인프라 135개·빌드를 통과했다. 독립 검증에서 발견한 만료 경합과 기존 제공자 전환 보호 누락을 모두 수정·재검증 완료했으며 dev 병합·푸시·서버 배포는 하지 않았다. [구현·검증 인계](records/2026/11/2026-11-10-resend-to-ses-handoff.md). 아래의 Resend 유지 설명은 배포된 dev 기준이며 이 미커밋 변경과 구분한다.

최종 정리: 2026-11-10.

메일 자동 이벤트 10종·SES 공통 큐·설정/디자인·광고 동의·발송 내역을 구현하고 네 저장소 dev에 커밋·푸시했다. 사용자는 최신 개발 배포 완료를 보고했다. **운영은 SES/SNS/IAM 리소스 생성만 완료했으며 이번 메일 변경의 코드 배포·DB migration은 아직이다.**

- [세션 종합 기록: 확정 범위·구현·Git 전체 이력·검증·AWS·배포·남은 일](records/2026/11/2026-11-10-mail-session-summary.md)
- [자동 메일 10종의 제목·본문·조건별 생략](records/2026/11/2026-11-10-automatic-mail-template-snapshot.md)
- [전체 SHA·부모·commit별 변경 파일·검증 원본·기본 HTML](records/2026/11/2026-11-10-mail-session-evidence.json)

발신자는 `Clipper <clipper@metabuzz.co.kr>`, 자동 제목은 `[Clipper] `로 시작한다. 환경별 링크는 WEB_BASE_URL을 따른다. 문의 전달·운영자 초대/비밀번호 재설정은 Resend 유지, 탈퇴 완료는 기존 시점의 SES 공통 큐다. 현재 메일 작성 버튼은 비활성화이며 수동 작성 UI와 외부 에디터는 추후다. 기존 회원 광고 수신은 미동의 OFF로 처리한다.

개발 구성 세트/이벤트 대상/SNS는 `clipper-mail-dev` / `clipper-mail-dev-feedback` / `clipper-mail-dev-events`, 운영은 각각 prod를 쓴다. 초기 repo 예시의 `clipper-mail`과 혼동하지 않는다. 운영 실제 자격 증명·SNS 구독 확인·워크 활성화는 아직 별도 작업이다.

## 과거 설계·실행 기록

아래는 당시 상태를 보존한 문서다. ‘19개 후보·트리거 미연결·Resend 이전’은 현재 기준이 아니다. 실행 포트와 프로세스도 현재 보장하지 않는다.

- [초기 구현 계획](records/2026/11/2026-11-09-manual-mail-plan.md)
- [초기 로컬 실행 검토](records/2026/11/2026-11-09-local-review.md)
- [초기 SES 적용 안내 — 현재 배포 명령으로 사용하지 말 것](records/2026/11/2026-11-09-ses-deployment.md)

## 2026-11-10 후속 — 아직 미커밋

[미리보기 링크 차단·상세 패널 UI·유형 정리·작성 재설계 인계](records/2026/11/2026-11-10-mail-preview-detail-and-compose-handoff.md). 관리형 Admin 워크트리에서만 수정했고 3,089개 테스트/prod build를 통과했다. 위 종합 기록의 dev 반영 상태는 이 추가 수정 이전까지다. 메일 유형은 변경하지 않았고 새 작성 채팅은 요구·에디터/화면 대안 컨펌 단계다.

**유형 확정 후속:** 사용자가 **계정 / 결제 / 문의 / 공지 / 광고**를 확정했고, 로컬 발송 현황·상세 패널에 같은 기준으로 반영했다. 기존 자동 기록도 이벤트 ID로 분류한다. 광고 동의/발송 API·DB 기준은 유지, 전체3,099개·prod build 통과. 미커밋·미푸시·미배포이며 [후속 기록](records/2026/11/2026-11-10-mail-preview-detail-and-compose-handoff.md)의 마지막 절을 우선한다.
