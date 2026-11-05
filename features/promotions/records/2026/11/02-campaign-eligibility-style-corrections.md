# 캠페인 참여 조건·가입 코드 입력란 스타일 보정

2026-11-02 KST. 작업 브랜치 `feat/signup-credit-promotion-free-20261102`의 실제 관리자·회원 웹에 반영. 기존 참여 정책과 API는 변경하지 않았다.

## 수정

- 관리자 캠페인 추가: 참여 가능 조건 전체를 감싸던 fieldset 테두리·패딩을 제거했다. 목업과 같이 제목 아래 참여 대상과 추가 조건의 선택 목록을 각각 묶고 설명·구분선·요약 스타일을 적용했다. 기존 공통 drawer와 Material 컨트롤을 재사용한다.
- 라디오: 공통 strong-focus 표시가 마우스 클릭에도 노출되고 persistent ripple이 겹치던 원인을 확인했다. 이 참여 대상 그룹에만 클릭 ripple을 끄고 mouse/touch focus 표시를 억제했다. 키보드 focus 표시는 유지한다.
- 가입 코드 입력란: outlined Material label이 notch border만큼 아래로 치우친 것을 확인했다. 해당 필드의 비부동 label만 1px 위로 보정한다. 입력 시 부동 label의 원래 위치·대문자 변환은 유지한다.

수정 파일: 관리자 `promotions.component.html`, `promotions.component.scss`; 회원 웹 `signup-consent.component.scss`. 기존 미커밋 W19 변경은 유지했고 stage/commit/push/merge는 하지 않았다.

## 검증·로컬 반영

- 관리자 promotions 컴포넌트 49개, 회원 signup-consent 컴포넌트 43개 기존 테스트 통과. 두 웹 build와 git diff --check 통과, 관리자 직접 색상 검사 0건. 기존 bundle budget 경고는 그대로다.
- 실제 4242 브라우저: 외부 테두리는 위 구분선만 있고 양옆·아래 0px, 내부 fieldset border 0px. 선택 목록 두 곳만 자체 border가 있다. 마우스 radio focus pseudo display=none / ripple transparent, 키보드 focus pseudo display=block 확인.
- 실제 4241 브라우저: 빈 label의 입력창 중심 오차 약 -0.074px(보정 전 약 +1.10px). 입력 후 floating label과 대문자 TEST123 확인, 지우고 blur 후 원위치 확인.
- 동의 화면은 로컬 가상 신원의 signed signup ticket으로 표시만 했다. 동의·가입 제출, 실제 계정 생성, 캠페인 저장, DB 초기화는 하지 않았다. 임시 가입 확인 탭은 종료했다.
- 4241/4242는 새 build를 기존 runtime 정적 서버로 복사하여 갱신했다. 서버 재시작이나 다른 작업 서버·앱 변경 없음.
- 로그: `/tmp/promotion-admin-style-tests.log`, `/tmp/promotion-client-style-tests.log`, `/tmp/promotion-admin-style-build.log`, `/tmp/promotion-client-style-build.log`.

[관리자 화면](02-campaign-eligibility-style-fixed.jpg) · [가입 입력란](02-signup-promotion-label-fixed.jpg).

## 후속: 필수 표시·기본 대상·간소화·가입 버튼

- 사용자 지시에 따라 입력란 공통 디자인 변경은 진행하지 않았다. 가입 코드 안내 문구의 좌우 기본 padding만 16px에서 0으로 제거했다.
- 가입 화면 취소 버튼은 위 가입 버튼과 같은 width:100%. 실제 브라우저에서 양쪽 모두 약404.03px, 좌우 경계 차이0px 확인.
- 캠페인 추가의 참여 대상에 *와 required를 표시하고 기본값을 new(회원가입하는 신규 회원만)로 변경했다. 수정 시에는 저장된 대상 값을 그대로 불러온다.
- 추가 조건 제목 옆 ‘선택 · 복수 선택 가능’을 제거했다. 안내는 ‘조건을 선택하지 않으면 추가 제한이 없습니다. 선택한 조건은 모두 충족해야 합니다.’로 변경했다.
- ‘참여할 수 있는 회원’ 요약 블록 및 해당 블록에만 쓰던 스타일을 제거했다. 캠페인 상세의 참여 조건 설명은 유지한다.
- 관리자 컴포넌트49개 테스트 및 두 웹 build·diff --check 통과. 기본 대상·required·추가 조건 visible/disabled·요약 미표시를 실제4242에서 확인했다. 4241/4242는 기존 서버를 유지하면서 번들만 갱신했다. 새 캠페인이나 회원 데이터 생성 없이 확인 탭을 정리했다.
- 로컬 확인 첫 로딩에 일시적인 Angular NG0908이 한 번 기록됐고 재로드 후 정상 부팅·확인됐다. 이번 UI 변경과 직접 연관된 오류는 재현되지 않아 제품 초기화 코드는 변경하지 않았다.

[참여 대상 기본값 화면](02-campaign-create-default-new-member.png) · [가입 버튼 너비 화면](02-signup-cancel-full-width.png).
