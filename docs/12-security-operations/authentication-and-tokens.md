# 인증과 토큰

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 한눈에 보기

Databricks는 사람과 기계가 쓰는 인증 방식을 나눕니다. 사람이 브라우저로 로그인하는 **OAuth U2M**, 서비스 프린시펄이 클라이언트 자격증명으로 인증하는 **OAuth M2M** 이 기본 축입니다. 개인 액세스 토큰(Personal access token, PAT)은 지원되지만 문서는 OAuth를 권장하며, 워크스페이스 관리자가 PAT 정책을 관리합니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 장기 토큰은 한 번 만들면 만료가 없거나 길어서, 유출 시 피해 기간이 깁니다.
- 코드나 노트북에 토큰을 넣으면 저장소 이력에 남아 회수가 어렵습니다.
- 사람 계정의 토큰으로 잡을 돌리면 그 사람이 퇴사하는 순간 잡이 멈춥니다.

OAuth는 짧게 살아 있는 토큰을 발급하고, 사람과 기계의 인증 경로를 나눕니다. 그래서 문서는 OAuth를 먼저 쓰라고 권장합니다.

## 2. 어떻게 동작하는가

### 인증 방식 비교

문서의 인증 방식 표를 옮기면 다음과 같습니다.

| 방식 | 누가 쓰는가 | 토큰 획득 방법 | 문서 기준 설명 |
|---|---|---|---|
| OAuth 토큰 연동 (OAuth token federation) | 사용자 또는 서비스 프린시펄 | IdP가 발급한 OAuth 토큰 | 권장. Databricks 시크릿을 따로 관리하지 않음 |
| OAuth M2M (서비스 프린시펄) | 잡, CI/CD 같은 무인 작업 | 클라이언트 ID와 클라이언트 시크릿으로 발급 | 짧게 살아 있는 OAuth 토큰 |
| OAuth U2M (사용자) | 사람이 직접 쓰는 작업 | 브라우저 로그인 | 짧게 살아 있는 OAuth 토큰 |
| 개인 액세스 토큰 (PAT) | 사용자 또는 서비스 프린시펄 | 토큰 문자열 발급 | 지원되지만 OAuth 사용을 권장 |

> **참고** 토큰 수명 값은 문서에 구체적인 시간으로 적혀 있지 않습니다. "짧게 살아 있는(short-lived)" 토큰이라는 표현만 확인했습니다.

### OAuth U2M

사용자가 브라우저에서 Databricks에 로그인하면 토큰이 발급됩니다. 문서는 대화형(attended) 시나리오에 쓰인다고 설명합니다. CLI와 SDK의 통합 인증(unified authentication)이 이 토큰을 자동으로 만들고 갱신합니다.

### OAuth M2M

서비스 프린시펄이 클라이언트 ID와 클라이언트 시크릿으로 토큰을 받습니다. 문서는 이 자격증명을 `DATABRICKS_CLIENT_ID`와 `DATABRICKS_CLIENT_SECRET` 환경 변수에서 읽는다고 설명합니다. 서비스 프린시펄은 워크스페이스에 배정된 뒤에 이 시크릿을 받을 수 있습니다.

```bash
# 서비스 프린시펄 M2M 인증용 환경 변수 예시
# 값은 실제 값으로 바꾸되, 셸 이력이나 저장소에 남지 않도록 주의하십시오.
export DATABRICKS_HOST="https://<workspace-url>"
export DATABRICKS_CLIENT_ID="<service-principal-application-id>"
export DATABRICKS_CLIENT_SECRET="<client-secret>"
```

> **주의** 위 예시의 `<workspace-url>`은 자리표시자입니다. 실제 워크스페이스 URL과 자격증명을 공개 문서나 저장소에 쓰지 마십시오.

### OAuth OBO (On-behalf-of)

서비스 프린시펄을 관리하는 사용자가 그 프린시펄의 권한으로 작업하는 방식입니다. 문서는 이 방식이 긴 수명의 서비스 프린시펄 시크릿 필요를 줄인다고 설명합니다. 상태 표기는 페이지마다 다릅니다. OAuth M2M 페이지는 **Beta** 로 표기하고, 인증 개요 페이지는 상태 라벨을 두지 않습니다. 실제 사용 전 원문에서 다시 확인하십시오.

### 사용 권한 전제

문서는 사용자나 서비스 프린시펄이 접근하려는 기능에 대해 `CAN USE` 권한이 있어야 한다고 명시합니다. 관리자가 이 권한을 주지 않으면 토큰이 있어도 해당 기능을 쓸 수 없습니다.

### 외부 AI 에이전트의 OAuth 앱

릴리즈 노트에 따르면 2026년 10월 27일부터 "Default OAuth apps for external AI agents"가 GA입니다. AI 에이전트 클라이언트가 기본 OAuth 클라이언트 ID로 Databricks MCP 서버에 연결할 수 있어, 관리자가 OAuth 앱을 따로 만들 필요가 없습니다. 에이전트 쪽 구성은 [09장 도구: UC 함수와 MCP 서버](../09-ai-agents/tools-uc-functions-and-mcp.md)에서 다룹니다.

## 3. 어떻게 쓰는가

### PAT 정책 (문서 원문 기준)

PAT 관리는 다음 항목으로 구성됩니다. 문서의 표현을 최대한 그대로 옮겼습니다.

| 항목 | 문서 내용 |
|---|---|
| 관리 권한 | 관리자만 PAT를 관리할 수 있음. 계정 관리자는 계정 전체의 토큰을 모니터링하고 폐기할 수 있음. 워크스페이스 관리자는 워크스페이스의 PAT를 비활성화하고, 생성·사용 가능한 사용자를 제어하고, 최대 수명을 설정할 수 있음 |
| 플랜 요건 | 워크스페이스에서 PAT를 관리하려면 Premium 플랜 이상 |
| 기본 상태 | PAT 인증은 기본으로 켜져 있음 |
| 기본 최대 수명 | 새 토큰의 기본 최대 수명은 730일 |
| 수명 설정 | `maxTokenLifetimeDays`를 정수로 설정(예: `"90"`). `"0"`이면 사용자 지정 제한을 제거하고 730일 기본값으로 되돌림 |
| 수명 설정 범위 | 설정은 새로 만드는 토큰에만 적용됨 |
| 권장 수명 | 90일 미만 |
| 미사용 자동 폐기 | 90일 이상 사용하지 않은 PAT는 자동으로 폐기됨 |
| 만료 알림 | 이메일 형식 사용자 이름은 만료 약 7일 전 알림. 서비스 프린시펄 토큰 만료 알림은 워크스페이스 관리자에게 가며, 수명이 7일보다 길고 한 번 이상 쓰인 토큰에만 해당. 서비스 프린시펄 OAuth 시크릿은 알림 대상이 아님 |
| 비활성화 효과 | PAT를 끄면 기존 토큰이 삭제되지는 않음. 다시 켜면 만료되지 않은 토큰은 다시 사용 가능 |
| 의존 기능 | Partner Connect, 파트너 통합, 서비스 프린시펄은 PAT가 켜져 있어야 함 |

### 계정 콘솔에서 토큰 보고서 보기

계정 콘솔의 **Security** 메뉴에서 **Token report** 를 열면 토큰 소유자, 워크스페이스, 생성일, 만료일, 마지막 사용일로 필터링할 수 있습니다. **Export** 로 CSV를 받거나, 토큰을 선택해 **Revoke** 로 폐기할 수 있습니다. 문서는 이 보고서 쿼리가 계정 관리자가 해당 페이지에 있는 동안에만 실행된다고 설명합니다.

### CLI로 토큰 목록과 폐기

워크스페이스 수준에서는 토큰 관리 API나 CLI를 씁니다. 문서가 명시한 명령은 다음과 같습니다.

```bash
# 워크스페이스의 토큰 목록을 조회합니다.
databricks token-management list

# 특정 토큰을 폐기합니다. TOKEN_ID는 list 결과에서 확인합니다.
databricks token-management delete TOKEN_ID
```

### 최대 수명 설정

최대 수명은 워크스페이스 설정 항목 `maxTokenLifetimeDays`로 지정합니다. 문서는 CLI(`databricks workspace-conf set-status`)와 워크스페이스 구성 API를 모두 안내합니다. 이 설정은 기존 토큰을 소급하지 않으므로, 적용 후 기존 토큰은 별도로 점검해야 합니다.

## 4. 트레이드오프

| 선택 | 장점 | 제약 |
|---|---|---|
| OAuth 중심 | 짧은 수명, 시크릿 회수 쉬움 | 기존 PAT 기반 도구는 이전 작업이 필요함 |
| PAT 허용 | 간단하고 모든 도구가 지원 | 장기 토큰이라 유출 위험이 큼. 문서도 OAuth 이전을 권장 |
| 최대 수명을 짧게 | 유출 피해 기간 축소 | 자주 갱신해야 하므로 잡과 도구가 자주 깨질 수 있음 |
| PAT 비활성화 | 토큰 경로 자체를 차단 | Partner Connect, 파트너 통합, 서비스 프린시펄이 함께 막힘 |

## 5. 주의사항

- **PAT 사용 현황을 먼저 확인하십시오.** 토큰 보고서에서 마지막 사용일을 보고, 사용 중인 PAT를 OAuth로 옮긴 뒤 폐기하는 순서가 안전합니다.
- **서비스 프린시펄 토큰 만료 알림은 워크스페이스 관리자에게 갑니다.** 알림을 받을 관리자 주소가 실제로 살아 있는지 확인하십시오.
- **최대 수명 설정은 새 토큰에만 적용됩니다.** 기존 토큰은 자동으로 짧아지지 않습니다.
- **90일 미사용 자동 폐기를 믿고 방치하지 마십시오.** 자동 폐기는 최후의 안전장치입니다. 정기 점검으로 토큰을 직접 정리하는 것이 권장됩니다.
- **토큰 값을 노트북이나 코드에 쓰지 마십시오.** 시크릿 관리는 [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md)에서 다룹니다.

## 참고 문서

- [Authentication and access control overview](https://docs.databricks.com/aws/en/security/auth/)
- [Authorize access to Databricks resources](https://docs.databricks.com/aws/en/dev-tools/auth/)
- [OAuth M2M and OBO](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
- [Manage personal access token permissions](https://docs.databricks.com/aws/en/security/auth/api-access-permissions)
- [Monitor and revoke personal access tokens](https://docs.databricks.com/aws/en/admin/access-control/tokens)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
