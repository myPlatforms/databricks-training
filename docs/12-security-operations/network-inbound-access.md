# 인바운드 네트워크 접근

> 기준일: 2026-10-30 · 근거: 공식 문서 · 수준: 300

## 한눈에 보기

인바운드 접근은 "사용자와 도구가 워크스페이스에 들어오는 길"을 통제합니다. 세 가지 수단이 있습니다. 사설 연결로 들어오게 하는 **프런트엔드 PrivateLink**, 클래식 컴퓨트에서 컨트롤 플레인으로 나가는 길을 사설화하는 **백엔드 PrivateLink**, 공인 IP 대역을 허용하거나 차단하는 **IP 액세스 목록** 입니다. 최근에는 **컨텍스트 기반 인그레스**(Context-based ingress)가 세 번째 수단을 대체하는 방향으로 권장됩니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 워크스페이스 주소가 공인 인터넷에 열려 있으면 사내 네트워크 밖에서도 로그인 시도가 가능합니다.
- 공인 IP만 허용하면 VPN이나 Direct Connect로 들어오는 사설 트래픽은 막을 수 없습니다. 문서는 IP 액세스 목록이 PrivateLink로 들어오는 사설 IP를 막지 못한다고 명시합니다.
- 네트워크 규칙이 여러 곳에 흩어지면 어떤 경로가 열려 있는지 파악하기 어렵습니다.

Databricks는 이 문제를 PrivateLink로 사설 경로를 만들고, 그 위에 접근 정책을 겹쳐 두는 방식으로 풀도록 안내합니다.

## 2. 어떻게 동작하는가

### 프런트엔드 PrivateLink (Front-end PrivateLink)

사용자 트래픽을 웹 애플리케이션과 REST API로 보내는 경로를 VPC 인터페이스 엔드포인트로 바꿉니다. 문서는 Databricks Apps와 Databricks Connect API도 이 경로에 포함된다고 설명합니다.

| 구성 요소 | 설명 (문서 기준) |
|---|---|
| 요금제 | Enterprise 요금제 계정 필요 |
| VPC 엔드포인트 | 전이(transit) VPC에 "General Access (including REST API)" 서비스 이름으로 생성. 보안 그룹은 443 인바운드 허용 |
| 엔드포인트 등록 | 계정 콘솔의 **Security > Private endpoints** 에서 등록. 리전이 엔드포인트 리전과 같아야 함. General Access 엔드포인트는 모든 리전의 워크스페이스에 쓸 수 있음 |
| 프라이빗 액세스 설정 | 설정 객체를 만들어 워크스페이스의 **Advanced configurations > Private Link** 에 연결. Private Access Level은 Account 또는 Endpoint |
| DNS | 워크스페이스 URL을 엔드포인트로 라우팅. 사용자 지정 URL을 쓰면 그것도 라우팅 |
| 클래식 컴퓨트 요건 | 클래식 컴퓨트가 있는 워크스페이스는 고객 관리 VPC(customer-managed VPC)가 필요. 서버리스 전용 워크스페이스는 필요 없음 |

**Private Access Level** 두 값의 차이는 다음과 같습니다.

| 값 | 허용 범위 |
|---|---|
| Account | 계정에 등록된 모든 VPC 엔드포인트에서 오는 연결 |
| Endpoint | 명시한 엔드포인트 집합에서 오는 연결만. 집합에 인바운드 엔드포인트 등록이 포함되어야 함 |

프라이빗 액세스 설정이 없는 워크스페이스는 사설 접근을 모두 거부한다고 문서가 설명합니다.

> **주의** 공개 접근 설정(**Public access enabled**)은 True 또는 False입니다. 문서는 DNS 테스트 중에는 True로 두고, 테스트가 끝나면 False로 바꾸라고 권장합니다. False로 바꾸기 전에 사설 경로가 정상인지 확인하지 않으면 사용자가 접속할 수 없게 됩니다.

### 백엔드 PrivateLink (Back-end PrivateLink)

클래식 컴퓨트 플레인(고객 VPC의 클러스터)에서 컨트롤 플레인으로 가는 트래픽을 사설화합니다. 범위는 클래식 컴퓨트입니다. 서버리스 컴퓨트에는 적용되지 않는다고 문서가 명시합니다.

| 엔드포인트 | 용도 |
|---|---|
| 워크스페이스 VPC 엔드포인트 | 컴퓨트 플레인에서 REST API 호출 (워크스페이스의 리전별 서비스 이름 사용) |
| SCC 릴레이 VPC 엔드포인트 | 보안 클러스터 연결(Secure cluster connectivity) 릴레이 (릴레이의 리전별 서비스 이름 사용) |

두 엔드포인트 모두 **Enable private DNS name** 을 켜야 합니다. 클래식 VPC 엔드포인트는 같은 고객 관리 VPC를 쓰는 워크스페이스끼리 공유할 수 있습니다. 엔드포인트 등록은 생성 후 수정할 수 없다고 문서가 명시합니다. 워크스페이스 상태가 `RUNNING`이 된 뒤에도 약 20분 기다린 후 클러스터를 만들라고 안내합니다.

> **참고** 백엔드 PrivateLink는 Databricks가 만드는 NCC 사설 엔드포인트 규칙과 다릅니다. 백엔드 PrivateLink의 VPC 엔드포인트는 고객이 자기 VPC에 만듭니다. NCC의 사설 엔드포인트는 서버리스 컴퓨트가 자원에 접근할 때 쓰며, 자세한 내용은 [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md)에서 다룹니다.

### IP 액세스 목록 (IP access lists)

허용 목록과 차단 목록으로 공인 IP 대역을 제한합니다. 문서 기준 Enterprise 요금제가 필요하며, 기본값은 모든 IP 주소에서 접속을 허용하는 것입니다.

| 대상 | 제한 범위 | 설정 방법 |
|---|---|---|
| 계정 콘솔 | 계정 콘솔 UI와 계정 수준 REST API | UI 또는 REST API |
| 워크스페이스 | 워크스페이스와 워크스페이스 수준 API | REST API |

평가 순서는 다음과 같습니다.

1. 차단 목록을 먼저 확인합니다. 일치하면 차단합니다.
2. 차단에 걸리지 않았고 허용 목록이 하나 이상 있으면, 주소가 허용 목록 중 하나에 들어 있어야 합니다.
3. 허용 목록이 없으면 차단되지 않은 모든 주소를 허용합니다.

CIDR 표기를 쓸 수 있으며, 서브넷 하나가 한도 한 개로 계산됩니다. 계정 콘솔의 허용·차단 목록을 합친 최대치는 1,000개 IP/CIDR 값입니다. 변경이 적용되기까지 몇 분 걸릴 수 있습니다.

PrivateLink와의 관계는 다음과 같습니다.

- IP 액세스 목록은 **인터넷 트래픽에만** 적용됩니다. PrivateLink로 들어오는 사설 IP를 막지 못합니다. 이를 막으려면 AWS Network Firewall을 쓰라고 문서가 안내합니다.
- PrivateLink 접근을 등록된 엔드포인트로만 제한하려면 프라이빗 액세스 설정 수준을 **ENDPOINT** 로 바꾸거나, 컨텍스트 기반 인그레스로 선택한 프라이빗 엔드포인트만 허용하도록 설정합니다.
- 컨텍스트 기반 인그레스와 워크스페이스 IP 액세스 목록은 **둘 다** 적용됩니다. 둘 중 하나라도 거부하면 접근이 거부됩니다.
- 문서는 컨텍스트 기반 인그레스를 기본 접근 통제로 삼고, 기존 워크스페이스 IP 액세스 목록을 여기로 옮기라고 권장합니다.

### 컨텍스트 기반 인그레스 (Context-based ingress)

등록된 VPC 엔드포인트 중 어떤 엔드포인트가 워크스페이스에 접근할 수 있는지를 정책으로 정합니다. 릴리즈 노트에 따르면 2026년 10월 12일부터 **GA** 입니다. 정책 조건에는 아이덴티티와 요청 유형이 포함됩니다.

정책에는 두 모드가 있습니다.

| 모드 | 동작 |
|---|---|
| Dry run | 거부를 차단하지 않고 `system.access.inbound_network`에 기록만 함 |
| Enforced | 정책에 맞지 않는 요청을 실제로 차단 |

dry run으로 먼저 거부 로그를 보고, 정상 트래픽이 막히지 않는 것을 확인한 뒤 Enforced로 바꾸는 순서가 안전합니다.

> **참고** 릴리즈 노트(2026-10-12)는 인바운드 Private Link용 컨텍스트 기반 인그레스 정책이 **GA** 가 되었다고 적습니다. 프런트엔드 PrivateLink 페이지는 상태 라벨 없이, 계정 관리자가 계정 콘솔의 Previews 페이지에서 "Context-Based Ingress: Workspace Private Access Policies"를 켜야 한다고 설명합니다. 계정 콘솔에서 이 설정이 어디에 있는지 먼저 확인하십시오.

## 3. 어떻게 쓰는가

### 인바운드 거부 로그 조회

컨텍스트 기반 인그레스의 dry run 결과와 실제 인바운드 거부는 `system.access.inbound_network` 시스템 테이블에 남습니다. 최근 거부 기록을 보려면 다음 쿼리를 씁니다.

```sql
SELECT *
FROM system.access.inbound_network
WHERE event_date >= current_date() - INTERVAL 7 DAYS
LIMIT 100;
```

> **참고** 이 테이블은 Public Preview입니다. 컬럼 구성은 테이블 조회로 먼저 확인한 뒤 필요한 필드만 고르십시오. 보존 기간은 [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md)의 표를 참고하십시오.

### IP 액세스 목록 설계 순서

1. 현재 사용자가 쓰는 공인 IP 대역을 조사합니다.
2. 사설 경로(프런트엔드 PrivateLink)를 먼저 구성하고 DNS를 검증합니다.
3. 공개 접근 설정을 True로 둔 상태에서 사설 경로와 공인 경로를 모두 테스트합니다.
4. 허용 목록을 적용하고 몇 분 기다린 뒤 접속을 확인합니다.
5. 공개 접근 설정을 False로 바꾸고, 사설 경로만 남깁니다.

## 4. 트레이드오프

| 수단 | 장점 | 제약 |
|---|---|---|
| 프런트엔드 PrivateLink | 공인 인터넷을 거치지 않음 | Enterprise 요금제, VPC 엔드포인트와 DNS 구성 필요 |
| 백엔드 PrivateLink | 클래식 컴퓨트의 컨트롤 플레인 트래픽을 사설화 | 고객 관리 VPC 필요. 서버리스에는 적용 안 됨. 등록 수정 불가 |
| IP 액세스 목록 | 설정이 단순하고 즉시 효과 | 인터넷 트래픽에만 적용. 사설 IP는 못 막음. 목록 관리 부담 |
| 컨텍스트 기반 인그레스 | 엔드포인트와 아이덴티티 단위로 정밀 제어 | 설정이 복잡. 계정 콘솔에서 기능을 켜야 함 |

## 5. 주의사항

- **잠금(lockout)을 조심하십시오.** 문서 본문에는 잘못된 목록에서 복구하는 절차가 없습니다. 변경 전에 관리자가 자기 IP를 허용 목록에 넣었는지 확인하고, 계정 콘솔에 접속할 수 있는 두 번째 경로를 준비하십시오.
- **공개 접근 설정을 먼저 끄지 마십시오.** 사설 경로 검증이 끝나기 전에 끄면 모든 사용자가 접속하지 못할 수 있습니다.
- **IP 액세스 목록으로 PrivateLink 트래픽을 막는다고 생각하지 마십시오.** 적용 범위가 다릅니다.
- **백엔드 PrivateLink 엔드포인트 등록은 수정할 수 없습니다.** 잘못 만들면 삭제 후 다시 만들어야 합니다.
- **클러스터는 워크스페이스 `RUNNING` 직후 바로 쓰지 마십시오.** 문서가 약 20분 대기를 권장합니다.

## 참고 문서

- [Network security](https://docs.databricks.com/aws/en/security/network/)
- [Front-end networking](https://docs.databricks.com/aws/en/security/network/front-end/)
- [Configure private connectivity to Databricks](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect)
- [Back-end PrivateLink](https://docs.databricks.com/aws/en/security/network/classic/privatelink)
- [IP access lists overview](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
