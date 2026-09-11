# 모달·설치 파일 정렬·CPU·Clipper 브랜딩 배포 — 2026-09-10

**후속 실기 증거:** 사용자 현재 Windows 설치 버전은 **0.0.3.7**이며 CPU 사용률21.3%/25.5% 및 논리 프로세서20 표시 확인. 아래 단순 `새 앱 빌드 대기`는 그 보고 이전 상태다. Build7 소스 snapshot/artifact SHA·서명·브랜딩 전체 실기는 별도 대조 필요. 새 CPU 카드 코어·스레드 표시 수정은 [현재 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md) 5절에서 별도 추적한다.

현재 상태: 사용자 `배포해줘` 요청에 따라 아래 네 저장소의 검증, 커밋, 기존 배포 브랜치 일반 push 및 원격 전체 SHA 대조 완료. **사용자가 제공한 m4-prod 실행 결과로 Admin·Customer 이미지 빌드·운영 컨테이너 교체·각 HTTP200/running/restarts0/예상 SHA 일치와 WEB_DEPLOY_OK를 확인하여 웹 배포 완료**. 이어서 사용자 `확인했어`로 안내한 Admin 상품 모달 동작·설치 파일 정렬 운영 화면 확인 완료. Customer 다운로드 안내 모달 및 새 앱 설치 파일 빌드·실기 확인은 아직 남았다. 이전 후속문서의 미커밋·미푸시·웹 배포 대기 표기는 이 기록으로 대체한다.

## 확정 커밋

| 저장소 | 대상 브랜치 | 이전 커밋 → 새 커밋 |
| --- | --- | --- |
| clipper_web_admin | release/pg-expiry-20260910 | 59b7903b3810afd3f7cc2dd35266617e25511ec1 → 87c4424d050d3a6f2acf50c8692c2d2ef2a464cf |
| clipper_web_client | integration/toss-payments-pg-20260903 | 05121731b603a1251e4b61b7cdef14a94031d43a → 9fff91a475c5ef61fd8a6ee121d090fb3aca07b6 |
| clipper_electron | integration/toss-payments-pg-20260909 | 2d492fee3284263a2207a8a76d11aa035d01d9b0 → a34a39d510bca51bf8b3e527d433ff9112c686fc |
| clipper_angular | integration/toss-payments-pg-20260909 | 7ae7366d51a997ee009f73a825467db061daca2b → c8b186770ae6f77294a2a1689226834f05a8944a |

- Admin: 내부 ModalComponent로 13개 모달/상세창 통합, 배경 드래그·Escape·포커스·스크롤 공통 처리, 설치 파일 Build 숫자 내림차순.
- Customer: 다운로드 모달의 내부→외부 텍스트 드래그 후 닫힘 방지.
- Electron/Angular: Windows CPU 시간차 사용률과 논리 프로세서 수 표시, 실행 앱 이름을 창·로그인 등에 반영, 운영 설치 파일 Clipper 이름.
- 각 OhMyMetabuzz GitHub 저장소의 위 브랜치에 일반 fast-forward push. 격리 checkout의 origin은 원본 로컬 repo이므로 push 대상에 정확한 GitHub URL을 직접 지정했다. 원본 브랜치/HEAD 및 변경파일 diff SHA256 보존 확인. node_modules symlink는 커밋 제외.

## 이번 배포 직전 검증

- Admin 전체 422개, Customer 전체 280개, 앱 Angular 관련 83개, Electron 관련 94개 테스트 통과. 각 prod/packaged/TypeScript 빌드 통과.
- Admin initial bundle 574.74kB로 500kB warning 유지, hard error budget 이내. Electron 전체 suite 성공이나 Windows 실기 완료로 확대하지 않는다.
- 초기 웹 test CLI에 지원되지 않는 `--port` 옵션을 지정해 실행 전 종료했다. 옵션을 제거하고 Karma 테스트 단계를 직렬 실행하여 위 최종 결과를 얻었다. 테스트 실패를 무시하거나 skip한 것이 아니다.
- 최종 검증 JSON `/private/tmp/clipper-ui-deploy-verification.json`, 로그 `/private/tmp/clipper-ui-deploy-{admin,client,electron,angular}-{test,build}.log`.
- 커밋 manifest `/private/tmp/clipper-ui-deploy-commits.json`, 원격 확인 `/private/tmp/clipper-ui-deploy-remote-verification.json`, 원본 비교 기준 `/private/tmp/clipper-ui-deploy-original-state.json`.

## 운영 적용과 남은 확인

- m4-prod `/Users/m4-prod/Documents/projects/clipperstudio/clipper_infra`에서 Admin/Customer만 build-only → 두 이미지 SHA 확인 → Admin start-only/health/revision → Customer start-only/health/revision 순서. 검토한 명령 파일은 작업 Mac의 `/private/tmp/clipper-ui-prod-deploy.sh`이며 같은 내용을 사용자에게 제공했다. m4-prod 파일 존재를 가정하지 않는다.
- API 및 DB migration 대상 없음. 배포 script는 기존 infrastructure/선택 repo의 fast-forward pull과 이미지 빌드를 수행한다. branch 확인 실패나 이미지 SHA 불일치 때 중단한다.
- 사용자 m4-prod 출력 확인: Admin `87c4424d050d3a6f2acf50c8692c2d2ef2a464cf`, Customer `9fff91a475c5ef61fd8a6ee121d090fb3aca07b6` 이미지 빌드 후 각각 start-only 완료. 두 컨테이너 모두 `running 0 <예상 SHA>`, 각 HTTP200, 마지막 `WEB_DEPLOY_OK`. 운영 DB migration 미실행 출력도 확인. 이 증거는 사용자가 제공한 서버 실행 결과이며 직접 서버에 접속해 재조회한 것으로 기록하지 않는다.
- 실제 화면: 사용자 `확인했어`로 직전 안내 두 항목(Admin 상품 수정 모달의 내부→외부 텍스트 드래그 열림 유지·배경 클릭/Escape 닫기, 설치 파일 Build 숫자 내림차순) 확인 완료. 13개 모든 업무 동작 또는 Customer 다운로드 안내 모달 실기 확인까지 확대하지 않는다.
- 앱 수정은 새로운 릴리즈 소스 스냅샷에 Electron/Angular 두 SHA를 함께 포함하여 새 설치 파일을 빌드해야 반영된다. 기존 게시 0.0.2 파일을 덮어쓰거나 새 버전·정식 지정 작업을 대신 실행하지 않았다. 새 버전 번호는 이번 요청에서 지정되지 않았다.
- 사용자 후속 질문 `빌드만 다시 하면 되게 이미 배포 끝난거야?`에 대한 코드 재확인: 서버/runner 추가 배포는 이번 앱 수정에 필요 없음. 수정 소스는 위 integration 브랜치에 push 완료. 다만 API releases.service는 이미 고정된 스냅샷의 변경을 거부하고 빌드 시 해당 sourceRevisions를 사용하므로 기존 0.0.2 재빌드는 수정 전 소스를 사용한다. 새 릴리즈를 `integration/toss-payments-pg-20260909`에서 준비 → 소스 스냅샷 고정(전자/화면 두 새 SHA 확인) → 새 빌드 → 정식 지정/다운로드·설치 순서가 필요하다. runner captureSourceSnapshot의 fetch origin/브랜치 SHA 수집 흐름 확인.
- 새 Windows 빌드에서 CPU 사용률 변화·논리 프로세서 20 표시, Clipper 창/로그인/설치 파일명과 개발판 공존 확인 필요.
- **Build 5 전체 QA·플러그인 실행 검증 HOLD 유지**. 남은 TEST PG 환불 검증은 별도 유지.
