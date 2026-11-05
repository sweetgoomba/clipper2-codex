# Mac 하이라이트 가속 구현과 검증 인계

2026년 11월 4일 KST. 공통 가속을 dev에 통합한 뒤 Mac의 큰 CPU 얼굴 병목을 줄였다. 최종 Made My Night 안무 분석은 334.958초 → 266.034초이며 63개 목록·설정·집계가 같고 CPU 재분석은 없었다. 이번 문서화에서는 제품 소스·앱·설정·서버를 바꾸거나 새 성능 시험을 실행하지 않았다.

[현재 색인](../../../../operations/accelerators/README.md) → [사용·재현·장애 확인](../../../../operations/accelerators/runbooks/mac-highlight-acceleration.md) → [실측 보고서](../../../../operations/accelerators/records/2026/11/04-mac-remaining-models-speed-results.md) 순서로 읽는다.

## 사용자 결정과 작업 범위

- 지원 대상은 Apple Silicon Mac과 Windows x64다. Intel Mac은 제외하고 Windows ARM은 후속으로 분리했다.
- 실행 시간 단축을 우선하며 기존 품질과 작업 중 변경을 보존한다. 검증 영상은 Made My Night 하나다.
- Windows는 새 채팅에서 계속하고 이 세션은 Mac 병목을 맡는다.
- dev 통합은 이번 가속 변경만 반영한다. 독립 품질 작업을 임의로 합치거나 덮어쓰지 않는다.
- 개발 서버 배포 전에 원본 8개 dev와 local-api Mac 앱을 확인한다.
- 사용자 허락 후 앱을 잠시 종료했고, 측정 후 새 앱으로 다시 실행했다. 사용자가 직접 삭제한 프로젝트는 복원하지 않았다.
- 원본 8개와 대량 변경 조사도 새 채팅에서 완료했다. 이후 그 채팅의 사용자 지시로 수행한 DB·서버 작업은 별도 이력이다.

## 완료와 검증 경계

| 영역 | 완료한 내용 | 검증 경계 |
|---|---|---|
| 공통 기반 | 실제 모델 연결·설정·유휴/순환 비교·CPU 복구·revision | 모든 후보를 모든 PC에서 승인한 것은 아님 |
| MPS 시작 | 공유 메모리 예산과 오류 분류 수정 | 04-mps 기록 참조 |
| AuraFace | 알려진 원본의 CoreML 로컬 선택 | MMN 721.975초 → 327.616초, 63행 동일 |
| YuNet과 수명 | 원본 크기 FP32 CoreML·다른 ROI CPU·단계별 YOLO/YuNet 해제 | MMN 재기준 334.958초 → 266.034초 |
| SFace | FP32 후보·원래 정렬·진단 | 단독 샘플 확인, 전체 MMN은 메모리 거절로 CPU |
| Person | 공통 AuraFace·기존 자동 선택 | 이번 전체 속도 미측정, YuNet source 크기 준비 미연결 |
| Dialog | CLIP MPS/선택적 ONNX·Whisper 복구 | 이번 안무에서 호출되지 않음 |
| Whisper | 기존 CTranslate2 계약 유지 | Mac CPU int8, 새 음성 엔진 미구현 |
| 앱과 dev | Python/Electron 원격·원본 반영, Mac 빌드·설치 환경·기동 | Windows 실기기와 서버 배포 완료는 아님 |

모델·소비자·실행 경로·검증 영상을 나누어 설명한다. “전부 ONNX”, “얼굴 전부 CPU”, “새 GPU 전부 차단”, “모든 하이라이트 품질 동일”은 현재 상태를 정확히 나타내지 않는다. 기존 63행 보존은 초단편·미확인 문제 자체를 해결했다는 주장도 아니다.

## 최종 코드 경계

| 저장소 | 이번 커밋 | 직전 기준 |
|---|---|---|
| Python | 17259bcf1c7c466cd7108e04a25250172dd28151 | a73593a2c6445bc87401eb4de30e9954ef2467ba |
| Electron | 849a51b7906f84054e1a55d02da45bfa3768be6f | 6831d8de76d34bb6ae2523122e9c6271ba68d00f |

원격과 원본 dev에 반영했다. 아래 Python 경로는 /Users/jina/project/adlight/desktop/clipper_python 기준이다.

| 파일 | 책임 |
|---|---|
| clipper_accelerators/clipper_accelerators/native_face.py | 원본·변환 hash, 최초 비교, 노드 확인, CPU 참조 해제/재생성, 늦은 오류 |
| 같은 패키지 native_yunet.py | source 크기 FP32 후보, CPU ROI, 집계, 단계 해제 |
| 같은 패키지 native_sface.py | 기존 alignCrop, FP32 후보, 선택 고정 |
| 같은 패키지 face_adapter.py | 선택적 팩과 기본 후보 연결 |
| 같은 패키지 native_sessions.py / lease_client.py | 소유 모델별 승인, ACK 후 예약 반환 |
| clipper_face_core/clipper_face_core/opencv_backend.py | 자체 집계 detector의 중복 기록 방지 |
| plugins/dance_highlight/dance_highlight/services/pose_engine.py | 실제 MPS 모델 파괴·할당 0 확인·지연 재생성 |
| 같은 services의 face_runtime.py / pipeline.py | 기존 캐시 유지, 마지막 사용 단계에서 해제 |
| clipper_accelerators/tests의 native face/yunet/sface/phase tests | 품질·거절·늦은 실패·동시성·모델 생존 회귀 |

Electron은 src/main/accelerators/leases.ts와 test/accelerator-admission-memory.test.js만 이번 후속에서 변경했다. /unreserve-native와 지원 flag를 추가하고 토큰·소유권·활성 worker·메모리 승인을 유지한다. SAM 활성화·threshold·샘플링·영상 크기·판정 정책은 바꾸지 않았다.

## 증거와 검증

- [구조화 요약](../../../../operations/accelerators/records/2026/11/04-mac-remaining-models-speed-results.json).
- [원본 57개 증거 manifest](../../../../operations/accelerators/records/2026/11/04-mac-remaining-models-speed-results-evidence/manifest.json): 소스 patch·실측·후보·host·red/green·빌드·설치 SHA·health.
- [문서화 보충 증거](../../../../operations/accelerators/records/2026/11/04-mac-acceleration-documentation-evidence/): baseline/final view·원본 결과 SHA·테스트 runner·provenance.
- 관련 Python 2,073개/54.80초, Electron 전체 1,977개/34.812초. 최초 Electron 두 실패, 단독 20개 통과, 제한된 동시성의 전체 재통과도 보존했다.
- 영상 SHA는 3400a0f3d21399609c54b38884d0208bf28e2541e10d450c5135306deba2e363이며 참조 사진은 31장이다. 출력 목록 SHA는 20e815c03c379b28af5b8e76031cb09db917037f2814fd82c46055fae6ce8d0d다.
- 앱을 닫은 단독 조건이다. 중복 실행·메모리 압력·다른 선택 조합은 최종 속도 결론에서 제외했다.

과거 시험을 이번에 재실행했다고 표시하지 않는다. 날짜·실제 소비자/모델·종료 코드·결과 비교를 함께 읽는다.

## 앱과 보존

원본 Electron의 local-api arm64 빌드는 exit 0으로 완료했다. 앱은 dist-app/mac-arm64/Clipper Studio (dev).app, API는 http://127.0.0.1:3000, autoUpdateDisabled=true다. 당시 원본 8개 HEAD·서버 dev·추적 변경 0을 대조했다. 패키지 10개·설치 7개 모듈·app.asar lease SHA가 일치했고 안무 화면·API 3000·Nest 동적 52454 health를 확인했다. 현재 실행 상태와 동적 포트는 재개할 때 다시 확인한다.

직전 앱 .tmp/mac-before-remaining-face-20261104, 이전 비교 앱 2개, Python 캐시를 보존했다. VSCode의 Electron 1,720개/Python 38개는 과거 앱·캐시였고, 이후 .git/info/exclude로 보이지 않아도 삭제된 것이 아니다. [독립 조사](../../../../operations/env-runtime/records/2026/11/04-original-eight-repositories-independent-audit.md)와 [최종 보존 JSON](../../../../operations/accelerators/records/2026/11/04-mac-remaining-models-speed-results-evidence/original-dirty-counts-final.json)을 함께 본다.

03:43 재빌드는 a73593a/6831d8d 시점이며 이후 가속 빌드는 17259bc/849a51b 시점이다. 같은 앱 경로라도 과거 SHA를 최신 앱에 그대로 적용하지 않는다.

## 후속 우선순위

1. 사용자 Mac 실사용 조건에서 측정할 때 자동/시험 모드·UI 메모리·compile/cache·환경·단계/모델 시간을 함께 기록한다.
2. 남은 메인 선택·CPU ROI·SFace·구간/후처리 비용은 동시 수명·실제 peak·준비/전송 비용부터 확인한다.
3. Person source 크기 연결과 고정 face_provider 표시는 개선 후보다. 전체 시각/음성 분석과 인물 신원을 검증하기 전에는 완료로 표현하지 않는다.
4. Mac Whisper는 CPU 비용 측정 후 small/beam 5/word timestamp/chunking·전사/자막 품질을 별도로 검증해야 한다. 이번에는 교체하지 않았다.
5. Windows 담당은 실제 지원 가능한 조합만 순환 비교한다. Mac 배율이나 DirectML 한 PC 수치를 전체 최선으로 사용하지 않는다.

이는 후속과 검증 공백 목록이다. 문서화 요청만으로 모델 교체·재시험·서버 배포·사용자 데이터 정리를 자동 재개하지 않는다.

## 담당 채팅과 재개

- Mac·공통 원래 세션: [하이라이트 GPU·ONNX 전환 및 Windows 시험 도구 감사](codex://threads/01a19e03-43e4-7880-83f1-92e0b923fb88).
- [Windows x64 하이라이트 가속 조합 비교와 실행 앱 빌드](codex://threads/01a1a294-76cc-7d73-af4d-be827b33bde9): 두 커밋·보고서·측정 완료·빌드 재개를 전달했다. 이번 문서화에서는 추가 조회나 메시지를 보내지 않았다.
- [원본 8개 저장소 dev 상태와 대량 변경 파일 독립 확인](codex://threads/01a1a2af-d619-7691-866b-77adad808c0d).

## 이번 문서화

기존 57개 증거와 manifest를 검증·보존하고 현재 색인·사용/재현 절차·종합 인계·기존 진입점을 보강했다. 제품 소스·환경·설정·결과·배포 상태는 바꾸지 않았고 문서 커밋·푸시도 하지 않았다. 다른 세션의 미커밋 문서 내용은 유지했다.

## 문서 자체의 검증

[문서 검증 JSON](../../../../operations/accelerators/records/2026/11/04-mac-acceleration-documentation-validation.json)에 새 링크·명령 문법·결과 대조·증거 hash 검사 결과를 남겼다. 기존 8개 문서에 이번 추가분을 제외한 본문이 그대로 보존됐는지도 hash로 확인했다. 이 검사는 모델 추론이나 새 성능 측정이 아니다.
