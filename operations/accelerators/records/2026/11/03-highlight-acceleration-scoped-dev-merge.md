# 하이라이트 자동 가속 — 최신 원격 dev 통합

기록: 2026-11-03T22:39:22.651023+09:00

사용자 요청으로 네 저장소의 원격 `dev`에 병합·푸시하고 실제 서버 SHA가 검증한 커밋과 일치함을 확인했다. 사용자가 추가로 선택한 **이번 세션의 가속 변경만 반영** 범위를 적용했다. 다른 세션의 미커밋 안무 품질 개선은 통합하지 않고 원래 작업 폴더·stash·소스 사본에 보존했다. 강제 푸시·PR 우회·기존 로컬 dev 체크아웃 변경은 하지 않았다.

## 원격 반영 결과

| 저장소 | 반영 전 최신 dev | 반영된 dev | 범위 |
|---|---|---|---|
| clipper_python | `4b54bced17e13aadbeb97be75259b7f7213a9b24` | `469370b206c82a8a1d4a0e181e72fb6ce8c3910c` | 132파일 |
| clipper_nestjs | `c8b71e7fc2079d666c0c3e32a6fc690190613dd9` | `a75f6ba46d91dce4bbde35c2871c51e63f7cee3e` | 38파일 |
| clipper_electron | `8e70e99bc44e164d84dba16dd253b3b939928859` | `540c6e6544e8aa46ad97224958d7e543c44c1c0c` | 23파일 |
| clipper_angular | `c558fb3f13090877371d1fe20d56028bb8804118` | `4d508c0d3b0c3009f48f171edd6bfac11de33d04` | 9파일 |

검증 중 새로 올라온 Nest W20 macOS 프로세스 식별 보정과 Angular I-19 대사 결과 레이아웃도 다시 가져와 포함했다. 해당 파일들은 그 원격 버전과 정확히 같다. 원격 다른 변경을 덮어쓰지 않았다.

## Python 범위 분리와 호환 조정

세션 시작 전의 안무 품질 WIP·프리패치·legacy GPU 실행기가 테스트용 작업 트리에 함께 들어 있었다. 단순 통째 복사 대신 원격 HEAD의 안무 처리를 기준으로 새 어댑터·작업 수명주기·복구·교정 연결만 추출했다.

- Dance production은 app, face_cluster, pose_engine, pipeline, cut_face_link, sampled_face_link 6파일만 변경. 나머지 45파일은 원격과 바이트 단위로 같다.
- pipeline 변경은 작업량 추정과 불변 원본 보관뿐이다. 원격의 SAM CPU·신원 판정·구간 처리 호출은 유지했다. 기존 안무 품질 WIP의 SAM 비활성화·인물/단체 구간 개선을 이번 병합에 포함하지 않았다.
- 원격의 얼굴 CPU 기준 경로를 유지하고 새 공통 승인 어댑터만 연결했다. 미커밋 legacy GPU helper가 자동 활성화되지 않도록 제외했으며 CPU 기준 실행은 optional GPU를 거치지 않는다.
- SFace는 Cut/Sampled 두 소비자가 같은 승인 경로를 사용한다. 원래 정렬·가중치·입력·판정 수치는 유지한다.
- 실제 원격 SAM 실행과 모순되던 이전 WIP의 disabled 상태 표시는 복사하지 않았다. 이전 작업의 legacy GPU 전용 테스트는 현재 CPU 기준 및 소유 worker deadline 회귀로 맞췄다.
- 새 범위 재현 5건 RED 후 집중 433개 GREEN. 독립 검토에서 범위와 추가 CPU 복구/SFace 확인 4건을 통과했다.

## 검증과 경계

| 검사 | 결과 |
|---|---|
| Python 전체 | 2,890 통과, 기존 렌더링 6실패, 5skip |
| Python 통합 후 집중 | 433 통과 |
| Python Ruff / uv lock --check --offline | 통과 / 144패키지 일관성 확인, 설치 없음 |
| NestJS 최신 통합 전체 | 5,340 통과 |
| Electron 최신 통합 전체 | 1,962 통과 |
| Electron 공백 정리 후 관련 검사 | 23 통과, 컴파일 파일 326개 완전 동일 |
| Angular 최신 UI·API·재생·대사 관련 | Chrome 165 통과 |
| Angular 스타일 | 21 통과 |
| 네 저장소 통합 Mac 패키징 | 성공 |
| 실제 패키지 코드·자산 | 787개 일치, 의존성 9개 확인 |

Python의 annotation golden 5건과 fadeblack 렌더 1건은 기존 기준선과 실패 ID가 동일하다. 원격 렌더 코드·테스트·골든 자료에 이번 변경을 넣지 않았으며, 이를 해결됐거나 전체 테스트가 모두 통과했다고 표시하지 않는다. 별도 안무 WIP를 제외했으므로 이전 전체 검사 3,379와 이번 검사 수를 동일한 파일 집합으로 비교하지 않는다.

실제 Windows 빌드·다양한 GPU의 최종 품질/속도/고장 검증은 이 통합 검사에 포함하지 않았다. 품질 승인 gate를 완화하거나 새 인증서를 생성하지 않았다. 기본 CLI의 native 전체 영상 인수 범위는 기존 수정 보고서의 제한을 유지한다.

## 보존과 재현 자료

원래 desktop 네 저장소에서 기록한 소스 4,802개, HEAD와 브랜치가 병합 후에도 그대로임을 재확인했다. 모델·개인 교정 자료·개인 환경·생성 앱·검증 로그는 커밋에 넣지 않았다. 기존 설치 앱을 종료하거나 교체하지 않았고 공유 Python 가상환경을 변경하지 않았다.

- Python 전체 보존 stash: `7e48aaa62ecf9dca211d02ab27a9964f88e574dc` (697개 소스 사본과 SHA도 별도 보존).
- Nest 사용자 access WIP: `383174d0e0c3ed8a2566c3602eec06ffb4e16324`.
- Angular overlay 보존: `9c42e703f52a7c48dc79c13de7f3209fdd190046` (이미 원격 반영된 동일 내용).
- 기존 ZIP/시험 앱은 이전 단계의 동결 전달물로 보존했다. 이번 패키징은 별도 검증 폴더를 사용해 덮어쓰지 않았다.

검증·원격 SHA·재현 로그 hash: [검증 JSON](03-highlight-acceleration-scoped-dev-merge-validation.json). 상세 로컬 증거: `/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/.implementation-evidence/dev-merge` 및 각 Node 작업 트리의 `.implementation-evidence/dev-merge*`.

이번 작업의 전달 기준은 네 저장소의 위 원격 dev 커밋이다. Windows에는 이 버전의 소스를 받아 빌드하면 된다. 기존 ZIP을 자동 갱신하거나 Windows 설치본을 교체한 작업은 아니다.
