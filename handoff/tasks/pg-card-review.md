# 카드사 심사·임시 운영·복원

최종 확인: 2026-09-15 KST. 상태: **외부 심사 결과 대기**.

[전체 작업 현황](../WORKBOARD.md)

## 현재 상태

운영 도메인은 개발 기준 심사용 Client/Admin/API와 m4-prod의 별도 복사DB를 사용한다. 사용자 단건·정기결제 성공, dev주소 미전환, 로고 수정 이후200 확인. 카드사에 URL 전달 완료. 심사 결과 자체는 아직 보고되지 않았다.

## 정본

- [상세 상태·백업·복원](../../implementation/2026-09-15-pg-review-production-cutover-and-rollback.md)
- [실행 명령 전체 부록](../../implementation/2026-09-15-pg-review-production-cutover-commands.md)

실행 공간은 m4-prod `/Users/m4-prod/Documents/projects/clipper-pg-review-20260915`. live.compose.json이 현재 앱 설정, db.compose.json은 별도DB 설정. 기존prod 컨테이너는 stop, DB/이미지태그/환경파일 보존. DB/secret JSON은 원격Git에 올리지 않는다.

## 다음 행동

심사 결과가 오면 기존 운영 이미지로 복원할지 integration을 신규 배포할지 사용자와 선택한다. 런북 §13/§14는 다른 절차다. 무작정 기존prod와 심사를 동시에 시작하면 포트 충돌한다.

## 알려진 제한

현재 심사용 API에는 운영 webhook route가 없다(코드상404예상, 실제전송 미확인). 토스 URL등록은 유지. 최종 로고수정 Client image ID/monitor대상/Admin로그인 확인은 미확보. 기존prod DB dump와 image tar는 이번 전환에서 만들지 않았다. 서버 직접 접속 금지: 사용자가 명령 실행, 에이전트는 방법 안내.

## 갱신 규칙

작업 재개 시 실제 branch/HEAD/미커밋과 아래 근거를 대조한다. 세션 종료 때 상태·중단 지점·다음 행동·검증 한계만 갱신하고, 세부 실행 이력은 날짜별 기록에 링크한다. 다른 작업의 우선순위나 상태를 자동 변경하지 않는다.
