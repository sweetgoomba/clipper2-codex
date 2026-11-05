# Production HA

## 현재 기준과 전체 진행 기록

[회사 조사부터 전체 운영 서비스 AWS 전환까지의 전체 기록](records/2026/11/03-aws-production-cutover-full-record.md)을 먼저 읽는다. 2026년 11월 2일부터 3일의 결정 변경, 자원 구성, 실행 순서, 오류 수정, 실제 검증과 보존 경로를 포함한다. 이 문서가 아래 과거 설계와 조사 기록보다 최신 운영 상태다.

마지막 실제 검증 기준으로 운영 고객 웹과 www 및 관리자와 API는 모두 Route 53 DNS로 ALB에 진입하고, ALB의 HTTPS 기본 작업은 AWS 8081 대상 그룹 한 개로만 전달한다. 앱 EC2 두 대가 모두 서비스하며 DB-a의 세 PostgreSQL은 주 DB, DB-c의 세 PostgreSQL은 TLS 비동기 복제본이다. 회사 클리퍼 운영 고객 웹과 관리자 및 API와 DB 세 개는 모두 정지했고 재시작 정책은 no다. 원본 데이터와 컨테이너는 보존했다. 개발 도메인과 다른 회사 서비스는 기존 환경을 유지한다.

회사의 기존 API와 DB를 단순 재시작하거나 ALB만 회사 경로로 되돌리면 안 된다. AWS에 새 변경이 있으므로 회사 재가입은 최신 AWS 데이터로 전체 재복제하고 쓰기 메인 전환을 별도로 수행해야 한다. 현재 자동 장애 감지와 fencing 및 자동 승격은 구축하지 않았다. 비동기 복제의 순간 지연 0을 상시 무손실 보장으로 해석하지 않는다.

- [자원과 최종 설정 JSON](records/2026/11/03-aws-production-resource-inventory.json)
- [배포 산출물과 스크립트 체크섬](records/2026/11/03-aws-production-artifact-manifest.csv)
- [시간순 대화 근거 색인](records/2026/11/03-aws-production-conversation-index.csv)
- [최초 공유기 포트포워딩 목록](records/2026/11/03-office-router-forwarding-inventory.csv)
- [실제 전환 원장](records/2026/11/03-aws-production-cutover-ledger.txt)

## 2026-11-02 API 요청 경로와 수동 전환 개념

[설치형 앱의 API 요청 경로와 ALB 전환 설명](records/2026/11/02-api-request-path-and-alb-transition.md)은 전환 전 회사 경로와 단계별 개념을 설명한 이력이다. DNS와 HTTP 전달, Host와 SNI, 프록시 순환 방지, 루트 도메인 Alias 지원 조건을 참고하되 현재의 완료 상태는 위 11월 3일 전체 기록을 따른다.

## 2026-10-30 자동 HA 논의 이력

설계 기준은 [2026-10-30 논의 정리·사전 확인](records/2026/10/30-decisions-and-preflight.md)이며, 이후 장비 식별 결과와 발표 흐름은 [팀 설명용 화이트보드 자료](records/2026/10/30-team-whiteboard-briefing.md)에 반영했다. Windows에서 BIOSTAR A520MT와 AMD SMBus 1022:790B rev 61을 확인했고, Linux sp5100_tco 드라이버의 탐색 대상임을 확인했다. 다음 현장 단계는 USB 확보 후 Ubuntu 체험 환경의 watchdog 인식 확인과 실제 리셋 시험이다. Linux 플랫폼 확정은 이 검증 이후다.

- AWS EC2 네 대(두 AZ에 앱 하나+DB 하나씩). 각 DB 호스트에 user/admin/release 독립 PostgreSQL 세 개를 둔다.
- 조건부 우선안: native Linux PC 한 대+Pacemaker/Corosync/PAF+diskless SBD+실제 하드웨어 watchdog. 장비 검증 후 확정한다.
- 대안: 기존 Apple Silicon Mac+전용 LTE/VPN 라우터+원격 전원 PDU+UPS. 공기계 테더링과 PC 세 대 배치는 제외한다.
- 타 리전 재해 복구와 별도 백업 계정은 범위 밖이다. 같은 계정 S3에 pgBackRest 주간 full/일간 diff/지속 WAL을 보관한다.
- AWS 자동 전환 후 자동 로컬 메인 복귀는 없다. 출시 전 prod 시험 DB 초기화가 가능하며, 공개 도메인의 테스터 접근 제한을 먼저 구성한다.

[Windows 읽기 전용 사양 확인 스크립트](records/2026/10/clipper-ha-windows-inventory.ps1)

과거 문서는 논의 이력이다. 아래 문서의 8 EC2, 별도 백업 계정, 공기계 연결, 신규 Linux 장비 구매 요건을 최신 합의로 읽지 않는다.

- [10월28일 초기Linux/Patroni안](records/2026/10/28-local-primary-aws-standby-design.md)
- [10월28일 잔여기술감사](records/2026/10/28-local-primary-aws-standby-remaining-audit.md)
- [10월29일Mac외부차단안](records/2026/10/29-existing-mac-aws-external-fencing-design.md)
