# 쿼리 프로필 읽기

> 기준일: 2026-10-28 · 근거: 공식 문서

쿼리 프로필(Query profile)은 쿼리가 실행된 과정을 시각화한 화면입니다. 왼쪽에는 요약 지표 탭이, 오른쪽에는 연산자(operator)의 방향성 비순환 그래프(DAG)가 있습니다. 어느 연산자가 시간을 쓰고, 메모리를 얼마나 쓰고, 행을 얼마나 처리했는지 보여주므로 병목을 찾는 1차 도구입니다.

## 왜 필요한가

쿼리가 느릴 때 SQL 문장만 보고 원인을 추정하면 빗나가기 쉽습니다. 같은 문장이라도 조인 순서, 데이터 분포, 파일 레이아웃에 따라 시간이 크게 달라집니다. 쿼리 프로필은 실행 단계별 지표를 보여주므로, "문장의 어느 부분이 실제로 비싼지"를 확인할 수 있습니다.

| 질문 | 확인하는 곳 |
|---|---|
| 가장 오래 걸린 연산자는 무엇인가 | Top operators 탭, "See longest operators for this query" |
| 셔플 비용이 큰가 | DAG의 Shuffle 노드와 Time spent 지표 |
| 필터가 데이터를 얼마나 걸러냈는가 | Scan 노드의 필터 아이콘(프루닝 비율) |
| 어떤 권장 사항이 있는가 | Performance insights 탭 |

## 어떻게 동작하는가

### 화면 구성

| 영역 | 구성 요소 (문서 표기 기준) |
|---|---|
| 왼쪽 탭 | Details(요약 지표), Top operators(가장 비싼 연산자), Query text(쿼리 문장) |
| 요약 헤더 | See longest operators for this query, Aggregated task time, Query wall-clock duration, Input/Output (IO) |
| 오른쪽 DAG | 연산자 그래프. 클릭한 지표를 기준으로 색과 값이 바뀜 |
| 지표 선택 | Time spent, Memory peak, Rows 등 |
| 케밥 메뉴 | Open in Spark UI, Enable verbose mode(기본으로 숨겨진 연산자 표시) |
| 인사이트 탭 | Performance insights — 각 인사이트의 상세 |

### 연산자 종류

공식 문서가 예시로 드는 연산자 이름은 Scan, Join, Union, Shuffle, Hash / Sort, Filter입니다.

| 연산자 | 읽는 포인트 |
|---|---|
| Scan | 읽은 데이터 대비 프루닝 비율. 프루닝이 낮으면 필요 이상으로 많이 읽은 것 |
| Join | 출력 행 수가 입력보다 지나치게 크면 조인 폭발(exploding join) 의심 |
| Shuffle | 데이터를 실행기 사이로 옮기므로 비용이 큼. Time spent가 높은지 확인 |
| Filter | 필터가 Scan 가까이 내려왔는지 확인 |
| Hash / Sort | 메모리 사용량(Memory peak)을 함께 확인 |

> **참고** 공식 문서는 "Full table scan"과 "exploding join"을 흔한 SQL 실수로 들며, 이 두 가지를 쿼리 프로필에서 찾아보라고 안내합니다.

### 쿼리 기록에서 프로필 열기

1. 사이드바에서 **Query History** 를 엽니다.
2. 쿼리 이름을 클릭하면 오른쪽에 쿼리 상세 패널이 열립니다.
3. **See query profile** 을 클릭하면 **Details** 패널이 열립니다.

캐시에서 실행된 쿼리는 프로필이 없다는 메시지가 나옵니다. 이때는 `LIMIT`을 바꾸거나 제거해 캐시를 우회합니다.

## 어떻게 쓰는가

프로필을 읽는 권장 순서는 다음과 같습니다.

1. **요약 헤더에서 wall-clock 시간과 집계 태스크 시간을 확인합니다.** 두 값의 차이가 크면 대기나 직렬 구간이 있는지 봅니다.
2. **Top operators 탭에서 상위 연산자 3개를 적습니다.**
3. **DAG에서 Time spent 지표로 바꾸고 상위 연산자 위치를 찾습니다.**
4. **Scan 노드의 프루닝 아이콘을 확인합니다.** 조건절이 파티션이나 파일 통계로 전달되는지 봅니다.
5. **Memory peak를 선택해 메모리 집중 연산자를 확인합니다.** 공식 문서는 spill 항목을 쿼리 프로필 페이지에서 다루지 않으므로, spill 판단은 Performance insights의 DATA_SPILL 항목(8번 페이지)을 함께 봅니다.
6. **Performance insights 탭에서 권장 항목을 확인합니다.** 인사이트 목록은 8번 페이지에서 다룹니다.

### 예: 프로필에서 확인할 쿼리 패턴

아래 쿼리는 프로필에서 조인과 필터 위치를 비교하기 좋은 형태입니다. 같은 결과를 내는 두 가지 작성 방식을 실행해 DAG를 비교합니다.

```sql
-- 방식 A: 큰 팩트 테이블을 먼저 조인한 뒤 필터한다
SELECT c.region, SUM(o.amount) AS total_amount
FROM main.sales.orders AS o
JOIN main.sales.customers AS c
  ON o.customer_id = c.customer_id
WHERE o.order_date >= DATE'2026-10-01'
GROUP BY c.region;

-- 방식 B: 필터를 먼저 적용해 조인 입력을 줄인다
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

> **주의** 옵티마이저는 두 문장을 같은 계획으로 다시 쓸 수도 있습니다. 차이가 실제로 있는지는 두 쿼리의 프로필에서 Scan의 읽은 행 수와 Join의 입력 행 수를 비교해 확인합니다.

## 트레이드오프

| 관점 | 쿼리 프로필의 한계 |
|---|---|
| 해석 난이도 | 연산자 이름과 지표 의미를 알아야 원인을 좁힐 수 있음 |
| 캐시 쿼리 | 캐시에서 실행되면 프로필이 없어 재실행이 필요 |
| 원인 제시 | 병목 위치는 보여주지만 해결책을 자동으로 주지는 않음 (권장 항목은 인사이트 탭에서 확인) |
| 반복 실행 | 한 번의 프로필은 그 실행의 기록. 평균을 보려면 여러 실행을 비교 |

## 주의사항

- **캐시 결과로 판단하지 않습니다.** 캐시에서 나온 응답은 실행 비용이 낮게 보이므로, 측정 전에 캐시를 우회합니다.
- **웨어하우스 상태를 같이 봅니다.** 대기 시간(EXCESSIVE_QUEUE_TIME 같은 인사이트)은 쿼리 자체가 아니라 웨어하우스 부하에서 올 수 있습니다. 웨어하우스 선택과 크기는 03장에서 다룹니다.
- **Enable verbose mode를 필요할 때만 켭니다.** 기본으로 숨겨진 연산자가 보이면서 그래프가 복잡해집니다.
- **Spark UI는 상세 디버깅용입니다.** 일상적인 SQL 튜닝은 쿼리 프로필만으로 충분한 경우가 많습니다.

## 참고 문서

- [쿼리 프로필](https://docs.databricks.com/aws/en/sql/user/queries/query-profile)
- [쿼리 기록](https://docs.databricks.com/aws/en/sql/user/queries/query-history)
- [쿼리 성능 인사이트](https://docs.databricks.com/aws/en/sql/user/queries/performance-insights)
- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
