# 배포 형태 비교: Autoscaling과 Provisioned

> 기준일: 2026-10-28 · 근거: 공식 문서

Lakebase에는 문서상 두 가지 배포 형태가 있습니다. 현재 문서 표기는 **Autoscaling**(프로젝트 단위)과 **Provisioned**(인스턴스 단위, 원래 버전)입니다. 두 형태는 같은 Lakebase 플랫폼 위에서 동작하며, Provisioned 인스턴스는 2026년 7월에 Autoscaling 플랫폼으로 업그레이드되었습니다.

## 1. 왜 두 형태를 구분하는가

Provisioned는 고정 크기 컴퓨트를 사람이 직접 조정하는 방식이었습니다. 워크로드가 변하면 수동으로 크기를 바꿔야 했습니다. Autoscaling은 최소·최대 범위 안에서 컴퓨트 크기를 자동으로 조정하고, 스케일 투 제로, 브랜칭, 포인트인타임 복구를 제공합니다.

문서는 Provisioned에서 Autoscaling으로 가는 방향을 명확히 보여줍니다. Provisioned 페이지는 다음과 같이 설명합니다.

- Provisioned는 Lakebase의 **원래 버전(original version)** 입니다.
- 기존 Provisioned 인스턴스는 모두 Autoscaling 플랫폼으로 업그레이드되었습니다. 이 업그레이드는 2026년 7월에 완료되었다고 적혀 있습니다.
- 업그레이드 과정에서 데이터, 연결 문자열, API 호출, Asset Bundle과 Terraform 구성은 보존되었다고 적혀 있습니다.
- 앞으로의 관리는 Postgres API, CLI, Lakebase UI를 사용하도록 안내합니다.

## 2. 두 형태의 차이

| 항목 | Autoscaling (프로젝트) | Provisioned (인스턴스) |
|---|---|---|
| 기본 구조 | 프로젝트 → 브랜치 → 컴퓨트·데이터베이스·역할 | 단일 인스턴스 (페이지에 구조 상세 없음) |
| 컴퓨트 크기 조정 | 최소·최대 범위 안에서 자동 조정 | 고정 크기를 수동 조정 |
| 스케일 투 제로 | 지원 (AWS 문서: 최대 크기 32 CU 이하에서만) | 문서에 명시 없음 |
| 브랜칭 | 지원 | 문서에 명시 없음 |
| 포인트인타임 복구 | 지원 (기록 보존 기간 2–30일, 기본 7일) | 문서에 명시 없음 |
| 관리 표면 | Lakebase UI, Postgres API(`databricks postgres` CLI, SDK) | `databricks database` CLI 등 인스턴스 API(기존 인스턴스 유지 목적) |
| 신규 생성 | 권장 경로 | 문서에 신규 생성 가능 여부 명시 없음 |

> **참고** Provisioned 페이지가 적은 Provisioned UI의 제공 기간은 "September 1, 2026까지 유지"입니다. 이 날짜는 기준일(2026-10-28) 이전이므로, 이후에는 Lakebase UI에서 관리하도록 안내합니다. 문서가 Provisioned 신규 생성을 막았다고 적지는 않습니다.

## 3. 용량 단위 (CU) 비교

Autoscaling 문서는 1 CU가 **2 GB RAM** 을 제공한다고 명시합니다. Provisioned 페이지는 CU 크기나 GB당 단위를 설명하지 않습니다.

| 컴퓨트 크기 | RAM (Azure 문서 표) |
|---|---|
| 0.5 CU | 1 GB |
| 1 CU | 2 GB |
| 4 CU | 8 GB |
| 8 CU | 16 GB |
| 16 CU | 32 GB |
| 32 CU | 64 GB |
| 64 CU | 128 GB |
| 112 CU | 224 GB |

- Autoscaling은 최대 64 CU까지 지원합니다.
- 64 CU보다 큰 고정 크기 컴퓨트는 최대 112 CU까지 제공된다고 문서가 설명합니다.
- AWS Autoscaling 페이지는 "up to 64 CU (128 GB)"를, "max - min ≤ 16 CU"를 명시합니다.

> **주의** 과거 자료에서 Provisioned를 "CU당 16 GB"로 서술한 내용이 있습니다. 공식 문서의 현재 원문에서는 이 수치를 확인할 수 없었습니다. Autoscaling 기준은 "1 CU = 2 GB"입니다. 두 형태의 사이징을 비교할 때는 이 차이를 혼동하지 마십시오.

## 4. 어떻게 선택하는가

| 상황 | 권장 | 근거 |
|---|---|---|
| 새 애플리케이션을 시작하는 경우 | Autoscaling | 문서가 Lakebase의 현재 형태로 설명하며, 브랜칭·복구·스케일 투 제로가 모두 여기에 있음 |
| 워크로드 변동이 큰 경우 | Autoscaling | 최소·최대 범위 안에서 자동 조정 |
| 개발·테스트 환경을 운영과 분리해야 하는 경우 | Autoscaling | 브랜치 단위로 역할·데이터 격리 |
| 기존 Provisioned 인스턴스를 이미 운영하는 경우 | 현재 상태를 유지하고 Lakebase UI·Postgres API로 관리 전환 | 업그레이드로 데이터·연결 문자열 보존 |
| 64 CU 초과 고정 크기가 필요한 경우 | 문서 기준 고정 크기 컴퓨트 검토 | 문서가 최대 112 CU 고정 크기를 언급 |

> **참고** 기존 Provisioned 인스턴스의 업그레이드 후 연결 문자열이 보존된다는 점은 문서가 명시합니다. 그래도 운영 자동화(Terraform, Asset Bundle)가 있다면 적용 후 설정 값을 다시 확인하십시오.

## 5. 트레이드오프

### Autoscaling의 제약

- 최소·최대 범위 차이는 16 CU를 넘을 수 없습니다(AWS 문서).
- 스케일 투 제로는 최대 크기가 32 CU 이하일 때만 사용할 수 있습니다(AWS 문서).
- 고가용성(HA) 구성에서 보조(Secondary) 컴퓨트는 주 컴퓨트의 현재 CU보다 작게 줄일 수 없고, 스케일 투 제로도 사용할 수 없습니다(AWS 문서).
- 크기를 바꾸면 활성 연결이 잠시 끊길 수 있습니다(AWS 문서: "may cause a brief interruption to active connections").

### Provisioned의 제약

- 크기 변화에 사람이 개입해야 합니다.
- 브랜칭과 포인트인타임 복구 같은 Autoscaling 기능은 이 페이지에서 설명하지 않습니다.

## 6. 주의사항

- **형태 용어를 혼용하지 않습니다.** "Lakebase Provisioned"와 "Lakebase Autoscaling"은 관리 표면과 기능이 다릅니다. 인증 방식도 다르므로(연결 페이지 참조), 설계 문서에 어떤 형태를 쓰는지 명시하십시오.
- **상태 라벨을 추정하지 않습니다.** Autoscaling 프로젝트 페이지와 Provisioned 페이지에는 GA 또는 Public Preview 라벨이 없습니다. 상태는 대상 워크스페이스의 Preview 메뉴와 릴리즈 노트에서 확인하십시오.
- **클라우드별 리전이 다릅니다.** AWS 문서는 12개 리전을, Azure 문서는 24개 리전을 나열합니다. 리전 목록은 [클라우드별 가용성](#7-클라우드별-가용성)에서 비교합니다.

## 7. 클라우드별 가용성

### 리전 목록 (문서 원문 기준)

| 클라우드 | 문서가 나열한 리전 |
|---|---|
| AWS | us-east-1, us-east-2, us-west-2, ca-central-1, sa-east-1, eu-central-1, eu-west-1, eu-west-2, ap-south-1, ap-southeast-1, ap-southeast-2, ap-northeast-1 (12개) |
| Azure | eastus, eastus2, centralus, northcentralus, southcentralus, westus, westus2, westcentralus, canadacentral, brazilsouth, northeurope, uksouth, westeurope, francecentral, germanywestcentral, swedencentral, uaenorth, southafricanorth, australiaeast, centralindia, southeastasia, eastasia, japaneast, koreacentral (24개) |

> **주의** AWS 리전 목록에는 서울 리전(ap-northeast-2)이 없습니다. Azure 목록에는 `koreacentral`이 있습니다. 한국 리전에서 사용하려면 워크스페이스 리전과 기능 지원 여부를 먼저 확인하십시오. 이 장은 리전 가용성을 추정하지 않습니다.

> **참고** 프로젝트는 워크스페이스 리전에 생성되며, 리전은 생성 후 바꿀 수 없다고 문서에 적혀 있습니다.

### 기능별 클라우드 차이 (문서에 명시된 범위)

| 기능 | AWS | Azure |
|---|---|---|
| Autoscaling 프로젝트 | 문서 제공 | 문서 제공 |
| Postgres 버전 | 16, 17, 18 (CDF·LTAP 조건으로 확인) | 16, 17, 18, 기본값 17 |
| 동기화 테이블 | 문서 제공 | 문서 제공 |
| CDF | Public Preview (AWS 문서 기준) | 이 장에서 확인하지 않음 |
| 논리 복제 | 문서 제공 | 문서 제공 |
| GCP | 이 장에서 다루지 않음 | 이 장에서 다루지 않음 |

## 참고 문서

- [Lakebase Postgres 개요](https://docs.databricks.com/aws/en/oltp/projects/)
- [Autoscaling (AWS)](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [Lakebase Provisioned (AWS)](https://docs.databricks.com/aws/en/oltp/instances/)
- [Manage projects (AWS)](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)
- [Manage projects (Azure)](https://learn.microsoft.com/en-us/azure/databricks/oltp/projects/manage-projects)
- [Point-in-time restore](https://docs.databricks.com/aws/en/oltp/projects/point-in-time-restore)
- [Logical replication](https://docs.databricks.com/aws/en/oltp/projects/logical-replication)
