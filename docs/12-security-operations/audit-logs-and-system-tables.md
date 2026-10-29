# 감사 로그와 시스템 테이블

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Databricks는 플랫폼 활동 기록을 두 경로로 제공합니다. 하나는 **시스템 테이블**(System tables)로, `system` 카탈로그 아래의 Delta 테이블을 SQL로 조회합니다. 다른 하나는 **계정 수준 감사 로그 전달**(Audit log delivery)로, 감사 로그 JSON 파일을 S3 버킷으로 내보냅니다. 문서는 가능하면 시스템 테이블을 쓰라고 권장합니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 워크스페이스마다 로그 파일을 따로 모으면 "누가 무엇을 했는가"를 계정 전체에서 답하기 어렵습니다.
- 로그를 외부로 내보내면 보존과 조회 권한을 따로 관리해야 합니다.
- 비용, 계보, 쿼리 기록이 각각 다른 도구에 있으면 한 번의 조사에 여러 화면을 오가야 합니다.

시스템 테이블은 같은 계정의 기록을 SQL로 한데 모아 조회하게 합니다. Unity Catalog 권한 모델을 그대로 따르므로 접근 통제도 한 곳에서 관리합니다.

## 2. 어떻게 동작하는가

### 활성화 조건

| 항목 | 문서 기준 |
|---|---|
| 워크스페이스 | Unity Catalog가 활성화되어 있어야 함 |
| 메타스토어 | 권한 모델 버전(Privilege Model Version) 1.0이어야 함 |
| 조회 권한 | `system` 카탈로그에 `USE CATALOG`, 각 시스템 스키마에 `USE SCHEMA`와 `SELECT` 필요 |
| 기본 접근 | 계정 관리자와 메타스토어 관리자는 기본으로 접근 가능 |

권한을 다른 사용자에게 주는 GRANT 예시는 문서에 없습니다. 권한 구문은 [권한 모델과 소유권](../06-unity-catalog/privileges-and-ownership.md)을 따르십시오.

```sql
-- 감사 담당 그룹이 billing과 access 스키마를 조회할 수 있게 합니다.
GRANT USE CATALOG ON CATALOG system TO `audit-team`;
GRANT USE SCHEMA ON SCHEMA system.access TO `audit-team`;
GRANT SELECT ON SCHEMA system.access TO `audit-team`;
```

> **주의** 감사 로그에는 요청 파라미터가 들어 있습니다. 문서는 SQL 정의를 담은 일부 키를 계정 관리자 또는 `databricks_pii_access` 그룹 구성원에게만 보이게 한다고 설명합니다. 감사 팀 그룹에 `SELECT`를 주기 전에 이 점을 검토하십시오.

### 시스템 스키마와 테이블

아래 표는 문서의 시스템 테이블 목록을 요약한 것입니다. 상태 라벨이 없는 항목은 문서 본문에 라벨이 표기되지 않은 것입니다. 보존 기간은 문서 표의 "무료 보존" 값입니다.

| 스키마 | 테이블 | 상태 (문서 기준) | 보존 기간 |
|---|---|---|---|
| `access` | `audit`, `clean_room_events`, `assistant_events`, `inbound_network`, `outbound_network`, `workspaces_latest` | 모두 Public Preview | `audit`, `clean_room_events`, `assistant_events`, `outbound_network`: 365일. `inbound_network`: 30일. `workspaces_latest`: 무기한 |
| `access` | `column_lineage`, `table_lineage` | 라벨 없음 | 365일 (계보 페이지는 롤링 1년) |
| `billing` | `usage`, `list_prices` | 라벨 없음 | `usage`: 365일. `list_prices`: 무기한 |
| `compute` | `clusters`, `instance_events`, `instance_pools`, `node_timeline`, `node_types`, `warehouse_events`, `warehouses` | `instance_events`, `instance_pools`: Public Preview | 대부분 365일. `node_timeline`: 90일. `node_types`: 무기한 |
| `query` | `history` | 라벨 없음 | 365일 |
| `lakeflow` | `job_run_timeline`, `job_task_run_timeline`, `job_tasks`, `jobs`, `pipeline_update_timeline`, `pipelines`, `zerobus_stream`, `zerobus_ingest` | `zerobus_stream`, `zerobus_ingest`: Beta. 나머지는 라벨 없음 | 365일 |
| `lakeflow_pipeline_events_preview` | `pipeline_events` | Beta | 365일 |
| `alert` | `alerts`, `alert_evaluation_history` | Public Preview | 365일 |
| `lakebase` | `*` | Beta | 7일 |
| `serving` | `served_entities`, `endpoint_usage` | Public Preview | `served_entities`: 365일. `endpoint_usage`: 90일 |
| `ai_gateway` | `usage`, `external_model_spend` | `usage`: Public Preview. `external_model_spend`: Beta | 365일 |
| `data_classification` | `results` | Public Preview | 13개월 |
| `data_quality_monitoring` | `table_results` | Public Preview | 13개월 |
| `tags` | `governed_tags` | Beta | 365일 |
| `sharing` | `materialization_history` | 라벨 없음 | 365일 |
| `replication` | `states` | 라벨 없음 | 365일 |
| `storage` | `table_auto_upgrade_operations_history`, `predictive_optimization_operations_history` | Public Preview | 180일 |
| `mlflow` | `experiments_latest`, `runs_latest`, `run_metrics_history` | Public Preview | 180일 |
| `marketplace` | `listing_funnel_events`, `listing_access_events` | Public Preview | 365일 |
| `lineage` | (지원 중단) | 라벨 없음 | 빈 테이블 |

> **참고** `access.audit`의 상태 표기는 페이지마다 다릅니다. 시스템 테이블 목록 페이지는 Public Preview로, 감사 로그 페이지는 "Public Preview"로 표기합니다. 같은 상태이므로 충돌은 아니지만, 최신 상태는 원문에서 다시 확인하십시오.

> **참고** 릴리즈 노트에 따르면 2026년 10월 21일부터 `lakeflow`의 `pipelines`와 `pipeline_update_timeline` 테이블이 GA입니다. 위 표는 시스템 테이블 목록 페이지의 라벨을 옮긴 것이므로, GA 표기는 릴리즈 노트 기준으로 따로 확인하십시오.

> **참고** `system.information_schema`는 다른 시스템 테이블과 동작 방식이 달라 별도 페이지에서 다룹니다.

### 감사 로그 시스템 테이블 (`system.access.audit`)

감사 로그 시스템 테이블은 워크스페이스와 계정의 이벤트를 기록합니다. 주요 컬럼은 다음과 같습니다.

| 컬럼 | 의미 (문서 기준) |
|---|---|
| `event_time` | 이벤트 시각(UTC) |
| `event_date` | 이벤트 날짜. 문서는 성능을 위해 `event_time`보다 `event_date`로 필터링하라고 권장 |
| `workspace_id` | 워크스페이스 ID. 계정 수준 이벤트는 `0` |
| `service_name` | 요청을 시작한 서비스 (예: `unityCatalog`) |
| `action_name` | 이벤트 종류 |
| `user_identity` | 시작한 사용자의 `email`과 `subject_name` 구조체 |
| `request_params` | 요청 파라미터 맵. 요청 종류마다 다름 |
| `response` | `statusCode`, `errorMessage`, `result` 구조체 |
| `identity_metadata` | `run_by`(시작한 주체)와 `run_as`(권한 판단에 쓰인 주체) |

문서는 워크스페이스가 삭제되면 그 워크스페이스의 14일 넘은 감사 이벤트를 `system.access.audit`에서 제거한다고 설명합니다. 일반 보존 기간은 시스템 테이블 목록에서는 365일로 표기되지만, 감사 로그 페이지에서는 일반 보존 기간을 명시하지 않았습니다. 규제 기준에 맞추려면 보존 기간을 원문과 실제 테이블에서 함께 확인하십시오.

## 3. 어떻게 쓰는가

### 최근 이벤트를 종류별로 집계하기

감사 로그의 액션 종류는 이 장에서 나열하지 않습니다. 먼저 집계해서 본인 환경에서 기록되는 값을 확인하십시오.

```sql
SELECT service_name, action_name, COUNT(*) AS event_count
FROM system.access.audit
WHERE event_date >= current_date() - INTERVAL 7 DAYS
GROUP BY service_name, action_name
ORDER BY event_count DESC;
```

### 특정 사용자의 활동 추적하기

```sql
SELECT event_time, workspace_id, service_name, action_name,
       user_identity.email AS actor_email
FROM system.access.audit
WHERE event_date >= current_date() - INTERVAL 30 DAYS
  AND user_identity.email = 'user@example.com'
ORDER BY event_time DESC
LIMIT 200;
```

### 계보 조회

테이블 계보는 `system.access.table_lineage`에 기록됩니다. 이 테이블은 읽기와 쓰기 이벤트를 모두 기록하며, `source_type`만 있고 `target_type`이 없으면 읽기, 그 반대면 쓰기입니다.

```sql
SELECT source_table_full_name, target_table_full_name, created_by, event_time
FROM system.access.table_lineage
WHERE event_date >= current_date() - INTERVAL 7 DAYS
ORDER BY event_time DESC
LIMIT 100;
```

계보는 롤링 1년 기간만 보존합니다. 1년이 넘은 계보는 카탈로그 탐색기나 계보 API에서 조회합니다. 문서는 2024년 9월 1일 이후 캡처된 계보에 대해 이 방법을 안내합니다. 계보 기능의 개념은 [계보와 데이터 분류](../06-unity-catalog/lineage-and-classification.md)에서 다룹니다.

### 계정 수준 감사 로그 전달 (S3)

계정 수준 감사 로그 전달은 감사 로그를 JSON 파일로 S3 버킷에 씁니다. 설정 순서는 문서 기준으로 다음과 같습니다.

1. S3 버킷을 만들고, Databricks API로 스토리지 구성(storage configuration) 객체를 만듭니다.
2. AWS IAM 역할을 만들고, 그 역할의 ARN으로 자격증명 구성(credentials configuration) 객체를 만듭니다.
3. 역할의 AWS 계정과 다른 계정에 전달하려면 교차 계정 IAM 역할을 참조하는 S3 버킷 정책을 추가합니다.
4. 로그 전달 API로 스토리지와 자격증명 객체를 사용하는 전달 구성을 만듭니다.

계정 전체 구성에서는 계정 수준 이벤트가 `workspaceId=0` 파티션에 저장됩니다. 계정 수준 이벤트를 받으려면 모든 워크스페이스가 공유하는 한 구성(버킷과 IAM 역할)이 필요하며, 이 구성이 기본값입니다. 로그 타입별로 활성 계정 수준 구성은 최대 두 개입니다.

파일 경로는 `<bucket-name>/<delivery-path-prefix>/workspaceId=<workspaceId>/date=<yyyy-mm-dd>/auditlogs_<internal-id>.json` 형식입니다. 전달 상태는 API 응답의 `log_delivery_status`에서 확인합니다. 최초 전달은 최대 1시간 걸릴 수 있습니다.

> **주의** 전달 페이지에는 "JSON 형식"과 "사람이 읽을 수 있는 형식"이라는 두 표현이 함께 나옵니다. 파일 경로 패턴은 `.json`입니다. 실제 파싱 전에 샘플 파일을 열어 형식을 확인하십시오.

## 4. 트레이드오프

| 방식 | 장점 | 제약 |
|---|---|---|
| 시스템 테이블 | SQL로 바로 조회, Unity Catalog 권한으로 통제 | 일부 테이블은 Preview·Beta이고 보존 기간이 테이블마다 다름 |
| 계정 수준 S3 전달 | 외부 SIEM이나 장기 보관 저장소로 보낼 수 있음 | S3 버킷, IAM 역할, 교차 계정 정책을 직접 관리해야 함 |
| 둘 다 사용 | 조회는 시스템 테이블, 장기 보관은 S3 | 두 경로의 누락을 따로 점검해야 함 |

문서는 감사 데이터를 플랫폼 밖으로 옮기는 것을 강하게 권장하지 않는다고 설명합니다. 외부 보관이 필요하면 전달 기능을 쓰되, 시스템 테이블을 기본 조회 경로로 두는 것이 권장됩니다.

## 5. 주의사항

- **보존 기간을 기준으로 계획하십시오.** 시스템 테이블의 무료 보존 기간이 짧은 테이블(예: `node_timeline` 90일, Lakebase 7일)은 필요한 기간보다 먼저 사라질 수 있습니다. 필요한 기간이 365일보다 길다면 주기적으로 복사하거나 계정 수준 S3 전달을 설정하십시오.
- **보존 기간 확장은 Beta입니다.** 계정 관리자가 계정 수준 Previews 페이지에서 "System Tables Configurable Retention"을 켜면 지원 스키마의 무료 보존 기간이 395일로 늘어난다고 문서가 설명합니다. 적용에 최대 24시간이 걸리며, `data_classification`, `data_quality_monitoring`, `lakebase`에는 적용되지 않습니다.
- **`event_date`로 필터링하십시오.** `event_time`만 쓰면 조회가 느려질 수 있다고 문서가 권장합니다.
- **비공개 프리뷰 테이블은 기본으로 비어 있습니다.** 문서는 다른 테이블이 계정에 보일 수 있으며 비어 있고, 쓰려면 Databricks 계정팀에 문의하라고 설명합니다.
- **비용 테이블은 몇 시간 늦게 갱신됩니다.** `system.billing.usage`는 몇 시간마다 갱신되므로 알림 메일이나 상세 페이지와 수치가 다를 수 있습니다. 비용 페이지에서 자세히 다룹니다.
- **인바운드·아웃바운드 네트워크 테이블은 정책 점검에 씁니다.** 각각 `inbound_network`(30일)와 `outbound_network`(365일)입니다. 자세한 쿼리는 [인바운드 네트워크 접근](network-inbound-access.md)과 [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md)를 참고하십시오.

## 참고 문서

- [System tables](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Audit log system table](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)
- [Lineage system tables](https://docs.databricks.com/aws/en/admin/system-tables/lineage)
- [Audit logs](https://docs.databricks.com/aws/en/admin/account-settings/audit-logs)
- [Account-level audit log delivery](https://docs.databricks.com/aws/en/admin/account-settings/audit-log-delivery)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
