# Databricks Apps 개요와 리소스 바인딩

> 기준일: 2026-10-28 · 근거: 공식 문서

Databricks Apps는 워크스페이스 안에서 웹 애플리케이션을 실행하는 서버리스 플랫폼입니다. 앱은 컨테이너로 돌아가며, Unity Catalog와 Databricks SQL에 통합됩니다. 이 페이지는 지원 프레임워크, 앱이 쓰는 리소스, 두 가지 권한 모델(앱 권한과 사용자 권한), 앱 상태를 다룹니다. 설정 파일과 배포 절차는 [앱 설정과 배포](configure-and-deploy.md)에서 다룹니다.

## 1. 왜 필요한가

데이터 팀이 만든 분석 도구나 데이터 입력 화면은 보통 다음 문제를 겪습니다.

- 별도 서버를 띄우면 인프라, 네트워크 격리, 인증 연동을 직접 관리해야 합니다.
- 앱이 쓰는 SQL 웨어하우스나 비밀 값을 코드에 넣으면 환경을 옮기기 어렵습니다.
- 사용자마다 다른 데이터 접근 권한을 앱이 존중하는지 확인하기 어렵습니다.

Databricks Apps는 전용 컴퓨트, 네트워크 분리, 암호화, 최소 권한 원칙을 플랫폼이 적용한다고 소개합니다. 앱이 쓸 리소스는 선언해서 연결하고, 권한은 앱 권한 또는 사용자 권한 중 하나로 실행합니다.

## 2. 상태

| 항목 | 상태 | 근거 |
|------|------|------|
| Databricks Apps 전체 | 페이지에 라벨 없음 | 개요, 핵심 개념 페이지에 상태 표기 없음 |
| 앱 상태 | Running, Stopped, Deploying, Crashed | 핵심 개념 페이지의 "App status" 항목 |

> **참고** 이 장의 근거 페이지에는 Databricks Apps의 GA·Public Preview 라벨이 없습니다. 기능 단위 상태가 필요하면 릴리즈 노트에서 Apps 관련 항목을 따로 확인하십시오. 이 장은 상태를 추정해서 적지 않습니다.

## 3. 지원 프레임워크

개요 페이지의 프레임워크 목록은 다음과 같습니다.

| 언어 | 프레임워크 (문서 원문) |
|------|-------------------------|
| Python | Streamlit, Dash, Gradio |
| Node.js | React, Angular, Svelte, Express |

Flask 예시는 앱 실행 설정 페이지(app-runtime)의 `app.yaml` 예시에 나옵니다. 개요 페이지의 목록에는 Flask가 없습니다. 그러므로 "지원 목록에 Flask 포함"으로 단정하지 않고, 실행 설정 예시가 있다는 수준으로만 씁니다. FastAPI 등 다른 프레임워크는 이 장의 근거 페이지에서 확인하지 못했습니다.

## 4. 구성 요소와 용어

핵심 개념 페이지가 정의하는 용어는 다음과 같습니다.

| 용어 | 정의 (페이지 요지) |
|------|--------------------|
| App | 서버리스 플랫폼에서 컨테이너로 실행되는 웹 앱 |
| App URL | `https://<app-name>-<workspace-id>.<region>.databricksapps.com` 형식으로 자동 할당. 생성 후 바꿀 수 없음 |
| Template | 기본 파일 구조, `app.yaml`, `requirements.txt`, 샘플 코드를 담은 스캐폴드 |
| System environment | Databricks가 관리하는 사전 구성 실행 환경. 의존성은 `requirements.txt`·`pyproject.toml`(Python) 또는 `package.json`(Node.js)으로 관리 |
| App resources | 앱이 쓰는 워크스페이스 리소스. 아래 5절 |
| App state | 앱이 데이터를 저장하는 위치. 아래 6절 |
| App users | 앱을 쓸 사용자와 그룹. `CAN_USE` 또는 `CAN_MANAGE` 권한 |

App URL의 `<app-name>`은 앱 이름이고, 이름은 생성 후 바꿀 수 없다는 점을 주의하십시오. 이름을 정할 때 운영 명명 규칙을 먼저 정하십시오.

## 5. 리소스 바인딩

### 5-1. 지원하는 리소스 종류

리소스 전용 페이지(Add resources to a Databricks app, 2026-10-02 갱신)는 앱에 붙일 수 있는 리소스로 다음 14종을 나열합니다. 괄호는 리소스 유형 키입니다.

| 리소스 | 유형 키 | 용도 (예) |
|--------|---------|-----------|
| Databricks app | `app` | 다른 앱 호출 |
| Genie Agent | `genie-space` | 앱이 호출하는 Genie Agent |
| Lakebase database | `postgres` (Lakebase Autoscaling), `database` (Lakebase Provisioned) | 데이터 저장·조회용 PostgreSQL. 권한 "Can connect and create" |
| Lakeflow job | `job` | 앱이 트리거하는 잡 |
| MLflow experiments | `experiment` | 실험 기록 |
| Model serving endpoint (Model) | `model` | 앱이 호출하는 모델 서빙 엔드포인트 |
| Unity Gateway model service (Model) | `model` | Unity Gateway 모델 서비스 호출 |
| Secret | `secret` | 자격 증명 등 민감 값 |
| SQL warehouse | `sql-warehouse` | 앱이 쿼리를 실행하는 웨어하우스 |
| Unity Catalog connection | `connection` | 외부 시스템 연결 |
| Unity Catalog table | `table` | 테이블 읽기·쓰기 |
| User-defined function | `function` | UC 함수 호출 |
| Unity Catalog volume | `volume` | 파일 읽기·쓰기 |
| AI Search index | `vector-search-index` | 검색 인덱스 조회 |

> **참고** 핵심 개념 페이지는 이 중 일부(SQL warehouse, Job, Model serving endpoint, Genie Agent, Secret, Volume)만 예시로 듭니다. 전체 목록은 리소스 페이지를 기준으로 합니다. Lakebase 연결 절차와 주입되는 환경 변수는 [Databricks Apps와 함께 쓰기](../../10-lakebase/apps-integration.md)에서 다룹니다.

### 5-2. 선언과 연결

페이지 원문은 다음 흐름을 설명합니다.

1. 앱에 필요한 리소스를 `databricks.yml` 매니페스트에 선언합니다. 원문: "Declare each required resource in the `databricks.yml` manifest."
2. 배포할 때 Databricks Apps UI가 선언된 리소스를 실제 워크스페이스 인스턴스에 연결합니다.
3. 앱은 **기존** 리소스만 쓸 수 있습니다. 원문: "Apps must use existing resources and can't create new ones."
4. 워크스페이스 관리자가 접근 요청을 승인하고, 앱의 서비스 프린시펄에 필요한 권한을 줍니다.

> **참고** 1번의 `databricks.yml`과 `app.yaml`의 역할 분담은 이 두 페이지에서 명확히 설명하지 않습니다. `app.yaml`은 실행 명령과 환경 변수를 정의하는 파일입니다. 리소스 선언이 어느 파일에 들어가는지는 번들 기능 페이지와 함께 확인하십시오.

### 5-3. 자격 증명 주입

리소스에 해당하지 않는 자격 증명은 Unity Catalog 관리 시크릿으로 넣는 방식을 권장합니다. 원문은 "use a Unity Catalog–managed secret to securely inject credentials"입니다. 리소스 ID나 환경별 값을 코드에 하드코딩하지 말고, 환경마다 다른 값은 설정으로 주입합니다.

## 6. 앱 상태 데이터 저장

앱은 다음 위치에 데이터를 둘 수 있습니다. 개요 페이지 목록입니다.

| 저장 위치 | 특징 |
|-----------|------|
| 메모리 | 앱이 재시작되면 사라짐 |
| 로컬 파일 시스템 | 앱 인스턴스 안에서만 보임 |
| Databricks 테이블 | 영속 저장, 다른 사용자와 공유 가능 |
| 워크스페이스 파일 | 소스 폴더와 같은 공간 |
| Unity Catalog 볼륨 | 파일 저장, 권한은 Unity Catalog로 관리 |
| Lakebase 데이터베이스 인스턴스 | 영속 관계형 데이터 저장 |

> **주의** 메모리와 로컬 파일 시스템은 재배포나 재시작 때 사라질 수 있다고 보고 설계합니다. 사용자 입력이나 상태를 남기려면 테이블, 볼륨, Lakebase 중 하나를 씁니다. 재시작 시 보존 여부의 세부 동작은 이 장의 근거 페이지에서 확인하지 못했습니다.

## 7. 두 가지 권한 모델

| 항목 | 앱 권한 (App authorization) | 사용자 권한 (User authorization) |
|------|----------------------------|----------------------------------|
| 신원 | 앱별 서비스 프린시펄 (자동 생성) | 로그인한 사용자 |
| 권한 부여 주체 | 앱 개발자가 서비스 프린시펄에 부여 | Unity Catalog 등 리소스의 기존 권한 |
| 사용자 간 차이 | 모든 사용자가 같은 권한 공유 | 사용자마다 다른 권한 적용 |
| 적합한 작업 | 로깅, 시스템 수준 작업 등 사용자 맥락과 무관한 작업 | 세밀한 데이터 접근 제어가 필요한 조회 |

원문 설명은 다음과 같습니다.

- 앱 권한: "This service principal acts as the app’s identity and is granted permissions by the app developer." 그리고 "All users of the app share this identity and have access to the same set of permissions."
- 사용자 권한: 사용자는 앱이 배포된 Databricks 계정에 속해야 합니다. SSO로 로그인하면 앱이 해당 사용자의 자격 증명을 씁니다. Unity Catalog의 세밀한 권한이 그대로 적용됩니다.

> **참고** 이 페이지는 사용자 권한을 설명하면서 on-behalf-of(OBO)라는 용어를 쓰지 않습니다. 인증 문서의 U2M·OBO 설명(통합 인증 페이지)과 함께 읽으십시오.

### 7-1. 선택 기준

| 질문 | 권장 |
|------|------|
| 모든 사용자가 같은 데이터를 봐도 되는가 | 앱 권한 |
| 사용자마다 다른 행이나 테이블을 보여야 하는가 | 사용자 권한 |
| 앱이 쓰기 작업을 하는가 | 앱 권한에 최소 권한만 부여. 쓰기 대상의 권한 범위를 먼저 정의 |

## 8. 앱 사용 공유

앱을 쓸 사람은 `CAN_USE`, 앱을 관리할 사람은 `CAN_MANAGE` 권한으로 나눕니다. 권한은 사용자나 그룹에 부여합니다. 개인 사용자보다 그룹에 주는 편이 관리하기 쉽습니다.

## 9. 트레이드오프

| 항목 | 장점 | 제약 |
|------|------|------|
| 서버리스 실행 | 인프라 관리가 없음 | 로컬 파일이 영속되지 않음 |
| 리소스 선언 | 환경 간 이식성 | 앱이 새 리소스를 만들 수 없음. 기존 리소스를 먼저 준비해야 함 |
| 앱 권한 | 단순한 공유 모델 | 사용자별 세밀한 제어가 안 됨 |
| 사용자 권한 | Unity Catalog 권한을 그대로 존중 | 사용자가 계정에 속해야 하고 권한 설계가 필요 |

## 10. 주의사항

- **새 리소스를 앱이 만들지 않습니다.** 웨어하우스, 볼륨, 엔드포인트, 시크릿은 배포 전에 만들어 둡니다.
- **시크릿 리소스는 등록 확인.** 시크릿을 리소스로 연결한 뒤 설정이 반영되었는지, 서비스 프린시펄이 읽기 권한을 가지는지 배포 후 확인합니다.
- **앱 이름과 URL은 고정.** 이름을 바꾸려면 새 앱을 만듭니다.
- **상태 확인.** `Crashed` 상태면 Logs 탭에서 원인을 확인합니다(배포 절차는 다음 페이지).

## 참고 문서

- [Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [Key concepts in apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts)
- [Databricks 통합 인증](https://docs.databricks.com/aws/en/dev-tools/auth/unified-auth)
- [Databricks Apps와 함께 쓰기 (Lakebase)](../../10-lakebase/apps-integration.md)
- [Add resources to a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources)
