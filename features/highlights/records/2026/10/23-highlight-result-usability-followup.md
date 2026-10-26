# 2026-10-23 — 안무·인물 결과 화면 후속 사용성

## 작업 기준

- 사용자 요청으로 원본 8개 저장소의 최신 원격 dev를 fetch/pull했다. 실제 변경은 원본 Angular·Python의 새 `feature/highlight-result-usability-20261023` 브랜치에서 진행한 뒤 사용자 후속 승인으로 원격 dev에 반영했다.
- 시작점: Angular `0262c7b8`, Python `e6a138f`; Nest `ae40eb90`, Electron `dfc84d4`, Web API `4b88fdb`, Admin `07c08ba`, Client `fbd4573`, Infra `e504093`.
- 이번 후속은 사용자 “최신 dev에 병합해줘” 승인으로 커밋·푸시·원격 dev 반영을 완료했다. 후속 사용자 요청으로 아래 로컬 API 앱을 재빌드·실행했다. API 서버와 DB는 재시작/초기화하지 않았다. m2-stage 배포는 사용자 미실행 상태다.
- Web API의 기존 로컬 인증 URL 4201 변경 두 파일은 pull 전 임시 보존 후 원상 적용했다. 백업 patch `/tmp/adlight-highlight-local-auth-before-pull-20261023.patch`, stash `preserve-local-auth-during-highlight-dev-pull-20261023`는 보존한다.

## 결과 화면

- 두 플러그인의 체크된 장면/클립이 바로 미리보기와 생성 순서에 반영된다. 최초에는 원본 목록 순서다. 순서를 편집한 뒤 선택 해제한 항목은 순서에서 빠지고 다시 체크하면 현재 순서 뒤에 추가된다. 모든 선택 해제 시 미리보기가 빈다.
- 미리보기 제목 오른쪽 `클립 순서 변경`에서 기존 16:9 구성 모달을 재사용한다. 일괄 메뉴의 별도 미리보기 생성 항목과 생성 버튼 위 수동 구성 안내는 제거했다.
- 메뉴 표기: 안무 `선택 클립 다운로드`·`선택 클립 삭제`, 인물 `선택 장면 다운로드`.
- 인물 제목은 `인물`, 아이콘은 안무와 같은 `group`. 인물 카드 병합 아이콘은 기존 merge 편집 동작·대상 검색 메뉴를 재사용한다. 메뉴를 연 프로젝트와 현재 프로젝트가 달라지면 병합 요청을 내지 않는다.
- 인물 장면 묶음 드래그, 안무 미확인→멤버 카드 병합·선택 클립 이동의 설명을 각 목록에 추가/정리했다.
- 안무 순서는 멤버 → 미확인 인물 → 함께 등장·배정 대기 → 얼굴을 알아보지 못한 클립이다. 미확인 카드의 오른쪽 버튼 안내를 없앴다. 선택 해제된 클립의 흐림 효과를 없앴다.
- 안무 인물 카드의 멤버/미확인 사진은 100×100px로 키웠다. 좁은 창에서도 사진과 조작 아이콘이 겹치지 않도록 기존 컨테이너 배치를 조정한다.
- 안무 아티스트 검색 후보의 `한글명 (영문명)`을 `영문명 (한글명)`으로 바꾼다. 서버/매칭 이름은 그대로다.
- 안무 판정 지도 진입 분기·복귀 버튼·컴포넌트 등록은 주석으로 보존하고 결과 화면으로 직접 진입한다.

## 썸네일 품질과 메모리

- 멤버는 선택한 원본 참조 파일을 Nest에서 그대로 저장하고 Python이 그대로 복사한 파일을 결과 카드에서 사용한다. 중간 저해상도 preview 변환이 없음을 확인했다. 입력 원본 자체가 작으면 개선할 수 없으며, 표시 사진 선택/얼굴 매칭 정책은 바꾸지 않았다.
- 미확인 인물은 기존 얼굴 추출 시 원본 얼굴 주변을 정사각형으로 잘라 최대256px·JPEG92로 별도 저장한다. 원본보다 확대하지 않는다. 정렬된112px recognition evidence·특징·매칭·관측·ML 호출·영상 디코드는 유지한다. 저장 시 JPEG를 다시 압축하지 않는다.
- 기존 결과의112px 파일은 소급 복원되지 않는다. 재분석한 결과부터 새 크기가 적용된다.
- 0.2초 owned 관측은 후보12장 제한의 대상이 아니므로 큰 JPEG를 모두 RAM에 추가하면 10분 합성자료에서150.42MiB가 추가된다. batch별 익명 TemporaryFile에 JPEG를 쓰고 RAM에는 offset만 둔다. 최종 identity 분할에서 선택한 이미지들만 읽는다.
- refinement 후 파일을 명시적으로 닫고, 예외/결과 해제 시 TemporaryFile 수명으로 정리한다. 임시 디스크 사용량은 관측 수에 비례한다. 이후 구간의 이미지나 인물을 임의 top-K로 누락하지 않는다.
- 실제 batch+앞/뒤 분할 선택 합성 회귀에서 Python 추적 peak13,533,630 →1,170,693bytes. 초기/후기 선택 JPEG 바이트 보존, 관련56tests 통과.

## Windows 아이콘 상시 노출

- 사용자 Windows 빌드 보고에 따라 조사했다. Person SCSS의 `@media (hover: none)`가 카드의 모든 조작 아이콘을 항상 보이게 덮어쓰고 있었다.
- Chrome을 `--blink-settings=primaryHoverType=1,availableHoverTypes=1`로 실행해 실제 `(hover: none)` 조건을 확인한 뒤 기존 카드 opacity 테스트에서 동일한 실패를 재현했다.
- 해당 예외를 제거했다. OS/주 입력 장치 분류와 관계없이 기본 숨김, 카드 hover 또는 조작 버튼 keyboard focus-visible에서만 표시한다. 실제 Windows 패키지 검증은 사용자가 해야 한다.

## 검증

- 최종 Angular 전체9,612·스타일14 통과, packaged renderer build 성공. 호버 없음 환경의 Person/Dance 관련135개 통과.
- 최초 최종 전체 검사에서 변경 밖 TemplateBuilderEditor 배경 이미지 업로드1개가 실패했다. 해당 파일193개 단독 검사 및 전체9,612개 재검사에서 모두 통과했다. 관련 제품/테스트 코드는 변경하지 않았다.
- 빌드 최초 제한 환경 실행은 출력 없이134로 종료했고, 같은 명령의 일반 로컬 실행은0으로 완료됐다.
- 로그: `/tmp/highlight-windows-hover-red.log`(아이콘 상시 노출 재현), `/tmp/highlight-windows-hover-green4.log`(135), `/tmp/highlight-template-upload-isolated.log`(193), `/tmp/highlight-result-usability-angular-final-full.log`(9,611pass/1fail), `/tmp/highlight-result-usability-angular-final-full-retry.log`(9,612), `/tmp/highlight-result-usability-angular-final-styles.log`(14), `/tmp/highlight-result-usability-angular-final-build-escalated.log`(빌드), `/tmp/highlight-thumbnail-final-related.log`(Python56).
- Python 관련56tests 통과. 썸네일 최초 변경 전체 검사1,626passed·6skipped·5failed. 이5개는 untouched `e6a138f`에서도 재현됐다: annotation golden4개, ranking fadeblack golden1개. 추가 메모리 수정 뒤 관련 경로를 재검증했으며 전체를 다시 실행하지는 않았다.
- 전체/기준 Python 로그: `/tmp/adlight-dance-thumbnail-python-suite-escalated.log`, `/tmp/adlight-dance-thumbnail-baseline-tests.log`.
- 독립 정적 리뷰에서 선택 순서 유지·프로젝트 범위 병합 보호·hover 예외 제거에 남은 차단 지적 없음.
- 실제 영상 정확도와 Windows 실제 실행은 별도다. 새 Electron 패키지는 아래 후속 요청으로 재빌드·실행했다.


## 후속 요청 — 로컬 API 앱 재빌드

- 사용자 “앱 재빌드해줘”에 따라 Node24로 `npm run build:app:mac:arm64:local-api` 전체 빌드 성공. Angular packaged → Nest bundle → Electron tsc → uv 준비 → electron-builder mac-arm64 순서를 완료했다.
- 앱: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`.
- 패키지 설정의 `webApiBaseUrl=http://127.0.0.1:3000`, 자동 업데이트 비활성화를 확인했다. API `/health`200을 확인했다.
- 패키지 renderer136파일이 현재 Angular 산출물과 동일하고, 변경 Python 소스5파일도 현재 브랜치와 바이트 일치한다. asar의 Electron 진입점·electron-updater·fs-extra 포함을 확인했다.
- 새 앱을 실행하고 해당 패키지의 renderer/index.html#/projects 창이 열렸음을 확인했다. 이번 재빌드는 macOS ARM64이며 Windows 패키지는 별도다.
- 빌드 로그: `/tmp/adlight-highlight-result-app-build-20261023.log`.


## 후속 요청 — 최신 원격 dev 병합 완료

- 사용자 “최신 dev에 병합해줘” 승인 후 두 저장소의 원격 dev를 다시 fetch했다. 시작점 이후 원격 추가 커밋이 없어 충돌 없이 fast-forward했다.
- Angular: `baf2f54d3a74d57b64e10d2e5168bc88d5e09df1` — `feat(highlights): refine result previews and person interactions` (15파일).
- Python: `3b3e203cab1f45b38ac729ba2537c2fcfa11dfaa` — `fix(dance): preserve sharp face thumbnails with bounded memory` (8파일).
- 각 저장소의 dev와 `feature/highlight-result-usability-20261023`을 atomic push했다. `git ls-remote`로 원격 dev=원격 작업 브랜치=로컬 HEAD를 확인했다. 원본 두 체크아웃은 dev·clean, origin/dev와 양방향 차이0/0이다.
- 병합 전 새 검증: Angular 전체9,612·스타일14 통과. Python 안무 파이프라인 전체와 공통 얼굴 모듈206 통과.
- 로컬 dev 반영 후 검증 트리와 Git tree hash 일치 확인. 호버 없음 환경의 Person/Dance135, Python 안무·공통 얼굴206 재검증 통과 후 푸시했다.
- 로그: `/tmp/adlight-highlight-dev-merge-angular-tests-20261023.log`, `/tmp/adlight-highlight-dev-merge-angular-styles-20261023.log`, `/tmp/adlight-highlight-dev-merge-python-tests-20261023.log`, `/tmp/adlight-highlight-dev-merge-angular-postmerge-20261023.log`, `/tmp/adlight-highlight-dev-merge-python-postmerge-20261023.log`.
- 원본 작업 patch 백업: `/private/tmp/adlight-highlight-dev-merge-20261023/`. 작업 브랜치는 로컬·원격에 보존했다.
- 이번 반영에는 Electron·Nest·Web API 소스 변경이 없다. 앞서 실행한 앱의 소스 내용과 동일하며 앱·서버·DB를 재시작/초기화하지 않았다.


## 추가 후속 — 안무 카드 텍스트 정렬 (최초 수정·빌드 당시)

- 사용자 보고: 인물 사진 아래로 멤버 이름·클립 개수가 내려가고, 클립 제목·시간은 세로 중앙에 놓이지 않았다.
- 최신 origin/dev(`baf2f54d`)와 로컬 dev 일치를 확인하고 Angular `fix/dance-result-card-alignment-20261023`에서 수정했다. 당시 변경은 Dance 결과 SCSS·기존 spec 두 파일인 미커밋 상태였다. 이후 추가 요청을 함께 반영한 원격 dev 병합은 아래 최신 기록을 따른다.
- 원인은 직전100px 사진 대응의 person-list329px 이하 규칙이 person-row를1열로 바꾼 것이었다. 이1열 전환을 제거하여 사진 오른쪽 이름·클립 수와 중앙 정렬을 유지한다.100px 사진·기존 좁은 폭 아이콘 배치는 유지한다.
- 클립 grid에 `align-items:center`를 지정하여 제목·시간을 포함한 텍스트 묶음을 사진과 카드의 세로 중앙에 놓는다. 매우 좁은 클립 칸의 기존 사진 위/제목 아래 배치는 별도 정책으로 유지한다.
- 실제 브라우저에서 수정 전5개 실패를 재현했다. 인물 오른쪽 배치1200·1440·1600px 및 클립 중앙 정렬1440·1600px 회귀를 포함해 관련81, 전체9,616, 스타일14 통과. packaged renderer build 성공.
- 로그: `/tmp/adlight-dance-card-alignment-red-20261023.log`, `/tmp/adlight-dance-card-alignment-green-20261023.log`, `/tmp/adlight-dance-card-alignment-full-20261023.log`, `/tmp/adlight-dance-card-alignment-styles-20261023.log`, `/tmp/adlight-dance-card-alignment-build-20261023.log`.
- 후속 사용자 “재빌드해줘” 요청으로 카드 정렬 수정이 포함된 로컬 API용 macOS ARM64 앱을 전체 재빌드·실행했다. renderer136파일이 최신 산출물과 일치하고 API 주소127.0.0.1:3000·arm64 실행 파일을 확인했다. 빌드 로그: `/tmp/adlight-dance-card-alignment-app-build-20261023.log`.


## 추가 후속 — 카드 정렬·인물 이동 모달 공통화, 원격 dev 반영 완료

- 사용자 “dev 병합해줘” 승인 후 이어진 아이콘·정렬·모달·장면 수 요청을 함께 반영했다. Angular 커밋 `7c06eade87ff2f3e892b4c52a2a4e7dc61c07c53` (`fix(highlights): align cards and reuse person destination picker`), 11파일이다.
- `fix/dance-result-card-alignment-20261023`에서 커밋하고 최신 원격 dev(`baf2f54d`)를 다시 확인한 뒤 충돌 없이 fast-forward했다. dev·작업 브랜치를 atomic push했고 `git ls-remote`로 원격 두 ref=로컬 HEAD를 확인했다. 원본 Angular는 dev·clean, origin/dev와0/0이다. 검증한 diff와 커밋 내용, 병합 전후 tree hash 일치를 확인했다.

### 동작

- 안무 인물 이름·클립 개수는100px 사진 오른쪽, 클립 제목·시간은 카드의 세로 중앙에 유지한다.
- 안무 인물 카드의 단일 다운로드 아이콘이 좁은 폭에서 중앙보다17px 아래로 놓이던 문제를 실제 브라우저에서 재현했다. 아이콘을 묶고 묶음 전체를 가운데 정렬하여 단일/복수 아이콘 모두 중앙에 배치한다. 좁은 폭의 hover 아이콘 overlay 방식은 유지한다.
- 인물 카드의 병합 아이콘·툴팁은 장면 카드와 같은 `drive_file_move`·`다른 인물로 이동`이다. 인물 전체 이동은 기존 merge 편집 동작을 사용한다.
- 인물 전체·개별 장면·선택 장면 일괄 이동에서 기존 `DanceMemberPickerDialogComponent`를 재사용한다. 별도 인물 메뉴·검색 입력·hover 얼굴 팝업과 관련 상태/스타일은 제거했다.
- 모달은 사진·이름·`장면 N개`를 함께 표시한다. 목록의 `visiblePersonSceneCount`와 같은 기준으로 중복 ID·제외 장면·없는 ID를 제외하며0개도 표시한다. 현재 원본 인물과 미확인 그룹은 목적지에서 제외한다. 장면 수 순서는 인물 목록과 같다.
- 모달 제목·장면 수는 선택적 데이터이므로 안무의 기존 멤버 지정 모달 기본 제목·항목 선택은 유지한다.
- 원본 인물/장면 ID는 모달을 열 때 고정한다. 취소·다른 프로젝트로 전환·원본/대상 삭제·처리 중 상태에서는 잘못된 편집 요청을 내지 않는다. 중복 모달을 막고 화면 해제 시 모달을 닫는다. 드래그 이동 경로는 변경하지 않았다.

### 검증·남은 한계

- 정렬 RED5개·아이콘 중앙 정렬 RED3개·모달 전환 RED6개를 확인했다. 최종 안무/인물/공통 모달 관련150개, 스타일14개, packaged renderer 빌드 통과.
- 최종 전체9,619개는 Jasmine `random:true`, seed `20261023` 고정으로 통과했다. 테스트를 제외하거나 단언 기준을 완화하지 않았다. 재현용 config `/private/tmp/adlight-card-picker-karma-20261023.cjs`.
- 일반 임의 순서 전체 검사 두 번은 각각9,618pass/1fail이었다. 첫 실패는 `TemplateBuilderEditorComponent 배경 추가가 서버 쪽 실패면 서버 에러번호를 그대로 싣는다`(spec1627, notify 호출 미관측), 두 번째는 `StoreComponent [모두 설치]가 사라져도(N=0) 카드가 움직이지 않는다`(spec245,3px 차이)다. 템플릿193개 단독 통과, 원본 dev 제품 코드 전체9,612개 통과도 확인했다. 두 간헐 실패의 원인을 이번 작업에서 해결했다고 주장하지 않는다. 관련 제품/테스트 파일은 변경하지 않았다.
- 안무 레이아웃 검사는 자신이 바꾼 전역 viewport 속성을 원상 복구하도록 보완했다. 앞선 병합 준비 중 Store3px 실패 뒤 추가한 테스트 격리이며, 이후 Store 실패가 재관측됐으므로 이것을 Store 문제의 확정 해결로 취급하지 않는다.
- 별도 읽기 전용 코드 리뷰에서 병합 차단 지적 없음. 실제 Windows·다크/라이트 앱 시각 확인은 이번 코드/헤드리스 검증과 별도다.
- 화면 빌드는 실행 중 앱 리소스를 덮지 않는 `/private/tmp/adlight-highlight-card-picker-renderer-20261023`에 생성했다. 앞서 실행한 ARM64 앱에는 최초 카드 정렬까지만 포함되어 있다. 이번 추가 아이콘·이동 모달·장면 수 표시의 Electron 패키지는 아직 재빌드하지 않았다.
- 로그: `/tmp/adlight-person-move-picker-red-20261023.log`, `/tmp/adlight-person-move-picker-green-20261023.log`, `/tmp/adlight-highlight-card-picker-full-20261023.log`, `/tmp/adlight-highlight-card-picker-template-isolated-20261023.log`, `/tmp/adlight-highlight-card-picker-full-retry-20261023.log`, `/tmp/adlight-highlight-card-picker-baseline-full-20261023.log`, `/tmp/adlight-highlight-card-picker-full-seed-20261023.log`, `/tmp/adlight-highlight-card-picker-styles-20261023.log`, `/tmp/adlight-highlight-card-picker-build-20261023.log`.
- 최종 diff 백업 `/private/tmp/adlight-highlight-card-picker-final-20261023.patch`, 검증 tree `/private/tmp/adlight-highlight-card-picker-verified-tree-20261023.txt`.


## 후속 — 원본 8개 저장소 최신 dev pull 및 앱 재빌드·실행 완료

- 사용자 “모든 저장소 (원본) 최신 dev 원격 다시 pull 받고 빌드 다시해줘” 요청으로 원본8개에 `git pull --ff-only origin dev`를 실행했다. 모두 dev이며 로컬 HEAD=origin/dev를 확인했다. 당시 기준 SHA:

- `desktop/clipper_angular`: `01b815f3db2e809be65837d8cb57478717cb55c3`
- `desktop/clipper_electron`: `dfc84d4889a2ee6ecbf8dec326436d76a514ba79`
- `desktop/clipper_nestjs`: `df4d586f09bf6852dfc810c6f7648b1549ee058d`
- `desktop/clipper_python`: `11fbc9d486bab5f5b46cefee60a9ab10e6f8d7e9`
- `web/clipper_web_api`: `db0ca363366765147d08fa12d698b7857f536149`
- `web/clipper_web_admin`: `090d4e7003517e8cb79adbad27d6c42520fa2421`
- `web/clipper_web_client`: `fbd457314982350da159e5ab1fb386074626bcc9`
- `web/clipper_infra`: `e5040931fb3ecb2b7d715f3938eaa39ca9ad8b96`

- Web API의 기존 `.env.example`·`auth.controller.ts` 로컬 인증 주소 변경은 patch와 stash로 보존한 뒤 다시 적용했다. pull 전후 실제 추가/삭제 줄이 일치한다. 다른7개는 clean이다. 백업 `/private/tmp/adlight-web-api-local-auth-before-dev-pull-rebuild-20261023.patch`, stash `preserve-local-auth-before-dev-pull-rebuild-20261023` 보존.
- 원본 Electron에서 Node24로 `npm run build:app:mac:arm64:local-api` 전체 빌드 성공. Angular packaged·Nest ncc·Electron tsc·uv·electron-builder까지 완료했다. 이번 빌드는 앞서 미반영이던 이동 모달·장면 수·아이콘 정렬도 포함한다.
- 앱: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`. arm64 실행 파일, API주소 `http://127.0.0.1:3000`, 자동 업데이트 비활성화를 확인했다.
- 패키지의 renderer136·Nest88·Python158파일이 원본 산출물/소스와 SHA-256 일치한다. asar의 Electron 진입점·electron-updater·fs-extra 포함을 확인했다. 빌드 전후8개 HEAD·로컬 수정 상태도 일치했다.
- 새 앱을 실행해 해당 패키지의 `index.html#/projects` 홈과 실제 프로젝트 목록·인증 상태 표시를 확인했다. 로컬 Web API `/health`는200이며3개 DB 상태ok다. Web API 프로세스/클라이언트4201/어드민4202는 기존 실행을 유지했다. Web API 소스 pull 자체가 실행 중 서버 재기동을 뜻하지는 않는다.
- 빌드 로그 `/tmp/adlight-all-dev-pull-app-build-20261023.log`, SHA/수정 상태 manifest `/private/tmp/adlight-all-dev-pull-build-manifest-20261023.json`. 별도 전체 단위검사·Windows 빌드·ML 실영상 실행은 이번 빌드 확인에 포함하지 않았다.


## 후속 — 인물 이동 모달 사진80px·이름/장면 수 간격 축소 (미커밋)

- 사용자 요청으로 최신 origin/dev `01b815f3`에서 Angular `fix/person-move-picker-spacing-20261023`을 만들었다. SCSS1파일만 수정한 미커밋 상태다.
- 인물 이동 모달의 장면 수가 있는 후보 타일에 한해 사진·빈 사진 자리를80×80px로 키웠다. 인물 이름과 `장면 N개` 사이 flex gap은8→2px다. 사진과 이름 사이 기존8px는 유지한다. 안무 멤버 지정 타일은 장면 수가 없어 기존52px 사진을 유지한다.
- 기존 실제 모달/Person/Dance 관련150개·스타일14개 통과, `git diff --check` 통과. 이번 크기·간격 변경으로 새 테스트를 추가하지 않았다. 로그 `/tmp/adlight-person-picker-size-spacing-tests-20261023.log`, `/tmp/adlight-person-picker-size-spacing-styles-20261023.log`.
- 실행 중인 앱은 종료·교체하지 않았다. 이 후속 스타일은 Electron 패키지를 아직 재빌드하지 않아 기존 실행 앱에는 미반영이다.


## 후속 — 80px 모달 스타일 앱 재빌드·실행 완료

- 사용자 “재빌드해줘” 요청으로 `CLIPPER_BUILD_OUTPUT_DIR=dist-app-person-picker-80px-20261023 npm run build:app:mac:arm64:local-api` 전체 빌드 성공. Angular의 미커밋 SCSS1파일을 포함한다.
- 시작 시 기존 앱에 대기 작업2개가 보여 별도 출력 경로로 빌드했다. 빌드 후 기존 앱 프로세스가 종료된 것을 확인하고 새 패키지를 실행했다. 기존 앱 종료를 에이전트가 요청하지 않았다.
- 실행 앱: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app-person-picker-80px-20261023/mac-arm64/Clipper Studio (dev).app`. 해당 경로의 renderer `index.html#/projects` 창이 실제 열렸음을 확인했다.
- renderer136·Nest88·Python158파일 SHA-256 일치, 새 renderer 청크의80×80px·2px 간격 규칙 포함, asar main/electron-updater/fs-extra, arm64·로컬 API3000·자동 업데이트 비활성화를 확인했다. 빌드 전후4개 데스크톱 HEAD/수정 diff 해시도 같다. API health200이다.
- 로그 `/tmp/adlight-person-picker-80px-app-build-20261023.log`, 입력 manifest `/private/tmp/adlight-person-picker-80px-build-manifest-20261023.json`. 새 커밋·푸시·dev 병합은 하지 않았다.


## 후속 — 80px 인물 이동 모달 원격 dev 병합 완료

- 사용자 “dev병합해줘” 요청으로 Angular `af8fe16e2679e211dfa13cf3510c8cbc2cb198d2` (`fix(person): enlarge move picker faces and tighten labels`)을 커밋했다. 변경은 공통 모달 SCSS1파일10줄이며 인물 타일80×80px·이름/장면 수 간격2px를 포함한다.
- 최신 원격 dev `01b815f3`를 다시 fetch했고 추가 변경이 없었다. 충돌 없는 fast-forward 후 dev와 `fix/person-move-picker-spacing-20261023`을 atomic push했다. 원격 두 ref=로컬 HEAD, 원본 Angular dev·clean·0/0을 확인했다. 검증한 diff·커밋 내용·병합 tree가 일치한다. 작업 브랜치는 보존했다.
- 최종 전체9,647개(Jasmine random:true·seed20261023)·스타일14개 통과. 최초 전체는9,646pass/1fail로 기존 `TemplateBuilderEditorComponent 배경 추가가 서버 쪽 실패면 서버 에러번호를 그대로 싣는다`(spec1627, notify 호출 미관측)가 실패했다. 제품/테스트 변경 없이 템플릿193개 단독·동일 순서 전체 재검사 모두 통과했으며 간헐 실패를 이번 CSS로 해결했다고 주장하지 않는다.
- 읽기 전용 코드 리뷰에서 차단/중요 지적 없음. 사진 없는 자리도80px, 사진/이름8px 유지, 이름/장면 수2px,380px 모달3열 수용 및 안무52px 유지 범위를 확인했다.
- 앞서 재빌드·실행한 별도 ARM64 앱과 같은 소스 내용이다. 이번 병합에서 실행 중 앱·서버·작업을 종료하거나 재빌드하지 않았다.
- 로그 `/tmp/adlight-person-picker-80px-dev-merge-full-20261023.log`, `/tmp/adlight-person-picker-80px-dev-merge-template-isolated-20261023.log`, `/tmp/adlight-person-picker-80px-dev-merge-full-retry-20261023.log`, `/tmp/adlight-person-picker-80px-dev-merge-styles-20261023.log`. diff `/private/tmp/adlight-person-picker-80px-before-dev-merge-20261023.patch`, tree `/private/tmp/adlight-person-picker-80px-dev-merge-verified-tree-20261023.txt`.
