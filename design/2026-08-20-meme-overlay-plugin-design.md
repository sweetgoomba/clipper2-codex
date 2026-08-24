# 밈 오버레이 플러그인 — 교차 레포 설계 (MVP)

> 작성일: 2026-08-20
> 상태: Plan 1·2·3 구현 및 검증 완료 (2026-08-24)
> 대상 레포: `clipper_angular`, `clipper_nestjs`, `clipper_python`, `clipper_web_api`, `.codex`
> 패키징 확인: `clipper_electron`(코드 변경은 원칙적으로 없음)
> 기준 목업: `.superpowers/brainstorm/76135-1787177041/content/meme-overlay-editor-layout.html`
> 관련 구현: 댓글 오버레이, 영상 랭킹, 공용 소스 인제스트·Range 스트리밍, 공용 영상 렌더 잡
> 구현 계획: [1. 카탈로그·캐시](./2026-08-20-meme-overlay-plan-1-catalog-cache.md) · [2. 편집기·프리뷰](./2026-08-20-meme-overlay-plan-2-editor-preview.md) · [3. 렌더·재편집](./2026-08-20-meme-overlay-plan-3-render-integration.md)
> 구현 기록: [밈 오버레이 구현 기록](../features/clipper-studio/records/2026/08/2026-08-20-meme-overlay-implementation-record.md)

## 1. 개요 · 목표

사용자가 배경 쇼츠를 불러온 뒤, 클리퍼 스튜디오가 제공하는 짧은 밈 영상을 원하는 시점과 위치에 얹어 새 9:16 영상을 만드는 `밈 오버레이` 가상 워크플로 플러그인을 추가한다.

첫 카탈로그는 고양이 밈으로 시작하지만 런타임 모델은 고양이에 종속하지 않는다. 제작 단계에서 투명 VP9 WebM으로 표준화할 수 있는 짧은 영상·GIF라면 같은 카탈로그와 편집기에 넣을 수 있다.

이 기능의 제품 목표는 댓글 오버레이와 같다.

- AI 분석이나 고비용 모델 없이도 결과물이 눈에 띄어야 한다.
- 기존 소스 인제스트, 미디어 스테이지 공용 primitive, 프로젝트 매니페스트, 작업 큐, FFmpeg 렌더 경로를 최대한 재사용한다.
- 밈 미디어를 Electron 설치 파일에 포함하지 않는다.
- 저사양 PC를 고려해 메인 미리보기의 동시 밈 영상은 최대 2개로 제한한다.

## 2. MVP 범위

### 2.1 포함

1. 플러그인 스토어에서 `밈 오버레이` 설치·제거, 설치 시 내비게이션 노출
2. 배경 영상 입력
   - 로컬 영상 파일
   - YouTube URL 다운로드
3. 원격 밈 카탈로그
   - 페이지당 12개
   - 이름·태그 검색
   - 투명한 움직이는 카드 프리뷰
4. 밈 인스턴스 편집
   - 현재 플레이헤드 위치에 추가
   - 같은 밈 여러 번 추가
   - 타임라인 좌우 이동
   - 양 끝 핸들로 소스 시작·끝 트림
   - 9:16 스테이지에서 이동·등비 리사이즈
   - 효과음 켜기/끄기·볼륨
   - 맨 앞으로 보내기
   - 삭제
5. 동적 타임라인
   - 배경 영상 1줄 고정
   - 겹침이 없으면 오버레이 1줄
   - 겹침이 있을 때만 오버레이 2줄
   - 어느 시점에도 밈은 최대 2개만 활성
6. 브라우저 실시간 미리보기
   - 배경 `<video>` 1개
   - 오버레이 `<video>` 슬롯 최대 2개
   - 재생·일시정지·스크럽·타임라인 동기화
7. 최종 렌더
   - 1080×1920 MP4
   - 밈 투명도, 위치, 크기, 타이밍, 앞뒤 순서 반영
   - 배경 원본 소리와 밈 효과음 믹스
8. 결과물을 작업물에 저장하고 다시 편집
9. 밈 프리뷰·오버레이 파일의 로컬 디스크 캐시

### 2.2 범위 외

- WebGL 크로마키
- 브라우저에서 초록 배경을 실시간 제거하는 기능
- FFmpeg로 임시 프리뷰 영상을 만들어 재생하는 기능
- 자동 성능 저하 감지·자동 화질 전환
- 동시 밈 3개 이상
- 회전, 좌우 반전, 키프레임 이동·확대 애니메이션
- 사용자가 자기 밈 파일을 업로드하여 카탈로그에 추가하는 기능
- 런타임에서 GIF를 직접 재생·렌더하는 별도 경로
- 카탈로그 관리자 화면·웹 콘솔
- 앱 설치 시 전체 밈 팩 사전 다운로드
- 오프라인 최초 사용 보장
- ProRes 4444를 포함한 대용량 알파 마스터 배포

GIF나 다른 투명 영상은 **카탈로그 게시 전에 공용 투명 WebM으로 변환**한다. 따라서 런타임은 입력 원본 형식과 무관하게 한 형식만 다룬다.

## 3. 기존 기능 조사 결과와 재사용 경계

### 3.1 댓글 오버레이의 실제 구조

댓글 오버레이는 다음 구조다.

1. Angular가 로컬 파일 또는 YouTube URL을 로컬 Nest의 소스 모듈에 인제스트한다.
2. 배경 영상은 `GET /v1/sources/stream?path=...`의 HTTP Range 응답을 `<video>`에 연결해 재생한다.
3. 댓글 카드는 프론트의 HTML/CSS 레이어다. 댓글 자체를 영상으로 스트리밍하지 않는다.
4. 댓글 카드 위치·크기는 캔버스 대비 퍼센트 `x/y/w/h`로 저장한다.
5. 최종 생성 시 Nest가 댓글별 시간창을 RenderRecipe로 만들고 Python이 댓글 PNG를 생성해 FFmpeg로 굽는다.

재사용할 부분:

- 로컬/YouTube 소스 입력과 다운로드
- 로컬 영상 Range 스트리밍
- 9:16 스테이지의 공용 레이아웃 primitive와 포인터 기반 이동·리사이즈 순수 계산
- 퍼센트 좌표 계약
- 프로젝트 매니페스트, 렌더 예약·작업 큐·보관함 이동
- 플러그인 스토어의 가상 워크플로 설치 게이팅

새로 필요한 부분:

- 원격 밈 카탈로그
- 밈 파일 다운로드·무결성 확인·디스크 캐시
- 동영상 레이어용 2레인 타임라인
- 배경 영상과 최대 2개 투명 영상의 브라우저 동기 재생
- FFmpeg의 타임드 알파 동영상 합성 및 밈 오디오 믹스

### 3.2 기존 타임라인 재사용 여부

댓글 오버레이에는 여러 오버레이 클립을 자유롭게 배치하는 멀티트랙 타임라인이 없다. 댓글은 `시퀀스 시작 + 댓글별 재생시간`으로 순차 배치된다.

영상 랭킹에는 소스 구간 트리머와 전체 재생 시각 동기화가 있으므로 다음 계산과 포인터 처리 패턴은 재사용할 수 있다.

- 시작·끝 핸들 드래그
- 플레이헤드 스크럽
- 소스 시각과 전체 타임라인 시각 변환
- `<video>` 소스 교체·시크

그러나 밈의 동적 1~2레인 배치 컴포넌트는 새로 구현한다.

### 3.3 코드 재사용 원칙: 복제가 아니라 직접 호출·좁은 공용 추출

이 문서에서 `재사용`은 댓글 오버레이 폴더를 복사해 이름만 바꾸는 것을 뜻하지 않는다. 다음 세 규칙을 적용한다.

1. **이미 공용인 코드는 그대로 호출한다.** 새 wrapper나 사본을 만들지 않는다.
2. **기능 내부에 있지만 의미가 완전히 같은 계산은 작은 공용 코드로 추출한다.** 기존 기능도 새 공용 코드를 사용하도록 함께 바꾼다.
3. **화면 모양만 비슷하고 도메인 의미가 다른 코드는 억지로 합치지 않는다.** 이 경우 새 기능 전용 코드를 만들되 기존 구현을 복사하지 않고 필요한 공용 primitive 위에서 작성한다.

| 대상 | 구현 방식 | 복제하지 않는 것 |
|---|---|---|
| 파일/YouTube 소스 입력 UI | 기존 `@shared/highlight-setup/source-input`의 `SourceInputComponent`를 직접 import | 댓글 인테이크 HTML·이벤트 핸들러 |
| 소스 인제스트·영상 probe·stream URL | `SourceInspectService` 위에 얇은 공용 `VideoSourceIngestService`를 두고 댓글·랭킹·밈을 이 서비스로 이관 | 각 store의 로컬/YouTube 분기, `BackendLocator` 조회, stream URL 조립 |
| 배경 영상 스트림 | 기존 `/sources/stream`을 그대로 사용 | 배경용 스트림 endpoint |
| 로컬 파일 Range 응답 | 현재 `SourcesController` 안의 byte-range 계산·응답 코드를 `core/http`의 공용 helper로 좁게 추출하고 소스·밈 controller가 함께 호출 | `resolveByteRange`, 200/206/416, stream close/error 처리 |
| 정규화 좌표 | 댓글 preview 내부의 px↔%·clamp 순수 계산을 `shared/media-stage` 유틸로 추출하고 댓글·밈이 함께 호출 | clamp와 pointer delta 수식 |
| 재생 버튼·진행바·시간 표시 | 댓글·랭킹에 반복된 transport를 작은 shared presentational component로 추출하고 세 preview가 이벤트로 제어 | play/pause 버튼, pointer scrub, 진행률·시간 포맷 markup |
| 페이지·오류·파일 선택·YouTube 로그인 | 기존 `PageComponent`, `FilePickerService`, `YoutubeAuthService`, 오류 배너·알림을 직접 사용 | 페이지 셸과 오류 처리 boilerplate |
| 렌더 예약·잡·보관함 | `VideoRenderService`에 `reserveAndSubmit` 형태의 공용 원자 연산을 추가하고 기존 댓글·랭킹·배리에이션과 밈을 이관 | 각 workflow의 reserve→submit→catch→failReserved 블록 |
| Python 영상 합성 | 기존 `filter_graph`, `AudioMixer`, segment renderer를 확장 | 독립된 두 번째 FFmpeg 렌더 파이프라인 |
| 가상 플러그인 설치 | 기존 plugin catalog와 `InstalledVirtualWorkflowsRepository`에 항목만 등록 | 별도 설치 저장소·설치 프로토콜 |

반대로 다음은 의미가 달라 새 기능 전용 코드가 필요하다.

- 댓글의 순차 `seqStart/perDur`와 다른 밈 interval·동적 레인 모델
- HTML/CSS 댓글 카드와 다른 투명 영상 슬롯 동기화
- 일반 사용자 소스 캐시와 다른, ID+버전+checksum 기반 원격 카탈로그 캐시
- 정적 PNG 댓글 합성과 다른 타임드 알파 동영상·효과음 합성

이 전용 코드는 댓글 store/component를 상속하거나 feature 간에 직접 import하지 않는다. 공용 계층만 의존한다. 또한 이번 기능을 이유로 댓글·랭킹·밈을 모두 포괄하는 거대한 `UniversalOverlayEditor`를 만들지 않는다. 실제로 동일한 부분만 작게 추출한다.

## 4. 확정 결정 로그

| # | 결정 | 이유 |
|---|---|---|
| D1 | 기능 ID는 `meme_overlay`, 표시명은 `밈 오버레이` | 고양이에 종속하지 않는 확장 가능한 이름 |
| D2 | 가상 워크플로 플러그인으로 등록 | 별도 ML 프로세스나 모델 설치가 필요 없음 |
| D3 | 밈 파일은 Electron 번들에 넣지 않음 | 설치 파일 크기를 카탈로그 규모와 분리 |
| D4 | 메인 미리보기는 HTML `<video>` 레이어 방식 | 위치 편집과 즉시 재생에 가장 단순하고 기존 Angular 구조와 잘 맞음 |
| D5 | WebGL과 FFmpeg 프리뷰는 MVP에서 제외 | 사용자 결정, 구현·운영 복잡도 억제 |
| D6 | 동시 활성 밈은 최대 2개 | 저사양 환경의 동시 디코딩 상한을 명확히 제한 |
| D7 | 레인은 저장하지 않고 시간 겹침에서 파생 | 겹침이 없으면 항상 한 줄에 모으려는 사용자 모델과 일치 |
| D8 | 좌표는 퍼센트가 정본 | 창 크기와 실제 1080×1920 출력 간 정합 유지 |
| D9 | 런타임 파일은 `card-preview.webm` + `overlay.webm` 2개 | 별도 렌더 원본 없이 선택 시 받은 투명 파일을 편집과 렌더에 공용 사용 |
| D10 | 카드와 메인 오버레이 모두 실제 투명 배경 | 카드 배경색·테마가 바뀌어도 재제작 불필요 |
| D11 | 파일 바이트는 Web API가 프록시하지 않고 CDN에서 받음 | API 서버 대역폭 절약, 대용량 응답과 메타데이터 계약 분리 |
| D12 | 다운로드 파일은 메모리가 아닌 `CLIPPER_DATA_DIR` 아래 디스크 캐시에 보존 | 앱 재실행·재방문 시 재다운로드 방지 |
| D13 | 플러그인 설치 자체는 미디어를 받지 않음 | 설치와 콘텐츠 사용을 분리 |
| D14 | 플러그인 첫 진입 시 1페이지 카드 프리뷰를 준비한 뒤 화면을 연다 | 사용자가 빈 카드 대신 움직이는 카탈로그를 즉시 보게 함 |
| D15 | 필요한 파일이 캐시에 없고 인터넷도 없으면 명시적 오류와 재시도 제공 | 오프라인 최초 사용은 요구하지 않음 |
| D16 | 메인 재생 중 카드 애니메이션은 모두 일시정지 | 메인 3개 디코더에 자원 집중 |
| D17 | 자동 저사양 감지·자동 품질 전환을 선구현하지 않음 | 실제 측정 전의 추측성 복잡도 방지 |
| D18 | 카탈로그 원본이 GIF·크로마키 MP4여도 게시 전에 투명 VP9 WebM으로 통일 | 프론트·렌더의 형식 분기 제거 |

## 5. 미디어 규격과 게시 파이프라인

### 5.1 런타임 파일 2종

| 파일 | 용도 | 영상 | 오디오 |
|---|---|---|---|
| `card-preview.webm` | 라이브러리 카드 | VP9 알파, 짧은 변 기준 최대 240px, 반복 재생 | 없음 |
| `overlay.webm` | 편집 스테이지 + 최종 FFmpeg 렌더 | VP9 알파, 콘텐츠 원본 해상도 유지 | Opus, 있으면 유지 |

`overlay.webm`이 편집 프록시이면서 렌더 입력이다. 사용자가 밈을 선택해 처음 타임라인에 추가할 때 이 파일을 받는다. 이후 `영상 생성`을 눌러도 별도의 `render-source.mp4`를 다시 받을 필요가 없다.

### 5.2 전처리

카탈로그 게시 도구는 입력 형식별로 다음을 수행한다.

1. 크로마키 MP4: 키 색 제거, 가장자리 blend와 green despill 적용
2. 알파 영상·GIF: 기존 알파 유지
3. 모든 프레임의 알파 영역 합집합을 구해 투명 여백을 자르고 안전 패딩을 추가
4. `overlay.webm` 생성
5. 같은 투명 소스에서 무음 저해상도 `card-preview.webm` 생성
6. duration, width, height, FPS, 오디오 유무, byte size, SHA-256 계산
7. 품질 확인용 임의 배경 합성 프레임 생성
8. 카탈로그 메타데이터 행 생성

프레임마다 다른 crop을 적용하면 피사체가 흔들리므로, 한 에셋의 모든 프레임에 **하나의 공통 알파 바운딩 박스**를 사용한다.

### 5.3 제공 샘플 실측

입력: `/Users/jina/Downloads/Angry cat green screen 1.mp4`

- 원본: H.264 + AAC, 1280×720, 30fps, 6.95288초, 249,879 bytes
- 전체 캔버스 투명 VP9 + Opus: 405,281 bytes
- 240px 카드 투명 VP9, 무음: 30,365 bytes
- 알파 영역 공통 crop 실험: 대략 362×646(패딩 포함)
- crop된 투명 VP9 + Opus: 413,989 bytes
- crop된 240px 카드: 56,644 bytes

이 한 샘플에서는 투명 공용 파일이 초록 H.264 원본보다 약 1.6배 컸지만, 절대 크기는 약 396KiB였다. crop은 파일 크기를 줄이지 않았으나 디코딩 픽셀 수와 편집 선택 박스의 투명 여백을 크게 줄였다. 따라서 crop은 용량 최적화가 아니라 **편집 UX와 디코딩 면적 최적화**로 채택한다.

FFmpeg가 VP9 알파를 읽을 때 현재 환경에서는 `libvpx-vp9` 디코더를 명시해야 알파가 보존됐다. 렌더 구현과 회귀 테스트에 이 조건을 고정한다.

이 측정은 단일 샘플 결과다. 모든 투명 파일이 원본보다 항상 크거나 작다는 일반 규칙으로 사용하지 않는다.

## 6. 전체 사용자 플로우

```text
플러그인 스토어에서 설치
  → 설치 상태만 로컬 JSON에 저장, 미디어 다운로드 없음
  → 내비게이션에 "밈 오버레이" 노출

플러그인 첫 진입
  → 로컬 Nest가 Web API에서 카탈로그 1페이지 메타데이터 요청
  → 1페이지의 card-preview.webm만 CDN에서 병렬 다운로드
  → 모든 카드의 준비 시도가 끝날 때까지 페이지 스피너
  → 준비된 카드로 소스 입력 화면 표시, 일부 에셋만 실패하면 그 카드에 재시도
  → 네트워크 전체가 실패하고 쓸 수 있는 캐시도 없으면 "인터넷 연결이 필요합니다" + 재시도

배경 쇼츠 입력
  → 로컬 파일 또는 YouTube URL을 기존 sources.ingest로 처리
  → 배경 Range 스트림 URL 생성
  → 편집 화면 진입

밈 카드 추가
  → 현재 플레이헤드 위치에 새 인스턴스 생성 시도
  → overlay.webm 캐시가 없으면 CDN 다운로드·검증
  → 준비 중인 타임라인 블록/스피너 표시
  → 준비되면 스테이지와 타임라인에서 편집 가능

영상 생성
  → Nest가 요청의 에셋 ID+버전을 다시 검증하고 캐시 파일 존재 확인
  → 없는 파일만 다운로드, 오프라인이면 생성 중단 및 명시적 오류
  → ProjectManifest/RenderRecipe 생성
  → Python+FFmpeg가 배경, 투명 밈, 오디오 합성
  → 작업 큐와 보관함에 결과 표시
```

다음 카탈로그 페이지로 이동할 때는 그 페이지의 카드 파일만 같은 방식으로 준비한다. 이미 검증된 파일은 디스크 캐시에서 즉시 재사용한다.

## 7. 화면·상호작용 설계

### 7.1 화면 구성

- 상단: 배경 파일명, 취소, 영상 생성
- 중앙 왼쪽: 9:16 미리보기와 재생 컨트롤
- 중앙 오른쪽 위: 검색 가능한 밈 라이브러리 12개 카드·페이지네이션
- 중앙 오른쪽 아래: 선택한 오버레이의 시간·위치·크기·효과음·앞뒤 순서 설정
- 하단: 배경 1줄 + 동적 오버레이 1~2줄 타임라인

기존 목업의 최대 3개 표시는 구현 전에 최대 2개로 수정한다.

### 7.2 카드 프리뷰

- 카드 배경과 분리된 실제 투명 `<video>`를 사용한다.
- muted, loop, playsinline으로 재생한다.
- 현재 페이지 안에서 화면에 보이는 카드만 재생 대상으로 삼는다.
- 메인 미리보기가 정지 상태일 때만 카드가 움직인다.
- 메인 미리보기 재생이 시작되면 모든 카드 영상을 pause한다.
- 페이지를 떠난 카드의 `src`는 해제하여 불필요한 버퍼를 유지하지 않는다.
- 개별 카드 로딩 실패는 해당 카드에 재시도 상태를 표시하며 전체 페이지를 깨지 않는다.

### 7.3 밈 추가

- 카드의 `+` 또는 더블클릭으로 추가한다.
- 기본 시작점은 현재 플레이헤드 시각이다.
- 기본 소스 구간은 밈 전체이며, 배경 끝을 넘으면 오른쪽을 배경 끝에 맞춰 자른다.
- 남은 배경 구간이 최소 0.5초보다 짧으면 추가하지 않고 이유를 표시한다.
- 해당 시간에 이미 밈 2개가 활성이라면 추가하지 않고 최대 2개임을 표시한다.
- 같은 카탈로그 에셋을 여러 인스턴스로 추가할 수 있다.

### 7.4 스테이지 편집

- 현재 시각에 활성인 밈만 스테이지에 표시한다.
- 밈을 클릭하면 선택한다.
- 본체 드래그는 이동, 모서리 핸들은 원본 비율을 유지한 확대·축소다.
- 좌표 정본은 `xPct/yPct/wPct/hPct`이며 화면에는 필요하면 1080×1920 기준 px를 함께 표시할 수 있다.
- 이동·리사이즈 결과는 전체 오버레이 바운딩 박스가 캔버스 안에 있도록 clamp한다.
- `맨 앞으로`는 선택 인스턴스의 z-order를 올린다. 동시 활성 두 밈의 합성 순서는 이 값으로 결정한다.
- 선택한 비활성 타임라인 블록을 클릭하면 플레이헤드를 그 블록 시작으로 옮겨 즉시 스테이지에 보이게 한다.

### 7.5 타임라인 의미

배경 줄은 소스 전체 길이를 나타내며 이동·트림하지 않는다.

오버레이 줄은 사용자가 소유하는 고정 트랙이 아니다. 모든 밈 인스턴스를 시작 시각 순으로 정렬한 뒤, 겹치지 않는 첫 번째 레인에 넣어 화면에 그린다.

```text
배경 영상       [==============================]
오버레이 1      [Angry]       [Laugh] [Dance]
오버레이 2          [Shock]
```

`Shock`가 `Angry`와 겹치므로 두 번째 레인이 생긴다. 겹치는 블록이 없어지면 두 번째 레인도 사라진다.

시간 구간은 반열림 구간 `[start, end)`로 계산한다. 한 밈이 5.0초에 끝나고 다른 밈이 5.0초에 시작하면 겹침이 아니다.

레인 배치 알고리즘:

1. `timelineStartMs`, 안정적인 ID 순서로 정렬
2. 레인 1의 마지막 종료보다 시작이 같거나 늦으면 레인 1
3. 아니면 레인 2의 마지막 종료보다 시작이 같거나 늦으면 레인 2
4. 둘 다 아니면 동시 3개가 되므로 유효하지 않은 편집

레인 번호는 파생값이라 프로젝트에 저장하지 않는다.

### 7.6 타임라인 편집 규칙

- 블록 본체를 좌우로 끌면 `timelineStartMs`만 바뀐다.
- 왼쪽 핸들은 `sourceStartMs`와 `timelineStartMs`를 함께 바꾸며 오른쪽 끝을 유지한다.
- 오른쪽 핸들은 `sourceEndMs`를 바꾼다.
- 핸들은 속도 변경이나 영상 늘이기가 아니라 소스 트림이다.
- 최소 길이는 0.5초다.
- 배경 범위를 벗어날 수 없다.
- 드래그 중 동시 3개가 되는 위치는 붉은 invalid ghost로 표시하고 pointer up 시 원래 값으로 되돌린다.
- 플레이헤드와 눈금은 모든 레인에 하나만 공유한다.

## 8. 프론트 미리보기 동기화

### 8.1 플레이어 수

메인 스테이지 DOM에는 다음 비디오 슬롯만 둔다.

- 배경 비디오 1개
- 오버레이 비디오 슬롯 2개

타임라인 인스턴스 수만큼 `<video>`를 만들지 않는다. 현재 활성 클립과 비어 있는 슬롯에서 준비할 수 있는 바로 다음 클립만 두 슬롯에 매핑한다.

### 8.2 기준 시계

배경 `<video>.currentTime`을 단일 기준 시계로 사용한다.

전역 시각 `t`에서 밈 인스턴스의 소스 시각은 다음과 같다.

```text
sourceTime = sourceStart + (t - timelineStart)
```

재생 중에는 `requestAnimationFrame` 루프가 배경 시각을 읽어 다음을 수행한다.

- 시작·종료 경계를 통과한 인스턴스 mount/unmount
- 새로 활성화된 밈을 정확한 소스 시각으로 seek 후 play
- 일시정지·종료 시 밈 pause
- 드리프트가 허용치(초기값 100ms)를 넘을 때만 밈 시각 교정

매 프레임마다 `currentTime`을 강제로 덮어쓰지 않는다. 그러면 디코더가 계속 seek하여 오히려 끊긴다.

스크럽 중에는 배경과 활성 밈을 pause하고 계산된 시각으로 seek한다. 메타데이터나 필요한 range가 아직 준비되지 않았을 때만 해당 레이어에 작은 로딩 상태를 표시한다.

### 8.3 재생과 버퍼링 기대치

선택된 `overlay.webm`은 로컬 디스크에서 localhost Range 스트리밍되므로 일반 인터넷 동영상처럼 매 재생마다 네트워크 버퍼링하지 않는다. 다만 최초 선택 다운로드, 최초 디코더 준비, 새로운 `src`로 교체하는 순간에는 짧은 준비 시간이 있을 수 있다.

MVP는 이 시간을 숨기기 위해 다음만 적용한다.

- 선택 직후 파일 다운로드가 끝나기 전에는 재생 가능한 상태로 표시하지 않음
- 비어 있는 오버레이 슬롯이 있으면 다음 시작 클립의 metadata를 미리 로드
- 메인 재생 중 카드 영상 pause
- 최대 배경 1 + 밈 2 디코더 유지

성능 저하 자동 감지는 구현하지 않는다.

## 9. 편집 데이터 모델

```ts
interface MemeOverlayProject {
  schemaVersion: 'meme-overlay-project.v1';
  source: {
    sourcePath: string;       // 로컬 Nest가 해석한 배경 파일 경로
    sourceLabel: string;
    durationMs: number;
    width: number;
    height: number;
  };
  instances: MemeOverlayInstance[];
}

interface MemeOverlayInstance {
  id: string;                // 한 프로젝트 안의 인스턴스 ID
  assetId: string;           // 카탈로그 에셋 ID
  assetVersion: string;      // 불변 CDN 버전
  assetName: string;         // 재편집 표시용 스냅샷
  sourceStartMs: number;
  sourceEndMs: number;
  timelineStartMs: number;
  transform: {
    xPct: number;
    yPct: number;
    wPct: number;
    hPct: number;
  };
  audio: {
    muted: boolean;
    volume: number;          // 0..1
  };
  zIndex: number;
}
```

파생값:

```text
durationMs  = sourceEndMs - sourceStartMs
timelineEnd = timelineStartMs + durationMs
lane        = 전체 instances의 interval partition 결과
active(t)   = timelineStartMs <= t < timelineEnd
```

`overlay.webm`의 로컬 절대 경로와 스트림 URL은 프로젝트에 저장하지 않는다. ID+버전으로 로컬 Nest에 다시 요청한다. 절대 경로를 저장하면 캐시 위치 변경·다른 OS·캐시 삭제 시 프로젝트가 깨진다.

## 10. 원격 카탈로그 (`clipper_web_api`)

### 10.1 저장 방식

MVP 카탈로그 메타데이터는 `clipper_web_api`가 읽는 작은 버전 관리 JSON으로 둔다. Postgres 테이블과 관리자 UI는 만들지 않는다.

- 페이지네이션·검색은 서버 메모리에서 수행한다.
- 미디어 파일은 버전이 포함된 불변 S3/CDN key에 둔다.
- 새 에셋 게시 시 파일 업로드, 카탈로그 JSON 갱신, Web API 배포가 필요하다.
- 숨겨진 구버전 메타데이터는 기존 프로젝트 재편집을 위해 유지한다.

카탈로그 갱신을 서버 재배포 없이 운영할 필요가 확인되면 후속으로 S3 manifest 또는 관리자 DB로 옮긴다. 데스크톱 API 계약은 유지한다.

### 10.2 Web API 계약

OpenAPI 정본은 `clipper_web_api/docs/api/openapi.yaml`에 먼저 추가한다.

```http
GET /meme-assets?page=1&limit=12&q=angry
Authorization: Bearer <user-access-token>
```

```json
{
  "items": [
    {
      "id": "angry-cat",
      "version": "v1",
      "name": "Angry cat",
      "tags": ["cat", "angry", "화남"],
      "durationMs": 6953,
      "width": 362,
      "height": 646,
      "hasAudio": true,
      "cardPreview": {
        "url": "https://cdn.example/.../v1/card-preview.webm",
        "mimeType": "video/webm",
        "sizeBytes": 56644,
        "sha256": "..."
      },
      "overlay": {
        "url": "https://cdn.example/.../v1/overlay.webm",
        "mimeType": "video/webm",
        "sizeBytes": 413989,
        "sha256": "..."
      }
    }
  ],
  "page": 1,
  "limit": 12,
  "total": 48,
  "hasNext": true
}
```

정확한 재편집·렌더 확인용:

```http
GET /meme-assets/{assetId}?version=v1
Authorization: Bearer <user-access-token>
```

두 endpoint 모두 `JwtAuthGuard`로 보호한다. 응답에는 파일 바이트가 아니라 CDN URL·크기·checksum이 들어간다.

### 10.3 콘텐츠 권리

유튜브에서 찾았다는 이유만으로 밈 파일을 제품 카탈로그에 재배포할 권리가 생기지 않는다. 제공 샘플은 기술 검증용이며, 운영 S3에는 회사가 사용·변형·재배포 권리를 확인한 에셋만 게시한다.

카탈로그 원본에는 내부 운영용으로 출처, 권리 확인 상태, 확인 일자를 기록하고 `approved`가 아닌 에셋은 API 목록에 내보내지 않는다. 이 검증은 출시 차단 조건이다.

## 11. 로컬 에셋 캐시 (`clipper_nestjs`)

### 11.1 디스크 구조

```text
CLIPPER_DATA_DIR/
  meme-assets/
    catalog-cache.json
    angry-cat/
      v1/
        card-preview.webm
        overlay.webm
        metadata.json
```

이 파일들은 메모리 캐시가 아니다. 재생 중 Chromium과 OS가 일부 디코딩 버퍼를 RAM/GPU 메모리에 올릴 수 있지만, 원본 파일의 보존 위치는 디스크다.

### 11.2 다운로드 규칙

- Web API가 준 URL 중 HTTPS와 허용된 CDN authority만 허용한다. 포트를 생략한 항목은 기본 HTTPS 포트만 허용하고, 비기본 포트는 allowlist에 `host:port`로 명시해야 한다. 사용자정보가 든 URL은 거부하며 signed CDN query는 허용한다.
- 응답 header 대기부터 body 스트리밍 완료까지 하나의 다운로드 deadline을 적용한다. 기본값은 60초다.
- 선언된 최대 크기와 실제 수신 byte 수 검사
- `.part` 임시 파일에 스트리밍 저장
- SHA-256 검증 성공 후 atomic rename
- 동일 ID+버전+variant의 동시 요청은 하나의 Promise로 합침
- 실패한 `.part` 파일 제거
- 완료 파일이 size+checksum과 맞으면 캐시 hit
- 카드 페이지 준비는 작은 동시성 제한(초기값 3)으로 병렬 다운로드
- 캐시 파일 전체를 Node Buffer로 읽지 않고 stream으로 기록

MVP는 자동 LRU 삭제를 넣지 않는다. 카드 파일과 선택한 짧은 오버레이만 쌓이는 실제 용량을 먼저 측정한다. 캐시 정리 기능이 필요해지면 앱 설정의 명시적 `밈 캐시 비우기`와 용량 상한을 후속으로 추가한다.

### 11.3 로컬 API 계약

카탈로그 페이지 준비:

```http
GET /v1/meme-overlay/catalog?page=1&limit=12&q=
```

Nest가 Web API 메타데이터를 받은 뒤 해당 페이지의 카드 파일을 캐시하고, Angular가 localhost에 붙일 상대 stream path를 반환한다.

Web API가 일시적으로 닿지 않으면 마지막으로 정상 저장한 `catalog-cache.json`에서 같은 검색·페이지를 복원한다. 캐시된 메타데이터와 카드 파일이 모두 있는 항목은 오프라인에서도 표시하고, 어느 쪽이든 빠진 항목은 준비 실패 상태로 반환한다.

```json
{
  "items": [
    {
      "id": "angry-cat",
      "version": "v1",
      "name": "Angry cat",
      "tags": ["cat", "angry", "화남"],
      "durationMs": 6953,
      "width": 362,
      "height": 646,
      "hasAudio": true,
      "cardStatus": "ready",
      "cardStreamPath": "/v1/meme-overlay/assets/angry-cat/stream?version=v1&variant=card"
    },
    {
      "id": "missing-cat",
      "version": "v1",
      "name": "Missing cat",
      "tags": ["cat"],
      "durationMs": 3000,
      "width": 640,
      "height": 360,
      "hasAudio": false,
      "cardStatus": "failed",
      "cardErrorCode": "meme_asset_network_required"
    }
  ],
  "page": 1,
  "limit": 12,
  "total": 48,
  "hasNext": true
}
```

`cardStatus`는 `ready | failed` 판별자다. `ready` 항목만 `cardStreamPath`를 가지며, `failed` 항목은 `cardErrorCode`로 해당 카드만 재시도한다. 카드 준비는 동시성 제한 안에서 모든 항목을 끝까지 시도하고 원래 순서를 보존한다. 하나 이상 준비되면 실패 항목도 같은 페이지에 유지하며, 비어 있지 않은 페이지에서 준비된 카드가 하나도 없을 때만 페이지 전체 `meme_catalog_unavailable`을 반환한다.

선택한 공용 오버레이 준비:

```http
POST /v1/meme-overlay/assets/angry-cat/prepare
Content-Type: application/json

{ "version": "v1" }
```

```json
{
  "assetId": "angry-cat",
  "version": "v1",
  "overlayStreamPath": "/v1/meme-overlay/assets/angry-cat/stream?version=v1&variant=overlay",
  "durationMs": 6953,
  "width": 362,
  "height": 646,
  "hasAudio": true,
  "cacheHit": false
}
```

Web API가 일시적으로 닿지 않아도 같은 ID+버전의 저장된 카탈로그 메타데이터와 checksum 검증된 `overlay.webm`이 모두 있으면 다운로드 없이 `cacheHit: true`로 반환한다. 둘 중 하나라도 없으면 `meme_asset_network_required`이며, 인증·권한·설정·계약 오류에는 이 fallback을 적용하지 않는다.

Range 스트림:

```http
GET /v1/meme-overlay/assets/{assetId}/stream?version=v1&variant=card|overlay
Range: bytes=...
```

이 endpoint는 ID·버전·variant로 캐시 경로를 내부 해석한다. Angular에 로컬 절대 경로를 노출하지 않는다.

### 11.4 오류

| code | 상황 | 사용자 메시지 |
|---|---|---|
| `meme_catalog_unavailable` | 카탈로그 메타데이터도 로컬 사본도 없음 | 인터넷 연결을 확인하고 다시 시도해 주세요. |
| `meme_asset_network_required` | 필요한 variant가 캐시에 없고 다운로드 실패 | 이 밈을 사용하려면 인터넷 연결이 필요합니다. |
| `meme_asset_integrity_failed` | size/checksum 불일치 | 밈 파일을 확인하지 못했습니다. 다시 다운로드해 주세요. |
| `meme_asset_not_found` | ID·버전이 카탈로그에 없음 | 더 이상 제공되지 않는 밈입니다. |

캐시된 파일이 있으면 인터넷이 없어도 그 파일은 쓸 수 있다. 다만 이것은 오프라인 보장 계약이 아니며, 누락 파일은 네트워크 없이는 사용할 수 없다.

## 12. 로컬 렌더 API와 매니페스트

### 12.1 요청

```http
POST /v1/meme-overlay/render
```

```ts
interface MemeOverlayRenderRequest {
  sourcePath: string;
  sourceLabel?: string;
  instances: Array<{
    id: string;
    assetId: string;
    assetVersion: string;
    assetName: string;
    sourceStartMs: number;
    sourceEndMs: number;
    timelineStartMs: number;
    transform: { xPct: number; yPct: number; wPct: number; hPct: number };
    audio: { muted: boolean; volume: number };
    zIndex: number;
  }>;
}
```

Nest DTO는 다음을 다시 검증한다.

- 최소 한 개 인스턴스
- 각 소스 구간 `0 <= sourceStart < sourceEnd <= asset.duration`
- 파생된 timeline end가 배경 길이 이내
- 위치·크기 0..100 및 캔버스 경계
- volume 0..1
- 같은 시점 최대 2개
- 요청의 asset ID+버전이 카탈로그에 존재
- 모든 `overlay.webm`의 캐시 파일 checksum

프론트 검증만 믿지 않는다.

### 12.2 매니페스트

새 `modules/meme-overlay-render/`는 공용 프로젝트 매니페스트와 기존 렌더 예약 서비스를 사용해 단일 배경 클립 매니페스트를 만든다. 댓글 오버레이 builder 파일을 복제하지 않고, 두 workflow에서 완전히 같은 매니페스트 조립 primitive가 확인되면 그 부분만 공용 helper로 추출한다.

- 배경: `media.source`
- 밈 에셋: `media.meme.{instanceId}`
- 결과: `renders/meme_overlay.mp4`
- `editState.memeOverlay`: §9의 프로젝트 상태
- `sourceAudioVolume: 1`
- output: 1080×1920, 배경 전체 duration
- workflow displayName: `밈 오버레이`

RenderRecipe의 `OverlayTrack` role에 `meme`을 추가한다. 각 track은 밈 artifact, 전역 시작·끝, source 시작, transform, audio, z-order를 가진다. `OverlayTrack`이 이미 `artifactId`, 시간창, params를 제공하므로 범용 타임라인 모델에 별도 평행 구조를 만들지 않는다.

Payload mapper는 이를 다음 계약으로 명시 변환한다.

```ts
meme_overlays: Array<{
  mediaUrl: string;
  timelineStartSec: number;
  timelineEndSec: number;
  sourceStartSec: number;
  xPct: number;
  yPct: number;
  wPct: number;
  hPct: number;
  muted: boolean;
  volume: number;
  zIndex: number;
}>;
```

`timeline*`은 출력 전체 기준임을 이름에 담는다. 댓글의 기존 `startSec/endSec`가 단일 세그먼트 로컬 축인 것과 섞지 않는다.

## 13. Python·FFmpeg 최종 합성

### 13.1 영상

`clipper_video_render`는 `meme_overlays`를 zIndex 순으로 정렬해 단일 배경 세그먼트 위에 차례로 합성한다.

각 밈 입력은 다음 의미를 갖는다.

```text
입력 seek       = sourceStartSec
입력 길이       = timelineEndSec - timelineStartSec
출력 PTS 시작   = timelineStartSec
크기            = 1080*wPct/100 × 1920*hPct/100
위치            = 1080*xPct/100, 1920*yPct/100
알파 디코더     = libvpx-vp9 명시
종료 동작       = eof_action=pass
```

배경은 댓글 오버레이처럼 원본 전체를 `contain`하여 자르지 않고, 남는 곳은 검정 레터박스로 둔다. Angular 스테이지도 같은 규칙을 사용한다.

개념 필터:

```text
[meme] trim → setpts(STARTPTS + timelineStart) → scale → format=yuva420p
[previous][meme] overlay(x,y, enable=between(t,start,end), eof_action=pass)
```

최종 출력은 기존 H.264 yuv420p MP4다. 투명도는 최종 영상에 남는 것이 아니라 배경과 이미 합성된다.

### 13.2 오디오

밈 파일의 Opus 오디오는 영상과 같은 source range로 자른 뒤 다음을 적용한다.

- muted면 제외
- volume 0..1 적용
- `timelineStartSec`만큼 `adelay`
- 전체 출력 길이로 trim
- 배경 원본 오디오와 `amix normalize=0`
- 최종 단계에 limiter 적용하여 동시 효과음의 clipping 완화

오디오 스트림이 없는 밈은 조용히 건너뛴다. 최대 두 밈이므로 배경을 포함해 동시에 섞이는 소스도 최대 3개다.

### 13.3 회귀 격리

`meme_overlays`가 없는 기존 payload에는 새 입력·필터·오디오 단계가 생기지 않아야 한다. 댓글·랭킹·숏폼의 기존 명령과 결과를 바꾸지 않는 회귀 테스트를 둔다.

## 14. 플러그인·레포 통합

### 14.1 `clipper_nestjs`

- `PLUGIN_CATALOG`에 `meme_overlay` 가상 워크플로 추가
- `VIRTUAL_WORKFLOW_PLUGINS` 추가
- `modules/meme-assets/`: Web API catalog client, disk cache, downloader, Range stream
- `modules/meme-overlay-render/`: DTO, manifest builder, render service/controller
- RenderRecipe role과 payload mapper 확장

`meme-overlay-render`는 workflow 고유 DTO 검증과 editState 조립만 소유한다. 렌더 예약, 실패 롤백, 소스 probe, 프로젝트 저장 코드는 기존 서비스를 호출한다.

플러그인 설치는 현재 댓글 오버레이처럼 이름만 `installed-virtual-workflows.json`에 기록한다. 에셋 캐시는 별도 모듈이며 설치 API의 부작용이 아니다.

### 14.2 `clipper_angular`

```text
src/features/meme-overlay/
  meme-overlay.providers.ts
  models/
    meme-overlay.ts
    meme-overlay-timing.ts
    meme-overlay-lanes.ts
  flow/
    meme-overlay.state.ts
    meme-overlay.store.ts
  services/
    meme-overlay-api.ts
  pages/
    meme-overlay-setup/
  components/
    meme-overlay-preview/
    meme-overlay-library/
    meme-overlay-settings/
    meme-overlay-timeline/
```

- 내비게이션 metadata, feature order, route guard, lazy component 등록
- 기존 `app-source-input`을 직접 사용
- `SourceInputComponent`는 실제 shared component를 직접 import하고, 댓글 페이지 파일을 복사하지 않음
- `VideoSourceIngestService`가 로컬/YouTube 인제스트와 stream URL 반환을 한 번만 구현
- 정규화 좌표의 순수 계산은 `shared/media-stage`로 추출해 댓글·밈 두 consumer가 사용
- 댓글·랭킹에 반복된 transport는 shared 표시 컴포넌트로 추출해 밈까지 세 consumer가 사용
- standalone + signals + 4-file component 규칙 준수
- 새 화면은 `<app-page>` 안에서 시맨틱 Material token 사용

### 14.3 `clipper_web_api`

- `modules/meme-assets/` 카탈로그 모듈
- JWT 보호 목록·상세 endpoint
- 버전 관리 JSON과 DTO
- OpenAPI 계약·예제

### 14.4 `clipper_python`

- 밈 카탈로그 게시용 전처리 스크립트
- `meme_overlays` 영상 필터 입력
- 밈 오디오 track builder
- 알파·위치·시간·z-order·오디오 테스트

### 14.5 `clipper_electron`

별도 밈 파일이나 Python 플러그인을 추가하지 않는다. 기존 Angular renderer와 Nest bundle, 기존 `clipper_video_render` 업데이트가 패키징에 포함된다.

확인 항목만 있다.

- 패키징된 Chromium에서 VP9 알파 WebM 재생
- 패키징된 FFmpeg/libvpx에서 알파 렌더
- 설치 파일에 `meme-assets/*.webm`이 들어가지 않음
- 변경 전후 installer size 비교

## 15. 성능 정책과 측정

### 15.1 MVP 정책

- WebGL 없음
- FFmpeg 프리뷰 없음
- 자동 성능 감지 없음
- 메인 영상 최대 3개 동시 디코딩
- 카드 영상은 메인 재생 중 정지
- 타임라인 인스턴스별 `<video>` 생성 금지
- 파일은 로컬 디스크 캐시에서 Range 재생

### 15.2 구현 후 수동 검증

자동 감지 코드를 만들기 전에 실제 앱으로 다음을 측정한다.

- 배경 1 + 밈 0/1/2 재생의 CPU, GPU, 메모리
- 재생 시작 준비 시간
- 10초 앞뒤 스크럽 후 화면이 맞는 데 걸리는 시간
- 2개 밈 시작·종료 경계의 프레임 드롭·오디오 싱크
- 4GB RAM 문서용 노트북 또는 동급 저사양 장비
- macOS arm64와 Windows x64 패키징 앱

저사양에서 문제가 확인되면 첫 대응은 모든 사용자에게 동일한 `overlay.webm` 해상도·비트레이트 조정이다. 자동 기기 판별이나 복수 화질 variant는 실제 필요가 입증된 뒤 별도 설계한다.

## 16. 테스트·완료 기준

### 16.1 순수 모델

- 반열림 구간 동시성 계산
- 최대 동시 2개 검증
- 동적 1~2레인 배치
- 경계가 같은 인접 클립은 같은 레인
- drag/trim의 배경 범위·최소 길이 clamp
- 퍼센트 좌표·등비 리사이즈·캔버스 경계
- z-order 정규화

### 16.2 Angular

- 첫 페이지 준비 중 spinner와 실패 재시도
- 투명 카드 동영상 렌더
- 메인 재생 시작 시 카드 pause
- 선택 시 overlay 준비를 한 번만 호출
- 배경+활성 밈 시각 동기화
- 비활성 인스턴스용 video element를 만들지 않음
- 두 레인 이상 생성되지 않음
- 세 번째 겹침 편집 거부
- 저장 요청에 ID+버전·시간·transform·audio·zIndex 전달
- 프로젝트 다시 열기 복원

### 16.3 Nest

- 카탈로그 bearer token 전달
- 페이지 카드 prefetch와 cache hit
- atomic download·checksum 실패 정리
- 같은 파일 동시 다운로드 합침
- Range 200/206/416
- 경로 traversal 차단
- 허용 CDN host·HTTPS·size 제한
- 렌더 DTO에서 동시 3개 거부
- 캐시 누락+오프라인 오류 code
- 매니페스트 라운드트립

### 16.4 Python

- VP9 알파가 임의 배경 위에 실제 합성되는 프레임 테스트
- x/y/w/h 정규화 좌표와 1080×1920 픽셀 결과
- source trim과 timeline start
- 두 밈 z-order
- EOF 뒤 마지막 프레임이 남지 않음
- 배경+밈 효과음 시각·볼륨
- muted/no-audio 분기
- `meme_overlays` 없는 기존 payload 명령 회귀

### 16.5 사용자 시나리오 완료 기준

1. 플러그인 설치 후 앱 설치 파일 크기와 무관하게 카탈로그가 열린다.
2. 첫 진입에서 12개 투명 움직이는 카드가 준비되고, 네트워크 실패 시 이유와 재시도가 보인다.
3. 한 밈을 현재 시각에 추가해 스테이지에서 이동·확대하고 효과음을 들을 수 있다.
4. 겹침이 없으면 배경+오버레이 두 줄만 보인다.
5. 두 밈을 겹치면 두 번째 오버레이 줄이 생기고, 세 번째 겹침은 허용되지 않는다.
6. 생성 결과의 위치·크기·구간·앞뒤 순서·효과음이 프리뷰와 실질적으로 일치한다.
7. 같은 밈을 다시 사용할 때 CDN 다운로드가 발생하지 않는다.
8. 앱을 재시작해도 디스크 캐시를 재사용한다.
9. 저장된 프로젝트를 다시 열 때 누락된 에셋만 다운로드하며, 오프라인이면 명확히 안내한다.

## 17. 구현 순서의 큰 경계

상세 구현 계획은 이 문서 승인 후 별도 plan으로 작성한다. 순서는 다음 경계를 따른다.

1. **미디어 사전 검증**: 실제 Electron에서 투명 WebM 카드·스테이지 재생, 패키징 FFmpeg 알파 합성
2. **카탈로그·캐시**: Web API metadata, Nest disk cache/Range, 첫 페이지 UI
3. **편집기**: 소스 입력, 상태 모델, 동적 타임라인, 스테이지 합성·동기화
4. **렌더**: 매니페스트, payload, Python 영상·오디오 합성
5. **재편집·패키징·저사양 검증**

1단계가 실패하면 WebGL로 전환하지 않는다. 먼저 WebM 인코딩 규격이나 Chromium/FFmpeg 디코더 사용법을 바로잡는다. 제품 방향을 바꿔야 할 정도의 근본 제약이 확인될 때만 새 설계 결정을 사용자와 다시 논의한다.

## 18. 설계상 미결 없음 · 구현 중 수치 조정 가능 항목

MVP 기능 경계와 아키텍처 선택은 이 문서에서 닫는다. 다음 값은 의미를 바꾸지 않는 범위에서 샘플 팩·실기기 측정으로 조정할 수 있다.

- 크로마키 similarity, blend, despill 값
- VP9 CRF와 카드 해상도
- 카드 페이지 다운로드 동시성(초기값 3)
- 프리뷰 드리프트 교정 허용치(초기값 100ms)
- 기본 밈 크기·위치·효과음 볼륨

동시 오버레이 최대 2개, 2파일 전략, WebGL/FFmpeg 프리뷰 제외, 미디어를 Electron에 번들하지 않는 원칙은 수치 조정 대상이 아니다.

## 19. 구현 완료 시점의 실제 계약

2026-08-24 구현 완료 시점에는 다음 계약으로 동작한다. 설계 결정을 바꾸지 않고 실제 코드에서 확정된 이름과 기본값만 기록한다.

- 로컬 렌더 진입점은 `POST /v1/meme-overlay/render`, 출력 ID는 `output.meme_overlay.render.main`, 결과 경로는 `renders/meme_overlay.mp4`다.
- manifest → recipe → Python payload에는 선택된 밈만 `meme_overlays`로 전달한다. 밈이 없는 기존 워크플로 payload에는 이 키를 만들지 않는다.
- 최종 출력은 1080×1920 H.264/AAC MP4다. 투명 VP9 밈 합성 뒤 배경 원본 오디오와 음소거되지 않은 밈 오디오를 합친다.
- 프로젝트 편집 상태 스키마는 `meme-overlay-project.v1`이며 source snapshot과 ID/version 기반 instance snapshot만 저장한다. 캐시 절대 경로나 런타임 stream URL은 저장하지 않는다.
- 카탈로그 카드 다운로드 동시성 기본값은 3이다. 카드/오버레이 최대 크기는 각각 2 MiB/32 MiB, 다운로드 제한 시간은 60초다.
- `MEME_ASSET_CDN_HOSTS`는 기본 허용 호스트가 없는 HTTPS 전용 명시 allowlist다. 운영 배포 전에 카탈로그 CDN의 정확한 `host[:port]`를 쉼표로 구분해 설정해야 한다.
- Electron 패키지에는 밈 WebM을 포함하지 않는다. Angular renderer, Nest bundle, 기존 `clipper_video_render` Python worker만 포함하고 밈 파일은 실행 중 로컬 캐시에 준비한다.
