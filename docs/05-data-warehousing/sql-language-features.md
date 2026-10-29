# SQL 언어 기능

> 기준일: 2026-10-28 · 근거: 공식 문서

Databricks SQL의 SQL 언어 레퍼런스에는 분석 쿼리를 간결하게 만드는 기능이 많습니다. 이 페이지는 실무에서 자주 쓰는 네 가지를 다룹니다. 행 묶음 단위 계산을 하는 **윈도 함수(Window functions)**, 행과 열을 바꾸는 **PIVOT과 UNPIVOT**, 윈도 함수 결과를 바로 거르는 **QUALIFY 절**, 값을 안전하게 바인딩하는 **파라미터 마커(Parameter markers)** 입니다.

## 왜 필요한가

분석 쿼리는 "각 부서의 최고 연봉자", "분기별 매출을 열로 펼친 표", "중복 중 최신 행만" 같은 요구가 자주 나옵니다. 이를 서브쿼리와 임시 테이블로 풀면 문장이 길어지고, 같은 테이블을 여러 번 읽어 비용도 늘어납니다. 위 기능들은 이 패턴을 한 문장으로 표현하게 해줍니다.

| 요구 | 기존 방식 | 이 장의 기능 |
|---|---|---|
| 그룹 안에서 순위 매기기 | 자기 조인이나 상관 서브쿼리 | 윈도 함수 `RANK() OVER (...)` |
| 바로 앞 행 값 가져오기 | 자기 조인 | `LAG`, `LEAD` |
| 윈도 결과로 행 거르기 | 서브쿼리로 한 번 감싸기 | `QUALIFY` |
| 행 값을 열로 펼치기 | `CASE WHEN` 나열 | `PIVOT` |
| 열을 행으로 되돌리기 | `UNION ALL` 나열 | `UNPIVOT` |
| 문자열 결합으로 값 넣기 | SQL 인젝션 위험 | 파라미터 마커 |

## 1. 윈도 함수

### 동작 원리

공식 레퍼런스는 윈도 함수가 행 묶음(윈도)에 대해 계산하고, 각 행마다 그 묶음을 기준으로 값을 돌려준다고 설명합니다. 이동 평균, 누적 통계, 상대 위치의 값을 가져오는 작업에 적합합니다.

윈도 함수는 `OVER` 절을 가지며, 그 안에서 다음을 지정합니다.

| 구성 요소 | 의미 |
|---|---|
| `PARTITION BY` | 행을 묶는 기준. 생략하면 모든 행이 한 파티션 |
| `ORDER BY` | 파티션 안에서 행 순서. `SORT BY`는 별칭 |
| 프레임 절 `ROWS` 또는 `RANGE` | 파티션 안에서 계산에 쓸 행의 범위 |

공식 문서는 함수를 세 범주로 나눕니다.

| 범주 | 예 | 제약 (문서 기준) |
|---|---|---|
| 순위(Ranking) | `RANK`, `DENSE_RANK` | `ORDER BY`가 필요하며 프레임 절을 쓸 수 없음 |
| 분석(Analytic) | `LAG`, `LEAD` | 현재 행을 기준으로 다른 행의 값에 접근 |
| 집계(Aggregate) | `MIN` 등 집계 함수 | `FILTER` 절을 포함할 수 없음 |

### 예시

```sql
-- 부서별 연봉 순위
SELECT
  dept,
  employee,
  salary,
  RANK() OVER (PARTITION BY dept ORDER BY salary) AS rank
FROM main.hr.employees;

-- 같은 부서에서 바로 앞 행의 연봉
SELECT
  dept,
  employee,
  salary,
  LAG(salary) OVER (PARTITION BY dept ORDER BY salary) AS prev_salary
FROM main.hr.employees;
```

> **주의** 위 두 예시의 `main.hr.employees`는 설명용 이름입니다. 실제 테이블에 맞춰 바꿔 실행하십시오.

## 2. QUALIFY 절

### 동작 원리

`QUALIFY`는 윈도 함수의 결과를 기준으로 행을 거르는 절입니다. 문법은 `QUALIFY boolean_expression` 하나입니다. 공식 문서는 윈도 함수가 `SELECT` 목록이나 `QUALIFY` 절 안에 있어야 한다고 설명합니다. 집계 함수는 `QUALIFY` 안에 쓸 수 없습니다.

적용 범위는 Databricks SQL과 Databricks Runtime 10.4 LTS 이상입니다.

### 예시

```sql
-- 모델별로 수량 순위 1위인 행만 남긴다
SELECT city, car_model
FROM dealer
QUALIFY RANK() OVER (PARTITION BY car_model ORDER BY quantity) = 1;
```

중복 행 제거에도 자주 씁니다. 같은 고객의 가장 최근 주문 한 건만 남기는 패턴입니다.

```sql
SELECT customer_id, order_id, order_ts
FROM main.sales.orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_ts DESC) = 1;
```

> **참고** 위 `ROW_NUMBER` 예시는 `QUALIFY` 패턴을 보이기 위한 설명용 쿼리입니다. 공식 윈도 함수 페이지의 예시는 `RANK`와 `LAG`를 사용합니다.

## 3. PIVOT과 UNPIVOT

### PIVOT: 행을 열로 펼치기

`PIVOT`은 지정한 열의 고유 값을 회전시켜 새 열로 만듭니다. 적용 범위는 Databricks SQL과 Databricks Runtime입니다.

문법의 핵심은 다음과 같습니다.

```
PIVOT ( aggregate_expression [ [ AS ] agg_column_alias ] [, ...]
        FOR column_list IN ( expression_list ) )
```

공식 문서의 예시는 `sales` 뷰에서 분기(quarter)별 매출을 열로 펼칩니다.

```sql
SELECT year, region, q1, q2, q3, q4
FROM sales
PIVOT (
  SUM(sales) AS sales
  FOR quarter IN (1 AS q1, 2 AS q2, 3 AS q3, 4 AS q4)
);
```

**PIVOT의 제약 (문서 기준)**

| 제약 | 설명 |
|---|---|
| 값은 리터럴이어야 함 | `1 + 0` 같은 비리터럴 값은 `NON_LITERAL_PIVOT_VALUES` 오류 |
| 타입 호환 | 피벗 값과 열 타입은 최소 공통 타입(least common type)이 있어야 함. 아니면 `PIVOT_VALUE_DATA_TYPE_MISMATCH` |
| 식의 개수 | 식 튜플의 개수는 열 목록의 열 개수와 같아야 함 |
| 집계 인자 | `aggregate_expression`의 열 참조는 집계 함수의 인자여야 함 |

### UNPIVOT: 열을 행으로 되돌리기

`UNPIVOT`은 여러 열을 행으로 바꿉니다. 적용 범위는 Databricks SQL과 Databricks Runtime 12.2 LTS 이상입니다.

```sql
-- 분기 열 q1..q4를 quarter, sales 두 열로 바꾼다
SELECT *
FROM sales
UNPIVOT INCLUDE NULLS (
  sales FOR quarter IN (q1 AS `Jan-Mar`, q2 AS `Apr-Jun`, q3 AS `Jul-Sep`, q4 AS `Oct-Dec`)
);
```

- `INCLUDE NULLS`를 쓰면 값 열이 NULL인 행도 결과에 남습니다.
- 생략하거나 `EXCLUDE NULLS`를 쓰면 NULL 행이 빠집니다. 공식 문서는 기본값을 `EXCLUDE NULLS`로 명시합니다.
- 대응되는 열의 타입이 호환되지 않으면 `UNPIVOT_VALUE_DATA_TYPE_MISMATCH` 오류가 납니다.

## 4. 파라미터 마커

### 동작 원리

파라미터 마커는 SQL 문장의 값 자리에 두는 **타입이 있는 자리표시자** 입니다. 값은 호출하는 쪽(API)이 따로 전달합니다. 공식 문서는 값을 SQL 구조와 분리해 SQL 인젝션을 막는다고 설명합니다.

| 형태 | 문법 | 지원 시작 버전 (문서 기준) | 값 전달 방식 |
|---|---|---|---|
| 명명된 마커 | `:name` | Databricks Runtime 12.1 이상 | 이름-값 쌍 |
| 이름 없는 마커 | `?` | Databricks Runtime 13.3 이상 | 순서가 있는 배열. 마커 하나가 값 하나를 소비 |

규칙은 다음과 같습니다.

- 명명된 마커와 이름 없는 마커는 한 문장에 섞어 쓸 수 없습니다.
- 값이 바인딩되지 않은 마커는 `UNBOUND_SQL_PARAMETER` 오류를 냅니다.
- 명명된 마커의 `:`는 열 이름과 네임스페이스를 구분하기 위해 필수입니다.

### 쓸 수 있는 위치

공식 문서는 Databricks Runtime 버전에 따라 허용 위치가 다르다고 설명합니다.

| 버전 | 허용 위치 |
|---|---|
| 17.3 LTS 이하 | 식(expression)에서만 허용. 생성된 열, `DEFAULT` 정의, 뷰, SQL 함수 같은 DDL에서는 불가. `IDENTIFIER` 절은 예외 |
| 18.0 이상 | 해당 타입의 리터럴이 허용되는 모든 자리. `LOCATION` 같은 DDL 위치 포함 |

Databricks Runtime 18.0 미만에서 DDL에 값을 넣어야 하면 `EXECUTE IMMEDIATE`와 문자열 연결을 쓰는 우회 방식이 문서에 나옵니다. 마커는 문자열 리터럴 안에 넣을 수 없습니다.

### 예시

SQL에서는 `EXECUTE IMMEDIATE`와 `USING` 절을 씁니다.

```sql
-- 명명된 마커를 USING 절로 바인딩한다
EXECUTE IMMEDIATE 'SELECT :x * :x AS square'
  USING 15.0 AS x;
```

공식 문서의 `EXECUTE IMMEDIATE` 예시는 `INTERVAL '3' HOURS AS later`처럼 시간 값도 같은 방식으로 바인딩합니다. Python에서는 `spark.sql()`에 `args` 인자를 넘깁니다.

```python
# 명명된 마커는 dict로, 이름 없는 마커는 list로 값을 넘긴다
spark.sql("SELECT :x * :x AS square", args={"x": 15.0}).show()
spark.sql("SELECT ? * ? AS square", args=[15.0, 15.0]).show()
```

> **참고** 식별자(테이블 이름 등)를 바꿔 넣어야 할 때는 `IDENTIFIER` 절을 씁니다. 문서는 `IDENTIFIER` 절이 객체 이름에만 쓰이며, `LOCATION` 같은 문자열 절에는 쓸 수 없다고 명시합니다.

## 트레이드오프

| 기능 | 장점 | 주의할 점 |
|---|---|---|
| 윈도 함수 | 자기 조인 없이 행 단위 맥락 계산 | 파티션이 크면 정렬 비용이 큼. 프로필에서 Sort·Shuffle 확인 |
| QUALIFY | 윈도 결과 필터를 한 단계로 | 집계 함수와 함께 쓸 수 없음. 이식성이 낮은 방언이 될 수 있음 |
| PIVOT | 긴 `CASE WHEN` 나열을 줄임 | 피벗 값을 리터럴로 고정해야 함. 새 값이 생기면 문장 수정 필요 |
| UNPIVOT | 열 구조를 분석에 맞게 정규화 | NULL 처리 기본값(EXCLUDE NULLS)을 의식해야 함 |
| 파라미터 마커 | 인젝션 방지, 쿼리 재사용 | 런타임 버전별 허용 위치가 다름 |

## 주의사항

- **윈도 함수의 프레임 절은 문법을 먼저 확인합니다.** 순위 함수는 프레임 절을 쓸 수 없으므로 오류가 납니다.
- **`QUALIFY`에 집계 함수를 넣지 않습니다.** 집계가 필요하면 서브쿼리나 CTE로 먼저 집계합니다.
- **PIVOT의 피벗 값은 DISTINCT 목록과 맞춰 관리합니다.** 값이 추가되는 데이터라면 열 목록이 자동으로 늘지 않는다는 점을 설계에 반영합니다.
- **문자열 연결로 SQL을 만들지 않습니다.** 값은 항상 파라미터로 전달합니다. 식별자만 `IDENTIFIER`로 다룹니다.
- **런타임 버전을 확인합니다.** 파라미터 마커의 DDL 허용 여부는 Databricks Runtime 18.0을 기준으로 달라집니다.

## 참고 문서

- [Window functions](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-window-functions)
- [QUALIFY clause](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-qualify)
- [PIVOT clause](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-pivot)
- [UNPIVOT clause](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-unpivot)
- [Parameter markers](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-parameter-marker)
- [SQL language reference](https://docs.databricks.com/aws/en/sql/language-manual/)
