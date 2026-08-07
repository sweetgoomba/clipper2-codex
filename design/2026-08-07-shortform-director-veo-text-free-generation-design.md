# Shortform Director Veo 무텍스트 영상 생성 — 설계 (Spec)

> 작성일: 2026-08-07 · 대상 레포: `desktop/clipper_nestjs`, `web/clipper_web_api` · 관련: AI 영상 생성 모델별 프롬프트 정책

## 1. 개요 · 범위

Veo 3.1 Lite/Fast로 새 스토리보드를 만들 때 공급자 생성 영상 픽셀 안에
글자·숫자·자막·라벨·간판·UI 문구·타이포그래피를 만들도록 요구하지 않는다.
Veo의 텍스트 렌더링 품질 문제를 피하되, Clipper 템플릿 방식의 TTS 자막과
타이틀 합성 책임은 유지한다.

## 2. 결정 로그 (Decision Log)

| # | 결정 | 비고 |
|---|---|---|
| 1 | Veo 3.1 Lite/Fast만 생성 영상 내부 텍스트를 금지한다 | Gemini Omni와 Seedance의 기존 정책은 유지 |
| 2 | 스토리보드 추론 입력에 명시적인 visual policy를 전달한다 | 새 `generationBrief`가 처음부터 무텍스트 영상 연출로 작성됨 |
| 3 | 실제 공급자 프롬프트에서도 Veo 무텍스트 규칙을 다시 강제한다 | 저장된 계획이나 모델 응답 실수에 대한 실행 경계 보호 |
| 4 | Clipper 자막·타이틀은 제거하지 않는다 | AI 생성 영상 픽셀과 최종 합성 레이어의 책임을 분리 |

## 3. 디자인 / 아키텍처

`clipper_nestjs`가 선택 모델에서 `generatedVideoText: false` 정책을 파생해
스토리보드 추론 입력으로 전달한다. `clipper_web_api`의
`scene-media-decision` 프롬프트는 이 값이 `false`이면 `onScreenText`를
영상 내부에 렌더링하지 않고, 같은 내용을 텍스트 없는 피사체·행동·공간·카메라
연출로 표현하도록 지시한다.

컷 생성 시 `clipper_nestjs`는 Veo 프롬프트 끝에 무텍스트 제약을 추가한다.
이 규칙은 Clipper가 최종 렌더에서 합성하는 자막이나 타이틀에는 적용되지 않는다.

## 4. 상세 설계

- Veo: 문자, 숫자, 자막, 캡션, 라벨, 간판 문구, 로고 문자, UI 텍스트,
  타이포그래피를 생성 영상에 포함하지 않는다.
- 비-Veo: 현재의 scene-native 텍스트 생성 정책을 유지한다.
- `videoPlan.scenes[].onScreenText` 데이터 자체는 유지한다. 이는 스토리보드
  정보와 Clipper 합성 경계를 위한 데이터이며 Veo 픽셀 생성 지시로 쓰지 않는다.
- 기존에 저장된 스토리보드나 이미 생성된 영상은 수정하지 않는다.

## 5. 인터페이스 · API 접점

내부 추론 입력의 `aiVideoProduction`에 다음 정책을 추가한다.

```json
{
  "visualPolicy": {
    "generatedVideoText": false
  }
}
```

공용 HTTP 엔드포인트나 응답 스키마는 변경하지 않는다.

## 6. 미결 (TBD)

없음.

## 7. 범위 외

- 기존 Veo 스토리보드 자동 마이그레이션
- OCR 기반 생성 결과 검수
- Clipper 자막·타이틀 디자인 변경
- Gemini Omni 또는 Seedance의 텍스트 정책 변경
