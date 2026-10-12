# W13 첫 MoveNet 실행 범위 — 승인·실행 기록

사용자가 아래 범위를 확인하고 `해`라고 답한 뒤 **CPU MoveNet metadata 평가 3회를 완료**했다. [실제 결과](01-w13-movenet-first-real-metadata-evaluation.md)와 [상세 manifest](01-w13-movenet-comparison-manifest.yaml)에 산출물·해시를 기록했다. manifest 상태는 완료로 바꿔 같은 파일로 재실행할 수 없게 했다.

| 항목 | 제안 범위 |
|---|---|
| 원본 | 기존 앱에서 이미 쓴 `/Users/jina/Library/Application Support/Clipper Studio Dev/sources/youtube/yFTAYXDTjqI/source.mp4` **0~133.654059초 전체**. SHA-256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`. 기존 프로젝트·원본은 읽기 전용. |
| 새 모델 | Google MoveNet MultiPose Lightning TF2 v1 로컬 SavedModel. 추출 디렉터리 SHA-256 tree `ea71312368f39053ed7b9b2e4fac3bcecd94c667f679830a0a999b31ccaf705c`, 보관 archive SHA-256 `f01b9e5e8c3bc31f82e9ca7fa4a2876f25d7a54b65c83da5df2eca3e1632cec8`. Google 배포 weight 표기는 Apache-2.0. |
| 무엇을 실행하나 | 격리 Python 평가 경로에서 pose 관측·현행 main selector/track을 **metadata로만** 기록. 얼굴 인식·멤버 이름·참조 사진·clip/썸네일 export·제품 기본 모델 변경 없음. 기존 YOLO 새 pass는 **0회**. |
| 라벨 | [고정 표본](01-w13-pose-scoring-labels-v1.json)의 SHA-256 `c76866b1962279b6320e0222dc47e4056d950e3068590df1902c078ebebad704`. 사람 검출 45명/9프레임과 빈 화면 2장; 메인 신원 4프레임. 다섯 솔로 기준 창은 합계 18초지만 창 전체를 채점하지 않는다. 그룹·전환·불확실 장면은 보존 검토. |
| 비교 결과 | 사람 검출 표본 건수, 네 메인 표본의 맞음/틀림/짝 미확인 건수, 6.0~112.5초 공연 후보 보존 시간, 실행시간·최대 메모리·오류. 기존 앱의 4.271초 미출력은 정적 참고. **기존 YOLO와 같은 프레임의 pose 정확도 A/B, 영상 전체 정확도, P5 메인 정확도, 전환 지연·얼굴 신원 점수는 내지 않는다.** |
| 실행 장치·한도 | macOS 27.0 Mac mini M4/24GB, CPU, `analyze_skip=4`, 새 MoveNet **3회**, 회당 **600초**, 총 **1800초**, worker RSS **12,288MiB**, metadata 총 **250MiB**. 사용자 승인 범위에서 세 회 모두 완료했다. |
| 출력 | 격리 worktree `/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-v1/`. 기존 앱 결과를 덮어쓰지 않았다. |

**결과 요약:** 3회 모두 exit 0, 회당 56.75~60.90초, 최대 RSS 937.42MiB였다. 세 metadata JSON의 SHA-256이 동일했다. 표본 사람 검출은 33/45명, 명확한 메인 위치 표본은 1/4프레임이 맞았다. 원본 공연 시간 106.5초 중 분석 단계의 main/group 후보 없는 시간은 약 0.267초다. **이 수치로 현행 YOLO보다 정확한지, 최종 clip 누락이 개선되는지 판단할 수 없다.** [해석과 한계](01-w13-movenet-first-real-metadata-evaluation.md)를 먼저 본다. [런타임·signature 기록](01-w13-movenet-runtime-signature-lock.md)은 실행 전 준비 근거다.
