# W14 ANTIFRAGILE 작은 얼굴·메인 몸↔얼굴 연결 후속 점검 (10/14)

## 목적과 경계

사용자가 확인한 얼굴 20장은 연결된 전체 얼굴보다 컸다. 따라서 기존 SFace와 제한 Seeta 보충의 14/18·16/18 결과를 작은 얼굴이나 전체 클립으로 확대해 말할 수 없다. 이 점검은 **저장된 동일 영상·동일 W13 69번 메인 몸 선택·동일 YuNet 얼굴 관측**에서 작은 얼굴의 기존 분류 처리율과 연결 보류의 원인을 분리한다. 새 모델 추론, 제품 규칙 변경, W13 메인·구간 수정은 없다.

원본 1920×1080 MP4 SHA-256 `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`. 얼굴 관측 `93967024e0d79b0fa8276aa59cce22dc3a1a26878db3234ab2a63dad64949544`, 메인↔얼굴 연결 `4d9dddd5d77d2f2dd3f3ecebb34d4f32c60200423f68ce3afc008d0965ddd036`, W13 후보 계약 `f31825eb73021b2257c2ae5db487c3ecdfc691f7964d2e8bf3d134604073c019`을 고정했다. 나머지 SFace 특징·참조·정책·pose·adapter 해시는 각 계획 JSON에 있다. [작은 얼굴 사전 계획](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/small-face-association-review-v1/plan.json), [연결 보류 사전 계획](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/ambiguous-head-audit-v1/plan.json).

## 작은 얼굴: 배정 처리율과 신원 정답을 분리

W13 `single` 역할 522시점 중 W14가 얼굴 하나를 위치상 연결한 435시점을 기존 SFace 특징과 **기존 개발 문턱 그대로** 한 얼굴씩 재계산했다. 얼굴 가로 크기별 현황은 아래와 같다. `확정`은 점수 기준을 넘은 배정 횟수이며, 맞혔다는 뜻이 아니다.

| 원본 얼굴 가로 | 연결 시점 | SFace 확정 | 보류·미매칭 |
| --- | ---: | ---: | ---: |
| 90px 미만 | 149 | 36 (24%) | 113 |
| 90–159px | 160 | 80 (50%) | 80 |
| 160px 이상 | 126 | 84 (67%) | 42 |

기존 사용자 라벨 20장은 그대로 두고, 모델 이름·점수 없이 폭 45–89px/높이 55px 이상/YuNet 점수 0.8 이상인 시점을 15초 칸마다 하나씩 고른 **작은 얼굴 13장**을 원본에서 추출했다. 기존 SFace는 7장을 확정, 5장을 모호, 1장을 미매칭으로 처리했다. 이 13장은 높은 검출 점수를 갖춘 표본이므로 90px 미만 전체 149시점을 대표하지 않는다. 사용자가 [S00–S12 얼굴 검토 이미지](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/small-face-association-review-v1/small13.jpg)에서 12장을 멤버로, S09를 `판단 어려움`으로 라벨링했다. 아래 후속에서 정답 대조를 마쳤다. [선정 얼굴 ID·원본 해시](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/small-face-association-review-v1/selection.json), [SFace 크기별 재계산](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/small-face-association-review-v1/coverage.json).

### 13장 사용자 라벨 이후 고정 정책 비교

같은 13장/기존 등록 사진 21장/기존 YuNet 얼굴 행을 사용했다. 기존 SFace 특징과 앞서 검산된 Seeta 참조 특징은 재사용하고 Seeta 얼굴 인식만 **13회** 새로 실행했다. 두 모델은 각자의 정렬·특징 공간·개발 자료에서 정한 문턱을 유지했다. Seeta가 SFace 보류 얼굴을 보충하려면 Seeta가 확정하고 SFace 원시 1위와 같은 멤버여야 한다. 이번 사용자 라벨로 문턱을 조정하지 않았다.

| 방식 | 식별 가능한 12장 정답 | 다른 멤버 오확정 | 보류 | 식별 어려운 S09 배정 |
| --- | ---: | ---: | ---: | ---: |
| 기존 SFace | 7 | 0 | 5 | 0 |
| Seeta 단독 | 2 | 0 | 10 | 0 |
| 기존 SFace + 제한 Seeta 보충 | 7 | 0 | 5 | 0 |

보충으로 새로 맞힌 작은 얼굴은 **0장**이다. Seeta 단독은 SFace가 맞힌 다섯 얼굴을 추가로 보류했다. 이전의 큰 얼굴 18장에서는 보충이 SFace 정답 14→16을 만들었지만 작은 얼굴에서는 7→7이었다. SFace 원시 1위는 식별 가능한 12장 모두 사용자 라벨과 같았으나 네 장은 1·2위 차이 부족, 한 장은 거리 초과로 보류됐다. 이 표본의 순위가 맞았다는 이유로 전역 문턱을 낮추면 다른 촬영 영상·등록 외 인물의 오확정 위험이 있어 라벨에 맞춰 보정하지 않는다. 따라서 크기가 다른 두 선정 층을 섞어 전체 영상 개선으로 말하지 않으며 Seeta 전면 교체·제한 보충의 제품 채택은 계속 보류한다. [13장 얼굴별 표·사용자 라벨·원시 점수·계산 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/small-face-user-comparison-v1/comparison.md).

사전 계획 SHA `5e72085238c1974db0f4e2383373ca444136a55ddfce045cabec796f5c9ae9b0`, 실행 결과 SHA `dfb89157dd054a89f2c2b89fc2a5c8173d127bdbc8085f66ec81c5a65e7f4a0c`, 독립 감사 SHA `3f8c404d816c3b3e3200087d28096bbcc67a46fa4983a2388b2e23aee39f9ee2`. 추론·정렬 실패 0, Mac arm64 CPU에서 1.005초·최대 RSS 703,102,976바이트로 사전 600초·4GiB·20MiB/13회 상한 안이었다. 이는 저장 자료를 쓴 짧은 평가 실행이며 제품 전체 처리 시간은 아니다. 감사는 13개 전 거리/판정과 과거 라벨 전 SFace 상태 일치·입력 해시를 확인했다. 한 영상의 고검출 점수 작은 얼굴을 하나씩 본 결과라 149개 작은 얼굴 전체, 드문 오확정, 몸↔얼굴·구간·클립 정확도는 미검증이다.

### 보류 다섯 얼굴의 시간상 근거 후속 진단

사용자 진행 승인 뒤 위 다섯 보류 얼굴과 S09만 사전 고정했다. 같은 원본 ±1초의 저장 관측을 후보 장면 컷 안으로 제한하고, 같은 W13 단독 메인 몸 추적 ID·확정된 W14 얼굴 연결에서만 **기존 SFace 판정**을 모았다. 대상 얼굴의 원시 1위와 같은 멤버가 주변 서로 다른 시점 두 장 이상에서 확정되고 반대 멤버 확정이 없을 때만 확인 후보를 낸다. 원본 48프레임/6장의 몸·얼굴 카드에는 모델 이름·점수를 숨기고 먼저 연속성을 한 검토자가 보았다. [얼굴별 원본·고정 규칙·29관측 점수·감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/temporal-face-diagnostic-v1/diagnosis.md).

| 대상 | 사용자 라벨 | 같은 몸 경로의 주변 확정 얼굴 | 확인 후보 |
| --- | --- | ---: | --- |
| S00 | 홍은채 | 0 | 보류 |
| S01 | 허윤진 | 0 | 보류 — W13 추적 ID 79→82 교체, 자동 합산 금지 |
| S02 | 카즈하 | 카즈하 6 | 카즈하 |
| S06 | 카즈하 | 카즈하 3 | 카즈하 |
| S08 | 홍은채 | 0 | 보류 |
| S09 | 판단 어려움 | 0 | 이름 배정 없음 |

따라서 다섯 사용자 라벨 얼굴의 **탐색 후보 2장 일치/타인 후보 0/보류 3**이다. 이 결과는 이미 본 영상·선정 라벨을 대상으로 한 사후 진단이라 2/5 회복률이나 0/5 오배정 안전성 검증으로 보고하지 않는다. S01은 화면에서는 같은 출연자로 보이나 추적 ID가 바뀌어 제외한 것이고, S00·S08은 몸/얼굴이 이어져 보여도 확정 표본이 없었다. S09는 사용자의 `판단 어려움`을 이름 정답으로 바꾸지 않았다. 후보 장면 컷과 W13 track ID는 완전한 동일인 보장이 아니다. 계획 SHA `82e8e2049aeca83c5169e777fb6b3eb86bf137f0a1f012391be6e15e625d4a82`, 결과 SHA `a139cbdebf95067b25d0f6e91de4353db894ed6c178a67bf19ea4b7b12fe5150`, 독립 산술 감사 SHA `25081db46e08242ad0a04f6cafc0ab00fe16c4adce91599860fe7fc610363da8`. 신규 얼굴/몸 모델 호출 0, 원본 추출 2.78초·최대 RSS 387MB로 고정 상한 이내. **제품 SFace 경로와 W13/core는 그대로다.** 다른 촬영 영상의 메인 몸·얼굴·실제 멤버/등록 외 인물·컷/교대 GT에서만 이 후보의 적용 가능성을 판단한다.

같은 선정 규칙으로 원본 연결 보류 53시점 중 10시점을 먼저 한 화면에서 판독했다. 단일 화면에서 8시점은 얼굴 행이 비교적 분명하고 2시점은 불확실했다. 이는 한 검토자의 **몸과 얼굴의 위치 판독**이며 독립 신원 정답이나 W13 메인 정답이 아니다.

## 연결 보류 53시점 전수 원본 검토

연결 보류 53시점은 모두 `shared_head_candidate`다. 기존 adapter는 선택 몸의 머리에 가장 가까운 얼굴이 다른 pose 머리에도 가까우면 보류한다. 53시점 중 다른 pose **몸 상자**와 선택 몸의 IoU가 0.5 이상인 경우가 35시점이다. 중첩 pose 상자 때문에 일부 보류했을 가능성을 시사하지만, 상자 중첩만으로 두 pose가 한 사람이라는 결론은 내리지 않는다.

앞서 본 10시점을 개발 예로만 취급하고, 나머지 **43시점 전부**를 원본 화면·선택 몸·모든 얼굴 상자로 렌더링했다. 자동 선택 얼굴과 멤버 점수는 숨긴 채 한 차례 판독을 저장한 다음, 미리 고정한 읽기 전용 규칙을 대조했다. 그 규칙은 `shared_head_candidate`에만 적용한다: 가장 가까운 얼굴의 메인 코 거리 ≤얼굴 높이 0.15배, 두 번째 얼굴의 메인 코 거리 >0.75배(없으면 통과), 가까운 경쟁 pose 몸과 선택 몸 IoU ≥0.5. 통과해도 얼굴 ID 후보만 반환하며 멤버를 배정하지 않는다.

| 구분 | 시점 | 후보 규칙이 선택 | 한 화면 판독과 얼굴 행 일치 | 한 화면에서 불확실한 후보 |
| --- | ---: | ---: | ---: | ---: |
| 먼저 본 개발 예 | 10 | 7 | 6 | 1 |
| 나머지 전수 검토 | 43 | 28 | 27 | 1 |
| 합계 | 53 | 35 | 33 | 2 |

규칙은 18시점을 계속 보류했다. 사전 단일 화면 판독에서 명확한 얼굴과 **다르게 선택한 사례는 없었지만**, 선택한 35시점 중 A00·H38 두 시점은 판독 자체가 불확실했다. 두 시점의 앞뒤 원본을 **규칙 채점 후** 추가로 살펴보니 A00은 얼굴 3번, H38은 얼굴 0번 연결이 그럴듯했다. 이 사후 맥락 판독은 블라인드 33건에 합산하지 않는다. 같은 영상의 연속 프레임은 독립 사례가 아니고 W13의 선택 몸이 올바른 안무 메인인지는 이 점검으로 알 수 없다. 제품 adapter에 이 규칙을 넣을 근거가 아직 부족하다. [43시점 선정·원본 카드](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/ambiguous-head-audit-v1/selection.json), [사전 화면 판독](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/ambiguous-head-audit-v1/visual-review.json), [규칙 대조 전수 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/ambiguous-head-audit-v1/result.json), [사후 앞뒤 화면 판독](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/ambiguous-head-audit-v1/adjacent-review.json).

## 얼굴 연결 실패 34시점: 검출과 몸 머리 위치의 분리

`single`이지만 얼굴을 배정하지 못한 **34시점 전부**를 프레임 번호순으로, 선택 몸과 검출된 모든 얼굴 상자만 보이게 원본에서 다시 그렸다. 결과 이름·점수는 숨겼다. 이 화면을 한 번 판독한 라벨을 저장한 뒤 기존 adapter의 실패 코드와 대조했다. 검출 입력은 이 원본의 **1920×1080 전체 해상도**, YuNet 점수 문턱 0.60이었다. 작은 입력으로 축소해서 생긴 누락이라고 가정하지 않는다. [사전 범위·모델/입력 SHA](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/unassigned-face-audit-v1/plan.json), [34개 원본 카드/프레임 목록](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/unassigned-face-audit-v1/selection.json), [단일 화면 판독 라벨](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/unassigned-face-audit-v1/visual-review.json).

| 원본에서 선택 몸의 얼굴 | 시점 | 해석 |
| --- | ---: | --- |
| 얼굴이 보이고 해당 YuNet 상자도 있음 | 2 | U07은 `unreliable_main_head`, U18은 `no_face_at_main_head`로 연결 거부. 머리 위치·자세 조건을 따로 볼 사례다. |
| 얼굴이 보이지만 해당 YuNet 상자는 없음 | 11 | 주로 옆얼굴·고개 젖힘·움직임. U14/U15의 옆얼굴과 U20의 젖힌 얼굴 등은 검출 단계 진단 사례다. |
| 얼굴이 안 보이거나 식별 불가 | 17 | 등짐·머리카락·팔·어두운 실루엣에서 신원을 자동 채우면 안 된다. |
| 한 화면에서 얼굴/몸 대응이 불확실 | 4 | 원본 앞뒤 시점 또는 독립 검토가 필요하다. |

기존 실패 코드는 `no_face_at_main_head` 26, `no_face_detection` 5, `unreliable_main_head` 3이다. 코드별 원본 판독 교차표는 [34건 전수 출처·산술 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/unassigned-face-audit-v1/result.json) SHA-256 `294c0c276be3280039fb543563286396ba81970eeb0a1e5b538a22e203cbe977`에 있다. 34프레임 원본 추출은 2.75초, 최대 RSS 약 373MB, 이미지·선정 목록 약 3.0MB로 사전 180초·4GiB·20MB 상한 이내였다. 신규 모델 호출은 없었다. 단일 화면을 한 검토자가 본 결과라 11건을 검출기 성능 지표로 일반화하거나 2건의 상자를 정답 연결로 제품에 반영하지 않는다. **보이는 얼굴 13건과 보이지 않는 얼굴 17건은 서로 다른 후속 작업**이다. 검출 누락은 별도 후보 검출기/입력 조건과 독립 얼굴 GT에서, 머리 위치 보류는 다른 영상의 몸↔얼굴 GT에서 비교한다.

## 동일 YuNet의 점수 기준만 낮춘 격리 진단

사용자가 허용한 추가 얼굴 추론 범위에서 새 모델 다운로드 없이 **동일 YuNet SHA `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`**를 사용했다. 위 34개 고정 프레임·원본 전체 1920×1080·NMS 0.30·top-k 5,000을 그대로 두고 검출 점수 기준만 0.60(저장 기준선)에서 0.45와 0.30으로 낮췄다. [추론 전 계획·입력/코드 hash·68회 호출 상한](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/yunet-threshold-diagnostic-v1/plan.json), [34프레임·68회 전 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/yunet-threshold-diagnostic-v1/result.json) SHA-256 `bea319e3c35a920c022b9c3ee249c8acca3c99d449e8b09a32d869e2433edce8`. Mac arm64 CPU/Python 3.11.14/OpenCV 4.13.0, 두 조건 합쳐 7.86초·최대 RSS 약 628MB였다. 실제 설치 앱·Windows 실행 시간은 아니다.

| 같은 원본 검토 표본 | 저장 0.60 | 시험 0.45 | 시험 0.30 |
| --- | ---: | ---: | ---: |
| 선택 몸의 얼굴이 보이는데 해당 상자 없음: 11시점 중 새 상자 회복 | 0 | 2 | 4 |
| 위 11시점 중 여전히 선택 얼굴 미검출 | 11 | 9 | 7 |
| 선택 몸의 얼굴이 안 보이는 17시점에 추가된 상자 수 | — | 16 | 44 |
| 위 17시점 중 새 상자가 생긴 프레임 | — | 10 | 15 |

0.45의 회복은 U05·U16, 0.30에서 U10·U14가 추가됐다. U16의 0.30은 **같은 얼굴의 중복 상자 2개**이고 회복 프레임은 하나로 센다. U20의 0.30 새 상자 중 하나는 선택 인물의 **손/팔**이며 얼굴 회복으로 세지 않았다. U21의 새 얼굴 상자는 선택 몸이 아닌 다른 사람 것이다. 선택 몸 얼굴이 보이지 않는 프레임의 추가 상자도 다른 실제 사람과 배경/비얼굴이 섞이므로 16·44를 전부 오검출로 부르지 않는다. 다만 U01의 무대 배경, U08의 등·머리카락 등 **명확한 비얼굴 상자**가 생겼다. [원본 상자 판독 번호별 기록](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/yunet-threshold-diagnostic-v1/visual-review.json), [입력·68회·상자 보존·11건 회복·17건 추가 산술 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/yunet-threshold-diagnostic-v1/audit.json).

이 34프레임은 **기존 실패를 보고 선택한 개발 표본**이고, 상자 회복도 한 검토자의 원본 판독이다. 새 상자의 멤버 신원, 연결 안전성, 전체 영상 누락률·오검출률은 확인하지 않았다. 따라서 **0.45/0.30 전역 문턱 변경을 모두 미채택**한다. 7/11 잔여 누락은 YuNet 점수만 낮춰 해결되지 않으며, 검출기 후보를 비교하려면 미리 정한 별도 영상·얼굴 GT와 다른 사람/비얼굴 상자의 손실 기준이 필요하다.

## 실제 검증, 결정, 다음 입력

원본 추출은 처음 43프레임과 나머지 43프레임, 사후 맥락 6프레임이다. 앞의 두 실행은 각각 180초·4GiB·20MB, 맥락 추출은 30초·5MB의 사전 상한 안에서 끝났고 신규 ML 호출은 0회다. 저장 SFace 크기별 계산을 다시 실행해 위 435건과 13건의 분모·상태를 재현했다(결과 JSON SHA-256 `0f168d0027f110458fbcac4600350d943010098ac15dd1030d50475afad8bc1b`). 53시점 분할·입력 SHA·43장 카드 SHA·규칙 산술·사후 판독 분리를 [독립 재계산 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/ambiguous-head-audit-v1/audit.json)로 확인했다(규칙 결과 SHA-256 `d9f19e2b45a5026ede63ce73a2bfa7475c26b4e7737a6f2279e9c4ed5fb17bd5`). 이 감사는 **계산·출처 검증**이며 얼굴 신원 정확도 검증이 아니다.

**결정:** 기존 YuNet 0.60+SFace 제품 경로를 유지한다. Seeta 보충, 연결 보류 해제 규칙, YuNet 0.45/0.30은 평가 후보 또는 기각된 설정으로만 남긴다. W13 Dance adapter, 공통 얼굴 공개 API, 사용자 결과·편집·MP4는 수정하지 않았다. S00–S12 사용자 라벨과 고정 비교는 위에서 완료했다. 다음에는 **다른 촬영 영상**에서 작은/흐린 얼굴, 등록 외 인물, 몸↔얼굴 연결과 동시 출연 오연결을 독립 라벨로 평가해야 한다. 34시점 진단의 `보이는 얼굴이지만 검출되지 않음`은 별도 검출기·입력 비교 과제로 남기고, 얼굴이 보이지 않는 장면에 다른 사람 얼굴을 임의로 대입하지 않는다. W13의 안정된 메인·교대·구간 정답을 확보하기 전에는 개별 얼굴 점수를 클립 분류 정확도로 전파하지 않는다. Windows x64·설치 앱 패키징·전체 영상 오배정률도 미검증이다.

**후속, 시간 이웃 규칙의 다른 촬영 대조:** S02/S06에서 후보가 맞았던 지역 투표를 같은 규칙으로 이전 뉴진스 개발자료 353얼굴에 적용했다. 직접 라벨34지점의 정답18→23/신규 오확정0이지만, 앞뒤 혜인 직접 라벨과 같은 보라색 출연자로 보이는 중간 8얼굴에 하니 후보가 나왔다. 이 8개의 직접 사용자 GT는 없으므로 채점 오답 수에 넣지 않으며 원본 연속성상 강한 위험 사례로 보존한다. [별도 고정 입력·원본7장·감사·미채택 결정](../10/14-w14-temporal-cross-video-stress-result.md). 따라서 위 S02/S06의 사후 회복을 제품 정책으로 승격하지 않는다. 새 독립 촬영·컷/교대·등록 외 인물의 직접 GT와 W13 안정 메인 출력이 여전히 필요하다.
