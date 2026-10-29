# Lakeflow Connect

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Lakeflow Connect는 SaaS 애플리케이션, 데이터베이스, 파일 서비스, 메시지 버스에서 데이터를 수집하는 **관리형 커넥터(managed connectors)** 모음입니다. 공식 문서는 Lakeflow Connect가 "local files, popular enterprise applications, databases, cloud storage, message buses, and more"에서 데이터를 수집하는 커넥터를 제공한다고 설명합니다. 수집 결과는 스트리밍 테이블(Delta 테이블에 증분 처리 기능이 추가된 형태)에 저장됩니다.

## 왜 필요한가

SaaS API나 데이터베이스 변경 로그를 직접 읽는 수집 코드는 다음 작업을 모두 떠안습니다.

- **인증**: 원천마다 OAuth, API 토큰, 서비스 계정 등 방식이 다릅니다.
- **증분 읽기**: 마지막 커서(시각, 페이지 토큰, 로그 위치)를 저장하고 이어 읽어야 합니다.
- **스키마 변경**: 원천에 필드가 추가되거나 타입이 바뀌면 대상 테이블을 맞춰야 합니다.
- **재시도**: 속도 제한(rate limit), 일시 장애, 부분 실패를 처리해야 합니다.

Lakeflow Connect 문서는 각 커넥터가 이 네 가지를 처리한다고 설명합니다. 사용자는 연결(Connection)과 수집 파이프라인을 설정하는 데 집중할 수 있습니다.

## 어떻게 동작하는가

### 커넥터 분류

문서는 다음과 같이 커넥터 유형을 나눕니다. 분류명과 예시는 "What is Lakeflow Connect?"와 "Lakeflow Connect connector concepts" 페이지의 표기를 따릅니다.

| 유형 (문서 표기) | 설명 | 문서에 나온 예시 |
|---|---|---|
| Database connectors | 변경 데이터 캡처(CDC)로 관계형 DB 수집 | MySQL, PostgreSQL, Oracle, SQL Server |
| SaaS connectors | 기업용 SaaS 애플리케이션 수집 | Salesforce, HubSpot, Jira, Workday |
| File connectors | 클라우드 스토리지와 기업 파일 서비스의 파일 수집 | Google Drive, SharePoint |
| Streaming connectors | 메시지 버스·이벤트 스트림 연속 수집 | Apache Kafka, RabbitMQ (Amazon Kinesis, Google Pub/Sub, Apache Pulsar 언급) |
| Query-based connectors | CDC 없이 쿼리로 DB 직접 조회 | 예시 없음 |
| Direct write (Zerobus Ingest API) | 애플리케이션이 스트리밍 테이블에 직접 쓰기 | 단일 제공 방식 |
| Community connectors | 커뮤니티 커넥터 | 별도 페이지 |
| Custom connectors | 내장 커넥터가 없는 원천용 | 별도 페이지 |

### SaaS 커넥터 목록

"SaaS connectors" 개요 페이지(saas-overview)에 나열된 커넥터 이름은 다음과 같습니다. 원문 표기 그대로 옮겼습니다. 이 목록에는 상태 라벨이 표시되지 않습니다.

1Password Event Logs, Aha!, Akamai WAF, Amplitude, Anaplan, Anthropic, Anysphere Audit Logs, Anysphere Organization, Asana, Atlassian Audit Logs, Azure DevOps, Box Audit Logs, Celigo, Confluence, Cribl, CrowdStrike Falcon Event Stream, Microsoft Dynamics 365, GitHub, GitLab, Glean, Gmail, Google Ads, Google Analytics, Google Analytics Aggregated, Google Search Console, Google Workspace, HubSpot, Jira, LinkedIn Ads, Marketo, Meta Ads, Microsoft 365 Unified Audit Logs, Microsoft Entra ID, Monday.com, Netskope Logs, NetSuite, Notion, Okta System Logs, OpenAI, Oracle Eloqua, Outlook, PagerDuty, PayPal, Pendo, Productboard, QuickBooks, Reddit Ads, Salesforce, Salesforce Marketing Cloud, SendGrid, ServiceNow, SharePoint, Shopify, Smartsheet, Square, Strac, SurveyMonkey, TikTok Ads, Veeva Vault, Verkada, Vimeo, Wiz Audit Logs, Workday Activity Logging, Workday HCM, Workday Reports, Workiva, Zendesk Support, Zip, Zoho Books, Zoho CRM

> **참고** 위 목록에는 70개 커넥터가 있습니다. 목록은 문서 기준 시점의 것이며 커넥터는 계속 추가됩니다. 최신 목록은 [saas-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/saas-overview)에서 확인하십시오.

SAP Business Data Cloud 공유는 Lakeflow Connect가 아니라 OpenSharing 기반이라고 문서가 따로 설명합니다.

### 상태 라벨 (GA / Public Preview / Beta)

커넥터 개요 페이지와 SaaS 목록 페이지에는 커넥터별 상태 라벨이 없습니다. 문서는 "Lakeflow Connect connectors are in various release states"라고만 밝히고 [릴리즈 상태 정의](https://docs.databricks.com/aws/en/release-notes/release-types)로 연결합니다. 상태는 커넥터 페이지나 릴리즈 노트에서 확인해야 합니다. 2026년 8월부터 10월까지 릴리즈 노트에 올라온 커넥터 상태는 다음과 같습니다. 날짜는 릴리즈 노트 표제에 표시된 날짜입니다.

| 커넥터 | 상태 | 발표일 (2026) | 비고 |
|---|---|---|---|
| MySQL integrated CDC pipeline | GA | 10-15 | 단일 파이프라인, 별도 수집 게이트웨이 없음 |
| NetSuite | GA | 08-04 | |
| Google Drive (managed, standard) | GA | 08-04 | 두 변형 모두 GA |
| SharePoint (managed, standard) | GA | 08-04 | 두 변형 모두 GA |
| QuickBooks | Beta | 10-26 | |
| Google Analytics Aggregated | Beta | 10-23 | 커넥터 페이지에서도 "Beta" 확인 |
| Box Audit Logs | Beta | 10-23 | 커넥터 페이지에서도 "Beta" 확인, 관리자가 Previews 페이지에서 활성화해야 함 |
| PayPal | Beta | 10-24 | |
| Microsoft Entra ID | Beta | 10-22 | |
| SurveyMonkey, Oracle Eloqua, Asana | Beta | 10-20 | |
| Cribl | Beta | 10-13 | |
| Zoho CRM, Google Workspace, Productboard, Azure DevOps, Vimeo, GitLab | Beta | 10-12 ~ 10-01 | |
| Workday Activity Logging, Okta System Logs, Microsoft 365 Unified Audit Logs, CrowdStrike Falcon Event Stream, Akamai WAF, 1Password Event Logs | Beta | 09-28 | |
| Shopify | Beta | 09-22 | |
| Celigo, Anysphere Organization, Anaplan | Beta | 09-09 | |
| Atlassian Audit Logs, Anysphere Audit Logs, Verkada, Workiva, SendGrid, Gmail, Google Search Console, Glean, Amplitude, Notion, PagerDuty | Beta | 08-04 ~ 08-27 | |

> **참고** 위 표는 릴리즈 노트 표제 기준 스냅샷입니다. 표에 없는 커넥터(예: Salesforce, Confluence, Jira)의 상태 라벨은 이 장에서 확인하지 못했으므로 "문서에 명시 없음"으로 봅니다. 해당 커넥터 페이지에서 직접 확인하십시오.

> **참고** Box Audit Logs 커넥터 페이지는 **Beta** 라벨을 두 번 표시합니다(제목 아래와 "This feature is in Beta." 안내). 이처럼 Beta 기능은 워크스페이스 관리자가 Previews 페이지에서 먼저 활성화해야 할 수 있습니다.

## 어떻게 쓰는가

커넥터 설정은 일반적으로 다음 흐름입니다. 세부 단계와 화면은 커넥터마다 다르므로 해당 커넥터의 `-source-setup`, `-connection`, `-pipeline` 페이지를 따릅니다.

1. **원천 준비**: 원천 시스템에서 API 권한, 서비스 계정, OAuth 클라이언트 등을 만듭니다. Box Audit Logs는 OAuth M2M(Server Authentication, Client Credentials Grant)만 지원하며 OAuth U2M과 사용자 이름·비밀번호 인증은 지원하지 않는다고 문서가 명시합니다.
2. **연결(Connection) 생성**: Catalog Explorer에서 자격 증명을 저장하는 Unity Catalog 연결을 만듭니다. `USE CONNECTION` 권한이 있는 사용자는 자격 증명을 보지 않고 파이프라인을 만들 수 있습니다. Google Analytics Aggregated 문서도 같은 방식을 설명합니다.
3. **수집 파이프라인 생성**: 연결을 선택하고 수집할 테이블과 대상 카탈로그·스키마를 지정합니다.
4. **실행과 모니터링**: 수집 파이프라인은 서버리스 컴퓨트에서 실행된다고 문서가 설명합니다. 진행 상황은 게이트웨이 이벤트 로그(gateway-event-logs)와 비용 페이지로 확인합니다.

### 과금 구조

문서에 명시된 과금 구조는 다음과 같습니다.

- 사용량은 `system.billing.usage` 시스템 테이블에 기록됩니다. `billing_origin_product = 'LAKEFLOW_CONNECT'` 조건으로 관리형 커넥터 사용량을 분리합니다.
- `usage_type`은 파이프라인 처리 시간에 대해 `COMPUTE_TIME`으로 기록됩니다.
- `usage_unit`은 원시 컴퓨트 시간인 `MILLISECOND`와 과금 단위인 `DBU`로 기록됩니다.
- `usage_metadata`에는 `dlt_pipeline_id`와 대상 테이블의 `uc_table_catalog`, `uc_table_schema`, `uc_table_name`이 들어갑니다.
- 관리형 수집 파이프라인에는 Lakeflow 파이프라인과 비슷한 **유지 관리(maintenance) 요금** 이 발생한다고 문서가 설명합니다. 인프라, 메타데이터 관리, 실행 사이의 변경 추적을 포함한다고 설명합니다.
- 달러 비용 추정은 `system.billing.list_prices`를 `sku_name`으로 조인하고 `pricing.effective_list.default`를 곱하는 방식을 제시합니다. 실제 비용은 계정 가격 등급과 권한에 따라 다를 수 있다고 문서가 덧붙입니다.

다음은 문서의 조회 방식을 따른 DBU 사용량 집계 예시입니다. 컬럼명은 문서에 나온 이름을 사용했습니다.

```sql
SELECT
  usage_date,
  usage_metadata.dlt_pipeline_id AS pipeline_id,
  SUM(usage_quantity) AS dbus
FROM system.billing.usage
WHERE billing_origin_product = 'LAKEFLOW_CONNECT'
  AND usage_unit = 'DBU'
GROUP BY ALL
ORDER BY usage_date DESC;
```

> **참고** 문서에 명시되지 않은 항목: SKU 이름, DBU당 단가, 게이트웨이나 서버리스 컴퓨트의 별도 과금 여부, 무료 사용 허용량(free allowance). 이 장에서는 수치를 적지 않습니다. 과금 단가는 공식 pricing 페이지에서 확인하십시오.

## 트레이드오프

| 항목 | 관리형 커넥터 | 직접 구현 (노트북·API 호출) |
|---|---|---|
| 초기 구축 | 연결과 파이프라인 설정으로 시작 | 인증, 증분, 재시도 코드 필요 |
| 원천 범위 | 목록에 있는 커넥터만 | 임의의 API 가능 |
| 상태 | Beta 다수 | 직접 관리 |
| 과금 | 파이프라인 처리 + 유지 관리 요금 | 노트북·잡 컴퓨트 |
| 스키마 변경 | 커넥터가 처리한다고 문서가 설명 | 직접 처리 |

커넥터가 목록에 없거나 운영 SLA가 필요한 원천에는 커스텀 커넥터(custom-connectors)나 커뮤니티 커넥터 페이지를 함께 검토합니다. 파일 기반 원천이면 [Auto Loader](auto-loader.md)가 더 적합할 수 있습니다.

## 주의사항

- **상태 라벨을 확인하십시오**: Beta 커넥터는 SLA와 안정적인 인터페이스가 보장되지 않습니다. 릴리즈 상태 정의는 release-types 페이지에 있습니다.
- **Beta 활성화**: Beta 커넥터는 관리자가 Previews 페이지에서 활성화해야 하는 경우가 있습니다 (Box Audit Logs, Google Analytics Aggregated 문서 명시).
- **권한 분리**: 연결은 관리자가 만들고 `USE CONNECTION` 권한으로 공유하는 방식이 권장됩니다. 자격 증명을 파이프라인 작성자에게 노출하지 않도록 설계합니다.
- **과금 추적**: 수집 비용은 `system.billing.usage`에서 `LAKEFLOW_CONNECT`로 따로 집계하십시오. 유지 관리 요금이 있어 처리 시간만으로는 전체 비용이 맞지 않을 수 있습니다.
- **원천 준비 항목**: 원천 측 관리자 권한이 필요한 커넥터가 많습니다. 설정 전에 커넥터별 `-source-setup` 페이지의 요구 사항을 먼저 확인하십시오.

## 참고 문서

- [What is Lakeflow Connect?](https://docs.databricks.com/aws/en/ingestion/overview)
- [Lakeflow Connect connector concepts](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/)
- [SaaS connectors (saas-overview)](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/saas-overview)
- [Database connectors (CDC overview)](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/cdc-overview)
- [Monitor managed ingestion pipeline cost](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/monitor-costs)
- [Box Audit Logs connector](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/box-audit-logs)
- [Google Analytics Aggregated connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-analytics-aggregated-connection)
- [Release types](https://docs.databricks.com/aws/en/release-notes/release-types)
- [Release notes, 2026년 10월](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
- [Release notes, 2026년 9월](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [Release notes, 2026년 8월](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
