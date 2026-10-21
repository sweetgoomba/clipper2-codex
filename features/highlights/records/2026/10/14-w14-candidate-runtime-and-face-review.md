# W14 — AuraFace / Intel0095 실제 CPU 실행과 얼굴 정답 확인 화면

2026-10-14 KST. 사용자는 영상2개·모델2개 확보, 격리 평가 환경/adapter, 입력 잠금 뒤 SFace 대조라는 실행 범위를 제시받고, 정답이 새 영상의 모든 main 구간 재작성 요구인지 질문했다. **실제 선택된 얼굴의 identity 확인이며 main 재작성은 아니라는 설명 후 `그래`**에 따라 이 범위를 실행했다. 제품 통합/모델 채택 승인이 아니다.

## 1. 이번 결론

- AuraFace-v1과 face-reidentification-retail-0095는 현재 **Apple M4 CPU에서 실제로 실행**됐다. Windows/최저 지원 macOS/설치형 앱 배포 검증은 아니다.
- 기존 참조23장 + 기존 영상의 선택 얼굴406개를 고정했다. 후보 각각 참조23+얼굴403=426회 성공, 특징점 좌우 순서 오류3개는 추론 전에 정렬 오류로 보존했다. smoke 각1회를 포함한 신규 인식 추론은 총854회. 검출/pose/0009 추론은0회.
- SFace406개 기존 특징 재사용. 전체451관측(406선택/36미검출/9연결 보류)을 그대로 남겼다. 모델 오류를 미매칭으로 바꾸거나, 여러 사람의 track을 평균내지 않았다.
- 같은403얼굴의 점수1위가 SFace와 다른 경우 Aura92/Intel119개다. **바뀐 수는 개선된 수가 아니다.** 후보별 영상 threshold를 아직 정하지 않았고, 새 구간 최종 분류도 만들지 않았다.
- 영상 얼굴의 독립 정답이 없어 영상 정확도는 계산하지 않았다. 먼저19개 클립의 시간순 중앙 얼굴을 확인하는 화면을 준비했다. 클립20에는 선택 얼굴이 없어 최초 확인 목록에서 빠지지만 전체 목록의27관측은 보존된다.

## 2. 파일·환경·격리

작업: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/desktop/clipper_python`, HEAD `47782953228861f4bdbdc135265d067c2a826b0e`, 기존 feature branch. 새 코드 범위 `evaluation/candidate_comparison/`만. 기존 core/SDK/plugin/W13/pyproject/uv.lock/기존 venv·v1~v5 변경 없음. 커밋·push·병합·새 작업 세션 없음.

실행 산출물 루트: `/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/candidate-comparison-20261014`.

장비: Apple M4, RAM24GiB, macOS27.0 arm64, Python3.11.12. 새 전용 uv venv에 NumPy2.4.4/OpenCV4.13.0.92/ORT1.24.4/OpenVINO2026.4.1/ONNX1.20.1/pytest8.4.2 설치. `uv pip check`28패키지 호환 확인. 설치환경/라이선스·WHEEL75파일은 `metadata/runtime-licenses/`와 inventory에 보존했다. 모델+원본 약491MB, venv+cache 약942MB, 보고서 약99MB로 설정한4GiB/4GiB/2GiB 이내다.

실행 manifest: `input-manifest-v2.json`, SHA256 `b1de9b06450b4da3839d9f6def94d88dd2ca651eca66eb60f672968bf3d1a9c2`. 각 원본/참조/캐시/모델/실행 Python 코드의 hash와474슬롯, 최대 호출 수, CPU1/batch1/worker600초·4GiB를 추론 전에 고정했다. v1 manifest는 최초 Aura smoke의 근거로 별도 보존했다.

### 정확한 가중치

| 모델 파일 | 실제 SHA256 | 출처/권리 근거 |
| --- | --- | --- |
| Aura `glintr100.onnx` | `a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60` | fal/AuraFace-v1 revision `af6d057c9b0ec4071d4c49c80e3539258798b609`, 같은 revision의 README/LICENSE.md Apache2 보존 |
| 0095 FP32 XML | `6cf60c341452155e35c467510c6c50a96ade5b2bd8f88c5a90902e905d8a80c3` | 공식2023.0/models_bin/1 경로, OMZ manifest SHA384 일치 |
| 0095 FP32 BIN | `21319b95e54181857f99e22dc32ec89770eca2969a1432cfa1594bffc94edd62` | 동일, manifest가 파일 URL·checksum과 Apache2를 연결 |

OMZ 문서/manifest/LICENSE revision `464159ff32fbd2469b9ebf4e388eb0ebb63db9ee`. `metadata/file-inspection.json`에 파일크기·SHA256/SHA384·graph검사 보존. Aura 부속 검출/나이/성별 pack, InsightFace package,0009 모델은 받지 않았다.

공식 근거: [Aura 카드](https://huggingface.co/fal/AuraFace-v1/tree/af6d057c9b0ec4071d4c49c80e3539258798b609), [0095 manifest](https://github.com/openvinotoolkit/open_model_zoo/blob/464159ff32fbd2469b9ebf4e388eb0ebb63db9ee/models/intel/face-reidentification-retail-0095/model.yml). 제공자의 공개 성능/학습 데이터 설명은 Clipper 검증 결과가 아니다. 런타임 제3자 라이선스와 실제 앱 패키징 의무는 별도이며 제품 배포 승인을 선언하지 않는다.

## 3. 실제 입력 경로와 전처리

- 이전 영상 `yFTAYXDTjqI`,1920×1012,133.654059초, 원본 SHA `7f23b9ad8dd6873d8c39a8369083626de5e1807468d083247f0545c3299688d4` 재검산. 원본 frame index로 디코딩→저장ROI→선택 YuNet15값(5점 포함). 예전 미리보기 JPEG는 **표시에만 사용**, 신규 모델 입력에는 사용하지 않았다.
- 참조23사진은 원본 hash·크기와 이전에 선택한 얼굴 index/5점을 대조했다. 모델별 참조 특징을 다시 만들고 모델 hash/정렬/정규화/정밀도/거리별 공간을 분리했다.
- Aura: ONNX checker 통과, opset11, float32 NCHW112 RGB, input이 Conv로 직접 들어가 내부 입력 정규화 없음. 외부 `(RGB-127.5)/127.5`1회,512차원 출력 L2. YuNet5점→ArcFace112 template similarity/linear warp.
- 0095: FP32 IR128 BGR, input 뒤 Multiply/Add가 있는 실제 BIN상수 확인. **외부 정규화 없음**. 문서의 normalized5점 template, native tight crop→OMZ 방식 inverse nearest warp→128 linear resize,256차원 출력 L2.
- 0095 모델 README의 template과 demo의 상수에는 작은 숫자 차이가 있다. 이번은 **모델 README template**을 채택했다. 두 후보는 필수 정렬이 다른 `모델+정렬` 비교이며 동일 정렬 픽셀을 강제하지 않는다. Intel0009로 5점을 바꾸는 대조는 미실행.
- 역전된 YuNet5점3개: `face-109`, `extra-segment-10-13-3760`, `face-202`. 양 후보 모두 `alignment_invalid/reversed_landmarks`로 남았다. 기존 SFace 캐시는 이3개에도 값이 있으므로 전체406 vs403을 구분한다.

## 4. 실제 실행·한계

| 항목 | AuraFace ORT CPU | 0095 OpenVINO CPU FP32 |
| --- | --- | --- |
| smoke | 1회 성공 | 1회 성공 |
| 본 실행 | 426회 성공 | 426회 성공 |
| 본 실행 전체 | 72.029초 | 38.226초 |
| forward+L2 warm p50 / p95 | 74.51 / 92.65ms | 6.76 / 9.45ms |
| native 첫 forward | 141.49ms | 8.56ms |
| 본 실행 load | 0.077초 | 0.197초 |
| 최초 smoke load | 0.639초 | 5.289초 |
| 본 실행 peak RSS | 2.213GiB | 0.304GiB |

양 후보는 순차 실행했다. 같은 시간에 새 영상 preview 디코딩이 있어 **장비 경합 없는 정밀 속도 순위 시험은 아니다**. 본 실행 load는 이미 smoke를 거친 OS cache 영향이 있다. 위 p50/p95는 한 번씩 처리한 서로 다른 이미지의 분포이며 전처리/seek 제외다. 원본 decode·정렬 포함 관측별 시간도 원시 결과에 저장했다. 모델 파일 크기를 메모리라고 보고하지 않는다.

운영상 발견/처리:

1. 기존 yt-dlp2026.6.9가HTTP403. 격리 venv의2026.8.19로 같은format137 확보 완료. 로그인/쿠키 접근 없음, 제품 downloader 미수정.
2. 최초 Aura smoke에서 외부 RSS 감시의 `ps`가 sandbox 권한으로 실패했다. native1회는0.796초/653MB로 완료됐다. 최초의 외부감시 성공을 주장하지 않는다. 감시 권한을 **worker 생성 전** 확인하게 수정해 권한 실패 시 worker0임을 재현했고, 이후 실제 full은 외부250ms poll/600초·4GiB kill 감시를 적용했다.
3. OpenVINO2026.4.1의 일반 import도 converter를 eager import해 telemetry 모듈을 초기화한다. 첫 Intel smoke는 import event 전송 시도가 가능한 기본 경로였으며 전송 성패는 확인되지 않았다. 얼굴/사진을 보내는 코드 경로는 사용하지 않았다. 이후 **공식 `CI=true` 경로의 consent=False**를 별도 확인하고 본 실행에 적용했다. 사용자 전역 opt-out 파일이나 HOME을 변경하지 않았다. 제품 adapter에서는 이 startup 동작을 반드시 제어해야 한다.

wheel 확인상 ORT는 `macosx_14_0_arm64`, OpenVINO는 `macosx_11_0_arm64`. 이는 wheel tag 근거이며 앱 최소지원OS 확정이나 Windows 실행 증거가 아니다.

## 5. 새 두 영상 입력 준비

| 원본 | 실제 크기/길이 | SHA256 |
| --- | --- | --- |
| `J9DlrnNlgfE.mp4` |105,656,414bytes /215.248367초 | `fa434d6d1d62c19fd75f606b70fd158a943fcbdfd1fe91778ef784e4ca149cc0` |
| `6bVUjsUi9sw.mp4` |120,120,200bytes /231.064167초 | `0e778c49ecb3325e1fe507d7179f5e5b638686896fbd5c3bc07fd03027f63f63` |

둘 다format137,1920×1080,H264,30000/1001,video-only. 내려받은 스트림 정보이며 원본 촬영 master의 최대 해상도라는 뜻이 아니다. source file을 모델 간 바꾸지 않는다.

각 `[30,60)`, `[80,110)`, `[125,155)`, `[165,195)`초 고정, 합계240초. 정수초 이상인 첫 실제 source PTS를 선택한240프레임의 preview를 정상 디코딩했다. 최대 requested→actual 지연0.033267초, PTS/timebase/frame index/source hash는 `holdout-frames.json`. preview960px는 보기용이며 모델 입력은 원본을 쓴다. 새 영상의 **인식/검출/pose 추론0**, main 출력·독립 얼굴 정답·참조 사진 촬영 중복 검토는 남았다.

## 6. 결과 화면과 정답 입력

[사용자 화면](http://127.0.0.1:58261/candidates-v1/index.html). 원본 영상과 저장된 메인 몸/선택 얼굴, 클립별 관측, 세 모델 점수, 멤버별 관련 클립을 확인할 수 있다. 처음은 점수 숨김, 클립별 시간순 중앙19얼굴(모델 점수 비참조). 얼굴이 없는 클립20도 전체451관측에서 볼 수 있다. **새 두 영상의 구간별 main 정답을 전부 작성해 달라는 요청이 아니다.**

라벨: 해당 얼굴의 멤버/등록 외/판단 어려움, 이미지 자체 식별 가능 여부. 판단이 어려우면 임의로 멤버 이름을 고르지 않는다. 다른시점·같은track로 라벨을 자동 복사하지 않는다. UI의 한국어 `identity`와 `identifiable`은 raw 사용자 응답이며 후속 수입 시 reference ID/outside-gallery/unresolved와 정답 version/reviewer로 명시적으로 매핑한다. 기존 `gt:null`은 원래 미확인 snapshot이고 사용자가 입력한 정답으로 덮어쓴 평가 결과가 아니다.

확인 내용은 manifest+페이지별 localStorage로 저장, JSON 내보내기 가능. 모델을 본 뒤 숨기거나 라벨을 지우고 다시 입력해도 `prediction_seen_ever`를 지우지 않는다. 점수 숨김/노출 당시 상태도 구분해 기록한다. 노출 이력은 보수적으로 페이지 전체에 적용한다. 이19개는 시작점일 뿐 전체406개 얼굴/전체영상 정확도 분모로 확대하지 않는다.

QA는 별도 `qa.html` 저장공간에서만 수행했다. 임시 `판단 어려움`1건은 기능시험값이며 실제 GT가 아니다. 내보내기 JSON을 검사한 뒤 Downloads의 시험파일을 평가 metadata로 이동하고 QA 라벨을 복원했다. 사용자 index.html은0/19에서 시작한다.

## 7. 실제 검증과 미검증

- 전처리/공간/정렬/실패분모/표본선정16pytest 통과. 기존 segment/core와 함께116통과. 기존617/651회귀 숫자를 이번 모델 검증으로 재사용하지 않는다. 제품 전체 부팅/패키징 테스트는 미실행.
- 노출이력 결함을 독립 리뷰가 지적: 처음에는 현재 표시상태만 기록했다. 노출 이력 보존으로 수정, Node5검증 RED→GREEN. 실제 브라우저에서 점수보기→숨기기→임시라벨→reload→내보내기 후 `prediction_seen_ever=true`, 현재표시false 확인했다.
- 독립 리뷰는 전체 manifest hash,426×2특징,451관측,6,060거리 재계산 일치(maxdelta0)를 확인했다. 작성자의 별도 scalar합산은 최대차1.14e-7. 다른사람을 track으로 합치는 집계/구간확정 없음.
- 참조사진 leave-one-out: SFace23/23, Aura22/23,0095 23/23. **참조사진끼리의 검사이고 영상 정확도가 아니다.**
- 후보 품질 우열, 영상 threshold, 잘못된 멤버 확정/과도한 거부 개선, 독립 holdout 성능, 최신 W13 통합, Windows/코드서명/클린설치/최저OS는 미검증.

## 8. W13 인계와 다음 단계

W14는 계속 공통 얼굴 API·선택 인식adapter·gallery/거리/실패/공간 계약을 소유한다. 이번 adapter는 evaluation-only이며 공통 패키지 공개 backend로 아직 승격하지 않았다. W13의main/몸/구간/crop 책임은 그대로다. 새 두 영상에 고정된W13 출력이 없어 main→얼굴→멤버 전체평가를 수행했다고 주장하지 않는다.

순서: 사용자 실제 선택 얼굴 라벨 수신 → 기존개발자료의 모델별 오류/거부 trade-off·threshold 고정 → 새영상에서 같은 관측과 독립GT 확보 후 비교 → W14 공개관측/인식API·manifest/선택의존성 확정 → W13 adapter compatibility/실기 → 병합. 현재 모델 우승자·전체영상 재라벨링·제품통합 승인을 사용자에게 요구하지 않는다.

핵심 판단: 같은track 이름 GT를 자동복사하지 않음(확인량 증가를 감수); 0095는 문서정렬을 따라 모델+정렬로 평가(정렬효과 분리에는0009 등 별도대조 필요); 단일장비 실행은 배포보장으로 확대하지 않음(Windows 후속검증 필요). 초기감시/telemetry 문제와 해결범위를 위에 기록하고 성공만 남기지 않았다.
