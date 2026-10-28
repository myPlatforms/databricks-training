# Databricks Apps와 함께 쓰기

> 기준일: 2026-10-28 · 근거: 공식 문서

Databricks Apps는 워크스페이스 안에서 웹 애플리케이션을 만들고 배포하는 기능입니다. 앱에 Lakebase 데이터베이스를 **리소스로 바인딩** 하면, 플랫폼이 앱 전용 서비스 프린시펄(Service Principal)과 Postgres 역할을 만들고 연결 정보를 환경 변수로 주입합니다. 이 페이지는 바인딩 절차, 주입되는 환경 변수, 앱의 서비스 프린시펄이 받는 권한, 코드에서 연결하는 방법을 다룹니다.

> **참고** 이 페이지의 상태 라벨은 문서에 없습니다. 앱 리소스 바인딩은 Lakebase와 Databricks Apps 각각의 상태를 따릅니다. 배포 전에 워크스페이스에서 두 기능의 가용성을 확인하십시오. Azure 문서는 Lakebase와 서버리스 컴퓨트가 켜져 있어야 한다고 전제합니다.

## 1. 왜 필요한가

Databricks Apps로 만든 앱이 데이터를 저장하려면 보통 다음 작업이 필요합니다.

- 데이터베이스 인스턴스 접속 정보를 앱 설정에 넣습니다.
- 비밀번호나 토큰을 시크릿으로 관리하고 교체합니다.
- 앱 전용 DB 계정을 따로 만들고 권한을 부여합니다.

Lakebase 리소스 바인딩은 이 작업의 대부분을 플랫폼이 맡습니다. 앱 서비스 프린시펄, 대응하는 Postgres 역할, 권한 부여, 연결 환경 변수가 자동으로 준비되므로 앱 코드에 접속 정보를 넣지 않아도 됩니다.

## 2. 어떻게 동작하는가

| 단계 | 플랫폼이 하는 일 |
|---|---|
| 리소스 바인딩 | 앱에 Lakebase 데이터베이스(프로젝트·브랜치·데이터베이스)를 리소스로 연결 |
| 서비스 프린시펄 | 앱은 자기 전용 서비스 프린시펄로 실행 (사용자 개인 계정이 아님) |
| 역할 생성 | 서비스 프린시펄과 대응하는 Postgres 역할을 자동 생성 |
| 권한 부여 | 그 역할에 데이터베이스 전체 접근 권한을 부여 (문서는 "full database access"라고 설명, 세부 권한 목록은 명시 없음) |
| 스키마 생성 | 앱 전용 스키마를 `{app-name}_schema_{service-principal-id}` 형식으로 만듦. 서비스 프린시펄 ID에서 하이픈을 뺀 값 |
| 환경 변수 주입 | 연결 정보를 앱 환경 변수로 주입 |

> **참고** 스키마 이름은 나중에 바꿀 수 있다고 문서가 설명합니다. 앱 이름 자체는 생성 후 바꿀 수 없다고 Azure 문서가 설명합니다.

## 3. 리소스 바인딩 절차 (UI)

문서의 UI 절차는 다음과 같습니다.

1. 앱 스위처에서 **Databricks Apps** 를 선택하고 **+ Create app** 을 클릭합니다.
2. **Database** 탭에서 템플릿을 고릅니다. 문서가 제시하는 템플릿은 Dash, Flask, Streamlit의 할 일(todos) 앱입니다.
3. **Configure** 단계의 **App resources** 에서 Lakebase 프로젝트, 브랜치, 데이터베이스를 고릅니다. 브랜치는 ID로 표시되므로 프로젝트의 브랜치 페이지에서 이름과 대응을 확인합니다.
4. **Compute size** 를 고릅니다. 문서 예시는 **Medium** 입니다. 이 값은 앱 서버 컴퓨트이며 Lakebase 데이터베이스 컴퓨트와 별도로 확장됩니다.
5. 권한 검토 화면에서 서비스 프린시펄 권한을 확인하고 **Create app** 을 클릭합니다.
6. 배포는 약 2–3분 걸리며, 상태가 **Running** 이 되면 앱 URL을 엽니다.

기존 앱에 리소스를 추가하는 방법은 문서의 "Add a Lakebase resource to a Databricks app" 절을 참조합니다. 이 페이지 근거 문서에는 `databricks.yml`이나 `app.yaml`의 리소스 선언 예시가 없었습니다. 따라서 이 장에서는 YAML 예시를 쓰지 않습니다.

## 4. 주입되는 환경 변수

문서 원문의 환경 변수 목록입니다.

| 환경 변수 | 설명 (문서 원문 요지) |
|---|---|
| `PGAPPNAME` | 앱 이름 |
| `PGDATABASE` | 데이터베이스 이름 |
| `PGHOST` | Postgres 서버 호스트 이름 |
| `PGPORT` | Postgres 서버 포트 |
| `PGSSLMODE` | 연결의 SSL 모드 |
| `PGUSER` | 서비스 프린시펄의 클라이언트 ID이자 역할 이름 |

> **주의** 환경 변수가 주입되는 것은 ** 첫 번째 데이터베이스 리소스** 입니다. 여러 데이터베이스를 바인딩하면 환경 변수는 첫 번째 것만 반영합니다. 문서는 나머지 연결 정보를 얻으려면 리소스 키와 함께 `valueFrom`을 쓰라고 안내합니다.

> **주의** 문서가 나열한 환경 변수에는 ** 비밀번호나 토큰 변수가 없습니다**. 그래서 앱이 Postgres 비밀번호를 어떻게 얻는지는 이 장의 근거 문서에서 확인하지 못했습니다. 아래 코드 예시는 앱의 `WorkspaceClient`로 토큰을 발급하는 방식이며, 문서가 명시한 조합이지만 실제 배포에서 한 번 검증하십시오.

## 5. 서비스 프린시펄과 권한

- 앱은 서비스 프린시펄 하나로 실행됩니다. 이 프린시펄은 플랫폼이 자동으로 제공하므로 직접 만들 필요가 없습니다.
- 바인딩하면 같은 프린시펄의 Postgres 역할이 생기고 데이터베이스 전체 접근이 부여된다고 문서가 설명합니다. 세부 권한 목록은 명시되지 않았습니다.
- 앱 SDK 호출(`WorkspaceClient`)은 앱의 아이덴티티를 자동으로 씁니다. 문서 비교 표는 "WorkspaceClient uses app identity automatically (no credentials in code)"라고 적습니다.
- 앱에서 다른 사용자의 데이터를 접근하는 방식은 이 페이지에서 다루지 않습니다.

> **참고** 서비스 프린시펄 역할은 `PGUSER` 값과 같은 클라이언트 ID를 씁니다. 이 역할에 최소 권한만 주려면 바인딩 후 GRANT로 권한을 줄일 수 있는지 확인하십시오. 문서는 기본 부여 권한을 줄이는 절차를 이 페이지에서 설명하지 않습니다.

## 6. 코드에서 연결하기

문서는 앱 코드 예시 전체를 제공하지 않았습니다. 아래 예시는 문서에서 확인된 요소를 조합한 것입니다.

- 환경 변수 이름(`PGHOST`, `PGDATABASE`, `PGUSER`, `PGPORT`, `PGSSLMODE`)은 문서 원문입니다.
- `WorkspaceClient()`가 앱 아이덴티티를 자동 사용한다는 설명은 문서 원문입니다.
- `generate_database_credential(endpoint=...)`는 [연결과 인증](connect-and-auth.md)의 API입니다.
- 엔드포인트 경로는 환경 변수로 주입되지 않습니다. 앱 설정이나 상수로 직접 넣어야 합니다.

```python
import os

import psycopg
from databricks.sdk import WorkspaceClient

# 엔드포인트 경로는 주입되지 않으므로 앱 설정으로 전달합니다 (예시 값)
ENDPOINT = os.environ.get(
    "LAKEBASE_ENDPOINT",
    "projects/my-project/branches/production/endpoints/my-compute",
)

w = WorkspaceClient()  # 앱 서비스 프린시펄을 자동으로 사용

def connect():
    token = w.postgres.generate_database_credential(endpoint=ENDPOINT).token
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=token,
        sslmode=os.environ.get("PGSSLMODE", "require"),
    )
```

> **주의** `PGUSER`는 서비스 프린시펄의 클라이언트 ID입니다. 이 값을 쓰는 역할이 실제로 바인딩 시 만들어진 역할과 일치하는지 연결 테스트로 확인하십시오. 위 코드는 연결 수명 제한(유휴 24시간, 최대 3일)에 대응하기 위해 새 연결마다 토큰을 발급합니다. 연결 풀을 쓸 때는 풀 생성 단계에서 이 함수를 호출하십시오.

## 7. 콜드 스타트와 스케일 투 제로

- Lakebase는 유휴 상태에서 스케일 투 제로로 일시 중지될 수 있습니다. 문서는 그 뒤 첫 쿼리가 몇 초 걸릴 수 있다고 설명합니다.
- 앱의 첫 요청은 지연이 크게 보일 수 있으므로 재시도와 타임아웃을 설계에 넣으십시오.
- 연결 자체는 [연결과 인증](connect-and-auth.md)의 재연결 로직을 따릅니다.

## 8. 트레이드오프

| 항목 | 장점 | 주의 |
|---|---|---|
| 플랫폼 자동 구성 | 서비스 프린시펄, 역할, 환경 변수 자동 준비 | 권한 범위가 기본값(전체 접근)이므로 최소 권한 설계가 어려울 수 있음 |
| 비밀 저장 불필요 | 앱 코드에 접속 정보 없음 (문서 설명) | 토큰 발급과 갱신 로직은 앱이 직접 구현 |
| 템플릿 | Dash, Flask, Streamlit 템플릿으로 빠른 시작 | 템플릿은 할 일 앱 예시이므로 실제 설계에 그대로 쓰기 어려움 |

## 9. 주의사항

- **첫 번째 리소스만 환경 변수에 반영됩니다.** 여러 데이터베이스를 쓰면 `valueFrom`으로 나머지를 가져오십시오.
- **비밀번호 변수가 주입되지 않습니다.** 토큰 발급 로직을 앱에 구현하십시오.
- **스키마 이름과 앱 이름을 기록해 둡니다.** Unity Catalog에 등록하면 스키마 이름에 하이픈이 남아 백틱으로 감싸야 합니다(Azure 문서 예시).
- **앱 서버 컴퓨트와 Lakebase 컴퓨트는 별도입니다.** 두 컴퓨트의 크기와 비용을 따로 계산하십시오.

### Unity Catalog에서 앱 데이터 조회 (Azure 문서 예시)

Lakebase 프로젝트를 Unity Catalog에 등록하면 Databricks SQL에서 앱 테이블을 레이크하우스 테이블과 함께 조인할 수 있습니다. Azure 문서는 하이픈이 있는 카탈로그와 스키마 이름을 백틱으로 감싸는 예를 보입니다.

```sql
SELECT * FROM `your-catalog-name`.`lakebase-autoscaling-app_schema_aeb6ff9198ff4752af7dfc6d4cf570d0`.todos;
```

> **참고** 카탈로그 등록 방법과 카탈로그 종류(Lakebase Postgres, Autoscaling)는 Azure 문서의 "Register a Lakebase database in Unity Catalog" 절에서 확인하십시오. 이 장에서는 등록 절차를 다루지 않습니다.

## 참고 문서

- [Build applications with Lakebase (AWS)](https://docs.databricks.com/aws/en/oltp/projects/build-applications)
- [Databricks Apps로 Lakebase 사용 (AWS)](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps)
- [Add a Lakebase resource to a Databricks app (AWS)](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
- [Using Lakebase with Databricks Apps (Azure)](https://learn.microsoft.com/en-us/azure/databricks/oltp/projects/databricks-apps)
- [연결과 인증 (이 장)](connect-and-auth.md)
