# <img src="https://www.databricks.com/sites/default/files/2024-06/primary-icon-orange-delta-lakehouse.svg" alt="" width="40" class="chapter-icon"> 02. 레이크하우스 스토리지 (Delta Lake·Iceberg)

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

레이크하우스(Lakehouse)는 데이터 레이크처럼 저렴한 오브젝트 스토리지에 열린 포맷으로 데이터를 두면서, 데이터 웨어하우스처럼 트랜잭션과 스키마 관리, 빠른 SQL 조회를 제공하는 구조입니다. Databricks에서 이 구조의 중심에는 두 개의 오픈 테이블 포맷이 있습니다. 하나는 Databricks가 기본으로 쓰는 **Delta Lake** 이고, 다른 하나는 여러 엔진이 공유하는 **Apache Iceberg** 입니다. 이 장은 두 포맷이 어떻게 동작하는지, Unity Catalog에서 어떤 테이블 유형으로 관리되는지, 그리고 테이블을 오래 운영할 때 필요한 최적화와 변경 추적 기능을 다룹니다.

이 장은 데이터 엔지니어, 데이터 아키텍트, 그리고 Databricks에 처음 데이터를 적재하는 분석가를 대상으로 합니다. 테이블을 만들고 쓰는 방법뿐 아니라, 같은 데이터를 외부 엔진이 읽을 때의 제약, 파일과 메타데이터가 쌓이는 방식, 보존 기간과 비용의 관계까지 설명합니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- 데이터 웨어하우스와 데이터 레이크의 한계를 설명하고, 레이크하우스가 그 사이에서 해결하는 문제를 구분합니다.
- Delta Lake의 트랜잭션 로그가 ACID 보장과 버전 이력을 만드는 방식을 설명합니다.
- 스키마 강제(Schema enforcement)와 스키마 진화(Schema evolution)의 차이를 이해하고, 각각을 설정합니다.
- Iceberg 관리형 테이블(Managed Iceberg tables)을 만들고, 외부 Iceberg 클라이언트가 어떤 작업을 할 수 있는지 표로 구분합니다.
- UniForm(Delta 테이블을 Iceberg 클라이언트에 읽기 전용으로 노출하는 기능)의 전제 조건과 제약을 확인합니다.
- 관리형 테이블과 외부 테이블의 데이터 수명, 삭제 동작, 저장 위치 차이를 설명합니다.
- 리퀴드 클러스터링(Liquid clustering), 예측 최적화(Predictive optimization), `OPTIMIZE`, `VACUUM`의 역할을 구분하고 설정합니다.
- 삭제 벡터(Deletion vectors)가 `DELETE`·`UPDATE`·`MERGE`의 비용을 줄이는 방식과 물리 정리(`REORG ... APPLY (PURGE)`)의 필요성을 이해합니다.
- 타임 트래블(Time travel), `RESTORE`, 변경 데이터 피드(Change Data Feed, CDF)를 보존 기간과 함께 설계합니다.
- 메달리온 아키텍처(Medallion architecture)를 브론즈·실버·골드 계층으로 나누는 기준을 세웁니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [레이크하우스가 필요한 이유](why-lakehouse.md) | 100 | 웨어하우스와 레이크의 한계, 레이크하우스의 정의, 구성 요소 |
| 2 | [Delta Lake 동작 원리](delta-lake-internals.md) | 200 | 트랜잭션 로그, ACID, 스키마 강제와 진화, 컬럼 매핑, 멀티 문장 트랜잭션 |
| 3 | [Apache Iceberg 지원](iceberg-support.md) | 300 | 관리형 Iceberg 테이블, Iceberg REST 카탈로그 접근, 외부 클라이언트 권한 표, UniForm, Iceberg v3 |
| 4 | [관리형 vs 외부 테이블](managed-vs-external-tables.md) | 200 | 데이터 수명, 삭제 동작, 저장 위치, 외부 쓰기의 주의점 |
| 5 | [테이블 레이아웃 최적화](table-layout-optimization.md) | 200 | 리퀴드 클러스터링, 예측 최적화, `OPTIMIZE`, `VACUUM` |
| 6 | [삭제 벡터](deletion-vectors.md) | 300 | 행 단위 삭제 최적화, 활성화, `REORG`와 `PURGE`, 읽기 호환성 |
| 7 | [타임 트래블과 변경 데이터 피드](time-travel-and-cdf.md) | 200 | `DESCRIBE HISTORY`, 버전 조회, `RESTORE`, 자동 CDF와 레거시 CDF |
| 8 | [메달리온 아키텍처](medallion-architecture.md) | 100 | 브론즈·실버·골드 계층 설계 기준, 계층별 테이블 유형과 보존 정책 |
| 9 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 9개와 실무 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 특히 「Delta Lake 동작 원리」 페이지는 그 뒤 모든 페이지의 전제가 되므로 건너뛰지 않는 것을 권장합니다.

> **참고** 이 장의 기능 상태(GA, Public Preview, Beta)는 각 페이지 본문에 명시된 라벨을 그대로 옮겼습니다. 페이지에 라벨이 없는 기능은 "문서에 명시 없음"으로 표기했습니다. 릴리스 노트의 상태와 기능 페이지의 표기가 다른 경우에는 두 값을 모두 적고 차이를 명시했습니다.

> **참고** 이 장은 AWS 문서(`docs.databricks.com/aws/en/`)를 기준으로 작성했습니다. 예시 경로(`s3://...`)와 Azure 문서의 값이 다를 수 있으므로 적용 전 원문을 확인하십시오.

## 선수 지식

- **SQL 기초**: `CREATE TABLE`, `INSERT`, `MERGE`, `SELECT` 문법을 알고 있어야 합니다. 예제는 Databricks SQL 문법을 사용합니다.
- **Unity Catalog 기초**: 카탈로그, 스키마, 테이블의 3단계 이름(`catalog.schema.table`)과 권한(`GRANT`) 모델을 이해해야 합니다. 이 장의 테이블은 모두 Unity Catalog에 등록된 것을 전제로 합니다.
- **클라우드 오브젝트 스토리지 개념**: 파일 단위 저장, 파일 크기, 외부 위치(External location)의 의미를 알고 있으면 관리형과 외부 테이블 차이를 빨리 이해할 수 있습니다.
- **Parquet 파일 개념**: Delta Lake와 Iceberg의 데이터 파일은 모두 Parquet입니다. 열 기반 저장과 파일 단위 통계라는 개념만 알고 있으면 충분합니다.

## 이 장의 읽는 법

각 기능 페이지는 같은 구조를 따릅니다. 왜 필요한지, 어떻게 동작하는지, 어떻게 쓰는지, 트레이드오프, 주의사항 순서입니다. 코드 예시는 공식 문서에 있는 SQL 문법만 사용합니다. 문서에 없는 파라미터를 추측해서 넣지 않습니다.

다른 장과의 관계는 다음과 같습니다.

| 주제 | 이 장에서 다루는 범위 | 더 자세한 내용 |
|---|---|---|
| Lakebase 동기화 테이블 | Unity Catalog Delta 테이블이 원본이 되는 개념만 언급 | [10. Lakebase: 동기화 테이블](../10-lakebase/synced-tables.md) |
| Lakebase 변경 데이터 반출 | CDF의 개념 비교만 언급 | [10. Lakebase: 변경 데이터 반출](../10-lakebase/change-data-out.md) |
| Lakeflow 파이프라인으로 적재와 변환 | 메달리온 계층별 테이블 생성 방식만 언급 | 04장에서 다룹니다 |
