# 고정 스레드 1~5·7~9 / 원격 dev 전수 대조 (2026-10-16 KST)

## 범위와 확인 방법

사용자가 지정한 고정 스레드 8개를 끝까지 읽었다. 6번 `배포, 빌드, 브랜치 전략`은 요청대로 제외했다. 대화의 당시 표현을 현재 상태로 그대로 옮기지 않고, 10/16에 desktop 4개·web 4개 저장소에서 `git fetch origin dev`를 실행한 후 `origin/dev` 조상 관계, local/remote branch의 순수 커밋, patch 동등성, 작업 트리의 미커밋 파일을 대조했다. **원격 Git 반영과 개발서버 배포, 사용자 설치 앱 실행은 서로 다른 사실**이다. 서버·빌드 결과는 대화와 실행 기록의 관찰 범위로만 적는다. 조사 과정에서 앱 소스·브랜치·서버/DB를 수정하지 않았다.

| 번호 | 스레드 | 이 주간의 실제 범위 | 현재 판정 |
|---|---|---|---|
| 1 | Clipper 내부 QA 결제 버그 수정 | BUG-02-005 외 내부 QA 이슈 전수 분류, ISS-028·056 등 수정 | 일부 dev 반영. 원 제보 재현/해결 판정이 남은 항목 다수. [W16 카드](tasks/payment-qa-bugs.md) |
| 2 | 안무 하이라이트 | W13 pose·메인/군무·구간 노트북 1~72, 별도 공유 클립 앱 | 노트북 72 미채택, 공유 클립 수동 귀속은 dev 반영. [실험 회고](../features/highlights/records/2026/10/16-w13-w14-experiment-reconciliation.md) |
| 3 | 인물 하이라이트 | Person MVP 후 안무용 W14 공통 얼굴 매칭·모델/참조/시간 근거 실험 | Person 고도화 보류, YuNet/SFace 기본 유지, core와 Dance adapter는 dev 반영. [W14 카드](tasks/person-highlight.md) |
| 4 | 안무 하이라이트 사용성 개선 | 아티스트 검색·카탈로그·직접 입력·사진·관리자 외부 데이터, 후반 통합/진단 | 대부분 dev 반영. LOVE DIVE 별칭 오탐·실제 게시/영상 품질 확인은 남음 |
| 5 | 안무 하이라이트 사용성 개선 (2) | 4번의 기록을 이어받아 원본 URL 복사·사진 버튼 등 후속 | 고유 후속도 dev 반영. 앞 74턴은 4번과 같은 기록이라 이중 집계하지 않음 |
| 7 | 클리퍼 작업 현황 정리 | W13/W14·W16/W17 출발점, 통합 병합·서버 상태 추적 | 처음 보드 누락/오래된 정답을 고쳤으나 이후 변경이 다시 생겨 이번 대조로 갱신 |
| 8 | 안무·인물 얼굴 매칭 통합 빌드 준비 | W13/W14 시험 checkout, 공유/진단 기능 dev 병합, 빌드·품질 실험 | 병합된 코드와 미커밋 시험 코드가 섞여 있음. **미커밋 변경을 dev 기능으로 부르지 않음** |
| 9 | 개발서버 TossPayments 새 MID 테스트키 동기화 | W06 코드 병합, 개발 DB 세 개 초기화, 키 교체/배포/시험 거래 | dev 코드 및 서버 검증 기록 있음. 일부 웹훅·메일·계좌이체와 m2-db Git 인증은 남음 |

## 새로 fetch한 원격 dev 기준

| 저장소 | `origin/dev` | 기본 checkout `dev`와의 차이 | 관련 확인 |
|---|---:|---:|---|
| desktop/clipper_angular | `4709d250` | 3커밋 뒤 | 결과 URL 복사 `abaceeb5`, 배지 `0587ed46`, 판정지도 `d532b4e0`, 공유 UI 등 포함 |
| desktop/clipper_electron | `c944830` | 같음 | W14 runtime/core 패키징 연결과 W13/W14 통합 선행 커밋 포함 |
| desktop/clipper_nestjs | `5bb2ea3` | 같음 | 공유 클립 `76b0f8e`, 판정지도 `5bb2ea3` 등 포함 |
| desktop/clipper_python | `6b655ad` | 같음 | 공유 클립 `a6500b9`, 판정지도 `8698f00`, 샘플 프레임 시간 수정 `6b655ad` 포함 |
| web/clipper_web_api | `f243914` | 3커밋 뒤 | W06 `e252a1c`, QA/카탈로그, 개별 아티스트 `b48c1c3` 포함 |
| web/clipper_web_admin | `2eee9b2` | 5커밋 뒤 | 카탈로그 관리자, 수동 아티스트 `e3b076d`, 외부 데이터 화면 `b5c8310` 포함 |
| web/clipper_web_client | `07defb2` | 7커밋 뒤 | BUG-02-005 `bed65a3`, W06 `3e51f9e`, ISS-056 후속 포함 |
| web/clipper_infra | `e504093` | 2커밋 뒤 | W06 코드 `328f8b8`, [개발 DB/배포 실행 기록](../../web/clipper_infra/runbooks/toss-dev-mid-sync-execution-20261016.md) `3c335b8` 포함 |

기본 checkout이 뒤에 있는 저장소에서 `git status`나 현재 파일만 보고 원격 dev 누락이라고 판정하지 않는다. `desktop/clipper_angular`의 기존 미커밋 스펙, `web/clipper_web_api`의 `.env.example`·auth 수정, `web/clipper_infra`의 runbook 수정 등 다른 세션 작업은 보존하고 건드리지 않았다.

### dev에 포함됐지만 원래 브랜치가 남은 사례

| 남은 ref | 조사 결과 | 조치 |
|---|---|---|
| Angular `feat/highlight-results-copy-url-20261015` `7c23a5da` | Git 조상은 아니며 `git cherry`도 `+`지만 dev의 `abaceeb5`가 **동일 제목·동일 8파일 기능**을 다시 커밋했다. 해당 8파일의 두 commit 차이는 이후 버튼 클래스/아이콘 설명 두 줄 | 기능 누락으로 재병합하지 않음. ref 보존 |
| Web API `fix/dance-catalog-solo-retention-20261015` `b4d03be` | `git cherry -v origin/dev`가 `-`; dev에는 같은 patch `3187646` | 재병합 불필요 |
| Web API 원격 `fix/iss-056-credit-ledger-server-filter` `3a72a15` | `git cherry`가 `-`; dev 통합의 `655b934`와 patch 동등 | 재병합 불필요 |
| QA `fix/bug-02-005-billing-window`, ISS-028 관련, W13/W14 통합·카탈로그·W06 dev MID 브랜치 | 대상 커밋이 각 `origin/dev` 조상임을 확인 | 브랜치명만 보고 미반영으로 세지 않음 |

10/7 Toss **운영 라이브 전환**의 Web API/Client/Infra `feature/toss-live-cutover-20261007`와 `integration/main-promotion-20261008`는 dev에서 순수 커밋이 보이지만 조사 시점의 로컬 `origin/main` 조상이다. W06의 **개발 MID** 전환 누락으로 취급하지 않는다. 오래된 8월 desktop `feature/toss-payments-pg-integration`에도 dev 외 커밋이 있으나 이 주간 1·9번 작업 범위가 아니고 재병합 판단 근거가 없다. 이 두 군의 현재 원격 main 최신성은 이번 `fetch origin dev`만으로 보장하지 않는다.

### 실제로 dev에 없는 내용과 보존 위치

| 위치/상태 | dev에 없는 내용 | 판단 |
|---|---|---|
| [W13 평가 worktree](../../.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/notebooks/w13_dance_iteration_lab_72_stage_focus.ipynb) (`feature/w13-dance-metadata-eval-20261001`, HEAD `4778295`) | 노트북 71개, `output/`, 평가 helper·테스트, `pipeline.py`·`face_cluster.py` 미커밋 | **의도적 평가 분리**. 72번은 반례가 있어 미채택. 파일은 보존하되 일괄 제품 이식 금지 |
| Person MVP 네 desktop worktree (`.worktrees/person-highlight-mvp-20261001/`) | Angular 18·Electron 8·Nest 15·Python 2개 tracked 수정과 별도 실험 출력 | 품질 문제로 고도화 보류. dev 반영 계획 확정 전 선별 필요 |
| W13 공유 클립 개별 worktree (`.worktrees/w13-stage-shared-clips-20261015/`) | 원래 실험 당시 미커밋 파일 | 공유 노출/귀속의 후속 구현은 dev에 별도 반영. 이 트리 전체를 다시 병합하지 않음 |
| [W13/W14 통합 시험 tree](../../.worktrees/w13-w14-build-test-20261015/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/segment.py) | Python/Nest/Angular의 후반 **미커밋** 수동 클립 인물·장면종류 수정 UI/API, `max_clip_sec`로 긴 group 분할, 메인 초점 분할, 미확인 얼굴 재비교와 결과 실험 | 실제 누락 후보. 같은 시험 tree가 현재 원격 dev보다 오래된 기반이므로 전체 diff를 병합하면 관계없는 새 변경을 덮을 수 있음. 기능별 분리·재검증 필요. [후속](../../.worktrees/dance-diagnostic-docs-20261016/clipper_docs/todos/2026-10-16-dance-result-trial-worktree-followups.md) |
| `clipper_docs`의 `docs/dance-diagnostic-status-20261016` `922e153` | 시험 tree의 미반영 사항을 정리한 status/todo 2문서 | 문서 브랜치에 커밋됨, `clipper_docs/main`에는 미병합·미푸시. 이번 `.codex` 기록에서 링크로 인계 |
| Web API `dance-catalog-match-perf-20261016` worktree | 아티스트 제목 매칭 캐시/정규식 회피의 tracked 변경 2개 | 함수 단위 6.7~8.4초→12~33ms 측정은 있으나 실제 서버 지연 미측정. 시험 중 작업으로 dev 완료 표시 금지 |

이 표의 `dev 없음`은 결함 확정이나 즉시 병합 지시가 아니다. 시험 tree 일부는 의도적 평가 격리, 일부는 후반에 미커밋으로 남은 작업이다. 특히 8번 스레드의 새 앱/새 영상 개선량은 확보되지 않았다. [W13/W14 회고](../features/highlights/records/2026/10/16-w13-w14-experiment-reconciliation.md)에 채택 판단과 재현 출발점을 따로 정리했다.

## QA 스레드 1번: 버그 목록과 해결 증거

내부 QA 시트에서 진아 담당은 정식 ISS 10개와 번호 없는 이름 표시 메모 1개, 연결 원제보 21건이었다. QA 스레드 이름에 결제가 들어가지만 실제로는 다음 비결제 이슈도 다뤘다. `기획팀_김주희` 시트의 BUG-10-001/002는 기존 ID와 충돌해 원본에서 BUG-20-001/002로 고쳤다는 대화 기록도 보존한다.

| 항목 | 현재 확인 | 남은 검증 |
|---|---|---|
| ISS-011 / BUG-02-005 | Toss SDK 2.8.1, `payment.destroy()`, 복원 주문 상태 확인 수정 `bed65a3` 고객웹 dev 포함 | 원 제보 Windows Chrome 정기결제→영수증→뒤로 가기/탭 복귀 실거래 수동 재현 및 운영 main/배포 여부 별도 확인 |
| ISS-011 관련 BUG-05-009 | 법인카드 만료 원제보가 같은 QA 묶음에 있음 | BUG-02-005 수정으로 해결됐다고 간주하지 않고 별도 재현/결과 확인 |
| ISS-056 | KST 날짜 범위와 서버 원장 페이지 필터가 API/Client dev에 들어감 | 원 제보의 역전 날짜·페이지 넘김 재검증, 실제 서버/운영 반영 분리 |
| ISS-028 | 미지원 URL 처리와 안내 후속이 Angular/Nest dev에 들어감 | 실제 제보 URL과 설치본 UX 재검증 |
| ISS-025·026·031 | 연관 코드/브랜치 진척 있음 | 각각 다른 멤버·검색 누락·제작 목적 초기화의 **원 제보** 해결 여부 미확정. 031의 `5570f8ca`는 선택 해제/빈값 저장 수정이며 초기화와 동일 원인으로 단정 불가 |
| ISS-006·010·052·053 | 대화에서 원 제보 종결 증거 없음 | 스토리보드 생성 실패, 네이버페이 완료 직후 취소창, 직접입력 뒤 선택 해제 무반응, 아티스트 검색 오류 팝업을 재현/분류 |

결제 상세와 잔여 QA 항목은 갱신된 [W16 카드](tasks/payment-qa-bugs.md)에 둔다. 관리자 원장의 지급분별 `처리 후 잔여`와 회원 `전체 잔액`은 다른 값이고, 열 이름 변경·전체 잔액 열은 의도적으로 뒤로 미룬 항목이다. 10/8 대시보드 외부 취소/부분환불은 Clipper 내부 환불 기록·크레딧 자동 정리를 뜻하지 않는다.

## W06 스레드 9번: 개발 MID·DB 초기화·서버 경계

Web API `e252a1c`, 고객 웹 `3e51f9e`, 인프라 `328f8b8`을 dev에 통합한 뒤, 사용자가 10/16 User/Admin/Release의 세 개발 DB 컨테이너와 `_dev` 볼륨만 재생성하고 마이그레이션·테스트키 교체·API/고객 웹 배포를 진행했다. 운영 DB 세 개는 healthy로 기록했다. m2-db에서 Git 인증 오류가 있어 checkout 최신성이라고 주장하지 않고 실제 compose 파일 SHA256을 대조했다. m2-stage Docker Desktop 메모리 한도 약 2GB에서는 빌드가 실패했고 약 4GB로 늘려 성공했다.

정기 ₩29,900/4,000크레딧, 단건 ₩5,900/400크레딧, ₩5,900 전액환불 및 400회수 후 잔액 4,400 복귀, `PAYMENT_STATUS_CHANGED` 웹훅 처리를 사용자가 실행한 결과와 대조했다. 토스 키 원문은 기록하지 않았고, 사용자 MID 소속 대조와 키 형식 확인에 의존한다. `BILLING_DELETED`, 변경 후 정기결제 메일 호칭, 계좌이체 실거래는 미검증이다. 관리자 웹은 기존 컨테이너 포트와 프록시 대상 불일치로 502였고 admin만 재생성해 `073d044` 화면을 확인했다. 이후 개별 아티스트 API `b48c1c3`/Admin `e3b076d`도 개발서버 빌드·migration 후 health와 DB 3곳 OK를 확인했으나 KATSEYE 실제 게시 UI는 확인되지 않았다. [W06 실행 이력](../../web/clipper_infra/runbooks/toss-dev-mid-sync-execution-20261016.md)과 [05:26 당시 스냅샷](../../clipper_docs/status/2026-10-16-dev-merge-and-deployment-snapshot.md)을 본다. 후자에는 이후 개별 아티스트 배포/새 원격 dev 커밋이 없다.

## 이어서 할 때의 순서

1. W13/W14: 대표님께 전달한 설치본의 4개 desktop SHA·원본/참조 이미지·결과를 고정하고, 현재 dev와 같은 입력으로 비교한다. 메인/군무/컷, 얼굴 이름, 공유 인물·클립 경계의 정답을 따로 기록한다.
2. 시험 tree: Python 분할/재비교, Nest 수동 귀속 API, Angular 편집 UI를 기능별로 현재 dev에 재적용 가능한지 검토한다. 오래된 시험 tree 전체를 병합하지 않는다. `LOVE DIVE` 오탐·사용자 영상의 Nest 자원 정책 오류와 실제 재시도도 별도 항목으로 둔다.
3. QA: ISS별 원 제보 재현·설치본/개발서버/운영 반영을 구별해 닫는다. W06은 남은 웹훅·메일·계좌이체와 m2-db 인증을 후속으로 둔다.
4. 문서: `.codex`의 이 감사/WORKBOARD를 재개점으로 사용한다. `clipper_docs`의 05:26 스냅샷과 문서 전용 브랜치 `922e153`, 인프라 미커밋 배포 runbook은 각 소유 세션의 후속 병합 대상으로 추적한다.
