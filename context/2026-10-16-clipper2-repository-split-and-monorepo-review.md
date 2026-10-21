# Clipper2 초기 저장소 분리와 모노레포 검토

작성일: 2026-10-16

Clipper2의 데스크톱 코드가 네 저장소로 나뉜 배경과, 그 직후 제안된 모노레포 구상을 정리한다. 범위는 2026년 4월 27일의 프로젝트 변천사와 4월 29일의 NestJS 재설계안이다. 두 기록을 함께 보면 **역할별 분리는 실행됐고, TypeScript 저장소를 다시 묶는 구상은 장기 제안으로 남아 있었다**.

## 분리 이전에 겪은 문제

기존 `adlight_angular`와 `adlight_python`에는 ClipperStudio와 HighlightStudio의 기능이 함께 쌓였다. 같은 코드베이스에서 두 제품의 빌드 설정, 버전, 릴리스 스크립트, 서버 로직과 모델 런타임이 서로 영향을 줬다. 이미 사용자가 있던 ClipperStudio의 배포를 HighlightStudio 작업으로부터 보호하기 위해 릴리스 스크립트와 버전 처리도 복잡해졌다.

Python 쪽에서는 무거운 파이프라인들이 하나의 frozen 실행 파일과 의존성 집합에 묶인 것이 특히 문제였다. 4월 중순 재설계는 플러그인을 배포·의존성·런타임·업데이트의 단위로 삼고, 각 플러그인을 별도 프로세스로 실행하는 방향을 택했다. 이는 Git 저장소 분리와는 구별되는 **실행 및 의존성 경계**에 대한 판단이다.

## 네 저장소로 나뉜 구조

4월 16~17일에는 `clipper_python`이 플러그인 SDK와 Python 플러그인을 담는 새 저장소로 만들어졌다. 4월 20~21일에는 세 저장소가 더 생겼다.

| 저장소 | 당시 맡긴 역할 |
|---|---|
| `clipper_angular` | Electron과 NestJS에 직접 빌드 의존하지 않는 Angular UI |
| `clipper_electron` | 데스크톱 셸, 로컬 프로세스 실행, OS 기능과 패키징 |
| `clipper_nestjs` | 로컬 앱 API, 사전 처리와 외부 API 연결 |
| `clipper_python` | 플러그인 SDK와 영상·모델 계산 작업 |

이 구조는 기존 저장소에 뒤섞였던 UI, 데스크톱 호스트, 앱 API, Python 계산의 책임을 드러냈다. 변천사 문서는 네 저장소가 만들어진 과정과 역할을 설명하지만, 네 개의 **Git 저장소**를 선택한 대안 비교나 최종 의사결정문까지 제시하지는 않는다.

## 분리 직후 검토한 모노레포 구상

4월 29일 NestJS 재설계안은 Angular, NestJS, Electron을 한 `clipper_app` 저장소의 `apps/`에 두고, `packages/contracts`, `packages/ui`, `packages/config`를 공유하는 장기 구조를 제안했다. Angular와 NestJS가 같은 TypeScript 생태계에 있어 DTO와 인터페이스를 공유하기 쉽다는 점이 핵심 이점이었다.

그 설계안은 Python을 별도 `clipper_python` 저장소로 두는 구성을 예시로 들었다. Python까지 합치는 것도 가능하지만 TypeScript DTO 공유의 이점은 Python에 직접 적용되지 않으므로, Python과의 계약은 OpenAPI·코드 생성이나 Pydantic 스키마 정렬로 다루는 편이 현실적이라고 봤다.

설계안의 단기 우선순위는 저장소 병합이 아니었다. 먼저 `contracts` 패키지의 위치를 정하고 NestJS API를 중심으로 DTO를 정리하자고 했다. 당시 Angular가 NestJS와 Python 플러그인 API를 모두 직접 호출하는 구조에서는 TypeScript 계약 공유의 이점이 약해진다는 문제의식도 함께 적혀 있다.

## 두 기록으로 확인되는 판단

2026년 4월에는 역할별 데스크톱 저장소 네 개가 실제로 만들어졌다. 동시에 4월 29일 설계안은 그중 TypeScript 코드의 모노레포 통합을 장기 선택지로 제시했다. 따라서 이 두 기록만으로는 **모노레포를 최종적으로 배제한 이유**를 확정할 수 없다. 확인되는 당시의 실행 순서는 책임 분리와 플러그인 런타임 재설계를 먼저 진행하고, 저장소 통합보다 API·공유 계약 정리를 우선한다는 것이다.

## 근거 문서

- [Adlight에서 Clipper2로의 프로젝트 변천사](./PROJECT_HISTORY_AND_STATUS.md): §2.1, §2.4~2.5, §3의 3월 18~19일·4월 13~21일 기록.
- [NestJS Control Plane 중심 Clipper2 재설계](../design/NESTJS_CONTROL_PLANE_REDESIGN.md): §3.4, §10. 모노레포 구조와 단기 우선순위는 설계안의 제안이다.
