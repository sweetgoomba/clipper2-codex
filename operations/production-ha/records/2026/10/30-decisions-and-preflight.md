# 운영 HA 논의 정리 및 PC 사전 확인 — 2026-10-30

현재 단계: 상세 설계 후보와 보호 정책 정리, 현장 장비 확인 직전. 설계·장비 선택을 배포 완료로 표시하지 않는다. 최우선 다음 행동은 선택된 Windows PC의 읽기 전용 사양 수집이다. Linux 설치, 펌웨어 변경, 재시작 시험은 그 결과를 검토한 다음 단계다.

## 사용자 확정 조건

- 로컬 앱·DB 메인, AWS 앱·DB 상시 대기. 올바르게 성공을 확정한 회원·결제 데이터는 회사 정전/WAN 단절 시 보존. 자동 AWS 전환에 사람 승인을 넣지 않는다.
- Apple Silicon Mac mini를 사용 중. 앱 맥미니는 유지 가능. DB 맥미니 유지 대안도 남긴다.
- 전용으로 사용할 수 있는 남는 Windows PC는 한 대. PC 세 대 배치는 제외.
- 공기계 테더링은 제외. Mac 유지 대안에서는 전용 LTE/VPN 라우터를 사용한다. 신규 유선 회선은 요구하지 않는다.
- AWS는 두 AZ에 DB EC2 1대씩(각각 user/admin/release 독립 PG 3개), 앱/HAProxy EC2 1대씩: 총4대. DB 6EC2/전체8EC2는 초기 분리 배치의 과거안이다.
- 한 AWS 리전 안에서 구축. 타 리전 재해 복구·타 리전 백업은 범위 밖.
- 별도 AWS 백업 계정과 그 계정 침해 방어 구조는 범위 밖. 같은 계정 S3, 버전 관리, 백업용 IAM 권한 분리는 사용한다. 별도 계정 면책 보장을 주장하지 않는다. Object Lock 별도 불변 복제본은 이번 기본안에 넣지 않는다.
- pgBackRest: 주간 full, 일간 differential, 지속 WAL archive. 제안 보관 기본값: 주간 full 5세대와 그에 필요한 diff/WAL, S3 noncurrent version 30일. 실제 최저 복원 시점은 만료·스케줄을 포함해 시험하며 정확히30일 보존이라고 오인하지 않는다. 월1회 복원 시험.
- AWS 전환 후 자동 로컬 메인 복귀는 하지 않는다. 로컬 재가입·계획 복귀는 별도 절차.
- 운영 DB는 출시 전 테스트 데이터이므로 초기화 가능. 개발DB/다른 프로젝트 DB는 대상 아님. 외부 방문자에게는 Coming soon을 유지하고 회원가입/API/설치파일도 제한한다.
- 짧은 복구 시간은 계속 최적화하되, 과거의 1~5초 희망치를 반복해서 설명하지 않는다.

## 논의 흐름과 현재 후보

1. 로컬 메인 + AWS 대기 + 동기 복제: 성공 응답 전에 AWS 내구 저장 확인이라는 목표를 설정했다.
2. Patroni/etcd: PostgreSQL별 선출·복제를 관리하는 초기 도구 후보였다.
3. macOS Docker Desktop 안의 감시만으로는 바깥 VM/물리 호스트 정지·재개까지 독립 제어하지 못한다는 한계를 확인했다.
4. Mac 유지 + 외부 PDU: AWS 승격 전에 회사 생산 writer 장비 전원을 OFF하고 확인. 회사 WAN 장애 중 제어하려고 독립 LTE, 정전 중 제어하려고 UPS가 등장했다. UPS는 미복제 데이터를 정전 후 급히 보내기 위한 필수물이 아니다.
5. Windows 제어PC + 휴대폰 USB tether: 신규 유선 공사 없이 독립 연결을 만드는 재활용안이었다. 사용자가 무인 안정성 때문에 제외했다. Mac 대안은 AWS 제어기→LTE/VPN 라우터→PDU 직접 경로이며 별도 Windows 중계PC도 보통 필요 없다.
6. 남는 PC에 native Linux: 로컬이 권한 상실 때 스스로 중단하도록 하면 현장 LTE/PDU/UPS를 필수에서 제거할 가능성이 생겼다.
7. 3PG/1PC watchdog: 세 Patroni가 하나의 Linux watchdog device를 그대로 함께 열 수 없으므로 KVM VM 분리, custom multiplexer, PC3대 대안을 비교했다. PC3대는 현재 제외. VM-only는 물리 호스트 보호와 동일하지 않다.
8. 현재 우선 검증안: Linux PC1대 + PostgreSQL3개 + Pacemaker/Corosync/PAF + diskless SBD1개 + hardware watchdog. Patroni/etcd를 이 안에 중복으로 넣지 않는다. 하드웨어 지원 실패 시 Mac+PDU+전용LTE라우터+UPS 안을 비교한다. 조건부 추천이지 하드웨어 미확인 상태의 최종 플랫폼 확정은 아니다.

## Windows에서 지금 확인

동봉 clipper-ha-windows-inventory.ps1의 내용을 선택한 PC의 PowerShell에 붙여넣는다. 장치 모델·메인보드·BIOS·CPU·RAM·디스크·네트워크 장치명만 출력한다. watchdog 비슷한 PnP 이름은 참고 단서일 뿐이며 유무 판정으로 사용하지 않는다. Windows driver의 watchdog 문자열이 Linux 하드웨어 timer를 증명하지 않는다.

후속: 모델별 제조사 BIOS/매뉴얼과 Linux driver 지원을 조사 → 필요하면 Ubuntu24.04 라이브 환경으로 부팅해 sysfs 확인 → 전용 PC 상태에서 계획된 실제 reset 시험. 설치USB 부팅 자체는 재부팅이므로 지금 출력 명령과 구분한다. 드라이버 로딩·/dev/watchdog 열기·SBD test는 현재 읽기 단계에 포함하지 않는다.

Linux에서 수집할 읽기 전용 자료(설치 여부와 무관하게 호스트 Linux에서 실행):

```sh
uname -m
lscpu
free -h
lsblk -o NAME,MODEL,SIZE,TYPE,FSTYPE,MOUNTPOINTS
lspci -nn
ls -l /sys/class/watchdog
for dev in /sys/class/watchdog/watchdog*; do
  [ -e "$dev" ] || continue
  for field in identity state timeout nowayout; do
    [ -r "$dev/$field" ] || continue
    printf '%s: ' "$dev/$field"
    cat "$dev/$field"
  done
  readlink -f "$dev/device/driver"
done
```

빈 sysfs 결과도 driver 미로드/BIOS 설정 때문일 수 있어 부재 확정으로 쓰지 않는다. `/dev/watchdog`를 열면 timer가 활성화되는 장치가 있으므로 `cat /dev/watchdog`, 임의 `wdctl`, `sbd watchdog test`는 이 단계에서 실행하지 않는다. 실제 timer가 목표 시간 안에 PC를 reset하는 시험이 최종 증거다.

하드웨어 watchdog은 칩셋/보드의 실제 타이머+reset 회로다. Linux driver는 그 회로에 접근한다. 소프트웨어 softdog는 커널 실행에 의존한다. 지원 회로가 없는 PC에 driver만 설치해 물리 회로가 생기지 않는다. 일부 PCIe watchdog 장치나 reset header 연동 장치를 추가할 수 있으나 PC 슬롯/배선/driver에 따라 다르며 범용 USB watchdog이라는 이름만으로 인정하지 않는다.

## 현재 소스 확인 결과

- web/clipper_web_api/src/app.module.ts:44 ScheduleModule.forRoot.
- payments.module.ts:99 PaymentRecoveryScheduler provider.
- payment-recovery.scheduler.ts:32 매분 실행. 예약 최초결제, 갱신, 미완료 주문/이용권 복구, 빌링키 정리, 만료 접근 종료.
- subscription-renewal.service.ts:135 이후 트랜잭션과 구독 잠금;147 주기별 idempotency key;281 charge claim;466 Toss chargeBillingKey.
- typeorm-subscriptions.repository.ts:53 이후 pg_advisory_xact_lock. 스케줄러 running 변수는 한 프로세스 중첩만 막지만 DB 수준의 중복 방지 코드도 이미 존재한다. 없다거나 전체가 HA 검증됐다고 주장하지 않는다.
- web/clipper_infra/db/compose.yml: postgres:16-alpine 3개, restart unless-stopped, pg_isready10초. 복제/선출/fencing 구성은 아니다.
- scripts/deployment.mjs: apps Compose배포, 별도 migrate 동작으로 DB별 migration 실행;운영포트55202/55212/55222 검사, prod Toss live모드 검사.
- ops/monitor/README.md: DB Mac에서30초주기 검사·Slack알림. 회사 외부 자동전환 제어와 동일하지 않다.

## 재사용과 변경 범위

단순히 기존 Compose를 Linux Docker Engine에서 실행하는 것은 가능하지만 HA 목표를 달성하지 않는다. Pacemaker 추천안은 PG3개를 native process로 PAF가 관리하며 기존 DB Compose와 restart 정책을 대체한다. DB명·3DataSource·schema/migration·API image·업무코드는 재사용하고, endpoint/env·포트검사·seed 절차와 백업·HA bootstrap을 보완한다. 서비스 image가 ARM 전용이면 x86 rebuild/multiarch 검증이 필요하다.

사용자 초기화 허용에 따라 ARM PGDATA를 x86으로 이전하지 않고 빈 PG3개→migration→필수 seed→시험 데이터로 시작한다. AWS로 복제할 최종로컬DB가 x86이면 AWS DB도x86; Mac 유지면 실제DBcontainer architecture 확인 후ARM64/Graviton을 맞춘다. Linux설치 자체보다 HA의 공유차단/복제/복귀 시험이 주된 작업이다.

## Linux 기준안 핵심

Ubuntu 24.04 LTS/PostgreSQL 16을 기준 후보로 한다. 물리 office-db와 AWS DB A/B가 세 Corosync 투표 노드다. A-B 통신은 회사를 경유하지 않는다. 과반수는 2/3이며, two-node 예외나 자동 투표 수 축소를 쓰지 않는다. Pacemaker+PAF가 PG 세 개를 별도 승격 가능 자원으로 관리하고, SBD만 현장 하드웨어 watchdog을 소유한다. 별도 PostgreSQL 자동 시작, 절전·최대 절전·과거 메모리 복원은 금지한다.

회사 메인은 AWS 두 사본 모두의 durable flush를 확인한다. AWS A가 메인이면 B, B가 메인이면 A를 확인한다. synchronous_commit, fsync, full_page_writes는 on이다. 회사 메인에서 AWS 한 사본이라도 없으면 쓰기가 대기하는 보수적 정책이며, 임의로 비동기로 내리지 않는다. DB별 최신 안전 후보를 선출하고 세 DB의 메인을 같은 AWS 호스트로 강제로 묶지 않는다. 로컬 PC 한 대에 세 DB를 두는 조건은 유지하며, 앱은 DB별 프록시 접속 주소를 사용한다.

동기 COMMIT의 경고·취소·연결 단절은 결과 불명으로 처리한다. synchronous_commit은 USERSET이므로 권한 REVOKE만으로 고정할 수 있다고 주장하지 않는다. 공통 트랜잭션 처리와 모든 쓰기 경로를 검증한다. 로컬에서 행이 보인다는 사실만으로 원격 저장까지 확정됐다고 추론하지 않는다.

EC2 API 차단 대상은 AWS DB 인스턴스다. 웹 EC2는 DB 차단 대상이 아니다. 고정 버전 fence_aws의 모든 상태 판정 경로를 보완한다. stopping/shutting-down/pending은 미완료, stopped는 차단 완료, terminated는 정확한 기존 ID를 확인했을 때만 종료된 대상으로 취급한다. StopInstances → DescribeInstances 반복 조회 → 기한 안에 stopped 확인 시 성공 순서다. API 오류·ID 불명·시간 초과는 실패이며 승격하지 않는다. status와 action-off 경로 모두 같은 정책을 적용한다. 필요한 경우 상류 agent의 작은 수정본을 유지하고 버전과 변경 내용을 고정한다. IAM 권한은 허용된 DB 인스턴스에 한정한다. 회사 장애 복구 시간과 AWS 정지 지연은 별도로 측정한다.

SBD 자체 차단 시간과 Pacemaker 대기 시간을 실제로 측정한다. 하드웨어 timeout 10초/peer wait 30초는 측정 전 후보값이다. 기능이 있다는 사실만으로 해당 수치를 보장하지 않는다. 초기 회사 장애 복구 목표는 30~60초다. 자동 AWS 복구 후 로컬 재합류·계획 복귀는 별도 절차다. 백업 복원은 정상적인 자동 전환 경로에 들어가지 않는다.

## 배포 전 접근 제한

공개 도메인 clipperstudio.ai는 유지한다. 회사 사설 IP인 192.168.x.x가 아니라 실제 접속의 공인 출구 IPv4/IPv6와 검증용 접속을 허용한다. ALB source-ip 조건으로 회사 테스터는 실서비스에 보내고, 일반 웹 방문자는 Coming soon으로 보낸다. 비허용 사용자의 API·설치파일·업데이트 manifest 접근도 막는다. 화면 버튼을 숨기는 것으로 끝내지 않는다. 앞에 기존 프록시가 있으면 그 접점에서 신뢰 가능한 원본 IP를 판단하고, 원본 서버 직접 접근도 제한한다. 클라이언트가 위조한 X-Forwarded-For를 신뢰하지 않는다.

회사 회선 차단 시험에는 회사 밖의 허용된 시험 접속도 필요하다. 테스트용 AWS VPN 경로나 명시적으로 허용한 외부 테스터 IP를 사용하고, 외부 probe는 인증된 별도 경로를 사용한다. 고정 IP가 없으면 테스터 인증 방식을 병행한다. 결제 webhook·콜백·로드밸런서 상태 검사는 필요한 경로만 예외로 두고 기존 인증·서버 검증을 유지한다. 회원가입 전체를 예외로 열지 않는다. S3/CloudFront 다운로드 원본의 직접 노출도 함께 제한한다.

테스트 초기화 범위는 prod 시험 DB 세 개다. 반복 시험은 Toss 테스트 키/가짜 결제 fixture로 진행한다. 현재 prod=live 검증 스크립트가 있으므로 명시적 HA 검증 프로필을 추가하고 실운영 검증을 조용히 해제하지 않는다. 시험 데이터가 AWS에도 동기 저장되는지 확인한다. 외부 진입 제한을 먼저 만든 후 초기화와 실페이지 시험을 진행한다.

## 장애 범위와 동작

실제 발생률 자료가 없어 백분율을 제시하지 않는다. 아래는 현재 구성에 관련된 장애 모드 목록이다.

| 장애 | 우선순위 | 동작 |
|---|---|---|
| 회사전체정전/차단기 | 자동복구필수 | AWS quorum·안전차단대기·승격 |
| 유선WAN/공유기/스위치/VPN단절 | 자동복구필수 | 로컬자체차단, AWS승격;양방향/한쪽방향모두시험 |
| DB PC종료·OSfreeze·SBD/클러스터프로세스장애 | 자동복구필수 | hardwarewatchdog+AWS안전승격 |
| DB한프로세스crash/OOM | 자동복구필수 | 제한된restart;안전중단불가시호스트차단 |
| 디스크full/read-only/I/Ohang | 안전중단·조건부자동전환필수 | 복제본정상확인후전환;오류같이복제되면복원 |
| Mac API/DockerVM OOM·중단,API프로세스hang | 자동복구필수 | AWS API로전환,DB정상이면현재DB유지가능;DB까지무조건재시작하지않음 |
| 보호된쓰기만막힘,복제단절·대규모lag | 감지·안전정책필수 | async성공금지,준비감시가클러스터전환요청 |
| 반환응답유실·COMMIT취소·부분단절 | 데이터안전필수 | 결과불명,동일요청ID결과조회 |
| scheduler중복/잠금끊김·결제결과불명 | 데이터안전필수 | claim+멱등키+결제사대조 |
| 이전PC재부팅·회선flap | 데이터안전필수 | 로컬자동메인복귀금지,PGDATA재검증 |
| AWS app1대장애 | 자동복구필수 | 다른app로라우팅 |
| AWS DB1대/AZ장애 | 안전정책필수 | 공유된3DB동시영향;필요사본없으면쓰기중지.자동EC2재생성은후속범위 |
| 과반수소실/차단결과불명 | 안전중단필수 | 강제승격금지 |
| 감시프로그램중단 | 감지필수 | 서로다른AWS감시와CloudWatch heartbeat누락알림 |
| WAL보관/backup실패·용량부족 | 감지·복원검증필수 | 재시도·경보·보존가능시점표시 |
| 잘못된DELETE/스키마배포·논리손상 | 복구수단필수 | 자동메인교체로해결안됨,검증된백업/PITR·배포복귀 |
| DNS/TLS/인증설정장애·외부PG/OAuth/S3장애 | 감지·명확한오류필수 | 서버전환으로안고쳐질수있음,재시도/원인별복구 |
| AWS리전전체장애 | 이번제외 | 타리전DR없음 |
| 계정전체침해·백업권한동시상실 | 강화보호이번제외 | 타계정사본없음 |
| 악성공격대규모DDoS·다중독립장애중첩 | 별도정책 | 현재가용성보장범위아님 |

CloudWatch는 로그·지표·알림·감시 프로그램 생존 신호를 담당한다. 필요하면 분 단위 Synthetics를 추가한다. 자동 전환의 핵심 판단은 Corosync/Pacemaker/SBD/PAF 및 HAProxy가 담당한다. 현재 사내 30초 Slack 모니터만으로 회사 정전 감시가 완성됐다고 보지 않는다. 사람이 알림을 읽어야 전환되는 설계가 아니다.

## 접수·성공·요청유실의 구분과 후속 항목

클라이언트 durable outbox는 구현 가능하지만 출시 직전 필수 HA 범위에는 넣지 않는다. 브라우저 IndexedDB/Electron 저장소에 요청 ID와 필요한 최소 입력을 저장하고, 재시작 후 동일 ID로 결과 조회·재전송하는 방식이다. 토큰·결제 비밀키·카드 정보를 무작정 로컬 저장하지 않는다. 브라우저 저장소나 앱이 삭제된 경우까지 복구한다고 약속하지 않는다.

남는 빈틈: 서버가 접수 완료·성공을 응답하지 않은 요청이 회사에만 도착했고 클라이언트 기록도 사라지면 AWS는 그 요청을 알 수 없다. 이는 성공 확정 데이터 보존과 다른 요구다. 원격 접수 기록을 확정하기 전에는 접수 완료로 응답하지 않는다. 결과 조회·안전한 동일 ID 재시도는 필수이며, 앱 재시작까지 견디는 자동 재전송 저장소는 후속 연구로 기록한다.

AWS 입구에서 먼저 영구 접수하려면 ALB만으로는 부족하고 요청 접수 API와 AWS의 영구 DB/큐가 필요하다. 이번에는 새 구성으로 추가하지 않는다. 결제사 호출 전 주문·요청 기록 저장과 결과 재조회는 별도이며 필수로 유지한다.

## 현재할일 순서

1. Windows 사양 출력을 받고 제조사/watchdog 지원을 확인한다. 사용자에게 새 아키텍처 결정을 반복 요구하지 않는다.
2. Linux 호환성과 실제 watchdog reset을 시험한다. 통과하면 Linux 한 PC 안을 상세 구현 계획으로 고정한다. 실패하면 Mac+전용 LTE 라우터/PDU/UPS 대안의 구체 모델을 검토한다.
3. 공개 도메인의 테스터 접근 제한을 구현하고 AWS 네 대·두 AZ·사설 연결·이미지·키·파일 의존성을 정리한다.
4. 초기 PG 세 개와 HA·복제·백업을 구성한다. 기존 DB 초기화 허용을 활용해 migration과 필수 seed를 실행한다.
5. 앱의 성공 판정·작업 소유권·DB 접속 주소·AWS 정지 완료 adapter·준비 감시를 구현한다.
6. 실제 장애 시험에서 성공 요청 보존, 동시 메인 방지, 중복 결제 방지, 안전한 복귀, 복구 시간, 백업 복원을 확인한다.

운영 준비는 자동화된 초기 구성·상태 조회·전환·복귀 절차와 실제 시험으로 구성한다. 서비스 장애의 자동 복구와 장비 수리·잘못된 데이터 복원까지 전부 무인으로 수행한다는 요구를 섞지 않는다.

## 확인한 공식 자료

- [Windows 메인보드 정보 조회](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-baseboard)
- [Linux watchdog API](https://docs.kernel.org/watchdog/watchdog-api.html)
- [Ubuntu Server 설치](https://ubuntu.com/tutorials/install-ubuntu-server)
- [Apple Silicon용 Fedora Asahi](https://asahilinux.org/fedora/)
- [PAF](https://clusterlabs.github.io/PAF/)
- [SBD와 선택적 watchdog 차단](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/configuring_and_managing_high_availability_clusters/configuring-sbd-fencing-in-a-high-availability-cluster)
- [AWS EC2 stopped 상태 waiter](https://docs.aws.amazon.com/boto3/latest/reference/services/ec2/waiter/InstanceStopped.html)
- [ALB listener 조건](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-rules.html)
- [CloudWatch Synthetics 일정](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries_cron.html)
