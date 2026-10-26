# 무대 하이라이트 사용성 개선과 원본 구간 저장 전환

작성일: 2026-10-23 KST

무대 결과의 구간 편집·일괄 작업·숏폼 구성을 Person과 공통화하고, 새 무대 분석 결과를 원본 영상과 구간 메타데이터로 저장하도록 변경했다. 사용자 요청에 따라 Angular·NestJS·Python 작업을 커밋·푸시하고 최신 원격 `dev`에 충돌 없이 fast-forward로 반영했다. Electron 소스 변경은 없다.

## 사용자 요청과 확정한 동작

- Person의 원본 구간 편집과 결과 화면 동작을 무대 하이라이트에 적용한다.
- 새 무대 분석에서도 개별 클립 MP4와 합본 영상을 미리 생성하지 않는다. 원본과 시작·끝 시각을 저장하고, 다운로드·내보내기·숏폼 생성 시 해당 구간을 렌더한다.
- 선택한 장면을 삭제·다운로드·멤버 지정·숏폼 구성에 함께 사용한다. 체크한 장면 묶음의 드래그 이동을 지원한다.
- 미확인 인물은 등록 멤버에 병합할 수 있고, 등록 멤버끼리의 병합은 허용하지 않는다. 미확인 인물 카드에는 실제 관측 얼굴을 표시한다.
- 마지막 Git 요청은 “커밋·푸시 후 최신 원격 dev에 병합하되 충돌 시 멈추고 설명”이었다. 실제 충돌은 발생하지 않았다.

## 저장과 내보내기 구조

새 Dance 분석은 관리되는 원본 영상, 안정적인 `clip_id`, 원본 기준 시작·끝 시각, 썸네일, 인물 연결 정보를 남긴다. 구간 편집 저장은 메타데이터 오버레이만 수정한다. 분석 단계에서 개별 장면 MP4와 합본 MP4를 만드는 처리를 제거했다.

미리보기는 원본의 해당 구간을 재생한다. 단일·선택·전체 다운로드와 숏폼 렌더는 저장된 현재 구간을 읽어 요청 시 영상을 만든다. 화면의 장면 상대 시간과 서버의 원본 절대 시간을 구분해, 편집한 범위가 각 출력 경로에 동일하게 적용되도록 연결했다.

과거 결과는 원본이 없고 구간이 편집되지 않았을 때 기존 MP4를 재생·내보내기에 사용할 수 있다. 원본이 없으면 구간 편집을 비활성화하며, 이미 편집된 범위의 내보내기에 필요한 원본이 사라지면 오래된 MP4를 대신 반환하지 않고 오류를 낸다. 기존 결과 파일을 일괄 삭제하거나 재분석하는 마이그레이션은 수행하지 않았다.

## 화면과 인물 연결 변경

| 기능 | 구현 내용 |
|---|---|
| 공통 장면 모달 | Person의 원본 재생·범위 편집·취소 복원·장면 상대 시간·이전/다음·얼굴 표시를 `SourceSceneOverlayComponent`로 추출해 재사용 |
| 선택 상태 | 목록과 모달 체크박스 동기화. 제목의 전체 개수는 체크 수와 독립적으로 유지 |
| 선택 메뉴 | 선택 삭제·ZIP 다운로드·멤버 지정·숏폼 구성 제공 |
| 숏폼 구성 | Person 구성 모달 재사용. 원본 비율 플레이어, 가로 장면 목록, 재생 위치 자동 스크롤, 장면 클릭/재정렬 시 재생. 확인한 순서만 실제 구성에 적용 |
| 묶음 드래그 | 체크한 장면 전체를 이동하며 공통 드래그 미리보기에 개수 표시. 단일 지정·메뉴 지정·드래그가 같은 일괄 API 사용 |
| 공유 클립 | 출발 인물의 연결만 바꾸고 다른 수신 인물과 `clip_id` 보존 |
| 인물 병합 | 미확인→등록 멤버만 UI/API에서 허용. 성공 알림 제공 |
| 얼굴 썸네일 | 기존 분석에서 추출한 실제 관측 얼굴 JPEG를 미확인 인물 카드에 제공. 등록 멤버 참조 사진과 얼굴 판정 알고리즘은 유지 |

## 주요 구현 위치

아래 경로는 각 저장소 루트 기준이다. 작업 폴더는 `/Users/jina/project/adlight/.worktrees/stage-usability-20261023/desktop/<repo>`다.

| 저장소 | 주요 파일과 모듈 |
|---|---|
| Angular | `src/core/history/project-history.service.ts`, `src/shell/projects/{dance-result-detail,person-result-detail,person-shortform-assembly-dialog,projects-detail-page,dance-diagnostic-timeline,source-scene-overlay,result-drag-preview}` |
| NestJS | `src/modules/projects/application/{projects.service.ts,dance-project-detail-builder.ts,person-clip-export.service.ts}`, `src/modules/projects/domain/project.model.ts`, `src/modules/projects/presentation/projects.controller.ts`, `src/modules/highlight-shortform/application/highlight-shortform-render.service.ts` |
| Python | `plugins/dance_highlight/dance_highlight/services/{pipeline.py,dance_meta.py,person_thumbnails.py}`, `tests/test_dance_person_thumbnails.py` |

NestJS는 기존 Projects API 아래에 다음 경로를 연결했다.

- `PATCH /v1/projects/:projectId/dance/clips/:clipId/range`: 구간 저장.
- `DELETE /v1/projects/:projectId/dance/clips/:clipId/range`: 구간 오버레이 초기화.
- `POST /v1/projects/:projectId/dance/clip-actions`: 선택 장면 일괄 작업.
- `POST /v1/projects/:projectId/dance/zip-selections`: 선택 장면 ZIP.
- `GET /v1/projects/:projectId/dance/clips/:clipId/download`: 현재 구간 단일 다운로드.

## 독립 검토에서 발견하고 수정한 항목

1. 클립 이동 뒤 이전 인물 이름이 남던 제목과 ZIP 파일명을 갱신했다.
2. 마지막 클립을 옮겨 출발 인물 카드가 사라진 경우 선택 상태를 갱신했다.
3. 원본이 없는 과거 MP4 결과에서 탐색 완료 직전의 재생 요청이 누락되던 처리를 수정했다.

각 항목은 실패 회귀를 확인한 뒤 수정했다. 후속 UI 검토에서 해당 지적사항의 해결을 확인했다.

## 검증 결과

### 커밋 직전 재검증

| 범위 | 결과 | 실행 명령 또는 조건 |
|---|---|---|
| Angular 전체 Karma | **8,330 passed** | Node 24.19.0 절대 경로로 `ng test --watch=false --browsers=ChromeHeadless`, `NG_BUILD_MAX_WORKERS=2` |
| Angular 스타일 | **14 passed** | `npm run test:styles` |
| Nest 빌드 및 관련 회귀 | **build 성공, 97 passed** | `npm run build` 후 아래 6개 node:test 파일 |
| Python Dance·face | **161 passed** | 아래 Python 실행 환경에서 `pytest tests/test_dance*.py clipper_face_core/tests -q` |
| 변경 파일 공백 검사 | 통과 | 각 저장소 `git diff --check`, 커밋 전 staged diff 검사 |

Nest 재검증 파일은 `test/dance-result-usability.test.js`, `test/dance-clip-overlays-builder.test.js`, `test/dance-clip-overlays-service.test.js`, `test/dance-member-assignment-service.test.js`, `test/person-clip-export.test.js`, `test/highlight-shortform-render-service.test.js`다. 이 97개는 아래 구현 중 실행한 관련 테스트 110개와 선택 범위가 다르다.

Python은 작업 트리의 `clipper_plugin_sdk`, `clipper_face_core`, `clipper_speech_core`, `plugins/dance_highlight`, `plugins/person_highlight`, `plugins/dialog_highlight`, `plugins/clipper_video_render`와 `/tmp/adlight-pytest-shim`을 `PYTHONPATH`에 명시했다. 실행기는 기존 `/Users/jina/project/adlight/.worktrees/stage-person-integration-20261023/desktop/clipper_python/.venv/bin/python`을 읽기 전용으로 사용했고, `PYTHONDONTWRITEBYTECODE=1`로 실행했다. 기존 venv의 설치 상태는 변경하지 않았다.

### 구현 중 검증과 남은 한계

- Angular packaged build 성공. 최종 소스 변경 후 빌드했으며 이후 커밋 단계에서는 소스를 수정하지 않았다. 구현 중 전체 Karma 8,329개 이후 legacy 재생 회귀를 추가했고, 최종 전체 실행은 위의 8,330개다.
- Nest 관련 회귀 110개 통과. 전체 실행은 **4,253 passed / 1 failed**로, 실패는 새 격리 트리에 없는 ignored `.env.packaged` 읽기였다. 전체 통과로 기록하지 않는다.
- Python Dance·face 161개와 Ruff 통과. broad non-E2E 실행은 **1,456 passed / 2 skipped / 2 failed / 5 errors**였다. 실패는 별도 ranking fadeblack 프레임 허용 오차와 RapidOCR 모델 파일 부재, 오류는 제한 환경의 localhost bind 권한으로 인한 remote-assets/remote-font fixture 문제였다. 해당 코드·모델 설치 상태는 이번 작업에서 바꾸지 않았다.
- 실제 Angular 컴포넌트와 합성 20초 영상을 localhost:4283에서 열어 원본 비율, 편집 후 취소 복원, 모달→목록 체크, 다음 장면, 전체 개수, 선택 메뉴, 7개 장면 구성, 마지막 장면 클릭 재생·자동 스크롤, 다크/라이트 화면을 확인했다.
- 브라우저 자동화에서 카드 묶음 드롭의 성공 결과는 확인하지 못했다. 선택 묶음·출발 인물·개수 표시·등록 멤버 드래그 금지는 DOM 이벤트 회귀 테스트로 확인했다. 실제 드롭 스모크 성공으로 계산하지 않는다.
- 임시 화면 확인용 소스를 작업 트리에서 제거하고 해당 테스트 서버만 종료했다. 기존 실행 앱은 교체하지 않았다.
- 실제 사용자 영상의 얼굴 정확도 재평가, Windows 패키징·실기, 설치 앱 배포는 이번 검증에 포함하지 않았다. 얼굴 모델·임계값 및 별도 무대 파이프라인 세션의 추가 개선도 이번 커밋 범위에 포함하지 않았다.

### 실행 로그

로컬 임시 로그는 다음 경로에 남겼다. `/tmp` 로그는 정본 보관소가 아니므로 향후 정리될 수 있다.

- `/tmp/stage-push-angular-full.log`
- `/tmp/stage-push-nest-regression.log`
- `/tmp/stage-push-python-regression.log`
- `/tmp/stage-angular-packaged-final.log`
- `/tmp/stage-nest-full-unrestricted.log`
- `/tmp/stage-usability-python-suite.log`

## 커밋과 원격 dev 반영

세 저장소 모두 `feature/stage-usability-20261023` 브랜치에 커밋하고 해당 원격 브랜치를 먼저 푸시했다. dev 반영 직전에 `git fetch origin dev`와 `git merge-base --is-ancestor origin/dev HEAD`로 최신 dev가 작업 커밋의 조상임을 확인했다. `git push origin HEAD:refs/heads/dev`의 일반 fast-forward 업데이트로 반영했다. 충돌·충돌 해결·강제 푸시는 없었다.

| 저장소 | 작업 기준 dev | 작업 커밋과 반영 직후 원격 dev |
|---|---|---|
| clipper_angular | `8f45aef8844818fc168fd84e2aa96379b2d9a527` | `f488e8a4201ffc664494485122789484be6afaf1` |
| clipper_nestjs | `a577c8b6fcdcb88e12b118c16375535303542cd1` | `8397afbcd9185033dc9453dc416587015ac00c4e` |
| clipper_python | `153bb69571ccc348a88f83df84d2ecd5ebe38c6b` | `3fbb002afa9cd329945629d1d968efab2ffc6e6d` |
| clipper_electron | `43319ab8e1eeaa40ef2e1b82d4dc41bb840531d8` | 소스 변경 없음. 이번 세션의 추가 커밋·푸시 대상에서 제외 |

커밋 메시지:

- Angular: `feat(stage): add source-range editing and batch result actions`
- NestJS: `feat(stage): persist source ranges and export selected clips`
- Python: `feat(stage): retain source ranges and observed face thumbnails`

반영 직후 `git ls-remote origin refs/heads/dev refs/heads/feature/stage-usability-20261023`로 각각 작업 커밋과 일치함을 확인했다. 세 작업 트리의 `git status --short --branch`는 clean이었다. 원본 체크아웃의 로컬 dev나 다른 세션의 작업 트리를 갱신한 것은 아니다. 이 SHA와 clean 판정은 반영 당시 관찰값이므로 다음 작업 때 다시 확인한다.

## 다음 세션에서 확인할 항목

1. 작업할 저장소의 최신 원격 dev와 로컬 변경을 먼저 확인한다. 위 작업을 다시 이식하거나 과거 미완료 인계에 따라 중복 구현하지 않는다.
2. 실제 새 무대 결과에서 원본 구간 수정→재생→단일/선택 ZIP→숏폼 생성의 범위를 확인한다. 기존 MP4 결과와 원본 유실 오류도 함께 확인한다.
3. 실제 포인터로 선택 묶음 드롭과 공유 클립 이동을 확인하고, 다른 인물의 연결이 보존되는지 확인한다.
4. Windows 패키징·설치 앱 검증과 실제 영상 얼굴/구간 품질 평가는 별도 검증으로 진행한다. 이 기록의 테스트 통과를 정확도 개선 결과로 재사용하지 않는다.

## 관련 기록

- [Person dev 병합과 무대 사용성 인계](23-person-highlight-dev-merge-and-stage-usability-handoff.md)
- [무대 하이라이트 작업 카드](../../../../../handoff/tasks/dance-highlight.md)
- Angular 작업 커밋의 `docs/superpowers/specs/2026-10-23-stage-result-usability.md`, `plans/2026-10-23-stage-result-usability.md`, `reviews/2026-10-23-stage-result-usability.md`는 구현 단계의 설계·검토 기록이다. 그 안의 “커밋·push·dev 병합 안 함”은 당시 상태이며, 최종 반영 상태와 최신 테스트 수는 이 문서의 커밋·검증 절을 따른다.
