# 동결 얼굴 근거 기반 구간 연결 구현 계획

2026-11-02. 사용자가 Astra 검토 결과 적용, 테스트와 같은 세 YouTube 앱 비교를 명시 승인했다. 원본 저장소에서 실행한다. 커밋/푸시는 하지 않는다.

**목표:** SAM 비활성화를 유지하고, 기존 얼굴 pair와 정확한 원본 연속성이 지지하는 미확인 전체 구간만 복원하여 불필요한 경계 하나를 없앤다. 인물/shared 제품 소스는 불변이다.
**설계:** [Astra 검토](02-astra-quality-review.md) §4의 one-sided path. 새로운 결과를 신원 seed로 재사용하지 않는다. 기존 main/group eligibility나 확정 이름을 변경하지 않는다. 역할이 모호한 후보의 적용 여부는 별도로 검증한다.
**대안:** 전체 SAM 복구는 비용 때문에 제외. 단순 pose/이름 전파는 원경 반례 때문에 제외. 기존 소스/얼굴 검증을 유지하는 최소 후보를 먼저 구현하고 측정한다.

- [ ] `face_seeded_paths.py`의 proposal 생성·적용: 방향별 최근접 독립 얼굴 pair, 전체 경로 role/소유/충돌/교대/정확한 원본 검증, frozen evidence, 검증한 방향만 join.
- [ ] 실제 디코더 fixture의 성공/실패 테스트부터: 한쪽 얼굴만 있는 prefix, 실제 컷/경쟁 몸/타인 얼굴/누락 관측/단체 경로/양쪽 다른 이름/동일 프레임 중복, 6초 파트 보존. 원본 gallery/anchors 불변.
- [ ] 최종 eligibility 투영·기존 coalesce 이후, incoming preparation 이전에 통합. 이미 계산한 original main observations와 frozen joint를 사용. 진단과 독립 stage 시간 기록.
- [ ] 저장된 세 영상 재현 및 Astra diff 검토. 원본 범위와 기존 이름/교대 보존, 새 proposal의 역할 확인. hardcoded 영상/시각 분기 금지.
- [ ] SAM 기존 per-attempt 비용/효과 조사. 짧은 부분 실행이 실제 이득인지, 엄격한 총 시간 제한 가능한 취소 구조인지 확인. 기본 파이프라인에 SAM을 켜지 않는다.
- [ ] 관련 테스트와 전체 pytest, 원본 앱 지정 빌드. 실제 UI에서 세 YouTube URL·동일 대표 이미지 제출, queue 제외 실제 시간 비교. ML 실험/빌드와 동시 실행하지 않는다.
- [ ] unknown 시간/짧은 클립 수뿐 아니라 사용자 확인 사례·신규 이름·경계·유효 시간 보존 비교. 큰 품질 해결로 과장하지 않는다.

기준: MMN 314.043초/89클립/미확인6.8072초, ANT 422.293초/134/16.0178초, NEON 483.083초/206/16.7516667초. 입력 및 소스 스냅샷: `/private/tmp/dance-quality-paths-20261102`.

## 검증 중 설계 수정

Astra 추가 검토 결과, one-sided path의 신원 증명과 main 역할 증명을 구분해야 한다. 기존 main fallback 또는 새 central-closeup 크기 필터만으로 네 후보를 자동 확정하는 안은 채택하지 않았다. 구현과 22개 테스트/원본 재생 실험은 `/private/tmp/dance-quality-paths-20261102/experimental`에 보존하고 제품 호출·모듈은 제거했다. 과분할 개선 성공으로 보고하지 않는다.

먼저 적용할 변경은 `named_boundaries.py`의 인접 확정 이름 경계 교정이다. 원본 frozen joint pair가 출력 A→B 경계를 넘어 A임을 확인하고(.15–.6초), 전체 경로 소유/main/group/handoff/primary/alien/source 검사를 통과하면 마지막 확인 원본 프레임 끝까지만 A를 연장한다. 새로운 미확인/단체의 named 승격, midpoint extrapolation, gallery 수정 없음. 기존 `.6초`는 얼굴 독립 pair의 검증 범위이며 클립 최대 길이가 아니다.

실제 저장 데이터 재현: ANT117.317200–117.600817 (0.283617초) 홍은채→사쿠라 교정. MMN/NEON 변경 없음. 원본 검사 포함 추가 계산 약0.005/0.178/0.015초. 이는 실제 앱 시간이 아니며 새 빌드 세 영상에서 다시 측정한다. `observed_main`은 이미 계산한 전체 frame의 role reason/box/경쟁feature/source를 진단에 보존만 하며 선택은 바꾸지 않는다.
