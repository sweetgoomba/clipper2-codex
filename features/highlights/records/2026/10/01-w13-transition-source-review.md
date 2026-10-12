# W13 세 오선택 주변 원본 장면 검토 — 2026-10-01

## 무엇을 확인했나

앞선 메인 오선택이 나온 **22.022초, 29.029초, 55.989초**의 앞뒤를, 사용자가 지정한 로컬 원본에서 다시 보았다. 원본은 SHA-256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`다. 약 **0.1001초마다 한 장**(원본 59.94fps에서 6프레임 간격)을 뽑았고, 세 오선택과 정확히 같은 원본 프레임 `1320, 1740, 3356`도 전체 해상도로 확인했다. 이미지에는 앱 판정이나 MoveNet 상자를 겹치지 않았다.

다만 작성자가 이미 모델 결과를 본 뒤 수행한 검토다. 따라서 [이번 구간표](01-w13-transition-source-review-v2.json)는 **원본 기반 잠정 검토표**이며 새 독립 정답이나 새 채점 분모가 아니다. 이전에 모델 결과를 보지 않은 사람이 확인한 [동결 라벨 v1](01-w13-pose-scoring-labels-v1.json)의 솔로 창과 네 앵커는 그대로 둔다. `P1`~`P5`는 영상 안의 익명 인물 ID이며 실명이나 얼굴 판정이 아니다.

| 원본 구간 | 눈으로 확인한 흐름 | 이번 처리 |
|---|---|---|
| **20.0~23.5초** | 첫 주도 인물 `P1`이 뒤로 돌고 물러나는 동안 `P2`가 앞으로 나와 관객을 향한다. [20~21.9초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w22_01.jpg), [22~23.4초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w22_02.jpg), [정확한 22.022초 원본](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/anchor_01.jpg). | **20.5~22.0초는 P1→P2 교체 검토**. 22.0초 이후 `P2` 단독 창은 기존 독립 라벨과 일치. 교체 구간에 두 사람이 동시에 메인인지는 미확정. |
| **26.5~31.0초** | `P2`가 앞선 순서를 마치고 `P3`가 뒤에서 나와 앞에서 동작한다. [26.5~28.4초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w28pre_01.jpg), [27.5~29.4초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w29_01.jpg), [29.5~30.9초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w29_02.jpg), [정확한 29.029초 원본](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/anchor_02.jpg). | **27.0~29.0초는 P2→P3 교체 검토**. 29.0초 이후 `P3` 단독 창은 기존 독립 라벨과 일치. 두 사람이 동시에 메인인지 미확정. |
| **51.5~59.5초** | 왼쪽에 서 있던 `P4`가 낮은 자세의 뚜렷한 동작을 이어가고 나머지 인물은 대체로 자리를 지킨다. 뒤에는 `P5`가 앞으로 나온다. [51.5~53.4초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w56pre_01.jpg), [53.5~55.4초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w56_01.jpg), [55.5~57.4초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w56_02.jpg), [57.5~59.4초](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/w56post_01.jpg), [정확한 55.989초 원본](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/transition_review/anchor_03.jpg). | **52.8~54.0초는 그룹→P4 교체 검토**, **54~57초 P4 단독**은 기존 독립 라벨과 일치, **57~59초는 P4→P5 교체 검토**. 59초 이후 P5 단독은 기존 라벨과 일치. |

## 확정할 수 있는 것과 남은 것

- 세 정확한 앵커 프레임의 기존 익명 인물 정답 `P2`, `P3`, `P4`는 원본 전체 해상도와 주변 움직임에서 **기존 독립 감사에 반하는 모습이 없었다**. 새 검토가 그 감사의 독립성을 높인 것은 아니다.
- 교체 구간은 한 시각으로 찍지 않고 **검토 시간대**로 남겼다. 표의 `main_ids: null`은 아무도 없다는 뜻이 아니라, **후보를 보존하고 아직 확정하지 않았다는 뜻**이다. 이번 세 시간대에서 `공동 메인`이라고 확정할 근거도 없다.
- 기존 [오프라인 규칙 비교](01-w13-main-selector-offline-rule-comparison.md)의 **1/4 또는 2/4**는 여전히 기존 네 앵커의 결과다. 이번 검토로 정확도 분모를 늘리지 않았다. 전환 지연을 숫자로 내기 위해서는 원본에서 교체 시작/끝의 허용 범위와 **각 분석 프레임의 사람별 위치 또는 신원 연결**을 독립 확인해야 한다. 현재는 0.1초 간격 장면 모음과 세 정확한 앵커만 있다.
- 공동 메인 precision/recall에는 실제 동시에 앞서는 인물 **집합**의 정답이 필요한데, 이 세 교체 구간에서는 아직 확정하지 않았다. 42~48.5초 그룹과 98.5~104.3초 빠른 교체를 별도 후보로 두되, 그룹 전원을 무조건 메인으로 간주하지 않는다.

## 다음 비교에 필요한 최소 라벨

`20.5~22.0`, `27.0~29.0`, `52.8~54.0`, `57.0~59.0`초의 원본을 모델 판정 없이 재검토해 **단독/공동/판정 보류**와 전환 시각의 허용 범위를 고정한다. 각 분석 프레임 중 채점에 넣는 프레임에는 익명 인물별 상자를 함께 기록한다. 공동 메인 구간이 있다면 여러 ID를 한 집합으로 남긴다. 그 뒤 저장된 pose JSON을 다시 채점할 수 있어 **새 ML 실행은 필요하지 않다**. 결과는 메인 일치, 전환 지연의 범위, 공동 메인 오배정, 보류 보존을 분리한다.

이번에는 원본 읽기와 이미지 추출, 잠정 구간표 기록만 했다. 모델·얼굴 분석, clip export, 제품 코드 변경, commit/push/merge/deploy는 없었다.
