# Highlights — Person And Shared Face Matching

인물 하이라이트와 여러 플러그인이 공유하는 얼굴 매칭 문서의 진입점이다. 무대의 메인 선택·구간 정책은 [무대 하이라이트 색인](../dance-highlight/README.md)과 해당 작업 기록을 따른다.

## 현재 상태를 읽는 순서

- [W14 작업 카드](../../handoff/tasks/person-highlight.md)
- [10/23 인물·공통 얼굴 모델 체크포인트](records/2026/10/23-person-highlight-checkpoint-and-shared-face-model.md)
- [10/23 dev 병합·후속 담당 인계](records/2026/10/23-person-highlight-dev-merge-and-stage-usability-handoff.md)

검증 수치와 보류 판단은 각 기록의 날짜·입력 범위에 한정한다. 과거 SFace 기준이나 Person 보류 지시를 최신 제품 정책으로 적용하지 않는다.

## 인물 하이라이트 설계 이력

- [10/1 초기 MVP 제품 계약](records/2026/10/2026-10-01-person-highlight-mvp-design.md): 결과 편집·다운로드·공통 API의 초기 설계.
- [10/19 연속 등장·얼굴/몸 근거 설계](../../design/2026-10-19-person-highlight-continuity-design.md): 초기 face-only 분석·구간 생성 가정을 갱신.
- [10/20 후속 구현 계획](../../implementation/2026-10-20-person-highlight-implementation-plan.md)

## 공통 참조 매칭·모델 비교 이력

- [10/13 공통 참조 매칭 설계](records/2026/10/2026-10-13-shared-reference-face-matching-design.md)
- [10/13 상세 구현 계획](records/2026/10/2026-10-13-shared-reference-face-matching.md)
- [10/13 실제 구현·검증·품질 한계](records/2026/10/13-w14-shared-reference-matching-implementation.md)
- [10/14 인식 후보 비교시험 설계](records/2026/10/14-w14-recognition-candidate-evaluation-design.md)
- [10/14 격리 비교 실행 계획](records/2026/10/2026-10-14-isolated-face-candidate-comparison.md)
- [10/14 실제 CPU 실행·얼굴 정답 확인 자료](records/2026/10/14-w14-candidate-runtime-and-face-review.md)

## 문서 이관과 보존 사본

[2026-10-26 이동 대응표](../../records/2026/10/26-root-docs-relocation.md)에 루트 `docs/`의 옛 위치와 현재 정본을 연결했다. `evidence/`의 봉인 사본·manifest·실험 원장은 당시 경로와 hash를 보존하므로 현재 정본과 구분한다.
