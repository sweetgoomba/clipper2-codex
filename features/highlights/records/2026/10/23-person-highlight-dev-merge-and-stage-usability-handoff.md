# 인물 하이라이트 원격 dev 병합 및 무대 사용성 인계

**후속 상태 갱신:** 이 기록에서 착수로 남긴 무대 사용성 이식은 이후 [무대 사용성·원본 구간 전환 결과](23-stage-usability-source-ranges-dev-merge.md)와 같이 구현·검증하고 Angular `f488e8a4`, Nest `8397afbc`, Python `3fbb002`로 원격 dev에 반영했다. 아래 전달 당시 상태와 SHA는 당시 기록으로 보존한다.

## 범위와 승인

- 사용자가 최신 원격 dev 병합을 요청했고, 최초 충돌 보고 후 2026-10-23에 “충돌 해결하고 병합해줘봐”로 해결·병합을 승인했다.
- 데스크톱 4개 저장소의 `feature/person-highlight-w14-20261020`을 각 최신 `origin/dev`에 병합하고 일반 push했다. force push 없음.
- 작업 트리: `/Users/jina/project/adlight/.worktrees/person-highlight-dev-merge-20261023/desktop/<repo>`
- 로컬 통합 브랜치: `merge/person-highlight-dev-20261023`. 기존 Person 작업 트리, 실행 앱, 다른 세션의 stage integration 작업은 변경하지 않았다.

## 원격 dev 체크포인트

| 저장소 | 기존 dev | 병합 후 dev |
|---|---|---|
| clipper_angular | 73b378aae74d54d313c7492f1faed7a7fddd8cb0 | 8f45aef8844818fc168fd84e2aa96379b2d9a527 |
| clipper_electron | 31bd8041bf31a90a1f6fc806ae7e83369305745e | 43319ab8e1eeaa40ef2e1b82d4dc41bb840531d8 |
| clipper_nestjs | c9eb82cb91c5322f3776d5f3225d61a1b6b989f0 | a577c8b6fcdcb88e12b118c16375535303542cd1 |
| clipper_python | 09899982d2aa94cdef2b970fb128c60f3e8c4da2 | 153bb69571ccc348a88f83df84d2ecd5ebe38c6b |

Person 부모 커밋: Angular `7a453546`, Electron `2502255`, Nest `0ec0822a`, Python `ef9ae0d`.

## 충돌 및 통합 보완

1. Angular navigation 메타데이터와 테스트: 인물 하이라이트, 해외 영상, 큐레이션을 모두 유지했다. 새 인물 메뉴를 unknown으로 사용하던 news 테스트 픽스처도 갱신했다.
2. Electron model-files/install-state: 설치된 공유 모델 사용자를 전체 확인하고 Person을 모델 검사 목록 및 HF cache 목록에 추가했다. 인물의 얼굴/포즈 자산은 안무 소유 규칙을 유지했다.
3. Electron 모델 IPC: 안무·인물·대사·해외 영상의 설치/삭제를 같은 큐로 직렬화하고, 실제 모델 경로가 겹치는 모든 peer의 starting/running/stopping을 확인한다. 실행 중인 peer의 파일과 임시 얼굴 다운로드 파일을 보호한다.
4. Electron `hasFiles`: 실제 삭제 가능한 파일 기준을 Person에도 적용했다. 공유 모델만 남으면 마커 정리로 이어지는 최신 dev 제거 UI 계약을 보존한다.
5. Python lock: 이전 stage 통합 커밋의 양쪽 의존성이 포함된 lock을 출발점으로 전체 workspace manifests에 대해 `uv lock --offline` 및 `uv lock --check --offline`을 실행했다. ONNX Runtime 1.31.0, 해외 영상, 인물, speech-core를 모두 유지했다. 의존성 임의 업데이트 없음.
6. Nest 자동 병합 후 전체 테스트에서 발견된 큐레이션 경로 불일치: ProjectsService의 충돌 방지 경로 인코딩을 `project-artifact-paths.ts`의 `projectPathSegment`로 공통화해 CurationRenderService에서도 재사용했다. 두 초기 렌더 경로가 같은 위치를 산출하도록 기존 테스트로 검증했다.

독립 코드 검토에서 Electron hasFiles 계약 문제를 발견해 수정했고, 후속 검토에서 추가 조치할 통합 결함은 없었다. Shortform/Variation은 initial/retry에서 explicit output_root를 일관되게 전달하므로 별도 경로 변경은 하지 않았다.

## 검증

- Angular 전체 Karma: 8,304 passed. 스타일 검사: 14 passed. packaged renderer build 성공.
- Electron tsc build 성공. 전체 node:test: 1,721 passed. 공유 모델/설치/IPC 회귀 51 passed. 패키징 산출물 검사 8 passed(전체에 포함).
- Nest tsc build 및 bundle 성공. 최종 전체 node:test: 4,237 passed.
- Python 전체 pytest: 1,472 passed, 6 skipped, 21 warnings. skipped: 빠르게 완료돼 duplicate race를 포착하지 못한 2건, 제공되지 않은 실제 대사/안무 영상 2건, 로컬 해외 영상 fixture 부재 2건.
- Python 테스트는 병합 작업 트리의 패키지 경로들을 PYTHONPATH에 명시하고 기존 stage venv 의존성 + `/private/tmp/adlight-pytest-shim`으로 실행했다. 기존 venv 설치 상태는 바꾸지 않았다.
- Python lock check 통과. Git conflict marker/whitespace 검사 통과.
- 원격 dev SHA를 `git ls-remote`로 확인하고 Person feature 부모 포함 여부를 확인했다.
- Windows 빌드·실제 사용자 영상 정확도 재평가는 이번 병합 검증에 포함하지 않았다. 설치 앱 패키징/실행 교체는 하지 않았다.

### 테스트 실행 환경 관련 기록

- 초기 제한 환경에서 로컬 포트/프로세스 검사 실패 → 필요한 권한으로 재실행했다.
- Electron POSIX 자식 프로세스 종료 검사: PATH를 앞에 덧붙인 Node 24.19 실행에서 실패하지만, 같은 Node의 절대 경로 실행, Node22 절대 경로 실행, 기본 Node24.3 실행은 6/6 passed. 양쪽 reader/writer와 해당 테스트는 dev와 동일하다. PATH에 민감한 정확한 원인은 미진단 상태이며 소유권 보호 코드를 완화하지 않았다. 최종 Electron 전체 테스트는 기본 환경에서 전부 통과했다.
- 새로운 격리 트리에 없는 ignored `.env.packaged`와 공개키 설정은 기존 작업 트리에서 복사했고, 렌더러/Nest 산출물을 현재 소스로 생성한 뒤 패키징 테스트했다. 비밀 내용은 로그/커밋에 넣지 않았다.
- 최종 테스트 로그: `/tmp/person-merge-angular-tests.log`, `/tmp/person-merge-angular-styles.log`, `/tmp/person-merge-angular-build.log`, `/tmp/person-merge-electron-tests-final.log`, `/tmp/person-merge-nest-tests.log`, `/tmp/person-merge-python-tests.log`.

## 무대 사용성 후속 전달 범위

대상: `2026.10.19-23 무대 하이라이트 사용성` (01a1435b-1fed-7d33-9d25-9bfeb3c83045).
각 저장소 최신 원격 dev에서 새 작업 브랜치/격리 작업 트리를 만들어 진행한다.

- 클립 모달에 원본 구간·구간 편집·선택 체크박스 추가. 목록/모달 선택 동기화.
- 클립 제목 옆 전체 개수. 전체 선택 오른쪽 점 세 개 메뉴로 선택 삭제/다운로드/멤버 지정/숏폼 미리보기.
- 숏폼 구성 모달은 Person의 큰 원본 비율 플레이어와 가로 스크롤 순서 목록·드래그 재정렬·재생 위치 동기화 동작 재사용.
- 체크된 클립들을 카드에서 드래그하면 선택 묶음 전체를 인물 카드로 이동, 드래그 개수 표시.
- 미확인 인물 카드 → 멤버 카드 병합 허용. 등록 멤버 카드끼리 병합은 금지.
- 미확인 인물의 실제 얼굴 썸네일 표시. 공통 코드 재사용, 얼굴 판정 알고리즘 튜닝은 별도 파이프라인 세션과 분리.
- Person 참고: Angular `src/shell/projects/person-result-detail`, `person-shortform-assembly-dialog`, `projects-clip-overlay`, 공통 result-card action 스타일.

주의: 별도 무대 파이프라인 세션의 stage-person-integration 브랜치에서 진행 중인 추가 알고리즘 개선은 이번 dev 병합에 포함하지 않았다. 웹 API의 로컬 미커밋 인물 과금/entitlement 패치도 이번 데스크톱 4개 저장소 병합에는 포함되지 않았다.

## 전달 결과와 다음 재개 순서

- `2026.10.19-23 무대 하이라이트 사용성`에 위 확정 요구와 네 저장소 dev SHA를 실제 전달했다. 전달 직후 `active/inProgress` 및 격리 작업 공간·구현 계획을 준비한다는 응답을 확인했다. 이는 구현 착수 확인이며 해당 UX의 구현 완료/검증 결과는 그 세션에서 기록한다.
- `2026.10.19-23 무대 하이라이트 파이프라인` (01a1435b-139b-70c2-ac58-36dd9e010b1d)에도 새 dev SHA와 공유 모델/큐레이션 경로 통합 내용을 전달했다. 기존 작업을 이어가되 과거 stage 통합의 충돌 해결본으로 새 dev 수정을 덮어쓰지 않도록 인계했다.
- `2026.10.19-23 공통 얼굴 매칭 품질` (01a1435b-36ee-71c3-ad82-b9b584cd759b)의 기존 검토 결과는 [공통 얼굴 이식 검토](23-shared-face-stage-transfer-review.md)를 참고한다. 이 기록을 별도 추가 구현 완료로 해석하지 않는다.
- 파이프라인 이식 근거는 [Person→Stage 미확인 분류 조언](23-person-to-stage-unidentified-transfer-advice.md), 이전 격리 통합은 [stage 통합 기록](23-stage-person-integration-result.md)에 보존한다. 이전 격리 통합 SHA보다 이번 원격 dev 체크포인트가 이후 기준이다.
- 다음 작업 시작 시 원격 dev를 다시 fetch하고 사용자 작업/다른 세션의 미커밋 변경을 보존한다. 두 무대 세션의 후속 구현은 아직 dev에 반영됐다고 간주하지 않는다.
- **후속 완료:** Web API Person 과금/권한은 이후 사용자 승인으로 `ba68b2b`에 커밋해 원격 dev에 반영했다. 로컬 DB는 이미 해당 정책/권한이 적용돼 있어 추가 migration 0건을 확인했다. [서버 통합·검증 기록](23-person-highlight-web-api-billing-dev-merge.md). 운영 배포·실제 결제 검증과는 구분한다.
