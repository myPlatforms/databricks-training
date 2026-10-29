# MCP 서버 연결

> 기준일: 2026-10-28 · 근거: 공식 문서

## 왜 필요한가

Genie Code가 워크스페이스 안의 테이블과 노트북만 보면, 팀이 실제로 쓰는 외부 시스템은 빠집니다. 티켓 시스템의 요구사항, 메일의 승인 내역, 팀 문서가 여기에 해당합니다. 예전에는 이런 정보를 채팅에 복사해 붙여 넣어야 했습니다.

MCP(Model Context Protocol)는 AI 에이전트가 외부 도구와 데이터 원천을 같은 방식으로 호출하게 하는 프로토콜입니다. Genie Code는 MCP 서버를 연결해 외부 도구를 에이전트의 도구 목록에 추가합니다.

## 어떻게 동작하는가

### 연결 경로

1. Genie Code 패널을 열고 톱니바퀴 아이콘(**Settings**)을 누릅니다.
2. **MCP Servers** 항목에서 **Add Server** 를 누릅니다.
3. 서버를 고르고 **Save** 를 누릅니다.

저장하면 바로 쓸 수 있습니다. 설정에서 서버 전체 또는 개별 도구를 켜고 끌 수 있습니다.

### 연결 가능한 원천

| 옵션 | 설명 |
|------|------|
| UC MCP Service | **Select a UC MCP Service** 에서 고릅니다. Unity Catalog에 등록된 외부 서버입니다. |
| Unity Catalog function | 스키마를 고릅니다. UC 함수를 도구로 씁니다. |
| AI Search | 인덱스가 있는 스키마를 고릅니다. |
| Genie Agent | 에이전트를 고릅니다. |
| Custom MCP server | Databricks App을 고릅니다. |

문서가 분류하는 방식은 다음과 같습니다.

| 분류 | 내용 |
|------|------|
| 기본 제공 커넥터 (native connectors) | Databricks가 제공합니다. 서버를 호스팅하거나 OAuth 앱을 등록할 필요가 없습니다. 목록: Google Drive, Gmail, Google Calendar, Microsoft 365, Atlassian, Glean (Beta), Slack, GitHub |
| 외부 서버 (external servers) | Unity Catalog에 UC MCP Service로 등록합니다. 사용자별 OAuth를 쓰면 먼저 해당 서비스에 로그인해야 합니다. |
| 사용자 정의 서버 (custom servers) | Databricks App으로 배포합니다. 같은 워크스페이스에 있어야 합니다. |

사용자 정의 서버의 엔드포인트는 문서에 `https://<server-url>/mcp` 형태로 나옵니다. 서버는 상태를 가지지 않아야(stateless) 한다고 문서가 명시합니다. CORS 오류가 나면 앱의 허용 origin에 워크스페이스 URL을 추가합니다.

### 인증과 거버넌스

| 항목 | 문서 내용 |
|------|-----------|
| 기본 제공 커넥터 | 사용자마다 개별 인증합니다. OAuth 토큰은 사용자 사이에서 공유되지 않습니다. |
| 도구 호출 통제 | Unity Catalog와 Unity Gateway가 연결을 통제합니다. 게이트웨이는 호출마다 Unity Catalog 권한을 확인하고, 정책과 승인 요구를 적용하며, 사용량을 시스템 테이블에 기록합니다. |
| Jailbreak 검사 (Beta) | Unity Gateway에서 MCP 도구 호출과 그 결과를 jailbreak·prompt injection 시도로부터 검사할 수 있습니다. Jailbreak guardrail을 입력(input), 출력(output), 또는 둘 다에 적용합니다. |
| 연결 권한 관리 | 메타스토어 관리자와 연결 소유자가 사용자 권한을 관리하거나 철회할 수 있습니다. |
| 서버 선택 | 워크스페이스 관리자가 사용할 수 있는 서버를 통제하고, 사용자는 승인된 원천에서 고릅니다. |
| 연결 권한 변경 | 사용자가 다시 인증해야 합니다. 그 전까지 예약 작업은 실패합니다. |
| 인증 만료 | Genie Code가 만료를 미리 알려 주지 않습니다. 도구 호출이 실패하거나 연결 목록을 열 때 알게 됩니다. |

GitHub 커넥터는 쓰기가 파일 내용, 이슈, 풀 리퀘스트로 제한되며, 기본 설정에서는 공개 저장소만 읽습니다.

### 지역 제약

문서는 외부 MCP 서버를 **Model Serving이 지원되는 지역에서만** 쓸 수 있다고 명시합니다.

## 어떻게 쓰는가

### 예 1: Genie Agent를 도구로 연결

팀이 이미 만들어 둔 Genie Agent를 Genie Code 도구로 붙입니다.

1. **Settings** → **MCP Servers** → **Add Server**
2. **Genie Agent** 선택 후 대상 에이전트를 고릅니다.
3. **Save**. 이후 채팅에서 해당 에이전트가 답할 수 있는 질문을 요청합니다.

### 예 2: 사용자 정의 Databricks App을 MCP 서버로 연결

```text
1. Databricks App을 같은 워크스페이스에 배포합니다.
2. 앱이 https://<app-url>/mcp 엔드포인트로 MCP 요청을 받는지 확인합니다.
3. 앱의 허용 origin에 워크스페이스 URL을 추가합니다 (CORS 오류가 나는 경우).
4. Genie Code Settings → MCP Servers → Add Server → Custom MCP server에서 앱을 고릅니다.
```

문서가 제시하는 실제 설정 키나 배포 명령은 이 페이지에 없습니다. 배포 방법은 Databricks Apps 문서를 따릅니다.

## 트레이드오프

| 항목 | 장점 | 제약 |
|------|------|------|
| 기본 제공 커넥터 | 서버 운영이 없습니다. | 사용자마다 인증해야 하고, 권한 변경 시 다시 인증이 필요합니다. |
| UC MCP Service | 등록과 권한을 Unity Catalog에서 한곳에서 관리합니다. | 사용자별 OAuth는 사전 로그인이 필요합니다. |
| 사용자 정의 서버 | 팀의 내부 API를 그대로 노출합니다. | 상태 없는 설계가 필요하고, 앱 운영 책임이 생깁니다. |

> **주의** 예약 작업은 연결 권한이 바뀌면 사용자가 다시 인증할 때까지 실패합니다. 예약 작업이 의존하는 MCP 연결은 담당자를 정해 두고 만료를 주기적으로 확인합니다.

## 주의사항

- **허용된 원천만 씁니다.** 워크스페이스 관리자가 서버를 통제하도록 설계되어 있습니다. 임의의 외부 서버를 추가하기 전에 관리자 승인 절차를 거칩니다.
- **쓰기 권한을 최소화합니다.** GitHub처럼 쓰기 범위가 정해진 커넥터도 있지만, 사용자 정의 서버는 앱이 가진 권한만큼 쓸 수 있습니다.
- **Auto-approve 아래에서 MCP 도구가 실행될 수 있습니다.** 운영 환경에서 승인 설정을 함께 검토합니다. 승인 설정은 [모드·기능과 데이터 접근 권한](features-and-permissions.md)을 참고하십시오.
- **Genie Code CLI에서도 MCP를 쓸 수 있습니다.** CLI는 `genie mcp add`로 추가합니다. 자세한 내용은 [Genie Code CLI](cli.md)를 참고하십시오.
- **상태 라벨은 이 페이지에 없습니다.** 릴리즈 노트에는 2026-08-06 "Databricks-managed MCP connectors are now integrated with Unity Gateway (Beta)"가 있습니다. 기본 제공 커넥터의 통합 상태이며, 이 페이지 전체의 상태를 뜻하지는 않습니다.

## 참고 문서

- [Connect to MCP servers](https://docs.databricks.com/aws/en/genie-code/mcp)
- [Genie Code 릴리즈 노트 (2026년 8월)](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
- [Genie Code 릴리즈 노트 (2026년 10월)](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
- [Screen MCP tool calls and results for jailbreaks (Beta)](https://docs.databricks.com/aws/en/release-notes/unity-gateway#screen-mcp-tool-calls-and-results-for-jailbreaks-beta)
