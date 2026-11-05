# 중복된 신원·메인 교대 경계 조립 수정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 같은 관측 교대를 서로 다른 시각으로 두 번 자르면서 생성하는 근거 없는 짧은 미확인 조각을 제거한다.
**Architecture:** 단체/메인 eligibility와 원래 identity 관측은 동결한다. 최종 조립에서만 동일 관측 bracket의 provisional identity midpoint와 이미 확정된 main handoff를 대조한다. 고유 source cut 또는 반대 얼굴이 없고 outgoing 이름·선택 몸이 원래 관측으로 지지되는 경우에만 기존 first-observed-new-main 경계에 맞춘다. 다른 종류의 짧은 구간은 길이를 이유로 합치지 않는다.
**Tech Stack:** Dance 전용 Python, dataclass, 기존 frame/face/joint 진단, pytest. 새 모델/영상 추론/전역 설정 없음.
**Spec:** 사용자의 2026-11-03 범위: group 탈락→main 판정 보류, identity/main 구간 교차로 인한 초단편 우선. 기존 실제 앱 3개 결과를 동결 입력으로 재생한다.

## Global Constraints
- 역할 영역/그룹 목록/accepted 이름 교대/정밀 source cut 변경 금지.
- Person/Dialog/shared SDK, heavy SAM OFF 보존.
- 출력에서 수정한 경계가 인식 anchor가 되지 않는다.
- 기본 얼굴 evidence·preview·body 좌표는 그대로 보존한다.
- 별도 모델 호출·source 영상 읽기 추가하지 않는다.
- 이번 변화가 모든 과분할을 해결한다고 주장하지 않는다. 원래 identity≥1초→짧아진16개는 다른 원인이 포함된다.

## Review Focus
- 다른 main handoff 또는 실제 컷을 이름 경계와 근접하다는 이유만으로 묶지 않는다.
- outgoing 마지막 얼굴이 conflict/insufficient면 이름을 연장하지 않는다.
- 새로 이름 붙일 시간 안에 다른 관측이 있으면 그대로 남긴다.
- 단체로 제외된 시간에 걸쳐 이름을 연장하지 않는다.
- 실제 짧은 B 또는 정밀 frame boundary를 지우지 않는다.

### Task 1: 동일 교대 경계의 최종 조립
**Files:** services/performance_parts.py, services/identity_projection.py 또는 작은 boundary helper; tests/test_dance_performance_parts.py 및 최소 실제 fixture.
**Interface:** immutable identity + projected parts + recorded boundaries/handoffs/cuts/face ownership → projected parts + accepted/rejected audit. 기존 index를 보존한다.
- [x] 실제 MMN88.254833–88.2882의 두 경계가 하나로 되는 실패 테스트. NEON34 conflict·정밀컷·real short B·다른bracket·missing proof·main mask gap 회귀 반례.
- [x] 최소 조립 변경. 기존 반복/매칭/영상 처리를 늘리지 않는다.
- [x] 실제 세 저장 결과에 동일 함수를 적용해 변경 전부 열거. 인식/역할·group·원본span 불변,14사용자구간불변,변경시간/미확인/clip개수 분리.
- [x] 독립 검토와 관련 Dance 테스트. 통과 결과와 개선 폭·한계를 .codex에 기록. 이번 턴 커밋/푸시는 요청되지 않았다.

Ruling: helper는 모든기존복원후1회 실행한다. 독립검토에서 파생출력의재사용을차단하도록권고했고 새경계가인식근거가되는위험을줄인다. 원래 primary 반대양성도검증하며 모델추론은없다.
Ruling: 직접반대얼굴이있는projection의부모이름계승도거부한다. 거부된출력vote의후속재사용을테스트로차단한다. 새이름으로추측하지않는다.
