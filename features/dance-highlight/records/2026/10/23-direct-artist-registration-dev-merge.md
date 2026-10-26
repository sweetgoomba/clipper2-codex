# 2026-10-23 — 안무 카탈로그 직접 아티스트 등록과 dev 병합

## 요청과 결정

- 관리자 `/external-data`의 Wikidata 아티스트 후보 입력은 이름 검색만 제공한다. QID 직접 검색 안내와 처리 경로를 제거한다.
- Wikidata에 없는 그룹·솔로도 관리자가 직접 등록해 게시할 수 있다. `A2O LITE`는 등록 필요성을 설명한 예시이며, 이번 작업에서 실제 운영 카탈로그에 등록한 데이터는 아니다.
- 직접 등록 그룹은 멤버 0명으로도 게시할 수 있다. 공유 명단이 비어 있으면 데스크톱 사용자가 기존 화면에서 멤버를 직접 추가한다. 관리자가 명단을 입력하거나 나중에 수정하면 새 조회에 공유된다.
- 사용자가 설계·구현 계획을 승인하고 직접 구현을 선택했다. 구현 후 별도 지시로 4개 저장소의 변경을 원격 `dev`에 병합했다. 배포 지시는 없었다.

설계와 계획: [설계](../../../../../../web/clipper_web_api/docs/superpowers/specs/2026-10-23-dance-catalog-direct-artist-registration-design.md), [구현 계획](../../../../../../web/clipper_web_api/docs/superpowers/plans/2026-10-23-dance-catalog-direct-artist-registration.md). 제품 구현은 `/Users/jina/project/adlight/.worktrees/dance-manual-catalog-20261023/`의 네 독립 worktree에서 최신 원격 `dev`를 기준으로 진행했다.

## 구현 결과

| 저장소 | 반영 내용 |
| --- | --- |
| `web/clipper_web_api` | 직접 등록 ID `local_<32자리 hex>`와 멤버 ID `local_member_<32자리 hex>` 발급·검증. `POST /admin/dance-catalog/direct-artists`로 게시 버전, 이력, 빈 명단 행까지 한 트랜잭션에 저장. `PUT /admin/dance-catalog/direct-artists/:id/members`로 공유 명단을 수정하고 `updatedAt` 충돌 시 409 응답. 사용자 검색·제목 감지에 게시 항목을 포함하고, 직접 등록 그룹 명단은 Wikidata 대신 저장 명단에서 조회. Wikidata 후보의 QID 직접 검색 제거. 전체 수집과 이전 버전 복구에서 활성 버전의 게시 상태를 따르도록 처리. |
| `web/clipper_web_admin` | `/external-data`에 그룹·솔로 직접 등록, 선택 이름·별칭·멤버 입력, 게시 확인 모달, 직접 등록 그룹 명단 수정 UI 추가. 후보 검색은 이름만 받으며 결과가 없어도 직접 등록할 수 있다. 내부 ID 대신 `직접 등록` 출처를 표시하고, 직접 등록 그룹에 Wikidata 명단 재수집을 제공하지 않는다. |
| `desktop/clipper_nestjs` | 제품 코드는 그대로 두고 `local_` 후보 ID와 빈 공유 명단을 기존 문자열 계약으로 전달하는 테스트 추가. |
| `desktop/clipper_angular` | 직접 등록 후보에 `그룹 · 직접 등록`을 표시하고 내부 ID를 숨김. 공유 명단이 비었을 때 기존 멤버 직접 추가 흐름을 회귀 테스트로 확인. |

전체 수집이 이미 준비된 사이 직접 등록이 게시되면 오래된 수집 결과가 새 아티스트를 지울 수 있다는 리뷰 지적을 받았다. PostgreSQL 회귀 테스트로 재현한 뒤, 수집 결과를 게시하는 시점에 활성 버전을 다시 확인하는 보호를 추가했다. 관리자 화면에도 충돌 시 다시 확인할 안내를 넣었다.

## 병합 상태

각 저장소의 기능 브랜치를 원격 `dev`로 fast-forward push했고 원격 SHA를 확인했다.

| 저장소 | 원격 `dev` SHA |
| --- | --- |
| Web API | `ab5c82c7d32f8d0308022052c917b1abdb102d30` |
| Web Admin | `07c08ba68fded0b182587051b06ead54ecba5f69` |
| Desktop Nest | `c9eb82cb91c5322f3776d5f3225d61a1b6b989f0` |
| Desktop Angular | `73b378aae74d54d313c7492f1faed7a7fddd8cb0` |

기본 체크아웃의 미커밋 변경은 이 병합에 포함하지 않았다. 서버 배포, 실제 관리자 계정으로 게시하는 UI 확인, 배포된 데스크톱 앱의 실사용 확인은 수행하지 않았다. 새 후보 표시를 보려면 반영된 데스크톱 빌드가 필요하다.

## 검증

| 범위 | 결과 |
| --- | --- |
| Web API 전체 Jest | 406 suites / 4,186 tests 통과; 6 suites / 26 tests skip |
| Web API 전용 PostgreSQL e2e | 6/6 통과. 직접 게시·빈 명단·검색·버전 복구·전체 수집 충돌 경로 확인. 테스트용 DB는 종료함. |
| Web Admin | Karma 2,387/2,387, build, `check:colors` 통과. 초기 번들 예산 경고는 남음. |
| Desktop Angular | Karma 8,197/8,197, build, 스타일 검사 14/14 통과. |
| Desktop Nest | build와 관련 `dance-catalog-controller.test.js` 10/10 통과. |

Desktop Nest 전체 `node --test --test-concurrency=4 test/*.test.js`도 시도했으나, 격리된 실행 환경에서 `listen EPERM 127.0.0.1` 오류 88건과 checkout에 없는 ignored `waguri.ttf`·`.env.packaged` 의존성 등으로 104 failed / 27 canceled였다. 전체 suite 통과로 기록하지 않는다. 임시 의존성 링크는 제거했고 깨끗이 재빌드한 뒤 직접 관련 10개 테스트가 통과했다. 이 저장소에는 전체 suite용 정식 `npm test` 스크립트가 없다.

## 병합 후 기본 체크아웃 정리와 W14 문의

- 기본 `desktop/clipper_angular`의 스토리보드 설계 문서에는 공백 한 칸만 추가된 미커밋 변경이 있었다. 사용자 지시에 따라 해당 파일을 `git restore`해 되돌렸고 diff가 없는 것을 확인했다. 버릴 커밋은 없었다.
- 기본 `web/clipper_web_api`의 `feat/promotion-followups-20261023`에는 인물 하이라이트 `person_highlight.extract` 크레딧 요금·이용권 권한, 관리자 DB 마이그레이션과 테스트가 미커밋 상태로 남아 있다. `.env.example`의 `WEB_BASE_URL` 기본값 `4200→4201` 변경은 별도 로컬 로그인 설정이다. 두 종류 모두 이번 안무 카탈로그 병합에 포함하지 않았다.
- 사용자가 요청한 대로 **「2026.10.19-23 인물 하이라이트 플러그인」** 세션에 문의했다. 그 세션은 Web API의 인물 과금·권한 변경이 W14에 필요하고 원격 `dev`에는 아직 없다고 답했다. 별도 확인에서도 `person_highlight.extract`와 관련 마이그레이션이 당시 `origin/dev`에 없었다. W14 데스크톱 기능이 `dev`에 들어갈 때 해당 API 작업도 함께 별도 통합해야 하며, 빠뜨리면 과금 경로에서 `operation policy not found`가 날 수 있다. W14의 `dev` 병합은 사용자가 보류시킨 상태라 이번 세션에서 진행하지 않았다. `WEB_BASE_URL` 변경은 그 병합과 별도로 판단한다.

이후 W14를 병합할 때는 인물 하이라이트 세션의 [체크포인트 기록](../../../../highlights/records/2026/10/23-person-highlight-checkpoint-and-shared-face-model.md)과 현재 작업 트리를 다시 확인한다. 위 문의 과정에서는 인물 하이라이트 코드를 수정·커밋·푸시하지 않았다.
