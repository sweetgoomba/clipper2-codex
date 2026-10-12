# W07 — 삭제 프로필 기록과 패키지 내부 서버 부팅 검증 (2026-09-30)

## 원인과 범위

원본 `dev` NestJS의 프로필 색인 초기화는 `profiles/*.json`을 전부 일반 `shortform-director-operating-profile.v1`로 파싱한다. 이미 삭제한 프로필을 보존하는 정상 기록 `shortform-director-deleted-profile.v1`을 만나면 `ShortformDirectorStorageCorruptionError: Managed JSON failed parse or schema validation`로 초기화가 중단된다. 이 기록은 파일 손상이라는 근거가 아니므로 삭제·수정하지 않았다.

W07 미커밋 NestJS는 `shortform-director-profile-record.ts`에서 삭제 기록을 별도로 검증하고, `shortform-director-profile-catalog.persistence.ts`에서 활성 색인·목록으로 재투영할 때 제외한다. 삭제 기록 안의 과거 프로필과 별도 배치 스냅샷은 보존한다. 원본 `dev` 소스와 실행 앱은 수정하지 않았다.

## 임시 사본 검증

실제 `Clipper Studio Dev` 사용자 데이터에서 `shortform-director`, `projects` 등 필요한 디렉터리만 권한 0700의 `/private/tmp` 임시 디렉터리로 복제했다. 원본 프로필 상세 파일은 활성 6개, 삭제 기록 2개였다. 같은 사본에서 원본 `dev`의 `JsonShortformDirectorProfileRepository.reconcileIndex()`는 보고된 예외로 실패했고, W07의 동일 초기화는 성공했다.

W07 `npm run build` 종료 0, 프로필 저장소·삭제 관련 `node --test` **36/36 통과**. 임시 사본에서 W07 repository의 `onModuleInit()` 뒤 활성 목록 6개, 삭제 기록 2개의 `get()`은 모두 null, 색인에도 삭제 ID가 없었다. 실제 저장된 배치 7개(그중 삭제 프로필의 배치 1개)와 완료 스토리보드 문서 35개를 `StoryboardBatchReadService`로 열었다. `projects` 파일 298개의 원본·사본 SHA-256은 전부 같고, `shortform-director`의 색인 외 파일은 원본·사본 checksum 차이 0개였다. 임시 사본에서만 색인을 복구했다.

최신 W07 macOS arm64 local-api `.app`의 `Contents/Resources/clipper_nestjs/index.js`를 패키지의 `.env.packaged`와 JWT **공개키** 경로, 임시 데이터 루트로 직접 실행했다. 실제 포트 바인딩이 허용된 환경에서 `/v1/health`는 HTTP 성공과 `status: ok`를 반환했다. 첫 단독 실행은 Electron이 보통 주입하는 공개키 경로가 빠져 `JWT public key is not configured`로 종료됐고, 해당 경로를 주입해 성공했다. 앞선 제한 실행의 포트 바인딩 `EPERM`도 별개의 실행환경 제한이었다. 어느 것도 삭제 기록 손상을 뜻하지 않는다.

**검증 한계:** 이는 앱 패키지에 포함된 **실제 NestJS 번들의 부팅/HTTP 검증**이며 Electron GUI가 `utilityProcess`로 그 번들을 띄우는 전체 흐름을 실행한 것은 아니다. macOS Electron은 임시 `HOME`을 지정해도 `app.getPath('appData')`를 실제 사용자 경로로 반환했다. 원본 사용자 데이터에 앱이 쓰는 위험을 피하려고 전체 GUI 앱 실행을 하지 않았다. 특히 원본 `dev` 앱의 정상 기동을 주장하지 않는다. W07 변경은 여전히 미커밋·미병합이고, 현재 원본 `dev`는 삭제 기록이 있는 데이터에서 동일한 초기화 오류를 낸다.

실제 AI/DB/과금·원장 실행 서버 변경·원본 사용자 데이터 수정/삭제는 없었다. 검증용 사용자 데이터 사본은 결과 기록 후 삭제한다.
