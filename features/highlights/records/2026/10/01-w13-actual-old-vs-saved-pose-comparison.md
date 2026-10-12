# W13 같은 영상: 수정 전 완성 결과와 새 자세 실험을 실제로 대조

2026-10-01 KST. 사용자 지정 영상 `yFTAYXDTjqI` **전체 0~133.654초**를 입력과 기본 시간 분모로 사용했다. 공연을 눈으로 확인할 수 있는 6.0~112.5초(106.5초)도 따로 계산했다. 왼쪽은 9/29 Dev 앱이 이미 만든 **실제 MP4 20개**와 그 `dance_meta.json`; 오른쪽은 승인된 MoveNet 3회 중 동일한 `run-01`의 **저장 자세 관측**을 현행 구간 정리·그룹 필터에 재생한 값이다. 새 모델 실행, 얼굴 인식, 새 앱 프로젝트·최종 클립 생성은 없다. 세 승인 pass의 pose JSON hash는 같으므로 첫 pass를 대표로 썼다.

## 한눈에 보는 결과

| 같은 영상 전체 133.654초에서 | 수정 전 앱의 완성 MP4 | 저장 MoveNet 자세를 같은 구간 규칙에 넣은 결과* |
|---|---:|---:|
| 개별 메인 구간 | **93.16초** / 완성 클립 19개 | **24.62초** / 얼굴·export 전 후보 5개 |
| 그룹 구간 | **10.08초** / 완성 클립 1개 | **84.15초** / 얼굴·export 전 후보 2개 |
| 원본에서 먼저 고정한 단독 메인 18프레임 중 개별 메인으로 남은 장면 | **9장** | **3장** |

\* 오른쪽은 **예상 앱 완성 결과가 아니다.** 얼굴 검출/멤버 매핑/clip export 전에 멈춘 판정이다. 그 이후에도 구간이 사라질 수 있지만, 새 개별 클립이 더 생겼다는 주장은 할 수 없다. 수정 전의 9장도 클립이 있다는 뜻이지 그 멤버 이름이나 화면의 메인 인물이 맞았다는 점수는 아니다. 두 쪽의 구간 길이는 단계가 달라 최종 clip 성능 수치로 직접 비교하지 않는다. 그럼에도 **현재 MoveNet을 그대로 제품에 교체하면 메인 구간이 줄어드는 명백한 사전 차단 근거**다.

공연 구간 **6.0~112.5초만** 보면 개별 메인은 기존 완성 MP4 **92.15초**, 저장 자세의 얼굴 전 후보 **22.83초**다. 그룹은 각각 **10.08초**, **83.60초**다. 영상 전체 수치에는 앞뒤 도입·마무리도 포함되며, 저장 자세에는 120.05~121.59초의 별도 메인 후보가 있다. 이 후보를 좋은 하이라이트로 평가한 것은 아니다.

![수정 전 완성 결과와 저장 자세 판정의 전체 공연 시간표](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-v1/old-vs-saved-pose-timeline.png)

**직접 보는 영상:** [수정 전 실제 MP4와 저장 자세 판정의 18초 비교](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-v1/actual-old-vs-pose-preview-five-solo-windows.mp4). 같은 원본의 단독 리드 다섯 창(P1 초록 16.5~20.0, P2 노랑 22.0~27.0, P3 빨강 29.0~33.0, P4 파랑 54.0~57.0, P5 연보라 59.0~61.5초)을 이어 붙였다. **왼쪽은 기존 프로젝트의 실제 export MP4 프레임**, 오른쪽은 원본 위에 저장 MoveNet 선택 상자를 그린 진단 화면이다. 오른쪽은 새 완료 clip이 아니다. 왼쪽에 clip이 없는 시각은 검은 화면으로 표시한다. 음성은 넣지 않았고 원본 시각을 두 쪽에 맞췄다.

## 왜 줄었나

MoveNet 저장 관측에서 그룹 구간이 **19.686~99.566초**로 길게 이어졌다. 현행 `_filter_group_like_main_segments()`는 겹침 비율 0.6 이상인 메인 구간을 버린다. 새 관측을 같은 smoothing/group 규칙에 넣으면 정리된 메인 후보 17개 중 **12개가 그룹 중첩으로 제외**된다. 그러므로 P2·P3·P4·P5의 명확한 단독 리드 표본 15장 모두 새 개별 메인 후보가 없고, P1 첫 3장만 후보에 남는다. 이후 얼굴 판정은 수행하지 않았다. 이는 모델 검출·선택 오류와 그룹 판정 오류를 구분해 고쳐야 한다는 근거다. 이미 확인한 저장 자세 자체의 18장 메인 bbox 일치는 6/18이며, 그룹 필터만 끄거나 움직임 점수만 바꿔도 전체 정확도가 좋아진다고 볼 수 없다.

기존 완성 결과의 main+group MP4 합집합은 공연 102.229초, 빈 시간은 4.271초다. 새 관측의 **얼굴 전** main+group 후보 합집합은 104.832초이지만 이 대부분이 그룹이고, 새 MP4 coverage로 세지 않는다. 새 결과의 main/group 후보는 1.601초가 겹쳐 각 길이를 단순 합산하지 않는다. 기존 탈락 후보 표시 UI가 보존하는 4.271초 역시 새 완성 MP4나 정확도 향상이 아니다.

## 근거와 재현

- 원본: `/Users/jina/Library/Application Support/Clipper Studio Dev/sources/youtube/yFTAYXDTjqI/source.mp4`, SHA-256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`.
- 기존 완료 meta: `/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/78ba4bfb-ec22-4a1b-a0e8-0201ee9f789a/1790659628130/json/dance_meta.json`, SHA-256 `274eddd3f4a7777987d29a34517abf39c4af344c65155efc6209e5ea03110450`. 19개 main MP4와 1개 group MP4 파일이 모두 존재함을 재확인했다.
- 기존 MP4 20개를 `ffprobe`로 모두 열어 재생 길이를 확인했다. 저장 meta 경계와 인코딩된 파일 길이의 최대 차이는 0.0504초다. 위 coverage는 실제 디코딩 프레임별 합이 아닌 **저장 meta의 원본 구간 경계** 기준이다.
- [프레임·구간별 JSON](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-v1/old-app-vs-pose-pre-face-v1.json), SHA-256 `4724b53ea528ae5d6ebbd6f30cfbcec4c65c11443568526abf557bc85896b407`. JSON에 pose·기존 meta·라벨·평가 코드 hash와 **전체 원본/공연 구간 양쪽 집계**가 들어 있다. [구간 재생 스크립트](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/tools/w13_compare_old_app_to_saved_pose.py)를 `PYTHONPATH=.`와 `--whole-end-sec 133.654059`로 실행한다.
- [전체 시간표 PNG](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-v1/old-vs-saved-pose-timeline.png), SHA-256 `7386908fddfcf770c99c8ddc71fc6163ea7228d1cb482d356c0c8858eec848ae`. [실제 기존 MP4 대조 영상](/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/movenet-v1/actual-old-vs-pose-preview-five-solo-windows.mp4), SHA-256 `2fbc2b5dd9ed0ddee6751ab35bffba1d0161b04ecb5bbb66ecf8d69bdbe3ae77`, 1920×506, 15fps, 18.067초. ffmpeg 전체 decode와 26.48초·55.00초 시각의 양쪽 프레임을 확인했다.

**판단:** 현재 저장 MoveNet 관측+현행 메인/그룹 규칙을 제품에 그대로 넣는 것은 추천하지 않는다. 사용자가 원하는 “예전보다 나아진 완성 클립” 수치는 **아직 존재하지 않는다.** 지금 정직하게 확인되는 차이는 개별 메인 후보가 크게 줄고 그룹 후보가 늘었다는 점이다. 다음 개선은 그룹 판정의 솔로 오검출과 자세의 사람 누락·오선택을 각각 해결한 후, 새 완료 clip을 실제 생성하고 동일 원본 라벨로 얼굴 identity·clip coverage·전환·품질을 분리 평가해야 한다. W14 공통 얼굴 경로, 기존 프로젝트, 제품 기본 모델은 변경하지 않았다. Commit/push/merge/deploy 없음.
