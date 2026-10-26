# 2026-10-16 Clipper `dev` 병합·개발서버 상태

기준 시각: 2026-10-16 05:26 KST. 이 문서는 10월 16일 새벽 로컬 `dev`를 최신 `origin/dev`로 갱신한 뒤 병합한 작업과, 그 전후의 개발서버 배포를 구분한 스냅샷이다. **`dev` 코드 병합은 개발서버 배포나 데스크톱 설치 파일 갱신을 뜻하지 않는다.** 커밋·배포 이력은 해당 세션 기록과 각 저장소 Git 이력으로 대조했다. 이 문서를 작성하면서 앱 코드, DB, 서버 배포는 변경하지 않았다.

## 1. `dev` 갱신 후 병합한 작업

| 작업 | 저장소와 `dev` 반영 커밋 | 반영 범위 |
| --- | --- | --- |
| 안무 사용성·W13/W14 공통 얼굴 매칭·ISS-028 URL 차단 | Desktop Angular `dfa684e1`; Python `3be469f`; NestJS `7017447`; Electron `64e7788` | 안무 아티스트 선택·직접 입력 흐름, 공유 얼굴 매칭 코어와 Dance 연결·패키징, URL 검증. W13/W14 통합 시험 브랜치에 남은 후속 미커밋 작업 전체를 병합했다는 뜻은 아니다. |
| 결과 화면 원본 URL 복사 | Desktop Angular `abaceeb5` | 안무·대사 결과 화면 헤더의 원본 URL 복사 동작. |
| 안무 카탈로그·외부 데이터 운영 | Web API `c43de1e`; Web Admin `073d044` | Wikidata 목록 수집·검증·게시 및 그룹 명단 조회, 관리자 외부 데이터 화면. Web API 병합에는 이름→QID 7일 캐시, 연락처가 포함된 공통 User-Agent, 429 응답 처리도 포함된다. |
| ISS-056 크레딧 원장 날짜 필터 | Web API `c43de1e`; Web Client `010b2a4` | KST 날짜 기준 원장 조회·화면 필터. |
| 카탈로그 개인 활동자 보존 | Web API `3187646` | 기존 게시 솔로가 Wikidata의 한국 국적 기록만 잃은 경우 수집본에서 보존하고 경고로 표시. 래퍼 QID 정정과 검증 정책 버전 3도 포함된다. |
| 결제 고객명 전달 보완 | Web API `15ff474`; Web Client `df60b7c` | 단건 결제·카드 인증·정기 청구와 Toss SDK 요청에 계정 이름 전달. 내부 QA 뒤 추가된 별도 수정이다. |

위 일곱 저장소의 로컬 `dev`와 `origin/dev` 추적 ref는 05:26 KST 확인에서 각각 일치했다. 현재 HEAD는 Angular `abaceeb5`, Python `3be469f`, NestJS `7017447`, Electron `64e7788`, Web API `15ff474`, Web Client `df60b7c`, Web Admin `073d044`다. 이는 **로컬 추적 ref 확인**이며, 이번 문서 작성 중 원격 서버를 새로 fetch한 결과는 아니다. 병합 당시의 빌드·테스트 통과는 원래 세션에 기록돼 있으며 이번에는 재실행하지 않았다.

### `dev` 갱신 전에 이미 병합됐던 W06

TossPayments 새 MID 개발 환경 동기화 코드는 10월 15일 먼저 Web API `e252a1c`, Web Client `3e51f9e`, 인프라 `328f8b8`로 `dev`에 들어갔다. 따라서 위 표의 새벽 병합 작업과 시점이 다르다. 인프라 로컬 `dev`는 `328f8b8`이며, 이후 W06 실행 이력 문서만 추가한 `3c335b8`이 `origin/dev` 추적 ref에 반영돼 있다. [W06 실행안](../../../../web/clipper_infra/runbooks/toss-dev-mid-sync-20261015.md)의 당초 코드 병합 단계 이후, 개발 DB 3개 초기화·마이그레이션·테스트 MID 키 교체·API/고객 웹 배포와 테스트 거래 검증이 별도 세션에서 진행됐다. 실제 서버 작업·거래 결과는 [W06 실행 이력](../../../../web/clipper_infra/runbooks/toss-dev-mid-sync-execution-20261016.md)에 남아 있다.

## 2. 실제 개발서버 반영과 확인 범위

| 대상 | 마지막으로 확인된 실행 상태 | 근거·한계 |
| --- | --- | --- |
| Web API | `clipper-web-api-dev` 실행 중, 이미지 revision `15ff474ab2091f98bb8262d8337961215826f69b` | 10월 16일 m2-stage 사용자 제공 `docker inspect` 출력. W06 세션의 `/health`에서 User/Admin/Release DB 모두 `ok`. `15ff474`에는 위 표의 Web API 병합이 포함된다. |
| Web Client | `clipper-web-client-dev` 실행 중, revision `df60b7c2855360f8d035fe943035d061f110af72` | W06 세션의 m2-stage 사용자 제공 `docker inspect` 출력. 결제 고객명 수정까지 포함한다. |
| Web Admin | `clipper-web-admin-dev` 실행 중, revision `073d0446d53b5a695b1ef6d70f884a262e6da162` | 사용자 실행 `sh scripts/deploy-dev.sh admin` 결과. 외부 데이터 메뉴가 `dev`에 병합된 뒤 관리자 배포 대상이 빠져 구 화면이 보였고, 관리자 전용 배포로 갱신했다. |
| Desktop 4개 저장소 | 소스 `dev` 병합 완료 | 새 설치 파일의 배포·실제 영상 품질·W13/W14 정확도 향상은 이 병합 사실만으로 확인되지 않는다. 통합 시험 checkout의 후속 변경과 구분한다. |

### Wikidata User-Agent 실서버 확인

‘안무 하이라이트 사용성 개선’ 세션의 `bee4350`이 Web API 실행 revision `15ff474`의 조상임을 Git으로 확인했다. [SPARQL 수집 코드](../../../../web/clipper_web_api/src/modules/dance-catalog/infrastructure/wikidata-catalog-source.ts)와 [그룹 이름 검색 코드](../../../../web/clipper_web_api/src/modules/dance-catalog/infrastructure/wikidata-group-name-source.ts)는 공통 `wikidataUserAgent()` 결과를 `User-Agent` 헤더에 넣는다. 기본값은 애플리케이션 이름과 연락처를 포함한다. [개발 Compose](../../../../web/clipper_infra/apps/compose.yml)는 `WIKIDATA_USER_AGENT`를 별도로 전달하지 않는다.

사용자가 **10월 16일 05:09 전체 목록 수집 후** m2-stage에서 실행한 읽기 전용 확인 결과는 아래와 같다. 이는 현재 컨테이너에 실린 함수와 환경변수의 결과다. 외부로 나가는 패킷을 직접 캡처한 검사는 아니다.

```text
state=running revision=15ff474ab2091f98bb8262d8337961215826f69b
{"source":"code-default","contactIncluded":true}
```

따라서 확인 시점의 개발 API는 별도 환경변수 없이 연락처 포함 코드 기본 User-Agent를 사용한다. User-Agent 설정으로 Wikidata의 호출 제한 자체가 없어지지는 않는다.

### 카탈로그 게시 상태

관리자 외부 데이터 화면에서 사용자는 2026-10-16 05:09 KST에 전체 목록 수집 작업 `463c45e0-bd1b-4ae2-b55e-4f54d751009e`가 **검증 완료**인 것을 확인했다. 검증 완료는 자동 게시가 아니다. 해당 작업의 추가·삭제·변경 내역을 확인하고 `검증된 버전 게시`를 눌렀다는 후속 증거는 아직 받지 않았으므로 **게시 여부는 미확인**으로 둔다. 이 작업의 성공을 W13/W14 하이라이트 품질 검증으로 해석하지 않는다.

## 3. 결제 개발 환경 검증의 범위

W06 세션에서는 개발 API·고객 웹의 새 이미지 기동, 개발 DB 초기화·마이그레이션 후 `/health`, Business 월간 테스트 결제 29,900원과 4,000 크레딧 지급, 추가 크레딧 400 결제 5,900원과 전액 환불·크레딧 회수, Toss 거래·안내 메일·취소 웹훅·관리자 기록을 대조했다. 추가 크레딧 메일에는 새 계정 이름이 표시됐다. `BILLING_DELETED` 이벤트는 빌링키를 실제 삭제하지 않아 수신 검증을 하지 않았고, 새 고객명 코드로 **정기결제를 다시 실행해 보낸 메일**도 확인하지 않았다. 개발 거래 검증은 운영 결제 상태를 증명하지 않는다.

## 4. 기록의 경계

- 기존 [W13/W14 통합 시험 기록](../../../features/highlights/records/2026/10/15-w13-w14-test-build-integration.md)은 격리 checkout과 당시 시험 범위를 설명한다. 그 뒤 `dev`에 병합한 커밋 범위는 이 문서의 표를 기준으로 읽는다.
- [W06 초기 조사](../../../implementation/2026-10-15-toss-dev-mid-sync-audit.md)의 ‘아직 배포 전’ 서술은 당시 상태다. [실행안](../../../../web/clipper_infra/runbooks/toss-dev-mid-sync-20261015.md)은 재실행 참고 절차이며, 실제 개발서버 전환·테스트 결과는 [W06 실행 이력](../../../../web/clipper_infra/runbooks/toss-dev-mid-sync-execution-20261016.md)과 이 문서의 2·3절을 기준으로 읽는다.
- 05:26 KST 이후의 원격 push, 컨테이너 교체, 게시 버튼 실행 여부는 이번 스냅샷에서 확인하지 않았다.
