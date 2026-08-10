# External Integrations Runbook

## Zeplin via Composio MCP

### 목적

새 Codex 세션이 이전 대화에 의존하지 않고 Composio의 Zeplin 연결을 확인하고, Zeplin
공유 화면의 전체 레이어 트리와 지정 레이어를 조회하기 위한 운영 절차다.

### 알려진 정상 구성

- Codex MCP server: `https://connect.composio.dev/mcp`
- Composio toolkit: `zeplin`
- 정상 연결 상태: `ACTIVE`
- 검증된 Zeplin 사용자: `wlsdk318`

Codex 설정에서는 다음 항목이 있어야 한다.

```toml
[mcp_servers.composio]
url = "https://connect.composio.dev/mcp"
```

### 빠른 시작

1. Composio 도구 검색을 먼저 실행한다.
   - `COMPOSIO_SEARCH_TOOLS`
   - Zeplin 화면, 화면 버전, 레이어 조회 용도를 명시한다.
2. 검색 결과의 `toolkit_connection_statuses`에서 `zeplin`이 `ACTIVE`인지 확인한다.
3. 연결이 없다면 다음 순서로 연결한다.
   - `COMPOSIO_MANAGE_CONNECTIONS`로 `zeplin` 연결 링크 생성
   - 사용자에게 링크를 보여주고 Zeplin 승인 요청
   - `COMPOSIO_WAIT_FOR_CONNECTIONS`로 `ACTIVE`까지 대기
4. `ACTIVE` 확인 전에는 Zeplin API를 호출하지 않는다.
5. 전체 화면·레이어 조회에는 Composio remote workbench의 인증된 `proxy_execute`를
   사용한다.

### 가장 중요한 endpoint 규칙

Composio Zeplin proxy의 base URL에는 API 버전 `/v1`이 이미 포함되어 있다.
`proxy_execute`에 전달하는 endpoint에는 `/v1`을 다시 붙이지 않는다.

올바른 예:

```text
/users/me
/projects
/projects/{project_id}/screens/{screen_id}
/projects/{project_id}/screens/{screen_id}/versions
/projects/{project_id}/screens/{screen_id}/versions/{version_id}
```

잘못된 예:

```text
/v1/users/me
/v1/projects/{project_id}
```

`/v1`을 중복 지정하면 올바른 계정과 ID를 사용해도 `404 Not Found`가 발생한다.

### 공유 URL 해석

`zpl.io` 공유 URL의 HTTP `Location` 헤더에서 canonical URL을 얻는다.

```bash
curl -s -D - -o /dev/null https://zpl.io/ezgwZWY
```

응답의 위치 형식:

```text
https://app.zeplin.io/project/{project_id}/screen/{screen_id}
```

격리된 브라우저 자동화는 사용자의 로컬 Zeplin 로그인 쿠키를 공유하지 않는다. 브라우저
자동화가 로그인 화면으로 이동해도 MCP OAuth 연결 실패로 단정하지 않는다.

### 전체 레이어 조회

화면 버전 목록은 버전 ID와 이미지 메타데이터를 반환하지만 전체 `layers`를 포함하지 않을
수 있다. 프로젝트·화면·버전 ID를 모두 포함한 단일 버전 endpoint를 호출해야 한다.

```python
screen, screen_error = proxy_execute(
    "GET",
    f"/projects/{project_id}/screens/{screen_id}",
    "zeplin",
)

versions, versions_error = proxy_execute(
    "GET",
    f"/projects/{project_id}/screens/{screen_id}/versions",
    "zeplin",
    query_params={"limit": "100", "offset": "0"},
)

version, version_error = proxy_execute(
    "GET",
    f"/projects/{project_id}/screens/{screen_id}/versions/{version_id}",
    "zeplin",
)
```

지정 레이어는 `version["layers"]`를 재귀 순회하며 `name`의 정확한 일치로 찾는다.

```python
matches = []

def walk_layers(nodes, parents=None):
    parents = parents or []
    for node in nodes or []:
        path = parents + [node.get("name") or "<unnamed>"]
        if node.get("name") == "사각형 20626":
            matches.append({"path": path, "layer": node})
        walk_layers(node.get("layers"), path)

walk_layers(version.get("layers"))
```

Composio의 `ZEPLIN_SCREEN_VERSION_GET`은 연결이 정상이어도 `{ "version": {} }`을 반환한
사례가 있다. 전체 레이어가 필요하면 위의 프로젝트 ID 포함 `proxy_execute` 경로를
우선한다.

### 검증 fixture

아래 값은 읽기 전용 연결 재검증에 사용한다.

| 항목 | 값 |
|---|---|
| 사용자 | `wlsdk318` |
| 프로젝트 ID | `5f15726b9180598d58598dab` |
| 프로젝트 이름 | `메타버즈 - 클리퍼` |
| 화면 ID | `6a699b8ee072e9025b0a3bbb` |
| 화면 이름 | `01. 홈` |
| 버전 ID | `6a699b8ee072e9025b0a3bbc` |
| 레이어 이름 | `사각형 20626` |
| 레이어 ID | `6a699b8ee072e9025b0a3c35` |
| 레이어 경로 | `그룹 26777 > 사각형 20626` |

검증 당시 대상 레이어 속성:

- 위치: `x=0`, `y=10`
- 크기: `64 × 990`
- 채우기: `rgb(30, 31, 37)` / `#1E1F25`
- opacity: `1`
- border radius: `0`

### 성공 판정

다음 네 조건을 모두 만족해야 연결과 레이어 조회가 정상이다.

1. `/users/me`가 `wlsdk318`을 반환한다.
2. 단일 화면 조회가 `01. 홈`을 반환한다.
3. 단일 버전 조회가 비어 있지 않은 `layers`를 반환한다.
4. 재귀 검색에서 이름이 정확히 `사각형 20626`인 레이어가 한 개 발견된다.

2026-08-03 검증에서는 네 조건이 모두 통과했고 단일 버전에 최상위 레이어 68개가
반환됐다.

### 문제 해결

- `No Active connection`
  - 새 Zeplin 연결 링크를 발급하고 사용자가 승인한 뒤 `ACTIVE`까지 대기한다.
- `/users/me`까지 404
  - endpoint에 `/v1`을 중복 지정했는지 먼저 확인한다.
- 사용자와 `/projects`는 정상인데 대상 화면만 404
  - 연결된 Zeplin 계정의 프로젝트 접근 권한과 ID를 확인한다.
- 버전 목록은 있으나 `layers`가 없음
  - 목록 응답이 아니라 단일 버전 endpoint를 호출한다.
- `ZEPLIN_SCREEN_VERSION_GET`이 빈 객체를 반환
  - 프로젝트 ID가 포함된 `proxy_execute` 단일 버전 endpoint를 사용한다.
- 브라우저 자동화가 로그인 화면으로 이동
  - 격리 브라우저의 쿠키 문제다. `/users/me`와 `/projects` API 결과로 OAuth 상태를
    판단한다.

### 보안 주의사항

- access token, refresh token, OAuth 인증 링크를 문서나 로그에 저장하지 않는다.
- 서명된 Zeplin CDN URL은 만료되며 서명 정보를 포함하므로 문서화하지 않는다.
- 검증 fixture는 GET 요청에만 사용하고 Zeplin 데이터를 수정하지 않는다.

