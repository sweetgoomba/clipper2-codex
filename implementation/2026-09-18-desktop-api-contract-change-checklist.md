# 데스크톱 API 계약 변경 체크리스트

날짜: 2026-09-18 KST

목적: Web API의 응답 필드를 추가·변경했는데 중간 Desktop NestJS 투영이나 Angular 소비 계약이 빠져 설치형 앱에서 조용히 사라지는 문제를 방지한다.

## 1. 실제 데이터 경로를 먼저 기록한다

설치형 앱 기능은 기본적으로 다음 경로를 확인한다.

```text
Web API producer
  → Desktop NestJS client/service/projector/controller
  → Desktop Angular API service
  → store/facade
  → component/template
```

기능별로 일부 계층이 없을 수 있지만, 없다는 사실을 검색 결과로 확인한다. Web API와 Angular 양 끝 테스트만 통과했다고 전체 경로가 검증된 것으로 보지 않는다.

## 2. 구현 전 영향 범위 검색

- route 문자열을 모든 저장소에서 검색한다. 예: `rg -n '/credits/summary|currentBenefit' desktop web`
- producer DTO/OpenAPI, Desktop NestJS 응답 타입·허용 목록 투영, Angular DTO/store/template을 모두 목록화한다.
- 값이 여러 번 새 객체로 만들어지는 지점을 특히 확인한다. 객체 spread가 아니라 명시적 필드 투영이면 새 필드는 자동 전달되지 않는다.
- 설치형 앱과 웹 클라이언트가 같은 API를 서로 다른 경로로 소비하는지 구분한다.

## 3. 계약 변경 테스트

각 계층에서 다음 증거를 만든다.

1. Web API: 실제 service/controller 응답과 OpenAPI schema가 새 필드를 포함한다.
2. Desktop NestJS: Web API와 같은 완전한 fixture를 입력하고 로컬 endpoint 결과 전체를 `deepEqual`로 검사한다.
3. Desktop NestJS 호환: 이전 서버의 필드 부재, 명시적 null, 유효 값, malformed 값을 각각 검사한다.
4. Angular service/store: 실제 Desktop NestJS 결과 fixture를 사용한다.
5. Angular component: 최종 사용자 문구와 표시/비표시 조건을 검사한다.
6. 닫힌 투영이 필요한 경계에서는 알 수 없는 필드가 제거되는지도 유지한다.

mock fixture를 각 저장소에서 임의로 따로 만들지 않는다. producer 계약의 필드 집합과 variant를 기준으로 소비자 fixture를 맞춘다.

## 4. 호환성 행렬

배포 전에 최소 다음 조합을 문서와 테스트로 판정한다.

| 조합 | 기대 동작 |
| --- | --- |
| 새 Web API + 새 Desktop | 새 필드와 UI 정상 동작 |
| 새 Web API + 옛 Desktop | 추가 필드를 무시하되 기존 기능 유지 |
| 옛 Web API + 새 Desktop | optional/default 처리로 기존 기능 유지 |
| malformed Web API + 새 Desktop | 잘못된 값을 사용자 UI에 표시하지 않고 명시적 오류 처리 |

필드를 optional로 만드는 것만으로 호환 검증을 끝내지 않는다. 중간 계층이 필드를 실제 전달하는지와, 누락 시 어떤 기본값이 생기는지를 함께 확인한다.

## 5. 완료 전 검증

- producer focused test와 전체 suite/build
- Desktop NestJS bridge focused test와 전체 suite/build
- Angular service/store/component focused test와 전체 suite/build
- 세 저장소 `git diff --check`
- 가능하면 로컬 Web API와 Desktop NestJS를 실제로 띄워 endpoint 응답을 비교
- 설치형 빌드에서 화면 실기 확인

테스트 수와 명령 결과를 문서에 기록한다. 한 계층의 mock 테스트로 다른 계층을 검증했다고 표현하지 않는다.

## 6. 리뷰·배포 확인

- PR/커밋 설명에 producer, bridge, consumer 세 범위를 명시한다.
- 각 저장소의 브랜치와 커밋 SHA를 기록한다.
- 배포 순서는 producer의 하위 호환 여부를 기준으로 정한다.
- 서버 배포만으로 끝나는지, 새 데스크톱 앱 재빌드·재배포가 필요한지 명시한다.
- 실기에서 발견된 누락은 해당 계층의 회귀 테스트로 먼저 재현한 후 고친다.
