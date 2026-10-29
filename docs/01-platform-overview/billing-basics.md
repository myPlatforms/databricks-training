# 과금 모델 기초

> 기준일: 2026-10-28 · 근거: 공식 문서

> **참고** 이 페이지는 ** 단가(가격 숫자)를 다루지 않습니다.** 단가는 리전, 가격 기준 시점, Edition, 계약 조건에 따라 달라지므로 공식 가격 페이지(`databricks.com/product/pricing`)에서 확인하십시오. 여기서는 과금이 ** 어떤 단위로 계산되고 어디서 확인하는지** 만 정리합니다.

## 한눈에 보기

Databricks 사용 비용은 **DBU(Databricks Unit)** 라는 처리 단위를 기준으로 계산됩니다. 공식 용어 정의는 다음과 같습니다.

> DBU (Databricks unit): units of processing capability per hour based on VM instance type.

즉, DBU는 **인스턴스 유형에 따른 시간당 처리 능력의 단위** 입니다. 사용량은 DBU 수량(`usage_quantity`)과 SKU(Stock Keeping Unit, 청구 품목) 이름으로 기록되고, 이 기록은 `system.billing.usage` 시스템 테이블에서 조회합니다.

| 개념 | 설명 |
|---|---|
| DBU | 시간당 처리 능력의 단위입니다. 청구의 기본 단위입니다. |
| SKU | 청구 품목 이름입니다. 같은 제품도 컴퓨트 유형에 따라 다른 SKU로 청구될 수 있습니다. |
| `usage_quantity` | 한 레코드에서 소비한 단위 수량입니다. |
| `usage_unit` | 사용량을 재는 단위입니다. DBU 사용량은 `usage_unit = 'DBU'`로 기록됩니다. |
| `system.billing.usage` | 사용량 레코드가 쌓이는 시스템 테이블입니다. |

## 1. 왜 DBU라는 단위를 쓰는가

클라우드 자원은 VM, 디스크, 네트워크처럼 여러 항목으로 나뉩니다. 플랫폼 기능마다 이 자원을 조합하는 방식도 다릅니다. 그래서 Databricks는 기능과 워크로드를 하나의 처리 단위로 통일해 측정합니다. 고객은 "작업 한 번에 DBU가 얼마나 들었는가"를 기준으로 비교할 수 있습니다.

> **참고** 공식 문서는 DBU를 "인스턴스 유형에 따른 시간당 처리 능력"으로 정의합니다. 같은 DBU라도 클라우드 인스턴스 자체의 비용은 별도 항목일 수 있으므로, 비용 추정은 DBU만 보지 말고 실행 환경을 함께 보십시오(아래 2절 참고).

## 2. 서버리스와 클래식의 과금 구조

공식 문서는 서버리스와 클래식의 과금 구조를 비교 표로 설명하지 않습니다. 이 페이지는 공식 문서에서 확인한 문장만 근거로 정리하고, 확인되지 않은 부분은 "문서에 명시 없음"으로 표기합니다.

| 항목 | 서버리스 컴퓨트 | 클래식 컴퓨트 |
|---|---|---|
| 사용량 기록 | `system.billing.usage`에 DBU 단위로 기록됩니다. 공식 서버리스 문서는 서버리스 사용량 조회 시 `usage_unit = 'DBU'`와 SKU 이름에 `SERVERLESS`가 포함되는 조건을 사용합니다. | 같은 시스템 테이블에 기록되지만, 공식 컴퓨트 문서는 클래식 청구 구조를 설명하지 않습니다. |
| 한 워크로드의 DBU 합계 | 문서는 한 잡 실행의 시간대별 DBU를 합하면 그 실행의 시간당 DBU 소비량이 된다고 설명합니다. | 문서에 명시 없음 (이 페이지에서 확인한 범위) |
| 클라우드 인프라 비용 | 문서에 명시 없음. 서버리스 컴퓨트는 Databricks 계정 안의 컴퓨트 레이어에서 실행된다고 아키텍처 문서가 설명합니다. | 클래식 컴퓨트는 고객 클라우드 계정의 VM에서 실행됩니다(아키텍처 문서). 이 인스턴스 비용이 DBU 청구와 별도로 발생하는지는 이 페이지의 확인 범위에서 명시되지 않았습니다. 가격 페이지와 계약 조건에서 확인하십시오. |
| 비용 추정 방법 | 공식 문서는 대표 워크로드를 실행해 벤치마크한 뒤 `system.billing.usage`를 확인하라고 권장합니다. | 같은 방식을 권장합니다. |

> **주의** 클래식 컴퓨트의 비용 구조(인스턴스·디스크·DBU 포함 여부)를 한 문장으로 단정하지 마십시오. 이 페이지에서 확인한 공식 문서 범위에는 그 청구 구조가 명시되어 있지 않습니다. 견적이나 비교표를 만들 때는 대상 클라우드의 가격 문서를 직접 확인하고 근거 링크를 붙이십시오.

> **참고** 서버리스 과금에는 **DBU 청구 외 항목이 포함되는지** 에 대한 혼동이 많습니다. 공식 서버리스 과금 문서는 데이터 품질 모니터링(data quality monitoring), 예측 최적화(predictive optimization), AI Search 같은 기능이 서버리스 잡 SKU(serverless jobs SKU)로 청구된다고 설명합니다. 즉, 노트북·잡·파이프라인 외 기능도 SKU 이름을 따로 확인해야 합니다.

## 3. 사용량 조회: `system.billing.usage`

시스템 테이블(system table)은 Databricks가 `system` 카탈로그에 제공하는 테이블이고, 청구 테이블은 계정의 사용량 레코드를 담습니다. 공식 문서 기준으로 다음 열을 중심으로 봅니다.

| 열 | 의미 |
|---|---|
| `record_id` | 레코드의 고유 ID입니다. |
| `account_id`, `workspace_id` | 계정과 워크스페이스 식별자입니다. 식별자는 공유 문서에 넣지 마십시오. |
| `sku_name` | 청구 SKU 이름입니다. |
| `cloud` | 클라우드 종류(`AWS`, `AZURE`, `GCP`)입니다. |
| `usage_start_time`, `usage_end_time`, `usage_date` | 사용 시각(UTC)과 날짜입니다. |
| `usage_unit`, `usage_quantity` | 단위와 수량입니다. |
| `billing_origin_product` | 사용량을 일으킨 제품입니다. 예: `JOBS`, `DLT`, `SQL`, `ALL_PURPOSE`, `MODEL_SERVING`, `LAKEBASE`, `APPS` 등. |
| `usage_metadata`, `identity_metadata` | 리소스와 신원에 관한 구조체(struct) 정보입니다. |
| `product_features` | 티어·서버리스 여부 등 기능 세부 정보입니다. |
| `record_type` | `ORIGINAL`, `RETRACTION`, `RESTATEMENT` 중 하나입니다. |

### 쿼리 예시

아래 쿼리는 최근 7일의 DBU 사용량을 날짜·제품·SKU별로 합산합니다. 열 이름은 위 표의 공식 열 이름과 같습니다.

```sql
-- 최근 7일 DBU 사용량 합계 (날짜, 제품, SKU별)
SELECT
  usage_date,
  billing_origin_product,
  sku_name,
  SUM(usage_quantity) AS dbu_total
FROM system.billing.usage
WHERE usage_unit = 'DBU'
  AND usage_date >= DATE_SUB(CURRENT_DATE(), 7)
GROUP BY usage_date, billing_origin_product, sku_name
ORDER BY usage_date DESC, dbu_total DESC;
```

> **주의** `record_type`을 고려하지 않으면 정정 레코드가 합계에 섞일 수 있습니다. 공식 문서는 `RETRACTION`이 원래 레코드를 상쇄하고, `RESTATEMENT`가 정정된 값을 담는다고 설명합니다. 정확한 합계가 필요하면 원문 명세를 확인해 필터 조건을 정하십시오.

> **주의** 사용량 레코드는 지연되어 나타날 수 있습니다. 공식 문서는 빌링 테이블의 레코드가 보통 12시간 안에 제공된다고 설명하고, 서버리스 문서는 워크로드 실행 후 최대 24시간의 지연이 있을 수 있다고 설명합니다. 두 문장은 같은 조건을 말하지 않으므로, 실시간 모니터링 용도로 쓰지 마십시오.

## 4. 어떤 값이 청구에 영향을 주는가

| 요인 | 영향 |
|---|---|
| 워크로드 실행 시간 | 실행 시간이 길수록 사용량이 늘어납니다. |
| 컴퓨트 종류 | 서버리스와 클래식은 과금 구조와 SKU가 다릅니다. |
| 제품 기능 | 같은 컴퓨트라도 기능별로 SKU가 나뉠 수 있습니다. |
| 자동 종료 설정 | 유휴 컴퓨트를 방치하면 DBU가 계속 쌓입니다. 자동 종료 설정은 03장에서 다룹니다. |
| 태그 | 공식 클래식 컴퓨트 문서는 풀(pool)에서 시작한 컴퓨트의 커스텀 태그가 DBU 사용 보고서에만 적용되고 클라우드 리소스로 전파되지 않는다고 설명합니다. 비용 귀속을 볼 때 이 차이를 기억하십시오. |

> **참고** 태그 설명은 클래식 컴퓨트 구성 문서의 설명입니다. 태그를 비용 배분의 근거로 쓰기 전에 공식 태그 문서를 함께 확인하십시오.

## 5. 트레이드오프

| 관점 | 서버리스 | 클래식 |
|---|---|---|
| 운영 부담 | 낮습니다. 인스턴스 설정을 직접 하지 않습니다. | 높습니다. 클러스터 구성과 종료 정책을 직접 관리합니다. |
| 비용 예측 | 워크로드를 벤치마크해 DBU 기준으로 추정하기 쉽습니다. | 인스턴스 비용을 포함해 따로 추정해야 합니다(공식 가격 문서 확인 필요). |
| 비용 통제 | 실행 단위로 비용을 보기 쉽습니다. | 클러스터 정책과 종료 설정으로 통제합니다. |

> **참고** 어느 쪽이 싸다고 일반화하지 마십시오. 워크로드 크기, 실행 시간, 인스턴스 할인 조건에 따라 결과가 달라집니다. 같은 워크로드를 두 방식으로 실행해 `system.billing.usage`와 클라우드 청구 내역을 함께 비교하는 것이 가장 확실합니다.

## 6. 주의사항

> **주의** 단가 숫자를 교육 자료나 보고서에 옮기기 전에, 리전·기준일·Edition을 함께 적고 공식 가격 페이지에서 다시 확인하십시오. 가격은 자주 바뀝니다.

> **주의** 무료 체험(free trial)과 Free Edition은 과금 조건이 다릅니다. 체험 기간의 크레딧과 한도는 [시작하기](getting-started.md)에서 정리합니다.

> **참고** 비용을 줄이는 구체적인 설계는 12장에서 다룹니다. 이 페이지는 측정 단위와 조회 방법까지만 다룹니다.

## 다음으로 읽을 페이지

과금 단위를 알았으면 처음 시작하는 방법을 [시작하기](getting-started.md)에서 확인합니다. 무료로 체험할 수 있는 범위도 그 페이지에서 다룹니다.

## 참고 문서

- [Billable usage system table](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Monitor the cost of serverless compute](https://docs.databricks.com/aws/en/admin/system-tables/serverless-billing)
- [Serverless compute](https://docs.databricks.com/aws/en/compute/serverless/)
- [Concepts (DBU 정의)](https://docs.databricks.com/aws/en/getting-started/concepts)
- [Compute](https://docs.databricks.com/aws/en/compute/)
- [Databricks 가격 페이지](https://databricks.com/product/pricing)
