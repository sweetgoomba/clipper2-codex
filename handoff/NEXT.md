# 다음 세션 시작 안내

## 2026-11-10 메일 세션 재개 기준

먼저 [메일 종합 인계](../features/mail/records/2026/11/2026-11-10-mail-session-summary.md)를 읽는다. 4repo dev 커밋·푸시와 다른 결제 채팅의 통합은 완료했으며 사용자는 최신 개발 배포 완료를 보고했다. 운영 SES/SNS/IAM은 생성만 했고 이번 메일 코드/DB는 아직 운영 미배포다. prod 구성 세트 clipper-mail-prod, 실제 자격 증명 선택, DB migration, SNS HTTPS 확인과 제한된 수신 테스트·워커 활성화가 남는다. 초기 문서의 Resend 이전/19개 미연결/미커밋 문구는 과거 기록이다. 수동 작성 UI·상세 실패 사유·나머지 실제 전체 흐름 검증은 보류를 유지한다. 실제 env·사용자 DB·다른 채팅 런타임을 임의로 변경하지 않고, 재개 시 repo/서버 상태를 새로 확인한다.

## 2026-11-04 고객 환불과 PG 두 세션 인계

[통합 문서](../features/payments/records/2026/11/04-two-session-pgops-summary.md)와 [보존 증거](../features/payments/records/2026/11/04-two-session-pgops-evidence.json)를 먼저 읽는다. 서비스 기능은 dev에 들어갔으며 가격·무료체험이 미커밋이거나 외부 취소 후처리가 미구현이라는 과거 기록은 현재 판정이 아니다. 유효기간 편집 상한은 **365일**이다.

고객 환불은 관리자 승인 절차를 유지한다. 외부 전액 취소의 내부 정리는 자동화했고, 사용분 정산·부분 취소·모호한 귀속은 운영자 확인 대상으로 남긴다. 실앱 강제 종료와 API 오프라인 복구의 각1회 반환은 실제 확인했다.

남은 것은 실제 Toss 전체 환불/외부취소/복구 E2E, 조건부 DB 테스트86개, 운영 배포/정책 문구와 시험 도구 별도 정리다. 고객 환불은 플래그 없이 기본 제공한다. 새 API 빌드는 준비됐지만 API3311도 현재 정지 상태이며 웹4203/4204는 재실행하지 않았다. 전용 DB15433·작업 폴더/데이터는 보존했다. 원본3000/4201/4202와 프로모션4340/4241/4242는 별도 환경이다.

이 PG 작업의 dev 반영 전에는 반드시 별도 컨텍스트의 독립 검증을 맡기고, 결과 확인·보완·재검토와 최신 원격/tree 확인을 거친다. [필수 절차와 검토 기록](../features/payments/records/2026/11/04-customer-refunds-default-and-pre-dev-review.md).

아래 다른 세션의 인계와 환경은 보존한다. 이 문서화 요청은 실결제·DB 초기화·서버 재시작·다른 세션 변경을 새로 실행하라는 지시가 아니다.

## 2026-11-04 하이라이트 Mac 가속 인계

[모델별 현재 상태](../operations/accelerators/README.md), [종합 인계](../records/sessions/2026/11/04-highlight-mac-acceleration-handoff.md), [사용·검증 절차](../operations/accelerators/runbooks/mac-highlight-acceleration.md)를 먼저 읽는다. Python 17259bc·Electron 849a51b를 dev에 반영하고 원본 8개 대조·local-api Mac 빌드·재기동을 완료했다. Made My Night 안무 335초 → 266초, 63개 목록·설정·집계 동일, Python 2,073개·Electron 1,977개 통과다.

Windows는 별도 채팅 01a1a294-76cc-7d73-af4d-be827b33bde9 담당이다. 모든 모델의 ONNX 전환·모든 GPU 승인·서버 배포 완료로 확대하지 않는다. SFace·일부 ROI·Whisper의 CPU 잔존과 Person의 source 크기 준비 미연결은 인계에 명시했다. 기존 결과·사용자 삭제 상태·다른 작업·캐시·비교 앱을 보존한다. 과거의 기반만 구현/얼굴 CPU/새 GPU 전체 미활성 설명은 당시 이력이다.

## 2026-11-03 W19 최종 배지·6개 저장소 dev 반영 완료

[최종 결과](../features/plugin-catalog/records/2026/11/03-store-plan-badges-dev-merge.md). API `6e1d001` / Admin `e84d531` / Client `50779ad` / App `222ef59a` / Nest `f2cc17a9` / Electron `8e70e99`. 작업 브랜치와 원격 dev가 일치하고6개 작업 폴더 clean, 충돌 없이 fast-forward 통합했다. 카드/상세의 요금제별 배지·권한 안내와 이번 세션 W19 전체 구현을 포함한다.

API5,142/Admin2,728/Client591/App10,656/Electron1,913/PostgreSQL39 통과. Nest는 기존 macOS 종료 시험1건 실패를 사용자 승인으로 [W20 새 세션](tasks/macos-owned-child-identity.md)에 이관했으며 전체 통과로 표시하지 않는다. 100원 업그레이드 문제는 계속 다른 세션 담당이다. 새 앱/API4340 반영, 사용자 DB15438/웹4241·4242/로그인 프로필 유지. 이전 ‘미커밋’ 문구/스냅샷은 단계별 이력이다. `.codex` 문서 커밋·푸시는 하지 않았다.

## 2026-11-03 프로모션 세션 재개 기준

먼저 [종합 정리](../records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md)와 [현재 W19 카드](tasks/signup-promotion-plan-entitlements.md)를 읽는다. 가입 프로모션·참여 조건/확인창/종료일 미정·Free·공통4카드·실행 검사·일괄 허용 설정/양방향 체크/sticky·변경 이력 한국어 표시는 이미 구현·로컬 검증됐다. 초기 유료 예약/레퍼럴 성과/XLSX는 현재 코드에서 제거, 보존 브랜치에 유지했다. 아래 W19의 ‘목업만 완료/미구현/잠금 체크’ 기록은 단계별 과거 상태다.

[PG 분리 정리](../features/payments/records/2026/11/03-session-pg-discussions-and-changes.md)는 승인 전 자격 보완과 MID/업그레이드 정책 조사·문의문을 구분한다. **토스100원 최소 청구로 즉시 업그레이드가 예약되는 문제는 다른 세션 담당이므로 이번 구현·TODO·검증에서 제외한다.** W18 목록 동기화는 별도 후속이고 여기서 자동 재개하지 않는다.

현재6개 제품 저장소 `feat/signup-credit-promotion-free-20261102`는 미커밋·staged0. 이번 정리에서 커밋/푸시/fetch/제품 변경 없음. API4340/Client4241/Admin4242/DB15438/독립 앱의 사용자 테스트 데이터를 임의로 초기화하거나 프로세스를 종료하지 않는다. 이번에는 실행 상태를 새로 보증하거나 앱을 재빌드하지 않았다. 상세 Git 조회는 [스냅샷](../records/sessions/2026/11/03-promotion-worktree-snapshot.json)을 따른다.

## 2026-11-03 W19 플러그인 설정 변경 이력 표시 개선

[구현·검증](../features/plugin-catalog/records/2026/11/03-readable-plugin-audit.md). JSON 전체 목록 대신 바뀐 요금제·플러그인별 허용 전후를 표시한다. 기존 이력은 이름을 조회해 표시하고 새 이력은 이름 스냅샷 보존. 원본 감사 기록 해시 유지 확인, 실제01:40기록18행 확인. API315/Admin79 tests/build/색상/diff 통과. API4340 PID37139/Admin4242 반영. DB/권한 설정 유지, 미커밋·미푸시.


## 2026-11-03 W19 플러그인 체크 양방향 연동

[최종 조작·검증](../features/plugin-catalog/records/2026/11/03-plan-plugin-bidirectional-selection.md). ON에서 체크는 상위로 전파, 해제는 하위로 전파하며 잠금 제거. OFF는 개별 선택 유지. 실제 Pro 스토리보드 해제→Business만 유지 확인. 관련81 tests/build/색상/diff 통과, Admin4242 반영. API/DB 변경·저장 설정 변경 없음, 미커밋·미푸시.


## 2026-11-02 W19 실제 요금제별 플러그인 일괄 관리 적용

[구현·검증·로컬 적용](../features/plugin-catalog/records/2026/11/02-plan-plugin-settings-implementation.md). /plans 단일 관리 버튼·외부 공통 배지·Free 포함 ON/OFF 비교 모달을 실제 API/DB에 연결했다. 전체 목록 원자적 저장, revision 충돌 방지, 신규 등급 상속, 재사용 편집기 반영. API5,131/Admin2,723/실제PG16 통과. 전용DB15438 백업 후 admin migration1 적용, 사용자 데이터 유지. API4340 PID81887/Admin4242 갱신. W18 동기화 제외 유지, 미커밋·미푸시.


**최신 재초기화·재실행:** [런타임 최신 절](../operations/env-runtime/records/2026/11/02-promotion-branch-isolated-local-runtime.md). 사용자 요청으로3DB 백업·초기화/migration13·103·5/관리자2계정·테스트 데이터0 검증.4개빌드 성공. API4340 최신PID19844/웹60587/앱20762·Nest20891(port56212). 아래67957/16214 등은 과거 이력. 사용자 테스트 환경은 계속 유지하고 추가 요청 없이 초기화/종료하지 않는다.

**최신 정책 정정:** [종료일 단축·인원 제한 검증·요약 열 배경](../features/promotions/records/2026/11/02-campaign-deadline-and-summary-colors.md). 등록 이력이 있어도 종료일을 시작일 이후로 단축 가능, 기존 혜택 유지. 옛 단축 금지 설명은 폐기. API5113/Admin2718/PG38·build 통과. API4340 최신PID67957, 웹60587/앱16214 유지. 사용자DB15438 초기화 없음. 미커밋·미푸시.

**최신 관리자 후속:** [생성 확인/문구/인원 입력 배치/수정 규칙](../features/promotions/records/2026/11/02-campaign-create-confirmation-and-edit-rules.md). 공통 모달 생성 확인, 취소 입력 보존, 생성 요약만 두 열 왼쪽 정렬. 관리자2717/API정책35 통과·4242갱신. 기존 회원/캠페인 데이터 초기화 없음. API14845/웹60587/앱16214 유지. 미커밋·미푸시.

**최신 실행:** 종료일 미정 후속까지 API/Admin/Client/앱 재빌드·실행 완료. DB15438 데이터는 이미0건이라 재초기화하지 않았고 관리자2계정/기본 상품·정책 유지. API4340 PID14845/웹4241·4242 PID60587/앱16214·Nest16285(port51814) 정상. [실행 기록](../operations/env-runtime/records/2026/11/02-promotion-branch-isolated-local-runtime.md). 기존 다른 환경 보존. 아래 PID64548/8088은 이전 실행 이력이며 환경을 임의 종료/초기화하지 않는다.

**종료일 양방향 수정 추가 검증:** [결과](../features/promotions/records/2026/11/02-open-ended-campaign-edit-regression-check.md). 실제DB33/화면55 통과. 제품 변경 없이 테스트14개 보강, 미커밋·미푸시. 기존 종료일이 지났던 캠페인은 미정으로 바꿔도 자동 활성화하지 않으며 명시적 재활성화가 필요하다.

**최신 후속:** 종료일 미정 캠페인 구현 완료. [검증 기록](../features/promotions/records/2026/11/02-open-ended-campaign-implementation-and-verification.md). API4340 최신PID64548, 웹4241/4242 PID60587 유지. DB15438 초기화 없이 백업·migration1 적용. API5,106/Admin2,707/Client591·PG23 통과. 아래 PID7681/55613은 과거 실행 이력. 사용자 테스트 환경을 임의 종료/초기화하지 않는다. 미커밋·미푸시.

**2026-11-02 사용자 요청 재초기화·실행 최신:** [전용 로컬 런타임 최신 절](../operations/env-runtime/records/2026/11/02-promotion-branch-isolated-local-runtime.md). DB15438의3DB를 백업 후 초기화하고 migration/기본 설정/관리자2계정 준비. 회원·크레딧·결제·이용권·프로모션·릴리스 데이터 모두0 확인. API4340 PID7681/웹4241·4242 PID60587 정상. 앱을4340용으로 다시 빌드·실행(main8088/Nest8131, gateway65380). 기존 다른 작업 서버·DB·원본 dev앱18096 유지. 아래 PID55613·66870은 이전 실행 이력이며 최신 상태가 아니다. 사용자 테스트용 환경은 계속 실행해 두고 임의 종료/재초기화하지 않는다.


**2026-11-02 W19 최신:** 참여 대상3가지/추가 조건2개 실제 구현 완료. [정본](../features/promotions/records/2026/11/02-campaign-eligibility-implementation-and-verification.md)을 먼저 읽는다. 직전 보류 해제, 새 조건 후보는 문서로만 보존. API5100/Admin2705/Client591·실제PG21 및 빌드·브라우저 검증, 독립 검토 수정 완료. API4340 PID55613·웹60587의4241/4242와 별도 앱을 유지한다. DB15438 초기화 없이 백업 후 migration1 적용. QA15439만 제거. 아직 커밋·푸시하지 않았다. 이미 완료한 구현을 재시작하거나 로컬 환경을 종료하지 않는다.


## 2026-11-02 전용 로컬 테스트 환경 실행 중

[전용 DB·포트·앱·관리자 계정·시작/종료](../operations/env-runtime/records/2026/11/02-promotion-branch-isolated-local-runtime.md). API4340·Client4241·Admin4242, DB15438, `Clipper Studio Local - promo-signup-20261102` 앱을 실행해 뒀다. 기존3000/4202/개발 앱/DB는 유지했다. Google callback4340은 사용자 추가 후 정상 로그인 화면 진입을 확인했다. 필수 동의 아래 코드 입력도 반영했다. 사용자 테스트용이므로 다음 턴에 임의 종료/재초기화하지 않는다.


## 2026-11-02 W19 최신 인계

**최신 사용자 지시: 참여 대상3가지/추가 조건2개 승인, 실제 관리자/API 구현 재개.** 제외 조건 대신 참여 가능 조건 목업(참여 대상 단일 선택 + 추가 조건2개/모두 충족)을 다시 검토한다. 직전 보류는 이번 구현 진행 지시로 해제되었다. [목업 최신 기록](../features/promotions/records/2026/11/02-campaign-create-eligibility-mockup.md).

[가입 프로모션 크레딧·Free 구현/검증 정본](../features/promotions/records/2026/11/02-ai-booth-signup-free-implementation-and-verification.md)과 [W19 카드](tasks/signup-promotion-plan-entitlements.md)를 먼저 읽는다. `feat/signup-credit-promotion-free-20261102` 격리 checkout에서5개 repo 구현·전체 테스트·실제DB16·브라우저·최종 재검토를 완료했고 **미커밋·미푸시·미병합·미배포**다. 원본·보존 브랜치·기존 로컬DB는 유지했다. 이미 끝낸 구현을 다시 시작하지 않는다. 다음 사용자 지시가 커밋/통합이면 최종 manifest와 현재 diff를 대조한 뒤 수행한다. 배포는 새 마이그레이션과 worker drain·API/웹/앱 계약을 함께 확인해야 한다. W18 전체 목록 동기화는 재개하지 않았다.


**2026-11-02 W19 최신 범위:** [AI 부스 가입 크레딧·Free·제안 F·브랜치 기록](../features/promotions/records/2026/11/02-ai-booth-signup-credits-and-free-scope.md)과 [작업카드](tasks/signup-promotion-plan-entitlements.md)를 먼저 읽는다. 신규 가입에만 코드 보너스를 적용하고 첫 로그인 잔액에 가입 혜택과 프로모션 지급을 함께 반영한다. 관리자에는 참여 회원 조회를 남기되 프로모션 종료 후 유료 예약·레퍼럴 결제 성과·XLSX는 현재 코드에서 제거할 대상이다. Free는 지속 상태이며 카드 문구는 **가입 시 1회 N크레딧**이다. 제안 F를 확인했고 목업 수량·가격·기능 조합은 예시다. 6개 저장소에서 최신 원격 dev 기준 보존/작업 브랜치를 만들었으며 기존 checkout/미커밋 파일은 유지했다. 제품 삭제/신규 구현·커밋·푸시·배포 완료는 아니다. 아래 10/29의 Free 명칭 미정·예약/성과 유지 등 상충 내용은 당시 기록이다.

**2026-10-29 W18/W19 분리:** [W18 동기화](tasks/plugin-catalog-sync.md)는 후속 TODO다. [W19 남은 기능](tasks/signup-promotion-plan-entitlements.md)는 가입 코드·크레딧형·지속 기본·허용 설정/실행과 **관리자 DB를 읽는 회원 웹 요금제 카드**다. [최신 설계 재점검](../features/promotions/records/2026/10/29-remaining-scope-after-plugin-sync-deferral.md)를 먼저 읽는다. `/#price`·`/pricing`은 공통 카드를 재사용하고 요금제별 기능 목록 하드코딩을 금지한다. Free는 아직 명칭으로 결정되지 않았다.

**2026-10-29 플러그인 목록 동기화 보류:** 웹 관리자/앱 스토어 목록 공통화·동기화는 이 세션에서 구현하지 않기로 했다. [논의와 전략실 답변](../features/plugin-catalog/records/2026/10/29-admin-store-sync-discussion-and-deferral.md) · [후속 TODO·재개 조건](../todos/2026-10-29-plugin-catalog-admin-store-sync.md). 기술 실험을 제품 완료로 오인하거나 다른 기능에 자동 편입하지 않는다. 유료 상위 플랜의 하위 기능 포함은 최신 방향이고, 요금제 미제공 기능 노출은 이사님 확인 전이다.

**2026-10-26 문서 위치 정리:** 루트 `docs/merge`·`docs/superpowers`의 Markdown 6개를 `.codex`로 옮겼다. [새 위치·옛 경로 대응·증거 사본 보존 범위](../records/2026/10/26-root-docs-relocation.md)를 참고한다. `docs/tips`는 유지한다. 새 설계·계획·병합 기록 위치는 [문서 규칙](../README.DOCS.md)을 따른다.

**2026-10-23 안무 메인 전용·완료 지연 원격 dev 반영:** Python `ea27940`, Nest `0fe9f8b0`를 dev·작업 브랜치에 atomic push했고 원본 두 저장소 dev·clean·0/0이다. 안무 주변 얼굴 보충/단체 자동 멤버 배정을 제거하고 메인 얼굴 근거를 요구한다. 저장 병합·완료 복구·UI 준비 상태·취소/progress 경합을 보완했다. 관련 Python507·Nest전체4,941 통과. Python 전체의 렌더5개 실패는 기존 dev에서도 재현돼 남겨두었다. 후속 사용자 요청으로 기본 dist-app의 ARM64 앱을 다시 빌드·실행했다. 기존 완료 결과는 유지하며 새 분석에 정책이 적용된다. [원인·정책·회귀·빌드·검증 한계](../features/highlights/records/2026/10/23-dance-main-only-and-completion-delay.md).

**2026-10-23 인물 이동 모달80px 원격 dev 반영 완료:** Angular `af8fe16e`을 dev·`fix/person-move-picker-spacing-20261023`에 커밋·atomic push했다. 썸네일80×80px·이름/장면 수 간격2px, 원본 Angular dev·clean·0/0 확인. 전체9,647(seed20261023)·스타일14 통과, 최초 템플릿 간헐 실패는 단독193·전체 재검사 통과 이력과 함께 기록했다. 앞서 실행한 별도 ARM64 앱에도 같은 수정이 포함됐다. [후속 기록](../features/highlights/records/2026/10/23-highlight-result-usability-followup.md).

**2026-10-23 카드 정렬·이동 모달 dev 반영 완료:** Angular `7c06eade`를 원격 dev와 `fix/dance-result-card-alignment-20261023`에 반영했다. 안무 카드 텍스트·hover 아이콘 중앙 정렬, 인물 이동 아이콘 통일, 공통 얼굴 선택 모달·장면 수 표시를 포함한다. 전체9,619(seed20261023)·관련150·스타일14·화면 빌드 통과. 임의 순서의 템플릿/Store 간헐 실패 이력과 실제 앱 반영 범위는 [후속 기록](../features/highlights/records/2026/10/23-highlight-result-usability-followup.md)을 읽는다. 이후 사용자 요청으로 원본8개 최신 dev pull 및 로컬 API용 ARM64 앱 재빌드·실행을 완료하여 추가 모달 변경도 앱에 포함됐다. 당시 Angular `01b815f3`, Nest `df4d586f`, Python `11fbc9d`; 정확한8개 SHA·실행 범위는 같은 기록의 마지막 절을 읽는다.

**2026-10-23 결과 화면 후속 dev 반영 완료:** 안무·인물 결과 화면 사용성·100px 사진 품질·Windows hover 수정은 Angular `baf2f54d`, Python `3b3e203`으로 원격 dev에 반영했다. 원본 두 저장소도 dev·clean이다. Angular9,612+스타일14, Python 안무·공통 얼굴206, 병합 후 hover135 통과. [변경·빌드·병합 기록](../features/highlights/records/2026/10/23-highlight-result-usability-followup.md).

**2026-10-23 최종 통합:** 세 관련 세션을 재감사하고 빠져 있던 무대 파이프라인 작업도 원격 dev에 반영했다. Angular `975e16f6`, Electron `dfc84d4`, Nest `15f534b9`, Python `584d76b`; 작업 브랜치와 dev SHA가 모두 일치한다. Angular 8,330+스타일 14 / Electron 1,721 / Nest 4,258 / Python 1,512 통과·6 skip. 이전 Nest 종료 테스트 실패는 이번 재검증에서 해소됐다. [최종 통합·검증·한계](../features/highlights/records/2026/10/23-stage-person-integration-dev-merge-result.md)를 먼저 읽는다. 앱 재빌드·실영상·Windows 확인은 별도다.

**2026-10-23 무대 사용성 후속 완료:** [구현·검증·dev 반영 기록](../features/highlights/records/2026/10/23-stage-usability-source-ranges-dev-merge.md)을 먼저 읽는다. 원본 구간 저장, 편집·선택·숏폼 구성·묶음 드래그·미확인 얼굴 썸네일은 Angular `f488e8a4`, Nest `8397afbc`, Python `3fbb002`로 원격 dev에 충돌 없이 반영됐다. 다음 확인은 실제 영상에서 편집 범위와 출력 일치, 실제 카드 드롭, Windows 검증이다.

**2026-10-23 W14 최신:** 인물 하이라이트의 데스크톱 4개 저장소는 원격 `dev` 병합·푸시 완료다. 먼저 [병합 체크포인트·검증·인계](../features/highlights/records/2026/10/23-person-highlight-dev-merge-and-stage-usability-handoff.md), [W14 카드](tasks/person-highlight.md)를 읽는다. 병합 보류 지시는 후속 사용자 승인으로 해제됐다. 무대 사용성 후속은 위 기록처럼 구현·dev 반영을 완료했다. 무대 파이프라인 세션은 별도 정확도 개선을 이어간다. 추가 얼굴 모델 교체나 별도 병합을 이미 수행했다고 간주하지 않는다. Web API 과금·권한 후속도 `ba68b2b`로 원격 dev 반영 및 로컬 DB 확인을 완료했다([기록](../features/highlights/records/2026/10/23-person-highlight-web-api-billing-dev-merge.md)). 기존 로컬 미커밋 사본이 남아 있어도 원격 미반영으로 오해하지 않는다.

최신 갱신: **2026-10-23 KST (W14·W17)**. 아래 W13/W14·QA 설명은 별도 표기된 10/16 스냅샷이다.

**W17 프로모션:** Web API·관리자 웹·회원 웹의 프로모션 캠페인/복수 코드 후속 작업과 데스크톱 NestJS·Angular의 프로모션 출처 인식이 원격 `dev`에 병합됐다(API `0776268`, 관리자 `98e2e8c`, 회원 `fbd4573`, NestJS `b9602b2f`, Angular `1a839571`). 캠페인 공통 설정의 **코드별 등록 상한**, 회원당 캠페인 1회, 유료/관리자 지급 이력 선택, XLSX 성과와 회원 참여 내역이 현재 기준이다. 데스크톱 NestJS 전체 테스트는 별도 실패로 통과하지 못했고, 변경 경로 테스트와 빌드는 통과했다. 재개 시 [W17 카드](tasks/festival-voucher.md), [현행 설계](../design/2026-10-23-promotion-campaign-current-state.md), [병합 기록](../implementation/2026-10-23-promotion-campaign-dev-merge.md)을 먼저 읽는다. 운영 배포/DB 적용과 실제 Toss 결제망 검증은 완료로 취급하지 않는다.

**다음 주 범위:** [10/19~23 작업 초안](2026-10-16-next-week-scope-draft.md)을 먼저 본다. 사용자의 최신 방향은 기존 안무 플러그인의 **무대 하이라이트 전환**, 저동작 솔로 무대 지원, 별도 사용성 개선, **인물 하이라이트 플러그인 시연**, 대사 하이라이트 개선이다. 6번 배포·빌드·브랜치 전략과 앱/플러그인 버전 관리는 낮은 우선순위로 추가했다. 아래의 "Person MVP 보류"는 10/16 당시 상태이며 다음 주 제품 개발을 보류하라는 뜻이 아니다.

**10/16 재개 안내(이력):** 당시에는 안무·인물 하이라이트 재개 전에 [작업 현황판의 10/16 요약](WORKBOARD.md), [고정 스레드 1~5·7~9 / 8개 저장소 dev 감사](2026-10-16-pinned-thread-dev-reconciliation.md), [W13 노트북 71개·W14 얼굴 평가 회고](../features/highlights/records/2026/10/16-w13-w14-experiment-reconciliation.md)를 먼저 읽도록 안내했다. 사용자 보고상 대표님께 전달한 새 빌드의 SHA·영상/참조 입력을 고정하고, W13 메인/군무/컷과 W14 얼굴 신원/구간을 분리해 현재 dev와 비교한다. 72번 노트북은 제품 미채택, Person MVP는 보류, 통합 시험 tree의 수동 클립 수정·긴 구간 분할은 dev 미반영 미커밋이다. 코드 수정 전에 해당 저장소의 원격 `dev`를 다시 fetch한다. 10/16 대조 당시 Angular·Web API·Admin·Client·Infra 기본 checkout은 원격보다 뒤에 있었다.

QA/W06은 [W16](tasks/payment-qa-bugs.md)·[W06](tasks/pg-production-followups.md)의 10/16 상단 갱신을 우선한다. 아래 9/29 지침의 “새 MID 발급만 됨”, “8repo dev clean”, “하이라이트 전체 조사부터 시작”은 지금의 상태가 아니다.

## 9/29 당시 시작 안내 (이력)

1. [작업 현황판](WORKBOARD.md)에서 사용자가 선택한 작업을 확인한다. [새 세션 시작 프롬프트](prompts/2026-09-29-new-sessions.md)에 5개 세션의 시작 문구가 있다.
2. 해당 작업카드와 필요한 repo 규칙을 읽는다. [9/29 인계](../records/sessions/2026/09/29.md)에 이번 대화의 결정·완료 사항·검증 한계가 있다.
3. 원본8repo는 이번 조회 기준 dev·clean·로컬 origin/dev와 0/0. 재개 시 실제 상태를 다시 읽고, 코드 수정 전에 필요한 repo의 최신 origin/dev에서 새 브랜치·격리 작업 폴더를 만든다.
4. `dev-merge-0.0.36`, `storyboard-ux-overhaul-20260920` 폴더는 삭제됐다. 브랜치는 보존됐다. 과거 문서의 해당 폴더를 재사용하지 않는다.
5. PG는 심사 완료·새 MID 2개·테스트/라이브 키 발급 사용자 보고 단계다. 우선 MID/키/기존 결제·billingKey·DB 영향과 전환안을 설명한다. 실결제·환불은 구체적 대상/금액 확인 뒤, 서버는 사용자 실행 방식으로 진행한다.
6. 하이라이트는 전체 조사 세션에서 공통 구조·변경 이력·측정 계획을 정리하고 안무/인물/대사 세 세션의 인계 프롬프트를 만든다. 출력이 미정인 인물 플러그인을 확정 구현처럼 다루지 않는다.
7. 기존 HOLD는 해당 세션의 새로운 사용자 지시와 대조한다. 과거 단위테스트 PASS를 실제 ML/PG/운영 배포 완료로 재사용하지 않는다.
8. 종료 시 해당 작업카드·보드·세션 기록을 갱신한다. 요청 없는 commit/push·새 작업 세션 생성은 하지 않는다.

## 바로 이동

- [공통 버그·문구·기획 보정](tasks/app-bugfix.md)
- [TossPayments 새 MID·키 전환](tasks/pg-production-followups.md)
- [스토리보드 후속 개선](tasks/storyboard.md)
- [홈·보관함·큐](tasks/home-archive.md)
- [하이라이트 전체 조사](tasks/highlight-overview.md)
- [ICP TC4 기존 로그 활용](tasks/icp-tc4.md)

[과거 NEXT 원문](archive/2026/09/next-through-2026-09-18.md) · [9/18 PG 통합 종료 감사](../implementation/2026-09-18-pg-integration-closeout-and-remaining-work.md).

## 2026-11-02 요금제 F 후속과 미구현 조건

[제안 F 재대조 및 참여 제한 정정](../features/promotions/records/2026/11/02-proposal-f-fidelity-and-eligibility-correction.md): UI84시험/빌드/실화면 확인,4241최신. 혜택/참여 시점 분리와 선택 제한(현재 활성·과거 유료·관리자 지급)은 설계 정정이며 API/Admin에 아직 구현하지 않았다. 사용자 테스트용 API4340·Client4241·Admin4242·앱은 계속 실행한다.

## 캠페인 추가 목업 사용자 정정

상단 기본정보/지급혜택/참여조건/등록상한 탭을 실제 UI에 넣지 않는다. ‘참여 시점’을 따로 두지 말고 ‘이미 가입을 완료한 회원 제외’를 나머지 제한과 같은 체크박스 목록으로 처리한다. 목업은 수정·검증했으며 제품/API는 아직 변경하지 않았다. `/__mockups/campaign-create-eligibility.html`에서 현재 시안을 볼 수 있다.
