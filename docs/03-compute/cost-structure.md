# 비용 구조 비교

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 컴퓨트 유형별로 비용이 어떤 구성 요소로 나뉘어 청구되는지 구조만 비교합니다. 단가 숫자는 다루지 않습니다. 단가는 리전, 플랜, 계약에 따라 달라지므로 Databricks 공식 가격 페이지에서 확인하십시오. 이 페이지의 목적은 "같은 워크로드라도 어떤 항목이 청구되는가"를 이해하는 것입니다.

## 1. 왜 필요한가

컴퓨트 비용을 비교할 때 가장 흔한 실수는 DBU 단가만 보고 판단하는 것입니다. Databricks 청구는 보통 두 부분으로 나뉩니다.

- **DBU(Databricks Unit)**: Databricks 플랫폼 사용량 단위입니다.
- **클라우드 인프라 요금**: 가상 머신, 디스크, 네트워크 등 클라우드 제공자가 청구하는 비용입니다.

어떤 컴퓨트가 이 두 부분을 어떻게 나눠 청구하는지 알아야 "DBU 단가가 낮은데 총액이 높은" 상황을 설명할 수 있습니다.

## 2. 어떻게 동작하는가

### 2.1 유형별 청구 구조

| 컴퓨트 | DBU 청구 | 클라우드 인스턴스 청구 | 근거 (문서 설명) |
|---|---|---|---|
| 서버리스 컴퓨트 (노트북·Job·파이프라인) | 사용량 기준 DBU | 문서에서 명시 확인 못 함 | 컴퓨트 레이어가 Databricks 계정 안에서 실행. 사용량은 DBU 단위로 측정 |
| 클래식 컴퓨트 (올-퍼포즈·Job·파이프라인) | 사용량 기준 DBU | 고객 클라우드 계정에 별도 청구 | 클래식 컴퓨트 리소스는 고객 AWS 계정에서 실행. 풀 문서는 인스턴스 제공자 청구가 적용된다고 설명 |
| 서버리스 SQL 웨어하우스 | 사용량 기준 DBU | 문서에서 명시 확인 못 함 | 컴퓨트 레이어가 Databricks 계정 안에서 실행 |
| Pro·Classic SQL 웨어하우스 | 사용량 기준 DBU | 고객 AWS 계정에 별도 청구 (위치 설명에서 추론) | 컴퓨트 레이어가 고객 AWS 계정에 존재 |

> **참고** 위 표에서 "문서에서 명시 확인 못 함"은 이 장에서 연 공식 페이지가 해당 질문에 직접 답하지 않았다는 뜻입니다. 서버리스 청구에 인프라 요금이 포함되는지 여부는 공식 가격 페이지나 청구 문서에서 따로 확인하십시오. 또 다른 자료에서 특정 클라우드의 서버리스 인프라 포함 여부를 단정하는 설명을 보더라도, 이 장은 그 설명을 근거로 쓰지 않았습니다.

> **주의** Pro·Classic 행의 클라우드 청구 설명은 "컴퓨트가 고객 계정에서 실행된다"는 위치 설명에서 추론한 것입니다. 청구 세부 구조는 워크스페이스 청구 내역과 공식 가격 페이지로 확인하십시오.

### 2.2 DBU 소비율이 달라지는 경우

같은 컴퓨트라도 설정에 따라 DBU 소비가 달라집니다. 이 장에서 확인한 문서 근거는 다음과 같습니다.

| 설정 | 문서 설명 |
|---|---|
| 서버리스 Job 성능 모드 Standard | 같은 SKU를 쓰지만 Standard 모드는 DBU를 더 적게 소비한다고 문서가 설명 |
| Photon 인스턴스 유형 | 같은 인스턴스 유형의 Photon이 아닌 런타임과 다른 DBU 비율로 소비 |
| 풀의 유휴 인스턴스 | 풀에서 대기 중인 인스턴스에는 DBU가 청구되지 않지만 인스턴스 제공자 청구는 적용 |

### 2.3 청구 SKU와 기능

문서는 일부 기능이 서버리스 Job SKU로 청구된다고 명시합니다. 즉, 기능 이름과 청구 SKU 이름이 같지 않을 수 있습니다. 실제 청구 내역에서 SKU 이름으로 필터링할 때는 기능별 청구 SKU를 확인하십시오.

## 3. 청구 데이터 확인 방법

### 3.1 청구 시스템 테이블

Unity Catalog의 청구 시스템 테이블(`system.billing.usage`)에 사용량이 기록됩니다. 서버리스 사용량 모니터링 문서가 쓰는 주요 필드는 다음과 같습니다.

| 필드 | 설명 |
|---|---|
| `sku_name` | 청구 SKU 이름 |
| `billing_origin_product` | 청구 원천 제품 |
| `usage_unit` | 사용 단위. 서버리스 집계는 `DBU`로 필터링 |
| `usage_quantity` | 사용량 |
| `product_features.is_serverless` | 서버리스 여부 |
| `workspace_id` | 워크스페이스 ID. 계정 전체 사용량이 섞이므로 필터가 필요 |

`system.billing.list_prices`는 가격 정보를 담는 시스템 테이블입니다. 문서의 알림 쿼리는 사용 기간과 가격 유효 기간 범위로 두 테이블을 조인해 목록 비용을 계산합니다.

### 3.2 사용량 집계 예시

아래 쿼리는 DBU 사용량을 SKU와 날짜별로 집계하는 구조만 보여 줍니다. 값은 원본 테이블에서 확인하십시오. 워크스페이스 ID는 실제 값으로 바꾸되, 공개 문서에는 쓰지 마십시오.

```sql
-- DBU 사용량을 SKU와 날짜별로 집계합니다.
-- <WORKSPACE_ID>는 확인하려는 워크스페이스 ID로 바꾸십시오.
SELECT
  sku_name,
  billing_origin_product,
  CAST(usage_start_time AS DATE) AS usage_day,
  SUM(usage_quantity) AS dbus
FROM system.billing.usage
WHERE usage_unit = 'DBU'
  AND workspace_id = <WORKSPACE_ID>
GROUP BY sku_name, billing_origin_product, CAST(usage_start_time AS DATE)
ORDER BY usage_day, sku_name;
```

> **주의** 문서는 서버리스 사용량이 청구 시스템 테이블에 최대 24시간 뒤에 나타날 수 있다고 설명합니다. 방금 실행한 Job의 비용을 바로 확인하려고 하면 값이 비어 보일 수 있습니다.

### 3.3 비용 점검 순서

1. 워크로드를 컴퓨트 유형(서버리스, 클래식, SQL 웨어하우스)으로 분류합니다.
2. DBU 집계를 SKU별로 확인합니다.
3. 클래식과 Pro·Classic 웨어하우스는 클라우드 청구 내역에서 인스턴스 요금을 따로 확인합니다.
4. 풀을 쓴다면 유휴 상태의 인스턴스 요금을 확인합니다. 유휴 DBU는 0이지만 클라우드 요금은 남습니다.
5. 공식 가격 페이지의 단가를 청구 기간에 맞춰 곱합니다. 이 장은 단가를 다루지 않습니다.

## 4. 트레이드오프

| 질문 | 구조상의 답 |
|---|---|
| DBU 단가만 비교하면 충분한가 | 아닙니다. 클래식과 Pro·Classic은 인스턴스 요금이 따로 붙습니다 |
| 유휴 시간의 비용은 어떻게 되는가 | 클래식 풀의 유휴 인스턴스는 DBU가 없지만 클라우드 요금은 나갑니다. 서버리스는 사용한 만큼 청구되는 구조입니다 |
| 성능 모드를 바꾸면 비용이 달라지는가 | 서버리스 Job의 Standard 모드는 DBU를 적게 소비한다고 문서가 설명합니다 |
| 같은 워크로드를 Photon으로 바꾸면 DBU가 어떻게 되는가 | DBU 소비율이 달라집니다. 실제 값은 가격 페이지와 측정으로 확인합니다 |

## 5. 주의사항

- **DBU와 인프라를 항상 함께 보십시오.** 클래식 비용 비교에서 한쪽만 보면 결론이 뒤집힐 수 있습니다.
- **청구 기간과 지연을 고려하십시오.** 서버리스 사용량은 최대 24시간 뒤에 반영됩니다.
- **워크스페이스 필터를 쓰십시오.** `system.billing.usage`는 계정 전체 사용량이므로 `workspace_id` 필터 없이 합산하면 다른 워크스페이스 값이 섞입니다.
- **단가는 공식 가격 페이지에서 확인하십시오.** 이 장과 블로그, 제3자 자료의 숫자를 그대로 옮기지 마십시오. 리전과 플랜에 따라 다릅니다.
- **풀 크기와 설정을 함께 점검하십시오.** 풀은 쓰지 않을 때도 클라우드 요금이 나갈 수 있습니다.

## 참고 문서

- [Serverless compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/)
- [서버리스 사용량 모니터링 (AWS)](https://docs.databricks.com/aws/en/admin/system-tables/serverless-billing)
- [청구 가능 사용량 시스템 테이블 레퍼런스 (AWS)](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Instance pools (AWS)](https://docs.databricks.com/aws/en/compute/pool-index)
- [Serverless 잡 실행 — 성능 모드 (AWS)](https://docs.databricks.com/aws/en/jobs/run-serverless-jobs)
- [Photon (AWS)](https://docs.databricks.com/aws/en/compute/photon)
- [High-level architecture (AWS)](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [SQL warehouse 유형 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)
