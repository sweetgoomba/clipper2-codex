# W14 공통 참조 얼굴 매칭 0.2.0 — 실제 구현·검증

**후속 설명·증거:** 사용자가 완료 표현의 범위를 지적해 [원본 기반 비교 화면과 정정](13-w14-face-matching-visual-comparison.md)을 추가했다. 코드 검증은 통과했지만 saved256의 개별 이름 일치는 기존보다 줄어드는 사례가 있다. 이 문서를 전체 영상의 품질 개선 완료로 읽지 않는다.

작성: 2026-10-13 KST. 사용자의 “니 추천대로 진행해”는 기존 설계/계획을 이 세션에서 직접 구현하고 마지막 독립 리뷰를 받는 Native 실행 승인이다. 계획 여섯 작업과 리뷰 수정까지 수행했다. **공통 패키지 구현 완료이며 W13 앱 적용·독립적인 정확도 개선 완료는 아니다.**

## 1. 구현 위치와 범위

- checkout: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python`
- branch: `feature/shared-reference-face-matching-20261013`
- 실제 `git fetch origin dev` 성공 후 고정한 base/HEAD: `47782953228861f4bdbdc135265d067c2a826b0e`. 조사 당시 SHA만 최신이라고 가정하지 않았다.
- 공통 root가 Git 저장소가 아니어서 앱 create_worktree가 실패했고 Python repo에서 Git fallback으로 격리했다. 앱 managed worktree 첨부는 없다.
- 기존 Person checkout의 donor 7개 파일 hash를 확인해 선택 복사했다. 기존 donor, W13 제품/평가 파일과 사용자 결과는 수정하지 않았다.
- 새 패키지 `clipper_face_core` 0.2.0, workspace member 및 lock 추가. NumPy 기본 의존성, OpenCV는 선택 extra 및 lazy import. SDK 시작 경로에 ML 의존성을 추가하지 않는다.
- `uv lock --offline` 성공, 공통 패키지/member 외 기존 dependency 업그레이드 없음. 사용자 지시 없이 commit/push/merge/deploy하지 않았다.

[패키지 설명·공개 API](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/clipper_face_core/README.md) · [소비 예제](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/clipper_face_core/examples/reference_matching.py) · [실행한 계획](2026-10-13-shared-reference-face-matching.md).

## 2. 무엇이 달라졌는가

| 공개 기능 | 구현된 동작 |
|---|---|
| `build_gallery` | 사용자 참조 ID별 여러 얼굴 특징의 float32 평균/L2. 기존 Dance의 epsilon 1e-9 계산 유지. 실패한 사진·불량 centroid 사유 보존, 중복 표본의 투표 증가 방지 |
| `match_reference` | 영상 얼굴 하나를 참조 전부와 독립 비교. 거리·1/2위 격차·후보·matched/ambiguous/unmatched/invalid·이유 반환. 다른 query가 같은 멤버에 매칭됐어도 영향을 받지 않음 |
| `combine_reference_matches` | 소비자가 같은 사람 범위라고 전달한 표본만 결합. 서로 다른 멤버의 강한 근거가 충돌하면 모호 결과로 유지. 관측 ID 중복이 support를 늘리지 않음 |
| provenance | 모델/전처리/정규화/차원/거리 공간, source·detector·config hash, 분석/관측/track/scope ID와 version, bbox·회전·PTS/time base 또는 파생 초를 명시 |
| evidence fingerprint | 결과를 실제 query 특징·출처에 결합. 같은 ID에 나중에 다른 특징을 넣어 이전 결과를 재사용하는 경우 거부 |
| 선택 의존성 | DTO/갤러리/매칭만 사용할 때 OpenCV import·모델 준비 없음. 모델 생성과 플러그인 venv는 소비자 소유 |

실명 자동 식별, 몸에서 얼굴 소유자 추정, 새로운 tracking/구간 생성은 수행하지 않는다. 기존 익명 grouping/대표 선택·검출 알고리즘은 보존했다. Person legacy `vector/norm`과 Dance `vector/(norm+1e-9)`를 같은 공간이라고 섞지 않는다.

## 3. 테스트와 독립 리뷰

환경: macOS, 기존 Python 3.11.12/NumPy 2.4.4/OpenCV 4.13.0. 새 venv 설치나 모델 다운로드 없이 PYTHONPATH를 새 core에 고정했다. synthetic 테스트는 모델 대신 고정 벡터/가짜 backend를 쓴다.

| 검증 | 실제 결과 |
|---|---|
| 여섯 task의 TDD | 각 새 테스트 실패를 먼저 확인 후 구현. 순차 GREEN 20→32→47→60→66→68 |
| 독립 리뷰 | fresh-context reviewer가 선택 suite 68개 재실행. Critical 0, Important 3, Minor 0 |
| 리뷰 회귀 | 새 5개 사례 RED(5 failed/20 passed) 확인 후 수정. 최종 core/replay **73 passed in 0.77s** |
| 기존 donor core+Person | 새 core import 경로로 **27 passed in 0.25s**. donor cache/pyc 생성 억제 |
| 확대 repo 회귀 | **617 passed, 3 skipped in 33.72s**, 17개 기존 Pillow 경고. 실제 plugin 부팅 smoke 11개 제외 |
| 정적 검사 | Ruff 통과, tracked diff whitespace 검사 통과 |

리뷰에서 수정한 3건:

1. 거의 상쇄되는 참조 평균이 불량 centroid를 만들어 정상인 다른 멤버까지 비교 실패시키던 경계. 동일 validator로 centroid 검사 후 해당 참조의 실패만 기록한다.
2. 소비 예제에서 다른 scope/미지정 scope에 같은 관측 ID와 다른 특징을 넣을 수 있던 경계. batch 전체에서 충돌을 거부하고 동일 반복은 한 번만 사용한다.
3. replay에 얼굴 소유 확정 여부가 없으면 confirmed로 간주하던 경계. association 필드를 명시해야 실행한다.

최초 전체 suite는 sandbox의 localhost bind 차단으로 **4 failed/16 errors/603 passed/3 skipped**였다. 전부 bind 이전/지점의 PermissionError였으며 제품 assertion 실패와 구분했다. localhost 권한을 허용하고 기존 venv·offline/no-sync로 재검증하여 비부팅 9개 해당 사례를 포함한 617개가 통과했다. 11개 실제 plugin 부팅 smoke는 새 모델 startup 범위 없이 실행하지 않았다. skip3은 Dance/Dialog 실영상 경로 미지정2개, Python 단독 checkout에 Angular sibling이 없는 parity1개다. **전체 제품 E2E 통과라고 표현하지 않는다.**

## 4. 실제 저장 데이터 replay — 모델 호출 0회

기존 10/13 진단 archive 77개 hash와 source·model·cache·정답표 hash를 대조했다. 참조23장/영상18프레임×3조건의 **저장 특징**만 사용했다. 최초 실행 v1과 리뷰 후 코드 hash를 갱신한 v2를 별도 폴더로 보존했다.

최종 실행 위치:
`/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/reference-replay-v2/`

source: `/Users/jina/project/adlight/.worktrees/w13-review-scenes-20261001/runtime-preview/sources/youtube/yFTAYXDTjqI/source.mp4`

- source SHA: `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`, 1920×1012, 133.654059초.
- SFace SHA: `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`.
- YuNet SHA: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`.
- space: OpenCV4.13.0, alignCrop5점, BGR uint8, float32 L2 epsilon1e-9,128D,cosine distance.
- policy: max_distance .60/min_margin0/minimum_support1, **기존 nearest 결과 재현용**이며 제품 권장값 아님.
- association: 명시적으로 confirmed를 입력하되 `legacy_selected_candidate_assumption_not_face_ownership_gt`라는 가정을 manifest/결과에 보존. 얼굴-몸 소유 정답이 독립적으로 검증됐다는 뜻이 아니다.

| 조건(각 18개) | 입력 라벨 일치 | 다른 라벨 | 미배정 |
|---|---:|---:|---:|
| annotated_target | 14 | 2 | 2 |
| saved256 | 4 | 12 | 2 |
| saved512 | 7 | 8 | 3 |

5명 참조 centroid 모두 array-equal, 54개 query 전체의 거리 차이 **0**, 기존 개별 배정/미배정 **54/54 재현**. 위 숫자는 진단 입력의 재현이며 새 독립 정확도 측정이 아니다.

동일 기존 track3/10.6106~20.2202초에 속하는 saved512의 17.2172/18.2182/19.2192초 세 표본을 결합하면 **해린**으로 나온다. 기존 전역 군집 후 최종 이름 **하니**와 차이가 난다. 이 사례는 올바른 개별 근거가 후단 전역 군집에 의해 다른 이름으로 바뀌는 경로를 피하는 근거지만, 전체 영상의 개선 증명은 아니다. 다른 scope의 연속성을 임의로 만들지 않았다.

자원 상한120초/2GiB/25MiB. supervisor exit0/limit중단없음, 0.196934초, sampled peak RSS38,256,640B, 전체 출력83,779B. worker 0.086380초/peak RSS38,273,024B. RSS는 polling과 worker peak 확인이며 순간 peak를 OS 차원에서 강제하는 hard cap은 아니다. 새 모델 실행/다운로드·유료 API·Build5 없음.

## 5. W13 소비 순서와 파일 소유

1. W14 소유: `clipper_face_core/**`, 공통 workspace/lock, `evaluation/reference_matching/**`. 위 branch는 **미커밋**이므로 HEAD만으로 전달하면 코드가 빠진다. durable 코드 inventory/hash를 함께 확인한다.
2. W13 소유: `plugins/dance_highlight/**`의 대상 사람/얼굴 선택·track/scope·결과 적용. `classify_selected_faces` 예제처럼 새 public API를 소비하되 `association`을 근거 없이 confirmed로 만들지 않는다.
3. 공유 workspace/lock·Electron 설치 fingerprint 변경은 단일 수정 소유자를 정해 순서대로 적용한다. 공통 package 먼저 통합한 뒤 W13 adapter/consumer venv가 따라오거나, W13 선행 변경 SHA로 core를 재기준화해 호환 검사를 다시 한다. 현재 API 수용 완료나 merge를 문서만으로 주장하지 않는다.
4. 기존 27개 호환 테스트, 선택 import 경계, 동일 입력 centroid/거리 재현, 결과의 모호/미배정/충돌, Mac/Windows 플러그인 설치 및 Electron fingerprint 반영을 소비 gate로 삼는다.
5. 다음 품질 평가는 모델 결과를 보기 전에 고정한 별도 얼굴 bbox/대상 몸 연결/익명 ID/가림·해상도 라벨이 필요하다. 올바른 얼굴 직접 입력과 실제 W13 선택 입력을 분리해 멤버별 맞음/오배정/미배정/모호/실패를 모두 보고한다.

W13 외부 세션 메시지나 새 작업 세션은 만들지 않았다. 인계 파일에 소비 계약을 남겼으며 W13 adapter 연결 자체는 W13에서 이어갈 작업이다.

## 6. 구현 중 판단·미검증

- native worktree 도구 실패 후 Git fallback: 작업 격리는 확보했으나 앱 첨부가 없어 경로를 직접 관리해야 한다.
- commit 없이 ledger/worktree 보존: 저장소 규칙을 따랐다. 커밋 전이므로 삭제/유실 시 복구 위험이 있어 코드 inventory와 실행 증거를 함께 보관한다.
- 잘못된 출처/시간/공간 계약은 예외, 실패 embedding은 결과 상태: 소비자가 예외와 분석 실패 상태를 구분해야 한다.
- `ReferenceMatch.evidence_fingerprint` 보완: stale 결과와 변경된 특징을 섞는 것을 차단한다. 소비자는 새 필드를 보존해야 한다.
- 독립 얼굴 매칭률·얼굴 소유 품질은 미검증: 이미 본 진단 표본으로 개선을 단정하면 실제 오배정을 숨길 수 있다.
- 제품 adapter/플러그인 설치 미검증: 예제만으로 앱이 새 엔진을 사용하지 않는다. 연결 전까지 현재 앱 동작은 기존 방식이다.
- Windows 미검증: import/path/의존성 문제가 별도 발견될 수 있다.
- 기존 grouping/검출 선택 정책 유지: 원래의 사람 오선택·익명 grouping 한계가 해결되었다고 해석하지 않는다.
- 전체 테스트 중 모델 부팅11/실영상2/Angular parity1은 미검증: 확대617개 통과와 제품 E2E를 구분한다.
- supervisor는 부모 작업에서 검증하고 reviewer는 재실행하지 않았다. polling RSS의 순간 overshoot 가능성을 기록한다.
- 미뤄 둔 Minor 리뷰 항목: **없음**. Important3개는 전부 수정했다.

증거 보관: [manifest·코드 hash 목록](evidence/13-w14-shared-reference-matching/manifest.json). 계획 ledger의 자동 commit 범위 표기 `4778295..4778295`는 실제 커밋 생성이 없음을 뜻한다. 최종 diff/새 파일 hash와 별도로 읽어야 한다.
