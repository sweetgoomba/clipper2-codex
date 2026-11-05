# Dance mask cost reduction implementation plan

> Execution: superpowers:executing-plans. User explicitly approved the measured improvement sequence and conditional removal on 2026-11-02; do not request approval again.

**Goal:** Reduce unnecessary dance-only identity recovery work, compare packaged-app results for the same three YouTube URLs, then comment out the expensive mask recovery stage if any video still exceeds 60 seconds there.
**Architecture:** Preserve classification thresholds, model devices, sample cadence and all main-selection/face stages. First stop only provably failed or ineligible mask work. Evaluate through normal app runs. The user's explicit conditional removal overrides the initial output-parity constraint for that subsequent stage; report resulting quality differences rather than hiding them.
**Spec:** User request plus [measured causes](02-gpu-performance-results.md).

## Global constraints
- Original sibling checkouts, current fix/dance-gpu-performance-20261102 branch; retain existing uncommitted GPU improvements. No commit/push requested.
- Person plugin and shared code unchanged. No invented clip length limit, no relaxed quality thresholds.
- Original projects preserved; new runs use original YouTube URLs and identical artist/reference choices.
- Conditional threshold means any video mask_continuity stage >60 seconds; disable that supplemental SAM stage globally for dance if triggered, not basic YOLO tracking.
- Retain implementation and comment its pipeline invocation; preserve truthful disabled diagnostics and retain any context evidence needed by subsequent stages.

## Tasks and checks
- [x] 1. Tests first: reverse IoU failure stops further model calls and closes generators; passing path still traverses both directions. Group-only unresolved targets never call the verifier and retain all input classifications. Mixed main/group paths preserve eligible recovery. Implement only these proven rejection shortcuts before larger candidate selection changes.
- [x] 2. Focused mask/continuity tests and related dance/person regressions. Build original app using npm run build:app:mac:arm64:local-api. Compare full clip rows, people, frame decisions and source/reference hashes for three app submissions with the latest GPU-on baseline.
- [x] 3. If any mask stage exceeds 60 seconds, comment the supplemental call; test that normal pipeline executes without constructing MaskTracker and reports skipped stage. Rebuild and repeat three app runs, recording exact final output changes and all previously user-confirmed intervals.
- [x] 4. Independent final code review, final report and evidence in .codex. Keep final app open. No Windows hardware claim.

## Review focus
- Rejected reverse path must not become a recoverable partial prefix through a different reason.
- Generator finalizers release model/source state after early rejection.
- Main/group mixtures and short support retries must remain eligible.
- Disabled diagnostics must not claim successful model verification; downstream stages must not fail from missing keys.
- Wall timing excludes queue waits; baseline is same refs/model/config and original YouTube source.

## Ledger
- Original checkout follows established user preference; all prior GPU edits preserved. Initial tests will use current branch as baseline.
- Expensive context-candidate skipping after one name succeeds is deferred unless provably safe: competing identities can reveal incorrect ownership. Exact mask cache already exists; SAM prefix cache is unsafe because temporal attention depends on total path length. No arbitrary candidate limit added to claim quality parity.

- Task 1: complete. Baseline mask tests 130 passed. New regression cases first failed (3 failures/2 passes), then focused mask/cache suite 145 passed. Related dance/person suite 891 passed, git diff --check clean.
- Optimized app built successfully after explicitly selecting Node 24.19.0 (elevated shell initially picked unsupported system Node 24.3.0). Packaged modified service hashes equal source. App restarted, existing login retained.
- Three original YouTube jobs submitted through UI using unchanged saved reference profiles: Made My Night 1793567629022, ANTIFRAGILE 1793567681642, NEON 1793567756677. First running, other two queued. User's existing unlimited-credit authorization applies; 120 credits displayed for this round.
- Evidence workspace: /private/tmp/dance-mask-cost-20261102/optimized. Baseline is the immediately preceding GPU-on actual app runs 1793558808114 / 1793558865224 / 1793558916550. Reference selection and byte hashes compared before analysis completes.

- Optimized Made My Night completed: active 721.211s vs 719.981s baseline; mask 77.9676s vs72.1434s. No speed gain for this video. All83 clip rows, people and2324 diagnostic frames exactly equal. Threshold >=60s is now empirically met. ANTIFRAGILE and NEON optimized app runs continue to complete requested comparison before replacing the package.
- Prepared final source while optimized package remains unchanged: comment recover_mask_names import/invocation, record disabled_runtime_cost_v1/zero times and recovery. Test-first: four pipeline cases failed before,147focused cases passed after.
- Final independent code review found early IoU break and all-group skip safe. Important qualification promoted to fix: joint_identity also calls MaskTracker for unknowns, so leaving it enabled could shift the cost into that stage. User requested body stage entirely off once limit exceeded. Both SAM pipeline invocations/imports are now commented; implementations and unit coverage retained. Main YOLO, normal face matching, secondary face verification and cheap bridge_main_face_gaps remain.
- Regression now includes accepted frozen joint faces inside an unresolved interval: confirms no MaskTracker construction through either pipeline entry, no invented names, truthful disabled diagnostics. Four cases failed before the second call was commented;149focused tests pass after. Full related regression will run before final build.
- Context-face collection stays for now because the same function supplies source cuts/camera evidence to downstream boundary/context logic. Its unused identity-anchor collection is a remaining optimization; this change does not remove that evidence blindly.
- Reviewer could not judge final packaged speed/quality or remaining optimized runs because they were pending. Those are required completion checks, not waived. No other blocking code findings. No re-review after the single test-first fix pass.

- Optimized ANTIFRAGILE completed: active1154.669s vs1104.987s baseline; mask234.2258s vs225.7541s. No gain for this video. All123 full clip rows/person cards/3310 diagnostic frames/thumbnail bytes equal, all11 reviewed intervals across completed two videos unchanged. Source/model/config hashes equal. NEON started2026-11-01T21:45:06Z approximately (use job exact startedAt for final timing).
- Final source now comments BOTH recover_mask_names and revalidate_named_segments pipeline imports/invocations, preserves implementation functions, and records zero/disabled diagnostics. Additional behavior tests for unknown interval containing accepted joint faces failed before second-call disable and now pass. Focused suite149passed1.18s. Packaged app still runs the optimized version, untouched by source preparation.

- Optimized NEON completed:2133.574s vs2238.808s baseline (35m34s vs37m19s). Mask1163.120764s vs1279.728494s; still19m23s. All three:406full clip rows,9266diagnostic frames,person cards andthumbnailbytes identical;all14reviewed intervals unchanged;video/model/config/reference hashes equal. Optimized comparison complete.
- Final full dance+Person regression exposed4obsolete expectations in test_dance_member_timeline_pipeline (1158others passed). They required the now-commented SAM call and fake-SAM name correction. Updated those4cases to verify source ranges remain A0–6/B6–10, supporting C is never promoted, secondary face recovery/cut context remain, and constructing SAM raises. Focused4pass;full rerun pending. Product code did not change in this test alignment.
- Optimized app quit after all three jobs completed; final benchmark directory prepared at /private/tmp/dance-mask-cost-20261102/disabled.

- Final full regression:1162passed27.54s (52dance test files plus Person suite);git diff --check clean. Build-disabled.log confirms successful original-repo npm run build:app:mac:arm64:local-api using Node24.19.0. All51packaged Dance Python source files equal working source;both disabled audit markers present. App relaunched successfully with existinglogin.
- Final-body-disabled actual UI jobs: Made My Night1793571868350 running, ANTIFRAGILE1793571915955queued;same savedreference choices andbytesconfirmed.NEONsubmissioninprogress.

- Disabled final-round jobs:Made1793571868350,ANT1793571915955,NEON1793571975392. All UI-submitted original YouTube URLs andsavedreference selections/bytes equal.
- Disabled Made My Night completed603.000s vs719.981s baseline(16.25%faster),mask/joint both0s/noSAMmodel/disabled_runtime_cost. Source/model/config hashes equal;2324main diagnosticframes unchanged. Identity coverage changes2.45275s:사쿠라34.4344–34.8348 and38.204733–39.3393;홍은채68.301467–68.835533 and97.464033–97.84775 nowunknown. Unknown4.35445→6.8072s;clips83→89;subsecond38→42. Reviewed Sakura34.73–35.44 partlyunknown(.1048s) and37.738–39.339 partlyunknown(1.134267s). Kaz89–93 andotherfive reviewedwindows unchanged. These are real quality/boundary tradeoffs, not output parity; disclosed to user. ANTnextstarted,NEONqueued.
- After all final-round jobs finish: status-only follow-up needed in app.py get_runtime_accelerators:body_tracking currentlyreportsCPU withoutenabledflag. Add enabled=False/reason=disabled_runtime_cost withunitregression,thenrebuild/relaunch. Keep analysis code unchanged; recordfinalpackagevsbenchmarkhashes. No need three more analyses forread-onlystatusmetadata;documentthis distinction. Details:/private/tmp/dance-mask-cost-20261102/post-benchmark-note.txt.

- SAM 비활성화 ANTIFRAGILE 완료: 834.592초(13분 55초), 기준 1104.987초 대비24.47% 단축. SAM 두 단계0초, 모델 초기화/시도 없음. 원본·모델·설정 해시와3310개메인판정프레임 동일. 미확인8.175733→16.0178초(+7.842067초), 전체클립123→134, 1초미만73→79. 추가로117.3172–117.6175초의 이름이 기존사쿠라에서홍은채로 돌아감(교차교정제거). 원본시간축분류변화합계8.142367초. 검토구간홍은채4.571–6.139 대부분과김채원9.4–10.277 후반.367초가미확인으로바뀜;8.375–9.0은구간내분류는같고바깥클립경계만변경. 사용자에게손실공개완료. NEON최종측정진행중.
- Final report generator ready at /private/tmp/dance-mask-cost-20261102/write_results_report.py; refuses to emit until all three jobs completed. After remaining NEON run, refresh comparisons + reviewed-case-analysis, then make status-only runtime fix/test/build described above, and publish report/evidence under this record directory.

## 최종 완료 기록

- NEON 최종 실행 완료: 907.704초(15분 08초), 직전 GPU 앱 2238.808초 대비 59.46% 단축. SAM 복원/재검증 모두 0초이며 모델 초기화나 후보 시도가 없다. 미확인 12.246867→16.985333초, 전체 클립 200→208, 1초 미만 119→126. NEON의 사용자 검토 구간 3개는 유지됐다.
- 세 영상 합계 67분 44초→39분 05초, 42.3% 단축. 원본·모델·설정·대표 이미지가 같고 메인 판정 프레임 9,266개도 같다. 하지만 SAM 비활성화 후 이름 복원과 구간 연결 일부가 사라져 최종 클립 품질 동등성은 달성하지 못했다. 알려진 홍은채/사쿠라 구간의 미확인 증가와 짧은 클립 증가를 최종 보고서에 명시했다.
- 추가 상태 표시 수정은 app.py의 런타임 응답에만 한정했다. body_tracking.enabled=false 및 disabled_runtime_cost를 추가해 CPU에서 실행 중인 것으로 오해하지 않게 했다. 실패 테스트 확인 후 관련 테스트 9개 통과. 분석 파이프라인과 나머지 Python 파일 50개는 측정 앱과 같다.
- 최종 앱을 원본 저장소에서 지정한 명령으로 재빌드하고 실행했다. 앱에서 완료된 프로젝트 3개(89/134/208클립)를 확인했고, 실제 런타임 조회도 modelsLoaded=true 및 body_tracking.enabled=false를 반환했다. 최종 패키지의 안무 Python 파일 51개가 현재 소스와 일치한다.
- 안무/인물 관련 1,162개 테스트 통과와 상태 표시 관련 9개 테스트 통과 기록을 보존했다. 인물/공유 소스는 변경하지 않았다. Windows에는 동일한 비활성화 로직이 적용되지만 Windows 하드웨어 실측은 하지 않았다.
- [최종 결과·제약·남은 과제](02-mask-cost-reduction-results.md), [측정 증거 사본](02-mask-cost-app-evidence/publication-manifest.json). 커밋·푸시·병합은 하지 않았다.
