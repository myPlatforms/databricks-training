# 서버리스 이그레스와 NCC

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 300

## 한눈에 보기

인바운드 접근이 "들어오는 길"이라면, 이 페이지의 주제는 "나가는 길"입니다. 서버리스 컴퓨트(노트북, 잡, SQL 웨어하우스, Lakeflow pipelines, Model Serving 등)가 외부 인터넷이나 다른 자원에 연결할 때의 통제 수단은 세 가지입니다. **서버리스 이그레스 제어**(Serverless egress control)는 아웃바운드 연결 정책을 정하고, **네트워크 정책**(Network policy)은 그 정책의 실체이며, **네트워크 연결 구성**(Network connectivity configuration, NCC)은 사설 엔드포인트를 만드는 계정 수준 객체입니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 서버리스 컴퓨트는 Databricks가 관리하는 플레인에서 돌기 때문에, 고객이 방화벽으로 출발지를 막을 수 없습니다.
- 아웃바운드가 열려 있으면 노트북 코드가 임의의 외부 주소로 데이터를 보낼 수 있습니다.
- 자원이 공인 IP로만 열려 있으면 사설 자원에 접근하려고 공인 노출을 늘려야 합니다.

서버리스 이그레스 제어는 아웃바운드 목적지를 정책으로 명시하게 하고, NCC는 사설 연결을 계정 수준에서 만들게 합니다.

## 2. 어떻게 동작하는가

### 서버리스 이그레스 제어

문서 기준 Enterprise 요금제가 필요합니다. 적용 대상은 노트북, 워크플로(잡), SQL 웨어하우스, Lakeflow pipelines, Model Serving, Data Quality Monitoring, Databricks Apps(제한적 지원)입니다.

네트워크 접근 모드는 두 가지입니다.

| 모드 | 동작 | 범위 |
|---|---|---|
| Full Access | 서버리스 워크로드의 아웃바운드 접근을 제한하지 않음 | 아웃바운드만 해당. 워크스페이스 간 접근은 별개 |
| Restricted Access | 아웃바운드를 기본 거부. 허용된 목적지만 통과 | Unity Catalog 외부 위치와 명시한 목적지만 허용 |

네트워크 정책은 계정 수준에서 만드는 설정 객체이며, 한 워크스페이스에는 한 번에 한 정책만 연결할 수 있습니다. 문서는 새 정책을 먼저 **dry-run 모드** 로 평가한 뒤 강제 적용하는 방법을 설명합니다.

Restricted Access에서 허용되는 목적지는 다음과 같습니다.

| 목적지 | 조건·메모 |
|---|---|
| Unity Catalog 외부 위치 | Restricted 모드에서 기본 허용. Unity Catalog 리전과 S3 버킷 리전이 같아야 함 |
| 정책에 나열한 FQDN과 S3 버킷 | 정책에 명시한 경우 |
| 같은 워크스페이스의 워크스페이스 API | 문서가 허용 목적지로 나열 |
| 다른 Databricks 워크스페이스 | 정책에 나열해야 하며, 목적지 워크스페이스의 인그레스 규칙도 허용해야 함 |
| 워크스페이스 자체 S3 버킷, 필수 시스템 테이블, 읽기 전용 샘플 데이터 | 암시적으로 허용 |
| Model Serving 외부 모델 제공자와 MCP 서버 | Restricted 모드에서 DNS 이름을 추가해야 함 |

> **참고** 문서에는 네트워크 정책을 NCC나 계정 설정을 통해 연결하는 구체 절차가 이 페이지 범위에서 명시되지 않았습니다. 정책 연결 절차는 "Manage network policies for serverless egress control" 페이지에서 확인하십시오.

### 서버리스 컴퓨트 네트워킹

서버리스 컴퓨트는 Databricks 관리 플레인에서 실행됩니다. 컨트롤 플레인에서 서버리스로 가는 트래픽은 항상 클라우드 백본 망을 타고, 공인 인터넷을 거치지 않는다고 문서가 설명합니다.

서버리스 컴퓨트가 고객 자원에 닿는 방식은 자원 위치, 설정, 종류에 따라 다릅니다.

| 방식 | 상태 (문서 기준) |
|---|---|
| S3 게이트웨이 엔드포인트 | GA (별도 명시가 없는 경우) |
| 사설 IP | GA (별도 명시가 없는 경우) |
| 공인 IP | GA (별도 명시가 없는 경우) |
| 레거시 고정 IP 목록(stable IP list) | 지원 중단(decommissioned). 이전에는 Public Preview |

> **주의** 레거시 고정 IP 목록은 NCC UI와 Network Connectivity API에서 더 이상 제공되지 않습니다. 새 방식으로 옮기기 전까지 서버리스 컴퓨트가 자원에 접근할 때 `403 Forbidden` 오류가 날 수 있다고 문서가 경고합니다.

### 서버리스 방화벽 구성

자원 쪽 방화벽에서 서버리스 접근을 허용하려면 "Serverless compute firewall configuration" 페이지를 따릅니다. 주의할 점은 자원 방화벽이 클래식 컴퓨트에도 영향을 준다는 것입니다. 서버리스 접근을 허용하더라도 클래식 연결용 네트워크는 따로 허용해야 합니다.

### NCC (Network connectivity configuration)

NCC는 사설 엔드포인트 생성을 관리하는 계정 수준 객체입니다.

| 항목 | 문서 기준 설명 |
|---|---|
| 범위 | 계정 수준이며 리전 단위 |
| 생성 | 계정 콘솔에서 계정 관리자가 생성 |
| 워크스페이스 연결 | 한 리전의 여러 워크스페이스에 연결 가능. 연결된 모든 워크스페이스에 그 NCC의 사설 엔드포인트 규칙이 적용 |
| 메타스토어 연결 | OpenSharing SecureConnect를 위해 메타스토어에도 연결 가능 |

사설 연결 상태는 문서에 따라 다르게 적혀 있습니다. 서버리스 네트워킹 페이지는 "Databricks 사설 연결(Databricks private connectivity) 기능은 Private Preview"라고 표기합니다. 반면 릴리즈 노트에는 2026년 10월 12일부터 "서버리스 컴퓨트에서 AWS 관리형 자원으로의 사설 연결"이 GA라고 적혀 있습니다. 두 문서가 충돌하므로, 실제 적용 전에 대상 자원 유형별 상태를 원문에서 다시 확인하십시오.

> **참고** 사설 엔드포인트는 시간당 요금과 처리 데이터량(GB)당 요금이 부과된다고 문서가 설명합니다. 단가는 이 장에 쓰지 않습니다. 비용 구조는 [비용 관리](cost-management.md)를 참고하십시오.

## 3. 어떻게 쓰는가

### 아웃바운드 접근 기록 조회

`system.access.outbound_network` 시스템 테이블에서 서버리스 아웃바운드 기록을 확인할 수 있습니다. 이 테이블은 Public Preview이며 보존 기간은 365일로 표기되어 있습니다.

```sql
SELECT *
FROM system.access.outbound_network
WHERE event_date >= current_date() - INTERVAL 7 DAYS
LIMIT 100;
```

정책을 강제하기 전에 dry-run 결과를 이 테이블로 점검하면 정상 워크로드가 막히는 것을 미리 찾을 수 있습니다. 컬럼 목록은 `DESCRIBE TABLE system.access.outbound_network`로 확인하십시오.

### 적용 순서 예시

1. 서버리스 워크로드가 접근하는 외부 주소와 자원 목록을 수집합니다. 노트북과 잡의 코드, Unity Catalog 외부 위치, Model Serving 외부 제공자 목록이 기준이 됩니다.
2. Restricted 모드 정책을 작성하되 dry-run으로 평가합니다.
3. 아웃바운드 기록에서 차단될 호출을 확인하고 허용 목록에 추가합니다.
4. 강제 적용 후 주요 잡과 노트북을 다시 실행합니다.
5. 레거시 고정 IP 목록을 쓰고 있었다면 NCC 방식으로 옮긴 뒤 자원 방화벽을 조정합니다.

## 4. 트레이드오프

| 선택 | 장점 | 제약 |
|---|---|---|
| Full Access | 설정 부담이 없음 | 아웃바운드가 열려 있어 유출 통제가 약함 |
| Restricted Access | 목적지를 명시해 유출 위험 축소 | 목록 관리가 필요하고, 새 외부 호출이 추가되면 막힐 수 있음 |
| NCC 사설 연결 | 공인 IP 노출 없이 자원에 접근 | 사설 엔드포인트 비용 발생, 리전 단위 구성, 상태 확인 필요 |
| 공인 IP 허용 | 설정이 단순함 | 자원 방화벽 규칙이 늘어나고 노출 면적이 커짐 |

## 5. 주의사항

- **dry-run을 건너뛰지 마십시오.** 강제 적용 후 막힌 잡은 장애로 드러나므로, 먼저 기록으로 확인하는 것이 안전합니다.
- **Model Serving 외부 제공자와 MCP 서버는 DNS 이름을 추가해야 합니다.** 빠뜨리면 서빙 호출이 실패합니다.
- **NCC 연결 범위를 확인하십시오.** 한 NCC의 규칙은 연결된 모든 워크스페이스에 적용됩니다. 한 워크스페이스만 바꾸려는 의도라면 NCC를 나눠야 합니다.
- **고정 IP 목록 사용 여부를 먼저 점검하십시오.** 지원 중단된 방식을 쓰고 있으면 `403` 오류가 날 수 있습니다.
- **자원 방화벽은 서버리스와 클래식을 함께 영향 줍니다.** 한쪽만 고려해 바꾸면 다른 쪽 잡이 깨집니다.
- **Unity Catalog 외부 위치의 리전을 맞추십시오.** 문서가 Unity Catalog 리전과 S3 버킷 리전 일치를 요구합니다.

## 참고 문서

- [Serverless compute plane networking](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)
- [What is serverless egress control?](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)
- [Manage network policies for serverless egress control](https://docs.databricks.com/aws/en/security/network/serverless-network-security/manage-network-policies)
- [Configure a firewall for serverless compute access](https://docs.databricks.com/aws/en/security/network/serverless-network-security/serverless-firewall-config)
- [Understand data transfer and connectivity costs](https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
