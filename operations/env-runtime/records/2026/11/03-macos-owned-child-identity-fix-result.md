# W20 macOS owned child identity 수정 결과

2026-11-03 KST · 세션 `01a19dcf-acaf-7371-9d72-58b3fce5f985`.

## 원인과 수정

원격 `dev`의 `7f57ff1b`에서 독립 브랜치 `fix/macos-owned-child-identity-20261103`와 격리 작업 공간 `/Users/jina/project/adlight/.worktrees/macos-owned-child-identity-20261103/desktop/clipper_nestjs`를 만들었다. 원본 저장소와 W19 작업 공간은 수정하지 않았다.

기존 실제 child tree 테스트는 `Refusing SIGTERM: owned child … identity changed`로 재현됐다. `readOwnedChildIdentity`가 macOS `ps eww -o lstart=,command=` 전체를 해시하므로, 시작 직후 사라지는 임시 환경 필드만으로 같은 PID·출생·명령의 해시가 달라진다. 자체 생성한 일회용 child에서 환경 포함 출력은 환경 제외 출력의 시작 시각·명령을 앞부분에 유지하는 것을 원문 출력 없이 확인했다.

POSIX child identity는 이제 `ps eww`의 환경 부분에서 owner token을 확인하고, `ps -ww -o lstart=,command=`의 시작 시각·명령만 해시한다. 두 조회의 시작 시각·명령이 일치하지 않거나 token이 없으면 identity를 반환하지 않는다. 따라서 저장 identity 재검사, descendant별 검사, TERM→KILL 및 manifest 흐름은 그대로 적용된다. Windows 분기는 바꾸지 않았다.

## 회귀와 검증

- 제어된 `ps` 응답에서 임시 환경 필드 제거 시 정상 종료 회귀는 수정 전 기대한 `identity changed`로 실패했고 수정 후 통과했다. 출생·명령·owner token 변경 거절도 통과했다.
- Node `/Users/jina/.nvm/versions/node/v24.19.0/bin/node`로 대상 테스트 **10/10 통과**. 실제 POSIX parent/descendant 종료 테스트를 별도 **10회 반복 통과**했다.
- `npm run build` 통과. 전체 `node --test test/*.test.js`는 **5,291개 중 5,283 통과·8 건너뜀·실패 0**. 정상 PATH에 `/opt/homebrew/bin/ffmpeg`를 유지했다.
- 최초 격리 checkout의 전체 실행은 폰트와 `.env.packaged` 자산 누락으로 14개 실패했다. 원본의 `clipper_python/fonts`와 `clipper_nestjs/.env.packaged`를 가리키는 심볼릭 링크를 격리 공간에 만들고 다시 빌드·전체 실행해 위 결과를 얻었다. 제품 소스나 원본 자산을 바꾸지 않았다.
- `git diff --check` 통과. 변경은 registry 소스 한 파일과 회귀 테스트 한 파일뿐이다. 검토에서 PID/출생/명령/owner 거절 경로, tree 재확인, manifest와 Windows 분기의 변경 범위를 대조했다.

## 한계와 상태

Windows 실기 종료는 이 macOS 세션에서 실행하지 않았다. POSIX의 기존 `lstart` 초 단위 정밀도는 그대로이며, 같은 owner가 같은 명령을 같은 초에 같은 PID로 재사용하는 극단적 경우까지 구별한다는 주장은 하지 않는다. 두 `ps` 조회 사이에 대상이 바뀌어 앞부분이 달라지면 종료를 거절한다.

코드는 격리 브랜치의 미커밋 상태다. 커밋·푸시·원격 `dev` 병합·앱/서버 재시작은 하지 않았다. 환경 원문이나 token 값은 출력·문서화하지 않았다.

## 최신 원격 dev 병합 전 점검

2026-11-03 KST 원격 `dev`가 `f2cc17a9`로 한 커밋 전진한 것을 읽기 전용 조회로 확인했다. 새 커밋은 접근 권한·프로모션 관련 다섯 파일만 변경하고 W20의 두 파일을 변경하지 않는다. 최신 `dev`의 일회용 작업 공간에 W20 미커밋 diff를 `git apply --check` 후 적용했으며 `git diff --check`와 빌드가 통과했다. 합성본의 전체 Node 테스트는 **5,295개 중 5,287 통과·8 건너뜀·실패 0**이었다. 검증 종료 시 원격 `dev`가 여전히 `f2cc17a9`임을 다시 확인했다. 일회용 작업 공간은 원복해 제거했다.

합성본의 첫 집중 실행은 제어된 `ps` fixture에서 초기 identity 저장을 1초 안에 관측하지 못해 9/10으로 실패했다. 동일 집중 파일을 이어서 **20회 연속 통과**했고, 전체 실행도 통과했다. 첫 실패의 단일 원인은 확정하지 못했으므로 테스트 fixture/실행 환경의 간헐성 가능성으로 남긴다. 제품 코드의 실제 child tree 종료 회귀는 이후 실행에서 통과했다. W20 브랜치는 여전히 미커밋이며 실제 병합은 하지 않았다.

## 독립 검증과 후속 수정 — 현재 상태

사용자 요청에 따라 GPT-6.1 Sol / xhigh의 별도 채팅 `01a19fb6-4a3d-7592-9d3a-02c1a8404dfb`에서 독립 검증했다. [독립 결과 정본](03-macos-owned-child-identity-independent-sol-xhigh-01a19fb6.md). 계측100회·비계측100회, 추가 경계15개(Windows 제어 분기4개 포함), 최신 dev 합성본 전체가 통과했다. 제품 수정은 타당하다는 검토 결과이며 최초 자연 실패의 단일 원인은 확정하지 못했다. Windows 실기 접근도 없었다.

독립 진단은 기존 1초 manifest 폴링이 진행 중인 조회와 이미 null로 끝난 조회를 같은 assertion으로 표시함을 고장 주입으로 확인했다. 권고를 반영해 테스트의 임시 실행 파일·PATH 변경·파일 polling을 제거하고, 지정 가상 PID의 `execFile` callback에 조회 종류별 초기/후속 snapshot을 순서대로 반환한다. `track` 직후 `shutdown`을 호출해 제품의 실제 `identityReady` 대기를 검증한다. 제품 코드의 검사 완화·재시도·대기 시간 증가는 추가하지 않았다.

최종 회귀에 두 `ps` snapshot 불일치 시 무신호 거절, 초기 EACCES 조회 실패 시 identity unavailable·null manifest 보존을 추가했다. 대상 **12/12 통과**. 최종 transient 회귀를 기존 제품 모듈에 연결하면 원래 `identity changed`로 실패(red)한다. 독립 검증자는 이 후속 diff도 별도 검토해 snapshot·callback·PID 한정·실제 child 통합 경로에서 논리적 결함을 발견하지 못했다.

최종 diff를 원격 dev `f2cc17a9`의 별도 archive 복제본 `/private/tmp/w20-after-review-01a19dcf/desktop/clipper_nestjs`에 적용 검사 후 빌드·전체 검증했다. **5,297개 중 5,289 통과·8 skip·0 fail·0 cancelled**. 로그 `/private/tmp/w20-after-independent-review-full.log`. 종료 시 원격 dev가 여전히 `f2cc17a9`임을 확인했고 `git diff --check`도 통과했다. 변경은 registry 소스와 시험 두 파일의 미커밋 diff이며 커밋·푸시·병합은 하지 않았다.

최초 자연 실패를 유발한 사건까지 해결됐다고 단정하지 않는다. 후속 수정은 잘못된 고정 시간 의존성과 실패 원인 혼동을 제거했으며, 초기 조회가 실제 실패하면 안전하게 종료를 거절하는 제품 동작을 명시적으로 검증한다.

## 사용자 승인 커밋·원격 dev 병합 완료

2026-11-03 KST 사용자가 W20 코드의 dev 병합과 이번 세션 문서 커밋을 명시적으로 요청했다. 코드 커밋은 `5708ee5e` (`fix(process): stabilize owned child identity on macOS`), 병합 커밋은 `c8b71e7fc2079d666c0c3e32a6fc690190613dd9`이다. 최신 원격 dev `f2cc17a9`에서 독립 통합 브랜치 `merge/macos-owned-child-dev-20261103`를 만들어 충돌 없이 병합했다.

실제 병합 커밋에서 빌드와 전체 Node 회귀를 다시 실행해 **5,297개 중 5,289 통과·8 skip·0 fail·0 cancelled**를 확인했다. 로그는 `/private/tmp/w20-dev-merge-final-node24.log`이다. 이후 `git push origin HEAD:refs/heads/dev`가 `f2cc17a9..c8b71e7f`로 성공했다. 원본 checkout과 W19 작업 공간은 checkout·서버 종료 없이 보존했다. 제품 변경은 registry와 시험 두 파일뿐이다. 앱 배포나 Windows 실기 검증은 수행하지 않았다.

`.codex` 문서 커밋은 W20 계획·결과·독립 검증·초기 인계·작업카드와 WORKBOARD의 W20 행만 포함한다. 다른 세션의 문서 변경은 작업 트리에 보존한다. 이전 절의 미커밋/미병합 표시는 당시 상태의 이력이며 현재 상태는 이 절을 따른다.
