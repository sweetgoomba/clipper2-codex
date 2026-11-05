# YuNet·SFace GPU 가속 — 구현·검증 기록

2026-11-02. 안무 전용 가속 구현·원본 앱 빌드·3영상 YouTube 실행 및 전후 비교 완료. **출력은 보존됐지만 전체 시간 단축은 합계4.5%로 제한적이다.** Windows 실제 기기 검증은 미완료다.

## 범위

- 원본 `desktop/clipper_python`, `fix/dance-gpu-performance-20261102`, HEAD `4b54bced17e13aadbeb97be75259b7f7213a9b24`. 기존 미커밋 변경 보존. 커밋/푸시/병합 없음.
- 원본 Electron `npm run build:app:mac:arm64:local-api` 성공. 패키지의 안무 Python·pyproject·lock 54개 SHA256이 작업 소스와 일치.
- 인물 플러그인·공유 face core·SDK 제품 소스 변경 없음. SAM 복원 및 joint SAM 검증은 주석 상태 유지.

## 구현

`services/opencv_acceleration.py`에 안무 전용 어댑터를 둔다. 기존 OpenCV 객체를 CPU 복귀 및 SFace 정렬에 사용한다. 모델 가중치·원본 픽셀·해상도·임계값·샘플링·구간 정책은 변경하지 않는다.

- **YuNet**: 원본 영상 크기를 한 번 읽고, 32배수로 아래/오른쪽 0 padding한 동일 BGR 입력으로 고정 크기 ONNX Runtime 세션을 준비한다. 원본과 같은 크기의 프레임은 GPU, 다른 크기의 ROI는 기존 OpenCV CPU. 가변 크기 CoreML은 이번 Mac에서 느려 채택하지 않았다. 크기별 ROI 세션을 만들지 않으며 서비스당 원본 크기 세션은 최대 하나다. 원본 크기가 바뀌면 이전 세션을 해제한다. CoreML 디스크 캐시는 모델 파생 bytes hash로 구분되며 서로 다른 원본 해상도별 캐시는 디스크에 남는다.
- YuNet의 640×640 고정 중간 shape metadata를 제거하고 해당 영상의 shape를 다시 추론한다. 가중치와 노드 연산은 보존한다. score clamp·sqrt·stride decode·후보 순서·**정수 박스 NMS**는 OpenCV 4.13과 같게 구현한다.
- **SFace**: 원본 OpenCV `alignCrop`를 유지한다. 112×112 RGB float32, scale1 입력으로 동일 모델을 실행한다. 픽셀 정규화를 추가하지 않는다. 상수 initializer를 중복 graph input으로 기록한 오래된 metadata만 정리한다. 같은 FaceClusterService를 쓰는 검증 단계끼리 SFace 세션을 공유한다.
- **Mac**: CoreML MLProgram CPUAndGPU, float32 accumulation. 실제 MLComputePlan에서 Apple M4 GPU 배정 확인.
- **Windows**: 제공되는 CUDA 실행기가 있으면 TF32를 끄고 사용, 기본 배포 의존성은 DirectML1.24.4. DirectML은 ORT_SEQUENTIAL·memory pattern 비활성·단일 세션 호출 lock 적용. Windows 의존성 export에는 CPU onnxruntime이 중복되지 않음. 실제 Windows 기계 실행은 미검증.
- 가속 준비/호출 실패 또는 잘못된 출력은 기존 OpenCV CPU로 복귀. 프레임마다 실패한 GPU를 무한 재시도하지 않는다. 런타임 조회 및 face_evidence에 실제 provider·호출 수·복귀 횟수·시간을 기록한다.

## 실험

- 동적 YuNet 1920×1088: CoreML 약50.6ms, OpenCV28.7ms → 채택 안 함.
- 고정 YuNet 1920×1088: CoreML 약11.7ms, OpenCV33.1ms. 단일 프로토타입의 warm 값이며 전체 분석 시간 단축률이 아님.
- SFace: CoreML 약2.9ms, OpenCV7.0ms. 초기 컴파일/첫 실행 비용은 warm 추론과 별도다. 실제 앱 wall time에는 그 실행에서 발생한 로딩 비용이 포함된다. 모델과 영상 캐시는 이미 있는 상태이며 신규 설치/빈 캐시 측정이 아니다.
- 세 실제 영상에서 각48프레임, 총144프레임·628얼굴 비교: 검출 개수/순서 같음. 좌표 최대 절대오차0.000183px. 정렬 픽셀은 일부 최대6밝기값 차이, SFace 벡터 cosine distance 최대9.18e-6. 수치가 bit-identical하다는 뜻은 아니므로 최종 멤버 분류와 클립 경계를 전체 앱 출력으로 다시 비교한다.

## 테스트·검토

- TDD: 신규 테스트13개 실패→13개 통과, 런타임 연결2개 실패→15개 통과. 관련 통합58개 통과. 보조 얼굴 기존 테스트31개 통과.
- 독립 리뷰에서 CPU-only CI의 테스트 가속기 가정 문제를 발견하여 fake_gpu fixture로 수정. 리뷰어가 CPU-only provider 환경에서 신규15개 재검증. 추가 Critical/Important 제품 결함 없음.
- 전체 `.venv/bin/python -m pytest -q`: 샌드박스 바인딩 제한으로 오류가 나 제한 없는 실행으로 재검증. **2,528통과, 6실패, 6생략**. 실패는 미수정 렌더링 영역: `test_annotation_layer_renderer.py::{test_counter_formats_value_and_matches_goldens,test_chip_tones_and_badge_goldens,test_arrow_goldens,test_arrow_target_above_golden,test_layer_without_area_or_zone_tops_is_byte_identical_to_before}`, `test_clipper_video_render_ranking_transitions.py::test_real_render_list_holds_still_through_transitions_and_switches_at_handoff[fadeblack]`. 전체 테스트 green이라고 보고하지 않는다. 관련 소스·golden은 변경하지 않았다.
- `git diff --check`, 신규 모듈·테스트 ruff 통과.

## 비교 기준

직전 실제 앱 CPU 병렬 개선 결과를 기준으로 한다. SAM-on 및 초기 SAM-off 결과와 혼동하지 않는다.

| 영상 | 기준 프로젝트 | 실행 시간 | 미확인 초 | 전체 클립 | 1초 미만 |
|---|---|---:|---:|---:|---:|
| Made My Night |1793599782691|440.817|6.8072|89|42|
| ANTIFRAGILE |1793599859534|586.194|16.0178|134|79|
| NEON |1793599963190|646.469|16.8184|207|125|

URL은 각각 `https://youtu.be/BZDZBUyaJbA`, `https://youtu.be/p_XdZdg9oGc`, `https://youtu.be/93j1fDGi_-8`. 앱 UI로 제출하고 기존 저장 대표이미지를 그대로 사용한다. 시작→완료 시간에서 대기열 시간은 제외. 앞선 검사/빌드 프로세스는 실제 분석 전에 완료시켰다.

## 공식 근거

- [OpenCV 4.13 YuNet](https://raw.githubusercontent.com/opencv/opencv/4.13.0/modules/objdetect/src/face_detect.cpp)
- [OpenCV 4.13 SFace](https://raw.githubusercontent.com/opencv/opencv/4.13.0/modules/objdetect/src/face_recognize.cpp)
- [ORT CoreML](https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html)
- [ORT DirectML](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html)
- [ORT CUDA](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)

작업 증거: `/private/tmp/dance-yunet-sface-20261102`. 모델·영상 대용량 파일을 문서에 복제하지 않는다.


## 실제 빌드 앱 최종 결과

| 영상 | 기준→이번 프로젝트 | 기준 시간 | GPU 적용 후 | 단축 |
|---|---|---:|---:|---:|
| Made My Night |1793599782691→1793603593237|7분20.817초|6분45.185초|35.632초 / 8.1%|
| ANTIFRAGILE |1793599859534→1793603739918|9분46.194초|9분16.052초|30.142초 / 5.1%|
| NEON |1793599963190→1793603971986|10분46.469초|10분36.499초|9.970초 / 1.5%|
| 합계 ||27분53.480초|26분37.736초|1분15.744초 / 4.5%|

각 조건 영상별1회 실측이며 신뢰구간을 계산한 반복 실험이 아니다. 특히 NEON의1.5% 차이는 작으므로 안정적인 큰 성능 향상이라고 해석하지 않는다. 요청한 가속 경로와 실제 실행은 확인했으나, 전체 분석이 충분히 빨라졌다는 목표는 달성했다고 보지 않는다.

### 품질·격리 결과

- **430개 클립 전체 행(멤버·유형·시작·끝 포함), 인물 카드, 430개 썸네일이 모두 기준과 같다.** 기준과 이번 각각의 main/group 리스트를 완전 비교했다.
- **9,266개 판정 프레임**이 모두 같다: MMN2324 / ANT3310 / NEON3632. 메인 몸·단체 판정 기록까지 비교했다.
- 미확인 시간6.8072 /16.0178 /16.8184초, 1초 미만42 /79 /125개, 전체89 /134 /207개 그대로다. 이름별 시간 커버리지 변화0초.
- 사용자 피드백14구간의 분류와 클립 경계도 그대로다. 기존 오분류/잘린 클립이 새로 해결됐다는 뜻은 아니다.
- 원본 영상 SHA256, 설정 SHA256, 프로젝트에 저장된 대표 이미지 파일 bytes, 대표 이미지 manifest 및 primary embedding이 세 영상 모두 동일하다.
- 실제 가속 호출 누계: YuNet8701회, SFace16420회. 가속 오류로 CPU 복귀0회. YuNet ROI CPU12894회는 의도된 경로다. 수치는 동일 앱 프로세스의 세 작업 누계이며 영상별 수치처럼 합산하지 않는다.
- SAM 복원 및 joint SAM 시간은 세 영상 모두0초. 기존의 가벼운 저장 포즈/색상 공백 검증은 그대로이며, 꺼둔 추가 SAM 모델을 다시 실행하지 않았다.
- 원본 앱 프로젝트 목록에서 새3개 결과(16:19 /16:29 /16:39)를 확인했고 앱을 열어두었다. 커밋·푸시·dev 병합 없음.

### 전체 단축이 작은 이유와 남은 작업

측정된 메인 판정은137.54→92.77 /200.49→155.84 /196.27→150.33초로, 각 영상 약45초 줄었다. 그러나 이 단계 밖의 비용은 그대로 있거나 이번 실행에서 늘었다. 특히 NEON은 포즈101.30→110.04초, 장면 구성77.10→83.49초, 얼굴 특징98.82→109.38초, 이름/연속성 묶음118.38→123.58초였다. 이 증가를 GPU 회귀나 열/시스템 부하 중 하나로 단정할 측정은 아직 없다.

SFace 추론 자체는 가속됐지만, `secondary_faces` 단계는 모델 추론만 측정하는 구간이 아니다. 영상 읽기·정렬·갤러리 및 이름 판정 등도 포함되어 MMN52.75→45.64초, ANT65.17→62.61초, NEON56.83→55.88초로 전체 단계의 이득은 작았다. ROI YuNet은 많은 입력 크기의 재컴파일 비용을 피하기 위해 CPU에 남겼다. CoreML을 모든 크기에 강제 적용하는 실험은 오히려 느렸으므로 채택하지 않았다.

다음 성능 작업에서는 남은 메인/얼굴 단계 안의 영상 디코딩·ROI/회전 검출·정렬·이름 비교 비용을 따로 계측해, 실제 큰 비용의 반복을 줄여야 한다. 샘플 수/해상도/판정 기준을 낮춰 이번 결과 보존을 깨는 변경은 하지 않았다. 몸 추적 재활성화는 대상이 아니다. Windows DirectML 실기기 검증도 별도로 남는다.

### 보존된 증거

[증거 manifest](02-yunet-sface-gpu-evidence/manifest.json), [최종 요약](02-yunet-sface-gpu-evidence/app/final-summary.json), [전체 전후 비교](02-yunet-sface-gpu-evidence/app/run-comparison.json), [입력·가속 확인](02-yunet-sface-gpu-evidence/app/provenance-comparison.json), [14사용자 구간](02-yunet-sface-gpu-evidence/app/reviewed-case-analysis.json), [전체 테스트 로그](02-yunet-sface-gpu-evidence/full-suite-unrestricted.log).
