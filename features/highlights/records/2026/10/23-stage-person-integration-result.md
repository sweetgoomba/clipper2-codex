# 2026-10-23 무대·인물 통합 검증

## 통합 상태

`origin/dev`를 기준으로 네 데스크톱 저장소의 독립 작업 트리 `feature/stage-person-integration-20261023`에 **푸시된** `origin/feature/person-highlight-w14-20261020`을 병합했다. `dev` 병합·푸시·배포는 하지 않았다. 기존 실행 앱과 인물 작업 트리는 수정하지 않았다.

| 저장소 | 기준 `origin/dev` | 병합한 인물 SHA | 로컬 통합 merge SHA |
| --- | --- | --- | --- |
| Angular | `1a839571` | `7a453546` | `c690307c` |
| Electron | `31bd8041` | `25022554` | `41bf515b` |
| NestJS | `b9602b2f` | `0ec0822a` | `ee98b21b` |
| Python | `09899982` | `ef9ae0df` | `2572c7b0` |

작업 트리: `/Users/jina/project/adlight/.worktrees/stage-person-integration-20261023/desktop/`. 병합 충돌은 Angular 내비게이션의 인물·해외 더빙 동시 노출, Electron의 공용 모델 삭제 보호·인물 설치 상태, Python `uv.lock`에서 해결했다. 모든 merge index에 미병합 항목이 없고 `git diff --cached --check`를 통과했다. Electron의 `dist-app-stage-person/`만 의도한 untracked 빌드 산출물이다. `uv lock --check`도 통과했다.

## 빌드와 회귀 검증

- Angular `build:packaged` 통과, 관련 ChromeHeadless 699개 통과. macOS의 LMDB 캐시 native abort를 피해 빌드에는 `NG_BUILD_CACHE_STORE=sqlite`, 테스트에는 `CI=1`을 사용했다.
- Electron TypeScript build 통과, 전체 1,713개 통과. 여기에는 Dance/Person 모델 설치·삭제와 해외 더빙 모델 공유 테스트가 포함된다.
- NestJS build 통과, 관련 195개 통과. 로컬 테스트 서버 바인딩에 필요한 sandbox 외 실행으로 확인했다.
- Python 공통 얼굴·인물·안무 얼굴/매칭/그룹 관련 409개 통과.
- Apple Silicon macOS 로컬 API 앱 패키징 완료. 전체 `build:app:mac:arm64:local-api` 파이프라인은 컴파일 단계까지 통과했으나 마지막 Electron 다운로드에서 GitHub DNS가 실패했다. 동일한 Electron 43.3.0 ARM64 로컬 캐시 아카이브를 검증하고 `electron-builder --dir`로 최종 패키징을 완료했다. 앱은 ARM64 Mach-O이고 401MB다. 렌더러, Nest 번들, Dance·Person Python 플러그인, 공통 AuraFace 코드, ARM64 `uv`가 포함돼 있다. 패키지 설정은 `identity=development`, `webApiBaseUrl=http://127.0.0.1:3000`, 자동 업데이트 비활성이다.

앱: `/Users/jina/project/adlight/.worktrees/stage-person-integration-20261023/desktop/clipper_electron/dist-app-stage-person/mac-arm64/Clipper Studio (dev).app`

설치본의 실제 GUI 시작·모델 다운로드·실영상 작업은 이번 검증에 포함하지 않았다. 로컬 API가 `127.0.0.1:3000`에서 제공돼야 한다. Windows 실행은 사용자 검증 범위다.

## 안무 품질 판단과 이식 후보

통합된 안무는 YuNet 얼굴 검출과 기존 W13 몸/포즈/구간 정책을 유지하고, 참조 사진과 영상 얼굴의 임베딩을 모두 AuraFace v1로 계산한다. 모델 SHA·정렬·전처리 공간 정보가 매칭에 포함되므로 SFace 저장 벡터를 섞지 않는다. 새 분석 결과에 적용되며 완료된 프로젝트는 자동 재분석하지 않는다. 기존 안무 거리 문턱·ROI 얼굴 소유·track 평균·익명 클러스터·group 수신자 정책은 재보정되지 않았다.

10/14의 고정된 W13 몸 경로 35개 비교에서는 SFace 이름 배정 16개, AuraFace 13개였다. 같은 사용자 정답이 있는 34개 얼굴 관측에서는 각각 정답 18개·19개, 다른 멤버 확정 0개·0개였다. 이 비교는 새 통합 앱의 실영상 실행 결과가 아니며, 이름 배정 감소가 정확도 악화와 동의어도 아니다. 다만 AuraFace가 안무 출력에 일관된 이득을 준다는 근거는 부족하다. 원본 자료와 사례는 `2026/10/14-w14-current-dance-face-comparison-result.md`에 있다.

인물의 다각도 관측·시간 연속성·짧은 조각 연결·동시 등장 배제는 안무 파이프라인에 자동 연결되지 않는다. 안무에는 개별 얼굴 관측과 소유 신뢰도를 판정 단계까지 보존하는 계약 및 원본 영상의 메인 교대/동시 등장 정답이 아직 필요하다. 인물의 임계값·대사 중심 클립 정책을 그대로 적용하면 다른 멤버 오합침이나 잘못된 이름 전파를 검증할 수 없다. 이번에는 추가 이식을 하지 않았다. 선행 조건과 단계별 A/B 설계는 `2026/10/23-shared-face-stage-transfer-review.md`에 있다.

## 직접 출력 확인

기존 완료 프로젝트를 덮어쓰지 않고 같은 원본 영상·같은 참조 사진으로 새 Dance 프로젝트를 만든다. 먼저 설치·모델 다운로드와 로컬 API 연결을 확인하고, 메인 멤버 이름/보류, 동시 등장과 group 수신자, 교대 전후 경계, 작은·측면·가림 얼굴, 처리 시간과 메모리를 이전 결과와 비교한다. 차이가 난 구간의 원본 시각과 기대 멤버를 기록해야 규칙 채택 여부를 판단할 수 있다. 등록 외 인물이 잘못 확정되는 사례는 특히 확인한다.
