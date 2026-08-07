# Shortform Director Veo 무텍스트 영상 생성 — 구현 계획 (Plan)

> 작성일: 2026-08-07 · spec: `architecture/2026-08-07-shortform-director-veo-text-free-generation-design.md` · 대상 레포: `desktop/clipper_nestjs`, `web/clipper_web_api`

## 목표 / 완료 기준 (Definition of Done)

새 Veo 3.1 Lite/Fast 스토리보드가 영상 내부 텍스트를 요구하지 않고, 실제
Veo 컷 생성 프롬프트도 무텍스트 규칙을 포함한다. 다른 모델과 Clipper 합성은
기존 동작을 유지한다.

## 선행조건 · 의존성

- 기존 `aiVideoProduction` 추론 입력
- 기존 `scene-media-decision` 프롬프트 계약
- 기존 컷별 AI 영상 preflight 프롬프트

## 단계

1. Desktop 도메인 테스트에 Veo/비-Veo visual policy 기대값을 추가한다.
2. Desktop 컷 preflight 테스트에 Veo 무텍스트 실행 경계와 비-Veo 비회귀를 추가한다.
3. Web API 프롬프트 계약 테스트에 조건부 무텍스트 지시를 추가한다.
4. 실패 테스트를 확인한 뒤 최소 구현으로 정책 전달과 실행 경계 제약을 추가한다.
5. 관련 테스트와 두 Nest 프로젝트 빌드를 실행한다.

## 위험 · 롤백

정적 시스템 프롬프트의 조건문을 LLM이 잘못 해석할 수 있으므로 공급자 프롬프트에서도
같은 정책을 강제한다. 문제가 생기면 visual policy 필드와 Veo 전용 프롬프트 분기만
되돌릴 수 있다.

## 검증 체크리스트

- [ ] Veo 계획 입력은 `generatedVideoText: false`
- [ ] 비-Veo 계획 입력은 `generatedVideoText: true`
- [ ] Veo 컷 프롬프트는 영상 내부 텍스트를 금지
- [ ] Seedance/Gemini 프롬프트는 기존 정책 유지
- [ ] Web API 프롬프트 버전과 계약 테스트 갱신
- [ ] 관련 테스트 및 빌드 통과
