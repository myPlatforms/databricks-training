# 비용 관리

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Databricks 비용을 관리하는 도구는 네 가지입니다. **사용량 대시보드**(Usage dashboard)로 전체 추세를 보고, ** 예산**(Budgets)으로 한도를 넘기 전에 알림을 받고, ** 태그**(Tags)로 팀과 프로젝트에 비용을 귀속하며, ** 서버리스 사용량 정책**(Serverless usage policies)으로 서버리스 사용량에 태그를 자동으로 붙입니다. 원자료는 `system.billing.usage` 시스템 테이블에 있습니다. 이 페이지는 단가 숫자를 다루지 않습니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 월말 청구서를 받고 나서야 비용을 알 수 있으면 조치 시점이 늦습니다.
- 클러스터 하나에 여러 팀의 작업이 섞이면 누가 얼마를 쓰는지 나눌 수 없습니다.
- 서버리스 컴퓨트는 클러스터 설정이 없어서 기존 클러스터 태그 방식으로는 귀속이 어렵습니다.

Databricks는 청구 기록을 시스템 테이블로 제공하고, 태그와 정책으로 귀속하고, 예산으로 경고와 차단을 나누는 구조를 제공합니다.

## 2. 어떻게 동작하는가

### 원자료: `system.billing.usage`

청구 사용량은 `system.billing.usage`에 기록됩니다. 문서가 설명하는 주요 컬럼은 다음과 같습니다.

| 컬럼 | 의미 (문서 기준) |
|---|---|
| `usage_date` | 기록 날짜. 날짜별 집계에 빠르게 쓸 수 있는 필드라고 문서가 설명 |
| `workspace_id` | 사용량이 속한 워크스페이스 ID |
| `sku_name` | SKU 이름 |
| `usage_quantity` | 소비된 단위 수량(decimal) |
| `usage_unit` | 단위. 예: `DBU` |
| `custom_tags` | 사용량 기록에 붙은 사용자 정의 태그 맵 |
| `identity_metadata` | `run_as`, `owned_by` 같은 신원 관련 메타데이터 구조체 |

갱신 지연은 일반적으로 12시간 이내입니다. 이는 `ORIGINAL` 레코드에 적용되며, 새 워크스페이스는 더 오래 걸릴 수 있다고 문서가 설명합니다. 보존 기간은 365일입니다. 문서 원문은 이 테이블이 리전과 무관하게 전 리전으로 집계된다고 설명합니다.

`system.billing.list_prices` 테이블도 있으며 보존 기간은 무기한으로 표기되어 있습니다. 이 페이지에서는 컬럼과 값을 확인하지 못했으므로 쓰지 않습니다.

### 사용량 대시보드

계정 관리자는 계정 콘솔의 **Usage** 탭에서 대시보드를 워크스페이스에 가져올 수 있습니다. 절차는 다음과 같습니다.

1. 계정 콘솔에서 **Usage** 탭을 엽니다.
2. **Setup dashboard** 를 클릭합니다.
3. 대시보드 버전을 고릅니다. **Usage Dashboard version 2.0 (Preview)** 또는 기본 버전입니다.
4. 범위를 계정 전체 또는 한 워크스페이스로 정합니다.
5. 대상 워크스페이스를 고르고 **Import** 를 클릭합니다.

가져온 대시보드는 다른 대시보드와 같이 수정하고 게시할 수 있습니다. 새 버전을 언제든 다시 가져올 수 있습니다.

| 버전 | 기본으로 보여주는 것 | 필요한 권한 |
|---|---|---|
| 기본 | 제품, SKU 이름, 사용자 정의 태그별 분해. 가장 비싼 사용량 원천 분석 | `system` 카탈로그 `USE CATALOG`, `system.billing` 스키마 `USE SCHEMA`, `system.billing.usage`와 `system.billing.list_prices` `SELECT` |
| 2.0 (Preview) | 기본 항목에 비용 예측과 객체 단위 드릴다운 추가 | 기본 권한에 더해 `system.access`, `system.compute`, `system.lakeflow`, `system.serving` 스키마 `USE SCHEMA`와 여러 테이블 `SELECT` |

> **참고** 사용량 대시보드의 **Consumption (Legacy)** 탭은 레거시 데이터를 담고 있으며, 문서는 청구 시스템 테이블을 권장합니다. 워크스페이스·SKU·태그 집계 옵션은 이 레거시 탭의 그래프에 있으며, 가져온 대시보드에는 없습니다.

### 예산 (Budgets)

예산은 지정한 범위의 지출을 추적하고 임계값에 도달하면 알립니다.

| 항목 | 문서 기준 |
|---|---|
| 측정 단위 | USD, SKU 정가 기준. 플랫폼 부가 기능 포함. 크레딧과 할인은 반영하지 않음 |
| 기본 범위 | 계정 전체 |
| 범위 축소 | 워크스페이스, 리소스 유형(**All** 또는 **Unity Gateway**), 사용자 정의 리소스 태그 |
| 임계값 | 예산당 공유 임계값 최대 4개. 각각 월별 금액을 고유하게 지정 |
| 알림 수신자 | 임계값마다 별도 이메일 목록. 목록이 비어 있으면 메일은 안 가지만 계정 콘솔에서는 보임 |
| 수신자 자격 | Databricks 사용자가 아니어도 됨 |
| 개수 한도 | 계정당 예산 최대 1,000개 |

Unity Gateway 예산에는 추가 기능이 있습니다. 사용자별 임계값(Per-user spend threshold)을 기본값 하나로 두고, 사용자나 그룹별 재정의를 줄 수 있습니다. 여러 그룹에 속한 사용자는 가장 높은 임계값이 적용됩니다.

**차단**(Block usage)은 Unity Gateway 예산에서만 쓸 수 있습니다. 공유 임계값 중 하나에서만 차단할 수 있고, 반드시 가장 높은 임계값이어야 합니다. 문서는 차단이 근사치로 동작하며, 사용자가 한도에 도달하기 전에 막히거나 차단 적용 전에 지출이 한도를 넘을 수 있다고 설명합니다. 진행 중인 요청은 중단되지 않으며, 절대적 지출 상한을 보장하지 않습니다.

예산 알림 메일은 사용량보다 최대 24시간 늦을 수 있습니다. Unity Gateway 알림은 거의 실시간입니다. `system.billing.usage`는 몇 시간마다 갱신되므로, 같은 시점의 수치가 메일이나 상세 페이지와 다를 수 있습니다.

예산 관리 권한은 예산 관리자(Budget Manager)와 예산 열람자(Budget Viewer) 역할을 사용자, 그룹, 서비스 프린시펄에 주는 방식으로 위임할 수 있습니다. 릴리즈 노트에 따르면 2026년 10월 16일 공개되었습니다.

### 태그 (Tags)

태그는 리소스와 사용량에 붙이는 키-값 쌍입니다. 사용량 기록의 `custom_tags`에 전파되어 비용을 귀속하는 데 쓰입니다. 어떤 리소스에 태그를 붙일 수 있는지와 전파 범위는 "Use tags to attribute and track usage" 페이지에서 확인하십시오. 이 페이지에서는 세부 한도 숫자를 쓰지 않습니다.

### 서버리스 사용량 정책 (Serverless usage policies)

서버리스 사용량 정책은 정책에 담긴 사용자 정의 태그를, 그 정책이 할당된 사용자가 만든 서버리스 컴퓨트 활동에 붙입니다. 태그는 청구 기록에 나타나므로, 예산과 부서별 귀속에 쓸 수 있습니다. 상태는 **Public Preview** 입니다.

| 항목 | 문서 기준 |
|---|---|
| 적용 대상 | 노트북, 잡, Lakeflow pipelines, Model Serving 엔드포인트, Lakebase Autoscaling 프로젝트, Databricks Apps |
| 적용 제외 | 클래식 컴퓨트 리소스에는 태그를 붙이지 않음 |
| 청구 반영 | 태그가 `system.billing.usage`의 `custom_tags` 컬럼에 전파됨 |
| 여러 정책 할당 | 사용자가 여러 정책을 받으면 리소스를 만들 때 하나를 고름. 고르지 않으면 이름 순서상 첫 번째 정책이 기본 |
| 잡 안의 노트북 | 잡으로 실행되는 노트북은 잡의 정책만 적용 |
| 잡이 트리거한 파이프라인 | 잡의 정책을 상속하지 않음 |
| 변경 적용 | 정책 변경은 변경 후 시작되는 사용량부터 적용 |

> **주의** 정책을 부여받았더라도 기존 자산에 정책이 자동으로 붙지는 않습니다. 소유자가 직접 설정해야 합니다. 잡 목록 UI에는 정책 태그가 보이지 않습니다.

### 서버리스 사용 비용 추적과 과다 지출 보호

서버리스 비용을 추적하는 기본 경로는 사용량 정책이 붙인 태그와 `system.billing.usage`를 함께 보는 것입니다. 노트북 페이지에는 **Serverless overspend protection** 항목이 있습니다. 이 페이지에서는 세부 동작을 확인하지 못했으므로 설명하지 않습니다. 필요하면 노트북 서버리스 설정 페이지에서 원문을 확인하십시오.

### 거버넌스 허브 비용 (Beta)

거버넌스 허브(Governance Hub)에 비용 페이지가 있으며 상태는 **Beta** 입니다. 문서 목록에서는 "Drill-down into costs with Governance Hub"로 소개됩니다.

## 3. 어떻게 쓰는가

### 태그별 월간 사용량 집계

`custom_tags`는 맵 타입이므로, 키를 꺼내 집계할 때는 맵 접근 구문을 씁니다. 아래 쿼리는 `team`이라는 태그 키를 가정합니다. 실제 키 이름은 본인 환경의 태그 정책에 맞춰 바꾸십시오.

```sql
SELECT
  date_trunc('MONTH', usage_date) AS usage_month,
  custom_tags['team'] AS team,
  sku_name,
  SUM(usage_quantity) AS total_usage
FROM system.billing.usage
WHERE usage_date >= add_months(current_date(), -3)
GROUP BY ALL
ORDER BY usage_month DESC, total_usage DESC;
```

> **참고** 위 쿼리는 단위를 합산합니다. `usage_unit`이 여러 종류일 수 있으므로, 단위별로 나눠 보려면 `usage_unit`을 `GROUP BY`에 추가하십시오. 단가를 곱한 금액은 이 쿼리로 계산하지 않습니다.

### 서버리스 사용량 정책 만들기

정책은 사용자 정의 태그 집합이며, 정책이 할당된 사용자가 만든 서버리스 활동에 태그가 붙습니다. 정책을 만들고 사용자에게 할당하는 구체 절차는 "Attribute usage with serverless usage policies" 페이지를 따르십시오. 이 장에서는 설정 화면이나 명령을 확인하지 못했으므로 예시를 쓰지 않습니다.

### 예산 설정 흐름

1. 계정 콘솔에서 예산을 만들고 범위(전체, 워크스페이스, 태그)를 정합니다.
2. 임계값을 정하고, 각 임계값에 알림 수신자를 넣습니다.
3. Unity Gateway 사용량을 제한하려면 임계값에 **Block usage** 를 체크합니다.
4. 예산 상세 페이지에서 누적 지출과 임계선을 확인합니다.

## 4. 트레이드오프

| 도구 | 적합한 용도 | 한계 |
|---|---|---|
| 사용량 대시보드 | 전체 추세와 가장 비싼 원천 확인 | 청구 데이터 갱신 지연. 레거시 탭은 권장하지 않음 |
| 예산 | 임계값 알림과 Unity Gateway 차단 | 차단은 Unity Gateway에서만. 절대 상한 보장 없음. 메일 지연 최대 24시간 |
| 태그 | 팀과 프로젝트 귀속 | 태그를 빠뜨리면 귀속되지 않음. 태그 체계를 먼저 정해야 함 |
| 서버리스 사용량 정책 | 서버리스 사용량에 태그를 자동 부여 | Public Preview. 클래식 컴퓨트에는 적용되지 않음 |
| 시스템 테이블 직접 조회 | 원하는 기준으로 자유롭게 집계 | SQL 작성과 권한 관리 필요 |

## 5. 주의사항

- **클래식과 서버리스를 같은 방식으로 귀속하지 마십시오.** 클래식 컴퓨트는 클러스터 태그로, 서버리스는 사용량 정책 태그로 귀속하는 것이 문서의 구조입니다. 사용량 정책은 클래식에 적용되지 않습니다.
- **예산 금액은 정가 기준임을 기억하십시오.** 크레딧과 할인이 있으면 실제 청구와 차이가 날 수 있습니다.
- **정책과 태그 변경은 과거 사용량에 소급되지 않습니다.** 변경 시점 이후의 사용량부터 반영됩니다.
- **잡이 실행하는 파이프라인은 잡의 정책을 상속하지 않습니다.** 파이프라인 자체에 정책을 붙이거나, 파이프라인 사용량 귀속을 따로 설계하십시오.
- **차단은 최후의 수단으로 쓰십시오.** 문서가 근사치 동작과 상한 미보장을 명시하므로, 예산 차단만으로 지출 상한을 가정하면 안 됩니다.
- **단가는 가격 페이지에서 확인하십시오.** 이 장과 비용 구조 페이지는 단가를 다루지 않습니다.

## 참고 문서

- [Cost management](https://docs.databricks.com/aws/en/admin/usage/)
- [Usage dashboards](https://docs.databricks.com/aws/en/admin/account-settings/usage)
- [Create and monitor budgets](https://docs.databricks.com/aws/en/admin/account-settings/budgets)
- [Use tags to attribute and track usage](https://docs.databricks.com/aws/en/admin/account-settings/usage-detail-tags)
- [Attribute usage with serverless usage policies](https://docs.databricks.com/aws/en/admin/usage/budget-policies)
- [Monitor costs with system tables](https://docs.databricks.com/aws/en/admin/usage/system-tables)
- [Billing system table](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
