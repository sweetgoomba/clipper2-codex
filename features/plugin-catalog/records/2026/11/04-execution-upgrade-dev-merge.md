# 플러그인 실행 요금제 제한·업그레이드 dev 병합

- 완료 시각: 2026-11-04T08:52:21+09:00
- 사용자 지시: “데브 병합 해”. 앞선 병합 보류를 이 지시로 해제했다.
- 구현 전 별도 세션 독립 검증, 구현·검사, 구현 후 새 별도 세션 독립 검증 및 P2 수정 재검증을 모두 완료한 최종 코드다.
- 최신 원격 dev를 fetch해 각 기능 브랜치를 커밋한 뒤 네 저장소의 로컬 dev에 no-ff 병합했다. 충돌은 없었다. 웹 API와 웹 클라이언트에 먼저 반영된 환불 활성화 커밋도 보존했다.
- 병합 결과 검증 후 네 저장소 모두 일반 git push origin dev로 반영했다. force push는 사용하지 않았다.
- git ls-remote로 실제 원격 dev가 아래 병합 커밋과 일치함을 확인했다. 각 로컬 HEAD 및 origin/dev도 동일하며 네 코드 저장소의 작업 트리는 깨끗하다.

| 저장소 | 기능 커밋 | dev 병합·원격 확인 커밋 |
| --- | --- | --- |
| web/clipper_web_api | `62290cc8eaa38353df002c04e2316fec7326dd19` | `7922d0502c0b66f2a94212052ace2e4800bc3a5c` |
| web/clipper_web_client | `c219ac518c69bfe04dd329b4d80a259b82ecaece` | `ea1b98524ba83015afdbb897e1c6b2f28cd14654` |
| desktop/clipper_nestjs | `629843501442b540021f3f1fb043bfbf5eade6ed` | `cbc1cadafc10604f5e25e3ed6797cdde30bed7f1` |
| desktop/clipper_angular | `ae0fac802a8796ba929a0d125e247208e882ce6c` | `444dcf642f0ea1ccebecac6bb33484c15dc12018` |

## 병합 결과 검증

- 웹 API: 전체 485 스위트/5,326 테스트 및 5 스냅샷 통과. 기존 16 스위트/175 테스트 skip. 빌드 통과.
- 로컬 서버: 지정 Node 24.19.0, CLIPPER_AUTH_MODE=local에서 전체 5,401 테스트 통과(실패·취소 0). 빌드 통과.
- 웹 클라이언트: 전체 663 테스트와 빌드 통과. 빌드 예산 경고는 514.91 kB / 500 kB로 14.91 kB 초과다.
- 앱: 전체 단일 실행 두 번은 각각 기존 TemplateBuilderEditorComponent 비동기 업로드 검사 1건, StoreComponent 카드 위치 3px 단언 1건 실패(각각 10,768 통과). 이전 구현 검사에서도 관측된 간헐 실패이며 이 이력을 보존한다. 원인을 완전히 규명했다고 주장하지 않는다.
- 앱 검사는 소스 수정 없이 3개 실행으로 나누어 모든 10,769 테스트를 검증했다: TemplateBuilderEditorComponent 195/195, StoreComponent 81/81, 두 파일 외 나머지 10,493/10,493 통과. 스토어 소스·템플릿·스타일·테스트가 기존 dev와 동일한 것도 확인했다. 테스트를 삭제하거나 skip으로 바꾸지 않았다. 스타일 검사 21개와 앱 빌드도 통과했다.
- 합계: 22,159개 테스트 통과(앱은 위 분리 실행 합산). 스타일 21개 및 API 스냅샷 5개는 별도. 네 저장소 diff 공백 검사와 기존 dev/기능 커밋의 병합 조상 관계도 확인했다.
- 로컬 서버 최초 실행은 지정 버전과 다른 Node 22로 실행해 44개가 취소됐다(단언 실패 0). 지정 Node 24에서 해당 62개와 전체 5,401개가 통과했으며 환경 파일이나 제품 코드는 바꾸지 않았다.
- 앱 단독 검사 준비 중 한 실행은 테스트 시작 전 프로세스가 비정상 종료(exit 134)됐다. 동일 검사를 승인된 실행 환경에서 실행해 통과했다.
- 실제 PG 결제·운영 회원 데이터 변경·외부 생성 호출·배포 완료 검증은 이 병합 작업 범위에서 수행하지 않았다.

## 증거와 관련 기록

- [구현 및 검사 결과](04-execution-upgrade-result.md)
- [새 별도 세션의 구현 후 독립 검증과 P2 수정 재검증](04-execution-upgrade-final-independent-review.md)
- /tmp/adlight-plugin-dev-merge-manifest.json
- /tmp/adlight-plugin-dev-merge-pushed.json
- /tmp/adlight-plugin-dev-api-tests.log, /tmp/adlight-plugin-dev-api-build.log
- /tmp/adlight-plugin-dev-local-node24-tests.log, /tmp/adlight-plugin-dev-local-node24-build.log
- /tmp/adlight-plugin-dev-web-tests.log, /tmp/adlight-plugin-dev-web-build.log
- /tmp/adlight-plugin-dev-desktop-tests.log, /tmp/adlight-plugin-dev-desktop-retry-tests.log
- /tmp/adlight-plugin-dev-desktop-template-isolated-unsandboxed.log
- /tmp/adlight-plugin-dev-desktop-store-isolated.log
- /tmp/adlight-plugin-dev-desktop-partition-tests.log
- /tmp/adlight-plugin-dev-desktop-styles.log, /tmp/adlight-plugin-dev-desktop-build.log

문서 저장소의 다른 세션 변경은 커밋·push하지 않았다. 이전 결과 기록의 미커밋·병합 보류 상태는 그 시점의 이력이며, 현재 상태는 이 병합 기록이 대체한다.
