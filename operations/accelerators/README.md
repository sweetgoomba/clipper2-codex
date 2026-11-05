# 하이라이트 자동 가속의 현재 구현과 검증

2026년 11월 4일 KST 기준. 안무·인물·대사에는 실행 환경 감지, 자동/CPU 설정, 실행기 비교, 오류 시 CPU 재분석과 결과 revision 관리가 연결돼 있다. 이번 후속은 Mac 얼굴 처리의 실제 병목을 줄였다. 모든 모델을 ONNX나 GPU로 바꾼 상태는 아니다.

대상은 Apple Silicon Mac과 Windows x64다. Intel Mac은 제외하며 Windows ARM은 후속으로 분리했다. Windows 기기별 조합 비교·실행 앱 빌드는 별도 채팅 담당이다.

## 읽는 순서

1. [Mac 추가 가속 실측](records/2026/11/04-mac-remaining-models-speed-results.md): Made My Night 안무 334.958초 → 266.034초, 20.58% 단축, 최종 63개 목록·설정·집계 동일.
2. [Mac 가속 사용과 검증 절차](runbooks/mac-highlight-acceleration.md): 설정 의미, 모델 선택, CPU 복구, 재현·빌드 명령, 진단과 남은 병목.
3. [종합 인계](../../records/sessions/2026/11/04-highlight-mac-acceleration-handoff.md): 반영 커밋, 코드 경계, 다른 채팅 담당, 보존, 후속 우선순위.
4. [첫 AuraFace 병목 개선](records/2026/11/04-face-coreml-speed-results.md): 별도 단일 비교 721.975초 → 327.616초. 이후 334.958초 재기준과 서로 다른 실행이므로 개선율을 단순 합산하지 않는다.

## 모델별 현재 Mac 경로

| 모델과 역할 | 플러그인 | 원본 형식과 기본 경로 | 이번 후속 상태 |
|---|---|---|---|
| YOLO Pose, 몸·관절 | 안무·인물 | .pt, Ultralytics/PyTorch CPU 또는 MPS | .pt/MPS 유지. 안무에서 끝난 모델·예약 해제 후 필요할 때 같은 모델 재생성 |
| YuNet, 얼굴 위치·랜드마크 | 안무·인물 | 원래 ONNX, OpenCV CPU | 안무의 명시된 원본 크기에 FP32 ONNX/CoreML 후보. 다른 ROI는 CPU. 인물의 source 크기 준비 미연결 |
| AuraFace, 얼굴 신원 특징 | 안무·인물 | 원래 ONNX, ORT CPU | 알려진 원본의 batch 1·내부 FP16/입출력 FP32 CoreML 후보. 로컬 비교·노드·메모리 검사 후 선택 |
| SFace, 보조 신원 확인 | 안무 | 원래 ONNX, OpenCV CPU | 기존 정렬·FP32 CoreML 후보 구현. 이번 전체 실행은 메모리 거절로 CPU |
| CLIP ViT-B-32, 장면 영상 특징 | 대사 | OpenCLIP/PyTorch CPU 또는 MPS | 기존 MPS·선택적 ONNX 구조 유지. 이번 안무 실측에는 호출 없음 |
| Whisper small, 전사·단어 시간 | 인물·대사 | faster-whisper/CTranslate2 | Mac CPU int8 유지. 새 음성 엔진으로 교체하지 않음 |
| SAM2 / OCR | 안무 / 대사 | 비활성 모델 | 이번 작업에서 재활성화·측정하지 않음 |

ONNX는 모델 표현 형식이고 MPS·CoreML·DirectML·CUDA 등은 실행 방식이다. .pt 모델도 지원 장치에서는 PyTorch로 GPU 실행할 수 있다. Windows 키트의 YOLO 7~8배는 같은 ONNX의 CPU 대비 DirectML 수치이며, .pt 변환만으로 앱 전체가 그 배율로 빨라진다는 의미는 아니다.

## 이번 검증의 범위

- 앱을 닫고 다른 무거운 측정을 중지한 단독 조건에서 안무 전체 334.958초 → 266.034초.
- 얼굴 검출 누적 104.721초 → 65.404초, 메인 인물 선택 118.110초 → 73.555초.
- main 49개 + group 14개. 구간·인물·상대 썸네일 경로·설정·집계 동일. 영상 1개·참조 사진 31장에 한정한다.
- YOLO MPS 2,459회, YuNet CoreML 2,275회 + CPU 3,389회, AuraFace 요청 4,603회, SFace CPU 3,925회.
- CPU 전체 재분석 없이 완료. CoreML 노드를 실제 ORT profile로 확인했다. CoreML ALL을 물리 GPU 단독 실행으로 확대하지 않는다.
- 관련 Python 2,073개, Electron 전체 1,977개 통과. 다른 범위의 과거 전체 테스트와 합쳐 저장소 전체 무결점으로 표현하지 않는다.

## 반영과 Mac 앱

| 저장소 | 이번 최종 dev 커밋 |
|---|---|
| Python | 17259bcf1c7c466cd7108e04a25250172dd28151 |
| Electron | 849a51b7906f84054e1a55d02da45bfa3768be6f |

앞선 AuraFace a73593a와 MPS 승인 6831d8d의 후속이다. 두 최종 커밋은 원격·원본 dev에 반영했다. 기존 Angular/Nest 공통 가속 연결을 이번 후속에서 다시 수정하지 않았다.

원본 Electron의 npm run build:app:mac:arm64:local-api를 완료했다. [Mac 앱](</Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app>)의 패키지 API는 http://127.0.0.1:3000이며 업데이트는 꺼져 있다. 소스/패키지 10개·설치 모듈 7개·app.asar lease SHA, 앱 시작·안무 입력 화면·API/Nest health를 당시 확인했다. 같은 기본 앱 경로는 다음 빌드에서 교체될 수 있으므로 현재 revision은 실제 패키지와 다시 대조한다. 개발/운영 서버 배포는 하지 않았다.

## CPU 복구와 승인 기록

“전체 CPU 복구”는 삭제한 프로젝트나 파일을 복원하는 뜻이 아니다. 선택한 GPU가 분석 도중 실패하면 임시 실패 결과를 공개하지 않고 해당 분석 단위를 처음부터 CPU로 한 번 재분석하는 동작이다. 이전 성공 결과와 사용자 프로젝트는 보존한다.

후보 선택 전의 품질·속도·메모리 거절은 원본 CPU로 이어갈 수 있다. GPU 결과를 사용한 뒤에는 얼굴 한 장만 CPU로 바꿔 섞지 않는다. 취소·입력 오류·CPU 자체 실패를 GPU 성공/복구로 처리하지 않는다.

기존 선택적 팩의 일반 자동 채택에는 모델·입력·소비자·환경의 승인과 유효한 측정이 필요하다. 이 기기 시험이나 유휴 비교 성공은 모든 후보의 제품 승인을 자동 생성하지 않는다.

이번 기본 Mac 얼굴 경로는 알려진 원본 hash·고정 변환·실제 입력 로컬 수치/속도 비교·노드·메모리 검사를 거쳐 그 분석에서 선택한다. 범용 선택적 팩 승인과 별도 경로다. 전기기 인증서를 발급하지 않으며 진단의 release_qualified=false도 유지한다. “새 GPU 전체 차단”이나 “모든 GPU 승인 완료”로 요약하지 않는다.

## 이력과 담당

| 기록 | 단계 |
|---|---|
| [초기 설계](records/2026/11/03-highlight-auto-acceleration-design.md) · [계획](records/2026/11/03-highlight-auto-acceleration-implementation-plan.md) | 요구·후보·계획. 현재 완료 목록과 구분 |
| [독립 감사](records/2026/11/03-highlight-auto-acceleration-independent-audit.md) · [수정](records/2026/11/03-highlight-auto-acceleration-audit-remediation.md) | 인증·품질·revision·실제 CPU 복구 |
| [모델·설정 연결](records/2026/11/03-highlight-auto-acceleration-completion.md) | 얼굴·CLIP·Whisper·앱 설정 통합 |
| [유휴·순환 비교 최종 수정](records/2026/11/03-highlight-idle-rotation-reaudit-remediation.md) | foreground 우선·소유 자식 종료·실행기 비교 |
| [범위 선별 dev 반영](records/2026/11/03-highlight-acceleration-scoped-dev-merge.md) | 다른 품질 작업 보존과 가속 변경 통합 |
| [MPS 승인·CPU 복구 수정](records/2026/11/04-mps-admission-cpu-recovery-fix.md) | Mac 공유 메모리 예산·거절 사유 |
| [원본 8개·대량 변경 조사](../env-runtime/records/2026/11/04-original-eight-repositories-independent-audit.md) | 비교 앱/캐시가 소스 변경으로 보인 이유 |
| [Windows 담당 채팅](codex://threads/01a1a294-76cc-7d73-af4d-be827b33bde9) | Windows x64 조합 비교·실행 앱 |

“현재”는 위 날짜와 커밋의 상태다. Windows 채팅의 이후 변경·실기기 결과는 그 채팅의 새 기록을 따른다.

## 문서 검증

[문서 검증 결과](records/2026/11/04-mac-acceleration-documentation-validation.json)에 링크, 명령 예시, 저장 결과 동등성, 기존 증거와 미커밋 본문 보존 검사를 남겼다. 기존 성능 시험을 다시 실행한 결과와 구분한다.
