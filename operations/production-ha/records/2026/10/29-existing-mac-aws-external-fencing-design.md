# 기존 맥미니 유지: 동기 복제와 외부 전원 차단을 이용한 AWS 자동 전환

작성일: 2026-10-29 (Asia/Seoul). 설계 제안이며, 장비 구매·배포 명세로 확정된 측정 결과가 아니다.

이 문서는 [10월 28일 Linux DB 호스트 기준안](28-local-primary-aws-standby-design.md)의 로컬 실행·차단 방식을 바꾸는 변형안이다. [잔여 기술 감사](28-local-primary-aws-standby-remaining-audit.md)의 COMMIT 경고·작업 인계·백업 검증 요구는 계속 적용한다. 이번 독립 설계 검토에서는 내부 restart 경로와 잠재 writer 이력 두 항목을 보완했다. 실제 장비 동작을 확인했다는 의미는 아니다.

## 목적과 선택

- 로컬 운영 API와 DB의 기존 맥미니 및 macOS를 유지한다. 새 Linux DB 컴퓨터를 구매하지 않는다.
- 회사 정전 또는 회사 업무용 유선 WAN 단절 시, 이미 사용자에게 성공으로 확정한 회원·결제 업무 데이터를 보존하고 사람 승인 없이 AWS로 전환한다.
- 회사 내 기존 메인의 DB와 운영 worker가 계속 실행되지 못하게 하는 최종 수단은 **외부 switched PDU로 해당 맥미니의 AC 전원을 OFF하고 확인하는 것**이다.
- 소프트웨어만 추가하는 안은 채택하지 않는다. macOS/VM 내부의 watchdog, launchd, SSH 종료, HAProxy 차단만으로 물리 호스트/VM의 정지·재개 및 기존 내부 writer까지 독립적으로 차단했다고 볼 수 없다.
- 추천안은 **맥미니 유지 + 관리형 전원 장치 + LTE 관리망 + UPS + AWS 상시 복제본**이다. 새 서버 비용은 없지만 전원·통신 장치, SIM 요금과 구축 비용은 추가된다.
- 서비스 자동 복구는 AWS에서 서비스가 정상 재개되는 시점이다. 본 기준안은 사고 후 맥미니를 **OFF로 유지**하며 자동 전원 ON/자동 로컬 메인 복귀를 하지 않는다. 맥미니 재가동은 별도 복귀 작업이며 AWS 서비스 재개를 막지 않는다. 앞선 일반적인 자동 재합류 제안보다 좁고 안전한 기본 정책으로 명시한다.

비교: (1) 현재 Mac + 내부 종료 스크립트만: 비용이 낮지만 독립 차단 증거가 없어 제외. (2) 현재 Mac + 외부 전원 fencing: 이 문서의 선택. (3) 새 Linux 장비: 사용자 제약으로 제외. 사용자에게 이 세 선택을 다시 정하도록 요구하지 않는다.

## 보호 범위와 가정

정전/회사 WAN 장애 시 AWS의 두 AZ, 양쪽 DB 복제본, etcd 과반수, PDU 및 독립 LTE 제어 경로는 정상이라는 단일 현장 장애 모델이다. UPS는 현장 실측 부하에서 초기 목표 30분 이상 제어 장치를 유지하고, 배터리 상태 저하를 감시한다. 장시간 정전으로 UPS까지 소진된 경우에도 PDU가 재부팅하면 출력은 OFF로 유지해야 한다.

ACK를 받은 완료 업무의 RPO는 0을 목표로 한다. AWS에 한 번도 전달되지 않은 접수 전 요청까지 재구성한다는 뜻이 아니다. 보호되는 접수 기록이 없는 클라이언트 요청은 클라이언트의 동일 요청 ID 재전송이 필요하다. 처리 중 결제는 사전에 AWS까지 복제한 intent로 자동 대조한다.

전원 차단 확인 실패, DCS 과반수 부재, 안전한 동기 복제본 부재에서는 자동화가 쓰기와 승격을 중단한다. 사람의 승인을 기다려 정상 전환하는 구조는 아니지만, 차단 증거가 없는데도 빠른 전환을 위해 강제 승격하지 않는다.

## 실제 구성

현 소스 `web/clipper_infra/db/compose.yml`은 postgres:16-alpine 세 컨테이너(user/admin/release), 직접 PostgreSQL 시작, restart: unless-stopped이다. 이 compose를 그대로 두고 fencing만 붙이는 것은 안 된다.

| 위치 | 구성 |
|---|---|
| 회사 운영 앱 맥미니 | 기존 API와 worker. 새 실행 역할/중복 방지/준비 검사 적용. 생산 writer가 있는 모든 장비를 fencing 대상 목록에 포함한다. |
| 회사 DB 맥미니 | 기존 Linux 컨테이너 실행 환경 유지. 독립 DB 세 개 각각 PostgreSQL 16 + Patroni로 전환. local watchdog은 off; 외부 fencing을 안전 근거로 사용한다. |
| AWS AZ A | user/admin/release DB EC2 각 1대, API/HAProxy/제어 프로세스 EC2 1대. |
| AWS AZ B | 같은 구성. |
| etcd | 회사 1개 + AWS A/B 각 1개, 총 3개. 회사 노드가 없어도 AWS 2개로 과반수. 앱과 동거하는 AWS etcd는 CPU/RAM 및 전용 디스크 예산을 확보한다. 부하 시험 실패 시 분리가 필요하며 비용에 반영한다. |
| 외부 접근 | 고정 ALB → AWS HAProxy 2개 → 정상 시 로컬 API, 전환 후 AWS API. DNS 변경은 전환 경로에서 제외. |
| 전원 제어 | 회사 switched PDU의 지정 출력에 운영 앱 맥미니와 DB 맥미니를 각각 연결. 개발기는 별도 출력/전원. |
| 독립 통신 | LTE 라우터가 AWS A/B 제어 호스트에 상시 WireGuard 터널 2개를 유지. PDU 관리망만 전달한다. |

AWS 초기 토폴로지는 기존안의 8 EC2(6 DB + 2 앱/제어)를 유지한다. 최소 비용 구성이라는 뜻은 아니다. 두 제어 호스트가 한 번에 하나의 제어 작업만 수행하도록 etcd CAS/lease로 직렬화한다. 주 경로가 죽은 뒤 LTE 접속을 시작하지 않고 이미 연결해 둔다.

Apple Silicon 맥미니의 DB 컨테이너가 arm64라면 AWS DB도 Graviton arm64로 맞춘다. Intel 맥미니이면 x86_64로 맞춘다. 실제 실행 architecture를 조사하고 같은 PostgreSQL 빌드 계열·패치·확장·locale을 사용한다. 기존 ARM/Alpine를 근거 없이 x86_64 DB에 물리 복사하지 않는다. 이미지 기반을 바꾸면 최초 이관은 검증된 논리 dump/restore, 이후는 물리 스트리밍 복제다.

회사 DB 장비에 개발 DB도 있으면 해당 장비 전원 차단은 개발 DB도 중지시킨다. 운영 도입 전에 개발 DB를 기존 개발 맥미니로 옮기는 것을 권장한다. 새 컴퓨터 구매는 포함하지 않는다.

AWS 앱은 같은 배포 이미지와 JWT 서명키·암호화키·결제사 설정을 갖추고, S3 파일/현재 DB를 이용해 독립적으로 운영 가능해야 한다. 회사 안의 파일 공유·DNS·프록시·세션 메모리가 AWS 서비스의 필수 의존성이어서는 안 된다.

## 전원·통신 연결과 장치 요구

전원: 벽 전원 → UPS → switched PDU → 운영 맥미니. UPS를 PDU 출력 뒤에 두면 PDU를 꺼도 맥미니가 UPS로 계속 켜져 있으므로 금지한다. LTE 라우터와 관리 스위치는 UPS의 항상 켜진 출력으로 공급하고 fencing 대상 출력에 연결하지 않는다. PDU 자체 관리부도 UPS로 유지한다.

네트워크: 업무용 WAN/VPN과 LTE 관리망을 분리한다. LTE 라우터는 PDU에 직접 연결하거나 독립 관리 스위치를 사용한다. 회사 업무용 공유기·스위치·Mac VM이 LTE 제어의 중계점이면 안 된다. LTE 터널은 PDU 관리 주소만 허용하고 로컬 앱/DB/etcd 트래픽의 우회 경로로 사용하지 않는다. AWS 제어 호스트의 WireGuard 종단은 고정 주소를 사용한다. LTE CGNAT는 라우터가 터널을 먼저 연결하고 keepalive를 보내는 구조로 처리한다.

구매 후보 예시는 APC AP79xx/AP89xx/APDU 계열 switched PDU와 Teltonika RUT241급 LTE/VPN 라우터다. 모델명만으로 적합성을 확정하지 않는다. 국내 전압·플러그·인증·통신사 주파수, 지원 펌웨어, 공급 상태는 실사로 고른다. PDU 필수 기능은 다음과 같다.

1. 출력별 OFF와 현재 출력 상태 조회(인증된 SNMPv3 또는 동등한 관리 API).
2. 즉시 OFF; 재부팅 후 자동 ON인 `power cycle`을 사용하지 않는다.
3. PDU의 전원 복구/재부팅 후 `Never Power UP` 또는 startup OFF. Last Known/기본 ON으로 대신하지 않는다.
4. 예약 ON, ping 실패 후 자동 reboot, 전면 버튼 우회 동작을 통제한다.
5. OFF 명령 접수가 아니라 지정 출력의 OFF 완료 상태를 다시 읽을 수 있어야 한다. 0W 측정만으로 OFF를 판정하지 않는다. 인수 시험에서 실제 출력/대상 장비가 꺼지는지 확인한다.
6. 장비 ID/일련번호와 outlet→Mac 매핑을 고정하고 변경 이력을 남긴다.

클러스터 장애 대응 자동화에는 OFF 기능만 노출한다. 별도 복귀 권한 없이는 ON하지 못한다. PDU에 세밀한 명령별 권한이 없으면 자격증명은 제한된 actuator 서비스만 보관하고 다른 컴포넌트에는 OFF/status API만 제공한다. 단순 UI 제한을 하드웨어 수준 권한 분리라고 주장하지 않는다.

## 복제와 성공 응답

세 DB 각각 local + AWS A + AWS B로 구성한다. Patroni 동적 설정의 초기값은 아래와 같다. 일부만 복사해서 프로덕션 완성 설정으로 사용하지 않는다.

```yaml
synchronous_mode: true
synchronous_mode_strict: true
synchronous_node_count: 2
ttl: 20
loop_wait: 1
retry_timeout: 3
primary_start_timeout: 0
primary_stop_timeout: 3
failsafe_mode: false
check_timeline: true
postgresql:
  parameters:
    synchronous_commit: 'on'
    fsync: 'on'
    full_page_writes: 'on'
```

각 노드의 로컬 설정에는 `postgresql.use_pg_rewind: true` 및 `postgresql.pre_promote: /opt/clipper-ha/pre-promote-gate`를 둔다. checksums 또는 wal_log_hints 등 pg_rewind의 전제도 설정한다. 로컬 Mac 노드에서는 watchdog.mode=off, AWS DB EC2에서는 watchdog.mode=required, safety_margin=-1의 Linux softdog를 보조 보호로 사용한다. AWS 외부 fencing을 softdog와 동일한 보장이라고 섞지 않는다.

정상 상태에서는 로컬과 AWS 복제본 두 개의 디스크 저장 확인을 기다린다.
Patroni는 가용 후보 수가 줄면 synchronous_node_count를 조정할 수 있다. strict는 복제본 0개에서 로컬 단독 성공으로 내려가는 것을 막는 것이지 항상 세 사본을 보장하는 옵션은 아니다. 회사 장애 후 AWS A가 메인이면 AWS B와 동기 복제를 유지한다. AWS 복제본까지 한 개뿐인 상황에서는 새 쓰기 성공을 중단할 수 있다.

앱은 DB 오류가 없었다는 것만 성공으로 판정하지 않는다. 동기 COMMIT 취소 WARNING, 연결 단절, 앱 COMMIT 기한 초과는 결과 불명으로 처리한다. 연결별 warning 수신·취소·종료 상태를 묶는 공통 처리를 모든 보호 업무에 적용한다. statement_timeout만으로 COMMIT 대기 기한이 보장된다고 가정하지 않는다. 완료 상태를 다른 연결에서 재조회하여 성공을 알리는 경로도 필요한 원격 내구성 확인을 거친다.

결제사 승인 호출 전에 주문/사용자/금액/요청 ID/멱등키와 재처리에 필요한 입력을 intent로 저장하고 원격 내구성을 확인한다. AWS 복구 worker는 미완료 intent를 조회해 결제사 결과와 대조한다. 이미 전송된 결제사 HTTP 요청은 Mac 전원을 꺼도 결제사에서 끝날 수 있다. 타임아웃/404만으로 새 멱등키를 만들어 재결제하지 않는다. 회원/결제/이용권 등 서로 다른 DB의 효과는 단계별 멱등 처리하며 분산 트랜잭션으로 간주하지 않는다.

## 이전 메인 차단과 승격: 외부 controller 계약

Patroni 자체는 PDU를 자동 설정하지 않는다. `pre_promote`는 외부 fencing을 붙이는 공식 확장 지점이며, non-zero 종료 시 승격을 막는다. 두 AWS 앱/제어 EC2에서 실행하는 `ha-controller`와 PDU actuator, 그리고 각 DB의 gate 스크립트를 구현해야 한다. Pacemaker를 Patroni와 함께 DB 선출 관리자로 추가하지 않는다.

안전 조건은 `Patroni가 인정한 동기 후보 ∧ 현재 DCS 메인 권한 ∧ 이전 writer 차단 완료`다. controller가 최신 WAL을 추측하거나 수동 force promote로 후보 규칙을 우회하지 않는다.

1. etcd에 `site-mode`, 증가하는 operation generation, 물리 대상 목록, 그리고 DB scope별 **쓰기 가능성을 부여했던 노드들의 이력과 아직 차단이 확인되지 않은 잠재 writer 집합**을 지속 기록한다. 이 기록을 만료되는 leader lease에만 매달지 않는다. 승격 허가를 반환하기 전에 후보 노드를 잠재 writer로 등록한다. 후보를 등록한다고 기존 writer 기록을 덮어쓰거나 삭제하지 않는다. 직후 승격이 실패해도 다음 후보는 그 노드가 실행됐을 수 있다고 보수적으로 처리한다. 다음 후보는 자신을 제외한 미차단 잠재 writer를 모두 차단해야 한다. 초기 bootstrap 때도 동일한 writer 등록을 한다. 이 기록이 없거나 DCS를 잃은 뒤 빈 상태라면 자동으로 새 클러스터로 간주하지 않고 승격을 거절한다.
2. 회사 메인의 lease가 만료되어 AWS 후보가 Patroni 선거를 통과하면 pre_promote가 controller에 현재 lease/후보/operation 정보를 전달한다. controller는 mTLS로 요청자를 인증하고 DCS를 linearizable read로 재확인한다.
3. 같은 세대의 회사 전환은 한 번만 실행한다. site-mode를 FENCING으로 기록하고 로컬 앱 경로를 닫는다. 운영 앱/worker 맥미니 및 DB 맥미니의 지정 출력을 모두 OFF한다. 세 DB가 같은 물리 Mac을 공유하므로 전환도 사이트 단위로 묶는다.
4. 각 대상의 최신 OFF 완료를 직접 조회한다. 이전 세대의 OFF 로그, ping 실패, 명령 접수 응답만으로 통과시키지 않는다. 후보가 바뀌어도 같은 세대의 **계속 OFF로 유지되는** 물리 대상 차단은 재사용 가능하되 현재 상태를 재조회한다.
5. 현재 DCS leader/operation이 여전히 같은지 재확인하고, scope와 후보에 묶인 일회성 승격 허가를 발급한다. 후보 등록과 허가는 CAS로 기록한다. hook도 종료 직전 조건을 재검사한다. 지연된 답변/이전 세대 token은 거절한다.
6. 공통 전원 차단 완료를 기록한 뒤 물리 제어 lock을 해제한다. 각 scope는 자기 잠재 writer/허가를 짧은 CAS로 처리하고 독립적으로 승격한다. 전역 lock을 잡은 채 세 DB 전체 ready를 기다려 다른 scope의 승격을 막지 않는다. AWS DB가 실제 승격되고 읽기·쓰기 및 동기 복제 준비가 확인되면 해당 scope의 실제 writer를 기록한다. 별도 집계기가 세 scope의 준비를 확인한 뒤 서비스 전체 ready를 열고 site-mode=CLOUD_ACTIVE로 둔다.

AWS 자체가 이전 writer인 후속 장애에서는 같은 계약으로 그 DB EC2에 EC2 StopInstances를 요청하고 실제 stopped 상태를 확인한 뒤 다음 노드를 허가한다. 정상 watchdog 강등은 우선 경로지만 EC2 정지 확인을 생략하는 근거로 사용하지 않는다. 이 후속 장애의 RTO는 회사 장애와 별도로 측정하며 EC2 stop 지연을 수초라고 약속하지 않는다.

회사 장애와 동시에 AWS 후보까지 실패해 정지시키면 AWS 한 노드만 남아 strict 정책상 새 쓰기를 재개하지 못할 수 있다. 자동 복제본 생성/재합류는 이 복합 장애를 해결할 별도 회복 경로이며 이 문서에서 구현 완료로 간주하지 않는다. 이번 인수 기준은 정상 대기 중인 AWS 두 사본을 전제로 한 회사 장애다.

제어 작업은 제한된 시간 안에 끝내고 초과 시 hook은 실패한다. 다음 시도는 같은 idempotent OFF 작업을 이어간다. DCS 작업 lock을 잃으면 새 명령/승격 허가를 중단한다. OFF-only이므로 늦게 도착한 동일 전환의 OFF는 이중 메인을 만들지 않지만 복귀와 충돌할 수 있어 복귀 전 모든 진행 중 제어 작업을 종료·차단해야 한다. ON은 자동 장애 대응 경로에 존재하지 않는다.

`pre_promote`는 모든 start/restart를 가로채지 않으며, Patroni 내부의 PostgreSQL restart는 컨테이너 entrypoint를 다시 실행하지 않는다. 이번 장애 전환의 안전 근거는 그 경로를 entrypoint로 가로채는 것이 아니다. OFF 확인 전에는 기존 노드가 restart할 수 있지만 AWS 승격은 금지되고, 실제 OFF 후에는 기존 노드의 어떤 프로세스도 실행될 수 없다. OFF를 계속 유지하고 자동 ON을 하지 않기 때문에 이 경계를 지킨다. entrypoint의 DCS/site admission 검사는 별도 계획 복귀 때의 cold boot 및 기존 raw postgres 자동기동 방지에 사용하는 보조 수단이다. 독립 postgres 기동·pg_ctl promote·강제 failover를 운영 도구에서 제한한다. 자동 ON/자동 로컬 재합류는 이 문서가 보장하는 경로에 추가하지 않는다.

## 장애 감지와 라우팅

- Patroni는 DB 상태/leader lease를 관리한다. AWS HAProxy는 1초 간격 API/DB 준비 상태를 검사한다. CloudWatch 알림은 의사결정의 필수 경로에 두지 않는다.
- 정상 회사 WAN 단절은 local→AWS DCS 과반수 접근도 끊기므로 기존 lease 만료 후 위 자동 전환이 시작된다.
- 복제만 막히고 DCS는 살아 있는 부분 장애는 lease 만료만 기다려서는 해결되지 않는다. controller는 AWS 두 관측점에서 로컬의 보호된 쓰기 probe가 5초 이상 신선하지 않고, AWS 동기 후보와 DCS/전원 제어가 정상임을 확인하면 사이트를 FENCING으로 옮겨 전체 local writer를 전원 차단한다. 그 뒤 기존 lease 만료와 정상 Patroni 선거를 기다린다. 단순 HTTP 500 한 번으로 이 절차를 실행하지 않는다. probe는 프로세스당 한 개만 진행하고 2초 앱 기한과 연결 폐기/서버 세션 정리로 누적을 막는다.
- 전원 단절은 UPS 덕분에 서비스가 계속 정상일 수 있다. 이 경우 유효한 메인을 불필요하게 끄지 않는다. 실제 서비스/WAN/DB가 끊기거나 UPS 저전력에 따른 계획 전환 조건을 만족하면 전환한다. UPS가 DB를 버텨주더라도 fencing OFF는 UPS 뒤에서 실제 공급을 차단한다.
- HAProxy는 고정 ALB 뒤에서 local priority/AWS backup을 관리하고 site-mode 및 현재 DB writer readiness를 함께 확인한다. 기존 HTTP/TCP 연결을 다른 서버에 순간 이동시키지 않는다. POST를 프록시가 무조건 재전송하지 않는다. 클라이언트는 동일 operation ID로 결과 조회/재시도한다.
- worker는 현재 writer의 DB claim/lease와 멱등키를 사용한다. 앱 준비 완료와 기존 결제/AI 작업 대조 완료 시점은 다를 수 있다.

## 속도 목표

초기 Patroni 값의 ttl 하한은 20초다. 완전한 회사 장애에 대해 1~5초 전환을 약속하지 않는다. 외부 fencing을 덧붙였으므로 기존 Linux watchdog 기준의 40초 목표를 측정 없이 재사용하지 않는다.

초기 목표 예산: lease 감지 최악 약 20초 + OFF 및 확인 2~10초 예산 + WAL 적용/승격/다른 AWS 복제본 연결/앱 준비 3~15초 예산. 직렬 단계와 병렬 단계를 실측한다. 회사 장애의 서비스 RTO p95 45초 이하, 인수 시험 최대 60초를 목표로 두며 실패하면 원인을 개선하거나 목표를 수정한다. 이는 장비와 통신 측정 전 설계 예산이지 보장 수치가 아니다. 동시 AWS 장애, 차단 확인 실패, 누적 WAL 지연이 있는 상태에는 이 목표를 적용하지 않는다.

속도를 줄이는 수단은 AWS 앱/DB 상시 실행, LTE 터널 상시 유지, API 키/이미지/캐시 사전 준비, DNS 전환 제거, 지속 WAL 적용, OFF 지연 최소화다. 안전 확인 생략/비동기 전환/강제 승격은 수단으로 사용하지 않는다.

## Mac 실행과 복귀

- macOS 절전·최대절전, Docker VM 수동 pause/resume·메모리 snapshot 복원을 운영 절차에서 제외한다. Docker Desktop Resource Saver는 실행 중 DB를 임의로 자는 기능이라고 설명하지 않는다(기본은 컨테이너가 없는 idle 상태). 운영 설정은 예측 가능하게 고정한다.
- Docker의 재시작 대상은 raw postgres가 아니라 admission 검사와 Patroni로 들어가는 entrypoint다. 현재 compose의 직접 postgres 자동 시작은 교체한다. 관리 GUI/개발 명령으로 옛 컨테이너를 켜지 못하게 별도 배포 프로젝트/권한으로 분리한다.
- 자동 장애 대응은 PDU OFF를 유지하고 AWS에서 계속 운영한다. 복귀 시에는 CLOUD_ACTIVE/로컬 nofailover/라우팅 차단을 유지한 채 제어 작업을 모두 정리하고, 격리된 cold boot 후 필요시 로컬 볼륨 사본을 보존하고 pg_rewind 또는 새 base backup으로 복제본에 합류시킨다. 로컬 데이터를 AWS에 덮어쓰지 않는다.
- 로컬을 다시 메인으로 바꾸는 작업은 별도 계획 전환이다. 그 작업의 허가/전원 ON을 장애 자동 전환용 OFF 권한과 분리한다.
- macOS FileVault 부팅 잠금/로그인 전 Docker 시작 가능 여부는 자동 로컬 재가동에 영향을 준다. 이를 해결하려고 사용자 승인 없이 암호화 해제나 자동 로그인을 도입하지 않는다. 이 조건은 AWS 서비스 자동 복구에는 영향을 주지 않는다.

## 백업과 검증

pgBackRest로 AWS 측에서 주간 full/일간 differential/연속 WAL 보관, S3 versioning 및 별도 계정 immutable 보관, 이전 감사의 restore index·키·WAL 의존성 계약을 유지한다. 백업은 잘못된 삭제/손상 복구용이며 정전 failover 시 백업 복원을 기다리지 않는다.

출시 인수 시험은 다음을 포함한다.

1. 외부 클라이언트가 성공 응답받은 요청 ID와 업무 내용을 기록한다. 회사 전원/WAN 장애 후 AWS의 동일 ID·내용과 대조한다. 결과 불명 요청은 별도 집합으로 추적한다.
2. 업무용 WAN 케이블을 실제 분리하고 LTE 경로로 지정 PDU 출력을 OFF할 수 있는지, AWS 승격보다 OFF 완료가 먼저인지 확인한다.
3. UPS 입력 전원을 끊고, 제어부가 생존하며 PDU 뒤의 Mac은 실제 끊을 수 있는지 확인한다. UPS 뒤/앞 잘못된 배선도 탐지한다.
4. Patroni만 정지, Docker VM pause, macOS/VM 재시작 상태에서도 외부 power fence로 기존 프로세스가 살아남지 못하는지 확인한다.
5. PDU 재부팅/전원 복구 후 출력이 OFF로 유지되는지 확인한다. 자동 reboot/예약 ON이 없음을 검증한다.
6. PDU OFF 응답 유실/실제 OFF 실패/LTE 장애이면 승격하지 않는지 확인한다. 이후 제어 복구 시 사람이 승인하지 않아도 재시도하는지 확인한다.
7. pre_promote 도중 controller/candidate 종료, lease 만료, 응답 지연, 3개 scope 동시 선거, stale permit을 시험한다.
8. COMMIT 대기 취소 WARNING 뒤 command completion, API 타임아웃, 결제 승인 직후 회사 단절, 클라이언트 중복 요청을 시험한다. 성공 오인과 중복 결제/이용권 지급이 없어야 한다.
9. 독립 PG autostart, manual promote, 기존 컨테이너 복원, 잘못된 outlet 매핑이 안전 gate를 우회할 수 없는지 확인한다.
10. 세 DB와 API/worker 실제 부하 및 백업을 동시에 실행하며 RTO p95/최대, WAL 지연, WAN commit 지연을 측정한다. 최소 30회 반복해 표본의 한계를 기록한다.

현장에서 확인할 사실: Mac CPU/RAM와 실제 Docker VM 구현·버전/재부팅 동작, 생산 writer 전체 목록, 실제 전원 배선과 UPS 용량, LTE 신호·통신사 장애 독립성, PDU 모델/펌웨어/원격 OFF 상태 의미, 현재 회선·CIDR·AWS 리소스/권한. 이 값은 사용자가 추측해서 정할 선택지가 아니라 구축 전 inventory와 시험으로 채울 사실이다.

## 근거

- Patroni replication: https://patroni.readthedocs.io/en/latest/replication_modes.html
- Patroni timing: https://patroni.readthedocs.io/en/latest/dynamic_configuration.html
- Patroni pre_promote: https://patroni.readthedocs.io/en/latest/yaml_configuration.html
- Patroni watchdog: https://patroni.readthedocs.io/en/latest/watchdog.html
- ClusterLabs fencing와 독립 전원/통신 경로: https://clusterlabs.org/projects/pacemaker/doc/3.0/Pacemaker_Explained/html/fencing.html
- PDU 전원 복구 시 기본 ON 및 Never Power UP: https://www.se.com/ca/en/faqs/FAQ000267873/
- APC AP7920B 예시: https://www.se.com/us/en/product/AP7920B/apc-netshelter-switched-rack-pdu-1u-1ph-2-3kw-230v-10a-or-2-5kw-208v-12a-8-c13-outlets-c14-cord/
- LTE/VPN 라우터 예시: https://teltonika-networks.com/products/routers/rut241-esim
- PostgreSQL 물리 복제 compatibility: https://www.postgresql.org/docs/16/warm-standby.html
- Docker Resource Saver: https://docs.docker.com/desktop/use-desktop/resource-saver/
- EC2 stop: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html
