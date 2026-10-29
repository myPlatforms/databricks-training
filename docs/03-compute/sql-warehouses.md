# SQL 웨어하우스

> 기준일: 2026-10-28 · 근거: 공식 문서

SQL 웨어하우스(SQL warehouse)는 SQL 쿼리, 대시보드, BI 도구 연결을 위해 쓰는 컴퓨트입니다. 유형은 서버리스(Serverless), Pro, Classic 세 가지이고, 크기(T-shirt size)와 클러스터 수 범위를 정해 씁니다. 이 페이지는 세 유형의 차이, 크기와 클러스터 개념, 자동 확장과 자동 중지, 큐 동작, 설정 방법을 다룹니다. 서버리스 노트북과 Job의 컴퓨트는 [서버리스 컴퓨트](serverless-compute.md) 페이지에서 다룹니다.

## 1. 왜 필요한가

SQL 쿼리는 노트북 Job과 다른 패턴을 가집니다. 많은 사용자가 짧은 쿼리를 동시에 던지고, 대시보드는 주기적으로 같은 쿼리를 다시 실행하며, BI 도구는 연결을 오래 유지합니다. 이 패턴에서 필요한 것은 다음과 같습니다.

| 요구 | SQL 웨어하우스의 대응 |
|---|---|
| 빠른 시작 | 서버리스 유형은 시작이 빠릅니다 (문서: 2~6초) |
| 동시 쿼리 처리 | 클러스터 수를 자동으로 늘리거나 줄입니다 |
| 유휴 비용 억제 | 일정 시간 쓰지 않으면 자동 중지합니다 |
| BI 도구 연결 | JDBC·ODBC와 Power BI, Tableau 등 연결을 지원합니다 |

## 2. 어떻게 동작하는가

### 2.1 세 가지 유형

| 유형 | 문서 설명 (원문 인용 요약) | 성능 기능 | 실행 위치 | 시작 시간 (문서) |
|---|---|---|---|---|
| Serverless | "a serverless SQL warehouse supports all of the performance features of Databricks SQL" | Photon, Predictive IO, Intelligent Workload Management | Databricks 계정 | 2~6초 |
| Pro | "supports Photon and Predictive IO, but does not support Intelligent Workload Management" | Photon, Predictive IO | 고객 AWS 계정 | 약 4분 |
| Classic | "supports Photon but does not support Predictive IO or Intelligent Workload Management" | Photon | 고객 AWS 계정 | 약 4분 |

> **참고** Serverless 행의 "Databricks 계정"과 Pro·Classic 행의 "고객 AWS 계정"은 문서가 설명한 컴퓨트 레이어 위치입니다. 청구 구조에 대한 설명은 [비용 구조 비교](cost-structure.md) 페이지에서 다룹니다.

문서 표에서 Classic 행의 Predictive IO 칸에는 렌더링 오류가 있어 본문 설명을 기준으로 적었습니다.

서버리스 유형은 같은 크기 이름을 쓰지만 노드 수를 문서에 명시하지 않습니다. 문서는 서버리스 크기가 일부 경우 Pro·Classic과 다른 인스턴스 유형을 쓸 수 있다고 설명합니다.

#### Lakehouse Real-Time (Beta)

문서는 Lakehouse Real-Time(Lakehouse//RT)을 저지연·고동시성 워크로드용 서버리스 웨어하우스 유형으로 소개하며 상태는 **Beta** 입니다. 지원하는 쿼리는 `SELECT`뿐입니다. 운영 쿼리에 쓰기 전에 Beta 상태를 확인하십시오.

### 2.2 크기 (Cluster size)

문서가 정의한 크기 값은 다음 10단계입니다.

`2X-Small`, `X-Small`, `Small`, `Medium`, `Large`, `X-Large`, `2X-Large`, `3X-Large`, `4X-Large`, `5X-Large`

5X-Large는 Pro와 서버리스에서 Public Preview입니다.

Pro와 Classic의 크기별 구성은 문서 표 기준으로 다음과 같습니다. 모든 워커는 `i3.2xlarge` 인스턴스를 씁니다.

| 크기 | 드라이버 인스턴스 | 워커 수 |
|---|---|---|
| 2X-Small | i3.2xlarge | 1 |
| X-Small | i3.2xlarge | 2 |
| Small | i3.4xlarge | 4 |
| Medium | i3.8xlarge | 8 |
| Large | i3.8xlarge | 16 |
| X-Large | i3.16xlarge | 32 |
| 2X-Large | i3.16xlarge | 64 |
| 3X-Large | i3.16xlarge | 128 |
| 4X-Large | i3.16xlarge | 256 |
| 5X-Large | i3.16xlarge | 512 |

> **참고** 이 표의 값은 Pro와 Classic 크기에 대한 문서 표입니다. 크기가 커질수록 워커 수가 두 배로 늘어납니다. 서버리스의 노드 수는 문서에 명시되지 않았습니다.

### 2.3 클러스터 수와 자동 확장

Pro와 Classic 웨어하우스는 생성 시 최소와 최대 클러스터 수를 정합니다. 문서는 클러스터 한 개당 동시 쿼리 10개 정도를 처리한다고 설명합니다. 동시 쿼리가 많아지면 클러스터를 더 씁니다.

| 동작 | Pro·Classic 문서 설명 |
|---|---|
| 확장 (부하 추정) | 예상 부하 2~6분이면 1개 추가, 6~12분이면 2개, 12~22분이면 3개, 22분 이상이면 3개에 15분마다 1개씩 더 추가 |
| 확장 (큐 대기) | 쿼리가 큐에서 5분 대기하면 확장 |
| 축소 | 15분 연속으로 부하가 낮으면, 그 구간의 최고 부하에 맞는 최소 수로 축소 |

서버리스는 클러스터 확장과 축소를 자동으로 처리합니다. 문서는 피크 부하를 견딜 수 있도록 최대 클러스터 수를 충분히 설정하라고 권장합니다.

API에서 확인한 클러스터 수 관련 필드는 다음과 같습니다.

| 필드 | 타입 | 문서 설명 |
|---|---|---|
| `min_num_clusters` | int32 | 항상 실행 상태로 유지할 최소 클러스터 수. 기본값 1 |
| `max_num_clusters` | int32 | 오토스케일러가 만들 수 있는 최대 클러스터 수. 40 이하이고 `min_num_clusters` 이상이어야 함 |

### 2.4 자동 중지 (Auto stop)

| 필드 | 문서 설명 |
|---|---|
| `auto_stop_mins` | 유휴 상태가 이 분 수를 넘으면 자동 중지. 기본값 120. 0이면 비활성화, 아니면 10 이상 |

웨어하우스가 중지된 상태여도 다음 경우에는 자동으로 다시 시작합니다. 쿼리 실행, 예약 Job 할당, JDBC·ODBC 연결, 대시보드 열기(대시보드 수준 웨어하우스인 경우)입니다.

### 2.5 큐와 대기

문서 기준으로 모든 웨어하우스 유형의 최대 큐 깊이는 1,000개 쿼리입니다. 서버리스에서 사용 가능한 용량이 없으면 쿼리가 큐에서 기다리고, 대기 시간이 늘면 오토스케일러가 클러스터를 추가합니다.

모니터링 페이지의 **Peak Queued Queries** 지표는 큐 압력을 보여 줍니다. 값이 지속적으로 0보다 크면 크기를 키우거나 최대 클러스터 수를 늘리는 것을 검토하십시오.

### 2.6 가용성 영역과 재시도

Pro와 Classic의 가용성 영역(Availability zone)은 `auto`로 설정되며, AWS가 용량 부족 오류를 내면 다른 가용성 영역에서 재시도합니다.

## 3. 어떻게 쓰는가

### 3.1 UI로 만들기

SQL 웨어하우스는 워크스페이스의 SQL Warehouses 화면에서 만듭니다. 이름, 크기, 유형, 최소와 최대 클러스터 수, 자동 중지 시간을 정합니다. 문서는 생성 절차를 별도 페이지(Create a SQL warehouse)에서 안내합니다.

### 3.2 API로 만들기

REST API는 `POST /api/2.0/sql/warehouses`입니다. 주요 요청 필드는 다음과 같습니다.

| 필드 | 설명 |
|---|---|
| `name` | 웨어하우스 이름. 조직 내 고유해야 하며 100자 미만 |
| `cluster_size` | 위 10단계 중 하나 |
| `warehouse_type` | `CLASSIC` 또는 `PRO`. 서버리스는 `PRO`에 `enable_serverless_compute`를 `true`로 설정 |
| `enable_serverless_compute` | 서버리스 컴퓨트 사용 여부 |
| `min_num_clusters`, `max_num_clusters` | 클러스터 수 범위 |
| `auto_stop_mins` | 자동 중지 시간(분) |
| `enable_photon` | Photon 사용 여부. 기본값 true |
| `spot_instance_policy` | 스팟 인스턴스 정책. 기본값 `COST_OPTIMIZED` |

```bash
# 서버리스 SQL 웨어하우스 생성 예시 (REST 요청 본문)
# 워크스페이스 URL과 토큰은 환경 변수나 CLI 프로필로 설정하십시오.
curl -X POST "https://<WORKSPACE_HOST>/api/2.0/sql/warehouses" \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bi-serverless-example",
    "cluster_size": "Small",
    "warehouse_type": "PRO",
    "enable_serverless_compute": true,
    "min_num_clusters": 1,
    "max_num_clusters": 3,
    "auto_stop_mins": 10
  }'
```

> **주의** 예시의 토큰은 환경 변수로만 넘기고, 셸 기록이나 저장소에 남기지 마십시오. 공개 문서에는 실제 호스트와 토큰을 쓰지 않습니다.

조회는 CLI로도 할 수 있습니다.

```bash
# 웨어하우스 목록을 조회합니다. 프로필은 ~/.databrickscfg의 값을 씁니다.
databricks warehouses list --profile <PROFILE_NAME>
```

### 3.3 쿼리에서 웨어하우스 고르기

노트북은 SQL 웨어하우스를 컴퓨트로 연결할 수 있습니다. 문서는 노트북에 Pro나 서버리스 SQL 웨어하우스를 붙일 수 있다고 설명합니다. Python 커넥터, Databricks SQL CLI, JDBC·ODBC 도구 같은 외부 도구에서도 웨어하우스를 지정해 쿼리를 보낼 수 있습니다. 각 도구의 연결 방법은 [Python SQL 커넥터](https://docs.databricks.com/aws/en/dev-tools/python-sql-connector) 등 도구별 문서를 따르십시오.

## 4. 트레이드오프

| 기준 | Serverless | Pro | Classic |
|---|---|---|---|
| 시작 시간 | 2~6초 | 약 4분 | 약 4분 |
| 성능 기능 | 전체 | Predictive IO 포함 | Photon만 |
| 관리 부담 | 가장 낮음 | 중간 | 중간 |
| 실행 위치 | Databricks 계정 | 고객 AWS 계정 | 고객 AWS 계정 |
| 권장 | 문서가 가능하면 서버리스를 권장 | 서버리스 불가 조건일 때 | 기능 요구가 가장 낮을 때 |

> **참고** 문서는 Databricks가 서버리스 SQL 웨어하우스를 사용할 수 있으면 권장한다고 설명합니다. 서버리스 가용성은 리전과 워크스페이스 설정에 따라 다르므로 [기능 리전 지원](https://docs.databricks.com/aws/en/resources/feature-region-support) 페이지를 확인하십시오.

## 5. 주의사항

- **최대 클러스터 수를 고려하십시오.** 최대값이 너무 낮으면 피크 시간에 큐가 길어집니다. 큐 지표를 보고 조정합니다.
- **자동 중지를 설정하십시오.** 기본값은 120분입니다. 짧은 대화형 조회 워크로드는 더 짧게 잡는 것이 비용에 유리합니다.
- **Pro와 Classic은 인스턴스 요금이 별도로 청구됩니다.** 웨어하우스가 실행 중이면 DBU 외에 인스턴스 요금이 나갑니다. 비용 구조는 [비용 구조 비교](cost-structure.md)에서 다룹니다.
- **Predictive IO와 Intelligent Workload Management를 구분하십시오.** Pro는 Predictive IO를 지원하지만 Intelligent Workload Management는 지원하지 않습니다. Classic은 Photon만 지원합니다.
- **Beta 기능은 Previews에서 켜야 하는 경우가 있습니다.** 문서가 명시한 웨어하우스 수준 문장 시간 제한(statement timeout)은 Beta이며 Previews 페이지에서 켜야 합니다.

## 참고 문서

- [SQL warehouses 개요 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/)
- [SQL warehouse 유형 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)
- [SQL warehouse 크기, 확장, 큐 동작 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-behavior)
- [SQL warehouse 생성 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/create)
- [웨어하우스 REST API 레퍼런스 (생성)](https://docs.databricks.com/api/workspace/warehouses/create)
- [2026년 9월 릴리즈 노트 — Query tags for SQL warehouses GA (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
