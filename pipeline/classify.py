"""Task 2 (classify) — map new source items to site pages with ai_query.

Reads   <catalog>.<schema>.source_items (status new|error) and .pages

The endpoint must support ai_query responseFormat (structured output). As of 2026-10,
Claude 5.x endpoints reject it; GPT-5.x, Gemini and Claude Sonnet 4.6 accept it.
Writes  <catalog>.<schema>.item_page_map, sets source_items.status to classified|error
Sets task values for downstream tasks: relevant_count, classified_count

Job usage (spark_python_task parameters):
  --catalog C --schema S --llm-endpoint E [--max-items N]
"""

from __future__ import annotations

import argparse
import json
import traceback
from datetime import UTC, datetime

from pyspark.sql import SparkSession

# Planned curriculum — keep in sync with docs/README.md.
CHAPTERS = """\
01 플랫폼 개요
02 레이크하우스 스토리지 (Delta Lake, Iceberg)
03 컴퓨트 (서버리스, 클래식, SQL 웨어하우스)
04 데이터 엔지니어링 (Lakeflow: 수집, 파이프라인, Jobs)
05 데이터 웨어하우징 (Databricks SQL)
06 Unity Catalog 거버넌스
07 AI/BI (대시보드, Genie)
08 머신러닝 (MLflow, Model Serving)
09 AI 에이전트
10 Lakebase
11 개발자 도구 (Genie Code, CLI, Bundles, SDK, Apps)
12 보안·운영 (시스템 테이블, 비용)"""

CHANGE_TYPES = [
    "new_feature",
    "status_change",
    "rename",
    "deprecation",
    "limit_change",
    "behavior_change",
    "model_added",
    "region_added",
    "other",
]

RESPONSE_FORMAT = json.dumps(
    {
        "type": "json_schema",
        "json_schema": {
            "name": "training_impact",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "relevant": {"type": "boolean"},
                    "change_type": {"type": "string", "enum": CHANGE_TYPES},
                    "chapter": {"type": "string"},
                    "pages": {"type": "array", "items": {"type": "string"}},
                    "new_page_candidate": {"type": "string"},
                    "summary_ko": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": [
                    "relevant",
                    "change_type",
                    "chapter",
                    "pages",
                    "new_page_candidate",
                    "summary_ko",
                    "reason",
                ],
                "additionalProperties": False,
            },
        },
    }
)

INSTRUCTIONS = """\
당신은 Databricks 한국어 교육 자료의 편집자입니다. 아래 변경 항목(릴리즈 노트, 블로그 글, 또는 교육 자료가 인용한 공식 문서의 변경 diff)이
교육 자료의 어느 장·페이지에 영향을 주는지 판정합니다.

판정 기준:
- relevant=true: 교육 자료가 가르치는 사실이 바뀌거나 새로 생김 — 신기능, GA/Preview 상태 변경, 제품·기능 개명, 폐기,
  한도·수치 변경, 동작 방식 변경, 교육 대상 기능의 리전 추가.
- relevant=false: 교육 내용에 영향이 없음 — 단순 모델 추가(model_added), 마케팅·이벤트·고객 사례 위주 블로그,
  오타·서식만 바뀐 문서 diff, 교육 범위 밖의 아주 좁은 기능.
- pages: 아래 '현재 페이지 목록'의 path 중 수정이 필요한 것만 고릅니다. 목록에 없는 path는 절대 만들지 않습니다.
  인용 문서 diff 항목은 'Cited by:'에 적힌 페이지가 우선 후보입니다.
- new_page_candidate: 해당 내용을 다룰 페이지가 아직 없지만 장 범위 안이면 제안할 페이지 제목(한국어). 없으면 빈 문자열.
- chapter: 아래 커리큘럼의 두 자리 장 번호("10" 등). 해당 없으면 빈 문자열.
- summary_ko: 무엇이 바뀌었는지 한국어 한 문장(60~120자). 제품명·기능명은 원문 표기 그대로, 상태 라벨(GA, Public Preview, Beta)은 원문대로.
- reason: 판정 근거 한국어 한 문장.

커리큘럼:
{chapters}

현재 페이지 목록 (path | 제목 | 기준일):
{page_index}
"""


def build_prompts(spark: SparkSession, fq: str, max_items: int) -> int:
    pages = spark.sql(f"SELECT path, title, basis_date FROM {fq}.pages ORDER BY path").collect()
    page_index = "\n".join(f"{p.path} | {p.title} | {p.basis_date}" for p in pages)
    header = INSTRUCTIONS.format(chapters=CHAPTERS, page_index=page_index)
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW pending AS
        SELECT item_id, source, area, url, title, published_date, body
        FROM {fq}.source_items WHERE status IN ('new', 'error')  -- errors are retried
        ORDER BY published_date DESC NULLS LAST LIMIT {int(max_items)}""")
    spark.createDataFrame([(header,)], "header STRING").createOrReplaceTempView("prompt_header")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW prompts AS
        SELECT p.item_id,
               concat(h.header, '\n\n--- 변경 항목 ---\n',
                      '출처: ', p.source, ' / ', coalesce(p.area, ''), '\n',
                      '날짜: ', coalesce(cast(p.published_date AS STRING), '미상'), '\n',
                      'URL: ', p.url, '\n',
                      '제목: ', coalesce(p.title, ''), '\n\n',
                      substr(coalesce(p.body, ''), 1, 8000)) AS prompt
        FROM pending p CROSS JOIN prompt_header h""")
    return spark.sql("SELECT count(*) c FROM prompts").first().c


def classify(spark: SparkSession, fq: str, endpoint: str) -> dict:
    fmt = RESPONSE_FORMAT.replace("'", "\\'")
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW classified AS
        SELECT item_id, ai_query('{endpoint}', prompt,
                                 responseFormat => '{fmt}', failOnError => false) AS r
        FROM prompts""")
    # Materialize once: ai_query must not be re-evaluated by each downstream statement.
    spark.sql("SELECT item_id, r.result AS result, r.errorMessage AS error FROM classified").write.mode(
        "overwrite"
    ).saveAsTable(f"{fq}._classify_tmp")
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW parsed AS
        SELECT item_id, error,
               from_json(result, 'relevant BOOLEAN, change_type STRING, chapter STRING,
                 pages ARRAY<STRING>, new_page_candidate STRING, summary_ko STRING, reason STRING') AS j
        FROM {fq}._classify_tmp""")
    # Higher-order functions cannot contain subqueries — pass valid paths as a literal array.
    valid_paths = sorted(r.path for r in spark.sql(f"SELECT path FROM {fq}.pages").collect())
    valid_sql = "array(" + ", ".join("'" + p.replace("'", "''") + "'" for p in valid_paths) + ")"
    spark.sql(f"""
        MERGE INTO {fq}.item_page_map t
        USING (
          SELECT item_id, j.relevant, j.change_type, j.chapter,
                 filter(j.pages, x -> array_contains({valid_sql}, x)) AS pages,
                 j.new_page_candidate, j.summary_ko, j.reason
          FROM parsed WHERE error IS NULL AND j IS NOT NULL) s
        ON t.item_id = s.item_id
        WHEN MATCHED THEN UPDATE SET relevant = s.relevant, change_type = s.change_type,
          chapter = s.chapter, pages = s.pages, new_page_candidate = s.new_page_candidate,
          summary_ko = s.summary_ko, reason = s.reason, model = '{endpoint}',
          classified_at = current_timestamp()
        WHEN NOT MATCHED THEN INSERT (item_id, relevant, change_type, chapter, pages,
          new_page_candidate, summary_ko, reason, model, classified_at)
          VALUES (s.item_id, s.relevant, s.change_type, s.chapter, s.pages,
          s.new_page_candidate, s.summary_ko, s.reason, '{endpoint}', current_timestamp())""")
    spark.sql(f"""
        MERGE INTO {fq}.source_items t
        USING (SELECT item_id, CASE WHEN error IS NULL AND j IS NOT NULL THEN 'classified' ELSE 'error' END AS st
               FROM parsed) s
        ON t.item_id = s.item_id
        WHEN MATCHED THEN UPDATE SET status = s.st""")
    row = spark.sql("""
        SELECT count(*) AS total,
               count_if(error IS NULL AND j IS NOT NULL) AS ok,
               count_if(j.relevant) AS relevant,
               first(error, true) AS sample_error
        FROM parsed""").first()
    spark.sql(f"DROP TABLE IF EXISTS {fq}._classify_tmp")
    return row.asDict()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--llm-endpoint", required=True)
    ap.add_argument("--max-items", type=int, default=200)
    ap.add_argument("--job-run-id", default="")
    args = ap.parse_args()

    spark = SparkSession.builder.getOrCreate()
    fq = f"`{args.catalog}`.`{args.schema}`"
    started = datetime.now(UTC)
    stats: dict = {}
    error = None
    try:
        stats["pending"] = build_prompts(spark, fq, args.max_items)
        if stats["pending"]:
            stats |= classify(spark, fq, args.llm_endpoint)
        print("classify", stats)
        if stats["pending"] and stats.get("ok", 0) == 0:
            raise RuntimeError(f"all {stats['pending']} classifications failed: {stats.get('sample_error')}")
        try:
            from databricks.sdk.runtime import dbutils

            dbutils.jobs.taskValues.set(key="relevant_count", value=int(stats.get("relevant", 0)))
            dbutils.jobs.taskValues.set(key="classified_count", value=int(stats.get("ok", 0)))
        except Exception as e:  # noqa: BLE001 — not running inside a job
            print(f"task values not set: {e}")
    except Exception:
        error = traceback.format_exc()[-4000:]
        raise
    finally:
        spark.createDataFrame(
            [
                (
                    args.job_run_id,
                    "classify",
                    started,
                    datetime.now(UTC),
                    json.dumps(stats, default=str),
                    error,
                )
            ],
            "job_run_id STRING, task STRING, started_at TIMESTAMP, finished_at TIMESTAMP, stats STRING, error STRING",
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.run_log")


if __name__ == "__main__":
    main()
