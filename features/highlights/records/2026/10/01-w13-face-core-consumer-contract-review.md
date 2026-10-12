# W13이 본 W14 공통 얼굴 API와 안무 연결 조건 — 2026-10-01

## 판단

**파일 소유 경계는 수용한다.** W14가 독립 `clipper_face_core`의 초기 공개 API·관측 계약을 소유하고, W13은 안무의 main 선정·참조 멤버 매핑·crop 소비 정책을 맡는다. 공개 패키지는 앞으로 다른 플러그인도 쓸 수 있어야 하며 Dance/Person 이름으로 사용자를 제한하지 않는다. 같은 공통 Python 파일을 두 작업이 동시에 고치지 않는다. 이 문서는 W13의 **소비자 검토**이며, 미커밋 W14 API의 출시 승인이나 안무 이식 완료를 뜻하지 않는다.

읽은 상태는 W14 격리 worktree Python HEAD `47782953228861f4bdbdc135265d067c2a826b0e` 위의 **미커밋** `clipper_face_core`다. 읽은 공개 파일 SHA-256은 `__init__.py` `424bc88e4f6cd4de01a901d05633f529d7e0685636a3ba86900f3c70f25fa7c3`, `opencv_backend.py` `1d51c616e4feaa2711d10b47d72e9fd126b4f5771daa5de44684fcaf84178b3e`, `grouping.py` `911fc6bc4b923924c12c40f676b0a98fed7e3ea78ca60852f825f5b28077d1a2`다. 병렬 작업 중 바뀌면 다시 본다. W13 안무 `face_cluster.py` SHA-256은 `b60e37ee65ecf794f13e916181a026b9eac224fac613ada9cf8219d10e818904`다.

## 제안 계약과 현재 구현의 차이

| W14 인계에서 제안한 공통 경계 | 지금 공개 코드에서 확인한 것 | W13 연결 전 필요한 결정 |
|---|---|---|
| 원본 PTS/timebase·회전/표시 좌표를 가진 `FrameRef`; source `[start,end)` | 공개 `FrameRef`/`Track` 타입이 아직 없다. `FaceObservation`은 `time_sec: float`, `time_base="seconds"`, pixel bbox와 width/height를 갖는다. `FaceInterval`도 float 초다. | `frameIndex/fps` 파생값과 원본 PTS를 구분하는 versioned DTO를 합의한다. W13 탈락 장면 sidecar·향후 crop keyframe의 source 시각과 좌표계를 이 계약에 맞춘다. |
| 모든 얼굴 관측과 실패/불확실 상태 | `detect(frame)`는 검출된 얼굴 목록과 embedding 실패를 돌려준다. 빈 입력과 유효 프레임의 얼굴 미검출은 둘 다 빈 목록이며, OpenCV 예외·상위 단계 decode 실패의 구조화된 상태는 없다. `FaceObservation.failure`은 `none/alignment/embedding`만 표현한다. | 빈 검출·threshold 아래·decode/model 실패를 구분해 **관측 요약 또는 실패 이벤트**로 남기는 공개 방법을 정한다. W13의 `no_valid_face_candidate`와 `insufficient_track_samples`를 조용히 삭제하지 않는다. |
| 모델+정렬+정규화가 같은 embedding 공간, 캐시 재사용 범위 | backend의 `model_sha256`은 recognizer hash이고 `config_sha256`은 backend ID·detector threshold/NMS/top-k 문자열 hash다. 별도 `embeddingSpaceId`, 정렬/출력 정규화 버전, detector hash가 공개 관측에 모두 들어가지는 않는다. | 비교 가능성 fingerprint와 캐시 버전을 정한다. 기존 Dance 참조 이미지 centroid·threshold를 새 공간에 곧바로 재사용하지 않는다. |
| 공용 검출/embedding과 소비자별 정책 분리 | `OpenCvFaceBackend.detect()`는 전 얼굴 결과를 준다. `group_observations()`는 자체 threshold·대표 순위·group 정책을 가진다. | Dance는 ROI 최고 score 한 얼굴과 품질 상위 표본 평균·2개 미만 track drop·DBSCAN/계층 cluster·참조 매핑을 유지할지 각각 fixture로 비교한다. 공용 `group_observations()`를 안무에 자동 적용하지 않는다. |
| `{shotId, trackId}` 유일성과 컷 경계 | `FaceObservation`에 둘 다 있지만 grouping은 `track_id`만으로 모으므로 호출자가 전역 고유 ID를 보장해야 한다. | 공개 계약에 key 범위를 명시하거나 `(shotId,trackId)`로 그룹화한다. 컷을 넘어 bbox IoU만으로 다른 얼굴을 이어붙이지 않는 사례를 포함한다. |

OpenCV 모델을 **바이트로 로드**하는 방식은 양쪽에서 확인됐다. 기존 Dance는 `np.fromfile`/`cv2.imdecode`로 한글 참조 이미지 경로를 읽고, W14 backend는 모델 파일 bytes를 읽는다. 이것은 두 경로의 호환 가능성을 보여줄 뿐이며 Windows 실기 설치/실행을 검증한 것은 아니다. 현재 W14 backend의 얼굴 `quality` 계산은 Dance의 계산과 달라, 같은 SFace weight라도 표본 순위와 평균 embedding·멤버 매핑이 달라질 수 있다.

## W13의 구체적인 수용 검사

1. 고정 입력 한 ROI에서 기존 Dance 최고 검출 score 얼굴과 W14 전체 검출 중 최고 score 선택 결과를 비교한다. 얼굴 0개/2개, 부분 가림, 낮은 점수와 Windows 한글 경로를 넣는다. 기존 품질 순위·두 표본 조건·drop 사유가 유지되는지 따로 본다.
2. 같은 참조 사진과 main segment에서 기존과 새 embedding의 모델/정렬/정규화 지문이 같을 때만 거리·threshold를 대조한다. 다른 지문이면 centroid/cache를 새로 만들고 동일 입력 멤버별 precision·unknown 오배정률·coverage를 별도 채점한다.
3. 공통 관측의 원본 시간·좌표를 W13의 source-relative review 후보와 crop track으로 변환할 때 PTS/회전/clip trim 원점을 명시한다. 그룹 장면에서 한 얼굴 또는 한 인물로 단정하지 않는다.
4. Python 두 plugin 설치 marker와 source fingerprint, Mac/Windows 모델 파일·한글 경로·해시 검증을 확인한다. 현재 Dance 플러그인의 설치 상태가 Person 플러그인의 준비 상태를 뜻하지 않는다.

**현재 작업 순서:** W13은 공통 파일을 수정하지 않고 이 차이를 W14 공개 API 결정에 전달한다. 탈락 장면 보존의 첫 읽기 전용 범위는 공통 얼굴 이식 없이 독립적으로 설계한다. W14 API가 고정되고 사용자에게 안무 적용 범위를 선택받은 뒤 W13만 Dance adapter를 수정·검증한다. 실제 Dance adapter 호환 실행과 얼굴/identity 평가 입력은 아직 없다.

## W14에서 보낸 10/2 계약·평가 상태

W14 격리 공통 backend의 대표 선명도 계산만 변경된 후보 파일 SHA-256은 `419858898d3a463f51f5c7fc36f0499038eaa7eaa8a2b93f2147e19671b4331e`, config SHA-256은 `bca4dc55a1ac77e4afdf34f5eeb7c31a9bb484d01022a80d5ce0d270e2cf4710`이다. 이 변경은 `sharpness`와 대표 순위에 영향을 줄 수 있으므로 W13 기존 SFace centroid/quality/threshold와 같다고 간주하지 않는다. 공개 DTO·timebase·failure 상태·embedding 공간/캐시 지문은 위 표의 **미합의** 상태 그대로다. W13 파일 소유·소비자 compatibility test 및 merge 순서도 변경하지 않았다.

W14가 다른 음악 영상에서 기존 YuNet/SFace로 288프레임/931관측·128그룹을 시험했으나 14개 원본 진단 프레임의 명확 얼굴 23점만 채점했다. 검출 얼굴과 원본 의미상 장면 사이의 차이, 46개 빠른 컷/43클립, 전체 인물 그룹 정확도 미검증을 [W14 기록](02-w14-third-video-source-first-and-boundary-audit.md)에 남겼다. 동일 shot track 추가 연결 후보는 다른 드라마 오합침/과분리를 고치지 못해 제품과 공통 API에 적용하지 않았다. Dance adapter나 기존 참조 이미지 mapping/crop 경로에 이번 점수를 전용하지 않는다.

10/2 사용자 영상의 별도 20초 원본 우선 점검에서 기존 YuNet은 음식 소스를 얼굴로 검출하면서도 정상 순서의 5점 landmark를 반환했다. 기존 0.60 detector score/landmark 모양만으로 검출 유효성이나 Dance main 후보의 신뢰성을 보장하지 않는다. 같은 요리 출연자의 28×34px 와이드 얼굴과 223×309px 클로즈업 얼굴이 SFace cosine 0.251로 서로 다른 Person 그룹이 된 것도 확인했다. 이는 특정 두 관측의 사례이며 Dance ROI/main 정확도 수치로 옮기지 않는다. [원본 GT·3프레임 실행 상한·실제 결과](02-w14-user-source-cut-and-false-face-audit.md). **공용 API·backend·W13 adapter 수정은 없다.** W13 공개 DTO/실패 상태/embedding fingerprint 합의와 기존 Dance 참조 매핑·crop compatibility gate는 그대로 남는다.

같은 사용자 원본의 `shot_0244`에서는 두 clip의 0.2초 공백 양쪽이 서로 다른 사람의 얼굴이었다. 같은 shot/짧은 시간 공백만으로 track 또는 PersonGroup을 이어 붙이면 잘못된 인물 합침이 된다. W13의 main 단일 추적/안무 구간 소비도 이 Person 결과의 공백 메우기 규칙을 공통 API로 받아서는 안 된다. [원본 우선 반례](02-w14-user-source-cut-and-false-face-audit.md#같은-shot의-짧은-공백-반례-추가).

이어서 기존 YuNet raw score/상자 크기 조건을 W14 격리 평가로 151프레임 확인했다. 개발에서 얼굴104/104를 유지한 고정 조건도 재사용 검증에서 실제 큰 얼굴 1/63을 제거해 [제품 적용 gate에 실패](02-w14-large-low-score-detector-gate.md)했다. W13의 main/ROI 후보 선택에 이 점수 조건을 이식하지 않는다. 공용 detector 출력·관측 DTO·config/embedding 공간과 Dance adapter는 변경하지 않았고 기존 소유권·merge 순서·compatibility 검사 조건도 유지한다.
