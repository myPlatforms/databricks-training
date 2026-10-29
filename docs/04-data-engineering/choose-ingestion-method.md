# 수집 방법 선택 기준

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

데이터를 레이크하우스로 가져오는 방법은 여러 가지입니다. 원천이 파일인지, SaaS 애플리케이션 API인지, 데이터베이스 변경 로그인지, 메시지 버스인지에 따라 맞는 도구가 다릅니다. 공식 문서 "Ingest with SQL and Spark APIs" 페이지는 수집 계층을 **Structured Streaming**, **Lakeflow 파이프라인**, **Managed connectors**(관리형 커넥터)로 나누어 설명합니다. 이 페이지는 원천별 시작점을 고르는 기준을 정리합니다.

## 왜 기준이 필요한가

수집 방법을 잘못 고르면 다음 문제가 생깁니다.

- **구현 부담**: SaaS API를 직접 호출하는 코드를 만들면 인증, 페이지네이션, 증분 조회, 스키마 변경, 재시도를 모두 직접 관리해야 합니다. Lakeflow Connect 문서는 커넥터가 "source-specific authentication, incremental reads, schema evolution, and automated retries"를 처리한다고 설명합니다.
- **지연과 비용의 불일치**: 실시간 스트림이 필요하지 않은 파일 적재를 상시 실행 파이프라인으로 만들면 불필요한 컴퓨트가 계속 과금됩니다. 반대로 저지연 요구를 일 단위 배치로 처리하면 요구를 충족하지 못합니다.
- **중복과 누락**: 파일을 디렉터리 전체 목록으로 매번 다시 읽는 방식은 파일이 많아질수록 느려지고, 체크포인트 없이 짜면 재시작 시 중복이나 누락이 생깁니다.

## 어떻게 동작하는가

문서가 제시하는 원천별 선택지는 다음과 같습니다. 표는 "Choose an option" 표의 항목을 옮긴 것입니다.

| 원천 | 선택지 (문서 원문 표기) |
|---|---|
| 클라우드 오브젝트 스토리지 | Auto Loader with Structured Streaming / Auto Loader with Lakeflow pipelines / Auto Loader with Databricks SQL |
| SFTP 서버 | Ingest files from SFTP servers (Python, SQL) |
| Apache Kafka | Structured Streaming with Kafka source / Lakeflow pipelines with Kafka source / Databricks SQL with Kafka source |
| Amazon Kinesis | Structured Streaming with Kinesis source / Lakeflow pipelines with Kinesis source / Databricks SQL with Kinesis source |
| Google Pub/Sub | Structured Streaming with Pub/Sub source |
| SaaS, 데이터베이스 등 | Lakeflow Connect 관리형 커넥터(managed connectors) |

파이프라인 계층에서는 공식 문서가 "Databricks recommends Lakeflow pipelines, built on Apache Spark™ Declarative Pipelines (SDP), for most ETL workloads"라고 권장합니다. 아래 표는 "Choose an ETL approach" 페이지의 시나리오별 권장을 정리한 것입니다.

| 시나리오 | 공식 문서의 권장 |
|---|---|
| 새 배치·증분 ETL (기본 선택) | Lakeflow 파이프라인 (streaming tables, materialized views, flows, `AUTO CDC`) |
| 이미 dbt 프로젝트를 운영 중 | dbt on Databricks (dbt 태스크를 Lakeflow Jobs에서 실행) |
| 복잡한 변환 로직을 Spark 코드로 직접 작성 | Spark 노트북·스크립트를 Lakeflow Jobs로 오케스트레이션 |
| 패키지화된 절차형 SQL 로직 | 저장 프로시저(`CREATE PROCEDURE`), SQL 웨어하우스에서 실행 |

> **참고** 위 "Choose an ETL approach" 페이지는 Lakeflow Connect, Auto Loader, COPY INTO를 별도 시나리오로 다루지 않습니다. 이 세 가지는 위 "Choose an option" 표와 각 전용 페이지를 기준으로 판단합니다. 문서에서 `COPY INTO`는 `CREATE STREAMING TABLE`이 대체하는 옵션으로 언급됩니다.

### 계층 관계 정리

| 계층 | 역할 | 이 장의 페이지 |
|---|---|---|
| 관리형 커넥터 (Lakeflow Connect) | SaaS·데이터베이스·파일 서비스에서 증분 수집을 선언적으로 설정 | [Lakeflow Connect](lakeflow-connect.md) |
| 파일 증분 로더 (Auto Loader) | 클라우드 스토리지 파일을 `cloudFiles` 소스로 증분 읽기 | [Auto Loader](auto-loader.md) |
| 파이프라인 (Lakeflow 파이프라인) | 스트리밍 테이블·구체화된 뷰를 선언형으로 정의하고 의존성을 관리 | [스트리밍 테이블과 구체화된 뷰](pipelines-streaming-tables-and-mvs.md) |
| 오케스트레이션 (Lakeflow Jobs) | 노트북·파이프라인·SQL 등 태스크를 스케줄·이벤트로 실행 | [Lakeflow Jobs 태스크와 트리거](jobs-tasks-and-triggers.md) |
| 저수준 스트리밍 (Structured Streaming) | 직접 짠 Spark 스트리밍 쿼리의 기반 | [Structured Streaming 기초](structured-streaming-basics.md) |

Lakeflow Connect 수집 결과 테이블은 **스트리밍 테이블** 입니다. 즉 관리형 커넥터는 내부적으로 파이프라인을 통해 스트리밍 테이블을 채웁니다. Auto Loader도 Lakeflow 파이프라인 안에서 쓸 수 있습니다.

### 직접 쓰기 경로

문서 개요 페이지는 애플리케이션이 레코드를 스트리밍 테이블에 직접 쓰는 경로로 **Zerobus Ingest API**(Direct write)를 소개합니다. 릴리즈 노트에 따르면 "Zerobus Ingest into streaming tables"는 2026-08-26에 GA로 발표되었고, "Zerobus Ingest into default storage"는 2026-09-07에 Public Preview로 발표되었습니다. 이 장의 세부 설정은 다루지 않습니다.

## 어떻게 쓰는가

선택 과정은 다음 순서로 진행합니다.

1. **원천 유형 확인**: 원천이 파일(클라우드 스토리지, SFTP), SaaS API, 데이터베이스 CDC, 메시지 버스 중 어디에 속하는지 구분합니다.
2. **전용 경로 선택**: 위 "Choose an option" 표에서 해당 원천의 선택지를 찾습니다. SaaS·데이터베이스는 관리형 커넥터를 먼저 확인합니다.
3. **지연 요구 확인**: 몇 초 이내가 필요한지, 하루 단위로 충분한지 정합니다.
4. **처리 계층 결정**: 테이블을 만들 때 파이프라인을 쓸지, 노트북을 Jobs로 돌릴지 정합니다.

다음은 파일 수집의 최소 예시입니다. Auto Loader 페이지의 원문 예제를 그대로 옮겼으며, 자세한 옵션은 [Auto Loader](auto-loader.md) 페이지에서 다룹니다.

```python
(spark.readStream.format("cloudFiles")
  .option("cloudFiles.format", "parquet")
  # The schema location directory keeps track of your data schema over time
  .option("cloudFiles.schemaLocation", "<path-to-schema>")
  .load("<path-to-source-data>")
  .writeStream
  .option("checkpointLocation", "<path-to-checkpoint>")
  .start("<path-to-target>"))
```

## 트레이드오프

| 방법 | 장점 | 비용·제약 | 맞는 경우 |
|---|---|---|---|
| 관리형 커넥터 | 인증·증분·스키마 변경을 플랫폼이 처리 | 커넥터 목록에 있는 원천만 가능, 상태가 Beta인 커넥터 다수 | SaaS, 데이터베이스 CDC, 감사 로그 |
| Auto Loader | 파일을 증분으로 감지, 스키마 추론 지원 | 파일 기반 원천에 한정 | 클라우드 스토리지에 쌓이는 파일 |
| 파이프라인 (Lakeflow 파이프라인) | 의존성·증분 처리를 선언형으로 관리 | 파이프라인 정의 방식을 익혀야 함 | 배치·증분 ETL의 기본 선택 |
| Spark 노트북 + Jobs | 임의의 Spark 로직 | 증분 상태와 품질 규칙을 직접 관리 | 파이프라인 문법으로 표현하기 어려운 로직 |

## 주의사항

- **상태 라벨 먼저 확인**: 관리형 커넥터 다수가 Beta입니다. 운영 적용 전에 해당 커넥터의 릴리즈 노트 날짜와 상태를 확인하십시오 (자세한 내용은 [Lakeflow Connect](lakeflow-connect.md) 페이지).
- **"표준 커넥터"와 "관리형 커넥터" 구분**: 문서 원문에서 "Standard connectors"라는 분류명은 개요 페이지에서 확인되지 않았습니다. 대신 "managed connectors"라는 표현이 나옵니다. 2026-08-04 릴리즈 노트는 Google Drive와 SharePoint에 대해 "managed"와 "standard" 두 커넥터가 모두 GA라고 발표했으므로, 같은 원천이라도 커넥터 변형이 나뉠 수 있습니다. 어느 변형을 쓸지는 해당 커넥터 페이지에서 확인하십시오.
- **지연 요구와 스케줄러**: Jobs의 스케줄러는 저지연 작업용이 아닙니다. 밀리초 단위 응답이 필요하면 Structured Streaming의 실시간 모드(real-time mode)를 검토합니다 ([Structured Streaming 기초](structured-streaming-basics.md) 참고).
- **Unity Catalog 권한**: 볼륨과 외부 위치 접근 권한은 수집 경로마다 다릅니다. 권한 모델은 06장에서 다룹니다.

## 참고 문서

- [Ingest with SQL and Spark APIs](https://docs.databricks.com/aws/en/ingestion/)
- [What is Lakeflow Connect?](https://docs.databricks.com/aws/en/ingestion/overview)
- [Choose an ETL approach on Databricks](https://docs.databricks.com/aws/en/data-engineering/choose-etl-approach)
- [What is Auto Loader?](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/)
- [Release notes, 2026년 8월](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
- [Release notes, 2026년 9월](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
