# 배포와 인증

> 기준일: 2026-10-28 · 근거: 공식 문서

## 왜 필요한가

에이전트를 만든 뒤에는 누군가 호출할 수 있는 엔드포인트가 필요합니다. 배포 방식은 서버를 직접 운영할지, 플랫폼이 실행을 맡을지를 정합니다. 인증은 더 중요합니다. 에이전트가 데이터를 읽을 때 **누구의 권한** 으로 읽는지에 따라 같은 질문에 다른 데이터가 나오고, 감사 로그에 남는 주체도 달라집니다.

이 페이지는 배포 방식의 현재 권장과 레거시를 구분하고, Databricks Apps 사용자 권한(on-behalf-of, OBO)과 앱 서비스 프린시펄의 차이를 공식 문서 기준으로 정리합니다.

> **참고** 문서 원문에서 "on-behalf-of 인증", "서비스 프린시펄 인증", "자동 인증 패스스루"를 쓰는 방식으로 찾지 못했습니다. Databricks Apps 문서는 **app authorization**(앱 서비스 프린시펄)과 **user authorization**(사용자 권한 위임, 문서 본문에서 on-behalf-of, OBO로 설명)이라는 두 모델로 설명합니다. 이 장은 원문 명칭을 씁니다.

## 어떻게 동작하는가

### 배포 구성 요소

공식 문서의 배포 페이지는 세 층으로 나눕니다.

| 층 | 옵션 | 상태 | 용도 |
|---|---|---|---|
| 에이전트 서버 | `DurableAgentServer` | 새 에이전트 권장 | Agent Bricks CLI로 만든 에이전트. 실행 상태를 Runtime Store에 보존 |
| 에이전트 서버 | 레거시 에이전트 서버 | 문서에 "legacy" 표기 | 앱 템플릿으로 만든 기존 에이전트 유지보수 |
| 에이전트 서버 | 자체 서버 | 문서에 명시 없음 | 커스텀 엔드포인트, 요청 형식, 프로토콜이 필요할 때 |
| 실행 런타임 | Agent Runtime | 문서에 명시 없음 | 새 에이전트. 인증된 엔드포인트를 제공. 실행 위치는 문서 설명이 엇갈림 (서버리스 컴퓨트 또는 Databricks Apps, [제품 지도의 상충 항목](agent-product-map.md) 참고) |
| 실행 런타임 | Model Serving | Legacy | 이전에 Model Serving 엔드포인트로 배포한 에이전트 |

Agent Runtime에서 각 배포는 `agent-bricks-<name>`이라는 이름의 앱이 되고 고유 URL을 가집니다. 클라이언트는 Databricks OAuth 토큰으로 호출합니다. 에이전트는 앱의 서비스 프린시펄로 실행됩니다. 단, `auth = "user"`로 선언한 도구는 요청한 사용자의 권한으로 실행됩니다.

### 인증 모델 두 가지

Databricks Apps는 OAuth 2.0 기반의 두 신원 모델을 씁니다.

| 모델 | 문서 명칭 | 신원 | 쓰는 경우 |
|---|---|---|---|
| 앱 권한 | App authorization | 앱의 서비스 프린시펄 (변경 불가) | 백그라운드 작업, 공유 메타데이터, 로깅, 외부 서비스 호출 |
| 사용자 권한 | User authorization (on-behalf-of, OBO) | 앱에 접속한 사용자 | 결과가 개인별 권한을 따라야 할 때. 테이블 질의, 사용자에 묶인 작업 |

앱 권한에서는 모든 사용자가 같은 서비스 프린시펄의 권한을 공유하므로 앱이 사용자별 접근을 강제하지 못합니다. 서비스 프린시펄에는 SQL 웨어하우스나 UC 테이블에 대한 권한을 명시적으로 줘야 합니다.

사용자 권한에서는 Databricks가 사용자의 액세스 토큰을 전달하고, 모든 접근이 그 사용자의 UC 권한을 따릅니다. 행 필터와 열 마스크도 자동으로 적용되므로 앱이 별도 필터 로직을 가질 필요가 없다고 문서가 설명합니다. 행 필터와 열 마스크는 [6장](../06-unity-catalog/row-filters-and-column-masks.md)에서 다룹니다.

## 어떻게 쓰는가

### 1. 에이전트 배포

Agent Bricks CLI 프로젝트는 `agentbricks deploy`로 배포합니다. 명령은 [Agent Bricks CLI로 에이전트 개발하기](build-agent-with-cli.md)에 있습니다. 배포하는 사용자는 앱, 저장소, MLflow 실험을 만들거나 관리할 권한이 있어야 합니다.

배포 후 상태를 확인하는 명령은 다음과 같습니다.

```bash
agentbricks deployments logs
agentbricks deployments stop
```

Agent Runtime의 제약은 다음과 같습니다.

- 인스턴스는 1개부터 5개까지 실행할 수 있습니다.
- 여러 인스턴스를 쓰면 `X-Routing-Key` 헤더로 한 세션을 같은 인스턴스에 고정할 수 있습니다.
- 배포된 에이전트의 서버 종류는 바꿀 수 없습니다. 바꾸려면 새 프로젝트를 만들어 새 이름으로 배포합니다.
- Runtime Store는 `DurableAgentServer`를 쓰는 에이전트에만 준비됩니다.
- 서비스 프린시펄에 데이터와 리소스 접근을 주는 일은 사용자 책임입니다. 문서가 명시합니다.

### 2. 호출 주체 정하기

에이전트가 도구로 데이터를 읽을 때는 아래 세 가지 조합 중 하나를 고릅니다.

| 조합 | 실행 신원 | 감사 로그 | 권장 상황 |
|---|---|---|---|
| 에이전트 기본 + 도구 `auth = "app"` | 앱 서비스 프린시펄 | 서비스 프린시펄 | 모든 사용자에게 같은 데이터가 보여도 되는 경우 |
| 에이전트 기본 + 도구 `auth = "user"` | 요청한 사용자 | 사용자 | 사용자별 UC 권한이 결과에 반영되어야 하는 경우 |
| Unity Catalog 함수 도구 | 앱 서비스 프린시펄 (`auth = "app"`만 지원) | 서비스 프린시펄 | UC 함수로 캡슐화된 로직을 공유하는 경우 |

`agent.toml`에서 도구별 인증을 씁니다.

```toml
[[tools]]
id = "web_search"
auth = "user"
source = { kind = "mcp", service = "system.ai.web_search" }
```

### 3. Databricks Apps에서 사용자 토큰 읽기

Databricks Apps에서 사용자 권한을 쓰려면 앱이 요청할 **사용자 API 범위**(scope)를 선언해야 합니다. 범위는 예를 들어 `sql`, `genie`, `files` 같은 값입니다. 범위에 없는 기능은 사용자 권한이 있어도 막힙니다.

CLI로 범위를 지정하는 예시는 다음과 같습니다.

```bash
databricks apps create <app-name> \
  --json '{
    "user_api_scopes": ["sql", "files"]
  }'
```

범위를 하나도 고르지 않으면 `iam.access-control:read`와 `iam.current-user:read`가 기본으로 붙습니다. 이 두 범위는 신원 조회만 허용하며, 데이터나 컴퓨트 접근은 허용하지 않습니다.

사용자 토큰은 `x-forwarded-access-token` 헤더로 전달됩니다. 프레임워크별로 읽는 방법은 문서에 다음처럼 나옵니다.

```python
import streamlit as st
user_access_token = st.context.headers.get('x-forwarded-access-token')
```

```python
from flask import request
headers = request.headers
user_token = headers.get('x-forwarded-access-token')
```

```javascript
import express from 'express';
const userAccessToken = req.header('x-forwarded-access-token');
```

> **주의** 토큰을 출력하거나, 로그에 남기거나, 파일에 쓰지 마십시오. 문서가 명시적으로 금지합니다.

관리자는 개발자가 추가할 수 있는 범위를 허용 목록으로 정합니다. 기본값은 **All APIs** 이고, **None** 을 고르면 사용자 권한 기능이 꺼집니다. 사용자는 앱과 범위 조합마다 한 번 동의하고, 그 동의를 보거나 철회할 수 있습니다.

### 4. MCP 서버의 호출 인증

MCP 서버로 들어오는 호출의 인증은 다음과 같습니다. 자세한 도구 설정은 [도구: UC 함수와 MCP 서버](tools-uc-functions-and-mcp.md)에 있습니다.

| 방식 | 설명 |
|---|---|
| OAuth 사용자-머신 (U2M) | 사람이 코딩 에이전트나 비즈니스 클라이언트에서 로그인. 로그인한 사용자로 호출 |
| OAuth 머신-머신 (M2M) | 무인 에이전트나 서비스. 서비스 프린시펄로 호출 |
| OAuth 토큰 연합 | 외부 IdP 토큰을 Databricks OAuth 토큰으로 교환 |
| 개인 액세스 토큰 (PAT) | 토큰 소유자로 호출. Databricks Apps의 MCP 서버에는 지원 안 됨 |

Databricks Apps 위의 MCP 서버를 호출하려면 호출자에게 앱의 **CAN USE** 권한과 OAuth 토큰이 필요합니다.

> **참고** 호출자의 권한은 두 종류입니다. MCP 호출에 필요한 **Consumer access** 엔타이틀먼트와, 워크스페이스 관리에 필요한 **Workspace access** 엔타이틀먼트입니다. 문서는 Consumer access로 MCP 도구를 쓸 수 있고, Unity Gateway UI에서 MCP를 관리하려면 Workspace access가 필요하다고 명시합니다.

## 트레이드오프

| 선택 | 장점 | 제약 |
|---|---|---|
| Agent Runtime | 서버 운영 없이 인증 엔드포인트 제공 | 인스턴스 수 1~5, 서버 종류 변경 불가 |
| Model Serving (레거시) | 기존 엔드포인트 유지 | 문서가 새 에이전트에 권장하지 않음 |
| 앱 권한 | 설정이 단순, 공유 데이터에 적합 | 사용자별 접근 제어 불가 |
| 사용자 권한 | UC 권한과 행·열 보안이 사용자 기준으로 적용 | 범위 설정과 동의 절차가 필요하고, 다른 워크스페이스 호출에는 제약이 있음 |

문서는 사용자 토큰이 워크스페이스 범위로 제한된다고 명시합니다. 다른 워크스페이스의 웨어하우스에 접근하려면 그 워크스페이스에 앱을 배포하거나, 서비스 프린시펄을 쓰는 M2M OAuth를 써야 합니다. 후자는 사용자별 제어를 잃습니다.

## 주의사항

- **권한 오류의 첫 확인 사항**: 권한이 부족하다는 오류가 나면 호출 주체가 앱 서비스 프린시펄인지 사용자인지부터 확인하십시오. 두 주체의 권한은 다르므로, 이 구분이 원인 분석의 출발점입니다.
- **범위 최소화**: 필요한 범위만 선언하십시오. 범위 밖 기능은 차단되고, 이미 실행 중인 앱은 기존 범위로 계속 돌아갑니다. 그러나 범위가 허용 목록에서 빠진 앱은 시작, 배포, 업데이트가 안 됩니다.
- **지원 중단된 범위 이름**: 예를 들어 `sql.warehouses`는 `sql`로 바뀌었습니다. 오래된 예제의 범위 이름을 그대로 쓰지 마십시오.
- **감사**: 사용자 수준 작업은 감사 로그로 남기고, 범위를 최소로 유지하십시오. 문서가 권장합니다.
- **PAT 금지**: MCP 서버 호출에 PAT를 쓰지 마십시오.
- **문서 명칭 확인**: 문서 페이지에는 Agent Runtime의 기능 상태 라벨이 없습니다. 운영 적용 전에 해당 페이지에서 라벨과 지역 가용성을 확인하십시오.
- **Model Serving 레거시**: 기존 Model Serving 에이전트를 옮기는 작업은 마이그레이션 가이드를 따르십시오. 문서 링크는 아래 참고 문서에 있습니다.

## 참고 문서

- [Deploy agents on Databricks](https://docs.databricks.com/aws/en/agents/deploy/)
- [Agent Runtime](https://docs.databricks.com/aws/en/agents/deploy/agent-runtime)
- [Agent Server](https://docs.databricks.com/aws/en/agents/deploy/agent-server)
- [Databricks Apps authorization](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth)
- [Configure permissions for a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/permissions)
- [MCP authentication](https://docs.databricks.com/aws/en/agents/mcp-tools/authentication-networking)
- [Migrate an agent from Model Serving to Databricks Apps](https://docs.databricks.com/aws/en/agents/custom-agents/migrate-agent-to-apps)
- [Query agents deployed on Databricks](https://docs.databricks.com/aws/en/agents/query-llms)
