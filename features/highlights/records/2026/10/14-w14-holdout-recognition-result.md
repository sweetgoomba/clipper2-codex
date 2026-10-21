# W14 — 사용자 새 영상 정답 수신 및 세 모델 비교

2026-10-14 KST. [비교 화면](http://127.0.0.1:58261/holdout-results-v1/index.html). 기존 YuNet 검출 결과와 모델별 정상 정렬/전처리, 기존 참조 23개를 고정한 **선택 얼굴 단위** 비교다. 최종 안무 메인/구간 분류 시험은 아니다.

## 사용자 정답과 고정 조건

- `/Users/jina/Downloads/clipper-holdout-face-labels.json` 원본 SHA256 `ea75e27a332057a5003b80341d683049cbbb6d9b3f60556f560859f9768db0be`.
- origin `user_review`, 문서 경로 `/holdout-review-v1/index.html`, 기존 관측 manifest SHA와 15개 ID/source hash/frame index/PTS/time base/face row/bbox/crop 일치를 검증했다. QA export는 읽어 들이지 않았다. 원문 바이트는 별도 복사해 보존했다.
- 15개 완료: 멤버 7개(해린 3/민지 3/다니엘 1), 등록 외 인물 2개, 판단 어려움 5개, 얼굴 아님 1개. 멤버 7개는 모두 사용자가 사진만으로 식별 가능이라고 입력했다. **하니·혜인 정답은 0개**다.
- 명확하지 않은 5개에 임의 정답을 붙이지 않았다. 손/가슴 검출은 사용자도 얼굴 아님으로 확인했다. 이 정답들을 파이프라인 gate로 쓰지 않고 **15개 전부 세 모델에 동일하게 입력**했다.
- source/검출/bbox/5점/참조 gallery/centroid 결합 방식은 고정했다. 모델별 임베딩 공간, 정렬, 전처리는 분리했다. 원본1920×1080 프레임으로 정렬하며 사용자 화면용 crop을 모델 입력으로 쓰지 않았다.

## 새 결과 전에 고정한 시험 기준

기존 `gallery-diagnosis-v1/result.json`의 centroid 개발자료 wrong_budget0 지점을 복사했다. 이 지점은 기존 사용자 멤버 정답128개에서 얻은 개발자료 내 결과이며 신규 두 영상으로 보정하지 않았다. 기존 Aura/Intel의 정렬 오류1개는 별도로 보존한다.

| 모델 | cosine distance 상한 | 1·2위 거리 차이 하한 |
|---|---:|---:|
| SFace | 0.7239670157432556 | 0.13533276319503784 |
| AuraFace | 0.6163947582244873 | 0.04980224370956421 |
| Intel0095 | 0.5232793688774109 | 0.15660852193832397 |

기준은 **탐색용 시험 기준**이다. 개발자료에 등록 외 인물 정답이 없었고 인접 얼굴 표본도 포함돼 있어 제품 threshold나 낮은 FAR 보장이 아니다. 새 영상 결과를 보고 기준을 조정하지 않았다. 점수 1위와 실제 이름 배정/보류를 화면에서 분리했다.

## 실제 결과

| 모델 | 멤버7개 점수1위 일치 | 올바른 이름 배정 | 잘못된 이름 배정 | 식별 가능하지만 보류 | 등록 외2개 거부 |
|---|---:|---:|---:|---:|---:|
| SFace | 6/7 | 5 | 0 | 2 | 2/2 |
| AuraFace | 6/7 | 5 | 0 | 2 | 2/2 |
| Intel0095 | 6/7 | 3 | 0 | 4 | 2/2 |

- 세 모델 모두 판단 어려움5개와 얼굴 아님1개에 이름을 배정하지 않았다. 판단 어려움은 정체가 미확정이므로 정답/오답에 넣지 않는다. 얼굴 아님은 검출 오탐이며 인식 정답률과 분리한다.
- [얼굴3](http://127.0.0.1:58261/holdout-results-v1/face-3.html), OMG95.028초 민지·얼굴폭39.5px: SFace 점수1위 민지, Aura 하니, Intel 혜인. 세 모델 모두 보류.
- [얼굴10](http://127.0.0.1:58261/holdout-results-v1/face-10.html), Super Shy95.028초 민지·폭116.0px: SFace 점수1위 해린(거리0.622991, 민지0.634421), Aura/Intel 점수1위 민지. 세 모델 모두 보류. 새 모델은 이 얼굴의 순위를 회복했지만 얼굴3에서 회귀했다.
- 이름을 배정한 SFace/Aura5개는 같은 표본이다. 이번 자료에서 모델 교체로 배정 가능한 얼굴이 늘었다는 증거 없음. Intel은 과도한 보류가 더 많다.
- OMG140.007초는 YuNet 얼굴 검출0인 별도 프레임이다. 세 인식 모델에 입력되지 않았으며 미검출을 인식 오답/거부로 계산하지 않았다.

**판단:** 이번 비교에서 새 모델 단순 교체를 채택하지 않는다. 현재 SFace 기준선도 민지 혼동/거부 문제가 남는다. 새 표본에 혜인이 없으므로 과거 혜인 오류 해결 여부는 미검증이다. 신규 두 영상 전체/안무 파이프라인 품질 향상 판정도 할 수 없다.

## 실제 실행·자원

기존 전용 uv Python3.11.12 환경, Apple M4/macOS27 arm64, CPU1thread/batch1. OpenCV4.13.0 / ORT1.24.4 / OpenVINO2026.4.1. 기존 로컬 모델만 사용하고 OpenVINO는 worker import 전에 CI=true opt-out을 적용했다.

| 모델 | 실제 새 추론 | worker시간 | 로딩 | 첫 추론 | warm p50/p95 | peak RSS |
|---|---:|---:|---:|---:|---:|---:|
| SFace | 15 | 1.280초 | 56.4ms | 26.3ms | 13.2/15.4ms | 489.6MiB |
| AuraFace | 15 | 2.254초 | 169.4ms | 146.0ms | 67.2/72.8ms | 880.6MiB |
| Intel0095 | 15 | 1.445초 | 368.2ms | 8.1ms | 6.3/7.8ms | 371.1MiB |

합계45성공, 정렬/추론 오류0. 새 검출/pose/참조추론/설치/다운로드0. 모델별 최대15회/180초/4GiB, 총산출물100MB의 사전 상한과 외부 `/bin/ps` 250ms 감시를 적용했다. 세 supervisor 모두 exit0, 강제 중단 없음. warm은 첫1개를 제외한14개, native forward+출력정규화만 포함하고 디코드/정렬은 제외한다. 한 번의 소표본 실험이며 Windows 성능이나 앱 전체 자원으로 일반화하지 않는다.

## 검증과 산출물

루트: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014/holdout-comparison-v1`.

- 추론 전 확정 `manifest.json` SHA256 `d8c099e39a41cf193f1cb6777549300cc22e6a41341b3733cb92e01454f0609a`. 원본/모델/참조23/각공간cache/정답/정책/코드/계획/표시crop 등61개 입력hash 보존.
- 사용자 원문 `labels.original.json`, 각 모델 `result.json`, `embeddings.local.npz`, `aligned/`, log/supervisor/start 파일 보존.
- `verification.json`: 61hash, canonical15행, 모델45행, **225개 멤버 거리**를 독립 float64 계산으로 검산했다. 최대차이 `8.958733510588957e-08`, 모든순위/판정/요약 일치. 각45입력의 원본 crop픽셀 일치 확인. SFace 참조23cache는 원래 정규화특징과 일치.
- strict import/QA 거부/provenance 변조/중복/완료/unknown/에러 분리11개를 RED→GREEN으로 구현, candidate 평가 전체39pytest 통과. 기존 Node 얼굴응답 검증 통과.
- 읽기 전용 요약+얼굴1~15 상세 페이지, 총68이미지. 사용자 정답 저장소에는 쓰지 않는다. 긴 페이지 anchor 이동의 screenshot이 공백으로 표시되어 짧은 상세 페이지로 바꾸고 원본crop/context/세모델 정렬·점수·보류를 한 화면에서 확인했다. 브라우저 내부 원인은 미특정. 요약→얼굴10→얼굴11→요약 및 점수 펼치기 확인, 콘솔 warning/error0. `summary-screen.png`, `face10-screen.png`.
- 신선한 독립 리뷰에서 수치·입력/provenance/cache를 별도 검산했다. 최종 결과는 execution-ledger에 기록한다.

## 남은 작업·공통 계약

이 결과로 제품 모델/threshold/공통 core/W13을 바꾸지 않는다. 다음 품질 개선은 이미 확보한 개발용 오류구간에서 얼굴 소유 연결과 같은 인물의 시점별 관측 수집을 검증하고, 최신 W13의 고정 메인/동일인 scope와 결합해 최종 구간의 올바른 배정·오배정·거부를 함께 평가하는 것이다. 같은track 번호만으로 인물 정답을 전파하지 않는다. 새 영상의 결과를 보고 설계를 조정하면 그 부분은 이후 개발자료로 명시해야 한다.

W14 소유: 평가 import/runner/결과화면과 고정 fixture. W13 소유: 메인 댄서/몸추적/구간/crop 및 소비 adapter. W14 공개 계약·fixture → 최신 W13 동일인/실패 상태 compatibility → W13 소비 adapter/venv 검증 → 병합 순서를 유지한다. 최신 W13 통합, 전체영상 정답, Windows/깨끗한 설치환경은 미검증이다. 새 세션/다른 세션 메시지/commit/push/merge 없음.
