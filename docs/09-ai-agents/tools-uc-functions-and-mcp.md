# 도구: UC 함수와 MCP 서버

> 기준일: 2026-10-28 · 근거: 공식 문서

## 왜 필요한가

에이전트가 답만 하면 쓸모가 제한됩니다. 실제 업무는 데이터를 조회하고, 계산하고, 외부 시스템에 요청하고, 때로는 결과를 기록하는 일이기 때문입니다. 도구(Tool)는 이 실행 능력을 에이전트에 붙이는 단위입니다.

도구를 붙이는 방법이 여러 가지라서 설계 실수가 자주 생깁니다. 같은 도구라도 누구의 권한으로 실행되는지가 다르고, 등록 방식마다 필요한 권한이 다릅니다. 이 페이지는 도구 종류, 등록 방식, 인증 주체를 공식 문서 기준으로 정리합니다.

## 어떻게 동작하는가

도구는 크게 네 종류로 나눌 수 있습니다. 문서가 쓰는 명칭을 그대로 옮겼습니다.

| 도구 종류 | 문서 명칭 | 등록 방식 | 상태 |
|---|---|---|---|
| Databricks가 제공하는 관리형 MCP | Databricks-provided MCPs | Unity Gateway 또는 워크스페이스 엔드포인트 | 항목별로 다름 (아래 표) |
| 외부 MCP 서버 | External MCP servers | Unity Gateway의 MCPs UI에서 등록 | 문서에 상태 라벨 없음 |
| 커스텀 MCP 서버 | Custom MCP servers | Databricks Apps 템플릿으로 빌드 | 문서에 상태 라벨 없음 |
| REST API 프록시 | REST API proxy | 에이전트 코드에서 REST 호출 | 문서에 상태 라벨 없음 |

UC 함수는 별도 항목입니다. 문서의 MCP 페이지에는 UC 함수가 도구 종류로 나오지 않지만, 워크스페이스 MCP 엔드포인트 목록에 UC 함수용 엔드포인트가 있습니다. 이 엔드포인트는 Public Preview입니다. 또 `agentbricks tools` CLI는 Unity Catalog 함수 도구에 `auth = "app"`만 지원합니다.

### 관리형 MCP 서비스 목록

Unity Gateway에 등록된 시스템 MCP 서비스는 URL 패턴 `https://<workspace-hostname>/ai-gateway/mcp-services/<mcp-name>`을 씁니다.

| MCP | 상태 | 조건 |
|---|---|---|
| `system.ai.genie_one_mcp` (Genie One) | generally available | Unity Gateway 권한과 정책, 기반 리소스 권한 필요 |
| `system.ai.dbsql` (Databricks SQL) | Unity Gateway Beta | 계정 관리자가 계정 콘솔 Previews에서 Unity Gateway 베타를 켬. 호출자의 UC 권한과 웨어하우스 권한 사용 |
| `system.ai.web_search` | Unity Gateway Beta | 같은 베타 필요. HIPAA/BAA 규정 준수 설정이 켜져 있으면 사용 불가 |
| `system.ai.sandbox` | Unity Gateway Beta | 같은 베타 필요. 네트워크 송신 없음 |

외부 서비스 MCP(`system.ai.slack`, `system.ai.github`, `system.ai.atlassian`, `system.ai.google_drive`, `system.ai.google_calendar`, `system.ai.gmail`, `system.ai.microsoft_365`)는 페이지에 상태 라벨이 없습니다. GitHub는 기본으로 공개 저장소만 읽고, 비공개 저장소나 쓰기 작업에는 GitHub 커넥터 앱 설치가 필요하다고 문서가 설명합니다.

워크스페이스 MCP 엔드포인트는 Public Preview이며, 워크스페이스 관리자가 Previews 페이지에서 **Managed MCP Servers** 를 켜야 합니다.

| 서버 | URL 패턴 | OAuth 범위 |
|---|---|---|
| Genie Agent | `https://<workspace-hostname>/api/2.0/mcp/genie/{genie_space_id}` | `genie` |
| AI Search | `https://<workspace-hostname>/api/2.0/mcp/ai-search/{catalog}/{schema}/{index_name}` | `ai-search` |
| Databricks SQL (legacy) | `https://<workspace-hostname>/api/2.0/mcp/sql` | `sql` |
| Unity Catalog 함수 | `https://<workspace-hostname>/api/2.0/mcp/functions/{catalog}/{schema}/{function_name}` | `unity-catalog` |

> **참고** 위 표의 Unity Gateway 경로(`/ai-gateway/mcp-services/`)와 워크스페이스 엔드포인트(`/api/2.0/mcp/`)는 거버넌스 적용 범위가 다릅니다. 문서는 워크스페이스 엔드포인트가 Unity Gateway의 거버넌스 대상이 아니라고 명시합니다. 운영에서는 두 경로 중 무엇을 쓰는지 설계 단계에서 정하십시오.

## 어떻게 쓰는가

### 외부 MCP 서버 등록

문서의 등록 절차를 요약합니다. 실제 UI 라벨은 워크스페이스 버전에 따라 다를 수 있습니다.

1. Unity Gateway를 열고 **MCPs** 에서 **+ MCP** 를 클릭합니다.
2. **Connect an existing MCP server** 를 선택합니다.
3. 카탈로그와 스키마를 고르고 MCP 이름을 입력합니다. 이름은 나중에 바꿀 수 없습니다.
4. 기존 HTTP 연결을 고르거나 **Create new connection** 으로 서버 URL과 자격 증명을 입력합니다.
5. **Create & load tools** 로 연결을 저장하고 도구 목록을 가져옵니다.
6. 필요하면 **Login** 으로 제공자 계정에 로그인하고, 노출할 도구를 고릅니다.
7. **Create MCP Service** 를 클릭합니다.

등록하려면 다음 권한이 필요합니다. 문서는 등록에 **Workspace access** 엔타이틀먼트가 필요하며 **Consumer access** 사용자는 등록할 수 없다고 명시합니다.

| 권한 | 용도 |
|---|---|
| `USE CATALOG`, `USE SCHEMA` | 상위 카탈로그와 스키마 접근 |
| `CREATE SERVICE` (스키마) | MCP 서비스 생성 |
| `CREATE CONNECTION` 또는 `USE CONNECTION` | 연결 생성 또는 기존 연결 사용 |

등록한 MCP는 에이전트 설정에서 `<catalog>.<schema>.<service>` 전체 이름으로 참조합니다.

```
https://<workspace-hostname>/ai-gateway/mcp-services/<catalog>.<schema>.<service>
```

### 커스텀 MCP 서버: 스타터 템플릿

Databricks Apps로 MCP 서버를 올리면 에이전트가 붙을 HTTPS URL이 생깁니다. 가장 빠른 방법은 **MCP Server (Starter)** 템플릿입니다.

1. Unity Gateway에서 **MCPs**, **+ MCP**, **Build a new MCP server** 를 선택합니다.
2. **Install from a template** 의 **Agents** 탭에서 **MCP Server (Starter)** 를 고릅니다.
3. 앱 이름에 `mcp-` 접두사를 붙입니다. 예: `mcp-my-server`. 접두사가 있어야 AI Playground가 이 서버를 인식합니다.
4. 배포가 끝나면 앱 URL 뒤에 `/mcp`를 붙입니다.

템플릿에는 `health` 도구가 들어 있습니다. 도구를 추가하려면 `server/tools.py`의 `load_tools(mcp_server)` 안에 다음을 넣습니다.

```python
@mcp_server.tool
def uppercase(text: str) -> str:
    """Convert a string to uppercase."""
    return text.upper()
```

변경 사항을 동기화하고 앱을 다시 배포한 뒤, 에이전트 연결을 새로 해야 새 도구가 보입니다.

### 커스텀 MCP 서버: 기존 서버 배포

이미 만든 MCP 서버를 올릴 때는 소스 폴더에 다음이 있어야 합니다.

- Streamable HTTP를 쓰는 HTTP 서버. `0.0.0.0`에서 listen하고, `DATABRICKS_APP_PORT` 환경 변수의 포트를 씁니다(기본값 `8000`).
- 의존성 파일(Python은 `requirements.txt`, Node.js는 `package.json`).
- 시작 명령을 적은 `app.yaml`.

```yaml
command: ['python', 'server.py']
```

### 커스텀 MCP 서버: OpenAPI 템플릿

기존 REST API를 MCP 도구로 바꾸려면 **MCP Server (OpenAPI)** 템플릿을 씁니다.

- OpenAPI 3.x 명세를 `spec.json`으로 저장해 볼륨 루트에 올립니다. 하위 폴더에 두면 안 됩니다.
- API 자격 증명을 담은 HTTP 연결을 만듭니다. 생성에는 `CREATE CONNECTION` 권한이 필요합니다.
- 앱의 `app.yaml`에서 `UC_CONNECTION_NAME`을 연결 이름으로 지정합니다.

```yaml
- name: UC_CONNECTION_NAME
  value: my_api_connection
```

호출자에게는 앱에 **CAN USE** 를, HTTP 연결에는 **USE CONNECTION** 을 줍니다. 템플릿의 도구는 `list_api_endpoints`와 엔드포인트 호출 도구입니다.

### 에이전트에서 MCP 도구 호출

Python 에이전트가 MCP 도구를 쓰는 기본 구성은 다음과 같습니다. 문서가 예시로 드는 패키지는 `databricks-mcp`(`DatabricksMCPClient`)와 `databricks-sdk`(`WorkspaceClient`)입니다. MCP 클라이언트는 `list_tools()`로 도구 이름, 설명, 입력 스키마를 얻고, `call_tool(tool_name, arguments)`로 호출합니다. 결과는 `structuredContent` 또는 `content` 블록에 오므로, 사용 전에 `isError`를 확인하라고 문서가 안내합니다.

Claude Code, Codex, Cursor 같은 코딩 에이전트에 연결하는 방법은 `ug mcp add --names "app:mcp-my-server"` 명령으로 안내됩니다. 코딩 에이전트 구성은 [11장 Genie Code](../11-developer-tools/genie-code/README.md)와 함께 보십시오.

## 인증 주체

이 표가 이 페이지에서 가장 중요합니다. 같은 도구라도 어느 신원으로 호출되는지에 따라 접근 범위가 달라집니다.

| 호출 경로 | 인증 방식 (문서 명칭) | 실행 주체 |
|---|---|---|
| 사용자가 직접 MCP를 호출 | OAuth user-to-machine (U2M) | 로그인한 사용자 |
| 무인 에이전트나 서비스가 호출 | OAuth machine-to-machine (M2M) | 서비스 프린시펄 |
| 외부 IdP 토큰을 가진 워크로드 | OAuth 토큰 연합 (token federation) | 매핑된 사용자 또는 서비스 프린시펄 |
| 개인 액세스 토큰(PAT) | 토큰 소유자 | Databricks Apps 위의 MCP 서버에는 지원 안 됨 |
| 에이전트 도구 (`agentbricks`) | `auth = "user"` | 요청한 사용자 |
| 에이전트 도구 (`agentbricks`) | `auth = "app"` | 앱 서비스 프린시펄 |

외부 서비스로 나가는 연결은 UC 연결의 인증 방식으로 정합니다.

| 연결 방식 | 의미 |
|---|---|
| Bearer 토큰 | 모든 호출자가 하나의 토큰을 공유 |
| OAuth Machine-to-Machine | 연결에 설정된 공유 서비스 신원 |
| OAuth User-to-Machine Shared | 한 제공자 계정을 여러 호출자가 공유 |
| Dynamic Client Registration (DCR) | 호출자 본인이 인증한 제공자 계정 사용 |
| OAuth User-to-Machine Per User | 사용자별 제공자 계정과 OAuth 클라이언트 설정 |

> **참고** 앱에서 사용자 권한으로 호출하려면 앱의 사용자 권한(User authorization) 설정과 연결의 사용자별 OAuth를 함께 구성해야 합니다. 자세한 내용은 [배포와 인증](deploy-and-authentication.md)에서 다룹니다.

## 트레이드오프

| 선택 | 장점 | 제약 |
|---|---|---|
| UC 함수 도구 | UC 권한과 감사가 그대로 적용 | `agentbricks`에서는 `auth = "app"`만 지원 |
| 관리형 MCP (Genie One, DBSQL 등) | 서버를 직접 운영하지 않음 | 항목별 상태가 다르고 일부는 Beta |
| 외부 MCP 등록 | 기존 외부 서비스를 공유 | 등록 권한(Workspace access)이 필요하고 Consumer access 사용자는 등록 불가 |
| 커스텀 MCP (Apps) | 사내 로직과 REST API를 도구로 노출 | 서버 코드와 배포 관리가 필요 |
| REST API 프록시 | 에이전트 코드에서 직접 호출 | 호출 로직과 인증 처리를 코드가 맡음 |

## 주의사항

- **PAT 사용 금지**: Databricks Apps 위의 MCP 서버는 개인 액세스 토큰을 지원하지 않습니다. OAuth 토큰을 써야 합니다.
- **앱 이름 접두사**: 커스텀 MCP 앱 이름은 `mcp-` 접두사를 쓰십시오. AI Playground가 이 접두사로 서버를 찾습니다.
- **등록 후 이름 고정**: 외부 MCP 이름은 생성 후 바꿀 수 없습니다. 이름 규칙을 먼저 정하십시오.
- **등록 제외 대상**: Genie, Databricks Apps, UC 엔티티 소스는 자체 MCP로 등록할 수 없다고 문서가 명시합니다.
- **Global Search에 안 보임**: Unity Catalog 전역 검색에는 MCP가 나오지 않으므로 MCPs 페이지에서 찾습니다.
- **OpenAPI 명세 위치**: `spec.json`은 볼륨 루트에 있어야 하고, OpenAPI 3.x 형식이어야 합니다.
- **서버 요구사항**: Streamable HTTP, `0.0.0.0` listen, `DATABRICKS_APP_PORT` 사용을 지키지 않으면 배포가 동작하지 않습니다.
- **Beta 항목 주의**: `system.ai.dbsql`, `system.ai.web_search`, `system.ai.sandbox`는 계정 베타가 필요합니다. 고객 환경에서 쓰기 전에 베타 활성 여부를 확인하십시오.

## 참고 문서

- [MCPs](https://docs.databricks.com/aws/en/agents/mcp-tools/)
- [Databricks-provided MCPs](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [Custom MCP servers](https://docs.databricks.com/aws/en/agents/mcp-tools/custom-mcp)
- [MCP authentication](https://docs.databricks.com/aws/en/agents/mcp-tools/authentication-networking)
- [Register an external MCP server](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service)
- [Use MCP tools in a Python agent](https://docs.databricks.com/aws/en/agents/custom-agents/use-mcp-tools)
- [Agent Bricks CLI](https://docs.databricks.com/aws/en/agents/custom-agents/agent-bricks-cli)
