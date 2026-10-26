# 2026-10-23 Clipper 인프라 런북 문서 브랜치 기록

## 처리 결과

- 저장소: `web/clipper_infra`
- 브랜치: `docs/w06-dev-mid-cutover-execution-20261016`
- 커밋: `0b549215ee7786c542d3a209741c46235a785fab` (`docs(runbooks): record dance catalog deployment and draft migration steps`)
- 변경 문서: `runbooks/deploy-dev.md`, `runbooks/dance-catalog-manual-artist-dev-deployment-20261016.md`
- 두 문서만 현재 문서 브랜치에 커밋·푸시했다. 원격 브랜치가 해당 커밋을 가리키고 작업 트리가 깨끗한 것을 확인했다.
- 사용자의 지시에 따라 `dev`에는 병합하지 않았다. 확인 당시 원격 `dev`는 `e5040931fb3ecb2b7d715f3938eaa39ca9ad8b96`로 변경되지 않았다.

## 문서 내용과 후속 검토

- 개발 배포 런북의 마이그레이션 명령을 현재 API 런타임 이미지와 `deploy-dev.sh`의 `--build-only` / `--start-only` 흐름에 맞게 갱신했다. 기존 Toss 개발 MID 전환의 상세 명령은 해당 전환 런북과 실행 기록으로 연결했다.
- 2026-10-16 안무 카탈로그 직접 아티스트 개발 배포 기록을 새 문서로 보존했다.
- 이 브랜치의 마이그레이션 절차를 실제 배포에 사용하거나 `dev`에 병합하기 전, 마이그레이션 중 기존 API를 계속 실행해도 호환되는지와 선택한 데이터소스의 **모든 미적용 마이그레이션**이 실행되는 범위를 검토해야 한다. 해당 검토는 이번 커밋·푸시의 완료 조건에 포함하지 않았다.
