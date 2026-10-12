# W13 첫 비교 실행안 — 승인 전 한 장 요약

**지금 상태: 정적 비교와 첫 지표용 라벨 준비 완료. 새 모델 실행은 아직 하지 않았고 승인도 받지 않았다.**

## 무엇을 비교하나

이미 앱이 만든 안무 결과에서, 사람별 메인 clip이 없는 **20.487~34.835초**를 우선 확인한다. 이 사이에는 그룹 clip이 **23.357~33.433초**에만 있고, 양옆 **합계 4.271초는 어떤 clip에도 없다.** 원본 정지 장면에는 이 시간 내내 출연자가 보인다. 기존 로그상 메인 후보 두 개가 그룹과 겹쳐 얼굴 분석 전에 제외됐다. 비교할 변화는 **이렇게 탈락한 원본 구간과 이유를 `확인 필요` 목록에 남기는 정책 하나**다. 같은 장면의 그룹 clip과 검토 후보가 함께 있어도 된다. 검토 후보를 특정 멤버에게 자동 배정하거나 새 MP4로 만드는 실험은 아니다.

첫 점수는 [보수적으로 고정한 공연 장면 라벨](01-w13-retention-visibility-label-v1.json)의 **6.0~112.5초**에서 `메인 clip / 그룹 clip / 확인 필요 / 어디에도 없음`으로 원본 시간을 나누어 센다. 입장과 종료 화면의 불확실한 양쪽 1초는 점수에서 뺀다. 이는 **공연 장면 보존 지표**이며, 춤의 정확한 시작·끝이나 메인 인물 정확도는 아니다. 현재 앱 결과의 이 구간 미출력 시간은 **4.271초**다. 비교 정책을 적용해 이 시간이 확인 목록에 나타나는지는 향후 metadata 실행에서 확인한다. 기존 자료로 계산한 예상값을 실제 개선 결과라고 부르지 않는다.

## 입력과 실행 상한 제안

| 항목 | 고정값 또는 제안값 |
|---|---|
| 원본 | 이미 저장된 `/Users/jina/Library/Application Support/Clipper Studio Dev/sources/youtube/yFTAYXDTjqI/source.mp4`; SHA-256 `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4`; **0~133.654059초 전체** |
| 참조 이미지 | 이번 보존 비교에는 **없음**. 이름·얼굴 정확도는 측정하지 않음 |
| 모델 | 기존 로컬 YOLOv8s Pose `234314cd…b186cfb3`, YuNet `8f2383e4…ed2552fa4`, SFace `0ba9fbfa…9e83484087c34e79`의 [전체 hash 목록](01-w13-existing-app-input-inventory.json). 새 모델 다운로드 0 |
| 분석 코드 | Python `47782953228861f4bdbdc135265d067c2a826b0e` 기반 W13 격리 worktree의 export 없는 adapter. **실행 코드 fingerprint는 아직 미고정** |
| 장치·횟수 | 현재 Mac mini M4/macOS 27.0에서 CPU 명시 제안. 같은 현행 분석 최대 3회; 비교 정책은 기록된 metadata에 적용해 별도 모델 실행 0회 |
| 중단 상한 | 제안: 1회 10분, 전체 30분, 전체 프로세스 최대 RSS 12GB, metadata 합계 250MB. 강제·측정 runner는 실행 전 준비·검증 필요 |
| 출력 | 제안: `/Users/jina/project/adlight/.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python/output/evaluation/yFTAYXDTjqI/retention-v1`; 기존 앱 결과 폴더는 읽기만 함 |

## 실행 전 남은 결정

1. **모델 이용 조건 대조:** 사용자는 YOLO 첫 도입 때 사용 가능 여부를 확인했던 기억이 있다. [도입 Git 이력과 현재 공식 조건](01-w13-yolo-license-provenance.md)을 조사했지만, 당시 검토의 링크·메모·계약 범위는 저장소에서 찾지 못했다. 이는 사용권이 없다는 뜻이 아니다. AGPL은 영리 사용 자체를 금지하지 않지만, 공급사는 AGPL 공개 의무를 충족하는 경우와 비공개 SaaS의 상업 라이선스를 구분한다. 기존 검토 근거나 실제 계약을 확인해 이 제품 범위에 적용되는지 대조한다. 부적합으로 확인되면 **기존 artifact·로그 정적 비교까지만** 한다. YuNet/SFace의 해당 OpenCV Zoo 디렉터리는 각각 [MIT](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/README.md), [Apache-2.0](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md)이라고 명시한다.
2. **재현 가능 실행 정보 고정:** adapter의 코드 fingerprint·정확한 Python 환경/설정·실제 장치, 모델 파일 hash 재검증, 상한을 강제하는 runner와 출력 경로를 [manifest](../09/30-w13-experiment-manifest.yaml)에 확정한다. 그 뒤 사용자가 **이 범위의 새 추론 실행**을 선택해야 한다.
3. **메인/신원 평가는 별도:** 사람별 정답은 [19구간 검토 초안](01-w13-full-source-label-draft.json)에 아직 없다. 원본 연속 관찰과 익명 사람별 위치·교체·공동 메인 확인 후 메인 정확도/전환 지연을 계산한다. 멤버 이름은 신원 평가가 필요할 때 독립 확인한다. 의상 색 대응이나 이름표 작성을 사용자에게 요구하지 않는다.

이 단계에서 제품 코드·기존 영상/clip·공통 얼굴 모듈을 바꾸지 않았고, 새 ML 추론·다운로드·유료 호출·Build5·commit/push/merge/deploy는 0회다.
