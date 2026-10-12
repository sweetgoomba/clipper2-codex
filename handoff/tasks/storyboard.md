# W07 — 스토리보드 후속 수정・개선

최종 확인: 2026-09-30 KST. 상태: **입력/목적 선행 변경과 선택 삭제·카드 UI·진행 표시/계측·원장 명칭을 Angular/Nest/Web API 원격 dev에 병합·푸시. 전체 삭제 UX 사용자 최종 판정과 구형 화면/API 정리, 실제 생성 시간 단축은 미완료. 실행 Web API 반영과 로그인 후 최신 앱 화면은 미확인**.

**9/30 최신 병합:** 사용자 확인 후, 아래 첫 부분 병합에서 빠졌던 선택 삭제·카드/결과 안내·공통 모달·진행 표시/계측·원장 문구를 Angular `705c49c1`, Nest `60a7771`, Web API `1feac57`로 각 원격 `dev`에 추가 병합·푸시했다. 원본 W07 격리 worktree의 미커밋 변경은 그대로 보존했다. 구형 화면/API 정리(D12/D13), 실제 속도 단축과 동일 조건 실공급자 전후 비교는 **미병합·미완료**. 실행 중인 Web API 서버는 재시작하지 않아 런타임 원장 문구 반영은 미확인. [최신 범위·검증](../../implementation/2026-09-30-storyboard-final-dev-merge.md).

## 9/30 사용자 요청에 따른 부분 dev 병합

Angular `5570f8ca`, Nest `c8b8b07`을 각각 원격 `dev`에 fast-forward 병합했다. 포함 범위는 (1) 삭제 기록의 **읽기·활성 목록 제외만** 적용해 Nest 부팅 실패를 막는 처리, (2) 한글 키워드 IME 최종 글자 누락 수정, (3) 제작 목적 추천 해제 후 빈 목적 표시·저장 차단, (4) 신규 이름50자·목적150자 제한과 안내/예시 및 복제 이름 자르기다. 기존 120/500자 저장값은 읽고 다른 필드를 수정해도 그대로 유지한다. 기존 목적 필드 두 개의 값이 서로 다른 프로필을 복제할 때도 각각 보존한다.

**이번 병합 제외:** 레거시 화면/API 정리 또는 전환, 프로필 선택 삭제 UI/API, 카드 hover·완료 문구 정렬, 진행 미터/단계 메시지, 공통 모달, 삭제 원본 복제 버튼 툴팁, 설정 정렬, Web 원장, 생성 속도 계측/최적화. 이 항목들은 W07 구현·사용자 확인·완료 여부를 별도로 판단한다. 레거시 정리는 사용자가 이해·승인한 완료 항목이 아니므로 dev 병합 완료로 보지 않는다. [부분 병합 계획·검증](../../implementation/2026-09-30-storyboard-ready-dev-merge-plan.md).

검증: 통합/병합 후 Angular 전체5418/5418, 스타일6/6, local build; Nest build와 프로필 API·저장소38/38, ncc 패키지 모드 임시 데이터 사본 `/v1/health` `ok`. 원본 Angular checkout의 다른 설계 문서 미커밋 변경은 유지했다. 전체 Electron GUI 앱을 새 병합 커밋으로 빌드·실행한 것은 아니다.

[전체 현황](../WORKBOARD.md) · [새 세션 프롬프트](../prompts/2026-09-29-new-sessions.md)

## 현재 상태 — 요구별 재감사

- 프로필 삭제: **완료 판정 보류**. 사용자 선택에 따라 다중 선택 삭제를 유지한다. 상단 버튼 스타일·문구를 고치고 카드 클릭·키보드 선택, 추천 전구 아이콘, 확인창 ‘취소’를 적용했다. 이전 앱에서 선택 모드 진입·취소를 확인했으며 이번 새 앱은 패키지 검증까지만 마쳤다. 사용자는 실제 프로필 삭제·홈 결과 보존·결과 페이지 열기를 확인했다. 삭제된 원본의 복제/재생성 액션은 이번 후속에서 막았으며 새 앱 실기와 전체 삭제 UX 완료 판정은 남았다.
[전체 요구·구현/적용/미완료 구분](../../implementation/2026-09-29-storyboard-status-audit.md).

- 초기 조사 세분 메시지와 프로필 카드 진행 미터: **구현·최신 테스트 앱 포함**, 관련 재검증27/27. 단계 진행률이며 예상 남은 시간 기능은 아니다.
- 원장 `스토리보드 생성 · 크레딧 사용/반환`: **Web API 소스·테스트19/19 완료 / 실행 서버 반영 미완료**. 현재3000은 원본 checkout이고 표시 map이 빠져 있다. 테스트 앱에는 Web API 서버가 포함되지 않는다.
- 지연 조사: 코드/기존 로그/오프라인 측정 완료. 새로 남은 실제 성공 job233926ms(약3분54초) 시간대의 stage 로그에서 소재 결정98.5초(43%), 본문 구성43.9초(19%), 두 정규화40.0초(17%)를 측정했다. 외부 웹 검색/새 유료 생성 요청은 하지 않았다.
- **생성 병렬화·실제 시간 단축 구현 및 같은 조건의 전후 품질/비용/정산 평가는 미완료**. 목록 옛 조회180→0은 생성 시간 개선 증거가 아니다.
- 추가 레거시 철거·물리IME·실DB/과금 검증·W07 나머지 코드의 커밋/병합/배포는 남아 있다. 위 4항목의 9/30 부분 병합이 최신 상태이며, 아래 검증/빌드 문단은 각 시점 이력이다.

## 기존 작업의 완료 상태

`feature/storyboard-ux-update`의 Angular/Nest/Web API 커밋은 현재 원본 dev에 모두 포함됐다. 이번 확인에서도 각 저장소 `git rev-list --count dev..feature/storyboard-ux-update`는 0이다.

기존 원격 보존 커밋: Angular `18006cb0`, Nest `693edf6`, Web API `580211e`. 이 Git 포함 확인은 후속 모든 기능/배포/실제 AI 검증 완료를 뜻하지 않는다.

옛 `.worktrees/storyboard-ux-overhaul-20260920`는 5repo 모두 dev 포함·clean 확인 후 사용자 요청으로 **백업 없이 제거**했다. 브랜치는 보존했으며 원본 repo는 dev다. 옛 폴더나 LOCAL-PREVIEW.md를 새 세션의 실행 경로로 사용하지 않는다.

[기존 구현·검증 증거](../../implementation/2026-09-21-storyboard-implementation-verification.md) · [9/21까지 카드 이력](../archive/2026/09/storyboard-through-2026-09-21.md)

## 이번 요구 — 9/29 구현·검증 상태

### A. 팀원(민준님)의 후속 범위

이전 대화에서 아래 항목은 원본 작업 누락이 아닌 새 후속 설계의 미완료 범위로 구분했다. 새 세션에서는 현재 dev 코드에 이미 반영된 부분을 다시 확인한다.

- [ ] 프로필 삭제: 선택 모드·DELETE API·상단 버튼 스타일 코드는 수정·자동화·패키지 UI 확인. 사용자는 선택 삭제 유지를 결정했다. 실제 삭제·보관함 결과 보존의 사용자 실기 전까지 완료 처리하지 않는다.
- [ ] 레거시 잠금 제거·레거시 결과 화면 철거: W07에는 코드 변경이 있으나 사용자에게 범위·필요성이 충분히 설명되지 않아 완료 판정·dev 병합 보류. 기존 데이터 처리/보존 요구도 별도 판단한다.
- [x] 초기 조사 단계의 세분된 진행 메시지 및 프로필 카드 진행 미터.

팀원 출처:
`/Users/jina/project/adlight/desktop/clipper_angular/docs/superpowers/specs/2026-09-21-storyboard-v2-ui-refinement-design.md`,
`.../plans/2026-09-21-storyboard-v2-ui-refinement-fe.md`.
D6–D13과 단계4–6이 관련 범위다. 설계 파일 존재만으로 구현 완료로 표시하지 않는다.

### B. 입력・선택 상태 버그

- [x] 키워드 입력에서 “독서”를 입력했는데 조합/입력이 씹혀 최종 “독”만 남는 현상. 한글 IME composition, 태그 입력·Enter/blur·폼 갱신 경로를 실제 재현으로 확인한다.
- [x] 제작 목적의 추천 선택을 모두 해제하고 직접 입력도 비었는데 “프로필 수정하기”가 활성화된다.
- [x] 위 상태에서 저장/생성한 프로필에는 마지막에 선택했다가 해제한 제작 목적이 남는다. UI 선택 상태·폼값·검증·저장 payload/읽기 값까지 함께 확인한다.

### C. 표시・크레딧 명칭

- [x] 프로필별 세부 설정의 레이블/값 위치와 컬럼 정렬·반응형이 어색한 부분을 확인하고 맞춘다. 캡처/실제 화면 기준으로 정한다.
- [x] 원장 표시 map 소스 수정: `스토리보드 생성 · 크레딧 사용/반환`, 관련19/19.
- [ ] 원장 표시 수정의 실행 Web API 반영. 현재 localhost3000은 원본 checkout이며 이 map이 빠져 있다.

### D. 생성 속도

- [x] 기존 실로그 총시간·재시도와 코드 순차 경계를 조사하고, 단계별 요청·대기·재시도·검색·저장/취소 계측 및 오프라인 전후 측정을 추가했다. 초기에는 실공급자 단계 비중이 미확인이었고, 최신 실로그1건에서 소재 결정/본문 구성/정규화 비중을 추가 측정했다.
- [x] 프로필→주제→시나리오→상세 의존성과 병렬 가능한 독립 호출을 구분한다.
- [x] 병렬 처리, 중복 요청 제거, 캐시/배치 등 후보의 품질·요청 제한·비용·취소/복구/정산 영향을 비교한다.
- [ ] 실제 생성 시간 단축(제한 병렬화 등)을 구현한다. 계측/후보 검토만 완료했으며 아직 순차 실행이다.
- [ ] **실공급자로** 같은 입력·조건의 전후 시간/품질/정산을 비교한다. 오프라인 fixture의 호출·결과·복구·정산 불변성 전후 비교는 완료했으나 실성능 개선을 증명하지 않는다. 원인 측정 전 병렬화나 모델 교체를 확정하지 않는다.

## 작업 공간

우선 `desktop/clipper_angular`, `desktop/clipper_nestjs`. 원장/추론/정산 계약 변경이 필요하면 `web/clipper_web_api`. 전체 패키징이면 Electron/Python 형제 경로도 준비한다.

9/29 세 대상 repo fetch 성공 후 최신 origin/dev 기반 공통 브랜치 `feat/storyboard-followups-20260929`, 격리 루트 `/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929`를 준비했다. Angular `797782e8`, Nest `824a7a9f`, Web API `31f44826`. 원본 checkout은 dev·clean·0/0, 변경은 새 worktree 미커밋이다. W10 공통 폼/UI·W11 shell/projects·TC4 logging/jobs·하이라이트 Web credits/inference 겹침을 검증 보고서에 기록했다.

## 실행 결과・남은 검증

현행 dev·민준님 D6–D13/단계4–6 대조 후 누락된 선택 삭제/API·레거시 표시/잠금 철거·초기 메시지/미터를 구현했다. 한글 composition 경계와 실제 Material 목적 해제 RED→GREEN, 저장 payload 일치 확인. 삭제는 owner/busy·정산/시작/복구 lock을 지키며 역사 profile·batch/artifact 데이터는 tombstone과 snapshot으로 보존한다. 설정 정렬·반응형, `스토리보드 생성 · 크레딧 사용/반환` 명칭을 수정했다.

최종 Angular5395/5395 + 스타일6/6 + local AOT, Nest build875/875, Web 관련503/build PASS. Web 전체 기존7개 실패는 원본 동일 재현. 브라우저 fixture에서 payload·순차 삭제/실패 재시도·active 제외·삭제 후 결과 접근·다크/라이트1920/1280/768/390 PASS, JS error0. OS 물리 한글 입력/설치형 Electron은 미검증. 리뷰의 확인 대상 expansion과 취소 elapsed 누락도 보완·재검토했다.

성능: 기존 실제 로그 총시간610563/142428ms를 관측했으나 서로 다른 입력의 작업이며 단계 비중/수량은 미확인. 신규 단계·재시도·검색·저장·취소 시간 로그 추가, 20-profile fixture의 obsolete legacy reads180→0. 병렬/캐시/모델 후보의 비용·품질·취소/복구/정산 영향을 비교했다. 실공급자 전후 비교 없이 병렬화나 모델 교체를 적용하지 않았다.

[구현·회귀·화면·충돌 경로](../../implementation/2026-09-29-storyboard-followups-verification.md) · [성능 근거·후보 분석](../../diagnostics/2026-09-29-storyboard-performance.md) · [실행 계획](../../implementation/2026-09-29-storyboard-followups-plan.md) · [독립 리뷰/보완](../../implementation/2026-09-29-storyboard-followups-review.md)

남은 실기: 같은 입력/수량/모델/조건의 실공급자 시간·품질·정산 비교, 설치형 macOS IME·패키징, 실제 서버/DB/과금 확인. 이번에 commit/push/merge/deploy/DB/실AI는 하지 않았다.

회귀는 실제 한글 입력/선택 해제/저장 payload와 UI, 삭제 API의 실행 중 작업·차감/환급 경계, 진행 상태·레거시 데이터, 성능 전후를 확인한다. 실제 AI/과금 테스트 범위는 해당 세션의 명시 지시로 구체화한다.

## 근거

- [9/29 인계](../../records/sessions/2026/09/29.md)
- [기존 구현 계획](../../implementation/2026-09-21-storyboard-implementation-plan.md)
- [과거 9/21 기록](../../records/sessions/2026/09/21.md)


## 후속 — 사용자 테스트 앱 빌드

사용자 요청으로 현재 W07 변경을 포함한 macOS arm64 local-api `.app` 전체 빌드를 완료했다. Angular packaged/Nest ncc bundle/Electron TS/uv/electron-builder --dir exit0. 실제 패키지 renderer86파일 및 Nest bundle hash 일치, Python .git 미포함, production 의존성 problems0, actual Electron updater/fs-extra 로드 PASS. Electron 최신 origin/dev0cd7ed7b 기반 새 격리 worktree와 Python 최신47782953의 Git 없는 archive 빌드 입력을 추가했다. 제품 소스 추가 변경 없음.

[실행 명령·빌드 입력·주석 질문 근거](../../implementation/2026-09-29-storyboard-native-test-build.md). 기존 앱을 종료한 뒤 `open "/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app"`을 실행한다. 기존 원본 Web API localhost3000 프로세스는 변경하지 않았으므로 Web 원장 명칭은 그 API에 W07 코드를 별도로 반영해야 한다. 에이전트는 앱 UI를 실행하거나 기존 앱을 종료하지 않았고 실AI/DB/서버 재시작/commit/push/merge/deploy 없음. 위 초기 검증 기록의 패키징 미실행은 이 후속에서 해소됐으며 물리 IME/실성능은 사용자 실기 대상으로 남는다.


## 후속 — 제작 목적 UX·150자 / 이름50자

사용자 최신 지시에 따라 목적 미입력 이유를 고정 footer에 표시하고 목적 이동/포커스, 필수 표기·항상 보이는 입력 안내, 상호작용 후 인라인 오류·유효 입력 회복을 구현했다. 이름120→50, 목적500→150을 UI와 생성/수정 API에 적용하고 목적 placeholder를 대상·방법·기대 행동 예시로 바꾸며3줄 입력란으로 넓혔다. 복제 이름의 접미사 포함50자/충돌도 처리했다. 저장 parser 기존 스키마는 그대로며 새 호환 분기나 데이터 변환 없음.

최신 Angular5400/5400·스타일6/6·Nest관련54/54·packaged/native PASS. Chrome fixture dark/light1280/390 overflow없음·JSerror0. 최신 앱은 `dist-app/purpose-ux/mac-arm64/Clipper Studio (dev).app`이며 이전 앱은 이번 변경 전 빌드다. [구현·화면·검증·새 실행 명령](../../implementation/2026-09-29-storyboard-purpose-ux.md). 실공급자 성능/물리IME 대기, 미커밋.

프로필 이름 예시 후속: 생활 팁 placeholder 누락을 “예: 퇴근 후 10분 독서 루틴”으로 수정해 목적 예시와 맞췄다. 최신 앱은 `dist-app/purpose-ux-name/mac-arm64/Clipper Studio (dev).app`. Angular packaged/native build 및 실제 package 문구/hash 검증 PASS. HTML문구만 변경, 기존50/150 동작 유지.

완료 카드 문구 철회 후속: 사용자 요청으로 “결과 보기 ›”와 전용CSS를 제거했다. 완료 개수/기존 클릭 이동 유지, 관련33/33·packaged/native PASS. 최신 앱 `dist-app/result-label-reverted/mac-arm64/Clipper Studio (dev).app`; 실행 명령은 최신 목적 UX 보고서.


## 후속 — 카드 hover 배경

사용자 요청으로 hover 추가외곽선 대신 모든 프로필 카드에 primary6% 옅은 배경을 적용했다. mouseout원복·border/레이아웃불변·키보드focus-visible outline유지. 실제Chrome dark/light1440/768/390·스타일6/6·packaged/native PASS. 최신 앱 `dist-app/hover-tint/mac-arm64/Clipper Studio (dev).app`. [화면·검증·실행 명령](../../implementation/2026-09-29-storyboard-card-hover.md).


## 후속 — 완료 표시 세로 중앙·레거시 정리안

사용자 피드백으로 완료 카드 액션 영역의 세로 중앙을 복구했다. Chrome RED중앙오차42.28125px→GREEN dark/light1440에서1px미만, hover/focus/responsive도 PASS. 스타일6/6·packaged/native·renderer86/Nesthash확인. 최신 앱 `dist-app/card-alignment/mac-arm64/Clipper Studio (dev).app`. [정렬 검증/명령](../../implementation/2026-09-29-storyboard-card-alignment.md).

레거시 감사 결과 실제 옛 API와 닿지 않는 코드/전환UI가 남아 있다. [현행v2전용 철거 정리안](../../implementation/2026-09-29-storyboard-legacy-retirement-plan.md)을 작성했다. 이전 D13 전환 유지 방침을 바꾸는 **제안·미구현**으로, 공용 함수를 먼저 분리하고 독립 옛 지원을 철거하는 순서다. 이번 추가 build에는 세로 정렬만 반영했고 레거시 추가철거/데이터 변경은 없다. 실제 구데이터 존재/사용을 확인했다는 뜻이 아니다.


## 후속 — 9/21 팀원 설계 전체 대조·선택 삭제 버튼 수정 (9/30)

사용자가 선택 삭제 유지에 동의했다. D6의 과거 ‘사용자 요청’ 출처는 현재 대화로 입증되지 않으므로 이를 새 동의와 구분한다. [D1~D25 항목별 설명·dev 선행/W07 구현/철회·미검증 구분](../../implementation/2026-09-30-storyboard-v2-design-audit.md)을 작성했다. 상단 추천/생성/삭제 버튼 모두 Material 아이콘·버튼 방식으로 통일하고 삭제 문구를 ‘프로필 삭제’로 변경했다. 빈 화면의 추천/생성에도 같은 아이콘을 썼다. Angular5402/5402·스타일6/6·diff check PASS. 별도 macOS arm64 local-api 앱을 빌드해 실제 앱에서 세 버튼과 선택 모드 진입/취소를 확인했다. Electron 원격 다운로드 실패는 설치된 로컬 배포판으로 패키징을 마쳤다. 최신 테스트 앱: `/Users/jina/project/adlight/.worktrees/storyboard-delete-style-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. 실제 삭제/보관함 데이터, 라이트 테마 앱, 실행 Web API 원장 명칭, 실공급자 성능은 미확인. 앱 빌드 미러는 기존 앱 산출물을 덮지 않았고 W07 소스는 미커밋이다. 검증 로그: `output/storyboard/2026-09-30/storyboard-delete-*.log`.


## 후속 — 전구 아이콘·카드 전체 선택·삭제 확인 문구 (9/30)

추천 아이콘을 목록/빈 화면에서 `lightbulb`로 통일했다. 선택 모드 카드 자체 클릭·Enter·Space를 선택 토글로 연결하고, 체크박스와 선택 수가 함께 갱신되며 잠긴 카드·평소 결과 이동이 유지됨을 검증했다. 삭제 확인창의 ‘그대로 두기’를 홈과 같은 ‘취소’로 변경했다. 홈과 스토리보드는 같은 `ConfirmDialogService`를 쓰며, 취소는 공통 디자인 규칙의 text 버튼이라 hover 상태 레이어가 옅게 보이는 것이지 hover를 끄는 코드가 있는 것은 아니다. 자세한 근거·빌드·남은 검증: [카드 선택·공통 모달 조사](../../implementation/2026-09-30-storyboard-card-selection-confirm-ux.md). 집중41/41·전체5405/5405(종료0)·스타일6/6·패키지 renderer86개 hash 일치. 최신 테스트 앱: `/Users/jina/project/adlight/.worktrees/storyboard-card-select-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. 이번 앱의 실제 화면 열기는 UI 도구 시간 초과로 못 했고 실제 삭제·보관함 사용자 실기도 여전히 미완료. 소스 미커밋.


## 후속 — 삭제된 프로필 결과 액션·확인창 초기 포커스 (9/30)

실제 삭제 후 결과 보존·열기는 사용자가 확인했다. 결과 스냅샷 때문에 삭제된 프로필이 카드에 계속 보이는데, 복제 버튼은 현존 목록 프로필이 필요해 빈 이동을 일으켰다. 결과 화면에서 원본 404를 확인하면 복제·재생성을 막는다. 이유는 복제 버튼 툴팁에서만 안내한다. 공통 확인창은 Material의 첫 버튼 자동 포커스 때문에 취소 버튼에 열린 직후 배경이 보인다는 것을 실제 오버레이 테스트로 재현하고 대화상자 자체에 초기 포커스를 옮겼다. [원인·회귀·새 앱](../../implementation/2026-09-30-storyboard-deleted-profile-and-dialog-focus.md). 관련52/52·전체5409/5409·스타일6/6·macOS arm64 local-api 패키지 renderer86/86 hash 일치. 새 앱은 `storyboard-deleted-profile-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. 원본 dev/기존 앱/실행 Web API는 그대로이며 소스 미커밋.


## 후속 — 삭제 프로필 복제 버튼 표시·툴팁 (9/30)

사용자 최신 지시로 삭제된 원본의 복제 버튼 숨김을 철회했다. 버튼은 결과 화면에 남되 disabled이며 hover/키보드 포커스 시 짧은 이유를 보여준다. 이미 삭제된 원본으로는 복제·재생성할 수 없고 저장된 결과는 계속 읽는다. [구현·테스트·최신 앱](../../implementation/2026-09-30-storyboard-disabled-duplicate-tooltip.md). Angular5409/5409·스타일6/6·macOS arm64 local-api 앱 renderer86/86 hash 일치. 앱: `storyboard-disabled-duplicate-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. 앱 실기는 아직 사용자 확인 전, 소스 미커밋.


툴팁 문구 후속: 사용자가 ‘프로필이 삭제되어 복제할 수 없어요.’를 선택했다. 별도 삭제 안내 블록과 오류 안내 블록·전용 재확인 메서드는 제거했고, 최신 앱은 `storyboard-tooltip-only-build-20260930/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`다. 전체5409/5409·스타일6/6·패키지 문구 부재/해시 확인. [최신 기록](../../implementation/2026-09-30-storyboard-disabled-duplicate-tooltip.md).

## 후속 — 완료 카드 결과 안내 재추가·호버 범위 (9/30)

사용자 최신 요청으로 완료 개수 아래에 `결과 보기 →`를 작고 별도 배경 없는 안내로 다시 추가했다. 완료 개수는 세로 중앙에 유지하고 카드 전체 클릭은 그대로다. 옅은 초록 배경은 결과를 열 수 있는 완료 카드의 hover에만 적용한다. 생성 전·생성 중·선택 모드에는 적용하지 않는다. 집중8/8, 전체5410/5410, 스타일6/6, packaged Angular 통과. 최초 macOS arm64 local-api 앱은 Electron `node_modules` 심볼릭 링크로 인해 `fs-extra`가 누락돼 실행 실패했다. 같은 경로에 실물 의존성 폴더로 재빌드했고 앱 패키지의 Electron 런타임에서 `electron-updater`/`fs-extra` 로드를 확인했다. 로그인 후 실데이터 화면은 아직 직접 확인하지 못했다. [디자인·검증·새 앱 경로·패키징 오류](../../implementation/2026-09-30-storyboard-result-cue-and-hover.md). 이 변경은 W07에만 있으며 `dev` 미병합이다.


## 후속 — 삭제 기록이 있는 사용자 데이터 사본으로 패키지 서버 부팅 (9/30)

당시 원본 `dev`는 삭제 기록 2개를 일반 프로필로 파싱해 보고된 `ShortformDirectorStorageCorruptionError`가 재현됐다. W07은 같은 임시 사본에서 색인 초기화와 활성6/삭제2 분리·삭제 ID 미노출, 배치7/완료문서35 열람, 프로젝트 파일298개 해시 보존을 확인했다. Nest build와 관련36/36 통과. 당시 최신 `.app` 안의 NestJS 번들을 패키지 설정/JWT 공개키 및 사본 데이터로 실행해 `/v1/health`의 `status: ok`를 확인했다. macOS Electron은 임시 `HOME`에서도 실제 appData를 사용하므로 **전체 GUI 앱 실행은 하지 않았다**. [상세·한계](../../implementation/2026-09-30-storyboard-deleted-record-boot-verification.md). 9/30 부분 병합에서는 이 읽기 전용 수정만 Nest `dev`에 반영하고 새 번들로 패키지 모드 health를 재확인했다. 원본 사용자 데이터와 실행 Web API는 수정하지 않았다.
