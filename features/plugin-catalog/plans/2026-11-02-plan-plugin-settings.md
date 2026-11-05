# 요금제별 플러그인 일괄 설정 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. 사용자 승인 목업을 실제 UI/API로 연결한다. 커밋/푸시 없이 기존 전용 워크트리에서 진행한다.

**Goal:** /plans에서 관리 버튼 하나와 공통 상태 배지, 네 등급 비교 모달로 허용 목록·포함 정책을 함께 저장한다.
**Architecture:** 관리자 catalog API에 pluginSettings 공통 정책과 일괄 PUT을 추가한다. 공통 정책은 별도 singleton DB 테이블에 저장하고 각 등급에는 실제 허용 목록을 저장한다. 기존 실행 권한·공개 catalog는 동일한 등급 목록을 그대로 읽는다. 기존 목업과 실제 화면은 같은 편집 컴포넌트를 재사용한다.
**Tech Stack:** NestJS/TypeORM/PostgreSQL, Angular/Material, Jest/Karma.
**Spec:** ../records/2026/11/02-plan-plugin-access-front-mockup.md 및 사용자의 ‘이렇게 구현하고 적용’ 승인.

## Global Constraints

- ON은 Free 포함 하위 등급의 모든 선택을 상위 등급에 강제한다. OFF는 독립 허용이다.
- 체크/정렬/배지는 실제 catalog의 등급·플러그인 목록을 사용한다. 별도 하드코딩 목록·W18 목록 동기화는 추가하지 않는다.
- 기존 사용자 데이터와 다른 환경을 보존한다. 전용 API4340/Admin4242만 갱신한다. 커밋/푸시/원격 배포 없음.
- 초기 ON 적용 시 기존 허용을 삭제하지 않고 필요한 하위 플러그인만 상위에 추가한다.
- 모달 취소·에러 시 초안 유지/폐기 원칙과 공통 관리자 스타일을 재사용한다.

## Review Focus

- Free 포함·OFF 독립·상위 직접 해제 거부: 도메인/컴포넌트 테스트.
- 모르는 플러그인, 중복/누락/잘못된 등급: DTO·서비스/저장소 테스트.
- 쓰기 권한 없는 관리자, 요청 중 재저장/닫기, 서버 실패: API/화면 테스트.
- 트랜잭션 중 실패 시 정책과 목록 동시 롤백: 실제 격리 DB 검증.
- 다른 작업자가 추가한 등급/기존 all 모드: 서버 현재 목록 검증, 실제 catalog 기반 UI 검증.

### Task 1: 정책과 원자적 API

Files: catalog domain model/repository/hierarchy, TypeORM repository, admin catalog controller/DTO, admin migration, 해당 spec.
- [x] ON Free/사용자 정의 등급·OFF·불완전 요청 거부 테스트 먼저 추가하고 실패 확인.
- [x] catalog_plugin_settings singleton 및 기존 허용 보존 마이그레이션, 일괄 저장 및 감사 로그 구현.
- [x] 권한·검증·한 트랜잭션 처리와 관련 테스트 통과.

### Task 2: 관리자 편집 UI

Files: catalog API/types/mock, plans component, 재사용 plugin editor 4파일, 목업 연결, 관련 spec.
- [x] 단일 관리 버튼/외부 배지, ON/OFF/잠금, 실패/취소/중복 요청 테스트 먼저 추가하고 실패 확인.
- [x] 승인 모달을 실제 catalog 입력/일괄 저장으로 연결. 등급별 버튼/이전 편집 UI 제거.
- [x] 변경 없음 저장 비활성화, 저장 중 입력/닫기 차단, 에러 시 초안 보존.
- [x] 관련 테스트·빌드·색상 검사 통과.

### Task 3: 통합과 실행 환경 반영

- [x] 실제 격리 DB에서 migration·ON/OFF 저장/조회·롤백 및 공개 catalog/실행 권한 일치 확인.
- [x] API4340/Admin4242 업데이트, 브라우저 실제 화면 검증·캡처.
- [x] 전체 관련 회귀 검사, 문서·WORKBOARD 갱신.

## 실행 중 판단과 완료 기록

전역 revision으로 동시 편집 덮어쓰기를 거절하고 신규 등급 생성/순위 변경에서도 포함 규칙을 유지했다. 실제 문서·진행 기록은 사용자 지정 .codex 위치를 사용했다. 검토·결과는 [적용 기록](../records/2026/11/02-plan-plugin-settings-implementation.md)을 따른다.
