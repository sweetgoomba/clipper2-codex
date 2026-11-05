# 원본 Web Client/Admin 재시작과 별도 환경 확인

2026-11-04 KST. 사용자 지정 4201/4202만 대상으로 재시작했다. 4241/4242는 조사만 했으며 종료하지 않았다.

## 원본 환경

- 4201은 시작 전 listener가 없었다. 원본 `/Users/jina/project/adlight/web/clipper_web_client`에서 Node24.19로 `npm start` 실행. npm PID97993, Angular listener PID98035.
- 4202는 원본 Admin의 기존 Angular PID17622와 npm parent17607을 SIGTERM으로 종료한 후 `/Users/jina/project/adlight/web/clipper_web_admin`에서 `npm start` 실행. npm PID97994, Angular listener PID98036.
- 두 서버 모두 Angular 초기 번들 완료, watch mode, HTTP200 확인. 기본 serve configuration은 local이며 API는 localhost:3000, useMocks=false.
- 소스·공유 설정은 수정하지 않았고 두 저장소 Git status는 비어 있다.
- 로그: `/tmp/adlight-original-web-20261104/client.log`, `admin.log`.

## 4241/4242는 무엇인가

별도 `signup-promotion-plugin-access-20261028` worktree의 프로모션/회원가입/플러그인 접근 테스트 환경이다. 원본 dev 환경과 분리돼 있다.

실행 위치: `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/.local-runtime/promotion-signup-20261102`

- Python PID60587, 2026-11-02 14:15:10 KST 시작. `serve-web.py` 하나가127.0.0.1:4241(client)과4242(admin)를 함께 listen한다.
- `serve-web.py`는 해당 runtime의 client/admin 정적 빌드 복사본을 제공한다. ng serve/HMR 서버가 아니다.
- 원본 코드를 저장하면 자동 갱신되는 환경이 아니다. 이전 빌드 결과를 따로 복사해 사용하며 API 대상은4340이다.
- 관리 스크립트는 같은 위치의 `manage.py`. 해당 스크립트의 stop은 API4340도 대상으로 하므로 웹만 정리하려고 무작정 전체 stop을 실행하면 안 된다.
- 실제 HTTP200과 API4340 health 및 DB3개 ok를 확인했다. DB15438·별도 local-profile 앱 구성은 기존 운영 기록에서 확인했다.
- 해당 환경은 이전 사용자 요청에 따라 계속 실행해 두기로 기록돼 있다. 원본 최신 dev의4201/4202와 이번 Mac 앱(API3000) 확인에는 필요하지 않다.

별도 프로모션 테스트를 더 사용하지 않는다면 웹 프로세스60587만 정상 종료해4241/4242를 비울 수 있다. 한 프로세스이므로 두 웹이 함께 내려간다. 웹 종료 자체는 소스·빌드·DB·기존 테스트 데이터를 삭제하지 않는다. DB·worktree·앱 데이터 삭제까지 묶어 정리할 근거는 없다. 이번 사용자는 종료 여부 확인만 요청했으므로4241/4242와API4340/DB는 그대로 유지했다.

현재 runtime의 단순 PID만으로 실제 사용자가 테스트 중인지까지 확정하지는 않는다. 이전 구성과 유지 의도는 `02-promotion-branch-isolated-local-runtime.md` 및 `README.md`에서 확인했다.

검증 시각: 03:47:17 KST. 같은 이름 JSON에 재시작 대상과 HTTP·health 확인 결과를 남겼다.
