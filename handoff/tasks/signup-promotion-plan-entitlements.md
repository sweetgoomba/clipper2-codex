# W19 가입 프로모션·Free·요금제별 플러그인

최종 정리: **2026-11-03 KST**. **관련6개 제품 저장소 커밋·푸시 및 최신 원격 dev 통합 완료. 충돌0·작업 폴더 clean.** 서버 배포/실제 PG망 검증은 별도다.

[세션 종합 정리](../../records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md) · [WORKBOARD](../WORKBOARD.md) · [초기 구현·검증](../../features/promotions/records/2026/11/02-ai-booth-signup-free-implementation-and-verification.md) · [이전 카드 이력](../archive/2026/11/03-w19-task-before-consolidation.md)

## 현재 완료 범위

- Google 복귀 후 필수 동의 아래 선택 코드 입력. 실제 신규 가입 판정·서명 대기표·별도 가입/프로모션 크레딧 지급·멱등 복구·첫 로그인 합산 잔액.
- 캠페인→복수 코드, 회원당 캠페인1회, 캠페인 공통 설정을 각 코드에 독립 적용하는 등록 인원 제한, 코드별 추천인/상태/참여 이메일 조회.
- 일반 크레딧 지급/이용권 지급과 참여 대상(new/existing/all) 분리. 기본은 신규. 추가 조건은 현재 활성 이용권 없음/과거 유료 이력 없음(AND). 신규 전용은 추가 조건을 해제·비활성화하되 계속 표시.
- 크레딧형만 자체 유효일수 입력. 이용권형은 일반 유료와 같은 월별 지급·월별 만료. 관리자 과거 이력·무료체험·다른 캠페인 이력은 선택 제한에서 제외.
- 생성 전 공통 요약 확인창, 코드별 인원 입력 배치/쉬운 문구, 종료일 미정 및 양방향 수정/단축, 등록 후 수정 잠금과 삭제 제한, 해당 등록의 남은 혜택 회수.
- 지속 Free와 최초 가입 혜택1회 분리. Free 복귀 시 재지급 없음. 현재 등급의 허용 플러그인과 크레딧을 실제 실행에서 검사. 설치/준비는 허용.
- 제안F 공통4카드(`/#price`, `/pricing`)를 가격·수량·기한·허용 플러그인 API에 연결. Free 가입1회N/유효D 표시.
- /plans 공통 일괄 모달·자동 포함 전역 ON/OFF·외부 상태 배지·전체 원자 저장/revision·신규 등급 상속. ON 체크는 상위/해제는 하위 전파, 잠금 없음. 토글/안내 sticky. Free는 ‘항상 활성’ 표시.
- 변경 이력은 JSON 대신 요금제·플러그인의 허용 전후/요약 표시. 새 기록 이름 스냅샷·옛 기록 일괄 이름 조회, 원본 감사 데이터 보존.

## 범위에서 뺀 것

- 기존 프로모션 종료 후 유료 예약·레퍼럴 결제 귀속/성과·XLSX는 보존 브랜치에 남기고 현재 코드 실행 경로에서 제거했다. 일반 결제/카드/재시도/환불/장부와 참여 조회는 유지한다.
- [W18 전체 카탈로그·앱 스토어 동기화/분류/전역 중지](plugin-catalog-sync.md)는 후속 TODO이며 W19에 자동 편입하지 않는다.
- **100원 최소 결제액으로 즉시 업그레이드가 예약되는 문제는 다른 세션 담당. 이번 세션의 구현·TODO·검증에서 제외한다.**

## 작업 위치와 상태

작업 루트 `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028`, 웹3개/데스크톱 Angular·Nest·Electron6개 모두 `feat/signup-credit-promotion-free-20261102`. 각 저장소에 `archive/promotion-access-referral-20261102` 보존. 현재 HEAD/미커밋 경로 수는 [조회 스냅샷](../../records/sessions/2026/11/03-promotion-worktree-snapshot.json)을 따른다. 초기 조회 스냅샷은 병합 전 이력이다. 이후 사용자 요청으로6개 저장소 모두 커밋/작업 브랜치 푸시/dev fast-forward 통합을 완료했다. 원본 체크아웃과 실행 worktree는 유지한다.

## 최신 검증과 세부 근거

- [참여 대상/추가 조건/월별 만료](../../features/promotions/records/2026/11/02-campaign-eligibility-implementation-and-verification.md)
- [생성 확인·수정 잠금](../../features/promotions/records/2026/11/02-campaign-create-confirmation-and-edit-rules.md) · [종료일 단축/인원 제한/최종 확인 표](../../features/promotions/records/2026/11/02-campaign-deadline-and-summary-colors.md)
- [종료일 날짜↔미정 회귀](../../features/promotions/records/2026/11/02-open-ended-campaign-edit-regression-check.md)
- [일괄 플러그인 설정](../../features/plugin-catalog/records/2026/11/02-plan-plugin-settings-implementation.md): 당시 API5,131/Admin2,723/실제PostgreSQL16.
- [체크 양방향·고정 영역](../../features/plugin-catalog/records/2026/11/03-plan-plugin-bidirectional-selection.md): 관련81, 고정 영역6.
- [읽기 쉬운 감사 이력](../../features/plugin-catalog/records/2026/11/03-readable-plugin-audit.md): API315/Admin79·빌드, 기존 실제 기록 원본 해시 유지/18행 표시.

숫자는 단계별 범위이며 합산하지 않는다. 마지막 관련 테스트를 현재 모든 변경의 새 전체 회귀로 주장하지 않는다. 실제 토스망/운영 배포 검증 완료가 아니다.

## 환경과 다음 행동

[전용 로컬 환경](../../operations/env-runtime/records/2026/11/02-promotion-branch-isolated-local-runtime.md): API4340/회원4241/관리자4242/DB15438/별도 local-api 앱. 사용자의 캠페인·회원·허용 설정 테스트 데이터를 유지한다. 임의 재초기화/종료 금지. PID는 환경 기록의 마지막 적용 시점 값이지 영구 현재값이 아니다.

새 수동 테스트 문제는 재현 후 수정한다. 요청 시 커밋/원격 dev 통합·배포를 진행하되 그때 원격·마이그레이션/worker 호환을 다시 확인한다. 이미 완료한 구현을 과거 ‘목업만 완료’ 문구 때문에 재시작하지 않는다. PG 보완과 조사/문의문은 [별도 정리](../../features/payments/records/2026/11/03-session-pg-discussions-and-changes.md)를 따른다.

## 11/03 최종 스토어 배지·dev 통합

[최종 구현·여섯 커밋·검증·인계](../../features/plugin-catalog/records/2026/11/03-store-plan-badges-dev-merge.md). 카드에는 현재 미허용인 기능만 Basic 이상/Pro 이상/Business 등으로 표시하고 상세에는 사용 가능 요금제를 표시한다. 불연속 허용 조합은 개별 배지로 보존하며 모든 활성 등급을 판매 여부와 독립 조회한다. API5,142/Admin2,728/Client591/App10,656/Electron1,913/PostgreSQL39 통과, Nest는 기존 종료 시험1건을 사용자 승인으로 [별도 새 세션](macos-owned-child-identity.md)에 이관했다. 이번 작업을 전체 Nest 통과나 W20 오류 해결로 보고하지 않는다.
