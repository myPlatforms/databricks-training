# 데이터 모델링 기초

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100

데이터 모델링은 분석에 쓸 테이블을 어떤 구조로 나눌지 정하는 작업입니다. 이 페이지는 웨어하우스에서 가장 많이 쓰는 **스타 스키마(Star schema)** 와 **스노우플레이크 스키마(Snowflake schema)** 를 설명하고, Unity Catalog에서 **PK/FK 제약(Primary key·Foreign key constraint)** 을 어떻게 선언하는지, 그리고 그 제약이 무엇을 보장하지 않는지를 정리합니다.

> **참고** 공식 Databricks 문서는 골드 계층의 데이터 마트가 차원 모델(dimensional model)이라고 설명합니다. 스타와 스노우플레이크라는 이름과 구조 비교는 문서의 특정 페이지가 아니라 일반 모델링 지식입니다. 이 페이지는 두 방식을 일반 지식으로 설명하고, PK/FK 문법과 상태만 공식 문서 근거로 씁니다.

## 왜 필요한가

원천 시스템의 테이블은 업무 처리에 맞춰 정규화되어 있어 조인이 많습니다. 분석가가 이 구조를 그대로 쓰면 쿼리가 길어지고, 같은 정의(예: "매출")가 쿼리마다 다르게 해석됩니다. 차원 모델링은 **측정값(사실)과 그 측정값을 설명하는 맥락(차원)을 나누어**, 분석 쿼리를 단순하고 일관되게 만듭니다.

| 문제 | 모델링이 주는 효과 |
|---|---|
| 조인이 많아 쿼리가 복잡 | 팩트 한 개와 차원 몇 개의 단순한 조인 구조 |
| 같은 지표가 쿼리마다 다름 | 팩트 테이블에 측정값을 한 번 정의 |
| 기간·지역·상품 같은 축이 제각각 | 차원 테이블에 축을 공통으로 정의 |

## 어떻게 동작하는가

### 팩트와 차원

| 구분 | 역할 | 예시 |
|---|---|---|
| 팩트 테이블(Fact table) | 발생한 사건을 행으로 기록. 금액, 수량 같은 측정값을 가짐 | 주문 한 건당 한 행, 판매 수량·금액 |
| 차원 테이블(Dimension table) | 사실을 설명하는 맥락을 가짐. 이름, 분류, 속성 | 고객, 상품, 날짜, 지점 |

팩트의 각 행은 차원 키(보통 surrogate key 또는 자연 키)를 통해 차원 테이블을 가리킵니다.

### 스타 스키마

팩트 테이블 하나를 중심에 두고, 차원 테이블 여러 개가 **직접** 연결되는 구조입니다. 차원 테이블은 정규화하지 않고 한 테이블에 속성을 평평하게 둡니다.

| 테이블 | 주요 열 | 연결 |
|---|---|---|
| `fact_sales` | `date_key`, `customer_key`, `product_key`, `quantity`, `amount` | 각 차원 키 |
| `dim_date` | `date_key`, `day`, `month`, `quarter`, `year` | `fact_sales.date_key` |
| `dim_customer` | `customer_key`, `name`, `region`, `segment` | `fact_sales.customer_key` |
| `dim_product` | `product_key`, `product_name`, `category`, `brand` | `fact_sales.product_key` |

장점은 조인 깊이가 얕아 쿼리가 단순하고, 분석 도구가 구조를 이해하기 쉽다는 점입니다. 단점은 차원 테이블에 값이 중복되어 저장된다는 점입니다.

### 스노우플레이크 스키마

차원 테이블을 다시 정규화해 하위 테이블로 나눈 구조입니다. 예를 들어 `dim_product`가 `dim_category`를 참조하도록 나눕니다.

| 테이블 | 주요 열 | 연결 |
|---|---|---|
| `fact_sales` | `product_key`, `amount` 등 | `dim_product` |
| `dim_product` | `product_key`, `product_name`, `category_key` | `dim_category` |
| `dim_category` | `category_key`, `category_name`, `category_group` | `dim_product.category_key` |

장점은 중복이 줄고 차원의 계층 변경을 한 곳에서 관리할 수 있다는 점입니다. 단점은 조인이 늘어나 쿼리가 복잡해진다는 점입니다.

### 비교

| 기준 | 스타 스키마 | 스노우플레이크 스키마 |
|---|---|---|
| 차원 구조 | 평평함(비정규화) | 정규화 |
| 조인 수 | 적음 | 많음 |
| 저장 중복 | 있음 | 적음 |
| 쿼리 단순성 | 높음 | 낮음 |
| 차원 속성 변경 관리 | 여러 행에 반영 | 한 테이블에서 관리 |
| BI 도구와의 궁합 | 일반적으로 좋음 | 조인 설계가 필요 |

> **참고** 웨어하우스에서는 스타 스키마를 기본으로 두고, 차원의 계층이 자주 바뀌는 경우에만 일부를 정규화하는 절충이 흔합니다. 이 판단은 쿼리 패턴과 변경 빈도를 근거로 합니다.

### 실버와 골드 계층에서의 위치

공식 문서의 데이터 웨어하우징 아키텍처는 실버 계층에서 3정규형(3NF) 또는 Data Vault 모델이 자주 쓰인다고 설명합니다. 골드 계층의 데이터 마트는 차원 모델입니다. 즉, 정규화된 통합 데이터(실버)를 차원 모델(골드)로 가공하는 흐름이 일반적입니다.

## 어떻게 쓰는가

### PK와 FK 선언

공식 문서의 제약 페이지는 테이블 생성 시 인라인으로 선언하는 문법을 보여줍니다.

```sql
CREATE TABLE main.dw.dim_customer (
  customer_key BIGINT NOT NULL,
  name STRING,
  region STRING,
  CONSTRAINT dim_customer_pk PRIMARY KEY (customer_key)
);

CREATE TABLE main.dw.fact_sales (
  sale_id BIGINT NOT NULL,
  customer_key BIGINT,
  amount DECIMAL(12, 2),
  CONSTRAINT fact_sales_pk PRIMARY KEY (sale_id),
  CONSTRAINT fact_sales_customer_fk FOREIGN KEY (customer_key)
    REFERENCES main.dw.dim_customer (customer_key)
);
```

기존 테이블에는 `ALTER TABLE ... ADD CONSTRAINT`로 추가합니다. 문서 예시는 다음과 같습니다.

```sql
ALTER TABLE main.default.S ADD CONSTRAINT s_t_fk FOREIGN KEY(fk1, fk2) REFERENCES main.default.T;
```

> **주의** `CTAS`(CREATE TABLE AS SELECT) 문장은 제약 절을 지원하지 않는다고 문서에 명시되어 있습니다. 제약이 필요한 테이블은 `CREATE TABLE`로 먼저 만들고 데이터를 적재하거나, `ALTER TABLE`로 나중에 추가합니다.

### 지원 상태와 요구 사항 (문서 기준)

| 제약 | 적용 대상 | 상태 |
|---|---|---|
| PRIMARY KEY, FOREIGN KEY | Unity Catalog와 Delta Lake 테이블, Databricks Runtime 13.3 LTS 이상 | 문서: "GA in Databricks Runtime 15.2 and above" |
| UNIQUE | Unity Catalog와 Delta Lake 테이블, Databricks SQL과 Databricks Runtime 18.2 이상 | Public Preview |

### 제약의 성격

공식 문서는 PK, FK, UNIQUE 제약을 **정보성(informational only)** 으로 설명하며, **강제되지 않는다(aren't enforced)** 고 명시합니다. 즉 제약을 선언해도 중복 키 삽입이나 참조 무결성 위반을 막지 않습니다. 대신 제약은 다음 목적으로 쓰입니다.

- Unity Catalog에서 테이블 사이의 관계를 사용자가 이해하도록 돕습니다. 문서는 실버 계층 설명에서 이 점을 근거로 PK/FK 지정을 권장합니다.
- 관계 정보를 BI 도구와 메타데이터 탐색에 전달합니다.

FK는 다른 테이블의 PK나 UNIQUE 제약을 참조해야 합니다. UNIQUE 열은 NULL을 허용할 수 있는데, 문서는 NULL 값이 서로 다른 값으로 취급된다고 설명합니다. 문서의 예시는 PK 열을 `NOT NULL`로 선언하지만, PK의 NOT NULL 요구를 명시적으로 서술하지는 않습니다. 실무에서는 PK 열에 `NOT NULL`을 함께 둡니다.

## 트레이드오프

| 선택 | 장점 | 고려할 점 |
|---|---|---|
| 스타 스키마 | 쿼리 단순, BI 친화적 | 차원 중복 저장, 차원 변경 시 다량 갱신 |
| 스노우플레이크 스키마 | 정규화로 중복 최소, 계층 관리 용이 | 조인 증가, 쿼리 복잡 |
| PK/FK 선언 | 관계 문서화, 도구 이해도 향상 | 강제되지 않으므로 데이터 품질 검사는 별도 필요 |
| 제약 없음 | 설계 부담 없음 | 관계 정보를 BI와 메타데이터에 전달하지 못함 |

## 주의사항

- **제약은 품질 검사를 대체하지 않습니다.** PK 중복이나 FK 누락은 제약이 있어도 적재 단계에서 검사해야 합니다.
- **CTAS로 만든 테이블에는 제약 절을 쓸 수 없습니다.** 생성 순서를 설계에 반영합니다.
- **UNIQUE는 Public Preview입니다.** 운영 설계에는 상태를 반영합니다.
- **차원 키 정책을 정합니다.** 자연 키를 쓸지, 대리 키를 쓸지, 차원 변경 이력을 어떻게 보관할지는 설계 단계에서 정합니다. 이 페이지는 이력 관리 기법을 자세히 다루지 않습니다.
- **팩트 행의 입도(grain)를 먼저 정합니다.** "주문 한 건당 한 행인지, 주문 항목당 한 행인지"가 정해져야 측정값과 차원 키가 결정됩니다.

## 참고 문서

- [Data warehousing architecture (Databricks SQL concepts)](https://docs.databricks.com/aws/en/sql/get-started/data-warehousing-concepts)
- [Constraints (PRIMARY KEY, FOREIGN KEY)](https://docs.databricks.com/aws/en/tables/constraints)
- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
