# W14 기존 pose 모델의 얼굴 없는 구간 연속성 검증 — 2026-10-02

> **최신 사용자 결정:** 이 기록의 YOLOv8 pose 모델은 앞으로 사용할 수 없다. W13 Dance가 대체 모델로 변경 중이나 아직 모델을 정하지 않았다. 아래의 검출 수치는 과거 격리 시험 결과로만 보존하며 W14 Person 통합·추가 YOLO 추론·제품 채택 근거로 쓰지 않는다. 얼굴/몸 연동 검토는 사용 가능한 모델과 새 검증 범위가 정해질 때까지 보류한다.

> **후속 판정:** 아래 3/3·14/14·동시 5/5는 몸 검출/짧은 추적만의 성공이다. 사용자가 요구한 원본 우선 익명 인물·배경·동시 출연 연결을 [별도 30초 평가](02-w14-independent-continuity-and-fusion-audit.md)로 대조하니 유효 71지점 중 얼굴 그룹 연결 46, 배경 통행인 0/5, 동시 전원 별도 그룹 5/16화면이었다. 음악 원본 GT 일부 오류를 제외한 기술 감사 결과이며 **제품 품질 불합격**이다.

## 문제와 실행 전 잠금

사용자 37분 결과의 짧은 장면과 같은 사람 과분리를 개선하려면 먼저 **원본 컷**, **얼굴이 화면에 없는 같은 shot**, **다른 사람의 동시 등장**을 분리해야 한다. 앞선 원본 우선 라벨에서 요리 출연자의 얼굴 없는 `[1815.733,1818.533)`초와 남색 재킷 인물의 얼굴이 나중에 들어오는 `shot_0244`를 확인했다. 후자는 같은 shot의 인접 얼굴 clip 두 개가 실제로 서로 다른 사람인 반례다. 이 시험은 몸 검출이 얼굴 없는 구간의 증거가 될 수 있는지 확인하는 **격리·읽기 전용 기술 탐색**이다. 인물 동일성/ReID, 새 완료 카드, 제품 통합 실험이 아니다.

[실행 계획](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/plan.json) SHA-256 `144f8fe9c69a00dd79c2a544c46c6d68a3f7793b66c32e2a700c5cc388254888`와 [원본 우선 익명 몸 위치 GT](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/pose-source-first-gt.json) SHA-256 `2a7a2d217e2aa7ece5c056f5d083c8cb50f637db2a338ba1e0ae4f6c12eacd30`를 첫 pose 예측 전에 고정했다.

- 사용자 YouTube 원본 `/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_nestjs/.clipper_data/sources/youtube/0KQDhi7ddrk/source.mp4` SHA-256 `29101ea99c489fba8be54ec56f3470a92730485b905528e359c67a5b16ecdea3`, 1280×720/30fps. 별도 음악 원본 `/Users/jina/project/adlight/desktop/clipper_nestjs/.clipper_data/sources/youtube/dZs_cLHfnNA/source.mp4` SHA-256 `708004f323ad2679f8793b639bfd58f3648c5367934849a313adc462dddd4b6a`, 1920×1080/24fps.
- 기존 Dance 경로에서 이미 로컬에 있던 `/Users/jina/project/adlight/desktop/clipper_python/yolov8s-pose.pt` SHA-256 `234314cd8baf62616791aceb9ea6ad5c19f26cf6c0d8f3a1bfce1e23b186cfb3`. 새 모델 다운로드 없음. 기존 venv의 Ultralytics 8.4.38/PyTorch 2.11.0/OpenCV 4.13.0, macOS 27 arm64 **CPU**. `imgsz=640`, `conf=0.25`, pose box/keypoint 관측만; 사람 임베딩·body ReID 없음.
- 원본 프레임 7개의 수동 위치를 먼저 표시했다: 잘린 머리/몸 3점, 무대 전경 4명, 작은 배경 4명, 음악의 동시 5명씩 두 프레임. 부분만 보이는 왼쪽 가장자리 2점은 판정 불확실로 별도 기록했다. 몸 중심점을 포함하는 서로 다른 box 하나씩만 대응한다. 원본 접촉 시트 SHA-256 `804d668b3f14a3fd9c7e450482912592710dec3783970a5a633e6009977bd221`.
- Gate: 잘린 몸 3점 중 2점 이상(남색 인물 적어도 1점), 음악 14초의 동시 5명 중 4명 이상이 서로 다른 box에 대응해야 연속 표본으로 간다. 1차 7프레임/120초/RSS4GiB/출력1MiB, 통과 시 2차 정확한 106프레임/600초/RSS4GiB/출력20MiB. 출력은 `desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/`에만 기록하고 기존 MP4/JSON/편집은 읽기 전용으로 둔다.

처음 실행 계획 SHA `a1447037aca94bfdebdb962467e550077171491893762539b065fe4a8efe91eb`의 [runner](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/run_existing_pose.py)가 GT JSON까지 영상으로 열어 첫 호출이 **`.predict()` 전에 실패**했다. 이 실패를 숨기지 않는다. source role 필터를 `source_user/source_music`으로 고치고 Ultralytics 설정 경로를 평가 폴더로 제한한 뒤, runner SHA `caa9906833a7144189e0b886197cb6efe4ce20de952d3c2e1678c20b83098f94`로 계획을 재잠갔다. 수정 뒤 dry run을 통과하고 처음 pose 예측을 했다.

## 실제 실행과 원본 대조

| 확인 | 실제 결과 | 해석 |
| --- | --- | --- |
| 1차 pose | 7프레임, 25상자, 0.605초, peak RSS 637,140,992B, 출력 6,154B. [실행 로그](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/stage1-run-report.json), [상자](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/stage1-pose.json) SHA `04a4e4f744c11080221766eab76545abb225bba52e36929f8b5ac242edf4f3f0` | 사전 상한 내. |
| 잘린 얼굴/몸 | 남색 재킷 2/2 시점, 요리 출연자 1/1 시점의 몸 위치 포함. 1825.4초 전경 4/4. | pose는 얼굴 없는 **같은 shot 내 등장 근거**의 후보가 된다. |
| 동시 출연 | 음악 14.0초 5/5, 16.917초 5/5가 각각 서로 다른 상자에 포함. 원본 overlay도 확인. | 이 두 정지 표본에서 동시 인물을 구별했으나 identity 보장은 아니다. |
| 작은 배경 | 방송 무대 1825.4초 배경 4점 중 **1점만** pose box에 포함. 같은 프레임 저장 YuNet 얼굴 4개 중 2개의 얼굴 중심에는 대응 pose box가 없다. | pose 단독으로 YuNet을 대체하면 배경/단역 누락 위험이 있다. 검출된 모든 그룹 기본 표시 정책도 그대로 필요하다. |
| 2차 pose | 사전 gate 통과 뒤 106프레임, 336상자, 6.77초, peak RSS 600,965,120B, 출력 81,811B. [실행 로그](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/stage2-run-report.json), [상자](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/stage2-pose.json) SHA `b86f9ac2be5d1a56ad1eb06dab13ebe1df2874a7bb540260c7b91a7f3ead784e` | 5fps 인접 box 연속성만 확인했다. |

[1차 점수](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/stage1-score.json) SHA `942b237961b9def07b0ff3e4e2901857289b7a7101873d0fe530dd75b75aff2b`와 [원본 위 상자 그림](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/stage1-pose-overlay.jpg) SHA `ab50e975ccea66a151371558ace540e402b05f92d0490c449db513ca1deadb75`를 함께 확인했다. 2차 [연속성 요약](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/stage2-summary.json)은 얼굴이 없는 요리 출연자 14연속 표본에서 상자 **14/14**, 인접 13쌍 IoU 최소 **0.893**, 중앙 **0.952**였다. 무대의 편집 컷 전 14표본은 상자 5개가 모두 인접 13쌍에서 IoU≥0.3으로 따로 이어졌다. 음악 첫 8표본의 5개 상자도 인접 7쌍에서 각각 이어졌다. 이 값은 **상자 안정성 대리 지표**이지 사람 ID 정답률이나 장면 경계 정답률이 아니다. 54786→54792의 5→2 변화처럼 편집 컷을 가로질러 묶지 않았다.

이미 저장된 37분 5fps 얼굴 manifest SHA `ea007b7745c139d6e36efedc1fb297a924eb4ba5f3aff5966f13b865817f9230`를 pose 출력과 **사후 탐색**으로 맞췄다. 81개 사용자 프레임의 저장 얼굴 93개 중, 얼굴 중심을 포함하는 몸 상자가 0개인 얼굴 **12개**, 1개 **80개**, 2개 이상 **1개**였다. 얼굴 관측이 하나도 없는데 몸 상자는 있는 표본도 **27개**였다. [사후 대응 목록](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/posthoc-stage2-face-body-candidates.json). 646.4초 남색 인물의 얼굴은 몸 상자 **두 개**에 들어가며 645.2초에는 같은 몸을 크게 겹쳐 잡은 box도 보인다. 단순 얼굴 중심 포함이나 최고 점수 1개 선택만으로 fusion하면 중복/오배정 위험이 있다. 이 93개 수치는 원본 사람이 전부 라벨된 검출 recall이 아니다.

원본 우선 20초 컷 GT를 다시 대조하면 요리 출연자의 몸만 보이는 원본 `[54472,54556)`프레임은 **그 shot 전체에서 얼굴이 보이지 않는다**. 따라서 14/14 몸 상자만으로 이 구간을 기존 `person_257`이나 `person_093`에 자동 배정할 수 없다. 이 몸 상자는 **검출기 진단값일 뿐 Person 카드·확인 필요 그룹의 후보가 아니다.** 반면 남색 재킷과 왼쪽 가장자리 **다른 사람**이 같은 `shot_0244`에 있는 645.2→646.4초 7표본의 [사후 경로 탐색](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-existing-pose-continuity/posthoc-navy-edge-paths.json)에서는 두 몸 경로가 서로 다른 terminal box로 이어지고 남색 얼굴은 자신의 경로 상자 안에 있었다. 그러나 처음의 남색 몸 중복 상자 두 개가 도중에 한 경로로 수렴한다. 이 탐색은 사전 고정된 다중 추적기 성능 시험이 아니며 한 shot 사례에만 해당한다.

## 설계 판정과 다음 제품 gate

**기술 가능성은 좁게 확인, 제품 채택은 보류.** 몸 상자는 얼굴이 잘려도 같은 shot에서 사람의 등장 근거가 될 수 있다. 그 shot에 연결 가능한 얼굴 앵커가 **전혀 없으면 Person의 인물 그룹이나 등장 구간을 만들 수 없다.** 작은 배경 인물 3/4 누락, 큰 중복 상자, 얼굴↔몸 모호성, 컷 이후 요리 출연자 두 얼굴의 낮은 SFace 유사도 **0.251** 문제도 해결하지 않는다. 기존 5fps 결과의 3초 미만 clip **601개 중 539개(89.7%)는 원본 shot 자체가 3초 미만**이라는 앞선 전체 컷 재계산이 있다. 그러므로 같은 shot 안의 몸 추적을 완벽하게 만들어도 그 539개를 3초 이상의 단일 연속 source 구간으로 바꿀 수 없다. 이는 clip 수 감소 예측이 아닌 물리적 길이 상한이다. 몸 추적만 넣어 Person 5/6/8/13 과분리나 컷을 가로지르는 동일인 grouping이 고쳐진다고 말할 수 없다.

| 후속 접근 | 이점 | 한계/선행 조건 |
| --- | --- | --- |
| A. 현행 face-only + 사용자 수정 | 현 설치 경로와 권리/의존성 변화 없음 | 머리가 잘린 구간 복구 불가, 컷 사이 과분리·오검출은 남음. |
| B. **같은 shot 내 body box 연속성 + 얼굴 앵커** | 남색 재킷 사례처럼 그 shot 안에 얼굴이 다시 보이면 몸만 보이던 시간의 등장 interval 후보를 제시할 수 있음 | 현재 YOLO 시험 모델은 사용 불가. 대체 모델 미정으로 이 경로는 보류. 향후 별도 모델을 검토한다면, shot 전체에 연결 가능한 얼굴이 없을 때 Person 결과를 만들지 않고 몸 상자 중복·얼굴↔몸 1:1/모호 상태·동시 출연 cannot-link, 컷 정지, 배경 얼굴 유지, 독립 GT를 검증해야 함. |
| C. 컷 간 body appearance/ReID + 얼굴 fusion | 작은/큰 얼굴·재등장 과분리 개선 가능성 | 첫 MVP 밖. 별도 모델/weight 권리·임베딩 공간·검증 영상·false merge 상한·UX 계약 필요. 이번 결과는 성능 근거가 아님. |

향후 사용 가능한 모델로 B를 다시 검토할 경우 `BodyObservation`은 **플러그인별 선택 입력**으로 두고 source/model/config hash, frame index/time base, pixel/normalized box, confidence, track ID/version, 실패/모호 상태를 기록한다. 공용 `clipper_face_core`의 얼굴 `FaceObservation` DTO·SFace embedding/cache/0.55 문턱에 몸 관측 ID를 섞지 않는다. shot-local 다중 몸 추적은 1:1로 하고 중복 상자·서로 다른 동시 인물 충돌을 먼저 표시한다. 얼굴↔몸 관계가 하나로 검증될 때만 얼굴 앵커 그룹의 **같은 shot interval**을 연장한다. 얼굴 앵커가 없거나 매칭이 모호한 몸은 **내부 진단 상태로만** 남기고 Person 카드·클립·확인 필요 그룹을 만들지 않는다. 컷 간 연결/장면 합침/MP4 이어붙이기, 얼굴=화자, 실명 식별은 하지 않는다. 현재 Scene↔PersonGroup 다대다와 사용자 수정 overlay/revision을 존중하고 원본/사용자 편집 clip 경계를 덮어쓰지 않는다. 기본 SDK 시작 경로에 별도 몸 모델/runtime을 강제하지 않고 Person 선택 venv/모델 준비와 W13 Dance 기존 main/ROI/mapping/crop을 독립시킨다.

제품 변경 전에는 (1) **모든 인물·몸만 보임·배경·동시 출연·실제 컷/원하는 등장 구간**을 원본 우선 라벨한 독립 짧은 영상, (2) 배경 포함 인물/interval recall과 다른 사람 false merge·같은 사람 false split의 동시 gate, (3) 중복 pose 상자와 얼굴↔몸 모호/미매칭/1:1 정합 회귀, (4) 사용자 병합·재배정·대표 이미지·경계/제외 수정 보존 및 clip/export 중복 검증, (5) Mac/Windows CPU·CUDA/패키징 확인이 필요하다. **검출된 얼굴 기반 인물 그룹**의 기본 표시 정책은 유지하지만, 몸 상자만의 그룹은 만들지 않는다. 이 기록에는 전체 37분의 정답·배경 interval recall·pairwise/B-cubed·제품 속도·Windows 실기·새 MP4 결과가 없다.

당시 기술 탐색에 사용한 [Ultralytics YOLOv8 문서](https://docs.ultralytics.com/models/yolov8)는 `yolov8s-pose.pt`를 pose 모델로 열거하고, [예측 문서](https://docs.ultralytics.com/modes/predict)는 CPU/CUDA 장치 선택을 설명한다. 이번에는 Mac CPU만 실제 확인했고 Windows/CUDA 실기와 Dance compatibility는 미검증이다. **사용자 결정에 따라 이 모델은 후속 사용 대상에서 제외된다.** Dance/Person은 같은 앱·SaaS의 기능 구분이므로 플러그인별 별도 허가 문제로 설명한 과거 문구도 철회한다. [W13 도입 이력](../10/01-w13-yolo-license-provenance.md)은 과거 경위일 뿐 W14의 모델 선택이 아니다. 이 시험으로 W14 공통 API 초기 소유/W13 Dance adapter 소비 소유 및 `W14 DTO 고정 → W13 fixture → 병합` 순서를 변경하지 않는다. 기존 0.60 YuNet/0.55 SFace, 카드·편집·모든 그룹 표시·MP4/ZIP, 완료 프로젝트는 수정하지 않았다.
