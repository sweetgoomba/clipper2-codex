# W14 몸 경로별 얼굴 근거 소비 계약 — 구현·저장 자료 비교

2026-10-14. 사용자 「진행해줘」에 따라 앞선 시간순 진단의 후속을 실행했다.
Superpowers 설계/검증·TDD·독립 리뷰 적용. **평가 adapter만 변경했으며 제품 연결은 아니다.**

## 1. 쉽게 읽는 결론

전에는 한 구간 안의 얼굴을 모두 합쳐서 이름을 정했다. 앞부분은 누구인지 모르고
뒷부분에서만 혜인을 알아봐도 구간 전체가 혜인이 될 수 있었다.

이번에는 안무 출력의 몸 경로마다 얼굴 판정을 따로 계산했다. 모든 경로에 충분한
얼굴 근거가 있고 그 이름도 같을 때만 전체 이름을 준다. 앞부분을 모르더라도 뒤쪽에서
알아본 혜인 결과는 사라지지 않는다. 앞부분의 모름과 뒤쪽의 혜인을 함께 보존한다.

**인식력이 높아진 것은 아니다. 근거 없는 부분까지 이름을 넓히던 평가 처리를 막았다.**
모델/점수/참조 사진은 그대로이며 새 모델 추론은 0회다. 특히 SFace 다니엘 사례처럼
표본이 적으면 추가 보류도 생겼다. 그러므로 이 규칙만 넣고 제품 품질 개선 완료라고
판단할 수 없고, 과도한 미매칭에 대한 평가와 경로별 표본 보완이 남는다.

[전후 비교·원본 재생](http://127.0.0.1:58261/run-scope-contract-v1/index.html)

## 2. 이번 범위와 고정 입력

- Python 격리 worktree: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python`
- branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e`.
- W13 **35번 고정 출력**의 구간·메인·source track runs를 소비했다. 현재 보드의 W13 42번 출력이나 제품을 검증한 결과가 아니다.
- 기존 36 참여자 범위×기존 표본선택 3방식×3모델=324개, 진단 5범위×3모델=15개. 합계339개 비교.
  공동 메인은 참여자별로 별도 scope다. 독립적인339개 영상/정답은 아니다.
- 저장 표본 243+238개(서로 겹치는 시점 있음), 각3모델의 기존 match1,443개를 원본과 완전히 동일하게 재현했다.
- 모델: YuNet 검출 저장 결과 + SFace / AuraFace-v1 / Intel0095 저장 embedding.
  모델별 임베딩 공간·참조23사진·threshold·margin·최소근거2개 고정.
- native source SHA `74e4769a59b0f73bf9e5f909549f441f38e95dc7691905c419bfdc52510d4013`,
  기존1080 source SHA `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`.
  모델/입력/캐시 세부 hash는 원래 manifest와 이번 `plan.json`을 따른다.
- 이번 원본 동영상 재디코딩/모델 로딩/추론/다운로드/설치/유료 API는0회. 브라우저 원본 재생은 별도 UI 검증이다.

## 3. 구현 내용과 경계

파일은 위 Python worktree 기준이다.

- `evaluation/segment_review/run_scoped_matching.py`: 경로별 판정 후 전체 참여자 판정.
- `evaluation/segment_review/test_run_scoped_matching.py`: 신규 회귀24개.
- `evaluation/segment_review/RUN_SCOPE_CONTRACT.md`: 입력/출력·실패·소유권·통합 계약.
- `evaluation/native_sampling/run_scope_replay.py`: 고정 입력/기존 판정 정확 재현/339개 비교.
- `evaluation/native_sampling/audit_run_scope.py`: adapter를 호출하지 않는 거리/근거/판정 검산.
- `evaluation/native_sampling/build_run_scope_report.py`, `run_scope_report.js`: 결과 설명/원본/얼굴 확인 화면.

얼굴이 없는 경로도 예정 목록에 남긴다. 한 번 확정된 다른 멤버 근거를 다수결로 지우지 않는다.
정상 거부·연결 보류·추론 실패·표본 없음은 원래 사유와 함께 보존한다. 같은 관측 중복으로
근거 수를 늘릴 수 없으며, 같은 참여자의 동일 프레임 중복 ID도 차단한다.

원래 immutable 관측을 보존하고 경로 전용 scope로 복사한 뒤 저장 embedding에서
match를 다시 계산한다. 원본→경로용 fingerprint 대응을 기록하며 과거 match의 지문을
문자열로 바꿔 재사용하지 않는다. 모델 공간 혼용·잘못된 source/scope/track 배정은 오류다.

`conflict_run_ids`는 이름 충돌, `unsupported_run_ids`는 표본/유효 얼굴/근거 부족이다.
두 문제가 동시에 있을 수 있다. 전체가 보류여도 `runs[].reference_id`를 보존한다.
공통 core API에 Dance `BodyRun`·UI·job 객체를 넣지 않았다.

## 4. 실제 결과

### 전체 이름이 달라진 4개 비교

| 자료/모델/선택 | 구간 | 이전 전체 이름 | 수정 전체 이름 | 남아 있는 경로별 근거 |
|---|---|---|---|---|
| 36범위/SFace/시간대별 선택 | 21.89–27.29초 | 다니엘 | 확인 필요 | 앞 경로 다니엘3, 뒤 경로 다니엘1로 최소2개 미달 |
| 36범위/Aura/간격 선택 | 57.26–63.06초 | 혜인 | 확인 필요 | 앞 경로 확정0, 뒤 경로 혜인2 |
| 진단5/Aura/전체 표본 | 57.26–63.06초 | 혜인 | 확인 필요 | 앞 경로33표본/확정0, 뒤54표본/혜인28 |
| 진단5/Intel0095/전체 표본 | 57.26–63.06초 | 혜인 | 확인 필요 | 앞 경로33표본/확정0, 뒤54표본/혜인4 |

339개 비교 중 다른335개는 전체 이름(null 포함)이 같다. 다른 멤버로 바꾸거나 신규 전체
배정을 만든 결과는 없다. **4개 추가 보류를4개 오류 수정/정답 개선으로 해석하면 안 된다.**

### 전체 이름이 붙은 범위 수 — 정답 수 아님

| 자료/표본선택 | SFace 이전→수정 | Aura 이전→수정 | Intel0095 이전→수정 |
|---|---:|---:|---:|
| 36범위/기존 시점 | 16→16 | 14→14 | 9→9 |
| 36범위/시간대별 | 15→14 | 14→14 | 9→9 |
| 36범위/시간 간격 | 16→16 | 14→13 | 10→10 |
| 진단5/전체 표본 | 3→3 | 4→3 | 5→4 |

SFace 다니엘은 적은 표본에서만 추가 보류됐다. 저장된 촘촘한 자료에서는 앞 경로44개,
뒤 경로30개가 다니엘을 지지하여 전체 다니엘이 유지된다. 이는 **표본 수집과 모델 실패를
분리해야 하는 사례**이며, 보수적 규칙의 미매칭 비용이다.

같은 촘촘한 다니엘 범위에서 Aura의 뒤 경로는 다니엘28/해린2가 충돌해 계속 보류다.
반대 이름2개를 지우지 않았다. 그 두 정확한 얼굴 시점의 사용자 GT는 없어 실제 오인식으로
확정하지 않는다. 혜인 앞 경로도 실제 인물 정답/연속성 전체를 이 시험으로 증명하지 못한다.

## 5. 검증 증거

출력 폴더:
`/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/run-scope-contract-v1`

- `plan.json`: 실행 전 입력/코드 hash 고정. SHA `0b9ab0b93b7c3433b84aa7ca33a6fc8bd09a9d39eda0f035f5d2e5b0b5ff9f58`.
- `result.json`: SHA `380a99f66fafe2eb43635bc91ca0e200e88523b62b6a93c40e649fca79a3bd93`.
  기존 얼굴 match1,443개 exact equality, 희소 baseline consensus324개 exact equality.
  진단15개 이전 전체 합의는 같은 관측으로 기존 공통 규칙을 다시 계산했다.
- `audit.json`: 거리6,300개, 경로 판정363개, 비교 속 개별 match1,605건, 전체 판정339개를 별도 검산.
  각 비교의 모든 observation ID가 정확히 한 경로에 보존되는지 확인했다.
- 신규 TDD: 미구현 상태24실패 → 구현 후24통과. 전체 관련 테스트165개 통과(0.88초).
  명령: `PYTHONPATH=clipper_face_core:. CI=true ../../evaluation-output/candidate-comparison-20261014/venv/bin/python -m pytest clipper_face_core/tests evaluation/segment_review evaluation/native_sampling -q`.
- 독립 reviewer가 adapter와 replay/audit를 검토했다. 중요한 코드/검산 결함 없음.
  희소 다니엘 추가 보류를 정확도 개선으로 쓰지 말라는 해석 지적을 결과/화면에 반영했다.
- 새 모델 추론0, replay2.754초/RSS53,051,392bytes. 저장 벡터 처리 비용이며 모델 추론 속도가 아니다.
- UI: 세 모델·세 대표 사례·얼굴 연결 보류·개별 얼굴 전환·원본 구간 재생/종료 확인.
  재생 원본1920폭/readyState4, 이미지 오류0/console error0/가로 넘침0. 세부증거는 `verification.json`.

제품 전체 suite는 이번 범위에서 실행하지 않았다. 직전 평가 venv에서는
`clipper_video_render` 누락으로 제품 suite 수집이 실패한 이력이 있다.
Mac arm64 평가 Python만 확인했고 Windows 설치/모델 실행·제품 앱 전체 실행은 이번 검증에 포함하지 않았다.

## 6. 소유권·인계와 남은 일

- W14: 평가 adapter/공통 API/fixture. W13: 메인/몸/구간/mapping/crop/제품 소비 adapter.
  다른 worktree·기존 결과·사용자 정답/편집·공통 core·제품 코드를 변경하지 않았다.
- 순서: 계약/fixture 상호 확인 → source·시간/좌표·scope·실패 compatibility → W13 소비 adapter/
  선택 venv/모델 준비 → Mac arm64/Windows x64 설치 → 합의한 merge.
  이번 문서 갱신은 W13의 새 수락이나 merge/배포 승인 기록이 아니다. 다른 채팅에 메시지를 보내지 않았다.
- 다음 기술 작업: 경로별 표본 보완이 추가 미매칭을 줄이는지 고정 자료로 비교하고,
  계속 남는 얼굴 판정 충돌/혜인 앞부분의 인식 실패를 분리한다. 낮은 확신을 타인표로 보지 않고
  이미 확정한 반대 멤버의 근거는 보존한다.
- 별도 촬영 영상의 충분한 멤버/등록외/식별 가능 GT, 경로/구간 정답과 연속성 검증,
  같은 오배정률에서의 회복량·미매칭 비용, 런타임/양OS 패키징 검증이 남았다.
- 최종 모델 선택과 안무 제품 통합은 미완료. YuNet/SFace 대조군 유지,
  Aura/Intel0095 제품 교체는 이번 결과로 채택하지 않는다.
- 지금 사용자에게 필요한 추가 입력/클릭은 없다. 비교 화면은 확인용이며 정답 입력을 요구하지 않는다.

### 10/14 W14→W13 얼굴 소비 계약 후속: 작은 얼굴 신원 비교

동일 르세라핌 원본에서 사용자가 원본 작은 얼굴 13장에 신원 라벨을 제공했다. [고정 입력·13장 전 결과](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/small-face-user-comparison-v1/comparison.md)에 따르면 식별 가능 12장에서 YuNet+SFace 7정답/0오확정/5보류, Seeta 단독 2/0/10, SFace 뒤 제한 Seeta 보충 7/0/5다. **Seeta 추가 회복 0**이므로 이번 작은 얼굴 자료를 근거로 W13 소비 adapter나 공통 core의 기본 인식 모델·문턱·참조 캐시를 바꾸지 않는다. 얼굴 한 장의 라벨을 W13 메인 몸·run·구간 이름으로 전파하지 않는다. `no_face`/몸↔얼굴 보류/인식 보류를 구분하고, W13이 안정된 메인·교대·구간을 제공한 뒤 동일 source/face/track/timebase에서 compatibility를 재검증한다. W14 평가 산출물만 추가했으며 W13의 계약 수락, 제품 연결, merge/배포가 새로 이뤄진 것은 아니다. 파일 소유와 적용 순서는 위 §6 그대로다.

**동일 자료의 시간상 근거 후속:** [S00/S01/S02/S06/S08/S09 원본 진단](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/antifragile-holdout-20261014/temporal-face-diagnostic-v1/diagnosis.md)에서 W13 단독 메인 몸 ID와 W14 확정 얼굴 연결을 같은 임시 장면 안에서만 사용했다. 기존 SFace 보류 다섯 장 중 S02·S06 두 장에 동일 멤버 주변 확정 근거가 있었고 사용자 라벨과 일치했다. **S01의 W13 몸 ID가 79→82로 바뀌었다.** 계약 소비자는 같은 ID를 맹신하거나 다른 ID를 자동으로 이어 얼굴 점수를 합쳐서는 안 된다. `no_face`/연결 모호/타인 근거와 단순 무관측을 분리하고, W13이 메인·컷·교대의 안정된 run 경계를 제공한 뒤에만 재평가한다. 이번 사후 후보는 W13 adapter나 공통 API에 적용하지 않았으며 W13 수락/merge를 뜻하지 않는다. 파일 소유/merge 순서와 양 OS compatibility gate는 위 §6을 유지한다.
