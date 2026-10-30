# <img src="https://www.databricks.com/sites/default/files/2026-03/primary-icon-orange-data-warehouse.svg" alt="" width="40" class="chapter-icon"> 5. 데이터 웨어하우징 (Databricks SQL)

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

Databricks SQL(Databricks SQL)은 레이크하우스 위에서 SQL로 데이터를 조회·가공·공유하는 서비스입니다. 이 장은 BI 분석가, 데이터 엔지니어, 분석 엔지니어를 대상으로 합니다. SQL 에디터에서 쿼리를 작성하고, 쿼리 기록과 쿼리 프로필로 실행을 점검하며, 윈도 함수·PIVOT·QUALIFY 같은 SQL 기능을 익힙니다. 이어서 SQL 스크립팅과 저장 프로시저, AI Functions, 구체화 뷰와 스트리밍 테이블을 다루고, 마지막으로 쿼리 성능과 데이터 모델링 기초를 정리합니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- Databricks SQL이 무엇이며 어떤 문제를 해결하는지 설명하고, 메달리온 구조(브론즈·실버·골드)에서 웨어하우징 계층이 어디에 놓이는지 구분합니다.
- SQL 에디터에서 쿼리를 실행하고, 쿼리 기록(Query history)에서 상태와 실행 주체를 확인합니다.
- 쿼리 프로필(Query profile)의 DAG와 Top operators를 읽어 병목 연산자를 찾습니다.
- 윈도 함수, PIVOT, QUALIFY, 파라미터 마커를 조건에 맞게 선택합니다.
- SQL 스크립팅과 `CREATE PROCEDURE`의 최소 런타임, 권한 모델(INVOKER·DEFINER)을 구분합니다.
- AI Functions 가운데 `ai_query`, `ai_extract`, `ai_parse_document`의 요구 사항과 권한을 확인합니다.
- 구체화 뷰(Materialized view)와 스트리밍 테이블(Streaming table)의 생성 방식과 상태를 구분합니다.
- 쿼리 성능 인사이트(Performance insights)를 기준으로 쿼리 측면의 최적화 항목을 점검합니다.
- 스타 스키마와 스노우플레이크 스키마의 차이를 설명하고, PK/FK 제약의 성격(정보성, 비강제)을 이해합니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [Databricks SQL 개요](what-is-databricks-sql.md) | 100 | 무엇이고 왜 쓰는가, 메달리온 구조에서의 위치, 주요 인터페이스 |
| 2 | [SQL 에디터와 쿼리 기록](sql-editor-and-query-history.md) | 200 | SQL 에디터 기능, 쿼리 기록의 상태·필터·권한, `system.query.history` |
| 3 | [쿼리 프로필 읽기](query-profile.md) | 200 | 쿼리 프로필 열기, DAG와 연산자, 병목 찾기 절차 |
| 4 | [SQL 언어 기능](sql-language-features.md) | 200 | 윈도 함수, PIVOT·UNPIVOT, QUALIFY, 파라미터 마커 |
| 5 | [SQL 스크립팅과 저장 프로시저](scripting-and-procedures.md) | 200 | 스크립팅 문장, `CREATE PROCEDURE`, 실행 권한 모델 |
| 6 | [AI Functions](ai-functions.md) | 200 | 함수 분류, 상태 라벨, `ai_query`·`ai_extract`·`ai_parse_document`의 요구 사항 |
| 7 | [구체화 뷰와 스트리밍 테이블](materialized-views-and-streaming-tables.md) | 200 | 생성 구문, 실행 주체, 새로 고침, 상태 |
| 8 | [쿼리 성능 최적화](query-performance.md) | 300 | 성능 인사이트 항목, 쿼리 측면 점검 순서 (웨어하우스 선택은 03장) |
| 9 | [데이터 모델링 기초](data-modeling-basics.md) | 100 | 스타·스노우플레이크 스키마, PK/FK 제약의 성격과 한계 |
| 10 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 10개와 실무 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 페이지 2와 3은 이후 성능 관련 페이지의 전제가 되므로 순서대로 읽는 것을 권장합니다.

> **참고** 웨어하우스(SQL 웨어하우스)의 유형, 크기, 서버리스·프로 구분은 이 장에서 다루지 않습니다. 03장(컴퓨트)에서 다룹니다.

## 선수 지식

- **SQL 기초**: `SELECT`, `JOIN`, `GROUP BY`, 서브쿼리를 작성할 수 있어야 합니다.
- **Unity Catalog 기초**: 카탈로그·스키마·테이블의 3단계 이름(`catalog.schema.table`)과 `GRANT` 기반 권한 모델을 알고 있어야 합니다.
- **Delta Lake 기초**: 테이블의 기본 저장 형식과 트랜잭션 개념을 이해하고 있으면 좋습니다. 저장 계층은 02장에서 다룹니다.
- **데이터 웨어하우스 개념**: 팩트·차원 테이블의 의미를 알고 있으면 9번 페이지가 수월합니다.

## 이 장의 읽는 법

각 기능 페이지는 **왜 필요한가 → 어떻게 동작하는가 → 어떻게 쓰는가 → 트레이드오프 → 주의사항** 순서를 따릅니다. 기능마다 상태(GA, Public Preview, Beta 등)를 표기하고, 문서에 상태 라벨이 없으면 "라벨 없음(원문 기준)"으로 적습니다. 문서에 없는 한도나 수치는 쓰지 않습니다.

> **참고** 이 장의 SQL 예시는 공식 SQL 레퍼런스의 문법을 따릅니다. 실제 실행 전에는 워크스페이스의 Databricks Runtime 버전과 Unity Catalog 설정이 예시 요구 사항을 충족하는지 확인하십시오.

## 참고 문서

- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
- [SQL language reference](https://docs.databricks.com/aws/en/sql/language-manual/)
- [Databricks SQL 릴리즈 노트 2026](https://docs.databricks.com/aws/en/sql/release-notes/2026)
