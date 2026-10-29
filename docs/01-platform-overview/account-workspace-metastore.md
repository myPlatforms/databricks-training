# 계정·워크스페이스·메타스토어

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Databricks 리소스는 세 계층으로 묶입니다. 위에서부터 **계정(account)**, ** 워크스페이스(workspace)**, **Unity Catalog 메타스토어(metastore)** 입니다. 계정은 여러 워크스페이스를 포함하고, 메타스토어는 계정 단위로 존재하며 여러 워크스페이스가 공유할 수 있습니다.

| 개념 | 공식 문서의 정의 | 주요 역할 |
|---|---|---|
| 계정(account) | "represents a single entity that can include multiple workspaces." | 청구와 지원이 계정 단위로 처리됩니다. 워크스페이스를 만들고 묶습니다. |
| 워크스페이스(workspace) | "a Databricks deployment in the cloud that functions as an environment for your team to access Databricks assets." | 팀이 노트북, 잡, 쿼리, 컴퓨트를 사용하는 작업 공간입니다. |
| 메타스토어(metastore) | "an account-level metastore that registers metadata about data, AI, and permissions about catalogs, schemas, and tables." | 카탈로그·스키마·테이블의 메타데이터와 권한을 등록하고 관리합니다. |

> **참고** 메타스토어는 계정 수준에 있으며, 같은 리전의 여러 워크스페이스에 연결할 수 있다고 아키텍처 문서가 설명합니다. 여러 워크스페이스가 같은 데이터를 같은 권한 체계로 보는 구조가 이 설계에서 나옵니다.

## 1. 계층 관계

계정 → 워크스페이스 → 메타스토어의 포함 관계는 아래 표로 정리합니다. 같은 리전의 워크스페이스 여러 개가 하나의 메타스토어를 공유하는 것이 핵심입니다.

| 상위 | 하위 | 관계 |
|---|---|---|
| 계정 | 워크스페이스 | 한 계정은 여러 워크스페이스를 가질 수 있습니다. |
| 계정 | 메타스토어 | 메타스토어는 계정 수준으로 등록됩니다. |
| 메타스토어 | 워크스페이스 | 같은 리전의 여러 워크스페이스가 한 메타스토어를 공유할 수 있습니다. |
| 메타스토어 | 카탈로그 → 스키마 → 테이블·볼륨 등 | 메타스토어 안에서 3단계 이름 구조로 데이터 자산을 구성합니다. |

## 2. 계정: 청구와 관리의 단위

계정은 Databricks 계정 콘솔에서 관리합니다. 공식 문서 기준으로 계정은 다음 역할을 맡습니다.

- 워크스페이스를 생성하고 묶는 최상위 단위입니다.
- 청구와 지원이 계정 단위로 처리됩니다.
- 메타스토어를 등록하고 워크스페이스에 할당하는 기준입니다.

> **참고** 계정 콘솔의 메뉴 이름과 세부 절차는 Databricks가 자주 바꿉니다. 이 장은 계정 콘솔의 화면 구성을 다루지 않습니다. 워크스페이스를 만드는 절차는 공식 문서 "Create a workspace"(`/aws/en/admin/workspace/`)를 따르십시오.

## 3. 워크스페이스: 팀의 작업 공간

워크스페이스는 "팀이 Databricks 자산에 접근하는 환경"입니다. 노트북, 쿼리, 대시보드, 잡, 파이프라인, 컴퓨트가 워크스페이스 안에 만들어집니다.

공식 문서의 워크스페이스 UI 개요는 워크스페이스를 "your central hub for accessing all Databricks objects and features"라고 설명합니다. 세부 화면은 [워크스페이스 UI](workspace-ui.md)에서 다룹니다.

### 워크스페이스를 나누는 기준

| 상황 | 워크스페이스를 나누는 것이 맞는가 | 이유 |
|---|---|---|
| 팀별로 권한과 컴퓨트를 분리하고 싶다 | 대체로 예 | 워크스페이스는 팀의 작업 환경 단위입니다. |
| 같은 데이터를 여러 팀이 본다 | 워크스페이스를 나누되 메타스토어는 공유 | 메타스토어를 같은 리전의 워크스페이스에 연결해 데이터 권한을 한 곳에서 관리합니다. |
| 개발과 운영을 분리한다 | 대체로 예 | 배포 경로와 권한을 분리하는 단위로 씁니다. 구체적인 배포 방식은 11장과 DAB 관련 문서를 참고하십시오. |
| 리전이 다르다 | 나눠야 합니다 | 메타스토어 연결은 같은 리전 워크스페이스가 기준이라고 문서가 설명합니다. |

> **참고** 위 표의 "개발과 운영 분리"는 일반적인 설계 원칙입니다. 공식 문서가 권장 구조를 명시한 것은 아닙니다.

## 4. Unity Catalog 메타스토어: 거버넌스의 중심

Unity Catalog는 Databricks의 데이터·AI 거버넌스 시스템입니다. 공식 문서는 메타스토어를 "테이블과 ML 모델 같은 데이터 자산을 관리하는 중앙 거버넌스 시스템"으로 설명하고, **catalog → schema → object** 세 단계의 네임스페이스(namespace)를 사용한다고 명시합니다.

### 3단계 이름 구조

| 단계 | 설명 | 예시 |
|---|---|---|
| 카탈로그(catalog) | 데이터를 구분하고 격리하는 최상위 컨테이너 | `sales_dev` |
| 스키마(schema) | 카탈로그 안의 데이터베이스 역할. 테이블, 볼륨, 함수, 모델을 담습니다. | `orders` |
| 테이블(table) 등 객체 | 실제 데이터 자산 | `sales_dev.orders.daily_orders` |

테이블 이름은 `catalog.schema.table` 형식으로 씁니다. 예를 들어 다음 SQL은 이 3단계 이름을 그대로 사용합니다.

```sql
-- 카탈로그와 스키마를 만든 뒤 테이블을 조회하는 예
CREATE SCHEMA IF NOT EXISTS sales_dev.orders;

SELECT order_id, order_date, amount
FROM sales_dev.orders.daily_orders
WHERE order_date >= '2026-10-01'
LIMIT 100;
```

> **참고** 카탈로그를 만들 권한이 없다면 `CREATE SCHEMA` 단계에서 실패합니다. 권한 모델은 06장에서 다룹니다.

### 메타스토어와 저장소의 관계

메타스토어는 메타데이터와 권한을 저장하고, 실제 데이터 파일은 클라우드 객체 스토리지에 둡니다. 관리형(managed) 테이블의 데이터는 Unity Catalog가 관리하는 저장 위치에 기록되고, 외부(external) 위치를 쓰는 경우에는 고객이 지정한 클라우드 경로를 사용합니다. 저장 위치의 세부는 02장에서 다룹니다.

## 5. 기본 카탈로그와 기본 스토리지

서버리스 워크스페이스는 기본 스토리지(Default storage)를 사용하고, 워크스페이스가 만들어질 때 기본 카탈로그가 함께 생깁니다. 공식 문서는 다음을 명시합니다.

- 기본 스토리지는 Databricks 계정 안의 완전 관리형 객체 스토리지입니다.
- 기본 스토리지에 생성한 카탈로그는 기본적으로 만든 워크스페이스에서만 접근할 수 있습니다. 다른 워크스페이스에 권한을 부여할 수 있지만, 그 워크스페이스는 서버리스 컴퓨트를 써야 합니다.
- 클래식 컴퓨트는 기본 스토리지의 데이터 자산과 상호작용할 수 없습니다.
- 관리형 테이블이나 볼륨을 삭제한 뒤에도 데이터 파일은 **7일 복구 기간** 동안 보존된다고 문서가 설명합니다.

## 6. 설계 체크리스트

| 질문 | 확인할 것 |
|---|---|
| 워크스페이스를 몇 개 만들 것인가 | 팀·환경·리전 기준으로 나눕니다. 리전이 다르면 메타스토어를 공유할 수 없습니다. |
| 메타스토어는 리전마다 하나인가 | 같은 리전 워크스페이스가 한 메타스토어를 공유하는 구조를 기준으로 설계합니다. |
| 카탈로그를 환경별로 나눌 것인가 | 카탈로그가 격리 단위이므로 개발·운영 데이터를 나누는 데 쓸 수 있습니다. |
| 기본 스토리지를 쓸 것인가 | 클래식 컴퓨트 사용 여부와 함께 결정합니다. 기본 스토리지 데이터는 클래식 컴퓨트에서 직접 다룰 수 없습니다. |

## 7. 트레이드오프

| 선택지 | 장점 | 주의 |
|---|---|---|
| 워크스페이스를 많이 나눈다 | 팀별 격리와 권한 분리가 쉽습니다. | 워크스페이스마다 설정과 컴퓨트 정책을 따로 관리해야 합니다. |
| 워크스페이스를 적게 쓰고 카탈로그로 나눈다 | 설정이 한곳에 모입니다. | 카탈로그 권한이 복잡해지면 실수가 생기기 쉽습니다. |
| 메타스토어를 여럿 둔다 | 리전·조직별 독립성이 높습니다. | 같은 데이터를 여러 메타스토어에서 따로 관리하게 되어 거버넌스가 나뉩니다. |

## 8. 주의사항

> **주의** 메타스토어는 리전 단위로 생각해야 합니다. 다른 리전의 워크스페이스를 같은 메타스토어에 묶으려는 설계는 처음부터 다시 검토하십시오.

> **주의** 계정 관리자와 워크스페이스 관리자, 카탈로그 소유자는 서로 다른 권한입니다. 한 사람이 모든 권한을 가진 상태를 운영 기본값으로 두지 마십시오.

> **참고** 공식 문서의 "Get started with Unity Catalog" 페이지에서 메타스토어 등록과 첫 카탈로그 생성 절차를 확인할 수 있습니다.

## 다음으로 읽을 페이지

계정과 메타스토어의 구조를 이해했다면, 실제 화면에서 이 구조가 어떻게 보이는지 [워크스페이스 UI](workspace-ui.md)에서 확인합니다.

## 참고 문서

- [Concepts (account, workspace, metastore, catalog, schema, table)](https://docs.databricks.com/aws/en/getting-started/concepts)
- [What is Unity Catalog?](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)
- [Get started with Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started)
- [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [Default storage in Databricks](https://docs.databricks.com/aws/en/storage/default-storage)
- [Workspace UI](https://docs.databricks.com/aws/en/workspace/)
