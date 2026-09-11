# 관리자 모달 전체 추상화 — 2026-09-10

최신 배포 후속: [모달·CPU·브랜딩 배포 기록](./2026-09-10-modal-cpu-branding-deployment.md). 사용자 배포 요청으로 Admin `87c4424` 등 네 저장소 커밋·일반 push·원격 SHA 대조 완료. 사용자 m4-prod 출력으로 Admin/Customer 운영 교체·HTTP200/running/restarts0/예상 SHA 일치 확인, 웹 배포 완료. 실제 모달 화면 확인과 새 앱 빌드 확인은 대기 중이며, 아래 미커밋 표기는 구현 당시 기록이다.

사용자 정정: 닫힘 동작만이 아니라 관리자 모달 자체를 재사용 부품으로 구성해야 한다. 새 `@shared` 패키지를 만드는 요청은 아니다. 기존 격리 Admin 작업본에서 수정했다.

## 구현

- `src/app/components/modal/modal.component.{ts,html,scss,spec.ts}`: 공통 배경, 제목/보조 설명, 닫기 버튼, 스크롤 본문, 작업 버튼 footer, 크기 4종, 중앙/오른쪽 상세 배치. 같은 디렉터리 README에 사용 계약과 예시 기록.
- 화면은 ModalComponent와 ModalActionsDirective를 상대 경로 import하고 `<app-modal>` 안에 본문, `<ng-template appModalActions>`에 작업 버튼을 제공한다. 상속 대신 Angular content projection/template 조합. 폼 바인딩·유효성 검사·API·저장/환불 실행은 화면 책임이다.
- BackdropDismissDirective와 테스트는 Admin `shared/ui`에서 `components/modal`로 이동하여 내부 구현으로 제한. 화면에서는 backdropDismiss를 직접 연결하지 않는다.
- CDK CdkTrapFocus를 사용해 초기 포커스/Tab 순환/원래 요소 복원을 공통 처리. 환불 안전 버튼은 cdkFocusInitial로 지정. dismissDisabled는 배경·Escape·상단 닫기를 함께 차단하며 화면의 취소 버튼에도 동일 busy 상태 적용.
- ModalStackService는 표시 순서와 페이지 body 스크롤 잠금의 수명만 소유한다. Escape는 맨 위 모달만 처리하고 마지막 모달이 닫힌 뒤 기존 overflow 복원.
- 13곳 전환: 상품, 회원 수동 처리, 크레딧 정책, 작업 복구, 결제 지급 복구, 환불 최종 확인, 환불 상세 동작 확인, API 키 확인/테스트, 릴리즈 상세, 정식 지정 확인, 웹/설치형 오류 상세 drawer.
- 위 화면의 반복 배경/panel/header/close/footer 스타일과 자체 Escape 코드를 제거. 릴리즈 내용도 공통 body가 스크롤을 담당. 환불 일반 취소 포커스 복원 중복 제거. 서버 재조회 뒤 원래 작업 버튼이 사라질 수 있는 환불 상세의 대체 포커스 선택은 업무 화면에 유지한다.
- 공통 모달은 결제/회원/릴리즈 모델이나 서비스를 import하지 않는다. SRP는 shell/표시 순서/업무 내용으로 구분하고 새 내용은 projection으로 확장한다. 필요 없는 추상 부모 클래스/팩토리/공유 배포 패키지를 추가하지 않았다.

## 검증

- RED: 기존 크레딧 정책 편집창 Escape 취소 테스트 실패(창이 남음), 기존 조회/저장 2개 통과.
- 최종 Admin 전체 **422개 통과**. 새 공통 모달 5개 테스트: 접근성 제목 및 본문/하단 조합, 양방향 드래그, busy 모든 닫힘 차단, 포커스/스크롤 복원, 중첩 모달 Escape/잠금. 크레딧 정책 실제 화면 회귀 1개 추가. 이전 directive 및 업무 테스트 유지; 제거된 화면별 CSS/DOM 선택자는 공통 구조로 갱신.
- 최종 prod 빌드 성공. initial 574.74kB로 500kB 경고 유지(직전 567.32kB); error budget 이내. 기존 경고를 해결했다고 기록하지 않는다.
- CUA 로컬 mock Admin: 상품 Basic 편집에서 이름 input→바깥 드래그 후 열림 유지, Escape 닫기/원래 수정 버튼 포커스 복원, Shift+Tab 마지막 저장 버튼 순환, 정상 배경 클릭 닫기. 오류 상세는 오른쪽 전체 높이 표시·본문 드래그 유지·Escape 닫기 확인. 운영 API/결제/키 변경 없이 실제 소스 복사본으로 검사.
- 최종 로그: `/private/tmp/clipper-modal-component-final-test.log`, `/private/tmp/clipper-modal-component-prod-build.log`; 최초 RED `/private/tmp/clipper-modal-component-red.log`. `git diff --check` 통과.
- 원본 7개 repo 상태 재확인: API06316a4 tracked8/untracked1, Admincafebe3 tracked7, Customerae75f51 tracked10, Infraf948922 tracked2/untracked3. Electrondd4e9d6/Angular7ae7366d/Nest780128a clean. 원본 공유 변경 보존.

## 작업 위치와 남은 적용

- Admin: `/private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn/clipper_web_admin`, 기준 59b7903b3810afd3f7cc2dd35266617e25511ec1.
- 이번 후속은 Admin 모달 전체 전환이다. Customer 이전 드래그 수정, Electron/Angular CPU·Clipper 브랜딩, Admin 설치 파일 정렬 변경은 보존했다. 앱/Customer 전체 공용 UI 패키지 전환을 완료했다고 확대하지 않는다.
- 적용에는 Admin 변경 커밋·push·배포와 운영 화면 확인이 남는다. 현재 요청은 리팩토링이며 이번 턴에서 배포하지 않았다. 이전 미배포 웹/앱 변경과 묶는 범위는 기존 후속문서 참고.
- Build 5 전체 QA·플러그인 실행 검증 HOLD, Windows 새 빌드 실기 확인 및 남은 TEST 환불 검증 유지.
