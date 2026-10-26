# 2026-10-23 — 인물 개선의 안무 미확인 인물 적용 자문

## 결론

**적용 후보는 있다. 그러나 인물의 익명 그룹 병합 성공이 안무의 실명 배정 성공을 뜻하지 않는다.** 우선 현재 새 프로젝트의 미확인 사유를 집계하고, 다음 순서로 시험한다.

1. 프레임별 얼굴·소유 근거를 보존하고 여러 각도의 참조/영상 얼굴을 비교한다.
2. 이름이 직접 검증된 영상 속 인물 근거를 고정하여 짧은 미확인 구간을 재검증한다.
3. 같은 물리적 인물이 이어지는 구간에서 최근 얼굴·몸 근거와 제한된 추가 표본을 사용한다.

이번 자문은 소스 대조·기존 검증 기록 확인·국소 테스트다. 새 안무 프로젝트의 로그나 원본을 확인하여 원인을 확정한 보고서는 아니다. 사용자 피드백인 “기존과 같은 결과”만으로 새 모델 미적용 또는 모델 자체 실패라고 결론내리지 않는다. 무대 소스·앱·기존 결과·DB는 수정하지 않았다.

## 1. 확인한 기준과 변경 상태

- 인물 Python: `/Users/jina/project/adlight/.worktrees/person-highlight-w14-20261020/desktop/clipper_python`, `ef9ae0df`, 작업 트리 clean. 푸시 이후 추가 소스 변경 없음.
- 무대 Python: `/Users/jina/project/adlight/.worktrees/stage-person-integration-20261023/desktop/clipper_python`, `2572c7b0`, 작업 트리 clean.
- 두 기준의 `plugins/dance_highlight/dance_highlight/services/{face_cluster,reference_matcher,config,pipeline}.py` 차이는 없다. 무대 통합 이후 인물 전용 후처리가 안무에 추가 이식된 상태가 아니다.
- 통합 4개 저장소 상태와 기존 검증은 [통합 기록](23-stage-person-integration-result.md), 공통 모델/설치 검토는 [공통 얼굴 검토](23-shared-face-stage-transfer-review.md)를 따른다. `dev` 병합·푸시·배포는 보류한다.

아래 코드 경로에서 `Person`은 인물 Python 루트, `Stage`는 무대 Python 루트를 뜻한다. 두 루트는 위 절대 경로다.

## 2. 인물에서 실제 확인된 효과와 한계

| 변경·정확한 구현 | 확인된 근거 | 해석 한계 |
| --- | --- | --- |
| `Person/plugins/person_highlight/person_highlight/analysis.py:188` `_continuous_faces_across_visual_change`, `:309` `ObservationTracker.continues_across_visual_change` | 프로젝트 `1792684044866`의 20.5205/21.021/21.5215초 검출 재생에서 거짓 컷 2개를 복구하고 하나의 얼굴 track 유지. 앞선 19.5195–21.5215초 진단에서는 컷 ID를 고정하면 4 tracks→1. | LED/배경 색 변화의 특정 사례다. 무대의 실제 컷·메인 교대가 같은 조건이라고 입증하지 않았다. |
| `Person/clipper_face_core/clipper_face_core/view_templates.py:79` `build_view_templates`, `:161` `compare_observation_evidence`; `Person/plugins/person_highlight/person_highlight/identity_refinement.py:68` `refine_face_groups`, `:312` `refine_person_groups` | 같은 프로젝트의 얼굴 근거 그룹 재생 273→267, 0.624초. 사용자가 같은 사람이라고 지목한 UI 54·60·49가 UI 10에 연결. 모든 관측 유지, 새 동시 등장 충돌 0. | 저장 관측 재생이며 새 전체 영상 실행이나 독립 신원 정답 검증이 아니다. UI 후보 수 예측도 아니다. |
| 위 최종 비교를 선택된 템플릿에서 원래 관측 전체로 확대 | UI 10↔54 반복 지지 점수 .5476→.7305, 10↔60 .5310→.7699, 10↔49 .5749→.7141. 기존 579개 유효 관측을 33개 벡터로 요약하면서 연결 각도가 빠졌음을 확인. | 점수는 확률이 아니다. 171↔10 .2994, 176↔10 .3532처럼 근거 자체가 약한 조각은 최종에도 분리 유지. |
| `analysis.py:264` `_recent_face_support`, `:320` `ObservationTracker.add_frame`; `identity_continuity.py:19` `body_face_links`; `occurrences.py:486` `_merge_local_body_fragments` | 최근 얼굴 반복 지지, 유일한 얼굴↔몸 대응, 교차·컷·시간 공백·기존 인물 훼손 방지 테스트가 있다. | 이 요소 하나만 켠 실영상 A/B 개선량은 따로 입증되지 않았다. 안정적 몸 ID를 얼굴 신원 정답으로 취급하면 안 된다. |
| `adaptive_sampling.py:11` `AdaptiveSampling`, `:52` `needs_more_samples` | 최근 인물 진단에 기본 2691+추가 120표본 기록. 예전 refinement는 337→331을 재현했으나 사용자가 지적한 분리 묶음은 그 병합에 포함되지 않았다. | 추가 추론 자체가 해결을 보장하지 않는다. 거짓 컷이 나면 연속성·추가 표본이 함께 끊기는 한계도 확인됐다. |

근거 문서:

- `Person/docs/superpowers/reviews/2026-10-23-person-latest-fragmentation-analysis.md`
- `Person/docs/superpowers/reviews/2026-10-23-person-fragmentation-v3-results.md`
- `Person/docs/superpowers/plans/2026-10-23-person-identity-refinement.md`

사용자 실기 피드백에 후보 수 164→126→110→99, 큰 인물의 장면 수 증가가 있었지만 여러 변경이 누적된 실행이다. 개별 개선의 정확도나 안무 실명 미확인 감소 수치로 인용하지 않는다. **이 세션에서 안무의 미확인 실명을 줄였다고 직접 입증한 Person 후처리는 아직 없다.**

## 3. 현재 안무가 잃는 근거와 보류 위치

| 단계·현재 위치 | 코드로 확인한 동작 | 대응 가능한 개선 |
| --- | --- | --- |
| 얼굴 검출/정렬, `Stage/.../services/face_cluster.py:66` `get_face_embedding_candidate` | 확장 몸 ROI에서 검출 점수가 가장 높은 얼굴 하나만 선택. 검출 없음·정렬 실패는 `None`. 다른 얼굴 위치·경쟁 후보는 결과에 없음. | 후보 얼굴 bbox/5 landmarks/검출 점수/실패 사유와 모든 사람 bbox를 보존하고 실제 메인 몸의 얼굴인지 검증. 모델/임계값 변경만으로 소유 오류는 해결되지 않음. |
| 품질 순위, 같은 파일 `:165` `face_embedding_quality` | 선명도는 얼굴 안쪽이 아닌 ROI 전체에서 측정. 의상/자막이 품질 점수를 올릴 수 있음. | 얼굴 crop/얼굴 내부 선명도 사용을 별도 A/B. 인물의 얼굴 크기·정면성 가중치를 그대로 복사하면 작은/측면 얼굴을 더 잃을 수 있음. |
| 표본 보존, `:216` `batch_segment_embeddings` | 기본 구간당 최대 12개 bbox 표본. track별 상위 5개 얼굴 평균만 출력. 유효 얼굴이 1개면 `len(embs)<2`로 제외. `FaceEmbeddingCandidate`는 벡터/품질/JPEG뿐이며 시각·얼굴 bbox를 보존하지 않음. | 개별 관측을 보존. 0얼굴/1얼굴/소유 불명/정렬 실패를 분리. 1개를 보존하는 것과 이름을 확정하는 것은 별도 정책. |
| 메인 장면 누락, `pipeline.py:694` 이후 | 평균이 없으면 `dropped_main_no_face`로 장면 자체를 제외. diagnostics의 `no_face_samples`에는 실제 얼굴 1개였던 경우도 섞임. | 미확인 카드 수뿐 아니라 누락 장면 수/시간도 별도 집계. |
| 익명 클러스터, `face_cluster.py:360`, `pipeline.py:714` 이후 | track 평균의 계층 군집, 3개 미만 클러스터의 최근접 centroid 거리 .45 병합, 구간별 다수 cluster 선택. 현재 이 경로에는 co-visibility/소유 veto 없음. | 단순 작은-cluster 합침을 강화하지 않음. 개별 근거·동시 등장·충돌 보존 뒤 근거 있는 재검증으로 대체 검토. |
| 참조 실명, `pipeline.py:332` `_assign_reference_members`, `reference_matcher.py:57` `assign_reference_person_ids` | 다수 cluster에 남은 track 평균들을 query로 사용. 가상 구간 중간 시각, bbox/track ID 없음, 소유 상태를 모두 `confirmed`로 전달. | 실제 프레임 query와 검증된 동일인 scope를 사용. 다수 cluster 밖 얼굴을 이름이 잘 맞는다는 이유만으로 메인에 되돌려 넣으면 안 됨. |
| 참조 사진 평균, 공통 `gallery.py:17` `build_gallery`, `matching.py:7` `match_reference` | `ReferenceGallery.samples`에는 원본 사진 벡터가 남지만, 판정은 인물당 centroid 하나만 비교. 영상 측도 평균이어서 양쪽 각도 정보 손실 가능. | opt-in 다각도 참조 비교. Person 그룹 비교 함수와 실명 참조 matcher는 현재 같은 기능이 아님. |
| 최종 보류, `reference_matcher.py:166` 이후 | 일반 거리 .60을 통과한 이름도 다른 cluster이면 `min(.45, primary거리+.08)` 초과 시 `duplicate_cluster_distance_exceeded`. | 고정된 확정 인물 근거로 해당 조각을 재검증. guard를 일괄 삭제하지 않음. |
| 합의/전파, 공통 `consensus.py:6`, `pipeline.py:71` `confirmed_group_recipients` | 서로 다른 이름 지지가 있으면 보류. 반대로 현행 `minimum_support=1`은 한 aggregate 지지로 통과 가능. 매칭된 메인과 절반 이상 겹치는 group에 이름 전파 가능. | 충돌을 단순 다수결로 지우지 않음. 새 관측 matcher의 지지 단위를 실제 시점으로 정의하고 group 오전파도 검사. |

### 이번에 확인한 합성 벡터 재현

실제 얼굴 추론 없이 현재 adapter를 호출했다. 아래 벡터 각도는 수학적 예시이며 얼굴의 고개 각도가 아니다.

- 같은 참조 ID의 두 벡터를 ±70°로 만들고 query를 한 참조와 동일하게 주면 개별 사진 거리는 0이지만 centroid 거리는 0.65798이다. 현행 .60 기준은 `distance_exceeded`. 이는 평균이 근거를 잃을 수 있다는 실행 증거이며 실제 사진 정확도 실험은 아니다.
- 참조 A에 primary cluster 거리 0, 별도 cluster 거리 .50이면 두 번째는 일반 .60 이내여도 duplicate 제한 .08에 막힌다. 현재 테스트 `test_duplicate_cluster_guard_rejects_weak_second_match`도 이 정책을 검증한다. 그 두 번째 사람이 실제 A라는 뜻은 아니므로 guard 제거의 근거가 되지 않는다.

`_map_cluster_to_member_name`은 옛 mapper로 파일에 남아 있지만 현재 `run()`의 실명 경로는 `_assign_reference_members`이다. 실제 호출되지 않는 mapper만 고쳐서는 결과가 바뀌지 않는다.

## 4. 우선 적용할 3개 후보

### 1순위 — 평균 이전의 얼굴 관측 보존 + 다각도 직접 참조 매칭

**연결 위치:** `FaceEmbeddingCandidate`/`SegmentFaceResult` → `batch_segment_embeddings` → `select_majority_cluster_embeddings`에 대응하는 근거 선택 → `SegmentEmbeddingScope`/`assign_reference_person_ids`.

단계별로 분리해 적용한다.

1. 기존 평균 출력을 유지하면서 관측 계약을 추가한다. 새 계약만 켰을 때 기존 결과가 동일한지 확인한다.
2. 확인된 같은 메인 몸 경로 안에서 각 얼굴을 개별 query로 비교하고 합의한다. 얼굴별 소유 불명 상태는 그대로 `QueryEvidence.association`에 전달한다. 경로 안에서 타인이 교대하면 동일인 scope로 합의하지 않는다.
3. 직접 참조 centroid 실패 중 개별 참조/영상의 반복 근거가 있는 경우만 opt-in 다각도 비교를 시험한다. 서로 다른 참조 ID 간 runner-up margin과 반복 지지를 확인한다. 단 한 장과의 최고 유사도만으로 확정하지 않는다.

필수 관측 정보:

- source/model SHA, 정렬·전처리/정규화 버전, 실제 분석 설정 fingerprint, 관측 ID.
- 원본 frame index와 측정 시각/PTS. 현재 안무의 `fidx/fps` 시각은 파생 시각으로 표시하고 PTS인 척하지 않는다.
- 얼굴 원본 좌표 bbox·landmarks·크기·score·얼굴 내부 sharpness·정렬/추출 실패.
- 메인/몸 track ID와 bbox, 같은 프레임의 다른 몸/얼굴 후보, 유일 대응 여부/경쟁 점수.
- shot/카메라 전환과 main-run ID, 그 경계의 근거·불확실성. 기존 데이터에 없는 값은 만들어 확정 표시하지 않는다.
- float32 L2 벡터, 선택/제외 사유. JPG는 제한된 진단용, 원본 프레임 배열은 보관하지 않는다.

**재사용:** `SourceEvidence`, `EmbeddingSpace`, `QueryEvidence`, `match_reference`, `combine_reference_matches`; `view_templates.py`의 제한된 다양한 관측 선택/반복 근거/64벡터 블록 비교 원칙.

**추가 구현 필요:** 현행 `match_reference`는 centroid 전용이다. 예를 들어 `match_reference_views`라는 별도 opt-in 공통 함수를 추가하되 기존 함수 동작을 조용히 바꾸지 않는다. `ReferenceSample`의 사진 ID/해시와 `ReferenceGallery.samples`를 사용한다. 정지 사진을 가짜 영상 시각을 가진 `FaceObservation`으로 바꿔 기존 함수를 억지로 재사용하지 않는다. 사진 중복은 이미지 해시로 제거하고 사진 수와 영상 시점 수를 따로 센다. 두 출처 모두 같은 모델 공간인지를 검사한다.

공통 core는 비교/근거 검증만 맡고, 무대 adapter는 메인 소유·동일인 scope·group 수신자 정책을 맡는다. `dance_highlight`에서 `person_highlight` 플러그인을 직접 import하지 않는다.

**기대 범위:** 얼굴은 제대로 잡혔지만 평균/각도 선택 때문에 참조 거리가 나빠진 미확인. 검출 자체가 없거나 잘못된 몸의 얼굴이면 이것만으로 해결되지 않는다. 이미지 증거 없이 현재 미확인의 주원인이라고 단정하지 않는다.

### 2순위 — 이름이 검증된 영상 내 인물을 기준으로 짧은 조각 재검증

**연결 위치:** 직접 참조 결정을 만든 다음, `person_ids`와 `confirmed_group_recipients`를 만들기 전. 원래 결정과 새 결정을 둘 다 보존한다.

- Person `refine_face_groups`의 고정 anchor·반복 지지·runner-up·co-visibility 원칙을 공통의 순수 근거 판정으로 추출한다. `refine_person_groups`의 익명 `PersonGroup` 재구성과 장면 병합은 가져오지 않는다.
- 원본 참조 사진과 여러 독립 시점에서 직접 일치한 영상 얼굴만 named anchor로 고정한다. `association_uncertain`, 추적으로만 연결된 얼굴, 다른 이름과 충돌하는 scope는 anchor에서 제외한다.
- `duplicate_cluster_distance_exceeded` 또는 `distance_exceeded`인 짧은 조각을 원래 관측으로 비교한다. anchor의 잘 맞는 한 프레임만으로 연결하지 않고 반복 지지·경쟁 이름·소유·실제 동시 등장 veto를 모두 적용한다.
- 새로 연결된 조각은 그 실행의 anchor가 되지 않는다. A→B 연결 뒤 B→C로 이름을 연쇄 전파하지 않는다. 모든 후보는 같은 고정 기준으로 판정하며, 탈락한 runner-up도 모호성 계산에서 없애지 않는다.
- 별도 cluster라는 이유만으로 거부되던 사례는 검증된 같은-identity 근거가 있을 때만 보완한다. 현재 duplicate guard는 미검증 후보에서 유지한다. 특히 참조 인물이 한 명뿐일 때는 경쟁 참조가 없으므로 더 강한 영상 반복 근거와 등록 외 인물 반례가 필요하다.
- 짧음의 정의는 관측 횟수만 쓰지 않고 유효 관측 시간/등장 run을 사용한다. Person의 30초·8run·3배/각종 cosine 문턱은 현재 춤 영상으로 보정된 값이 아니므로 그대로 제품 기본값으로 옮기지 않는다.

**기대 범위:** 영상 초반/정면에서 이름을 이미 알아낸 사람의 나중 측면·짧은 조각. 올바른 named anchor가 하나도 없는 사람은 익명 병합이 되어도 여전히 실명 미확인이다.

### 3순위 — 같은 장면 안의 최근 얼굴·몸 연속성과 필요한 곳의 추가 표본

**연결 위치:** 얼굴 표본을 모으는 단계에서 local face run을 구성하고 1순위의 query scope에 전달한다. W13 메인 선택/클립 경계를 우선 그대로 둔다.

- `ObservationTracker.add_frame`, `_recent_face_support`, `body_face_links`의 유일 대응/짧은 시간 창/최근 신뢰 얼굴 원칙을 재사용한다. 고개를 돌리거나 잠깐 가린 한 표본이 평균과 run을 망가뜨리지 않게 한다.
- 현재 Stage `track.py:24` `TrackAssigner`는 선택된 메인 bbox의 IoU·TTL만 사용한다. `FrameRec`/`Segment`에는 `shot_id`나 Person의 몸 appearance가 없다. 동일 track 번호를 동일 인물의 근거로 바로 사용하거나 없는 몸 score/appearance를 확정값으로 채우지 않는다.
- 같은 얼굴 근처에 두 몸/두 얼굴이 경쟁하거나 메인이 교대하면 연결을 중지한다. 단순히 컷 전후 화면 같은 위치에 있다는 이유로 연결하지 않는다. 샷 정보가 없으면 경계를 가로지르는 보완을 보류하고 같은 확인된 run 내부에서만 시험한다.
- 무확정/추적 충돌 근처에서만 추가 얼굴 표본을 제한적으로 수집한다. Person `AdaptiveSampling`의 최대 대기 2개·쿨다운·총 예산 원칙을 참고하되 안무의 12개/구간 표본 구조에 맞춰 별도 scheduler를 둔다. 모든 프레임 재추론을 기본으로 하지 않는다.
- LED 거짓 컷 복구는 이 단계에서도 후순위다. 현재 Stage가 Person과 같은 색 기반 컷 초기화를 쓰는 구조가 아니므로 `_continuous_faces_across_visual_change`를 단순 복사해도 같은 효과가 나지 않는다. 실제 컷 검출과 identity run이 연결되는 경우에만 구조/전체 얼굴 유일 대응 guard를 이식해 시험한다.

**기대 범위:** 이름을 아는 인물의 짧은 고개 회전·가림, 프레임 간 얼굴 특징 불안정. 컷을 건너 옷 색으로 실명을 추정하거나 전체 구간을 한 사람에게 주는 기능은 아니다.

## 5. 공통 안전 조건

- 같은 실제 프레임의 서로 다른 얼굴이 한 identity에 들어가는 제안은 차단한다. 단, 한 얼굴을 겹친 클립/ROI에서 중복 수집한 것은 먼저 동일 관측으로 중복 제거한다. 재생 구간 겹침 자체를 동시 등장으로 취급하지 않는다.
- 카메라/메인 교대 전후 이름이 다르면 다수결로 하나를 지우지 않는다. 하나의 장면에 실제 교대가 있으면 하위 run 충돌로 남기거나 W13 경계 정책에서 별도 다룬다.
- 작은/측면/가림 얼굴은 유효 근거가 있으면 보완 대상이지만 강한 오배정 위험도 있다. 정면 얼굴만 남겨 보류가 줄어 보이도록 분모에서 장면을 삭제하지 않는다.
- 상호 비교의 .70 등 cosine similarity와 안무 .60 cosine distance는 방향·통계가 다르다. 단순 숫자 치환 금지. 다각도 비교는 최근접 기회가 많아 오매칭도 늘 수 있어 별도 margin/반복 지지 보정이 필요하다.
- 현행 consensus는 아무 conflicting match도 majority로 삭제하지 않는다. 새 방법에서도 충돌 제외는 실제 소유 오류·무효 검출 등 독립 근거가 있어야 한다.
- anchor/템플릿 수를 제한하고 원래 벡터는 sidecar나 선형 보관을 사용한다. 64×64 블록 비교는 peak 임시 행렬을 제한하지만 전체 비교 시간까지 상수로 만들지 않는다. 경쟁자 전체 검증의 시간·취소 응답도 측정한다.
- 인물의 음성/대사 묶기·앞뒤 패딩·등장 장면 병합·미확인 카드 숨김은 이 미확인 신원 개선에 포함하지 않는다.

## 6. 새 실행 여부와 원인 분포부터 확인

현재 `dance_meta.json`에서 바로 확인 가능한 항목:

- `stats.reference_match_status_counts`, `stats.dropped_main_no_face`.
- `diagnostics.clips[]`: `match_status`, `match_reason`, `closest_reference`, `closest_distance`, `distance_threshold`, `cluster_id`, `main_track_id`, `body_samples`, `query_images`, `reference_images`.
- `diagnostics.rejections[]`의 `no_face_samples` 및 실제 원본 구간.

이 값으로 우선 `distance_exceeded` / `duplicate_cluster_distance_exceeded` / `conflicting_references` / `no_valid_references` / 얼굴 근거 부족을 나눈다. `no_face_samples`는 0개와 1개가 섞여 있으므로 원본/새 진단으로 세분한다. 여러 사유를 “얼굴 모델 품질” 하나로 합치지 않는다.

새 분석 확인에는 다음 증거가 함께 필요하다.

1. 새 project/job ID와 생성·시작·완료 시각, 사용자가 실제 실행한 .app 경로.
2. 해당 Python child의 실행 파일·플러그인 소스 경로·venv와 실제 import한 파일 해시. 앱 패키지 SHA만으로 오래 살아 있는 child가 새 소스를 쓰는지 알 수 없다.
3. 실제 로드한 AuraFace 파일 경로/내용 SHA와 runtime provider, 512차원·정규화 확인. manifest의 기대 SHA만 기록한 것은 실제 로드 증거와 다르다.
4. 원본 영상 SHA, 참조 사진별 SHA, face 추론 호출/성공 수, 선택 표본·설정 fingerprint. 예전 결과를 표시한 것인지, 새 분석이지만 결정이 같은 것인지 구분한다.
5. 결과 파일 경로/수정 시각과 로그 job ID 연결. 기존 `shared_reference_v1` 문자열만으로 AuraFace를 확인하지 않는다. 현재 meta stats에는 모델/설정 SHA 전체가 저장되지 않으므로 없는 증거는 없다고 적고 국소 진단을 추가한다.

## 7. 최소 실험과 채택/중단 조건

### 비교 고정

- 기준 A0은 **현재 통합 AuraFace 코드**다. SFace 교체 효과와 이번 후처리 효과를 섞지 않는다.
- 최신 사용자 영상의 원본/참조 사진을 복사 또는 읽기 전용으로 해시 고정하고, W13 pose·메인 bbox·구간·렌더 정책을 고정한다. 저장 정보만으로 새 얼굴/시각/bbox를 복원할 수 없으면 해당 기존 구간만 원본에서 오프라인 재추론한다.
- 기존 프로젝트나 사용자 편집을 덮어쓰지 않고 별도 평가 폴더를 사용한다. 과금 큐/MP4 재생성 없이 얼굴 단계만 비교할 수 있게 한다.

### 표본

- 최신 결과의 미확인 중 주된 사유별 5구간 정도를 먼저 원본으로 확인한다. 적으면 전부 사용한다. 최소한 측면/짧은 등장, 두 사람 교차·동시 등장, 메인 교대 전후, 작은/가린 얼굴을 포함한다.
- 현재 올바르게 이름이 붙은 10구간 이상과 등록 외 인물/타인 얼굴 반례를 별도로 포함한다. 원본 얼굴이 식별 불가능하면 정답을 추정하지 말고 평가 보류로 둔다. 참조 ID·UI 후보 번호는 정답이 아니다.
- 이름·메인 몸 소유·변화 시점을 원본과 참조 사진으로 먼저 고정한다. 모델 점수를 본 뒤 유리하게 라벨을 바꾸지 않는다. 구간 앞/중간/뒤와 얼굴 선택 시점, ±1초의 교대 맥락을 확인한다.
- 기존 [10/14 W13 비교](14-w14-current-dance-face-comparison-result.md)의 353관측/34얼굴 정답과 25.759·25.826초 충돌, 57.257–59.459초 무확정 사례도 회귀용으로 활용한다. 그 정답을 전체 클립 신원 정답으로 확대하지 않는다.
- 개발/잠금 비교는 인접 프레임이 서로 새지 않도록 shot/run 단위로 나눈다. 동일 영상 내 성공을 임의의 새 영상 일반화로 보고하지 않는다.

### 실험 순서

1. A0: 새 실행·모델 경로 확인, 사유별 수/시간 집계.
2. A1a: 관측 보존만, 기존 판단 재현. A1b: 개별 query 합의. A1c: 다각도 참조 비교. 각 차이를 따로 기록한다.
3. A2: 고정된 named anchor의 짧은 조각 재검증만 추가. duplicate guard를 통과한 이유와 실제 영상 근거를 저장한다.
4. A3a: 같은 run 연속성, A3b: 제한된 추가 표본. LED 컷 정책은 필요성이 확인될 때 별도 실험.

### 지표·gate

- 대상 구간/실제 main-run을 고정한 상태의 정답 실명 배정, 보류, 오배정, 등록 외 인물 강제 배정. 총수와 시간 비율을 함께 기록한다.
- 익명 분리 수는 별도 보조 지표다. 미확인 카드가 합쳐져 수만 줄거나 장면이 누락되면 성공으로 세지 않는다.
- 기존 정답 손실, 교대 구간 잘못된 이름 전파, co-visible 오합침, group 수신자 오추가를 각각 기록한다. 새 배정과 바뀐 배정은 원본에서 모두 확인한다.
- wall time/추론 호출 수/peak RSS, 표본 수·정확한 관측 보존, 취소 응답을 비교한다.
- 잠금 표본에서 새로운 명백한 오배정·동시 등장 오합침·기존 정답 손실이 하나라도 나오면 해당 후보의 기본값 채택을 중지하고 원인 수정 후 재평가한다. 원래 정답이 틀렸다는 근거 없이 문턱을 다시 맞춰 통과시키지 않는다.
- named anchor가 없는 인물, 식별 불가능 얼굴은 보류를 허용한다. 전체 배정 수 증가만을 gate로 삼지 않는다. 실명 정답 개선이 없거나 이득 대비 시간/메모리 비용이 과하면 해당 후보를 보류한다.

## 8. 이번 검증

- 8개 관련 파일의 테스트 **150 passed / 19.30초**. view templates, matching, consensus, Person refinement/continuity/analysis, Dance reference adapter/face cluster를 재실행했다.
- 최초 `--import-mode=importlib` 명령은 이 테스트 파일 조합에서 `clipper_face_core` namespace 수집 오류로 실패했다. 제품 소스 수정 없이 기존 검토에 사용한 기본 import mode와 명시적인 패키지 PYTHONPATH로 실행해 통과했다. 수집 실패를 제품 회귀로 세지 않는다.
- 실행 명령(Person 루트):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/adlight-pytest-shim:./clipper_face_core:./clipper_face_core/tests:./clipper_plugin_sdk:./clipper_speech_core:./plugins/dance_highlight:./plugins/person_highlight .venv/bin/python -m pytest -q -p no:cacheprovider clipper_face_core/tests/test_view_templates.py clipper_face_core/tests/test_matching.py clipper_face_core/tests/test_consensus.py plugins/person_highlight/tests/test_identity_refinement.py plugins/person_highlight/tests/test_identity_continuity.py plugins/person_highlight/tests/test_analysis.py tests/test_dance_reference_matcher.py tests/test_dance_face_cluster_opencv.py
```

- 위 합성 벡터 adapter 재현 2건 실행. 실제 새 사용자 영상 전체 분석/새 품질 수치/Windows 실행은 하지 않았다.
- 이번 추가 파일은 이 자문 문서 하나다. 기존 다른 세션의 `.codex` 변경과 인물·무대 작업 트리, 실행 중 앱을 보존한다. 커밋·병합·푸시 없음.
