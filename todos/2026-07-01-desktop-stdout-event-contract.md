# Desktop Stdout Event Contract Follow-up

작성일: 2026-07-01

## 배경

desktop plugin child process stdout은 기본적으로 `v:1` JSON Lines 로그 계약을 따른다.
다만 현재 일부 모델 다운로드 진행률은 stdout으로 `{"type":"download_progress", ...}` 형태의
제어 이벤트를 내보내고, Electron main이 이를 UI 진행률 이벤트로 소비한다.

현재 진행률 표시가 깨진 것은 아니다. Electron log funnel이 비 `v:1` 라인을 로그 파일에 쓸 때는
`v:1` 형태로 감싸므로 로그 파일 유효성도 유지된다.

## TODO

- stdout을 로그 전용 채널로 유지할지, 다운로드 진행률 같은 제어 이벤트도 허용할지 명시적으로 결정한다.
- 제어 이벤트를 계속 stdout에 둘 경우 허용 이벤트 schema와 parser 위치를 문서화한다.
- 가능하면 장기적으로는 plugin runtime 이벤트 채널과 로그 채널을 분리한다.
- 변경 시 Electron `PluginProcess` parser, Python plugin SDK progress emit, 로그 뷰어 기대값을 함께 검증한다.

## 비범위

- 이번 dance highlight 정확도 개선 작업에서는 변경하지 않는다.
- 현재 진행률 UI 동작을 막는 버그로 취급하지 않는다.
