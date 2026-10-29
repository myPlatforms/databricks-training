# Databricks 교육 자료

> 기준일: 2026-10-28 · 근거: 공식 문서

Databricks Data + AI Platform을 기능별로 정리한 한국어 교육 자료입니다.
각 기능을 **왜 필요한가 → 어떻게 동작하는가 → 어떻게 쓰는가 → 트레이드오프 → 주의사항** 순서로 설명합니다.

## 이 자료의 특징

- **공식 문서 기반**: 모든 내용은 Databricks 공식 문서·릴리즈 노트·블로그를 근거로 하며, 각 페이지 끝에 참고 문서를 링크합니다.
- **상태 표기**: 기능마다 GA / Public Preview / Beta 상태를 기준일과 함께 표기합니다.
- **수준 표시**: 모든 페이지 맨 위에 수준(100·200·300)을 표시합니다. 아래 [수준 안내](#수준-안내)를 보세요.
- **퀴즈와 체크리스트**: 장마다 마지막 페이지에 내용 확인 문제와 실무 적용 체크리스트가 있습니다.
- **주기적 최신화**: 릴리즈 노트와 블로그를 정기적으로 수집해 영향받는 페이지를 갱신합니다. 반영 내역은 [변경 이력](updates.md)에서 확인할 수 있습니다.

## 커리큘럼

| 장 | 주제 | 수준 | 상태 |
|---|---|---|---|
| 01 | [플랫폼 개요](01-platform-overview/README.md) | 100~200 | 공개 |
| 02 | [레이크하우스 스토리지 (Delta Lake·Iceberg)](02-lakehouse-storage/README.md) | 100~300 | 공개 |
| 03 | [컴퓨트 (서버리스·클래식·SQL 웨어하우스)](03-compute/README.md) | 100~300 | 공개 |
| 04 | [데이터 엔지니어링 (Lakeflow)](04-data-engineering/README.md) | 100~300 | 공개 |
| 05 | [데이터 웨어하우징 (Databricks SQL)](05-data-warehousing/README.md) | 100~300 | 공개 |
| 06 | [Unity Catalog 거버넌스](06-unity-catalog/README.md) | 100~300 | 공개 |
| 07 | [AI/BI (대시보드·Genie)](07-ai-bi/README.md) | 100~300 | 공개 |
| 08 | [머신러닝 (MLflow·Model Serving)](08-machine-learning/README.md) | 100~300 | 공개 |
| 09 | [AI 에이전트](09-ai-agents/README.md) | 100~300 | 공개 |
| 10 | [Lakebase](10-lakebase/README.md) | 100~300 | 공개 |
| 11 | [개발자 도구](11-developer-tools/README.md) — Genie Code, Databricks CLI, Declarative Automation Bundles, SDK·REST API, Databricks Apps, Git·CI/CD | 100~300 | 공개 |
| 12 | [보안·운영 (시스템 테이블·비용)](12-security-operations/README.md) | 100~300 | 공개 |

## 수준 안내

| 수준 | 다루는 내용 | 주 독자 |
|---|---|---|
| 100 | 개념 — 무엇이고 왜 쓰는지, 구성 요소와 용어. 코드 없이 읽을 수 있습니다 | 누구나 (의사결정자·비기술 직군 포함) |
| 200 | 실무 — 설정, UI 절차, SQL·코드로 직접 사용하는 방법 | 분석가·엔지니어·개발자 |
| 300 | 심화 — 설계 판단, 내부 동작, 한도·제약의 조합, 운영·비용·보안 | 플랫폼 관리자·아키텍트 |

수준은 페이지의 중심 내용을 기준으로 붙였습니다. 각 장 첫 페이지의 페이지 안내 표에서 페이지별 수준을 볼 수 있습니다.

## 역할별 학습 경로

모든 경로는 01장(플랫폼 개요)에서 시작합니다. 처음에는 각 장의 수준 100 페이지만 읽고, 필요한 장으로 돌아가 200·300 페이지를 읽는 방식을 권장합니다.

| 역할 | 권장 순서 | 비고 |
|---|---|---|
| 처음 접하는 분·의사결정자 | 01 → 02 → 07 → 09 → 12 | 수준 100 페이지 중심 |
| 데이터 분석가 | 01 → 05 → 07 → 06 | 06장은 권한·메트릭 뷰 중심 |
| 데이터 엔지니어 | 01 → 02 → 03 → 04 → 05 → 06 → 11 | 11장은 CLI·번들·CI/CD |
| ML·AI 엔지니어 | 01 → 03 → 08 → 09 → 11 | 09장 다음 11장의 Apps |
| 애플리케이션 개발자 | 01 → 10 → 11 → 06 | Lakebase와 Apps 연동 |
| 플랫폼 관리자·아키텍트 | 01 → 03 → 06 → 12 → 각 장 수준 300 | 비용·보안·운영 |

## 참고 문서

- [Databricks 공식 문서 (AWS)](https://docs.databricks.com/aws/en/)
- [Azure Databricks 공식 문서](https://learn.microsoft.com/en-us/azure/databricks/)
- [Databricks 릴리즈 노트](https://docs.databricks.com/aws/en/release-notes/)
- [Databricks 블로그](https://www.databricks.com/blog)
