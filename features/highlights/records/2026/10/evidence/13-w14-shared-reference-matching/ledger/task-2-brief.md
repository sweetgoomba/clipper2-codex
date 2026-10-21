## Task 2: 참조 갤러리와 기존 평균 재현

**Files:** Create `clipper_face_core/clipper_face_core/gallery.py`, `clipper_face_core/tests/test_gallery.py`; Modify core `__init__.py`.

**Interfaces:** `build_gallery(samples: Sequence[ReferenceSample], *, space: EmbeddingSpace) -> ReferenceGallery`. 무효 참조는 failures에 보존; 섞인 공간·상충 sample ID·유효 entry 0개는 `GalleryBuildError(ValueError)`(필드 `reason`, `failures`)로 실패.

- [ ] **1.** 실패 테스트를 작성한다. `test_mean_matches_existing_dance`는 float32 입력을 받은 기존 계산 `avg=np.mean(np.stack(vectors),axis=0); avg/(float(np.linalg.norm(avg))+1e-9)`와 array equality를 검사한다. 입력 norm이 1에서 1e-5 이상 벗어나면 실패 표본으로 남기며 몰래 재정규화하지 않는다. 평균 영벡터/비유한 값은 해당 entry 실패다.
- [ ] **2.** `test_duplicate_sample_id_is_not_an_extra_vote`는 동일 sample의 재전달로 centroid/used sample 수가 변하지 않음을, `test_conflicting_sample_id_rejected`는 같은 ID의 다른 참조/벡터가 오류임을 확인한다. `test_gallery_owns_immutable_vectors`는 생성 후 caller 원본 배열 변경으로 centroid/hash가 바뀌지 않음을 확인한다. 다른 space/실패 일부/실패 전부/중간 entry의 zero mean도 검사한다.
- [ ] **3.** `python -m pytest clipper_face_core/tests/test_gallery.py -q` → 구현 전 FAIL 확인.
- [ ] **4.** sample 순서와 실패 상태를 보존하고 valid sample을 reference ID별 평균/L2로 집계한다. 유효한 첫 등장 reference ID 순서를 entry 저장 순서로 쓰며 결과 순위 정렬은 Task 3이 맡는다. 배열을 독립 read-only 복사한다. aggregation version은 `mean_f32_l2_eps1e-9_v1`이다.
- [ ] **5.** 같은 명령 → PASS. 실패를 성공 entry로 바꾸거나 데이터에서 삭제하지 않았는지 확인한다.

