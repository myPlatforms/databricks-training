# Databricks notebook source
# MAGIC %md
# MAGIC # Lakebase 실습: Postgres 작업, 브랜치, 동기화 테이블
# MAGIC
# MAGIC 이 노트북은 Lakebase Postgres 프로젝트를 만들고 다음 순서로 실습합니다.
# MAGIC
# MAGIC 1. 프로젝트 생성 (가장 작은 컴퓨트, 스케일 투 제로)
# MAGIC 2. OAuth 자격 증명으로 Postgres에 접속해 테이블 생성, INSERT, SELECT, UPDATE, DELETE 실행
# MAGIC 3. 자식 브랜치에서 데이터를 바꾸고 기본 브랜치에 변경이 없는지 확인
# MAGIC 4. Unity Catalog Delta 테이블을 만들고 동기화 테이블(Snapshot)로 Postgres에서 조회
# MAGIC 5. 실습으로 만든 리소스 삭제
# MAGIC
# MAGIC 실행 전에 위젯 값을 확인하십시오. 기본값은 자리표시자입니다. 5단계는 이 노트북이 만든 리소스만 삭제합니다.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 0. 준비: 라이브러리 설치

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.158.0" "psycopg[binary]>=3.2"

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 0-1. 위젯과 공통 설정
# MAGIC
# MAGIC - **UC 카탈로그**: 원본 Delta 테이블을 만들 카탈로그. 권한이 있는 카탈로그를 입력합니다.
# MAGIC - **UC 스키마**: 원본 Delta 테이블과 동기화 테이블 이름을 정할 스키마.
# MAGIC - **Lakebase 프로젝트 ID**: 이 실습이 만들고 마지막에 삭제할 프로젝트 이름. 이미 있는 프로젝트 이름을 넣으면 1단계에서 실패합니다.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "UC 카탈로그")
dbutils.widgets.text("schema", "lakebase_lab", "UC 스키마")
dbutils.widgets.text("project_id", "lakebase-lab", "Lakebase 프로젝트 ID")

# COMMAND ----------

import time

import psycopg
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.postgres import (
    Branch,
    BranchSpec,
    Duration,
    Project,
    ProjectDefaultEndpointSettings,
    ProjectSpec,
    SyncedTable,
    SyncedTableSyncedTableSpec,
    SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy,
)
from psycopg import sql

w = WorkspaceClient()
# The Postgres login name is the Databricks user's email address.
ME = w.current_user.me().user_name

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
PROJECT_ID = dbutils.widgets.get("project_id")

PROJECT = f"projects/{PROJECT_ID}"
PROD = f"{PROJECT}/branches/production"
LAB_BRANCH = f"{PROJECT}/branches/lab-branch"
DB_NAME = "databricks_postgres"

SOURCE_TABLE = f"{CATALOG}.{SCHEMA}.lab_source_notes"
SYNCED_TABLE = f"{CATALOG}.{SCHEMA}.lab_source_notes_synced"


def endpoint_name(branch: str) -> str:
    """Return the resource name of the primary read-write endpoint of a branch."""
    return f"{branch}/endpoints/primary"


def connect(branch: str = PROD):
    """Open a Postgres connection. The OAuth token is used as the password."""
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


def wait_for_synced(synced_table_id: str, timeout_s: int = 1800) -> None:
    """Poll the synced table until the initial copy has finished."""
    deadline = time.time() + timeout_s
    while True:
        st = w.postgres.get_synced_table(name=f"synced_tables/{synced_table_id}").status.detailed_state
        state = getattr(st, "value", str(st))
        print(time.strftime("%H:%M:%S"), state)
        if state == "SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE":
            return
        if "FAIL" in state or time.time() > deadline:
            raise RuntimeError(f"Synced table is not ready: {state}")
        time.sleep(20)


def ignore_missing(fn) -> None:
    """Run a cleanup call and ignore the error if the resource is already gone."""
    try:
        fn()
    except NotFound:
        print("already deleted, skipping")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 프로젝트 생성
# MAGIC
# MAGIC 가장 작은 컴퓨트(0.5 CU 고정)와 5분 무활동 후 스케일 투 제로를 설정합니다. 프로젝트를 만들면 `production` 루트 브랜치와 `primary` 엔드포인트가 함께 생깁니다.

# COMMAND ----------

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

ep = w.postgres.get_endpoint(name=endpoint_name(PROD))
print("project:", project.name)
print("default branch:", project.status.default_branch)
print("endpoint state:", ep.status.current_state)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Postgres에서 기본 SQL 실행
# MAGIC
# MAGIC `connect()`가 OAuth 토큰을 발급받아 비밀번호로 씁니다. 실습 테이블 `lab_notes`를 만들고 INSERT, SELECT, UPDATE, DELETE를 실행합니다.

# COMMAND ----------

with connect(PROD) as conn:
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS lab_notes "
        "(id SERIAL PRIMARY KEY, body TEXT NOT NULL, done BOOLEAN DEFAULT FALSE)"
    )
    cur.execute("TRUNCATE lab_notes")

    cur.execute("INSERT INTO lab_notes (body) VALUES ('첫 메모'), ('둘째 메모'), ('셋째 메모') RETURNING id")
    print("INSERT ids:", [r[0] for r in cur.fetchall()])

    cur.execute("SELECT id, body, done FROM lab_notes ORDER BY id")
    print("SELECT:", cur.fetchall())

    cur.execute("UPDATE lab_notes SET done = TRUE WHERE id = 1")
    print("UPDATE rows:", cur.rowcount)

    cur.execute("DELETE FROM lab_notes WHERE id = 3")
    print("DELETE rows:", cur.rowcount)

    cur.execute("SELECT id, body, done FROM lab_notes ORDER BY id")
    print("SELECT after changes:", cur.fetchall())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. 브랜치에서 변경하고 기본 브랜치 확인
# MAGIC
# MAGIC `production`의 자식 브랜치 `lab-branch`를 만듭니다. 만료 기간은 1일(`ttl`)입니다. 브랜치에서 데이터를 바꾼 뒤 두 브랜치를 각각 조회합니다.

# COMMAND ----------

w.postgres.create_branch(
    parent=PROJECT,
    branch=Branch(spec=BranchSpec(source_branch=PROD, ttl=Duration(seconds=86400))),
    branch_id="lab-branch",
).wait()

with connect(LAB_BRANCH) as conn:
    conn.execute("INSERT INTO lab_notes (body) VALUES ('브랜치 전용 메모')")
    conn.execute("UPDATE lab_notes SET body = '브랜치에서 수정' WHERE id = 1")
    conn.execute("DELETE FROM lab_notes WHERE id = 2")
    print("lab-branch:", conn.execute("SELECT id, body FROM lab_notes ORDER BY id").fetchall())

with connect(PROD) as conn:
    print("production (변경 없어야 함):", conn.execute("SELECT id, body, done FROM lab_notes ORDER BY id").fetchall())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Delta 원본 테이블을 동기화 테이블로 Postgres에 복사
# MAGIC
# MAGIC 실습 노트북이 원본 Delta 테이블 `lab_source_notes`를 직접 만듭니다. 그 다음 Snapshot 모드 동기화 테이블을 `production` 브랜치에 만듭니다. 초기 복사가 끝날 때까지 상태를 기다린 뒤 Postgres에서 조회합니다.
# MAGIC
# MAGIC > **참고** SDK의 `.wait()`는 생성 작업 요청이 끝났다는 의미일 수 있습니다. 실제 복사가 끝났는지는 `wait_for_synced()`의 상태 값으로 확인합니다.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"CREATE OR REPLACE TABLE {SOURCE_TABLE} (id BIGINT NOT NULL, body STRING, updated_at TIMESTAMP)")
spark.sql(
    f"INSERT INTO {SOURCE_TABLE} VALUES "
    "(1, '레이크하우스 메모 1', current_timestamp()), "
    "(2, '레이크하우스 메모 2', current_timestamp()), "
    "(3, '레이크하우스 메모 3', current_timestamp())"
)
print("source rows:", spark.table(SOURCE_TABLE).count())

# COMMAND ----------

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

# COMMAND ----------

with connect(PROD) as conn:
    rows = conn.execute(
        sql.SQL("SELECT id, body FROM {}.{} ORDER BY id").format(
            sql.Identifier(SCHEMA), sql.Identifier("lab_source_notes_synced")
        )
    ).fetchall()
    print("synced rows in Postgres:", len(rows), rows)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. 정리
# MAGIC
# MAGIC 순서는 동기화 테이블, Postgres 테이블 확인, 브랜치, 프로젝트, 원본 Delta 테이블입니다. 동기화 테이블을 지운 뒤에도 Postgres 테이블이 남아 있으면 `DROP TABLE`로 지웁니다. 이 셀은 여러 번 실행해도 안전합니다.

# COMMAND ----------

# 5-1. Delete the synced table from Unity Catalog.
ignore_missing(lambda: w.postgres.delete_synced_table(name=f"synced_tables/{SYNCED_TABLE}").wait())

# 5-2. Check whether the Postgres table remains, and drop it if so.
with connect(PROD) as conn:
    left = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name = %s",
        (SCHEMA, "lab_source_notes_synced"),
    ).fetchall()
    print("Postgres table remaining after synced delete:", left)
    if left:
        conn.execute(sql.SQL("DROP TABLE {}.{}").format(sql.Identifier(SCHEMA), sql.Identifier("lab_source_notes_synced")))
        print("dropped Postgres table")

# COMMAND ----------

# 5-3. Delete the child branch, then the project (the project deletion also removes production).
# A plain delete is a soft delete that keeps the project ID reserved, so purge is used here
# to let the lab be run again with the same project ID.
ignore_missing(lambda: w.postgres.delete_branch(name=LAB_BRANCH).wait())
ignore_missing(lambda: w.postgres.delete_project(name=PROJECT, purge=True).wait())

# COMMAND ----------

# 5-4. Drop the source Delta table created in step 4.
spark.sql(f"DROP TABLE IF EXISTS {SOURCE_TABLE}")

# COMMAND ----------

# 5-5. Verify that the lab resources are gone.
remaining_projects = [p.name for p in w.postgres.list_projects() if p.name == PROJECT]
print("project still listed:", remaining_projects)
try:
    w.postgres.get_synced_table(name=f"synced_tables/{SYNCED_TABLE}")
    print("synced table still exists")
except NotFound:
    print("synced table: deleted")
print("source table exists:", spark.catalog.tableExists(SOURCE_TABLE))
