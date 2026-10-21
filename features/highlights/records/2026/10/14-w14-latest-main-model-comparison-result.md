# W14 — 최신 안무 메인 얼굴 고정·세 인식 모델 비교

2026-10-14 KST. 사용자 진행 승인에 따라 이전 단계의 W13 iteration27 출력, 129개 선택 얼굴, 23개 참조 사진을 고정하고 기존 설치 모델들을 비교했다. **AuraFace와 Intel0095를 교체안으로 채택하지 않는다. SFace의 과도한 보류·혜인 구별 문제도 해결되지 않았다.** 테스트 통과는 계산·기록의 검증이며 품질 개선 성공을 뜻하지 않는다.

- [동일 얼굴·멤버별 구간·원본 재생 비교](http://127.0.0.1:58261/latest-main-models-v1/index.html)
- [실행 전 계획](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python/docs/superpowers/plans/2026-10-14-latest-main-model-comparison.md)
- [고정 입력/모델/hash manifest](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/latest-main-models-v1/manifest.json)
- [결과·회복·회귀 ID 원문](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/latest-main-models-v1/summary.json)
- [독립 검산](/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/latest-main-models-v1/verification.json)

## 1. 고정 입력과 실행 경계

- 기존 격리 branch `feature/shared-reference-face-matching-20261013`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e` + manifest에 기록한 평가 코드. 제품/core/W13 및 기존 GT 수정 없음. 새 worktree/채팅/세션 메시지/commit/push 없음.
- 원본 `yFTAYXDTjqI/source.mp4`, 1920×1012, 133.654059초, 60000/1001fps. SHA256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`.
- W13 `role-continuity-27/revision-a` combined frames/segments, `handoff-26/revision-b/recent_bridge-pose.json`을 이전 W14 실행 그대로 사용. W13이 그 뒤 갱신한 결과를 이 비교에 섞지 않았다.
- 70구간 중 single40/joint1의 42 segment×main 범위. group7/unknown22는 멤버 분류 대상 아님. 서로 다른 구간의 같은 track 숫자를 자동으로 합치지 않는다. 진짜 shot 경계/물리적 동일인 연속성이 보증된 것은 아니다.
- 전체 표본161개: 얼굴 선택129, 연결미정21, 연결모호11. 32개를 결과에서 지우지 않았다. 얼굴/몸/frame/GT 연결을 모델별로 바꾸지 않았다.
- 기존 사용자 정답 원본 hash `684cbd4d1a40904e64b43b9b9efeeaad52a94e7dafebee1a7ecfd2f4399b2aec`. 같은 frame에서 유일한 얼굴 IoU≥0.5인 항목만 연결한다. 알려진 멤버34개/식별가능 표시28개, identity 없는 품질 답변1개. 이는 새 crop 재확인이나 구간 전체 정답이 아니다.
- 참조23개 및 모델별 참조 특징 캐시 재사용. 가중치·정렬/전처리·차원·runtime·거리 기준을 분리한다. 같은 얼굴 bbox/5점이어도 모델에 필요한 정렬은 다르므로 **모델+필수 정렬 비교**다.
- manifest SHA256 `b138a5aeb95e5a071d979252e94b1702fed81c584bb9aaeafbd99eec6f52f502`, parent manifest `84840f8ce2e461a25cc575af230e748837a4c81b48b2248099ec6a505ef912d5`. 입력189개 hash 검증.

## 2. 모델·판정 기준과 실제 추론

이번 결과를 보고 기준을 조정하지 않았다. 이전 개발자료에서 정한 centroid cosine distance 최대값/1·2위 거리 차이 최소값을 그대로 사용한다. 최종 범위는 최소2개의 지지 관측을 요구한다.

| 모델 | 정확한 파일 | 차원 | 최대 거리 / 최소 차이 | 이번 새 추론 |
|---|---|---:|---|---:|
| SFace | face_recognition_sface_2021dec.onnx | 128 | 0.7239670157 / 0.1353327632 | 0 (129개 캐시) |
| AuraFace-v1 | glintr100.onnx | 512 | 0.6163947582 / 0.0498022437 | 129 |
| Intel0095 | face-reidentification-retail-0095.xml/bin | 256 | 0.5232793689 / 0.1566085219 | 129 |

- SFace hash `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`.
- Aura hash `a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60`.
- Intel XML hash `6cf60c341452155e35c467510c6c50a96ade5b2bd8f88c5a90902e905d8a80c3`; BIN `21319b95e54181857f99e22dc32ec89770eca2969a1432cfa1594bffc94edd62`.
- Apple M4 / macOS27 arm64 / Python3.11.12 / OpenCV4.13.0 / NumPy2.4.4 / ORT1.24.4 / OpenVINO2026.4.1。CPU1thread・batch1。`CI=true`로 OpenVINO telemetry 옵트아웃. 신규 다운로드·설치·유료API 없음. 검출/참조/자세 추론0.
- 모델별 180초/4GiB, 전체 출력300MiB 상한, ps 250ms 외부 감시, 순차 실행. 모든 worker exit0·중단/자동재시도 없음. 새 추론258회 모두 성공, 정렬/추론 오류0. 실패 발생 시 invalid observation으로 합의에 전달하는 경로도 회귀 테스트했다.
- 원본 재디코딩 후 저장 얼굴 crop과 모델별129개 픽셀 완전일치 확인. SFace는 직전 원본 재현이 검증된 캐시를 사용했다.

| 모델 | worker 소요 | peak RSS | warm forward+L2 p50 / p95 |
|---|---:|---:|---:|
| SFace 캐시 처리 | 0.081초 | 66,093,056 bytes | 새 추론 아님 |
| Aura | 20.086초 | 1,172,062,208 bytes | 68.44 / 83.55 ms |
| Intel0095 | 11.825초 | 292,945,920 bytes | 6.393 / 7.311 ms |

위 시간은 이 장비의 단일 실행이다. warm은 첫 추론을 제외하고 decode/정렬을 제외한 forward+L2이며, 전체 worker 시간은 입력 검증 등 모든 준비를 포함하는 사용자 작업 전체 지연시간이 아니다. SFace 캐시 시간을 신규 모델 추론 시간과 속도 순위로 비교하면 안 된다. Windows/깨끗한 앱 설치/최소 OS 검증 아님.

## 3. 정답이 연결된 34개 얼굴 결과

| 모델 | 점수1위 정답 | 올바른 확정 | 잘못된 확정 | 보류 |
|---|---:|---:|---:|---:|
| SFace | 28 | 9 | 0 | 25 |
| Aura | 21 | 8 | 0 | 26 |
| Intel0095 | 18 | 1 | 1 | 32 |

식별가능 표시28개만 따로 보면 올바른 확정은9/6/1, 잘못된 확정0/0/1, 보류19/22/26이다. 다니엘·등록 외 정답이 없고 인접 얼굴 표본이 포함되므로 전체 영상 정확도/낮은 FAR 보장이 아니다. 모든129개 중 성공한 것만 분모로 고르지 않았다.

- Aura: SFace 보류에서 정답으로 회복4개, 기존 정답에서 보류로 회귀5개. 새 오확정0. 순증 개선 아님. 회복/회귀 전체 ID는 summary에 보존했고 화면에 각각 대표 바로가기 제공.
- Intel: 회복0, 기존 정답8개를 보류, 새 오확정1개. 모델이 작은 것은 사실이지만 이번 매칭 품질로 교체할 근거가 없다.
- 혜인 정답10개에서 올바른 확정은 **세 모델 모두0**. SFace 점수1위 정답7개지만 확정 기준 미통과, Aura 점수1위4개·전부보류, Intel 점수1위1개·오확정1개.
- 구체적 실패 `s0051-68-f3492`, 58.2582초, 사용자 혜인 답변과 IoU0.933189 연결. SFace 최근접혜인0.63992이나 해린0.64700과 차이가 작아 보류. Aura 최근접하니0.74740로 거리 미통과. Intel은 해린0.52205/2위하니0.70389로 기준 통과해 **얼굴을 해린으로 잘못 확정**. 그러나 같은 범위의 지지2개가 없어서 **구간51 전체는 보류**다.

해석: SFace도 과도한 거부와 멤버 혼동이 남는다. 대안 두 모델은 이번 동일 메인 얼굴에서 그 문제를 해결하지 못했다. 거부 기준만 낮추면 올바른 배정이 늘 것이라는 이유로 오배정 위험을 무시할 수 없다. 인식 점수 분리력/참조와 영상 조건/거부 규칙을 분리해야 하며, 이번은 그 원인을 하나로 확정한 실험이 아니다.

## 4. 시간축 결합도 함께 대조

세 모델 각각 기존 개별 비교 합의와 기존의 보수적 특징 평균 결합안을 동일하게 적용했다. 특징 공간 간 혼합 없음. 결합안은 invalid/충돌을 숨기지 않고, 서로 다른 2시점 이상·0.25초 이상·최근접 멤버 일치·평균 특징의 동일 거리/차이 기준 통과를 요구한다. 같은 scope 자체의 물리적 동일인 보장은 여전히 별도다.

| 모델 | 전체42범위 배정: 기존→결합 | 일부 얼굴 정답이 있는14범위: 일치/보류 기존→결합 |
|---|---|---|
| SFace | 12→18 | 7/7→7/7 |
| Aura | 8→11 | 4/10→5/9 |
| Intel0095 | 6→7 | 1/13→2/12 |

14범위의 일부 정답과 상충하는 확정은 없지만, 구간 전체 정확도가 아니다. GT 없는 범위 배정 증가를 개선으로 세지 않는다. 혜인 범위는 세 모델 모두 결합 후에도 보류다. 신규 모델과 시간 결합안 모두 제품 채택 근거가 부족하다.

## 5. 실제 검증과 독립 리뷰

- 관련 pytest **170 passed**: `evaluation/candidate_comparison`, `evaluation/segment_review`, `clipper_face_core/tests`. 모델 전체 부팅/제품 전체 회귀를 수행했다는 의미 아님.
- 독립 거리2,045개 재계산(SFace690/Aura685/Intel670), 최대 오차1.1921e-7. 합의/결합 정책126개 검산, 모든161행의 source/시간/몸/얼굴/정답 연결 불변, 42범위·129선택 관측의 정확한 포함 확인. SFace 이전 판정 재현.
- 최종 독립 리뷰 Important1건: 기존 검산기가 emitted match만 검사해 누락/후보 순서/상태 불일치를 놓칠 수 있었음. 저장 실제 결과에는 이 오류가 없었다. 누락·오류관측 소실·row/scope 불일치·순서/후보 수·거부 사유·margin·최종 상태·사용ID·scope 누락/중복 변조 테스트에서 **13 RED / 3 PASS → 16 PASS** 확인 후 검산기 보완. 원래 ML runner/고정 결과/manifest는 수정하지 않고 전체170테스트 및 실제 검산 재통과.
- Node 문법 검사 및 실제 브라우저에서 모델 전환·멤버 필터·빈 목록의 재생 비활성화·회복/회귀/오배정 사례·같은 얼굴의 세 정렬 이미지·원본 재생/구간 끝 정지를 확인. 재생 중 정지 시점 박스를 숨긴다. 원본 player의 timeupdate 정지는 export frame 경계 보장 아님.
- UI는 읽기 전용이며 기존 사용자 답변 storage/내보내기/옛 비교 페이지를 건드리지 않는다. 정답 없는 얼굴도 남긴다. 새 페이지와 코드/결과/스크린샷 hash는 artifact manifest로 별도 보존.

## 6. 소유권·통합·남은 입력

W14가 `evaluation/candidate_comparison`의 평가 adapter/검산/리포트만 추가·수정. public core, 기본 SDK 시작, 플러그인별 venv, W13 main/mapping/crop/제품 adapter 변경 없음. 신규 모델 API 승격/실제 안무 앱 통합/merge 아님. 라이선스는 이전 정확한 파일 조사 경로를 유지했으며 이번에 별도 법적 검토를 새로 완료한 것이 아니다.

통합 순서: W14 공개 API·고정 fixture → W13 source/동일인 scope/관측 실패 계약 compatibility → W13 소비 adapter·선택 의존성·모델 준비 → Mac/Windows 실제 패키징 → 합의한 병합. 서로 다른 모델 캐시/threshold 혼용 금지. 새 계약을 W13이 이번에 수락했다는 주장은 하지 않는다.

다음 조사 우선순위는 현재 입력에서 점수1위가 맞아도 확정되지 않는 사례와 아예 다른 멤버가 더 가까운 사례를 분리해, 참조 조건/판정 기준의 실제 영향을 평가하는 것이다. 이미 실패한 참조42px·두눈정렬·단순평균 대조를 같은 이름으로 반복하지 않는다. 개발자료에서 선택한 규칙을 별도 영상에 고정 적용해야 하며, holdout 자료를 보고 재튜닝해 검증 성과로 주장하지 않는다.

남은 근거: 새 두 영상의 혜인/하니·등록 외 정답 확대, 최신 W13 동일인 연속성/shot 계약과 실제 안무 최종 분류, 전체 구간 정답, Windows x64 및 Apple Silicon 깨끗한 설치·선택 runtime 패키징. **이번 비교 완료에 사용자가 추가로 조작하거나 정답을 입력할 필요는 없다. 품질 개선 완료는 아니다.**
