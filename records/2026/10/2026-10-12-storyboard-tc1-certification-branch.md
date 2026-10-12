# TIPS TC1 스토리보드 시험인증용 구현 보관

2026-10-12 기준, 프로필 표현 점검 기능은 TIPS 시험인증의 TC1 판정과 화면 증빙을 위해 한시적으로 구현한 것이다. **Clipper 서비스의 스토리보드 플러그인에 정식 반영하기로 결정한 기능이 아니다.** 추후 쓸 가능성이 있어 코드를 삭제하지 않고 별도 브랜치에 커밋해 원격에 보관했다. 브랜치 보관을 `dev` 병합이나 운영 배포 결정으로 해석하지 않는다.

## 보관 위치와 범위

- 코드 저장소: `desktop/clipper_angular` ([원격 브랜치](https://github.com/OhMyMetabuzz/clipper_angular/tree/feat/storyboard-profile-requirement-check))
- 브랜치: `feat/storyboard-profile-requirement-check`
- 보관 커밋: [`e371756ead29935fed2d3b1951770f29ab8f3ad6`](https://github.com/OhMyMetabuzz/clipper_angular/commit/e371756ead29935fed2d3b1951770f29ab8f3ad6). 원격 브랜치의 해당 커밋을 확인했다.
- 구현 내용: 프로필의 필수 포함 표현·금지 키워드 입력과 카드 표시, 생성 결과의 표현 반영률·금지 표현 건수 표시, 상세 모달과 대본 내 일치 표현 강조. 기존 생성 결과를 수정하거나 점수가 100%가 되도록 강제하지 않는다.

## TC1에 사용한 기준과 증거

시험 대상 프로필은 **주말 여행 짐 싸기**, **퇴근 후 책상 정리**, **스마트폰으로 음식 사진** 3개다. 각 프로필에서 주제 1개와 시나리오 2개를 사용해 스토리보드 6개를 확인한다. 각 결과의 대본에 설정된 고유 필수 포함 표현이 80% 이상 나타나고, 대본과 화면 문구에 금지 표현이 0건이면 이 항목을 충족한 것으로 판정한다. 2026-10-08에 저장한 6개 결과의 100% 반영률·금지 표현 0건은 실제 관측값이지 고정 점수가 아니다. 이 검사는 **표현 포함 여부**를 수치화하며 스토리의 완성도·창의성·프로필과의 의미상 연관성을 보증하지 않는다.

구현 계획과 시험 대상 선정은 Angular 저장소의 [`docs/superpowers/plans/2026-10-08-storyboard-requirement-check.md`](https://github.com/OhMyMetabuzz/clipper_angular/blob/feat/storyboard-profile-requirement-check/docs/superpowers/plans/2026-10-08-storyboard-requirement-check.md)에 있다. 실제 화면 캡처와 생성 원문은 로컬 `/Users/jina/project/adlight/workspaces/tips-storyboard-20261008/evidence/ui-update/`에 있으며 Angular 원격 저장소에는 포함되지 않았다.

향후 이 기능을 제품에 쓰기로 한다면 시험인증용 기준을 그대로 제품 요구사항으로 간주하지 않고, 사용자 경험과 품질 기준을 별도로 검토한 뒤 통합 여부를 결정한다.
