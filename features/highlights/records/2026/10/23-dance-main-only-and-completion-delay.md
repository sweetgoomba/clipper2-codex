# 2026-10-23 안무 메인 전용 분류·완료 지연 수정

## 사용자 요구와 원인

- ANTIFRAGILE 최근 완료 프로젝트의 카즈하 첫10개가 카즈하 메인 구간으로 보기 어렵다는 피드백. 안무는 해당 멤버가 메인인 구간만 자동 배정한다. 인물 하이라이트의 모든 등장 수집 정책을 안무에 적용하지 않는다.
- 저장 진단에서 카즈하 첫10개 모두 음수 main_track_id를 가진 주변 인물 보충 경로였다. member_coverage가 메인 선택 몸 밖의 보이는 얼굴을 별도 main 클립으로 추가했고, 이 프로젝트에178개를 추가했다. 얼굴 신원과 무대 메인 역할을 혼동한 정책 문제다.
- 분석 완료 뒤 결과보기 무반응·다음 큐 시작 지연도 함께 추적했다. Python TOTAL=03:56:00.273Z, jobs.finishedAt=03:56:00.878Z, 프로젝트 기록=03:57:54.269Z, Nest succeeded=03:57:54.677Z, 다음 작업 시작=03:57:54.678Z. 약114초 지연 후 큐는 즉시 다음 작업을 시작했다.
- jobs.json 약111.5MB를 모든 이벤트마다 직렬로 다시 저장했다. 이 잡 이벤트739개, 마지막1분331개가 들어와 저장 대기가 누적됐다. 완료 상태가 결과 프로젝트 준비보다 먼저 UI에 보일 수 있었다.

## 구현

### Python 안무

- 메인 선택 구간만 얼굴 분석 대상으로 전달한다. 주변 visible segment 추가·주변 얼굴 anchor 주입·주변 인물 클립 append를 제품 파이프라인에서 제거했다.
- 메인 몸에 연결된 얼굴 관측이 없으면 기존 확장 몸 crop 매칭 이름을 상속하지 않고 미분류로 유지한다.
- 단체 장면은 얼굴이 확인돼도 개별 멤버에게 자동 배정하지 않고 함께 등장·배정 대기에 둔다. 확인된 보이는 멤버는 진단 visible_reference_ids에만 보존한다. 사용자 수동 배정 API는 유지한다.
- 동일한 진행률·문구를 연속 중복 전송하지 않는다. 진단 버전 member_timeline_main_only_v3.
- 공통 AuraFace 모델·가중치·매칭 기준과 Person 파이프라인은 변경하지 않았다.

### 데스크톱 Nest

- JSON 저장 중 도착한 변경을 다음 사본 하나로 합친다. 각 호출은 자신의 변경이 포함된 사본의 저장을 기다리고 원자 교체·저장 실패 처리 계약을 유지한다.102번 쓰던 재현에서 최대2번으로 감소했다.
- 완료 결과를 먼저 jobs.json에 영속화한다. 결과 프로젝트 준비 중인 ID만 메모리 Set으로 추적해 공개 list/get과 snapshot에는 running·결과 정리 중으로 보여준다. 준비 후 완료를 노출한다.
- 앱이 준비 도중 종료돼도 저장된 completed/result를 기존 부팅 백필로 복구한다. completeCommitted의 기존 canonical commit 계약은 건드리지 않았다.
- 완료와 늦은 취소를 기존 lifecycle lock으로 직렬화한다. Set 정리는 완료 projection에만 finally로 적용해 이전 progress flush 반환이 마스크를 지우지 않게 했다.

## 검증과 한계

- 수정 전 회귀 실패 확인: 주변 C도 solo에 포함됨,102개 전체 파일 저장, 결과 준비 중 completed 노출, 메인 얼굴 근거 없는 이름 상속, 늦은 progress 반환 시 조기 completed 노출. 수정 후 해당 검사 통과.
- Python 안무·공통 얼굴·인물 관련507개 통과: /tmp/adlight-main-only-related-tests.log.
- Nest 최종 전체4,941개 통과: /tmp/adlight-completion-nest-suite-final-retry.log. 테스트용 CLIPPER_AUTH_MODE=local 및 loopback 허용. 실제 앱 JWT 설정은 변경하지 않았다. 최초 포트 EPERM, 개발 JWT 설정 혼입401, 생성자를 생략한 삭제 테스트 픽스처의 Set 초기화 누락은 원인을 구분하고 재검증했다.
- Python 전체 시도는1,658pass/7fail/6skip. 그 중2개는 최종 수정 전 로드된 테스트 픽스처의 owned_previews 누락으로, 최종507개 검사에서 수정·통과했다. 나머지5개는 변경 없는 원격 dev 임시 사본의 모듈을 직접 로드해 동일하게 재현했다(37pass/5fail). 따라서 전체 Python GREEN으로 주장하지 않는다.
- 기존 dev에서도 실패한 검사: test_annotation_layer_renderer의 counter_formats_value_and_matches_goldens, chip_tones_and_badge_goldens, arrow_goldens, arrow_target_above_golden; test_clipper_video_render_ranking_transitions의 real_render_list_holds_still_through_transitions_and_switches_at_handoff[fadeblack]. 이번 범위에서 렌더 구현이나 golden을 변경하지 않았다.
- 전체 로그 /tmp/adlight-main-only-python-suite-unrestricted.log, dev 비교 /tmp/adlight-main-only-python-render-baseline-isolated.log.
- ANTIFRAGILE 저장 얼굴 근거 재판정: main321→143, 카즈하 main71→21, 주변 보충178개 제외. /tmp/adlight-antifragile-main-only-replay.json. 원본부터 모델을 다시 실행한 정확도 평가가 아니며, 기존 프로젝트 결과·수동 편집·과금은 변경하지 않았다. 남은 메인 구간의 실영상 품질은 새 분석으로 확인해야 한다.
- 읽기 전용 독립 리뷰에서 재시작 결과 유실과 progress 경합을 발견·재현해 보완했다. 최종 리뷰 차단/중요 지적 없음.

## dev 병합·빌드

- 사용자 dev 병합 요청으로 최신 원격에서 분기한 두 작업을 커밋하고 충돌 없는 fast-forward 후 각 dev·작업 브랜치를 atomic push했다.
- Python ea2794088b8847879437f8d1f5c39949be0647bd / fix/dance-main-only-20261023.
- Nest 0fe9f8b0b827078e0455910ba24c62d2d0486ea8 / fix/job-completion-backlog-20261023.
- 두 원본 저장소 dev·clean·원격0/0, ls-remote 두 ref 동일, 검증 tree와 병합 tree 일치. 다른6개 저장소 소스 변경 없음.
- 최종 앱: /Users/jina/project/adlight/desktop/clipper_electron/dist-app-dance-main-only-20261023/mac-arm64/Clipper Studio (dev).app.
- 로컬 API3000·자동 업데이트 비활성화·arm64·asar main/electron-updater/fs-extra 확인. 최종 renderer136·Nest88 및 변경 Python2파일 SHA 일치. /tmp/adlight-dance-main-only-final-package-check.json, 빌드 로그 /tmp/adlight-dance-main-only-app-build-final-20261023.log.
- 현재 실행 중인 dist-app-person-picker-80px-20261023 앱과 작업은 유지했다. 새 빌드는 대기 상태이며 현재 앱에 자동 반영되지 않는다. 기존 결과를 다시 계산하거나 새 프로젝트를 대신 실행하지 않았다. Windows 재검증은 하지 않았다.


## 후속 — 사용자 요청 재빌드·실행 완료

- 사용자 “다시 빌드해서 띄워줘” 요청으로 데스크톱4개 원본 dev를 fetch 확인했다. Angular af8fe16e·Electron dfc84d4·Nest0fe9f8b0·Python ea27940이며 모두 origin/dev와0/0이다.
- 원본 Electron에서 npm run build:app:mac:arm64:local-api 재실행 성공. 새 앱 /Users/jina/project/adlight/desktop/clipper_electron/dist-app/mac-arm64/Clipper Studio (dev).app 을 실제 실행했고 해당 renderer index.html#/projects 홈·인증 상태·프로젝트 목록을 확인했다. 앞서 대기시킨 별도 출력 앱 대신 기본 dist-app 패키지다.
- renderer136·Nest88·Python265파일 전체 SHA 일치, arm64·API3000·자동 업데이트 비활성화·asar main/electron-updater/fs-extra 확인. Web API health200 및3개 DB ok. 기존 API3000·클라이언트4201·어드민4202 프로세스를 유지했다.
- 시작 전 기존 앱은 종료돼 있었다. 종료된 앱의 running 기록1개는 새 앱의 기존 재시작 복구 정책에 따라 “앱 종료로 작업 미완료”로 표시됐다. 실행 중 앱/작업을 에이전트가 강제 종료하거나 재실행하지 않았다. 기존 완료 결과는 그대로이며 새 분류 정책은 새 분석에 적용한다.
- 로그 /tmp/adlight-dev-rebuild-launch-20261023.log, 검증 /tmp/adlight-dev-rebuild-launch-package-check-20261023.json. 이번 빌드에서 소스 수정·새 커밋·DB 초기화는 하지 않았다.
