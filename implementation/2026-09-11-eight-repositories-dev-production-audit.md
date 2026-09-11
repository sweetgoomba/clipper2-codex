# 8개 저장소 dev·운영 기준 비교 — 2026-09-11

조회 시각(로컬): 2026-09-11T11:23:48.135493+09:00

**결론: 5개 저장소에 운영 기준 브랜치에 없는 dev 변경이 있다. 운영 기준 8개 원격 HEAD는 9/10 마지막 기록과 같고, dev는 Electron·Angular·Nest·API에서 추가 진전했다.**

현재 GitHub 원격 heads를 읽고 별도 임시 bare clone에만 dev/운영 객체를 fetch했다. 공유 checkout의 branch/HEAD/status/추적 diff hash는 조회 전후 동일하다. 테스트·빌드·merge·commit·push·배포 없음. .env 내용은 읽지 않았다.

## 실제 운영 증거의 한계

API e0e5b35 / Admin cd3a306 / Customer 4d95a96은 9/10 사용자 서버 출력과 화면 확인으로 마지막 배포가 확인된 revision이다. 이번에는 운영 컨테이너에 직접 접속하여 실행 revision을 재조회하지 않았다. 따라서 현재 원격 운영 브랜치가 같은 것은 확인했지만, 현재 실행 서버까지 새로 확인했다고 해석하지 않는다. 데스크톱은 설치0.0.3.7 보고만 있으며 Build7의 정확한 source snapshot은 여전히 미확보다. 아래 desktop SHA는 운영용 소스 브랜치 기준이며 설치본 SHA로 확정한 값이 아니다. Infra도 원격 소스 기준이다.

| 저장소 | 운영 기준 SHA | dev SHA | dev 전용 전체 / 비merge 패치 | 운영 전용 전체 | dev의 주요 미반영 묶음 |
|---|---|---|---:|---:|---|
| clipper_web_api | e0e5b356 | 37318b0f | 17 / 16 | 166 | 텔레메트리 서버 인제스트·desktop_sessions/오류 origin migration·보존 스케줄러 |
| clipper_web_admin | cd3a3069 | eae522f4 | 0 / 0 | 41 | 없음; dev는 운영 기준의 조상 |
| clipper_web_client | 4d95a963 | 4b361efc | 0 / 0 | 57 | 없음; dev는 운영 기준의 조상 |
| clipper_electron | a34a39d5 | 3977142c | 69 / 65 | 9 | 텔레메트리 동의·전송기·민감 경로 제거 보완, 저장공간 캐시 삭제 IPC |
| clipper_angular | c8b18677 | 84628f4f | 28 / 24 | 9 | 텔레메트리 동의 UI, 저장공간 화면·자동 정리 설정·보관함 다중 삭제 |
| clipper_nestjs | 780128a0 | 4a22f0b0 | 42 / 39 | 8 | 저장공간 조회·회수·자동 캐시 정리, 로그 민감 경로 제거 보완 |
| clipper_python | 260751d2 | 88b1da27 | 2 / 1 | 0 | TTS 클립 간 공백350ms → 200ms |
| clipper_infra | f948922c | 4d320226 | 0 / 0 | 15 | 없음; dev는 운영 기준의 조상 |

전체 개수는 git rev-list prod...dev의 도달 가능성 기준이며 merge·문서·테스트 커밋도 포함한다. 비merge 패치는 git cherry -v의 + 개수로, 동일 patch-id의 cherry-pick 여부까지 확인했다(모든 저장소 - 항목0). 숫자가 그대로 기능 개수는 아니며 squash·부분 수동 이식의 의미 동등성을 전부 증명한 결과도 아니다. 주요 storage/telemetry/TTS 변경은 변경 파일 목록까지 확인했다.

## 반영 단위와 주의점

- 저장공간 관리: Angular UI + Nest 조회/회수/자동 GC + Electron 캐시 IPC가 함께 변경된 묶음이다. 최근 merge는 각각84628f4f/4a22f0b0/3977142c(9/11).
- 텔레메트리: API 서버 수신(37318b0f), Electron 전송(f943e97), Angular 동의 UI와 Nest/Electron 경로 제거 변경이 연결된다. API에는 새 admin migration2개가 있으므로 앱 변경만의 항목이 아니다.
- Python TTS 공백 변경은8ca1268, dev merge88b1da2(9/10).
- API는 운영 전용166커밋이 별도로 있다. Electron/Angular/Nest도 운영 전용9/9/8커밋이 있으므로 dev checkout을 그대로 운영 소스로 대체하는 방식은 기존 PG·운영 수정 누락 위험이 있다. 운영 기준 위에서 선택 통합할 후보이며 이번에는 통합하지 않았다.
- 이전 CPU·R1~R5·RAM watchdog·UI 누적4repo/50파일은 별도 미커밋 보관본이다. 위 원격 dev 커밋 수에 포함하지 않으며 함께 보존해야 한다.

## 공유 checkout 상태

| 저장소 | 로컬 브랜치 | 로컬 HEAD | 미커밋 경로 수 |
|---|---|---|---:|
| clipper_web_api | integration/toss-payments-pg-20260903 | 06316a41 | 9 |
| clipper_web_admin | integration/toss-payments-pg-20260903 | cafebe37 | 7 |
| clipper_web_client | integration/toss-payments-pg-20260903 | ae75f51a | 10 |
| clipper_electron | integration/toss-payments-pg-20260909 | dd4e9d67 | 0 |
| clipper_angular | integration/toss-payments-pg-20260909 | 7ae7366d | 0 |
| clipper_nestjs | integration/toss-payments-pg-20260909 | 780128a0 | 0 |
| clipper_python | dev | 260751d2 | 0 |
| clipper_infra | integration/toss-payments-pg-20260903 | f948922c | 5 |

로컬 원본 Electron/Angular는 운영용 소스보다 오래되었다. Python 로컬 dev도 원격 dev보다2커밋 뒤다. 웹 M표시의 배포 통합 대조 의미는 [9/10 감사](./2026-09-10-current-state-and-resource-dashboard-audit.md)를 따른다. 이번에는 이 변경들을 다시 적용·삭제하지 않았다.

## 저장소별 원격 기준과 dev 전용 커밋

### clipper_web_api

운영 기준: `release/pg-expiry-20260910` / `e0e5b356017cc55ea2d4f3e19ecd549bb802b5f5`

dev: `37318b0f21f196f88d10bc794482895d0667a80b`

```text
37318b0	2026-09-10T13:13:53+09:00	merge: Phase 1B-1 데스크톱 텔레메트리 서버 인제스트 (feat/telemetry-server-ingest)
2e95d2a	2026-09-10T11:40:18+09:00	docs(telemetry): occurred_at이 행 종류마다 다른 시계임을 엔티티에 명시한다
f3ef049	2026-09-10T11:39:56+09:00	fix(telemetry): 믿을 수 없는 미래 occurredAt은 겉봉투 파손으로 버린다 (시계 오차 48시간)
871257c	2026-09-10T11:39:05+09:00	fix(telemetry): installId를 겉봉투 파싱에서 소문자로 접는다 — 대문자 재전송이 두 번째 행이 되던 것
6dad5e7	2026-09-10T11:37:36+09:00	fix(telemetry): 이 브랜치가 만든 spec의 타입 오류 2건을 고친다 (TS2769)
586030d	2026-09-10T11:36:56+09:00	fix(telemetry): 보존 크론에 timeZone: 'UTC'와 이름을 명시한다
9413a3d	2026-09-10T11:35:54+09:00	feat(telemetry): 버린 봉투를 서버 로그에 남긴다 — 202가 전량 유실을 가리지 못하게
982bee1	2026-09-10T11:32:05+09:00	test(telemetry): 충돌 술어 WHERE **전문**을 못박는다 — AND→OR 뮤테이션이 죽는다
a8917d8	2026-09-10T11:31:08+09:00	fix(telemetry): error_count는 에러/치명 **발생 횟수 합**이다 — 서명 종류 수가 아니다
b7cc708	2026-09-10T11:04:08+09:00	feat(telemetry): 보존 삭제 스케줄러 — 세션 365일·번들 90일, 매일 03:10 UTC (D15)
f567d6e	2026-09-10T10:46:25+09:00	feat(desktop-error-reports): origin 열 — 수동/자동 번들 구분
a4b6fe5	2026-09-10T10:36:49+09:00	test(telemetry): gzip 본문이 실제로 파싱되는지 실HTTP로 증명한다 — 한도는 올리지 않는다
692f46c	2026-09-10T10:30:15+09:00	docs(telemetry): raw SQL 근거를 정정한다 — TypeORM orUpdate는 WHERE를 달 수 있다
b357535	2026-09-10T10:19:53+09:00	fix(telemetry): dedupe 파생 고정 · 빈 startedAt 접기 · 끝을 아는 봉투가 이긴다 · 키 미설정 거부
717f59d	2026-09-10T09:56:35+09:00	feat(telemetry): POST /ingest/desktop-telemetry — 겉봉투만 보고 payload는 그대로 저장한다
eb41399	2026-09-10T09:34:27+09:00	feat(telemetry): 인제스트 키 가드 — 계정 토큰과 분리된 빌드 인증
a83aa9e	2026-09-10T09:25:19+09:00	feat(telemetry): desktop_sessions 테이블 — 승격 열은 필터·정렬 축뿐
```

### clipper_web_admin

운영 기준: `release/pg-expiry-20260910` / `cd3a3069310bdae13f123615e1a1a2a8972187cd`

dev: `eae522f4908c65a55680be09353dd95df2a71190`

```text
(dev 전용 커밋 없음)
```

### clipper_web_client

운영 기준: `integration/toss-payments-pg-20260903` / `4d95a963cde6f4e4067244c6cc8c148bb66709ce`

dev: `4b361efc742db797e85848c5aea90eb1736194c5`

```text
(dev 전용 커밋 없음)
```

### clipper_electron

운영 기준: `integration/toss-payments-pg-20260909` / `a34a39d510bca51bf8b3e527d433ff9112c686fc`

dev: `3977142c9460ee1442205fdac208094098afd5a1`

```text
3977142	2026-09-11T11:04:14+09:00	merge: 설치형 저장공간 관리 — 앱 캐시 삭제 IPC — feat/storage-management
f943e97	2026-09-11T10:08:02+09:00	merge: Phase 1B-2 기기 전송기 — 텔레메트리 전송을 켠다 (feat/telemetry-device-flush)
bdde285	2026-09-10T19:48:53+09:00	fix(telemetry): fix wave 마무리 — 판별자를 모양 기준으로, 틀린 수치 정정, gpu 가드·상한 관계 고정
e4c5dc7	2026-09-10T19:19:56+09:00	docs(telemetry): F7·F11 — 남의 부수효과에 얹힌 방어를 앵커로 못박고, stop() 미호출을 명문화
fcfc583	2026-09-10T19:18:37+09:00	refactor(telemetry): F6 — 도달 불가능한 문자열 수술 경로를 삭제한다
1d4b7cd	2026-09-10T19:17:06+09:00	fix(telemetry): F8 — 기기 인제스트 키 환경변수 이름을 의미로 가른다
61e3caa	2026-09-10T19:15:07+09:00	fix(telemetry): F9 — 손상된 consent.json이 옵트아웃을 되돌리지 않는다(fail-closed)
c4e8683	2026-09-10T19:12:38+09:00	fix(telemetry): F4·F10·F5 — 정직한 격리 회계 + 격리도 10MB 예산 안 + 티어별 장애 독립
539092c	2026-09-10T19:06:48+09:00	fix(telemetry): F3 — 동의를 배치마다 다시 읽는다(flush는 원자적 순간이 아니다)
b6e778a	2026-09-10T19:03:39+09:00	fix(telemetry): F2 — 4xx 기본값을 뒤집는다(지울 것만 열거, 나머지는 남긴다)
8749bae	2026-09-10T19:02:06+09:00	fix(telemetry): F1 — Tier 1 서명 경계 필터(경로 잔해 차단), 레다크터는 그대로
8909f81	2026-09-10T18:21:38+09:00	fix(telemetry): Task 7 review fix round 1 — 거절은 격리·토큰 대기 상한·표식 정정
30ad6ae	2026-09-10T17:51:49+09:00	feat(telemetry): 아웃박스 flush 스케줄러 — 동의 재확인·단일 실행·전송 후 삭제 + 배선
0941838	2026-09-10T17:51:49+09:00	feat(auth): resolveUsableAccessToken — 401 전에 쓸 토큰을 얻는 통로
4656fea	2026-09-10T17:51:49+09:00	feat(telemetry): Tier 2 본문 DTO 매핑 + 전송 전 로컬 검증(Ruling 17 방어층)
6b693ed	2026-09-10T17:28:39+09:00	fix(telemetry): tier2-transport origin 주입 — 문자열 경로 우회 + BOM 가드 (Task 6 review fix round 1)
ccd32e7	2026-09-10T17:17:01+09:00	feat(telemetry): Tier 2(동의 기반 에러 번들) 전송 — sendBundle(POST /ingest/desktop-error-reports)
45e2a36	2026-09-10T17:07:03+09:00	fix(telemetry): Task 5 review fix round 1 — 빈/공백 인제스트 키 방어 + no-auth 주석 정정
faf8541	2026-09-10T17:02:00+09:00	feat(telemetry): Tier 1(익명) 전송 — sendSessions(POST /ingest/desktop-telemetry)
b3ead42	2026-09-10T16:56:15+09:00	fix(telemetry): flush-policy 숫자-문자열 status가 강제형변환으로 자기 행을 건너뛰던 버그 (Task 4 fix round 1)
72d8261	2026-09-10T16:50:48+09:00	feat(telemetry): 전송 결과 → 행동 결정 순수 함수(flush-policy) — 401/403 keep 함정 수정
cf61214	2026-09-10T16:48:30+09:00	fix(telemetry): byWriteOrder가 같은 ms 충돌에서 접미사를 텍스트로 비교하던 버그 (Task 3 fix round 1)
e914a45	2026-09-10T16:36:54+09:00	feat(telemetry): 아웃박스 → flush 배치 순수 함수(planBatches)
5547c01	2026-09-10T16:35:55+09:00	feat(telemetry): 아웃박스에 read/readEntry/listEntries 추가 — 봉투 내용을 읽는 통로
8cad558	2026-09-10T16:28:01+09:00	fix(telemetry): getIngestKey이 실제 I/O 실패에서도 안 던지게 고친다 (Task 2 fix round 1)
c88923e	2026-09-10T16:21:17+09:00	feat(telemetry): 인제스트 키를 빌드에 굽는 접근자 + 허용목록 정책 명문화
1e9da28	2026-09-10T16:00:30+09:00	fix(logging): 슬래시 UNC는 측정으로 접고, 경계 셋을 사실로 못 박는다 (Task 1 fix round 3)
1b932d2	2026-09-10T15:33:22+09:00	fix(logging): 이스케이프 깊이를 레벨이 아니라 구조로 닫는다 (Task 1 fix round 2)
32e4720	2026-09-10T15:01:24+09:00	fix(logging): 이스케이프된 경로·산문 오탐·마커 횡단을 닫는다 (Task 1 fix round 1)
15d2dce	2026-09-10T14:22:09+09:00	fix(logging): 경로 안쪽 공백으로 사람 이름이 새던 것을 닫는다 (Task 1)
b16058a	2026-09-10T08:39:17+09:00	merge: Phase 1B-0 레다크션 경화 (feat/telemetry-redaction-hardening)
1dda575	2026-09-09T23:42:10+09:00	fix(storage): clear Code Cache alongside HTTP cache (Finding 7)
b2299b3	2026-09-09T23:07:05+09:00	docs(telemetry): 재리뷰가 지적한 두 주석 주장을 정정한다
7478a34	2026-09-09T22:39:55+09:00	docs(telemetry): fix wave 보고서 + 원장 기록, .tar.gz 주석 정확화
0fe109a	2026-09-09T22:35:15+09:00	docs(telemetry): 역방향 확장의 반대 방향 두 결과를 문서화 + 병합률 실측 (F7)
5b8c9b3	2026-09-09T22:32:47+09:00	fix(telemetry): 값싼 잔여 3건 — never-throw 구조화·int 대칭·주석 정정 (F6/M3·M4·M5)
172149d	2026-09-09T22:30:10+09:00	perf(telemetry): 서명 정규화의 75배 회귀를 짧은 회로로 되돌린다 + 성능 가드 100ms (F5)
123726d	2026-09-09T22:24:15+09:00	test(logging): 동등성 테스트에 이를 넣는다 — 변이 3종을 각각 잡는 코퍼스 (F4)
f27746d	2026-09-09T22:20:55+09:00	test(logging): 미등록 루트 브리지 불변식을 양 레포 같은 픽스처로 시험한다 (F3)
a44734a	2026-09-09T22:19:31+09:00	fix(logging): 대괄호 든 파일명 꼬리를 가린다 — 배제 하나가 지던 두 불변식을 분리 (F2/A1)
fb95635	2026-09-09T22:15:08+09:00	fix(logging): 파일명 규칙 두 개가 대문자 확장자를 놓쳤다 (F1, Critical)
71c14c7	2026-09-09T21:35:35+09:00	fix(telemetry): Tier 2 system에 memFreeBytes·uptimeSec 추가 (Task 6)
b55cb6e	2026-09-09T21:21:12+09:00	fix(telemetry): 아웃박스 쓰기를 tmp+rename으로 원자화 (Task 5)
207cc1e	2026-09-09T21:09:51+09:00	fix(telemetry): 다단어 파일명·영문 축약형 결함 수정 + 커밋된 성능 가드 (fix round 1)
a8f1da0	2026-09-09T20:53:22+09:00	fix(telemetry): Tier 1 서명에서 파일명·인용 사용자 입력을 지운다 (Task 4)
44d02b9	2026-09-09T20:37:34+09:00	fix(logging): Task 3의 14루트 확장을 되돌리고 /Volumes만 추가 (Ruling 10, fix round 1)
eff6ede	2026-09-09T20:13:52+09:00	fix(logging): POSIX_PATH_TOKEN 접두 목록을 표준 루트로 확장 (Task 3)
2da7b20	2026-09-09T20:01:38+09:00	fix(logging): 꼬리 브리지 폭을 1로 좁히고 대괄호를 차단 — 리뷰가 실증한 과잉 레다크션 수정
ec63f38	2026-09-09T19:44:57+09:00	fix(logging): 공백 든 파일명의 꼬리까지 가린다 — 경로 토큰은 그대로, 마커 뒤만 브리지
fe81e77	2026-09-09T19:29:24+09:00	feat(storage): add app cache clear IPC
d09706b	2026-09-09T19:13:27+09:00	fix(logging): UNC 경로를 가린다 — 로밍 프로필의 사람 이름이 새던 통로
4fb072e	2026-09-09T17:58:14+09:00	merge: 설치형 텔레메트리 Phase 1A — 봉투 조립·아웃박스·계층형 동의 — feat/telemetry-phase1a
29dafdf	2026-09-09T17:56:48+09:00	fix(telemetry): 크래시 봉투 durationSec — 0은 거짓말, null이 모른다 (Ruling 41)
f9df4ce	2026-09-09T15:24:17+09:00	fix(telemetry): 최종 리뷰 fix wave — Tier 2 payload 계약·종료 배선 앵커·테스트 3건
4c430c8	2026-09-09T14:28:45+09:00	feat(telemetry): 동의 IPC 창구 — getConsent/setConsent (T8)
11cf99b	2026-09-09T14:08:28+09:00	feat(telemetry): Tier 2 에러 번들 자동 트리거 (T7)
c1ffe3a	2026-09-09T13:38:59+09:00	fix(telemetry): T6 리뷰 5건 반영 — 배선 한 줄 잠금·게이트 의미·성공시에만 완료·이름표 레다크션
a808d95	2026-09-09T13:18:38+09:00	feat(telemetry): 세션 종료 시 Tier 1 봉투를 아웃박스에 놓는다 (T6 배선)
9591808	2026-09-09T12:55:10+09:00	fix(telemetry): 아웃박스 I/O 실패를 'failed'로 정직하게 알리고 remove()를 테스트한다 (review Finding 1/2)
86f6d75	2026-09-09T12:44:30+09:00	fix(telemetry): 아웃박스 파일명 = 쓰는 시각 + 충돌 접미사 (Ruling 21/22)
63bd7f9	2026-09-09T12:39:08+09:00	feat(telemetry): 아웃박스 — 봉투를 디스크에 store-and-forward로 놓는다
f9e8a8d	2026-09-09T12:27:55+09:00	fix(telemetry): payload 배열 상한 + level 화이트리스트 (review fix 1/5)
21fa2d5	2026-09-09T12:18:46+09:00	feat(telemetry): Tier 1 봉투 조립(envelope + session-summary)
a576ed1	2026-09-09T12:12:01+09:00	fix(telemetry): 플로우/process.exited 줄의 에러서명 이중 계상 제거 (review fix 1/5)
b76ab56	2026-09-09T12:02:38+09:00	fix(telemetry): 에러 서명이 공용 레다크터를 먼저 통과하게 한다 (Ruling 14)
ba6865b	2026-09-09T11:58:06+09:00	feat(telemetry): 세션 카운터 — 플로우/프로세스종료/에러서명 집계
2baaf8e	2026-09-09T11:47:02+09:00	feat(telemetry): 동의 상태 저장소
f49f619	2026-09-09T11:42:46+09:00	fix(telemetry): session-lifecycle end() 재시도 안전망 + stage 판별자 복원
1cb0851	2026-09-09T11:28:42+09:00	refactor(telemetry): 세션 상태기계를 테스트 가능한 모듈로 뺀다
```

### clipper_angular

운영 기준: `integration/toss-payments-pg-20260909` / `c8b186770ae6f77294a2a1689226834f05a8944a`

dev: `84628f4f5615d9e419784b65db51442faa4571c9`

```text
84628f4f	2026-09-11T11:05:52+09:00	merge: 설치형 저장공간 관리 — 저장공간 화면·정리 플로우·보관함 다중삭제 — feat/storage-management
8fe1b87f	2026-09-10T13:55:37+09:00	merge: 텔레메트리 동의 UI 예시 문구 (feat/telemetry-consent-copy)
20fbc27d	2026-09-09T23:50:03+09:00	fix(storage): whole-branch review fixes (findings 1,2,3,9,10,11)
a6e3082e	2026-09-09T23:19:28+09:00	feat(storage): warn about low disk before starting a run
014919cf	2026-09-09T23:01:19+09:00	fix(storage): serialize saveSettings, revert UI on failed save, fix TTS copy
c191430a	2026-09-09T22:41:45+09:00	feat(storage): add auto-clean settings card
cbfdf15e	2026-09-09T22:33:04+09:00	fix(storage): give the banner's reclaim button a visible edge
8e77a618	2026-09-09T22:24:56+09:00	fix(storage): don't let a settings failure hide a successful reclaim
8a58e158	2026-09-09T22:14:45+09:00	feat(storage): warn when disk space runs low
349b1cd5	2026-09-09T22:07:11+09:00	fix(storage): keep failed deletes selected, prune stale grid selection
76805447	2026-09-09T21:53:59+09:00	feat(storage): add multi-select delete to the archive grid
496a8583	2026-09-09T21:38:39+09:00	fix(storage): mark locked entry rows as "사용 중" in the entries dialog
a44de31f	2026-09-09T21:31:17+09:00	fix(storage): use backend reclaimable/locked fields, always reload on entries-dialog close
1449d0e1	2026-09-09T21:08:53+09:00	feat(storage): add reclaim confirm flow and entries dialog
6ff73371	2026-09-09T20:51:34+09:00	test(storage): pin canClean and 0-byte hiding to real invariants
9d2b8083	2026-09-09T20:41:32+09:00	feat(storage): add storage page under settings
93deff80	2026-09-09T20:25:27+09:00	fix(storage): swallow storage load/navigate rejections in settings card
b99a22cd	2026-09-09T20:15:35+09:00	feat(storage): add storage entry card to settings
c9d5461c	2026-09-09T20:08:34+09:00	fix(storage): add TB tier and fix largest-tier rejection logic
6409319d	2026-09-09T20:02:53+09:00	fix(storage): formatBytes boundary rounding, bridge contract canonicalization, test isolation
4491a511	2026-09-09T19:52:14+09:00	feat(storage): add storage store orchestrating server and IPC reclaim
3ca815db	2026-09-09T19:46:09+09:00	fix(storage): add url encoding and comprehensive test coverage
15483c05	2026-09-09T19:40:49+09:00	feat(storage): add angular storage api client
52f40c76	2026-09-09T18:17:31+09:00	feat(telemetry): 동의 UI 예시 문구안 + 모달 토글 접근성 이름 + 죽은 import 제거
5c01c3cb	2026-09-09T17:58:14+09:00	merge: 설치형 텔레메트리 동의 UI — 설정 개인정보·첫 실행 모달 — feat/telemetry-phase1a
85250aae	2026-09-09T10:56:31+09:00	feat(storage): assemble usage snapshot with disk free and cache
b669b298	2026-09-09T15:24:31+09:00	fix(telemetry): 최종 리뷰 fix wave — 동의 모달은 로그인 뒤에·IPC reject로 굳지 않게
0a3a7653	2026-09-09T14:41:59+09:00	feat(telemetry): 동의 UI — 설정→개인정보 + 첫 실행 모달 (T8)
```

### clipper_nestjs

운영 기준: `integration/toss-payments-pg-20260909` / `780128a069c38a9df6438cc64d79f7a2e42bc1ea`

dev: `4a22f0b09350691eb93fd332312d4e4ba578fa72`

```text
4a22f0b	2026-09-11T11:03:34+09:00	merge: 설치형 저장공간 관리 — 사용량 가시화·캐시 자동 회수·보관함 삭제 — feat/storage-management
2e230d7	2026-09-11T10:08:21+09:00	merge: Phase 1B-2 레다크션 락스텝 (feat/telemetry-device-flush)
23d8911	2026-09-10T16:00:44+09:00	fix(logging): 슬래시 UNC는 측정으로 접고, 경계 셋을 사실로 못 박는다 — electron 락스텝 (Task 1 fix round 3)
72dfde5	2026-09-10T15:33:37+09:00	fix(logging): 이스케이프 깊이를 레벨이 아니라 구조로 닫는다 — electron 락스텝 (Task 1 fix round 2)
e12340a	2026-09-10T15:01:38+09:00	fix(logging): 이스케이프된 경로·산문 오탐·마커 횡단을 닫는다 — electron 락스텝 (Task 1 fix round 1)
891699e	2026-09-10T14:22:21+09:00	fix(logging): 경로 안쪽 공백으로 사람 이름이 새던 것을 닫는다 — electron 락스텝 (Task 1)
ae63200	2026-09-10T08:39:33+09:00	merge: Phase 1B-0 레다크션 경화 락스텝 (feat/telemetry-redaction-hardening)
1c5590e	2026-09-09T23:41:05+09:00	fix(storage): whole-branch review fixes (findings 4,6,8,9,10,11)
b556740	2026-09-09T23:07:05+09:00	docs(logging): .tar.gz 미추가의 근거를 실측으로 바꾼다 — electron 락스텝
d830e2e	2026-09-09T22:40:03+09:00	docs(logging): FILE_EXT 주석의 .tar.gz 설명을 정확히 고친다 — electron 락스텝
bcdc1d8	2026-09-09T22:32:56+09:00	docs(logging): 동등성 baseline 갱신 예시가 어느 규칙 때문인지 못 박는다 (F6/M3)
6726af9	2026-09-09T22:24:23+09:00	test(logging): 동등성 테스트에 이를 넣는다 — 변이 3종을 각각 잡는 코퍼스 (F4)
4fe36f7	2026-09-09T22:21:07+09:00	test(logging): 미등록 루트 브리지 불변식 픽스처를 추가한다 — 이 레포에는 0이었다 (F3)
2ecaac9	2026-09-09T22:19:39+09:00	fix(logging): 대괄호 든 파일명 꼬리를 가린다 (F2/A1) — electron 락스텝
54b9c06	2026-09-09T22:15:17+09:00	fix(logging): 파일명 꼬리 규칙이 대문자 확장자를 놓쳤다 (F1, Critical) — electron 락스텝
b91e308	2026-09-09T21:21:26+09:00	feat(storage): report lock state in entries() API
4baec7e	2026-09-09T21:13:48+09:00	storage: add reclaimable field to CategoryUsage
863dfa3	2026-09-09T20:53:33+09:00	chore(logging): FILE_EXT를 export한다 — electron Task 4가 재사용 (Ruling 12)
cc7055b	2026-09-09T20:37:57+09:00	fix(logging): Task 3의 14루트 확장을 되돌리고 /Volumes만 추가 (Ruling 10, fix round 1)
651f06c	2026-09-09T20:14:02+09:00	fix(logging): POSIX_PATH_TOKEN 접두 목록을 표준 루트로 확장 (Task 3)
089feb6	2026-09-09T20:01:52+09:00	fix(logging): 꼬리 브리지 폭을 1로 좁히고 대괄호를 차단 — 리뷰가 실증한 과잉 레다크션 수정
4ffe9a0	2026-09-09T19:45:09+09:00	fix(logging): 공백 든 파일명의 꼬리까지 가린다 — 경로 토큰은 그대로, 마커 뒤만 브리지
66dea84	2026-09-09T19:36:55+09:00	storage: narrow app_cache to only what clearCache() frees
8998b5f	2026-09-09T19:23:16+09:00	fix(storage): containment-aware lock checks, explicit category allowlist, and reclaim body validation
f916167	2026-09-09T19:13:32+09:00	fix(logging): UNC 경로를 가린다 — 로밍 프로필의 사람 이름이 새던 통로
230c92d	2026-09-09T19:13:26+09:00	feat(storage): add reclaim, entries and settings routes
87f3bca	2026-09-09T19:00:11+09:00	fix(storage): restore tts/cache skip and commit skip-scope regression test
33c3ec2	2026-09-09T18:53:13+09:00	fix(storage): close orphan-sweep false-positive gaps from review
e094432	2026-09-09T18:39:23+09:00	feat(storage): sweep orphan and legacy directories
fc5e6f6	2026-09-09T18:24:25+09:00	feat(storage): run cache GC at write time for sources and tts
b36d91c	2026-09-09T18:13:00+09:00	fix(storage): wrap sizing/planning in error handling; add rm failure test
4c5b5e0	2026-09-09T18:07:47+09:00	feat(storage): add write-time cache GC
1cec9b3	2026-09-09T18:00:39+09:00	feat(storage): expose usage snapshot endpoints
e5ce247	2026-09-09T17:54:26+09:00	test(storage): improve legacyRoots() test to verify normalization fix
bbb7cce	2026-09-09T17:47:44+09:00	feat(storage): assemble usage snapshot with disk free and cache
e8ad826	2026-09-09T17:32:00+09:00	test(storage): add symlink guard coverage in childrenOf
45e583f	2026-09-09T17:28:05+09:00	feat(storage): add symlink-safe directory sizer
2fe5a43	2026-09-09T17:25:58+09:00	fix(storage): use atomic writes for settings persistence
9faa851	2026-09-09T17:21:52+09:00	feat(storage): add retention settings with safe defaults
694c681	2026-09-09T17:18:54+09:00	fix(storage): exclude out-of-root bytes from total, add separator guard tests
e5baaa4	2026-09-09T17:13:34+09:00	feat(storage): add LRU eviction planner with path/lock invariants
0b61dc2	2026-09-09T17:08:49+09:00	feat(storage): add path-to-category classification
```

### clipper_python

운영 기준: `integration/toss-payments-pg-20260909` / `260751d2fa5be8a5a9cd8e346c60ba22d1512ed9`

dev: `88b1da277922cc5734a3e72e32425aa4054fa158`

```text
88b1da2	2026-09-10T16:09:41+09:00	merge: TTS 클립 간 공백 200ms — fix/tts-gap-200
8ca1268	2026-09-10T15:44:52+09:00	fix(tts): 클립 간 공백 350ms → 200ms
```

### clipper_infra

운영 기준: `integration/toss-payments-pg-20260903` / `f948922c812ab583a84e4a64c5d8faa423afe294`

dev: `4d3202263d84de9d046a1abc6eb51826a47009ae`

```text
(dev 전용 커밋 없음)
```
