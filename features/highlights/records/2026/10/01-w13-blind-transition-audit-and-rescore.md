# W13 전환 구간 독립 원본 검토와 저장 pose 재채점 — 2026-10-01

## 결과

기존에 원본 라벨을 별도로 감사한 검토자가 **원본 영상과 원본 프레임만** 보고 22초·29초·54초·58초 전후를 다시 검토했다. 검토자에게 앱·MoveNet 판정과 앞선 오프라인 규칙 비교를 제공하지 않았고, 검토자도 미열람을 보고했다. 검토자가 고른 정확한 원본 프레임 8개와 사람 상자를 [라벨 v2](01-w13-blind-transition-labels-v2.json)에 먼저 고정했다. 그 뒤에만 이미 저장된 MoveNet `run-01/pose.json`과 [채점 결과](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-v1/score-transition-v2.json)를 대조했다. 새 모델 추론은 하지 않았다.

**엄격하게 단독 메인이라고 본 새 6프레임 중 2프레임 일치, 4프레임 오선택**이었다. 오선택한 4프레임에서도 해당 사람은 MoveNet의 사람 후보로 검출됐다(IoU≥0.30). 이번 여섯 장에서 문제가 확인된 단계는 사람 검출 이후의 메인 선택이다. 특정 교체 주변을 골라 본 작은 표본이므로 영상 전체 정확도나 모델 간 우열로 환산하지 않는다. 앞서 채점한 네 장의 1/4와도 **별도 표본**으로 표시한다.

| 원본 시점·이미지 | 독립 원본 판정 | 현행 선택 | 정답 사람의 순간 점수 순위 | 결과 |
|---|---|---|---:|---|
| [20.821초 P1](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f1248.jpg) | 초록 `P1` 단독 | 다른 사람 | 4위 | 오선택. 정답 후보 IoU 0.821 |
| [21.822초 P2](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f1308.jpg) | 노랑 `P2` 단독 | 다른 사람 | 2위 | 오선택. 정답 후보 IoU 0.859 |
| [27.828초 P2](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f1668.jpg) | 노랑 `P2` 단독 | 다른 사람 | 2위 | 오선택. 정답 후보 IoU 0.887 |
| [28.962초 P3](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f1736.jpg) | 빨강 `P3` 단독 | 다른 사람 | 1위 | 오선택. 정답 후보 IoU 0.773; 전환 유지 영향 확인 필요 |
| [58.325초 P5](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f3496.jpg) | 연보라 `P5` 단독 | `P5` | 1위 | 일치. 선택 IoU 0.837 |
| [58.792초 P5](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f3524.jpg) | 연보라 `P5` 단독 | `P5` | 1위 | 일치. 선택 IoU 0.714 |

현행 선택은 현재 점수 1위였던 `P3`도 28.962초에 고르지 않았다. 반대로 앞의 세 오선택에서는 정답의 순간 점수가 각각 4·2·2위라 전환 대기만 줄여도 해결되지 않는다. 매 프레임 최고 점수 인물을 즉시 고르는 가정은 이 여섯 장에서 3/6이지만, 이전 [오프라인 비교](01-w13-main-selector-offline-rule-comparison.md)에서 bbox 불연속이 늘었으므로 제품 변경 근거로 삼지 않는다.

## 보류한 장면

- **21.2~21.5초:** `P1`이 돌아서고 `P2`가 앞으로 나오는 인계. 한 명으로 강제하지 않는다.
- **28.2~28.6초:** `P2`와 `P3`가 겹친다. 공동 메인 *후보*이지만 가림 때문에 확정 정답 집합은 없다.
- **52.8~53.4초:** 그룹에서 `P4` 동작으로 넘어가는 과정. [53.787초 P4](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f3224.jpg)는 장비가 다리 일부를 가리고 단독 판정이 약해 점수에서 제외했다.
- **57.3~57.6초:** `P4`에서 `P5`로 인계. [57.124초 P4](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/label-samples/yFTAYXDTjqI/blind_transition_v2/f3424.jpg)도 인계 직전이라 엄격한 점수에서 제외했다.

네 검토 시간대의 저장된 분석 프레임은 합계 **100장**이다. 모두 `main_bbox`가 있고 `is_group=true`였다(구간별 22·30·18·30장). 이것은 네 시간대에 실제 공동 메인이 100장 있었다는 뜻이 아니다. 원본의 단독 메인 6장에도 모두 그룹 플래그가 켜졌다. 따라서 그룹 플래그를 공동 배정 또는 보류의 유일한 조건으로 쓰면 안 된다. 보류 장면 자체는 최종 clip에서 조용히 탈락시키지 않고 검토 가능하게 남겨야 한다.

## 이번 결과의 범위와 다음 판단

- 채점은 원본 전체 `1920×1012`, `60000/1001fps`에서 4의 배수 프레임 6장에만 적용했다. 라벨의 원본 hash `7f23b9ad…9688d4`, 동결 라벨 v1 hash `c76866b1…a704`, 새 라벨 v2 hash `9b871c05…274cbe8`, 저장 pose hash `fcc077e5…1260d3`을 확인했다. 정확한 값은 JSON에 있다. 선택 상자와 독립 상자의 IoU≥0.30이면 일치로 처리했다.
- 라벨에는 엄격 채점 6장과 약한/경계 2장을 **모델 결과를 보기 전에** 나눠 적었다. 라벨의 약 0.1초 경계는 전환 시각의 점 추정값이 아니다. 원본의 모든 프레임과 오디오를 검토한 것은 아니다.
- 이번에도 **확정된 공동 메인 집합이 없다**. 공동 메인 precision/recall과 전환 지연의 단일 숫자는 아직 내지 않는다. 다음 비교에서는 28.2~28.6초를 독립적으로 추가 판정하거나 계속 보류하고, 단독 메인 누락과 보류 장면의 보존 여부를 분리해 본다.
- 얼굴 identity·멤버 이름·crop·최종 clip 품질, 기존 YOLO와 같은 입력 pose 비교는 이 결과가 답하지 못한다. 제품 코드·W14 공통 얼굴 파일·기존 앱 결과는 이번에 수정하지 않았다. 새 ML·clip export·commit/push/merge/deploy는 없었다.
