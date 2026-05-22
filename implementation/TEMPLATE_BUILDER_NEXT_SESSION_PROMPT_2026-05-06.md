# Template Builder Next Session Prompt

작성일: 2026-05-06
용도: 다음 Codex 세션에서 그대로 붙여 넣을 인계 prompt

## 붙여 넣을 문장

```text
Using Superpowers.
Clipper2 템플릿 생성기 설계를 이어서 진행하자. 먼저 `.codex/README.md`, `.codex/design/LEGACY_CLIPPER1_TEMPLATE_SYSTEM_2026-05-06.md`, `.codex/design/TEMPLATE_BUILDER_DESIGN_BRIEF_2026-05-06.md`, `.codex/implementation/TEMPLATE_BUILDER_NEXT_SESSION_PROMPT_2026-05-06.md`를 읽어.

지금까지 확정된 결정은 유지해:
- 템플릿 생성기는 플러그인이 아니라 top-level `템플릿` 메뉴다.
- 생성된 템플릿은 Clipper1뿐 아니라 Variation과 향후 숏츠 출력 plugin들이 공유한다.
- 기존 Clipper1 템플릿 적용 결과와 최종 출력물이 호환되어야 한다.
- 저장소는 지금은 local filesystem이어도 나중에 DB/API로 갈아끼울 수 있게 repository/adapter로 추상화한다.
- 기본 제공 템플릿과 사용자 custom template은 분리한다.
- export/import는 만들지 않는다.
- ratio는 `16:9`, `4:3`, `1:1`, `full` 네 개만 지원한다.
- UI에는 `variant 추가`, `없는 비율 만들기` 같은 버튼을 두지 말고, 네 개 ratio 슬롯의 상태로 표현한다.
- 템플릿은 `draft`와 `published`를 분리하고, published만 workflow plugin에서 선택 가능하다.
- publish 전에는 schema validation과 3-5초 sample mp4 test render가 필요하다.
- 1차 editor는 기존 Clipper1 고정 레이어만 지원한다.

마지막 요구사항을 최우선으로 반영해:
캔버스 영역이 너무 넓으니 줄이고, 속성 영역을 더 넓게 만들고, 컬러 팔레트와 텍스트별 스타일 속성(폰트/크기/색상/위치/박스/윤곽선/그림자)을 제대로 보여주는 한국어 editor mockup v4부터 다시 제안해줘.

아직 구현하지 말고, mockup v4와 설계 변경점을 먼저 정리해서 컨펌을 받아.
그리고 문서화가 필요한 결정이나 진행 내용은 `.codex`와 `.codex/session-logs/YYYY-MM-DD.log`에 계속 남겨.
```

## 다음 세션 체크리스트

- `.codex/README.md`를 먼저 읽는다.
- legacy template 분석 문서를 읽는다.
- template builder brief를 읽는다.
- session log에 시작 기록을 남긴다.
- editor mockup v4를 한국어로 다시 그린다.
- canvas 영역을 줄이고 properties 영역을 넓힌다.
- color palette를 추가한다.
- 텍스트 레이어별 box/outline/shadow controls를 빠뜨리지 않는다.
- 사용자 컨펌 전에는 구현하지 않는다.
