# 쿼리 프로필 읽기

> 기준일: 2026-10-29 · 근거: 공식 문서

쿼리 프로필(Query profile)은 쿼리가 실행된 과정을 시각화한 화면입니다. 왼쪽에는 요약 지표 탭이, 오른쪽에는 연산자(operator)의 방향성 비순환 그래프(DAG)가 있습니다. 가장 느린 부분을 찾고, 쿼리를 바꾼 효과를 평가하고, 조인 폭발(exploding join)이나 전체 테이블 스캔(full table scan) 같은 실수를 찾는 1차 도구입니다.

## 왜 필요한가

쿼리가 느릴 때 SQL 문장만 보고 원인을 추정하면 빗나가기 쉽습니다. 같은 문장이라도 조인 순서, 데이터 분포, 파일 레이아웃에 따라 시간이 크게 달라집니다. 쿼리 프로필은 실행 단계별 지표를 보여주므로, "문장의 어느 부분이 실제로 비싼지"를 확인할 수 있습니다.

| 질문 | 확인하는 곳 |
|---|---|
| 가장 오래 걸린 연산자는 무엇인가 | **Top operators** 탭, "See longest operators for this query" |
| 시간이 스케줄링·최적화·실행 중 어디에 쓰였나 | Query wall-clock duration 분해 |
| 필터가 데이터를 얼마나 걸러냈는가 | 쿼리 지표의 필터 아이콘(스캔 중 프루닝된 데이터 비율) |
| 어떤 권장 사항이 있는가 | **Performance insights** 탭 |

## 어떻게 동작하는가

### 프로필 열기

프로필을 보려면 쿼리 소유자이거나, 쿼리를 실행한 SQL 웨어하우스에 CAN MONITOR 권한이 있어야 합니다.

| 진입점 | 방법 |
|---|---|
| 쿼리 기록 | 사이드바 **Query History** → 쿼리 이름 클릭 → 오른쪽 상세 패널에서 **See query profile** → **Details** 패널 |
| SQL 에디터 | 페이지 하단의 경과 시간·반환 행 수 링크 클릭 → **See query profile** (새 SQL 에디터(Public Preview)는 노트북과 같은 방식의 링크) |
| 노트북 (SQL 웨어하우스·서버리스 컴퓨트 연결) | 셀 아래 **See performance** → 구문 선택 |
| Lakeflow pipelines UI | **Query History** 탭 |
| Jobs UI | SQL 웨어하우스·서버리스 컴퓨트의 Job |

"Query profile is not available"가 나오면 쿼리 캐시에서 실행된 것입니다. `LIMIT`을 바꾸거나 제거하는 사소한 변경으로 캐시를 우회합니다.

### 쿼리 상세 패널

| 항목 | 설명 (원문) |
|---|---|
| Query status | Queued, Running, Finished, Failed, Cancelled |
| ID | 쿼리 실행의 UUID |
| Query metrics | 핵심 지표. 필터 아이콘은 스캔 중 프루닝된 데이터 비율 |
| See longest operators for this query | **Top operators** 패널을 엶 |
| Query wall-clock duration | 스케줄링 시작부터 실행 종료까지. 스케줄링, 쿼리 최적화·파일 프루닝, 실행으로 분해 |
| Aggregated task time | 모든 노드의 모든 코어에서 쓴 시간의 합. 태스크가 병렬로 돌면 wall-clock보다 길 수 있고, 노드를 기다리면 짧을 수 있음 |
| Input/Output (IO) | 실행 중 읽고 쓴 데이터 |

### 상세 프로필 화면

| 영역 | 구성 요소 (문서 표기 기준) |
|---|---|
| 왼쪽 탭 | **Details**(요약 지표), **Top operators**(가장 비싼 연산자), **Query text**(쿼리 문장) |
| 오른쪽 DAG | 연산자 그래프. 지표(**Time spent**, **Memory peak**, **Rows**)를 클릭하면 그래프가 그 지표를 보여줌. 검색으로 연산자·열 강조, 확대·축소 가능 |
| 연산자 클릭 | 오른쪽 패널에 상세 지표와 설명 |
| 케밥 메뉴 | **Open in Spark UI** (Databricks SQL 쿼리), **Enable verbose mode** |
| 인사이트 탭 | **Performance insights** — 각 인사이트의 상세 |

**Enable verbose mode** 를 켜면 기본으로 숨겨진 연산자(병목일 가능성이 낮아 숨김)와 추가 지표가 모두 보입니다. 일부 non-Photon 연산은 묶음으로 실행되어 부모 연산자의 지표 값을 공유합니다.

### 연산자 종류

| 연산자 | 원문 설명 | 읽는 포인트 |
|---|---|---|
| Scan | 소스에서 데이터를 읽어 행을 출력 | 필터 아이콘의 프루닝 비율. 낮으면 필요 이상으로 읽는 것일 수 있음 |
| Join | 여러 릴레이션의 행을 결합 | 출력 행이 입력보다 지나치게 크면 `EXPLODING_JOIN` 인사이트와 함께 확인 |
| Union | 같은 스키마의 릴레이션 행을 이어 붙임 | |
| Shuffle | 데이터를 재분배·재파티션. 실행기 사이로 옮기므로 자원 소모가 큼 | **Time spent** 가 높은지 확인 |
| Hash / Sort | 키로 행을 묶고 그룹 안에서 집계 함수 적용 | **Memory peak** 를 함께 확인 |
| Filter | `WHERE` 같은 조건에 맞는 행의 부분집합 반환 | 필터가 Scan 가까이 내려왔는지 확인 |

> **참고** 공식 문서는 exploding join과 full table scan을 쿼리 프로필에서 찾을 수 있는 실수로 언급하지만, 정의나 해결책은 적지 않습니다. 해결책은 [쿼리 성능 최적화](query-performance.md)의 인사이트별 권장 조치를 봅니다.

## 어떻게 쓰는가

### 읽는 순서

1. **상세 패널에서 wall-clock 시간과 Aggregated task time을 비교합니다.** wall-clock 분해로 스케줄링·최적화·실행 중 어디가 긴지 봅니다.
2. **Top operators 탭에서 상위 연산자 3개를 적습니다.**
3. **DAG에서 Time spent 지표로 바꾸고 상위 연산자 위치를 찾습니다.**
4. **쿼리 지표의 필터 아이콘으로 프루닝 비율을 확인합니다.**
5. **Memory peak를 선택해 메모리 집중 연산자를 확인합니다.** 공식 쿼리 프로필 페이지는 spill 지표를 다루지 않습니다. spill 판단은 Performance insights의 `DATA_SPILL`을 봅니다.
6. **Performance insights 탭에서 권장 항목을 확인하고, 필요하면 Optimize로 Genie Code를 엽니다.**

### 병목 패턴과 확인 위치

| 패턴 | 프로필에서 볼 곳 | 연결되는 인사이트 (원문) |
|---|---|---|
| 필요 이상으로 읽음 | 프루닝 비율, Scan 행 수 | `COVERAGE_FILTER_KEYS_CLUSTERING`, `COVERAGE_FILTER_KEYS_PARTITIONING`, `WIDE_PROJECTION` |
| 조인 폭발 | Join의 Rows | `EXPLODING_JOIN` |
| 셔플 비중이 큼 | Shuffle의 Time spent | 해당 인사이트 명시 없음 |
| 메모리 부족 | Memory peak | `DATA_SPILL` |
| 작은 파일 | Scan 시간 | `DATA_FILE_SIZE` |
| 큐 대기 | wall-clock 분해 | `EXCESSIVE_QUEUE_TIME` |

### 공유·내려받기·가져오기

- **Share**: 받는 사람이 쿼리에 CAN MANAGE 권한이 있으면 프로필 URL을 복사해 공유합니다.
- **Download**: 권한이 없거나 워크스페이스 구성원이 아니면 JSON 파일로 내려받아 전달합니다.
- **Import**: 쿼리 기록의 케밥 메뉴에서 **Import query profile (JSON)** 을 선택합니다. 가져온 프로필은 브라우저 세션에만 로드되고 워크스페이스에 저장되지 않습니다. 닫을 때는 페이지 위쪽 **X** 를 누릅니다.

프로그램으로 지표를 얻으려면 문서는 쿼리 기록 API를 안내합니다.

### 예: 프로필에서 비교할 쿼리 패턴

같은 결과를 내는 두 가지 작성 방식을 실행해 DAG를 비교합니다.

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

> **주의** 옵티마이저는 두 문장을 같은 계획으로 다시 쓸 수도 있습니다. 차이가 실제로 있는지는 두 쿼리의 프로필에서 Scan의 행 수와 Join의 입력 행 수(Rows)를 비교해 확인합니다.

## 트레이드오프

| 관점 | 쿼리 프로필의 한계 |
|---|---|
| 해석 난이도 | 연산자 이름과 지표 의미를 알아야 원인을 좁힐 수 있음 |
| 캐시 쿼리 | 캐시에서 실행되면 프로필이 없어 재실행이 필요 |
| 원인 제시 | 병목 위치는 보여주지만 해결책은 인사이트 탭에서 확인 |
| 반복 실행 | 한 번의 프로필은 그 실행의 기록. 평균을 보려면 여러 실행을 비교 |
| 숨김 연산자 | 기본 화면에는 일부 연산자가 없음. verbose mode로 전체를 볼 수 있으나 그래프가 복잡해짐 |

## 주의사항

- **캐시 결과로 판단하지 않습니다.** 캐시에서 나온 응답은 프로필이 없으므로, 측정 전에 캐시를 우회합니다 (캐시 종류는 [쿼리 성능 최적화](query-performance.md) 참고).
- **웨어하우스 상태를 같이 봅니다.** 대기 시간(`EXCESSIVE_QUEUE_TIME`)은 쿼리 자체가 아니라 웨어하우스 부하에서 올 수 있습니다. 웨어하우스 선택과 크기는 [SQL 웨어하우스](../03-compute/sql-warehouses.md)에서 다룹니다.
- **Aggregated task time이 wall-clock보다 길어도 이상이 아닙니다.** 병렬 실행의 합이기 때문입니다.
- **Enable verbose mode를 필요할 때만 켭니다.**
- **가져온 프로필은 저장되지 않습니다.** 보존이 필요하면 JSON 파일을 따로 보관합니다.
- **Spark UI는 상세 디버깅용입니다.** 일상적인 SQL 튜닝은 쿼리 프로필로 시작합니다.

## 참고 문서

- [쿼리 프로필](https://docs.databricks.com/aws/en/sql/user/queries/query-profile)
- [쿼리 기록](https://docs.databricks.com/aws/en/sql/user/queries/query-history)
- [쿼리 성능 인사이트](https://docs.databricks.com/aws/en/sql/user/queries/performance-insights)
- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
