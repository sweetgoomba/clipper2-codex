# 인물 하이라이트 Web API 과금·이용 권한 dev 반영

## 승인과 코드 반영

- 사용자가 서버 변경의 커밋·병합과 로컬 API 연결 DB의 정책·권한 반영을 승인했다.
- 저장소: `web/clipper_web_api`. 최신 원격 dev `ab5c82c7d32f8d0308022052c917b1abdb102d30`에서 인물 변경만 분리했다.
- 기능 브랜치: `feature/person-highlight-billing-20261023`.
- 커밋: `ba68b2b689563b7070e66a0e6d6ceb1d5f98444f` (`feat: enable person highlight billing and plan access`).
- 기능 브랜치와 원격 `dev`에 atomic 일반 push를 완료했다. dev는 fast-forward이며 강제 push가 아니다. 두 원격 ref가 같은 SHA임을 확인했다.
- 검증 작업 트리: `/Users/jina/project/adlight/.worktrees/person-billing-dev-20261023/web/clipper_web_api`.
- 기존 기본 checkout의 미커밋 13개 파일은 SHA-256 대조로 그대로 보존했다. 로그인 주소·환경 예제 등 무관한 변경은 이번 커밋에 포함하지 않았다. 해당 checkout의 Person 변경은 원격 미반영 상태가 아니라 보존된 로컬 사본이다.

## 반영 범위

- `person_highlight.extract` 등록, 기본 단가 50크레딧, `charge_then_refund` 정책.
- 대사·안무와 같은 영상 길이 계산 경로: `ceil(sourceDurationSec / 60) × 정책 단가`.
- 기존 트랜잭션·재요청 중복 차감 방지·실패 시 환불 경로 사용.
- 크레딧 사용 내역의 ‘인물 하이라이트’ 명칭.
- `all` 요금제는 작업 등록 목록에서 인물 기능을 포함하며, 명시적 대사 이용 권한이 있는 요금제에는 기존 마이그레이션으로 인물 권한을 추가한다.
- 이미 로컬 DB에 실행된 `EnablePersonHighlightEntitlements1792400000000`의 이름과 동작을 유지했다. 같은 숫자 timestamp의 다른 마이그레이션과 이름으로 구별된다.
- 최신 dev의 큐레이션·해외 더빙 등록을 보존하도록 권한/카탈로그 테스트 두 곳의 예상 목록을 통합했다.

## 검증

- 최신 dev 기준 전체 Jest: 406 suites / 4,186 tests passed, 6 suites / 26 tests skipped, 5 snapshots passed.
- 최종 변경 전체 Jest: 407 suites / 4,193 tests passed, 6 suites / 26 tests skipped, 5 snapshots passed. 기존 skip 수 증가 없음.
- `npm run build`, `git diff --check` 통과. 별도 읽기 전용 코드 리뷰에서 추가 결함 없음.
- 최초 제한 환경에서 로컬 포트 바인딩이 차단돼 전체 테스트를 필요한 권한으로 재실행했다.
- 로그: `/tmp/person-billing-api-baseline.log`, `/tmp/person-billing-api-tests.log`, `/tmp/person-billing-api-build.log`.

## 로컬 API·DB 확인

- 실행 API의 cwd는 기존 `web/clipper_web_api`, 포트 3000이며 admin DB는 `localhost:5433/clipper_admin`이다.
- DB에는 Person 마이그레이션이 이미 실행돼 있었다. Person 마이그레이션만 대상으로 실행한 결과 추가 적용 0건이며, 다른 대기 마이그레이션은 실행하지 않았다.
- 대사/인물 정책 모두 단가 50·`charge_then_refund`. 인물은 외부 공급자 권한 없이 로컬 분석을 사용하므로 provider scopes는 빈 목록이다.
- DB 요금제 4개는 `all`; 명시적 대사 권한이 있으나 인물 권한이 빠진 allowlist 요금제는 0개다. 임의 권한 행을 추가하지 않았다.
- 실제 PostgreSQL의 임시 테이블에서 마이그레이션의 정책/권한 복사, 중복 실행, 사용자 지정 기존 단가 보존을 검증하고 모든 테스트 데이터를 rollback했다.
- 기존 API의 컴파일 산출물에도 Person 과금 코드가 있으며 `/catalog`는 HTTP 200과 공개 요금제 3개의 Person 이용 가능을 반환했다. 서버 재시작이나 앱 교체는 필요하지 않았다.
- 이 작업은 원격 dev 코드 반영과 로컬 DB 확인이다. 운영 서버/DB 배포나 실제 회원 크레딧 차감·결제망 호출을 수행한 기록은 아니다.

이전 데스크톱 병합 때 남았던 Web API 통합 항목은 완료다. Windows와 새 실영상의 얼굴/클립 품질 검증은 [데스크톱 병합·세션 인계](23-person-highlight-dev-merge-and-stage-usability-handoff.md)의 별도 범위로 남는다.
