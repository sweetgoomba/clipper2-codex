# W14 — 새 두 영상의 얼굴 정답 확인 준비

2026-10-14 KST. 기존 입력 대조의 다음 단계. 제품 품질 개선 결과가 아니라 새 촬영 영상의 평가 입력 준비다.

## 결정과 실행 범위

- 사용자 제공 Super Shy `J9DlrnNlgfE` / OMG `6bVUjsUi9sw`의 기존 확보 1080p 원본을 사용했다. 각 고정 창의 중간인 요청 45/95/140/180초, 총 8프레임을 기존 actual-PTS manifest에서 선택했다.
- 기존 YuNet 2023mar만 원본 BGR 1920×1080에 실행했다. 검출 전 축소 없음. score 0.6 / NMS 0.3 / topK 5000 / CPU 1스레드. SFace/AuraFace/Intel 인식, pose, 모델 다운로드, 의존성 설치는 0이다.
- 모든 유효 검출 22개를 보존했다. 각 프레임에서 얼굴 폭의 최소/중간/최대 위치를 중복 제거하여 첫 사용자 확인 15개를 선정했다. 나머지 7개도 산출물에 남는다. 인식 예측이나 정답으로 고르지 않았다.
- 사용자 입력은 얼굴의 멤버/등록 외/판단 어려움/얼굴 아님과 얼굴 사진 자체의 식별 가능 여부다. 메인 댄서 및 구간 전체 정답 입력을 요구하지 않는다.

## 정확한 입력과 산출물

공통 산출물 루트: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-review-v1`.

- `manifest.json` SHA256: `5c6624684d718300154b7c006f35703af1473a02580eda332006607100c97ffd`. 원본 2개, 고정 PTS 목록, YuNet, 실행/선정 코드와 계획 총 8개 파일의 hash를 고정했다.
- Super Shy source SHA256: `fa434d6d1d62c19fd75f606b70fd158a943fcbdfd1fe91778ef784e4ca149cc0`.
- OMG source SHA256: `0e778c49ecb3325e1fe507d7179f5e5b638686896fbd5c3bc07fd03027f63f63`.
- YuNet SHA256: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`.
- `result.json`, `supervisor.json`, `worker.log`: 실행 원문. `review-data.json`: 전체 선정 입력. `verification.json`: 독립 검산 요약. `review-screen.png`: 최종 사용자 화면.
- 실행 상한 8검출/120초/2GiB/80MB. 실제 8검출, worker 1.195초, supervisor 1.803초, 프로세스 peak RSS 587,939,840bytes. 정상 종료, 상한 중단 없음.

## 실제 확인과 한계

- 입력 hash 8개, 모든 source frame index/PTS/time base, 22검출 및 15선정의 고유성/크기순 규칙/원본 crop 존재를 검산했다.
- 관련 pytest 28개, Node 응답 상태/완료 판정/정규 provenance 내보내기 검증, JS 구문 검증 통과. 독립 리뷰에서 전달을 막는 문제 없음.
- 별도 QA URL에서 얼굴 아님→판단 어려움 변경, 식별 여부 초기화, 새로고침 응답 복원, 실제 JSON 다운로드와 정규 ID/PTS/bbox 보존을 확인했다. QA export는 `annotation_origin=ui_qa_not_ground_truth`이며 **사용자 정답으로 수입하지 않는다**. QA 파일은 `qa-export.json`, SHA256 `f0d732ec53b5a763b4f9bceb98a7fa5b19a38fe2104410dc44ecb83561486670`.
- 사용자 페이지는 별도 pathname 저장소로 분리했고 실제 0/15 상태, 이미지/최종 상단 이전·다음·내보내기 배치를 확인했다. 사용자 정답을 대신 작성하지 않았다. 기존 후보 페이지 및 사용자 135기록은 보존했다.
- OMG 약140초는 측면 얼굴이 보이지만 검출 0으로 기록된다. Super Shy 약180초의 한 검출은 손/가슴 영역에 해당하는 것으로 시각 확인했다. 전자는 미검출, 후자는 검출 오탐이며 인식 실패로 합치지 않는다. 사용자 GT로 자동 확정하지 않았다.
- 비무작위 소수 표본이므로 전체 영상 정확도/낮은 FAR/최종 안무 구간 품질의 증거가 아니다. 새 영상 인식 추론 0, 사용자 GT 0이다. 새 영상 결과를 보고 threshold를 튜닝하면 그 영상은 독립 최종 평가 자료로 유지할 수 없다.

## 사용자 다음 행동과 후속

[새 영상 얼굴 15개 확인](http://127.0.0.1:58261/holdout-review-v1/index.html): 인물 선택 → 사진 자체의 식별 가능 여부 → 다음 얼굴 → 확인 내용 내보내기. 모르겠으면 판단 어려움, 다섯 멤버가 아니면 등록 외 인물, 손/옷이면 얼굴 아님을 사용한다.

수신 후 user_review origin 및 manifest/ID/source hash/PTS/bbox를 검증하고, 실제 얼굴과 검출 오탐을 구분하여 기존 SFace/AuraFace/0095를 같은 입력·모델별 정상 전처리로 비교한다. 기존 참조/개발자료에서 정한 규칙을 고정하고, 새 표본의 결과를 미리 보고 기준을 조정하지 않는다. 15개로 최종 후보를 확정하거나 제품에 적용하지 않는다.

## 소유권·호환·미검증

W14 기존 격리 worktree의 `evaluation/candidate_comparison/holdout_*`, 테스트와 평가 화면만 변경했다. 공통 `clipper_face_core`, 제품 SDK/플러그인, W13 main/track/구간/crop, 기존 pyproject/uv.lock/venv는 이번 변경 대상이 아니다. Git commit/push/merge, 새 세션/다른 세션 메시지 없음.

W14 공개 API/고정 fixture → 최신 W13 source/main/동일인 scope/실패 상태 compatibility → W13 소비 adapter/가상환경 검증 순서를 유지한다. 최신 W13 메인 출력과 결합한 실제 안무 평가 및 Windows 패키징/깨끗한 사용자 환경 검증은 남아 있다. 얼굴 표본의 정답을 track/메인 구간 정답으로 전파하지 않는다.
