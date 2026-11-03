# macOS 보조 프로세스 소유권 오인 — 별도 세션 인계

2026-11-03 KST. W19 최종 회귀 중 발견. 사용자는 **기존 오류를 별도 기록하고 새 세션에서 원인을 찾아 해결**하도록 지시했다. 이번 프로모션/배지 dev 병합에는 이 오류의 제품 수정을 넣지 않는다. 100원 최소 청구 업그레이드 문제와도 다른 작업이다.

## 대상과 재현

저장소는 `desktop/clipper_nestjs`. 조사본 경로는 `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/desktop/clipper_nestjs`. 이 경로는 실행 중인 W19 세션 소유이므로 새 세션이 직접 수정하거나 브랜치를 전환하지 않는다. 새 작업은 원본 저장소 상태를 보존하며 최신 원격 dev에서 별도 브랜치/격리 작업 공간으로 진행한다.

확인 당시 원격 dev는 `7f57ff1b`이며 아래 소스·시험은 dev와 같았다.

- `src/core/process/owned-child-process-registry.ts`: `track`의 즉시 identity 수집, `signal`의 재검사, `readOwnedChildIdentity`.
- `test/owned-child-process-registry.test.js:129`: 실제 POSIX parent/descendant 종료 검사.
- Node `/Users/jina/.nvm/versions/node/v24.19.0/bin/node`로 전체 및 단독 재현. Node 기본 명령은 다른 버전일 수 있으므로 절대 경로 사용.
- 실행: 위 Node로 `--test test/owned-child-process-registry.test.js`. `ps`와 테스트용 child를 사용할 수 있는 실행 환경이 필요하다. sandbox의 EPERM은 별개 원인이다.
- 실패: `Refusing SIGTERM: owned child … identity changed`. 실제 같은 PID가 실행 중인데 저장 시점과 종료 시점의 해시가 달라진다.

## 읽기 전용 조사에서 확인한 원인

`readOwnedChildIdentity`가 `ps eww -o lstart=,command= -p PID` 출력 전체를 해시한다. macOS는 실행 직후 이 출력에 임시 시작 메타데이터를 포함할 수 있고 곧 사라진다. 두 실패 probe에서 출생 시각/실제 명령의 해시는 같았지만 출력 길이는4317→3900으로 변했다. 사라진 필드명은 pfz, stack_guard, malloc_entropy, ptr_munge, main_stack, executable_file, dyld_file, executable_cdhash, executable_boothash, th_port, security_config였다. 원문 환경/값은 비밀 유출 방지를 위해 기록하지 않았다.

원인 조사 에이전트의 제어된 단독 검증: 최소 환경에서 기존 시험4/4 통과, 기존 환경에서 fixture 준비(stdout) 후 추적 시작 시2/2 통과. 이는 시작 시점 의존성의 근거이며 제품에서 즉시 track하는 경로의 안전성이 검증됐다는 뜻이 아니다. production도 즉시 track하므로 단순 테스트 문제로 덮지 않는다.

W19에서 최소 환경의 전체 회귀도 시도했으나 PATH에서 ffmpeg를 제외해 관련 시험들이 실패했고 소유권 시험도 실패했다. 이를 전체 통과라고 보고하지 않는다. 재실행에는 정상 도구 PATH가 필요하다.

## 해결 시 지켜야 할 경계

- PID 재사용·다른 프로세스 종료 방지, 출생/owner token 검증을 유지한다. identity 검사 제거·항상 종료·광범위 killall로 우회하지 않는다.
- transient 메타데이터 변화와 실제 PID/owner 교체를 각각 재현하는 회귀부터 만든다. 준비 완료를 기다리는 테스트 변경만으로 제품 race를 숨기지 않는다.
- macOS/Windows 종료 분기·TERM→KILL·자식 트리·manifest 보존을 검토한다. Windows가 검증되지 않았으면 명시한다.
- 실제 사용자 앱/서버/다른 세션 child를 종료하지 않는다. 테스트 자신이 만든 PID만 사용한다. `ps eww` 환경 원문/토큰을 출력·문서화하지 않는다.
- 원인 재확인→최소 수정→집중/전체 회귀→독립 검토→`.codex` 문서/작업카드 갱신까지 진행한다. 별도 요청 없는 커밋/푸시/원격 병합은 하지 않는다.

## 증거

- `/private/tmp/w19-final-20261103-nest-tests-node24.log`: 전체5,291개 중5,290 통과/1실패(집계 원문으로 재확인).
- `/private/tmp/w19-final-20261103-nest-owned-isolated.log`: 단독6개 중5통과/1실패.
- `/private/tmp/w19-final-20261103-nest-tests-controlled-env.log`: PATH 제한으로 ffmpeg 오류까지 난 실행, 성공 근거로 사용 금지.

[W20 작업카드](../../../../../handoff/tasks/macos-owned-child-identity.md) · [W19 세션](../../../../../records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md).
