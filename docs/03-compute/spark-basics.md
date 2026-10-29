# Spark 기초: 드라이버, 익스큐터, 지연 실행

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100

Databricks의 컴퓨트는 Apache Spark를 실행하는 자원입니다. 이 페이지는 컴퓨트 설정을 이해하는 데 필요한 Spark 기초만 간단히 다룹니다. 드라이버와 익스큐터의 역할, 클러스터 매니저, 변환(Transformation)과 액션(Action), 지연 실행(Lazy evaluation)을 설명합니다. Spark 전반은 Apache Spark 공식 문서가 더 자세합니다.

## 1. 왜 필요한가

컴퓨트를 고를 때 "메모리가 얼마나 필요한가", "드라이버가 어디서 터지는가", "왜 코드 한 줄이 실행되지 않는 것처럼 보이는가" 같은 질문이 생깁니다. 이 답은 Spark의 실행 구조에 있습니다. 구조를 모르면 다음 실수가 반복됩니다.

| 실수 | 원인 |
|---|---|
| 큰 데이터를 `collect()`로 드라이버에 모아 메모리 부족 발생 | 드라이버는 한 프로세스이고, 익스큐터 데이터를 모두 받을 수 없음 |
| 변환 코드를 작성했는데 실행 시간이 0초처럼 보임 | 지연 실행 때문에 액션 전까지 계산하지 않음 |
| 같은 DataFrame으로 여러 결과를 만들 때 매번 전체 계산 | 중간 결과를 저장하지 않으면 계보(Lineage)를 처음부터 다시 계산 |
| 워커를 늘렸는데 빨라지지 않음 | 병목이 드라이버 쪽이거나 셔플(Shuffle)에 있을 수 있음 |

## 2. 어떻게 동작하는가

### 2.1 드라이버 프로그램 (Driver program)

Apache Spark 공식 용어집은 드라이버를 "The process running the main() function of the application and creating the SparkContext"로 정의합니다. 즉 사용자 코드의 `main`을 돌리고 `SparkContext`를 만드는 프로세스입니다.

드라이버의 역할은 다음과 같습니다.

- 애플리케이션을 조정합니다. 공식 문서는 드라이버가 `SparkContext` 객체로 조정된다고 설명합니다.
- 태스크를 스케줄링합니다. 각 드라이버는 자기 태스크를 스케줄링합니다.
- 익스큐터의 연결을 받아들입니다. 드라이버는 수명 동안 익스큐터의 연결을 받아야 합니다.

Databricks 노트북에서 `spark`를 쓰는 코드가 실행되는 곳이 드라이버 쪽입니다. 결과를 드라이버로 가져오는 `collect()`나 `toPandas()`는 드라이버의 메모리를 씁니다.

### 2.2 익스큐터 (Executors)

익스큐터는 워커 노드에서 실행되는 프로세스이며, 태스크를 실행하고 데이터를 메모리나 디스크에 둡니다. Spark 용어집은 익스큐터를 "keeps data in memory or disk storage across them"이라고 설명합니다. 각 애플리케이션은 자기 익스큐터를 갖습니다.

- 익스큐터는 계산과 데이터 저장을 맡습니다.
- 익스큐터는 여러 스레드로 태스크를 실행합니다.
- 드라이버가 익스큐터에 태스크를 보냅니다.

### 2.3 클러스터 매니저 (Cluster manager)

클러스터 매니저는 클러스터의 자원을 얻는 외부 서비스입니다. Spark 문서는 독립형(standalone), YARN, Kubernetes를 예로 듭니다. 드라이버는 클러스터 매니저에 연결해 노드에 익스큐터를 할당받습니다.

Databricks 클래식 컴퓨트와 서버리스 컴퓨트는 이 자원 할당을 플랫폼이 관리합니다. 사용자는 노드 유형, 워커 수, 오토스케일링 범위로 간접 조정합니다.

### 2.4 Databricks 클러스터의 정의

Databricks 공식 문서는 클러스터를 "A set of computation resources and configurations on which you run notebooks and jobs"로 정의합니다. 같은 문서가 Databricks Runtime에 Apache Spark가 포함되고, 테이블은 Spark SQL과 Spark API로 조회한다고 설명합니다.

### 2.5 변환과 액션

Spark RDD 프로그래밍 가이드는 연산을 두 종류로 나눕니다.

| 종류 | 정의 (Spark 가이드 원문 요약) | 예 |
|---|---|---|
| 변환 (Transformation) | 기존 데이터셋에서 새 데이터셋을 만듭니다 | `map`, `filter` |
| 액션 (Action) | 데이터셋에서 계산을 수행한 뒤 값을 드라이버 프로그램에 돌려줍니다 | `reduce`, `collect` |

DataFrame API도 같은 원리입니다. `select`, `filter`, `groupBy`는 변환이고, `count`, `collect`, `show`, `write`는 액션입니다.

### 2.6 지연 실행 (Lazy evaluation)

Spark 가이드의 원문은 다음과 같습니다. "All transformations in Spark are lazy, in that they do not compute their results right away. Instead, they just remember the transformations applied to some base dataset (e.g. a file)." 그리고 "The transformations are only computed when an action requires a result to be returned to the driver program."

즉, 변환은 계산을 하지 않고 "어떤 변환을 적용했는지"만 기록합니다. 액션이 실행될 때 기록된 변환 전체를 계산합니다. 이 설계 덕분에 Spark는 실행 계획을 최적화할 수 있습니다.

```python
# 지연 실행을 보여 주는 예시입니다. 테이블 이름은 워크스페이스에 맞게 바꾸십시오.
from pyspark.sql import functions as F

orders = spark.table("main.sales.orders")                       # 변환이 아닌 참조: 계산 없음
large = orders.where(F.col("amount") > 1000).select("order_id", "amount")  # 변환: 계획만 기록
large.explain()                                                 # 실행 계획을 출력합니다 (계산 없음)

n = large.count()                                               # 액션: 이 시점에 실제 계산
print(n)
```

> **참고** `explain()`은 실행 계획만 출력하고 데이터를 계산하지 않습니다. 쿼리가 의도한 계획대로 세워졌는지 확인할 때 씁니다.

### 2.7 지연 실행과 캐싱

지연 실행 때문에 같은 DataFrame을 여러 액션에서 쓰면 액션마다 계보를 다시 계산합니다. 중간 결과를 재사용하려면 캐싱이 필요합니다.

서버리스 컴퓨트의 DataFrame 캐싱(Public Preview)은 `df.cache()`나 `df.persist()`를 호출하면 "Databricks computes it immediately and stores a snapshot for the session"이라고 문서가 설명합니다. 즉 서버리스 캐시는 호출 시점에 계산해 세션 스냅샷을 만든다는 것이 문서 설명입니다. 캐시를 쓰는 조건과 제한은 [서버리스 제약과 지원 기능](serverless-limitations.md) 페이지의 캐시 항목을 따르십시오.

```python
# 서버리스 DataFrame 캐싱 (Public Preview): 같은 DataFrame을 여러 번 쓰는 경우
base = spark.table("main.sales.orders").where("order_status = 'COMPLETED'").cache()

by_region = base.groupBy("region").count()
by_day = base.groupBy("order_date").count()

by_region.write.mode("overwrite").saveAsTable("main.sales.orders_by_region")
by_day.write.mode("overwrite").saveAsTable("main.sales.orders_by_day")

base.unpersist()
```

## 3. 어떻게 쓰는가 (컴퓨트 설정과 연결하기)

Spark 구조를 컴퓨트 설정과 연결하면 다음과 같습니다.

| 문제 증상 | 먼저 볼 곳 | 조정 방향 |
|---|---|---|
| 드라이버 메모리 부족 오류 | `collect`, `toPandas` 호출 위치 | 결과를 드라이버로 가져오지 말고 테이블로 쓰기 |
| 워커는 놀고 있는데 느림 | 셔플 크기와 파티션 수 | 파티션 설계와 조인 키 검토 |
| 첫 액션이 유독 느림 | 지연 실행으로 밀린 전체 계산 | 중간 결과 저장이나 캐싱 검토 |
| 대량 처리 중 익스큐터 실패 | 익스큐터 로그와 메모리 | 워커 노드 유형과 오토스케일링 범위 조정 |

서버리스 컴퓨트에서는 Spark UI와 Spark 로그를 쓸 수 없습니다. 대신 쿼리 프로파일과 클라이언트 쪽 로그를 씁니다. 자세한 제약은 [서버리스 제약과 지원 기능](serverless-limitations.md) 페이지에 있습니다.

## 4. 트레이드오프

| 설계 선택 | 장점 | 비용 |
|---|---|---|
| 드라이버에 결과 모으기 (`collect`) | 로컬에서 바로 다룰 수 있음 | 드라이버 메모리 한도가 전체 데이터 크기를 제한 |
| 결과를 테이블로 쓰기 (`write`) | 익스큐터가 병렬로 처리하고 재사용 가능 | 저장 비용과 쓰기 시간 |
| 중간 결과 캐싱 | 여러 액션에서 재계산 방지 | 메모리 사용과 세션 수명 관리 |
| 변환을 길게 쌓기 | 최적화 여지가 큼 | 액션 시점에 실행이 몰려 디버깅이 어려움 |

## 5. 주의사항

- **`collect()`와 `toPandas()`는 결과가 작을 때만 쓰십시오.** 큰 데이터는 드라이버 메모리를 초과합니다.
- **지연 실행을 기억하십시오.** 변환 줄이 빨리 끝나는 것은 계산이 끝났다는 뜻이 아닙니다. 실행 시간은 액션에서 측정합니다.
- **같은 DataFrame을 여러 번 쓰면 캐싱이나 저장을 검토하십시오.** 여러 액션에서 계보를 반복 계산하면 시간이 배로 늘 수 있습니다.
- **서버리스와 클래식의 Spark 설정 차이를 확인하십시오.** 서버리스는 허용된 Spark 설정만 세션 단위로 지정할 수 있습니다.
- **Spark 기초 용어는 Apache Spark 공식 문서를 기준으로 하십시오.** Databricks 문서는 드라이버, 익스큐터, 지연 실행을 상세히 정의하지 않고 Apache Spark 문서를 참조합니다.

## 참고 문서

- [Apache Spark 클러스터 개요 (드라이버·익스큐터·클러스터 매니저)](https://spark.apache.org/docs/latest/cluster-overview.html)
- [Apache Spark RDD 프로그래밍 가이드 (변환과 액션, 지연 실행)](https://spark.apache.org/docs/latest/rdd-programming-guide.html)
- [Databricks 개념 (AWS)](https://docs.databricks.com/aws/en/getting-started/concepts)
- [DataFrame caching on serverless compute (AWS)](https://docs.databricks.com/aws/en/compute/serverless/dataframe-cache)
- [Serverless compute limitations (AWS)](https://docs.databricks.com/aws/en/compute/serverless/limitations)
