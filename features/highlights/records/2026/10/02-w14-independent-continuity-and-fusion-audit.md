# W14 원본 우선 연속 등장·얼굴/몸 연결 점검 — 2026-10-02

> **후속 사용자 결정:** 이 시험에 쓴 YOLOv8 pose 모델은 앞으로 제품에 사용할 수 없다. Dance에서 대체 모델로 변경 작업을 진행 중이며 모델은 아직 미정이다. 아래 YOLO 수치는 **과거 격리 진단의 기록**일 뿐 W14의 후보 선정·제품 채택 근거가 아니다. W14는 이 모델을 Person에 통합하거나 추가 추론하지 않는다. 몸 경로는 사용 가능한 모델이 별도로 정해지기 전까지 보류하고, 현재 얼굴 기반 경로의 품질 문제를 독립적으로 다룬다.

## 판정부터

**기존 pose 검출 시험의 3/3·14/14·동시 5/5는 몸 상자를 찾은 좁은 결과였다. 인물 카드에 같은 사람의 등장 구간을 제대로 연결했다는 뜻은 아니다.** 이번에는 원본을 먼저 보고 익명 인물·배경·동시 출연·대략적인 연속 등장 구간을 표시한 뒤, 기존 로컬 얼굴/몸 모델과 보수적 연결 규칙을 격리 채점했다. 유효한 정답 지점 71개 중 몸 상자가 65개, 얼굴 인물 그룹까지 모순 없이 연결된 지점은 **46개**였다. 흐린 배경 통행인의 5개 지점은 **0개** 연결됐다. 함께 나오는 사람이 모두 **각자의 그룹**을 받은 프레임도 **5/16개**뿐이다. **제품 적용 실패**이며 기존 완료 카드의 품질이 좋아진 것은 아니다.

원하는 결과의 기준은 **얼굴로 검출·분류된 인물을 배경이라는 이유로 자동 숨기지 않고**, 같은 사람이 재등장하면 한 익명 그룹으로 연결하며, 동시에 보이는 다른 사람은 섞지 않는 것이다. **몸 상자만으로는 누구인지 알 수 없으므로 몸만 잡힌 배경 인물의 별도 카드나 `확인 필요` 결과를 만들지 않는다.** 몸 추적은 같은 편집 shot 안에서 이미 얼굴로 연결된 사람을 따라가다가 얼굴이 잠깐 보이지 않는 시간의 등장 구간을 연장할 수 있는지 확인하는 *내부 단서*일 뿐이다. 그 shot 어디에도 신뢰할 얼굴 연결이 없거나 연결이 모호하면 Person 결과에 사용하지 않는다. 이 표본의 `D_WHITE_PASSER`는 몸이 4/5지점에서 검출됐지만 **인물 그룹으로 연결되거나 UI에 표시된 것이 아니다**. 아예 검출되지 않은 경우도 표시할 결과가 없으며 평가에서 미검출로 센다. 편집 컷/등장 경계와 원본 구간도 별도로 맞아야 한다.

## 원본 우선 입력과 실제 실행

평가 폴더: [독립 연속성 GT와 관측](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/). 처음 모델 출력 전에 [선정 JSON](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/candidate-selection.json) SHA `8f4ba2b495f03daa90efbbed9650457989f4ca7cce00d5ec4a02c35c43082363`, [원본 우선 GT](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/source-first-gt.json) SHA `d738c726689032faa7ef74705aa55790d2858cfdd7528b4ab5c6ce5d099e534a`, [계획](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/plan.json) SHA `e7148003e36460cf5aa89af4302cb3edd3fb1bbaa4cfb8b45c2f247394146219`를 고정했다. 세 창은 편집/배경/동시 출연을 보기 위해 고른 **목적 표본**으로, 무작위 모집단 표본은 아니다.

| 원본 창 | SHA-256 | 원본 우선 확인 대상 |
| --- | --- | --- |
| 사용자 방송 `[400,410)`초, 1280×720/30fps | `29101ea99c489fba8be54ec56f3470a92730485b905528e359c67a5b16ecdea3` | 검은 옷·회색 앞치마 인물의 단독→동시 출연, 컷 뒤 손/몸 일부. |
| 드라마 `[200,210)`초, 1920×960/약 23.976fps | `90e6a9fea7d3967773bbb841fb8d15013a2c6442c8a30bd592414d17e3bd6c69` | 붉은 옷 인물의 와이드→클로즈, 흐린 흰옷 배경 통행인. 전화기만 보이는 끝은 인물 미확정. |
| 음악 `[90,100)`초, 1920×1080/24fps | `708004f323ad2679f8793b639bfd58f3648c5367934849a313adc462dddd4b6a` | 다섯 명 동시 출연, 모자 쓴 단독 인물, 빠른 편집. 컷을 건넌 동일성은 판정하지 않음. |

GT는 세 창 합계 60프레임·명확한 사람 지점 101개, 원본 기준 대략 ±0.5초의 등장 interval, 동시 인물 `cannot-link`, 별도 unknown/판정 제외를 포함했다. 새 다운로드 없이 기존 YuNet SHA `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`, SFace SHA `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`, Dance의 `yolov8s-pose.pt` SHA `234314cd8baf62616791aceb9ea6ad5c19f26cf6c0d8f3a1bfce1e23b186cfb3`를 Mac 27 arm64 **CPU**에서 실행했다. OpenCV 4.13.0/Torch 2.11.0/Ultralytics 8.4.38, 얼굴 config SHA `bca4dc55a1ac77e4afdf34f5eeb7c31a9bb484d01022a80d5ce0d270e2cf4710`. [잠금 실행기](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/run_locked_detectors.py) SHA `38f0cbf894017e1e3a83bec7fbaefb1aa76df2c89c2d5d398600b2dad96748a3`; 정확히 60프레임, 180초/RSS 4GiB/출력 10MiB 상한. 모델 호출 전 입력/코드 hash dry run 통과.

실행 결과는 얼굴 96개, 몸 상자 117개, 8.595초, peak RSS 1,078,378,496B, 관측 출력 342,286B였다. [관측 JSON](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/locked-observations.json) SHA `52c1bcb7003dab5bbebbdab37a3ea63345c6d0ba63dd86f99587bfb9bf83a960`; [실행 로그](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/run-report.json) SHA `d861962461c0e1be3b11a6318dd20f6ac8b3538e4da36fa66509952c797c3cc2`. 디코더의 `mmco: unref short failure` 문구가 한 번 나왔으나 계획한 60프레임은 전부 읽어 관측을 작성했다.

사전 계획의 연결 규칙은 같은 shot에서 인접 몸 상자 1:1 IoU≥0.3 추적, **얼굴 중심이 정확히 한 몸 상자에만 있고 그 몸 상자에도 얼굴이 하나일 때만** 얼굴 그룹의 앵커로 쓰기, 한 몸 track에 상충하는 얼굴 그룹이 있으면 자동 배정을 보류하는 것이다. 컷 뒤 body ID는 잇지 않는다. 원본 GT 몸 지점과 box는 최대 대응 1:1로 채점하고, 배경/얼굴 없는 몸도 점수 분모에 넣었다. [연결·점수 코드](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/score_locked_fusion.py) SHA `9d369a4b99828169552f13bc686241887068402a8f78ba78152024e5c1a997e8`와 [첫 점수](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/locked-score.json) SHA `18c334588a079a388c2adb02c82a494c3f2ee7f3e2e1f1b863af60f990461e0c`를 보존했다.

## 라벨 품질 점검과 유효 부분 채점

첫 점수 뒤 [원본·GT·검출 상자 오버레이](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/locked-face-pose-gt-overlay.jpg)를 직접 보니 **음악 95.1–97.6초 6프레임의 몸 지점 30개를 정지 좌표로 복사**한 오류가 있었다. 사람들은 춤을 추며 이동했다. 따라서 그 부분의 원래 43/50 몸 검출·13/50 그룹 연결, `M95_2/3` 오합침·분리 주장은 **무효**다. 잠근 원본 GT를 사후 수정하지 않고 해당 6프레임 전체를 채점에서 제외했다. [사후 QC 스크립트](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/audit_locked_score.py) SHA `aa835c615c058f4971b3985c2e535753a587ab760b9fcd375300ac8e85d1551b`와 [유효 부분 감사 JSON](/Users/jina/project/adlight/.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-independent-continuity-gt/locked-score-audit.json) SHA `2f48f788547695c83e45531923546504051e1200a0f611abd677d03fb59b81d1`에 제외 프레임을 명시했다. **제외 판단과 재채점 지표는 예측을 본 뒤의 기술 감사**이며 새 블라인드 제품 선택 점수가 아니다. 음악의 처음 다섯 명 두 프레임과 모자/클로즈 단독 구간, 방송·드라마 구간은 유지했다.

| 유효 원본 지점/프레임 | 실제 결과 | 뜻 |
| --- | --- | --- |
| 명확한 사람 71지점 | 몸 상자 65/71; 기존 얼굴 그룹까지 단정 가능한 연결 **46/71** | 나머지 6 미검출, 6 몸만/얼굴 연결 없음, 13 서로 다른 얼굴 앵커 충돌. 검출과 인물 묶기는 별개다. |
| 흐린 배경 통행인 5지점 | 몸 4/5, **인물 그룹 0/5** | 몸 상자 4개는 누구인지 연결하지 못했으므로 사용자 결과로 만들 근거가 없다. 배경 얼굴 그룹을 찾아야 한다는 원래 요구는 충족하지 못했다. |
| 서로 다른 사람이 동시 출연하는 16프레임 | 몸 track이 모두 별도인 화면 12/16, 얼굴 그룹까지 모두 별도 배정된 화면 **5/16**: 방송 5/9, 드라마 0/5, 음악 첫 다섯 명 0/2 | 원래의 음악 5/5 상자 두 표본은 identity 성공이 아니었다. |
| 같은 사람 재등장 | `U_GRAY`는 얼굴 그룹 **2개**; `D_RED`는 유효 17/17지점에서 한 그룹; 음악 첫 다섯 명은 몸 track 5개로 분리되지만 그룹 배정 0/10지점 | face-only 과분리·몸→얼굴 연결 보류가 남는다. |
| 오합침 관측 | 유효 부분의 **배정된 46지점**에서는 다른 사람 오합침 0; GT 대응 몸 track의 인물 변경 0 | 25지점을 보류/놓친 보수적 규칙에서 나온 값이다. 전체 37분 오합침 0이나 실제 동시 인물 보장으로 해석하면 안 된다. |

유효 71지점에서 미배정 지점을 각각 singleton으로 벌점을 주면 pairwise TP/FP/FN `216/0/157`, precision/recall `1.000/0.579`, B-cubed precision/recall `1.000/0.581`이다. precision 1은 **25지점을 배정하지 않은 결과**이므로 누락과 함께 읽어야 한다. 배정된 46지점만 계산하면 pairwise recall `0.861`로 높아 보이지만 누락을 가리는 분모라 제품 판정에 쓰지 않는다. 이 점수는 반초 간격의 **관측 지점** 점수이지 연속 interval 전체의 recall/정확한 시작·끝 경계 점수가 아니다.

상충하는 얼굴 앵커가 달린 몸 track은 10개였다. 유효 GT 안에서는 한 몸 track의 서로 다른 얼굴 그룹이 **동일 실제 사람**인 경우가 확인된다(예: 드라마 흐린 통행인 `drama:person_002/003`, 음악 첫 다섯 명 각 2그룹). 따라서 얼굴 그룹이 둘이라는 이유로 그 몸을 영구히 버리면 누락이 커진다. 반대로 한 shot/몸 상자를 무조건 합치거나 얼굴 그룹의 유사도 문턱을 일괄 낮추면 앞선 방송·드라마의 실제 오합침 반례를 다시 만들 수 있다. 이번 자료에서 안전하게 확인한 것은 **shot 내부에 몸만 보이는 등장 근거가 생길 수 있다**는 점과 **현재 얼굴 그룹 연결 규칙으로는 충분하지 않다**는 점이다.

## 제품/공통 계약 판단과 남은 검증

이번 결과로 Person 제품의 default에 pose/fusion을 추가하거나 37분 프로젝트를 다시 만들지 않는다. 후속 내부 평가에서 선택적 `BodyObservation`을 쓴다면 source/model/config hash, frame/time base, bbox/score, shot-local track ID·version, `face_anchor=unique/ambiguous/none` 같은 **내부 판정 상태**만 기록한다. 얼굴/몸 중복 box 해소·한 얼굴↔한 몸 연결, 서로 다른 동시 인물 cannot-link, 같은 몸에서 분리된 얼굴 그룹을 해결하는 명시적 규칙이 필요하다. 얼굴 앵커가 하나로 검증된 같은 shot에 한해 기존 Person의 등장 구간 연장 여부를 시험한다. **얼굴 앵커 없는 몸 관측은 인물 카드·클립·`확인 필요` 그룹을 만들지 않는다.** `clipper_face_core` 공개 `FaceObservation`/SFace embedding/cache·0.55 문턱과 body ID를 혼합하지 않으며 기본 SDK 시작 경로에 PyTorch/Ultralytics를 강제하지 않는다. Scene↔PersonGroup 다대다·사용자 수정 overlay/경계/대표 override와 기존 Dance adapter는 그대로 둔다.

다음 정확도 gate는 **새 원본에서 위치가 이동하는 사람을 프레임별로 다시 라벨한 독립 구간**이다. 이전 음악 라벨의 복사 좌표를 재사용하지 않는다. 실제 컷과 ±0.5초보다 촘촘한 연속 등장 경계를 분리해 배경·단역 포함 interval recall, 다른 사람 false merge와 같은 사람 false split을 함께 본다. YOLO를 이용한 body 후보 비교는 중단한다. W13의 대체 모델이 정해지더라도 W14가 자동으로 공유하지 않는다. 몸 경로를 다시 검토하려면 **W14에서 사용 가능한 모델의 독립 입력·권리·Mac/Windows 실행·정확도**를 새 범위로 검증해야 한다. 이번에는 representative 품질, 37분 전체, 편집/ZIP 수정 보존, Windows/CUDA/패키징, W13 Dance 실제 compatibility, 사용자 체감 탐색 시간, 새 MP4 결과를 검증하지 않았다. 새 모델 다운로드/유료 API/Build5도 없다.

**모델 사용 결정 정정:** Dance와 Person은 **하나의 앱·하나의 SaaS 서비스 안의 기능 구분**이며, 앞서 W14용 별도 YOLO 사용권을 묻거나 기존 모델을 Person 통합 후보처럼 다룬 것은 잘못이다. 사용자가 **YOLO 모델은 사용할 수 없고 Dance에서 다른 모델로 변경 중이며 대체 모델은 미정**이라고 명시했다. 따라서 W14는 이 weight를 재사용하지 않는다. [W13의 도입 이력 조사](/Users/jina/project/adlight/.codex/features/highlights/records/2026/10/01-w13-yolo-license-provenance.md)와 본 문서의 수치는 과거 상태·실험 기록일 뿐 현재 모델 선택을 뜻하지 않는다.
