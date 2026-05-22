# Build and Packaging Long-Term TODO Catalog - 2026-05-10

이 문서는 이번 세션에서 정리한 빌드/패키징 판단과, 앞으로도 장기적으로 남겨둘 TODO를 카테고리별로 고정한다.
이 항목들은 **다음 세션의 즉시 작업 목록이 아니라**, 나중에 별도 판단이 필요할 때 다시 꺼내 볼 보류 목록이다.

## 이번에 정리한 것

- `clipper_electron/src/main/setup/first-run.ts`에서 `userData/clipper_venv` 전체 삭제는 제거했다.
- 이유:
  - 앱 시작마다 venv를 통째로 재생성하는 것은 과하다.
  - 첫 실행/업데이트가 아닌 일반 실행까지 느리게 만든다.
  - 현재 문제는 venv 삭제로 푸는 문제가 아니었고, Python 렌더러 코드 자체를 바로잡는 쪽이 정답이었다.
- 유지한 것:
  - `--reinstall-package clipper-plugin-clipper1-video-render`
  - local workspace package의 source-only 변경을 packaged venv에 반영하기 위해서는 여전히 의미가 있다.

## 카테고리: Build / Packaging

### TODO: packaged venv invalidation 전략 정리

- 상태: 장기 보류
- 이유:
  - 현재는 `uv sync --reinstall-package`로 source-only 변경을 반영한다.
  - 이것은 동작하지만, “왜 이 패키지만 매번 다시 깔아야 하는가”를 코드 구조로 더 명시할 여지가 있다.
- 후보:
  - 패키지 버전에 build hash를 넣어 변경 감지를 명시적으로 만들기
  - 앱 버전/빌드 번호 기준으로 venv를 다시 만들지 결정하기
  - local workspace package의 배포 단위를 더 명확히 분리하기

### TODO: local Python package refresh 정책 문서화

- 상태: 장기 보류
- 이유:
  - `clipper-plugin-sdk`, `clipper-plugin-dance-highlight`, `clipper-plugin-dialog-highlight`, `clipper-plugin-clipper1-video-render`는 모두 로컬 소스 패키지다.
  - source-only 변경이 있는 경우 어떤 패키지를 강제 재설치할지 규칙을 문서로 고정해야 한다.

## 카테고리: Renderer Parity

### TODO: preview/final contract drift 감시

- 상태: 진행 중
- 이유:
  - Template Builder는 preview와 final render가 같은 geometry contract를 써야 한다.
  - pixel parity보다 contract parity를 먼저 보게 해야 한다.

### TODO: layout image / crop / overlay 합성 규칙 단일화

- 상태: 진행 중
- 이유:
  - layout image는 ratio 공통 template asset이고, preview와 final이 같은 visible intersection 규칙을 써야 한다.
  - renderer마다 좌상단 crop, stretch, cover-fit이 다시 섞이면 같은 문제가 반복된다.

## 카테고리: Template Builder UX

### TODO: read-only template editing rules 정리

- 상태: 진행 중
- 이유:
  - read-only legacy template에서는 선택/편집/상태 표기를 더 강하게 막아야 한다.
  - 사용하지 않는 layer는 preview와 property panel에서 같이 사라져야 한다.

### TODO: subtitle/title line mode UX 단일화

- 상태: 진행 중
- 이유:
  - 한 줄/두 줄 허용 여부와 각 줄의 위치 편집 규칙을 더 명확히 분리해야 한다.
  - 자막 박스 같은 중간 개념은 UI에서 제거된 상태를 유지해야 한다.

## 카테고리: Verification / Operations

### TODO: packaged smoke checklist 축약

- 상태: 장기 보류
- 이유:
  - 지금은 로그/파일/샘플 렌더를 함께 봐야 해서 확인 항목이 길다.
  - 다음 세션에서 바로 따라할 수 있는 짧은 smoke checklist가 있으면 좋다.

### TODO: session log format 축약 유지

- 상태: 결정 완료
- 이유:
  - 세션 로그는 자세한 설명보다, 결정/수정/검증/다음 액션만 남기는 쪽이 토큰 효율이 좋다.
