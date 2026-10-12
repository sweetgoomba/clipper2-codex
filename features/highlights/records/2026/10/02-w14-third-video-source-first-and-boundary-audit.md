# W14 세 번째 영상 원본 우선 인물·컷 점검 — 2026-10-02

## 목적과 범위

사용자가 지적한 **같은 인물 과분리**, **다른 사람 오합침**, **짧은 장면**, **배경 인물 누락**을 분리해서 평가한다. 이번 결과는 제품 수정이나 앱 완료 카드가 아니다. 이미 로컬에 있던 음악/댄스 영상 한 편의 20초 창 세 개를 원본 화면만 보고 선정했다. 배경 롤러 인물, 다섯 명의 동시 출연, 어두운 그룹 장면을 일부러 포함한 **스트레스 표본**이므로 인터뷰·토크 사용자의 평균 품질 또는 독립 무작위 표본이라고 주장하지 않는다.

- 원본: `/Users/jina/project/adlight/desktop/clipper_nestjs/.clipper_data/sources/youtube/dZs_cLHfnNA/source.mp4`, SHA-256 `708004f323ad2679f8793b639bfd58f3648c5367934849a313adc462dddd4b6a`, 1920×1080/24fps/5466 디코딩 프레임, 약 227.75초. 새 다운로드 0회.
- 원본만 본 뒤 고정한 [선정](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-source-selection/third-video-selection.json) SHA-256 `6c60f38f8df91629b2d91719728d8ffaf3cf73eb6a41cb7688da7e4b22b890e6`: `[4,24)`, `[58,78)`, `[150,170)`초, 총 60초, 각 96프레임/4.8fps(5프레임 간격). 선정 방식은 목적 표집이다.
- 얼굴 모델 결과를 보기 전 [익명 원본 GT](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-source-selection/third-video-source-first-gt.json) SHA-256 `44cc29b1237bf28cf9d285ce51e06ce85d54f45c4e96597201a360a52c9d3cb2` 고정. 정확한 표본 프레임 14개에 38개 얼굴 중심점과 전경/배경/가림·작음 상태를 표시했다. **명확한 얼굴 23점만** 얼굴 판정 분모에 넣고, 롤러 단역 명확 얼굴 3점을 별도 표시했다. 먼 배경 몸·손만 보이는 장면과 매우 작은 얼굴은 얼굴 ID GT로 추정하지 않았다. 이 GT는 연속 등장 interval 또는 정확한 컷 경계 GT가 아니다.
- [실행 계획](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-source-selection/plan.json) SHA-256 `c5981e9feee00e5ab4df4c65e07174a1b7f6e29f33cb8e27bc42c7b9c616b918`은 원본·선정·GT·runner·코드 SHA, 기존 YuNet `8f2383e4…2552fa4`/SFace `0ba9fbfa…c34e79`, 공통 backend config `bca4dc55…cf4710`, Mac CPU/OpenCV 4.13.0, 최대 300 표본 프레임/2,000관측/600초/4GiB/100MiB와 격리 출력 위치를 실행 전에 잠갔다. 설치 앱과 기존 완료 프로젝트는 읽기 외에 변경하지 않았다.

## 실제 검증

[실행 기록](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-source-selection/probe-existing-model-focus-v2/run-report.json) SHA-256 `88f542436c0b6a8fc2072d848f3f5635a8ec47b018b78e2716b09dfa4b537b6d`: 기존 YuNet/SFace와 후보 대표 선명도 config에서 288프레임/931관측/128그룹(확인 필요 83)/43클립, 15.383초, 최대 RSS 542,539,776B, 출력 2,853,296B. 14개 GT 프레임의 38점 중 37점에 검출 상자가 대응했고, 불일치 1점은 화면 끝에 잘린 인물이다. 명확 얼굴 23/23, 그중 단역 명확 얼굴 3/3 대응. **이 14프레임 밖의 모든 배경 인물 recall로 일반화하면 안 된다.**

[고정 점수](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-source-selection/probe-existing-model-focus-v2/score-source-points.json) SHA-256 `3ebea8820a3d543de4e53b59483f157d1f118d9986bf5c9283815d4e8e82e36c`에서 같은 931개 관측/embedding으로 cosine `0.50/0.55/0.60/0.65` **네 조건**만 대조했다. 명확 얼굴 23점만의 기준 `0.55`는 pairwise 및 B-cubed precision/recall 모두 1.000(같은 사람 26쌍, 다른 사람 227쌍), 동시 출연 다른 얼굴의 같은 그룹 합침 0이었다. 그러나 이는 아주 작은 편향 표본이고 128그룹 전체의 정확도 증거가 아니다. `0.65`는 이 표본에서 같은 사람 분리 5쌍이 생겼다. `0.50`은 이 표본 그룹을 100개로 줄여도, 별도 드라마 원본 우선 GT에서 기존 `0.55`와 동일하게 **서로 다른 두 사람 오합침 380쌍/같은 사람 분리 120쌍**이었다([교차 채점](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-source-selection/drama-threshold-crosscheck.json)). 전역 threshold 변경은 기각한다.

같은 60초 표본에서 컷 판정은 46개 shot, 43클립, 중앙 0.834초, 3초 미만 39개였다. 뮤직비디오의 빠른 실제 편집이 많은 원본에서 `shot=장면=clip` 계약은 사용자가 기대하는 길이와 다르다. 이 수치로 컷 46개 각각이 참이라고 검증한 것은 아니다. 이전 37분 사용자 영상의 3초 미만 클립 601개 중 539개가 3초 미만 shot에 들어 있고, 나머지 62개는 긴 shot 내 얼굴 관측 gap이라는 기존 분해와 일치하는 방향이다. 그러나 어떤 인접 컷을 **하나의 장면**으로 안전하게 볼지는 아직 원본 연속 구간 GT가 없다. 다른 사람의 교차 편집이나 컷 사이 얼굴 없는 순간을 자동으로 붙이지 않는다.

[동일 shot track 후보](../../../../../../.worktrees/person-highlight-mvp-20261001/desktop/clipper_python/evaluation/2026-10-02-source-selection/track-link-offline-probe.json) SHA-256 `882508805f9a5228d874522ad8166f139f4033b92ea76de67dafe7b29183d514`는 저장 관측만 사용한 버릴 수 있는 실험이다. 최근접·상호 최고 embedding/거리/격차와 동시 관측 금지로 32쌍을 이었으나 이 영상 128→123그룹뿐이고 명확 23점 점수는 그대로였다. 별도 드라마에서는 링크 0개, 11그룹 및 오합침 380쌍/분리 120쌍이 그대로다. 실효성/안전성 gate 실패로 Person tracker에 넣지 않는다.

## 결정·미검증·다음 입력

**제품 품질 불합격 유지.** 기존 0.60 검출/0.55 묶기·모든 검출 그룹 기본 표시·확인 필요 표시를 유지한다. 후보 대표 선명도 수정은 W14 격리 코드에만 있고 설치 앱에는 적용하지 않았다. 신규 MP4/ZIP·완료 카드·기존 사용자 수정 저장 변경·W13 Dance adapter 변경·새 모델 다운로드·유료 API·Build5 모두 0이다.

다음 실제 구현 gate에는 (1) 원본 시각 기준 **연속 등장/배경/동시 출연 interval과 의미상 한 장면의 시작·끝**을 별도로 라벨하고, (2) 사용자 영상과 다른 두 장르에서 오합침/과분리 **동시 개선** 및 짧은 장면의 원본 경계 오류만 수정하는 후보를 대조하며, (3) 기존 편집 overlay 보존·단일 MP4/인물별 ZIP/중복 source 구간 규칙을 검증해야 한다. 현 단계의 희소 얼굴 점수로 전체 37분 새 카드를 만들거나 품질 통과를 선언하지 않는다. 대표 이미지 499개 정량 선호, 전체 인물 interval recall, 편집/다운로드 실제 앱 회귀, Windows·W13 공개 DTO 호환은 미검증이다.
