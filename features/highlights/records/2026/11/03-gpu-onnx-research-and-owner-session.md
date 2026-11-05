# 하이라이트 GPU·ONNX 조사 요약과 담당 세션

> 2026-11-04 상태 갱신: 아래의 공통 기반 1차/실제 연결 미완료/새 GPU 미활성은 11/3 11:16 초기 스냅샷이다. 이후 모델·설정·유휴 비교·CPU 복구를 연결하고 dev 반영 및 Mac 기본 얼굴 실측 적용을 마쳤다. [현재 색인](../../../../../operations/accelerators/README.md)과 [추가 실측](../../../../../operations/accelerators/records/2026/11/04-mac-remaining-models-speed-results.md)을 따른다. Windows와 전체 플러그인 품질은 검증 범위별로 구분한다.

2026-11-03 11:16 KST 확인 기준. 안무 하이라이트 개선 중 나온 GPU·ONNX 조사 내용을 인물·대사를 포함한 공통 하이라이트 문서에 연결한다. 이번 요청은 **문서화와 담당 세션 상태 확인**이며, 이 기록을 남기는 세션에서는 가속 코드 변경·빌드·벤치마크·병합을 추가 수행하지 않았다.

## 담당 세션과 현재 상태

담당 세션은 **[하이라이트 GPU·ONNX 전환 및 Windows 시험 도구 감사](codex://threads/01a19e03-43e4-7880-83f1-92e0b923fb88)**다. 조사뿐 아니라 후속 공통 기반 구현도 이미 이 세션에서 진행했다. 다른 세션에서 동일 구현을 중복 시작할 필요가 없다.

- 세션 ID: `01a19e03-43e4-7880-83f1-92e0b923fb88`, host `local`.
- 확인 시 상태: **idle**. 최신 턴 `01a19ef7-d3b3-7223-8da6-d1d7cabfe417`은 **completed**. 작업 소유 세션은 유지되지만 확인 시점에 실행 중인 것은 아니다.
- 최신 완료 범위: 품질 검증을 통과한 실행기만 비교·선택하는 공통 기반, 추론 프로세스 격리, GPU 오류 시 분석 단위 전체를 CPU로 한 번 재실행하는 복구 엔진, 성공한 결과만 공개하고 이전 성공 결과를 보존하는 저장·읽기 연결.
- **전체 기능은 미완료**다. 실제 세 플러그인의 모델 추론 연결, GPU 자원 조정, 배포 패키지·모델별 품질 기준·실장비 검증 등이 남았고, **새 GPU 자동 선택은 활성화하지 않았다**.
- Python 작업트리: `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103`, 브랜치 `codex/highlight-acceleration-20261103`.
- Nest 작업트리: `/Users/jina/project/adlight/.worktrees/clipper-nestjs-accelerators-20261103`, 브랜치 `codex/highlight-artifact-recovery-20261103`.

최신 세션 보고 기준 Python 3,049개 통과·기존 렌더링 실패 6개, Nest 5,246개 통과·실패 0개다. 첨부 모델 102개 입력의 직접 CPU 실행과 격리 CPU 실행 출력도 일치했다. 이 수치는 **GPU 속도나 최종 하이라이트 품질 검증을 뜻하지 않는다**. 원본 변경 파일·모델 120개 해시 보존을 확인했으며 커밋·푸시·앱 재시작은 하지 않았다고 기록돼 있다. 세부 근거와 이후 상태는 아래 담당 세션의 정본을 따른다.

## 정본과 근거 위치

- [실제 첨부 키트·9개 저장소·세 하이라이트 GPU 조사 보고서](../../../../../operations/accelerators/records/2026/11/03-windows-onnx-trial-and-highlight-gpu-review.md)
- [공통 자동 가속 기반 1차 구현·검증·남은 작업](../../../../../operations/accelerators/records/2026/11/03-highlight-auto-acceleration-implementation.md)
- [구현 검증 결과 JSON](../../../../../operations/accelerators/records/2026/11/03-highlight-auto-acceleration-implementation-validation.json)
- [Windows 키트 원본·결과·검증 반례](../../../../../operations/accelerators/records/2026/11/03-windows-onnx-kit-evidence/)
- [원격 브랜치·Git 이력·clipper_docs 검색 증거](../../../../../operations/accelerators/records/2026/11/03-windows-onnx-ref-search-evidence/)

이 문서는 하이라이트 기능 문서에서 위 정본으로 찾아가기 위한 요약이다. 이후 상세 설계와 구현 상태는 담당 세션 문서에서 갱신하며, 조사 완료·기반 구현·제품 활성화·실제 앱 성능 검증을 구분한다.

## 조사에서 확인한 핵심 내용

1. **기존 파이프라인을 버릴 필요는 없다.** 모델 실행 부분을 ONNX 실행기로 교체하거나 확장하면서 기존 구간·이름·메인 판정, 캐시·병렬 처리 개선을 함께 유지할 수 있다. ONNX 전환만으로 판정 품질이나 초단편 문제가 자동으로 해결되는 것은 아니다.
2. YuNet·AuraFace·SFace는 이미 ONNX다. 제품의 YOLO pose와 대사 CLIP은 현재 PyTorch 경로이므로 주요 실행 경로 교체 후보다. 인물·대사의 음성 인식은 별도 faster-whisper/CTranslate2 경로이며 키트의 CLIP 결과가 음성 처리 가속을 입증하지는 않는다.
3. Windows 키트의 YOLO 약 5.1~8.3배, YuNet 약 1.9배, CLIP 약 1.9~2.5배는 **같은 ONNX 모델의 ORT CPU 실행 대비**다. 현재 앱 전체 대비 배율이 아니다. 원본 영상 읽기, 전후처리, 이름·구간 조립 비용도 따로 남는다. Mac의 기존 MPS 경로에 Windows 배율을 그대로 적용할 수 없다.
4. AuraFace 오류는 **batch 8 첫 호출**에서 발생했다. 키트가 앞선 batch 1 결과까지 오류로 덮어썼으므로, 전체 GPU 실패라는 초기 해석은 정정했다. 소실된 batch 1 시간·정확도 수치는 확인할 수 없으며, shape 수정 후보도 Windows 실제 실행 검증 전이다.
5. 키트의 기존 품질 비교는 YOLO 관절 좌표·confidence와 YuNet 얼굴 위치·랜드마크 오류를 놓칠 수 있다. 출력 계약과 최종 판정까지 검증해야 한다. 실제 GPU 출력이 틀렸다고 확정한 것이 아니라, 기존 시험만으로는 그 오류를 배제할 수 없다는 의미다.
6. 확인된 PC는 Windows 10·GTX 1660 Ti다. 제조사 실행기 등록이 실패해 세 시험의 실제 GPU 실행기는 DirectML이었다. 마지막 시험을 NVIDIA 전용 실행기의 성능으로 해석하면 안 된다.
7. 조사 당시 9개 저장소의 최신 원격 refs·이력과 최신 `clipper_docs`에서 해당 키트의 커밋이나 전용 문서를 찾지 못했다. 이후 담당 세션에 제공된 실제 `run_kit.py`, 배치파일, 모델·표본·결과 파일로 구현을 확인했다. 미푸시 파일이나 다른 저장소까지 없다는 뜻은 아니다.

## 안무 하이라이트에서 먼저 진행했던 개선과의 관계

안무 세션은 이미 GPU 실행 경로와 CPU 측 비용을 함께 개선했다. 아래는 각 당시 기록이며 서로 다른 변경과 입력 상태의 결과를 하나의 가속 배율로 합산하지 않는다.

- [GPU 설정·병목 감사](../../../../dance-highlight/records/2026/11/02-gpu-performance-audit.md): YOLO의 Mac MPS 사용 확인, AuraFace CoreML 비교, 긴 몸 추적 비용 확인.
- [몸 추적 비용 축소·비활성화](../../../../dance-highlight/records/2026/11/02-mask-cost-reduction-results.md): 무거운 SAM 몸 추적 검증은 비용 제한 요구에 따라 OFF. 새 GPU 조사로 자동 재활성화하지 않는다.
- [메인 판정·얼굴 처리 개선](../../../../dance-highlight/records/2026/11/02-main-face-performance-results.md): CPU 얼굴 연산 병렬 처리, 캐시 계산과 미사용 검증 비용 감소.
- [YuNet·SFace 안무 전용 GPU 경로](../../../../dance-highlight/records/2026/11/02-yunet-sface-gpu-results.md): Mac CoreML·Windows DirectML 경로와 CPU 복구. 당시 Mac 실제 앱 세 영상 합계 27분 53초→26분 38초, 약 4.5% 단축으로 효과는 제한적이었다. Windows 실측은 별도다.
- [메인·얼굴 내부 비용 실측 개선](../../../../dance-highlight/records/2026/11/02-deep-profile-results.md): 모델 추론 밖 비용도 줄였으며, 당시 실제 앱 합계 26분 38초→20분 19초. 전체 품질 문제는 남았다.

이 수정들은 당시 원본 Python 작업 브랜치 `fix/dance-gpu-performance-20261102`의 미커밋 변경을 포함한다. `origin/dev`에 모두 들어갔다고 간주하지 않는다. 공통 가속 세션은 원본 변경을 보존하고 별도 작업트리에 재현한 뒤 진행했다. 이후 통합 시에는 그 세션 시작 뒤의 안무 변경까지 별도로 비교해야 한다.

## 이 안무 세션의 범위

GPU·ONNX 공통 구현은 위 담당 세션에서 이어가는 작업이다. 이 안무 세션에서는 이름 구간과 메인 구간을 교차 조립할 때 생기는 초단편 문제를 별도 품질 과제로 다룬다. [이름·메인 중복 경계 조립 수정 기록](../../../../dance-highlight/records/2026/11/03-identity-assembly-results.md)을 참조한다.

사용자가 보류한 **‘단체 조건에서 탈락하면 개인 메인으로 간주’하는 변경은 진행하지 않는다**. 무거운 몸 추적 OFF 및 인물 하이라이트에 영향을 주지 않는다는 이 세션의 범위도 유지한다. 공통 가속 세션의 세 플러그인 대상 작업은 그 세션의 별도 지시와 검증 범위를 따른다.
