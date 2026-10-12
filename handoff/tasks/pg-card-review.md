# W03 — 카드사 심사・임시 운영・복원

최종 확인: 2026-10-07 KST. 상태: **카드사 심사 완료·라이브 키 발급 사용자 보고 / m4-prod 심사판과 `_review` DB 연결 확인 / 정식 운영 전환 후 임시 스택 제거 예정**.

[전체 현황](../WORKBOARD.md) · [새 MID・키 전환 작업 W06](pg-production-followups.md)

## 현재 상태

사용자가 카드사 심사 완료, 새 MID 2개, 새 테스트/라이브 키 발급을 보고했다. 과거 “심사 결과 대기” 상태는 종료됐다.

10/7 운영 API의 공개 `/payments/review/config`가 `{"mode":"checkout"}`을 반환하고 운영 어드민 정적 HTML은 9/15 빌드였다. 사용자 제공 m4-prod Docker 목록에서도 심사판 Client/Admin/API 3개가 공개 포트를 점유하고 정식 운영 3개는 중지 상태였다. `docker inspect`로 심사 API의 `_review` DB 3개 연결과 구 테스트 키 종류를 확인했다. webhook 등록·실전송은 아직 확인하지 않았다. **심사 완료와 정식 운영 배포 완료는 구분한다.**

9/29 W06에서 [현행 코드·MID 전환 영향 및 서버 read-only inventory](../../implementation/2026-09-29-toss-mid-key-transition-analysis.md)를 작성했다. 현행 dev 코드에는 `/payments/tosspayments/webhook`이 있으나 운영 심사판의 route/이미지/DB 상태는 사용자 실행 출력으로 재확인해야 한다. 새 키 연동·복원·배포·실결제는 미실행이다.

## 이전 운영 구성 — 9/15 기록

심사판은 Client/Admin/API와 m4-prod의 별도 복사 DB를 사용했다. 당시 사용자가 단건·정기결제 성공과 로고 변경을 확인하고 심사 URL을 전달했다.

과거 실행 공간: m4-prod `/Users/m4-prod/Documents/projects/clipper-pg-review-20260915`. 당시 `live.compose.json`과 `db.compose.json`, 기존 prod 컨테이너 stop 및 보존 설정/이미지는 **당시 기록**이다. 현재 상태로 단정하지 않는다.

## 다음 행동

사용자 지시에 따라 정식 `_prod` DB 3개를 전체 초기화하고 최신 앱·라이브 키로 전환한다. 심사용 `_review` DB·앱은 임시 자원이므로 새 운영 앱 검증 후 정리한다. 두 DB 세트의 실제 컨테이너·볼륨을 확인하고, 기존 운영 복원과 새 정식 배포를 구분해 런북을 현재 상태에 맞춘다. 과거 컨테이너를 무작정 동시에 시작하지 않는다.

## 근거·제약

- [심사판 상세·복원 런북](../../implementation/2026-09-15-pg-review-production-cutover-and-rollback.md)
- [과거 실행 명령](../../implementation/2026-09-15-pg-review-production-cutover-commands.md)
- 과거 심사 API의 webhook route 부재 기록은 현행 코드/서버로 재확인한다.
- 서버는 사용자가 실행하고 에이전트는 절차·명령 안내. secret/DB 설정값을 Git에 올리지 않는다.
