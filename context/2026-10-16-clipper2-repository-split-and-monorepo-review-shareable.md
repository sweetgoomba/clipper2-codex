# Clipper2 초기 저장소 분리와 모노레포 검토

작성일: 2026-10-16

Clipper2의 데스크톱 코드는 2026년 4월에 역할별 네 저장소로 나뉘었다. 당시의 주된 문제는 ClipperStudio와 HighlightStudio가 같은 코드베이스와 실행 환경을 공유하면서 빌드, 의존성, 버전, 배포가 서로 영향을 주는 것이었다. 분리 직후에는 TypeScript 코드의 계약을 공유하기 위해 일부 저장소를 모노레포로 다시 묶는 방안도 검토했다. 저장소 병합보다 API와 공유 계약을 먼저 정리하는 것이 단기 우선순위였다.

## 분리 이전에 겪은 문제

기존 `adlight_angular`와 `adlight_python`에는 ClipperStudio와 HighlightStudio의 기능이 함께 쌓였다. 같은 코드베이스에서 두 제품의 빌드 설정, 버전, 릴리스 스크립트, 서버 로직과 모델 런타임이 서로 영향을 줬다. 이미 사용자가 있던 ClipperStudio의 배포를 HighlightStudio 작업으로부터 보호하기 위해 릴리스 스크립트와 버전 처리도 복잡해졌다.

Python 쪽에서는 무거운 파이프라인들이 하나의 frozen 실행 파일과 의존성 집합에 묶인 것이 특히 문제였다. 4월 중순 재설계는 플러그인을 배포·의존성·런타임·업데이트의 단위로 삼고, 각 플러그인을 별도 프로세스로 실행하는 방향을 택했다. 이는 Git 저장소의 개수와 별개인 실행 및 의존성 경계에 대한 판단이다.

## 네 저장소로 나뉜 구조

4월 16~17일에는 `clipper_python`이 플러그인 SDK와 Python 플러그인을 담는 새 저장소로 만들어졌다. 4월 20~21일에는 세 저장소가 더 생겼다.

| 저장소 | 당시 맡긴 역할 |
|---|---|
| `clipper_angular` | Electron과 NestJS에 직접 빌드 의존하지 않는 Angular UI |
| `clipper_electron` | 데스크톱 셸, 로컬 프로세스 실행, OS 기능과 패키징 |
| `clipper_nestjs` | 로컬 앱 API, 사전 처리와 외부 API 연결 |
| `clipper_python` | 플러그인 SDK와 영상·모델 계산 작업 |

이 구조는 기존 코드에 뒤섞였던 UI, 데스크톱 호스트, 앱 API, Python 계산의 책임을 드러냈다. 당시 기록은 네 저장소의 생성 과정과 역할을 설명한다. 다만 네 개의 Git 저장소를 선택한 대안 비교나 최종 의사결정문은 담고 있지 않다.

## 분리 직후 검토한 모노레포 구상

4월 29일 NestJS 재설계안은 Angular, NestJS, Electron을 한 `clipper_app` 저장소의 `apps/`에 두고, `packages/contracts`, `packages/ui`, `packages/config`를 공유하는 장기 구조를 제안했다. Angular와 NestJS가 같은 TypeScript 생태계에 있어 DTO와 인터페이스를 공유하기 쉽다는 점이 핵심 이점이었다.

그 설계안은 Python을 별도 `clipper_python` 저장소로 두는 구성을 예시로 들었다. Python까지 합치는 것도 가능하지만 TypeScript DTO 공유의 이점은 Python에 직접 적용되지 않으므로, Python과의 계약은 OpenAPI·코드 생성이나 Pydantic 스키마 정렬로 다루는 편이 현실적이라고 봤다.

단기 우선순위는 저장소 병합이 아니었다. 먼저 `contracts` 패키지의 위치를 정하고 NestJS API를 중심으로 DTO를 정리하자고 했다. 당시 Angular가 NestJS와 Python 플러그인 API를 모두 직접 호출하는 구조에서는 TypeScript 계약 공유의 이점이 약해진다는 문제의식도 함께 적혀 있었다.

## 당시 판단의 범위

2026년 4월에는 역할별 데스크톱 저장소 네 개가 실제로 만들어졌다. 동시에 4월 29일 설계안은 그중 TypeScript 코드의 모노레포 통합을 장기 선택지로 제시했다. 따라서 당시 기록으로 확인되는 것은 **분리된 구조로 시작하고, 저장소 통합보다 API·공유 계약 정리를 우선했다**는 점이다. 모노레포를 최종적으로 배제한 이유까지 이 기록만으로 확정할 수는 없다.
