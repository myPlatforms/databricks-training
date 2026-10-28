# Lakebase 개요

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Lakebase는 Databricks 플랫폼에 통합된 **관리형 Postgres 데이터베이스** 입니다. 공식 문서는 Lakebase를 "fully managed Postgres database integrated into the Databricks platform"으로 설명합니다. 실시간 트랜잭션 애플리케이션을 레이크하우스 데이터와 나란히 운영하고, 자동 스케일링, 즉시 브랜칭, Unity Catalog 통합을 제공합니다.

| 항목 | 내용 | 상태 |
|---|---|---|
| Lakebase Postgres 전체 | 관리형 Postgres, Unity Catalog 통합 | 문서에 상태 라벨 없음 (Autoscaling 프로젝트 기준) |
| 동기화 테이블(Synced Table) | Unity Catalog 테이블 → Lakebase | 문서에 "generally available"로 명시 (LTAP Direct Writes는 Beta) |
| 변경 데이터 피드(Change Data Feed, CDF) | Lakebase 테이블 변경 → Unity Catalog Delta | Public Preview |
| 논리 복제(Logical replication) | Lakebase ↔ 외부 Postgres | 문서에 상태 라벨 없음 |
| Databricks Apps 연동 | 앱에 Lakebase 리소스 바인딩 | 문서에 상태 라벨 없음 |

> **참고** 상태 라벨은 공식 문서 페이지에 적힌 표기를 그대로 옮겼습니다. 라벨이 없는 기능은 "문서에 상태 라벨 없음"으로 표기했으며, GA라고 추정하지 않습니다. 배포 전에 대상 워크스페이스의 Preview 메뉴와 릴리즈 노트를 함께 확인하십시오.

## 1. 왜 필요한가

### 이전 방식의 한계

레이크하우스는 분석과 배치 처리에 강하지만, 애플리케이션이 초 단위 이하로 한 행씩 읽고 쓰는 **트랜잭션(OLTP) 워크로드** 에는 맞지 않습니다. 실무에서는 보통 다음 구조가 만들어집니다.

- 애플리케이션 DB(Postgres, MySQL 등)를 따로 운영합니다.
- 변경 데이터를 ETL이나 CDC 파이프라인으로 레이크하우스에 복사합니다.
- 반대로 분석 결과를 다시 애플리케이션 DB에 적재합니다(역방향 동기화).

이 구조에서는 다음 문제가 생깁니다.

| 문제 | 설명 |
|---|---|
| 데이터 복제가 여러 벌 | 같은 데이터가 운영 DB, 레이크하우스, 중간 적재 경로에 흩어집니다. |
| 지연과 정합성 | 파이프라인 지연 때문에 애플리케이션과 분석 결과가 서로 다른 시점을 봅니다. |
| 권한 체계 이원화 | 운영 DB의 권한과 Unity Catalog의 권한을 따로 관리해야 합니다. |
| 운영 부담 | 두 시스템의 백업, 복구, 버전 관리, 사이징을 따로 해야 합니다. |

### Lakebase가 해결하는 것

Lakebase는 Postgres를 레이크하우스 플랫폼 안으로 가져옵니다. 문서가 제시하는 사용 사례는 다음과 같습니다.

- 저지연 애플리케이션 구축
- 레이크하우스의 Unity Catalog 테이블을 애플리케이션에 제공(동기화 테이블)
- Postgres의 변경 내역을 Delta 테이블로 저장(CDF)
- ML 워크로드의 온라인 피처 스토어, 에이전트 상태 저장소 등 AI/ML 워크로드

> **참고** 문서가 "Lakebase Postgres"와 "Lakebase" 명칭을 함께 씁니다. 이 장은 문서 표기를 따라 "Lakebase" 또는 "Lakebase Postgres"로 씁니다.

## 2. 어떻게 동작하는가

### 구성 요소

문서의 Core concepts 설명을 기준으로 정리합니다.

| 구성 요소 | 역할 | 주의 |
|---|---|---|
| 프로젝트(Project) | 최상위 컨테이너. Databricks 워크스페이스에 속하며 하나 이상의 브랜치를 가짐 | 프로젝트 단위로 기록 보존 기간(History window)과 컴퓨트 기본값을 설정 |
| 브랜치(Branch) | Git 브랜치와 비슷하게 동작하는 데이터 분기 | 새 브랜치는 부모의 스키마와 데이터를 상속 |
| 컴퓨트(Compute) / 엔드포인트(Endpoint) | Postgres를 실행하는 가상 컴퓨팅 자원. 애플리케이션이 접속하는 안정적인 주소 | 브랜치마다 읽기-쓰기 기본 컴퓨트 1개, 읽기 전용 복제본(Read replica) 추가 가능 |
| 데이터베이스(Database) | 스키마, 테이블, 뷰, 함수, 인덱스의 컨테이너 | 기본 데이터베이스 이름은 `databricks_postgres` |
| 역할(Role) | Postgres 롤. 데이터베이스 접근의 주체 | 프로젝트 생성 시 소유자 Databricks 아이디에 대한 역할이 자동 생성 |
| 카탈로그(Catalog) | Lakebase 데이터베이스를 Unity Catalog에 등록한 것 | 별도 카탈로그 유형으로 등록 (연결 페이지에서 다룸) |

Azure 문서는 프로젝트 구조를 같은 방식으로 설명합니다. 프로젝트는 브랜치를 포함하고, 각 브랜치는 컴퓨트, 역할, 데이터베이스를 가집니다.

### 스토리지와 컴퓨트 분리

공식 문서는 Lakebase 아키텍처가 **상태가 없는(stateless) Postgres 컴퓨트** 와 **내구성 있는 스토리지 계층** 을 분리한다고 설명합니다. 스토리지 계층은 세이프키퍼(safekeeper), 페이지서버(pageserver), 클라우드 오브젝트 스토리지로 구성됩니다. 스토리지는 영역 중복(zone-redundant)이며, 컴퓨트가 실행 중이든, 일시 중지되었든, 장애 조치 중이든 데이터는 유지됩니다.

이 분리의 결과는 다음과 같습니다.

- 컴퓨트 크기는 워크로드에 따라 바꿀 수 있고, 데이터는 그대로 둡니다.
- 컴퓨트가 멈춰도 데이터는 남아 있으므로 스케일 투 제로(Scale to zero)가 가능합니다.
- 컴퓨트 교체나 재시작이 데이터 손실로 이어지지 않습니다.

> **주의** 문서가 "stateless"라고 설명하는 것은 Postgres 컴퓨트 자체의 상태 보관 방식입니다. 컴퓨트를 재시작하면 연결은 끊어지므로, 애플리케이션은 재연결 로직을 가져야 합니다(연결 페이지 참조).

### 브랜칭(Branching)

브랜치는 **copy-on-write** 방식으로 만들어집니다. 공식 문서 설명은 다음과 같습니다.

- 새 브랜치는 부모의 스키마와 데이터를 상속하고 스토리지를 공유합니다.
- 데이터가 바뀔 때만 변경분이 별도로 저장됩니다.
- 브랜치는 즉시 만들어지며, 데이터베이스 크기는 생성 시간에 영향을 주지 않습니다.
- 루트 브랜치(root branch)를 제외한 모든 브랜치는 부모를 가집니다.
- 자식 브랜치의 변경은 부모에 영향을 주지 않으며, 부모의 변경도 자식에 자동으로 반영되지 않습니다.
- 역할과 데이터베이스 상태도 브랜치마다 격리됩니다. 한 브랜치에서 만든 역할, 적용한 GRANT/REVOKE, 바꾼 역할 속성은 다른 브랜치에 영향을 주지 않습니다.
- 리셋(Reset)은 자식을 부모의 현재 상태로 맞추는 단방향 작업입니다. 연결 정보는 그대로 유지됩니다.

| 브랜치 종류 | 설명 | 과금 (문서 기준) |
|---|---|---|
| 만료 설정 브랜치 | 기간이 지나면 만료되는 브랜치 | 브랜치에서 바뀐 데이터만 과금 |
| 영구 브랜치 (만료 없음) | 만료되지 않는 브랜치 | 데이터 전체 크기로 과금 |

> **참고** 브랜치 과금 설명은 Lakebase 브랜치 문서의 원문입니다. 과금 단위의 단가는 이 장에서 다루지 않습니다(베스트 프랙티스와 비용 페이지 참조).

### 포인트인타임 복구 (Point-in-time restore)

루트 브랜치에 대해 기록 보존 기간(History window) 내의 임의 시점으로 복구할 수 있습니다.

- 보존 기간은 2일부터 30일까지 설정할 수 있으며, 기본값은 7일입니다.
- 보존 기간 설정은 프로젝트의 모든 브랜치에 적용됩니다.
- 보존 기간을 늘리면 스토리지가 늘어납니다.
- 복구는 기존 브랜치를 제자리에서 바꾸지 않고, **새 루트 브랜치** 를 만듭니다. 원래 브랜치와 연결은 영향을 받지 않습니다.

복구 방법과 세부 사항은 [트레이드오프](#4-트레이드오프)와 [주의사항](#5-주의사항)에서 다룹니다.

## 3. 어떻게 쓰는가

### 프로젝트 생성 (UI 흐름)

문서의 Get started 절차는 다음과 같습니다.

1. 앱 스위처에서 **Lakebase Postgres** 앱을 엽니다.
2. **Autoscaling** 을 선택해 Lakebase UI로 들어갑니다.
3. **New project** 를 클릭하고 이름과 Postgres 버전을 고릅니다.

생성 직후 기본으로 만들어지는 리소스는 다음과 같습니다.

| 리소스 | 기본값 |
|---|---|
| 브랜치 | `production` (기본 브랜치) |
| 컴퓨트 | `production` 브랜치의 읽기-쓰기 컴퓨트, 스케일 투 제로 활성, 비활성 24시간 후 일시 중지 |
| 데이터베이스 | `databricks_postgres` |
| 역할 | 생성한 사용자의 Databricks 아이디에 대한 Postgres 역할 |
| 리전 | 워크스페이스 리전으로 자동 설정(변경 불가) |

> **참고** Azure 문서의 프로젝트 생성 표는 `production` 브랜치 컴퓨트를 8–16 CU, HA 비활성, 오토스케일링 활성으로 적습니다. 같은 Azure 문서의 컴퓨트 기본값 절은 2↔4 CU 범위를 적습니다. 두 값이 서로 다르므로 실제 값은 워크스페이스에서 확인하십시오.

### 연결 확인 (psql)

Get started 페이지가 제시하는 연결 예시는 다음과 같습니다. 실제 값은 Lakebase UI의 **Connect** 대화 상자에서 복사합니다.

```bash
psql 'postgresql://user@example.com@ep-abc-123.databricks.com/databricks_postgres?sslmode=require'
```

> **주의** 위 예시의 `ep-abc-123.databricks.com`은 문서의 예시 호스트입니다. 실제 엔드포인트 호스트 이름과 인증 방식(토큰, 비밀번호)은 [연결과 인증](connect-and-auth.md)에서 설명합니다.

### 프로젝트 한도 (AWS 문서 기준)

| 항목 | 한도 |
|---|---|
| 동시 활성 컴퓨트 | 20 (기본 브랜치 제외) |
| 브랜치당 읽기 복제본 | 6 |
| 프로젝트당 브랜치 | 500 |
| 브랜치당 Postgres 역할 | 500 |
| 브랜치당 Postgres 데이터베이스 | 500 |
| 워크스페이스당 프로젝트 | 1000 |
| 보호 브랜치 | 1 |
| 루트 브랜치 | 3 |
| 수동 스냅샷 | 10 |
| 기록 보존 기간 최대 | 30일 |
| 스케일 투 제로 시간 | 최소 60초, 최대 7일 |
| 데이터베이스 스토리지 쿼터 (브랜치당) | 요청으로 조정 가능 |

## 4. 트레이드오프

### 언제 Lakebase가 맞는가

Lakebase는 **애플리케이션의 트랜잭션 저장소** 와 **레이크하우스 데이터의 서빙 계층** 이 필요할 때 적합합니다. 예를 들어 다음 경우입니다.

- 사용자 요청마다 행을 읽고 쓰는 웹·모바일 백엔드
- 분석 테이블의 결과를 애플리케이션이 저지연으로 조회해야 하는 경우(동기화 테이블)
- 에이전트나 앱의 상태 저장

### 언제 쓰지 않는가

| 상황 | 이유 | 대안 |
|---|---|---|
| 대량 스캔·집계 분석 | Postgres 엔진이 실행하므로 OLTP 성능에 영향 | Databricks SQL 웨어하우스 또는 레이크하우스 테이블 |
| Postgres 기능이 아닌 다른 DB 엔진이 필요 | Lakebase는 Postgres 호환 | 해당 엔진의 관리형 서비스 |
| 프로젝트 외부 네트워크에서 공용 인터넷 없이 접속 | 문서의 네트워크 설명 범위 밖 | 연결 페이지의 네트워크 항목과 IP 허용 목록 확인 |

> **주의** 문서는 쿼리를 Postgres 엔진이 실행한다는 점을 명시합니다. 따라서 대량 분석 쿼리를 Lakebase에 던지면 같은 컴퓨트에서 실행되는 애플리케이션 트래픽에 영향을 줄 수 있습니다.

### 재해 복구

Lakebase 개요 페이지는 재해 복구가 **보조 워크스페이스(Secondary Workspace)** 를 다른 리전에 두고 복제하며, 장애 조치는 **수동** 으로 수행한다고 설명합니다. 자동 장애 조치로 설명하지 않습니다. 세부 절차는 재해 복구 문서에서 확인해야 합니다. 이 장에서는 개요 설명만 옮겼습니다.

## 5. 주의사항

- **상태 라벨 확인**: 기능마다 상태가 다릅니다. CDF는 Public Preview이고, 동기화 테이블 페이지는 "generally available"이라고 적으며, 논리 복제와 Apps 연동 페이지에는 상태 라벨이 없습니다. 설계 문서에는 기능별 상태를 따로 적으십시오.
- **보존 기간과 스토리지**: 기록 보존 기간을 늘리면 스토리지 비용이 늘어납니다. 필요한 기간만큼만 설정하십시오.
- **스케일 투 제로와 첫 쿼리 지연**: 유휴 상태에서 깨어나는 데 몇 초가 걸릴 수 있습니다. Apps 페이지도 같은 설명을 합니다.
- **브랜치는 데이터 격리 단위**: 개발과 운영을 같은 프로젝트의 다른 브랜치로 나누면 역할과 권한도 브랜치 단위로 분리됩니다. 리셋은 부모 → 자식 방향만 가능합니다.

## 참고 문서

- [Lakebase Postgres 개요](https://docs.databricks.com/aws/en/oltp/)
- [Lakebase Postgres 프로젝트 개요](https://docs.databricks.com/aws/en/oltp/projects/)
- [Core concepts](https://docs.databricks.com/aws/en/oltp/projects/core-concepts)
- [Get started with Lakebase Postgres](https://docs.databricks.com/aws/en/oltp/projects/get-started)
- [Manage projects (AWS)](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)
- [Manage projects (Azure)](https://learn.microsoft.com/en-us/azure/databricks/oltp/projects/manage-projects)
- [Branches](https://docs.databricks.com/aws/en/oltp/projects/branches)
- [Point-in-time restore](https://docs.databricks.com/aws/en/oltp/projects/point-in-time-restore)
- [Lakebase Change Data Feed](https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf)
- [Synced tables](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)
- [Logical replication](https://docs.databricks.com/aws/en/oltp/projects/logical-replication)
