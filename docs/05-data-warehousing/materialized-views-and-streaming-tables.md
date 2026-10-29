# 구체화 뷰와 스트리밍 테이블

> 기준일: 2026-10-28 · 근거: 공식 문서

구체화 뷰(Materialized view)와 스트리밍 테이블(Streaming table)은 SQL 문장으로 정의한 결과를 Delta 테이블로 저장하고, 원천이 바뀌면 갱신하는 객체입니다. Databricks SQL 문서는 두 객체를 **독립형(standalone) 구체화 뷰·스트리밍 테이블** 로 SQL 웨어하우스 또는 서버리스 범용 컴퓨트의 노트북에서 만들고 새로 고침한다고 설명합니다. 이 페이지는 두 객체의 구문, 새로 고침, 실행 주체, 상태를 정리합니다.

## 왜 필요한가

분석용 집계 테이블을 노트북이나 잡으로 매번 다시 계산하면, 실행 코드와 스케줄 관리가 따로 필요하고 중간 결과가 누락되거나 중복되기 쉽습니다. 구체화 뷰와 스트리밍 테이블은 "정의(SQL)와 결과(테이블)"를 한 객체로 묶어, 갱신 방식을 선언적으로 관리하게 합니다.

| 상황 | 적합한 객체 |
|---|---|
| 원천 전체를 기준으로 집계 결과를 주기적으로 맞춤 | 구체화 뷰 |
| 새로 들어오는 데이터만 점진적으로 처리 | 스트리밍 테이블 |
| 일반 뷰로 충분 (매번 원천을 읽어도 되는 경우) | 뷰 (구체화하지 않음) |

## 어떻게 동작하는가

### 실행 주체와 명칭

공식 문서는 다음을 밝힙니다.

- 독립형 객체는 Databricks SQL 웨어하우스나 서버리스 범용 컴퓨트의 노트북에서 만들고 새로 고칠 수 있습니다.
- 이 기능은 Lakeflow 파이프라인(Lakeflow pipelines)이 가장 흔한 구현 방식이며, 독립형 객체를 쓰면 Databricks가 그 밑의 파이프라인을 관리합니다.
- 이 영역은 예전에 "Pipelines for Databricks SQL"이라고 불렸으며, 서버리스 범용 컴퓨트 노트북 지원을 반영해 이름이 바뀌었습니다.
- 컴퓨트 옵션, 기능 지원, 리전 가용성은 "Requirements for standalone pipelines" 페이지에 있습니다. 이 페이지는 해당 목록을 다루지 않습니다.

> **참고** 엔진 명칭 원문은 "Lakeflow pipelines"이며, 같은 기능을 "Spark Declarative Pipelines on Lakeflow"로도 소개합니다. 이 장은 원문 표기 "Lakeflow 파이프라인(Lakeflow pipelines)"을 씁니다.

### 구체화 뷰

**구문 (문서 기준)**

```
{ CREATE OR REPLACE MATERIALIZED VIEW | CREATE MATERIALIZED VIEW [ IF NOT EXISTS ] }
  view_name [ column_list ]
  [ view_clauses ]
  AS query
```

- 적용 대상: Databricks SQL.
- 새로 고침: 각 새로 고침은 원천의 변경을 반영하도록 결과를 다시 계산합니다. 수동 또는 일정에 따라 실행할 수 있습니다.
- 증분 새로 고침: 문서는 기대치(expectations)를 정의에 포함한 구체화 뷰가 대부분의 경우 증분 새로 고침을 지원한다고 설명합니다. 일부 경우에는 전체 새로 고침이 필요하며, 이는 별도 문서에 있습니다.
- 수동 새로 고침은 `REFRESH (MATERIALIZED VIEW or STREAMING TABLE)` 레퍼런스를 따릅니다.

```sql
-- 매일 갱신되는 구체화 뷰 (문서 예시와 같은 형태)
CREATE MATERIALIZED VIEW main.sales.daily_sales
  COMMENT 'Daily sales numbers'
  SCHEDULE EVERY 1 DAY
AS
SELECT order_date, SUM(amount) AS total_amount
FROM main.sales.orders
GROUP BY order_date;
```

> **주의** 위 예시는 문서의 구문 요소(`COMMENT`, `SCHEDULE EVERY 1 DAY`)를 쓴 형태입니다. `SELECT` 본문은 설명용입니다. 실행 전 대상 카탈로그와 스키마 이름을 바꿉니다.

**Managed Iceberg 구체화 뷰**: 문서는 `USING ICEBERG` 옵션을 쓰는 관리형 Iceberg 구체화 뷰를 **Public Preview** 로 표기합니다. 나머지 구체화 뷰 구문에는 상태 라벨이 없습니다.

### 스트리밍 테이블

**구문 (문서 기준)**

```
{ CREATE OR REFRESH STREAMING TABLE | CREATE STREAMING TABLE [ IF NOT EXISTS ] }
  table_name [ table_specification ]
  [ table_clauses ]
  [ { flow_clause | AS query } ]
```

- 적용 대상: Databricks SQL. 문서는 이 명령을 Databricks SQL 웨어하우스(Unity Catalog 필요)용으로 설명합니다.
- 설명: 스트리밍 또는 증분 데이터 처리를 위한 추가 기능을 가진 Delta 테이블입니다.
- 다른 Databricks Runtime 컴퓨트에서 실행하면 구문만 파싱되고 테이블은 만들어지지 않는다고 명시합니다.
- 지원 상태: `FLOW` 절은 **Beta**, `REPLACE USING` 흐름은 **Beta** 이며 Databricks Runtime 18.2 이상이 필요합니다. 명령 자체에는 상태 라벨이 없습니다.

```sql
-- read_files로 읽은 원천을 스트리밍 테이블로 적재한다 (문서 예시와 같은 형태)
CREATE OR REFRESH STREAMING TABLE main.raw.events
AS SELECT *
FROM STREAM read_files('<원천 경로>');
```

> **주의** 문서의 예시는 Azure 저장소 경로를 씁니다. 위 예시의 `<원천 경로>`는 실제 Unity Catalog 볼륨 경로나 클라우드 저장소 경로로 바꿉니다. 파일 형식 옵션은 `read_files` 레퍼런스에서 확인합니다.

### 구체화 뷰와 스트리밍 테이블 비교

| 항목 | 구체화 뷰 | 스트리밍 테이블 |
|---|---|---|
| 생성 구문 | `CREATE MATERIALIZED VIEW` | `CREATE STREAMING TABLE` |
| 기본 관점 | 결과 집합을 원천에 맞춰 갱신 | 새로 들어온 데이터를 증분 처리 |
| 새로 고침 | 수동 또는 일정(`SCHEDULE`) | 문서의 새로 고침 페이지 참조 (이 페이지는 일정·트리거 세부를 확인하지 않음) |
| 상태 라벨 | 관리형 Iceberg 옵션은 Public Preview, 나머지는 라벨 없음 | `FLOW`와 `REPLACE USING`은 Beta, 명령은 라벨 없음 |
| 실행 가능한 곳 | Databricks SQL 웨어하우스, 서버리스 범용 컴퓨트 노트북 | Databricks SQL 웨어하우스(Unity Catalog), Lakeflow 파이프라인 |

## 어떻게 쓰는가

1. 원천 테이블을 Unity Catalog에 준비합니다.
2. 목적에 따라 `CREATE MATERIALIZED VIEW` 또는 `CREATE STREAMING TABLE`로 정의합니다.
3. 수동 새로 고침은 `REFRESH` 레퍼런스의 구문을 씁니다. 자동 갱신은 구체화 뷰에 `SCHEDULE`을 지정합니다.
4. 대시보드와 쿼리는 일반 테이블처럼 조회합니다.

> **참고** 배치 ETL에서 `REPLACE WHERE` 흐름과 구체화 뷰 중 무엇을 고를지는 문서의 별도 가이드가 있습니다. 이 페이지는 두 방식의 선택 기준을 다루지 않습니다.

## 트레이드오프

| 관점 | 고려할 점 |
|---|---|
| 갱신 비용 | 전체 새로 고침이 필요한 정의는 원천 전체를 다시 계산. 증분 가능 여부를 먼저 확인 |
| 운영 주체 | 독립형 객체는 Databricks가 밑의 파이프라인을 관리. 세밀한 파이프라인 제어가 필요하면 04장의 Lakeflow 파이프라인 구성을 검토 |
| 상태 | Beta 기능(`FLOW`, `REPLACE USING`)과 Public Preview(Managed Iceberg)는 운영 필수 기능으로 쓰기 전 검토 |
| 컴퓨트 제약 | 스트리밍 테이블 명령은 Databricks SQL 웨어하우스에서 Unity Catalog를 요구. 다른 컴퓨트에서는 테이블이 생성되지 않음 |

## 주의사항

- **구문 위치를 먼저 확인합니다.** 스트리밍 테이블을 노트북의 일반 Databricks Runtime 컴퓨트에서 실행하면 테이블이 만들어지지 않습니다. 실행 위치를 웨어하우스나 파이프라인으로 맞춥니다.
- **`CREATE OR REPLACE`는 정의를 바꾸는 배포입니다.** 같은 이름의 객체를 다시 정의하면 결과와 하위 소비자에 미치는 영향을 먼저 확인합니다.
- **상태 라벨을 운영 설계에 반영합니다.** Beta와 Public Preview 기능은 SLA와 변경 가능성을 따로 검토합니다.
- **기대치(expectations)를 넣으면 증분 새로 고침 가능 여부가 달라질 수 있습니다.** 정의를 바꾸기 전에 새로 고침 방식을 확인합니다.

## 참고 문서

- [Use standalone materialized views and streaming tables (Data warehousing on Databricks)](https://docs.databricks.com/aws/en/sql/mv-st/)
- [CREATE MATERIALIZED VIEW](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-materialized-view)
- [CREATE STREAMING TABLE](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-streaming-table)
- [SQL language reference](https://docs.databricks.com/aws/en/sql/language-manual/)
