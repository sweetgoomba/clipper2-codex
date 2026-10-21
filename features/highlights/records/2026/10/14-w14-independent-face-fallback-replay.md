# W14 — 안무 구간 수정과 분리한 얼굴 매칭 진단

2026-10-14. W13의 르세라핌 구간·메인 역할 개선을 기다리는 동안 W14가 소유한 **얼굴 선택·멤버 비교·보류**만 따로 점검했다. 이번 턴의 새 모델 다운로드·얼굴 모델 추론·제품 코드 수정은 0회다. 저장된 모델 결과의 재판정과 새 무대 원본 프레임 확인을 수행했다.

## 먼저 내린 판단

기존 SeetaFace6 일반형으로 SFace를 전면 교체하는 안은 앞선 비교에서 다른 두 영상의 식별 가능한 얼굴 19개 중 정답 확정이 SFace 15개, Seeta 13개여서 기각했다. 이 결론은 유지한다. 이번에는 **SFace가 이미 확정한 이름을 유지하고**, SFace가 보류한 경우에만 Seeta가 확정하고 SFace의 원시 1위 후보도 같은 멤버일 때 이름을 보충하는 좁은 규칙을 시험했다. 몸↔얼굴 연결이 무효한 경우에는 보충하지 않는다. 두 모델의 거리 숫자·embedding·참조 캐시·threshold를 서로 섞지 않았다.

시험 전에 [규칙·입력 해시·검사 기준을 계획 파일](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/independent-w14-cascade-v1/plan.json)에 저장했다(SHA-256 `714804b5eeeade8a4f8e251f6151d7a50e673740becf59416a2ae9fb2aa300af`). 입력은 기존 SFace·Seeta 판정과 사용자 확인 라벨이다. 별도 새로운 임계값은 맞추지 않았다.

## 저장 결과 재판정

| 기존에 확인한 자료 | SFace 정답/오배정 | 제한 보충 정답/오배정 | 추가 정답 |
| --- | ---: | ---: | ---: |
| 예전 안무 메인에 연결된 얼굴 34개 | 18 / 0 | 20 / 0 | 2 |
| 다른 두 영상에서 식별 가능한 얼굴 19개 | 15 / 0 | 16 / 0 | 1 |
| 따로 사용자 확인을 받은 메인 시점 2개 | 1 / 0 | 2 / 0 | 1 |

이 세 행은 각각 다른 관측 ID이나, **모델 선택과 실험 과정에서 이미 살펴본 자료**다. 70개 전체 관측에는 안무 34개, 다른 영상 34개, 메인 시점 2개가 있다. 다른 영상의 식별 어려운 멤버 4개, 등록 외 인물 5개, 판단 어려움 5개, 비얼굴 1개는 전부 미배정으로 남았다. 새로 배정한 4개는 `s0043-p0-f3696` 혜인, `s0057-p0-f6176` 민지, `s0032-p0-f1544` 다니엘, `6bVUjsUi9sw-128-face-002` 혜인이다. 앞의 안무 얼굴 라벨은 과거 사용자 라벨을 같은 원본 프레임의 유일한 얼굴과 IoU 0.5 이상으로 연결한 것으로, 새 crop 전수 재확인은 아니다. 다니엘 메인 시점의 라벨은 사용자가 그 시점 메인 사람을 직접 확인한 것이며 얼굴 사진만의 식별성 라벨은 아니다.

[전체 70개 행과 계산 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/independent-w14-cascade-v1/result.json) SHA-256 `af04676f267ab8c0dc26fb11a03b85782962becdef5ffb70819930f91ab4b1e3`을 별도로 [독립 재계산 스크립트](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/independent-w14-cascade-v1/audit_replay.py)로 검산했다. 원본 입력 세 파일·계획 SHA, 70개 고유 ID와 전 판정, 기존 SFace 확정 보존, 무효 연결의 보충 금지, 새 배정 4개와 기록 정답 일치를 확인했다. [감사 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/independent-w14-cascade-v1/audit.json) SHA-256 `e12b5d0b57323dc5a9ba616f275c0f83b1cf488398a21e8cce1a4fcb0457ce6c`. 모델 호출은 0회다.

이 보수적 규칙은 저장 정답을 아는 상태에서 보면 Seeta가 맞힌 얼굴 3개를 추가로 보류한다. 세 얼굴에서 SFace 원시 1위는 다른 멤버였기 때문이다. 따라서 보충 규칙도 아직 최적이라고 할 수 없다. 이 자료를 보고 규칙을 완화하면 같은 자료에 맞춘 사후 조정이 되므로 바꾸지 않았다.

## 새 르세라핌 무대에서 W13 없이 한 일

사용자 지정 원본 SHA `8feb03c0283c0d50eaab88ad7237524d6eacab9ad874d2b38258ecab3bc67517`의 저장 YuNet 후보 중, 0–210초의 10초 구간별로 `폭≥90px`, `높이≥100px`, 검출 점수 `≥0.8`을 만족하는 가장 큰 얼굴 하나씩 21개를 **멤버 점수·W13 역할을 보지 않고 먼저** 고정했다. [선정 규칙과 얼굴 ID](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/face-only-source-review-v1/selection.json) SHA-256 `73655359ea62462eac735843b31675c48047ca19d1dcf157d2e6942ef2264ca9`, [원본 crop 한눈에 보기](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/face-only-source-review-v1/source-review-contact.jpg) SHA-256 `698ef86e5ac3b3127f539f838b412d95ecceff5d998a07f4f37f1addb4d7b956`. 원본 디코딩 21프레임의 크기·crop 저장을 확인했다. 02는 팔에 크게 가리고 12·15는 작거나 흐려, 면적 최대 선택이 식별 가능한 얼굴 최대 선택과 같지는 않다. 이 21개가 안무의 **메인 인물 얼굴**이라는 주장도 하지 않는다.

등록 사진 21장의 기존 SFace 특징에서는 각 사진의 가장 가까운 다른 사진이 모두 같은 등록 멤버에 속했고, 자기 사진을 뺀 멤버 평균도 21장 모두 자기 멤버가 1위였다. [참조 사진 내부 점검](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/sface-embeddings-v1/reference-coherence.json) SHA-256 `0301871b71778de00dca99c69c5dad0ac22fcf7961ebb0d1b413f7e79ed973df`. 이는 **등록 사진끼리 구별된다는 검사**이며 무대 얼굴의 실제 인식률이나 사진 라벨의 정확성을 증명하지 않는다. 새 무대 21개에는 아직 독립 멤버 정답이 없고, 후속 탐색 중 일부 SFace 순위를 열람했으므로 W14 자체 사후 이름 붙이기를 블라인드 정답으로 계산하지 않는다.

## 새 무대에서 메인 몸↔얼굴 연결을 따로 검사

W13이 저장한 **35번 기준 후보와 69번 후보**의 같은 원본 SHA·PTS·1920×1080 좌표를 읽어 W14 얼굴 1,104시점과 정확한 프레임으로 연결했다. W13 파일은 읽기 전용이다. 기존 W14의 코·얼굴 위치 연결 adapter를 그대로 적용했고, 멤버 점수와 이름은 사용하지 않았다. [고정 입력·상한](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-association-v1/plan.json), [재생 코드](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-association-v1/replay.py), [전체 시점별 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-association-v1/result.json) SHA-256 `4d9dddd5d77d2f2dd3f3ecebb34d4f32c60200423f68ce3afc008d0965ddd036`.

| 1,104개 얼굴 표본 시점 중 | W13 35번 | W13 69번 |
| --- | ---: | ---: |
| 단독 메인 역할 후보 | 517 | 522 |
| 그 몸의 얼굴을 위치상 하나로 연결 | 434 | 435 |
| 얼굴 연결 모호 | 53 | 53 |
| 단독 메인이나 얼굴 연결 실패 | 30 | 34 |

69번의 연결 실패 34개는 메인 머리 근처 얼굴 없음 26, 프레임 내 얼굴 검출 없음 5, 메인 머리 관절 불안정 3으로 나뉜다. **435개는 얼굴을 위치상 연결했다는 수이지 올바른 메인 인물 선택이나 멤버 이름 정답 수가 아니다.** 앞서 큰 얼굴만 고른 21시점은 69번 기준 13시점이 역할 불확실, 단독 메인 8시점 중 3시점은 큰 얼굴과 연결된 메인 얼굴이 달랐다. 따라서 처음 21개를 안무 메인 인식 정답 분모로 쓰지 않는다.

이를 바로잡기 위해 69번이 단독 메인을 고르고 기존 연결 adapter가 한 얼굴을 확정한 시점만 사용해 **모델 점수와 무관하게** 0–190초의 10초 구간마다 가장 큰 얼굴을 하나씩 다시 골랐다. 폭≥90px·높이≥100px·YuNet 점수≥0.8을 만족하는 20개 구간 모두에서 얼굴이 있었다. [선정 규칙](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-source-review-v1/plan.json), [20개 얼굴 ID·원본 crop 해시](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-source-review-v1/selection.json) SHA-256 `b6f773cf67eccfdc4da62b851d20684e4584cf1aac996473568214c5e1b68c50`, [원본 얼굴 한눈에 보기](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-source-review-v1/source-first-main-face-contact.jpg) SHA-256 `727393c72c5c709400b5cccde87d943f655b0f9461696f3e311209dfd5934863`. 원본 crop 20장과 contact를 직접 보고 모두 얼굴임을 확인했다. 52.1초는 움직임으로 흐려 신원 판단 가능성을 별도 확인해야 한다. 독립 [선정/해시 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-source-review-v1/audit.json)에서 20구간의 최대 면적 선택과 crop 해시를 전수 검산했다. 새 모델 추론은 0회다.

이 20개도 **W13이 고른 몸에 연결된 얼굴**이지 W13의 메인 판정이 맞다는 뜻은 아니다. 각각의 얼굴 자체가 어느 멤버인지, 이 얼굴만으로 식별 가능한지, 어느 구간이 올바른 메인 클립인지는 아직 별도 정답이 없다. 점수·이름 없는 [로컬 검토 화면](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-source-review-v1/index.html)을 저장했으나 앱 내 브라우저의 `file:` URL 정책이 자동 열기를 차단해 UI 동작 확인은 하지 못했다. 원본 이미지 20개는 로컬 이미지 도구로 직접 확인했다.

## 현재 결정과 다음 검증

- 제품 기본 YuNet+SFace는 유지한다. Seeta 전면 교체와 이번 제한 보충 모두 **제품 미채택**이다. 후자는 기존 자료에서 네 얼굴을 추가로 맞힌 탐색 결과이며 새 영상의 오배정률을 증명하지 않는다.
- W14는 W13이 구간을 다듬는 동안에도 독립 얼굴 평가 자료를 준비할 수 있다. 이번에 메인 몸에 위치상 연결된 얼굴 20장을 원본 기준으로 고정했다. 다음 유효한 비교는 **모델 결과를 가린 상태에서 각 얼굴의 멤버/식별 가능 여부를 먼저 확정**하고, 동일한 원본·참조·검출 얼굴에 SFace 단독과 제한 보충을 적용해 새 오배정 및 회복을 함께 세는 것이다. 가린 얼굴/비얼굴과 메인 몸↔얼굴 오연결은 별도 분모로 둔다.
- 안무 제품 연결 검증에는 W13의 실제 선택 메인·교대 경계가 추가로 필요하다. 현재 르세라핌 W13 69번은 구간 459개 중 401개가 1초 미만인 평가 후보이며 사용자도 품질이 불량하다고 확인했다. 이 상태에서 W14 얼굴 한 장의 맞힘을 전체 클립 정답으로 전파하지 않는다.
- Seeta 일반형을 실제 앱에 넣으려면 약 102.5MB ONNX 파일과 선택적 ONNX Runtime 경로, 정확한 재배포 고지, Apple Silicon/Windows x64 설치 실행, 시작 지연·메모리 검증이 추가로 필요하다. 이번 재생은 그 검증이 아니다.

파일 소유: W14 평가 출력·이 문서만 수정했다. W13 포즈/구간, 공통 얼굴 공개 API, Person 제품/UI, 기존 결과, 다른 세션의 worktree는 수정하지 않았다.

## 10/14 후속 — 사용자 확인 얼굴 20장으로 새 영상 전이 비교

사용자가 번호 00–19의 **표시된 얼굴 자체**를 `홍은채/김채원/카즈하/허윤진/사쿠라`로 18장, `판단 어려움`으로 05·14 두 장 라벨했다. 원문과 순서를 [잠금 라벨](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/main-face-source-review-v1/user-face-labels.json)에 저장(SHA-256 `d308fd6e8d443e52e53050ecd9ca825c68c014a5cb798041c89eddc9df151b65`)한 **뒤** 새 Seeta 추론·채점을 실행했다. 라벨은 W13이 고른 몸이 실제 안무 메인인지, 그 앞뒤 구간 전체가 한 멤버인지에 대한 정답이 아니다. 얼굴 선정은 앞 절의 사전 고정 20개 그대로이고 이름·모델 점수로 재선정하지 않았다.

이전 NewJeans 개발 자료에서 정한 SFace/Seeta 각각의 centroid 거리·margin 기준과 제한 보충 규칙을 [사전 계획](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/user-labelled-face-comparison-v1/plan.json) SHA-256 `7aedcf3bd0bf3c4b56600b5bdbccb6e0e35f04e322d7b7ec34568a97ec8d3431`로 잠갔다. 같은 원본 얼굴·기존 멤버별 참조 21장을 사용하되, SFace 기존 특징과 Seeta 전용 정렬·특징 공간은 별도 유지했다. 신규 모델 다운로드는 없었다. 기존 YuNet으로 참조 사진만 21회 재검출해 같은 얼굴 상자/점수를 확인했고 SeetaFace6 Normal ONNX 41회(참조21+영상20) 추론했다. 전체 실행은 Mac arm64 CPU/ORT 1.24.4/OpenCV 4.13.0에서 약 2.84초, worker peak RSS 1.27GB였다. 외부 `/bin/ps` 접근이 sandbox에서 막혀 supervisor RSS 표본은 0으로 남았지만 worker 내부 `ru_maxrss`로 상한 4GiB를 확인했다. 모델 load 약 0.08초, Seeta forward p50 0.0063초/p95 0.0119초는 이 소규모 실행의 호출 시간이며 전체 앱 지연이 아니다.

| 사용자 식별 가능 얼굴 18장 | 정답 확정 | 다른 멤버로 오배정 | 보류 |
| --- | ---: | ---: | ---: |
| 기존 YuNet+SFace | 14 | 0 | 4 |
| YuNet+Seeta 단독 | 13 | 0 | 5 |
| 기존 확정 보존+제한 Seeta 보충 | **16** | **0** | 2 |

보충된 것은 00·18의 홍은채 두 장뿐이다. 02 카즈하·12 홍은채는 계속 보류했다. SFace가 확정한 14장은 전부 유지했다. 사용자가 식별할 수 없다고 한 05·14는 정오답 계산에서 빼고 별도 확인했으며 세 방식 모두 보류했다. [20장 전체 번호별 원본·배정 비교](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/user-labelled-face-comparison-v1/comparison.md), [전 거리·판정·실행 기록](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/user-labelled-face-comparison-v1/result.json) SHA-256 `f17dc98aa6560203089a53b42bb76fe01a4e19e2be1f4d8e9d301cd2742d8c0b`에 보존했다. 독립 [재계산 감사](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/user-labelled-face-comparison-v1/audit.json) SHA-256 `92cc2abe00e795e80ba0534f73931bb8e12c725b9e126dae184767a3ce390bd9`는 원본/모델/참조/정책 해시, 20개 두 모델 거리·문턱·보충·분모, 41회 호출/오류 0을 확인했다. scoring 단위 테스트 4개도 통과했다.

**판정:** Seeta 단독 전면 교체는 이 새 영상에서도 SFace보다 정답 확정이 적어 유지하지 않는다. 보수적 보충은 이 20장에서는 정답 두 장을 회복하고 새 오배정을 보이지 않아 다음 검증 후보로 남긴다. 그러나 선택 20장의 얼굴 가로 중앙값은 약 199.5px로, 같은 W13 69번 단독 메인·W14 얼굴 연결 확정 435시점의 중앙값 123px보다 크다. 화면의 모든 작은·흐린 얼굴, 다른 촬영/공연, 메인 몸 선택 오류, 구간 경계, 클립별 최종 분류가 검증된 것은 아니다. 오배정 0/18도 실제 오류율 0의 보증이 아니다. 따라서 **제품·공통 API·W13 adapter에는 아직 넣지 않고 기존 SFace를 유지**한다. 다음은 W13이 다듬는 구간을 기다리지 않고 W14가 이미 저장한 435개 연결 시점에서 더 작은/흐린 얼굴의 원본 우선 라벨과 메인 몸↔얼굴 오연결을 분리한 평가를 준비한다. 전체 구간 적용은 W13의 안정된 메인·경계 결과와 별도로 결합 평가해야 한다.
