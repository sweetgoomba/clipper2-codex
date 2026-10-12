# W13 탈락 장면 검토 화면 — 격리 구현·검증 기록

2026-10-01 KST. 사용자가 추천 순서(탈락 장면 표시 → 메인 정확도 → crop → 복수 배정)를 승인한 뒤 **첫 단계만** 구현했다. 기존 완료 프로젝트, 실제 공연 영상, 모델 weight, W14 공통 얼굴 파일은 수정하거나 재실행하지 않았다. 새 분석을 실행한 프로젝트에서만 sidecar가 생기므로, 기존 `yFTAYXDTjqI` 완료 카드에는 이 변경만으로 4.271초 후보가 나타나지 않는다. 4.271초는 기존 artifact의 정적 계산이며 새 앱 결과가 아니다.

## 분리된 작업 공간

| 저장소 | fetch 후 `origin/dev` | W13 worktree |
|---|---|---|
| Python | `47782953228861f4bdbdc135265d067c2a826b0e` | `/Users/jina/project/adlight/.worktrees/w13-review-scenes-20261001/desktop/clipper_python` |
| Nest | `60a777181c2c9822415f40482c30b6904564a2aa` | `/Users/jina/project/adlight/.worktrees/w13-review-scenes-20261001/desktop/clipper_nestjs` |
| Angular | `705c49c18c4a9114d1d36cc93de7a653ca1c36fb` | `/Users/jina/project/adlight/.worktrees/w13-review-scenes-20261001/desktop/clipper_angular` |

세 worktree의 브랜치는 `feature/w13-review-scenes-20261001`이다. Desktop 형제 상대경로를 유지했다. 기존 Angular checkout의 다른 미커밋 문서와 다른 세션 worktree는 건드리지 않았다. **commit/push/merge/deploy는 0회**다.

## 구현한 자료 흐름

1. Python `DancePipeline.run()`은 group 필터 전 main 구간과 얼굴 표본 탈락 구간을 수집한다. 후자는 실제 이유(`no_main_bbox`, `video_decode_failed`, `no_valid_face_candidate`, `insufficient_track_samples`)와 추출 후보 수를 기록한다. 출력 MP4와 기존 `dance_meta_v1`의 클립·인물 계산은 변경하지 않았다.
2. 원본 경로·SHA-256·크기·revision UUID·구간 경계와 원래 float 시각·관측 시각·겹치는 그룹 clip ID를 `json/dance_review_candidates.json`에 원자 교체로 기록한다. `candidateId`는 해당 실행의 revision 안에서만 의미가 있다. 얼굴/인물 이름을 추정하지 않으며 `autoPersonId`와 `candidateBBoxRef`는 `null`이다.
3. Nest는 선택적 sidecar의 schema/revision/hash/중복 ID/시간 범위를 검사한다. `reviewScenes`는 `clips`/`persons`와 분리하고, 기존 main/group 출력 구간은 `reviewTimelineClips`로 분리한다. 원본 경로가 프로젝트 원본과 같은 실제 파일이고 SHA가 맞을 때만 `reviewSourcePath`를 준다. `/var`와 `/private/var` 별칭은 `realpath`로 비교한다. sidecar가 없거나 손상됐으면 기존 프로젝트 상세는 그대로 연다.
4. Angular 결과 상단에 `생성된 클립`과 `확인 필요` 원본 타임라인 두 줄을 표시한다. 후보의 시간/탈락 이유를 누르면 원본 플레이어가 시작 시각으로 이동한다. 원본 누락·변경 또는 플레이어 오류 때는 후보 정보와 안내를 남기고 이동 버튼을 막는다. 기존 네 열의 클립·인물·숏폼 화면은 유지한다.

## 검증 근거

| 검증 | 결과 |
|---|---|
| Python 집중 테스트 | 17 passed: 그룹 중첩·얼굴 미검출/표본 부족·빈 sidecar·원자 교체 실패·가짜 pipeline |
| Python 비 e2e 전체 | 493 passed. 기본 sandbox에서는 loopback fixture 5개가 `EPERM`이었고, 같은 테스트를 로컬 fixture 접근을 허용해 재실행해 전부 통과 |
| Nest build + 안무 상세 회귀 | build 통과, builder 관련 14 passed |
| Nest 안무/프로젝트 범위 | 183 passed. loopback fixture 때문에 로컬 접근 허용 상태에서 실행 |
| Angular 집중 브라우저 테스트 | ChromeHeadless 72 passed: 새 후보 두 건·기존 clip 줄·seek·원본 누락·구 프로젝트·서비스 URL 포함 |
| Angular 정적 검증 | `ngc --noEmit`, SCSS 컴파일, 스타일 테스트 6개, packaged `ng build` 통과 |
| Python → Nest 합성 sidecar | 1개 검토 후보, 0개 기존 clip 변형, source hash 검증 통과. 첫 실행에서 `/var` 경로 별칭 문제를 발견해 `realpath` 수정 후 통과 |

Angular 기본 sandbox에서 esbuild가 Go deadlock(exit 134)을 냈다. **변경 전에도 동일하게 재현**됐고, 격리 작업 공간의 빌드/브라우저 테스트를 허용된 실행 환경에서 통과했다. 전체 Angular 5천여 개 테스트는 이 좁은 변경의 필수 gate로 확장하지 않았다. Nest 전체 테스트의 기본 sandbox 실패는 다수의 loopback `EPERM`과 새 worktree에 없는 `.env.packaged` fixture였으며, 변경 범위의 182개를 통과시켰다.

## 아직 검증하지 않은 것과 다음 판단

- 이 변경을 기존 Dev 앱/사용자 완료 카드에 적용하지 않았다. 기존 카드에는 sidecar가 없다. 새 실영상 분석·기존 프로젝트 backfill·clip export를 승인 없이 하지 않았다.
- `/sources/stream`은 다운로드 캐시 또는 현재 프로세스의 허용 목록만 재생한다. 캐시 밖 로컬 원본은 재시작 후 SHA가 같아도 영상 요청이 실패할 수 있다. UI는 오류 안내를 제공하지만 배포 전 영속적인 project source streaming 계약을 별도로 정해야 한다.
- 상세 조회마다 후보가 있을 때 원본 전체 SHA를 다시 계산한다. 큰 파일 지연/자원은 아직 측정하지 않았다. UUID revision에는 weight/config/code hash가 없고 재시도 멱등성·캐시·editRevision은 없다.
- source boundary는 현행 fps 파생 float이고 원본 PTS·정확한 ffmpeg 첫/끝 프레임이 아니다. 멤버 재배정·경계 편집·새 MP4 생성·crop track·batch undo는 구현하지 않았다.
- 두 번째 단계인 메인 판정 정확도는 이 변경으로 좋아졌다고 주장할 수 없다. 이전 MoveNet 저장 관측의 독립 18프레임에서 현행 선택기는 6/18, 단일 규칙 변형 둘은 각각 4/18이었다. 다음 모델/선택기 변경 전에 입력·라벨·상업 이용 조건·실행 상한과 사용자 화면 검토 범위를 확정해야 한다.
