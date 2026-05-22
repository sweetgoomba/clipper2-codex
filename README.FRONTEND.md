# Frontend Notes

Angular UI 작업 시 우선 확인할 기준이다.

## Current Frontend Baseline

- Angular standalone component를 기본으로 한다.
- signal/computed/effect 기반 상태를 선호한다.
- zoneless 테스트 설정을 유지한다.
- UI 상태는 가능한 feature component 안에서 닫고, shared service는 실제 공유 책임이 있을 때만 만든다.
- loading/error/empty states는 컴포넌트 책임으로 명확히 분리한다.

## Component And Style Rules

- 큰 page component는 orchestration과 persistence 중심으로 남긴다.
- 반복 UI와 독립 loading state는 전용 component로 분리한다.
- CSS는 기존 component SCSS 패턴을 유지한다.
- 카드 안에 카드 중첩을 피하고, shell/page layout과 item card 역할을 분리한다.

## Current References

- [standards/ANGULAR_FRONTEND_RULES.md](standards/ANGULAR_FRONTEND_RULES.md)
- [features/template-builder/README.md](features/template-builder/README.md)
- [features/dance-highlight/README.md](features/dance-highlight/README.md)
