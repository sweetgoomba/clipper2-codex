# 안무 하이라이트: 추가 몸 추적 비활성화와 실제 앱 비교

2026-11-02 · 원본 저장소 · `fix/dance-gpu-performance-20261102` · macOS arm64 local-API 앱

실패가 확정된 검증의 조기 종료와 검증 대상 없는 후보 제외를 먼저 적용했다. 세 영상의 406개 클립 전체 행, 인물 카드, 9,266개 판정 프레임, 썸네일 바이트가 기존과 일치했다. 그러나 추가 SAM 몸 추적이 세 영상 모두 1분을 넘어서, 사용자의 조건부 지시에 따라 두 실행 경로를 주석 처리했다. 최종 비활성화 버전에서는 추가 SAM 검증이 0초이며, 그 대신 일부 이름 복원과 구간 연결이 사라졌다. **최종 결과가 기존과 동일하거나 품질 저하가 전혀 없다고 주장하지 않는다.**

## 실제 실행 시간

| 영상 | 직전 GPU 적용 앱 | 안전한 검증 단축 | 추가 SAM 비활성화 | 직전 대비 단축 |
|---|---:|---:|---:|---:|
| Made My Night | 12분 00초 | 12분 01초 | 10분 03초 | 16.2% |
| ANTIFRAGILE | 18분 25초 | 19분 15초 | 13분 55초 | 24.5% |
| NEON | 37분 19초 | 35분 34초 | 15분 08초 | 59.5% |

합계 67분 44초 → 39분 05초, 42.3% 단축.

기준은 10월 29일의 오래된 CPU 실행이 아니라, 직전 11월 2일 GPU 적용 앱 실행이다. 앱 작업의 실제 시작부터 프로젝트 완료까지이며 대기열 시간은 제외했다. 동일 Mac에서 버전별 각 1회 순차 측정한 값으로, 통계적 반복 벤치마크나 Windows 실측은 아니다.

## 추가 몸 추적 시간

| 영상 | 조기 종료 적용 후 SAM | 최종 SAM 복원 | 최종 SAM 이름 재검증 |
|---|---:|---:|---:|
| Made My Night | 1분 18초 | 0초 | 0초 |
| ANTIFRAGILE | 3분 54초 | 0초 | 0초 |
| NEON | 19분 23초 | 0초 | 0초 |

`recover_mask_names`와 `revalidate_named_segments`의 import/호출을 주석 처리했다. 후자는 확정 이름뿐 아니라 미확인 구간에도 SAM을 실행할 수 있어 함께 비활성화했다. 함수 구현과 독립 검증 테스트는 남겼다. 메인 선택을 위한 YOLO와 일반 얼굴 검증, 가벼운 얼굴 공백 연결은 계속 실행한다. 진단에는 `disabled_runtime_cost`와 0초를 기록하며, 세 실행 모두 SAM 모델 초기화 및 후보 시도가 없다.

## 결과 변화

| 영상 | 미확인 클립 길이 합계 | 전체 클립 수 | 1초 미만 클립 수 |
|---|---:|---:|---:|
| Made My Night | 4.35 → 6.81초 | 83 → 89 | 38 → 42 |
| ANTIFRAGILE | 8.18 → 16.02초 | 123 → 134 | 73 → 79 |
| NEON | 12.25 → 16.99초 | 200 → 208 | 119 → 126 |

미확인 복원이 사라지면서 일부 연속 멤버 구간 사이에 미확인 조각이 남는다. 클립 수 증가는 이 분할의 영향도 포함한다. 미확인 길이는 저장된 미확인 메인 클립의 길이 합계다. 원본 시각별 분류 변화는 별도로 비교했다.

| 영상 | 원본 시간축의 메인 분류가 달라진 시간 |
|---|---:|
| Made My Night | 2.453초 |
| ANTIFRAGILE | 8.142초 |
| NEON | 4.738초 |

기존 사용자 피드백 14개 검토 구간 중 4개에서 구간 내부 분류가 달라졌다.
이 비교는 기존 출력과의 차이를 확인한 것이며, 나머지 영상 전체에 정답 검수가 끝났다는 의미는 아니다.

| 영상 | 검토 구간 | 분류가 달라진 길이 | 사용자 피드백 |
|---|---|---:|---|
| Made My Night | 34.730–35.440초 | 0.105초 | 사쿠라 또는 단체 |
| Made My Night | 37.738–39.339초 | 1.134초 | 사쿠라 |
| ANTIFRAGILE | 4.571–6.139초 | 1.568초 | 홍은채 |
| ANTIFRAGILE | 9.400–10.277초 | 0.367초 | 김채원 |

미확인 증가 외에, 기존 SAM 교정이 빠져 다른 이름으로 남는 변화도 있다:

- ANTIFRAGILE 117.317–117.618초: 사쿠라 → 홍은채

모든 변경 구간·기존/신규 클립 행은 비교 JSON에 보존했다. 이전 프로젝트와 중간 최적화 프로젝트도 그대로 남겼다.

## 유지한 처리와 남은 비용

| 영상 | 메인 판정 | 얼굴 특징 추출 | 보조 얼굴 검증 |
|---|---:|---:|---:|
| Made My Night | 3분 49초 | 1분 28초 | 1분 21초 |
| ANTIFRAGILE | 5분 37초 | 2분 30초 | 1분 42초 |
| NEON | 5분 47초 | 2분 21초 | 1분 26초 |

추가 몸 추적 병목은 제거했지만 전체 분석에는 여전히 위 단계들의 시간이 필요하다. 다음 과제는 메인 판정과 얼굴 처리의 세부 비용을 분해해 줄일 작업을 찾고, 이번에 잃은 이름 근거를 비싼 SAM 재도입이나 영상별 하드코딩 없이 복원하는 것이다. context 얼굴 수집은 같은 함수에서 장면 경계·카메라 근거도 제공하므로 이번에 통째로 제거하지 않았다.

## 검증 및 격리

- 기존 세 YouTube URL을 실제 앱 UI에서 제출했다. 로컬 파일 입력을 쓰지 않았다. 정상 앱 경로의 기존 다운로드 캐시를 재사용해 새 네트워크 다운로드 시간은 비교하지 않았다.
- 세 영상 모두 저장된 아티스트/대표 이미지 선택·이미지 바이트, 원본 영상·모델·설정 해시가 기준과 같다.
- 안무/인물 관련 1,162개 테스트 통과. SAM 비활성화로 바뀐 동작을 전제하는 기존 통합 테스트 4개도 수정해, 얼굴 인식과 메인 교대 구간 유지 및 SAM 미생성을 확인했다.
- 독립 코드 검토에서 뒤쪽 이름 재검증도 SAM을 호출한다는 점을 확인하여 함께 비활성화하고 회귀 테스트로 검증했다.
- 인물 하이라이트, 공유 얼굴 코어, 공유 SDK의 제품 소스는 변경하지 않았다. 기존 안무 GPU 설정을 유지했다. Windows에도 같은 비활성화 코드가 적용되며 실제 Windows GPU 성능은 미검증이다.
- 원본 저장소에서 `npm run build:app:mac:arm64:local-api`로 빌드했다(Node 24.19.0). 벤치마크 앱의 안무 Python 파일 51개가 당시 소스와 일치한다.
- 측정 후 상태 조회 응답에만 `body_tracking.enabled=false`와 비활성화 사유를 추가했다. 관련 상태/가속 테스트 9개 통과. 최종 앱은 이 상태 표시 수정까지 다시 빌드한 버전이며, 분석 파이프라인과 나머지 안무 Python 파일 50개는 측정 버전과 동일하다. 이 상태 표시만의 변경으로 세 영상을 다시 측정하지는 않았다.
- 전체 저장소의 모든 테스트를 통과했다고 주장하지 않는다. 이번 검증은 변경과 관련된 안무/인물 범위다.
- 커밋·푸시·dev 병합은 하지 않았다.

## 사용한 YouTube URL

- Made My Night: https://youtu.be/BZDZBUyaJbA
- ANTIFRAGILE: https://youtu.be/p_XdZdg9oGc
- NEON: https://youtu.be/93j1fDGi_-8

## 측정 프로젝트

| 영상 | 기준 | 검증 단축 | SAM 비활성화 | 최종 분석 완료(한국 시각) |
|---|---|---|---|---|
| Made My Night | 1793558808114 | 1793567629022 | 1793571868350 | 11-02 07:34:31 |
| ANTIFRAGILE | 1793558865224 | 1793567681642 | 1793571915955 | 11-02 07:48:26 |
| NEON | 1793558916550 | 1793567756677 | 1793571975392 | 11-02 08:03:34 |

앱: `/Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app`

## 증거

큰 원본 진단 파일은 앱 프로젝트와 측정 디렉터리에 보존했다. 아래 비교 자료는 [원본 경로·발행 사본 SHA-256 목록](02-mask-cost-app-evidence/publication-manifest.json)으로 연결한다.

- [진행 계획·결정 이력](02-mask-cost-reduction-plan.md)
- [검증 단축 버전 비교](02-mask-cost-app-evidence/optimized/run-comparison.json)
- [SAM 비활성화 비교](02-mask-cost-app-evidence/disabled/run-comparison.json)
- [원본 시각별 분류 변화](02-mask-cost-app-evidence/disabled/identity-coverage-comparison.json)
- [사용자 검토 구간 변화](02-mask-cost-app-evidence/disabled/reviewed-case-analysis.json)
- [SAM 실행 여부·입력 해시](02-mask-cost-app-evidence/disabled/runtime-comparison.json)
- [관련 테스트](02-mask-cost-app-evidence/disabled-dance-person-regressions.log)
- [벤치마크 앱 빌드 로그](02-mask-cost-app-evidence/build-disabled.log)
- [최종 앱 빌드 로그](02-mask-cost-app-evidence/build-final.log), [상태 표시 수정 범위](02-mask-cost-app-evidence/runtime-status-only.diff)
- [최종 앱 소스 해시](02-mask-cost-app-evidence/final-source-hashes.json), [실제 상태 조회](02-mask-cost-app-evidence/final-runtime-accelerators.json)
- [직전 GPU 개선 결과](02-gpu-performance-results.md)
