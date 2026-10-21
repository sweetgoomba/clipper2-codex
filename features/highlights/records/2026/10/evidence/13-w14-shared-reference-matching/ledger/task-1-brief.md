## Task 1: 격리 패키지, 공개 타입, 선택 backend 경계

**Files:** 위 donor 7개 → 같은 경로로 Create; Create `clipper_face_core/clipper_face_core/{contracts,backend_types}.py`, `clipper_face_core/tests/{test_contracts,test_import_boundary}.py`; Modify `pyproject.toml`, `uv.lock`, `clipper_face_core/{pyproject.toml,README.md}`, core `__init__.py`, `opencv_backend.py`.

**Interfaces:** 위 DTO 및 `EmbeddingSpace.fingerprint`, `SourceEvidence.bbox_normalized`. 기존 `FaceObservation`, `FaceDetection`, `ModelFiles`, `OpenCvFaceBackend`, grouping/대표 함수 이름과 기존 생성자 유지.

- [ ] **1.** 실행 전 최신 remote/base·새 checkout·donor hash를 기록하고 allowlist만 가져온다. 이 단계에서 새 API/의존성 변경을 구현하지 않고 기존 10개 테스트의 재현 기준을 확보한다.
- [ ] **2.** `test_import_boundary.py`에서 child interpreter의 import hook으로 SDK는 numpy/cv2/torch/onnxruntime, core 타입은 cv2/torch/onnxruntime를 차단한 import를 각각 검사한다. 명시적 backend 사용은 OpenCV가 없으면 `Install clipper-face-core[opencv] in the consuming plugin environment` 안내로 실패하고 다운로드하지 않아야 한다. 기존 `from clipper_face_core import FaceDetection, ModelFiles`는 OpenCV 없이 성공해야 한다. 이후 Task 3/4에서 완성한 공개 matching/consensus import도 이 검사에 추가한다.
- [ ] **3.** `test_contracts.py`에 아래 assertion을 작성하고 실행해 새 타입 부재/기존 eager import로 실패하는지 확인한다.

```python
assert space.fingerprint != replace(space, normalization_version="other").fingerprint
assert source.bbox_normalized == (0.1, 0.2, 0.5, 0.8)  # 100x100, bbox=(10,20,50,80)
assert derived_source.time_kind == "derived_seconds" and derived_source.pts is None
with pytest.raises(ValueError): replace(pts_source, time_base=(1, 0))
with pytest.raises(ValueError): replace(space, recognizer_sha256="")
with pytest.raises(ValueError): MatchPolicy(0.60, 0.0, True)
```

- [ ] **4.** DTO/검증/지문을 구현한다. ModelFiles/FaceDetection을 `backend_types.py`로 옮기고 이전 `opencv_backend` import 경로에서도 재export한다. `__getattr__`로 root의 `OpenCvFaceBackend` 접근만 지연한다. detection/grouping 알고리즘은 유지한다. workspace에 core 하나만 추가하고 버전 0.2.0, numpy 기본 의존성, `[project.optional-dependencies].opencv`의 OpenCV 의존성으로 설정한다. 기존 Person은 자체 OpenCV 의존성이 있어 donor Person 파일을 바꾸지 않는다. lock은 기존 의존성 변경을 최소화해 생성하고 unrelated upgrade가 있으면 해결 후 진행한다.
- [ ] **5.** `python -m pytest clipper_face_core/tests/test_contracts.py clipper_face_core/tests/test_import_boundary.py clipper_face_core/tests/test_grouping.py clipper_face_core/tests/test_opencv_backend.py -q` → 모두 PASS. SDK pyproject의 필수 의존성에 core/ML이 추가되지 않았는지 확인한다.

