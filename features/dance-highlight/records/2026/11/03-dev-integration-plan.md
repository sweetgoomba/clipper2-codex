# 최신 dev 공통 가속 유지 및 안무 품질 이식 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Tasks use checkbox syntax.

**Goal:** 공통 가속·인물 처리를 최신 dev와 동일하게 유지하고 검증된 안무 품질 개선을 통합한 실제 앱을 세 YouTube 영상으로 비교한다.
**Architecture:** 원본 미커밋 소스와 Git stash를 보존한다. 원본 desktop 4개 저장소에서 동일 통합 브랜치를 최신 origin/dev에서 만들고, 비교 기준은 dev에 SAM/mask/joint 비활성화만 적용한다. 후보는 안무 내부 품질·캐시 개선만 이식하고 기존 공통 가속의 CPU 기준·승인·전체 작업 복구를 사용한다.
**Tech Stack:** Python 3.11/uv, Angular, NestJS, Electron/macOS arm64.
**Spec:** 이번 사용자 지시 및 03-main-eligibility-tail-app-results.md, operations/accelerators의 03-highlight-acceleration-scoped-dev-merge.md.

## Global Constraints
- 무거운 SAM/mask/joint 몸 추적 OFF. 구현 코드는 보존한다.
- Person·Dialog·공유 SDK·clipper_accelerators 소스는 최신 dev와 동일하게 유지한다.
- 임의 3초 제한·짧은 클립 삭제·이름 강제 병합 금지.
- 원본 분석 결과·개발자 교정·개인 환경 보존. 신규 프로젝트로만 분석한다.
- 명시적 push 요청 전 원격 dev는 변경하지 않는다.
- 원본 저장소에서 npm run build:app:mac:arm64:local-api 실행.

## Review Focus
- CPU 기준 검증에 legacy GPU가 개입하지 않아야 한다.
- GPU 오류가 기존 전체 작업 CPU 복구를 우회하지 않아야 한다.
- 컷·확실한 이름 교대·단체 경계를 같은 이름이라고 무조건 합치지 않아야 한다.
- 단체·미확인 전환의 개선을 중복 출력 제외 효과와 분리해 집계해야 한다.
- 신규 이름 확장을 정답 미확인 상태로 정확도 개선이라고 주장하지 않아야 한다.

## Tasks
- [ ] 1. 원본 112파일 해시·stash 보존, desktop 4개 최신 dev 기준 통합 브랜치 준비. 후보 이식 전 dev+SAM OFF 비교 앱 빌드와 세 영상 실행. SAM OFF 회귀 테스트를 먼저 수정해 RED 확인 후 최소 변경한다.
- [ ] 2. 안무 품질·캐시 코드를 이식하고 app/face_cluster/cut_face_link/sampled_face_link 충돌 해결. 최신 공통 route_detector/route_recognizer와 cpu_only 계약 유지; legacy face_runtime/opencv_acceleration 자동 실행은 이식하지 않는다. CPU 기준·가속 경로 계약 테스트 RED→GREEN.
- [ ] 3. 검증되지 않은 단체 전환·이름 확장을 독립 검토해 반영 범위 결정. 안무 전체·공통 가속·Person 회귀, uv lock 검사. Angular 판정 지도 재활성화만 이식. Nest의 중복 free 호환 변경은 제외.
- [ ] 4. 통합 앱 빌드·패키지 소스 해시 검증 후 같은 URL·설정·대표 이미지로 세 영상 실행. 동시 ML 부하를 기록하고 큐 대기 제외 시간·원시/출력 초단편·미확인·사용자 지적 구간을 비교한다.
- [ ] 5. 전체 차이의 독립 코드 검토와 실제 산출물 검증. 결과·한계·원격 기준 SHA·보존 위치·후속 과제를 .codex에 기록한다.

## Ledger
- Pre-flight: face_cluster 생성자 cpu_only와 공통 detector/recognizer route를 품질 캐시 wrapper가 보존해야 함. 새 GPU 계층을 추가하지 않는 것으로 결정.
- Ruling: 사용자 기존 원본 저장소 빌드 지시를 유지해 새 작업 트리를 만들지 않는다. 원본 소스를 사본+stash로 보존하고 별도 브랜치에서 진행한다.
- Ruling: 사용자 몸 추적 OFF 지시를 비교 기준에도 동일 적용한다. 따라서 기준은 순수 dev가 아닌 dev+SAM OFF이며 보고서에 명시한다.
- 원본 112개 파일은 03-dev-integration-evidence/preserved-source 및 manifest로 보존 완료.

- Task 1: 원본112파일 해시 사본 및3개 stash 보존, desktop4개 fix/dance-quality-dev-integration-20261103 생성. dev SHA는 원격 통합 기록과 동일. 비교 SAM OFF 계약1 RED→5 GREEN, 비교 앱 빌드 성공. 첫 MMN dance_1793715367745는 검증/빌드 부하가 겹칠 수 있어 기능 스모크로만 사용하고 시간 비교에서는 별도 반복한다.
- Task 2: legacy 제공자 선택·세션별 CPU fallback은 이식하지 않음. CachedInferenceSession은 선택된 공통 세션만 감싸며 예외를 그대로 전파. 공통가속/SDK/FaceCore/Person diff 없음. 공통/Person568 PASS, map UI120 PASS. SFace서비스재사용/강제CPU/공통라우팅65 PASS.
- Task 3 Ruling: ensemble은 확대 방향만 허용. 축소/정지 formation은 후보 유지; 원본MMN50/기존보호와 함께18 PASS. 비용은 확대 외 동일단체 가능성을 더 복구하지 않지만 미검증 단체 전환을 피한다.
- Task 3 Ruling: ANT raw negative boundary blanket원복은 MMN50 회귀를 만듦. 인접한 서로 다른 confirmed named runs 사이에 컷2개 이상이 있고 raw 후보가 그 bridge안에 있는 경우만 기존 raw지원범위를 보존. 기존거리/분산/시간은 불변. 해당126 PASS 및 음성veto6 PASS. 틀리면 bridge구간 추가미확인이 남을 수 있으나 이름을 임의확장하지 않는다.
- 독립 가속검토 P1/P2: active main/native pose/incoming, retainedcontext 및 모델생성에서 BackendFailure/Cancelled를 optional fallback이 삼키지 않게 명시적으로 재throw. source-routing변경시 검출cache무효화. 실제whole-unit retry를 포함한10 RED→GREEN, 관련28 PASS. 공통가속소스는수정하지않음.
- 첫 전체 pytest는 잘못된 상대PYTHONPATH 및 소켓 sandbox와 무관한 렌더까지 포함해 중단. 결과를 성공으로 세지 않음. 절대경로+로컬프로세스권한으로 공통/Person568 PASS. Dance초기1343PASS/6FAIL은 테스트fake세션계약2개와 SFace재사용누락4개;65개 집중범위에서 수정확인, 최종전체재실행중.
