# 플러그인 등록 자동 동기화 — 로컬 기술 검증

2026-10-28 KST. 사용자 요청에 따라 자동 감지·서버 전송·미공개 등록의 기술적 가능성을 로컬 실험으로 검증했다. **제품 API나 앱 기능에 반영한 구현이 아니라, 실제 소스와 실제 HTTP/PostgreSQL을 사용하는 별도 실험**이다.


## 검증한 흐름

1. 실제 Desktop Angular `src/app/app.config.ts`의 `providePipelineFeature` 등록을 TypeScript compiler API로 읽는다.
2. 해당 key를 `core/navigation/app-navigation-metadata.ts`의 실제 사용자용 정의와 대조한다. 과금 정의나 내부 TTS/렌더 모듈 목록에서 플러그인을 추측하지 않는다.
3. key/defaultName/route/icon 및 소스 revision/hash를 JSON artifact로 생성한다.
4. HTTP POST로 임시 `/internal/plugin-catalog/sync` endpoint에 보낸다.
5. 실제 PostgreSQL에서 plugin_key PK와 UPSERT를 이용해 신규 항목을 settings_pending으로 저장한다. 기술 정보만 갱신하며 운영 설정은 덮지 않는다.
6. 관리자 설정·공개를 별도 HTTP 요청으로 실행한다. 스토어용 조회는 published 항목만 반환한다.

이것이 여기서 말한 자동 감지다. 원격 서버가 개발자의 파일 시스템을 지켜보는 것이 아니라, 빌드/배포 도구가 생성된 등록 목록을 명시적으로 전송하는 방식이다. 본 구현에서는 앱 빌드 성공 이후 배포 대상 환경에 이 동기화 단계를 연결해야 한다.

## 결과

**11개 검사 통과, 프로세스 exit code 0.** 실제 앱 기준 revision `23392de036680cabac9c3f6a12630beaa39e4bb8`.

| 검사 | 관찰한 결과 |
|---|---|
| 실제 앱 등록 추출 | 사용자 플러그인 14개. person_highlight 포함, 내부 tts_supertonic 제외 |
| 인증 없는 업로드 | HTTP 401, DB 행 0 |
| 실제 HTTP 업로드 | 신규 14건, 전체 14건; 관리자 조회에는 설정 대기 14건, 스토어용 조회에는 0건 |
| 동일 artifact 동시·반복 전송 | 각각 신규 0건, 전체 14건 유지 |
| digest 변조·중복 ID artifact | HTTP 400, DB 변경 없음 |
| 동기화 자격으로 공개 요청 | HTTP 401 |
| 설정 없이 관리자 공개 요청 | HTTP 409 |
| 분류·표시 이름·허용 대상 설정 후 공개 | person_highlight 1건만 스토어용 조회에 노출 |
| 재동기화 | 공개 상태·운영자 표시 이름·분류·허용 대상 보존 |
| 소스 fixture에 신규 등록 추가 | 생성 artifact 15개, 서버 신규 1건·전체 15건, 새 항목은 미공개·허용 대상 없음 |
| 등록에 대응하는 메타데이터 누락 | 추출 단계에서 오류로 중단 |
| 임시 API·DB client 재시작 | 설정 대기/공개 및 운영 설정 그대로 보존 |

표의 일부 관찰은 같은 검사 함수에 포함된다. 실행 결과의 tests 항목은 11개다. 신규 15번째 항목은 소스 fixture에만 추가한 실험용 등록이다. 기존 컴포넌트의 로더를 재사용해 추출 경로를 확인했으며, 실제 새 플러그인을 개발·컴파일했다고 주장하지 않는다.

## 재실행 자료

- [실험 코드](28-plugin-catalog-sync-proof/plugin-catalog-sync-proof.mjs)
- [실제 소스에서 생성한 14개 목록](28-plugin-catalog-sync-proof/actual-app-plugin-catalog.json)
- [실험용 신규 등록을 포함한 15개 목록](28-plugin-catalog-sync-proof/fixture-app-plugin-catalog.json)
- [검사·DB 최종 상태 JSON](28-plugin-catalog-sync-proof/result.json)
- [실행 로그](28-plugin-catalog-sync-proof/run.log)

명령 예시(의존성 설치 불필요, 로컬 PostgreSQL 15 바이너리와 기존 API node_modules 사용):

```sh
/Users/jina/.nvm/versions/node/v22.22.3/bin/node /Users/jina/project/adlight/.codex/features/promotions/records/2026/10/28-plugin-catalog-sync-proof/plugin-catalog-sync-proof.mjs --output /private/tmp/plugin-catalog-sync-proof-repeat
```

코드는 매번 `/private/tmp/clipper-plugin-catalog-proof-*`에 새 전용 PostgreSQL cluster를 생성한다. TCP를 열지 않고 전용 Unix socket을 사용하며, HTTP는 127.0.0.1의 임의 포트만 사용한다. 최종 finally에서 HTTP·DB client·전용 PostgreSQL을 종료한다. 이번 실행의 종료와 제품 소스 불변을 result.json에서 확인했다.

## 증명 범위와 제품 구현에서 남은 연결

증명한 것은 실제 등록 정보의 자동 추출, HTTP 전송, 영속화, 신규 ID 판별, 중복 방지, 운영 설정 보존, 관리자 공개 전 비노출이다.

- 임시 서버는 기존 NestJS 제품 API가 아닌 작은 Express 실험 서버다. 인증도 실험 실행마다 생성한 별도 sync/admin token으로 경로를 분리했다. 실제 운영자 JWT/권한 또는 배포 자격 증명을 연동했다고 주장하지 않는다.
- 제품에 적용하려면 기존 Web API의 관리자 권한/배포 권한에 맞는 동기화 endpoint와 DB migration을 구현하고, 실제 빌드/배포 절차에 artifact 생성·전송 단계를 추가해야 한다.
- 현재 실험은 기존 TypeScript 등록 형식을 compiler API로 읽는다. 정식 구현에서는 플러그인의 기술 등록 정보와 관리자 운영 설정의 소유권을 나눠, 기술 정보의 정본에서 빌드와 artifact가 함께 생성되도록 구조를 정해야 한다.
- 스토어용 조회 결과를 검증했으며 실제 Desktop 스토어 UI나 실행 제한에 아직 연결하지 않았다. 전체 앱 패키징·개발/운영 서버 배포·제품 테스트는 이 실험의 범위가 아니다.
- digest는 artifact 동일성/변조 오류 확인용이며 호출 권한을 대신하지 않는다. source revision과 실제 배포 승인 여부를 결합하는 운영 절차는 제품 설계에 남는다.

## 크레딧 설명의 정확한 범위

‘무료체험 400 소진 후 유효한 프로모션 200이 남으면 쓸 수 있어야 한다’는 설명은 **무료체험 기간이 아직 남은 상황**을 예로 든 것이다. 무료체험에 허용된 플러그인 A는 남은 200으로 실행할 수 있고, Pro에만 허용된 플러그인 B는 잔액이 있어도 실행 대상이 아니다.

이는 플러그인 사용 대상과 과금 작업의 크레딧 잔액이 다른 검사라는 뜻이다. 무료체험 기간이 끝난 뒤의 접근 규칙을 자동 연장으로 확정한 것이 아니다. 현재 실제 차감은 출처별 유효기간을 따르며 이용권과 독립적이지만, 새 플러그인 사용 제한을 연결할 때 종료 후의 허용 범위는 별도로 결정해야 한다.
