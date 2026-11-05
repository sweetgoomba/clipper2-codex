# 안무 하이라이트 품질 독립 검증 인계 — Astra xhigh

독립 검증 세션: `01a19bab-62d3-7c52-8538-54703f0fc96a`, 모델 `gpt-6-astra`, reasoning `xhigh`, 원본 adlight 프로젝트(local). 생성 요청 성공 및 active 실행 확인.

2026-11-02. 사용자가 새 세션의 Astra xhigh에게 독립 검증·평가·개선안 제시를 요청했다. 기존 구현 세션은 제안을 받아 구현·회귀·실제 앱 비교를 담당한다. 이 문서는 출발 자료이며 기존 분석의 결론을 정답으로 취급하지 않는다.

## 역할·작업 경계

- 새 세션: 현재 코드와 실제 원본/관측/사용자 피드백을 직접 검증한다. 근본 설계, 과도한 거절 조건, 순서·표현 문제까지 재검토하고 재현 가능한 우선순위 개선안을 제시한다. 제품 파일은 부모 세션이 수정한다. 읽기 전용 분석과 별도 scratch 진단을 수행하고 보고서를 `.codex/features/dance-highlight/records/2026/11/02-astra-quality-review.md`에 작성한다. 먼저 확인한 구조적 문제와 우선 검증할 1안을 중간 보고에 남기면 부모가 병행 검증할 수 있다.
- 기존 세션: `2026.10.19-23 무대 하이라이트 파이프라인`, thread `01a1435b-139b-70c2-ac58-36dd9e010b1d`. 새 세션의 보고와 상태를 직접 읽어 적용·검증한다.
- 원본 `/Users/jina/project/adlight/desktop/clipper_python`, branch `fix/dance-gpu-performance-20261102`, HEAD `4b54bced17e13aadbeb97be75259b7f7213a9b24`. 많은 미커밋 변경이 실제 빌드 상태다. HEAD만 검토하면 안 된다. 기존 변경 보존, 커밋/푸시/병합/재설정 없음.
- 새 worktree/별도 제품 빌드를 만들지 않는다. 현재 제품 코드 쓰기는 기존 세션이 맡는다. 새 연구 모델/기법은 제안할 수 있으나 현재 앱과 인물/shared 코드를 변경하지 않는다.
- SAM 몸 추적 두 호출은 사용자 지시로 계속 비활성. 인물 하이라이트 영향 금지. Windows도 고려. 새 세션은 시간/과금/품질을 검토한다. 기존 승인: 기존 세 YouTube 재실행 및 크레딧 사용 한도 없음.
- 기존 임계값과 휴리스틱도 검증 대상이다. 근거 있는 정책 변경은 가능하나 미확인을 추측 이름으로 채우거나 짧은 클립을 삭제해 수치만 개선하면 안 된다. 기존 결론에 갇히지 말고 직접 반례와 대안을 찾는다.

## 사용자 목표·판정 기준

품질이 현재 만족스럽지 않다. 주요 문제는 잘못된 메인/이름, 미확인, 연속된 파트의 과분할, 실제 메인 교대를 한 클립에 묶음, 준비/마무리 동작 누락이다. 같은 멤버가 6초 동안 메인이면 6초 한 구간이어야 한다. 일괄 3초 제한은 사용자가 거절했고 현재 없다. ‘많이 쪼개 달라’는 과거 요구를 임의 길이 제한으로 해석하지 말 것.

카메라 각도나 컷이 바뀌어도 같은 멤버 파트는 이어질 수 있다. 잠깐 넓어졌다는 이유로 모두 단체로 자르면 안 된다. 스폿라이트·솔로 안무·시선·카메라 초점·전경 보행자와 실제 중앙 솔로의 구별이 필요하다. 먼 단체 장면에 억지로 메인을 고르지도 말아야 한다. 단체에 중앙 인물이 있다는 이유만으로 개인으로 확정해서도 안 된다. 단체와 개인이 모두 타당한 장면과 멤버 교대 구간이 존재한다.

과거 Made My Night 10/28 15:54 결과의 사용자 피드백(클립 번호는 당시 결과 기준, 최신 번호와 혼용 금지): 김채원30은 앞에서 지나가는 김채원 대신 중앙 솔로 허윤진; 김채원42는 초점/줌인되는 카즈하; 김채원35/36/37(38까지 가능),55/56 등은 이어져야 함;58/59 등 1초 미만 조각 다수. 사쿠라로 잘못 선택된 장면은 일렬 선 멤버들 앞에서 따로 안무하는 홍은채를 봐야 함; 사쿠라9/11 연결,45–약48초 준비부터 사쿠라 구간; 카즈하40/43/45는 약89–93초 하나의 파트. 이 중 무엇이 이미 고쳐졌고 무엇이 남았는지는 현재 원본과 결과로 검증해야 한다.

## 현재 결과와 속도 (품질 정답률은 아직 없음)

|영상|최신 프로젝트|클립|1초 미만 개인+단체|미확인 개인 합산 초|실행 시간|
|---|---|---:|---:|---:|---:|
|Made My Night|1793610108675|89|42|6.8072|314.043초|
|ANTIFRAGILE|1793610363935|134|79|16.0178|422.293초|
|NEON|1793610789306|206|124|16.7517|483.083초|

최신 원본 앱 3영상 합계1219.419초(20:19), 직전 GPU 앱1597.736초(26:38)에서23.7% 단축. **‘메인150→140초’는 NEON main_selection 계산 실행 시간이며 출력 구간 길이가 아니다.** NEON 확정 멤버 구간 길이 합계160.492067초는 전후 동일하다. 미확인0.066733초가 단체로 교정된 작은 변화만 있다. 전체 개인 main 합계177.310467→177.243733초. 합산 길이는 겹침이 있으면 union 길이와 다르다.

MMN/ANT는 직전 대비 클립 전체 행·썸네일·카드·판정 프레임 동일. NEON은154.888067–155.221733을 단체로 복원,155.155–155.221733 미확인 한 조각을 포함. 다른 확정 이름과 범위는 동일,205개 기존 구간 썸네일 bytes 동일. 판정9,266샘플 중5개만 바뀜. **기존 결과 보존은 정답이라는 뜻이 아니다.** 전체 정확도/누락 정답표는 없음. 짧은 클립 수나 미확인 초만으로 성공을 판정하지 않는다.

## 원본·실제 실행 증거 위치

모든 경로는 `/Users/jina/project/adlight` 기준이며 원본 영상은 아래 appdata에 있다.

- 최신 결과 보고서: `.codex/features/dance-highlight/records/2026/11/02-deep-profile-results.md`.
- 영구 증거: `.codex/features/dance-highlight/records/2026/11/02-deep-profile-evidence/`: `final-summary.json`, `run-comparison.json`, `run-manifest.json`, `provenance-comparison.json`, `package-source-manifest.json`, `task-only.patch`, `profile-summary.json`, `reviewed-case-comparison.json`, `reviewed-case-analysis.json`, `neon-semantic-comparison.json`.
- 실제 앱 데이터 root: `/Users/jina/Library/Application Support/Clipper Studio Dev`.
- `projects/items/ID.json`의 `project`, `jobs/items/dance_ID.json`의 `job`, `projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa/ID/json/dance_meta.json`, 같은 프로젝트 `diagnostics/face_evidence.json`, `refs/dance/`.
- YouTube 원본: appdata `sources/youtube/BZDZBUyaJbA/source.mp4`(MMN), `p_XdZdg9oGc/source.mp4`(ANT), `93j1fDGi_-8/source.mp4`(NEON). 실제 실행 URL은 각각 https://youtu.be/BZDZBUyaJbA , https://youtu.be/p_XdZdg9oGc , https://youtu.be/93j1fDGi_-8 . 입력은 로컬 파일이 아닌 YouTube URL로 했고 양쪽 모두 같은 다운로드 캐시를 사용했다.
- scratch 재현: `/private/tmp/dance-deep-profile-20261102`, 이전 `/private/tmp/dance-main-face-20261102`, `/private/tmp/dance-mask-cost-20261102`, `/private/tmp/dance-yunet-sface-20261102`.
- 직전 GPU 앱 기준 프로젝트1793603593237/1793603739918/1793603971986의 meta·관측 복사본은 scratch `app/baseline/`에 있다. 영구 manifest와 실제 appdata에서 경로를 재확인한다.
- 별도 worktree의 옛 evaluation-output에 일부 수동 영상이 있다. 원본 제품 소스와 혼동하지 말고 자료로만 읽는다.

## 현재 등록 멤버 경로의 파이프라인 지도

실제 소스 `plugins/dance_highlight/dance_highlight/services/pipeline.py`가 정본. 아래 설명도 검증한다.

1. URL 원본/대표 이미지 확보 → YOLOv8s Pose(기본 config),analyze_skip4. 약59.94fps 원본에서 약15Hz 포즈 관측. MainSelector와 가벼운 TrackAssigner로 메인 후보/soft group 추정.
2. `observed_main.refine_main_roles`: 얼굴/포즈 대응·구도/초점·카메라 episode·handoff 판단. 원본 색상 컷 전수 검사와 필요 시 두 얼굴 모델 대응을 사용.
3. `segment.classify_main_scenes` 및 `native_scene.refine_native_scenes`: 원경 단체와 no_person/main 분리. 추가1920 pose 관측의 전신/크기/원본 전경/시간/컷 조건이 매우 보수적이다. 역할 분류와 신원 추론용 관측은 `recs`/`evidence_recs`로 나뉜다.
4. `scene_boundaries`: 원본에서 경계 정렬. 출력 가능한 eligible_main과 group을 만들되 신원 추론은 앞선 원본 메인 관측을 유지한다. 같은 작업의 원본/컷 증거는 캐시한다.
5. `face_cluster.batch_segment_embeddings`: 등록 멤버는 모든 sampled main 관측의 얼굴 근거를 보존. 확장 ROI YuNet, 포즈 소유 검증, 필요 시 measured eye-roll 회전 재시도, AuraFace512 정렬/특징. CPU ROI 검출과 다음 프레임 prefetch를 겹친다. Anonymous 클러스터 fallback도 있으므로 legacy 설정만 보고 등록 경로를 설명하면 안 된다.
6. `member_timeline`: 주 참조 얼굴/독립 영상 anchor와 이름 타임라인. 얼굴 이름 변화/불연속 근거를 경계로 나눔. `secondary_faces`: SFace128 별도 gallery와 independent video anchor로 보조 이름 검증, joint dual 결과를 동결. 같은 프레임 대안은 독립 temporal vote가 아니다.
7. `body_continuity.bridge_main_face_gaps`: 기존 포즈 대응으로 짧은 얼굴 공백만 검증(약0.5–1.2초 실행 비용). `collect_source_context`: 컷/카메라 근거만 수집. **SAM `recover_mask_names`와`revalidate_named_segments` 둘 다 호출 주석,0초.** 주석 보존 구현과 실제 활성 경로를 혼동하지 않는다.
8. `scene_context`, `focal_output`: 근거 있는 개인 문맥/카메라 episode 복원. `project_main_at_scene_cuts`, 미확인 handoff 분할로 출력 구간 투영.
9. `recover_final_face_edges`, `output_continuity.coalesce_named_output`: 최종 구간의 실제 얼굴 근거/교대 경계를 재확인해 연결. `incoming_context`로 다음 멤버의 준비 동작을 근거가 있으면 포함.
10. `visible_member_refinement`/group 귀속, 원본 시간 구간·썸네일·카드와 진단sidecar 저장. 개인/group이 겹칠 수 있다. 현재 제품은 분석 때 모든 클립 MP4를 미리 만드는 방식이 아니다.

현재 제한의 핵심: 등록 경로 group 최소.15초/merge_gap0, `MAX_SUPPORT_GAP_SECONDS=.6`, valid observation detector score>=.8, 강한 anchor>=.9, 반복 anchor 독립시점>=.15초, 주 direct거리<=.6, SFace photo거리<=.637/margin>=.08, joint mean<=.5/각모델<=.6/margin>=.08 및2초query주변배제 등의 조합. config의 min_main_seg_sec1.2/min_group_seg_sec1.2/face_sample5/candidate12가 등록 경로 전체에 그대로 적용되는 것은 아니다. 실제 활성 함수와 saved config로 재검증할 것. 이 수치의 적절성도 검증 대상이다. 일괄 최대3초 제한/서비스1초미만삭제 규칙 없음.

## 관측된 원인·한계와 시도

- 원경에서 장식물/LED가 사람으로 오검출되거나 실제 사람의 머리·관절이 누락되어 역할/eligible_main이 흔들린다. NEON의 main 짧은91개 중54개는 scene projection 경계,49개는 identity 경계,27개는 face coverage 경계에 닿는다(서로 겹침, 원인 확정 exclusive counts 아님).
- 직전 세 기준 결과에 바로 맞닿은 동일 이름 확정 개인클립은0개였다. final 단순 같은 이름 병합만으로 남은 조각을 해결할 수 없다. 그 사이에 미확인/다른역할/증거공백이 있다.
- 전체 얼굴 대안8시점 비교: ANT4.671/4.938/5.339/5.739,MMN38.372/38.705/39.106/39.306. 원본 얼굴 폭21–62px, 조명/옆얼굴/soft detail. 같은 몸 소유는유일하나원본/ROI정렬대안에서새채택이름0/8. 기존6유효쿼리joint 재현, 거리차최대1.8e-7. 얼굴 검출 점수와 이름 정확성은 별개다. 작은크기 하나로 모든 실패를 단정할 수 없다.
- `roi-fullframe-eight-results.txt`와 `roi-fullframe-eight/`(31MB)의 원본15값·PNG·벡터·동결gallery·전체후보표를 직접 본다. 정렬이1px정도 달라도embedding은 크게 달라질 수 있다. 이를 성능 최적화만으로 해결했다고 보지 않는다.
- strict 원경 포즈 경로 bridge,한쪽다리추가관측,동결joint로unknown edge 복원: 모두3영상 추가회복0. 그 뒤 실제 원본을 보고 stage decoration예외를 좁게 교정하여 NEON만 작은 회복. 최초 예외는 native실패/원본실제전경 충돌의 회귀가 있어 원본머리/몸통근거를보존하도록 고쳤다.
- 두 full person+독립머리·torso 세번째 추가안도3영상추가장면0. 남은 veto는 다리 하나보다 복합적.
- 과거 전역 fullframe 교체는 기존 확정 이름을 바꿔 거절. 원본physical camera edit를 단지색상cutFalse로 통과시키는 안은실제반례때문에거절. MMN38.205–39.339는실제카메라전환이있지만사쿠라연속파트라는사용자판단과통합해야한다. 기존cutveto가사용자요구와충돌하는지검토한다.
- SAM은 미확인 보완/이름 검증에 도움을 주었으나 NEON CPU 비용이20분을 넘었고 최적화후에도1분을 넘어 사용자지시로꺼둠. 속도는줄었지만미확인·과분할이늘어난부작용이있다. 복원으로해결하지말고SAM없이대안을검토한다.
- 성능은 반복디코딩/갤러리직렬화/SIFT/포즈대응캐시와CPU/GPU겹침으로개선. GPU는YOLO MacMPS/WindowsCUDA, AuraFace+SFace MacCoreML/WindowsDML·CUDA, 원본크기YuNetGPU/ROI는CPU. ROI dynamicCoreML이CPU보다느려미채택. 인물/공유 소스는 그대로다.

## 사용자 확인 기준 (원본 시각, 허용하는 모호함 포함)

- ANT4.57–6.14 홍은채.8.375–약9.0 홍은채,약9초부터김채원으로교대,9.4–10.277김채원.32.3까지홍은채,33.4부터김채원,32.633–33.433전환은양쪽어느메인에붙여도가능.
- NEON78.378–79.680 및 해당 확인영상 전체는시리(XILI).150.617–152.619/183.15–184.82는먼단체.183초확인영상앞클로즈업은오아(Oa),이후줌아웃단체에서여러멤버로박스가흔들리는것은잘못된메인선택.
- MMN1.9–약2.3자막intro(no_person),2.3–4.37단체.10.91–11.31카즈하또는단체모두가능(중앙솔로/스폿라이트).34.73–35.44사쿠라또는단체모두가능(후속사쿠라메인문맥허용).37.738–39.339사쿠라.45–약48사쿠라준비부터마무리.89–93카즈하연속파트(각도전환으로쪼개지말것).79–79.81카즈하→김채원교대는카즈하끝에포함가능,이후김채원또는단체,81초이후먼단체는굳이개인지정필요없음.
- 최소14사례는 `reviewed-case-comparison.json`에정리. 이14개만으로전체정확도를계산하지말고다른오류/정상반례도확인한다. 현재case동일=품질정답이라는뜻이아니다.

## 요구하는 검토 산출물

1. 현재구조·실제출력·위분석의오류검증(파일/함수/증거). 관찰/확인원인/가설을구분한다.
2. 품질문제를메인선택/장면분류/신원이름/경계분할·연결/누락·중첩으로나눠재현. 얼굴모델원인과구간정책원인을혼동하지않는다.
3. 가장효과가클가능성이있는2~3개구조적개선안. 기존후처리증식이나문턱완화만반복하지말고,왜기존시도가막혔는지와구체수정지점·계산비용·Windows/Mac·실패위험·검증반례를제시한다. 새모델/해상도/관측정책/구간추론설계도근거가있으면제안한다.
4. 1순위안은부모가즉시구현·검증가능한수준의알고리즘,입출력,테스트fixture,실측계획을쓴다. 가능하면saved data기반의짧은독립진단으로현재보다나아질수있음을보인다. 모든새검사를실제시청정답평가라고표현하지않는다.
5. 품질평가는unknown0/클립수최대화가목표가아님:잘못된확정이름·원경메인오선택·실제교대혼합·동일인과분할·유효파트누락·구간길이분포·계산비용을함께본다. 타당한짧은파트는남기되불필요한조각은줄인다. 정답부족이병목이면기존피드백을활용해최소필요확인범위를구체화한다.

## 테스트/빌드 기준

직전전체pytest2548passed/6failed/6skip,후속native회귀추가뒤관련120passed. 기존미수정렌더링6실패(annotation goldens5,ranking fadeblack1)와새실패구분. 실제원본앱55소스해시일치. 제품빌드명령 `PATH=/Users/jina/.nvm/versions/node/v24.19.0/bin:$PATH npm run build:app:mac:arm64:local-api`(원본clipper_electron). 품질제안받기전같은실험을불필요하게재실행하지말것. 새세션분석증거는별도scratch에보존한다.
