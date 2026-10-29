# 3. 컴퓨트 (서버리스·클래식·SQL 웨어하우스)

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

컴퓨트(Compute)는 Databricks에서 코드와 쿼리를 실제로 실행하는 연산 자원입니다. 노트북을 실행하고, Job을 돌리고, 파이프라인을 처리하고, SQL 쿼리에 답하는 모든 작업이 어딘가의 컴퓨트 위에서 일어납니다. 이 장은 데이터 엔지니어, 분석가, 플랫폼 관리자를 대상으로 하며, 컴퓨트 종류를 구분하고 워크로드에 맞는 것을 고르는 기준, 각 컴퓨트의 설정과 제약, 비용이 어떤 구조로 청구되는지를 다룹니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- 서버리스 컴퓨트, 클래식 컴퓨트, SQL 웨어하우스의 차이를 설명하고 워크로드에 맞는 유형을 고릅니다.
- 서버리스 컴퓨트에서 노트북과 Job이 쓰는 환경(Environment)과 기본 환경(Base environment)을 선택하고, 서버리스의 주요 제약을 확인합니다.
- 클래식 컴퓨트의 액세스 모드(Standard, Dedicated, Auto)를 구분하고 Databricks Runtime 버전을 고릅니다.
- 오토스케일링(Autoscaling), 인스턴스 풀(Instance pool), 컴퓨트 정책(Compute policy)의 역할과 설정 단위를 이해합니다.
- SQL 웨어하우스의 유형(Serverless, Pro, Classic)과 크기, 클러스터 수 범위를 설정합니다.
- Photon 엔진이 어떤 워크로드를 가속하고 어떤 워크로드에서 이득이 적은지 판단합니다.
- DBU와 클라우드 인프라 비용이 컴퓨트 유형마다 어떻게 나뉘어 청구되는지 구조를 설명합니다.
- Spark의 드라이버, 익스큐터, 지연 실행(Lazy evaluation)을 이해하고 컴퓨트 설정과 연결합니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [컴퓨트 종류와 선택 기준](compute-types-and-selection.md) | 100 | 세 가지 컴퓨트 분류, 워크로드별 선택 표, 평면(Plane) 개념, 선택 기준 체크리스트 |
| 2 | [서버리스 컴퓨트](serverless-compute.md) | 200 | 노트북·Jobs·파이프라인용 서버리스, 환경 버전과 기본 환경, 성능 모드, 타임아웃 |
| 3 | [서버리스 제약과 지원 기능](serverless-limitations.md) | 300 | 언어·API·UDF·스트리밍·캐싱 제약, DataFrame 캐싱(Public Preview), 데이터 소스 |
| 4 | [클래식 컴퓨트](classic-compute.md) | 200 | 액세스 모드(Standard, Dedicated, Auto), Databricks Runtime 버전, 오토스케일링 |
| 5 | [인스턴스 풀과 컴퓨트 정책](pools-and-policies.md) | 300 | 풀의 유휴 인스턴스 과금 규칙, 풀 권한, 컴퓨트 정책의 제한 범위 |
| 6 | [SQL 웨어하우스](sql-warehouses.md) | 200 | Serverless·Pro·Classic 유형, 크기(T-shirt size), 클러스터 수, 자동 중지, 큐 |
| 7 | [Photon](photon.md) | 200 | Photon의 가속 대상, 지원 컴퓨트, 활성화 방법, 적합하지 않은 워크로드 |
| 8 | [비용 구조 비교](cost-structure.md) | 300 | DBU와 클라우드 인스턴스 청구 분리, 유형별 청구 구조 표, 청구 데이터 확인 방법 (단가 없음) |
| 9 | [Spark 기초](spark-basics.md) | 100 | 드라이버와 익스큐터, 클러스터 매니저, 변환과 액션, 지연 실행 |
| 10 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 10개와 실무 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 1번 페이지의 선택 기준을 먼저 잡은 뒤 서버리스 페이지(2·3번)와 클래식 페이지(4·5번)를 읽고, SQL 웨어하우스(6번)와 Photon(7번)으로 넘어가는 흐름을 권장합니다. 비용 구조(8번)는 모든 유형을 본 뒤에 읽으면 비교가 쉽습니다. Spark 기초(9번)는 Spark 경험이 없는 독자라면 2번 페이지 전에 읽어도 됩니다.

## 선수 지식

- **SQL 기초**: `SELECT`, `JOIN`, `GROUP BY`를 읽고 쓸 수 있어야 합니다. SQL 웨어하우스 페이지의 예시가 이 수준을 가정합니다.
- **Python 기초**: 노트북 예시는 PySpark(Python) 코드를 씁니다. 함수 호출과 객체 메서드를 이해하면 충분합니다.
- **Unity Catalog 기초**: 서버리스 노트북과 Job은 Unity Catalog가 활성화된 워크스페이스가 필요합니다. 카탈로그, 스키마, 테이블 3단계 이름을 알고 있어야 합니다. Unity Catalog 자체는 이 장의 범위가 아니며, 06장에서 다룹니다.
- **클라우드 계정 개념**: 클래식 컴퓨트와 Pro·Classic SQL 웨어하우스는 고객 클라우드 계정의 인스턴스를 씁니다. 가상 머신(VM) 인스턴스와 클라우드 청구의 기본 개념을 알고 있으면 8번 페이지를 이해하기 쉽습니다.

## 이 장의 읽는 법

각 기능 페이지는 같은 구조를 따릅니다. 왜 필요한지, 어떻게 동작하는지, 어떻게 쓰는지, 트레이드오프, 주의사항 순서입니다. 기능마다 상태(GA, Public Preview, Beta 등)를 표기하고, 같은 기능이라도 기본값이나 상태가 다르면 나누어 적습니다.

예시 코드는 공식 문서에 있는 API, 명령, SQL 문법만 사용합니다. 문서에서 확인하지 못한 파라미터는 쓰지 않았습니다.

> **참고** Databricks 제품 명칭은 현재 공식 문서 표기를 따릅니다. 예를 들어 클래식 컴퓨트의 액세스 모드는 문서 표기 그대로 Standard와 Dedicated로 씁니다. 이전 자료에서 쓰던 명칭을 만나면 해당 페이지의 용어 설명을 참고하십시오.

> **참고** 이 장의 사실은 공식 문서 원문을 확인한 내용입니다. 문서끼리 표현이 엇갈리는 항목은 해당 페이지에 "문서 간 상충"으로 따로 적었습니다. 이 항목들은 실제 적용 전에 최신 원문을 다시 확인하십시오. 서버리스 환경 버전처럼 자주 바뀌는 항목은 특히 그렇습니다.

> **참고** 이 장은 AWS 문서(`docs.databricks.com/aws/en/`)를 기준으로 작성했습니다. Azure 문서(`learn.microsoft.com/azure/databricks/`)는 리전 가용성이나 인스턴스 유형이 다를 수 있습니다. 이 장에서는 Azure 값을 섞지 않았습니다.

## 참고 문서

- [Compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/)
- [Serverless compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/)
- [Serverless compute limitations (AWS)](https://docs.databricks.com/aws/en/compute/serverless/limitations)
- [SQL warehouses 개요 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/)
- [Access mode limitations (AWS)](https://docs.databricks.com/aws/en/compute/access-mode-limitations)
- [Release notes (AWS, 2026)](https://docs.databricks.com/aws/en/release-notes/product/2026/)
