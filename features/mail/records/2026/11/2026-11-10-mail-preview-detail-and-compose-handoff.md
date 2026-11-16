# Clipper 메일 미리보기·상세 패널 후속과 작성 재설계 인계

작성일: 2026-11-10, 한국 시간 기준. [이전 세션 종합 기록](2026-11-10-mail-session-summary.md) 이후의 추가 요청이다.

## 현재 결과와 Git 범위

관리형 Admin 워크트리 `/Users/jina/.codex/worktrees/mail-integration-admin-261109/clipper_web_admin`의 `fix/mail-activity-detail-panel-261110`, HEAD `97c1cd9d6064e215cee7f6e8e7f94f929811027c` 위에서 수정했다. **이번 후속 변경은 미커밋·미푸시·미배포**다. 원본 `web/clipper_web_admin` dev는 여전히 clean이며 다른 제품 repo/API/DB/env/AWS는 변경하지 않았다. 이전 종합 기록의 ‘dev 반영 완료’는 이전 커밋까지를 뜻한다.

## 재현·원인·수정

사용자의 개발 어드민 크레딧 충전 상세에서 메일 내부 ‘문의하기’를 누르면 iframe의 문서가 `about:srcdoc`에서 `https://dev.clipperstudio.ai/#contact`로 바뀌는 것을 재현했다. 부모 어드민 URL은 유지되지만, 메일 문서가 홈페이지로 교체된다. `sandbox="allow-same-origin"`은 iframe 자신의 이동을 막는 설정이 아니며, 홈페이지에 필요한 스크립트는 허용하지 않으므로 정상 표시되지 않는다. 캡처에서 검은 본문과 오른쪽 얇은 흰색 영역도 확인했다. 확인 후 사용자의 원래 개발 화면은 새로고침으로 정상 메일 상태로 복구했다.

미리보기 전용 문서를 만들 때 a/area의 href·target·download·ping을 제거하고 읽기 전용 링크로 표시한다. 링크 글자/서식과 본문은 유지하며 ‘내용 확인용 미리보기입니다. 링크는 열리지 않습니다.’를 표시한다. 실제 저장된 메일 본문과 실제 발송 HTML은 변경하지 않는다. sandbox는 그대로 유지한다. 일반 클릭·가운데 클릭 모두 화면을 이동시키지 않는 것을 격리 브라우저에서 확인했다.

## 상세 패널 UI

기존 AppShell·Page·Card·Modal drawer·StatusChip·Material 버튼·토큰·폰트·아이콘을 재사용했다. 점으로 이어 붙인 메타 문장은 정의 목록의 라벨/값으로 바꿨다.

- 공통: 메일 유형, 발송 방식, 수신 인원. 상태 칩과 새로고침은 카드 상단에 분리.
- 자동: 자동 이벤트, 발송 요청 일시. 자동 메일에 예약 시각이라고 표시하지 않고 시스템 생성 일시와 중복되는 작성 일시도 생략.
- 수동 즉시: 발송 대상, 발송 요청 일시, 작성 일시. 없는 예약 시각을 만들어 보여주지 않음.
- 수동 예약: 발송 대상, 예약 발송 일시, 발송 요청 일시, 작성 일시를 별도 항목으로 구분.
- 한국 시간 안내를 한 번 표시. 목록/수신자 결과/취소/페이지 이동 흐름 유지.

제품 컴포넌트를 그대로 렌더링하는 별도 Angular 엔트리를 만들었다. fixture만 사용하고 HTTP·발송/취소 쓰기 요청을 차단한다. prod 라우트에는 추가하지 않았다.

- [자동 메일 상세 목업](http://127.0.0.1:4212/#/mail?screen=detail&id=review-payment-topup)
- [예약 메일 상세 목업](http://127.0.0.1:4212/#/mail?screen=detail&id=review-scheduled)

로컬 정적 서버4212는 검토용이며 임시 산출물에 의존한다. 새로 빌드할 때 `src/mail-detail-review-main.ts`, `src/mail-detail-review-index.html`, `tsconfig.mail-detail-review.json`을 사용하고 생성된 entry HTML은 정적 서버의 index.html로도 둔다. 그렇지 않으면 hash router가 `/`로 이동한 뒤 새로고침에서 디렉터리 목록이 나온다. UI 복제품이나 별도 HTML 목업을 만든 것이 아니라 기존 실제 페이지를 fixture로 구동한 것이다.

## 현재 메일 유형 — 이번에 변경하지 않음

API/admin의 MailType은 `notice | marketing` 두 개다. 자동 큐는 모든 확정 이벤트를 notice로 기록하며 관리자에서 서비스 안내라고 표시한다.

| 자동 이벤트 | 현재 유형 |
|---|---|
| 웰컴 메일 | notice · 서비스 안내 |
| 구독 결제 | notice · 서비스 안내 |
| 구독 갱신 | notice · 서비스 안내 |
| 플랜 변경 | notice · 서비스 안내 |
| 크레딧 충전 | notice · 서비스 안내 |
| 갱신 결제 실패 안내 | notice · 서비스 안내 |
| 갱신 결제 실패 최종 안내 | notice · 서비스 안내 |
| 문의 접수 안내 | notice · 서비스 안내 |
| 환불 접수 안내 | notice · 서비스 안내 |
| 탈퇴 완료 안내 | notice · 서비스 안내 |

최종 확정한 정보성 본문 기준의 비광고 분류다. 발송이 자동이라는 이유만으로 비광고가 되는 것은 아니다. 홍보가 들어가면 그 내용에 맞게 판단해야 한다.

| 향후 수동 작성 내용 | 현재 기반의 유형 | 상태 |
|---|---|---|
| 정책 변경·점검·장애·이용 제한 등 필요한 운영 안내 | notice · 서비스 안내 | 기존 manual API 범위. 작성 UI는 disabled |
| 개별 문의 답변 등 개별 응대 | 정보성 응대라면 notice | 문의 답변 업무·비회원 이메일 입력/선택은 별도 설계 대상, 구현 완료 아님 |
| 신기능·이벤트 참여·혜택 등 홍보 | marketing · 광고성 안내 | 동의 회원 전체 대상, 광고 표시·수신거부 적용 |

서비스 안내라는 이름이 가입·결제 알림과 운영 공지를 모두 묶어 가독성이 낮다는 문제를 확인했다. 내용 표시를 ‘이용·거래 안내 / 운영 공지 / 광고·홍보’처럼 나누는 것을 제안할 수 있지만 아직 사용자 확정이 아니며 enum/DB/API를 바꾸지 않았다. 광고/비광고 구분, 내용 분류, 자동/수동 발송 방식은 다른 기준이다. 자세한 내용 분류를 별도 저장할지도 작성 재설계 채팅에서 확정한다.

기존 Resend 문의 전달·운영자 초대/비밀번호 재설정은 메일 캠페인 목록의 notice/marketing 분류와 별개이며 이번 변경으로 SES로 이전하지 않는다.

## 메일 작성 별도 채팅

사용자 지시로 **‘Clipper 메일 작성·임시저장 재설계’**, ID `01a1c2aa-4db2-7330-8087-8e73261dc07f`를 생성했다. 해당 채팅은 코드·실제 개발 어드민·공식 라이선스를 조사하고 기능안/3가지 화면 구성을 제시한 뒤 사용자 컨펌을 기다린다. 목업·제품 코드 수정은 하지 않았다.

먼저 요구사항을 확인받고, 그 뒤 기존 앱 디자인을 사용해 다음 대안을 나눠 목업으로 보여주도록 전달했다.

1. 기존 버튼 + 임시저장 필터.
2. ‘작성·임시저장’ 추가 탭 + 초안 목록과 전용 작성 화면.
3. 새 작성/초안 불러오기부터 내용→대상·일정→확인으로 진행하는 단계형.

제목·서식/표/이미지/링크 에디터, 미완성 초안 저장·목록/검색/불러오기/수정/복제/삭제, 저장 상태/이탈 경고, 전체/조건/직접 선택 수신자·발송 가능 인원/제외 사유, 즉시/예약, 공통 디자인 포함 미리보기, 최종 확인, 예약 취소·결과, 권한/충돌/중복/오류 복구를 범위 제안에 포함했다. 기존 임시저장 API는 완성된 제목·본문·대상 검증을 요구하고 수동 본문은 텍스트여서, 일반적인 미완성 초안/이미지 보존과 삭제·복제를 모두 구현 완료로 볼 수 없다.

### 에디터 조사

- Tiptap: MIT 공개 코어/공개 확장 기반으로 기존 Angular 도구 모음을 붙이는 문서형 작성에 유리. 메일 전용 HTML/인라인 스타일과 업로드 연결은 별도 개발. [공식 개요](https://tiptap.dev/docs/editor/getting-started/overview), [이미지 확장](https://tiptap.dev/docs/editor/extensions/nodes/image).
- GrapesJS + MJML: BSD-3-Clause 코어/플러그인, MJML 이메일 HTML 생성. 이메일 블록/배치에 유리하나 데이터 표 편집·기존 어드민과의 UI 조정은 별도 검토. [코어 라이선스](https://github.com/GrapesJS/grapesjs/blob/dev/packages/core/LICENSE), [MJML 플러그인](https://github.com/GrapesJS/mjml).
- EmailBuilder.js: MIT 블록 편집기. React 기반이므로 Angular 통합 부담과 공개판 기능 범위를 검토. [공식 저장소](https://github.com/usewaypoint/email-builder-js).

확인 가능한 채택 사례로 Mautic 공식 문서에서 GrapesJS/MJML 사용을 확인했다. 보급률이나 비공개 제품의 내부 구현을 추측하지 않는다. [Mautic 개발 문서](https://devdocs.mautic.org/en/7.1/themes/grapesjs.html).

MIT/BSD 공개 패키지를 조합하고 필요한 고지를 유지하는 범위로 검토한다. Tiptap Pro/Cloud, GrapesJS Studio SDK 등 유료/별도 라이선스 제품을 무료 코어와 혼동하지 않는다. 라이브러리 최종 선정·설치·Angular22 실행 검증은 아직이다.

### 이미지와 S3 — 확정 전 제안

사용자는 ‘편집기 삽입 즉시 업로드하지 말고 실제 발송 내용에 남은 이미지만 S3 저장’을 원한다. 임시저장 이미지를 다시 열려면 저장 위치가 필요하므로, 브라우저 한정 보관과 S3 외 서버 임시 보관의 차이를 새 채팅에서 설명했다. 다른 PC에서 재열기, 삭제/취소·공유 참조/고아 파일 정리, 업로드 일부 실패/중복·예약 이미지 준비 시점과 발송본 장기 보존을 함께 정해야 한다. 예약 확정 때 업로드할지 실제 발송 직전 할지도 미확정이다.

‘공통 로고가 이미 S3’라는 사용자 전제는 현재 기본 코드와 다르다. 기본 로고는 API 소스 PNG를 CID 첨부하며 S3 업로드 관리가 이번 세션에 구현된 것은 아니다. 이 사실을 두 채팅에서 확인했고 기존 로고 동작은 변경하지 않는다.

## 검증·한계

- Node24.19 사용. 기본 시스템 Node24.3으로 첫 CLI가 지원 버전 오류로 중단되어 프로젝트 지원 버전으로 바꿔 실행했다.
- `ng test --watch=false --browsers=ChromeHeadless --include=...mail-preview...`: 기존 코드에서 새 링크 테스트 2개 실패, 기존 1개 통과.
- `ng test ... --include=...mail-detail-drawer...`: 기존 코드에서 신규 메타 표시 테스트 3개 실패, 기존 4개 통과.
- 수정 후 관련 10개 통과, Admin 전체 **3,089개 통과**.
- 최종 `ng build --configuration prod` 통과, initial799.44KB. 기존500KB 경고는 남고1MB 오류 한도 내.
- 새 최종 CSS는 기존 `--mail-preview-body` 흰색 토큰을 사용하고 브라우저에서 rgb(255,255,255)를 확인. 테스트 전체 실행 후 이 등가 토큰 참조 변경과 마지막 prod/review 빌드·브라우저 확인을 추가했다.
- `scripts/check-raw-colors.mjs`는 다른 기존 리뷰 파일 `features/samples/mail-compose-design/mail-design-preview-review.component.scss:5`의 직접 흰색 1건 때문에 여전히 실패한다. 현재 작업 파일의 기존 직접색은 공통 토큰으로 맞췄다. 관련 없는 리뷰 파일은 수정하지 않았다.
- 실제 앱 셸에서 자동/예약 메타 표시, 일반/가운데 클릭 후 본문 유지, disabled 링크의 href 없음, 흰 배경·기존 sandbox 유지, 링크 있는 원본 input HTML 불변을 확인했다.
- 마지막 diff 공백 검사 통과. 커밋·푸시·개발/운영 배포, 실제 이메일 발송, 실제 DB 변경은 하지 않았다.

## 근거

[검증 결과·범위 JSON](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/mail-preview-detail-261110/result.json), 같은 폴더의 change.patch·review-entry·red/green/full 테스트·prod build 로그와 01~05 스크린샷을 보존했다. 제품 수정은 mail-preview.component.* 및 mail.component.*·상세 테스트에 한정한다. 실제 프레임워크 목업은 src/mail-detail-review-main.ts/index.html 및 tsconfig.mail-detail-review.json이다.


## 추가 사용자 수정 — 상태 배지·툴팁

상세 패널과 페이지 설명의 ‘시각은 한국 시간 기준입니다.’ 및 수신자별 결과의 상시 접수/전달 설명을 제거했다. 시각 계산과 날짜 형식은 기존대로 유지한다. 상태 열은 기존 공통 StatusChipComponent와 MatTooltip으로 표시한다. 공통 컴포넌트 API는 바꾸지 않았다. 배지에 키보드 초점도 닿으며 설명이 aria-describedby로 연결된다.

| 상태 | 공통 tone | 툴팁 |
|---|---|---|
| 대기 중 | neutral | 아직 발송을 시작하지 않은 상태입니다. |
| 발송 중 | info | 메일 발송 요청을 처리하고 있는 상태입니다. |
| 접수 완료 | info | 발송 요청이 접수된 상태입니다. |
| 전달 완료 | ok | 상대 메일 서버에 전달된 상태입니다. |
| 반송됨 | danger | 수신 메일 서버에서 메일이 반송된 상태입니다. |
| 스팸 신고 | danger | 수신자가 메일을 스팸으로 신고한 상태입니다. |
| 발송 실패 | danger | 메일을 발송하지 못한 상태입니다. |
| 확인 필요 | warn | 발송 결과가 불명확해 확인이 필요한 상태입니다. |
| 발송 제외 | neutral | 발송 대상이나 수신 조건에 따라 보내지 않은 상태입니다. |

기존 코드에서 설명 삭제/배지 테스트10개 실패를 확인한 뒤 적용했다. 첫 전체 실행은 배지 테스트6개가 iframe ResizeObserver 알림 경합으로 실패했다. 상태/tooltip 테스트에서만 비대상인 MailPreviewComponent.fit 크기 측정을 spy로 분리하고 재실행했다. 실제 preview와 제품 코드는 이 테스트 분리 때문에 바꾸지 않았고, 실제 목업의 크기/색상/툴팁 검증은 유지한다. 최종 상세16개·Admin 전체3,098개 통과, prod799.44KB build 통과(기존500KB warning). 실제 브라우저에서 기존 문구 제거, 녹색 전달 완료 배지, 키보드 초점 시 툴팁과 aria-describedby를 확인했다. 각 상태 마우스오버 동작은 Material harness9개로 검증했다. 캡처는 06-delivery-status-tooltip.png, 검증 로그/누적 patch/result.json은 위 근거 폴더에 보존했다. 기존 미커밋 작업 위의 수정이며 새 커밋/푸시/배포는 하지 않았다.

### 메일 유형 이름 추가 대안 — 아직 미확정

사용자는 기존 3분류 추천에 대해 더 많은 안을 요청했다. 다음은 선택 전 제안이며 실제 MailType/DB/API는 notice/marketing으로 유지한다.

| 안 | 화면 유형 | 특징 |
|---|---|---|
| 1 | 계정 / 결제 / 문의 / 공지 / 광고 | 짧은5분류. 웰컴과 결제를 목록에서 바로 구분하는 안으로 추천 |
| 2 | 계정 안내 / 결제 안내 / 문의 안내 / 운영 안내 / 광고 안내 | 같은5분류를 안내라는 통일된 이름으로 표현 |
| 3 | 이용 안내 / 결제 안내 / 운영 공지 / 광고·홍보 | 가입·탈퇴·문의는 이용 안내로 묶고 결제만 분리한4분류 |
| 4 | 이용·거래 / 운영 공지 / 광고·홍보 | 정보성 자동 알림을 묶은3분류 |
| 5 | 일반 안내 / 광고 안내 | 기존 광고/비광고2분류 유지. 내용 구분은 이벤트 이름으로 확인 |

1안 기준 계정=웰컴/탈퇴, 결제=구독 결제/갱신/변경/충전/갱신 실패2종/환불 접수, 문의=문의 접수와 향후 답변, 공지=정책/점검/장애/이용 제한 등 수동 운영 공지, 광고=동의 대상 홍보다. 내용 분류와 광고 동의/자동·수동 방식은 구분한다. 이 분류를 선택해도 발송 권한·수신 동의 처리 기준을 이름만으로 변경하지 않는다.

다른 메일 작성 채팅에서 원본 Admin dev에 comparison 리뷰 전용 파일을 추가한 것이 관찰됐다. 해당 파일은 본 작업 소유가 아니며 수정/삭제하지 않는다. ‘원본 clean’은 앞 단계 관찰이고 현재 원본의 추가 untracked 리뷰 파일과 구분한다.


## 확정·적용 — 계정 / 결제 / 문의 / 공지 / 광고

사용자가1안을 확정하고 발송 현황과 상세 패널에 반영하도록 지시했다. 앞의 ‘유형 이름 미확정’은 이 지시 이전 기록이다.

두 화면이 같은 분류 함수를 사용한다. 웰컴/탈퇴=계정, 구독 결제·갱신·플랜 변경·충전·갱신 실패2종·환불 접수=결제, 문의 접수=문의, 기존 직접 발송 notice=공지, marketing=광고로 표시한다. 기존 저장 이벤트 ID로 판단하므로 과거 자동 발송 기록에도 화면에서 즉시 적용되며 제목 문자열을 추측하거나 DB를 일괄 갱신하지 않는다.

광고 동의·수신자·발송 워커의 원래 notice/marketing 기준은 유지한다. 이번은 두 화면의 내용 분류 표시 변경이며 API/DB migration은 없다. 향후 작성 화면에서 계정/문의 등의 수동 분류를 직접 선택·저장하는 기능은 별도 작성 재설계 범위다. 현재 비활성화된 예전 작성 폼의 두 발송 구분을 이번 변경에서 새로 활성화하지 않는다.

기존 코드에서 새 기대값3개 실패 후 수정했고, 관련17개·Admin 전체3,099개와 prod799.44KB build를 통과했다(기존500KB warning 유지). 격리 목업에 문의/공지 예시를 추가해 목록에서 다섯 분류를 모두 확인했으며 크레딧 상세=결제, 웰컴 상세=계정을 브라우저로 확인했다. category-*.log·category-change.patch와 result.json, 07-category-detail.png 및 08-category-list.png에 근거를 보존했다. 모두 관리형 Admin 워크트리의 미커밋·미푸시·미배포 변경이다.


## 확정·적용 — 발송 방식과 자동 발송 이벤트 분리

사용자 지시로 발송 현황의 발송 방식을 자동 발송/직접 발송 두 값으로 통일하고 바로 옆에 자동 발송 이벤트 컬럼을 추가했다. 직접 발송 이벤트는 —로 표시한다. 상세 패널도 같은 함수를 사용하며 예약/즉시 모두 직접 발송으로 표시한다. 실제 예약 일시는 별도 항목에 유지한다. eventName이 없으면 기존 eventId의 이름을 사용하고, 직접 발송이면 잔존 eventName과 무관하게 —로 표시한다. 빈 목록 colspan도10개 열에 맞췄다.

새 열로 좁은 화면에서 줄바꿈이 과해지는 것을 브라우저로 확인하여, 기존 app-table-scroll/app-table-scroll--wide 공통 스타일을 목록에 재사용했다. 별도 글꼴/표 스타일을 만들지 않았으며 가로 스크롤로 나머지 컬럼을 확인할 수 있다. 실제 컴포넌트·격리 목업 모두 반영했다.

기존 코드에서 관련4개 실패 후 수정, 전체3,100개 통과. 최종 공통 표 스타일 적용 후 관련18개와 prod799.44KB build를 추가 확인했다(기존500KB warning 유지). 브라우저에서 자동 발송+크레딧 충전, 직접 발송+—와 상세의 같은 값·별도 예약 일시, 공통 nowrap를 확인했다. 근거: 위 artifact 폴더 dispatch-*.log/dispatch-columns-change.patch/result.json 및 10-dispatch-event-columns.png, 11-direct-dispatch-detail.png. 미커밋·미푸시·미배포, API/DB/실제 발송 일정 변경 없음.


## 사용자 요청 후 관리자 커밋·로컬 dev 병합 완료

사용자가 미커밋 여부와 변경 범위를 확인하고 dev 병합을 지시했다. 위의 미커밋 상태는 이 지시 이전 기록이다. 관리형 Admin 브랜치 fix/mail-activity-detail-panel-261110에서 실제 수정8개와 격리 리뷰 엔트리3개, 총11개 파일만 커밋했다.

- 커밋: `e89a8d197b1c6f7a77beebfab1759df1fa988f2e` — fix(mail): refine preview and delivery activity presentation
- 로컬 dev: `97c1cd9d6064e215cee7f6e8e7f94f929811027c` → `e89a8d197b1c6f7a77beebfab1759df1fa988f2e`, 충돌 없는 fast-forward.
- 검증한 Git tree: `652a821cad3d9d9c46882593a139ec66704e0fd7`. 커밋/병합 결과와 일치.
- 최신 origin/dev fetch 결과는 기존97c1cd9와 동일했다. **원격 푸시는 하지 않았으므로 로컬 dev가 origin/dev보다1개 앞선 상태**다. 서버 배포도 하지 않았다.
- 미리보기 링크 차단, 상세 메타/상태 칩/툴팁, 유형5개, 발송 방식/이벤트 분리, 공통 넓은 표, 회귀 테스트와 리뷰 엔트리가 이번 커밋 범위다. 기존 상세 드로어 전환/고객 메뉴 이동 자체는 부모97c1cd9에 이미 있던 내용이다.
- 병합 직전 전체3,100개 테스트와 prod799.44KB build를 새로 통과했다. 기존500KB bundle warning은 유지. 별도 읽기 전용 코드 검토에서 조치할 사항 없음을 확인했다. stats 입력799개 중 새 리뷰 엔트리·메일 mock/review fixture 입력0개를 확인했다.
- 작업 워크트리는 clean이다. 원본 dev 체크아웃에 있는 별도 메일 작성 세션의 미추적 리뷰 파일15개는 병합 전후 SHA256 일치로 보존을 확인했다. 그 파일이나 .codex 문서는 이번 관리자 커밋에 포함하지 않았다. .codex는 별도 main 문서 repo이며 기존 미커밋 변경을 계속 보존한다.
- API·고객 웹·인프라·실제 env·DB·AWS는 이번 병합에서 변경하지 않았다. 추가 migration도 없다.

[커밋·병합 및 보존 결과](/Users/jina/.codex/visualizations/2026/11/06/01a1af4d-ee8f-78d1-b174-1e9748d4dc74/mail-admin-dev-merge-261110/result.json), 같은 폴더 before-manifest.json/before.patch/admin-tests.log/admin-prod-build.log/prod-bundle-verification.json/review.json에 근거를 보관했다. 사용자 요청 없이 관리형 워크트리·브랜치·실행 중인 검토 서버를 정리하지 않는다.


## 원격 dev 푸시 완료·배포는 사용자 직접 실행

후속 사용자 지시로 관리자 dev `e89a8d197b1c6f7a77beebfab1759df1fa988f2e`를 origin/dev에 정상 푸시하고 git ls-remote로 같은 SHA를 확인했다. 로컬/원격 dev ahead/behind=0/0이다. 이어 사용자가 ‘서버 배포는 직접 원격 접속해서 하며 에이전트는 명령어만 제공’으로 역할을 명확히 했다. 이에 서버 접속·배포는 실행하지 않았다. 앞으로도 별도 지시 없이 원격 서버 배포를 직접 실행하지 않는다.

이번은 관리자 변경만 있어 개발서버의 /Users/metabuzz/Desktop/project/clipper2/clipper_infra에서 ./scripts/deploy-dev.sh admin을 실행하도록 안내했다. 기존 스크립트가 infra/관리자 소스를 ff-only pull하고 관리자 이미지 빌드·web-admin만 재생성한다. 이번 변경의 DB migration이나 env 수정은 없다. 배포 후 clipper-web-admin-dev의 org.opencontainers.image.revision 라벨을 확인하도록 안내하며, 실제 배포 완료 여부는 아직 미확인이다.


## 개발 배포 적용 확인 — 사용자 제공 결과

사용자가 직접 개발서버에서 docker inspect clipper-web-admin-dev의 org.opencontainers.image.revision을 조회해 `e89a8d197b1c6f7a77beebfab1759df1fa988f2e`를 제시했다. 목표 커밋과 일치하므로 개발 관리자 컨테이너의 해당 이미지 적용을 확인했다. 에이전트가 서버에 접속하거나 배포한 것은 아니다. 이 결과만으로 실제 화면·외부 HTTP health를 독립 검증했다고 기록하지 않는다. 운영 배포와 DB/env 변경은 없다.
