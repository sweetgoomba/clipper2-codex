# 기타 보류 후보·과거 TODO

최종 확인: 2026-09-15 KST. 상태: **과거기록 목록 / 구현 승인 아님**.

[전체 작업 현황](../WORKBOARD.md)

이번 현황판은 handoff/NEXT, todos 폴더 전체, 주요9월감사·TASKS, 이름에 remaining/followup이 있는 문서 후보를 조사했다. 모든 소스와 과거 수백문서를 줄 단위로 완전감사한 것은 아니다. 아래는 다시 찾을 수 있도록 등록한 후보군이다.

| 후보 | 근거 | 재개 시 첫 행동 |
|---|---|---|
| 첫 실행runtime·Plugin Store로딩 | [7/16 TODO](../../todos/2026-07-16-desktop-first-launch-runtime-and-plugin-store-loading.md) | clean/warm/offline 측정 필요성과 현재코드 개선을 대조 |
| stdout로그·제어이벤트 분리 | [7/1 TODO](../../todos/2026-07-01-desktop-stdout-event-contract.md) | 계약 문서화는 완료. 장기 채널분리만 보류이며 당장 진행률장애가 아님 |
| 숏폼 provider승인·키revision·PEM탐지 | [7/28 보안 TODO](../../todos/2026-07-28-shortform-director-security-followups.md) | 최신 코드에서 반영 여부 확인 |
| 별도 쇼츠분석·시청자질문·공식카탈로그 | [8/4 아이디어](../../todos/2026-08-04-shortform-director-research-and-shorts-analysis-followups.md) | 제품필요성 먼저 확인; 현재기능의 필수선행으로 만들지 않음 |
| Auth/Session/License/Credit/Provider 잔여단계 | [7/8 잔여단계](../../design/AUTH_SESSION_LICENSE_PROVIDER_REMAINING_PHASES_2026-07-08.md) | 이후PG/로그인개선과 대조. 옛 /app 경로·요금제별플러그인차등을 되살리지 않음 |
| 6월 runner/S3/output/macOS 계획 | [기존 README 기록](../archive/2026/09/next-before-task-board-2026-09-15.md), README 과거섹션 | 9월운영기록과 대조하여 완료/대체 항목 제거; Mac공개보류 유지 |

## 관리

이 후보를 선택하면 범위를 좁혀 별도 작업카드를 만든다. 근거없는 새branch를 만들거나 무조건 구현하지 않는다. 후속완료를 확인하면 목록에서 삭제하지 말고 완료/대체 근거를 남긴다.

## 갱신 규칙

작업 재개 시 실제 branch/HEAD/미커밋과 아래 근거를 대조한다. 세션 종료 때 상태·중단 지점·다음 행동·검증 한계만 갱신하고, 세부 실행 이력은 날짜별 기록에 링크한다. 다른 작업의 우선순위나 상태를 자동 변경하지 않는다.
