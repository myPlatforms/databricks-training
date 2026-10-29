# 메트릭 뷰 소비하기: 대시보드·Genie Agent에서 쓰기

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

> **참고** 메트릭 뷰의 **정의 방식**(YAML, SQL DDL), 권한, 공유, 거버넌스는 [06장 메트릭 뷰의 거버넌스](../06-unity-catalog/metric-views-governance.md)에서 다룹니다. 이 페이지는 정의된 메트릭 뷰를 **쓰는 쪽**, 즉 쿼리, 대시보드, Genie Agent, 알림에서 소비하는 방법만 다룹니다.

## 한눈에 보기

**메트릭 뷰**(Metric view)는 측정값(measure)과 차원(dimension)을 한 번 정의해 두고, 소비자가 원하는 차원으로 묶어 측정값을 계산하는 UC 객체입니다. 일반 뷰는 집계와 묶음 기준을 만들 때 고정하지만, 메트릭 뷰는 쿼리 시점에 사용자가 고른 차원으로 집계합니다.

소비 경로는 다섯 가지입니다.

| 소비 경로 | 방식 | 측정값 접근 | 비고 |
|---|---|---|---|
| SQL 편집기 | 뷰처럼 `SELECT` | `MEASURE()` 함수 | 모든 측정값은 `MEASURE()`로 감싸야 함 |
| AI/BI 대시보드 | 데이터셋으로 선택 | 자동으로 `MEASURE()` 적용 | 동의어와 서식 메타데이터가 UI에 표시 |
| Genie Agent | 에이전트의 데이터 소스로 추가 | 에이전트가 생성 | 메트릭 뷰도 에이전트당 한도 50개에 포함 |
| 알림(Alerts) | 메트릭 뷰 측정값을 조건으로 | 쿼리 안에서 `MEASURE()` | [8페이지](alerts.md) |
| 외부 BI 도구 | 도구별 연결 패턴 | 도구마다 다름 | [9페이지](external-bi-tools.md) |

## 1. 왜 필요한가

### 이전 방식의 한계

지표 정의가 대시보드와 노트북에 흩어지면 같은 지표가 다르게 계산됩니다. 일반 뷰로 해결하려면 차원 조합마다 뷰를 따로 만들어야 합니다. 예를 들어 날짜, 지역, 제품 카테고리의 조합을 모두 원하면 뷰 수가 기하급수적으로 늘어납니다.

메트릭 뷰는 정의를 하나로 두고, 소비자가 차원을 고르게 합니다. 공식 메트릭 뷰 문서도 일반 뷰와의 차이를 같은 방식으로 설명합니다.

| 항목 | 일반 뷰 | 메트릭 뷰 |
|---|---|---|
| 집계 방식 | 생성 시 `GROUP BY`와 집계가 고정 | 쿼리 시점에 고른 차원으로 집계 |
| 정의 단위 | 저장된 SQL 쿼리 | 측정값과 차원의 의미 정의 |
| 차원 조합 | 조합마다 뷰가 필요 | 하나의 정의로 여러 조합 |

## 2. 어떻게 동작하는가

### 쿼리 규칙

공식 "Query metric views" 문서가 설명하는 규칙은 다음과 같습니다.

- **모든 측정값은 `MEASURE` 집계 함수로 감싸야 합니다.** Databricks Runtime 18.1 이상에서는 `AGG`도 쓸 수 있습니다.
- **`SELECT *`를 쓸 수 없습니다.** 각 차원과 측정값을 개별 열로 명시해야 합니다.
- **묶기** 는 `GROUP BY ALL`을 쓰는 예시가 문서에 있습니다. 필터는 일반 `WHERE`로 씁니다.
- **다른 테이블과 직접 조인할 수 없습니다.** 메트릭 뷰 쿼리를 CTE로 감싸고, 그 CTE 결과를 조인해야 합니다. 문서는 "Metric views cannot be directly joined with other tables at query time."이라고 명시합니다.
- **매개변수가 있는 메트릭 뷰** 는 명명된 인자(named argument)를 쓰는 테이블 반환 함수 형태로 호출합니다.
- 정의 확인은 `DESCRIBE TABLE EXTENDED ... AS JSON`으로 합니다. 결과에 YAML 정의와 에이전트 메타데이터가 나옵니다.

### 소비자별 동작

| 소비자 | 동작 |
|---|---|
| SQL 편집기 | SQL 웨어하우스 또는 지원 런타임의 컴퓨트에 연결해 쿼리. 문서는 "like standard views from any SQL editor"라고 설명 |
| AI/BI 대시보드 | `MEASURE()`를 자동으로 적용. 동의어와 서식이 UI에 나타남 |
| Genie Agent | 메트릭 뷰로 AI 기반 분석을 가능하게 함. 한도는 테이블·뷰와 합산 |
| 알림 | 측정값을 모니터링하고, 임계값을 넘으면 알림을 보냄 |
| 기타 도구 | 쿼리 프로파일링, JDBC·ODBC, 외부 BI 도구, Excel, Google Sheets |

문서는 노트북에서의 사용을 별도 항목으로 설명하지 않습니다. 노트북에서도 SQL 셀에서 같은 쿼리 규칙이 적용된다고 가정하지 말고 직접 확인하십시오.

## 3. 어떻게 쓰는가

### 기본 쿼리

아래 예시는 공식 문서의 형태(측정값 `MEASURE()`, `GROUP BY ALL`, `WHERE`)를 따른 예시입니다. 카탈로그 이름과 객체 이름은 가상의 이름입니다.

```sql
SELECT
  `Order Status`,
  MEASURE(`Order Count`)
FROM catalog.schema.orders_metrics
WHERE `Order Status` = 'Fulfilled'
GROUP BY ALL
```

정의를 확인하려면 다음을 실행합니다.

```sql
DESCRIBE TABLE EXTENDED catalog.schema.orders_metrics AS JSON
```

### 다른 테이블과 조인하기

조인은 메트릭 뷰를 CTE로 감싸 결과를 먼저 만든 뒤 수행합니다.

```sql
WITH m AS (
  SELECT
    `Order Status`,
    MEASURE(`Order Count`) AS order_count
  FROM catalog.schema.orders_metrics
  GROUP BY ALL
)
SELECT
  m.`Order Status`,
  m.order_count,
  s.status_label
FROM m
JOIN catalog.schema.status_labels AS s
  ON m.`Order Status` = s.status
```

`catalog.schema.status_labels`는 설명을 위한 가상의 테이블입니다.

### 매개변수가 있는 메트릭 뷰 쿼리

공식 문서는 매개변수가 있는 메트릭 뷰를 명명된 인자로 호출하는 형태를 보여 줍니다.

```sql
SELECT
  MEASURE(`Discounted Sales`),
  MEASURE(`Total Sales`)
FROM catalog.schema.metric_view(discount => 0.20)
```

대시보드에서는 같은 자리에 `:discount` 파라미터를 넣습니다. 자세한 설정은 [2페이지 대시보드 작성](dashboard-authoring.md)의 파라미터 절을 참고하십시오.

### 대시보드에서 메트릭 뷰 쓰기

1. 데이터셋을 만들 때 소스를 **Unity Catalog 테이블, 뷰 또는 메트릭 뷰** 로 고릅니다.
2. 메트릭 뷰 데이터셋에는 정의된 **모든 차원과 측정값** 이 포함됩니다.
3. 메트릭 뷰 데이터셋의 쿼리는 열을 빼거나 필터를 더하도록 편집할 수 없습니다. 필요한 필터는 대시보드 필터 위젯으로 처리합니다.

#### 로컬 메트릭 뷰

대시보드 안에서만 쓰는 메트릭 뷰도 만들 수 있습니다. 시각 인터페이스에서 필드, 측정값, 조인을 정의하고, UC에 게시하지 않습니다. 2026-08-20 릴리즈 노트에 따르면 로컬 메트릭 뷰는 **GA** 입니다.

2026-09-17 릴리즈 노트에 따르면 SQL 데이터셋을 우클릭 메뉴에서 로컬 메트릭 뷰로 바꿀 수 있고, 변환은 Genie Code가 돕습니다.

### Genie Agent에서 메트릭 뷰 쓰기

- 메트릭 뷰를 에이전트의 데이터 소스로 추가합니다. 에이전트당 테이블·뷰·메트릭 뷰 합계 한도는 **50개** 입니다.
- Genie Agent의 **Export to metric view** 는 에이전트 맥락에서 메트릭 뷰를 만듭니다.
- 2026-09-10 릴리즈 노트에 따르면 Genie Code는 대시보드를 만들 때 임시 SQL 데이터셋보다 **거버넌스된 메트릭 뷰를 우선** 합니다.

## 4. 트레이드오프

- **메트릭 뷰는 일관성을 주지만 쿼리 형태를 제한합니다.** `SELECT *`를 쓸 수 없고, 직접 조인도 안 됩니다. 기존 SQL을 옮길 때 이 규칙 때문에 CTE 구조가 늘어날 수 있습니다.
- **대시보드 데이터셋으로 쓰면 편하지만 편집 범위가 좁습니다.** 열 제외나 임의 필터를 쿼리에서 바꿀 수 없습니다.
- **로컬 메트릭 뷰는 빠르게 만들지만 UC 거버넌스 밖에 있습니다.** 여러 대시보드가 같은 정의를 써야 하면 UC에 게시한 메트릭 뷰가 맞습니다. 정의와 공유 설계는 06장을 참고하십시오.
- **구체화(Materialization)는 성능을 주지만 상태 라벨을 확인해야 합니다.** 2026-10-01 릴리즈 노트는 SQL 데이터셋과 로컬 메트릭 뷰의 구체화를 **Beta** 로 기록합니다. 메트릭 뷰 내보내기는 데이터셋 문서에서 **Public Preview** 로 표기됩니다.

### 권한 확인

메트릭 뷰 쿼리 문서는 필요한 권한을 명시하지 않습니다. 이 장은 `SELECT` 등 권한 요구 사항을 추측하지 않습니다. 권한 설계는 [06장 권한 모델과 소유권](../06-unity-catalog/privileges-and-ownership.md)과 메트릭 뷰 거버넌스 페이지에서 확인하십시오.

## 5. 주의사항

- **모든 측정값을 `MEASURE()`로 감쌉니다.** 하나라도 빠지면 쿼리가 실패합니다.
- **열을 명시합니다.** `SELECT *` 대신 차원과 측정값을 하나씩 씁니다.
- **다른 테이블과 조인할 때는 CTE로 감쌉니다.** 직접 조인 구문은 쓰지 않습니다.
- **대시보드 데이터셋은 메트릭 뷰 정의를 그대로 보여 줍니다.** 노출하고 싶지 않은 차원이 있으면 메트릭 뷰 정의 쪽에서 설계를 바꿉니다. 대시보드에서 열을 숨기는 방식으로는 데이터 노출을 막을 수 없습니다.
- **라벨을 확인합니다.** 로컬 메트릭 뷰는 GA, 구체화는 Beta, 메트릭 뷰 내보내기는 Public Preview로 기록되어 있습니다. 기능마다 다릅니다.
- **외부 BI 도구에서 메트릭 뷰를 쓰는 방식은 도구마다 다릅니다.** Power BI, Tableau의 연결 방식과 제약은 [9페이지](external-bi-tools.md)에서 확인하십시오.

## 참고 문서

- [메트릭 뷰 쿼리(Query metric views)](https://docs.databricks.com/aws/en/uc-semantics/metric-views/query)
- [외부 BI 도구와 메트릭 뷰(Use metric views with external BI tools)](https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools)
- [대시보드 데이터셋(Datasets)](https://docs.databricks.com/aws/en/dashboards/manage/data-modeling/datasets)
- [대시보드 한도(Dashboard limits)](https://docs.databricks.com/aws/en/dashboards/limits)
- [AI/BI 릴리즈 노트 (2026)](https://docs.databricks.com/aws/en/ai-bi/release-notes/2026)
- [메트릭 뷰의 거버넌스 (06장)](../06-unity-catalog/metric-views-governance.md)
