# W13 — RTMPose 추가 비교와 RTMO 검출 기준 실험

확인일: 2026-10-14 KST

## 이번에 한 일과 결론

사용자 진행 지시에 따라 **RTMPose-m을 새 자세 모델로 실제 실행**했다. 기존 RTMO의 사람 검출 기준값도 저장 자료로 비교했다. 같은 원본 전체, 같은 사용자 정답표, 같은 메인·군무 판정 규칙을 유지했다. 얼굴 매칭은 포함하지 않았다.

결론은 **새 모델을 추가했지만, 제품에 적용할 만큼 나은 설정은 아직 얻지 못했다**는 것이다.

1. **RTMO 검출 기준을 0.7에서 0.3으로 낮추기:** 앞서 놓친 한 사람을 다시 검출하고, 보조 표본의 메인 위치 선택도 일부 회복했다. 하지만 메인 장면을 군무로 잘못 분류하는 문제는 그대로였다.
2. **사람 상자는 그대로 두고 관절 추정만 RTMPose로 바꾸기:** RTMO와 전체 결과가 거의 같았다. 이번 관절 모델 교체만으로 핵심 문제가 해결되지 않았다.
3. **사람 검출기도 RTMDet으로 바꾸고 RTMPose와 결합하기:** 메인 장면의 군무 오판은 줄었지만, 실제 군무를 잘 찾지 못하고 짧게 끊기는 구간이 크게 늘었다. 전체 개선으로 인정할 수 없어 미채택했다.

이 결과는 RTMPose 계열 전체가 나쁘다는 결론이 아니다. 한 모델 크기·입력 해상도·검출 기준과 고정 후처리를 한 영상에서 비교한 결과다. 15번 결과를 비교 기준으로 유지하며, 15번 자체도 제품 채택 기준을 충족하지 못한 상태다.

## 어디서 확인하는가

[22번 노트북 — RTMPose와 RTMO 기준 비교](http://127.0.0.1:8899/lab/workspaces/auto-pose22/tree/notebooks/w13_dance_iteration_lab_22_rtmpose_and_rtmo_cutoff.ipynb)

`2. 전체 영상 나란히 보기`에서 재생한다. 기본은 왼쪽 MoveNet 512, 오른쪽 RTMDet + RTMPose다. 메뉴로 YOLO26s, RTMO 기준 0.7/0.3, RTMO 상자 + RTMPose를 선택할 수 있다.

- 초록색 영상 테두리: 해당 방법이 군무로 판정. 메인 상자는 없음.
- 빨간 상자: 단독 메인. 주황 상자: 공동 메인. 흰 상자: 검출한 사람.
- `관절 표시`: 모델이 추정한 관절을 겹쳐 표시.
- 아래 이름과 구간: 사용자 정답표이며 새 얼굴 인식 결과가 아님.

새 노트북을 처음 열기 전에 생성하고, 이후 Jupyter 화면에서 실행·저장했다. 기존 열린 노트북을 디스크에서 다시 쓰지 않았다. 사용자 정답표도 그대로 보존했다.

## 비교 조건

원본 `yFTAYXDTjqI` 전체 0–133.654059초의 동일한 2,002개 관측을 사용했다. 메인 점수, 역할 분류, 시간 안정화, 몸 위치 선택은 15번 설정으로 고정했다. 관절 신뢰도 문턱은 0.3이며, 모델 사이 신뢰도 숫자가 같은 확률로 보정되어 있다는 가정은 하지 않는다.

| 조건 | 바꾼 부분 | 새 추론 |
|---|---|---|
| RTMO 0.7 / 0.5 / 0.3 | 사람 검출 문턱만 변경, NMS 0.45 유지 | 없음, 저장 원시 출력 재사용 |
| RTMO의 기존 사람 상자 + RTMPose | 상자·검출 점수 유지, 관절만 변경 | RTMPose 실행 |
| RTMDet-nano + RTMPose | 새 검출기 점수 >0.3, 새 관절 모델 | 두 모델 실행 |
| MoveNet 512 / YOLO26s | 앞선 21번 비교와 동일 | 없음, 저장 결과 사용 |

RTMO 0.7 재생은 이전 사람 배열과 지표를 정확히 재현했다. RTMPose의 두 조건은 원본을 한 번 읽는 동안 함께 수집했다. 같은 2,002개 시각이지만 두 조건의 관절 추론을 수행했으므로 단일 모델 1회 속도와 직접 비교하지 않는다.

정답표는 예측 입력으로 쓰지 않고 채점에만 사용했다. 메인만 표시한 642관측, 군무만 표시한 407관측, 둘이 중첩된 556관측, 명시적 제외 388관측을 구분했다. 미표시 9관측은 건너뛰었다. 보조 몸 위치 정답 66장은 조사자가 작성한 제한된 표본으로, 사용자의 전체 영상 인물 평가나 얼굴 정확도를 대신하지 않는다.

## 결과

| 조건 | 메인을 군무로 오판 ↓ | 실제 군무를 찾음 ↑ | 보조 66장 메인 위치 ↑ | 보조 정답 사람 검출 ↑ | 1초 미만 구간 | 경계 F1 ±0.5초 ↑ |
|---|---:|---:|---:|---:|---:|---:|
| MoveNet 512 | 178/642, 27.7% | 384/407, 94.3% | 63/66 | 66/66 | 1 | 0.296 |
| YOLO26s | 170/642, 26.5% | 364/407, 89.4% | 61/66 | 66/66 | 8 | 0.200 |
| RTMO >0.7 | 188/642, 29.3% | 383/407, 94.1% | 61/66 | 65/66 | 1 | 0.148 |
| RTMO >0.5 | 200/642, 31.2% | 384/407, 94.3% | 61/66 | 65/66 | 3 | 0.154 |
| RTMO >0.3 | 188/642, 29.3% | 385/407, 94.6% | 63/66 | 66/66 | 1 | 0.250 |
| RTMO 상자 + RTMPose | 189/642, 29.4% | 383/407, 94.1% | 60/66 | 65/66 | 1 | 0.148 |
| RTMDet + RTMPose | 99/642, 15.4% | 254/407, 62.4% | 44/66 | 65/66 | 96 | 0.115 |

YOLO는 관절 신뢰도가 있는 20번 자료를 사용했다. 신뢰도가 빠졌던 옛 15번 YOLO의 군무 회수율 94.1%·짧은 구간 14개와 구분한다.

메인→군무 오판 12% 이하 목표는 전부 미달이다. RTMDet 결합은 군무 회수 85% 이상 목표도 미달이며, 메인/군무 각 54관측을 역할 미정으로 남겼다. 오판 하나만 줄었다고 전체 품질 향상으로 계산하지 않는다.

78.8–85.4초의 메인 구간은 RTMO의 세 문턱과 RTMO 상자 + RTMPose 모두 99/99관측 군무로 남았다. RTMDet 결합에서는 군무 55·단독 37·미정 7로 바뀌었으나, 단독 37개에서 올바른 사람을 골랐다는 뜻은 아니다. 실제 군무인 40–48초는 RTMO/고정 상자 조건 120/120군무에서 RTMDet 결합 91군무·26단독·3미정으로 악화했다.

## 얻은 근거와 아직 모르는 것

**확인한 사실:** 관절 모델 영향과 사람 검출기 영향을 분리했다. 같은 사람 상자에서 관절만 바꾸면 주요 오판이 유지된다. 검출기까지 바꾸면 사람 수와 이후 구간 판정이 크게 변한다.

안무 구간의 사람 관측 수는 RTMO/고정 상자 7,427개에서 RTMDet 결합 11,032개로, 익명 추적 번호 수는 37/38개에서 517개로 늘었다. 이것은 저장 출력의 변화이며 실제 검출 재현율이나 정답 ID 전환 횟수가 아니다. 추가 상자가 모두 오검출이라고 확정할 수도 없다. **불안정한 상자와 추적 연결이 구간 쪼개짐을 키웠는지**는 다음 원시 출력 감사에서 확인할 가설이다.

이번 영상에서 반복 시험했으므로 새 영상의 일반화 성능, 밀집된 관절/몸 추적 정답, 사람 교체 정확도, 얼굴 매칭, 최종 클립 품질은 인증하지 않았다.

## 실행·모델 출처

작업 공간: `/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python`

- 브랜치 `feature/w13-dance-metadata-eval-20261001`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e`. 평가 코드 미커밋, 실제 파일 해시는 실행 manifest와 code-snapshot에 보존.
- 원본 `/Users/jina/Library/Application Support/Clipper Studio Dev/sources/youtube/yFTAYXDTjqI/source.mp4`, SHA256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`.
- 사용자 정답표 SHA256 `d451572c00142fc8b110678da974665b26d9d058938c5be2e7115e6080e00ab0`.
- RTMPose-m Body7 COCO17 256×192: [공식 archive](https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip). ONNX SHA256 `5c0a4bf67953e6d2ac43ce15e77dc9d5d354ae18430a47d2c5963a7bc5683e3c`.
- RTMDet-nano person 320×320: [공식 CPU bundle](https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmpose-cpu.zip)의 `rtmdet-nano/end2end.onnx`. SHA256 `b8585adb6d1352796f6e86337e09c3459b830645a7e7192d9381670bea2facbd`. 실제 계보는 `coco-person_in1kpretrain-96154d0b`, 현재 문서의 다른 Obj365 모델이나 비슷한 이름의 손 검출 모델이 아님.
- Mac mini M4 / macOS 27 arm64 / Python 3.11.12 / ONNX Runtime 1.24.4 CPU, intra 4 / inter 1. 패키지 설치 없음.
- 공식 모델·자료 다운로드 105,406,510바이트, 약 5.00초. 승인 한도 200MiB/180초 이내.
- 실제 영상 실행 **345.996초, 최대 RSS 4,624,744,448바이트, 산출물 57,363,478바이트**. 상한 600초/12GiB/250MiB 이내. 원본 1pass·관절 조건 2개, 추가 ML 재시도 없음.
- RTMO 문턱 비교는 저장 원시 자료만 사용, 5.184초/최대 RSS 약 399MB.

RTMPose 전처리는 [MMPose v1.1 affine](https://github.com/open-mmlab/mmpose/blob/v1.1.0/mmpose/datasets/transforms/topdown_transforms.py)와 archive pipeline에 맞춰 padding 1.25, BGR→RGB, mean/std를 적용했다. SimCC는 [공식 decoder](https://github.com/open-mmlab/mmdeploy/blob/v1.2.0/csrc/mmdeploy/codebase/mmpose/simcc_label.cpp)의 축별 최대값 중 작은 값을 관절 신뢰도로 사용했다. rtmlib helper의 RGB 생략·평균 신뢰도와 차이를 명시했다. Python affine과 SDK 정수 crop의 비트 단위 일치를 주장하지 않는다.

검출기는 archive와 [공식 resize](https://github.com/open-mmlab/mmdeploy/blob/v1.0.0rc1/csrc/mmdeploy/preprocess/transform/resize.cpp)·[decoder](https://github.com/open-mmlab/mmdeploy/blob/v1.0.0rc1/csrc/mmdeploy/codebase/mmdet/object_detection.cpp)를 대조했다. 실제 반올림된 크기의 x/y 배율, BGR 정규화, 우측·하단 padding 114, 모델 내장 NMS 0.6을 사용했다. 추가 NMS와 빈 검출을 전 화면 사람으로 대체하는 처리는 없음.

범위/다운로드/실행/비교 manifest와 로그: `.superpowers/sdd/22-w13-pose-extensions/`. 원시 자세 자료: `output/evaluation/yFTAYXDTjqI/rtmpose-m-v1/`. 비교 결과·화면·검증: `output/evaluation/yFTAYXDTjqI/human-truth-iteration/pose-extensions-22/`.

실행 manifest SHA256 `77bf36b5b0b46a6bdca0f01644216f820a3431a2720f50d8d060aa0501b55b4c`. 템플릿에서 이어진 `created_utc`는 이전 21번 생성시각을 남겼다. 동결 파일을 사후 수정하지 않고, 실제 22번 동결시각 `2026-10-13T16:33:43.524769+00:00`과 이 차이를 `freeze-time-provenance.json`에 별도 기록했다. 출력의 시각은 frame index/fps 기준이며 원본 개별 PTS를 별도 인증한 것은 아니다.

## 검증·보존

- 신규 테스트 19개 RED→GREEN. 전체 **775 passed, 5 skipped, 17 warnings**, 52.19초. 최초 sandbox 실행은 localhost bind 제한으로 실패해 같은 테스트를 로컬 포트 허용 상태에서 재실행했다. 실제 영상 E2E 2건은 입력 환경변수 미설정으로 skip이며, 이 테스트 숫자가 영상 정확도 개선을 뜻하지 않는다.
- 독립 검토에서 RTMO 원시 출력 재현, 고정 상자 7,453개, 새 검출 상자 11,135개, 두 조건 전체 관절/신뢰도, 2,002개 시각, 후처리 지표와 파일 해시를 재검산했다. 해결되지 않은 P0–P2 지적 없음.
- 새 노트북 코드 셀 2개 실행·오류 없음. 여섯 조건 선택, 관절 표시, 영상 재생/정지, 42초 군무 테두리, UI 저장 확인. 초기 notebook kernel bind 실패 후 같은 표시 전용 생성기를 재실행한 것으로 모델 재평가가 아님.
- 기존 노트북 22개·사용자 정답표·기존 미커밋 파일 3개를 해시로 대조해 보존 확인.
- 제품/얼굴/W14 공통 파일 변경, clip export, Build5, commit/push/merge/deploy 없음.

## 다음 범위와 남은 결정

다음은 **저장된 RTMDet 원시 출력에서 추가 상자·누락·추적 끊김을 분리하고, 검출 문턱만 바꾼 비교가 가능한지 확인**하는 것이다. 새 모델이나 메인 규칙을 동시에 바꾸지 않는다. 해당 감사는 아직 미실행이다. 사용자 정답표 재작성이나 추가 준비는 필요 없다.

MMPose/관련 구현의 Apache 2.0 근거와 특정 가중치의 재배포 적합성은 구분한다. 이번 사용자 승인 로컬 시험을 완료했으며, 학습 데이터 계보를 포함한 정확한 weight 재배포 조건, Windows 실행, 설치형 패키징은 여전히 확인 필요다. 제품 채택과 배포를 완료했다고 표현하지 않는다.
