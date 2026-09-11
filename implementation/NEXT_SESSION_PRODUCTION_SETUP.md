# 버전 B — 전체 운영 구축 세션 (개발 전환 제외)

**2026-09-10 갱신:** 시작 시 [현재 상태 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md)와 [리소스 관리 검토](./2026-09-10-plugin-resource-management-review.md)를 먼저 읽는다. 아래 초기 미승인/미배포는 과거 기준이다. 현재0.0.3.7 CPU 표시 확인과 Build5/실제 플러그인 HOLD를 구분한다.

작성: 2026-09-09. 아래 블록을 새 세션에 붙여넣는다. TASKS.md 5번 중 개발 전환을 제외한 범위다.
라이브/식별자처럼 별도 승인이 필요한 항목은 준비·검토와 실제 전환을 구분한다.

```text
Using Superpowers.
Clipper 전체 운영 구축의 남은 작업을 이어가자.
별도 세션에서는 결제·환불 등 TEST PG 기능 검증을 진행할 예정이야.
이 세션은 TASKS.md의 “5. 전체 운영 구축 — 남은 범위” 중 개발 전환을 제외한 항목을 담당해.

먼저 아래 문서를 읽어줘.
0. /Users/jina/project/adlight/.codex/implementation/2026-09-10-current-state-and-resource-dashboard-audit.md (후속 결과 우선)
1. /Users/jina/project/adlight/.codex/implementation/2026-09-08-production-pg-session-closeout.md
2. /Users/jina/project/adlight/.codex/implementation/TASKS.md
상세 절차는 위 문서에 연결된 Infra 운영 매뉴얼을 참고해.

9/8 마지막 확인 배포는 Customer888c2b9 / Adminfb3e532 / API2710301이야.
이 값은 과거 확인값이므로 현재 원본 저장소 Git 상태와 미커밋 문서를 먼저 확인해줘.
원본 web/desktop이 작업 정본이고 .integration-clones는 건드리지 마.

이 세션 범위:
1. 운영 desktop 환경 분리: 이름/아이콘/appId/protocol 결정사항 확인,
   API/JWT/로그인/업데이트/userData/Keychain/모델·캐시/포트 분리.
2. 운영 runner 컨테이너·포트·env·작업/output·S3 prefix·Release 분리 및 빌드 검증.
3. 운영 Admin→runner→S3→Customer 다운로드→Windows/Mac 설치·개발판과 공존·업데이트 검증.
4. 운영 모니터·알림, 백업·복원, 정전·재부팅 복구, DB 접근·로그·비밀관리.
5. Google 게시/검증·지원메일/소유자와 Toss 계약/심사·live키/MID·테스트데이터 정책 준비.
6. 최종 branch/PR 통합 계획, desktop 원격 상태, Infra 운영 문서 검토·팀 공유 준비.
7. 라이브 실결제/취소 검증·정식 공개는 PG 테스트 결과와 연결해 전환 조건을 정리하되,
   실제 키 전환·거래·공개 결정은 별도 승인을 받은 뒤 진행.

개발 전환 항목은 제외해. 개발 DB 복제·마이그레이션·데이터 정리도 지금 시작하지 마.
기존 운영 웹/API/DB/HTTPS/로그인은 이미 구축돼 있으니 새로 초기 구축하지 마.
PG 테스트 계정·주문·환불·크레딧 상태는 이 세션에서 변경하지 마.

먼저 현재 구성과 TASKS 5번의 각 항목을 “진행 가능 / 결정 필요 / 별도 승인 필요”로 정리해줘.
이어 운영 desktop/runner의 환경 분리 현황과 결정된 값·미정인 값을 확인하고,
바로 수행할 수 있는 로컬 조사·구현·검증부터 진행해줘.
기존 개발판 보존과 운영앱 공존이 원칙이야. 과거 appId/protocol 제안을 확정값으로 쓰지 마.
결정이 필요한 항목은 구체적인 선택안과 영향을 준비하고, 독립적으로 진행 가능한 작업은 계속해줘.

두 세션이 같은 원본 저장소를 공유할 수 있으니 수정 전 현재 diff를 확인하고 다른 세션 변경을 보존해.
다른 세션과 같은 파일을 수정하거나 같은 서비스 배포·재시작이 필요하면 대상과 영향을 먼저 알려줘.
작업 기록은 이 세션 전용 파일에 남기고 TASKS.md는 담당 항목만 수정해. 공유 문서 전체를 덮어쓰지 마.

이 세션 전용 기록: /Users/jina/project/adlight/.codex/implementation/2026-09-09-production-setup-log.md
이 기록은 작업을 실제로 시작할 때 생성해. 구축/배포/설치검증을 각각 구분해서 기록해줘.
PG 테스트 도중 공용 운영 서비스 재시작·호스트 재부팅·DB 복원·키/웹훅 변경이 필요하면
PG 세션의 진행 상태를 확인하고 작업 시간을 조율한 뒤 사용자 실행 단계로 안내해줘.

서버 명령은 실행 장비·경로·영향을 설명하고 한 단계씩 알려줘. 내가 직접 실행할게.
개발 전환은 이번 두 세션 모두 범위 밖이야. 개발 서버·개발 DB·개발 데이터 전환 작업을 진행하지 마.
운영 DB 재생성은 이미 끝났으니 다시 초기화하지 마.
라이브키 전환·실결제와 desktop 앱 식별자 변경은 별도 승인 없이 진행하지 마.
기존 개발판 앱·runner·데이터·캐시를 변경하거나 삭제하지 마.
.codex의 기존 ahead 커밋이나 다른 세션의 미커밋 변경을 임의로 묶어 커밋·푸시하지 마.
```
