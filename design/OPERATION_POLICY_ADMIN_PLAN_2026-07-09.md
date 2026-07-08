# Operation Policy Admin Implementation Plan

작성일: 2026-07-09 KST

목표: 운영자가 product operation별 크레딧 단가를 조회하고 제한적으로 수정할 수 있게 한다.

범위:
- `web/clipper_web_api`: `GET/PATCH /admin/operation-policies` API 추가
- `web/clipper_web_admin`: 운영자 화면에 `크레딧 정책` 메뉴와 페이지 추가
- 수정 가능 항목은 1차로 `creditCost`만 허용한다.
- Create/Delete, provider credential 값 표시, secret/env 출력은 하지 않는다.

검증:
- API controller/service/repository 테스트로 list/update 동작을 확인한다.
- admin Angular service/component/route 테스트로 조회, 수정, 메뉴 노출을 확인한다.
- `npm run build`를 각 repo에서 실행한다.

후속:
- `enabled`, 변경 이력, updatedBy는 별도 phase에서 migration과 audit 정책을 같이 설계한다.
