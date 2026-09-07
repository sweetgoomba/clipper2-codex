# 웹 환경 이름 local/dev/prod 통일

사용자 승인: Customer와 Admin의 파일명·Angular 빌드/serve 설정·배포 스크립트를 local/dev/prod로 통일한다. 원본 integration 브랜치에서만 수정하며 서버/DB는 변경하지 않는다.

## 보존할 동작

- npm start와 watch는 local, localhost:3000, 실제 로컬 API(useMocks=false).
- npm run build와 Dockerfile 인자 생략은 기존과 같이 개발 서버용 결과물(dev-api)을 만든다. 이름만 dev로 바뀐다.
- 운영 빌드는 prod, api.clipperstudio.ai. dev/prod 모두 압축·최적화·해시 적용.
- environment.ts는 기존 import 진입점과 테스트 기본값을 보존한다. 빌드 시 environment.local/dev/prod.ts로 각각 교체한다. 객체 내부 production boolean은 설정 이름과 다른 기존 런타임 필드이므로 유지한다.
- 이전 production/development/deployment-prod 설정 별칭과 대응 옛 파일은 제거한다. 오래된 명령을 계속 쓰면 실패하므로 호출부를 함께 변경한다.

## TDD 실행 계획

1. infra deployment.test.mjs 빌드 인자 기대값을 dev/prod로 변경. web-build.integration.test.mjs를 local/dev/prod 실제 빌드 및 반대 API 주소 배제 테스트로 변경. 변경 전 실패 확인.
2. Customer/Admin angular.json에 공통 최적화 옵션과 local/dev/prod fileReplacements 구성. 기본 build=dev, serve=local. package watch와 Docker ARG 및 공통 배포 실행부 변경.
3. 환경 파일 이동: production→dev, deployment-prod→prod, Admin development→local, Customer local 추가. env 값은 그대로 유지.
4. 실제 빌드 6종, 기본 build 2종, 배포/PG 설정 테스트, JSON/쉘/변경분 검사. 서버 실행이나 DB 연결은 하지 않음.
5. 기존 사용법 문서의 현재 설명을 새 이름으로 수정하고 역사 기록에는 변경 시점을 추가. 저장소별 checkpoint commit, 원격 push 없음.

## 검증 결과

- 새 명칭 기준 테스트에서 배포 인자 2개와 실제 빌드 6개가 예상대로 실패하는 것을 먼저 확인했다.
- 구현 후 `node --test scripts/deployment.test.mjs scripts/validate-toss-payments-env.test.mjs scripts/web-build.integration.test.mjs` 101개 통과.
- Customer/Admin 각각 local/dev/prod/옵션 없는 기본 빌드 8종의 실제 JavaScript 결과물에서 목적 API 포함과 반대 환경 API 부재 확인. dev/prod 빌드 source map 미생성 확인.
- 옵션 없는 빌드는 계속 dev API를 사용한다. 새 환경 파일에서 API 주소·production/useMocks 값은 기존 해당 용도의 값 그대로다. Admin environment.ts의 기존 테스트용 mocks 기본값은 변경하지 않았다.
- 이번에는 API/DB/데스크톱 변경이 없으며 실제 서버 배포도 하지 않았다. Windows runner 등 별도 범위에 이름 변경을 적용하지 않았다.
- 옛 환경 파일은 이름을 바꾼 것이며 내용은 보존된다. 복구가 필요하면 Git 이전 커밋에서 확인할 수 있다.
- 별도 read-only 리뷰에서 지적 사항 없음. 리뷰에서도 배포 테스트22개와 세 저장소 diff 검사를 재확인했다.
- 로컬 checkpoint commit: Customer `70ac16b`, Admin `472e35e`, Infra `ea57a1a`. 기존 integration 브랜치에만 커밋했고 dev/main merge·원격 push 없음.
