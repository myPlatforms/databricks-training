# 브랜치와 복구

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 300

이 페이지는 Lakebase의 데이터 분기(Branches)와 데이터 복구 기능을 다룹니다. 복구는 세 가지로 나뉩니다. 인스턴트 복구(Instant restore), 특정 시점 브랜치(Querying data at a point in time), 재해 복구(Disaster recovery)입니다. 재해 복구는 Private Preview입니다.

## 1. 왜 필요한가

운영 데이터를 바꾸기 전에 같은 데이터로 테스트하고 싶을 때, 또는 실수로 데이터를 지웠을 때 원래 상태가 필요합니다. 전통적인 방식은 다음과 같습니다.

| 기존 방식 | 한계 |
|---|---|
| 운영 DB 전체 복제(dump & restore) | 데이터가 클수록 오래 걸리고 저장 공간을 두 배로 씀 |
| 백업 파일에서 복구 | 복구 시점이 백업 주기에 묶임, 복구 시간이 김 |
| 테스트 환경에 샘플 데이터만 적재 | 운영과 같은 데이터 분포로 테스트할 수 없음 |

Lakebase는 브랜치를 copy-on-write 방식으로 즉시 만들고, 기록 보존 기간 안의 임의 시점으로 복구하거나 그 시점을 브랜치로 엽니다. 재해 복구는 다른 리전의 보조 워크스페이스에 데이터를 주기적으로 복제합니다.

## 2. 브랜치 (Branches)

### 2.1 동작 원리

문서 설명은 다음과 같습니다. 브랜치는 Git 브랜치와 비슷하게 동작합니다. 새 브랜치는 **copy-on-write** 로 "in seconds" 만들어집니다. 부모의 스키마와 데이터를 상속하고 스토리지를 공유하며, 데이터가 바뀔 때만 변경분이 따로 저장됩니다. 브랜치 생성 시간은 데이터베이스 크기와 무관합니다.

| 개념 | 문서 설명 |
|---|---|
| 루트 브랜치 (root branch) | 프로젝트 생성 시 만들어지는 기본 `production` 브랜치. 기본 브랜치를 다른 브랜치로 지정할 수 있음 |
| 자식 브랜치 (child branch) | "Every branch (except the root branch) has a parent." 부모의 변경은 자동으로 반영되지 않음 |
| 격리 범위 | 역할과 데이터베이스 상태도 브랜치별로 격리. 한 브랜치에서 만든 역할, 적용한 GRANT/REVOKE, 바꾼 역할 속성은 다른 브랜치에 영향 없음 |
| 리셋 (Reset) | 자식을 부모의 현재 상태로 맞춤. 연결 정보는 그대로. **부모 → 자식 방향만 가능** |
| 보호 브랜치 (Protected branch) | 실수로 바꾸는 것을 막는 장치. 삭제와 부모로부터의 리셋 불가, 비활성 자동 아카이브 제외, 프로젝트당 1개. 보호 브랜치가 있으면 프로젝트 삭제도 막힘 |

> **참고** 문서는 자식 브랜치의 변경을 부모에 반영하는 방법으로 "표준 마이그레이션 도구"를 쓰라고 안내합니다. Lakebase 안에서 자동으로 합치는 기능은 문서에 없습니다.

### 2.2 과금 구조 (문서 원문)

| 브랜치 종류 | 과금 |
|---|---|
| 만료 설정 브랜치 (expiration 있음) | 브랜치에서 바뀐 데이터만 과금 |
| 영구 브랜치 (만료 없음) | 데이터 전체 크기로 과금 |

영구 브랜치는 의도적으로 설정해야 합니다. 단가는 이 페이지에서 다루지 않습니다([베스트 프랙티스와 비용](best-practices-and-cost.md) 참조).

### 2.3 브랜치 생성 예시

이 장의 근거 문서에 있는 SDK 예시입니다. 브랜치 생성 CLI 명령은 확인하지 못했으므로 쓰지 않았습니다.

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
# 프로젝트 목록 조회 (Postgres API)
for project in w.postgres.list_projects():
    print(project.name)
```

> **참고** 브랜치 생성·리셋·삭제의 정확한 SDK 호출은 이 장 조사에서 원문으로 확인하지 못했습니다. 자동화하기 전에 [Branches](https://docs.databricks.com/aws/en/oltp/projects/branches) 원문을 다시 확인하십시오.

## 3. 인스턴트 복구 (Instant restore)

문서 페이지 제목은 **Point-in-time restore** 이고, 랜딩 페이지의 기능 이름은 **Instant restore** 입니다. 이 장은 두 이름을 모두 표기합니다. 기능 상태 라벨은 페이지에 없습니다.

### 3.1 동작 원리

| 항목 | 값 (AWS 문서 원문) |
|---|---|
| 복구 기간 (restore window) | "from 2 days up to 30 days, with a default of 7 days" |
| 적용 범위 | "The restore window setting affects all branches in your project." |
| 복구 결과 | "A new root branch is created" — 선택한 시점의 데이터를 가진 새 루트 브랜치 |
| 원래 브랜치 | 바뀌지 않고, 기존 연결도 그대로 동작 |
| 루트 브랜치 한도 | "Projects have a maximum of 3 root branches" |
| 비용 | "Extending the restore window increases your storage." |

복구 범위는 **브랜치의 모든 Postgres 데이터베이스** 입니다. 문제가 된 데이터베이스 하나만 되돌릴 수 없습니다.

### 3.2 복구 절차 (UI)

문서가 설명하는 절차는 UI뿐입니다. CLI나 API 명령은 원문에 없습니다.

1. Lakebase 앱에서 프로젝트를 열고 사이드바의 **Backup & Restore** 를 선택합니다.
2. **Restore from history** 에서 원본 브랜치를 고르고, 날짜·시각 선택기로 복구 시점을 고릅니다. **Preview data** 로 미리 볼 수 있습니다.
3. **Restore** 를 클릭하고 확인 화면에서 **Restore** 를 한 번 더 클릭합니다.
4. 복구된 데이터를 쓰려면 애플리케이션의 연결 설정을 새 브랜치로 바꿉니다.

> **주의** 루트 브랜치는 최대 3개입니다. 복구 전에 쓰지 않는 루트 브랜치를 삭제해야 할 수 있습니다.

## 4. 특정 시점 브랜치 (Querying data at a point in time)

문서 설명에 따르면, 보존 기간 안의 임의 시점 데이터를 **별도 브랜치** 로 만들어 조회합니다. 운영은 영향을 받지 않습니다. 이 기능은 데이터 이슈를 조사하거나 과거 상태를 분석할 때 씁니다.

| 항목 | 내용 (원문) |
|---|---|
| 생성 방법 | UI만 문서화됨. 프로젝트 대시보드에서 **Create branch** → 브랜치 이름 입력 → **Branch data and schema from a past point in time** 선택 → 날짜·시각 선택 → **Create** |
| 조회 | 연결 문자열을 복사해 외부 도구에서 쓰거나, 왼쪽 메뉴의 **SQL Editor** 사용 |
| 제한 | "You can only query data from within your configured restore window." |
| 정리 | "Delete point-in-time branches when you're finished with your analysis to avoid unnecessary storage usage." |
| 포함 범위 | "The branch contains all databases and schemas as they existed at the selected point in time." |
| 상태 라벨 | 원문에 없음 |

> **주의** 인스턴트 복구와 특정 시점 브랜치는 둘 다 과거 시점의 데이터를 가진 브랜치를 만들지만, 문서상 절차와 정리 안내가 다릅니다. 두 기능을 같은 것으로 보지 말고 각 페이지의 절차를 따로 확인하십시오.

## 5. 재해 복구 (Disaster recovery)

> **참고** 재해 복구 상태는 **Private Preview** 입니다. 원문은 "During the Private Preview, disaster recovery is not intended for production use."라고 명시합니다. 운영 설계에 넣지 마십시오.

### 5.1 동작 원리

| 항목 | 내용 (원문) |
|---|---|
| 복제 방식 | "Lakebase currently offers periodic replication, which synchronizes your data into another region" — 주기적 복제 |
| 복제 대상 | "Lakebase periodically replicates committed data from the Primary to the Secondary." |
| 보조 워크스페이스 | "pairs your project's Primary Workspace with a Secondary Workspace in another region" |
| 보조 컴퓨트 | "The Secondary's compute stays idle until a failover." |
| 장애 조치 | "Failover is always manual." 프로젝트 관리자가 장애 조치를 실행. 자동화는 요구사항에 따라 선택 가능하다고 표에 적힘 |
| RPO·RTO 수치 | 원문에 RTO 수치 없음. RPO는 "RPO windows in the minutes range" 표현만 있음 |
| 리전 제약 | "The Primary and Secondary must be in different regions." 같은 리전 워크스페이스 간 복제는 미지원 |

### 5.2 복구 브랜치 (Recovery branch)

- 장애 조치 후 원래 주(Primary)가 돌아와 **페일백(failback)** 되면 복구 브랜치가 접근 가능해집니다.
- 복구 브랜치는 분기(divergence)가 감지되기 전까지 숨겨져 있다고 문서가 설명합니다.
- "Lakebase never automatically merges or deletes a recovery branch." 자동 병합이나 자동 삭제는 없습니다.

### 5.3 고가용성과의 차이

| 항목 | 고가용성 (HA) | 재해 복구 (DR) |
|---|---|---|
| 목적 | 같은 리전 안에서 장애 대응 | 다른 리전으로 복구 |
| 구성 | 보조 컴퓨트를 다른 가용 영역에 둠 | 보조 워크스페이스를 다른 리전에 둠 |
| 장애 조치 | HA 문서 설명 참조 | 수동 (Always manual) |
| 상태 | 원문에 상태 라벨 없음 | Private Preview |

HA 구성은 [컴퓨트와 스케일링](compute-and-scaling.md)을 참조하십시오.

## 6. 트레이드오프

| 기능 | 장점 | 비용·제약 |
|---|---|---|
| 브랜치 | 즉시 생성, 격리 | 영구 브랜치는 데이터 전체 크기만큼 과금 |
| 인스턴트 복구 | 보존 기간 안 임의 시점 복구 | 루트 브랜치 3개 한도, 보존 기간만큼 스토리지 증가 |
| 특정 시점 브랜치 | 운영 영향 없이 과거 조회 | 정리하지 않으면 스토리지 낭비 |
| 재해 복구 | 다른 리전으로 복구 | Private Preview, 수동 장애 조치, 운영 용도 아님 |

## 7. 주의사항

- **보존 기간을 필요 이상으로 늘리지 않습니다.** 기간을 늘리면 스토리지가 늘어납니다.
- **루트 브랜치 한도를 관리합니다.** 복구를 반복하면 3개 한도에 빨리 닿습니다.
- **복구 후 연결을 바꿉니다.** 복구는 새 브랜치를 만들 뿐이므로 애플리케이션 연결 문자열을 바꾸지 않으면 옛 데이터를 계속 봅니다.
- **재해 복구를 운영 설계에 넣지 않습니다.** Private Preview 기간에는 운영 용도가 아니라고 문서가 명시합니다.
- **자식 브랜치 변경은 자동으로 부모에 가지 않습니다.** 운영 반영 경로를 따로 설계하십시오.

## 참고 문서

- [Branches (AWS)](https://docs.databricks.com/aws/en/oltp/projects/branches)
- [Point-in-time restore (AWS, 인스턴트 복구)](https://docs.databricks.com/aws/en/oltp/projects/point-in-time-restore)
- [Querying data at a point in time (AWS)](https://docs.databricks.com/aws/en/oltp/projects/point-in-time-branching)
- [Disaster recovery (AWS)](https://docs.databricks.com/aws/en/oltp/projects/disaster-recovery)
- [High availability (AWS)](https://docs.databricks.com/aws/en/oltp/projects/manage-high-availability)
- [Lakebase Postgres 개요 (AWS)](https://docs.databricks.com/aws/en/oltp/)
