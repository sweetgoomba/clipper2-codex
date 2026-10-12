# W14 사용자 영상 20초 원본 우선 컷·가짜 얼굴 점검 — 2026-10-02

## 범위·잠금

사용자가 완료된 37분 인물 하이라이트 결과의 짧은 장면·동일인 분리·저품질 대표 얼굴을 지적한 상태다. 이번에는 그 원본에서 이전 평가 창과 30초 이상 떨어진 `[1810,1830)`초, 총 **20초**를 원본 SHA 기반 난수로 먼저 골랐다. 원본 영상은 기존 로컬 파일 SHA-256 `29101ea99c489fba8be54ec56f3470a92730485b905528e359c67a5b16ecdea3`, 1280×720/30fps다. 기존 사용자 결과와 별도로 만든 5fps 시험 manifest SHA-256 `ea007b7745c139d6e36efedc1fb297a924eb4ba5f3aff5966f13b865817f9230`를 읽기만 했다.

- [선정](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-boundary-source-first/selection.json) SHA-256 `e61161b1a2f0251781d76e38fa0209e88e476eb8c7cda1d30584616394d36b5d`.
- **저장된 얼굴/클립 결과를 열기 전에** 5fps 원본 접촉 시트와 30fps 인접 프레임 쌍을 보고 [익명 컷·인물 GT](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-boundary-source-first/source-first-shot-appearance-gt.json)를 고정했다. SHA-256 `31c39be4cbfef64619da07276db9fcf4bd9a8cfc7bf42c3a4bc2042d904b677c`. 8개 shot, 새 shot의 첫 원본 프레임 7곳, 요리 출연자 `P_COOK`/남색 정장 `P_NAVY` 등의 얼굴/몸만 보임, 음식만 보이는 화면을 구분했다. 먼 배경 인물은 존재만 기록하고 신원·정확한 interval을 추정하지 않았다.
- 전체 요리 시연/반응은 같은 **행사 맥락**이지만 음식 클로즈업에는 해당 인물이 화면에 없다. 이 20초를 한 인물 클립으로 붙여야 한다는 GT는 아니다. 컷은 ±1 원본 프레임 정밀도이며 창 시작·끝은 검열 경계다.

## 실제 검증

[재현 코드](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-boundary-source-first/score_saved_window.py)는 원본·GT·manifest SHA를 다시 확인하고 원본 600프레임을 읽어 제품의 `_shot_changed`를 같은 5fps 표본에 재적용한다. [채점 결과](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-boundary-source-first/saved-window-audit.json) SHA-256 `efd934b9971f01b9a48ab5b7cc0389a259c198f37336f2b366cafceaa3467617`: 원본 GT의 7개 컷이 각각 **새 shot의 첫 5fps 표본**에서 검출됐고, 이 창의 표본상 추가/누락 컷은 **0/0**이었다. 따라서 이 창의 짧은 결과를 컷 검출기의 과분할로 돌릴 근거가 없다. 이는 전체 834 shot의 정확도 검증이 아니다.

원본과 저장 관측의 수동 일대일 대응에서 음식 소스 화면 **1810.8초**의 상자 `[93,121,647,668]`가 `person_456` 하나의 얼굴로 저장돼 `clip_0676`을 만들었다. 원본에는 그 상자에 사람이 없어 **명확한 비얼굴 오검출**이다. 단일 관측이라 결과 상태는 `needs_review`이며 자동 숨김/제외는 하지 않았다. 남색 정장 반응 얼굴은 `person_001`; 같은 요리 출연자는 무대 와이드샷에서 `person_257` 15관측, 이어지는 클로즈업에서 `person_093` 17관측으로 **분리**됐다. 와이드 대표 표본 1825.4초 얼굴은 약 28×34px, 클로즈업 첫 표본 1826.4초는 약 223×309px이고 두 SFace embedding cosine은 **0.250816**으로 현행 묶기 0.55보다 낮다. 이 숫자는 해당 두 관측만의 유사도이며 인물 전체의 동일성을 증명하는 모델 점수는 아니다. 원본 시각 라벨로 동일인임을 판단했다. 다른 인물 오합침을 유발한 기존 전역 threshold 실험 때문에 문턱을 낮추지 않았다.

기존 YuNet 검출기가 비얼굴에 구조상 다른 특징점을 주는지 좁게 확인했다. [사전 실행 계획](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-boundary-source-first/landmark-plan.json) SHA-256 `2ba57e2a2e3fb2f7ae95d02e3ff271e4da9708a8c7adc1f3cedb13c1330742a4`에 원본/GT/weight/runner hash, Mac CPU/OpenCV4.13, 정확히 3프레임·60초·RSS2GiB·출력1MiB 상한과 격리 출력 폴더를 잠갔다. 새 모델은 받지 않았고 인식 embedding은 실행하지 않았다. 실제 [실행 기록](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-boundary-source-first/landmark-probe/run-report.json) SHA-256 `691ce5d7e2014dbabb894f5b4d7a6ff1be8e2a94b04919602cd1a544338d0d89`: 3프레임/3검출, 0.132초, 최대 RSS222,511,104B, 출력4,561B. [검출 수치](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-boundary-source-first/landmark-probe/landmarks.json) SHA-256 `7018a057d774ce952055527be5b3aff4abafc4ffdd4aa0cb52825fdbd0556ea9`: 소스 화면 비얼굴의 검출 score `0.685`, 실제 반응 얼굴 `0.927`, 실제 요리 출연자 얼굴 `0.919`. 비얼굴에도 눈·코·입 다섯 점이 상자 안에서 **그럴듯한 순서와 위치**로 나왔다. 단 세 표본의 점수/특징점만으로 전역 score 또는 landmark 필터를 만들지 않는다. 앞선 0.82/0.85 score 대조가 실제 얼굴을 놓쳤다는 결과도 있다.

## 결정·한계·다음 입력

**기존 결과 품질 불합격 유지.** 기존 앱 카드·사용자 수정·Person/Dance 모델/문턱·공통 API·MP4/ZIP을 변경하지 않았다. 얼굴 없는 구간을 특정 인물에게 붙이거나 인접 컷을 자동으로 이어 붙이지 않는다. 현재 face-only 경로는 요리 출연자 얼굴이 잘린 `[1815.733,1818.533)`초와 뒤통수만 보이는 사람을 복구할 수 없다. 이번 창은 배경 인물의 정확한 신원/연속 interval, 대표 이미지 499개의 선호도, 다른 장르 일반화, 실제 앱 편집·다운로드, Windows/W13 adapter를 검증하지 못했다.

다음에는 **인물별 얼굴 가시/몸만/화면 부재와 사용자가 원하는 장면 경계를 별개의 연속 interval**로 원본 우선 라벨해야 한다. 그 뒤 컷을 보존한 상태에서 잘못된 인물 합침·쪼개짐·음식 등 비얼굴 오검출과 배경 인물 누락을 동시에 대조해야 한다. 짧은 클립의 원인이 실제 컷인지 얼굴 관측 gap인지 구간별로 구분한다. 모델/threshold/대표 규칙 후보는 다른 영상의 독립 GT에서 오합침과 누락을 함께 통과한 뒤에만 제품 적용을 검토한다. 새 모델 다운로드·유료 API·Build5·기존 완료 프로젝트 덮어쓰기는 별도 범위이며, 사용자가 승인한 **기존 모델 얼굴 추론 횟수 제한 해제**는 유지한다.

## 같은 shot의 짧은 공백 반례 추가

위 판단 뒤 저장 manifest에서 **같은 shot의 클립 사이에 0.2초 공백**이 있는 `shot_0244`를 목표 표본으로 택했다. 결과 기반 선정이므로 독립/블라인드 표본은 아니다. 그룹 ID와 관측 상자를 열기 전에 원본 `[643,652)`초의 5fps 접촉 시트로 [원본 가시 GT](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-long-shot-gap/source-first-gap-gt.json)를 고정했다(SHA-256 `d2df27d8829d002fc801e568354f4fdd67f8ecb113c1a1339f90c4ffcc0423ae`). 원본에는 643.733초와 650.8초에 편집 컷이 있고 **두 클립 사이에는 컷이 없다**. 그 사이 카메라가 위로 올라가며 화면 밖에 있던 출연자의 얼굴이 나타난다. 처음에는 왼쪽 화면 가장자리에 **별도 사람의 부분 얼굴**도 잠깐 보인다.

잠금 후 [저장 관측 대조](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-user-long-shot-gap/saved-gap-audit.json) SHA-256 `dd57a78579498ed91641147e2a150dee0f06d43c4952ead30f0115bca57b0f06`: 앞 `clip_0239` 644.95–645.95초의 `person_256`은 왼쪽 가장자리 사람(`obs_0004428`, bbox x9–126)이고, 뒤 `clip_0240` 646.15–650.8초의 `person_002`는 얼굴이 화면 위에서 들어오는 남색 재킷 출연자(`obs_0004429`, bbox x544–756)다. **서로 다른 인물**이므로 같은 shot·0.2초 공백만 보고 자동 결합하면 오합침이다. 원본에서 머리가 잘린 주 출연자의 몸과 뒤 얼굴은 의복/동작상 같은 사람으로 보이지만 얼굴만으로 확인되지는 않는다. 이 한 사례는 같은 shot의 모든 gap을 보존해야 한다는 증거도 아니다. 판단 기준에 얼굴 가시성과 사람별 연결이 필요하다는 반례다. 새 얼굴 추론·제품 수정은 0회다.
