# 4. 데이터 엔지니어링 (Lakeflow)

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

데이터 엔지니어링은 원천 시스템의 데이터를 레이크하우스로 가져와(수집, Ingestion), 테이블 단위로 변환하고(파이프라인), 정해진 시점이나 이벤트에 맞춰 실행하는(오케스트레이션, Jobs) 일입니다. Databricks는 이 세 가지를 **Lakeflow** 라는 이름 아래 묶어 제공합니다. 이 장은 데이터 엔지니어, 분석 엔지니어, 플랫폼 담당자를 대상으로 하며, 수집 방법을 고르는 기준부터 파이프라인 정의, 잡 운영, 스트리밍 기초까지 실제 설정 단위로 설명합니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- 원천 유형(파일, SaaS, 데이터베이스, 메시지 버스)과 데이터 특성에 따라 수집 방법을 고릅니다.
- Lakeflow Connect의 커넥터 분류와 상태 라벨을 구분하고, managed connector의 과금 구조를 `system.billing.usage`로 추적합니다.
- Auto Loader의 파일 감지 모드(directory listing, file notification)와 스키마 추론·진화 옵션을 설정합니다.
- Lakeflow 파이프라인에서 스트리밍 테이블과 구체화된 뷰(Materialized view)를 정의하고, expectations로 데이터 품질 규칙을 적용합니다.
- `AUTO CDC`로 변경 데이터를 SCD Type 1 또는 Type 2 테이블에 반영하고, 이벤트 로그로 파이프라인 상태를 확인합니다.
- Lakeflow Jobs에서 태스크 유형, 트리거, 파라미터, 태스크 값, 조건 분기(Run if, If/else, For each)를 조합합니다.
- 재시도, 타임아웃, 알림, 실패 실행 복구(Repair run)의 동작을 이해하고 멱등성을 설계합니다.
- Structured Streaming의 트리거, 체크포인트, 워터마크의 역할과 쿼리 변경 시 제약을 설명합니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [수집 방법 선택 기준](choose-ingestion-method.md) | 100 | 원천별 권장 경로, Lakeflow Connect·Auto Loader·Lakeflow 파이프라인·Jobs의 역할 구분 |
| 2 | [Lakeflow Connect](lakeflow-connect.md) | 100 | 커넥터 분류, 상태 라벨, 관리형 커넥터의 과금 구조와 비용 추적 |
| 3 | [Auto Loader](auto-loader.md) | 200 | `cloudFiles` 소스, 파일 감지 모드, 스키마 추론·진화, 운영 설정 |
| 4 | [스트리밍 테이블과 구체화된 뷰](pipelines-streaming-tables-and-mvs.md) | 200 | Lakeflow 파이프라인의 흐름(flow), 스트리밍 테이블, 구체화된 뷰, 선택 기준 |
| 5 | [Expectations와 AUTO CDC](pipelines-expectations-and-cdc.md) | 200 | 데이터 품질 규칙 3가지 동작, 변경 데이터 반영(SCD Type 1·2), 스냅샷 변형 |
| 6 | [파이프라인 이벤트 로그](pipelines-event-log.md) | 200 | `event_log()`, 주요 열과 이벤트 유형, `pipeline_events` 시스템 테이블 |
| 7 | [Lakeflow Jobs 태스크와 트리거](jobs-tasks-and-triggers.md) | 200 | 태스크 유형, 트리거 종류와 제한, 스케줄의 최소 간격과 시간대 |
| 8 | [파라미터·태스크 값·조건 분기](jobs-parameters-and-control-flow.md) | 200 | 잡 파라미터, 태스크 값, 동적 값 참조, Run if, If/else, For each |
| 9 | [재시도·알림·Repair run](jobs-retries-notifications-repair.md) | 300 | 재시도와 타임아웃, 알림 이벤트, 실패 실행 복구와 멱등성 |
| 10 | [Structured Streaming 기초](structured-streaming-basics.md) | 300 | 트리거, 체크포인트, 워터마크, 출력 모드, Auto Loader와의 결합 |
| 11 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 10개와 실무 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 수집(1~3) → 파이프라인(4~6) → 오케스트레이션(7~9) 순서로 읽으면 데이터 흐름과 잡 구성을 자연스럽게 연결할 수 있습니다. 10번 페이지는 1~9번 페이지의 스트리밍 개념을 뒷받침하므로 파이프라인과 함께 읽는 것을 권장합니다.

## 이름 표기 안내

Databricks 공식 문서는 파이프라인 제품을 **Spark Declarative Pipelines on Lakeflow**(페이지 제목)로 소개하고, 본문에서는 **Lakeflow 파이프라인(Lakeflow pipelines)** 이라고 부릅니다. 이 장은 본문 표기를 따릅니다. 이전 이름인 Delta Live Tables(DLT)는 공식 문서의 "What happened to Delta Live Tables (DLT)?" 설명을 따라 구 명칭으로만 병기합니다. 리브랜딩이 잦으므로 실제 작업 전 각 페이지의 참고 문서에서 현재 표기를 다시 확인하십시오.

## 선수 지식

- **SQL 기초**: `SELECT`, `CREATE TABLE`, 집계와 조인을 읽을 수 있어야 합니다. 파이프라인 정의는 SQL과 Python 두 가지로 가능합니다.
- **Python 기초**: 노트북 태스크와 `spark.readStream` 예제를 읽을 수 있어야 합니다.
- **Delta Lake 기초**: 스트리밍 테이블과 구체화된 뷰는 Delta 테이블입니다. [02장 레이크하우스 스토리지](../02-lakehouse-storage/README.md)에서 다룹니다.
- **Unity Catalog 기초**: 카탈로그·스키마·테이블 3단계 이름, 볼륨(Volume), 외부 위치(External location), 권한 모델을 알고 있어야 합니다. 거버넌스 세부는 [06장 Unity Catalog 거버넌스](../06-unity-catalog/README.md)에서 다룹니다.
- **컴퓨트 개념**: 서버리스와 클래식 컴퓨트의 차이는 [03장 컴퓨트](../03-compute/README.md)에서 다룹니다. 이 장의 여러 기능은 컴퓨트 종류에 따라 지원 범위가 다르므로, 각 페이지의 주의 항목을 함께 확인하십시오.

## 이 장의 읽는 법

각 기능 페이지는 **왜 필요한가 → 어떻게 동작하는가 → 어떻게 쓰는가 → 트레이드오프 → 주의사항** 순서를 따릅니다. 기능마다 상태 라벨(GA, Public Preview, Beta)을 표기하고, 문서에 상태 라벨이 없으면 "문서에 명시 없음"으로 적습니다.

> **참고** 이 장의 사실은 공식 문서 원문과 2026년 8~10월 릴리즈 노트에서 확인한 내용입니다. 문서에 없는 과금 단가, 제한 수치, 실측치는 넣지 않았습니다. 상태 라벨은 릴리즈 노트 날짜 기준이므로 승격(Beta → Public Preview → GA)될 수 있습니다.

> **참고** 이 장은 AWS 문서(`docs.databricks.com/aws/en/`)를 기준으로 작성했습니다. Azure 문서(`learn.microsoft.com/azure/databricks/`)와 기능 가용성이 다를 수 있습니다.

## 참고 문서

- [Data engineering with Databricks](https://docs.databricks.com/aws/en/data-engineering/)
- [Lakeflow Connect (What is Lakeflow Connect?)](https://docs.databricks.com/aws/en/ingestion/overview)
- [Lakeflow Jobs](https://docs.databricks.com/aws/en/jobs/)
- [Spark Declarative Pipelines on Lakeflow](https://docs.databricks.com/aws/en/ldp/)
- [Structured Streaming concepts](https://docs.databricks.com/aws/en/structured-streaming/concepts)
- [Release notes (2026)](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
