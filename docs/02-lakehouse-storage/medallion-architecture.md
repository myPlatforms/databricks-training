# 메달리온 아키텍처

> 기준일: 2026-10-28 · 근거: 공식 문서

메달리온 아키텍처(Medallion architecture)는 레이크하우스의 데이터를 **브론즈(Bronze)·실버(Silver)·골드(Gold)** 세 계층으로 나누어 점진적으로 정제하는 설계 패턴입니다. 원본에 가까운 데이터를 버리지 않고 보관하면서, 계층을 올라갈수록 데이터 품질과 사용 목적에 맞는 형태로 다듬습니다. 이 페이지는 각 계층의 정의와 경계, 계층별 테이블 설계, 그리고 계층 사이의 이동에 Delta Lake 기능을 쓰는 방법을 다룹니다.

## 1. 왜 필요한가

한 테이블에 원본, 정제, 집계를 모두 담으면 다음 문제가 생깁니다.

| 문제 | 원인 | 결과 |
|---|---|---|
| 원본을 되돌릴 수 없음 | 정제 과정에서 원본을 덮어씀 | 로직을 고쳐 재처리할 수 없음 |
| 스키마 변경에 취약 | 원천 시스템이 바뀌면 모든 소비자가 깨짐 | 파이프라인 장애 범위가 넓음 |
| 품질 책임이 흐림 | 검증과 집계가 한 곳에 섞임 | 어떤 데이터를 믿어도 되는지 불분명 |
| 소비자별 요구가 충돌 | 하나의 테이블을 모든 용도에 맞추려 함 | 테이블이 점점 복잡해짐 |

메달리온 아키텍처는 계층을 나눠 이 문제를 줄입니다. 공식 문서는 레이크하우스 데이터가 보통 수집, 처리·큐레이션, 서빙 계층을 거치며, 이를 메달리온 아키텍처라고 부른다고 설명합니다.

## 2. 어떻게 동작하는가

### 2.1 계층 정의

공식 문서가 정의하는 세 계층은 다음과 같습니다.

| 계층 | 공식 문서의 정의 | 핵심 목적 |
|---|---|---|
| 브론즈 (Bronze, raw) | 검증되지 않은 원시 데이터를 담음. 원래 상태를 유지하며 최소한의 검증만 수행 | 원본 보관과 재처리 기반 |
| 실버 (Silver, validated) | 검증되고 정제되고 풍부해진(enriched) 데이터. 정제, 중복 제거, 정규화가 일어나는 곳 | 신뢰할 수 있는 기준 데이터 |
| 골드 (Gold, enriched) | 분석, 대시보드, ML, 애플리케이션을 위해 고도로 정제된 뷰. 집계되고 비즈니스 요구에 맞춤 | 소비자 맞춤 서빙 |

### 2.2 계층별 책임

| 책임 | 브론즈 | 실버 | 골드 |
|---|---|---|---|
| 데이터 품질 | 최소 검증 | 오류와 불일치를 바로잡음 | 소비 목적에 맞는 지표 정의 |
| 스키마 | 원천 변화에 흔들리지 않도록 문자열, `VARIANT`, 바이너리로 보관을 권장 | 스키마 강제와 진화를 담당 | 소비자 계약에 맞춘 고정 스키마 |
| 형태 | 원천 그대로 | 정규화된 엔티티, 중복 제거 | 집계, 차원·사실 조합, 비즈니스 뷰 |
| 재처리 | 원본이 있어 다시 실행 가능 | 브론즈에서 다시 만들 수 있음 | 실버에서 다시 계산 |

> **참고** 공식 문서는 브론즈 테이블에서 대부분의 필드를 문자열, `VARIANT`, 바이너리로 저장하는 것을 권장합니다. 원천이 예고 없이 스키마를 바꿔도 적재가 깨지지 않게 하기 위해서입니다.

### 2.3 계층 사이의 흐름

| 단계 | 입력 | 처리 | 출력 |
|---|---|---|---|
| 수집 | 원천 파일, 이벤트 스트림, 외부 DB | 있는 그대로 적재 | 브론즈 테이블 |
| 정제 | 브론즈 테이블 | 타입 변환, 검증, 중복 제거, 키 기준 병합 | 실버 테이블 |
| 서빙 | 실버 테이블 | 집계, 조인, 지표 계산 | 골드 테이블 또는 뷰 |

각 계층은 앞 계층의 테이블을 입력으로 삼으므로, 계층 간 의존 관계를 파이프라인에서 명시해 두면 재처리 범위를 좁힐 수 있습니다.

## 3. 어떻게 쓰는가

### 3.1 브론즈: 원본 보관

브론즈 테이블은 원천의 컬럼을 문자열이나 `VARIANT`로 받아 두고, 적재 시각과 원천 정보만 덧붙이는 식으로 설계합니다.

```sql
CREATE TABLE main.bronze.orders_raw (
  raw_payload  VARIANT,
  source_file  STRING,
  ingested_at  TIMESTAMP
);
```

`VARIANT`는 반정형 데이터를 스키마 없이 저장하는 타입입니다. 원천 스키마 변화가 적재 단계에서 실패하지 않도록 하는 목적에 맞습니다.

### 3.2 실버: 검증과 정규화

실버 테이블은 명확한 스키마를 가집니다. 타입을 고정하고, 키 기준으로 중복을 제거한 뒤 `MERGE`로 병합하는 패턴이 일반적입니다. 아래 예는 브론즈의 중복 행을 최신 한 건으로 줄여 실버에 업서트합니다.

```sql
MERGE INTO main.silver.orders AS target
USING (
  SELECT order_id, customer, amount, order_ts
  FROM (
    SELECT
      CAST(raw_payload:order_id AS BIGINT)        AS order_id,
      CAST(raw_payload:customer AS STRING)        AS customer,
      CAST(raw_payload:amount AS DECIMAL(12, 2))  AS amount,
      CAST(raw_payload:order_ts AS TIMESTAMP)     AS order_ts,
      ROW_NUMBER() OVER (
        PARTITION BY CAST(raw_payload:order_id AS BIGINT)
        ORDER BY ingested_at DESC
      ) AS rn
    FROM main.bronze.orders_raw
  )
  WHERE rn = 1
) AS source
ON target.order_id = source.order_id
WHEN MATCHED THEN
  UPDATE SET *
WHEN NOT MATCHED THEN
  INSERT *;
```

> **주의** 공식 문서는 `MERGE`에서 대상 행 하나에 소스 행이 두 개 이상 매칭되면 실패할 수 있다고 설명합니다. 위 예처럼 소스를 키 기준으로 한 건으로 줄인 뒤 병합하십시오. 자세한 `MERGE` 규칙은 [Delta Lake 동작 원리](delta-lake-internals.md)에 있습니다.

실버 테이블에서 스키마 강제와 진화를 맡는다는 점도 기억하십시오. 새 컬럼이 원천에 생기면 `ALTER TABLE ... ADD COLUMN`으로 명시적으로 추가하는 것이 가장 예측하기 쉽습니다.

```sql
ALTER TABLE main.silver.orders ADD COLUMN channel STRING;
```

### 3.3 골드: 소비 목적에 맞춘 집계

골드 테이블은 실버를 집계해 소비자가 바로 쓰게 만듭니다.

```sql
CREATE TABLE main.gold.daily_sales AS
SELECT
  CAST(order_ts AS DATE) AS order_date,
  customer,
  SUM(amount)            AS total_amount,
  COUNT(*)               AS order_count
FROM main.silver.orders
GROUP BY CAST(order_ts AS DATE), customer;
```

골드를 뷰로 만들지 테이블로 만들지는 계산 비용과 갱신 주기에 따라 정합니다. 뷰는 조회 때마다 계산하고, 테이블은 적재 시점의 결과를 저장합니다.

### 3.4 파이프라인으로 계층 자동화

계층 사이의 이동을 수작업 SQL로 관리하면 실패 재처리와 의존성 관리가 어렵습니다. 공식 문서는 메달리온 계층을 Delta Lake와 **Lakeflow pipelines**(구 Delta Live Tables)로 구성하는 예를 제시합니다. 이 장에서는 파이프라인 세부 문법을 다루지 않습니다.

| 기능 | 상태 | 근거 |
|---|---|---|
| Lakeflow pipelines에서 관리형 테이블 생성과 추가(append flow) 쓰기 | Beta (릴리스 노트 2026-09-10) | 릴리스 노트 |
| 파이프라인 삭제 시 테이블 기본 보존 | 기본 동작 변경 (릴리스 노트 2026-09-25). 보존된 테이블은 조회만 가능하고 활성 파이프라인으로 옮기기 전까지 갱신 불가 | 릴리스 노트 |

> **참고** 파이프라인 관련 세부 문법과 상태는 자체 장 또는 공식 문서의 Lakeflow pipelines 페이지에서 확인하십시오.

## 4. 트레이드오프

| 항목 | 장점 | 비용·제약 |
|---|---|---|
| 계층 분리 | 재처리와 책임 경계가 명확 | 테이블 수가 늘고 저장 비용이 누적됨 |
| 브론즈 원본 보관 | 로직 변경 시 재처리 가능 | 원본을 보관하는 기간만큼 저장 비용 발생 |
| 실버 정규화 | 소비자가 믿고 쓸 수 있는 기준 데이터 | 정제 로직 유지보수가 필요 |
| 골드 집계 | 대시보드와 ML의 응답 시간 단축 | 원천 변화가 골드까지 전파되는 지연 발생 |

### 언제 메달리온을 그대로 따르지 않는가

- 원천이 이미 깨끗하고 단일 소비자만 있다면 계층을 두 개로 줄이거나 하나로 합칠 수 있습니다.
- 실시간 이벤트를 밀리초 단위로 처리해야 한다면 계층 간 이동 지연이 문제가 될 수 있습니다. 이 경우 스트리밍 테이블 설계를 따로 검토하십시오.

## 5. 주의사항

- **브론즈에 정제 로직을 넣지 않습니다.** 원본을 보관하는 목적이 깨지면 재처리 기반이 사라집니다.
- **실버에서 스키마를 명시합니다.** 타입을 고정하지 않으면 원천 변화가 실버를 통해 골드까지 번집니다.
- **스키마 자동 진화는 실버에서 신중하게 켭니다.** 공식 문서는 실버 계층에서 스키마 강제와 진화를 맡긴다고 설명합니다. 자동 진화를 켜기 전에 [Delta Lake 동작 원리](delta-lake-internals.md)의 세션 단위·쓰기 단위 설정 차이를 확인하십시오.
- **골드 소비자와의 계약을 기록합니다.** 골드 테이블의 컬럼 이름이나 지표 정의를 바꾸면 소비자가 깨집니다. 변경 이력은 `DESCRIBE HISTORY`로 확인할 수 있습니다 ([타임 트래블과 변경 데이터 피드](time-travel-and-cdf.md) 참고).
- **계층별로 보존 정책을 다르게 둡니다.** 브론즈는 재처리 기간만큼, 실버와 골드는 소비 요구에 맞춰 보존 기간을 정합니다. 이력과 파일 보존 설정은 [테이블 레이아웃 최적화](table-layout-optimization.md)의 `VACUUM` 절을 참고하십시오.
- **계층 간 CDF 소비에는 보존 창을 고려합니다.** 실버 변경을 골드가 증분으로 읽는다면, 골드 갱신 주기가 로그 보존 창보다 짧아야 합니다.
- **관리형과 외부 테이블을 계층별로 섞을 때 권한 경계를 확인합니다.** 외부 테이블은 Unity Catalog 권한이 파일 접근에 적용되지 않으므로, 브론즈의 외부 원본과 실버 관리형 테이블을 나눠 설계하는 것이 보통입니다 ([관리형 vs 외부 테이블](managed-vs-external-tables.md) 참고).

## 참고 문서

- [What is the medallion lakehouse architecture?](https://docs.databricks.com/aws/en/lakehouse/medallion)
- [What is a data lakehouse?](https://docs.databricks.com/aws/en/lakehouse/)
- [What is Delta Lake in Databricks?](https://docs.databricks.com/aws/en/delta/)
- [Schema enforcement](https://docs.databricks.com/aws/en/tables/schema-enforcement)
- [Upsert into a Delta Lake table using merge](https://docs.databricks.com/aws/en/delta/merge)
- [Lakeflow pipelines](https://docs.databricks.com/aws/en/ldp/)
