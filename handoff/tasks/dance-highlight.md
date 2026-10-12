# W13 — 안무 하이라이트 정확성・편집 UX 개선

최종 확인: 2026-10-02 KST. 상태: **사용자 정답 우선으로 평가 기준 전환**. MoveNet 결합 실험은 사용자 확인 후 품질 미달·미채택이다. 종전 6/18 등은 AI가 고른 일부 프레임 라벨 기준의 탐색 수치이며 사용자 기준 정확도가 아니다. 사용자가 직접 원본 전체의 구간·복수 메인·그룹/제외/보류를 입력할 노트북을 준비했다. Ultralytics YOLO는 Enterprise 계약 없이 비공개 상업 SaaS에 쓸 수 없다는 사용자 제약으로 앞으로의 제품 후보·새 실행에서 제외한다. 현재 설치본의 기본 YOLO 경로는 아직 교체되지 않았고 자동 정확도 개선도 미달성이다. 코드 미커밋.

[전체 현황](../WORKBOARD.md) · [하이라이트 전체 조사](highlight-overview.md)

## 사용자 요구

### 정확성

- [ ] 예전보다 정확도가 떨어진 것 같은 현상을 Git 변경과 동일 입력 비교로 확인한다. 현 시점에는 회귀 가설이다.
- [ ] 사용 중인 기술·모델·파이프라인을 먼저 파악한다.
- [ ] YOLO pose 기반 각 장면의 **메인 댄서 집합 선정** 정확도와 **얼굴/인물 매칭** 정확도를 분리해 개선한다. 공동 메인은 여러 명일 수 있고 불확실한 안무 장면은 보류로 남긴다.
- [ ] 개선 후보별로 테스트하고 동일 조건의 정확도·시간·자원·실패 사례를 비교한다.

### 인물이 보이는 crop

- [ ] 가로 원본 clip을 1:1 콘텐츠 영역 등 템플릿에 넣으면 양옆이 잘리고, 메인 댄서가 옆으로 이동할 때 화면 밖으로 사라진다.
- [ ] 각 장면에서 판별된 메인 댄서 위치를 따라 crop 중심을 조정하는 방법을 검토한다. tracking 누락/인물 교체·급격한 이동·템플릿 ratio·미리보기/실제 렌더 일치도 함께 검증한다.

### 사용자가 분류를 고칠 수 있는 UX

- [ ] 잘못된 인물에 속한 개별 clip들을 다른 인물로 옮긴다.
- [ ] 같은 원본 장면이 실제 공동 메인 **여러 인물 카드에 동시에** 들어갈 수 있게 하는 계약을 검토한다. 불확실한 장면은 버리지 않고 확인 필요 목록에 남긴다.
- [ ] 복수 선택을 지원할지와 드래그 앤 드롭/목적 인물 선택 등의 방식을 비교해 직관적인 흐름을 정한다.
- [ ] 수정된 결과와 원본 자동판정, 재처리/재렌더/영속저장 관계를 정한다.

### 실제 clip 생성 전 검토・편집

- [ ] 원본 영상 타임라인에서 장면의 시작/끝과 판별된 메인 댄서를 보여준다.
- [ ] 사용자가 경계를 조절하고 장면을 제외하거나 다른 인물에 재배정한 후 ffmpeg로 개별 clip을 만들 수 있는 흐름을 검토한다.
- [ ] 현재 분석/clip 생성/결과 UX와 비교해 장단점·대기시간·재편집 비용·저장 계약을 정한다. 출력 생성 지연 방식을 이미 확정된 요구로 단정하지 않는다.

## 작업 공간・시작 순서

우선 Python/Angular/Nest, 필요 시 Electron/과금 Web API. 조사·설계 단계는 로컬 상태를 읽기 전용으로 확인한다. 제품 코드 수정 대상이 사용자 선택으로 정해진 뒤 해당 저장소의 최신 origin/dev를 확인하고 새 브랜치·격리 worktree를 준비한다.

현행/변경 이력 → 기준 데이터와 정확도 지표 → 원인별 개선 → crop/재배정/타임라인 UX 설계 → 선택 범위 구현·비교 검증. 한 세션에서 모델과 UX를 무조건 모두 바꾸지 않고 검증 가능한 단계로 진행한다.

## 완료 기준

W13 전체 목표는 메인 댄서/얼굴 매칭의 개선 정도를 별도로 설명하고 clip 이동/경계 편집/템플릿 렌더 결과를 유지하는 것이다. **이번 조사·설계 세션의 완료 기준은** 근거 분류, 비교 설계·manifest, 선택할 scope를 남기는 데 한정한다. 실제 ML 평가·테스트 입력/실행 비용 범위는 사용자 지시로 구체화한다.

[기존 안무 가이드](../../features/dance-highlight/README.md) · [W12에서 확인한 참조 임베딩 연결](highlight-overview.md).

## W12 조사에서 확인한 현행과 후속 경계

[종합 인계 §3–4·6–7](../../features/highlights/records/2026/09/29-pipeline-design-handoff.md) · [파일·함수·SHA 상세](../../features/highlights/records/2026/09/29-dance-code-history.md) · [새 안무 세션 프롬프트](../prompts/2026-09-29-highlight-sessions.md).

- 현행 face는 InsightFace가 아니라 YuNet 2023mar/SFace 2021dec. Python fe223e3(7/1, metabuzz-jinahan)의 backend·표본·매핑 교체와 86fc71a(8/13, 곽민준)의 단일 reference 과잉배정 방지, 49e7827(9/18)의 montage 제거를 구분한다.
- MainSelector 중앙/면적/정적 관절 거리와 skip4·IoU/TTL의 main 선정, face 검출/cluster/reference identity를 별도 평가한다. 얼굴 평균을 만들지 못한 main 구간은 생성 전 drop되므로 unknown 카드만으로 탈락 recall을 설명할 수 없다.
- 단일 clip 이동/숨김/되돌리기와 인물 배정은 현재 존재한다. 복수 이동은 batch/revision·undo를 별도로 설계한다. 안무 trim은 현재 API에서 거절된다.
- source bbox/track keyframes 저장 → clip/trim/render 시간축 변환 → 같은 preview/render crop을 먼저 설계한다. 현재는 중앙 crop이며 label 이동만으로 새로운 실제 인물의 track을 확보하지 못한다.
- 원본 timeline 검토 후 export는 후보·탈락 사유·stable ID·draft/revision·큐/취소/재개·원본 보존·과금 경계를 포함해 현행/선택 재export와 비교할 제안이다.
- 입력 제안은 3개×120초 이하, export 없는 평가 adapter 준비 후 현행3pass+대조 하나3pass. crop 제안은 4개×10초×2ratio×2방식=16출력. 실제 입력·모델·device·시간/자원 상한은 미확정이며 이번 ML 평가 0회다.

공통 얼굴 모듈은 향후 다른 플러그인도 쓰는 공개 API/독립 모듈을 목표로 한다. W14는 초기 작업 소유 제안, W13·인물은 초기 소비자이며 이용 대상을 두 플러그인으로 제한하지 않는다. 계약·경로·병합 순서를 먼저 합의하고 공유 파일을 동시에 수정하지 않는다.

## 9/29 얼굴 변경·좌표/crop 후속 근거

[7/1 작성자·설계·변경 전후 상세](../../features/highlights/records/2026/09/29-face-change-detail.md) · [픽셀 좌표와 clip 재배정/crop의 차이](../../features/highlights/records/2026/09/29-user-feedback-clarifications.md). 앞선 설명의 ‘화면이 따라간다’는 미래 추적 crop의 잘라낼 창 이동이며 현행 기능 설명이 아니다.

## 9/30 W13 조사·선택 대기

[코드·이력·UX·crop·timeline 평가 설계](../../features/highlights/records/2026/09/30-w13-investigation-evaluation-design.md)와 [실행 전 manifest 초안](../../features/highlights/records/2026/09/30-w13-experiment-manifest.yaml)을 작성했다. Python HEAD는 9/29 기준과 같고 Nest/Angular는 이후 커밋이다. fetch는 하지 않았다. `pose_energy`는 동작량이 아닌 관절 거리 합이며 skip4와 원본 FPS 기준 streak 시간의 차이를 재확인했다. 얼굴 유효 표본이 2개 미만인 main segment는 unknown 카드로 남기 전 drop된다. 이 규칙은 7/1 이전에도 있었으므로 새 회귀 원인으로 단정하지 않는다.

레거시 `dance_meta_v1` JSON 49개를 읽기 전용으로 집계했다. `dropped_main_no_face` 합계는 25이나 같은 저장 input 경로 문자열을 가진 비교 쌍은 없고 실제 원본 hash·GT·실행 SHA도 미확정이다. 따라서 정확도 수치/회귀를 주장하지 않는다. 현행 `JsonProjectRepository`는 CAS/atomic rename이 없어 복수 재배정의 revision·원자 저장을 별도 설계해야 한다. 현재 preview는 `object-fit`, 렌더 기본 cover는 중앙 crop이며 다른 인물로 clip을 옮겨도 그 인물 위치 track은 생기지 않는다.

다음은 사용자가 우선할 개선 scope와 정확한 입력·참조·라벨·모델/장치·상한·출력 위치를 선택하는 단계다. metadata 전용 adapter 준비 전에는 새 ML 평가를 수행하지 않는다. 제품 수정 시 대상 저장소만 최신 origin/dev 확인 후 새 브랜치·격리 worktree를 준비하고 W14 공통 Python 계약·파일 소유를 먼저 합의한다.

## W14 → W13 공통 얼굴 계약 검토 요청 (9/30)

[W14 공개 API·파일 소유·병합 순서·compatibility gate 제안](../../features/highlights/records/2026/09/30-w14-to-w13-face-contract-handoff.md). `clipper_face_core` 독립 Python package와 versioned 관측 계약을 W14가 초기 작업 소유하고 W13은 기존 Dance adapter·main/reference mapping/crop을 소유하는 **제안**이다. W13 상호 확인 전에는 파일 소유권·API 승인으로 기록하지 않는다. 기존 Dance single-ROI 동작과 Windows 한글 모델 경로, plugin venv fingerprint를 회귀 항목으로 둔다.

## 10/1 선택한 metadata 평가 경로 준비

사용자가 **평가 도구 준비까지만** 선택하고 제시한 설계를 승인했다. [구현 범위·worktree·검증·남은 결정](../../features/highlights/records/2026/10/01-w13-evaluation-adapter.md)에 상세 기록했다. Python만 `git fetch origin dev`로 확인했으며 HEAD는 조사 기준 `4778295`와 동일했다. `feature/w13-dance-metadata-eval-20261001` 격리 worktree에서 `analyze_for_evaluation()`을 추가하고 제품 `run()`과 분석 판단을 공유했다. 평가 출력은 clip·썸네일·제품 meta를 생성하지 않으며 URL 참조 다운로드도 사용하지 않는다. 얼굴 표본/탈락 사유, 원본·smoothed·group 제외 구간, main bbox/track과 cluster mapping 후보 거리를 남긴다. 실제 얼굴 검출 개수·미검출/정렬 실패 세부 구분 및 source PTS는 아직 없다.

가짜 입력의 안무 테스트 34개 통과. 비 e2e 전체 suite는 487 passed/1 skipped/5 setup errors이며 5개는 sandbox의 로컬 HTTP 포트 bind 거부다. 실제 영상·모델·다운로드·과금·Build5는 0회, commit/push/merge/deploy 없음. [manifest](../../features/highlights/records/2026/09/30-w13-experiment-manifest.yaml)는 `adapter` 선택과 미확정 실험 입력을 기록한다. W14 공통 얼굴 계약 상호 확인은 별개로 남고 공통 파일 수정은 없다.

## 10/1 첫 영상 후보 지정

사용자가 [YouTube 영상 `yFTAYXDTjqI`](https://youtu.be/yFTAYXDTjqI)를 첫 평가 입력 후보로 지정했다. 처음에는 프로젝트 트리만 검색해 로컬 파일이 없다고 잘못 판단했고 YouTube 페이지/`yt-dlp` metadata 조회도 실패했다. 아래 기존 앱 데이터 조사가 이 상태를 정정한다.

## 10/1 기존 앱 원본 확인·전체 영상 선택

사용자는 이미 앱에서 안무 작업을 마친 이 영상의 **다운로드된 원본**을 쓰고, 시작부터 끝까지 평가하라고 지정했다. [읽기 쉬운 조사 결과](../../features/highlights/records/2026/10/01-w13-first-video-static-review.md)와 [파일별 경로·SHA-256 목록](../../features/highlights/records/2026/10/01-w13-existing-app-input-inventory.json)을 작성하고 [manifest](../../features/highlights/records/2026/09/30-w13-experiment-manifest.yaml)에 반영했다. `Clipper Studio Dev`의 원본은 133.654059초·79,098,114 bytes·1920×1012·SHA-256 `7f23b9ad…88d4`; 일반 `Clipper Studio` 사본도 같은 hash다. 새 다운로드는 하지 않았다.

9/29 Dev 완료 결과와 9/10 일반 앱 완료 결과는 `config/stats/lists/persons`가 같고 최신 결과는 메인 clip 19개·그룹 1개·main 1개 얼굴 표본 단계 탈락이다. 이것은 정적 artifact 일치일 뿐 정확도 평가는 아니다. 기존 로그에는 그룹 중첩으로 메인 후보 `20.487~30.030`초·`30.030~34.835`초를 제외한 기록이 있고, 실제 그룹 clip `23.357~33.433`초 양옆에 2.870초·1.402초 공백이 남는다. 얼굴 표본 탈락 1건의 시점은 미확인이다. 최신 프로젝트는 참조 URL 24개를 골랐고 23개 로컬 파일이 남아 있다. YOLO pose·YuNet·SFace 파일의 SHA도 확보했다. 기존 3개×120초 제안은 이 입력에 대해서는 전체 133.654초 선택으로 대체됐다. 초당 1프레임 임시 contact sheet로 출연 전/안무/종료 화면을 예비 확인했으나 메인·멤버 정답표와 정확도 수치는 만들지 않았다. **새 모델 추론 0회**이며 정답 라벨·23개 참조 재사용 범위/권한·비교 변수 하나·실행 SHA/device/횟수/시간·자원 상한/출력 위치를 고정한 뒤 새 평가를 시작한다.

## 10/1 사용자 정정 — 다중 메인과 보류 보존

[한 장짜리 설계 정정](../../features/highlights/records/2026/10/01-w13-multi-main-retention-design.md)을 기록했다. 사용자는 분명한 단독 메인은 한 명으로 보되 공동 메인은 여러 명으로 두고, 같은 장면을 여러 인물에게 넣을 수 있으며, 불확실한 안무 장면은 보류로 남겨 버려지는 것을 줄이길 원한다. **의상 색↔멤버 이름 대응을 사용자에게 요구하지 않는다.** 기존 Python은 프레임당 메인 bbox/track 하나, Nest clip 이동은 목적 인물 하나라는 사실을 확인했다. 따라서 이 방향은 평가 라벨만 바꾸는 문제가 아니며 제품의 분석/배정 계약 변경이 필요하다. 이번에는 정답 schema와 비교 지표·설계안만 정정하고 제품 코드/기존 앱 파일·새 ML은 변경/실행하지 않았다.

## 10/1 전체 원본 독립 육안 검토 초안

사용자의 `진행해`에 따라 이미 저장된 동일 MP4 전체를 **초당 2장, 실제 267장**, 교체 후보 15~38.75초·50~65.75초를 **초당 4장**으로 읽어 [장면 모음과 쉬운 검토표](../../features/highlights/records/2026/10/01-w13-full-source-review-guide.md), [전체 구간 JSON 초안](../../features/highlights/records/2026/10/01-w13-full-source-label-draft.json)을 만들었다. 0~133.654초를 19개 연속 임시 구간으로 덮고 입장/단독 리드 후보/교체/그룹·공동 메인 검토/종료 화면을 분리했다. 익명 `V1`~`V5`는 대표 프레임의 사람 표식일 뿐 실제 멤버나 확정 track이 아니다. 정답 라벨 `main_track_ids`와 신원은 아직 비워 두었다.

정적 대조에서 기존 앱의 인물별 main clip이 **20.487~34.835초**에 없고, 그룹 clip은 23.357~33.433초만 있으므로 양끝에 2.870초·1.401초 결과 공백이 있다. 해당 원본 장면은 출연자가 보이고 앞사람이 바뀌는 순서로 보여 우선 검토 대상이다. 정확한 단독/공동 메인과 안무 경계, 이름 판정은 연속 재생·사람별 box/track·독립 확인 전에는 확정하지 않는다. 현재 표는 accuracy 점수 입력이 아니다. manifest에 초안 경로/hash를 기록했지만 실행용 frozen label 경로는 비워 두었다. 제품 코드·기존 앱 산출물 변경, 새 ML/다운로드/유료 호출, commit/push/merge/deploy 없음.

[첫 비교 범위](../../features/highlights/records/2026/10/01-w13-first-comparison-scope.md)는 **탈락 장면을 확인 필요로 보존**하는 정책 하나로 제안했다. 기존 `group_overlap` main 후보 2개가 덮는 14.348초 중 10.077초는 기존 그룹 clip과 겹치고 4.271초는 결과 clip 자체가 없다. 검토 목록 보존은 새 clip 생성이나 정확도 상승을 뜻하지 않는다. 같은 추론 metadata에서 현행 drop과 보존 정책을 오프라인 비교하면 별도 대조 모델 pass 없이 첫 조건을 측정할 수 있다. 실행용 정확한 라벨·weight 사용권·반복/자원 상한/출력 위치는 여전히 미확정이다.

## 10/1 첫 보존 지표 고정과 실행안 제시

사용자의 후속 진행 지시에 따라 기존 원본을 QuickTime에서 열어 시점을 대조하고, 전체 2fps·집중 4fps 장면 모음과 기존 결과를 다시 확인했다. **6.0~112.5초의 출연자가 보이는 공연 장면**만 [보수적 보존 지표용 라벨](../../features/highlights/records/2026/10/01-w13-retention-visibility-label-v1.json)로 고정했다. 입장/종료 경계의 각 1초는 점수에서 제외한다. 기존 clip 합집합은 이 106.5초 중 102.229초를 덮고, 20.487~23.357초와 33.433~34.835초의 **4.271초가 미출력**이다. 이는 공연 장면 가시성에 대한 정적 계산이다. 춤 동작 기준, 사람별 메인·공동 메인, 멤버 신원 정답은 여전히 고정하지 않았고 연속 프레임/track 검토가 필요하다.

[한 장 실행안](../../features/highlights/records/2026/10/01-w13-first-evaluation-one-page.md)에 원본·hash·전체 구간, 참조 없음, 현행 weight, CPU/최대 3회/시간·RSS·출력 제안을 모았다. 새 추론은 **미승인**이다. 이전 Ultralytics 이용 조건 검토 근거가 현재 자료에서 확인되지 않아 적용 범위를 대조해야 하며, 부적합으로 확인되면 기존 artifact·로그 비교만 유지한다. 코드 fingerprint·상한 강제 runner·환경/설정 고정도 남았다. 제품 코드·기존 clip·W14 공통 Python 파일은 바꾸지 않았고 새 ML/다운로드/과금/Build5·commit/push/merge/deploy는 하지 않았다.

사용자 지적 후 [YOLO 도입·이용 조건 기록](../../features/highlights/records/2026/10/01-w13-yolo-license-provenance.md)을 추가했다. 2/26 레거시 Python 커밋 `69e3d84`에서 동일 hash의 YOLOv8s Pose weight와 `ultralytics`를 처음 넣었고, 4/17 `61c1b1c`가 현행 플러그인으로 이식했다. 도입 커밋/문서에는 당시 이용 조건 검토 결과가 없지만, 사용자는 그때 사용 가능 여부를 확인한 것으로 기억한다. 저장소에 근거가 없다는 사실을 사용권 부재로 해석하지 않는다. AGPL 영리 사용 자체는 가능하며 현재 공식 조건은 공개 의무와 비공개 SaaS 상업 이용권을 구분한다. 이전 검토/계약과 현 제품 범위를 대조한 뒤 결론을 낸다. 새 ML 미실행은 사용자 지정 범위·manifest 미확정 조건도 별도로 따른다.

## 10/1 비공개 제품용 포즈 교체 후보 선택

사용자는 제품 소스 공개가 불가능하다고 밝히고 [Google MoveNet MultiPose Lightning을 1차 비교 후보](../../features/highlights/records/2026/10/01-w13-movenet-pose-replacement-review.md)로 두는 데 동의했다. Google 배포 TF2 v1 모델에 Apache 2.0이 명시되어 있다. 최대 6명·17개 관절·bbox를 출력하나 이 공연 영상에서 현행 YOLO보다 정확한지는 미검증이다. Python 3.11용 Mac arm64/Windows x64 TensorFlow CPU wheel은 공식 제공되지만 앱 배포 통합은 미검증이다. 기존 YOLO 결과는 프레임별 pose 출력이 없어 새 MoveNet과 통제된 A/B 기준선이 아니다. [별도 MoveNet manifest 초안](../../features/highlights/records/2026/10/01-w13-movenet-comparison-manifest.yaml)은 기존 전체 원본/hash, 참조 이미지 없음, CPU·최대 3회·상한·출력 제안을 기록하고 모델 파일/hash·사람별 정답·adapter·실행 fingerprint는 미확정으로 둔다. 신규 YOLO 추론은 이전 권리 범위 확인 전 진행하지 않는다. 이 선택만으로 모델 다운로드·제품 코드 수정·새 ML 실행을 승인한 것으로 기록하지 않는다.

## 10/1 MoveNet 평가 도구와 익명 메인 검토표 준비

후속 `진행해`에 따라 기존 W13 Python 격리 worktree에 [MoveNet 출력 변환·포즈 전용 평가 경로](../../features/highlights/records/2026/10/01-w13-movenet-adapter-and-label-prep.md)를 추가했다. 로컬 SavedModel만 여는 로더, RGB/패딩/원본 좌표 역변환, 각 분석 프레임의 모든 사람·단일 main·group 관측이 가짜 출력·가짜 프레임 테스트 12개를 통과했다. 비 e2e suite는 494 passed/1 skipped/5 socket 테스트 제외이고 전체 실행의 추가 20건은 이 sandbox의 localhost bind 거부로 실패/오류였다. 제품 기본 모델/실제 `run()`은 바꾸지 않았다. [익명 메인 검토표](../../features/highlights/records/2026/10/01-w13-anonymous-main-review.json)는 전체 19구간에 5명 솔로 후보를 `P1`~`P5`로 연결하지만 멤버 신원·공동 메인·사람별 bbox·정확 경계가 미확정이어서 scoring 정답이 아니다. 실모델 파일·hash·런타임·상한 강제 runner·실제 실행 fingerprint는 남았다. 모델 다운로드·실제 영상 ML·제품 전환은 0회다.

## 10/1 MoveNet 평가 실행기 후속

[상한 강제 runner](../../features/highlights/records/2026/10/01-w13-movenet-runner-readiness.md)를 같은 W13 격리 worktree에 만들고 합성 테스트 **19 passed** 및 현 draft manifest CLI 거절을 확인했다. 원본·모델·정답·코드/runtime hash와 정답의 원본 일치/전체 구간, CPU·분석 간격·점수 기준·반복/시간/worker RSS/출력 상한이 모두 고정돼야 실행한다. macOS sandbox가 자식 목록을 막아 RSS는 직접 worker PID로 감시하고 감시 불가·취소 시 중단한다. W13 집중 **39 passed**, 최종 변경 후 비 e2e suite **509 passed/1 skipped/1 socket fixture 제외**. 위 단락의 “runner가 남았다”는 작성 당시 상태다. [갱신된 manifest](../../features/highlights/records/2026/10/01-w13-movenet-comparison-manifest.yaml)는 계속 **미승인 초안**이다. 실제 모델 weight와 런타임, 독립 사람별 정답, 실 SavedModel signature 검증, 최종 실행 조건은 남았다. 이번에도 모델 다운로드·실영상 ML·제품 전환·commit/push/merge/deploy는 하지 않았다.

## 10/1 모델 파일 확보와 원본 프레임 검토 후속

[모델 파일·원본 라벨 진행 기록](../../features/highlights/records/2026/10/01-w13-model-file-and-source-label-progress.md)에 Google 공식 TF2 v1 archive 18,612,451 bytes와 archive/추출 디렉터리 SHA-256을 기록하고, 격리 worktree `output/model-assets/`에만 보관했다. 이는 위 “모델 다운로드 0회” 기록 **이후**의 후속 단계다. TensorFlow 설치·모델 로드·signature 확인·실영상 ML은 0회이고 제품 기본 YOLO는 그대로다. 공식 카드상 weight Apache-2.0, 제품 포함 시 라이선스/고지 확인이 별도로 필요하다.

[15개 시점의 원본 관찰·3프레임×5명 대략 위치 초안](../../features/highlights/records/2026/10/01-w13-source-frame-observations.json)을 만들었다. 29~32초 `P3` 리드 후보는 추가 프레임에서 뒷받침됐지만, 100~112초는 앞선 19구간의 넓은 `group_review` 분류를 재검토해야 한다. 기존 앱 결과가 검토자에게 이미 보였고 연속 영상/사람별 위치 독립 감사도 끝나지 않아 **채점용 정답은 아직 아니다**. [MoveNet manifest](../../features/highlights/records/2026/10/01-w13-movenet-comparison-manifest.yaml)에 정확한 weight 경로/hash와 초안 hash를 채웠으나 실행 상태는 닫혀 있다. 사용자가 할 일은 현재 없으며, 실제 추론 전에는 고정된 라벨·런타임·실행 상한/출력 위치를 한 장의 실행 범위로 제시해 확정받는다. commit/push/merge/deploy 없음.

## 10/1 원본만 본 2차 검토와 runner 잠금 보강

[기존 앱 판정·W13 앞선 초안을 보지 않은 2차 검토](../../features/highlights/records/2026/10/01-w13-source-only-second-review.md)는 앞선 솔로 후보 5구간에 대체로 동의했다. 42~48초 `P5` 주목 장면은 단독인지 공동인지, 99~105초 빠른 앞사람 교체는 구간별 메인 집합을 어떻게 둘지 의견이 갈려 보류한다. 두 검토 모두 정지 화면 중심이라 연속 영상/전신 위치의 채점 정답은 아니다. 이름·참조 사진 확인을 사용자에게 요청할 단계도 아니다.

runner의 코드 fingerprint에 직접 import하는 `protocols.py`·`dance_meta.py`를 포함하고, 실행 manifest에는 TensorFlow 외 NumPy·OpenCV·psutil·PyYAML·requests의 버전도 필수로 묶었다. 회귀 테스트 **22 passed**, 비 e2e 전체 재실행은 **571 passed/1 skipped/5 localhost bind errors**였다. 같은 5개만 제외하면 **571 passed/1 skipped/5 deselected**다. 실제 모델 로드·signature 확인·영상 추론은 계속 0회다. 다음에는 애매한 장면을 연속 검토하고 익명 인물 위치·공동 메인 라벨을 채점 가능하게 고정한 뒤, 런타임/시간·메모리·출력 상한을 확정한 실행 범위를 사용자에게 제시한다.

## 10/1 10fps 원본 추가 확인과 정답 후보 축소

[42~50초·98~113초의 원본 추가 확인](../../features/highlights/records/2026/10/01-w13-dense-source-review.md)으로 42~48.5초는 `P5`가 가운데에 있어도 다섯 명이 함께 춤추는 그룹 장면으로, 98.5~104.3초는 `P2→P3→P4`가 짧게 앞에 나오는 **후보**로 세분화했다. [임시 메인 표](../../features/highlights/records/2026/10/01-w13-anonymous-main-review.json)는 전체 26개 연속 구간, [위치 초안](../../features/highlights/records/2026/10/01-w13-source-frame-observations.json)은 19시점 관찰·9프레임×5명 총45개 육안 상자다. 상자는 원본 위에 겹쳐 자체 점검했으나 이번 촘촘한 판정/좌표에 대한 별도 감사와 연속 영상 검토는 끝나지 않았다. 첫 단독 메인 점수의 보수적 분모로 5구간 합계 18초를 **제안**했으며 그룹·전환·보류는 버리지 않고 coverage로 기록한다. 정답/실행 manifest는 여전히 미승인이고 실제 추론은 0회다. 다음은 독립 라벨 감사와 점수 규칙 고정 후 **구체적인 한 장 실행 범위를 사용자에게 제시**하는 것이다.

## 10/1 제한된 채점 라벨·실행 범위 준비

위 단락 이후 [10fps 장면·45개 상자 독립 표본 감사](../../features/highlights/records/2026/10/01-w13-independent-label-audit.md)를 마쳤다. 22.02초 `P3`를 부분 가림으로 수정했다. [제한된 채점 라벨](../../features/highlights/records/2026/10/01-w13-pose-scoring-labels-v1.json)은 원본 전체 36개 연속 구간에서 명확한 솔로 기준 창 5개·18초와 그룹/전환/보류를 나누고, 공연 9프레임의 45명 위치와 공연 밖 빈 화면 2프레임을 고정한다. **메인 신원 채점은 기준 창에 들어오면서 사람 위치도 독립 확인된 4프레임(P1~P4)에만 가능하다.** P5 기준 창의 위치 상자는 없으며 18초 매 프레임·영상 전체 메인 정확도, 전환 지연, 공동 메인 점수는 아직 낼 수 없다. [채점 규칙](../../features/highlights/records/2026/10/01-w13-pose-scoring-policy-v1.md)에서 그 분모와 미채점·가림 처리를 정의했다.

[MoveNet manifest](../../features/highlights/records/2026/10/01-w13-movenet-comparison-manifest.yaml)에 고정 라벨 경로/hash와 실제 채점 범위를 적고 [한 장 실행 범위](../../features/highlights/records/2026/10/01-w13-movenet-execution-scope-one-page.md)로 풀어 썼다. manifest는 계속 **실행 미승인**이다. TensorFlow 설치·실 SavedModel signature 검증·원본 실영상 추론은 0회이고, 제품 모델 변경/앱 통합·commit/push/merge/deploy도 없다. 다음은 런타임/실 signature·코드 fingerprint·CPU/최대3회·시간/RSS/출력 위치를 잠근 실행 범위를 사용자에게 제시하는 일이다. 더 넓은 정확도 비교를 원한다면 연속 프레임 라벨링을 별도 범위로 정해야 한다.

## 10/1 MoveNet 런타임·입출력 형식 잠금

위 단락 이후 사용자의 `진행해`에 따라 W13 worktree **격리 `.venv`**에 TensorFlow 2.21.0과 평가 의존성을 설치하고, 공식 PyPI wheel SHA-256 `51f46f4806139d01fc7920cc72a4c75876f80649bf40ff083ab6212ceb43ca88`를 검증했다. [런타임·signature 기록](../../features/highlights/records/2026/10/01-w13-movenet-runtime-signature-lock.md)에 실제 `tf.saved_model.load()`와 안무 평가 adapter 로더가 모델을 연 결과, `input: int32 [1,None,None,3]` → `output_0: float32 [1,6,56]`, 설치 36개 패키지 버전과 `pip check` 통과를 적었다. **추론 함수 호출·실영상 분석은 0회**다.

[manifest](../../features/highlights/records/2026/10/01-w13-movenet-comparison-manifest.yaml)의 정확한 코드 지문 `333b11306a8edea2a0339d91b26da2e0ef1b6f76d6be49ed8582a255ae7df2b1`, Python 3.11.12/macOS 지문, CPU·3회·회당 600초/총 1800초·RSS 12,288MiB·metadata 250MiB·격리 출력 위치를 채웠다. 승인 플래그를 **파일이 아닌 메모리 복사본에서만** 열어 `check_execution_manifest()`의 읽기 전용 사전 검사 통과를 확인했다. 저장된 manifest는 `ready_for_user_scope_review_no_inference`, 실행 승인값은 `false`이고 실제 CLI는 exit 2로 거절했다. 이제 [한 장 실행 범위](../../features/highlights/records/2026/10/01-w13-movenet-execution-scope-one-page.md)를 사용자에게 제시해 실제 **새 MoveNet 추론 시작 여부**를 선택받는다. 제품 코드 변경·W14 공통 얼굴 파일 변경·commit/push/merge/deploy는 없다.

## 10/1 사용자 승인 MoveNet metadata 평가 3회 결과

사용자가 [고정 실행 범위](../../features/highlights/records/2026/10/01-w13-movenet-execution-scope-one-page.md)를 본 뒤 `해`라고 승인했다. [실제 실행·표본 해석 기록](../../features/highlights/records/2026/10/01-w13-movenet-first-real-metadata-evaluation.md)에 원본 전체 `skip4` CPU MoveNet 3회, 해시/시간/RSS/출력, 첫 결과를 기록했다. 세 worker exit 0, pose JSON 해시 동일, 회당 56.75~60.90초, 최대 RSS 937.42MiB, 전체 출력 20.62MiB였다. 9개 원본 프레임의 45명 중 33명을 IoU≥0.30/0.50에서 짝지었고, 일부 가림은 3/9명이다. 명확한 메인 위치 표본 4프레임 중 1개만 맞았으며 **틀린 세 프레임 모두 정답 인물은 검출돼** 검출과 이후 메인 선택 실패를 분리했다. 사용자 요청대로 그룹·보류 장면은 오답 분모에 넣지 않았다. 6.0~112.5초의 공연 창에서 분석 프레임 기준 후보 없는 시간은 0.267초다. 기존 앱 최종 clip 공백 4.271초와 단계가 달라 개선량으로 비교하지 않는다.

실행 후 raw segment 끝이 마지막 관측 시각 **포함**이라는 것을 확인해, 보존 시간은 `skip4` 프레임 셀 합집합으로 보정했다. [표본 채점기](../../features/highlights/records/2026/10/01-w13-movenet-first-real-metadata-evaluation.md)는 7개 테스트를 실패→통과로 확인하고 모델 재실행 없이 JSON만 후처리했다. [manifest](../../features/highlights/records/2026/10/01-w13-movenet-comparison-manifest.yaml)는 `completed_scoped_metadata_run`으로 닫아 같은 범위의 추가 추론을 막았다. **현행 YOLO 대비 회귀/개선은 여전히 미검증**이다. 기존 YOLO의 같은 프레임 모든 pose 기록이 없고 신규 YOLO pass는 0회다. 얼굴 identity·멤버 mapping·crop·최종 clip 품질도 이번 실행 범위 밖이다. 제품 모델 변경·W14 공통 얼굴 코드 변경·commit/push/merge/deploy 없음.

## 10/1 저장 pose로 메인 선택 규칙 분해 비교

사용자의 후속 `진행해`에 따라 [오프라인 비교 기록](../../features/highlights/records/2026/10/01-w13-main-selector-offline-rule-comparison.md)을 작성했다. 저장된 2,002프레임을 현행 선택기에 재생해 main/group 불일치 **0건**을 먼저 확인했다. 메인 오선택 3장 중 22.022초와 55.989초는 정답이 순간 점수 3위·4위였고, 29.029초는 정답이 1위이나 현재 점수 문턱·전환 유지가 이전 인물을 남겼다. 즉시 최고 점수 선택은 솔로 표본 **1/4→2/4**지만 공연 창의 연속 bbox 불연속 대리 지표가 **230→380**으로 늘었다. 후보 점수 여유만 0으로 하거나 `skip4`에 맞춰 전환 연속 횟수만 줄인 단일 변수 재생은 각각 **1/4**였다. group 플래그는 명확한 솔로 창 269프레임 중 222프레임에서도 참이라 공동 메인 정답으로 볼 수 없다. `top-k` 자동 배정은 솔로 표본의 오배정을 늘린다. 다음에는 독립적인 연속 원본 라벨을 늘려 점수/전환/공동 메인을 분리 평가하고, 불확실한 후보를 검토 목록에 보존하는 계약을 정한다. 새 ML·clip/얼굴 평가·제품 코드 변경·commit/push/merge/deploy 없음.

## 10/1 세 오선택 전후 원본 전환 검토

[원본 장면 검토](../../features/highlights/records/2026/10/01-w13-transition-source-review.md)에서 22.022·29.029·55.989초 앞뒤를 원본 6프레임 간격(약 0.1001초) 장면 모음과 정확한 앵커 원본 프레임으로 확인했다. 기존 독립 라벨의 P2·P3·P4 단독 창에 반하는 모습은 없었다. [잠정 구간표](../../features/highlights/records/2026/10/01-w13-transition-source-review-v2.json)에 20.5~22.0초 P1→P2, 27.0~29.0초 P2→P3, 52.8~54.0초 그룹→P4, 57.0~59.0초 P4→P5를 **교체 검토 시간대**로 기록했다. 작성자가 모델 결과를 이미 보았으므로 새 독립 정답이나 정확도 분모로 사용하지 않는다. 이 구간에서 확정된 공동 메인도 없고 전환 지연 수치도 산출하지 않는다. 기존 동결 라벨·manifest·3회 실행 결과는 그대로다. 다음은 모델 판정을 보지 않은 검토로 교체 시간대의 단독/공동/보류와 채점 프레임의 사람별 위치를 고정한 뒤 저장 pose를 재채점하는 것이다. 이번 후속은 원본 읽기·장면 이미지 추출·문서 갱신만 했고 새 ML·제품 코드 변경·commit/push/merge/deploy는 없다.

## 10/1 독립 전환 라벨 6프레임 재채점

앞선 독립 감사자가 모델·앱 출력을 보지 않은 상태에서 네 교체 시간대의 원본을 약 10fps로 다시 보고, [전환 라벨 v2](../../features/highlights/records/2026/10/01-w13-blind-transition-labels-v2.json)의 단독 메인 6프레임과 경계/약한 2프레임을 **예측 확인 전에 고정**했다. [원본·저장 pose 대조 기록](../../features/highlights/records/2026/10/01-w13-blind-transition-audit-and-rescore.md)에서 엄격 표본은 **2/6 일치, 4/6 오선택**이었다. 틀린 네 프레임 모두 정답 인물 검출 IoU≥0.30이며, 셋은 순간 점수 4·2·2위, 하나는 1위인데 현행 선택은 다른 인물이다. `is_group`은 단독 정답 6장 모두에서 참이었다. 28.2~28.6초 겹침은 공동 메인 후보로 남기되 확정 채점하지 않았고, 52.8~53.4초·57.3~57.6초 등 인계도 보류했다. 기존 네 앵커 1/4와 새 여섯 장 2/6은 모두 의도적으로 고른 작은 표본이며 전 영상 정확도나 YOLO 대비 우위가 아니다. 독립 검토는 전체 연속 프레임 감사가 아니어서 전환 지연·공동 메인 점수도 미산출이다. 저장 pose JSON만 후처리했고 새 ML·제품 코드·공통 얼굴 파일 변경·commit/push/merge/deploy는 없다.

## 10/1 새 고정 표본과 탈락 후보 보존 범위

[사전 고정 표본 계획](../../features/highlights/records/2026/10/01-w13-holdout-source-sample-plan.json)에서 원본 프레임 27개(명확한 단독 18, 그룹 4, 빠른 인계 5)를 예측 확인 전에 정하고, 별도 원본 검토자가 [라벨](../../features/highlights/records/2026/10/01-w13-holdout-source-labels-v1.json)을 고정했다. 18개 단독 표본의 [저장 pose 재생 결과](../../features/highlights/records/2026/10/01-w13-selector-holdout-evaluation.md)는 현행 메인 **6/18 일치**, 정답 인물은 검출됐지만 다른 사람 선택 9, IoU≥0.30 정답 대응 실패 3이다. 전환 streak만 실제 `skip4` 간격으로 보정하거나 정적 관절 거리 항만 제거하면 각각 **4/18**로 낮아졌다. 세 조건 모두 앞선 개발용 10개 앵커는 3/10이다. 저장 결과와 현행 선택기 2,002프레임 재생의 main bbox/group 불일치는 0건이다. 그룹 4장은 단독 메인 정답 분모에서 제외했고, 빠른 인계 5장은 초점 후보만 기록해 전환 지연·공동 메인 점수로 사용하지 않았다. 한 영상의 선택된 프레임 결과이며 전체 정확도·기존 YOLO 대비 개선/회귀가 아니다.

[탈락 장면 보존 첫 제품 계약](../../features/highlights/records/2026/10/01-w13-review-candidate-preservation-contract.md)은 Python 분석의 `group_overlap`/얼굴 표본 부족 구간을 optional sidecar에 남겨 Nest/Angular가 원본 시간·사유를 **읽기 전용 검토**로 보여주는 안이다. 완료된 앱 artifact의 공연 창 106.5초에서 기존 MP4는 102.229초를 덮고, 그룹 중첩 탈락 후보 2개를 검토 목록에만 추가하면 clip이 전혀 없던 **4.271초가 보이게 된다**는 정적 계산이다. MP4를 만들거나 정확도를 올린 결과가 아니다. 현행 segment 끝은 다음 관측/마지막 관측의 의미가 섞여 있어 원본 PTS나 정확한 ffmpeg 경계를 보장하지 않는다. 제품 적용은 사용자 화면/저장 범위 선택 뒤 해당 저장소 최신 `origin/dev` 격리 worktree에서 한다.

[W14 공통 얼굴 API의 W13 소비자 검토](../../features/highlights/records/2026/10/01-w13-face-core-consumer-contract-review.md)는 W14가 공통 파일 초기 소유, W13이 main·참조 매핑·crop을 소유하는 경계를 수용한다. 현재 W14 미커밋 공개 API에는 인계안의 `FrameRef`/PTS·구조화 실패 이벤트·완전한 embedding 공간 지문 등 차이가 있어 Dance adapter 이식 계약은 아직 고정되지 않았다. W13은 공통 Python 파일을 수정하지 않았다. 다음 결정은 **탈락 후보 읽기 전용 검토 범위를 제품에 먼저 적용할지**이며, 모델/얼굴 재평가는 별도 입력·지표·실행 상한 결정이 필요하다. 새 ML·clip export·제품 코드·commit/push/merge/deploy 없음.

## 10/1 사용자 선택 — 탈락 장면 읽기 전용 구현

사용자가 추천 순서의 첫 단계인 **빠진 장면 검토 표시**를 선택했다. [격리 구현 기록](../../features/highlights/records/2026/10/01-w13-review-scenes-implementation.md)대로 최신 `origin/dev`에서 Python/Nest/Angular worktree를 준비했다. Python은 group 중첩/얼굴 표본 탈락 main 구간을 원본 시간·실제 사유·SHA와 함께 원자적 sidecar에 남긴다. Nest는 optional sidecar와 원본 SHA를 확인하고 기존 clip/person과 분리하며, Angular는 생성된 clip/확인 필요 두 줄 타임라인과 원본 seek·누락 안내를 표시한다. 기존 네 열 결과·clip export·숏폼·W14 공통 얼굴 경로는 유지한다.

합성 Python→Nest 계약 확인, Python 비 e2e **493 passed**, Nest 안무/프로젝트 **183 passed**, Angular 집중 Chrome **72 passed**와 빌드·스타일 확인을 마쳤다. 기존 `yFTAYXDTjqI` 완료 카드에는 sidecar가 없으므로 새 후보가 실제 표시된 결과는 **아직 없다**. 실제 영상 재분석·모델 추론·신규 clip 생성·커밋/푸시/병합/배포는 하지 않았다. 캐시 밖 로컬 원본의 앱 재시작 후 재생 경로와 큰 원본의 상세 SHA 계산 지연은 남은 제품 위험이다. 다음은 이 첫 화면의 실제 원본 확인과 영속 source streaming 결정을 거친 뒤, 별도 입력·라벨·상업 이용 조건·실행 상한으로 **메인 판정 정확도** 단계에 들어가는 것이다. crop과 복수 배정은 그 뒤 순서다.

## 10/1 같은 영상에서 사용자 확인용 전후 비교

[쉬운 비교 결과와 원본 증거 영상](../../features/highlights/records/2026/10/01-w13-same-video-before-after-check.md)을 추가했다. 9/29 완료 프로젝트의 공연 창 106.5초에서 기존 완성 MP4는 **102.229초**를 덮고, **4.271초는 어떤 클립에도 없다**. 9/29 로그의 그룹 중첩 탈락 후보 두 건을 새 `확인 필요` 목록으로 표시한다는 **정적 가정**에서는 그 4.271초를 원본에서 찾을 수 있지만, 완성 MP4 길이·메인 정확도가 개선된 결과는 아니다. 독립 원본 라벨의 단독 메인 18프레임 중 기존 결과의 인물별 메인 클립이 없는 9프레임(그룹만 8, 클립 없음 1)이 모두 두 후보에 들어간다. 기존 완료 카드에는 새 sidecar가 없고 새 앱 실행도 하지 않았다. 결과가 실제로 나아졌다고 말하려면 동일 입력의 새 완료 결과와 같은 기준의 라벨 비교가 더 필요하다.

[다음 메인 평가의 사전 진단](../../features/highlights/records/2026/10/01-w13-next-main-evaluation-gate.md)에서 저장 MoveNet 자세·기존 고정 라벨 18프레임을 재사용했다. 현행 단일 선택은 6/18, 점수 상위 2명 후보는 정답 포함 12/18이지만 후보 36개 중 24개가 그 프레임의 단독 정답 사람이 아니다. 그룹 4프레임에서도 8개 사람 후보가 생긴다. 이는 정확도 개선이 아니라 검토 부담을 동반한 후보 보존이므로 제품 자동 배정에 채택하지 않는다. 다음은 움직임 기반 단일 규칙을 새 원본 표본에 고정 평가하고 검출 실패 3건을 별도로 다루는 것이다.

[새 원본 표본의 움직임 단독 규칙 비교](../../features/highlights/records/2026/10/01-w13-motion-main-probe-result.md)를 마쳤다. 모델 출력 확인 전에 고정한 15개 단독 메인 프레임에서 저장 현행 선택 **6/15**, 움직임 단독 **5/15**였다. 정답 검출 자체가 안 된 프레임은 3장, 그룹 검토 3장에서는 두 규칙 모두 한 명을 골랐다. 움직임 단독 규칙은 미채택한다. 동일 영상·한 검토자·선택한 일부 프레임의 탐색 결과로, 이전 YOLO 앱과의 실제 품질 우위나 전체 영상 정확도를 뜻하지 않는다. 새 모델·제품 코드·완료 MP4 변경 없음. 다음은 검출 실패와 검출 후 오선택 원인 분리, 그룹 오배정 방지 설계, 이후 승인된 같은 원본 새 완료 결과의 직접 비교다.

[실제 수정 전 클립과 저장 자세 판정의 시각·시간 비교](../../features/highlights/records/2026/10/01-w13-actual-old-vs-saved-pose-comparison.md)를 만들었다. 기존 Dev 프로젝트의 19개 main/1개 group MP4 파일을 실제 확인하고, MoveNet `run-01` 저장 pose를 현재 smoothing/group 필터에 **새 모델 호출 없이** 재생했다. 사용자 지정 영상 전체 133.654초에서 기존 완성 개별 클립은 **93.16초**, 새 자세의 얼굴 전 개별 후보는 **24.62초**; 그룹은 각각 10.08초와 84.15초다. 공연 6~112.5초만 보면 개별 메인 92.15초→22.83초다. 17개 smoothed main 중 12개가 그룹 중첩으로 탈락했다. 원본 라벨의 단독 18장 중 기존 개별 clip이 있는 장면 9장, 새 얼굴 전 개별 후보 3장이다. 사용자가 직접 볼 수 있도록 실제 기존 MP4와 새 자세 상자를 같은 원본 시각에 맞춘 18초 비교 영상과 **전체 원본** 시간표 PNG를 남겼다. **제품에 MoveNet을 그대로 교체하지 않는다.** 새 완료 앱 결과, identity·crop·최종 clip 품질 우위는 여전히 미검증이며, 새 ML·얼굴 추론·export·기존 프로젝트 수정·commit/push/merge/deploy는 없다.

## 10/1 실제 로컬 앱에서 같은 영상 검토

사용자가 실제 앱에서 직접 확인할 수 있게 해 달라고 요청했다. [화면 실행·검증 기록](../../features/highlights/records/2026/10/01-w13-local-app-review-preview.md)대로 W13 Angular/Nest 작업본을 4201/9021에서 실행하고 기존 완료 프로젝트·원본을 격리 복사했다. 당시 로그의 그룹 중첩 탈락 두 구간 20.487–30.030초와 30.030–34.835초를 복사본에만 backfill했다. 화면에서 기존 19개 개별 클립·5명 인물과 `원본 장면 검토 2개`가 같이 보였고, 두 버튼을 눌러 원본 player가 각각 20.487초·30.030초로 이동하는 것을 확인했다. 사용자 링크는 `http://localhost:4201/#/projects/1790659628130`이다. Angular 패키지용 빌드도 통과했다.

이 앱은 W13 **로컬 작업본**이다. 기존 설치본이나 9/29 완료 프로젝트는 수정하지 않았다. 3001 로컬 로그인 fixture는 미리보기용이며 실제 사용자 인증/계정·결제 검증이 아니다. 새 모델/얼굴 추론/클립 export·commit/push/merge/deploy는 하지 않았다. 따라서 보여주는 것은 `기존 결과 + 탈락 후보 검토`이지 더 정확해진 새 완성 결과가 아니다. 메인·identity·crop과 새 최종 MP4의 전후 정확도 평가는 아직 남아 있다.

## 10/2 동일 영상의 실제 새 완료 결과

사용자가 검토 후보 화면보다 **새 버전이 실제 만든 클립**을 우선 요청했다. [실행·동일 입력 비교 기록](../../features/highlights/records/2026/10/02-w13-same-video-completed-variant.md)대로 이미 저장된 MoveNet 자세 2,002프레임을 재생하고, 그룹과 겹치는 메인 후보 보존/얼굴 미확인 `unknown` 보존 옵션을 켠 격리 Python 실행에서 YuNet/SFace 얼굴 분석과 19개 MP4 export를 실제 수행했다. 원본·참조 23장·모델 weight hash를 고정했고 추가 pose 추론/다운로드/과금은 없었다. 기존 완료 프로젝트의 메타 hash는 불변이다.

[새 W13 앱 프로젝트](http://localhost:4201/#/projects/1790950000001)는 메인 17개/그룹 2개, 기존 [비교 프로젝트](http://localhost:4201/#/projects/1790659628130)는 메인 19개/그룹 1개다. 개별 메인 출력 구간은 **93.16→108.78초**, 사전 고정 단독 18프레임의 개별 클립 존재는 **9/18→18/18**. 반면 그룹 출력은 **10.08→84.15초**로 과도하고, 저장 MoveNet 메인 bbox의 독립 라벨 일치는 **6/18**이므로 실제 메인/멤버 정확도 향상으로 표현하지 않는다. 20~35초 새 메인 출력은 15.0초, 기존은 0.65초다. 새 프로젝트에서 실제 클립 프레임 재생, Nest API 200, 19개 MP4 ffprobe를 확인했다. 설치본/기본 모델/공통 얼굴 API는 그대로이며 commit/push/merge/deploy 없음. 다음은 사용자의 육안 품질 판단과 복수 후보·그룹·identity 정확도 보정이다.

## 10/2 사용자 품질 평가 후 정정

사용자가 위 MoveNet 실험 클립을 실제로 보고 **이전보다 나쁘다**고 평가했다. [실패 원인·새 보수적 결과](../../features/highlights/records/2026/10/02-w13-user-quality-feedback-and-conservative-result.md)에 기록한 대로 22.489초 노랑, 54.52초 파랑 리드를 다른 중앙 인물로 고른 화면을 확인했다. 기존 20개 MP4의 SHA와 멤버 배정을 그대로 보존하고 9/29 그룹 중첩 탈락 두 장면만 `미분류`로 export한 [비교본](http://localhost:4201/#/projects/1790950000002)을 W13 격리 앱에 만들었다. 21 main/1 group, 신규 MP4 2개이며 화면에서 재생 확인했다. `미분류` 구분선을 `인물 확인이 필요한 클립`으로 수정해 얼굴 실패를 단정하지 않는다. Python 집중 41개·Angular 집중 Chrome 55개 통과, API 200. **자동 메인·멤버 정확도 개선이 아니라 안전한 기존 결과+검토용 장면 보존**이다. 기존 설치본/사용자 편집/W14 공통 파일 불변, 새 ML·다운로드·과금·Build5·commit/push/merge/deploy 없음. 다음 정확도 gate는 기존 대비 독립 메인·identity·그룹 품질 향상 검증이다.

## 10/2 메인 오선택 후속 진단과 다음 모델 입력 평가 준비

[저장 자세 후속 비교와 512 입력 준비](../../features/highlights/records/2026/10/02-w13-followup-main-quality-and-512-readiness.md)를 기록했다. 같은 원본에서 새로 표기한 단독 17프레임의 현행 선택은 7/17, 움직임 단독 규칙은 10/17이지만, 앞서 고정한 별도 단독 15프레임에서는 각각 6/15와 5/15다. 사람 검출은 새 17장 중 15장. 새 그룹 4장은 모두 기존 그룹 플래그가 켜졌으나 단독 17장 중 14장도 켜져 있었다. 표본 일부는 과거 관찰과 같은 인덱스이며 한 원본·선택 장면이라 독립 영상 정확도가 아니다. **움직임 단독 규칙과 그룹 플래그 단독 결정은 제품에 적용하지 않는다.**

기존 로컬 Apache-2.0 MoveNet weight를 그대로 두고 입력만 256→512로 바꾸는 metadata 평가 adapter를 격리 Python worktree에 준비했다. 기본값 256은 유지하고 입력 크기·모델/원본/라벨/코드 hash·Mac CPU·횟수·시간/메모리/출력 상한을 [새 manifest 초안](../../features/highlights/records/2026/10/02-w13-movenet-512-manifest.yaml)에 잠갔다. 기존 18장 holdout과 새 원본 라벨 파일도 hash·원본 연결을 검사한다. 테스트는 34개 통과하고 `git diff --check`·compile을 통과했다. **512 실영상 추론은 0회, 새 완료 클립은 없다.** 처음 사용자 요청의 실제 ML 전 범위 확정 조건에 따라 같은 영상 전체 1회·최대 10분/12GiB/250MiB·metadata만 수행할지 확인을 요청했다. 확인 전 manifest는 실행 불가 상태다.

## 10/2 사용자 승인 512 입력 1회와 후속 선택기 검토

사용자가 제시한 512 입력 범위에 “몇 회든 상관없이 진행해도 돼”라고 답했다. 잠근 manifest의 **1회만** Mac CPU에서 실행했다. [실행·점수 기록](../../features/highlights/records/2026/10/02-w13-movenet-512-result-and-selector-probe.md): 기존 모델/원본 그대로 입력만 256→512, 96.365초/RSS 1.105GB/metadata 약 9.1MiB. 45명 고정 사람 표본 검출은 33→45지만 단독 메인 18장 **6→6**, 추가 17장 **7→6**, 추가 비중복 14장 **6→5**. raw 그룹은 84.952→43.844초이나 여전히 길다. 512 단독 교체는 사전 gate 실패로 **미채택**이다. Manifest는 완료 상태로 같은 runner의 재실행을 차단했다.

저장 512 pose의 중앙 가중치·짧은 관절 움직임을 바꿔 본 오프라인 탐색에서 별도 원본 예약 20장의 몸통점 판정은 현행 8/20→후보 15/20이었지만 파랑 리드 `P4`는 **0/4**로 계속 실패했고 선택 bbox 큰 점프는 16→28이었다. 강한 움직임 가중치는 `P4` 일부를 찾았으나 큰 점프 66으로 사후 튜닝·미채택이다. 다음 별도 후보인 Intel Open Model Zoo `human-pose-estimation-0007`의 공식 Apache-2.0/448 입력/OpenVINO Mac CPU 지원을 확인했고, [획득·평가 범위](../../features/highlights/records/2026/10/02-w13-intel-hpe-acquisition-scope.md)와 격리 adapter/승인 게이트 runner·동일 원본 채점 도구를 준비했다. 공식 decoder 반환형을 반영했고 관련 **50개 테스트**·`git diff --check`·compile을 통과했다. 같은 MoveNet 512 결과를 양쪽 입력으로 넣어 기존 수치와 같게 나온 자체 점검은 **Intel 평가가 아니다**. 미승인 manifest의 `--execute`도 거절됨을 확인했다. 공식 모델 파일·runtime은 **아직 다운로드하지 않았고**, 사용자에게 신규 다운로드 250MB 상한을 확인 요청했다. Intel 실영상 ML·얼굴·clip export·제품 기본 모델 변경은 0회다.

## 10/2 Intel 후보 우선순위 정정

사용자가 갑자기 등장한 Intel 후보의 이유를 물어 [기존 YOLO·실험 MoveNet·보류 Intel의 관계](../../features/highlights/records/2026/10/02-w13-why-intel-deferred.md)를 구분했다. **Intel이 더 정확하다는 실측은 없다.** MoveNet 512의 45/45 사람 검출과 6/18 메인 선택 결과는 지금 먼저 고칠 부분이 메인 선정·추적임을 보여준다. Intel 모델/runtime 다운로드 확인 요청은 철회하고 manifest를 `deferred_pending_main_selection_diagnosis`로 잠갔다. 다음은 저장 자세와 원본에서 연속 전환·공동 메인 정답을 확인해 선택 규칙을 비교하는 작업이다. Intel 추론·제품 모델 교체는 여전히 0회다.

## 10/2 사용자 정답 우선 노트북으로 전환

[노트북·실행·검증·남은 결정](../../features/highlights/records/2026/10/02-w13-user-ground-truth-notebook.md)에 정리했다. 사용자가 기존 AI 표본의 주관적 메인/경계를 정답으로 쓰지 말고 본인이 영상 전체의 정답 구간과 복수 메인을 정하겠다고 했다. 해당 입력을 빈 상태로 둔 Jupyter 노트북을 W13 격리 Python worktree에 만들고, 기존 완료 프로젝트 둘과 저장 MoveNet 자세를 읽기 전용으로 보게 했다. 로컬 프록시/노트북 실행 환경과 helper 테스트 6개, 전 셀 실행을 확인했다. 사용자 정답은 아직 0행이므로 **사용자 기준 전후 개선량은 미측정**이다. 새 모델/얼굴 추론·clip export·제품 기본 모델 변경은 하지 않았다.
