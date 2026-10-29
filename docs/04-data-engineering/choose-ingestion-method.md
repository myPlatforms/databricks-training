# 수집 방법 선택 기준

> 기준일: 2026-10-29 · 근거: 공식 문서

## 한눈에 보기

데이터를 레이크하우스로 가져오는 방법은 여러 가지입니다. 원천이 파일인지, SaaS 애플리케이션 API인지, 데이터베이스 변경 로그인지, 메시지 버스인지에 따라 맞는 도구가 다릅니다. 공식 문서 "Ingest with SQL and Spark APIs" 페이지는 수집 계층을 **Structured Streaming**, **Lakeflow 파이프라인**, **Managed connectors**(관리형 커넥터)로 나누어 설명합니다. 이 페이지는 원천별 시작점을 고르는 기준을 정리합니다.

공식 Lakeflow Connect 개요는 한 가지 원칙을 먼저 제시합니다. **가장 관리되는 계층부터 시작하고**, 요구를 만족하지 못하면(예: 원천을 지원하지 않는 경우) 다음 계층으로 내려갑니다.

## 왜 기준이 필요한가

수집 방법을 잘못 고르면 다음 문제가 생깁니다.

- **구현 부담**: SaaS API를 직접 호출하는 코드를 만들면 인증, 페이지네이션, 증분 조회, 스키마 변경, 재시도를 모두 직접 관리해야 합니다. Lakeflow Connect 문서는 커넥터가 "source-specific authentication, incremental reads, schema evolution, and automated retries"를 처리한다고 설명합니다.
- **지연과 비용의 불일치**: 실시간 스트림이 필요하지 않은 파일 적재를 상시 실행 파이프라인으로 만들면 불필요한 컴퓨트가 계속 과금됩니다. 반대로 저지연 요구를 일 단위 배치로 처리하면 요구를 충족하지 못합니다.
- **중복과 누락**: 파일을 디렉터리 전체 목록으로 매번 다시 읽는 방식은 파일이 많아질수록 느려지고, 체크포인트 없이 짜면 재시작 시 중복이나 누락이 생깁니다.

## 어떻게 동작하는가

### 원천별 선택지

문서가 제시하는 원천별 선택지는 다음과 같습니다. 표는 "Choose an option" 표의 항목을 옮긴 것입니다.

| 원천 | 선택지 (문서 원문 표기) |
|---|---|
| 클라우드 오브젝트 스토리지 | Auto Loader with Structured Streaming / Auto Loader with Lakeflow pipelines / Auto Loader with Databricks SQL |
| SFTP 서버 | Ingest files from SFTP servers (Python, SQL) |
| Apache Kafka | Structured Streaming with Kafka source / Lakeflow pipelines with Kafka source / Databricks SQL with Kafka source |
| Amazon Kinesis | Structured Streaming with Kinesis source / Lakeflow pipelines with Kinesis source / Databricks SQL with Kinesis source |
| Google Pub/Sub | Structured Streaming with Pub/Sub source |
| SaaS, 데이터베이스 등 | Lakeflow Connect 관리형 커넥터(managed connectors) |

### 파이프라인 계층의 권장

파이프라인 계층에서는 공식 문서가 "Databricks recommends Lakeflow pipelines, built on Apache Spark™ Declarative Pipelines (SDP), for most ETL workloads"라고 권장합니다. 아래 표는 "Choose an ETL approach" 페이지의 시나리오별 권장을 정리한 것입니다.

| 시나리오 | 공식 문서의 권장 | 핵심 구성 요소 (문서 표기) |
|---|---|---|
| 새 배치·증분 ETL (기본 선택) | Lakeflow 파이프라인 | streaming tables, materialized views, flows, `AUTO CDC`, `REPLACE WHERE` |
| 이미 dbt 프로젝트를 운영 중 | dbt on Databricks (dbt 태스크를 Lakeflow Jobs에서 실행) | dbt models, dbt tasks in Lakeflow Jobs |
| 복잡한 변환 로직을 Spark 코드로 직접 작성 | Spark 노트북·스크립트를 Lakeflow Jobs로 오케스트레이션 | Spark DataFrames, notebooks, Lakeflow Jobs |
| 패키지화된 절차형 SQL 로직 | 저장 프로시저(`CREATE PROCEDURE`), SQL 웨어하우스에서 실행 | CREATE PROCEDURE, SQL scripting |

> **참고** 위 "Choose an ETL approach" 페이지는 Lakeflow Connect, Auto Loader, COPY INTO를 별도 시나리오로 다루지 않습니다. 이 세 가지는 위 "Choose an option" 표와 각 전용 페이지를 기준으로 판단합니다. 수집 개요 문서는 증분 SQL 수집에서 `CREATE STREAMING TABLE` 구문을 `COPY INTO`의 권장 대안으로 설명합니다.

### 계층 관계 정리

| 계층 | 역할 | 이 장의 페이지 |
|---|---|---|
| 관리형 커넥터 (Lakeflow Connect) | SaaS·데이터베이스·파일 서비스에서 증분 수집을 선언적으로 설정 | [Lakeflow Connect](lakeflow-connect.md) |
| 파일 증분 로더 (Auto Loader) | 클라우드 스토리지 파일을 `cloudFiles` 소스로 증분 읽기 | [Auto Loader](auto-loader.md) |
| 파이프라인 (Lakeflow 파이프라인) | 스트리밍 테이블·구체화된 뷰를 선언형으로 정의하고 의존성을 관리 | [스트리밍 테이블과 구체화된 뷰](pipelines-streaming-tables-and-mvs.md) |
| 오케스트레이션 (Lakeflow Jobs) | 노트북·파이프라인·SQL 등 태스크를 스케줄·이벤트로 실행 | [Lakeflow Jobs 태스크와 트리거](jobs-tasks-and-triggers.md) |
| 저수준 스트리밍 (Structured Streaming) | 직접 짠 Spark 스트리밍 쿼리의 기반 | [Structured Streaming 기초](structured-streaming-basics.md) |

Lakeflow Connect 수집 결과 테이블은 **스트리밍 테이블** 입니다. 문서는 수집 파이프라인이 원천 데이터를 스트리밍 테이블에 쓴다고 설명합니다. 즉 관리형 커넥터는 내부적으로 파이프라인을 통해 스트리밍 테이블을 채웁니다. Auto Loader도 Lakeflow 파이프라인 안에서 쓸 수 있습니다.

### 직접 쓰기 경로

문서 개요 페이지는 애플리케이션이 레코드를 스트리밍 테이블에 직접 쓰는 경로로 **Zerobus Ingest API**(Direct write)를 소개합니다. 릴리즈 노트에 따르면 "Zerobus Ingest into streaming tables"는 2026-08-26에 GA로 발표되었고, "Zerobus Ingest into default storage"는 2026-09-07에 Public Preview로 발표되었습니다. 스트리밍 테이블에 쓰는 방식은 관리형 Delta 테이블에 쓰는 방식과 같고, 같은 한도와 쿼터가 적용됩니다. 이 장의 세부 설정은 다루지 않습니다.

### 대안: 복사하지 않는 경로

수집 개요 문서는 수집이 원천 데이터를 복사해 중복 데이터를 만든다는 점을 밝히고, 복사가 필요 없는 경우의 도구를 함께 소개합니다.

| 도구 | 문서 설명 |
|---|---|
| Lakehouse Federation | 외부 데이터 소스를 옮기지 않고 질의 |
| OpenSharing | 플랫폼·클라우드·리전을 넘어 데이터를 안전하게 공유 |

## 어떻게 쓰는가

### 선택 절차

1. **원천 유형 확인**: 원천이 파일(클라우드 스토리지, SFTP), SaaS API, 데이터베이스 CDC, 메시지 버스 중 어디에 속하는지 구분합니다.
2. **가장 관리된 계층부터 확인**: 위 "원천별 선택지" 표에서 해당 원천의 선택지를 찾습니다. SaaS·데이터베이스는 관리형 커넥터를 먼저 확인합니다. 원천을 지원하지 않으면 다음 계층으로 내려갑니다.
3. **지연 요구 확인**: 몇 초 이내가 필요한지, 하루 단위로 충분한지 정합니다.
4. **처리 계층 결정**: 테이블을 만들 때 파이프라인을 쓸지, 노트북을 Jobs로 돌릴지 정합니다.
5. **복사 필요 여부 확인**: 데이터를 옮길 필요가 없다면 Lakehouse Federation을 검토합니다.

| 질문 | 예이면 시작점 |
|---|---|
| 원천이 SaaS 앱 또는 데이터베이스인가? | Lakeflow Connect 관리형 커넥터 (원천 목록 확인) |
| 클라우드 스토리지에 파일이 쌓이는가? | Auto Loader (Lakeflow 파이프라인 안에서 쓰는 것이 권장) |
| Kafka·Kinesis·Pub/Sub 메시지인가? | 해당 소스를 쓰는 Structured Streaming 또는 Lakeflow 파이프라인 |
| 사람이 직접 올리는 파일인가? | Add data UI(파일 업로드)로 테이블 생성 |
| 데이터를 복사하지 않고 조회만 하면 되는가? | Lakehouse Federation |

### 최소 예시: 파일 수집

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

> **참고** 공식 문서는 Auto Loader를 Lakeflow 파이프라인 안에서 쓸 때 스키마 위치와 체크포인트 위치를 직접 지정할 필요가 없다고 설명합니다. 위 예시는 Structured Streaming 방식입니다.

## 트레이드오프

### 방식별 비교

| 방법 | 장점 | 비용·제약 | 맞는 경우 |
|---|---|---|---|
| 관리형 커넥터 | 인증·증분·스키마 변경·재시도를 플랫폼이 처리 | 커넥터 목록에 있는 원천만 가능, 상태가 Beta인 커넥터 다수 | SaaS, 데이터베이스 CDC, 감사 로그 |
| Auto Loader | 파일을 증분으로 감지, 스키마 추론·진화 지원 | 파일 기반 원천에 한정 | 클라우드 스토리지에 쌓이는 파일 |
| 파이프라인 (Lakeflow 파이프라인) | 의존성·증분 처리를 선언형으로 관리 | 파이프라인 정의 방식을 익혀야 함 | 배치·증분 ETL의 기본 선택 |
| Spark 노트북 + Jobs | 임의의 Spark 로직 | 증분 상태와 품질 규칙을 직접 관리 | 파이프라인 문법으로 표현하기 어려운 로직 |

### 증분 처리·스키마 진화·과금 비교

아래 표는 각 방식의 공식 문서 설명을 항목별로 옮긴 것입니다. 문서에 없는 수치나 단가는 넣지 않았습니다.

| 방식 | 증분 처리 (문서 설명) | 스키마 진화 (문서 설명) | 과금·비용 성격 (문서 설명) |
|---|---|---|---|
| 관리형 커넥터 | 첫 실행은 선택 데이터 전체를 수집하고, 이후에는 변경 추적으로 **변경분만** 수집. 원천마다 방식이 다름(예: SQL Server는 change tracking과 CDC 둘 다 사용) | 자동 스키마 진화를 포함 | 데이터베이스·스트리밍 커넥터 파이프라인은 기본적으로 서버리스 컴퓨트에서 실행. 비용은 `system.billing.usage`로 추적 |
| Auto Loader | 새로 도착한 파일을 증분으로 처리. 파일 감지는 디렉터리 목록 모드가 기본이며, 대부분 워크로드에는 파일 알림 모드를 권장 | 스키마 드리프트 감지, 변경 알림, 무시되거나 유실될 데이터 구조(rescue) 지원 | 파일 탐색 비용이 디렉터리 수가 아니라 수집 파일 수에 비례. 파일 알림 모드는 디렉터리 목록 조회를 피해 클라우드 비용을 줄일 수 있음 |
| Lakeflow 파이프라인 | 선언된 흐름의 증분 처리를 엔진이 관리 | 문서 개요에 별도 항목 없음 (스트리밍 테이블 정의에 따름) | 파이프라인 실행 컴퓨트 기준 |
| Structured Streaming 직접 구현 | 체크포인트로 진행 상태를 직접 관리 | 스키마 처리 로직을 직접 설계 | 실행 컴퓨트 기준. 실시간 모드(RTM)는 장시간 배치로 동작 |

> **참고** Lakeflow Connect 데이터베이스 커넥터는 인제스천 게이트웨이를 별도 잡의 연속 태스크로 실행합니다. 게이트웨이 비용이 파이프라인 비용과 별도로 발생한다는 점을 설계 단계에서 확인하십시오.

### 언제 어떤 방식을 피하는가

- **관리형 커넥터**: 원천이 커넥터 목록에 없으면 쓸 수 없습니다. 이때는 커뮤니티 커넥터(오픈소스, Databricks SLA 없음)나 커스텀 커넥터(직접 빌드·배포)를 검토합니다.
- **Auto Loader**: 파일이 아닌 원천(예: 관계형 데이터베이스 변경 로그)에는 맞지 않습니다.
- **Spark 노트북 + Jobs**: 증분 상태와 품질 규칙을 직접 관리해야 하므로, 파이프라인으로 표현할 수 있는 로직이면 피합니다.

## 주의사항

- **가장 관리된 계층부터**: 공식 문서 권장대로 관리 수준이 높은 계층부터 확인합니다. 낮은 계층을 먼저 고르면 인증·재시도·스키마 처리를 직접 맡게 됩니다.
- **상태 라벨 먼저 확인**: 관리형 커넥터 다수가 Beta입니다. 운영 적용 전에 해당 커넥터의 릴리즈 노트 날짜와 상태를 확인하십시오 (자세한 내용은 [Lakeflow Connect](lakeflow-connect.md) 페이지).
- **표준 커넥터와 관리형 커넥터 구분**: 2026-08-04 릴리즈 노트는 Google Drive와 SharePoint에 대해 두 변형을 함께 GA로 발표했습니다. 관리형 커넥터는 완전 관리형 수집 파이프라인용이고, 표준 커넥터(standard connector)는 Spark·SQL API로 만드는 커스텀 파이프라인용입니다. 같은 원천이라도 변형에 따라 쓰는 방식이 다르므로, 어느 변형을 쓸지는 해당 커넥터 페이지에서 확인하십시오.
- **저지연 요구**: 밀리초 단위처럼 즉시 응답이 필요한 운영 워크로드라면 Structured Streaming의 실시간 모드(RTM, real-time mode)를 검토합니다. RTM은 Structured Streaming의 트리거 유형으로, 문서는 사기 탐지나 실시간 개인화처럼 즉시 응답이 필요한 운영 워크로드를 대상으로 설명합니다 ([Structured Streaming 기초](structured-streaming-basics.md) 참고).
- **Unity Catalog 권한**: 볼륨과 외부 위치 접근 권한은 수집 경로마다 다릅니다. 권한 모델은 [06장 Unity Catalog](../06-unity-catalog/README.md)에서 다룹니다.
- **복사 중복**: 수집은 데이터를 복사하므로 원천과의 동기화 지연과 중복 저장이 생깁니다. 복사가 불필요하면 Lakehouse Federation을 먼저 검토합니다.

## 참고 문서

- [Ingest with SQL and Spark APIs](https://docs.databricks.com/aws/en/ingestion/)
- [What is Lakeflow Connect?](https://docs.databricks.com/aws/en/ingestion/overview)
- [Choose an ETL approach on Databricks](https://docs.databricks.com/aws/en/data-engineering/choose-etl-approach)
- [What is Auto Loader?](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/)
- [Real-time mode concepts](https://docs.databricks.com/aws/en/structured-streaming/real-time)
- [Release notes, 2026년 8월](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
- [Release notes, 2026년 9월](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
