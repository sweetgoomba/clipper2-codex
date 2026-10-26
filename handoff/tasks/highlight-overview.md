# W12 — 하이라이트 전체 조사・설계・세션 분리

**2026-10-23 후속 구현 상태:** W14 인물 하이라이트는 데스크톱 4개 원격 dev에 병합됐다. [최신 병합·검증·후속 세션 분담](../../features/highlights/records/2026/10/23-person-highlight-dev-merge-and-stage-usability-handoff.md)을 현재 기준으로 읽는다. Person 결과 UX의 무대 이식과 원본 구간 저장은 [사용성 후속 기록](../../features/highlights/records/2026/10/23-stage-usability-source-ranges-dev-merge.md)처럼 원격 dev에 반영됐다. W13 품질 후속은 별도 무대 파이프라인 세션에서 이어간다. 아래 ‘조사·설계만 완료’는 W12의 9/29 당시 범위다.

W12 조사 세션 당시 확인: 2026-09-29 KST. 상태: **조사·설계·개별 프롬프트 작성 완료 / 실제 평가·구현 미실행**.

[전체 현황](../WORKBOARD.md) · [안무 W13](dance-highlight.md) · [신규 인물 W14](person-highlight.md) · [대사 W01](dialog-highlight.md) · [새 세션 프롬프트](../prompts/2026-09-29-new-sessions.md)

## 목표・이번 세션의 역할

안무/대사 현행 파이프라인과 팀원 변경을 조사하고, 신규 인물 하이라이트의 활용/출력/UX 후보를 구상한다. 공통 요소와 의존성을 정리한 뒤 **안무·인물·대사 개별 작업을 시작하는 프롬프트 3개**를 만든다. 사용자가 새 세션을 시작할 수 있도록 문서를 제공하며, 요청 없이 새 작업 세션을 자동 생성하지 않는다.

## 확인된 작은 근거와 미확인 범위

9/29 최신 로컬 dev의
`desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/pipeline.py`를 읽어 다음 연결을 확인했다:

- `_build_reference_embeddings`(167행 부근): 멤버별 참고 이미지의 얼굴 임베딩을 구하고 평균 임베딩을 만든다.
- 파이프라인에서 참고 임베딩과 장면 내 얼굴 track 임베딩을 구한다(410/454행 부근).
- 얼굴 track들을 클러스터링하고 클러스터 중심을 참고 임베딩과 매핑한다(491/566행 부근).

따라서 “먼저 확보한 멤버 이미지의 임베딩을 영상 인물과 매칭한다”는 사용자 이해는 큰 흐름에서 맞다. 다만 현행 전체 알고리즘, 메인 댄서 선택·tracking·threshold, 팀원 변경에 따른 정확도 회귀는 **이 짧은 확인으로 검증하지 않았다.**

인물 하이라이트는 참조 이미지 없이 영상 인물들을 묶는 아이디어 단계다. 현행 안무가 이미 갖는 clustering/track 코드의 재사용 가능성과 한계를 조사한다. 바로 적용 가능한 완성 플러그인으로 단정하지 않는다.

## 조사 항목과 산출물

1. **현재 구조 지도**: Angular 입력/결과 UX → Nest job/asset/API → Python 단계/모델/장면 메타데이터 → ffmpeg 개별 clip/미리보기/렌더. 파일·함수·설정·사용 모델/버전을 근거로 정리.
2. **변경 이력**: 민준님 등 팀원 변경을 commit/date/diff로 확인. 예전 코드·사용 영상과 비교할 기준선을 정하고 “예전보다 정확도 저하”는 동일 조건 측정 전 가설로 둠.
3. **측정/개선 후보**: 안무의 메인 댄서/얼굴 매칭을 따로 측정, 대사의 STT/후보/타이틀·OCR·속도·메모리·비용을 구분. 최신 모델 후보는 공식 문서/논문/모델 카드로 날짜·상업 이용 조건·OS/hardware·속도·정확도를 확인. 오래됐다는 이유만으로 교체하지 않음.
4. **UX 구상**: 안무의 인물 중심 crop, 잘못 배정된 clip 재배정(복수 선택), 원본 타임라인에서 경계/인물/제외를 편집한 후 실제 clip 생성. 인물의 썸네일 카드/장면 조회/개별 다운로드/선택 합치기 후보를 비교.
5. **공통 얼굴 처리 범위**: 검출/임베딩/track/cluster/대표 이미지/장면 metadata의 재사용 지점을 정함. 향후 다른 플러그인도 쓰는 공개 API·독립 모듈을 설계하고 안무/인물은 초기 소비자로 둠.
6. **분리 인계**: 각 플러그인의 목표, 구현 후보, 미결정, 필요한 repo, 최신 기준 SHA, 측정/검증 계획, 공통 코드 의존성, 새 세션 프롬프트 3개.

## 개별 세션 경계

- **안무**: 인물별 정확도·편집·crop 개선. 인물 카드/clip 이동/타임라인 설계는 [안무 카드](dance-highlight.md)에 있다.
- **인물**: 참조 이미지 필요 여부, 배경 포함 인물 전부 표시, 얼굴 grouping과 대표 이미지, 출력/MVP 결정. [인물 카드](person-highlight.md).
- **대사**: 팀원 변경·STT/LLM/타이틀·OCR 비교와 선택한 개선. [대사 카드](dialog-highlight.md).
- 얼굴 공통 코드의 소유 세션·계약·병합 순서를 먼저 정해 안무와 인물이 같은 경로를 동시에 다르게 고치지 않게 한다.

## 작업 공간・제약

조사 후보는 Desktop 4repo, 필요한 과금/API 계약에 한해 Web API다. 전체 조사는 읽기 전용 dev에서 시작할 수 있다. 구현 시 각 하위 세션별 최신 origin/dev 기반 새 브랜치·격리 worktree를 준비한다. 옛 `dialog-highlight-overhaul-20260904` worktree는 과거 기준선이므로 그대로 최신 구현 공간으로 쓰지 않는다.

처음에는 코드 조사·설계·측정 계획 및 세션 인계 문서를 작성한다. 실제 ML 실행·외부 과금·모델 다운로드·전체 Build5는 기존 HOLD와 새 사용자 지시를 대조하고 구체적 실행 범위를 정한다. 이번 문서 정리는 실제 모델 성능 평가를 실행한 것이 아니다.

## 근거

- [기존 안무 도메인 가이드](../../features/dance-highlight/README.md)
- [기존 대사 전체 감사](../../main/2026-09-04-dialog-highlight-end-to-end-architecture-memory-ui-ux-audit.md)
- [9/29 인계](../../records/sessions/2026/09/29.md)

## 9/29 조사 결과와 개별 세션 인계

[종합 조사·MVP·공통 계약·평가 범위](../../features/highlights/records/2026/09/29-pipeline-design-handoff.md) · [안무 코드·Git 상세](../../features/highlights/records/2026/09/29-dance-code-history.md) · [대사 코드·민준님 변경 상세](../../features/highlights/records/2026/09/29-dialog-code-history.md) · [공식 모델 후보](../../features/highlights/records/2026/09/29-official-model-candidates.md) · **[새 세션 시작 프롬프트 3개](../prompts/2026-09-29-highlight-sessions.md)**.

- 안무 현행은 YOLOv8s Pose와 OpenCV YuNet/SFace다. 7/1 얼굴 backend·sampling·mapping 변경과 8/13 중복 배정 제한이 비교 기준선이다. 메인/얼굴 정확도와 no-face 탈락을 분리하고 정확도 회귀는 측정 전 가설로 유지한다.
- 개별 clip 이동·숨김·undo·숏폼 생성은 구현돼 있다. 복수 이동, tracking crop, 안무 trim, 원본 검토 후 export는 후속 설계 범위다. bbox trajectory는 현재 최종 메타데이터에서 소실된다.
- 신규 인물 MVP는 참조 없는 익명 grouping·대표 카드·등장 구간 탐색·오분류 수정·선택 export 제안이다. 동시 출연 다대다 관계, 모든 인물 기본 표시, merge/split·사용자 수정 보존과 여러 플러그인이 쓰는 얼굴 공통 경로 소유권을 정한다. 자동 배경 필터는 사용자 결정으로 후속에 미뤘다.
- 대사 9/18 민준님 변경은 원본 비율 clip/타이틀 분리와 overlay title repair, 백필·숏폼 생성/복원이다. 현행 기본은 faster-whisper small + Web API gpt-5-mini다. EasyOCR는 OFF·CUDA 조건·의존성 부재를 함께 확인해야 한다.
- 새 세션별 입력/라벨·최대 pass·OCR 540프레임·provider 호출/비용 상한 제안을 기록했다. 실제 입력 경로와 실행 범위는 다음 세션에서 확정하며 이번에는 ML/다운로드/유료 호출/Build5를 실행하지 않았다.

조사 HEAD와 0/0은 로컬 origin/dev 기준이며 이번에도 fetch하지 않았다. 설계·MVP·공통 계약은 제안 상태이고 제품 구현 완료나 원격/서버 최신성 보증이 아니다.

## 9/29 후속 확인·방향 수정

[얼굴/제목 전후·좌표/crop 설명·MVP 수정](../../features/highlights/records/2026/09/29-user-feedback-clarifications.md). 7/1 얼굴 교체 작성자·설계 문서와 9/18 제목 prompt/repair를 추가 대조했다. 인물은 배경 포함 전부 기본 표시하며 soft filter를 후속으로 미룬다. 얼굴 공통 모듈은 향후 다른 플러그인도 공개 API로 사용할 수 있게 설계한다. 새 세션 프롬프트·평가안도 이 방향으로 갱신했다.
