# 클래식 컴퓨트

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

클래식 컴퓨트(Classic compute)는 올-퍼포즈(All-purpose), Job, Lakeflow 파이프라인용 자원으로, 사용자가 직접 만들고 설정하고 관리합니다. 자원은 고객 클라우드 계정에서 실행됩니다. 이 페이지는 클래식 컴퓨트를 설정할 때 가장 먼저 정하는 항목인 액세스 모드(Access mode), Databricks Runtime(DBR) 버전, 오토스케일링(Autoscaling), 자동 종료(Auto termination)를 다룹니다. 풀과 정책은 [인스턴스 풀과 컴퓨트 정책](pools-and-policies.md) 페이지에서 다룹니다.

## 1. 왜 필요한가

서버리스가 모든 워크로드에 맞지는 않습니다. 다음 경우에는 클래식 컴퓨트가 필요합니다.

- 서버리스 제약에 걸리는 기능을 써야 할 때 (RDD, R, GPU, 머신러닝 런타임, 컴퓨트 범위 라이브러리, init 스크립트)
- 노드 유형, 런타임 버전, 네트워크를 직접 정해야 할 때
- 여러 사용자가 같은 자원을 공유하면서도 데이터 격리가 필요할 때 (Standard 모드)
- 한 사용자나 그룹이 독점해서 쓰는 자원이 필요할 때 (Dedicated 모드)

클래식 컴퓨트는 설정 자유도가 높은 대신 관리 책임도 사용자에게 있습니다. 액세스 모드와 런타임 버전을 잘못 고르면 데이터 접근이 막히거나 기능이 빠질 수 있으므로, 설정 순서가 중요합니다.

## 2. 어떻게 동작하는가

### 2.1 액세스 모드 (Access mode)

공식 문서는 세 가지 선택지를 제시합니다. 문서 표기는 **Auto**, **Standard**, **Dedicated** 입니다.

| 액세스 모드 | 문서 설명 (원문 인용) | 지원 언어 (문서 기준) |
|---|---|---|
| Standard | "Can be used by multiple users with data isolation among users." | Python, SQL, Scala |
| Dedicated | "Can be assigned to and used by a single user or group." | Python, SQL, Scala, R |
| Auto | 기본값. Standard를 고르되, ML 런타임, GPU 인스턴스 유형, 또는 DBR 14.3 미만을 고르면 Dedicated를 씁니다 | 선택된 모드를 따름 |

> **참고** 예전 자료의 "No isolation shared" 같은 이름은 현재 문서의 액세스 모드 표기와 다릅니다. 이 장은 현재 문서 표기(Standard, Dedicated, Auto)를 씁니다.

#### Standard 모드

공식 문서는 "Standard compute is recommended for most workloads"라고 설명합니다. 여러 사용자가 한 자원에서 동시에 작업을 돌리고, 사용자 코드는 하위 수준 자원과 분리된 상태로 실행됩니다. 문서가 Standard 모드의 Scala 지원 조건으로 DBR 13.3 LTS 이상과 Unity Catalog를 명시합니다.

Standard 모드의 제약은 Standard 제약 페이지에 정리되어 있으며, 문서 요약은 다음과 같습니다.

- GPU 컴퓨트 없음
- Databricks Runtime for ML 없음
- Spark-submit 태스크 없음
- RDD API 없음
- Hive UDF 없음
- 소켓 스트리밍 소스 없음
- IMDS 접근 없음
- DBR 19 이상에서 일부 Spark 설정 속성 제한

R은 지원하지 않습니다. 권한 상승이 필요한 머신 접근, RDD API, 분산 머신러닝, GPU, R이 필요하면 Dedicated를 쓰라고 문서가 안내합니다.

#### Dedicated 모드

Dedicated 모드는 한 사용자나 그룹에게 할당되며, 할당된 사용자나 그룹만 붙을 수 있습니다. 문서에 따르면 Dedicated 컴퓨트를 사용자에게 할당할 수 있는 주체는 워크스페이스 관리자입니다.

Dedicated 모드의 제약 요점은 다음과 같습니다.

| 항목 | 문서 내용 |
|---|---|
| 세밀한 접근 제어(Fine-grained access control) | DBR 15.4 LTS 이상과 서버리스 컴퓨트 활성화가 필요합니다 |
| 그룹 할당 | Public Preview |
| 주된 사용 목적 | RDD API, GPU 인스턴스, R 언어, 권한 상승이 필요한 머신 접근 |

> **주의** 문서의 Dedicated 페이지는 Unity Catalog 지원 범위를 따로 명시하지 않습니다. 세부 기능은 Dedicated 제약 페이지에서 확인해야 합니다. 이 장에서는 확인하지 못했습니다.

#### Auto 모드

Auto는 기본값입니다. 실제로는 다음 조건에서 Dedicated가 선택됩니다.

- ML 런타임을 고른 경우
- GPU 인스턴스 유형을 고른 경우
- Databricks Runtime이 14.3 미만인 경우

그 밖의 경우에는 Standard가 선택됩니다. 액세스 모드를 명시적으로 정하지 않으면 워크로드가 의도와 다른 모드에서 돌 수 있으므로, 운영 설정에서는 Auto보다 명시적인 선택을 권합니다.

### 2.2 의존성 모드 (Dependency mode, Beta)

문서는 Standard 액세스 모드 컴퓨트에서 DBR 19 이상일 때 **의존성 모드(Dependency mode)** 를 Beta로 표기합니다.

| 옵션 | 설명 (문서 요약) |
|---|---|
| Auto (기본) | 환경(Environments)으로 워크로드별 의존성을 관리합니다 |
| Manual | 클러스터 라이브러리 방식. 컴퓨트 범위 라이브러리, init 스크립트, Docker를 씁니다 |

문서는 Cluster libraries 방식을 "The classic behavior"라고 부릅니다.

### 2.3 Databricks Runtime(DBR) 버전

공식 Runtime 릴리즈 노트 페이지 기준으로 2026-10-28 현재 다음 버전이 보입니다.

| Runtime | Apache Spark | 출시일 | 지원 종료 |
|---|---|---|---|
| 19 | 4.2.0 | 2026-06-15 | LTS 전환 시 결정 |
| 18 LTS | 4.1.0 | 2026-06-10 | 2029-06-10 |
| 18.2 | 4.1.0 | 2026-05-05 | 2026-11-05 |
| 17.3 LTS | 4.0.0 | 2025-10-22 | 2028-10-22 |
| 16.4 LTS | 3.5.2 | 2025-05-09 | 2028-05-09 |
| 15.4 LTS | 3.5.0 | 2024-08-19 | 2027-08-19 |
| 14.3 LTS | 3.5.0 | 2024-02-01 | 2027-02-01 |

> **참고** 위 표는 Runtime 릴리즈 노트 페이지의 현재 표입니다. 페이지가 자주 갱신되므로 적용 전에 원문에서 지원 종료일을 다시 확인하십시오.

문서의 용도별 권장은 다음과 같습니다.

| 용도 | 문서 권장 |
|---|---|
| 올-퍼포즈 컴퓨트 (대화형 개발) | 가장 최신 버전 |
| 운영 Job 컴퓨트 | LTS 버전 고려 |
| 데이터 사이언스, 머신러닝 | Runtime ML 버전 고려 |

Photon은 DBR 9.1 LTS 이상에서 기본으로 켜져 있다고 문서가 설명합니다. Photon의 세부 내용은 [Photon](photon.md) 페이지에서 다룹니다.

### 2.4 오토스케일링 (Autoscaling)

클래식 컴퓨트의 워커 수는 두 방식 중 하나로 정합니다.

- **Enable autoscaling** 을 체크하면 최소(Min)와 최대(Max) 워커 수를 입력합니다.
- 체크하지 않으면 **Workers** 에 고정 워커 수를 입력합니다.

API에서는 `autoscale` 객체의 `min_workers`와 `max_workers`를 씁니다.

```python
# Clusters API로 클래식 컴퓨트 생성 시 오토스케일링 범위를 지정하는 예 (필드 구조)
# 실제 실행 전에 워크스페이스 인증과 node_type_id 등 필수 값을 채우십시오.
cluster_spec = {
    "cluster_name": "etl-autoscale-example",
    "spark_version": "<DBR_VERSION>",  # 사용 가능한 버전 문자열은 워크스페이스에서 확인
    "autoscale": {
        "min_workers": 2,
        "max_workers": 8,
    },
    "spark_conf": {},
}
```

오토스케일링 동작은 플랜과 컴퓨트 유형에 따라 다릅니다.

| 구분 | 문서 설명 (요약) |
|---|---|
| 최적화 오토스케일링 (Optimized) | Premium 플랜 이상. Job 컴퓨트는 40초, 올-퍼포즈 컴퓨트는 150초 동안 활용도가 낮으면 축소 |
| 표준 오토스케일링 (Standard) | Standard 플랜 워크스페이스. 노드 8개를 추가하는 방식으로 시작하고, 노드의 90%가 10분 동안 바쁘지 않으면 축소 |

> **주의** 오토스케일링은 `spark-submit` 작업에 쓸 수 없습니다. 또한 Databricks 오토스케일링을 쓰는 컴퓨트에 Spark 동적 할당(`spark.dynamicAllocation.enabled`)을 켜면 안 됩니다. 두 기능이 서로 충돌합니다.

### 2.5 자동 종료 (Auto termination)

자동 종료는 고급 성능(Advanced performance) 섹션에서 비활성 시간을 분 단위로 설정합니다. 문서는 기본값을 명시하지 않습니다. 운영 컴퓨트는 명시적인 값을 주는 것이 안전합니다.

### 2.6 Lakeguard 격리

Standard 모드는 Lakeguard가 사용자 워크로드를 격리한다고 문서가 설명합니다. Lakeguard의 세부 구조는 이 장의 범위를 넘으므로 공식 Lakeguard 페이지를 참고하십시오.

## 3. 어떻게 쓰는가 (UI와 API)

UI에서 클래식 컴퓨트를 설정할 때 확인하는 항목은 다음 순서입니다. 화면의 버튼 이름은 워크스페이스 버전에 따라 다를 수 있으므로 문서 표기 기준으로만 적었습니다.

1. 컴퓨트 정책(Policy)을 고릅니다. 권한이 없으면 부여받은 정책만 보입니다.
2. **Access mode** 에서 Standard, Dedicated, Auto 중 하나를 고릅니다.
3. Databricks Runtime 버전을 고릅니다. 용도에 따라 최신 버전, LTS, ML 버전을 고릅니다.
4. **Enable autoscaling** 을 체크하고 Min과 Max 워커 수를 입력합니다.
5. **Advanced performance** 섹션에서 자동 종료 시간을 입력합니다.

Databricks CLI에서 클러스터 정보를 조회하는 예는 다음과 같습니다.

```bash
# 클러스터 목록을 조회합니다. 프로필은 ~/.databrickscfg의 값을 씁니다.
databricks clusters list --profile <PROFILE_NAME>
```

> **참고** 위 `cluster_spec`은 필드 구조를 보여 주기 위한 예입니다. `node_type_id`와 `autotermination_minutes`는 Clusters API 레퍼런스의 필드이지만, 이 장에서 생성 요청 본문 전체를 원문으로 대조하지 못했습니다. 실제 생성 전에 [Clusters API 레퍼런스](https://docs.databricks.com/api/workspace/clusters/create)에서 필드 이름을 확인하십시오.

## 4. 트레이드오프

| 항목 | 장점 | 한계 |
|---|---|---|
| 설정 자유도 | 노드, 런타임, 라이브러리, init 스크립트 모두 설정 | 설정이 많아 잘못 고르기 쉽습니다 |
| 기능 범위 | 서버리스 제약이 걸리는 기능까지 가능 | Standard 모드는 GPU, ML 런타임, RDD 등에 제약이 있습니다 |
| 시작 시간 | 풀(Pool)로 줄일 수 있음 | 풀 없이 만들면 클러스터 시작 시간이 필요합니다 |
| 비용 구조 | 클라우드 인스턴스 요금을 세밀하게 통제 | DBU 외에 인스턴스 요금이 따로 나옵니다 (비용 구조 페이지 참고) |
| 관리 부담 | 제어권이 많음 | 런타임 패치와 정책 관리를 직접 해야 합니다 |

## 5. 주의사항

- **액세스 모드를 명시적으로 고르십시오.** Auto 기본값은 조건에 따라 Dedicated로 바뀝니다.
- **Dedicated는 한 사용자 또는 그룹에 묶입니다.** 공유 대상이 바뀌면 컴퓨트 권한을 다시 설정해야 합니다.
- **Runtime 지원 종료일을 확인하십시오.** 지원이 끝난 버전은 보안 패치를 받지 못합니다. 운영 Job은 LTS 중 지원 기간이 남은 버전을 고르는 것이 일반적입니다.
- **오토스케일링과 Spark 동적 할당을 동시에 켜지 마십시오.** 문서가 명시한 충돌입니다.
- **자동 종료를 설정하십시오.** 설정하지 않으면 사용하지 않는 컴퓨트에 비용이 계속 나갑니다.

## 참고 문서

- [Compute 구성 (AWS)](https://docs.databricks.com/aws/en/compute/configure)
- [Classic compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/use-compute)
- [Standard compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/standard-overview)
- [Dedicated compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/dedicated-overview)
- [Access mode 제약 (AWS)](https://docs.databricks.com/aws/en/compute/access-mode-limitations)
- [Databricks Runtime 릴리즈 노트 (AWS)](https://docs.databricks.com/aws/en/release-notes/runtime/)
- [Clusters API 레퍼런스](https://docs.databricks.com/api/workspace/clusters/create)
