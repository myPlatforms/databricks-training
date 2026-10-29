# 스트리밍 테이블과 구체화된 뷰

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 한눈에 보기

Lakeflow 파이프라인(Lakeflow pipelines)은 **무엇을 만들지** 만 선언하면 실행 순서, 증분 처리, 의존성을 엔진이 관리하는 방식입니다. 공식 문서는 이 제품을 "Spark Declarative Pipelines on Lakeflow"라는 제목으로 소개하며, 본문에서는 Lakeflow 파이프라인이 Apache Spark Declarative Pipelines와 호환된다고 설명합니다. 이전 이름인 Delta Live Tables(DLT)는 공식 문서가 별도 페이지로 설명하는 구 명칭입니다. 이 페이지는 파이프라인의 세 가지 핵심 개념인 **흐름(flow)**, **스트리밍 테이블(streaming table)**, **구체화된 뷰(materialized view)** 를 다룹니다.

## 왜 필요한가

증분 ETL을 직접 짜면 다음 작업을 매번 반복해야 합니다.

- 마지막으로 처리한 위치를 기록하고, 이전 결과에 새 데이터만 추가하는 로직
- 테이블 간 실행 순서와 실패 시 재실행 범위 관리
- 쿼리를 바꿨을 때 이미 처리된 데이터를 어떻게 다시 계산할지 결정

선언형 파이프라인은 이 로직을 엔진에 맡깁니다. 사용자는 테이블과 변환 쿼리를 정의하고, 엔진은 업데이트 때마다 흐름을 실행합니다.

## 어떻게 동작하는가

### 핵심 개념

| 개념 | 문서 정의 요약 | 기본 흐름 |
|---|---|---|
| 흐름(flow) | 쿼리와 (보통) 대상을 가진 단위. 배치로 또는 스트림으로 증분 실행. 파이프라인이 업데이트될 때마다 실행되어 증분으로 갱신하거나 원천을 전부 다시 처리 | 스트리밍 테이블과 구체화된 뷰마다 같은 이름의 append flow가 기본으로 생김 |
| 스트리밍 테이블 | 증분 처리 기능이 추가된 Delta 테이블. 하나 이상의 흐름이 대상으로 삼을 수 있음 | 원천 행을 한 번만 처리하고 추가 |
| 구체화된 뷰 | 쿼리 결과를 캐시한 객체. 조회할 때마다 재계산하는 일반 뷰와 달리 지정한 주기나 트리거로 갱신 | 가능한 경우 증분으로 갱신, 일부 변경은 전체 재계산 |

### 흐름 종류

문서가 설명하는 흐름 유형은 다음과 같습니다.

| 유형 | 설명 | 상태 |
|---|---|---|
| Append flow | 가장 흔한 유형. 업데이트마다 새 원천 레코드를 대상에 추가. Structured Streaming의 append 모드와 같음. 하나의 대상에 여러 append flow 가능 | 문서에 상태 라벨 없음 |
| ONCE 플래그 | append flow에 붙여 "데이터를 한 번만 넣는" 배치 쿼리로 표시. 전체 새로 고침 전까지 다시 넣지 않음 | 문서에 상태 라벨 없음 |
| AUTO CDC flow | 변경 데이터 캡처(CDC) 데이터를 반영. 이전 이름은 "apply changes". 하나의 스트리밍 테이블에 여러 AUTO CDC 흐름 가능 | 상세는 [Expectations와 AUTO CDC](pipelines-expectations-and-cdc.md) 참고 |
| Update flow | 전역 비워터마크 스트리밍 집계를 싱크로 출력. 각 배치에서 바뀐 레코드만 출력 | **Public Preview**. Python에서만 사용 가능 |

> **참고** 문서는 Backfill(과거 데이터 채우기)을 별도로 정의된 흐름의 사용 사례로 소개하고 "Backfilling historical data with pipelines" 항목으로 연결합니다. 세부 구문은 이 페이지에서 다루지 않습니다.

### 파이프라인 종류 표기

| 파이프라인 유형 | 의미 |
|---|---|
| `ETL` | 파이프라인 안에 정의된 스트리밍 테이블과 구체화된 뷰 |
| `MV/ST` | 독립형(standalone) 스트리밍 테이블·구체화된 뷰. Databricks가 이를 갱신하는 파이프라인을 자동으로 만듦 |

Jobs & Pipelines 목록의 "Pipeline type" 열에서 확인할 수 있습니다.

## 어떻게 쓰는가

### 스트리밍 테이블 (SQL)

스트리밍 테이블은 스트리밍 쿼리로 정의합니다. 원천 참조에는 `STREAM` 키워드를 씁니다. 문서의 최소 예시를 옮겼습니다.

```sql
CREATE OR REFRESH STREAMING TABLE customers_silver
AS SELECT * FROM STREAM(customers_bronze)
```

파일을 바로 읽을 때는 `read_files`를 스트림으로 씁니다. 문서는 다음 형태를 제시합니다. 경로와 옵션은 예시값입니다.

```sql
SELECT * FROM STREAM read_files("/databricks-datasets/retail-org/customers/*", format => "csv")
```

`CREATE OR REFRESH STREAMING TABLE`의 전체 문법은 다음 절을 가집니다. 문서가 제시한 구조입니다.

- 컬럼 목록(`table_specification`): 컬럼 이름과 타입, `COMMENT`, `GENERATED ALWAYS AS (expr)`
- 테이블 절: `PARTITIONED BY`, `CLUSTER BY`, `TBLPROPERTIES`, `LOCATION`
- 원천: `AS query`. 문서는 "This query must be a streaming query."라고 명시

### 스트리밍 테이블 (Python)

Python에서는 빈 스트리밍 테이블을 만든 뒤 흐름을 추가하는 방식이 문서 예제에 나옵니다. 아래 코드는 AUTO CDC 튜토리얼에서 가져온 구조이며, 스트리밍 원천을 읽는 뷰와 테이블 생성 호출을 보여 줍니다.

```python
from pyspark import pipelines as dp

@dp.view
def users():
  return spark.readStream.table("main.cdc_tutorial.users_cdf")

dp.create_streaming_table("users_history")
```

### 구체화된 뷰 (Python)

문서의 예제입니다. 두 테이블을 조인한 결과를 구체화된 뷰로 정의합니다.

```python
from pyspark import pipelines as dp

@dp.materialized_view
def regional_sales():
  partners_df = spark.read.table("partners")
  sales_df = spark.read.table("sales")
  return (
    partners_df.join(sales_df, on="partner_id", how="inner")
  )
```

### 구체화된 뷰 (SQL)

문서는 SQL에서 `CREATE OR REPLACE MATERIALIZED VIEW`를 사용합니다.

```sql
CREATE OR REPLACE MATERIALIZED VIEW regional_sales
  AS SELECT *
  FROM partners
    INNER JOIN sales USING (partner_id);
```

> **참고** 스트리밍 테이블 예시는 `CREATE OR REFRESH`, 구체화된 뷰 예시는 `CREATE OR REPLACE`를 씁니다. 두 구문 모두 공식 문서 예시에 나오지만 표기가 다르므로, 팀 코드 스타일을 정할 때 참고 문서의 현재 구문을 함께 확인하십시오.

## 선택 기준: 스트리밍 테이블 대 구체화된 뷰

| 기준 | 스트리밍 테이블 | 구체화된 뷰 |
|---|---|---|
| 데이터 특성 | 추가만 되는 대용량 데이터, 행을 한 번만 처리 | 집계·조인 결과 |
| 조인 정확성 | 조인은 차원 데이터가 바뀌어도 다시 계산하지 않음 | 차원이 바뀌면 조인을 자동으로 다시 계산 (문서: "always correct") |
| 지연 | 저지연 스트리밍 변환에 적합 | 초 단위 또는 분 단위 갱신. 저지연 요구에는 맞지 않음 |
| 늦게 도착한 데이터 | 워터마크 설계가 필요 | 업데이트 시점에 정확하게 반영 |
| 쿼리 변경 후 | 변경 이전에 처리된 행은 그대로. 전체 새로 고침 필요 | 쿼리 결과가 다시 계산됨 |

문서 원문 표현으로는 "Materialized views are always correct because they automatically recompute joins when dimensions change"입니다.

## 트레이드오프

| 항목 | 스트리밍 테이블 | 구체화된 뷰 |
|---|---|---|
| 증분 방식 | 새 행만 추가 | 가능한 경우 증분, 일부 변경은 전체 재계산 |
| 비용 | 원천 증가분만 처리 | 재계산 범위에 따라 비용 증가 |
| 소유 | 하나의 파이프라인만 갱신 가능 | 파이프라인이 갱신 |
| 복잡도 | 원천이 변하거나 삭제되면 `AUTO CDC`가 필요 | 쿼리 결과 중심 |

## 주의사항

- **전체 새로 고침**: 전체 새로 고침(full refresh)은 원천 전체를 다시 읽어 모든 행을 갱신합니다. 쿼리를 바꾼 뒤 과거 행에도 반영하려면 필요하지만, 비용이 큽니다.
- **UDF 변경**: 구체화된 뷰에서 사용하는 UDF의 동작이 바뀌었는데 Databricks가 이를 감지하지 못하는 경우(예: 라이브러리 업그레이드)에는 사용자가 전체 새로 고침을 직접 해야 한다고 문서가 설명합니다.
- **무한 스트림과 워터마크**: 스트리밍 테이블이 무한 스트림을 워터마크 없이 상태 집계하면 메모리 압박으로 실패할 수 있습니다. 원천이 유한하거나 워터마크로 제한하십시오.
- **조인의 한계**: 스트리밍 테이블은 조인 상대 차원이 나중에 바뀌어도 과거 결과를 다시 계산하지 않습니다. 차원 변경을 반영해야 하면 구체화된 뷰가 맞습니다.
- **CLONE 불가**: 스트리밍 테이블은 deep·shallow clone의 원본이나 대상으로 쓸 수 없다고 문서가 명시합니다.
- **REFRESH 권한**: 관리자가 아닌 사용자가 스트리밍 테이블을 보려면 해당 테이블에 `REFRESH` 권한과 파이프라인 권한이 필요합니다.
- **저지연**: 밀리초 단위 엔드투엔드 지연이 필요하면 문서는 실시간 모드(real-time mode)를 안내합니다. [Structured Streaming 기초](structured-streaming-basics.md) 참고.
- **네이밍**: 원천 노트북을 바꾸면서 테이블 이름을 같이 바꾸면 기존 테이블과의 연속성이 끊깁니다. 이름 변경 전 영향 범위를 확인하십시오.

## 참고 문서

- [Spark Declarative Pipelines on Lakeflow](https://docs.databricks.com/aws/en/ldp/)
- [Pipeline concepts (flows, streaming tables, materialized views)](https://docs.databricks.com/aws/en/ldp/concepts/)
- [Flows in Lakeflow pipelines](https://docs.databricks.com/aws/en/ldp/concepts/flows)
- [Streaming tables](https://docs.databricks.com/aws/en/ldp/concepts/streaming-tables)
- [Materialized views](https://docs.databricks.com/aws/en/ldp/concepts/materialized-views)
- [CREATE STREAMING TABLE (SQL)](https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-streaming-table)
- [Lakeflow 파이프라인 튜토리얼 (tutorial-get-started)](https://docs.databricks.com/aws/en/ldp/tutorial-get-started)
- [What happened to Delta Live Tables (DLT)?](https://docs.databricks.com/aws/en/ldp/concepts/where-is-dlt)
