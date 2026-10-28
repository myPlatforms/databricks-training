# Genie Code

> 기준일: 2026-10-28 · 근거: 공식 문서

## Genie Code란

Genie Code는 Databricks 워크스페이스 안에서 동작하는 AI 코딩·데이터 어시스턴트입니다. 문서는 이 제품이 코드를 생성하고 실행하며, 파이프라인과 AI/BI 대시보드를 만들고, 오류를 디버깅하고, Unity Catalog의 테이블·컬럼·계보(lineage)를 다룬다고 설명합니다. 문서에서는 계획을 세우고, 코드를 실행하고, 오류를 고치는 **자율 에이전트(autonomous agent)** 로 소개합니다.

Genie Code를 쓰면 데이터 엔지니어와 분석가가 노트북이나 SQL 에디터를 떠나지 않고 다음을 할 수 있습니다.

- 자연어로 질문하고 결과 코드를 바로 실행합니다.
- 실패한 셀의 오류를 진단하고 수정안을 받습니다.
- 테이블 설명과 컬럼 메타데이터를 근거로 SQL을 작성합니다.
- 반복 작업을 예약 작업이나 Lakeflow Jobs 태스크로 옮깁니다.

## 어디에서 쓰는가

| 진입점 | 문서상 표현 | 비고 |
|--------|-------------|------|
| 채팅 패널 | "Genie Code is available as a chat pane on most Databricks pages" | 우상단 Genie Code 아이콘으로 엽니다. |
| 전체 화면 모드 | "full page command center" | 워크스페이스 홈 프롬프트 또는 패널의 Maximize 버튼 |
| 노트북·파일 | 셀 디버깅, 코드 편집 | 편집한 자산은 채팅 옆 탭으로 열립니다. |
| Unity Catalog 테이블 | 테이블·컬럼 탐색 | |
| AI/BI 대시보드 | "Data analysis in dashboards" | 필요 시 대시보드 페이지로 이동해 편집합니다. |
| Lakeflow Pipelines 에디터 | "Pipeline development in Lakeflow" | 기능 페이지에 명시됩니다. |
| SQL 에디터 | SQL 정확도 개선, 샘플 데이터 탐색 | 기능 페이지에 명시됩니다. |
| MLflow | "Observability and evaluation in MLflow" | |
| Lakeflow Jobs | Genie Code 태스크 | Job 안에서 자율 실행합니다. [상세](lakeflow-jobs-task.md) |
| 예약 작업 | Scheduled tasks | 반복 실행하며 실행마다 새 채팅을 만듭니다. [상세](scheduled-tasks.md) |
| 터미널 | Genie Code CLI (Beta) | 로컬 파일과 워크스페이스 데이터를 함께 다룹니다. [상세](cli.md) |

> **참고** 진입점 목록은 여러 페이지에 흩어져 있습니다. 노트북·SQL 에디터·파이프라인 에디터의 세부 노출 범위는 문서 페이지마다 서술이 다르므로, 실제 화면에서 확인한 뒤 사용하는 것을 권장합니다.

## 이 장의 구성

| 페이지 | 다루는 내용 |
|--------|-------------|
| [모드·기능과 데이터 접근 권한](features-and-permissions.md) | 진입점, 프롬프트 박스, 승인 모드, 기능 목록, 메모리, 권한 모델 |
| [인스트럭션과 스킬](instructions-and-skills.md) | 사용자·워크스페이스 인스트럭션 경로와 우선순위, AGENTS.md·CLAUDE.md 자동 로드, SKILL.md 구조 |
| [MCP 서버 연결](mcp.md) | 기본 제공 커넥터, 외부 서버, 사용자 정의 Databricks App 연결 |
| [예약 작업](scheduled-tasks.md) | 반복 실행 프롬프트, 자동 승인 항상 켜짐 |
| [Lakeflow Jobs의 Genie Code 태스크](lakeflow-jobs-task.md) | 프롬프트 파라미터, 상위 태스크 값, 출력, 설계 패턴, 예약 작업과의 차이 |
| [Genie Code CLI](cli.md) | 설치, 명령, MCP 추가, 로컬 파일 권한 범위, 제약 |
| [거버넌스와 비용](governance-and-cost.md) | 과금 구조, 예산, 사용량 확인, 파트너 AI 설정, 데이터 처리 지역 |

## 상태 요약

문서 페이지에 상태 라벨이 있는 항목과 릴리즈 노트로만 확인되는 항목을 구분했습니다.

| 기능 | 상태 | 근거 |
|------|------|------|
| Genie Code 채팅·전체 화면 | 페이지에 라벨 없음 | 전체 화면 모드는 릴리즈 노트 2026-08-04에 GA로 표기 |
| 예약 작업 | 페이지에 라벨 없음 | 릴리즈 노트 2026-09-01 GA |
| Lakeflow Jobs의 Genie Code 태스크 | 페이지에 라벨 없음 | 릴리즈 노트 2026-10-21 GA (2026-08-27에는 Beta) |
| Genie Code CLI | Beta | 페이지 및 릴리즈 노트 2026-10-06 |
| Genie Ontology | Public Preview | 기능 페이지 |
| 세션 간 메모리, 인스트럭션, 스킬, MCP 서버 | 페이지에 라벨 없음 | 릴리즈 노트에서 별도 항목 확인되지 않음 |
| 웹 검색 | Beta | 릴리즈 노트 2026-08-06 |
| AI Runtime 노트북 지원 | Public Preview | 릴리즈 노트 2026-08-27 |

## 클라우드 범위

이 장은 AWS 문서를 기준으로 합니다. Genie Code는 Azure(Microsoft Learn 호스팅)와 GCP 문서도 따로 가지고 있으며, 이 장에서는 그 문서를 확인하지 않았습니다. 지역별 처리 가능 여부는 [거버넌스와 비용](governance-and-cost.md)의 Designated Services 항목을 참고하십시오.

## 참고 문서

- [Genie Code 개요](https://docs.databricks.com/aws/en/genie-code/)
- [Navigate Genie Code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [Features and capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [Genie Code 릴리즈 노트 (2026년 8월)](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
- [Genie Code 릴리즈 노트 (2026년 10월)](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
