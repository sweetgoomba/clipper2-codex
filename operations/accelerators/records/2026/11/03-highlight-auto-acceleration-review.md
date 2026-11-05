# 세 하이라이트 자동 가속 설계·계획 검토 기록

2026-11-03 KST. 대상은 [설계](03-highlight-auto-acceleration-design.md)와 [구현 계획](03-highlight-auto-acceleration-implementation-plan.md)이다. 제품 구현과 실기기 품질 인증의 완료 기록이 아니다.

## 독립 builder check

brainstorming builder-check를 수행한 `/root/design_builder_check`는 최초 초안에서 다음 두 P1 미결정을 제기했다.

1. **인증의 장치 범위:** GPU 제품·드라이버 exact 조합, 계열 범위, 사용자 PC 자체 시험 중 무엇이 인증을 부여하는지 불명확했다.
   - 반영: certificate에 명시한 device ID/chip family·OS·driver 범위만 허용한다. 기본은 실제 시험 조합이며 범위 확대는 별도 근거와 릴리스 검토가 필요하다. 로컬 검사는 인증 범위를 넓히지 않는다. 범위 밖은 기존 인증 경로/CPU를 사용한다.
2. **사용자 PC의 시험 입력 배포:** 내부 corpus와 배포 fixture, 권리·오프라인 동작·기대 출력의 경계가 없었다.
   - 반영: 내부 개인 영상과 별개로 재배포 권리가 있는 `calibration-fixtures-v1`을 만든다. hash·CPU 기대 출력·라이선스·압축25MiB 상한·오프라인 사용·누락/불일치 시 후보 미활성화를 정했다.

수정본 재검토 결과 두 P1 모두 해소됨을 확인했다. 검토자의 결론은 두 항목에 관한 “nothing important left”이며, 구현 코드나 전체 하드웨어 호환성에 대한 승인으로 확대하지 않는다.

## 작성자 자기 검토

- 범위: Apple Silicon/Windows x64, 활성6모델/disabled2개, ARM 후속 분리를 두 문서에 일치시켰다.
- 실제 소스 대조: 대사 stage 이름은 `transcribe_media`/`analyze_media`; 기본 `analyze_media` 안에서 STT와 CLIP을 모두 실행하므로 CPU 복구도 둘을 포함하도록 바로잡았다. person 파일은 `speech_stage.py`, Electron bridge는 `src/main/backend/plugin-host-bridge.ts`임을 확인했다.
- 타입 일치: 단일 모델의 `ExecutionContext`와 전체 분석의 `AnalysisContext`를 분리했다. commit revision은 단조 증가 정수, epoch는 UUID다. 여러 runtime worker는 같은 unit lease의 worker 집합과 총 메모리 예산으로 관리한다.
- 품질: ONNX CPU/GPU 키트 비교를 기존 PyTorch/OpenCV 대비 품질·속도 증거로 대신하지 않는다. YOLO 관절, YuNet 실제 decode/NMS, 얼굴 identity, CLIP 장면/후속 구간, Whisper 자막을 별도 gate로 넣었다.
- 경계: GPU worker crash, CPU 재시도1회, 취소, 기존 결과 보존, Windows 파일 잠금, 후속 stage·프로젝트 파일 읽기의 generation resolver, 캐시 epoch/실제 backend 분리를 T05–08/T12에 연결했다.
- 계획 추적: 설계 §1–12가 T01–15에 연결되고 Review Focus5개 각각에 소유 태스크/시험이 있다. 기본 기능과 optional vendor 확장을 분리했다.
- 파일·형식 검증: 계획의 명시적 기존 파일33개와 설계의 절대 소스 링크12개를 검사했고 누락은 없었다. 신규 파일 표기는 별도로 구분했다. 태스크 T01–15 연속성, 활성6모델 등장, 코드 fence 균형, JSON 예시 파싱, 미결정 placeholder를 확인했다.

기계 검증 결과와 문서 SHA-256은 [검증 JSON](03-highlight-auto-acceleration-validation.json)에 있다. source HEAD는 조사 시점의 위치 표시이며 현재 미커밋 품질 작업을 대체하는 baseline이 아니다. T01에서 전체 dirty/untracked 내용과 모델·corpus까지 고정해야 한다.

## 아직 수행하지 않은 검증

모델 변환·추론, Python/TS 제품 시험, Windows/Mac 설치본 실기기 시험, 앱 재시작, dependency 설치, commit/push는 이 문서 작성에서 수행하지 않았다. 새 후보의 실제 지원 범위·성능·품질 합격은 구현 후 T01/T15 결과로만 결정한다.
