# 10. Lakebase

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

Lakebase는 Databricks 플랫폼에 통합된 관리형 Postgres 데이터베이스입니다. 이 장은 트랜잭션 워크로드를 레이크하우스와 함께 설계하려는 데이터 엔지니어, 애플리케이션 개발자, 데이터 아키텍트를 대상으로 합니다. Lakebase의 개념과 배포 형태를 이해하고, 연결·인증, 레이크하우스와의 데이터 이동(동기화 테이블, 변경 데이터 반출), Databricks Apps 연동, 운영 비용 기준까지 실제 설정 단위로 익히는 것이 목표입니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- OLTP 워크로드를 레이크하우스와 분리해서 운영할 때의 문제와 Lakebase가 해결하는 지점을 설명합니다.
- 컴퓨트의 자동 확장(Autoscaling), 스케일 투 제로, 읽기 복제본, 고가용성(HA) 구성을 설정하고 한도를 확인합니다.
- OAuth 토큰을 Postgres 비밀번호로 사용하는 연결 방식과 토큰 만료, 연결 수명 제한을 이해하고 재발급 로직을 설계합니다.
- 동기화 테이블(Synced Table)로 Unity Catalog의 Delta 테이블을 Lakebase로 옮기는 설정과 제약을 파악합니다.
- 변경 데이터 피드(Change Data Feed, CDF)와 논리 복제(Logical replication)의 지원 범위와 상태를 구분합니다.
- Databricks Apps에 Lakebase 리소스를 바인딩하고 주입되는 환경 변수를 확인합니다.
- 브랜치, 인스턴트 복구(Instant restore), 특정 시점 브랜치, 재해 복구(Private Preview)의 차이를 구분합니다.
- 과금 구조를 문서 원문 범위에서 점검합니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [Lakebase 개요](what-is-lakebase.md) | 100 | 왜 필요한가, 구성 요소(프로젝트·브랜치·컴퓨트·데이터베이스·역할), 스토리지·컴퓨트 분리, 리전 가용성 |
| 2 | [컴퓨트와 스케일링](compute-and-scaling.md) | 300 | Autoscaling(CU, 범위 제약), 스케일 투 제로, 읽기 복제본, 고가용성(HA) |
| 3 | [브랜치와 복구](branches-and-recovery.md) | 300 | 브랜치, 인스턴트 복구, 특정 시점 브랜치, 재해 복구(Private Preview) |
| 4 | [연결과 인증](connect-and-auth.md) | 200 | OAuth 토큰을 비밀번호로 쓰는 방식, 토큰 만료, 연결 수명, 롤과 권한, 클라이언트 도구 |
| 5 | [커넥션 풀링](connection-pooling.md) | 300 | 내장 PgBouncer 풀러, 트랜잭션 모드의 제약, 풀러와 OAuth의 배타 관계 |
| 6 | [동기화 테이블](synced-tables.md) | 200 | Unity Catalog Delta를 Lakebase로 동기화, 동기화 모드, 타입 매핑, 제약 |
| 7 | [변경 데이터 반출](change-data-out.md) | 300 | CDF(Lakebase → Delta), 논리 복제(Logical replication)의 지원 범위 |
| 8 | [Databricks Apps와 함께 쓰기](apps-integration.md) | 200 | 리소스 바인딩, 주입되는 환경 변수, 서비스 프린시펄 역할 |
| 9 | [베스트 프랙티스와 비용](best-practices-and-cost.md) | 300 | 운영 설정 기준, 연결 설계, 과금 구조(문서에 명시된 범위) |
| 10 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 10개와 실무 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 연결과 인증 페이지는 동기화 테이블, Apps 페이지의 전제가 되므로 건너뛰지 않는 것을 권장합니다.

> **참고** 이전 버전 **Lakebase Provisioned** 에서 넘어온 경우: Provisioned 인스턴스는 2026년 7월에 Autoscaling 플랫폼으로 업그레이드가 완료되었다고 문서가 설명합니다. 업그레이드 과정에서 데이터, 연결 문자열, API 호출, Asset Bundle과 Terraform 구성은 보존되었다고 문서가 명시합니다. Provisioned UI는 2026년 9월 1일까지 제공되며, 이후에는 Lakebase UI에서 인스턴스를 관리하라고 안내합니다. 이 장은 Provisioned를 주제로 다루지 않습니다.

## 선수 지식

- **SQL과 Postgres 기초**: 테이블, 인덱스, 트랜잭션, 롤(Role)과 권한(GRANT)을 알고 있어야 합니다.
- **Unity Catalog 기초**: 카탈로그, 스키마, 테이블 3단계 이름과 권한 모델을 이해해야 합니다. 동기화 테이블과 CDF의 출력은 Unity Catalog 테이블입니다.
- **Delta Lake 기초**: 동기화 테이블의 원본과 CDF의 대상은 Delta 테이블입니다.
- **Databricks CLI와 SDK**: 예제는 `databricks postgres` CLI 명령과 Python SDK(`WorkspaceClient`)를 사용합니다. 기본 인증 설정이 되어 있어야 합니다.
- **Python 기초**: 연결 예제는 psycopg(v3)를 사용합니다.

## 이 장의 읽는 법

각 기능 페이지는 같은 구조를 따릅니다. 왜 필요한지, 어떻게 동작하는지, 어떻게 설정하는지, 트레이드오프, 주의사항 순서입니다. 기능마다 상태(GA, Public Preview, Beta 등)를 표기하고, 클라우드별 차이가 있으면 나누어 적습니다.

> **참고** 이 장의 사실은 모두 공식 문서 원문에서 확인한 내용입니다. 문서에 명시되지 않은 값(예: 과금 단가, 특정 기능의 상태 라벨)은 "문서에 명시 없음"으로 표기합니다. Lakebase는 프리뷰 기능이 많고 CLI·API 형태가 바뀔 수 있으므로, 실제 적용 전 각 페이지의 참고 문서 링크에서 최신 원문을 다시 확인하십시오.

> **참고** 이 장은 AWS 문서(`docs.databricks.com/aws/en/`)를 기준으로 작성했습니다. Azure 문서(`learn.microsoft.com/azure/databricks/`)에 다른 값이 있는 항목(리전 목록, 컴퓨트 기본값 등)은 해당 페이지에 따로 표기했습니다.

## 참고 문서

- [Lakebase Postgres 개요](https://docs.databricks.com/aws/en/oltp/)
- [Lakebase Postgres 프로젝트 개요](https://docs.databricks.com/aws/en/oltp/projects/)
- [Get started with Lakebase Postgres](https://docs.databricks.com/aws/en/oltp/projects/get-started)
