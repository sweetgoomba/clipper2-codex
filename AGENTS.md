# Clipper 플랫폼 — 코드 에이전트 통합 규칙 (Consolidated Rules)

> **목적:** 이 한 파일만 읽으면 Clipper 플랫폼에서 코드를 작성할 때 지켜야 할 규칙을 알 수 있다. 다른 코드 에이전트(Claude 외 포함)에게 전달하는 핸드오프용 스냅샷.
> **정본 우선순위:** ① 사용자의 직접 지시 → ② 각 레포 `CLAUDE.md` / `clipper_docs/`의 출처 정본 → ③ 이 문서. 충돌하면 출처 정본을 확인할 것(이 파일은 합본 스냅샷이지 정본이 아니다).
> **출처:** `clipper_docs/`(루트 `CLAUDE.md`·`adr/`·`playbooks/`·`architecture/`) + 각 레포 `CLAUDE.md`. 섹션 끝 §11에 출처 인덱스.
> **최종 갱신:** 2026-06-24. (Material 파운데이션 §3, 데스크톱 로깅 계약 §6 신설, ADR-0008·0009 §1, §2.3 에러 퍼널 보정.)

## Codex 적용 메모

이 파일은 `clipper_docs`와 각 repo `CLAUDE.md`에서 온 코드 작업 규칙 요약본이다. Codex 세션에서는
이 문서를 전체 명령서로 보지 않고, 코드 구조·리팩토링·계약·테스트 원칙을 이해하기 위한 참고 자료로 사용한다.

Codex는 다음 기준으로 적용한다.

1. 사용자의 직접 지시가 최우선이다.
2. 현재 repo의 실제 코드, `package.json`, 테스트/빌드 결과를 우선 확인한다.
3. 이 문서와 `clipper_docs`의 구조·코딩·리팩토링 원칙은 가능한 한 존중한다.
4. Claude Code 전용 도구명, workflow, 문서 저장 위치 지시는 Codex 환경에 맞게 변환하거나 적용하지 않는다.
5. `.codex`의 `README.md`, `handoff/`, `records/sessions/`는 Codex 작업 이력과 인계용으로 계속 유지한다.
6. 충돌이 있으면 문서 문구보다 현재 코드 상태와 사용자의 명시 지시를 우선한다.

---

## 0. 레포 지도 · SoT(단일 출처)

```
desktop/                    설치형 데스크톱 제품 (Electron, 4레포 형제 — 상대경로 보존)
  clipper_angular           Electron 렌더러 UI (Angular 19 + Material + @ngrx/signals)
  clipper_electron          Electron 셸/메인 프로세스 (TS)
  clipper_nestjs            렌더/스튜디오 백엔드 (NestJS 10, trusted-header 소비자, 로컬 JSON 사이드카)
  clipper_python            ML 플러그인 (uv 워크스페이스, FastAPI)
web/                        웹 플랫폼
  clipper_web_client        고객용 FE (Angular 19)
  clipper_web_admin         운영자 콘솔 FE (내부 전용, IP 화이트리스트/VPN, Angular 19)
  clipper_web_api           웹 백엔드 (NestJS 11) — 신원·이용권·결제 SoT
  clipper_infra             인프라 (docker-compose·CI·도메인·백업) — 팀원 소유
clipper_docs/               크로스-레포 메타 (adr·architecture·playbooks·templates·glossary·todos·status)
```

- **데스크톱과 웹은 별도 레포.** 인증/회원/결제 로직을 양쪽에 복제 금지.
- **`clipper_web_api` = 신원·이용권 SoT.** `clipper_nestjs`는 **trusted-header 소비자**(헤더 `x-clipper-subject` / `x-clipper-tenant` / `x-clipper-plan`를 소비만, 자체 인증 로직 없음).
- **API 계약 SoT = `clipper_web_api/docs/api/openapi.yaml`** (단일 출처).

---

## 1. 플랫폼 결정 (ADR → 규칙)

각 ADR의 결정을 "지켜야 할 규칙"으로 압축. 상세는 `clipper_docs/adr/`.

- **ADR-0001 별도 레포:** 웹은 데스크톱에 모듈로 끼우지 않는다. 신규 레포는 언더스코어 역할/계층명(`clipper_web_*`).
- **ADR-0002 Google OAuth 단독(1차):** 웹 로그인 = Google OAuth만. 이메일/비번·타 소셜은 후순위. 계정 모델은 Google `sub` 기준으로 두고 추후 linking 가능하게 설계. 설치형은 딥링크 OAuth(커스텀 프로토콜 + PKCE).
- **ADR-0003 수동 이용권 발급(1차):** PG 자동결제 없음. **구매 요청 → 운영자 수동 발급/반려**. client=요청 폼·승인 대기, admin=요청 목록·발급/반려.
- **ADR-0004 TypeORM 멀티 DB:** `clipper_web_api`는 3개 독립 Postgres(`user`/`release`/`admin`)에 named DataSource ×3으로 연결. (DB 규칙은 §4.)
- **ADR-0006 TTS = 재사용 에셋(프리셋):** TTS는 일회성 생성기가 아니라 **저장·재사용되는 에셋**. 저장 단위 = 프리셋 `{ label, voiceId, speed }`(소리 파일 아님). 보이스(빌트인+클론) ↔ 프리셋 2계층. 소비는 `tts-picker`(template-builder→picker 선례 재사용). 클론은 seam만 열고 구현은 미래. SoT = Nest `CLIPPER_DATA_DIR`(JSON).
- **ADR-0007 NestJS 구조 표준:** `clipper_web_api` 골격을 표준으로, `clipper_nestjs`가 수렴. (구조 규칙은 §2.)
- **ADR-0008 NestJS 11 정렬(채택·실행 예정):** `clipper_nestjs`를 NestJS 11로 올려 `clipper_web_api`와 정렬(주말 일괄 슬롯). 모듈 시스템(CJS)·테스트 러너(`node:test`)는 이번 범위 밖. 근거 = Express 4 보안-유지보수 모드 탈출 + 분기 엔트로피 차단.
- **ADR-0009 데스크톱 관측성:** 4프로세스 `v:1` JSON Lines 로깅(main funnel) + trace 상관추적(`x-trace-id`) + 에러 퍼널. 온디바이스 로컬 진단. (계약은 §6.)
- **ADR-0005 응답 봉투 → 철회(2026-06-20):** 전면 봉투는 **도입하지 않는다.** 응답은 raw. (§5 참조.) ⚠️ 일부 문서(ADR-0006/0007 본문)에 "응답=ADR-0005 봉투"라는 **낡은 표현이 남아있을 수 있으나 무시** — 현재 정본은 raw다.

---

## 2. 백엔드 (NestJS) 규칙

### 2.1 디렉토리 구조 — "Clipper NestJS 표준" (ADR-0007)
- 공통 어휘(두 레포 동일): `src/modules/<feature>/{domain, application, infrastructure, presentation}` + `core/` + `shared/`.
  - **domain** — 도메인 모델 + repository **추상** 계약(추상 클래스) + 순수 업무 규칙(프레임워크 무의존).
  - **application** — service / use-case(오케스트레이션).
  - **infrastructure** — repository **구현**(`TypeOrm*`/`Json*`) + ORM 엔티티 + 외부 어댑터.
  - **presentation** — controller + `dto/`(HTTP 통신).
  - `<feature>.module.ts`(루트, 레이어 아님) — 조립/DI 바인딩(`{ provide: XRepository, useClass: TypeOrm/Json XRepository }`).
  - `core/` = 인프라·횡단(config·auth·realtime·logging·execution·database/storage·health), `shared/` = feature 비종속 유틸/filter/pipe.
- **"비어있지 않은 레이어만"(핵심 규칙):** 파일이 ≥1개인 레이어 폴더만 만든다. **빈 레이어 폴더 금지.** 얇은 feature는 `presentation/` + `<feature>.module.ts`만으로 접히고, 무거운 feature만 4-layer를 다 갖는다.
- **의존 방향(DIP):** `presentation → application → domain(추상)`, `infrastructure`는 domain 추상을 구현해 module에서 DI 바인딩. domain은 아무것도 의존하지 않는 중심.
- **auth 배치는 역할에 따른다:** 엔드포인트 노출이면 `modules/auth/`(web), 소비 provider면 `core/auth/`(desktop trusted-header).

### 2.2 임포트 / 런타임
- **import는 상대경로**(런타임 안전). TS path alias는 `tsc`가 dist에 리터럴로 남겨 `node dist/main` 크래시 위험 → 백엔드는 상대경로(또는 tsc-alias를 모든 실행모드에 적용). Angular(번들)는 alias OK.
- 소스 이동 시 테스트의 `require('../dist/...')` 경로도 함께 갱신.

### 2.3 응답 / 에러 / 검증
- **응답 = raw** (§5). 전역 응답 인터셉터·봉투 도입 금지.
- 에러 = NestJS 기본(`HttpException` throw → `{ statusCode, message, error }`). **클라이언트 응답 계약은 raw 유지**(봉투·머신 에러 코드 미도입). 단, 2026-06-23 "에러 퍼널"로 **로깅용 전역 예외 핸들러**가 추가됨(미처리 예외·잡 실패를 JSON 로그에 trace와 함께 기록 — 응답 형식 무변경, §6). ⚠️ 로컬·MERGE-READY(미머지).
- 입력 검증 = `ValidationPipe`(전역, `whitelist:true, transform:true`) + class-validator DTO.

### 2.4 영속성
- 영속성은 레포별 분리 유지: web=TypeORM/Postgres, desktop=JSON 파일(`CLIPPER_DATA_DIR`). 공유 계약은 **repository 추상 패턴**뿐.

### 2.5 레포별 핵심(출처 = 각 레포 `CLAUDE.md`)
- **clipper_nestjs:** NestJS 10. `127.0.0.1:9019`, API 프리픽스 `/v1`. 테스트 = **`node:test`**, `test/*.test.js`가 `dist/`를 `require()` → **`npm run build && node --test test/<name>.test.js`**. 12-factor(`/v1/health`·env·stdout 로그).
- **clipper_web_api:** NestJS 11. 신원·이용권·결제 SoT. 멀티 DB(§4). 테스트 = `*.spec.ts` colocated.

---

## 3. 프론트엔드 (Angular) 규칙

- **컴포넌트 구조:** Angular CLI 표준 — `*.ts` / `*.html` / `*.scss` / `*.spec.ts` 4파일 분리. **인라인 템플릿·인라인 스타일 금지.**
- **standalone + signals**(@ngrx/signals), `OnPush` 지향.
- **feature-first** 배치: `core/` · `modules/`(또는 `features/`) · `shared/`, 공개 웹은 `public/portal` 구분.
- **Material 파운데이션 (clipper_angular, origin/dev 머지됨):** 색·간격·폰트는 **시맨틱 토큰 한 세트**(`src/styles/_tokens.scss`)에서만 옴 — **앱 SCSS raw hex/rgba 금지(raw-hex 0 불변식)**. 부품은 **`mat-*` 우선**. **다크/라이트 2스킴**(`ThemeService`, 기본 다크), **다크 primary `#4fcf8c`**(네온 그린 `#02e600`/`#66f094` 부활 금지). 페이지는 공유 **`<app-page>`**(풀폭·좌측정렬·유동, min-width/content-max 캡 없음). 좌측 nav = **설치된 워크플로만 동적**. 상세 = `desktop/clipper_angular/CLAUDE.md` + spec `…/specs/2026-06-22-material-foundation-design.md`.
- **룩앤필 일관:** 모듈을 나눠도 위 토큰/`mat-*`/`<app-page>` 재사용. 모듈 전용 새 비주얼 언어 발명 금지. (web FE 2앱도 Angular Material 19 — 데스크톱 팔레트 공유 범위는 각 레포 `CLAUDE.md` 확인.)
- **환경설정:** build-time `environment.*` 분리(`fileReplacements`) + `environment.*` 직접 읽기. SPA 런타임 주입 금지.
- 깊은 상대경로 대신 `@env` 등 alias 권장(번들이라 alias 안전).

---

## 4. 데이터베이스 규칙 (`clipper_web_api`, ADR-0004)

- **3개 독립 Postgres**: `user` / `release` / `admin`. `TypeOrmModule.forRootAsync` ×3(named DataSource), 엔티티는 도메인 DB에 `forFeature([X], '<conn>')`.
- **DB 간 FK/JOIN 금지** — 교차 참조는 ID로, 정합성은 앱 레벨.
- **컬럼 = snake_case**, 엔티티에 **명시적 `@Column({ name })`**로 선언(네이밍 전략 안 씀). 마이그레이션도 직접 snake.
- 마이그레이션은 **DataSource별**, `synchronize:false`. 공유 DB에 unversioned 마이그레이션 금지.
- 연결값은 env(12-factor).

---

## 5. API 계약 / 응답 형식

- **계약 우선:** 계약은 `clipper_web_api/docs/api/openapi.yaml`(단일 출처)에 먼저 정의 → FE mock → 백엔드 per-endpoint(`useMocks` 해제). **백엔드에서 계약을 몰래 바꾸지 말 것** — 바꾸면 OpenAPI + FE mock + FE를 한 스텝으로.
- **응답 = raw (봉투 없음).** 성공 = 컨트롤러가 반환한 도메인 값을 그대로 직렬화(벌거벗은 객체/배열). 에러 = NestJS 기본 `{ statusCode, message, error }`.
  - FE는 `http.get<T>()`로 바디 직접 수신, 에러는 `HttpErrorResponse`로 처리. unwrap 인터셉터 도입 금지.
  - **재검토 트리거(이때만 국소 봉투화 검토):** `clipper_web_api`의 *목록형* 엔드포인트를 *설치형 데스크톱이 망으로 호출*하고 거기에 페이지네이션/메타가 필요해질 때 → 그 엔드포인트만. (lockstep인 `clipper_nestjs` 경로는 해당 없음.) 근거: `architecture/2026-06-20-api-response-raw-decision.md`.

---

## 6. 데스크톱 로깅 · 관측성 계약 (4프로세스 JSON Lines)

> 결정 = **ADR-0009**. 정본 = `clipper_docs/architecture/2026-06-16-cross-process-logging-design.md`(§4.1 스키마) + `2026-06-19-trace-correlation-sp1-design.md`(trace 전파).

- **데스크톱 4런타임(electron main · renderer · nest · python)은 동일한 `v:1` JSON Lines 스키마로 로그를 emit한다.** 1줄 = 완결 JSON 1개:
  `{"v":1,"ts":<ISO-8601 UTC+ms>,"level":<trace|debug|info|warn|error|fatal>,"src":<main|renderer|nest|python.{plugin}>,"msg":<str>,"trace"?:<8-hex>,"ctx"?:{…}}`.
- **수집 = Electron main 깔때기(funnel).** main/renderer=`electron-log`; 자식(nest/python) stdout을 main이 캡처 → 소스별 `~/Library/Logs/Clipper2/*.jsonl`(5MB 회전, `.old` 1개). 비유효 줄은 main이 스키마로 감싸 **항상 유효 JSON 보장**.
- **레포별 emit 책임:** electron=`electron-log` JSON 포맷, angular=`electron-log/renderer` funnel(`src:"renderer"`), nest=커스텀 `JsonLogger`(stdout JSON, `src:"nest"`), python=`structlog`(stdout JSON, `src:"python.{plugin}"`). **stdout 텍스트 로그 금지 — JSON 줄만.**
- **trace 상관추적:** 한 사용자 액션을 프로세스 너머로 묶는 8-hex ID. HTTP 헤더 `x-trace-id`로 전파(nest=AsyncLocalStorage, python=contextvar). 디버그 뷰어(`clipper_angular` 설정→로그)가 소스·레벨·검색·trace로 조회.
- **에러 퍼널(2026-06-23):** 두 백엔드의 미처리 예외·잡 실패를 이 로그에 trace·스택과 함께 남기는 전역 핸들러(§2.3, 응답 형식 무변경).
- **⚠️ 규칙화 전 머지 확인:** 베이스 v1(Tier 2 구조화 로깅)은 dev 반영. **trace wiring(SP1/SP2)·에러 퍼널은 로컬 브랜치·MERGE-READY(미머지)** — dev 반영 후 규칙으로 굳힌다. 비범위 = 서버 전송·Sentry·OTel·라이브 tail.
- **로컬 진단 전용** — `clipper_web_api`(신원·이용권 SoT)와 접점 없음. web 서비스 로그 = 12-factor stdout(§9, 별개).

---

## 7. 작업 흐름 (플레이북) — 작업 전 해당 규칙을 따른다

### 7.1 리팩토링 (`playbooks/refactor.md`)
- **동작 불변.** 엔드포인트·응답·스키마·UI 동작 그대로. 변경은 파일 위치·모듈 경계·import·네이밍·중복 제거까지.
- **안전망 먼저:** 변경 전후 `build` + `test` + (해당 시) 부팅/`/health` GREEN. 테스트 약하면 보강 후 시작.
- **작은 단위 + 태스크별 커밋**, 각 커밋 green 유지. 파일 이동은 **`git mv`**(이력 보존). 대량 이동 후 dev 서버 재시작.
- 계약/엔드포인트/스키마 무변경 — 바꿔야 하면 별도 작업.

### 7.2 기능 추가 (`playbooks/feature.md`)
- 흐름: **brainstorming → spec → plan → 구현(subagent-driven) → finishing**. 화면 관련이면 목업(static HTML) 먼저.
- **계약(OpenAPI) 우선 → FE mock → 백엔드.** **TDD**(실패 테스트 → 구현 → 통과 → 커밋).
- 신규 작업은 `feat/<topic>` 브랜치. 크로스-레포 기능은 레포 간 **동일 브랜치명**.

### 7.3 성능 (`playbooks/perf.md`)
- **추측 금지 — 먼저 측정.** 측정 → 가설(한 병목) → 최소 변경 → 재측정(개선 없으면 되돌림) → 회귀 방지(벤치 기록).
- 데이터 없으면 최적화하지 않는다. 읽기 쉬움 > 미세 최적화. 한 번에 한 변경.

---

## 8. 문서 규칙 (`clipper_docs/CLAUDE.md`)

- **레포 한정 문서** → 그 레포 `docs/superpowers/{specs,plans,reviews}/` (+ `docs/adr/`). **크로스-레포** → `clipper_docs/`.
- 한 토픽 흐름: **spec(설계) → plan(구현계획) → 구현 → review(피드백)**. 파일명 `YYYY-MM-DD-<topic>-...md`. 양식 = `clipper_docs/templates/`.
- `clipper_docs/` 하위 구분:
  - `adr/` — 시스템 차원 결정(`NNNN-제목.md`, 양식 `_TEMPLATE.md`).
  - `architecture/` — 아키텍처/분석/핸드오프.
  - `templates/` — 공통 양식. `glossary.md` — 도메인 용어.
  - **`todos/`** — 작업을 끝낸 뒤 **후순위로 미룬 것**(deferred follow-up·잔여 백로그·재검토 트리거). 한 작업에서 파생된, 지금은 안 하지만 잊지 않으려는 잔여 항목.
  - **`status/`** — 진척 스냅샷·상태 보고(**현재** 상태). 할 일 목록을 여기 두지 말 것 — `todos/`와 성격이 다름.

---

## 9. 작업 / 프로세스 규칙

- **커밋·push는 사용자가 요청할 때만.** 변경은 해당 레포 안에서.
- 루트는 git 레포가 아니다. 정본 성격 문서는 `clipper_docs`(git)에서 버전관리.
- **12-factor 계약 유지**(웹 서비스): 서비스=컨테이너, `/health`, 설정은 env 주입, 로그는 stdout, 산출물=Docker 이미지. (인프라 트랙=`clipper_infra`, 팀원 소유 — 경계 준수.)
- **횡단(전사) 변경은 기능에 끼워넣지 말고 별도 일괄 리팩토링으로 모은다.** 기능은 현 레포 관습 그대로 빌드.
- 런타임 검증: 유닛테스트 GREEN만 믿지 말 것. DI/라우트/provider 버그는 테스트가 가린다 → `ng serve`/`nest start` 기동 스모크로 실제 렌더·부팅 확인.

---

## 10. 빠른 체크 (코드 작성 직전 자문)

- [ ] 이 변경이 계약(OpenAPI)·엔드포인트·응답 형식을 바꾸나? → 바꾸면 별도 작업 + 계약 먼저.
- [ ] 응답에 봉투(`{data}`/`{error}`)를 씌우려 하나? → **금지(raw).**
- [ ] NestJS feature를 만드나? → `modules/<feature>/` + "비어있지 않은 레이어만" + 상대경로 import.
- [ ] DB 작업? → 3분리·FK/JOIN 금지·snake_case `@Column({name})`·DataSource별 마이그레이션.
- [ ] Angular 컴포넌트? → 4파일 분리·인라인 금지·signals/standalone·**시맨틱 토큰만(raw-hex 0)·`mat-*`·`<app-page>`·다크 #4fcf8c**.
- [ ] 데스크톱 로깅 추가? → **`v:1` JSON Lines**·`src`별 emit(nest=`JsonLogger`·py=`structlog`·renderer=`electron-log`)·**stdout 텍스트 로그 금지**.
- [ ] 커밋하려 하나? → **사용자 요청 없으면 금지.**
- [ ] 횡단 변경인가? → 기능에 끼우지 말고 일괄 리팩토링 후보로.

---

## 11. 출처 정본 인덱스

| 주제 | 정본 |
|---|---|
| 플랫폼 가이드(레포 지도·결정·작업규칙) | 루트 `CLAUDE.md` (정본은 `clipper_docs`에서 버전관리) |
| 문서 규칙 | `clipper_docs/CLAUDE.md` |
| 시스템 결정 | `clipper_docs/adr/0001~0009-*.md` |
| 작업 플레이북 | `clipper_docs/playbooks/{refactor,feature,perf}.md` |
| NestJS 구조 표준(상세) | `clipper_docs/architecture/2026-06-20-nestjs-structure-unification-design.md` (ADR-0007) |
| API 응답 raw 결정(상세·옵션 비교) | `clipper_docs/architecture/2026-06-20-api-response-raw-decision.md` |
| FE 구조 통일(상세) | `clipper_docs/architecture/2026-06-11-web-frontend-structure-unification-design.md` |
| Material 파운데이션(상세) | `desktop/clipper_angular/CLAUDE.md` + `clipper_angular/docs/superpowers/specs/2026-06-22-material-foundation-design.md` |
| 데스크톱 로깅 계약(상세) | `clipper_docs/architecture/2026-06-16-cross-process-logging-design.md` (+ `2026-06-19-trace-correlation-sp1-design.md`) |
| 에러 퍼널(상세) | `clipper_docs/architecture/2026-06-23-error-handling-conventions-design.md` (+ `-implementation-design.md`/`-plan.md`) |
| 레포별 규칙 | 각 레포 `CLAUDE.md` (예: `clipper_nestjs/CLAUDE.md`, `clipper_web_api/CLAUDE.md`) |
| 도메인 용어 | `clipper_docs/glossary.md` |
