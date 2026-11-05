# YuNet·SFace 안무 전용 GPU 가속 구현·검증 계획

> Execution: superpowers:executing-plans, inline. 사용자가 명시적으로 가속 적용·빌드·3영상 비교를 요청했고, 기존 원본 저장소·안무 격리·SAM-off·품질 보존 기준이 유지된다. 추가 설계 승인 질문 없이 그 범위에서 진행한다. 커밋·푸시 없음.

**Goal:** YuNet과 SFace의 실제 가속 가능성을 검증하고 품질을 유지하는 구현을 안무 앱에 적용, 기존 3개 YouTube 영상 실제 시간 비교.
**Architecture:** 기존 모델 가중치/픽셀/정렬/후처리/임계값은 유지하고 추론 실행기만 안무 전용 adapter로 분리한다. Mac CoreML, Windows CUDA(있으면)/DirectML, 실패 시 기존 OpenCV CPU. 현재 OpenCV wheel에 CUDA/Metal 실행기가 없으므로 ONNX Runtime 경로를 검증한다. 원본 모델 hash와 파생 실행 metadata를 기록한다. 가속 provider가 실제 연산을 맡는지 프로파일로 확인한다.
**Tech:** Python3.11, OpenCV4.13, ONNX Runtime1.31 macOS 및 DirectML1.24.4 Windows. ONNX graph metadata 수정이 필요하면 dance-only 의존성으로 한정한다.
**Spec:** 이번 사용자의 직접 요청; 직전 [실측 결과](02-main-face-performance-results.md).

## 제약·대안
- SAM 두 호출 주석 상태 유지. 인물 플러그인/공유 얼굴 코어 제품 소스 변경 금지. 기존 미커밋 변경은 `/private/tmp/dance-yunet-sface-20261102/before` 보존.
- 기존 OpenCV GPU target 직접 지정: 현재 wheel 지원 안 됨. 모델 교체/축소/샘플 생략은 품질 범위 벗어나 제외. 동일 ONNX 가중치 추론 adapter 우선.
- CoreML 사용 가능 표시만으로 GPU 가속 성공이라고 하지 않는다. 실제 node 배정·수치/판정 일치·warm latency·cold 비용·전체 앱 결과를 분리한다.
- Windows 실제 GPU 장치 없는 경우 분기/fallback/의존성 검증과 Mac 실측을 명확히 구분한다.
- 기준 실제 앱: MMN1793599782691(440.817s), ANT1793599859534(586.194s), NEON1793599963190(646.469s). 같은 URL·대표이미지·원본·모델·설정 유지.

## 작업
- [x] 1. 공식 OpenCV YuNet decode/SFace preprocessing, ORT CoreML/CUDA/DirectML 지원 확인. 같은 가중치 CPU/GPU spike로 출력 오차와 실제 provider 분담·시간 검증.
- [x] 2. 안무 전용 detector/secondary adapter 및 공통 provider 선택/fallback/캐시 수명 구현. 기존 직접 생성 callsites 통일, 상태 조회와 진단에 실제 모델별 실행기 기록. 실패/잘못된 출력/Windows Unicode 경로/경합/동적 크기 테스트 RED→GREEN.
- [x] 3. 실제 프레임·대표이미지의 검출 후보/좌표·embedding·이름 임계값 결정 비교, 관련 안무+인물 회귀 및 독립 코드 검토. 품질 악화 후보는 철회하거나 근본 수정.
- [x] 4. 원본 Electron `npm run build:app:mac:arm64:local-api`, 패키지 hash 확인, 실제 UI에서 동일 3개 YouTube 순차 실행. 시간·전체 clip/diagnostic 비교·14개 사용자 사례·SAM0 확인. 최종 보고서/증거/.codex 인덱스 갱신, 앱 열어둠.

## Review focus
- BGR/RGB, YuNet padding과 NMS 반올림, SFace OpenCV 정렬이 같은가.
- 고정/동적 크기 변경이 원본 픽셀이나 가중치를 변형하지 않는가.
- GPU provider 없거나 일부 node만 가속될 때 거짓 상태 표시/CPU보다 느린 강제 경로가 없는가.
- 세션 및 CoreML compile cache가 크기마다 무한 증가하지 않는가.
- DirectML 순차 실행/memory pattern 제한, CUDA 정밀도, fallback 후 cache/provider 기록이 올바른가.

## 실행 중 체크포인트

2026-11-02: 구현·공식 경로·실제 프레임 비교·독립 검토 및 앱 빌드 완료. 전체 Python검사는2528통과/미수정 렌더링6실패/6생략으로 기록하며 all-green을 주장하지 않는다. Made My Night1793603593237은405.185초(8.1%단축), 89클립 전체행/인물카드/썸네일/2324판정프레임 동일. ANT1793603739918 실행 중, NEON1793603971986 대기. [구현·검증 기록](02-yunet-sface-gpu-results.md).

## 완료 기록

세 실제 앱 실행·품질 비교 완료. 합계1673.480→1597.736초(4.526%), 430클립·9266프레임 동일. 사용자 요청의 가속 적용/빌드/비교는 완료, 전체 시간의 큰 개선 및 Windows 실기기 실측은 미달성·미검증으로 구분한다. 상세 수치와 남은 테스트6실패는 결과 문서에 기록했다.
