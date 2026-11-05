# 하이라이트 실제 분석 연결과 YOLO ONNX 시험

2026년 11월 3일. 기존 작업은 공통 계약·선택 규칙·worker·품질 도구와 대사 CPU 재분석까지였고, 세 플러그인의 자동 최적 실행이 완성된 상태가 아니었다. 이번에는 **안무·인물의 공개 작업 진입점에 실제 분석 단위 CPU 재분석을 연결하고, YOLO ONNX 추론을 두 플러그인의 원래 분석 코드에 연결했다.**

모든 모델의 실측 기반 자동 최적 실행기 선택, 런타임 설치·자원 조정·설정 UI 전체는 여전히 미완성이다. 아래 시험 도구는 실제 후보 실행을 확인하기 위한 개발용이며, 품질 인증서를 만들거나 일반 자동 선택을 켜지 않는다.

## 지금 실행되는 것

| 대상 | 이번에 연결한 동작 |
|---|---|
| 안무 | 새 소유 프로세스에서 전체 분석. GPU backend 오류면 새 CPU 프로세스로 처음부터 1회 재분석. CPU에서는 YOLO·YuNet·AuraFace·보조 SFace 모두 CPU. 기존 추적·인물 판정 로직 유지 |
| 인물 | 같은 분석 단위 복구와 generation 공개. 원래 YOLO/OpenCV/ORT 모델 구현 사용. 새 시도마다 tracker/gallery/model 상태 새로 생성 |
| 인물 음성 | CUDA 실행 오류·OOM·충돌·3600초 timeout 시 음성만 새 CPU 프로세스로 1회 재분석. CPU도 실패하면 결과 공개 중단. 처음부터 CPU/MPS인 Whisper backend 실패도 정상 완료로 숨기지 않음 |
| 대사 | 앞서 연결한 분석·STT CPU 재분석 유지 |
| YOLO ONNX | 안무·인물 실제 모델 factory에서 실행 가능. 원래 Ultralytics 전처리·rectangular letterbox·NMS·관절 처리를 사용하고 추론만 ORT worker로 교체 |
| GPU 시험 준비 | 원래 PT에서 dynamic FP32 ONNX 생성. CoreML/CUDA의 지정된 런타임 또는 별도 DirectML 1.24.4 시험 환경 준비. worker 모듈과 코드 해시도 사전 검사 |
| 실행 증거 | ORT 실제 provider별 실행 노드, IPC 포함 추론 시간 기록. GPU 시험 명령은 해당 작업의 요청 GPU 노드가 있어야 통과 |

CPU 강제 실행은 `acceleration_mode=cpu`로 요청하며 개발 시험 CLI에서는 `--cpu`다. 현재 GUI에 새 설정 화면을 추가한 것은 아니다. 평소의 원래 MPS/CUDA 실행 정책과, 명시적으로 선택하는 새 ONNX 시험 후보를 구분한다.

## 품질과 결과 보존

- 모든 시도는 비공개 generation에서 실행한다. 프로세스 종료 확인 후 성공 revision 하나만 공개하며 실패 파일은 공개하지 않는다.
- 재분석 전·공개 전 원본 영상의 파일 identity와 SHA를 검사한다. 중간에 영상이 바뀌면 입력 오류로 중단한다.
- 안무 참조 사진은 별도 소유 프로세스에서 한 번 준비하고 두 시도에 같은 바이트를 공급한다. 최종 metadata에 임시 입력 경로를 남기지 않는다.
- 안무의 새 소유 분석에서는 원본 영상을 hardlink로 저장하지 않고 복사한다. 이후 사용자 원본 수정이 이미 공개한 결과를 바꾸지 않게 한다. 원래 직접 pipeline 경로의 최적화는 유지했다.
- 안무 얼굴 가속기가 분석 중 실패하면 그 모델만 CPU로 바꿔 gallery를 섞지 않고 전체 CPU 재분석으로 전달한다. 소유 분석 밖의 기존 reference 동작은 유지했다.
- ONNX worker도 분석 소유 process group에 들어간다. 취소·충돌 시 분리된 model worker가 남아 GPU를 점유하지 않도록 했다. Windows는 기존 Job Object를 사용하며 native Windows 검증은 남아 있다.

## 실제 실행 증거

[증거 폴더](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration).

1. **실제 YOLO 출력:** 배포된 Ultralytics 인물 사진을 두 해상도로 실행. 안무·인물 모두 원래 Torch와 ONNX worker의 검출 인원이 4명으로 같았다. 안무 박스 최대 차이 약 0.000305픽셀, 인물의 정수 박스는 같았다. 관절도 비교했다. [출력 비교](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/real-pose-parity.json).
2. **전체 플러그인:** 같은 사진으로 만든 6초 영상에서 실제 YOLO·YuNet·AuraFace, 분석·미리보기·저장·공개까지 실행. Torch CPU와 ONNX CPU의 안무 `lists/persons`, 인물 `groups/clips`가 각각 같았다. 각 플러그인이 1개 인물·1개 클립을 생성했다. [최종 선택 비교](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/native-final-decision-comparison.json).
3. **실제 분석 재시도:** 실제 CPU-native 모델로 세 프레임을 분석한 뒤 OOM 종류의 오류를 주입. 두 플러그인 모두 새 CPU 시도로 완료했으며 최종 선택이 CPU 기준과 같았다. 저장 원본의 inode도 입력과 독립임을 확인했다. **실제 GPU OOM을 유발한 시험은 아니다.** [재분석 증거](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/native-recovery-proof.json).
4. **실제 Nest 소비:** 위 CPU/ONNX 결과 4개를 실제 ProjectDetailBuilder/LocalArtifactStorage로 조회. 클립·인물·미리보기·저장 원본 경로가 모두 연결됐다. [소비자 확인](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/native-nest-consumers.json).

이 짧은 정지 인물 영상은 움직임·다인 안무·참조 얼굴·한국어/영어 음성의 전체 품질 인증을 대신하지 않는다. 실제 Windows/Apple Silicon GPU 실행·속도·실영상 품질은 사용자가 예정한 기기 시험에서 확인해야 한다. 프로세스 시작·모델 로딩·원본 SHA 검사·원본 복사 비용이 추가되므로, 전체 앱 5% 성능 회귀 기준을 통과했다는 주장도 하지 않는다.

## 회귀와 독립 검토

- Python 전체: **3103 passed / 6 failed / 6 skipped**. [전체 로그](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/full-python.log). 6개 렌더 골든/전환 실패의 assertion은 이전 로그와 동일하다. 형제 Angular 경로 연결로 이전 skip 1개도 실행됐다. [대조](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/baseline-comparison.json).
- 넓은 대상 회귀: **485 passed**. 검토 전 실행이며, 검토 수정은 아래 별도 시험과 실제 native 재분석으로 재검증했다.
- 마지막 수정 대상: **56 passed**. 원본 변경 검사, 얼굴 epoch, runtime probe, GPU 실제 노드 확인, 음성 timeout·CPU 실패 정책 포함. [로그](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/final-last-targets.log).
- Electron 설치·bundle filter 대상: **24 passed**, TypeScript build 통과. 시험 결과·runtime cache와 `plugin_models`의 기기별 cache를 앱에 넣지 않도록 했다.
- 독립 reviewer가 원본 교체, 얼굴 내부 fallback, 외부 런타임의 worker 누락을 발견해 수정했다. 그 후 원본 hardlink와 ctime 검사 충돌도 실제 native 재현으로 수정했다. [검토 로그](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/independent-final-review.log). 마지막 CPU 음성 실패 정책도 [별도 8개 시험으로 확인했다](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/independent-speech-policy-review.log).
- 원본 소스 2087개와 기존 변경·모델 120개의 해시가 유지됐다. 원본 checkout은 수정하지 않았으며 commit/push/앱 실행도 하지 않았다. [보존 확인](/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/next-integration/original-preservation.json).

## 수동 GPU 시험 방법

Python 작업트리에서 실행한다. `--params`는 원래 작업 설정 JSON이며 안무 참조 사진/이름 등을 동일하게 공급할 때 사용한다. CPU와 후보는 서로 다른 output 폴더를 쓴다. 준비 명령의 `--source`에는 현재 앱이 사용하는 `yolov8s-pose.pt`를 지정한다.

먼저 원래 CPU 기준:

```text
uv run --frozen --package clipper-plugin-dance-highlight python -m scripts.accelerators.run_visual_test --plugin dance_highlight --video "영상 경로" --output "CPU 결과 폴더" --cpu --params "작업 설정.json"
```

Mac Apple Silicon의 CoreML 후보 준비:

```text
uv run --frozen --package clipper-plugin-dance-highlight python -m scripts.accelerators.prepare_yolo_test --source "yolov8s-pose.pt 경로" --output "가속 준비 폴더" --backend ort_coreml
```

Windows x64의 DirectML 후보 준비. `--uv`는 uv 실행 파일이다. 첫 실행에는 별도 Python/ORT 환경 다운로드가 필요하며 기존 CPU plugin 환경과 섞지 않는다:

```text
uv run --frozen --package clipper-plugin-dance-highlight python -m scripts.accelerators.prepare_yolo_test --source "yolov8s-pose.pt 경로" --output "가속 준비 폴더" --backend ort_dml --uv uv --adapter-index 0
```

생성한 plan으로 실제 분석:

```text
uv run --frozen --package clipper-plugin-dance-highlight python -m scripts.accelerators.run_visual_test --plugin dance_highlight --video "영상 경로" --output "GPU 시험 결과 폴더" --plan "가속 준비 폴더/pose-test-plan.json" --params "작업 설정.json"
```

인물은 package를 `clipper-plugin-person-highlight`, plugin을 `person_highlight`로 바꾸며 `--params`는 생략할 수 있다. `profiles` 아래 실제 provider 실행 기록과 시간을 저장한다. GPU 후보 명령의 exit 0은 분석 완료와 요청 GPU 노드 확인, exit 3은 요청 GPU 실행을 확인하지 못한 경우다. CPU로 재분석해 결과가 완성돼도 GPU 시험은 exit 3으로 구분된다. 취소는 Ctrl+C다.

앱으로 시험하려면 `CLIPPER_ACCELERATOR_TEST_PLAN`에 plan의 절대 경로를 설정한 프로세스에서 빌드/실행한다. 준비 도구는 개발 시험용이며 모델 exporter를 일반 고객 앱 실행에 추가한 것이 아니다.

현재 빌드 작업트리는 `/Users/jina/project/adlight/.worktrees/clipper-electron-accelerators-20261103`이다. 형제 Python/Nest는 이번 작업트리, Angular는 기존 작업 원본으로 연결돼 있다. 현재 원본 저장소에서 빌드하면 이 변경이 자동으로 포함되는 것은 아니다.

## 이어서 구현할 범위

실제 모델 연결 단계가 진행 중이다. 다음 작업은 나머지 얼굴/CLIP/Whisper 후보와 원래 CPU 기준을 모델별로 연결하고, 실제 환경 탐지·검증된 runtime pack·자원 임대·실측 cache를 실제 작업의 자동 선택에 연결하는 것이다. 새 설정/진단 UI와 일반 자동 실행 승격까지 끝난 상태로 보고하지 않는다. 사용자 실기기 시험에서 나온 품질·속도·provider 증거를 이 자동 선택에 사용할 수 있게 반영해야 한다.
