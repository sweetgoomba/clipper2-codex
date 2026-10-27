# W14 공통 참조 매칭 구현 계획 — 2026-10-13

**후속 실행:** 이후 사용자가 “니 추천대로 진행해”로 Native 실행을 승인했다. 여섯 작업·독립 리뷰 수정·저장 특징 replay/호환 검증까지 수행했다. [구현 기록](13-w14-shared-reference-matching-implementation.md)을 현재 상태로 읽는다. 아래는 실행 전 계획 작성 당시 기록이다.

## 결정과 현재 단계

사용자는 공통 얼굴 매칭 설계의 쉬운 설명을 요청했고, 설명 후 `진행해줘ㅗ`라고 답했다. 이를 설계 방향 승인으로 기록하고 Superpowers `writing-plans`를 적용했다. [구현 계획](2026-10-13-shared-reference-face-matching.md)은 여섯 task·31개 확인 가능한 단계로 작성했다. 계획 자체의 검토 및 실행 방식 선택은 아직 받지 않았다. 권고 방식은 이 세션에서 순서대로 직접 구현(Native), 마지막 독립 리뷰다.

1. 기존 core 선택 복사, 공개 계약, OpenCV 선택 import 경계.
2. 참조 gallery 평균/L2 및 실패/중복/지문.
3. query별 독립 참조 비교·모호/미배정·잘못된 공간 거부.
4. 같은 사람 표본의 지지/충돌·중복 방지·근거 보존.
5. 저장 23개 reference/54개 query 특징으로 기존 결과 재현 및 제한된 구간 대조.
6. 플러그인 비종속 소비 예제, 기존 Person API 호환, W13 적용 계약 인계.

## 실제 확인

- `git worktree list --porcelain`으로 로컬 dev/Person donor/W13 두 checkout을 읽었다. Python 조사 HEAD는 `47782953228861f4bdbdc135265d067c2a826b0e`; remote fetch는 하지 않았으므로 최신 origin/dev라고 보증하지 않는다. 새 코드 작업 때 새 격리 checkout과 당시 최신 remote를 고정한다.
- donor core의 소스·pyproject·README·테스트 7개 SHA-256을 계획에 기록하고 파일과 다시 대조했다. donor 전체 workspace/lock/Person/evaluation을 복사하는 방식은 제외했다.
- 기존 core10개 테스트: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=clipper_face_core`, 기존 Python3.11 interpreter, `pytest clipper_face_core/tests --noconftest -p no:cacheprovider -q` → **10 passed in 0.19s**. 테스트 detector/recognizer는 가짜이며 모델 추론은 없다.
- child interpreter에서 numpy/cv2/torch/onnxruntime import를 차단해 SDK import → **exit0**. cv2/torch/onnxruntime를 차단해 현재 core import → **exit1, blocked optional ML import: cv2**. 실제 core 루트가 OpenCV backend를 즉시 import하는 문제를 확인했고 계획 Task1에서 해소한다. SDK에 ML을 추가하는 변경은 필요하지 않다.
- 기존 Person 테스트도 같은 interpreter에서 `PYTHONPATH=clipper_face_core:plugins/person_highlight:clipper_plugin_sdk`, `pytest plugins/person_highlight/tests --noconftest -p no:cacheprovider -q` → **17 passed in 0.45s**. 기존 core10+Person17 합계27개를 별도 명령 두 번으로 확인했다. 후속에는 새 core를 선두에 두고 같은 호환 기준을 재검증한다.
- plan의 task/step 수, placeholder 없음, spec/plan 링크, donor hash7개를 검사했다. 자기검토 중 task3 이전 matching import를 요구하던 순서 오류, 새 의존성 변경을 실패 테스트보다 먼저 하던 단계, 실제 얼굴 소유 GT와 legacy 선택 가정을 혼동할 수 있던 재현 표기를 바로잡았다.

## 구현 선택 근거와 한계

현재 안무 `_l2`는 `norm+1e-9`, 기존 Person core는 `vector/norm`이다. 같은 SFace weight라도 이 처리 버전을 명시해 공통 embedding space/cache/threshold를 혼용하지 않는다. detector hash/config는 별도 provenance로 남긴다.

첫 실데이터 재현은 **새 모델 호출 없이 기존 특징**으로 수행하도록 계획했다. legacy 선택 얼굴을 소비자의 확정 선택으로 가정하는 진단이며 얼굴 소유가 검증됐다는 뜻은 아니다. 거리0.60/격차0/support1은 기존 결과 재현용이지 새 제품 설정 채택이 아니다. 이후 같은 사람 표본의 충돌과 전역 군집 전후 결과를 분리한다.

이번 턴은 제품 수정·공통 API 구현·W13 adapter 연결·새 ML·모델 다운로드·환경 설치·branch/worktree 생성·commit/push/merge/deploy를 수행하지 않았다. 실제 품질 개선, 새 독립 얼굴/연결 정답, Windows, 플러그인별 venv 설치 및 Electron fingerprint 소비는 미검증이다. W13의 최신 YOLO26s 실험은 읽기 전용으로 확인했으며 W14에서 그 모델을 호출하거나 얼굴 매칭의 전제 모델로 삼지 않았다.

## 다음 단계

Superpowers `writing-plans`의 Execution Handoff에 따라 계획 검토와 실행 방식을 받은 뒤 `executing-plans`로 실제 구현한다. 안무 제품 adapter는 W13 소유로 유지한다. 계획 검토는 이번에 처음 작성한 구현 파일/검증 순서에 관한 것으로, 이미 승인된 공통화 방향을 다시 묻는 단계가 아니다.
