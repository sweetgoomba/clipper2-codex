# Astra 재감사 수정 실행 기록

설계 기준: `2026-09-17-desktop-pg-safety-implementation-plan.md`, 결함/수정 명세: `2026-09-17-astra-independent-review.md` R01–R13. 사용자는 재감사 결과 뒤 “진행해줘”로 수정·회귀검증을 승인했다. 새 병합/커밋/push/배포/개발 DB 변경 승인은 아니다.

기존 통합 worktree와 HEAD를 유지한다. 새 기능/호환 계층을 만드는 것이 아니라 승인된 정책의 연결 결함을 수정한다. 루트 작업과 독립 파일 소유 범위를 분리해 병렬 진행한다.

## 작업 체크리스트

- [x] R01 서버 policy 조회를 같은 transaction manager에 연결, 유한 pool 및 격리 PostgreSQL 회귀검증. 담당 fix_api_pool.
- [x] R02 시작 응답 유실의 동일 key 복구, 미해결 이전 시도와 새 시도 분리. 담당 root, 교차 리뷰 fix_process.
- [x] R03 Variation 재시도 준비 전 새 job-attempt 연결 저장. 담당 root, 영속 통합 회귀 audit_billing_lifecycle.
- [x] R04 네트워크 이전 terminal/evidence outbox 저장 및 삭제 연결. 담당 root/audit_billing_lifecycle.
- [x] R05 interrupted-from 상태 영속화 및 두 번 부팅 검증. 담당 root.
- [x] R06 spawn 이후 PID/identity 확보 및 exit 이후 보관. 담당 fix_process.
- [x] R07 Nest writer/Electron reader 소유권 계약 일치. 담당 fix_process.
- [x] R08 로그인/네트워크 복구 시 owner별 outbox replay. 담당 root/fix_api_pool.
- [x] R09 Dance/Dialog 최초/재시도 차감 경계 정렬, 교차 검토 중 추가 확인한 예약·취소 경쟁 보완. 담당 audit_billing_lifecycle/fix_process.
- [x] R10 Shortform 미디어/TTS 실제 읽기/디코드·빈 슬롯 검사. 담당 audit_billing_lifecycle.
- [x] R11 Shortform 재시도 preflight를 확인창/예약보다 앞에 연결. 담당 audit_billing_lifecycle/fix_api_pool.
- [x] R12 무료 재시도 새 output_root 격리. 담당 audit_billing_lifecycle.
- [x] R13 서버에서 확인된 과금/환급 뒤 잔액 갱신, 확정 알림 유실 시 정기 재확인. 담당 fix_api_pool.
- [x] 각 regression RED → GREEN 확인, 교차 리뷰, 전체 관련 suite/build 및 격리 smoke. Nest 2,640 / Electron 955 / Web API 2,802 PASS, Angular 관련 226 PASS. 상세 한계는 결과 문서 참조.
- [x] A14 사용자 승인 후 최초 Variation 예약→job별 차감 순서 수정, 취소·삭제 경쟁 guard 및 회귀검증. 기존 R01–R13 변경 보존.
- [x] 결과/한계/미완료 항목 및 WORKBOARD·인계 기록. 설치형 실기와 아래 잔여 검토를 전체 로컬 완료/DB 리허설 전진으로 판정하지 않음.

## 경계 검토

| 경계 | 일치시킬 계약 |
|---|---|
| R01/R02 | 서버 key 멱등성은 유지, 클라이언트가 동일 key로 불명 응답을 복구 |
| R02/R04/R08 | 새 유료 렌더 자동 재개 금지, 과금 통신만 복구하고 실행하지 않은 시도는 환급 |
| R03/R05 | 준비 중단과 결과 불명의 실행 중단을 durable 연결/상태로 구분 |
| R04/R13 | job terminal이 아닌 금융 종결 확인도 UI 갱신 신호 |
| R06/R07 | parent birth identity와 owner-token 기반 child identity를 구분, 두 구현의 child 계산은 동일 |
| R10/R11 | 동일 authoritative preflight를 최초/사용자 재시도 양쪽에서 호출 |
| R12/프로젝트 삭제 | 새 프로젝트 output_root가 옛 프로젝트 디렉터리를 공유하지 않음 |

실제 ML/Build5 HOLD, Windows/Google 로그인 실기는 사용자 실행을 유지한다. 실제 금융 서버 접근 없이 로컬 코드·fake 네트워크·일회용 테스트 데이터만 사용한다. R01의 일회용 Unix-socket PostgreSQL은 기존 DB와 분리한 로컬 검증이다.

## A14 승인 후 보완과 남은 검증

후속 갱신: 두 진단 항목도 사용자 승인 후 수정했다. [최신 수정 결과](2026-09-17-archive-refund-fix-result.md)에 post-charge 삭제 전 환급 outbox 보존·stale attempt fallback 제거·Dialog 테스트 분리를 기록했다. 최종 Nest 전체 2,678, 대상 70, Dialog 20회 반복 모두 PASS. 설치형 실기 및 DB 리허설은 아직 남는다. 아래 미재현 표현은 A14 직후 과거 기록이다.

A14: 사용자 승인 후 preparing job을 먼저 영속 예약하고 각 job에 연결해 차감하도록 수정했다. 예약 공개 뒤 취소·삭제와 차감 시작의 경쟁도 실제 JobsService lock으로 보완했다. [최신 결과](2026-09-17-astra-fix-result.md)에 테스트와 한계를 기록했다. 설치형 UI 실기, 기존 post-charge 삭제→outbox 저장 전 종료의 미재현 위험 확인, Dialog 5ms 테스트 안정성은 남았다. 개발 DB 복제본 리허설은 보류한다.
