# Databricks SQL 개요

> 기준일: 2026-10-28 · 근거: 공식 문서

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
| 인터페이스·도구 | SQL 에디터, 노트북(SQL 웨어하우스 연결), 잡(SQL 태스크), 대시보드, 메트릭 뷰, 알림, ETL(구체화 뷰·스트리밍 테이블), REST API | 2번, 7번 |
| 모니터링·최적화 | 쿼리 기록, 쿼리 프로필, 쿼리 성능 인사이트 | 2번, 3번, 8번 |
| 시작 가이드 | Databricks SQL 개념, 데이터 웨어하우징 아키텍처, 대시보드 만들기 | 1번, 9번 |
| 레퍼런스 | SQL 언어 레퍼런스, SQL 웨어하우스 연결, 릴리즈 노트 | 4번, 5번, 6번 |

공식 문서는 데이터 웨어하우징 아키텍처를 메달리온 구조로 설명합니다.

| 계층 | 문서가 설명하는 역할 | 주로 쓰는 것 |
|---|---|---|
| 브론즈(Bronze) | 원본을 원래 형식 그대로 받아 Delta 테이블로 변환하는 원시 적재 영역 | 수집 파이프라인, `COPY INTO` |
| 실버(Silver) | 여러 원천을 통합하는 계층. 웨어하우스 모델링이 주로 이루어지는 곳 | 3정규형(3NF) 또는 Data Vault 모델, PK/FK 제약 |
| 골드(Gold) | 여러 데이터 마트와 셀프서비스 분석 샌드박스를 제공하는 프레젠테이션 계층 | 차원 모델(dimensional model) 기반 데이터 마트, 대시보드 |

> **참고** 이 장은 골드 계층의 SQL 분석과 실버 계층의 모델링 기초를 다룹니다. 원시 수집과 파이프라인 구현은 04장(데이터 엔지니어링)에서 다룹니다.

### Unity Catalog와 Delta Lake의 역할

공식 문서는 웨어하우스 구성에서 Unity Catalog를 거버넌스·감사·계보 제공 계층으로, Delta Lake를 ACID 트랜잭션과 스키마 변경을 지원하는 저장 계층으로 설명합니다. 따라서 Databricks SQL에서 조회하는 테이블은 대부분 Unity Catalog에 등록된 Delta 테이블입니다.

```sql
-- 3단계 이름으로 카탈로그·스키마·테이블을 지정한다
SELECT order_id, order_date, amount
FROM main.sales.orders
WHERE order_date >= DATE'2026-10-01';
```

## 어떻게 쓰는가

가장 빠른 시작 경로는 다음 순서입니다.

1. 워크스페이스 사이드바에서 **SQL Editor** 를 엽니다.
2. 상단에서 SQL 웨어하우스를 선택합니다. 웨어하우스 선택 기준은 03장에서 다룹니다.
3. 카탈로그 탐색기에서 테이블을 찾고 `SELECT`를 실행합니다.
4. 결과를 시각화하거나, 쿼리를 대시보드나 알림에 연결합니다.

공식 문서의 시작 가이드 목록에는 "Get started with data warehousing"과 "Create an AI/BI dashboard" 튜토리얼이 있습니다. 두 튜토리얼 모두 이 장의 2번 페이지와 7번 페이지의 기능을 선행 지식으로 가정합니다.

## 트레이드오프

| 항목 | 장점 | 고려할 점 |
|---|---|---|
| 단일 데이터 사본 | 복제 없이 Delta 테이블을 여러 도구가 공유 | 원천 테이블 설계가 나쁘면 모든 소비자가 영향을 받음 |
| 통합 거버넌스 | Unity Catalog 권한이 SQL, 대시보드, 알림에 함께 적용 | 권한 모델을 먼저 설계해야 함 (06장에서 다룸) |
| 노트북과 SQL의 공존 | 같은 테이블을 노트북 SQL 셀에서도 조회 | 노트북 컴퓨트와 SQL 웨어하우스의 과금·성능 특성이 다름 |
| 외부 BI 도구 연동 | 표준 커넥터로 외부 도구 연결 가능 | 도구별 기능 차이와 쿼리 생성 방식은 도구 문서를 따름 |

### 언제 쓰지 않는가

- 트랜잭션 처리(행 단위 갱신이 잦은 애플리케이션 백엔드)가 주 목적이라면 Lakebase(10장)가 더 적합할 수 있습니다.
- 원시 파일을 대량으로 가공하는 배치 파이프라인이 중심이라면 04장의 파이프라인 도구를 먼저 검토합니다.

## 주의사항

> **주의** 문서 기준 AI Functions는 Databricks SQL Classic 웨어하우스에서 사용할 수 없습니다. AI 함수를 쓰는 웨어하우스 유형은 6번 페이지에서 확인합니다.

> **참고** 공식 문서의 Databricks SQL 릴리즈 노트는 2026년 10월 기준 "Databricks SQL version 2026.43"을 Current 채널로 안내합니다. 버전 번호는 주기적으로 바뀌므로, 기능을 도입하기 전 최신 릴리즈 노트를 확인합니다.

- 테이블 이름을 `catalog.schema.table` 3단계로 명시하는 습관이 권한 오류와 잘못된 대상 조회를 줄입니다.
- 인터페이스마다 쿼리를 실행하는 주체가 다릅니다(에디터, 대시보드 게시자, 알림 실행자). 권한은 실행 주체 기준으로 확인합니다.

## 참고 문서

- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
- [Data warehousing architecture (Databricks SQL concepts)](https://docs.databricks.com/aws/en/sql/get-started/data-warehousing-concepts)
- [Databricks SQL concepts](https://docs.databricks.com/aws/en/sql/get-started/concepts)
- [Databricks SQL 릴리즈 노트 2026](https://docs.databricks.com/aws/en/sql/release-notes/2026)
