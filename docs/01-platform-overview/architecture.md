# 플랫폼 아키텍처

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Databricks 아키텍처는 **control plane**(제어 영역)과 **compute plane**(컴퓨트 영역)으로 나뉩니다. 저장소는 별도의 계층으로 함께 봐야 합니다. 공식 아키텍처 문서는 이 세 부분을 "control plane, compute plane, and storage components"로 묶어 설명합니다.

| 구성 요소 | 공식 문서의 정의 | 어디에 있는가 |
|---|---|---|
| **control plane** | "the backend services that Databricks manages in your Databricks account" | Databricks 계정 안 (고객 클라우드 계정 밖) |
| **compute plane** | "where your data is processed" | 클래식은 고객 클라우드 계정, 서버리스는 Databricks 계정 안 |
| **워크스페이스 스토리지** | 노트북·쿼리 같은 워크스페이스 파일과 실행 결과 같은 시스템 데이터 | 클래식은 고객 클라우드 계정의 버킷, 서버리스는 Databricks 관리형 기본 스토리지 |
| **Unity Catalog 메타스토어** | 테이블·모델 등 데이터 자산의 거버넌스 시스템 | 메타스토어 단위로 관리되며 여러 워크스페이스에서 공유 가능 |

> **참고** 공식 문서는 control plane에 대해 "The control plane is located in the Databricks account, not your cloud account."라고 명시합니다. 웹 애플리케이션(UI)도 control plane에서 동작합니다.

## 1. 왜 이렇게 나누었는가

데이터 플랫폼을 설계할 때 가장 중요한 질문은 "데이터는 누구의 계정에 있고, 누가 처리하는가"입니다. Databricks는 이 질문을 두 영역으로 분리해 답합니다.

- **제어 로직**(어떤 작업을 언제 실행할지, 누가 어떤 권한을 가졌는지, UI를 어떻게 보여줄지)은 Databricks가 운영하는 control plane에 둡니다.
- **데이터 처리**(실제로 파일을 읽고 쓰고 계산하는 일)는 compute plane에서 합니다. 이 영역이 고객 계정 안에 있느냐 Databricks 계정 안에 있느냐에 따라 "클래식"과 "서버리스"가 갈립니다.

이 분리 덕분에 고객은 데이터를 고객 클라우드 계정 밖으로 옮기지 않고도 관리형 제어 계층을 쓸 수 있습니다. 대신 네트워크 경계, 리전, 데이터 위치를 이해하고 설계해야 합니다.

## 2. 클래식과 서버리스 컴퓨트 플레인

공식 문서는 compute plane이 두 가지 형태로 존재한다고 설명합니다.

| 항목 | 클래식 컴퓨트 플레인(Classic compute plane) | 서버리스 컴퓨트 플레인(Serverless compute plane) |
|---|---|---|
| 컴퓨트가 실행되는 곳 | 고객 클라우드 계정 안, 워크스페이스의 가상 네트워크 | Databricks 계정 안의 컴퓨트 레이어 |
| 격리 방식 | 고객 계정 안에서 실행되므로 자연스럽게 분리됩니다. | 워크스페이스별 네트워크 경계와 다중 계층 보안으로 격리한다고 문서가 설명합니다. |
| 리전 | 워크스페이스의 리전 | 같은 AWS 리전의 워크스페이스에 대응 (문서는 클래식 컴퓨트 플레인과 같은 리전이라고 명시) |
| 네트워크 문서 | 클래식 컴퓨트 플레인 네트워킹 | 서버리스 컴퓨트 플레인 네트워킹 |
| 시작 속도 | 클러스터 기동 시간이 필요합니다. | 빠른 시작과 확장을 강조합니다(공식 서버리스 문서 설명). |
| 관리 부담 | 클러스터 구성, 인스턴스 타입, 런타임 선택을 직접 합니다. | 프로비저닝과 런타임 업그레이드를 플랫폼이 맡습니다. |

서버리스 컴퓨트 문서는 서버리스를 "available by default in most workspaces"라고 설명합니다. 즉, 대부분의 워크스페이스에서는 별도 활성화 없이 쓸 수 있다는 뜻입니다. 다만 문서는 Unity Catalog가 활성화되지 않은 레거시 워크스페이스는 먼저 업그레이드해야 한다고 명시합니다.

> **참고** 서버리스 SQL 웨어하우스는 서버리스 컴퓨트 문서와 별도 페이지에서 설명됩니다. 웨어하우스 유형은 03장에서 다룹니다.

### 실행 흐름 (순서로 보기)

표로 나타낸 흐름을 순서대로 읽으면 다음과 같습니다. 공식 문서에 도식 그림이 있으므로, 실제 그림은 [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture) 페이지에서 확인하십시오.

1. 사용자가 워크스페이스 UI나 API로 노트북 실행, SQL 쿼리, 잡 실행을 요청합니다. 요청은 control plane이 받습니다.
2. control plane은 요청에 맞는 컴퓨트를 찾거나 기동합니다. 서버리스인지 클래식인지에 따라 컴퓨트가 있는 위치가 달라집니다.
3. compute plane에서 실제 데이터 처리가 일어납니다.
4. 노트북 결과, 쿼리 결과, 실행 이력 같은 시스템 데이터는 워크스페이스 스토리지에 기록됩니다.
5. 테이블 데이터는 Unity Catalog가 관리하는 저장 위치(테이블 경로)에 기록됩니다.

## 3. 워크스페이스 스토리지

공식 문서는 워크스페이스 스토리지를 두 종류로 나눕니다.

| 종류 | 내용 |
|---|---|
| 워크스페이스 파일 데이터(workspace file system data) | 노트북, SQL 쿼리와 대시보드, 알림(alerts), Git 폴더(repos), 라이브러리, Python·YAML 같은 작은 파일 |
| 워크스페이스 시스템 데이터(workspace system data) | 캐시된 쿼리 결과, 잡 실행 결과, 노트북 리비전, 쿼리 플랜, 클러스터 로그 같은 내부 데이터 |

저장 위치는 워크스페이스 유형에 따라 다릅니다.

| 워크스페이스 유형 | 저장 위치 | 문서가 명시한 주의 |
|---|---|---|
| 클래식 워크스페이스 | 고객 AWS 계정의 워크스페이스 스토리지 버킷 | 이 버킷을 삭제하거나 수정하지 마십시오. 기본 워크스페이스 카탈로그와 레거시 DBFS 루트·마운트도 여기에 있을 수 있습니다. |
| 서버리스 워크스페이스 | Databricks 관리형 기본 스토리지(Default storage) | 자체 클라우드 스토리지를 연결할 수도 있습니다. |

### DBFS 루트 (레거시)

`dbfs:/` 네임스페이스로 보이는 DBFS 루트는 공식 문서는 이를 **deprecated** 이며 권장하지 않는다고 설명합니다. 워크스페이스 설정에 따라 비활성화되어 있을 수 있습니다. 새로 작성하는 자산은 Unity Catalog의 볼륨(Volume)이나 테이블을 쓰는 것을 기준으로 삼으십시오.

### 기본 스토리지(Default storage)의 제약

기본 스토리지 문서에는 중요한 제약이 있습니다.

> **주의** 공식 문서는 "Classic compute (any compute that is not serverless) cannot interact with data assets in default storage."라고 명시합니다. 즉, 기본 스토리지에 있는 데이터 자산은 클래식 컴퓨트에서 직접 다룰 수 없습니다. 클래식 컴퓨트로 작업할 계획이라면 데이터 위치를 먼저 확인하십시오. 자세한 내용은 02장에서 다룹니다.

## 4. 네트워크 경계와 데이터 위치

아키텍처를 설계할 때 확인할 질문은 다음과 같습니다.

| 질문 | 확인할 지점 |
|---|---|
| 데이터 처리가 고객 계정 안에서 일어나는가? | 클래식은 예, 서버리스는 Databricks 계정 안의 컴퓨트 레이어입니다. |
| 외부 네트워크(데이터 소스, 패키지 저장소)에 접근해야 하는가? | 서버리스와 클래식의 네트워크 문서를 각각 확인하십시오. 무료 체험에서는 외부 네트워크 접근이 제한된다는 문서 설명이 있습니다(시작하기 페이지 참고). |
| 데이터 저장 위치를 고객이 통제해야 하는가? | 클래식 워크스페이스 버킷, 외부 위치(External location), 기본 스토리지 중 어느 것을 쓰는지 정하십시오. |
| 리전 요건이 있는가? | 서버리스 컴퓨트는 워크스페이스와 같은 AWS 리전에 대응한다고 문서가 설명합니다. 리전별 기능 가용성은 별도로 확인하십시오. |

## 5. 트레이드오프

| 선택 | 장점 | 비용과 제약 |
|---|---|---|
| 클래식 컴퓨트 | 고객 계정 안에서 실행되어 네트워크와 인스턴스를 세밀하게 통제할 수 있습니다. | 클러스터 설정과 운영 부담이 큽니다. 고객 클라우드 계정의 인스턴스 비용이 별도로 발생할 수 있습니다. 문서 확인 범위에서 명시된 청구 구조는 [과금 모델 기초](billing-basics.md)에서 정리합니다. |
| 서버리스 컴퓨트 | 기동이 빠르고 운영 부담이 적으며 런타임이 자동 업그레이드됩니다. | 인스턴스를 직접 고르지 않습니다. 서버리스의 기능 제약과 네트워크 구성을 사전에 확인해야 합니다(서버리스 컴퓨트 제약 페이지 참고). |
| 기본 스토리지 | 설정이 가장 단순합니다. 서버리스 워크스페이스의 기본 카탈로그가 여기에 생깁니다. | 클래식 컴퓨트와 직접 상호작용하지 않는 제약이 있습니다. |

## 6. 주의사항

> **주의** 클래식 워크스페이스 스토리지 버킷을 직접 삭제하거나 수정하지 마십시오. 공식 문서가 명시한 금지 사항입니다.

> **주의** 아키텍처 그림을 만들 때 "Control Plane"과 "Compute Plane"은 공식 용어입니다. 그 밖에 조직 내부 용어(예: "관리 영역", "데이터 영역")로 바꿔 쓰면 공식 문서와 대조하기 어려워지므로, 처음에는 공식 명칭을 쓰고 설명을 덧붙이는 방식을 권장합니다.

> **참고** 공식 문서는 클래식 컴퓨트 플레인의 과금 방식(클라우드 인스턴스 비용 포함 여부)을 아키텍처 페이지에서 설명하지 않습니다. 비용 구조는 과금 장에서 따로 다룹니다.

> **참고** 서버리스 컴퓨트 문서에는 "versionless" 제품이라는 설명이 있습니다. 런타임 버전을 고정해야 하는 워크로드라면 이 특성을 먼저 확인하십시오.

## 다음으로 읽을 페이지

컴퓨트 플레인을 이해했다면, 워크스페이스·계정·메타스토어가 어떻게 묶이는지 [계정·워크스페이스·메타스토어](account-workspace-metastore.md)에서 이어서 봅니다.

## 참고 문서

- [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [Serverless compute](https://docs.databricks.com/aws/en/compute/serverless/)
- [Compute](https://docs.databricks.com/aws/en/compute/)
- [Default storage in Databricks](https://docs.databricks.com/aws/en/storage/default-storage)
- [What is DBFS?](https://docs.databricks.com/aws/en/dbfs/)
- [Serverless compute plane networking](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)
- [Classic compute plane networking](https://docs.databricks.com/aws/en/security/network/classic/)
