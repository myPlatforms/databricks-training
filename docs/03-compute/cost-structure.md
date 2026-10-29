# 비용 구조 비교

> 기준일: 2026-10-29 · 근거: 공식 문서

이 페이지는 컴퓨트 유형별로 비용이 어떤 구성 요소로 나뉘어 청구되는지, 그리고 그 사용량을 `system.billing.usage` 로 어떻게 조회하는지를 다룹니다. 단가 숫자는 다루지 않습니다. 단가는 리전, 플랜, 계약에 따라 달라지므로 [Databricks 공식 가격 페이지](https://www.databricks.com/product/pricing)에서 확인하십시오. 이 페이지의 목적은 "같은 워크로드라도 어떤 항목이 청구되는가"를 이해하고, 청구 데이터를 직접 집계하는 것입니다. 계정 단위의 예산·태그·알림 운영은 [비용 관리](../12-security-operations/cost-management.md)에서, 청구 개념의 기초는 [청구 기초](../01-platform-overview/billing-basics.md)에서 다룹니다.

## 1. 왜 필요한가

컴퓨트 비용을 비교할 때 가장 흔한 실수는 DBU 단가만 보고 판단하는 것입니다. Databricks 청구는 보통 두 부분으로 나뉩니다.

- **DBU(Databricks Unit)**: Databricks 플랫폼 사용량 단위입니다.
- **클라우드 인프라 요금**: 가상 머신, 디스크, 네트워크 등 클라우드 제공자가 청구하는 비용입니다.

어떤 컴퓨트가 이 두 부분을 어떻게 나눠 청구하는지 알아야 "DBU 단가가 낮은데 총액이 높은" 상황을 설명할 수 있습니다. 또 청구 내역은 SKU 이름으로 기록되므로, 기능 이름과 SKU 이름의 관계를 알아야 시스템 테이블을 올바르게 필터링할 수 있습니다.

## 2. 어떻게 동작하는가

### 2.1 유형별 청구 구조

| 컴퓨트 | DBU 청구 | 클라우드 인스턴스 청구 | 근거 (문서 설명) |
|---|---|---|---|
| 서버리스 컴퓨트 (노트북·Job·파이프라인) | 사용량 기준 DBU | 문서에서 명시 확인 못 함 | 컴퓨트 레이어가 Databricks 계정 안에서 실행. 사용량은 DBU 단위로 측정 |
| 클래식 컴퓨트 (올-퍼포즈·Job·파이프라인) | 사용량 기준 DBU | 고객 클라우드 계정에 별도 청구 | 클래식 컴퓨트 리소스는 고객 AWS 계정에서 실행. 풀 문서는 인스턴스 제공자 청구가 적용된다고 설명 |
| 서버리스 SQL 웨어하우스 | 사용량 기준 DBU | 문서에서 명시 확인 못 함 | 컴퓨트 레이어가 Databricks 계정 안에서 실행 |
| Pro·Classic SQL 웨어하우스 | 사용량 기준 DBU | 고객 AWS 계정에 별도 청구 (위치 설명에서 추론) | 컴퓨트 레이어가 고객 AWS 계정에 존재 |

> **참고** "문서에서 명시 확인 못 함"은 서버리스 개요, 서버리스 사용량 모니터링, 청구 시스템 테이블 레퍼런스, 사용량 모니터링 개요 페이지가 서버리스 청구에 인프라 요금이 포함되는지 여부를 직접 설명하지 않았다는 뜻입니다. 서버리스 개요 페이지는 비용 추정 방법으로 "대표 워크로드를 실행해 벤치마크한 뒤 청구 시스템 테이블을 분석"할 것을 권장할 뿐입니다. 포함 여부는 공식 가격 페이지나 계약 문서에서 따로 확인하십시오. 이 장은 특정 클라우드의 서버리스 청구 구성을 단정하지 않습니다.

> **주의** Pro·Classic 행의 클라우드 청구 설명은 "컴퓨트가 고객 계정에서 실행된다"는 위치 설명에서 추론한 것입니다. 청구 세부 구조는 워크스페이스 청구 내역과 공식 가격 페이지로 확인하십시오.

### 2.2 DBU 소비율이 달라지는 경우

같은 컴퓨트라도 설정에 따라 DBU 소비가 달라집니다.

| 설정 | 문서 설명 |
|---|---|
| 서버리스 Job 성능 모드 Standard | 같은 SKU를 쓰지만 Standard 모드는 DBU를 더 적게 소비한다고 문서가 설명 |
| Photon 인스턴스 유형 | 같은 인스턴스 유형의 Photon이 아닌 런타임과 다른 DBU 비율로 소비 |
| 풀의 유휴 인스턴스 | 풀에서 대기 중인 인스턴스에는 DBU가 청구되지 않지만 인스턴스 제공자 청구는 적용 |

### 2.3 청구 SKU와 기능

기능 이름과 청구 SKU 이름이 같지 않을 수 있습니다. 서버리스 개요 문서는 데이터 품질 모니터링(Data quality monitoring)과 예측 최적화(Predictive optimization)가 서버리스 인프라에서 실행되며 "서버리스 Job SKU로 청구된다"고 설명합니다. 청구 시스템 테이블에서는 `sku_name` 만으로 구분하기 어려운 경우를 위해 `billing_origin_product` 열이 있습니다. 레퍼런스는 "일부 제품은 같은 SKU로 청구된다"고 설명하며, 값의 예는 다음과 같습니다.

| `billing_origin_product` 값 (일부) | 의미 |
|---|---|
| `JOBS`, `DLT`, `SQL`, `ALL_PURPOSE` | Job, 파이프라인, SQL, 올-퍼포즈 컴퓨트 |
| `INTERACTIVE` | 서버리스 노트북 등 인터랙티브 사용 (서버리스 모니터링 문서의 예제에서 사용) |
| `MODEL_SERVING`, `VECTOR_SEARCH`, `ONLINE_TABLES` | 서빙, 벡터 검색, 온라인 테이블 |
| `LAKEHOUSE_MONITORING`, `PREDICTIVE_OPTIMIZATION` | 모니터링, 예측 최적화 |
| `LAKEFLOW_CONNECT`, `GENIE`, `APPS`, `LAKEBASE` 등 | 레퍼런스에 열거된 그 밖의 제품 (전체 목록은 레퍼런스 참조) |

## 3. 청구 데이터 확인 방법

### 3.1 청구 시스템 테이블

Unity Catalog의 `system.billing.usage` 에 계정의 청구 가능 사용량이 기록됩니다. 서버리스뿐 아니라 클래식 사용량도 같은 테이블에 들어갑니다. 레퍼런스가 설명하는 주요 열은 다음과 같습니다.

| 열 | 설명 (레퍼런스 기준) |
|---|---|
| `sku_name` | SKU 이름 (예: `STANDARD_ALL_PURPOSE_COMPUTE`) |
| `billing_origin_product` | 사용량을 일으킨 제품 |
| `usage_unit` | 사용 단위 (예: `DBU`) |
| `usage_quantity` | 해당 레코드에서 소비한 단위 수 |
| `usage_date` | 레코드 날짜. 날짜별 집계를 빠르게 하는 용도 |
| `usage_type` | 청구 목적의 사용 유형. `COMPUTE_TIME`, `STORAGE_SPACE`, `NETWORK_BYTE`, `TOKEN`, `GPU_TIME` 등 |
| `record_type` | `ORIGINAL`, `RETRACTION`, `RESTATEMENT` |
| `usage_metadata` | `cluster_id`, `job_id`, `warehouse_id`, `notebook_id`, `dlt_pipeline_id` 등 리소스 ID를 담은 구조체 |
| `identity_metadata` | `run_as`, `owned_by`(SQL 웨어하우스 전용), `created_by`(Apps·에이전트) 등 책임 주체 |
| `custom_tags` | 사용량에 붙은 사용자 정의 태그 (맵). 서버리스 사용 정책이 부여한 태그 포함 |
| `product_features` | `is_serverless`, `is_photon`, `performance_target`, `jobs_tier`, `sql_tier` 등 기능 세부 정보 |

`system.billing.list_prices` 는 SKU별 목록가를 담습니다. 열은 `account_id`, `sku_name`, `cloud`, `currency_code`, `usage_unit`, `price_start_time`, `price_end_time`, `pricing` 입니다. `pricing` 구조체의 `default` 는 단순한 장기 추정에 쓸 수 있는 단일 가격이고, `effective_list` 는 목록가와 프로모션 가격을 합쳐 해석한 값으로 비용 계산에 쓰입니다. 이 테이블은 SKU 가격이 바뀐 시점에만 레코드가 추가되므로, 특정 날짜의 가격은 그 날짜 이전의 가장 최근 변경 레코드를 찾아야 합니다. 레퍼런스는 이를 "목록가"로 설명하며 할인이나 협상 단가는 언급하지 않습니다. 따라서 이 테이블로 계산한 값은 실제 청구액이 아니라 목록가 기준 추정입니다.

### 3.2 보정 레코드 처리

`record_type` 때문에 단순 합계가 틀어질 수 있습니다. 레퍼런스에 따르면 `RETRACTION` 은 잘못된 원본 사용량을 상쇄하는 음수 `usage_quantity` 레코드이고, `RESTATEMENT` 는 정정된 레코드입니다. 정정 중에는 철회만 추가되고 재기재가 없는 경우도 있습니다. 합산하면 철회가 원본을 상쇄하므로, 레퍼런스의 예제는 시간대별로 합산한 뒤 0이 아닌 행만 남깁니다.

```sql
SELECT usage_metadata.job_id, usage_start_time, usage_end_time, SUM(usage_quantity) AS usage_quantity
FROM system.billing.usage
GROUP BY ALL
HAVING usage_quantity != 0
```

### 3.3 사용량 집계 예시

서버리스 사용량 모니터링 문서의 예제 패턴(`usage_unit = 'DBU'`, `usage_date` 범위 필터)을 따른 집계입니다. 열 이름은 모두 위 표에 있는 것입니다.

```sql
-- Daily DBU usage by SKU and product for the last 30 days
SELECT
  usage_date,
  sku_name,
  billing_origin_product,
  SUM(usage_quantity) AS total_dbu
FROM system.billing.usage
WHERE usage_unit = 'DBU'
  AND usage_date >= DATE_ADD(CURRENT_DATE(), -30)
GROUP BY usage_date, sku_name, billing_origin_product
ORDER BY usage_date, sku_name;
```

서버리스 문서의 다른 예제는 아래 조건으로 목적을 나눕니다. 각 예제는 모두 `usage_unit = 'DBU'` 와 최근 30일 `usage_date` 조건을 함께 씁니다.

| 목적 | 조건 (문서 예제 발췌) |
|---|---|
| 노트북별 지출 순위 | `usage_metadata.notebook_id IS NOT NULL AND billing_origin_product = 'INTERACTIVE' AND product_features.is_serverless` |
| Job별 지출 순위 | `usage_metadata.job_id IS NOT NULL AND sku_name LIKE '%JOBS_SERVERLESS_COMPUTE%'` |
| 사용자별 DBU | `identity_metadata.run_as = '<사용자 이메일>'` 및 `billing_origin_product IN ('JOBS','INTERACTIVE')` |
| 커스텀 태그별 DBU | `custom_tags.<key> = '<value>'` 및 `billing_origin_product IN ('JOBS','INTERACTIVE')` |
| 성능 모드별 DBU | `product_features.performance_target` 로 그룹화, `product_features.is_serverless` 및 `billing_origin_product IN ('JOBS','DLT')` |

> **참고** 서버리스 워크로드는 같은 시간대에 레코드가 여러 건 생길 수 있다고 문서가 설명합니다. 한 Job 실행의 시간당 DBU는 그 레코드들의 합입니다.

### 3.4 목록가 비용 환산

사용량에 `list_prices` 를 조인하면 목록가 기준 비용을 구할 수 있습니다. 아래는 사용 관리 문서의 태그별 월 비용 예제 구조입니다. `:key` 와 `:value` 는 쿼리 매개변수입니다.

```sql
SELECT SUM(usage.usage_quantity * list_prices.pricing.effective_list.default) AS `Total Dollar Cost`
FROM system.billing.usage
JOIN system.billing.list_prices ON list_prices.sku_name = usage.sku_name
WHERE usage.custom_tags [:key] = :value
  AND usage.usage_end_time >= list_prices.price_start_time
  AND (list_prices.price_end_time IS NULL OR usage.usage_end_time < list_prices.price_end_time)
  AND usage.usage_date BETWEEN "2025-05-01" AND "2025-05-31"
```

> **주의** 서버리스 모니터링 문서의 알림 쿼리는 `list_prices.pricing.default` 를, 사용 관리 문서의 위 예제는 `pricing.effective_list.default` 를 씁니다. 프로모션 가격이 있으면 두 값이 다를 수 있으므로, `list_prices` 레퍼런스의 정의대로 비용 계산에는 `effective_list` 를 쓰는 편이 안전합니다. 서버리스 모니터링 문서는 `cloud` 열도 조인 키로 사용합니다.

### 3.5 태그로 귀속하기

태그는 청구 레코드의 `custom_tags` 에 실립니다. 서버리스는 서버리스 사용 정책(Serverless usage policy, Public Preview)이 태그를 부여합니다. 문서가 설명하는 동작은 다음과 같습니다.

- 정책을 노트북, Job, 파이프라인, 앱에 적용하면 그 태그가 청구 레코드로 전파됩니다.
- 노트북이 Job의 일부로 실행되면 Job의 정책만 적용됩니다. Job이 트리거한 파이프라인은 Job의 정책을 상속하지 않습니다.
- 기존 노트북·Job·파이프라인에는 정책이 자동 적용되지 않아 소유자가 직접 설정해야 합니다.
- 정책은 클래식 컴퓨트에 태그를 달지 않으며, 태그 변경은 변경 이후 시작된 사용량에만 적용됩니다.

클래식 컴퓨트 태그와 컴퓨트 정책을 통한 강제는 [풀과 컴퓨트 정책](pools-and-policies.md)을 참고하십시오.

### 3.6 비용 점검 순서

1. 워크로드를 컴퓨트 유형(서버리스, 클래식, SQL 웨어하우스)으로 분류합니다.
2. DBU 집계를 `sku_name` 과 `billing_origin_product` 별로 확인합니다.
3. 클래식과 Pro·Classic 웨어하우스는 클라우드 청구 내역에서 인스턴스 요금을 따로 확인합니다.
4. 풀을 쓴다면 유휴 상태의 인스턴스 요금을 확인합니다. 유휴 DBU는 0이지만 클라우드 요금은 남습니다.
5. 공식 가격 페이지의 단가 또는 `list_prices` 로 목록가 기준 추정을 만들고, 계약 조건은 별도로 반영합니다.

## 4. 트레이드오프

| 질문 | 구조상의 답 |
|---|---|
| DBU 단가만 비교하면 충분한가 | 아닙니다. 클래식과 Pro·Classic은 인스턴스 요금이 따로 붙습니다 |
| 유휴 시간의 비용은 어떻게 되는가 | 클래식 풀의 유휴 인스턴스는 DBU가 없지만 클라우드 요금은 나갑니다. 서버리스 컴퓨트는 [서버리스 컴퓨트](serverless-compute.md) 페이지의 동작을 기준으로 판단합니다 |
| 성능 모드를 바꾸면 비용이 달라지는가 | 서버리스 Job의 Standard 모드는 DBU를 적게 소비한다고 문서가 설명합니다 |
| 같은 워크로드를 Photon으로 바꾸면 DBU가 어떻게 되는가 | DBU 소비율이 달라집니다. 실제 값은 가격 페이지와 측정으로 확인합니다 |
| `system.billing.usage` 만으로 총비용을 알 수 있는가 | 아닙니다. DBU 사용량과 목록가 환산만 나옵니다. 클라우드 인프라 요금은 클라우드 청구 내역에 있습니다 |

## 5. 주의사항

- **DBU와 인프라를 항상 함께 보십시오.** 클래식 비용 비교에서 한쪽만 보면 결론이 뒤집힐 수 있습니다.
- **반영 지연을 고려하십시오.** 청구 시스템 테이블 레퍼런스는 레코드가 "보통 12시간 이내"에 제공되며 신규 워크스페이스는 더 오래 걸릴 수 있다고 설명합니다. 서버리스 개요 페이지는 "최대 24시간 지연"이 있을 수 있다고 설명합니다. 두 표기가 다르므로 방금 실행한 작업의 비용이 비어 보여도 하루 정도는 기다려 보십시오.
- **보정 레코드를 무시하지 마십시오.** `RETRACTION` 이 있는 기간을 단순 필터로 `ORIGINAL` 만 합산하면 정정이 반영되지 않습니다.
- **계정 전체 데이터임을 기억하십시오.** `system.billing.usage` 는 계정의 사용량을 담으므로 특정 워크스페이스만 보려면 `workspace_id` 조건을 직접 추가해야 합니다. 값은 쿼리에서 매개변수로 받고 공개 자료에는 적지 마십시오.
- **`list_prices` 는 목록가입니다.** 협상 단가나 할인은 반영되지 않습니다.
- **단가는 공식 가격 페이지에서 확인하십시오.** 이 장과 블로그, 제3자 자료의 숫자를 그대로 옮기지 마십시오.
- **풀 크기와 설정을 함께 점검하십시오.** 풀은 쓰지 않을 때도 클라우드 요금이 나갈 수 있습니다.

## 참고 문서

- [Serverless compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/)
- [서버리스 사용량 모니터링 (AWS)](https://docs.databricks.com/aws/en/admin/system-tables/serverless-billing)
- [청구 가능 사용량 시스템 테이블 레퍼런스 (AWS)](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [가격 시스템 테이블 list_prices (AWS)](https://docs.databricks.com/aws/en/admin/system-tables/pricing)
- [사용량 모니터링 개요 (AWS)](https://docs.databricks.com/aws/en/admin/usage/)
- [시스템 테이블로 비용 모니터링 (AWS)](https://docs.databricks.com/aws/en/admin/usage/system-tables)
- [서버리스 사용 정책 (AWS)](https://docs.databricks.com/aws/en/admin/usage/budget-policies)
- [Instance pools (AWS)](https://docs.databricks.com/aws/en/compute/pool-index)
- [Serverless 잡 실행 — 성능 모드 (AWS)](https://docs.databricks.com/aws/en/jobs/run-serverless-jobs)
- [Photon (AWS)](https://docs.databricks.com/aws/en/compute/photon)
- [High-level architecture (AWS)](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [SQL warehouse 유형 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)
