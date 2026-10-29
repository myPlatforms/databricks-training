# 컴퓨트와 스케일링

> 기준일: 2026-10-29 · 근거: 공식 문서 · 수준: 300

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
| 80 CU 이상 | 고정 크기 전용 (Manage computes 페이지: "Computes of 80 CU or more are fixed-size only.") |

AWS 원문의 "Manage computes" 페이지는 64 CU와 80 CU 사이 구간을 따로 설명하지 않습니다. 실제 설정 가능한 값은 콘솔의 슬라이더가 강제합니다.

> **참고** Azure 프로젝트 문서에는 고정 크기 컴퓨트 상한으로 112 CU 표기가 있습니다. AWS 원문은 이 숫자를 명시하지 않으므로 이 페이지에서는 쓰지 않습니다.

### 2.2 스케일 투 제로

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 기본 비활성 시간 (inactivity timeout) | "defaults to 24 hours" |
| 설정 범위 | "can be set between 60 seconds and 7 days" |
| 사용 가능 조건 | "Scale to zero is available for computes of 32 CU or smaller." 자동 확장의 경우 최대 크기가 32 CU 이하여야 함 |
| 조건 위반 시 | 32 CU 초과 컴퓨트에서 켜려고 하면 오류 |
| 기본 설정 | `production` 브랜치는 스케일 투 제로가 켜져 있고 비활성 시간 24시간 |

**재접속 동작**: 일시 중지된 컴퓨트로 새 쿼리나 연결 요청이 오면 Lakebase가 자동으로 다시 활성화합니다. 재활성화는 "within a few hundred milliseconds"가 걸린다고 문서가 설명합니다. 문서는 애플리케이션이 이 짧은 재활성화 구간을 위해 **연결 재시도 로직** 을 구현해야 한다고 권장합니다.

재활성화 때 다음 상태가 초기화됩니다.

재활성화 후에도 유지되는 것은 연결 문자열과 자격 증명(일시 중지 중에도 유효), 누적 통계와 플래너 통계입니다. 초기화되는 것은 캐시, 임시 테이블, 프리페어드 문장, 세션 설정, 커넥션 풀, 활성 트랜잭션이며, `pg_stat_statements` 데이터도 보존되지 않습니다.

오토스케일링이 켜진 컴퓨트는 재활성화 때 최소 크기로 다시 시작합니다.

> **주의** 스케일 투 제로와 연결 풀은 함께 설계해야 합니다. 세션 상태가 초기화되므로, 풀이 오래된 연결을 들고 있으면 첫 요청에서 실패할 수 있습니다. 재시도와 연결 검증을 넣으십시오. 풀 동작은 [커넥션 풀링](connection-pooling.md)을 참고하십시오.

### 2.3 읽기 복제본 (Read replica)

문서 설명: 읽기 복제본은 주 읽기-쓰기 컴퓨트와 **같은 데이터에 대해 읽기 작업을 수행하는 독립된 읽기 전용 컴퓨트** 입니다. 주 컴퓨트와 같은 스토리지를 읽으므로 데이터 사본을 따로 만들지 않습니다.

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 브랜치당 개수 | "You can add up to 6 read replicas per branch." |
| 추가 스토리지 비용 | "No additional storage costs." |
| 복제 방식 | "asynchronous, which means they are _eventually consistent_" |
| 시작 직후 상태 | "immediately up to date when they start" |
| 지연 확인 | 복제 지연은 Metrics 대시보드에서 확인. 문서는 지연 수치를 쓰지 않음 |
| 자동 확장과 스케일 투 제로 | 복제본도 적용 가능. 복제본마다 컴퓨트 크기를 따로 정함 |

읽기 복제본은 **비동기** 입니다. 주 컴퓨트에 막 커밋된 값이 복제본에 아직 보이지 않을 수 있습니다. 방금 쓴 값을 바로 읽어야 하는 요청은 주 컴퓨트로 보내십시오.

복제본 추가 절차는 다음과 같습니다.

1. Lakebase 앱에서 브랜치를 엽니다.
2. **Computes** 탭에서 **Add Read Replica** 를 누릅니다.

읽기 복제본의 호스트 이름 형식과 HA와의 관계는 AWS 원문 페이지에 명시되어 있지 않습니다. 읽기 전용 커넥션 풀 호스트(`-ro-pooler`)는 [커넥션 풀링](connection-pooling.md) 페이지를 따릅니다.

> **주의** 동기화 테이블의 CDF 실행 위치는 주 컴퓨트입니다. 논리 복제도 읽기 복제본이 아니라 주 컴퓨트에서 실행됩니다([변경 데이터 반출](change-data-out.md) 참조).

### 2.4 고가용성 (High availability, HA)

HA 엔드포인트는 읽기-쓰기 트래픽을 받는 **주 컴퓨트(primary) 1개** 와 **보조 컴퓨트(secondary) 1~3개** 로 구성됩니다. 보조 컴퓨트는 다른 가용 영역(availability zone)에 배치됩니다. 보조 컴퓨트는 주로 장애 대기(failover standby) 역할을 하며, 읽기 접근은 선택 사항입니다.

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 컴퓨트 구성 | 총 2, 3, 4개 중 선택. "**2** (1 primary, 1 secondary)", "**3** (1 primary, 2 secondaries)", "**4** (1 primary, 3 secondaries)" |
| 배치 | "Lakebase provisions secondary compute instances in different availability zones." |
| 자동 장애 조치 | "Once all compute instances are active, the endpoint has automatic failover." |
| 장애 시 연결 | 기존 연결은 종료되고 재연결해야 함. 재시도 로직이 있으면 "within seconds"에 자동 재연결 |
| 연결 문자열 | 장애 후에도 주 연결 문자열은 바뀌지 않음 (새 주 컴퓨트로 라우팅) |
| 스케일 투 제로 | "Scale to zero must be disabled." 수동으로 모든 컴퓨트를 일시 중지하면 엔드포인트를 쓸 수 없음 |
| 보조 컴퓨트 크기 | 주 컴퓨트의 현재 CU 이상으로 확장 |

문서는 HA의 복구 목표 시점(RPO)과 동기 복제 여부를 이 페이지에서 수치로 명시하지 않습니다. 확인된 것은 "커밋된 트랜잭션은 장애 조치 후에도 보존된다"는 설명입니다. 재해 복구(Disaster recovery)는 HA와 다른 기능이며, 자세한 내용은 [브랜치와 복구](branches-and-recovery.md)를 참고하십시오.

#### 읽기 접근 옵션

보조 컴퓨트에서 읽기를 허용하려면 **Allow access to read-only compute instances** 옵션을 켭니다. 이 옵션을 켜야 `-ro` 연결 문자열이 생깁니다.

Computes 탭의 Access 열은 주 컴퓨트를 **Read/Write**, 읽기 접근을 켠 보조 컴퓨트를 **Read-only**, 끈 보조 컴퓨트를 **Disabled** 로 표시합니다.


> **주의** 보조 컴퓨트 1개와 읽기 접근을 켠 구성에서는 장애 조치 중 `-ro` 연결 문자열의 모든 읽기 트래픽이 중단된다고 문서가 경고합니다. 문서는 읽기 안정성을 위해 보조 컴퓨트를 2개 이상 두라고 권장합니다.

## 3. 어떻게 쓰는가

### 3.1 UI로 설정하기

1. Lakebase 앱에서 프로젝트를 열고 브랜치의 **Computes** 탭으로 갑니다.
2. 컴퓨트에서 **Edit** 을 눌러 슬라이더로 최소·최대 CU를 정하고 **Save** 를 누릅니다. 최대 32 CU 이하에서만 스케일 투 제로를 켤 수 있습니다.
3. 스케일 투 제로를 켜거나 끄고, 켠 경우 비활성 시간(60초~7일)을 정한 뒤 **Save** 를 누릅니다.
4. 필요하면 **Add Read Replica** 로 읽기 복제본을 추가합니다(브랜치당 최대 6개).
5. 고가용성이 필요하면 편집 창에서 **Compute type** 을 **High availability** 로 바꾸고 **Configuration** 을 고릅니다(2, 3, 4). 이때 스케일 투 제로는 꺼야 합니다.

### 3.2 SDK와 CLI로 설정하기

Manage computes 페이지의 예시입니다. 엔드포인트 이름은 `projects/<project>/branches/<branch>/endpoints/<compute>` 형식입니다.

최소·최대 CU 변경 (CLI):

```bash
databricks postgres update-endpoint \
  projects/my-project/branches/production/endpoints/my-compute \
  "spec.autoscaling_limit_min_cu,spec.autoscaling_limit_max_cu" \
  --json '{
    "spec": {
      "autoscaling_limit_min_cu": 1.0,
      "autoscaling_limit_max_cu": 8.0
    }
  }'
```

스케일 투 제로 끄기 (CLI). 켜려면 `suspend_timeout_duration`에 `"300s"`처럼 60~604800초 범위의 값을 넣습니다.

```bash
databricks postgres update-endpoint \
  projects/my-project/branches/production/endpoints/my-compute \
  spec.suspension \
  --json '{
    "spec": {
      "no_suspension": true
    }
  }'
```

> **주의** 비활성 시간과 `no_suspension`은 둘 중 하나만 설정합니다. 문서는 `no_suspension: false`를 유효하지 않은 값으로 명시합니다.

고가용성 활성화 (CLI 형식). 필수 전제는 `no_suspension: true`입니다. 구성 값은 `spec.group`의 `min`과 `max`에 씁니다.

```bash
databricks postgres update-endpoint \
  projects/my-project/branches/production/endpoints/my-compute \
  "spec.group,spec.suspension" \
  --json '{
    "spec": {
      "endpoint_type": "ENDPOINT_TYPE_READ_WRITE",
      "no_suspension": true,
      "group": {
        "min": 2,
        "max": 2,
        "enable_readable_secondaries": true
      }
    }
  }'
```

`min`과 `max`를 3으로 바꾸면 주 컴퓨트 1개와 보조 컴퓨트 2개가 됩니다. 보조 컴퓨트 읽기 접근을 끄려면 `enable_readable_secondaries`를 `false`로 바꿉니다. 문서는 HA를 끄는 방법으로 **Compute type** 을 **Single compute** 로 되돌리라고 설명합니다.

### 3.3 프로젝트 기본 컴퓨트 설정

새 프로젝트의 기본 컴퓨트 설정은 프로젝트 설정의 **Compute defaults** 에서 바꿉니다. 바꿔도 기존 컴퓨트 설정은 바뀌지 않고, 새로 만드는 주 컴퓨트와 읽기 복제본의 초기값에만 적용됩니다.

## 4. 트레이드오프

| 선택 | 장점 | 비용·제약 |
|---|---|---|
| Autoscaling | 부하에 맞춘 자동 조정 | 최대-최소 차이 16 CU 이하라는 제약. 크기 변경 시 연결이 잠시 끊길 수 있음 |
| 스케일 투 제로 | 유휴 시 자원 절감 | 재활성화 지연 (수백 ms), 세션 상태 초기화. 32 CU 이하에서만 가능 |
| 읽기 복제본 | 읽기 부하 분리, 추가 스토리지 없음 | 브랜치당 최대 6개. 비동기라 최신 쓰기가 바로 보이지 않을 수 있음 |
| HA | 보조 컴퓨트로 장애 대응 | 스케일 투 제로 불가. 보조 컴퓨트 1개 구성에서 읽기 중단 위험 |

HA와 스케일 투 제로는 동시에 쓸 수 없습니다. 자동 장애 조치가 필요하면 스케일 투 제로를 포기하고 상시 가동 비용을 받아들여야 합니다. 반대로 개발 브랜치처럼 장애 대응이 필요 없으면 스케일 투 제로로 비용을 줄이는 편이 맞습니다.

## 5. 주의사항

- **스케일 투 제로를 HA와 함께 쓰지 않습니다.** 문서상 HA에서는 꺼야 합니다.
- **CU 범위를 좁게 잡지 않습니다.** 최대-최소 차이가 16 CU를 넘을 수 없으므로, 피크가 큰 워크로드는 최소를 조금 올려 여러 단계 확장에 맞추십시오.
- **보조 컴퓨트 크기는 주 컴퓨트를 따라갑니다.** 주 컴퓨트를 키우면 보조 컴퓨트의 하한도 같이 올라갑니다.
- **연결 재시도를 구현합니다.** 스케일 투 제로, 장애 조치, 크기 변경 모두 연결에 영향을 줄 수 있습니다.
- **읽기 복제본에서 방금 쓴 데이터를 기대하지 않습니다.** 복제는 비동기입니다.
- **Azure와 AWS 기본값을 구분합니다.** Azure 프로젝트 문서의 기본 컴퓨트 표기(production 8–16 CU)와 기본값 절(2↔4 CU)은 서로 다릅니다. 원문 표기가 일관되지 않으므로 실제 기본값은 워크스페이스에서 확인하십시오.

## 참고 문서

- [Autoscaling (AWS)](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [Manage computes (AWS)](https://docs.databricks.com/aws/en/oltp/projects/manage-computes)
- [Scale to zero (AWS)](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)
- [Read replicas (AWS)](https://docs.databricks.com/aws/en/oltp/projects/read-replicas)
- [High availability (AWS)](https://docs.databricks.com/aws/en/oltp/projects/manage-high-availability)
- [Manage projects (AWS, Compute defaults 절)](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)
- [Manage projects (Azure)](https://learn.microsoft.com/en-us/azure/databricks/oltp/projects/manage-projects)
