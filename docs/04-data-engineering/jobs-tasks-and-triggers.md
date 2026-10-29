# Lakeflow Jobs 태스크와 트리거

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Lakeflow Jobs(잡)는 노트북, 파이프라인, SQL, Python 스크립트 같은 **태스크** 를 순서대로 묶어 실행하는 오케스트레이션 기능입니다. 잡은 하나 이상의 **트리거** 가 발생했을 때 실행됩니다. 트리거는 시간(스케줄), 파일 도착, 테이블 업데이트, 모델 업데이트, 잡 연속 실행 등이 될 수 있습니다. 이 페이지는 태스크 유형과 트리거 종류, 그리고 각 트리거의 제한을 정리합니다. 파라미터와 조건 분기는 [파라미터·태스크 값·조건 분기](jobs-parameters-and-control-flow.md), 재시도와 복구는 [재시도·알림·Repair run](jobs-retries-notifications-repair.md)에서 다룹니다.

## 왜 필요한가

여러 노트북이나 파이프라인을 cron과 셸 스크립트로 묶으면 다음 문제가 생깁니다.

- 한 단계가 실패했을 때 어디까지 끝났는지 알기 어렵습니다.
- 실행 이력, 알림, 재시도를 단계마다 따로 만들어야 합니다.
- 파일이 도착했을 때 실행하는 것 같은 이벤트 기반 실행을 구현하기 어렵습니다.

Lakeflow Jobs는 태스크 의존성 그래프, 실행 이력, 재시도, 알림을 한 곳에서 관리합니다.

## 어떻게 동작하는가

### 태스크 유형

문서의 태스크 유형 목록은 다음과 같습니다. 이름은 문서 표기 그대로입니다.

| 태스크 유형 | 비고 (문서 표기) |
|---|---|
| Notebook | Visual data prep 포함 |
| Lakeflow Integrations | **Beta** |
| Clean Room notebook | |
| Python script | |
| Python wheel | |
| SQL | |
| Pipeline | Database Table Sync pipeline, Ingestion pipeline 포함 |
| SQL Alert | **Public Preview** |
| Dashboards | |
| Power BI | |
| dbt | |
| dbt platform | **Public Preview** |
| JAR | 서버리스에서 GA (2026-08-06 릴리즈 노트) |
| Spark Submit | |
| Run Job | 다른 잡을 태스크로 실행 |
| Genie Code | GA (2026-10-21 릴리즈 노트). 상세는 아래 참고 |
| If/else | 조건 분기 태스크. [파라미터 페이지](jobs-parameters-and-control-flow.md) 참고 |
| For each | 반복 태스크. [파라미터 페이지](jobs-parameters-and-control-flow.md) 참고 |

> **참고** Genie Code 태스크는 [Lakeflow Jobs의 Genie Code 태스크](../11-developer-tools/genie-code/lakeflow-jobs-task.md) 페이지에서 자세히 다룹니다. 이 장에서는 설명을 반복하지 않습니다. 릴리즈 노트 기준 Genie Code 태스크는 2026-08-27에 Beta로 발표됐고 2026-10-21에 GA로 발표됐습니다.

### 트리거 종류

| 트리거 (문서 표기) | 동작 | 상태 |
|---|---|---|
| None (manual) | **Run now** 버튼 또는 외부 오케스트레이션 도구에서 프로그램 방식으로 실행 | 문서에 상태 라벨 없음 |
| Scheduled | 시간 기반 스케줄로 실행 | 문서에 상태 라벨 없음 |
| File arrival | 감시 중인 Unity Catalog 스토리지 위치에 새 파일이 도착하면 실행 | 문서에 상태 라벨 없음 |
| Table update | 원천 테이블이 업데이트되면 실행 | 문서에 상태 라벨 없음. 릴리즈 노트: OpenSharing 객체와 시스템 테이블 지원은 2026-09-30 GA |
| Model update | Unity Catalog 모델 생성, 모델 버전 준비, 모델 별칭 설정 시 실행 | **Beta** |
| Continuous | 실행이 끝나면(성공 또는 실패) 다음 실행을 바로 시작해 항상 실행 상태 유지 | 문서에 상태 라벨 없음 |

문서는 **여러 트리거(Multiple triggers)** 기능을 **Beta** 로 표기합니다. 릴리즈 노트는 2026-10-05에 "Use multiple triggers for Lakeflow Jobs (Beta)"를 발표했습니다. 잡 하나에 최대 5개 트리거를 두고 각각 독립적으로 일시 정지할 수 있습니다.

### 트리거 제한

문서에 명시된 제한입니다.

- 여러 트리거 Beta 기간 동안 잡 하나당 최대 **5개** 트리거.
- Continuous 트리거는 다른 트리거와 **함께 쓸 수 없습니다**.
- 워크스페이스 전체에서 활성 트리거는 모든 잡과 트리거 종류를 합쳐 최대 **12,000개**. 일시 정지된 트리거는 이 한도에 포함되지 않습니다.
- 기본적으로 잡 하나의 실행은 한 번에 하나만 활성화됩니다. 최대 동시 실행(max concurrency)을 넘는 실행은 건너뜁니다.

## 어떻게 쓰는가

### 스케줄 (Scheduled) 설정

UI 경로는 다음과 같습니다. 워크스페이스 사이드바에서 **Jobs & Pipelines** 를 열고 잡을 선택한 뒤 **Job details** 패널에서 **Add trigger** 를 누릅니다.

1. **Trigger type** 을 **Scheduled** 로 선택합니다.
2. **Schedule type** 을 고릅니다.
   - **Simple**: 간격과 시간 단위를 지정합니다. 첫 실행 시각은 지정할 수 없고, 스케줄러가 선택합니다.
   - **Advanced**: 주기, 시작 시각, 시간대를 지정합니다. **Show Cron Syntax** 를 켜면 Quartz cron 문법으로 편집할 수 있습니다.
3. **Save** 를 누릅니다.

> **참고** 문서는 Quartz cron 문법 설명 페이지로 연결하지만, 이 페이지에서는 cron 식 예시를 확인하지 못했습니다. 식을 직접 쓸 때는 Quartz 문법 설명을 함께 확인하십시오.

### 스케줄 동작 규칙

- **시간대**: 일광 절약 시간(DST)을 적용하는 시간대나 UTC를 고를 수 있습니다. DST가 시작·종료될 때 시간 단위 잡은 건너뛰거나 한두 시간 지연되어 보일 수 있습니다. 절대 시각 기준으로 시간마다 돌리려면 UTC를 고르라고 문서가 권장합니다.
- **최소 간격**: 스케줄 실행 사이에는 cron 식과 관계없이 최소 **10초** 간격이 강제됩니다.
- **지연**: 스케줄러는 저지연 잡용이 아닙니다. 실행이 몇 분 지연될 수 있으며, 서비스가 가능해지면 밀린 스케줄이 즉시 실행됩니다.

### 파일 도착 (File arrival) 설정

파일 도착 트리거의 요구 사항과 옵션입니다.

- **전제 조건**: 워크스페이스에서 Unity Catalog가 켜져 있어야 하며, 감시 위치는 Unity Catalog 볼륨 또는 외부 위치여야 합니다. 잡 권한으로 CAN MANAGE, 스토리지 위치에 READ 권한이 필요합니다.
- **파일 이벤트**: 외부 위치의 파일 이벤트 사용을 권장합니다. 설정하려면 외부 위치 소유자이거나 `MANAGE` 권한이 필요합니다. 볼륨은 기본으로 파일 이벤트를 지원한다고 문서가 설명합니다.
- **Storage location (URL)**: 감시할 외부 위치나 볼륨의 루트 또는 하위 경로. 하위 디렉터리까지 재귀적으로 확인합니다.
- **Minimum time between triggers in seconds**: 실행 사이의 최소 간격(쿨다운).
- **Wait after last change in seconds**: 마지막 파일 도착 후 조용한 기간을 기다린 뒤 실행. 새 도착마다 타이머가 초기화되므로 배치로 들어오는 파일에 유용합니다.
- **Test connection**: 저장 전에 설정을 검증합니다.

파일 도착 트리거의 제한입니다.

- 새 파일만 트리거합니다. 같은 이름으로 덮어쓴 파일은 트리거하지 않습니다.
- 경로에 외부 테이블, 카탈로그나 스키마의 관리형 위치, 와일드카드(`*`, `?`)는 포함할 수 없습니다.
- 파일 이벤트를 켠 경우 파일 수 제한은 없지만, 불필요한 파일 업데이트가 많으면 트리거가 시간 초과될 수 있습니다. 메타데이터가 보존 기간을 넘어선 수정 파일은 새 도착으로 취급됩니다.
- 파일 이벤트를 쓰지 않으면 해당 위치를 쓰는 잡은 워크스페이스당 최대 50개, 경로의 파일은 최대 10,000개입니다.
- 존재하지 않거나 삭제된 S3, GCS 경로에 대해서는 오류가 나지 않고, 파일이 나타날 때까지 실행되지 않습니다.

잡 파라미터나 상태 라벨은 이 페이지에서 확인하지 못했습니다. 문서는 트리거 평가 실패를 알기 위해 잡 실패 알림을 설정하라고 권장합니다.

파일 도착 트리거로 실행된 잡이 파일을 읽는 방법으로는 문서가 같은 URL을 쓰는 Auto Loader 코드를 보여 줍니다. 자세한 내용은 [Auto Loader](auto-loader.md)를 참고하십시오.

### 테이블 업데이트 (Table update)

원천 테이블이 업데이트되면 실행됩니다. 트리거가 실행될 때 `{{job.trigger.table_update.updated_tables}}` 참조로 바뀐 테이블 목록을 받을 수 있습니다. 실행 조건과 참조는 [파라미터 페이지](jobs-parameters-and-control-flow.md)의 동적 값 참조 표를 참고하십시오.

## 트레이드오프

| 상황 | 권장 트리거 |
|---|---|
| 매일·매시 정해진 시각에 배치 | Scheduled |
| 클라우드 스토리지에 파일이 쌓일 때마다 처리 | File arrival (또는 Auto Loader 파이프라인) |
| 원천 테이블 변경에 맞춰 후속 처리 | Table update |
| 항상 실행 상태가 필요하고 실행이 끝나면 바로 재시작 | Continuous (다른 트리거와 함께 쓸 수 없음) |
| 밀리초 단위 응답 | Lakeflow Jobs 스케줄러는 부적합. 실시간 스트리밍을 검토 |

## 주의사항

- **파일 덮어쓰기**: 같은 이름으로 덮어쓴 파일은 파일 도착 트리거를 발생시키지 않습니다. 새 파일 이름 규칙을 쓰거나, 처리 방식을 맞추십시오.
- **스케줄 지연**: 정확한 초 단위 시작이 필요하면 스케줄러를 쓰지 마십시오.
- **동시 실행**: 기본 설정에서 실행이 겹치면 새 실행은 건너뜁니다. 겹침을 허용하려면 최대 동시 실행 값을 바꿔야 하며, 그 전에 태스크가 동시 실행을 견딜 수 있는지 확인하십시오.
- **Continuous와 재시도**: Continuous 잡은 재시도가 지수 백오프로 자동 적용된다고 문서가 설명합니다. 자세한 내용은 [재시도·알림·Repair run](jobs-retries-notifications-repair.md) 참고.
- **트리거 한도**: 활성 트리거 12,000개 한도는 워크스페이스 전체 기준입니다. 많은 잡을 같은 방식으로 만들면 한도에 가까워질 수 있습니다.

## 참고 문서

- [Lakeflow Jobs (overview)](https://docs.databricks.com/aws/en/jobs/)
- [Configure tasks (task types, retries, timeouts)](https://docs.databricks.com/aws/en/jobs/configure-task)
- [Trigger types](https://docs.databricks.com/aws/en/jobs/triggers)
- [Scheduled trigger](https://docs.databricks.com/aws/en/jobs/scheduled)
- [File arrival triggers](https://docs.databricks.com/aws/en/jobs/file-arrival-triggers)
- [Table update triggers](https://docs.databricks.com/aws/en/jobs/trigger-table-update)
- [Genie Code 태스크 (이 저장소)](../11-developer-tools/genie-code/lakeflow-jobs-task.md)
- [Release notes, 2026년 9월](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [Release notes, 2026년 10월](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
