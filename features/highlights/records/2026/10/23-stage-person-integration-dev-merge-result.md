# Stage integration: latest dev merge

## 최종 상태 — 원격 dev 반영 완료 (2026-10-23 06:13 KST)

세 관련 세션의 이력과 원격 Git을 재감사한 결과, 사용성 작업은 dev에 포함되어 있었으나 파이프라인 작업은 dev를 작업 브랜치로 가져온 상태였다. 사용자 후속 “진해해줘” 승인에 따라 아래 검증한 네 커밋을 원격 dev에 fast-forward로 반영했다. 기존 dev와 사용성 변경을 모두 포함하며 추가 충돌은 없었다.

| 저장소 | 확인한 원격 dev 커밋 |
|---|---|
| Angular | `975e16f64a9f45d657da14b31013ad6148591a90` |
| Electron | `dfc84d4889a2ee6ecbf8dec326436d76a514ba79` |
| NestJS | `15f534b955aabc4bb6a15d188d571795afe91574` |
| Python | `584d76bf06284ec369d146a4013a5cf325743fa1` |

각 저장소의 `git ls-remote`로 dev와 `feature/stage-person-integration-20261023`의 SHA 일치를 확인했다. `origin/dev...HEAD`의 양방향 미반영 커밋 수는 모두 `0 / 0`, tracked 변경 및 `git diff --check` 오류도 0이다. 공통 얼굴 매칭 품질 세션은 별도 제품 소스 커밋이 없는 검토 세션이며, 공통 AuraFace 구현은 기존 Person 병합을 통해 포함되어 있다.

### 이번 반영 직전 재검증

- Angular 전체 **8,330 통과**, 스타일 검사 **14 통과**.
- Electron TypeScript build 및 전체 **1,721 통과**.
- NestJS TypeScript build 및 전체 **4,258 통과**. 이전 실패였던 실제 POSIX 자식 프로세스 종료 검사도 별도 **6/6**와 전체 검사 모두 통과했다. 프로세스 소유권 보호를 수정하거나 약화하지 않았다. 아래의 4,257/1 실패 기록은 이전 실행 환경의 이력이다.
- Python 전체 **1,512 통과 / 6 건너뜀 / 21 경고**, 164.64초. 건너뜀은 중복 요청 타이밍 2건, 입력 미설정 실영상 E2E 2건, 별도 해외 더빙 원본 부재 2건이다.
- 독립 코드 리뷰에서 병합을 막을 Critical/Important 회귀 없음. 기존 이름 확정 결과 보존, 미확인 구간만 교대 분할, 분할 전 기준의 군무 인물 배정, source_ranges와 썸네일 보존, 분석 중 MP4 미생성, 기존 공통 matcher 호출 호환성을 확인했다.
- 로그: `/tmp/stage-to-dev-angular-{tests,styles}.log`, `/tmp/stage-to-dev-electron-{build,tests}.log`, `/tmp/stage-to-dev-nest-{build,tests}.log`, `/tmp/stage-to-dev-owned-child.log`, `/tmp/stage-to-dev-python-tests.log`.

### 현재 남는 범위

이번 작업은 원격 dev 소스 통합이다. 새 설치 앱 빌드·교체, 병합 코드로 전체 실영상 프로젝트 재분석, Windows 검증은 하지 않았다. 실행 중 앱과 기존 결과·원본·평가 자료 및 작업 트리는 보존했다. 아래는 이 최종 반영 이전의 충돌 해결 및 작업 브랜치 검증 이력이다.

## Authorized resolution

The user authorized committing/pushing the integration branch, merging remote dev, stopping at conflicts, then explicitly approved both conflict resolutions after the reports.

Branch: `feature/stage-person-integration-20261023` across the four desktop repositories.

Incoming dev snapshots:

- Python: `3fbb002afa9cd329945629d1d968efab2ffc6e6d`
- Electron: `43319ab8e1eeaa40ef2e1b82d4dc41bb840531d8`
- Angular: `f488e8a4201ffc664494485122789484be6afaf1`
- NestJS: `8397afbcd9185033dc9453dc416587015ac00c4e`

## Conflict decisions

1. Electron `plugin-model-files.ts`: retain dev's already reviewed shared-model protection, temporary download file guard, plugin-specific allowed deletion root, and deletion status behavior. The resolved file is byte-identical to incoming dev. Electron's local evaluation-output packaging exclusion is retained.
2. Python `pipeline.py`: preserve pose-owned evidence, identity-switch detection, per-piece matching, baseline-only group assignments, diagnostics and exact start/end ranges. Adopt dev's `source_ranges` storage: save IDs, ranges and thumbnails during analysis; render videos only on export. Remove the earlier analysis-time `extract_clip` calls, including their split-only accurate-encoding branch.

## Verification — 작업 브랜치 통합 당시

- Conflict integration test uses the real DanceMetaBuilder, checks split ranges and names, invalid gallery fallback, group non-propagation, IDs, thumbnails and absence of analysis-time MP4s. Keeping the old eager extraction first produced 5 expected failures / 10 passes; removing it produced 15 passes.
- Python Dance + common face + Person regression: **465 passed** (36.68 s).
- Electron TypeScript build passed; full tests **1,721 passed**. Initial sandbox run could not bind loopback ports; the authorized unrestricted run passed.
- Angular packaged build passed; full headless Karma **8,330 passed**; style checks **14 passed**.
- NestJS TypeScript build passed. Full suite after the export boundary test: **4,257 passed / 1 failed**. The failure is `owned-child-process-registry.test.js`, “POSIX 실제 child tree는 shutdown 뒤 parent와 descendant PID가 모두 사라진다”, with `Refusing SIGTERM: owned child ... identity changed`. It repeated with test concurrency 2 and in the isolated file (5 passed / 1 failed). Before the new export test was added, the merged Nest tree was exactly dev (`cf88ca22ca39080f20c2f07785f414428703762b`); the sole subsequent Nest change is the export regression test. This establishes the failure also exists in the current environment on unchanged dev code. No process-identity protections were weakened to make tests pass.
- Actual FFmpeg single/ZIP export regression: **9 passed**, including a non-keyframe performer boundary. A red/blue/red source exports exactly the eight blue frames from 1.3–2.1 seconds, with no adjacent performer frames.
- Actual saved video replay through Nest's export service: 84.150733–86.152733 seconds exported as 2.002 seconds / 120 frames. First and last exported frames match source frames **5044** and **5163**, respectively. Compared against each target's two neighboring frames, the expected frames were the closest pixel matches (mean errors 1.20 and 1.56 on 0–255 pixels).

## Local evidence

- Python `evaluation-output/stage-face-evidence-20261023/product/nest-export-22.json` and `nest-export-22.mp4` (untracked; excluded from packages).
- `/private/tmp/stage-source-range-{red,green}.log`
- `/private/tmp/stage-merge-final-python-tests.log`
- `/private/tmp/stage-dev-merge-electron-tests-unrestricted.log`
- `/private/tmp/stage-merge-final-angular-{build,tests,styles}.log`
- `/private/tmp/stage-merge-final-nest-tests-retry.log`
- `/private/tmp/stage-merge-owned-child-isolated.log`
- `/private/tmp/stage-export-boundary.log`

## Limits — 작업 브랜치 통합 당시

This merge does not constitute a new complete user-project analysis or a newly packaged desktop app. Previously built app bundles are from before these dev merges. Existing projects, source videos and running app sessions were preserved. The remaining Nest process shutdown failure is recorded for a separate fix; overall Nest suite success is not claimed.


## 작업 브랜치 푸시 완료 — 원격 dev 반영 전 (2026-10-23)

네 저장소의 `feature/stage-person-integration-20261023` 브랜치에 병합 결과를 푸시했다. 각 저장소에서 HEAD와 원격 작업 브랜치 SHA가 같고, 가져온 최신 origin/dev가 HEAD의 조상임을 확인했다.

| 저장소 | 최종 커밋 |
|---|---|
| Python | `584d76bf06284ec369d146a4013a5cf325743fa1` |
| Electron | `dfc84d4889a2ee6ecbf8dec326436d76a514ba79` |
| Angular | `975e16f64a9f45d657da14b31013ad6148591a90` |
| NestJS | `15f534b955aabc4bb6a15d188d571795afe91574` |

병합 방향은 원격 dev → 작업 브랜치다. 원격 dev 자체에 이 작업 브랜치를 병합하지 않았다. 미해결 충돌이나 미커밋 소스 변경은 없으며, 로컬 실험 자료와 앱 빌드 산출물은 untracked로 남아 있다.
