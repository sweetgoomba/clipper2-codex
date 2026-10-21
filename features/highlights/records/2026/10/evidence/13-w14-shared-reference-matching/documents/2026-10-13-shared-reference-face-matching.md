# Shared Reference Face Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 안무가 제공한 대상 얼굴을 사용자 참조 ID와 비교하는 독립 공통 패키지 및 기존 저장 입력의 대조 실행기를 만든다.

**Architecture:** 기존 W14 `clipper_face_core`의 검출/익명 grouping API를 호환성 기준으로 보존하며, 참조 갤러리·개별 비교·같은 사람 표본 결합을 독립 함수로 추가한다. 새 경로는 전역 cluster/강제 일대일 멤버 배정을 요구하지 않는다. W14는 격리 대조까지 맡고 W13의 제품 adapter 연결은 W13 파일 소유권 아래 별도 소비 검증으로 진행한다.

**Tech Stack:** Python 3.11, dataclasses, NumPy float32, pytest, uv/hatchling workspace, 선택 OpenCV YuNet/SFace backend. 새로운 ML 모델/라이브러리를 도입하지 않는다.

**Spec:** [2026-10-13-shared-reference-face-matching-design.md](../specs/2026-10-13-shared-reference-face-matching-design.md). 사용자가 설명을 듣고 `진행해줘ㅗ`라고 답해 설계 진행을 승인했다. **사용자가 “니 추천대로 진행해”로 Native 실행을 승인했다. 2026-10-13 여섯 작업과 독립 리뷰 수정까지 실행 완료. W13 제품 연결·독립 품질 평가는 후속이다.**

## Global Constraints

- `사람 선택·추적·구간 경계는 W13, 얼굴 관측·비교·참조 매칭 공통 기능은 W14가 담당한다.`
- `현재 Person 자체 UI·출력·몸 검출/등장 interval 개발은 보류한다.`
- `첫 비교의 평균/L2 계산은 현재 Dance 방식과 동일하게 유지한다.`
- `다른 query가 먼저 배정됐다는 이유로 차순위 참조 ID를 대신 배정하지 않는다.`
- `새 기본 수치는 설계만으로 확정하지 않는다.` 평가의 거리 기준은 현행 0.60이며 신규 정책의 제품 기본값으로 채택하지 않는다.
- `공용 입력은 Dance Segment, PersonGroup, Angular UI, job/과금 타입에 의존하지 않는다.`
- `기본 SDK/app 시작 경로에 얼굴 모델 설치·초기화를 추가하지 않는다.` 각 플러그인의 선택 의존성·venv·모델 준비 유지.
- `10/13의 18개 표본은 이미 열람한 진단 자료이므로 새 독립 성능으로 재사용하지 않는다.`
- 최신 `origin/dev` 확인 후 새 격리 Python checkout에서 구현. 기존 Person/W13 checkout과 형제 저장소 변경 보존. 커밋·push·merge·배포는 별도 사용자 요청 시에만 수행한다.
- 이번 계획의 완료는 공통 코드/재현/소비 계약까지다. 안무 앱 적용·독립 영상 품질 검증·Windows 실기는 각각 별도 완료 여부를 기록한다.

## Review Focus

- 한 명만 등록한 갤러리: 2위가 없어도 거리 조건을 통과한 경우만 배정하고 `margin=null`의 한계를 남긴다. Task 3의 `test_single_reference_still_requires_distance`.
- 같은 관측을 반복 전달하거나 같은 ID에 다른 벡터를 넣는 입력: 지지 수 부풀림 방지, 상충 ID 거부. Task 2/4의 duplicate tests.
- 동일 SFace weight지만 정렬/정규화/backend 또는 gallery/policy가 다른 결과: 조용한 혼용 거부. Task 1/3/4의 provenance tests.
- 한 track에 서로 다른 참조를 지지하는 얼굴 또는 얼굴 소유 불명 표본이 섞임: 억지 평균 대신 충돌/보류와 모든 근거 유지. Task 3/4의 association/conflict tests.
- 호출자가 반환 후 원본 배열을 수정함: 갤러리 hash와 비교 결과 불일치 방지. Task 2의 `test_gallery_owns_immutable_vectors`.

## 확인한 코드와 구현 작업 공간

아래 `REPO`는 **실행 때 도구가 반환할 새 Python checkout**을 뜻한다. 계획 검토 중에는 worktree/브랜치/환경을 만들지 않았다. 실행자는 `list_artifacts`를 확인하고 `superpowers:using-git-worktrees` 및 `create_worktree`를 먼저 사용한다. 현재 채팅의 루트가 Git 저장소가 아니어서 도구가 지원하지 못하면 그 결과를 남기고 Python 저장소의 native Git worktree 대안을 사용한다. 새 브랜치 제안은 `feature/shared-reference-face-matching-20261013`이다. 실행 전에 remote fetch로 `origin/dev` SHA를 확정하고 기록하며 실패한 fetch를 최신 상태라고 표현하지 않는다.

소스 donor는 `/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python`이다. 로컬 dev·donor·W13 조사 HEAD는 `47782953228861f4bdbdc135265d067c2a826b0e`이며 **원격 최신 보증이 아니다**. donor의 `clipper_face_core`는 미커밋이므로 HEAD만으로 재현되지 않는다. 다음 7개 파일만 allowlist로 복사하며 과거 평가 자료·Person 플러그인·donor workspace/lock 전체는 옮기지 않는다.

| donor 상대 파일 | SHA-256 |
|---|---|
| `clipper_face_core/pyproject.toml` | `f2a73c7d45b78b69ce74ca693acc4e091b04046b55af614853c4bdb5704f91d9` |
| `clipper_face_core/README.md` | `51790893c5b3809be1ee48044856b64956a3b82df6619d8146d9b0ff4245c7a1` |
| `clipper_face_core/clipper_face_core/__init__.py` | `424bc88e4f6cd4de01a901d05633f529d7e0685636a3ba86900f3c70f25fa7c3` |
| `clipper_face_core/clipper_face_core/grouping.py` | `911fc6bc4b923924c12c40f676b0a98fed7e3ea78ca60852f825f5b28077d1a2` |
| `clipper_face_core/clipper_face_core/opencv_backend.py` | `419858898d3a463f51f5c7fc36f0499038eaa7eaa8a2b93f2147e19671b4331e` |
| `clipper_face_core/tests/test_grouping.py` | `7b0f089784847f621ec32f7162103a1b8bdadc9a97a1c9fd3c62943ccd22f688` |
| `clipper_face_core/tests/test_opencv_backend.py` | `67b2142d38331d3c8d19feecc044861dc9d279643bffa42cfd4de917c762f617` |

계획 작성 중 기존 core 테스트 **10 passed in 0.19s**, 기존 Person 테스트 **17 passed in 0.45s**를 각각 확인했다. 모델 없이 합성 입력/가짜 detector·recognizer로 실행했으며 제품/실영상 품질 점수가 아니다. donor 변경이 있으면 hash 불일치를 먼저 검토하고 덮어쓰지 않는다.

아래 검증 명령의 `python`은 기존 `/Users/jina/project/adlight/desktop/clipper_python/.venv/bin/python`을 쓰고, 실행 때 `PYTHONPATH` 선두를 새 `REPO/clipper_face_core:REPO/clipper_plugin_sdk`로 지정한다. 기존 환경에 패키지를 덮어 설치하지 않는다. `PYTHONDONTWRITEBYTECODE=1`과 pytest `-p no:cacheprovider`로 donor 검증 시 파일 생성을 막는다. 예제/replay 모듈을 실행할 때는 새 REPO를 작업 디렉터리로 쓴다. 새 소비 플러그인의 venv 설치 검증은 W13 연결 단계에 별도로 기록한다.

## 파일 구성과 공개 계약

모든 경로는 `REPO` 상대다. `clipper_face_core/clipper_face_core/`에 `contracts.py`(아래 DTO/지문), `backend_types.py`(기존 ModelFiles/FaceDetection의 의존성 분리), `gallery.py`(참조 집계), `matching.py`(개별 비교), `consensus.py`(근거 결합)를 추가한다. 기존 `grouping.py`의 판단 동작은 바꾸지 않는다. `__init__.py`는 기존 이름을 보존하고 OpenCV backend만 지연 import한다.

공개 DTO는 frozen dataclass이며 좌표/시간/정책의 float 수치는 유한해야 한다. 특징 ndarray는 float32 복사본을 만들고 read-only로 보관하되, NaN/Inf/영벡터 같은 특징 실패는 gallery/matching 단계가 명시적 결과로 반환한다. 아래 정의가 각 task의 공통 입력/출력이다.

| 타입 | 필드와 의미 |
|---|---|
| `EmbeddingSpace` | `recognizer_sha256:str`, `alignment_version:str`, `preprocessing_version:str`, `normalization_version:str`, `dimension:int`, `backend_version:str`, `metric:str='cosine_distance'`; `fingerprint:str` 파생 property. 필수 문자열/차원 및 SHA 검증. detector 설정은 이 지문과 별개 |
| `SourceEvidence` | `analysis_id:str`, `source_sha256:str`, `observation_version:int`, `detector_sha256:str`, `config_sha256:str`, `adapter_version:str`, `time_kind:Literal['pts','derived_seconds','still_image']`, `time_seconds:float\|None`, `pts:int\|None`, `time_base:tuple[int,int]\|None`, `frame_index:int\|None`, `width:int`, `height:int`, `rotation:int`, `bbox_px:tuple[float,float,float,float]\|None`, `track_id:str\|None`, `scope_id:str\|None`, `scope_range_seconds:tuple[float,float]\|None`; normalized bbox 파생 property |
| `ReferenceSample` | `sample_id:str`, `reference_id:str`, `source:SourceEvidence`, `space:EmbeddingSpace`, `embedding:ndarray\|None`, `failure:str\|None` |
| `QueryEvidence` | `observation_id:str`, `source:SourceEvidence`, `space:EmbeddingSpace`, `embedding:ndarray\|None`, `association:Literal['confirmed','ambiguous','unassigned']`, `failure:str\|None`, `quality:tuple[tuple[str,float],...]` |
| `SampleFailure` / `GalleryEntry` | 실패는 `sample_id,reference_id,reason`; entry는 `reference_id,centroid,used_sample_ids`. 빈 ID 불가 |
| `ReferenceGallery` | `space`, `entries:tuple[GalleryEntry,...]`, `samples:tuple[ReferenceSample,...]`, `failures:tuple[SampleFailure,...]`, `aggregation_version:str`, `fingerprint:str` |
| `MatchPolicy` | `max_distance:float`, `min_margin:float`, `minimum_support:int`; 기본값 없음. 앞의 두 값 [0,2], support 양의 정수(bool 불가); `fingerprint:str` |
| `CandidateDistance` / `ReferenceMatch` | 후보는 `reference_id,distance`; 결과는 `observation_id,status:Literal['matched','ambiguous','unmatched','invalid'],reference_id:str\|None,candidates:tuple[CandidateDistance,...],margin:float\|None,reason:str,space_fingerprint,gallery_fingerprint,policy_fingerprint,evidence_fingerprint`. evidence_fingerprint는 실제 query 특징/출처와 결과를 결합하는 구현 시 보완 필드다. source/quality는 QueryEvidence의 observation ID로 연결 |
| `ConsensusResult` | `scope_id:str`, `status`, `reference_id`, `reason`, `matches:tuple[ReferenceMatch,...]`, `used_observation_ids:tuple[str,...]`, `excluded:tuple[tuple[str,str],...]`, `gallery_fingerprint`, `policy_fingerprint` |

`SourceEvidence` 좌표는 회전 적용 display frame, pixel xyxy, 반열린 경계다. rotation은 0/90/180/270, width/height는 그 회전 적용 후 치수다. bbox는 프레임 범위 내 양의 면적만 허용한다. 범위 밖 raw 검출 좌표는 importer 원본 artifact에 유지하고, 변환/clip 버전을 adapter provenance에 기록한다. `pts`에는 정수 PTS와 양의 rational time base가 함께 필요하다. 파생 초는 원본 시각이라고 바꾸지 않고 `derived_seconds`로 표시한다. still_image에는 시각이 null이다. 관측 ID 유일 범위는 analysis 내부이며 집계는 동일 analysis/source/scope 안에서만 허용한다. scope_range_seconds는 소비자가 제공한 [start,end)이고 관측이 그 안에 있어야 한다. 범위를 모르면 null을 유지하고 구간을 추정해 만들지 않는다.

지문은 schema/version을 포함한 canonical JSON(키 정렬, NaN 불가, UTF-8, 고정 separators)의 SHA-256이다. 벡터는 little-endian float32 바이트 hash로 참조한다. 순서가 수치 연산에 영향을 주는 참조 sample 순서는 fingerprint에도 포함한다. 로그/일반 결과 JSON에 embedding 배열을 쓰지 않는다.

## Task 1: 격리 패키지, 공개 타입, 선택 backend 경계

**Files:** 위 donor 7개 → 같은 경로로 Create; Create `clipper_face_core/clipper_face_core/{contracts,backend_types}.py`, `clipper_face_core/tests/{test_contracts,test_import_boundary}.py`; Modify `pyproject.toml`, `uv.lock`, `clipper_face_core/{pyproject.toml,README.md}`, core `__init__.py`, `opencv_backend.py`.

**Interfaces:** 위 DTO 및 `EmbeddingSpace.fingerprint`, `SourceEvidence.bbox_normalized`. 기존 `FaceObservation`, `FaceDetection`, `ModelFiles`, `OpenCvFaceBackend`, grouping/대표 함수 이름과 기존 생성자 유지.

- [x] **1.** 실행 전 최신 remote/base·새 checkout·donor hash를 기록하고 allowlist만 가져온다. 이 단계에서 새 API/의존성 변경을 구현하지 않고 기존 10개 테스트의 재현 기준을 확보한다.
- [x] **2.** `test_import_boundary.py`에서 child interpreter의 import hook으로 SDK는 numpy/cv2/torch/onnxruntime, core 타입은 cv2/torch/onnxruntime를 차단한 import를 각각 검사한다. 명시적 backend 사용은 OpenCV가 없으면 `Install clipper-face-core[opencv] in the consuming plugin environment` 안내로 실패하고 다운로드하지 않아야 한다. 기존 `from clipper_face_core import FaceDetection, ModelFiles`는 OpenCV 없이 성공해야 한다. 이후 Task 3/4에서 완성한 공개 matching/consensus import도 이 검사에 추가한다.
- [x] **3.** `test_contracts.py`에 아래 assertion을 작성하고 실행해 새 타입 부재/기존 eager import로 실패하는지 확인한다.

```python
assert space.fingerprint != replace(space, normalization_version="other").fingerprint
assert source.bbox_normalized == (0.1, 0.2, 0.5, 0.8)  # 100x100, bbox=(10,20,50,80)
assert derived_source.time_kind == "derived_seconds" and derived_source.pts is None
with pytest.raises(ValueError): replace(pts_source, time_base=(1, 0))
with pytest.raises(ValueError): replace(space, recognizer_sha256="")
with pytest.raises(ValueError): MatchPolicy(0.60, 0.0, True)
```

- [x] **4.** DTO/검증/지문을 구현한다. ModelFiles/FaceDetection을 `backend_types.py`로 옮기고 이전 `opencv_backend` import 경로에서도 재export한다. `__getattr__`로 root의 `OpenCvFaceBackend` 접근만 지연한다. detection/grouping 알고리즘은 유지한다. workspace에 core 하나만 추가하고 버전 0.2.0, numpy 기본 의존성, `[project.optional-dependencies].opencv`의 OpenCV 의존성으로 설정한다. 기존 Person은 자체 OpenCV 의존성이 있어 donor Person 파일을 바꾸지 않는다. lock은 기존 의존성 변경을 최소화해 생성하고 unrelated upgrade가 있으면 해결 후 진행한다.
- [x] **5.** `python -m pytest clipper_face_core/tests/test_contracts.py clipper_face_core/tests/test_import_boundary.py clipper_face_core/tests/test_grouping.py clipper_face_core/tests/test_opencv_backend.py -q` → 모두 PASS. SDK pyproject의 필수 의존성에 core/ML이 추가되지 않았는지 확인한다.

## Task 2: 참조 갤러리와 기존 평균 재현

**Files:** Create `clipper_face_core/clipper_face_core/gallery.py`, `clipper_face_core/tests/test_gallery.py`; Modify core `__init__.py`.

**Interfaces:** `build_gallery(samples: Sequence[ReferenceSample], *, space: EmbeddingSpace) -> ReferenceGallery`. 무효 참조는 failures에 보존; 섞인 공간·상충 sample ID·유효 entry 0개는 `GalleryBuildError(ValueError)`(필드 `reason`, `failures`)로 실패.

- [x] **1.** 실패 테스트를 작성한다. `test_mean_matches_existing_dance`는 float32 입력을 받은 기존 계산 `avg=np.mean(np.stack(vectors),axis=0); avg/(float(np.linalg.norm(avg))+1e-9)`와 array equality를 검사한다. 입력 norm이 1에서 1e-5 이상 벗어나면 실패 표본으로 남기며 몰래 재정규화하지 않는다. 평균 영벡터/비유한 값은 해당 entry 실패다.
- [x] **2.** `test_duplicate_sample_id_is_not_an_extra_vote`는 동일 sample의 재전달로 centroid/used sample 수가 변하지 않음을, `test_conflicting_sample_id_rejected`는 같은 ID의 다른 참조/벡터가 오류임을 확인한다. `test_gallery_owns_immutable_vectors`는 생성 후 caller 원본 배열 변경으로 centroid/hash가 바뀌지 않음을 확인한다. 다른 space/실패 일부/실패 전부/중간 entry의 zero mean도 검사한다.
- [x] **3.** `python -m pytest clipper_face_core/tests/test_gallery.py -q` → 구현 전 FAIL 확인.
- [x] **4.** sample 순서와 실패 상태를 보존하고 valid sample을 reference ID별 평균/L2로 집계한다. 유효한 첫 등장 reference ID 순서를 entry 저장 순서로 쓰며 결과 순위 정렬은 Task 3이 맡는다. 배열을 독립 read-only 복사한다. aggregation version은 `mean_f32_l2_eps1e-9_v1`이다.
- [x] **5.** 같은 명령 → PASS. 실패를 성공 entry로 바꾸거나 데이터에서 삭제하지 않았는지 확인한다.

## Task 3: query별 독립 참조 비교

**Files:** Create `clipper_face_core/clipper_face_core/matching.py`, `clipper_face_core/tests/test_matching.py`; Modify core `__init__.py`.

**Interfaces:** `match_reference(query: QueryEvidence, gallery: ReferenceGallery, policy: MatchPolicy) -> ReferenceMatch`. 개별 입력 실패는 `invalid`로 반환하며 한 query의 실패가 다른 query에 영향을 주지 않는다.

- [x] **1.** 다음 테스트를 작성한다: 같은 A 특징의 q1/q2가 모두 A에 배정, q3 추가 후 q1 결과 불변, 두 query 호출 순서 교환 후 각 결과 불변. 2D 단위벡터 fixture에서 A=(1,0), B=(0,1), q=(1,0), policy=(0.60,0,1)을 사용한다.
- [x] **2.** 경계 테스트: `distance==max_distance` 허용, `margin==min_margin` 허용, 정확한 동률은 `min_margin=0`이어도 ambiguous. `test_single_reference_still_requires_distance`는 한 참조에서 q=(-1,0) 미배정, q=(1,0) 배정과 margin null을 검사한다. 차원/space mismatch·NaN/Inf·영벡터는 invalid; association ambiguous/unassigned는 어떤 거리여도 배정하지 않되 후보는 보존한다.
- [x] **3.** `python -m pytest clipper_face_core/tests/test_matching.py -q` → 구현 전 FAIL 확인.
- [x] **4.** 입력 space 검증 후 `1-float(np.dot(query, centroid))`를 계산하며 수치 오차만 [0,2]로 clamp한다. float32 입력을 다시 정규화하지 않는다. 후보를 `(distance, reference_id)`로 정렬하되 동률을 ID순 승자로 확정하지 않는다. 우선순위는 invalid → association 불명 ambiguous → 거리 미달 unmatched → 동률/격차 미달 ambiguous → matched. 각 상태·한 참조의 거리만 판단한 경우를 reason으로 명시한다.
- [x] **5.** 같은 명령 → PASS. 결과가 observation/space/gallery/policy 지문을 포함하고 embedding 벡터는 포함하지 않는지 확인한다.

## Task 4: 같은 사람 표본의 합의·충돌과 중복 방지

**Files:** Create `clipper_face_core/clipper_face_core/consensus.py`, `clipper_face_core/tests/test_consensus.py`; Modify core `__init__.py`.

**Interfaces:** `combine_reference_matches(scope_id: str, evidence: Sequence[QueryEvidence], matches: Sequence[ReferenceMatch], policy: MatchPolicy) -> ConsensusResult`. evidence/matches는 observation ID로 연결한다. 구조 오류(누락 대응·다른 analysis/source/scope·상충 중복 ID·다른 gallery/space/policy)는 ValueError로 명시적 실패.

- [x] **1.** `test_conflicting_references_are_preserved`에서 같은 scope의 A/B matched 두 표본은 ambiguous/conflicting_references, reference_id null이며 두 근거가 남아야 한다. A matched 2개+failed 1개는 support=2에서 A, failed도 excluded 사유로 남긴다. A 1개+ambiguous 1개는 support=2에서 insufficient_support다.
- [x] **2.** 동일 observation을 두 번 전달해도 support=2를 만족하지 않는 테스트, 다른 gallery/policy 결과 혼합 거부, 다른 source/analysis의 같은 track ID 거부를 작성한다. 모두 invalid/모두 거리미달/모호 표본만/빈 입력을 각각 invalid/unmatched/ambiguous/invalid(no_evidence)로 확인한다.
- [x] **3.** `python -m pytest clipper_face_core/tests/test_consensus.py -q` → 구현 전 FAIL 확인.
- [x] **4.** 중복을 제거한 뒤 matched 참조 ID 집합의 충돌을 먼저 검사한다. 지지 ID가 하나이고 고유 지지 수≥minimum_support인 경우만 배정한다. 후보 점수 평균으로 충돌을 지우지 않고 각 결과를 matches에 유지한다. used IDs는 해당 최종 배정의 지지 표본, excluded에는 나머지 사유를 남긴다. 미배정 집계에서는 used IDs를 비워도 matches 전체를 보존한다.
- [x] **5.** 같은 명령 → PASS. Task 3+4 결합 테스트로 다른 사람/구간을 추가해 기존 scope 결과가 변하지 않는지 확인한다.

## Task 5: 실제 저장 입력의 격리 대조 실행기

**Files:** Create `evaluation/reference_matching/{__init__,manifest,replay}.py`, `evaluation/reference_matching/tests/test_replay.py`. 기존 W13 도구와 제품 소스는 읽기만 한다. 실행 결과는 Git 소스 밖의 새 output 디렉터리에 저장한다.

**Interfaces:** `load_replay_manifest(path: Path) -> dict`, `run_replay(manifest_path: Path, output_dir: Path) -> dict`; CLI `python -m evaluation.reference_matching.replay --manifest PATH --output-dir PATH`. manifest v1은 정확한 input paths+SHA, code hashes, embedding space, policy, label limitation, 자원 상한을 필수로 한다. W13 cache 또는 이전 NPZ에 지문이 없으면 현재 지문을 추정해 넣지 않는다. 10/13 고정 worker/계산식/모델 hash로 복원 가능한 공간만 importer에 명시하고 근거를 기록한다.

- [x] **1.** 합성 fixture로 source hash 불일치 시 추론/출력 전에 실패, unknown/ambiguous/invalid를 분모에서 누락하지 않음, 출력 디렉터리 존재 시 덮어쓰기 거부, 서로 다른 space 파일의 혼합 거부, NPZ `allow_pickle=False`, JSON에 embedding 배열 없음 테스트를 작성한다. CLI 테스트에서는 cv2/모델 생성 자체를 차단해도 성공해야 한다.
- [x] **2.** `python -m pytest evaluation/reference_matching/tests/test_replay.py -q` → 구현 전 FAIL 확인.
- [x] **3.** 이 importer의 실입력은 [10/13 보관 자료](/Users/jina/project/adlight/.codex/features/highlights/records/2026/10/evidence/13-w14-face-matching-baseline/archive-manifest.json)의 `reference-gallery/reference-embeddings.local.npz`, `reference-result.json`, `selected-face-trace/query-embeddings.local.npz`, `trace-result.json` 및 각 plan.json이다. archive-manifest의 hash와 실제 file hash를 먼저 대조한다. W13 기존 cache/helper는 `cache-audit.json`에 고정된 hash와 일치할 때만 대조군으로 읽는다. 코드 내용 변경 시 새 manifest로 기록한다.
- [x] **4.** 이 성공 2회에 사용한 Dance SFace space를 선언한다: recognizer SHA `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`, OpenCV 4.13.0, SFace alignCrop 5점/BGR 처리, float32 L2 `norm+1e-9`, dimension128, cosine distance. Person core의 `vector/norm` 특징과 동일 공간으로 합치지 않는다. detector YuNet SHA `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`와 .28/NMS .30/topK5000은 관측 provenance로 보존한다.
- [x] **5.** 같은 명령 → PASS. 첫 실데이터 replay는 모델 호출 0회, max_distance=.60/min_margin=0/minimum_support=1의 **legacy nearest 재현 조건 한 개**만 사용한다. 이 비교에서는 기존 선택을 소비자의 확정 선택으로 가정해 association=confirmed로 전달하고 `association_basis=legacy_selected_candidate_assumption_not_face_ownership_gt`를 manifest/결과에 표시한다. 얼굴 소유 정답이 확보됐다는 뜻은 아니다. 참조23장의 갤러리 centroid는 기존 값과 array equality, 54개 query의 거리 허용오차≤1e-6와 후보/미배정 결과를 비교한다. 조건별 14/18·4/18·7/18 및 2·2·3 미배정을 재현한다. 이는 구현 재현이지 개선 점수가 아니다.
- [x] **6.** 세 표본(17.2172/18.2182/19.2192)의 saved512는 같은 기존 track 범위임을 cache로 대조한 후 합의 결과 해린을 확인한다. 기존 최종 하니와 나란히 기록한다. 다른 scope/몸 오선택/불확실한 소유는 verified same-person으로 넣지 않는다. 기존 데이터의 detector 선택을 새 알고리즘으로 개선했다고 주장하지 않는다. 시간·RSS·출력 상한은 각각120초/2GiB/25MiB로 manifest에 잠그고 enforce하는 supervisor로 실행한다. 제한 강제가 불가능하면 실행하지 않고 이유를 기록한다.

## Task 6: 소비 예제·호환 확인과 품질 평가 인계

**Files:** Create `clipper_face_core/examples/reference_matching.py`, `clipper_face_core/tests/test_consumer_contract.py`; Update core README 및 `.codex` W14 카드/WORKBOARD/날짜별 기록/W13 공통 계약 인계. **W13 `plugins/dance_highlight/**`는 이 task의 수정 대상이 아니다.**

**Interfaces:** 예제 `classify_selected_faces(references: Sequence[ReferenceSample], queries: Sequence[QueryEvidence], *, space: EmbeddingSpace, policy: MatchPolicy) -> tuple[ReferenceGallery, tuple[ReferenceMatch,...], tuple[ConsensusResult,...]]`; 예제 한 호출의 queries는 동일 analysis/source로 제한하고 다르면 ValueError다. scope가 있는 query만 해당 scope로 결합하고 없는 것은 개별 결과로 보존한다. 앱/SDK/job 객체를 요구하지 않는 소비 예제다.

- [x] **1.** 가짜 소비자가 참조2명/개별 얼굴/같은 사람 scope를 전달하는 test를 작성한다. 동일 인물 여러 구간, 선택 얼굴 불명, 비교 실패, 한 scope의 상충 표본을 함께 넣어 결과 상태·근거를 검사한다. 입력 구간/track/관측 ID가 변경되지 않고 구간 생성/삭제가 발생하지 않는지 검사한다.
- [x] **2.** `python -m pytest clipper_face_core/tests/test_consumer_contract.py -q` → 구현 전 FAIL 확인 후 위 공개 함수만으로 예제를 구현하고 PASS를 확인한다. SDK나 Dance 내부 타입을 import하지 않는다.
- [x] **3.** 최종 선택 검증: `python -m pytest clipper_face_core/tests evaluation/reference_matching/tests -q`, `python -m ruff check clipper_face_core evaluation/reference_matching` → PASS. donor의 기존 core 10개+Person 17개 테스트는 **새 core를 PYTHONPATH 선두에 두고** 별도로 실행해 API 호환을 확인한다. donor 파일은 수정하지 않고 cache/pyc를 생성하지 않는다. interpreter의 실제 import 경로를 출력해 donor core를 잘못 테스트하지 않았음을 증명한다.
- [x] **4.** W13 인계에 package 경로/version·공개 호출 예제·baseline/new 차이·입력 provenance·코드 hash·호환 결과를 기록한다. 실제 W13 adapter 소비는 그 세션의 branch에서 수행하며 새 API 수용/연결 완료는 문서만으로 주장하지 않는다. 소비 플러그인 pyproject/uv lock과 Electron 설치 fingerprint를 연결할 때 해당 세션과 단일 수정 소유를 정한다. 이 계획에서는 Electron·Nest·Angular·Web API를 수정하지 않는다.
- [x] **5.** 후속 **제품 품질 판정**에 필요한 입력을 실행 기록에 명시한다: 모델 결과를 보기 전에 고정한 새 원본 얼굴 bbox/대상 몸 연결/익명 ID/가림·해상도 상태 라벨, 같은 참조 gallery, source/model/config/code hash. 현재18표본은 진단용으로 표시한다. 올바른 얼굴 제공/실제 안무 대상 제공을 분리하고 맞음·다른 멤버·미배정·모호·실패 및 멤버별 편차를 모두 보고한다. 모델 교체·새 얼굴 선택 규칙·제품 적용은 이 검증을 거쳐 별도 판단한다.

## 최종 검토 및 실행 방식

설계의 import/공개 계약은 Task1, 참조 평균/실패는 Task2, 개별 독립 매칭은 Task3, 같은 사람 표본/충돌은 Task4, 원인별 재현은 Task5, 재사용/소유권/제품 판정 한계는 Task6이 담당한다. 얼굴 소유 선택의 새 알고리즘과 새 모델의 성능 개선은 이번 구현 완료 주장에 포함하지 않는다.

실행 권고는 **이 세션에서 순서대로 직접 구현(Native)**이다. 여섯 task가 같은 DTO와 지문을 차례로 소비하므로 구현자를 매번 바꾸는 이득이 적다. 실행 계획 검토 후 `superpowers:executing-plans`를 적용하고 마지막에 독립 리뷰를 받는다. 사용자 요청 없는 새 작업 세션 생성이나 W13 메시지 발송은 하지 않는다.

2026-10-13 실행 완료. 최신 origin/dev fetch 기준 47782953228861f4bdbdc135265d067c2a826b0e에서 feature/shared-reference-face-matching-20261013을 준비했다. core/replay 73개, 기존 core/Person 호환 27개 통과; 확대 회귀 617 passed/3 skipped(실제 모델 부팅 smoke 11개 제외). 독립 리뷰 Important 3건을 회귀 테스트 실패→수정→통과로 해결했다. 23개 참조/54개 저장 query 계산을 모델 호출 없이 재현했다. [실행·판단·미검증](/Users/jina/project/adlight/.codex/features/highlights/records/2026/10/13-w14-shared-reference-matching-implementation.md).
