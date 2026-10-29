# 쿼리 성능 최적화

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 **쿼리 측면** 의 성능 점검을 다룹니다. 쿼리 문장을 고치고, 테이블 접근 패턴을 바꾸고, 성능 인사이트(Performance insights)를 해석하는 방법입니다. SQL 웨어하우스의 유형과 크기를 고르는 기준은 03장(컴퓨트)에서 다룹니다.

## 왜 필요한가

느린 쿼리에 웨어하우스를 키우면 일시적으로 빨라질 수 있지만, 같은 문장이 더 많은 데이터를 읽는 구조라면 비용만 늘어납니다. 먼저 쿼리가 **무엇을 얼마나 읽고, 어디서 시간을 쓰는지** 확인해야 합니다. 쿼리 프로필과 성능 인사이트는 이 판단을 돕는 공식 도구입니다.

## 어떻게 동작하는가

### 성능 인사이트가 나타나는 곳

공식 문서 기준 인사이트는 다음 두 곳에 나타납니다.

- **쿼리 기록** 의 상세 패널: 요약이 "예상 총 태스크 시간에 미치는 영향"을 기준으로 순위를 매겨 표시됩니다.
- **쿼리 프로필** 의 **Performance insights** 탭: 각 인사이트의 전체 상세가 나타납니다.

인사이트에 실행 가능한 권장 사항이 있으면 **Optimize** 를 선택해 Genie Code를 열 수 있습니다. 이미 자동 적용된 최적화는 **Accelerated** 라벨로 표시되며 조치가 필요 없습니다.

### 인사이트 분류

공식 문서는 인사이트를 네 묶음으로 나눕니다.

| 묶음 | 인사이트 이름 (원문 그대로) |
|---|---|
| 쿼리 최적화 | `COVERAGE_FILTER_KEYS_CLUSTERING`, `COVERAGE_FILTER_KEYS_PARTITIONING`, `COVERAGE_PHOTON`, `EXPLODING_JOIN`, `FLOW_FULL_RECOMPUTE`, `REDUNDANT_AGGREGATION`, `REDUNDANT_JOIN`, `SELECTIVE_JOIN`, `WIDE_PROJECTION` |
| 데이터 배치(layout) | `CONCURRENT_WRITE`, `COVERAGE_STATS_DELTA`, `COVERAGE_STATS_OPTIMIZER`, `DATA_FILE_SIZE`, `DATA_SKEW`, `MANUAL_DATA_LAYOUT` |
| 컴퓨트·자원 | `DATA_SPILL`, `EXCESSIVE_QUEUE_TIME`, `IO_THROTTLING` |
| 적용된 가속 | `AUTO_LIQUID_CLUSTERING`, `HISTORY_BASED_JOIN_STRATEGY`, `METRIC_VIEW_MATERIALIZATION_MATCH`, `SHORT_QUERY_PRIORITIZATION` |

공식 문서는 인사이트에 정량 임계값을 명시하지 않습니다. 대부분은 "조인이 읽은 것보다 훨씬 많은 행을 만든다"처럼 정성적으로 설명됩니다. 예외로 `COVERAGE_STATS_DELTA`는 필터별 통계 상태를 **Full**, **Partial**, **Unavailable**, **Unused** 네 가지로 표시합니다.

> **참고** 임계값이 문서에 없으므로 "몇 % 이상이면 문제"라는 기준은 이 장에 쓰지 않습니다. 인사이트의 순위와 상세 설명을 기준으로 판단합니다.

## 어떻게 쓰는가

### 점검 순서

1. **쿼리 기록에서 대상 쿼리를 고릅니다.** 실행 시간, 상태, 사용자 필터로 느린 쿼리를 찾습니다.
2. **상세 패널의 인사이트 요약을 봅니다.** 순위가 높은 항목부터 확인합니다.
3. **쿼리 프로필의 Performance insights 탭에서 상세를 봅니다.**
4. **인사이트 묶음에 따라 조치를 고릅니다.** 아래 표를 기준으로 합니다.
5. **수정 후 같은 쿼리를 다시 실행하고, 프로필을 비교합니다.** 캐시 결과가 아닌지 확인합니다.

| 인사이트 | 확인할 것 | 쿼리 측면 조치 (일반 원칙) |
|---|---|---|
| `EXPLODING_JOIN` | 조인 출력 행이 입력보다 훨씬 많은지 | 조인 키의 유일성 확인, 중복 키를 먼저 집계 |
| `SELECTIVE_JOIN` | 선택도가 높은 조인이 어디인지 | 조인 전에 필터를 적용해 입력 줄이기 |
| `REDUNDANT_AGGREGATION`, `REDUNDANT_JOIN` | 같은 집계·조인이 반복되는지 | CTE나 중간 테이블로 한 번만 계산 |
| `WIDE_PROJECTION` | 필요 없는 열을 많이 읽는지 | `SELECT *` 대신 필요한 열만 선택 |
| `DATA_SKEW` | 특정 키에 데이터가 몰리는지 | 키 분포 확인, 편중 키 분리 (데이터 배치 관점) |
| `DATA_SPILL` | 메모리 부족으로 디스크에 쓰는지 | 조인·집계 입력을 줄이고, 필요하면 컴퓨트 조정 (03장) |
| `EXCESSIVE_QUEUE_TIME` | 실행 전 대기 시간이 긴지 | 쿼리보다 웨어하우스 부하 문제. 03장에서 다룸 |
| `DATA_FILE_SIZE`, `MANUAL_DATA_LAYOUT` | 작은 파일이 많거나 수동 레이아웃이 있는지 | 데이터 배치 관리 (02장 저장 계층에서 다룸) |

> **참고** 위 "조치" 열은 문서의 인사이트 설명을 바탕으로 한 일반 원칙입니다. 구체적 수정은 쿼리 프로필과 인사이트 상세를 근거로 정합니다.

### 조인 전에 필터를 적용하는 예

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

> **주의** 옵티마이저가 원래 문장을 이미 같은 계획으로 바꿀 수 있습니다. 효과는 두 버전의 쿼리 프로필에서 Scan 읽기 행 수와 Join 입력 행 수를 비교해 확인합니다.

### 결과 캐시와 측정

- 캐시에서 실행된 쿼리는 프로필이 없고, 실행 시간도 짧게 보입니다. 측정할 때는 캐시를 우회합니다. 공식 문서는 `LIMIT`을 바꾸거나 제거하라고 안내합니다.
- 결과 캐시 설정은 SQL 레퍼런스의 `USE_CACHED_RESULT` 파라미터에 정의되어 있습니다.

## 트레이드오프

| 선택 | 장점 | 고려할 점 |
|---|---|---|
| 쿼리 문장 수정 | 비용 구조를 직접 줄임 | 로직 변경 검증이 필요 |
| 웨어하우스 증설 | 빠른 완화 | 근본 원인이 쿼리면 비용만 늘어남 (03장) |
| 중간 테이블·구체화 뷰 | 반복 계산을 줄임 | 갱신 비용과 신선도 관리가 필요 (7번 페이지) |
| Genie Code 권장 적용 | 인사이트에서 바로 개선 시작 | 생성된 변경은 항상 결과와 권한을 검토 |

## 주의사항

- **인사이트를 맹신하지 않습니다.** 인사이트는 원인 후보를 보여주는 도구입니다. 수정 후 프로필로 효과를 확인합니다.
- **같은 조건으로 비교합니다.** 웨어하우스 대기 시간이나 캐시 여부가 다르면 문장 차이를 판단할 수 없습니다.
- **`SELECT *`를 기본값으로 쓰지 않습니다.** `WIDE_PROJECTION` 인사이트의 주된 원인입니다.
- **조인 키의 유일성을 확인합니다.** `EXPLODING_JOIN`은 중복 키에서 자주 나타납니다.
- **Spill과 대기 시간을 같은 문제로 보지 않습니다.** 전자는 쿼리 메모리 문제, 후자는 웨어하우스 부하입니다.

## 참고 문서

- [쿼리 성능 인사이트](https://docs.databricks.com/aws/en/sql/user/queries/performance-insights)
- [쿼리 프로필](https://docs.databricks.com/aws/en/sql/user/queries/query-profile)
- [쿼리 기록](https://docs.databricks.com/aws/en/sql/user/queries/query-history)
- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
