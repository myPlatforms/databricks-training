# 보안 모델 개요

> 기준일: 2026-10-29 · 근거: 공식 문서

## 한눈에 보기

Databricks의 보안은 여러 층에 걸쳐 있습니다. 계정(Account) 수준의 ID와 정책, 워크스페이스(Workspace) 수준의 접근과 컴퓨트, 데이터 수준의 Unity Catalog 권한과 암호화가 함께 동작합니다. 이 장은 이 층들을 다음 세 가지 질문으로 나누어 설명합니다.

| 질문 | 담당 영역 | 다루는 페이지 |
|---|---|---|
| 누가 들어올 수 있는가 | ID, 인증, 네트워크 인바운드 | [ID와 접근](identity-and-access.md), [인증과 토큰](authentication-and-tokens.md), [인바운드 네트워크 접근](network-inbound-access.md) |
| 데이터가 어디로 나가고 어떻게 보호되는가 | 서버리스 이그레스, 암호화, 시크릿, 컴플라이언스 | [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md), [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 무엇을 했고 얼마를 썼는가 | 감사 로그, 시스템 테이블, 비용 | [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md), [비용 관리](cost-management.md) |

> **참고** 아래 "영역 구분" 표는 이 장을 나누기 위한 구분입니다. 공식 문서의 분류 체계를 그대로 옮긴 것이 아닙니다. 실제 책임 범위는 계약과 클라우드 제공자 문서를 함께 확인하십시오.

## 1. 왜 필요한가

### 이전 방식의 한계

- 사용자 계정을 워크스페이스마다 따로 만들면 퇴사자 회수와 권한 점검이 워크스페이스 수만큼 반복됩니다.
- 접근 제어가 노트북과 클러스터 설정에 흩어져 있으면 "이 데이터를 누가 읽었는가"를 한 번에 답할 수 없습니다.
- 장기 자격증명(개인 토큰, 코드에 박힌 비밀번호)이 늘어나면 유출 시 피해 범위를 특정하기 어렵습니다.

Databricks는 ID를 계정에서 중앙 관리하고, 권한은 Unity Catalog에서 데이터 단위로 부여하고, 감사 기록은 시스템 테이블로 남기는 구조를 권장합니다.

## 2. 어떻게 동작하는가

### 2.1 보안 영역의 구성

공식 보안 문서 목차는 다음 영역으로 기능을 나눕니다. 아래 표는 문서 목차의 제목을 따르고, 각 행의 상세 페이지를 이 장의 페이지에 연결합니다.

| 영역 | 주요 기능 (문서 기준) | 상세 페이지 |
|---|---|---|
| 인증과 접근 제어 (Authentication and access control) | SSO, MFA, 접근 제어 목록(ACL) | [ID와 접근](identity-and-access.md), [인증과 토큰](authentication-and-tokens.md) |
| 네트워크 (Networking) | 프런트엔드 PrivateLink, 서버리스 이그레스 제어, 서버리스 방화벽, 고객 관리 VPC | [인바운드 네트워크 접근](network-inbound-access.md), [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md) |
| 데이터 보안과 암호화 (Data security and encryption) | 고객 관리 키(Customer-managed keys), 노드 간 암호화, 자격증명 편집(redaction) | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 시크릿 관리 (Secret management) | Databricks 시크릿 스코프 | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 컴플라이언스 (Compliance) | 컴플라이언스 보안 프로필, 향상된 보안 모니터링, FedRAMP High GovCloud | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |

공식 목차의 인증 영역은 SSO 설정, MFA 설정, 접근 제어 목록(ACL)을 각각 하위 페이지로 둡니다. 시크릿 영역은 개요, 시크릿 생성·사용 튜토리얼, Spark 설정과 환경 변수에서 시크릿을 쓰는 방법 페이지로 나뉩니다. 이 장에서는 이 구분을 "상세 페이지" 열에 묶었습니다.

### 2.2 계정과 워크스페이스의 역할

관리 권한은 두 층으로 나뉩니다. 계정 관리자는 계정 콘솔에서 사용자·서비스 프린시펄·그룹을 만들고 워크스페이스 접근을 부여합니다. 워크스페이스 관리자는 워크스페이스 안의 설정과 컴퓨트, 토큰 정책을 관리합니다.

| 역할 | 할 수 있는 일 | 할 수 없는 일 (문서 명시) |
|---|---|---|
| 계정 관리자 (Account admin) | 계정 수준 사용자·서비스 프린시펄·그룹의 추가·수정·삭제, 워크스페이스 접근 부여, 계정 콘솔 보안 설정, 토큰 보고서 조회·폐기 | 문서 명시 없음 |
| 워크스페이스 관리자 (Workspace admin) | 계정에 ID 추가와 해당 워크스페이스 접근 부여, 워크스페이스 설정, PAT 정책 관리 | 계정 사용자·서비스 프린시펄을 수정하거나 삭제하는 것 |

> **주의** 워크스페이스 관리자는 계정 수준 ID를 수정할 수 없습니다. 따라서 퇴사자 처리를 워크스페이스 관리자에게만 맡기면 계정 수준에 남은 ID가 정리되지 않습니다. 계정 관리자와 워크스페이스 관리자의 절차를 따로 정의하십시오.

### 2.3 계정 수준 보안 기능의 기본 제공 변경

릴리즈 노트 2026-10-26 항목의 제목은 **"Account-level security features are now available by default at GA"** 입니다. 항목 표기는 제목의 GA이며, 별도의 "behavior change" 라벨은 없습니다. 원문의 핵심 문장은 다음과 같습니다.

- "Going forward, account-level security features will be available to all accounts immediately upon General Availability (GA)," "without requiring account admins to manually enable them on the Previews page."
- "Account admins must still configure these features before they take effect."
- "Making these features available does not automatically change an account's security configuration or enforce new controls."

대상 기능은 네트워크 연결(예: 프라이빗 연결), 네트워크 보안(예: 인그레스·이그레스 통제), 암호화, 향상된 보안·컴플라이언스 기능입니다. 정리하면 기능을 **쓸 수 있는 상태** 가 기본이 되었을 뿐, **설정이 자동으로 바뀌지는 않습니다.** "기본으로 켜짐"을 "보안 설정 완료"로 읽으면 안 됩니다.

### 2.4 2026년 10월 보안·ID 관련 릴리즈 항목

아래 표는 2026년 10월 릴리즈 노트에서 보안·ID 관련 항목을 제목 기준으로 모은 것입니다. 상태 표기는 노트 원문을 따르며, 표기가 없는 항목은 "없음"으로 적었습니다.

| 날짜 | 항목 (요지) | 상태 | 이 장의 연결 |
|---|---|---|---|
| 10-01 | 지원되는 외부 엔진이 ABAC 정책이 붙은 Unity Catalog 관리형 테이블을 읽을 수 있음 | GA | [ID와 접근](identity-and-access.md) |
| 10-02 | 시스템 카탈로그에 고객 관리 키를 써서 쿼리 기록을 복호화 | GA | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 10-09 | Google Workspace 커넥터로 애플리케이션 감사 활동 수집 | Beta | [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md) |
| 10-12 | 컨텍스트 기반 인그레스 정책: 등록된 VPC 엔드포인트 단위로 워크스페이스 접근 통제 | GA | [인바운드 네트워크 접근](network-inbound-access.md) |
| 10-12 | 서버리스 컴퓨트에서 AWS 관리형 리소스로의 프라이빗 연결 | GA | [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md) |
| 10-16 | 컴플라이언스 보안 프로필이 켜진 워크스페이스에서 READ METADATA 권한 기본 제공 | 없음 | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 10-19 | 서비스 프린시펄 OAuth 토큰에 사용자 정의 ID 클레임 추가 (사용자별 행 필터) | 없음 | [ID와 접근](identity-and-access.md) |
| 10-21 | Unity Gateway에서 MCP 도구 호출과 결과를 탈옥(jailbreak) 시도 검사 | Beta | [인증과 토큰](authentication-and-tokens.md) |
| 10-22 | Microsoft Entra ID 커넥터로 사용자·그룹·애플리케이션·서비스 프린시펄 수집 | Beta | [ID와 접근](identity-and-access.md) |
| 10-27 | 외부 AI 에이전트를 위한 기본 OAuth 앱 (계정 관리자가 OAuth 앱을 만들 필요 없음) | GA | [인증과 토큰](authentication-and-tokens.md) |

> **참고** 위 표의 항목 요지는 릴리즈 노트 제목과 요약을 바탕으로 한 것입니다. 실제 적용 전에는 항목 원문에서 대상 워크스페이스와 권한 조건을 다시 확인하십시오.

## 3. 어떻게 쓰는가

보안 설정을 시작하기 전에 현재 상태를 확인하는 것이 첫 단계입니다. 아래 쿼리는 시스템 테이블에서 최근 감사 이벤트의 서비스 종류와 액션 종류를 집계합니다. 어떤 이벤트가 기록되는지 먼저 파악하는 데 쓸 수 있습니다.

```sql
SELECT service_name, action_name, COUNT(*) AS event_count
FROM system.access.audit
WHERE event_date >= current_date() - INTERVAL 7 DAYS
GROUP BY service_name, action_name
ORDER BY event_count DESC
LIMIT 50;
```

감사 테이블의 주요 컬럼과 특성은 다음과 같습니다.

| 항목 | 문서 기준 |
|---|---|
| 상태 | Public Preview |
| `service_name` | 요청을 시작한 서비스를 나타내는 문자열 |
| `action_name` | 기록된 이벤트의 범주를 나타내는 문자열 |
| `event_date` | 액션이 일어난 날짜. 문서는 성능을 위해 `event_time` 대신 `event_date`로 필터링하라고 권장 |
| 계정 수준 로그의 `workspace_id` | `0` |
| 워크스페이스 삭제 시 | 삭제된 워크스페이스의 14일보다 오래된 감사 이벤트를 제거 |
| 가용 범위 | 대부분의 감사 로그는 워크스페이스의 리전에서만 조회 가능 |

조회 권한(`USE CATALOG`, `USE SCHEMA`, `SELECT`)은 이 페이지에서 명시하지 않습니다. 권한 구성은 [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md)과 Unity Catalog 권한 문서를 따릅니다.

## 4. 트레이드오프

| 선택 | 장점 | 비용·제약 |
|---|---|---|
| ID를 계정에서 중앙 관리 (ID 연동) | 워크스페이스마다 사용자를 만들 필요가 없음 | 기존 레거시 워크스페이스는 마이그레이션 작업이 필요함 |
| 워크스페이스 로컬 그룹 유지 | 워크스페이스 단위 독립성 | 계정 수준 그룹과 별도 관리되어 권한 점검이 나뉨 |
| 보안 기능을 모두 켜기 | 감사·암호화·네트워크 통제가 넓게 적용됨 | 일부 기능은 추가 요금이나 상위 요금제가 필요할 수 있음. 기능별 요금제 조건은 기능 문서에서 확인 |
| 계정 수준 보안 기능 사용 (2.3절) | 기능이 GA 시점에 바로 쓸 수 있는 상태가 됨 | 관리자가 설정하기 전까지 기존 구성은 바뀌지 않음. 설정을 빠뜨리면 보호가 없는 상태가 계속됨 |

## 5. 주의사항

- **관리 경계를 문서로 정하십시오.** 계정 관리자와 워크스페이스 관리자 중 누가 어떤 설정을 바꾸는지 표로 정리해 두면 감사 때 설명하기 쉽습니다.
- **기본 제공과 설정 완료를 구분하십시오.** 2.3절의 원문대로, 기능이 기본 제공되어도 관리자가 설정해야 효과가 있고 기존 구성은 자동으로 바뀌지 않습니다.
- **보안 설정은 한 번 바꾸면 워크스페이스 전체에 영향을 줍니다.** 특히 네트워크 설정은 사용자 접속을 끊을 수 있으므로 변경 전 롤백 경로를 준비하십시오. 컨텍스트 기반 인그레스 정책은 등록된 VPC 엔드포인트 단위로 접근을 가르므로 엔드포인트 등록 순서를 먼저 확인하십시오.
- **시스템 테이블 접근 권한도 보안 설정의 일부입니다.** 감사 로그를 누구나 읽을 수 있으면 민감한 요청 파라미터가 노출될 수 있습니다.
- **감사 테이블은 Public Preview입니다.** 운영 감사 절차에 넣기 전에 상태와 보존 기간을 확인하고, 장기 보관이 필요하면 별도 적재 계획을 세우십시오. 보관 기간 관련 세부 내용은 [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md)을 참고하십시오.

## 참고 문서

- [Security and compliance](https://docs.databricks.com/aws/en/security/)
- [Authentication and access control](https://docs.databricks.com/aws/en/security/auth/)
- [Configure SSO in Databricks](https://docs.databricks.com/aws/en/security/auth/single-sign-on/)
- [Configure multi-factor authentication](https://docs.databricks.com/aws/en/security/auth/mfa)
- [Access control lists](https://docs.databricks.com/aws/en/security/auth/access-control/)
- [Configure private connectivity to Databricks](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect)
- [What is serverless egress control?](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)
- [Data security and encryption](https://docs.databricks.com/aws/en/security/keys/)
- [Secret management](https://docs.databricks.com/aws/en/security/secrets/)
- [Compliance overview](https://docs.databricks.com/aws/en/security/privacy/)
- [Administration guide](https://docs.databricks.com/aws/en/admin/)
- [Administration concepts](https://docs.databricks.com/aws/en/admin/admin-concepts)
- [Identity management](https://docs.databricks.com/aws/en/admin/users-groups/)
- [Audit logs (system table)](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
