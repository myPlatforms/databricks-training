# 쿼리 성능 최적화

> 기준일: 2026-10-29 · 근거: 공식 문서

이 페이지는 **쿼리 측면** 의 성능 점검을 다룹니다. 성능 인사이트(Performance insights)를 해석하고, 통계 수집·조인 힌트·캐시 같은 쿼리와 테이블 쪽 수단을 고르는 방법입니다. SQL 웨어하우스의 유형과 크기를 고르는 기준은 [SQL 웨어하우스](../03-compute/sql-warehouses.md)에서 다룹니다. 지표 화면 읽는 법은 [쿼리 프로필 읽기](query-profile.md)를 참고하십시오.

## 왜 필요한가

느린 쿼리에 웨어하우스를 키우면 일시적으로 빨라질 수 있지만, 같은 문장이 더 많은 데이터를 읽는 구조라면 비용만 늘어납니다. 먼저 쿼리가 **무엇을 얼마나 읽고, 어디서 시간을 쓰는지** 확인해야 합니다. 쿼리 프로필과 성능 인사이트는 이 판단을 돕는 공식 도구입니다.

## 어떻게 동작하는가

### 성능 인사이트가 나타나는 곳

공식 문서 기준 인사이트는 다음 두 곳에 나타납니다.

- **쿼리 기록** 의 상세 패널: 요약이 "예상 총 태스크 시간에 미치는 영향"을 기준으로 순위를 매겨 표시됩니다.
- **쿼리 프로필** 의 **Performance insights** 탭: 각 인사이트의 전체 상세가 나타납니다.

인사이트에 실행 가능한 권장 사항이 있으면 **Optimize** 를 선택해 Genie Code를 열 수 있습니다. 쿼리 변경이 필요한 인사이트는 Genie Code가 쿼리를 다시 쓰고 승인을 요청하며, 테이블·컴퓨트 변경은 평이한 문장으로 권장 조치를 설명합니다. 이미 자동 적용된 최적화는 **Accelerated** 라벨로 표시되며 조치가 필요 없습니다.

### 인사이트와 공식 권장 조치

공식 문서는 인사이트를 네 묶음(쿼리 최적화 9개, 데이터 배치 6개, 컴퓨트·자원 3개, 적용된 가속 4개)으로 나누고 각각 권장 조치를 적습니다. 아래 표는 원문 설명을 요약한 것입니다.

| 묶음 | 인사이트 | 원문 설명 | 원문 권장 조치 |
|---|---|---|---|
| 쿼리 최적화 | `COVERAGE_FILTER_KEYS_CLUSTERING` | 클러스터링 키로 스캔을 필터하지 않음 | 클러스터링 키에 필터 추가 |
| 쿼리 최적화 | `COVERAGE_FILTER_KEYS_PARTITIONING` | 파티션 키로 스캔을 필터하지 않음 | 파티션 키에 필터 추가 |
| 쿼리 최적화 | `COVERAGE_PHOTON` | Photon이 가속하지 못해 표준 엔진이 실행 | Photon 제약을 검토하고 쿼리 조정 |
| 쿼리 최적화 | `EXPLODING_JOIN` | 조인이 읽은 것보다 훨씬 많은 행을 만듦 | 조인 조건을 좁히거나 입력 행 축소 |
| 쿼리 최적화 | `FLOW_FULL_RECOMPUTE` | 플로우가 전체 재계산으로 실행 | 증분이 가능하도록 재작성 |
| 쿼리 최적화 | `REDUNDANT_AGGREGATION` | 집계가 결과를 바꾸지 않음 | 집계 제거 또는 기본 키·외래 키 제약 적용 |
| 쿼리 최적화 | `REDUNDANT_JOIN` | 외부 조인이 바깥쪽 행 수를 바꾸지 않고 조인 열도 쓰지 않음 | 조인 제거 또는 기본 키·고유 제약 적용 |
| 쿼리 최적화 | `SELECTIVE_JOIN` | 조인이 읽은 것보다 훨씬 적은 행을 만듦 | 조인 전에 필터 추가 |
| 쿼리 최적화 | `WIDE_PROJECTION` | 테이블의 모든 열을 선택 | 필요한 열만 선택 |
| 데이터 배치 | `CONCURRENT_WRITE` | 동시 쓰기 충돌이 자동 해결되거나 실패 | Delta 기록을 검토하고 스케줄 조정 |
| 데이터 배치 | `COVERAGE_STATS_DELTA` | Delta 데이터 스키핑 통계가 없거나 불완전 | Delta 통계 수집 |
| 데이터 배치 | `COVERAGE_STATS_OPTIMIZER` | 비용 기반 옵티마이저 통계가 없거나 불완전해 휴리스틱 사용 | 통계 수집 |
| 데이터 배치 | `DATA_FILE_SIZE` | 작은 파일을 많이 읽음 | Predictive Optimization 사용, `OPTIMIZE` 실행, 파티션 테이블은 리퀴드 클러스터링으로 전환 |
| 데이터 배치 | `DATA_SKEW` | 컴퓨트 자원 간 데이터 분포가 고르지 않음 | 분포 검토, 키 솔팅 또는 사전 집계 |
| 데이터 배치 | `MANUAL_DATA_LAYOUT` | 수동 최적화된 테이블로 Automatic Liquid Clustering의 이점 가능 | 관리형 테이블로 전환, Predictive Optimization 또는 자동 클러스터링 사용 |
| 컴퓨트·자원 | `DATA_SPILL` | 메모리에 맞지 않아 디스크로 spill | 웨어하우스 크기 증가, 또는 행·열·큰 열 크기 축소 |
| 컴퓨트·자원 | `EXCESSIVE_QUEUE_TIME` | 웨어하우스 큐에서 대기 | 웨어하우스 최대 클러스터 수 증가 |
| 컴퓨트·자원 | `IO_THROTTLING` | 클라우드 제공자가 스토리지 요청을 제한 | 관리자에게 스토리지 한도 상향 요청 |
| 적용된 가속 | `AUTO_LIQUID_CLUSTERING` | Automatic Liquid Clustering 덕분에 적게 읽음 | 조치 불필요 |
| 적용된 가속 | `HISTORY_BASED_JOIN_STRATEGY` | 이전 유사 쿼리의 측정값으로 브로드캐스트 조인 선택 | 조치 불필요 |
| 적용된 가속 | `METRIC_VIEW_MATERIALIZATION_MATCH` | 메트릭 뷰의 사전 계산된 구체화 결과로 응답 | 조치 불필요 |
| 적용된 가속 | `SHORT_QUERY_PRIORITIZATION` | 짧을 것으로 예측된 쿼리를 빠른 경로로 즉시 실행 | 조치 불필요 |

공식 문서는 인사이트에 정량 임계값이나 예제 SQL을 명시하지 않습니다. `COVERAGE_STATS_DELTA`는 필터별 통계 상태를 **Full**, **Partial**, **Unavailable**, **Unused**(필터가 데이터 타입을 변환함) 네 가지로 표시합니다.

> **참고** 임계값이 문서에 없으므로 "몇 % 이상이면 문제"라는 기준은 쓰지 않습니다. 인사이트의 순위와 상세 설명을 기준으로 판단합니다.

## 어떻게 쓰는가

### 점검 순서

1. **쿼리 기록에서 대상 쿼리를 고릅니다.** 사용자, 기간, 컴퓨트, 실행 시간, 상태 등으로 필터합니다.
2. **상세 패널의 인사이트 요약을 봅니다.** 순위가 높은 항목부터 확인합니다.
3. **쿼리 프로필의 Performance insights 탭에서 상세를 봅니다.**
4. **위 표의 권장 조치를 적용합니다.**
5. **수정 후 같은 쿼리를 다시 실행하고, 프로필을 비교합니다.** 캐시 결과가 아닌지 확인합니다.

### 조인 전에 필터를 적용하는 예 (`SELECTIVE_JOIN`)

```sql
-- 필터를 조인 이전 단계로 옮겨 조인 입력을 줄인다
WITH recent_orders AS (
  SELECT customer_id, amount
  FROM main.sales.orders
  WHERE order_date >= DATE'2026-10-01'
)
SELECT c.region, SUM(r.amount) AS total_amount
FROM recent_orders AS r
JOIN main.sales.customers AS c
  ON r.customer_id = c.customer_id
GROUP BY c.region;
```

> **주의** 옵티마이저가 원래 문장을 이미 같은 계획으로 바꿀 수 있습니다. 효과는 두 버전의 쿼리 프로필에서 읽은 행 수와 조인 입력 행 수를 비교해 확인합니다.

### 통계 수집 (`ANALYZE TABLE`)

옵티마이저는 통계로 효율적인 쿼리 계획을 만듭니다. `COVERAGE_STATS_OPTIMIZER`와 `COVERAGE_STATS_DELTA` 인사이트가 보이면 통계를 수집합니다.

```sql
-- 행 수와 크기(바이트) 수집
ANALYZE TABLE main.sales.orders COMPUTE STATISTICS;

-- 지정한 열의 열 통계까지 수집
ANALYZE TABLE main.sales.orders COMPUTE STATISTICS FOR COLUMNS customer_id;

-- 스키마 안 모든 테이블의 크기만 수집
ANALYZE TABLES IN sales COMPUTE STATISTICS NOSCAN;

-- Delta 로그의 데이터 스키핑 통계 재계산 (DBR 14.3 LTS 이상, Databricks SQL)
ANALYZE TABLE main.sales.orders COMPUTE DELTA STATISTICS;
```

| 옵션 | 원문 동작 |
|---|---|
| (옵션 없음) | 행 수와 바이트 크기 수집 |
| `NOSCAN` | 전체 스캔 없이 바이트 크기만 수집 |
| `FOR COLUMNS col [, ...]` / `FOR ALL COLUMNS` | 테이블 통계에 더해 열 통계 수집 |
| `COMPUTE DELTA STATISTICS` | 데이터 스키핑 대상 열의 Delta 로그 통계 재계산. 이 키워드를 쓰면 일반 옵티마이저 통계는 수집되지 않음 |

- 데이터 스키핑 열을 새로 지정했다면 `COMPUTE DELTA STATISTICS` 후 `COMPUTE STATISTICS`를 차례로 실행해 계획에 Delta 로그 변경이 반영되게 합니다.
- Unity Catalog 관리형 테이블은 예측 최적화(Predictive optimization)가 `ANALYZE`를 자동 실행합니다. 공식 문서는 관리형 테이블 전체에 켜기를 권장합니다 ([테이블 레이아웃 최적화](../02-lakehouse-storage/table-layout-optimization.md) 참고).
- `PARTITION` 절은 Delta 테이블에서 지원되지 않고, 열 통계와 함께 쓸 수 없습니다.

### 조인 힌트

힌트는 조인 전략을 **제안** 합니다. 일반 형식은 `/*+ { partition_hint | join_hint | skew_hint } [, ...] */`입니다.

| 힌트 | 전략 | 원문 비고 |
|---|---|---|
| `BROADCAST(table)` | 브로드캐스트 조인 | `autoBroadcastJoinThreshold`와 무관하게 힌트가 붙은 쪽을 브로드캐스트. 양쪽에 붙이면 통계상 작은 쪽 |
| `MERGE(table)` | 셔플 정렬 병합 조인 | |
| `SHUFFLE_HASH(table)` | 셔플 해시 조인 | 양쪽에 붙이면 통계상 작은 쪽이 빌드 측 |
| `SHUFFLE_REPLICATE_NL(table)` | 셔플 복제 중첩 루프 조인 | |

```sql
SELECT /*+ BROADCAST(c) */ c.region, SUM(o.amount) AS total_amount
FROM main.sales.orders AS o
JOIN main.sales.customers AS c
  ON o.customer_id = c.customer_id
GROUP BY c.region;
```

- 별칭: `BROADCASTJOIN`·`MAPJOIN`은 `BROADCAST`, `SHUFFLE_MERGE`·`MERGEJOIN`은 `MERGE`의 별칭입니다.
- 힌트끼리 충돌하면 BROADCAST, MERGE, SHUFFLE_HASH, SHUFFLE_REPLICATE_NL 순으로 우선합니다.
- 테이블에 별칭을 붙였다면 힌트도 별칭으로 지정해야 합니다.
- 적용 여부는 `EXPLAIN EXTENDED`로 확인합니다.
- 파티셔닝 힌트(`COALESCE`, `REPARTITION`, `REPARTITION_BY_RANGE`, `REBALANCE`)도 있습니다. `REBALANCE`는 AQE가 꺼져 있으면 무시됩니다.

### 캐시와 측정

Databricks SQL 문서가 설명하는 캐시는 다음과 같습니다.

| 캐시 | 범위 | 보존 | 웨어하우스 중지·재시작 후 |
|---|---|---|---|
| 쿼리 결과 캐시 - 로컬 | 웨어하우스 클러스터(메모리) | 클러스터 수명 동안 또는 가득 찰 때까지, 최대 24시간 | 지워짐 |
| 쿼리 결과 캐시 - 원격 | 워크스페이스의 모든 웨어하우스 공유, 서버리스 전용 | 24시간 | 유지 |
| 디스크 캐시 | 컴퓨트 노드의 로컬 SSD에 저장한 스토리지 데이터 | 클러스터 수명 | 지워짐 |
| Databricks SQL UI 캐시 | 사용자별 | 최대 7일 | 문서에 명시 없음 |

- 결과 캐시는 기반 테이블이 바뀌면 무효화됩니다. AI/BI 대시보드는 UI 캐시 대상이 아니며 자체 캐시 동작이 있습니다.
- 캐시에서 실행된 쿼리는 프로필이 없고 실행 시간도 짧게 보입니다. 공식 문서는 `LIMIT`을 바꾸거나 제거해 우회하라고 안내합니다.
- 테스트·벤치마크에서는 세션 파라미터로 결과 캐시를 끌 수 있습니다. 공식 문서는 테스트나 벤치마크에만 쓰라고 권장합니다.

```sql
SET use_cached_result = false;
```

### 예측 I/O (Predictive I/O)

예측 I/O는 Photon 전용 최적화로, 조건에 맞는 행이 적은 선택적 쿼리의 읽기와 일부 행만 바꾸는 `UPDATE`·`DELETE`·`MERGE`를 가속합니다. 쿼리별 설정은 없고 자동으로 동작합니다.

| 구분 | 원문 지원 컴퓨트 |
|---|---|
| 읽기 가속 | 서버리스·프로 SQL 웨어하우스, DBR 11.3 LTS 이상의 Photon 클러스터 |
| 업데이트 가속 | 서버리스·프로 SQL 웨어하우스, DBR 14.0 이상 클러스터 (12.2 LTS 이상도 지원하나 14.0 이상 권장) |

- 읽기: 딥러닝으로 효율적인 접근 패턴을 골라 필요한 데이터만 스캔합니다.
- 업데이트: 파일 전체를 다시 쓰는 대신 삭제 벡터로 제거 행을 표시합니다. 업데이트 가속에는 테이블에 삭제 벡터를 켜야 합니다 ([삭제 벡터](../02-lakehouse-storage/deletion-vectors.md) 참고).

```sql
ALTER TABLE main.sales.orders SET TBLPROPERTIES ('delta.enableDeletionVectors' = true);
```

> **주의** 삭제 벡터를 켜면 테이블 프로토콜 버전이 올라가 삭제 벡터를 지원하지 않는 Delta 클라이언트는 테이블을 읽지 못합니다. 예측 I/O는 Bloom 필터 인덱스(deprecated)를 대체합니다.

### 쿼리 큐잉과 웨어하우스 부하

`EXCESSIVE_QUEUE_TIME`은 쿼리가 아니라 웨어하우스 부하 문제입니다. 원문 기준 사실은 다음과 같습니다.

- 모든 웨어하우스 유형에서 큐에 둘 수 있는 쿼리는 최대 1,000개입니다.
- 클래식·프로: 클러스터 1개당 동시 쿼리 10개가 고정 한도입니다. 큐에서 5분 기다린 쿼리가 있으면 스케일 업하고, 부하가 15분 연속 낮으면 스케일 다운합니다.
- 서버리스: Intelligent Workload Management가 쿼리의 자원 요구를 예측해 여유가 있으면 즉시 시작하고, 없으면 큐에 둡니다. 피크 부하에 맞춰 최대 클러스터 수를 충분히 높이고 **Peak Queued Queries** 를 모니터링합니다.
- 모니터링 탭의 Peak Queued Queries가 지속적으로 0보다 크면 크기나 클러스터 수를 늘리는 신호입니다. 쿼리 프로필의 **Bytes spilled to disk** 는 웨어하우스가 작다는 신호입니다.

## 트레이드오프

| 선택 | 장점 | 고려할 점 |
|---|---|---|
| 쿼리 문장 수정 | 비용 구조를 직접 줄임 | 로직 변경 검증이 필요 |
| 웨어하우스 증설 | 빠른 완화 (`DATA_SPILL`, `EXCESSIVE_QUEUE_TIME`의 공식 권장 조치) | 근본 원인이 쿼리면 비용만 늘어남 |
| 통계 수집·예측 최적화 | 옵티마이저와 데이터 스키핑이 정확해짐 | 수집 비용. 관리형 테이블은 예측 최적화로 자동화 |
| 조인 힌트 | 전략을 직접 지정 | 보장되지 않고, 데이터가 바뀌면 부적합해질 수 있음 |
| 삭제 벡터(예측 I/O 업데이트 가속) | 소량 변경 시 재작성 감소 | 프로토콜 버전 상승으로 일부 클라이언트 비호환 |
| 중간 테이블·구체화 뷰 | 반복 계산을 줄임 | 갱신 비용과 신선도 관리 ([구체화 뷰와 스트리밍 테이블](materialized-views-and-streaming-tables.md)) |
| Genie Code 권장 적용 | 인사이트에서 바로 개선 시작 | 생성된 변경은 항상 결과와 권한을 검토 |

## 주의사항

- **인사이트를 맹신하지 않습니다.** 인사이트는 원인 후보를 보여주는 도구입니다. 수정 후 프로필로 효과를 확인합니다.
- **같은 조건으로 비교합니다.** 웨어하우스 대기 시간이나 캐시 여부가 다르면 문장 차이를 판단할 수 없습니다.
- **`SELECT *`를 기본값으로 쓰지 않습니다.** `WIDE_PROJECTION` 인사이트의 원인입니다.
- **`EXPLODING_JOIN`과 `SELECTIVE_JOIN`은 반대 방향입니다.** 전자는 조인이 행을 크게 늘리고, 후자는 크게 줄이는 경우입니다.
- **Spill과 대기 시간을 같은 문제로 보지 않습니다.** 전자는 쿼리 메모리, 후자는 웨어하우스 큐입니다. 권장 조치도 다릅니다(크기 증가 vs 최대 클러스터 수 증가).
- **힌트는 마지막 수단으로 검증과 함께 씁니다.** 힌트가 무시되면 경고가 로그에 남습니다.

## 참고 문서

- [쿼리 성능 인사이트](https://docs.databricks.com/aws/en/sql/user/queries/performance-insights)
- [쿼리 프로필](https://docs.databricks.com/aws/en/sql/user/queries/query-profile)
- [쿼리 기록](https://docs.databricks.com/aws/en/sql/user/queries/query-history)
- [쿼리 결과 캐싱](https://docs.databricks.com/aws/en/sql/user/queries/query-caching)
- [USE_CACHED_RESULT](https://docs.databricks.com/aws/en/sql/language-manual/parameters/use_cached_result)
- [Predictive I/O](https://docs.databricks.com/aws/en/optimizations/predictive-io)
- [ANALYZE TABLE](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-analyze-table)
- [SQL 힌트](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-hints)
- [SQL 웨어하우스 동작(큐잉·오토스케일링)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-behavior)
- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
