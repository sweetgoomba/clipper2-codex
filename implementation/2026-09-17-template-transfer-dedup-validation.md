# 독립 개발판 템플릿 이관 중복 수정·실기 결과

2026-09-17 KST. 새 독립 개발판의 필수 이관 대상인 `.cliptpl` 템플릿 export/import를 실제 옛 개발판 데이터와 새 개발판 데이터 경로 사이에서 검증했다.

## 발견한 결함

옛 개발판에는 기본 제공 템플릿 16개와 사용자가 만든 `새 템플릿` 1개가 있었다. 옛 앱에서 17개를 모두 내보낸 뒤 새 개발판으로 가져오자 importer가 기본 제공 템플릿도 사용자 복사본으로 승격해 총 33개가 됐다. 같은 기본 템플릿이 두 벌 보이는 실제 사용자 결함이다.

원인은 내보내기 UI와 backend export가 기본 제공 항목을 허용하고, import가 번들 안의 기본 제공 identity를 사용자 템플릿으로 변환한 데 있었다. manifest metadata만 믿으면 실제 기본 제공 ID가 `user/custom`으로 위장돼도 통과할 수 있었고, 기본 제공 항목만 든 번들의 embedded font가 설치될 수도 있었다.

## 승인된 동작과 구현

- 내보내기 화면에는 `ownerType=user`, `source=custom`, `readonly=false`인 사용자 생성 템플릿만 표시·선택한다.
- backend export도 UI 우회를 신뢰하지 않고 같은 기준으로 다시 필터한다.
- 새 importer는 옛 format v1 번들을 포함해 기본 제공 템플릿을 건너뛴다.
- canonical 기본 제공 ID는 manifest metadata가 사용자 항목처럼 위장돼도 거부한다.
- 실제 사용자 템플릿이 참조하는 embedded font만 설치한다. 이미 존재하는 사용자 템플릿을 재가져올 때 누락된 사용자 font를 복구하는 동작은 유지한다.
- 옛 비표준 사용자 template ID의 결정적 mapping은 유지하되, 이를 system-template 호환 경로로 표현하던 내부 이름은 legacy user ID 의미로 정정했다.

Angular 커밋:

- `19b407a7a6de56d7a43428f688e3e4e7258fdc8d` `fix: export only user-created templates`

NestJS 커밋:

- `884fa8bc7abf5d802a142c918568d8e606041900` `fix: prevent built-in template duplication on import`

두 커밋은 원본 checkout의 `integration/dev-pg-local-validation-20260917`에만 있고 각 원격 통합 브랜치보다 1커밋 앞선다. push·추가 병합·dev/main 변경·배포는 하지 않았다.

## 기존 중복 데이터 정리

새 개발판 로컬 데이터의 잘못 생성된 `custom.template.from-system.template-builder.default-shortform` 및 `-02`부터 `-16`까지 정확히 16개만 정상 DELETE API로 제거했다. 사용자 템플릿은 보존했다. 정리 전 JSON/assets 백업은 `/tmp/clipper-template-cleanup-20260917.gK57IT`에 있다. 원격 DB와 기존 개발판 데이터는 변경하지 않았다.

정리·재가져오기 뒤 로컬 API 실측:

- 전체 17
- 기본 제공 16
- 사용자 생성 1 (`custom.template.512c3fb2-d36b-4431-87ef-3c5cf28e2e13`, `새 템플릿`)
- 잘못된 기본 제공 복제본 0

사용자가 새 빌드 UI에서 같은 17개 번들을 다시 가져오고 총 17개 유지, 기본 템플릿 중복 없음, 내보내기 화면에는 사용자 템플릿 1개만 표시됨을 모두 확인했다.

## 검증

- 새 macOS arm64 local-api 개발 앱 build PASS.
- artifact: `Clipper Studio (dev).app`, `CFBundleIdentifier=ai.clipperstudio.dev`, URL scheme `clipperstudio-dev`.
- 로컬 Web API `/health`: User/Admin/Release DB 모두 `ok`. 대상은 로컬 검증 컨테이너 57433–57435이며 원격 서버·개발 DB가 아니다.
- Nest build PASS, 템플릿 대상 69/69 PASS.
- Nest 전체 `CLIPPER_AUTH_MODE=local node --test test/*.test.js`: exit 0. 원본 폴더의 `.env.local`이 `jwt`인 채 실행한 최초 전체 suite는 Shortform API 10건이 bearer token 부재로 실패했으나, 실패 파일을 local mode로 재실행해 12/12 PASS하고 전체 suite도 통과했다. 제품 코드 결함이 아니라 테스트 실행환경 혼입이었다.
- Angular 템플릿 대화상자 31/31 PASS.
- Angular 전체 4,494/4,494 PASS.
- 두 저장소 `git diff --check` PASS, 커밋 후 clean.

## 남은 작업

1. 두 새 코드 커밋의 push는 별도 사용자 지시 전 실행하지 않는다.
2. Windows 개발판 설치·identity·템플릿 이관은 사용자가 Windows 장비에서 확인한다.
3. 소재관리·프로젝트 데이터의 자동 이관은 선택사항이며 이번 필수 템플릿 이관 완료로 자동 포함하지 않는다.
4. W04의 남은 비-ML 로컬 PG acceptance와 개발 DB 복제본 전환 rehearsal을 순서대로 진행한다. 실제 ML 플러그인과 Build 5 전체 QA HOLD를 유지한다.
5. 실제 개발 DB 변경·배포·서버 접속은 하지 않았고, 전환 계획 확인 및 별도 승인 전에는 진행하지 않는다.
