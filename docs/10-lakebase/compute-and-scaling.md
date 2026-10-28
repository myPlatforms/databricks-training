# 컴퓨트와 스케일링

> 기준일: 2026-10-28 · 근거: 공식 문서

Lakebase의 컴퓨트(Compute)는 브랜치의 Postgres 엔드포인트를 실행하는 자원입니다. 이 페이지는 자동 확장(Autoscaling), 스케일 투 제로(Scale to zero), 읽기 복제본(Read replica), 고가용성(High availability, HA)을 다룹니다. 모든 수치는 AWS 공식 문서 원문 기준입니다.

## 1. 왜 필요한가

애플리케이션 트래픽은 시간대에 따라 크게 달라집니다. 고정 크기 컴퓨트는 두 가지 중 하나를 골라야 합니다.

| 선택 | 문제 |
|---|---|
| 피크에 맞춘 큰 컴퓨트 | 한가한 시간에도 같은 크기를 계속 씀 |
| 평균에 맞춘 작은 컴퓨트 | 피크에 응답이 느려짐 |

Autoscaling은 최소와 최대 사이에서 부하에 맞춰 크기를 조정합니다. 스케일 투 제로는 한동안 쓰지 않는 컴퓨트를 일시 중지합니다. 읽기 복제본은 읽기 부하를 주 컴퓨트에서 분리하고, HA 구성은 장애 시 보조 컴퓨트를 씁니다.

## 2. 어떻게 동작하는가

### 2.1 Autoscaling

문서 설명은 다음과 같습니다. 최소와 최대 크기를 정하면 Lakebase가 CPU 부하, 메모리 사용, 작업 집합(working set) 크기를 보고 그 범위 안에서 크기를 조정합니다. 범위 안의 조정은 컴퓨트 재시작이나 연결 끊김 없이 일어난다고 문서가 설명합니다. 최소나 최대 값을 바꾸면 활성 연결이 잠시 끊길 수 있습니다.

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 1 CU | "each CU providing 2 GB of RAM" (RAM 2 GB) |
| Autoscaling 최대 | "Autoscaling is available for computes up to 64 CU (128 GB)." |
| 최대와 최소의 차이 | "The difference between your maximum and minimum cannot exceed 16 CU" |
| 64 CU 초과 | "For workloads requiring more than 64 CU, larger fixed-size computes are available." (고정 크기, 최대 112 CU는 Azure·일반 문서 표기) |

> **참고** 위 "112 CU" 상한은 Azure 프로젝트 문서 원문의 "Larger fixed-size computes are available up to 112 CU" 표기입니다. AWS 원문은 "larger fixed-size computes"만 쓰고 숫자를 명시하지 않습니다.

Autoscaling 페이지 자체에는 상태 라벨이 없습니다. CU 구성은 "Manage computes" 페이지를 따르며, 이 페이지에는 CLI 예시가 없습니다.

### 2.2 스케일 투 제로

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 기본 비활성 시간 (inactivity timeout) | "defaults to 24 hours" |
| 설정 범위 | "can be set between 60 seconds and 7 days" |
| 사용 가능 조건 | "Scale to zero is available for computes of 32 CU or smaller." 자동 확장의 경우 "the maximum size must be 32 CU or smaller" |
| 조건 위반 시 | 32 CU 초과 컴퓨트에서 켜면 오류가 납니다 |

**재접속 동작**: 일시 중지된 컴퓨트로 새 쿼리나 연결 요청이 오면 Lakebase가 자동으로 다시 활성화합니다. 재활성화는 "within a few hundred milliseconds"가 걸린다고 문서가 설명합니다. 문서는 애플리케이션이 이 짧은 재활성화 구간을 위해 **연결 재시도 로직**을 구현해야 한다고 권장합니다. 재활성화 후 세션 상태(임시 테이블, 프리페어드 문장, 커넥션 풀)는 초기화됩니다.

> **주의** 스케일 투 제로와 연결 풀은 함께 설계해야 합니다. 세션 상태가 초기화되므로, 풀이 오래된 연결을 들고 있으면 첫 요청에서 실패할 수 있습니다. 재시도와 연결 검증을 넣으십시오.

### 2.3 읽기 복제본 (Read replica)

문서 설명: 읽기 복제본은 주 읽기-쓰기 컴퓨트와 **같은 데이터에 대해 읽기 작업을 수행하는 독립된 읽기 전용 컴퓨트**입니다.

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 브랜치당 개수 | "You can add up to 6 read replicas per branch." |
| 추가 스토리지 비용 | "No additional storage costs." |
| 추가 방법 | Lakebase 앱에서 브랜치의 **Computes** 탭 > **Add Read Replica** |
| 자동 확장 | 읽기 복제본도 자동 확장과 스케일 투 제로의 혜택을 받는다고 문서 설명 |

> **참고** 읽기 복제본의 호스트 이름 형식과 HA 전제 조건은 AWS 원문 페이지에 명시되어 있지 않습니다. 커넥션 풀러의 읽기 전용 호스트 형식(`-ro-pooler`)은 [커넥션 풀링](connection-pooling.md) 페이지를 따릅니다.

> **주의** 동기화 테이블의 CDF 실행 위치는 주 컴퓨트입니다. 논리 복제도 읽기 복제본이 아니라 주 컴퓨트에서 실행됩니다([변경 데이터 반출](change-data-out.md) 참조).

### 2.4 고가용성 (High availability, HA)

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 컴퓨트 구성 | 총 2, 3, 4개 중 선택. "**2** (1 primary, 1 secondary)", "**3** (1 primary, 2 secondaries)", "**4** (1 primary, 3 secondaries)" |
| 배치 | "Lakebase provisions secondary compute instances in different availability zones." |
| 설정 방법 | 주 컴퓨트의 편집 창에서 **Compute type**을 **High availability**로 설정한 뒤 **Configuration** 선택 |
| 스케일 투 제로 | "Scale to zero must be disabled." |
| 상태 표시 | Computes 탭의 Status 열에 "Starting, Active" 등 |

> **주의** 보조 컴퓨트 1개와 읽기 접근을 켠 구성에서는 장애 조치 중 `-ro` 연결 문자열의 모든 읽기 트래픽이 중단된다고 문서가 경고합니다. 문서는 읽기 안정성을 위해 보조 컴퓨트를 2개 이상 두라고 권장합니다.

비용에 대해 HA 페이지는 명시가 없습니다. HA는 "RPO = 0, synchronous" 설명과 함께 재해 복구(Disaster recovery)와 구분되는 기능입니다. 재해 복구는 [브랜치와 복구](branches-and-recovery.md) 페이지를 참조하십시오.

## 3. 어떻게 쓰는가

### 3.1 설정 흐름 (UI)

1. Lakebase 앱에서 프로젝트를 열고 브랜치의 **Computes** 탭으로 갑니다.
2. 컴퓨트를 편집해 크기 범위(최소·최대 CU)를 설정합니다. 최대 32 CU 이하에서만 스케일 투 제로를 켤 수 있습니다.
3. 필요하면 **Add Read Replica**로 읽기 복제본을 추가합니다(브랜치당 최대 6개).
4. 고가용성이 필요하면 **Compute type**을 **High availability**로 바꾸고 구성을 선택합니다. 이때 스케일 투 제로는 꺼야 합니다.

> **참고** 이 페이지의 근거 문서들은 컴퓨트 설정의 CLI나 SDK 예시를 제공하지 않았습니다. 자동화가 필요하면 Postgres API 레퍼런스를 확인하십시오.

### 3.2 프로젝트 기본 컴퓨트 설정

새 프로젝트의 기본 컴퓨트 설정은 프로젝트 설정의 **Compute defaults**에서 바꿀 수 있습니다. 바꿔도 기존 컴퓨트 설정은 바뀌지 않고, 새로 만드는 주 컴퓨트와 읽기 복제본의 초기값에만 적용됩니다.

## 4. 트레이드오프

| 선택 | 장점 | 비용·제약 |
|---|---|---|
| Autoscaling | 부하에 맞춘 자동 조정 | 최대-최소 차이 16 CU 이하라는 제약. 크기 변경 시 연결이 잠시 끊길 수 있음 |
| 스케일 투 제로 | 유휴 시 자원 절감 | 재활성화 지연 (수백 ms), 세션 상태 초기화. 32 CU 이하에서만 가능 |
| 읽기 복제본 | 읽기 부하 분리, 추가 스토리지 없음 | 브랜치당 최대 6개. 복제본의 전제 조건은 원문에 명시 없음 |
| HA | 보조 컴퓨트로 장애 대응 | 스케일 투 제로 불가. 보조 컴퓨트 1개 구성에서 읽기 중단 위험 |

## 5. 주의사항

- **스케일 투 제로를 HA와 함께 쓰지 않습니다.** 문서상 HA에서는 꺼야 합니다.
- **CU 범위를 좁게 잡지 않습니다.** 최대-최소 차이가 16 CU를 넘을 수 없으므로 피크가 큰 워크로드는 최소를 조금 올려 여러 단계 확장에 맞추십시오.
- **연결 재시도를 구현합니다.** 스케일 투 제로와 크기 변경 모두 연결에 영향을 줄 수 있습니다.
- **Azure와 AWS 기본값을 구분합니다.** Azure 프로젝트 문서의 기본 컴퓨트 표기(production 8–16 CU)와 기본값 절(2↔4 CU)은 서로 다릅니다. 원문 표기가 일관되지 않으므로 실제 기본값은 워크스페이스에서 확인하십시오.

## 참고 문서

- [Autoscaling (AWS)](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [Scale to zero (AWS)](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)
- [Read replicas (AWS)](https://docs.databricks.com/aws/en/oltp/projects/read-replicas)
- [High availability (AWS)](https://docs.databricks.com/aws/en/oltp/projects/manage-high-availability)
- [Manage projects (AWS, Compute defaults 절)](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)
- [Manage projects (Azure)](https://learn.microsoft.com/en-us/azure/databricks/oltp/projects/manage-projects)
