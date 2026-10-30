# 실습: Lakebase 프로젝트, 브랜치, 동기화 테이블

> 기준일: 2026-10-30 · 근거: 공식 문서 · 수준: 200

이 실습은 Lakebase Postgres 프로젝트 하나를 처음부터 만들고, Postgres에서 데이터를 다루고, 브랜치를 나눠 쓰고, Unity Catalog Delta 테이블을 동기화 테이블(Synced Table)로 옮겨 조회한 뒤 모든 리소스를 삭제합니다. 앞선 장에서 익힌 개념을 실제 리소스로 확인하는 것이 목표입니다.

## 목표

이 실습을 마치면 다음을 할 수 있습니다.

- 가장 작은 컴퓨트와 스케일 투 제로 설정으로 Lakebase Postgres 프로젝트를 만듭니다.
- OAuth 토큰을 Postgres 비밀번호로 써서 psycopg로 접속하고, 기본 SQL을 실행합니다.
- 자식 브랜치에서 데이터를 바꿔도 기본 브랜치(`production`)에는 영향이 없음을 확인합니다.
- Snapshot 모드 동기화 테이블을 만들고 Postgres에서 조회합니다.
- 동기화 테이블, 브랜치, 프로젝트를 삭제하고, 삭제 후 Postgres 테이블이 남는지 확인합니다.

## 소요 시간

약 40분입니다. 프로젝트와 브랜치 생성, 동기화 테이블 초기 복사를 기다리는 시간이 대부분입니다. 노트북 실행 자체는 수 분 안에 끝납니다.

## 준비물

| 항목 | 필요한 것 |
|---|---|
| 워크스페이스 | Lakebase Postgres를 쓸 수 있는 워크스페이스 (앱 스위처의 **Lakebase Postgres** → **Autoscaling** 화면에서 프로젝트를 볼 수 있음) |
| 프로젝트 권한 | Lakebase 프로젝트를 만들고 삭제할 수 있는 권한 |
| Unity Catalog 권한 | 대상 카탈로그에 대한 `USE CATALOG`, 스키마 생성(`CREATE SCHEMA`), 테이블 생성(`CREATE TABLE`) 권한 |
| 컴퓨트 | 노트북은 **서버리스 컴퓨트** 에서 실행합니다. 실습 Lakebase 엔드포인트는 0.5 CU 고정입니다 |
| 로컬 도구 | 필요 없습니다. 모든 단계를 노트북에서 실행합니다 |

> **참고** 위 권한은 공식 문서의 일반 요구 사항을 실습 단계에 맞춘 것입니다. 워크스페이스 정책으로 권한이 막혀 있으면 1단계나 4단계에서 실패합니다. 이 경우 워크스페이스 관리자에게 권한을 요청하십시오.

## 비용 주의

- Lakebase 컴퓨트는 활성 상태일 때 과금됩니다. 실습 엔드포인트는 5분(`300s`) 동안 활동이 없으면 자동으로 멈춥니다(스케일 투 제로).
- 동기화 테이블은 Lakeflow 파이프라인으로 실행되므로 파이프라인 컴퓨트를 씁니다. 원본이 작아도 실행 한 번에 비용이 듭니다.
- 브랜치는 1일 뒤 만료되도록 설정합니다. 만료 설정 브랜치는 브랜치에서 바뀐 데이터만 과금된다고 문서가 설명합니다.
- 실습이 끝나면 5단계를 반드시 실행합니다. 단가는 이 페이지에서 다루지 않습니다. [베스트 프랙티스와 비용](best-practices-and-cost.md)을 참고하십시오.

## 노트북 가져오기

실습 노트북은 공개 리포에 있습니다.

- GitHub 경로: [labs/10-lakebase/lakebase-lab.py](https://github.com/myPlatforms/databricks-training/blob/main/labs/10-lakebase/lakebase-lab.py)

워크스페이스로 가져오는 방법은 다음과 같습니다.

1. 워크스페이스 사이드바에서 **Workspace** 를 열고 원하는 폴더로 이동합니다.
2. 폴더 메뉴에서 **Import** 를 선택합니다.
3. GitHub에서 내려받은 `lakebase-lab.py` 파일을 올리거나, 파일 내용을 붙여 넣습니다.
4. 노트북을 열고 컴퓨트를 **서버리스** 로 고릅니다.

노트북 맨 위의 위젯 세 개를 워크스페이스 값으로 바꿉니다.

| 위젯 | 기본값 (자리표시자) | 설명 |
|---|---|---|
| `catalog` | `main` | 원본 Delta 테이블을 만들 Unity Catalog 카탈로그 |
| `schema` | `lakebase_lab` | 원본 테이블과 동기화 테이블 이름을 정할 스키마 |
| `project_id` | `lakebase-lab` | 이 실습이 만들고 마지막에 지울 프로젝트 ID |

> **주의** `project_id` 는 이미 있는 프로젝트 이름으로 바꾸지 마십시오. 5단계는 이 노트북이 만든 프로젝트를 삭제합니다.

## 단계별 설명

아래 코드는 노트북에서 발췌한 것입니다. 기대 결과는 실제 실행으로 확인한 출력입니다.

### 1단계: 프로젝트 생성

가장 작은 컴퓨트(0.5 CU 고정)와 5분 무활동 후 스케일 투 제로를 설정합니다. 문서는 프로젝트를 만들면 `production` 브랜치와 기본 데이터베이스 `databricks_postgres`가 생긴다고 설명합니다.

```python
from databricks.sdk.service.postgres import (
    Duration, Project, ProjectDefaultEndpointSettings, ProjectSpec,
)

project = w.postgres.create_project(
    project=Project(
        spec=ProjectSpec(
            display_name=PROJECT_ID,
            pg_version=17,
            history_retention_duration=Duration(seconds=172800),
            default_endpoint_settings=ProjectDefaultEndpointSettings(
                autoscaling_limit_min_cu=0.5,
                autoscaling_limit_max_cu=0.5,
                suspend_timeout_duration=Duration(seconds=300),
            ),
        )
    ),
    project_id=PROJECT_ID,
).wait()
```

기대 결과:

```text
project: projects/lakebase-lab
default branch: projects/lakebase-lab/branches/production
endpoint state: EndpointStatusState.ACTIVE
```

> **참고** `history_retention_duration` 은 복구 기간(2일에서 35일 사이)입니다. 이 실습은 최소값인 2일(`172800s`)을 씁니다.

### 2단계: OAuth 자격 증명으로 Postgres 접속

Postgres 비밀번호 자리에 OAuth 토큰을 넣습니다. 노트북의 `connect()` 함수는 토큰을 발급받은 뒤 psycopg로 접속합니다. 로그인 시 사용자 이름은 Databricks 사용자 이메일입니다.

```python
def connect(branch: str = PROD):
    ep = w.postgres.get_endpoint(name=endpoint_name(branch))
    token = w.postgres.generate_database_credential(endpoint=ep.name).token
    return psycopg.connect(
        host=ep.status.hosts.host,
        port=5432,
        dbname=DB_NAME,
        user=ME,
        password=token,
        sslmode="require",
        autocommit=True,
    )
```

이어서 실습 테이블 `lab_notes`에 INSERT, SELECT, UPDATE, DELETE를 실행합니다.

```python
cur.execute("INSERT INTO lab_notes (body) VALUES ('첫 메모'), ('둘째 메모'), ('셋째 메모') RETURNING id")
cur.execute("UPDATE lab_notes SET done = TRUE WHERE id = 1")
cur.execute("DELETE FROM lab_notes WHERE id = 3")
```

기대 결과:

```text
INSERT ids: [1, 2, 3]
SELECT: [(1, '첫 메모', False), (2, '둘째 메모', False), (3, '셋째 메모', False)]
UPDATE rows: 1
DELETE rows: 1
SELECT after changes: [(1, '첫 메모', True), (2, '둘째 메모', False)]
```

> **주의** 토큰은 로그인 시점에만 검사되지만 문서는 만료 후 재연결 로직을 권장합니다. 실습 노트북은 연결을 열 때마다 새 토큰을 발급하는 가장 단순한 방식을 씁니다. 자세한 내용은 [연결과 인증](connect-and-auth.md)을 참고하십시오.

### 3단계: 자식 브랜치에서 변경하고 기본 브랜치 확인

`production`의 자식 브랜치 `lab-branch`를 만듭니다. 만료 기간은 1일(`ttl`)입니다. 브랜치는 부모의 데이터를 상속하고, 변경분만 따로 저장합니다.

```python
w.postgres.create_branch(
    parent=PROJECT,
    branch=Branch(spec=BranchSpec(source_branch=PROD, ttl=Duration(seconds=86400))),
    branch_id="lab-branch",
).wait()
```

브랜치에서 INSERT, UPDATE, DELETE를 실행한 뒤 두 브랜치를 각각 조회합니다.

기대 결과:

```text
lab-branch: [(1, '브랜치에서 수정'), (4, '브랜치 전용 메모')]
production (변경 없어야 함): [(1, '첫 메모', True), (2, '둘째 메모', False)]
```

`production`에는 2단계 결과가 그대로 남아 있어야 합니다. 브랜치는 데이터베이스와 역할을 함께 격리합니다([브랜치와 복구](branches-and-recovery.md) 참고).

### 4단계: Delta 원본 테이블을 Snapshot 동기화 테이블로 복사

노트북이 원본 Delta 테이블 `lab_source_notes`를 직접 만듭니다. 그 다음 Snapshot 모드 동기화 테이블을 `production` 브랜치에 만듭니다. Snapshot은 동기화할 때마다 전체를 다시 복사하는 모드입니다.

```python
w.postgres.create_synced_table(
    synced_table=SyncedTable(
        spec=SyncedTableSyncedTableSpec(
            source_table_full_name=SOURCE_TABLE,
            branch=PROD,
            primary_key_columns=["id"],
            scheduling_policy=SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.SNAPSHOT,
            postgres_database=DB_NAME,
            create_database_objects_if_missing=True,
        )
    ),
    synced_table_id=SYNCED_TABLE,
).wait()

wait_for_synced(SYNCED_TABLE)
```

> **참고** SDK의 `.wait()`가 끝나도 초기 복사는 아직 진행 중일 수 있습니다. 실습 중 확인한 결과 생성 작업이 끝난 뒤에도 상태가 `PROVISIONING` 단계에 머물렀습니다. 노트북은 `wait_for_synced()`로 상태가 `SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE`가 될 때까지 기다립니다.

기대 결과(상태 변화 순서):

```text
SYNCED_TABLE_PROVISIONING_PIPELINE_RESOURCES
SYNCED_TABLE_PROVISIONING_INITIAL_SNAPSHOT
SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE
synced rows in Postgres: 3 [(1, '레이크하우스 메모 1'), (2, '레이크하우스 메모 2'), (3, '레이크하우스 메모 3')]
```

Postgres에서는 UC 스키마 이름이 Postgres 스키마가 되고, 테이블 이름은 UC 테이블 이름(`lab_source_notes_synced`)을 씁니다. 위젯 기본값이라면 조회 쿼리는 `lakebase_lab.lab_source_notes_synced` 형태입니다.

> **주의** 동기화 테이블의 Postgres 쪽은 읽기 전용으로 쓰는 것을 문서가 권장합니다. 이 실습은 조회만 합니다.

### 5단계: 정리

삭제 순서는 동기화 테이블, Postgres 테이블 확인, 브랜치, 프로젝트, 원본 Delta 테이블입니다.

```python
w.postgres.delete_synced_table(name=f"synced_tables/{SYNCED_TABLE}").wait()

# 동기화 테이블 삭제 후 Postgres 테이블이 남아 있으면 DROP TABLE
conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name = %s", ...)

w.postgres.delete_branch(name=LAB_BRANCH).wait()
w.postgres.delete_project(name=PROJECT, purge=True).wait()
spark.sql(f"DROP TABLE IF EXISTS {SOURCE_TABLE}")
```

기대 결과:

```text
Postgres table remaining after synced delete: []
project still listed: []
synced table: deleted
source table exists: False
```

동기화 테이블을 지운 뒤 Postgres 테이블은 남지 않았습니다. 문서는 한 곳에서 "Unity Catalog의 동기화 테이블을 삭제하면 Postgres 테이블도 함께 삭제된다"고 설명하고, 다른 곳에서는 "정리를 위해 Postgres 테이블을 DROP 한다"는 운영 작업을 나열합니다. 실습은 삭제 후 남는지 확인하는 단계를 넣어 두었고, 남으면 `DROP TABLE`로 지웁니다.

> **참고** `delete_project(..., purge=True)` 는 프로젝트를 영구 삭제합니다. 옵션 없이 삭제하면 이름이 soft-delete 상태로 남아 같은 ID로 다시 만들 수 없습니다([자주 나는 오류](#자주-나는-오류) 참고).

## 정리 (삭제) 확인

노트북 실행이 끝나면 다음 명령으로 리소스가 모두 없어졌는지 확인합니다. 명령은 로컬 Databricks CLI에서 실행합니다.

```bash
databricks postgres list-projects --show-deleted
databricks postgres get-synced-table synced_tables/<카탈로그>.<스키마>.lab_source_notes_synced
databricks tables list <카탈로그> <스키마>
```

첫 번째 명령에 `lakebase-lab`이 없어야 하고, 두 번째 명령은 `does not exist` 오류가 나야 합니다. 세 번째 명령에 `lab_source_notes`가 없어야 합니다.

## 자주 나는 오류

| 증상 | 원인 | 해결 |
|---|---|---|
| 1단계에서 `A soft-deleted project currently has this resource name` | 같은 ID의 프로젝트가 soft-delete 상태로 남아 있음 | `delete_project(name=..., purge=True)`로 영구 삭제하거나 다른 `project_id`를 씁니다 |
| 4단계에서 `Destination table ... already exists in UC` | 동기화 테이블의 UC 목적지 이름이 원본 Delta 테이블과 같음 | 목적지 이름을 원본과 다르게 씁니다. 이 실습은 `lab_source_notes_synced`를 씁니다 |
| 4단계 상태가 오래 `PROVISIONING`에 머묾 | 생성 작업이 끝난 것과 초기 복사가 끝난 것은 다름 | 상태가 `SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE`가 될 때까지 기다립니다 |
| 4단계 노트북 SQL 실패 | 카탈로그에 스키마나 테이블을 만들 권한이 없음 | 카탈로그의 `CREATE SCHEMA`, `CREATE TABLE` 권한을 요청합니다 |
| 실패 후 다시 실행이 안 됨 | 이전 실행의 프로젝트 또는 동기화 테이블이 남아 있음 | 정리 확인 명령으로 남은 리소스를 찾아 지운 뒤 다시 실행합니다 |

## 다음 단계

- 동기화 모드(Snapshot, Triggered, Continuous)와 타입 매핑은 [동기화 테이블](synced-tables.md)에서 다룹니다.
- 브랜치 만료, 리셋, 인스턴트 복구는 [브랜치와 복구](branches-and-recovery.md)에서 다룹니다.
- OAuth 토큰 재발급과 연결 수명은 [연결과 인증](connect-and-auth.md)에서 다룹니다.
- 확인 문제는 [퀴즈와 체크리스트](quiz.md)에서 풀 수 있습니다.

## 참고 문서

- [Get started with Lakebase Postgres (AWS)](https://docs.databricks.com/aws/en/oltp/projects/get-started)
- [Branches (AWS)](https://docs.databricks.com/aws/en/oltp/projects/branches)
- [Manage branches (AWS)](https://docs.databricks.com/aws/en/oltp/projects/manage-branches)
- [Authentication (AWS)](https://docs.databricks.com/aws/en/oltp/projects/authentication)
- [Sync tables (AWS)](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)
- [Quickstart: Serve lakehouse data (AWS)](https://docs.databricks.com/aws/en/oltp/projects/quickstart-synced-tables)
- [Postgres clients (AWS)](https://docs.databricks.com/aws/en/oltp/projects/postgres-clients)
