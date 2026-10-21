# W14 방향 전환 — 안무에 필요한 공통 얼굴 매칭 우선

2026-10-13 KST. 사용자 결정과 로컬 코드/작업 기록을 정리했다. 이 문서는 새 구현 스펙이나 새 모델 평가 결과가 아니다. 이번 작업은 코드·Git·기존 기록 읽기와 인계 문서 갱신만 수행했다.

## 사용자 결정

인물 하이라이트 자체 기능 개발과 종전의 여러 품질 실험을 우선 멈춘다. W13 안무 하이라이트의 품질 개선이 시급하므로 W14는 **미리 선택한 멤버별 참조 얼굴과 영상 속 인물을 정확히 매칭하는 공통 기능**에 집중한다. 인물 하이라이트는 추후 재개한다. 안무·인물·대사 3개 플러그인을 제공한다는 장기 목표와, 얼굴 기능을 어느 플러그인에서든 재사용할 독립 모듈로 만든다는 최초 요구는 유지한다.

## 지금까지 한 작업과 보존 상태

| 작업 | 실제 상태 | 이번 결정 이후 |
|---|---|---|
| Person MVP | 소스 선택→홈 큐→결과, 인물/클립/원본 3열 UI, 수정·개별 MP4/인물 ZIP의 시험용 코드가 격리 worktree에 있음 | 현재 코드와 사용자 결과/편집을 보존, 자체 기능 확장 보류 |
| 장면/결과 개선 | 중복 구간·긴 원본 편집 타임라인·병합/대표 수정 보존 등을 다룸. 자동 인물 품질은 사용자 불합격 | 새 공통 매칭 작업의 성공 지표에 클립 길이/UI/export를 섞지 않음 |
| YuNet/SFace | Person 영상의 검출·동일인 묶기·대표 품질, sampling/threshold 등을 평가 | 재현 자료로 보존. Dance 참조 멤버 매칭 정확도를 검증한 결과로 전용하지 않음 |
| ArcFace ResNet100 ONNX | SFace 대체 특징 추출을 격리 시험. 방송 독립 표본은 개선 없음, 드라마 일부 표본은 개선. 제품 미채택 | 해당 모델·전처리·기준·영상 범위에 한정한 증거로 보존 |
| 몸 경로 | YOLOv8s Pose 격리 진단/연결 평가. D-FINE-S/N·RF-DETR-S/N·RTMDet-tiny는 조사만 함 | W14의 새 우선순위에서 보류. W13의 pose 선택을 대신하지 않음 |
| 공통 얼굴 패키지 | 아래와 같은 0.1.0 시험용 구현. Person만 소비, Dance 미이식 | 필요한 부분을 확인해 참조 매칭 첫 소비 사례에 집중 |

기존 작업 위치: `/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/` 아래 Python/Nest/Angular/Electron 형제 저장소. 이번 정리에서 삭제·리셋·브랜치 이동·서버 재시작·기존 결과 재저장을 하지 않았다.

## 공통 모듈 구현을 코드로 확인한 결과

W14 Python branch `feature/person-highlight-mvp-20261001`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e` 위에 `clipper_face_core/`, `plugins/person_highlight/`, `evaluation/`가 untracked이고 workspace `pyproject.toml`·`uv.lock`이 수정돼 있다. 로컬 원본 Python `dev`의 같은 HEAD에는 `clipper_face_core`와 Person 플러그인이 없다. 이 점검에서 원격 fetch는 하지 않았다.

| 범위 | 실제 코드 근거 | 판정 |
|---|---|---|
| 독립 패키지 | `clipper_face_core/pyproject.toml`: `clipper-face-core` 0.1.0, workspace 등록 | 시험용 패키지 분리 구현됨, 미커밋/로컬 dev 미반영 |
| 검출·정렬·특징 | `OpenCvFaceBackend.detect()`가 모든 YuNet 검출과 SFace 정렬·L2 특징을 반환, 특징 실패 관측 보존 | 구현됨 |
| 품질·그룹 | `FaceObservation`, `FaceGroup`, `FaceInterval`, `group_observations`, `rank_representatives` 공개 | 익명 grouping과 대표 후보 초안 있음 |
| 모델 지문 | 두 local weight SHA 검증, 관측의 recognizer/config SHA, 혼합 공간 거부 | 일부 구현. 전체 전처리/정렬·검출기 지문/실패/PTS 계약은 미완료 |
| Person 소비 | `plugins/person_highlight/.../app.py`, `analysis.py`가 공통 API를 import | 시험판에서 연결됨 |
| Dance 소비 | 로컬 dev 및 W13 두 worktree의 Dance가 기존 `FaceClusterService`를 생성 | 공통 패키지로 미이식 |
| 참조 사진→멤버 매칭 | W13 `services/pipeline.py`의 `_build_reference_embeddings`, `_map_cluster_to_member_name`에 있음 | 공통 참조 매칭 API로 분리되지 않음 |
| 실행 환경 | Person이 공통 패키지를 선택 의존성으로 설치. 패키지 자체는 numpy/OpenCV 의존, 공개 import가 OpenCV backend도 import | 플러그인 범위의 분리는 있으나 backend 교체/순수 계약 import의 경계는 추가 설계 필요 |

따라서 **공통 모듈의 기반은 구현했지만, 사용자가 요구한 안무/인물의 공통 얼굴 매칭 기능 완성·양쪽 실제 사용은 아직 아니다.** 같은 YuNet/SFace 모델 파일을 공유하는 것과 공통 기능 코드를 소비하는 것은 별도 상태다.

코드 근거:

- [공통 패키지 README](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/clipper_face_core/README.md)
- [공개 API](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/clipper_face_core/clipper_face_core/__init__.py)
- [실제 backend](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/clipper_face_core/clipper_face_core/opencv_backend.py)
- [W13 참조 매칭](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pipeline.py:263)
- [10/1 W13 소비자 검토](01-w13-face-core-consumer-contract-review.md)

## 새 담당 경계와 다음 설계의 기준

W14는 플러그인과 무관한 얼굴 검출·정렬·특징 비교·참조 인물 매칭의 품질 및 공개 계약을 맡는다. 사용자 참조 사진으로 부여한 ID/라벨을 다루며 실명 자동 식별을 뜻하지 않는다. 공통 입력/출력을 Dance Segment/멤버 UI/작업 큐 타입에 종속시키지 않는다. 익명 인물 grouping 소비는 Person 재개 시 다시 연결한다.

W13은 메인/복수 메인 선택, 사람 추적, 구간 경계와 군무/제외 판정, crop, Dance adapter와 제품 통합을 맡는다. [10/13 안무 카드](/Users/jina/project/adlight/.codex/handoff/tasks/dance-highlight.md)의 사용자 범위 정정도 얼굴 매칭 후속을 W14에 맡긴다. 10/1 W13은 공통 파일 초기 소유=W14, Dance 소비=W13 경계를 이미 수용했다. 공통 비교 기능을 개선하더라도 메인 사람을 고르는 정책이나 안무 출력 정책을 공통 모듈에 넣지 않는다.

다음 얼굴 평가에서는 동일 안무 source와 선택된 참조 사진을 고정하고 다음 두 조건을 구분한다.

1. 원본에서 확인한 **올바른 대상 인물의 얼굴/구간**을 입력해 얼굴 검출·비교·참조 배정 자체의 품질을 확인한다.
2. 고정된 W13 실제 ROI/track/구간을 입력해 얼굴 선택/가림/다른 인물 혼입을 포함한 연결 결과를 확인한다. 메인/track 오류가 섞이면 원인을 따로 기록한다.

멤버별 올바른 매칭, 다른 멤버 오배정, 미배정/판단 보류, 얼굴 미검출과 품질, 처리 시간/자원을 별도로 측정한다. 매칭률만 높이려고 모호한 얼굴을 강제 배정하지 않는다. 기존 Person의 pairwise/B-cubed 점수를 안무 멤버 매칭률로 바꾸어 부르지 않는다. 정확한 입력 경로/hash·참조 집합·정답·모델/전처리·실행 범위/상한은 다음 구체 설계에서 확정한다.

파일/병합 순서는 W14 공통 계약·고정 fixture → W13 adapter 소비/동일 입력 호환 → 통합 검증 순서를 따른다. 새 구현 전 대상 repo의 최신 원격 상태와 기존 작업 의존성을 확인해 격리하며, 현재 W13 파일을 이 세션에서 수정하지 않는다. 새 세션 생성이나 다른 세션에 메시지 전송은 이번 정리에서 하지 않았다.

## 이번 실제 검증과 남은 항목

확인한 것: 공통 패키지 파일·공개 함수·workspace/Person import, W13 두 worktree와 로컬 dev의 기존 Dance 경로, 참조 매칭 위치, W14 Git 상태, W13 소유권 수용/10월 13일 범위 정정 기록.

실행하지 않은 것: 새 얼굴/몸 모델 추론·다운로드·성능 시험·앱 재분석·제품 코드 수정·커밋/병합/배포. 문서 갱신 외 제품 상태는 변경하지 않았다. 패키지 설치/실행·Windows·공통 API 이식 후 정확도는 이번에 검증하지 않았다.

남은 핵심은 **안무 참조 매칭 기준선과 오류별 평가를 고정하고, 필요한 공통 계약을 보완해 W13이 실제로 소비하도록 만드는 것**이다. 이는 구현이 완료됐다는 주장이 아니라 새 우선순위에 따른 다음 작업이다.
