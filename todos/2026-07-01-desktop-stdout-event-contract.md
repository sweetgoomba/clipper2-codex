# Desktop Stdout Event Contract Follow-up

작성일: 2026-07-01
상태: 2026-07-02 문서화 완료

## 배경

desktop plugin child process stdout은 기본적으로 `v:1` JSON Lines 로그 계약을 따른다.
다만 현재 일부 모델 다운로드 진행률은 stdout으로 `{"type":"download_progress", ...}` 형태의
제어 이벤트를 내보내고, Electron main이 이를 UI 진행률 이벤트로 소비한다.

현재 진행률 표시가 깨진 것은 아니다. Electron log funnel이 비 `v:1` 라인을 로그 파일에 쓸 때는
`v:1` 형태로 감싸므로 로그 파일 유효성도 유지된다.

## 결정

현재 결정은 `.codex/design/DESKTOP_STDOUT_AND_CONTROL_EVENT_CONTRACT_2026-07-02.md`에 정리했다.

- stdout은 기본적으로 로그 채널이다.
- 예외적으로 Python plugin startup/model-install 단계의 `model_loading`, `download_progress`
  제어 이벤트만 stdout에서 허용한다.
- 일반 job progress는 stdout이 아니라 plugin HTTP runtime의 WebSocket progress 계약을 사용한다.
- 새 stdout event shape를 추가하려면 schema, parser 위치, IPC/API consumer, 테스트 대상을 먼저 문서화한다.

## 장기 TODO

- plugin runtime 이벤트 채널과 로그 채널을 물리적으로 분리한다.
- 분리 작업을 시작할 때 Electron `PluginProcess` parser, Python plugin SDK progress emit,
  Angular model-download UI, 로그 뷰어 기대값을 함께 검증한다.

## 비범위

- 이번 dance highlight 정확도 개선 작업에서는 변경하지 않는다.
- 현재 진행률 UI 동작을 막는 버그로 취급하지 않는다.
