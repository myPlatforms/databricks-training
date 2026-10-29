# Photon

> 기준일: 2026-10-29 · 근거: 공식 문서 · 수준: 200

Photon은 Databricks의 네이티브 벡터화 쿼리 엔진(vectorized query engine)입니다. 이 페이지는 Photon이 어떤 워크로드를 가속하는지, 각 컴퓨트에서 어떻게 켜고 끄는지, 어떤 워크로드에 맞지 않는지 다룹니다.

## 1. 왜 필요한가

Spark SQL 엔진은 JVM에서 행 단위에 가까운 처리를 많이 합니다. 대량의 스캔, 집계, 조인에서 CPU와 메모리 효율이 한계에 부딪힙니다. Photon은 벡터 단위로 데이터를 처리하고 네이티브 코드로 실행해 같은 쿼리를 더 빨리 끝내는 것을 목표로 합니다.

문서 표현에 따르면 Photon은 SQL 워크로드, DataFrame 호출, ETL, 상태 없는 스트리밍을 가속합니다. 따라서 "SQL만 빠르게 한다"는 이해는 정확하지 않습니다.

## 2. 어떻게 동작하는가

### 2.1 가속 대상

| 영역 | 문서 설명 (요약) |
|---|---|
| SQL 분석과 BI | 모든 SQL 웨어하우스의 기본 엔진입니다 |
| 연산 | 조인, 셔플, 스캔, 쓰기. 문서는 TPC-DS 벤치마크에서 다른 클라우드 데이터 웨어하우스 대비 "up to 5x better price/performance"를 제시합니다 |
| ETL과 데이터 엔지니어링 | 배치 SQL과 DataFrame 작업, Delta Lake·Apache Iceberg·Parquet 테이블 쓰기 |
| Lakeflow 파이프라인 | 파이프라인 설정에서 켜면 실행이 빨라집니다 |
| 스트리밍 | 상태 없는(stateless) 스트리밍만. Delta 또는 Parquet 싱크 |
| AI·ML | Spark SQL, DataFrame, 피처 엔지니어링, GraphFrames 연산 |

### 2.2 컴퓨트별 지원과 활성화

| 컴퓨트 | Photon 지원 | 기본 동작 (문서 기준) |
|---|---|---|
| 서버리스 컴퓨트 | 지원 | 항상 켜짐 |
| SQL 웨어하우스 | 지원 | 기본 엔진 |
| 서버리스 Lakeflow 파이프라인 | 지원 | 항상 켜짐 |
| 클래식 올-퍼포즈·Job·Lakeflow 파이프라인 | 지원 | 기본으로 켜짐(Performance의 체크박스로 변경). Compute 구성 문서: Databricks Runtime 9.1 LTS 이상에서 기본 활성화 |

클래식 컴퓨트에서는 UI의 **Performance** 항목에 있는 **Use Photon Acceleration** 체크박스로 켜고 끕니다.

API로 클래식 리소스를 만들 때는 명시적으로 켜야 합니다.

| API | 설정 |
|---|---|
| Clusters API, Jobs API | `runtime_engine`을 `PHOTON`으로 설정 |
| Pipelines API | `photon`을 `true`로 설정 |

```python
# Clusters API 명세 일부: Photon 엔진을 명시적으로 선택합니다.
# 다른 필수 필드(spark_version, node_type_id 등)는 워크스페이스 값으로 채우십시오.
cluster_spec = {
    "cluster_name": "photon-etl-example",
    "runtime_engine": "PHOTON",
    "autoscale": {"min_workers": 2, "max_workers": 6},
}
```

> **참고** 클래식 컴퓨트에서 `runtime_engine`의 허용 값은 `NULL`, `STANDARD`, `PHOTON`입니다. Clusters API 레퍼런스는 이 필드가 `-photon-`을 포함한 레거시 `spark_version` 값과 호환되지 않는다고 설명합니다.

일부 기능은 Photon이 켜져 있어야 동작합니다. 문서가 명시한 예는 다음과 같습니다.

- Predictive I/O (읽기와 쓰기)
- MERGE, UPDATE, DELETE에서의 동적 파일 프루닝(dynamic file pruning)

### 2.3 DBU 소비율

문서는 Photon 인스턴스 유형이 같은 인스턴스의 Photon이 아닌 런타임보다 **다른 DBU 비율로** 소비된다고 설명합니다. 원문은 "Photon instance types consume DBUs at a different rate than the same instance type running the non-Photon runtime."입니다. 구체적인 비율은 문서가 가격 페이지를 참고하라고 안내하므로 이 장에 적지 않습니다.

## 3. 어떻게 쓰는가

### 3.1 Photon 사용 여부 관측

| 위치 | 확인 방법 (문서 설명) |
|---|---|
| 쿼리 프로필 (SQL 웨어하우스, 서버리스 컴퓨트) | Execution Details 보기에서 Photon에 쓰인 태스크 시간의 비율을 보여줍니다. Photon 연산자는 보라색, 일반 연산자는 회색입니다 |
| Spark UI (클래식 올-퍼포즈·Job 컴퓨트) | SQL/DataFrame 탭의 쿼리 DAG에서 Photon 연산자는 주황색, 표준 Spark 연산자는 파란색입니다 |

서버리스 노트북은 Spark UI에 접근할 수 없으므로 쿼리 프로필로 확인합니다. 쿼리 프로필은 Query History에서 쿼리를 열고 **See query profile** 을 눌러 엽니다. **Query profile is not available** 이 표시되면 쿼리 캐시에서 실행된 경우이므로 `LIMIT` 등을 바꿔 다시 실행합니다. 쿼리 프로필 문서는 Photon이 아닌 일부 연산이 묶여서 공통 지표를 공유한다고도 설명합니다.

```sql
-- 대형 테이블 집계 쿼리 예시. 실행 후 쿼리 프로필에서 Photon 비율을 확인합니다.
SELECT
  region,
  date_trunc('month', order_ts) AS order_month,
  SUM(amount) AS total_amount
FROM main.sales.orders
WHERE order_ts >= '2026-01-01'
GROUP BY region, date_trunc('month', order_ts);
```

### 3.2 클래식 컴퓨트에서 켜고 끄기

1. 클래식 컴퓨트의 설정 화면에서 **Performance** 항목을 엽니다.
2. **Use Photon Acceleration** 체크박스를 켜거나 끕니다.

> **주의** 설정 변경이 실행 중인 클러스터에 언제 반영되는지는 이 장에서 확인하지 못했습니다. 변경 후 실제 실행 엔진을 쿼리 프로파일에서 확인하십시오.

### 3.3 지원 연산·표현식·데이터 타입

| 구분 | 문서가 나열한 항목 |
|---|---|
| 연산자 | Scan(Parquet, Delta, CSV, JSON), Filter, Project, Hash Aggregate, Join, Shuffle, Nested-Loop Join, Null-Aware Anti Join, Spatial Join(브로드캐스트·셔플), Union, Expand, ScalarSubquery, Delta/Parquet Write Sink, Sort, TopK, Limit, Window Function |
| 표현식 | 비교·논리, 산술·수학, 조건, 문자열 함수, 캐스트, 집계, 날짜·타임스탬프 함수. 개별 함수에 제한이 있을 수 있습니다 |
| 데이터 타입 | Byte, Short, Int, Long, Boolean, String, Binary, Decimal, Float, Double, Date, Timestamp, TimestampNTZ, Struct, Array, Map, Variant, Null, Geometry, Geography, collated strings |

Photon이 지원하지 않는 연산을 만나면 해당 연산은 Spark 런타임으로 폴백(fallback)하며 결과는 정확합니다. 즉 미지원 연산이 있어도 쿼리가 실패하지는 않고, 그 구간만 가속되지 않습니다.

## 4. 트레이드오프

| 항목 | 장점 | 한계 |
|---|---|---|
| 쿼리 성능 | SQL과 대형 DataFrame 작업에서 빠릅니다 | 짧은 쿼리는 이득이 작습니다 |
| 호환성 | 같은 Spark API와 Catalyst 계획을 씁니다 | UDF, RDD API, Dataset API는 지원하지 않습니다 |
| 스트리밍 | 상태 없는 스트리밍을 가속합니다 | 상태 있는(stateful) 스트리밍은 지원하지 않습니다 |
| 인스턴스 | Graviton 기반을 포함한 다수의 드라이버·워커 인스턴스 유형을 지원합니다 | Graviton 기반 인스턴스의 Photon은 Dedicated 컴퓨트와 SQL 웨어하우스에서 Databricks Container Services를 지원하지 않습니다. Standard 컴퓨트의 Container Services에는 해당하지 않습니다 |
| 비용 | 빨리 끝나면 DBU 총량이 줄 수 있습니다 | Photon 인스턴스의 DBU 소비율이 다릅니다. 문서는 가격 페이지를 확인하라고 안내합니다 |

> **참고** "빨리 끝나면 비용이 준다"는 판단은 실제 측정으로 확인해야 합니다. 문서는 2초 안에 끝나는 쿼리는 이득이 작다고 설명하므로, 짧은 작업을 Photon으로 바꾸는 효과는 제한적일 수 있습니다.

## 5. 주의사항

- **UDF가 많은 코드는 효과가 작습니다.** Photon은 UDF를 지원하지 않습니다. UDF 호출이 많은 파이프라인이라면 SQL 함수나 내장 함수로 바꾸는 것을 먼저 검토하십시오.
- **RDD와 Dataset API를 쓰는 코드는 Photon 이득이 없습니다.** 문서가 Photon에서 지원하지 않는 API로 명시한 항목입니다. 이런 코드가 있으면 DataFrame이나 SQL로 옮기는 것을 검토하십시오.
- **상태 있는 스트리밍은 Photon 대상이 아닙니다.** 집계 상태를 쓰는 스트리밍 쿼리의 성능은 Photon으로 기대하지 마십시오.
- **Graviton 인스턴스와 Container Services 조합을 피하십시오.** Dedicated 컴퓨트와 SQL 웨어하우스에서 문서가 명시한 제약입니다.
- **미지원 연산은 조용히 폴백합니다.** 오류 없이 느려지기만 하므로 쿼리 프로필의 Photon 비율로 실제 가속 여부를 확인하십시오.
- **짧은 쿼리에 과도하게 기대하지 마십시오.** 시작 오버헤드가 대부분인 짧은 작업은 Photon을 켜도 체감이 작습니다.

## 참고 문서

- [Photon (AWS)](https://docs.databricks.com/aws/en/compute/photon)
- [쿼리 프로필 (AWS)](https://docs.databricks.com/aws/en/sql/user/queries/query-profile)
- [Compute 구성 (AWS)](https://docs.databricks.com/aws/en/compute/configure)
- [SQL warehouse 유형 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)
- [Clusters API 레퍼런스](https://docs.databricks.com/api/workspace/clusters/create)
