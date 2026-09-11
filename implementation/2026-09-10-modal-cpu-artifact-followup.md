# 모달 드래그·Windows CPU·설치 파일 정렬 후속 — 2026-09-10

**최신 배포 상태:** [모달·CPU·브랜딩 배포](./2026-09-10-modal-cpu-branding-deployment.md). Admin87c4424/Customer9fff91a/Electrona34a39d/Angularc8b18677 커밋·push·원격 SHA 확인 완료. 사용자 m4-prod 출력으로 Admin/Customer 운영 교체·HTTP200/running/restarts0/예상 SHA 일치 확인, 웹 배포 완료. 실제 화면 및 새 앱 빌드·실기 확인 대기. 아래 미커밋·미푸시 표기는 과거 구현 시점 기록이다.

**최신 후속 우선:** [관리자 모달 전체 추상화](./2026-09-10-admin-modal-component-refactor.md). 아래 directive-only 공통화는 사용자 요구 범위를 충족하지 못한 중간 기록이다. 이후 Admin13개 모달/상세창을 실제 ModalComponent로 전환했고, Admin422 테스트/prod빌드/로컬 브라우저 검증 완료. Admin directive는 `components/modal` 내부 구현으로 이동. Customer 및 앱/정렬 수정은 보존, 미커밋·미배포 유지.

현재 상태: 격리 checkout에서 수정·회귀 테스트·빌드 완료. 미커밋·미푸시·미배포. 이전 [운영판 Clipper 이름 수정](./2026-09-10-desktop-production-branding-followup.md)의 미커밋 변경도 함께 보존되어 있다. 원본 공유 변경 및 Build 5 전체 QA·플러그인 실행 검증 보류 유지.

후속 SOLID 검토 완료: directive의 출력은 readonly, 내부 이벤트 메서드는 protected로 축소. 개별 dialog 본문의 중복 stopPropagation 12곳(Admin11/Customer1)을 제거하여 내부 클릭 판별도 공통 코드만 담당하도록 정리. 최종 Admin416/Customer280 전체 테스트 및 양쪽 prod 빌드 통과. 아래 최초 413/278 수치는 이 보완 전 검증 기록이다.

## 1. 웹 모달 드래그와 공통화

- 원인: 개별 모달을 감싼 backdrop의 `(click)`에서 닫았다. 내부에서 누른 뒤 밖에서 놓으면 브라우저가 공통 조상인 backdrop에 click을 보낼 수 있어 내부 click의 stopPropagation만으로 막지 못했다.
- Admin과 Customer 각각 `src/app/shared/ui/backdrop-dismiss.directive.ts`를 추가. 배경 자체에서 주 버튼을 누르고 배경 자체에서 놓은 완전한 클릭만 닫기 이벤트를 보낸다. 내부→외부, 외부→내부, 오른쪽 클릭, pointercancel, 창 blur를 구분한다. 닫기/취소 버튼과 제출 중 닫힘 제한은 기존 계약 유지.
- Admin 13개 모달/상세창의 backdrop·scrim에 연결: 상품, 회원 수동 처리, 크레딧 정책, 작업 복구, 결제 지급 복구, 두 에러 drawer, 환불 확인, 환불 상세 동작 확인, API 키 확인/테스트, 릴리즈 상세, 설치 파일 정식 배포 확인. API 키 테스트에만 있던 개별 mousedown/up 처리는 제거.
- Customer의 별도 다운로드 안내 모달에도 연결. 결제/계정 확인은 기존 공통 ConfirmDialogComponent 및 Angular Material MatDialog, 요금제 선택도 MatDialog를 사용한다. Material의 형제 backdrop 구조는 실제 드래그에서 닫히지 않음을 확인.
- 화면별 내용과 스타일은 각각 유지하지만 직접 만든 모달의 배경 닫힘 동작은 각 웹의 한 directive로 통합. Admin/Customer는 독립 저장소이며 공유 배포 패키지는 없어 두 저장소 사이에는 같은 소스가 각각 한 파일씩 있다. 하나의 전역 패키지로 통합했다고 표현하지 않는다.

## 2. Windows CPU 사용률

- 설치 앱의 데이터 경로: Electron `host-resource-monitor.ts` → plugin-host bridge → Nest ElectronResourceHost/ResourcesService JSON 전달 → Angular ResourceStatusService/대시보드. Nest는 이 응답을 필드별로 잘라내지 않고 전달하므로 이번 계약 추가에 Nest 수정은 필요 없다.
- 원인: 기존 Electron 수집기가 모든 OS에 `os.loadavg()`를 사용. [Node 공식 문서](https://nodejs.org/api/os.html#osloadavg)에 명시된 대로 Windows는 항상 `[0, 0, 0]`을 반환한다. 해당 CPU의 고장이나 P/E 코어 클럭 문제가 아니다.
- Windows에서 연속 `os.cpus().times` 표본의 전체/idle 증가량으로 전체 논리 프로세서의 사용률을 계산하고 `cpu.utilizationPercent`로 전달. 첫 표본·코어 수 변경·카운터 초기화/잘못된 값은 측정 중, 실제 유휴 상태는 0%로 구분한다. 기존 polling을 사용하며 CPU용 PowerShell 호출이나 새 타이머는 추가하지 않는다.
- Windows 표시 예: `CPU 사용률`, `10.4% / 20 논리 프로세서`. 10.4는 회귀 테스트 예시이며 사용자 PC의 현재값을 측정한 결과가 아니다. 20은 물리 코어 12개가 아닌 논리 프로세서/스레드 수다.
- macOS는 기존 Unix 지표를 유지하며 `CPU 부하 · 1분 평균`으로 의미를 명확히 한다. 동일한 숫자 단위인 것처럼 Windows 사용률과 혼동하지 않는다.
- 이번 대상은 Electron이 실행되는 설치 앱 경로다. Electron 없이 Nest만 단독 실행하는 fallback의 별도 자원 수집기를 Windows 사용률로 바꾸었다고 확대하지 않는다. Windows 실기 값 확인은 새 앱 빌드 후 필요.

## 3. 설치 파일 표 정렬

- 원인: API artifact 응답을 행으로 변환할 뿐 명시적 정렬이 없었다.
- 공통 `buildArtifactRows` selector에서 Build 번호를 숫자 내림차순으로 정렬. 예: 3, 4, 6, 5 → 6, 5, 4, 3. 10과 6도 숫자 기준으로 비교한다.
- 같은 Build는 플랫폼/아키텍처/파일명/ID 순으로 안정화하고 Build 연결이 없는 행은 뒤로 보낸다. 입력 배열은 변경하지 않는다. 정식 배포 버전 표시는 해당 artifact에 유지하며 정식 지정 여부로 순서를 왜곡하지 않는다.

## 검증

- 수정 전: 실제 Admin/Customer 컴포넌트의 내부→외부 드래그, Build 혼합 순서, Windows 0 고정/첫 측정 미지원 표시 테스트 실패 확인.
- 공통 directive를 각 모달에 연결하는 최종 검토에서 API 키 삭제 확인의 imports 누락을 발견. 실제 삭제 확인 모달의 일반 배경 클릭 회귀 테스트 실패를 확인한 뒤 연결 수정. 삭제 요청 없이 닫힘만 검증.
- 최종 Admin 전체 **413개 통과**, Customer 전체 **278개 통과**. 두 저장소의 모든 backdropDismiss 사용처가 standalone imports에 포함됨을 확인(Admin 13, Customer 1).
- Electron CPU 4개 테스트 통과(20 논리 프로세서 10.4%, 첫 표본/실제 0%, 코어 수·카운터 초기화, macOS 유지). 창 제목/운영 식별자/설치 분리와 함께 10개 통과, 시스템 snapshot/IPC 경계와 함께 10개 통과. 두 실행은 CPU 4개가 겹치므로 20개 고유 테스트로 합산하지 않는다.
- Angular 대시보드 및 이전 로그인 변경 관련 **36개 통과**. Windows 값/측정 중과 macOS 표시를 실제 컴포넌트에 렌더하여 확인.
- Admin/Customer prod 빌드, Electron TypeScript 빌드, Angular packaged 빌드 통과. Admin에는 기존 initial bundle 예산 경고(567.32kB / 500kB)가 남는다. 최종 Admin 빌드 첫 시도는 제한 환경에서 종료134로 중단되어 로컬 권한으로 재실행했고 성공. 전체 Electron suite의 기존 sibling 산출물 부재 문제를 이번에 해결했다고 기록하지 않는다.
- CUA 실제 브라우저 드래그 확인: Admin 상품 수정 input→바깥, Customer 실제 ConfirmDialogComponent 본문→바깥, Customer 실제 다운로드 안내 본문→바깥에서 모두 열림 유지. 이후 정상 배경 클릭은 닫힘. 로컬 소스 복사본과 mock/fixture를 사용했으며 운영 로그인·결제·키 호출/변경은 하지 않았다. 검증 탭/서버 종료 완료.
- 설치 파일 정렬은 selector 및 실제 설치 파일 컴포넌트 회귀 테스트로 검증. 운영 artifact 목록을 읽어 새 순서를 확인하거나 실제 정식 배포를 수행한 것은 아니다.
- 네 checkout `git diff --check` 통과. 원본 API tracked8/untracked1, Admin tracked7, Customer tracked10, Infra tracked2/untracked3 보존. 원본 Electron/Angular/Nest clean 유지. `.env`, API 코드, 운영 DB 변경 없음.

## 작업 위치·다음 단계

- Admin: `/private/var/folders/1m/rqyx3mvn1tgc9z5hjr31q2380000gn/T/clipper-integrate-88un0ptn/clipper_web_admin`, 기준 `59b7903b3810afd3f7cc2dd35266617e25511ec1`.
- Customer: 같은 임시 통합 경로의 `clipper_web_client`, 기준 `05121731b603a1251e4b61b7cdef14a94031d43a`.
- Electron: `/private/tmp/clipper-isolation-fix-electron`, 기준 `2d492fee3284263a2207a8a76d11aa035d01d9b0`.
- Angular: `/private/tmp/clipper-branding-angular`, 기준 `7ae7366d51a997ee009f73a825467db061daca2b`.
- 웹 적용 시 Admin/Customer 커밋·푸시·재배포 필요. API/DB migration 불필요. 앱 적용 시 이전 Clipper 브랜딩과 이번 Electron/Angular CPU 변경을 새 릴리즈 소스에 포함하고 새 Windows 설치 파일 빌드 필요. 현재 게시 파일을 덮어쓰지 않는다.
- 새 Windows 설치 후 CPU 사용률 변화·측정 중 표시·논리 프로세서 수, 이름/파일명 및 개발판 공존 확인이 남음. 기존 Build 5 전체 QA·플러그인 실행 HOLD, 남은 TEST PG 환불 검증은 별도 유지.

## 후속 추상화·SOLID 검토

- 추상화 단위는 배경 클릭을 닫기 요청으로 변환하는 동작. Angular attribute directive를 기존 모달 요소에 합성한다. 소비 예: `(backdropDismiss)="closeEditor()"`; `imports`에 BackdropDismissDirective를 포함한다.
- SRP: directive는 제스처 판별과 요청 발행만 담당. 실제 열림 상태, 취소, 저장 중 닫힘 제한, 폼/API는 각 화면의 책임. 환불의 `!confirmation.submitting && cancel.emit()`은 화면 정책으로 유지한다.
- OCP: 새 모달은 같은 directive와 output을 연결하며 모달 종류별 분기를 공통 코드에 추가하지 않는다. 레이아웃·업무 흐름이 달라도 재사용 가능하다.
- LSP: 현재 상속 관계/대체 구현이 없어 직접적인 평가 대상이 아니다. 공통 부모 클래스 도입을 LSP 충족 조건으로 오해하지 않는다.
- ISP/캡슐화: 소비용 계약은 void 출력 하나. onMouseDown/onMouseUp/onClick/reset은 protected, 출력은 readonly로 변경하여 내부 처리와 공개 API의 경계를 명확히 했다. readonly는 emitter 교체 방지이며 런타임 보안 경계라는 뜻은 아니다. [Angular style guide](https://angular.dev/style-guide)의 protected/readonly 안내와 일치.
- DIP: 공통 directive가 부모 컴포넌트/업무 서비스를 주입하거나 닫기 메서드를 직접 호출하지 않고 이벤트로 연결한다. 다만 소비 컴포넌트는 Angular directive 구현을 imports에 연결하므로 명시적 교체용 추상 인터페이스를 둔 전면 DIP 구조라고 주장하지 않는다. 현재 하나의 UI 구현에 별도 추상 서비스/팩토리를 더할 필요는 없다.
- Admin/Customer 사이에 한 파일씩 중복되는 것은 SOLID와 별개인 DRY/패키지 배포 경계 문제다. 현 프로젝트의 독립 코드/빌드/배포 구조를 유지하여 공유 패키지는 추가하지 않았다. 한 번 수정으로 양쪽 저장소까지 자동 반영되는 상태가 아니라는 한계는 명시한다.
- 기존 drag 회귀 테스트의 green 이후 동작 보존 refactor로 진행. 추가 계약 테스트를 먼저 실행해 Admin13/Customer9 통과 확인 후 정리했다. 내부 일반 클릭에 별도 stopPropagation이 불필요한지, 두 모달 인스턴스의 제스처 상태가 분리되는지, 환불 처리 중 닫힘 정책을 소비 화면에서 유지하는지 검증한다.
- 최종 Admin416/Customer280 전체 테스트와 두 prod 빌드 통과. 기존 Admin bundle 경고 유지. 로컬 mock 실제 상품 input 클릭·내부→외부 드래그 열림 유지·정상 배경 클릭 닫힘을 재확인하고 탭/서버 종료. 오류 표 셀/파일 링크에 필요한 별도 stopPropagation은 유지했다. CPU/정렬/브랜딩 코드와 원본 공유 변경은 이번 보완에서 수정하지 않았다.
