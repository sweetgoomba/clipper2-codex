최신 hover 변경까지 포함한 앱은 [카드 hover 후속](2026-09-29-storyboard-card-hover.md)의 `dist-app/hover-tint/mac-arm64/Clipper Studio (dev).app`이다. 아래 purpose UX/이름/문구 철회 빌드는 후속에서 대체됐다.

# W07 제작 목적 안내·입력 제한 후속 — 2026-09-29

사용자 지시로 제작 목적 미입력 UX를 적용하고, 프로필 이름120→50자, 제작 목적500→150자로 변경했다. 목적500자 유지 초안은 후속 지시150자로 대체됐다. 기존 W07 격리 worktree의 미커밋 변경이며 원본 checkout·다른 세션 소스에는 반영하지 않았다.

## 구현

- 이름·분야·제작 목적에 필수 표기. 제작 목적에는 추천 하나 선택 또는 직접 입력 안내를 항상 표시한다.
- 고정 footer에서 비활성 버튼 이유를 표시한다. 목적만 비었으면 “제작 목적을 선택하거나 입력하면 프로필을 생성할 수 있어요.”와 목적 영역으로 스크롤/키보드 포커스를 옮기는 버튼을 표시한다. 편집은 “수정”으로 안내한다. 여러 필수 항목이 잘못되면 해당 항목 목록을 표시하고, 길이 초과는 글자 제한으로 설명한다.
- 초기 진입에서는 인라인 오류를 표시하지 않는다. 추천 해제/직접 입력/blur 후 목적이 비거나 길이를 넘으면 목적 아래에 오류를 표시한다. 유효한 목적을 입력·선택하면 인라인/버튼 안내가 사라지고 저장 버튼이 활성화된다. 기존 선택 해제값과 저장 payload 일치 동작을 유지한다.
- 이름 placeholder의 “예: …” 형식을 목적에도 적용: “예: 바쁜 직장인에게 하루 10분 독서 루틴을 소개해, 퇴근 후 스마트폰 대신 책을 읽는 습관을 만들도록 돕기”. 대상·방법·기대 행동 예시를 담았고 목적은3줄 textarea로 바꿨다.
- 입력 아래에 이름50자/목적150자 제한 안내를 항상 표시한다. UI validator와 신규 생성/수정 DTO·service 정책에 같은 제한을 적용한다. 복제 이름은 접미사/숫자를 포함해50자 안에 들어가게 원본 이름을 줄여 충돌을 회피한다.
- Nest 저장 profile/snapshot parser의 기존120/500 스키마는 그대로다. 신규 쓰기 경계만50/150으로 검증한다. 기존 파일/스냅샷 읽기를 실패시키거나 자동 절단하지 않고, 무관한 API patch는 기존 값을 그대로 보존한다. 새 호환 분기·변환·마이그레이션을 추가하지 않았다.

## 검증

- TDD: 초기 UI4expected failures 및 복제 이름1expected failure 확인. 목적150 변경 전에는150/151경계1fail/28pass. inline 테스트는 실제 Material 칩 click과 안정화 대기로 사용자 흐름을 검증하도록 수정했다. 최종 폼/프로필 focused56/56, 전체 Angular5400/5400, 스타일6/6, packaged AOT exit0.
- Nest name50 RED(storage2/API2) 및 목적150 RED5 확인 후 fresh build, API/storage/delete/lock/preflight54/54 PASS. root의 독립 확인51+preflight3 모두 PASS.151/51 거부 시 실제 파일 쓰기 없음, 기존 저장값/스냅샷/정산·실행 잠금 보존 확인.
- Chrome fixture: 생성 화면 목적만 미입력인 이유/필수 안내/포커스 이동, 선택 해제·빈 입력 blur 오류, 정상 입력 복구, native150/50 제한 PASS. 다크/라이트1280/390 모두 dialog/form 가로 넘침 없음, JS error0. 실제 서버 저장·AI 요청은 하지 않았다.
- 독립 추가 리뷰 Critical/Important 없음. Minor: native maxlength는 UTF-16 단위, validator/API는 Unicode code point라 emoji 입력은 UI에서 더 일찍 제한될 수 있다. 기존 방식의 제한 차이이며 한글/영문50/150경계 검증은 통과했다.
- 현재 성능/과금 처리에는 추가 변경 없음. 실제 생성 전후 성능·품질·정산 및 OS 물리 IME는 여전히 실기 미확인이다. 이전 오프라인 측정과 이 화면 fixture를 실공급자 성능으로 해석하지 않는다.

## 최신 테스트 앱

Angular packaged, Nest ncc+assets/fonts, Electron TS, uv, electron-builder --dir --publish never를 순서대로 실행해 새 경로에 빌드했다. 기존 테스트 앱을 덮어쓰지 않았다. 전체 renderer86파일/Nest bundle hash 일치, uv/auth/config 존재, Python git 메타 없음, actual packaged Electron Node 모드 updater/fs-extra 로딩 PASS. UI 앱을 실행하거나 기존 앱/서버를 종료하지 않았다.

```sh
open "/Users/jina/project/adlight/.worktrees/storyboard-followups-20260929/desktop/clipper_electron/dist-app/result-label-reverted/mac-arm64/Clipper Studio (dev).app"
```

같은 dev identity이므로 기존 Clipper 앱을 사용자가 종료한 후 실행한다. 기존 원본 Web API localhost3000 프로세스는 보존했으며 Web 원장 표시명 반영은 별도 대상이다. 이전 dist-app/mac-arm64 앱에는 이번150/50·안내 변경이 없으므로 위 새 경로를 사용한다.

## 근거·겹침

- output/storyboard/2026-09-29/purpose-ux-browser-results.json, purpose-ux-{dark,light}-{1280,390}.png, purpose-ux-limits.png, purpose-ux-packaged-files.json과 purpose-*.log.
- .worktrees/storyboard-followups-20260929/BACKEND-RESULTS.md, REVIEW.md.
- 후속 변경 경로: Angular features/shortform-director/components/operating-profile-form/* 및 pages/profiles-page/*.ts/spec; Nest modules/shortform-director/application/shortform-director-profile.service.ts, presentation/dto/{create,update}-shortform-director-profile.dto.ts, operating-profile-dto.validators.ts, profile API/storage tests.
- W10 공통 폼/UI 경계와 같은 주제지만 실제 소스 작업 경로는 W07 worktree로 분리했다. 원본 shared/UI, W10/W11/TC4 checkout, Web 코드에는 이번 추가 변경 없음. 문서 공유는 W07 카드·행·기록만 갱신했다. commit/push/merge/deploy 없음.

예전 예외 데이터가 존재할 수 있다는 이유만으로 계속 호환 기능을 늘리는 것은 정당화하지 않았다. 이전 W07의 기존 프로필 안내는 팀원D13 근거였지만 실제 사용/보존 필요 확인 없이 장기 유지 필요성을 단정할 수 없다. 이번 후속에서는 추가 레거시 기능을 구현하거나 저장 데이터를 자동 삭제하지 않았다.


## 후속 — 프로필 이름 예시 주제 통일

직전 앱에서 이름 placeholder가 생활 팁으로 남아 있던 누락을 수정했다. 이름은 “예: 퇴근 후 10분 독서 루틴”으로 목적의 직장인/하루10분 독서 습관 예시와 맞췄다. 제품 변경은 HTML문구 한 곳뿐이며 기존50/150 제한과 동작은 그대로다. Angular packaged build·native packaging exit0, renderer86파일/Nest bundle hash 일치 및 실제 패키지 문구 확인. 신규 테스트/전체 회귀 반복 없음. 최신 앱 경로는 위 purpose-ux-name이며 이전 purpose-ux 앱에는 이 이름 문구 변경이 없다. 기존 앱 보존·UI 실행 없음. 근거 output/storyboard/2026-09-29/name-example-{angular,native}.log, name-example-packaged-files.json.


## 후속 — 완료 카드 결과 보기 문구 철회

사용자 지시로 이번 세션에서 추가한 완료 카드의 “결과 보기 ›” span과 전용 CSS를 제거했다. 완료 개수 표시와 기존 카드 클릭 이동은 그대로다. 완료 갱신 회귀 테스트의 해당 문구 기대값을 “스토리보드2개 생성 완료”로 수정했다. 기존 카드/프로필 회귀33/33 PASS, git diff --check 및 packaged Angular/native build PASS. 새 app renderer86파일/Nest bundle hash 일치, 제거된 전용 class/label element 부재 확인. 최신 앱 result-label-reverted 경로이며 이전 빌드에는 제거가 반영되지 않았다. 기존 앱/서버 종료·UI 실행·커밋 없음. 근거 output/storyboard/2026-09-29/result-label-revert-* 파일.
