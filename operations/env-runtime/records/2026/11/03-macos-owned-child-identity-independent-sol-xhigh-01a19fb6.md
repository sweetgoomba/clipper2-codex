# W20 macOS owned child identity 독립 검증 — Sol xhigh

2026-11-03 KST · 검증 채팅 `01a19fb6-4a3d-7592-9d3a-02c1a8404dfb` · 원래 채팅 `01a19dcf-acaf-7371-9d72-58b3fce5f985`.

## 결론

W20 제품 수정에서 병합을 막을 기능·소유권 보호 회귀는 발견하지 못했다. 환경을 포함한 전체 문자열 해시를 시작 시각·명령 해시와 환경 suffix의 owner 확인으로 분리하는 변경은 제어 회귀에서 기존 오류를 제거하며, 최신 원격 dev 합성본의 빌드·전체 시험도 독립적으로 통과했다.

다만 **최초 자연 발생한 집중 시험 1회 실패의 단일 원인은 확정하지 못했다.** 원래 파일은 계측 100회와 비계측 100회 모두 통과했다. 현재 `waitForStoredIdentity`는 이미 null로 완료한 조회와 아직 진행 중인 조회를 같은 1초 assertion으로 표시한다. 두 경우 모두 똑같은 실패를 고장 주입으로 재현했다. 따라서 최초 실패를 단순 지연, 권한 문제, 또는 제품 identity 변경이라고 단정할 근거는 없다.

후속 수정은 **회귀 fixture의 응답 순서를 지정하고 `track()` 직후 `shutdown()`을 호출하여 제품의 기존 `identityReady` 대기를 사용하는 방식**을 권고한다. 1초 폴링을 제거하고 조회 null은 제품의 명시적 오류로 드러내면 된다. 제품의 안전 검사 완화나 조회 retry는 권고하지 않는다. 이 fixture 후보는 별도 진단본에서 red/green, 지연, null 분류를 검증했다. 최종 W20 수정은 원래 채팅이 수행한다.

## 대상·보존·실행 환경

- 공유 W20 경로: `/Users/jina/project/adlight/.worktrees/macos-owned-child-identity-20261103/desktop/clipper_nestjs`.
- 브랜치 `fix/macos-owned-child-identity-20261103`, HEAD `7f57ff1b2e6807376b2cb5c4393a6efdcf056f6b`.
- 검증 대상 미커밋 diff SHA-256: `de2fa4396fab56a6fe0f14995dc05923bf22ae71e3bc360d4fa2a9c24ebe5e74`.
- 시작·종료 시 `git ls-remote origin refs/heads/dev`로 `f2cc17a9c6a73fa7096c602e8fc68df4403aeacc`를 확인했다. 원격 dev의 추가 변경은 접근 권한·프로모션 관련 다른 다섯 파일이다.
- 진단 루트: `/private/tmp/w20-independent-20261103-28u4xx2x`. 그 아래 `desktop/clipper_nestjs`에 최신 dev를 `git archive`로 복제하고 diff를 `git apply --check` 후 적용했다. 공유 Git worktree 등록·checkout·커밋·push·원격 병합은 하지 않았다.
- Node `/Users/jina/.nvm/versions/node/v24.19.0/bin/node`, PATH `/Users/jina/.nvm/versions/node/v24.19.0/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin`. `/opt/homebrew/bin/ffmpeg` 포함.
- 원본 `node_modules`, `.env.packaged`, `desktop/clipper_python/fonts`는 임시 복제본에서 읽기용 심볼릭 링크로 참조했다. 원본 자산과 W19 여섯 저장소는 수정하지 않았다.
- 종료 검사는 시험이 만든 child에만 수행했다. 환경 원문·owner token 값은 로그나 문서에 출력하지 않았다. 계측은 boolean·길이·hash·exit/error code만 기록했다.
- 독립 반복·전체 시험 종료 뒤 중간 보존 확인에서 공유 W20 diff hash가 처음과 같고 `git diff --check`가 통과했다. 최종 보고 작성 중 다시 읽었을 때 제품 소스는 같은 blob `8eff57e5`였으나, 공유 시험이 순차 응답 mock으로 외부 변경된 것을 관측했다(그 시점 전체 diff hash `54f3710cf2abf7be37dcdd4ad5a39616f268b3b0942df376bd2d45c1d34fa05d`). 이 검증은 공유 파일에 쓰지 않았다. 아래 전체·반복 수치는 검증 시작 diff `de2fa439…`에 한정하며 새 공유 시험의 최종 검증은 원래 채팅이 수행한다.

## 독립 검증 수치

| 검증 | 결과 | 근거 파일(진단 루트 기준) |
|---|---|---|
| 최신 dev에 미커밋 diff 적용 검사 | 통과 | `candidate.patch` |
| `npm run build` | exit 0 | `build.log` |
| `node --test test/*.test.js` | 5,295개, 5,287 통과·8 skip·0 fail·0 cancelled | `full.log` |
| 원래 대상 파일, 계측 100회 | 100/100 파일, 총 1,000개 통과 | `audit-{1..100}.log`, `.jsonl` |
| 원래 대상 파일, 비계측 100회 | 100/100 파일, 총 1,000개 통과 | `baseline-{1..100}.log` |
| 위 반복의 실제 POSIX parent/descendant 종료 | 200/200 통과 | 각 대상 파일 로그 |
| 추가 제어 시험 | 15/15 통과, Windows 분기 4개 포함 | `controlled.test.cjs`, `controlled.log` |
| 기존 제품 모듈 + 신규 transient 회귀 | 예상한 `Refusing SIGTERM ... identity changed`로 1/1 실패(red) | `old-regression.test.cjs`, `red.log` |
| 순차 응답 fixture 후보 + 수정 제품 | 기존 파일 전체 10/10 통과 | `ordered.test.cjs`, `ordered-all.log` |
| 순차 응답 fixture 후보 + 기존 제품 | 같은 identity changed로 실패(red) | `ordered-old.test.cjs`, `ordered-red.log` |
| 순차 fixture 첫 callback에 1,100ms 지연 | 통과(약 1,108ms) | `ordered-delayed.log` |
| 순차 fixture 첫 조회 EACCES 주입 | 약 2ms에 identity unavailable로 예상 실패 | `ordered-null.log` |

의도적으로 고장을 주입한 red/null/timeout 실행의 실패는 제품 전체 회귀 실패 수치에 섞지 않았다. 계측 집계 `audit-summary.json`: ps callback 3,000건, 첫 기존 시험의 가상 PID 조회 실패 100건 외 오류 0건, prefix 불일치 0건. 첫 기존 시험은 가상 PID를 track한 뒤 바로 exit시키므로 해당 null은 새 회귀의 실패가 아니다.

## 최초 자연 실패에서 확정할 수 있는 것

원래 채팅의 도구 출력에서 최초 실패를 다시 읽어 `/private/tmp/w20-independent-20261103-28u4xx2x/recovered-initial-failure.log`로 보존했다. 해당 command id는 `exec-8ccbfc48-2643-4a75-9b72-808f58891880`이다.

- transient 회귀만 약 1,005.6ms 뒤 `owned child identity was not captured` assertion으로 실패했다.
- 같은 파일의 birth/command/owner 거절 및 실제 child tree 시험은 통과했고 총 9/10이었다.
- 그 실행은 합성본 build 뒤였고, 다음 단독·반복 실행 및 전체 실행은 통과했다.
- 당시 ps spawn 오류 코드, stdout 길이, owner/prefix boolean, `identityReady` 완료 여부는 기록되지 않았다. 따라서 로그만으로 nullable identity/실행 지연/단일 spawn 오류/출력 불일치를 구별할 수 없다. 실제 child tree 통과는 광범위한 ps 권한 부재와 맞지 않지만, 개별 조회의 일시적 실패를 배제하지는 않는다.

현재 소스 `track`은 identity를 한 번만 읽어 저장한다. 조회가 null로 완료하면 `identityReady`는 이미 해결되었고 이후 manifest 폴링은 조회를 다시 하지 않는다. 이 경우 timeout을 늘려도 회복되지 않는다. 반대로 아직 진행 중인 조회가 1초를 넘으면 정상 결과가 나올 수 있어도 fixture가 먼저 실패한다.

이를 구분하기 위해 원래 시험에 다음 **인위적 고장**을 각각 주입했다. 이는 최초 자연 실패의 원인을 확정한 재현이 아니다.

| 고장 주입 | 1초 시점의 계측 | 원래 시험 결과 |
|---|---|---|
| 첫 환경 조회 callback에 EACCES | 약 10ms에 완료, identity 없음 | 약 1,006ms에 같은 assertion |
| 첫 성공 환경 조회 callback을 1,100ms 늦게 전달 | identityReady 진행 중, identity 없음 | 약 1,009ms에 같은 assertion |

근거: `fault-null.log`, `fault-null.jsonl`, `fault-delay.log`, `fault-delay.jsonl`, `fault-preload.cjs`. 지연 실험에서는 assertion 이후 fixture가 정리된 뒤 늦은 callback이 도착했고, 후속 stable 조회도 null이 됐다. 이는 실패 후 정리가 최초 원인 분석을 흐릴 수 있음을 보여준다.

계측한 성공 ps 호출의 최대 wall duration은 약 887ms였다. 여기에는 동기 spawn 비용도 포함되므로 이 수치만으로 1초 polling 실패의 원인을 설명할 수 없다. 현재 관측에서 eww/stable의 권한·spawn 실패나 prefix mismatch가 새 회귀에 발생했다는 증거는 없다. 실제로 어떤 개별 명령이 일시 실패했을 가능성과 과거 실행 지연 가능성은 모두 가설로 남긴다.

## 원래 제품 원인과 안전성 검토

기존 모듈에 transient 환경 suffix 제거를 입력하면 identity가 바뀌고 종료가 거절된다. 수정 모듈은 같은 입력에서 동일한 시작 시각·명령 해시를 유지한다. 이 red/green으로 환경 전체 해시가 해당 오인의 원인이 되는 것은 독립 확인했다.

다만 이번 macOS의 별도 live probe 두 종류(각 20개, 총 40개 자체 child)에서는 환경 변화나 기존/수정 identity 변화가 자연 재발하지 않았다. `real-probe.json`, `immediate-probe.json`에 hash/boolean만 보존했다. 따라서 이전 조사에서 관측한 macOS transient launch 필드 소실 자체를 이번 live 실행에서 다시 관측했다고 주장하지 않는다.

제어 시험과 소스 검토에서 다음을 확인했다.

- `ps eww`는 owner를 확인하고 `ps -ww`의 `lstart+command`만 해시한다. 환경 출력과 stable 출력의 앞부분이 다르면 null로 거절한다.
- 명령 인자에만 owner 문자열이 있고 환경 suffix에는 없으면 거절한다. owner 변경, 출생/명령 변경, 비정상 PID, 빈 stable 출력, 두 ps 중 어느 쪽의 실패도 거절한다.
- 최초 identity unavailable은 manifest에 null을 남기고 signal을 보내지 않는다. TERM 후 KILL 전에 다시 identity를 읽고, 바뀌면 manifest를 보존하며 거절하는 기존 시험도 통과했다.
- POSIX descendant는 owner와 identity를 포착하고 각 signal 직전에 재확인한다. foreign-owner descendant를 제외하고 child-first로 signal을 보낸다. descendant 교체도 signal 전에 거절했다.
- Windows 코드는 변경하지 않았다. 제어 VM에서 StartTime ticks 조회, TERM/KILL의 taskkill `/F` 차이, descendant 우선 순서, `/T` 미사용, root 교체 시 tree 전체 fence를 확인했다. 어떤 Windows 명령도 실제로 실행하지 않았다.
- `lstart`의 초 단위 정밀도와 같은 owner·명령·초·PID 조합을 구별하지 못하는 극단적인 한계는 남는다. 이번 변경이 이 기존 보장의 정밀도를 높인다는 주장은 하지 않는다.

## 원래 채팅에 권고하는 후속 변경

1. **1초 manifest 폴링 제거.** fixture가 첫 identity 조회 쌍에는 transient 포함 환경과 원래 stable 값을, 이후 쌍에는 transient 제거 또는 birth/command/owner 변경 값을 반환하게 한다. `track` 직후 `shutdown`을 호출해 실제 제품의 `identityReady` 대기를 통과시킨다. `shutdown`이 이 대기를 하지 않으면 회귀가 실패하도록 순서를 유지한다.
2. 응답 순서는 한 테스트의 가상 PID와 조회 종류(eww/stable)에 한정한다. 첫 조회의 값은 snapshot으로 보관하여 다음 값을 바꿔도 진행 중인 첫 stable 조회가 섞이지 않게 한다. 외부 프로세스나 실제 child tree 조회가 fixture를 소비하지 않도록 한다.
3. 더 단순한 fixture로는 `t.mock.method(require('node:child_process'), 'execFile', ...)`의 비동기 callback stub을 권고한다. 이 방식은 ps 옵션·owner/prefix/hash 로직을 실제 제품 경로로 검증하면서, 임시 실행 파일·PATH 교체·chmod·파일 polling을 없앤다. 원래 실제 POSIX child tree 통합 시험은 real ps와 real child 그대로 유지한다. 제품에 테스트 전용 API를 추가할 필요가 없다.
4. shell PATH fixture를 유지해도 순차 출력 + `shutdown` 대기는 유효하다. 단, 네이티브 실행·파일·권한 실패 가능성은 그대로이므로 null을 retry/timeout 증가로 감추지 않고 `identity unavailable`로 드러내야 한다. global 호출 횟수만으로 순서를 정하면 다른 PID/조회가 끼어들 수 있어 위 2번의 범위 제한이 필요하다.
5. 현재 회귀에 없는 환경/stable prefix mismatch와 command 안의 owner spoof 거절, 초기 조회 null의 무신호·manifest 보존을 작게 추가하면 새 보호 조건을 직접 고정할 수 있다. 진단본 제어 시험에서는 이미 통과했다.

임시 `ordered.test.cjs`는 이 권고의 실행 가능한 증거이며 최종 패치가 아니다. 지연·오류 주입용 `W20_ORDERED_*` 설정은 진단 전용이므로 제품 회귀에 복사할 필요가 없다. 첫 eww·stable 결과를 일관된 초기 snapshot으로 주고 다음 조회에 변경값을 쓰면 수정 전 모듈에서도 올바른 red가 유지된다. 이 점에서 시작 준비 대기나 retry로 원래 제품 race를 숨기는 변경과 다르다.

원래 채팅이 적용을 검토할 수 있도록 진단용 fault 설정과 불필요한 import를 제거한 시험 파일 `/private/tmp/w20-independent-20261103-28u4xx2x/recommended-owned-child-process-registry.test.js` 및 **검증 시작 시점 W20 시험 파일 위에 적용하는 패치** `/private/tmp/w20-independent-20261103-28u4xx2x/recommended-ordered-fixture.patch`를 남겼다. 패치 SHA-256은 `56ffa02c7daa2b02230228feaa488d1e5ff91ef62b9b6f79bc7eba433d582c1e`이다. `node --check`와 시작본 대상 `git apply --check`가 통과했다. 정리된 패치를 일회용 복제본에만 적용한 최종 대상 시험도 10/10 통과했다(`recommended-fixture.log`). 이 패치는 이 검증에서 공유 W20 파일에 적용하지 않았다. 이미 순차 fixture로 바뀐 최신 공유 파일에는 중복 적용하지 말고 구현 참고용으로 사용한다.

## 병합 판단과 제약

현재 제품 diff는 최신 dev에 충돌 없이 적용되며 독립 전체 회귀도 통과했다. **제품 수정은 타당하다고 판단하지만, 최초 간헐 실패의 자연 원인이 해소됐다는 무조건적인 완료 선언은 지지하지 않는다.** 원래 채팅이 위 fixture 동기화를 적용하고 새 diff 기준 build·집중 회귀·전체 회귀·최신 dev 적용 검사를 재확인한 뒤 병합 준비를 판단하는 것이 적절하다.

이 세션에 제공된 실행 host는 local Darwin뿐이며, 로컬 `pwsh`/`powershell`/`wine`/`qemu-system-x86_64`와 확인한 SSH 구성에서 Windows 시험 연결을 찾지 못했다. Windows 실기 종료·CIM·PowerShell·taskkill의 실제 동작은 미검증이다. Linux도 제어 분기만 확인했으며 실기 검증으로 세지 않는다. Windows 실기 미검증은 POSIX 전용 수정의 정적·제어 검증과 구분해 기록한다.

공유 W20 소스, 공유 카드, WORKBOARD는 이 검증에서 수정하지 않았다. 진단 루트는 원래 채팅의 후속 검토를 위해 보존했으며 실행 중인 자체 child는 남기지 않았다.
