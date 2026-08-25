# 밈 오버레이 재생 중 타임라인 seek 수정

## 문제

밈 오버레이 편집기에서 미리보기가 재생 중일 때 타임라인의 다른 지점을 클릭하면 빨간 playhead가 클릭 위치로 잠깐 이동한 뒤, 기존 재생 위치로 되돌아왔다. 멈춘 상태의 타임라인 클릭은 정상적으로 이동했다.

## 원인

타임라인의 `seekMs` 출력은 페이지에서 `MemeOverlayStore.currentMs`만 변경했다. 재생 중 `currentMs`는 배경 HTML video의 `timeupdate`가 공급하는 표시용 상태이며, 미리보기는 재생 중의 일반 clock feedback을 실제 media seek으로 처리하지 않는다. 따라서 배경 video의 `currentTime`은 기존 위치에 남아 있었고 다음 `timeupdate`가 Store 값을 덮어썼다.

미리보기 transport의 scrub은 별도 `syncPaused()`를 호출하므로 재생을 멈춘 뒤 media와 상태를 같이 이동시켰다. 타임라인은 같은 명령 경로가 없었다.

## 수정

Angular 페이지가 타임라인 클릭마다 단조 증가 ID를 가진 `timelineSeekRequest`를 생성해 미리보기에 전달한다. 이 입력은 일반 `currentMs` clock feedback과 구분되는 명시적 사용자 명령이다.

미리보기는 재생 중인 요청에 `MemePreviewCoordinator.seekWhilePlaying()`을 호출한다. 이 메서드는 배경 video의 `currentTime`을 새 시점으로 설정하고 활성 밈 slot을 같은 시점에 동기화하지만, 재생·RAF loop를 중단하거나 새로 시작하지 않는다. 멈춘 상태에서는 기존 `syncPaused()` 경로를 사용한다.

## 회귀 검증

- preview component: 재생 중 명시적 요청이 배경 시계를 새 위치로 seek하고 `play()`를 다시 호출하지 않는지 검증
- setup page: timeline의 `seekMs` 출력이 Store 시각뿐 아니라 preview의 명시적 seek 요청에도 연결되는지 검증
- focused Karma/Chrome suite: 41 SUCCESS

## 브랜치 범위

- 수정 브랜치: `fix/meme-overlay-timeline-seek` (Angular의 `merge/meme-overlay-into-dev` 기준)
- 최종 반영 대상: Angular `merge/meme-overlay-into-dev`만
- `dev` 및 원격 push/merge는 사용자의 별도 승인 없이는 수행하지 않는다.
