# 플러그인 목록 동기화 설계 독립 검증 결과

검증일: 2026-11-18 KST. 검증 세션: [W18 플러그인 카탈로그 동기화 설계 독립 검증](codex://threads/01a1eabf-81d6-7192-bf5e-104f44f7c833).

아래는 새 세션의 최종 검토 응답 원문이다. 검토 응답의 로컬 파일 링크는 원격 SHA의 코드 줄을 설명한 것으로, 작업 폴더 HEAD와 줄 위치가 다를 수 있다. 원격 snapshot은 최초안과 동일하며 실제 실행 검증 결과가 아니다.

**최초안은 수정하는 것이 적합합니다.** 개발 등록과 운영 공개의 분리, 릴리스별 지원 목록, 운영 설정·W19·과금 복구 보존은 유지하되, **Nest 신규 JSON 정본과 등록 단계의 이중 DB 쓰기는 더 작은 방식으로 교체**할 것을 권고합니다.

초안에 기록된 9개 원격 SHA가 현재 기준과 일치함을 확인했습니다. 아래 코드 줄번호는 로컬 HEAD가 아니라 해당 `origin/dev`·`origin/main` 기준입니다. 주요 기준은 Angular `e01cd780`, Nest `c6050407`, Web API `c6c2941f`, Electron `16faddbc`, Infra `8204a11c`, 문서 `ca81fde1`입니다.

**(가) 우선순위별 문제와 근거**

1. **[P1] 과금 승인과 실제 실행 승인을 분리해야 합니다.**

   현재 Web API는 신규 과금 시작에서 등급 허용과 차감을 함께 처리하지만, 이것만으로 PC의 실제 실행을 막지는 않습니다. 기존 요청 재전송은 정책 검사보다 먼저 기존 run을 반환합니다. 이 순서는 응답 유실·과금 복구에 필요하므로 유지해야 합니다. 반환받은 기존 run을 새 실행 허가로 취급해서는 안 됩니다.  
   근거: [operations.service.ts:252](/Users/jina/project/adlight/web/clipper_web_api/src/modules/operations/application/operations.service.ts:252).

   Nest는 과금 후 큐에 넣고, dispatch에서는 로컬 제거 상태를 검사하지만 원격 전체 중지를 확인하지 않습니다. 또한 `LicensePolicyService`는 준비 작업을 허용하기 위해 의도적으로 항상 허용합니다. 여기에 일괄 차단을 넣으면 W19의 설치·준비 허용을 훼손합니다. **별도의 실제 실행 직전 검사**가 필요합니다.  
   근거: [jobs.service.ts:472](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts:472), [jobs.service.ts:837](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts:837), [license-policy.service.ts:9](/Users/jina/project/adlight/desktop/clipper_nestjs/src/core/auth/license-policy.service.ts:9).

   이미 결제된 큐 작업에는 기존 등급·차감 승인을 보존하고, 새로 도입하는 전체 중지·지원 앱 정책을 dispatch에서 확인하는 편이 적합합니다. 잔액이나 변경된 등급을 다시 적용해 동일 작업을 재차 차단·차감하는 설계는 피해야 합니다.

2. **[P1] 공유 worker의 이름으로 사용자 플러그인 중지를 판정할 수 없습니다.**

   랭킹·댓글·숏폼 등의 렌더 작업은 큐에서 모두 `clipper_video_render`가 됩니다. 따라서 `snapshot.pluginName`만 검사하면 랭킹만 중지하기 어렵고, worker를 중지하면 다른 기능까지 영향을 받습니다. **작업을 시작한 사용자 pluginKey를 서버 내부 코드가 결정해 실제 실행까지 전달하는 설계**가 필요합니다. 로그용 `flowName`이나 클라이언트가 보낸 문자열을 권한 정본으로 삼는 것은 부적절합니다.  
   근거: [video-render.service.ts:12](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/video-render/video-render.service.ts:12), [render-job-preparer.ts:16](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/jobs/domain/render-job-preparer.ts:16).

   큐 이외의 직접 실행도 확인해야 합니다. 설명 숏폼은 기존 묶음 run을 재사용하면서 새 과금 시작을 생략할 수 있습니다. 따라서 `Operations.start()`와 공통 큐만 막아서는 전체 중지가 완성되지 않습니다.  
   근거: [explainer-visuals.ts:425](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/shortform/application/explainer-visuals.ts:425).

3. **[P1] 현재 성공 보고는 재전송에 안전하지 않습니다.**

   성공 보고는 `building` 상태에서만 받아들입니다. 성공 저장 후 응답이 유실되면 재전송은 `RUNNER_JOB_NOT_BUILDING`으로 거절됩니다. 초안의 “같은 빌드 키·같은 hash는 성공”을 구현하려면 **inventory뿐 아니라 성공 보고 전체의 재전송 규칙**을 정의해야 합니다. 동일 job의 artifact 해시·inventory 해시가 같으면 기존 결과를 반환하고, 다르면 충돌이어야 합니다.  
   근거: [typeorm-release-runner.repository.ts:65](/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/infrastructure/typeorm-release-runner.repository.ts:65).

   target 공개를 재처리 과정에 섞어서도 안 됩니다. 현재 같은 artifact를 다시 공개하면 이전 target을 rollback 슬롯에 다시 넣어 기존 rollback 대상을 잃을 수 있습니다. 최소 범위에서는 **inventory 재처리가 target 공개를 재호출하지 않게** 하십시오.  
   근거: [typeorm-releases.repository.ts:357](/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/infrastructure/typeorm-releases.repository.ts:357).

4. **[P1] 현재 배포 target과 설치된 앱의 지원 여부를 분리해야 합니다.**

   현재 target은 “지금 다운로드·업데이트로 배포하는 파일”입니다. 이미 설치된 앱의 지원 집합과 같지 않습니다. Windows만 먼저 공개하거나 target을 롤백했을 때, 최신 target 목록만 사용하면 정상 설치 앱의 기능이 사라질 수 있습니다.

   권장 구분은 다음과 같습니다.

   - **배포 가능:** 현재 환경·플랫폼·arch의 target이 제공하는 artifact.
   - **설치 앱 지원:** 해당 설치 빌드의 불변 inventory와 공개·지원 이력.
   - **운영 실행 허용:** 공개·전체 중지·등급 정책.

   같은 버전 재빌드는 `buildNumber` 등으로 구분해야 합니다. Electron에는 이미 buildNumber·artifactVersion·platform·arch가 있지만, 과금 시작 계약에는 앱 빌드 식별자가 없습니다. 서버도 지원 앱을 검사하려면 계약 추가가 필요합니다.  
   근거: [app-info.ts:45](/Users/jina/project/adlight/desktop/clipper_electron/src/main/app-info/app-info.ts:45), [start-operation.dto.ts:28](/Users/jina/project/adlight/web/clipper_web_api/src/modules/operations/presentation/dto/start-operation.dto.ts:28).

   artifact ID는 성공 보고에서 DB가 생성합니다. 따라서 패키지 안에 넣을 식별자는 **패키징 전에 존재하는 build/job 식별자와 inventory hash**를 사용하고 서버에서 artifact에 연결하는 편이 자연스럽습니다.

5. **[P1] 등록 키 전환과 `all`의 의미가 아직 불완전합니다.**

   `REGISTERED_PLUGIN_KEYS`는 실행 허용뿐 아니라 관리자 입력 검증, 등급 포함 관계, `all`의 확장, 공개 요금제 표시에도 사용됩니다. 한 곳만 DB 조회로 바꾸면 결과가 어긋납니다.  
   근거: [effective-access.service.ts:74](/Users/jina/project/adlight/web/clipper_web_api/src/modules/access/application/effective-access.service.ts:74), [product-catalog.service.ts:392](/Users/jina/project/adlight/web/clipper_web_api/src/modules/catalog/application/product-catalog.service.ts:392), [plan-plugin-hierarchy.ts:11](/Users/jina/project/adlight/web/clipper_web_api/src/modules/catalog/domain/plan-plugin-hierarchy.ts:11).

   특히 다음 두 문장은 그대로는 양립하지 않습니다.

   - 신규 ID는 요금제에 자동 허용하지 않는다.
   - `all`은 앞으로 등록되는 모든 플러그인을 허용한다.

   **추천은 기존 `all` 의미를 당장 바꾸지 않고**, 신규 ID의 draft·paused 상태로 실행을 막으며 공개·활성화할 때 `all` 등급에 포함됨을 명확히 확인하는 것입니다. 모든 신규 ID를 등급별 명시 승인 대상으로 만들려면 기존 `all`을 현재 허용 집합의 allowlist로 전환하는 별도 제품 결정이 필요합니다.

   또한 **등록된 ID 집합과 회원 공개 목록은 별개**여야 합니다. 미공개·중지·폐기했다고 기존 허용 설정이나 과거 기록에서 ID를 제거하면 안 됩니다.

6. **[P2] Nest 신규 JSON은 현재 구조에서 최소안이 아닙니다.**

   Angular에는 이미 사용자 기능의 ID·이름·route·분류·순서를 구분하는 등록이 있습니다. Nest 목록에는 사용자 기능과 공유 TTS·렌더 worker가 섞여 있습니다.  
   근거: [app-navigation-metadata.ts:111](/Users/jina/project/adlight/desktop/clipper_angular/src/core/navigation/app-navigation-metadata.ts:111), [plugin-catalog.ts:252](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/plugins/domain/plugin-catalog.ts:252).

   새 JSON을 읽는다고 빌드 순환이 반드시 생기는 것은 아닙니다. 다만 Angular가 Nest 저장소의 새 선언을 소비하는 의존성이 생기며, route와 실제 처리 연결은 여전히 별도로 남습니다. 현재 패키징 순서도 Angular → Nest → Electron입니다. **지금 존재하는 Angular 사용자 등록에서 inventory를 추출하는 편이 변경 범위가 작습니다.**  
   근거: [build-app.mjs:232](/Users/jina/project/adlight/desktop/clipper_electron/scripts/build-app.mjs:232).

   실행기 목록에 존재한다는 검사만으로 구현 완료를 판단해서도 안 됩니다. 가상 workflow의 `run()`은 직접 실행을 거절하므로 실제 기능별 진입점 검증이 필요합니다.  
   근거: [virtual-workflow-executor.ts:46](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/workflows/infrastructure/virtual-workflow-executor.ts:46).

7. **[P2] 성공한 앱 빌드가 현재 서버 지원까지 증명하지는 않습니다.**

   runner snapshot의 Web API 소스는 `runtime_api` 역할입니다. 그 소스에 과금 정의가 있다는 사실과 대상 서버에 해당 정의·정책이 배포됐다는 사실은 다릅니다. 공개 게이트는 **현재 대상 서버의 실제 과금 연결**을 확인해야 합니다. 서버를 먼저 배포하는 단계에서 “모든 과금 ID가 이미 릴리스 inventory에 있어야 한다”는 시작 조건을 강제하면 첫 등록 전 배포가 막힐 수 있습니다.  
   근거: [release-runner.mjs:17](/Users/jina/project/adlight/web/clipper_infra/runner/release-runner.mjs:17).

   또 기존 성공 보고의 `ready` 설명은 “QA 대기”입니다. 이를 기능 검증 완료로 표현하지 말고, inventory 검사와 기존 운영자의 릴리스 공개 승인을 구분해야 합니다.  
   근거: [typeorm-release-runner.repository.ts:130](/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/infrastructure/typeorm-release-runner.repository.ts:130).

**(나) 대안 비교와 추천**

| 방식 | 평가 | 권고 |
|---|---|---|
| 어드민에서 ID 수동 등록 | 구현은 작지만 중복 입력 제거와 릴리스 지원 증거가 해결되지 않음 | 기본 경로로 부적합 |
| Nest에 새 사용자 JSON 정본 | 역할 분리는 가능하지만 새 선언·생성·저장소 의존성이 추가됨 | 최초 선택 교체 |
| 기존 Angular 사용자 등록에서 inventory 추출 | 실제 사용자 목록과 직접 연결되며 현재 등록을 재사용함 | **추천** |
| 회원 PC 보고로 공통 카탈로그 구성 | 개발판·구버전·임의 보고를 운영 정본에서 분리하기 어려움 | 제외 유지 |

추출은 정규식으로 소스를 훑는 제품 구현보다 **기존 순수 메타데이터 export를 읽는 빌드 도구**로 구성하고, 지원하지 않는 선언 형태는 명시적으로 실패시키는 편이 안전합니다. 실행 코드·Python 모델·과금 정의까지 새 파일에 모으지는 마십시오.

서버는 다음처럼 단순화할 수 있습니다.

- **release DB:** 검증된 불변 inventory를 artifact 성공 저장과 같은 트랜잭션에 보관.
- **admin DB:** 운영 이름·분류·순서·공개·중지와 기존 등급 설정 보관.
- **관리자 목록:** release inventory에서 발견된 ID와 admin 설정을 애플리케이션 계층에서 결합. 운영 설정이 없는 ID는 draft·paused로 표시.
- **설정 저장:** 발견된 항목을 선택해 저장하므로 ID 재입력이 없음.

이렇게 하면 성공 보고마다 admin DB에 기술 등록을 복제할 필요가 없어 **`catalogSync=pending/failed`와 그 재처리 절차를 첫 범위에서 제거**할 수 있습니다. DB 간 FK·JOIN도 필요하지 않습니다. 기술 등록을 admin DB에 반드시 물질화해야 한다면 초안의 재처리 모델이 필요하지만, 현재 요구에는 그 필요성이 확인되지 않았습니다.

운영 표시값도 첫 설정 시 기본값으로 초기화하고 이후에는 운영자가 소유하도록 하면 충분합니다. 과거 inventory가 늦게 도착했다고 표시값을 갱신하지 마십시오. 필드별 override·기본값 복원 기능은 선택 사항입니다.

**(다) 반드시 고칠 설계와 선택 가능한 개선**

반드시 명문화할 항목은 다음과 같습니다.

- inventory의 식별 단위는 버전 문자열이나 전체 build 하나가 아니라 **환경·job/artifact·플랫폼·arch**를 포함한다.
- 성공 보고 전체를 멱등 처리하고, inventory 저장과 artifact 성공 기록을 같은 release 트랜잭션에 넣는다.
- 오래된 inventory의 ID 누락은 그 빌드의 미지원일 뿐, 전역 삭제·개인 설정 삭제가 아니다.
- 등록 권한과 운영 공개 권한을 분리한다. 현재 runner 인증은 공유 토큰이며 job별 신원 인증은 아니므로, 기존 수준을 더 강한 보장처럼 표현하지 않는다. 서버가 job에 저장된 snapshot·profile·플랫폼을 기준으로 검증한다.  
  근거: [release-runner-token.guard.ts:9](/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/presentation/release-runner-token.guard.ts:9).
- 신규 실행 검사와 기존 run 조회·응답 복구·정산·환불을 분리한다. 취소·차단 시 기존 terminal outbox와 수량 정산 경로를 재사용한다. 모든 작업을 일괄 `fail()`로 전액 반환해서는 안 된다.  
  근거: [billable-job-attempt.coordinator.ts:197](/Users/jina/project/adlight/desktop/clipper_nestjs/src/modules/operations/application/billable-job-attempt.coordinator.ts:197), [operations.service.ts:394](/Users/jina/project/adlight/web/clipper_web_api/src/modules/operations/application/operations.service.ts:394).
- “진행 중”은 `OperationRun.running`이나 worker 프로세스 가동만으로 판정하지 않는다. 실제 workflow 시작과 큐 대기를 구분한다.
- 공개 여부를 저장할 때의 검사만 믿지 않고, 신규 실행에서도 지원 증거와 현재 운영 정책을 함께 검사한다.

의미 있는 인수 기준은 다음 정도가 필요합니다.

| 검증 시나리오 | 기대 결과 |
|---|---|
| 기존 14개 전환 | ID·현재 제공 상태·등급 허용·하위 포함 ON/OFF·개인 순서 보존 |
| 과금 작업이 없는 새 기능 | 가짜 operation 없이 발견·설정 가능, 설정 전 실행 불가 |
| 한 기능에 여러 과금 작업 | 사용자 카드는 하나이며 각 작업의 기존 과금 유지 |
| 성공 저장 후 응답 유실 | 같은 보고 재전송 성공, artifact·inventory 중복 없음 |
| 같은 job에 다른 내용 전송 | 충돌, 기존 성공 결과 불변 |
| Windows 선공개·Mac 실패 | Mac 지원을 추정하지 않으며 Windows 지원 증거 보존 |
| 이전 inventory 역순 수신·target 롤백 | 전역 ID·운영 중지·운영 표시값·설치 이력 불변 |
| 결제된 큐 작업을 dispatch 전에 중지 | 처리기 미호출, 기존 복구 경로로 한 번만 정산·반환 |
| 과금 응답 유실 후 전체 중지 | 원래 run 조회·복구 가능, 새 실행은 허가하지 않음 |
| 직접 실행·묶음 run 재사용·무료 local 실행 | 지원 앱에서는 실제 실행 경계에서 정책 검사 |
| 서버 연결 실패·재시작 | 결과·설치 상태 조회 유지, 보류 작업의 임의 실행·중복 환불 없음 |

선택 가능한 개선은 자동 재시도 작업, 더 세분화된 공개 권한, per-build 지원 철회, 필드별 기본값 복원입니다. 첫 단계에 메시지 버스·강제 푸시·독립 플러그인 업데이트·범용 실행 계약을 추가할 필요는 없습니다.

**(라) 개발 → 등록 → 설정 → 배포 → 공개의 권장 흐름**

1. 개발자가 기존 Angular 사용자 등록과 실제 화면·처리 코드를 추가합니다. 과금이 필요하면 기존 Operations에 연결합니다.
2. 대상 서버가 신규 계약·과금 작업을 먼저 지원하도록 준비합니다.
3. 동결한 snapshot에서 사용자 inventory를 추출하고 route 연결·실제 기능 경로·플랫폼 포함 여부를 검증합니다.
4. 동일 inventory를 패키지에 포함하고, 패키징 후 hash 일치를 확인합니다. 설치 파일 업로드 후 기존 성공 보고로 보냅니다.
5. 서버가 artifact와 inventory를 함께 저장합니다. 어드민은 새 ID를 draft·paused 상태로 발견해 보여줍니다.
6. 운영자가 이름·분류·순서와 기존 `/plans`의 허용 등급을 설정합니다. 과금 연결은 현재 서버 정의를 확인합니다.
7. 기존 릴리스 관리에서 플랫폼별 artifact를 target에 공개합니다. 이어 별도 카탈로그 공개·활성화 동작을 수행합니다.
8. 앱은 자기 빌드의 실제 구현 목록과 서버 카탈로그를 결합합니다. 탐색·설치·준비는 W19대로 허용하고, 신규 실제 실행에서 정책을 확인합니다.

초기 이전은 **서버·어드민 준비 → 기존 14개 설정 보존 → W18 지원 앱 배포·inventory 확인 → 앱 소비 전환 → 최소 지원 정책 적용** 순서가 적합합니다. 과금 정의에서 키를 유도하는 기존 경로는 관련 소비처를 모두 전환한 뒤 제거해야 합니다.

**(마) 제품 결정이 필요한 항목과 검증 한계**

다음은 확정 요구와 구분해 결정해야 합니다.

- **제안:** 이미 실제 시작한 workflow는 완료시키고, 대기 작업은 중지한다. 묶음 작업의 후속 단계·재시도를 어디까지 같은 workflow로 볼지 확정이 필요합니다.
- **제안:** 서버 연결 실패 시 신규 관리 대상 실행을 보류한다. 무료 local 기능까지 온라인 확인을 필수로 할지는 UX 결정입니다.
- **필수 결정:** target 롤백이 배포만 되돌리는지, 이미 설치된 해당 빌드의 지원도 철회하는지. 기본 추천은 두 동작의 분리입니다.
- **필수 결정:** Windows·Mac 비동시 공개를 허용하는지.
- **필수 결정:** `all`의 동적 의미를 유지할지, 명시 allowlist로 전환할지.
- **필수 결정:** 미공개 전환이 기존 설치자의 새 실행도 중지하는지. 전체 중지와 독립 상태라면 효과도 구분해야 합니다.

정적 대조 결과 Angular 사용자 목록·웹 표시 목록·과금 소속의 **14개 ID 집합은 일치했고 과금 작업은 18개**였습니다. 현재 `catalog_plugin_settings`는 등급 포함 설정용 단일 행이며, 기존 플러그인별 공개 상태 테이블은 아닙니다. 초기 공개 상태는 없는 DB 값을 복사하는 것으로 설명하지 말고 현재 제공 동작을 보존하는 이전 규칙으로 정의해야 합니다.

인접 모바일 설계는 PC 처리기의 원격 기능 설명·입력 계약이며 W18 전체 목록 동기화의 구현 근거가 아닙니다. §7-P1의 공유 계약·Python manifest 정본화도 별도 과제로 유지하는 것이 적합합니다.

파일·제품 코드·DB·빌드·배포·커밋·브랜치는 변경하지 않았습니다. 이번 검토는 원격 소스와 문서의 정적 분석이며, 빌드·실행·장애 주입 검증은 수행하지 않았습니다. 정책을 확인하지 않는 옛 앱이나 변조된 클라이언트의 무료 local 실행까지 서버에서 강제 차단할 수 있다는 보장은 할 수 없습니다.

## 수정안 재검증 원문

앞선 P1/P2는 대부분 반영됐습니다. **확정 전 두 곳을 보완하면 사용자에게 설명할 권고안으로 적합합니다.**

**1) 반드시 보완할 부분**

- **실제 공개 이력의 저장을 명시해야 합니다.** §7은 현재 target과 설치 앱의 공개 이력을 구분하지만, §4에는 그 이력을 어떻게 보존할지 빠져 있습니다. 현재 target은 변경 가능하고, 공개 이벤트 기록은 target 트랜잭션 밖에서 실행됩니다. 최소 수정은 **최종 배포 채널에 처음 공개한 사실을 artifact에 기록하고 target 변경과 같은 release 트랜잭션에서 저장**하는 것입니다. 예를 들어 `firstPublishedAt`과 공개 채널을 보관하면 롤백 후에도 설치 앱의 지원 근거가 남습니다. 감사 로그만으로 판정하지 마십시오. 근거: [typeorm-releases.repository.ts:357](/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/infrastructure/typeorm-releases.repository.ts:357), [releases.service.ts:278](/Users/jina/project/adlight/web/clipper_web_api/src/modules/releases/application/releases.service.ts:278).
- **§6의 “중지 해제는 기존 공개 상태 … 복원” 표현을 고쳐야 합니다.** 중지 중 공개를 취소한 경우, 해제가 예전 `published` 상태까지 되살리는 것으로 읽힙니다. “중지 해제는 execution만 enabled로 변경하며, 현재 공개 상태와 요금제 설정은 변경하지 않는다”로 명확히 하면 됩니다. 근거: [수정안:98](/Users/jina/project/adlight/.codex/features/plugin-catalog/records/2026/11/18-catalog-sync-recommended-design.md:98).

**2) 앞선 검토 대비 반영 결과**

Angular 기존 등록 추출, artifact·inventory 동일 트랜잭션, admin 기술 복제 제거, 성공 보고 전체 멱등성은 최초안의 중복과 복구 부담을 줄였습니다. `originPluginKey`, 직접 실행·묶음 run 재사용 검사, 이미 결제된 큐의 원래 승인 보존, 정산·복구 경로 분리도 앞선 실행 제어 지적을 반영했습니다.

`all`의 동적 의미와 공개 시 영향 확인, 현재 서버의 실제 과금 준비 확인, 플랫폼별 공개 및 롤백과 설치 지원의 분리도 정리됐습니다. 제품 기본값을 제안으로 명시하고 범용 계약 통합·독립 업데이트를 제외한 점도 적절합니다.

**3) 설명할 설계안으로서의 판단**

위 두 보완을 조건으로 적합합니다. 큰 구조를 다시 바꿀 필요는 없습니다. 다만 실제 실행 경계의 누락 여부와 장애·과금 복구는 §11의 인수 검증으로 확인해야 합니다. 이번 판단은 **설계 검토이며 사용자 승인이나 구현 검증을 대신하지 않습니다.** 파일·코드·DB·빌드·배포는 변경하지 않았습니다.

