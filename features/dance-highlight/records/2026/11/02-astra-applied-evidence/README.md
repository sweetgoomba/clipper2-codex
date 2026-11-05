# 2026-11-02 Astra 적용·실제 앱 비교 증거

`run-comparison.json`, `provenance-comparison.json`, `final-checks.json`은 실제 패키지 앱의 세 완료 실행을 읽은 결과다. baseline/new 원본 JSON 전체와 영상·얼굴 관측은 manifest의 프로젝트 ID 및 outputRoot에 남아 있다. 개인정보·참조 이미지·수십 MB 임베딩 전체를 이 문서 폴더에 중복하지 않았다.

재현 작업 폴더 `/private/tmp/dance-quality-paths-20261102/app`에는 baseline/new 입력 스냅샷이 있다. 이 폴더에서 비교 스크립트를 순서대로 실행한다: `compare_runs.py`, `check_provenance.py`, `review_cases.py <app 작업 폴더 절대 경로>`, `final_checks.py`. 임시 폴더가 사라지면 manifest의 기존 앱 프로젝트에서 같은 이름으로 JSON을 복사해야 한다. outputRoot와 baseline project ID는 run-manifest에 명시돼 있다.

`task-only.patch`는 이번 작업 시작 시점 대비 제품 변경만 담는다. 기존 미커밋 전체 diff가 아니다. 테스트 두 파일은 현재 전체 사본이며 observed-main 테스트에는 이번 이전의 변경도 포함된다. `experimental/`은 제품에서 제외한 연구 소스다. `sam-addendum-evidence.json`은 과거 SAM 실행 기록의 재집계이며 이번에 SAM을 다시 켠 실측이 아니다.

`ui-verification.json`은 CUA로 확인한 최종 앱 카드 상태 기록이다. 테스트/빌드 로그와 실제 실행된 모듈·패키지 해시를 함께 보존한다. 신규 named_boundaries 타이머는 cluster_map 내부 시간이다.
