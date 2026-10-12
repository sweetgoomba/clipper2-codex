# W13 안무 비교 평가용 metadata 경로 준비 — 2026-10-01 KST

## 선택과 실제 범위

사용자는 공통 얼굴 모듈 검토와 별개로 **평가 도구 준비까지** 선택하고, 설명된 설계대로 진행하라고 확인했다. 이 승인은 실제 원본 영상·모델 실행, 모델 다운로드, 새 후보 비교, crop 렌더, UX 구현, 공통 얼굴 core 구현을 포함하지 않는다. W14→W13 공통 API·파일 소유 제안의 상호 확인은 여전히 남아 있다. 이번 변경은 W13 소유인 기존 Dance Python 경로에만 적용했다.

Python 저장소 원본 `dev`는 clean이었다. `git fetch origin dev` 후 `origin/dev`는 `47782953228861f4bdbdc135265d067c2a826b0e`로, 9/29 조사 HEAD와 같고 0/0이다. 새 브랜치 `feature/w13-dance-metadata-eval-20261001`와 격리 worktree `/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python`에서만 수정했다. 이 기록 작성 시 코드 변경은 **미커밋·미병합**이다. 원본 checkout과 다른 세션 worktree는 변경하지 않았다.

## 코드와 관측 계약

- `DancePipeline.run()`의 분석 부분을 `_analyze_core()`로 분리하고 기존 export 경로가 같은 분석 결과를 소비하게 했다. 새 `analyze_for_evaluation(input_video, reference_image_paths)`는 **로컬 참조 경로**를 직접 받아 같은 분석 판단을 수행하고 `dance_eval_v1` dict를 반환한다. 평가 경로는 참조 URL 다운로드, MP4/썸네일 export, 제품 `dance_meta_v1` 작성과 프로젝트 폴더 생성을 호출하지 않는다. 이 함수 자체는 실행 시 포즈·얼굴 모델을 사용하므로 입력과 실행 상한이 확정되기 전 실호출 금지다.
- 평가 dict에는 프레임별 시간·main track/bbox·group, raw main/group, smoothing 뒤 main/group, group 중첩으로 얼굴 분석 전에 제외한 main, 얼굴 분석 입력 main, 얼굴 표본 부족 등으로 제외한 main, 유지된 main의 cluster/person, 참조 후보 cosine 거리와 mapping 상태를 넣었다. bbox는 원본 분석 좌표이며 얼굴 이미지·임베딩 벡터를 직렬화하지 않는다. smoothing이 Segment를 변경하므로 raw 구간은 별도 객체로 보존한다.
- `SegmentFaceResult`에 시도한 표본·decode 성공·유효 embedding 후보·drop_reason을 추가했다. `face_detected`의 기존 의미와 2표본 이상 track 평균 규칙은 유지했다. `no_valid_face_candidate`는 **얼굴이 실제로 없었다는 단정이 아니다**. 현행 API에서 미검출·검출 threshold 미달·정렬/embedding 실패를 구별하지 못하므로 합쳐진 상태다. 유효 후보 1개면 `insufficient_track_samples`, decode가 모두 실패하면 `video_decode_failed`로 분리한다. raw detector 검출 수와 구체적인 실패 원인은 후속 관측 API 결정이 필요하다.
- 현재 프레임 시각은 현행 `fidx/fps`에서 나온다. source PTS 기반 정확도와 VFR 검증은 이 adapter가 해결한 것이 아니다. GT 대조 수치·실행 시간·메모리·모델 SHA·원본 SHA를 자동 계산하는 runner/CLI는 만들지 않았다. 이 값은 실제 평가 scope와 manifest가 고정된 뒤 별도 실행 계약에서 다룬다.

## 검증과 한계

- 기존 안무 단위 테스트 **27개 통과**(변경 전 기준선). 수정 후 안무 관련 테스트 **34개 통과**. 합성 `FrameRec`/가짜 얼굴·렌더러로 평가 경로의 무 export·무 다운로드, raw 경계 보존, group 제외 이유, 표본 부족과 decode 실패, 기존 제품 `dance_meta_v1`·clip/썸네일 경로를 확인했다. 실제 영상이나 모델은 사용하지 않았다.
- Python 비 e2e 전체 테스트는 **487 passed, 1 skipped, 5 errors**. 5개 오류는 안무 경로가 아닌 렌더링 테스트 fixture의 `ThreadingHTTPServer(127.0.0.1, 0)`가 이 sandbox에서 `PermissionError: [Errno 1] Operation not permitted`로 bind되지 못한 것이다. 따라서 전체 suite green으로 기록하지 않는다.
- 같은 suite에서 그 5개 테스트만 deselect한 재실행은 **487 passed, 1 skipped, 5 deselected**다. skip 1개는 단일 Python repo worktree 옆에 Angular checkout이 없어 수행하지 않은 상대경로 parity 테스트다. Python syntax compile과 `git diff --check`도 통과했다.
- 이번 단계에서 모델 weight 다운로드, 실제 ML, 외부 과금, Build5, 서버 기동, commit/push/merge/deploy는 하지 않았다. 공통 `clipper_face_core`, Electron venv fingerprint, Windows 실기는 변경·검증하지 않았다.

## 다음 결정

실제 metadata 비교 평가는 [manifest](../09/30-w13-experiment-manifest.yaml)의 원본 절대경로/hash·구간, 참조 이미지/hash·권한, GT 라벨, 모델 파일/hash·사용권, OS/device, 실행 SHA·반복·시간/자원 상한·출력 위치를 사용자와 확정한 뒤에만 수행한다. 첫 비교 변수는 main streak·pose score·tracker·face·mapping 중 **하나**만 고른다. 현재 동일 입력 전후 정확도나 성능 수치는 없다. W14 공통 API 계약은 별도 검토 대상으로 유지한다.
