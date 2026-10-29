# Databricks SQL 개요

> 기준일: 2026-10-29 · 근거: 공식 문서

Databricks SQL(Databricks SQL)은 레이크하우스에 저장된 데이터를 SQL로 조회하고, 가공하고, 대시보드와 알림으로 공유하는 서비스입니다. 이 페이지는 Databricks SQL이 어떤 문제를 해결하는지, 레이크하우스 구조에서 어디에 놓이는지, 어떤 인터페이스로 접근하는지 정리합니다.

## 왜 필요한가

데이터 웨어하우스와 데이터 레이크를 따로 운영하면 같은 데이터가 두 곳에 복제되고, 권한 정책과 계보(lineage)도 둘로 나뉩니다. 분석가는 웨어하우스에서 쿼리하고, 엔지니어는 레이크에서 가공하며, 두 결과가 어긋나는 일이 생깁니다.

Databricks 공식 문서는 데이터 웨어하우징 아키텍처에서 레이크하우스가 데이터 레이크에 웨어하우스형 기능을 제공한다고 설명합니다. Databricks SQL은 이 구조에서 SQL 기반 분석 계층을 맡습니다. 같은 Delta 테이블을 노트북, 잡, 대시보드, 외부 BI 도구가 함께 읽으므로 복제 없이 한 벌의 데이터를 공유합니다.

| 문제 | Databricks SQL의 접근 |
|---|---|
| 웨어하우스와 레이크의 데이터 중복 | Delta 테이블을 SQL 웨어하우스가 직접 조회 |
| 권한 정책이 도구마다 다름 | Unity Catalog에서 테이블·뷰·함수 권한을 한 곳에서 관리 |
| 분석 쿼리의 성능 원인을 찾기 어려움 | 쿼리 기록과 쿼리 프로필로 실행 단계를 확인 |
| 분석 결과를 반복 공유하기 어려움 | 대시보드, 알림, 구체화 뷰로 결과를 재사용 |

## 어떻게 동작하는가

Databricks SQL의 실행 단위는 **SQL 웨어하우스** 입니다. 웨어하우스는 쿼리를 실행하는 컴퓨트이고, 데이터 자체는 Unity Catalog가 관리하는 테이블에 있습니다. 쿼리는 에디터, 대시보드, 알림, API 같은 인터페이스에서 웨어하우스로 전달됩니다.

공식 문서의 "Data warehousing on Databricks" 페이지는 인터페이스를 다음 묶음으로 나눕니다.

| 묶음 | 항목 | 이 장에서의 위치 |
|---|---|---|
| 인터페이스·도구 | SQL 에디터, 노트북(SQL 웨어하우스 연결), 잡(SQL 태스크), 대시보드, 메트릭 뷰, 알림, ETL(구체화 뷰·스트리밍 테이블), REST API | [SQL 에디터와 쿼리 기록](sql-editor-and-query-history.md), [구체화 뷰와 스트리밍 테이블](materialized-views-and-streaming-tables.md) |
| 모니터링·최적화 | 쿼리 기록, 쿼리 프로필, 쿼리 성능 인사이트 | [쿼리 프로필](query-profile.md), [쿼리 성능](query-performance.md) |
| 시작 가이드 | Databricks SQL 개념, 데이터 웨어하우징 아키텍처, 대시보드 만들기 | 이 페이지, [데이터 모델링 기초](data-modeling-basics.md) |
| 레퍼런스 | SQL 언어 레퍼런스, SQL 웨어하우스 연결, 릴리즈 노트 | [SQL 언어 기능](sql-language-features.md) |

공식 문서는 데이터 웨어하우징 아키텍처를 메달리온 구조로 설명합니다.

| 계층 | 문서가 설명하는 역할 | 주로 쓰는 것 |
|---|---|---|
| 브론즈(Bronze) | 원본을 원래 형식 그대로 받아 Delta 테이블로 변환하는 원시 적재 영역 | 수집 파이프라인 |
| 실버(Silver) | 여러 원천을 통합하는 계층. 웨어하우스 모델링이 주로 이루어지는 곳 | 3정규형(3NF) 또는 Data Vault 모델, PK/FK 제약 |
| 골드(Gold) | 여러 데이터 마트와 셀프서비스 분석 샌드박스를 제공하는 프레젠테이션 계층 | 차원 모델(dimensional model) 기반 데이터 마트, 대시보드 |

> **참고** 이 장은 골드 계층의 SQL 분석과 실버 계층의 모델링 기초를 다룹니다. 원시 수집과 파이프라인 구현은 04장(데이터 엔지니어링)에서 다룹니다.

### 메달리온 계층별 상세 (Medallion architecture 문서 기준)

| 계층 | 목적 | 검증 수준·특징 |
|---|---|---|
| 브론즈(Raw) | 원천을 원래 형태로 수집해 감사·재처리용 단일 진실 공급원으로 보존 | 검증은 최소. 스키마 변경에 대비해 대부분 필드를 string, VARIANT, binary로 저장하고 원본 파일명 같은 메타데이터를 추가. 데이터는 증분 append, 이력 보존. 원천은 클라우드 객체 스토리지, Kafka·Kinesis 같은 메시지 버스, Lakehouse Federation |
| 실버(Validated) | 정제·검증·보강해 소비 가능한 형태로 만듦 | 스키마 강제와 진화, null·누락 처리, 중복 제거, 순서 뒤바뀜·지연 도착 처리, 품질 검사, 타입 변환과 조인. 브론즈에서 읽을 때는 스트리밍 읽기를 권장하고 배치 읽기는 차원 테이블 같은 작은 데이터용. 수집에서 곧바로 쓰는 것은 피함. 레코드마다 검증된 비집계 표현을 최소 하나 유지 |
| 골드(Enriched) | 분석·대시보드·ML·애플리케이션용 업무 정렬 데이터 | 관계와 측정값이 있는 차원 모델, 평균·건수·합계 같은 집계(기간·지역 필터 포함). 잦은 쿼리와 대시보드에 최적화. 대용량 이력은 골드에 구체화하지 않고 보통 실버에 둠 |

문서의 골드 계층 예시는 구체화 뷰입니다. 아래는 원문 예제입니다.

```sql
CREATE OR REPLACE MATERIALIZED VIEW main.example_output.weekly_bookings AS
SELECT date_trunc('week', check_in) AS week,
       property_id,
       status,
       count(*) AS total_bookings,
       sum(total_amount) AS total_revenue
FROM samples.wanderbricks.bookings
GROUP BY week, property_id, status
```

수집 빈도는 비용과 지연의 교환입니다.

| 방식 | 비용 | 지연 |
|---|---|---|
| 연속 증분 수집 | 높음 | 낮음 |
| 트리거 증분 수집 | 낮음 | 높음 |
| 수동 증분 수집 배치 | 가장 낮음 | 가장 높음 (드문 실행) |

### 웨어하우스 모델링 (데이터 웨어하우징 아키텍처 문서 기준)

- 실버에서 웨어하우스를 모델링합니다. 3정규형(3NF) 또는 Data Vault를 주로 쓰고, 기본 키·외래 키 제약으로 관계를 명시합니다. 실버는 단일 진실 공급원이며 업무 변화에 맞춰 쉽게 바뀌도록 설계합니다.
- 골드는 프레젠테이션 계층으로, 대개 차원 모델인 데이터 마트와 셀프서비스 분석·데이터 과학용 샌드박스를 둡니다. 샌드박스에 별도 컴퓨트를 주면 팀이 레이크하우스 밖에 사본을 만들지 않게 됩니다.
- 모델링 실습은 [데이터 모델링 기초](data-modeling-basics.md)에서 다룹니다.

### Unity Catalog와 Delta Lake의 역할

공식 문서는 웨어하우스 구성에서 Unity Catalog를 거버넌스·감사·계보 제공 계층으로, Delta Lake를 ACID 트랜잭션과 스키마 변경을 지원하는 저장 계층으로 설명합니다. 따라서 Databricks SQL에서 조회하는 테이블은 대부분 Unity Catalog에 등록된 Delta 테이블입니다.

```sql
-- 3단계 이름으로 카탈로그·스키마·테이블을 지정한다
SELECT order_id, order_date, amount
FROM main.sales.orders
WHERE order_date >= DATE'2026-10-01';
```

### SQL 웨어하우스 유형

Databricks SQL의 모든 쿼리는 SQL 웨어하우스에서 실행됩니다(과거 명칭 SQL endpoints). "SQL warehouse types" 페이지의 비교는 다음과 같습니다.

| 항목 | Serverless | Pro | Classic |
|---|---|---|---|
| Photon 엔진 | 지원 | 지원 | 지원 |
| Predictive IO | 지원 | 지원 | 미지원 |
| Intelligent Workload Management | 지원 | 미지원 | 미지원 |
| 컴퓨트 위치 | Databricks 계정 | 고객 AWS 계정 | 고객 AWS 계정 |
| 시작 시간 | 보통 2~6초 | 보통 약 4분 | 보통 약 4분 |
| 스케일링 반응 | 빠른 증감 | 덜 민감 | 덜 민감 |

- Serverless 권장 용도: ETL, BI, 탐색적 분석, 특히 수요 변동이 클 때. 공식 문서는 가능하면 서버리스 웨어하우스를 쓰라고 권고합니다.
- Pro 권장 용도: 리전에서 서버리스를 쓸 수 없거나, 페더레이션·하이브리드를 위한 사용자 지정 네트워킹이 필요할 때.
- Classic 권장 용도: 입문 수준 성능의 대화형 탐색.
- Lakehouse Real-Time은 저지연·고동시성용 서버리스 유형으로 **Beta** 입니다. Unity Catalog 테이블에 대한 `SELECT`만 지원합니다.
- 정지된 웨어하우스는 쿼리 실행, 스케줄 잡 할당, JDBC/ODBC 연결, 해당 웨어하우스를 쓰는 대시보드를 열 때 자동으로 재시작됩니다. 수동 시작에는 웨어하우스의 CAN MONITOR 이상 권한이 필요합니다.
- UI는 지원되는 곳에서 기본으로 서버리스를 선택하지만, SQL warehouses API 기본값은 classic입니다. API·IaC로 만들 때 유형을 명시하지 않으면 UI와 다른 유형이 만들어질 수 있습니다.
- SQL 웨어하우스는 자격 증명 패스스루(credential passthrough)를 지원하지 않습니다. 거버넌스는 Unity Catalog를 씁니다.

### 핵심 개념 사전 (Databricks SQL concepts 기준)

| 개념 | 정의 |
|---|---|
| 쿼리(Query) | 데이터를 읽거나 변환하는, 저장·버전 관리되는 재사용 가능한 SQL 문 |
| 쿼리 기록(Query history) | 실행 시간·자원 사용·성능 정보 로그 |
| 쿼리 프로필(Query profile) | 병목을 찾기 위한 실행 계획 보기 |
| 대시보드(Dashboard) | 쿼리로 만든 시각화와 설명의 공유 가능한 모음, 대화형 필터 제공 |
| 메트릭 뷰(Metric view) | SQL 식으로 뒷받침되는 이름 붙은 지표 정의. 일관된 계산용 |
| 스트리밍 테이블(Streaming table) | 스트리밍 소스에서 증분 수집. 독립 파이프라인이 관리 |
| 구체화 뷰(Materialized view) | 미리 계산해 저장하는 뷰. 독립 파이프라인이 자동 갱신 |
| 알림(Alert) | 쿼리 결과를 조건과 비교해 알림 전송 |
| 개인용 액세스 토큰(PAT) | REST API 인증과 서드파티 도구의 웨어하우스 연결용 자격 증명 |
| 액세스 제어 목록(ACL) | 객체에 대해 어떤 주체가 어떤 작업을 할 수 있는지 정의 |

## 어떻게 쓰는가

가장 빠른 시작 경로는 다음 순서입니다.

1. 워크스페이스 사이드바에서 **SQL Editor** 를 엽니다.
2. 상단에서 SQL 웨어하우스를 선택합니다. 웨어하우스 유형별 차이는 아래 "SQL 웨어하우스 유형"에서, 크기·스케일링은 03장에서 다룹니다.
3. 카탈로그 탐색기에서 테이블을 찾고 `SELECT`를 실행합니다.
4. 결과를 시각화하거나, 쿼리를 대시보드나 알림에 연결합니다.

공식 문서의 시작 가이드 목록에는 "Get started with data warehousing"과 "Create an AI/BI dashboard" 튜토리얼이 있습니다. 두 튜토리얼 모두 [SQL 에디터와 쿼리 기록](sql-editor-and-query-history.md)과 07장(AI/BI)의 기능을 선행 지식으로 가정합니다.

공식 시작 가이드(Get started)는 세 묶음으로 구성됩니다.

| 묶음 | 항목 |
|---|---|
| 기본 익히기 | Databricks SQL 개념, 데이터 웨어하우징 아키텍처 |
| 첫 자산 만들기 | 샘플 대시보드 둘러보기(Dashboard Samples Gallery), AI/BI 대시보드 만들기, SQL 웨어하우스 만들기 |
| 연결·자동화 | 노트북에서 Databricks SQL 사용, `COPY INTO`로 클라우드 객체 스토리지 데이터 적재, 잡에서 SQL 쿼리·대시보드·알림 실행, Partner Connect로 BI 도구 연결 |

## 트레이드오프

| 항목 | 장점 | 고려할 점 |
|---|---|---|
| 단일 데이터 사본 | 복제 없이 Delta 테이블을 여러 도구가 공유 | 원천 테이블 설계가 나쁘면 모든 소비자가 영향을 받음 |
| 통합 거버넌스 | Unity Catalog 권한이 SQL, 대시보드, 알림에 함께 적용 | 권한 모델을 먼저 설계해야 함 (06장에서 다룸) |
| 노트북과 SQL의 공존 | 같은 테이블을 노트북 SQL 셀에서도 조회 | 노트북 컴퓨트와 SQL 웨어하우스의 과금·성능 특성이 다름 |
| 외부 BI 도구 연동 | 표준 커넥터로 외부 도구 연결 가능 | 도구별 기능 차이와 쿼리 생성 방식은 도구 문서를 따름 |

### 언제 쓰지 않는가

- 트랜잭션 처리(행 단위 갱신이 잦은 애플리케이션 백엔드)가 주 목적이라면 Lakebase([Lakebase란 무엇인가](../10-lakebase/what-is-lakebase.md))가 더 적합할 수 있습니다.
- 원시 파일을 대량으로 가공하는 배치 파이프라인이 중심이라면 04장의 파이프라인 도구를 먼저 검토합니다.

## 주의사항

> **주의** 문서 기준 AI Functions는 Databricks SQL Classic 웨어하우스에서 사용할 수 없습니다. AI 함수를 쓰는 웨어하우스 유형은 [AI Functions](ai-functions.md)에서 확인합니다.

> **참고** 공식 문서의 Databricks SQL 릴리즈 노트는 2026년 10월 기준 "Databricks SQL version 2026.43"을 Current 채널로 안내합니다. 버전 번호는 주기적으로 바뀌므로, 기능을 도입하기 전 최신 릴리즈 노트를 확인합니다.

- 서버리스가 항상 가능한 것은 아닙니다. 일부 리전은 서버리스 웨어하우스를 만들기 전에 설정 단계가 필요하고, 서버리스가 없는 리전은 Pro를 씁니다.
- 테이블 이름을 `catalog.schema.table` 3단계로 명시하는 습관이 권한 오류와 잘못된 대상 조회를 줄입니다.
- 인터페이스마다 쿼리를 실행하는 주체가 다릅니다(에디터, 대시보드 게시자, 알림 실행자). 권한은 실행 주체 기준으로 확인합니다.

## 참고 문서

- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
- [Data warehousing architecture (Databricks SQL concepts)](https://docs.databricks.com/aws/en/sql/get-started/data-warehousing-concepts)
- [Medallion architecture](https://docs.databricks.com/aws/en/lakehouse/medallion)
- [SQL warehouses](https://docs.databricks.com/aws/en/compute/sql-warehouse/)
- [SQL warehouse types](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)
- [Get started with data warehousing](https://docs.databricks.com/aws/en/sql/get-started/)
- [Databricks SQL concepts](https://docs.databricks.com/aws/en/sql/get-started/concepts)
- [Databricks SQL 릴리즈 노트 2026](https://docs.databricks.com/aws/en/sql/release-notes/2026)
