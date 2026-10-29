# 워크스페이스 UI

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 한눈에 보기

워크스페이스 UI는 Databricks의 웹 화면입니다. 공식 문서는 워크스페이스를 "your central hub for accessing all Databricks objects and features"라고 설명합니다. 이 페이지는 처음 로그인했을 때 보이는 화면, 왼쪽 사이드바(sidebar), 상단바(top bar)의 주요 항목을 정리하고, 자주 쓰는 작업을 어디서 시작하는지 안내합니다.

> **참고** 화면 구성은 릴리즈마다 바뀝니다. 아래 항목 이름은 공식 문서 "Navigate the workspace" 페이지에 적힌 표기를 따랐습니다. 실제 화면과 이름이 다르다면 워크스페이스 버전을 먼저 확인하십시오.

## 1. 홈 화면

홈 화면은 작업을 빠르게 다시 시작하는 곳입니다. 공식 문서가 설명하는 홈 화면 구성은 다음과 같습니다.

| 영역 | 내용 |
|---|---|
| Ask Genie | 데이터에 대한 질문을 하거나, 워크스페이스 객체를 검색하거나, Genie Code 대화를 시작합니다. |
| Suggested | 사용 이력을 바탕으로 추천되는 객체입니다. |
| Favorited | 즐겨찾기로 표시한 객체입니다. |
| Popular | 최근 30일 동안 상호작용이 많았던 객체입니다. |
| Mosaic AI | AI 관련 자산과 기능으로 가는 바로가기입니다. 문서 표기 그대로 옮겼습니다. |
| What's new | 최근 출시된 기능과 업데이트 안내입니다. |

> **참고** 홈 화면의 "Mosaic AI" 표기는 이 페이지를 작성할 때 공식 Navigate the workspace 문서에 있던 이름입니다. 다른 문서에서는 AI 관련 기능의 우산 명칭이 바뀌었을 수 있으므로, 수업 자료에 옮길 때는 대상 워크스페이스 화면과 릴리즈 노트를 함께 확인하십시오.

## 2. 사이드바

사이드바는 왼쪽에 고정된 메뉴입니다. 최상위 항목은 다음과 같습니다.

| 항목 | 용도 |
|---|---|
| Workspace | 워크스페이스 파일과 폴더를 탐색하고 관리합니다. 노트북도 여기 있습니다. |
| Recents | 최근에 연 객체를 빠르게 다시 엽니다. |
| Catalog | Unity Catalog에 등록된 데이터와 자산을 찾아봅니다(Catalog Explorer). |
| Jobs & Pipelines | 잡(job)과 파이프라인을 만들고 관리합니다. |
| Compute | 컴퓨트 리소스를 관리합니다. |
| Discover | 워크스페이스의 콘텐츠를 찾는 화면입니다. 문서에서 세부 설명은 확인되지 않았습니다. |
| Marketplace | 마켓플레이스 항목에 접근합니다. 세부 설명은 문서에 명시 없음. |

항목 옆에 **자물쇠(lock) 아이콘** 이 보이면 해당 기능을 쓰기 위한 권한(entitlement)이 없다는 뜻입니다. 권한을 요청하기 전에 관리자가 어떤 기능을 열어 두었는지 확인하십시오.

### 사이드바 아래 그룹

사이드바에는 최상위 항목 외에 영역별 그룹이 있습니다. 공식 문서가 그룹별로 나열한 항목은 다음과 같습니다.

| 그룹 | 포함 항목 |
|---|---|
| SQL | SQL Editor, Queries, Dashboards, Genie Agents, Alerts, Query History, SQL Warehouses |
| Data Engineering | Runs(잡 실행 모니터링), Data Ingestion(데이터 적재) |
| AI/ML | Playground, Agents, AI Gateway, Experiments, Features, Models, Serving |

> **참고** 그룹 이름과 항목 목록은 릴리즈마다 바뀝니다. 특히 AI 관련 항목은 이름이 자주 바뀌므로, 이 표는 "이런 그룹이 있다"는 안내로만 쓰고 메뉴 경로를 문서 자료에 고정해 쓰지 마십시오.

### 자주 쓰는 항목의 위치

| 하고 싶은 일 | 시작 위치 |
|---|---|
| 노트북 파일을 찾거나 새로 만든다 | Workspace |
| 테이블과 볼륨을 찾는다 | Catalog |
| 잡이나 파이프라인을 만든다 | Jobs & Pipelines |
| 실행 이력을 본다 | SQL 그룹의 Query History, 또는 Data Engineering 그룹의 Runs |
| SQL 쿼리를 작성한다 | SQL 그룹의 SQL Editor |
| 웨어하우스를 시작하거나 설정을 본다 | SQL 그룹의 SQL Warehouses 또는 Compute |

## 3. 상단바

상단바는 화면 위쪽에 있으며 공식 문서가 설명하는 항목은 다음과 같습니다.

| 항목 | 기능 |
|---|---|
| 워크스페이스 이름 | 같은 계정의 다른 워크스페이스로 전환합니다. |
| Genie Code | 질문을 하고, 문서와 연결된 답을 받습니다. |
| Search | 노트북, 쿼리, 대시보드, 파일, 테이블 같은 객체를 찾습니다. |
| + New | 객체와 컴퓨트를 만들고 파일을 업로드합니다. |
| 사용자 메뉴 | 설정(언어, 테마 등)을 열고 Databricks 지원에 문의합니다. |
| Help | Genie Code 메뉴 안에 있으며 도움말 센터, 설정, 피드백으로 연결됩니다. |

> **참고** 문서에서 "Genie"는 사이드바의 독립 항목이 아닙니다. 홈 화면에서는 "Ask Genie", SQL 그룹에서는 "Genie Agents"로 표기됩니다. 같은 이름을 다른 위치에서 찾으면 헷갈릴 수 있습니다.

Genie Code의 사용법은 [Genie Code 소개](../11-developer-tools/genie-code/README.md)에서 다룹니다.

## 4. + New 메뉴

+ New 메뉴는 새 객체를 만드는 가장 빠른 출발점입니다. 공식 문서 기준으로 다음을 할 수 있습니다.

- 노트북, 쿼리, 대시보드 같은 워크스페이스 객체를 만듭니다.
- 컴퓨트 리소스를 만듭니다.
- 파일을 업로드합니다.

이 교육 자료의 첫 실습에서는 **Notebook** 을 만드는 경로를 씁니다. 메뉴 항목의 세부 이름은 릴리즈에 따라 달라질 수 있으니, 메뉴가 보이지 않으면 Workspace 항목에서 같은 폴더 안에 새 노트북을 만드는 방법을 쓰십시오.

## 5. 워크스페이스 파일 탐색

Workspace 항목은 워크스페이스 파일 시스템을 보여 줍니다. 공식 문서는 이 영역을 "Workspace browser"로 설명하며, 폴더 정리와 파일 관리를 맡는다고 소개합니다.

| 작업 | 설명 |
|---|---|
| 폴더 만들기 | 사용자 폴더 아래에 프로젝트 단위로 폴더를 만듭니다. |
| 객체 식별자 확인 | 객체별 식별자(ID)는 "Get identifiers for workspace objects" 페이지에서 확인하도록 안내합니다. |
| 공유 | 객체별 권한을 설정합니다. 권한 세부는 06장과 공식 권한 문서를 참고하십시오. |

> **참고** 팀이 함께 관리하는 코드는 Git 폴더(Git folders)나 번들(bundle)로 관리하는 방식도 있습니다. 이 방식은 11장에서 다룹니다.

## 6. 검색

Search는 노트북, 쿼리, 대시보드, 파일, 테이블 같은 객체를 찾는 기능입니다. 상단바의 Search를 눌러 이름으로 찾을 수 있습니다. 검색 범위와 권한에 따라 보이는 결과가 다르다는 점을 기억하십시오. 객체에 권한이 없으면 목록에 보이지 않습니다.

## 7. 사용자가 자주 헷갈리는 지점

| 헷갈리는 점 | 정확한 이해 |
|---|---|
| Catalog와 Workspace가 같은 곳이라고 생각한다 | Workspace는 파일과 노트북, Catalog는 Unity Catalog에 등록된 데이터 자산입니다. 저장 위치가 다릅니다. |
| 사이드바의 SQL 그룹에 있으면 SQL 전용이다 | SQL 그룹의 항목은 SQL 작업 중심이지만, Genie Agents처럼 다른 영역과 겹치는 항목도 있습니다. |
| 화면에 메뉴가 없으니 기능이 없다 | 자물쇠 아이콘이나 권한, 워크스페이스 유형(서버리스·클래식)에 따라 메뉴가 보이지 않을 수 있습니다. |
| 홈 화면의 추천이 전체 목록이다 | Suggested, Popular는 사용 이력 기반의 일부 목록입니다. 전체는 사이드바에서 찾으십시오. |

## 8. 트레이드오프와 주의사항

> **주의** 화면 이름과 메뉴 위치는 자주 바뀝니다. 교육 자료나 실습 안내문에 메뉴 경로를 적을 때는 "기준일과 워크스페이스 버전"을 함께 적으십시오.

> **주의** 상단바의 "Genie Code"와 홈 화면의 "Ask Genie"는 서로 다른 입구입니다. 질문 범위와 권한이 다를 수 있으니 실습 중 결과가 다르면 입구를 먼저 확인하십시오.

> **참고** 워크스페이스 UI 외에 Databricks CLI와 API로도 같은 작업을 할 수 있습니다. 공식 문서의 Databricks CLI 페이지(`/aws/en/dev-tools/cli/`)를 참고하십시오.

## 다음으로 읽을 페이지

화면에서 노트북을 만들었다면, 노트북의 언어와 셀 실행 방식은 [노트북 기초](notebooks-basics.md)에서 이어집니다.

## 참고 문서

- [Workspace UI](https://docs.databricks.com/aws/en/workspace/)
- [Navigate the workspace](https://docs.databricks.com/aws/en/workspace/navigate-workspace)
- [Workspace browser](https://docs.databricks.com/aws/en/workspace/workspace-browser)
- [Search for workspace objects](https://docs.databricks.com/aws/en/search/)
- [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/)
