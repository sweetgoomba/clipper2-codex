# Dance Highlight

Dance Highlight는 artist/member detection, member image selection, reference image selection, pipeline execution을 포함한다.

## Current Notes

- [2026-11-04 Mac 얼굴 추가 가속과 dev 앱](../../operations/accelerators/records/2026/11/04-mac-remaining-models-speed-results.md): Python 17259bc·Electron 849a51b, Made My Night 334.958초 → 266.034초(20.58%), 63개 목록·설정·집계 동일, CPU 재분석 0회. AuraFace CoreML·원본 크기 YuNet FP32 CoreML·단계별 MPS/YuNet 해제를 적용했다. SFace와 일부 ROI는 CPU다. Python 2,073개·Electron 1,977개 통과, local-api Mac 빌드·설치 환경·기동 확인. [현재 모델과 사용법](../../operations/accelerators/README.md). 아래 MPS 재검증/얼굴 CPU는 이 개선 전 기록이다.

- [2026-11-04 MPS 시작 실패 수정·원본 dev 앱3영상 재검증](records/2026/11/04-mps-revalidation-results.md): 담당 세션이 메모리 자원 검사 거절을 재현·수정해 dev 반영. 원본 앱 새 빌드/세 URL 완료, YOLO MPS10,241회·CPU 재분석0. 합계53:29.4→49:12.5(관측8.0% 감소). 얼굴은CPU이고 메인·얼굴 병목 잔존. 출력1초미만187개 동일·미확인32.969→36.323초·ANT0.367초 김채원→미확인 회귀 기록. SAM OFF·인물 판정 코드 보존. 최신 사용자 속도 우선 지시에 따라 큰 병목/8개 원본/Windows 빌드는 기존 GPU 담당 세션에서 계속한다.

- [2026-11-04 공통 가속 dev 위 품질 선별 병합·새 앱3영상](records/2026/11/04-quality-dev-merge-and-app-results.md): Python `9a9a940`·Angular `4150871c` 원격dev 반영. 공통GPU/Person/Dialog/SDK 무변경, 고비용 SAM OFF, 지도 복구. 원본4저장소dev 기본 앱 빌드·세 URL 완료(12:10/20:05/21:15,합계53:29). 코드 누락이 아닌 세 실행 모두 MPS시작실패→CPU. 두 사용자 사례 교정 유지,전체1초미만187개/멤버59개/미확인32.969초로 전체 품질·속도 미해결. 직전품질앱23:05와 가속경로가 달라 인과 속도비교 불가. Dance1364·UI120·공통/Person568검사 및 실행모듈50개씩 일치.

- [2026-11-03 김채원16 메인 초단편 원인 교정·최종 앱3영상](records/2026/11/03-main-eligibility-tail-app-results.md): 단체 줌 크기문턱에서 생긴가짜main을실제컷까지교정,카즈하39홍은채97.80–104.02복원. 다중cut경계회귀·ANT검증suffix0.484초보존,앞0.050초unknown유지. 실제3URL short191→185/unknown36.773→36.323초,시간19:07→23:05(+20.76%). 전체품질/속도미해결·미검증확장별도기록. Dance1372·SAM OFF·Person31불변·지도복구앱열림·미커밋.

- [2026-11-03 Made My Night 사용자 두 사례·판정 지도 복구](records/2026/11/03-mmn-user-feedback-and-map-results.md): 잘못된 전경 경쟁자 제외를 고쳐 홍은채 몸/보조이름 복원, 가짜0.033초 경계를 실제컷으로 교정. 김채원0.184초 잔여 문제는 미해결. Dance1346·화면120 통과, 원본 앱 빌드·지도 복구. 전체 앱3영상 재실행 아님·미커밋.

- [2026-11-03 GPU·ONNX 조사 요약과 담당 세션](../highlights/records/2026/11/03-gpu-onnx-research-and-owner-session.md): 기존 안무 GPU·CPU 비용 개선과 Windows 키트 결과의 의미·한계를 정리했다. 공통 가속 작업은 「하이라이트 GPU·ONNX 전환 및 Windows 시험 도구 감사」 세션에서 진행하며, 공통 기반·CPU 복구 1차 구현 후 대기 중이다. 전체 구현·새 GPU 자동 선택은 미완료. 이 안무 세션은 구간 조립 품질 개선을 별도로 담당한다.

- [2026-11-03 이름·메인 중복 경계 조립 수정](records/2026/11/03-identity-assembly-results.md): 상류 단체/main 판정 동결. 저장된 실제3영상 결과 replay에서 표시 short195→191, unknown36.806633→36.773367초. 중복경계4곳·반대얼굴을무시한부모이름1곳수정,14구간불변. Dance1339통과·독립차단반례2개해소. 전체품질미해결, 앱재빌드/전체재실행아님,미커밋.

- [2026-11-03 샷별 이름·기존 메인 역할 유지 실제 앱 검증](records/2026/11/03-shot-context-quality-results.md): 전체414→409, short230→226, 미확인38.6089→38.1416초. MMN허윤진 연결·ANT김채원0.467333초복원·NEON오아구간의 중복단체제거. 실제앱 5:15/7:12/7:41, 합계18:37→20:08: 속도 개선 없음. SAM OFF·Person/SDK불변·독립반례 수정 및 세 URL 실측. 품질전체 미해결·미커밋.

- [2026-11-03 관측 근거 기반 멤버 구간 개선·실제 앱 검증](records/2026/11/03-member-part-quality-results.md): 전체424→414클립, 1초 미만240→230(이름 있음73→71), 미확인38.9761→38.6089초. 실제 새 이름 복원은ANT0.333667초1곳이며 MMN결과는그대로. 앱4:49/6:30/7:18, 합계19:48→18:37(각1회·관측6.0%, 인과적속도효과로일반화금지). 위험한카메라예외와3개역할근거없는복원안은독립반례로폐기. SAM OFF·Person/shared/SDK무변경, Dance1043통과·독립앱95조건통과. 품질전체미해결, 원본새앱열림·미커밋.

- [2026-11-02 공연 파트 조립 분리·실제 앱 검증](records/2026/11/02-performance-parts-results.md): 얼굴 신원 구간과 최종 클립 조립 분리, 단체 연속성 두 곳 교정. 실제 세 영상 1초 미만 245→240개·미확인 39.577→38.976초. 이름 있는 짧은 클립 73개는 그대로여서 핵심 분절 문제는 미해결. 실행 합계 18:52→19:48(+4.94%, 각 1회), 속도 개선 아님. 첫 실험의 과분할 회귀는 제외. SAM OFF·Person 무변경, Dance 1010 통과, 원본 앱 열림, 미커밋.

- [2026-11-02 Astra 품질 검토 적용·실제 앱 비교](records/2026/11/02-astra-applied-results.md): 이름 경계 0.284초 교정 1곳. 실제 앱 합계20:19→18:52(관측7.2%, 각1회); 1초 미만245개·미확인39.577초 그대로. SAM-off/인물 무변경. 제한 SAM의 과거 성공 비용·취소 구조 검토, 최적 예산 미확정. 관련111개·독립37개 통과, 원본 앱 빌드/세 URL 재실행 완료, 미커밋.

- [2026-11-02 메인·얼굴 내부 병목 실측 개선](records/2026/11/02-deep-profile-results.md): 원본 앱3영상 합계26:38→20:19(23.7%), NEON10:36→8:03. 입력·확정 이름 보존, 작은 원경 단체 복원1건. 짧은 클립·미확인 대부분은 남아 있으며 품질 전체 해결 아님. SAM-off/인물 무변경, 미커밋.

- [2026-11-02 YuNet·SFace 안무 전용 GPU 가속](records/2026/11/02-yunet-sface-gpu-results.md): Mac CoreML, Windows DirectML 경로 구현. 원본 앱3영상 합계27분53초→26분38초(4.5%단축)로 효과는 제한적. 430클립·9266판정프레임·썸네일 모두 동일, SAM-off/인물 무변경. Windows 실측 미검증. 전체 Python2528통과/미수정 렌더링6실패/6생략. 미커밋, 앱 열림.

- [2026-11-02 메인 판정·얼굴 처리 추가 개선](records/2026/11/02-main-face-performance-results.md): SAM-off 유지, 실제 세 영상 합계 39분 05초→27분 53초(28.6% 단축). 메인·얼굴 CPU 병렬/캐시 비용/미사용 context 작업 개선. 기존 확정 분류 보존, NEON 짧은 미확인 0.167초 연결 1건. 품질 복원 효과는 제한적이며 기존 사용자 지적 구간은 남음. 원본 앱 빌드·관련 검사 1,191개·실측 완료, 미커밋.

- [2026-11-02 추가 몸 추적 비용 단축·실제 앱 결과](records/2026/11/02-mask-cost-reduction-results.md): 먼저 결과가 동일한 검증 단축을 적용했으나 SAM이 세 영상 모두 1분을 넘어 두 호출을 주석 처리했다. Mac 실제 앱 합계 67분 44초→39분 05초(42.3% 단축). 미확인·짧은 클립 증가가 있어 품질 동등성은 미달성이다. 최종 앱 실행 및 관련 테스트 검증 완료, Windows 실측은 별도.

- [2026-11-02 GPU 설정·성능 감사](records/2026/11/02-gpu-performance-audit.md): YOLO MPS 사용 확인, AuraFace CoreML 독립 실측(프로파일링 비활성 약 1.63배), SAM2 MPS 품질 차이와 NEON 반복 검증 병목. 제품 설정 변경 전 검증 기록.

- 2026-10-23 Person 기능 브랜치가 데스크톱 4개 원격 dev에 병합됐다. 안무와 인물은 공통 AuraFace/ONNX Runtime 1.31.0을 사용하며, 후속 그룹화·구간 구성은 각 플러그인 정책이다.
- [최신 병합·검증·인계](../highlights/records/2026/10/23-person-highlight-dev-merge-and-stage-usability-handoff.md)와 [W13 작업 카드](../../handoff/tasks/dance-highlight.md)를 먼저 읽는다. 결과 UI 이식과 원본 구간 저장 전환은 [무대 사용성 완료 기록](../highlights/records/2026/10/23-stage-usability-source-ranges-dev-merge.md)과 같이 원격 dev에 반영됐다(Angular `f488e8a4`, Nest `8397afbc`, Python `3fbb002`). 품질 개선은 별도 무대 파이프라인 세션에서 이어간다. 실제 영상·Windows 검증은 별도다.

- member image search는 Python plugin이 아니라 NestJS image search API가 담당한다.
- Naver/Kakao image search key는 NestJS env에 있어야 한다.
- Python env에는 Naver/Kakao key를 두지 않는다.
- member image selection 페이지는 내부 단계 컨테이너가 스크롤을 소유한다.

## Active References

- [../../design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md](../../design/PLUGIN_RUNTIME_ISOLATION_AND_DANCE_FACE_MODEL_2026-07-01.md)
- [../../operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md](../../operations/env-runtime/records/2026/05/21-windows-dance-image-env-management-context.md)
- [../template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md](../template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md)
