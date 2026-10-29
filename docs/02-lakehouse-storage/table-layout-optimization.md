# 테이블 레이아웃 최적화

> 기준일: 2026-10-30 · 근거: 공식 문서 · 수준: 200

레이크하우스 테이블은 쓰기가 반복되면서 작은 파일이 많이 쌓이고, 데이터가 쿼리 조건과 무관하게 흩어집니다. 그러면 같은 쿼리도 읽는 파일 수가 늘어나 느려집니다. 이 페이지는 파일 레이아웃을 정리하는 네 가지 도구를 다룹니다. 데이터를 쿼리 조건에 맞춰 묶는 **리퀴드 클러스터링(Liquid clustering)**, 최적화 작업을 Databricks가 대신 실행하는 **예측 최적화(Predictive optimization)**, 파일을 실제로 다시 쓰는 **`OPTIMIZE`**, 오래된 파일을 지우는 **`VACUUM`** 입니다.

## 1. 왜 필요한가

| 문제 | 원인 | 결과 |
|---|---|---|
| 작은 파일이 많음 | 소량 쓰기가 반복되어 커밋마다 파일이 생김 | 파일 목록을 읽는 비용과 스캔 오버헤드 증가 |
| 조건 필터가 파일을 건너뛰지 못함 | 데이터가 조건 컬럼 기준으로 정렬되지 않음 | 쿼리가 대부분의 파일을 읽음 |
| 오래된 파일이 쌓임 | 삭제·갱신이 로그에만 제거를 기록하고 파일은 남김 | 저장 비용 증가, 시간 여행 보존 기간과 충돌 |
| 최적화를 잊음 | 수동 실행 주기 관리가 필요함 | 테이블마다 성능 차이가 커짐 |

공식 문서는 파티션, `ZORDER`, 기타 레이아웃 방식보다 리퀴드 클러스터링을 권장한다고 설명합니다.

## 2. 어떻게 동작하는가

### 2.1 리퀴드 클러스터링

리퀴드 클러스터링은 테이블에 **클러스터링 키** 를 지정하면, `OPTIMIZE`가 데이터 파일을 그 키 기준으로 묶어 다시 쓰는 방식입니다. 파티션처럼 디렉터리를 나누지 않으므로 키를 바꾸기 쉽고, 데이터 분포가 바뀌어도 키를 조정할 수 있습니다.

| 항목 | 내용 |
|---|---|
| 상태 (Delta Lake) | GA, Databricks Runtime 15.4 LTS 이상 |
| 상태 (Apache Iceberg) | Public Preview, Databricks Runtime 16.4 LTS 이상 |
| 클러스터링 키 개수 | 테이블당 최대 4개 |
| 통계 | 키는 통계가 수집되어 있어야 함. 기본적으로 처음 32개 컬럼에 통계가 수집됨 |
| 지원 타입 | Date, Timestamp, TimestampNTZ, String, Integer, Long, Short, Byte, Float, Double, Decimal |
| 제외 타입 | 복합 타입(struct, map, array)과 map·array 원소 |
| 구조체 필드 | 지원되는 타입이면 점 표기(dot notation)로 임의 깊이의 필드를 키로 지정 가능 |

> **참고** 공식 문서는 1개 컬럼 필터가 주로 쓰이는 10TB 미만 테이블에서는 키가 적을수록 성능이 좋다고 설명합니다.

### 2.2 `OPTIMIZE`의 동작

| 명령 | 동작 | 요구 런타임 |
|---|---|---|
| `OPTIMIZE table_name` | 증분 실행. 새로 들어온 데이터나 아직 클러스터링되지 않은 데이터만 다시 씀. 키와 맞는 파일은 건너뜀 | 리퀴드 클러스터링 GA는 Databricks Runtime 15.4 LTS 이상. 클러스터링 `OPTIMIZE` 트리거는 13.3 LTS 이상 (호환성 표 기준) |
| `OPTIMIZE table_name FULL` | 기존 데이터 전체를 다시 클러스터링 | 문서 기준 Databricks Runtime 16.4 LTS 이상 |
| `OPTIMIZE table_name FULL WHERE <predicate>` | 조건에 맞는 일부만 다시 클러스터링 | Databricks Runtime 18.1 이상 |

> **주의** `OPTIMIZE` 페이지는 `FULL`을 Databricks Runtime 16.0 이상으로, 리퀴드 클러스터링 페이지는 16.4 LTS 이상으로 적고 있습니다. 두 페이지의 값이 다르므로 실제 적용 전 원문을 다시 확인하십시오. 이 장에서는 더 구체적인 리퀴드 클러스터링 페이지 값을 표에 적었습니다.

공식 문서가 설명하는 `OPTIMIZE`의 공통 특징은 다음과 같습니다.

- 파일을 묶는 **빈 패킹(Bin-packing)** 으로 작은 파일을 합칩니다. 빈 패킹은 멱등(idempotent)이므로 같은 데이터에 두 번 실행해도 추가 변화가 없습니다.
- 읽기 쿼리는 중단되지 않으며 반환 데이터는 바뀌지 않습니다.
- 리퀴드 클러스터링이 켜진 테이블에서 `OPTIMIZE`는 클러스터링 키 기준으로 데이터를 묶어 다시 씁니다.
- Delta 테이블에 `ZORDER BY`를 쓰는 방식은 리퀴드 클러스터링이 없는 테이블에서만 의미가 있습니다. Iceberg 테이블은 `ZORDER` 대신 클러스터링과 정렬 전략을 씁니다.

### 2.3 예측 최적화 (Predictive optimization)

예측 최적화는 Unity Catalog 관리형 테이블에 대해 `OPTIMIZE`, `VACUUM`, `ANALYZE`를 자동으로 실행합니다. 전문 텍스트 검색 인덱스를 최신으로 유지하는 `REFRESH INDEX`도 함께 실행합니다.

| 항목 | 내용 |
|---|---|
| 대상 | Unity Catalog 관리형 테이블만 |
| 요구 사항 | Premium 이상 플랜, 지원 리전, SQL 웨어하우스 또는 Databricks Runtime 12.2 LTS 이상 |
| 기본 설정 | 2024-11-11 이후 생성된 계정은 기본 활성화. 이전 계정은 순차 적용 중이며 문서는 2026년 8월까지 완료 예정이라고 설명. 기준일(2026-10-28) 이후 원문 상태를 다시 확인할 것 |
| 상태 라벨 | 기능 페이지에 상태 라벨 없음 (문서 명시 없음) |
| 실행 기록 | Catalog Explorer의 History 탭에 `Auto`(실행됨) 또는 `Not applied`(건너뜀, 사유 확인 가능)로 표시 |

## 3. 어떻게 쓰는가

### 3.1 리퀴드 클러스터링 테이블 만들기

```sql
CREATE TABLE main.sales.orders_clustered (
  order_id  BIGINT,
  customer  STRING,
  amount    DECIMAL(12, 2),
  order_ts  TIMESTAMP
)
CLUSTER BY (customer, order_ts);
```

기존 데이터로 CTAS(`CREATE TABLE ... AS SELECT`)를 쓸 때는 `CLUSTER BY` 절이 테이블 이름 뒤, `AS SELECT` 앞에 옵니다. `SELECT` 안에 넣지 않습니다.

```sql
CREATE TABLE main.sales.orders_clustered2
CLUSTER BY (customer)
AS SELECT * FROM main.sales.orders;
```

같은 스키마로 빈 테이블을 만들 때는 `LIKE`를 씁니다.

```sql
CREATE TABLE main.sales.orders_clustered3 LIKE main.sales.orders_clustered;
```

### 3.2 기존 테이블에 클러스터링 적용과 변경

```sql
-- 키 지정 또는 변경
ALTER TABLE main.sales.orders CLUSTER BY (customer, order_ts);

-- 클러스터링 해제 (기존 데이터는 다시 쓰지 않음)
ALTER TABLE main.sales.orders CLUSTER BY NONE;
```

`CLUSTER BY NONE`은 클러스터링 키만 제거합니다. 이미 클러스터링된 데이터를 다시 쓰지 않으며, 이후 `OPTIMIZE`가 그 키를 쓰지 않습니다.

### 3.3 키를 처음 켠 뒤 전체 재클러스터링

키를 처음 지정했거나 키를 바꾼 뒤에는 기존 데이터도 새 키로 묶어야 합니다. 증분 `OPTIMIZE`만으로는 이전 데이터가 정리되지 않을 수 있으므로 `FULL`을 씁니다.

```sql
OPTIMIZE main.sales.orders FULL;
```

특정 기간만 다시 묶는 예는 Databricks Runtime 18.1 이상이 필요합니다.

```sql
OPTIMIZE main.sales.orders FULL WHERE order_ts >= '2026-01-01';
```

### 3.4 증분 최적화 일정

예측 최적화가 꺼져 있다면 `OPTIMIZE`를 일정에 맞춰 직접 실행해야 합니다. 공식 문서는 자주 갱신되는 테이블에는 대략 1~2시간마다 실행하라고 권장합니다.

```sql
OPTIMIZE main.sales.orders;
```

### 3.5 예측 최적화 설정

예측 최적화는 카탈로그, 스키마, 테이블 단위로 `ENABLE`, `DISABLE`, `INHERIT`를 설정할 수 있습니다.

```sql
ALTER CATALOG main ENABLE PREDICTIVE OPTIMIZATION;
ALTER SCHEMA main.sales ENABLE PREDICTIVE OPTIMIZATION;
ALTER TABLE main.sales.orders INHERIT PREDICTIVE OPTIMIZATION;
```

상위에서 상속되는 설정을 확인하려면 `DESCRIBE EXTENDED`를 씁니다.

```sql
DESCRIBE TABLE EXTENDED main.sales.orders;
```

> **참고** 문서의 구문은 `DESCRIBE (CATALOG | SCHEMA | TABLE) EXTENDED name` 형식입니다. 위 예시는 테이블용 형태입니다.

### 3.6 VACUUM으로 오래된 파일 정리

`VACUUM`은 현재 버전과 보존 기간 안의 버전이 참조하지 않는 데이터 파일을 지웁니다.

```sql
-- 삭제 대상 목록만 확인 (삭제하지 않음)
VACUUM main.sales.orders DRY RUN;

-- 실제 삭제 (기본 모드 FULL)
VACUUM main.sales.orders;
```

| 모드 | 설명 | 상태 |
|---|---|---|
| `VACUUM table_name` (FULL) | 기본 모드. 명시적으로 `FULL`을 붙일 수도 있음 | 기본 |
| `VACUUM table_name LITE` | 파일을 나열하지 않고 트랜잭션 로그를 사용 | Public Preview, Databricks Runtime 16.4 LTS 이상 |
| `VACUUM table_name DRY RUN` | 삭제 대상만 나열 | 기본 제공 |

`LITE` 모드는 **트랜잭션 로그 보존 기간**(기본 30일) 안에 성공한 `VACUUM`이 최소 한 번 있어야 합니다. 없으면 `FULL`을 실행해야 합니다. 이 30일은 `VACUUM`이 지울 데이터 파일을 고르는 보존 기준(기본 7일)과 다른 값입니다.

## 4. 트레이드오프

| 도구 | 장점 | 비용·제약 |
|---|---|---|
| 리퀴드 클러스터링 | 파티션 없이 쿼리 패턴에 맞춤. 키 변경이 쉬움 | 키 최대 4개. 복합 타입 불가. 변경 후 `FULL` 재클러스터링이 필요 |
| 예측 최적화 | 운영자가 주기를 관리하지 않아도 됨 | Premium 이상, 지원 리전, 관리형 테이블에만 적용 |
| 수동 `OPTIMIZE` | 실행 시점을 완전히 통제 | 주기 관리가 필요함. 잊으면 파일이 다시 쌓임 |
| `VACUUM` | 저장 공간 회수 | 보존 기간 밖 버전의 시간 여행이 불가능해짐 |
| `FULL` 재클러스터링 | 기존 데이터 전체에 새 키 적용 | 전체 파일을 다시 씀. 비용과 시간이 큼 |

### 언제 쓰지 않는가

- 테이블이 작고 쿼리 패턴이 단순하다면 리퀴드 클러스터링을 굳이 켤 필요가 없을 수 있습니다.
- 키 컬럼이 자주 바뀌는 테이블이라면 `FULL` 재클러스터링 비용을 먼저 계산하십시오.
- 외부 테이블은 예측 최적화 대상이 아닙니다. 관리형 테이블과 운영 방식을 나누십시오 ([관리형 vs 외부 테이블](managed-vs-external-tables.md) 참고).

## 5. 주의사항

> **주의** `VACUUM`은 시간 여행과 직접 충돌합니다. 기본 보존 기간(7일) 밖의 버전 파일은 삭제되므로, 그 버전으로 되돌릴 수 없습니다. 공식 문서는 보존 간격을 최소 7일로 두라고 강하게 권장합니다.

> **주의** 장기 실행 잡이 아직 커밋되지 않은 파일을 쓰고 있을 수 있습니다. 보존 기간을 짧게 줄이면 `VACUUM`이 그 파일을 지워 잡이 실패할 수 있습니다. `retentionDurationCheck` 검사는 끌 수 있지만, 테이블에서 보존 간격보다 긴 작업이 없다는 것을 확인한 경우에만 끄십시오.

- **로그 파일은 `VACUUM`이 지우지 않습니다.** 로그 파일은 체크포인트 이후 비동기로 삭제되며, 기본 보존 기간은 30일입니다.
- **보존 기간을 늘리면 저장 비용이 늘어납니다.** 공식 문서가 명시하는 내용입니다.
- **예측 최적화 설정은 상위 단위에서 상속됩니다.** 테이블 설정이 `INHERIT`인지 확인하지 않으면 스키마나 카탈로그 설정 변경이 예상과 다르게 적용될 수 있습니다.
- **`OPTIMIZE` 주기를 잡는 기준은 테이블 쓰기 빈도입니다.** 예측 최적화가 꺼진 상태라면 Job으로 주기 실행을 설계하고, 실행 결과는 `DESCRIBE HISTORY`로 확인하십시오 ([타임 트래블과 변경 데이터 피드](time-travel-and-cdf.md) 참고).
- **리퀴드 클러스터링 키를 바꾼 뒤에는 `OPTIMIZE ... FULL`을 잊지 마십시오.** 증분 실행만으로는 과거 데이터가 새 키 기준으로 정리되지 않습니다.
- **서버리스 컴퓨트 여부는 이 페이지 범위에서 확인하지 않았습니다.** 실행 환경은 원문에서 다시 확인하십시오.

## 참고 문서

- [Use liquid clustering for tables](https://docs.databricks.com/aws/en/delta/clustering)
- [Liquid clustering (Databricks tables)](https://docs.databricks.com/aws/en/tables/clustering)
- [Optimize data file layout](https://docs.databricks.com/aws/en/tables/operations/optimize)
- [Predictive optimization for Unity Catalog managed tables](https://docs.databricks.com/aws/en/optimizations/predictive-optimization)
- [Remove unused data files with vacuum](https://docs.databricks.com/aws/en/tables/operations/vacuum)
- [Work with table history](https://docs.databricks.com/aws/en/tables/history)
