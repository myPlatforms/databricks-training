# 연결과 인증

> 기준일: 2026-10-28 · 근거: 공식 문서

Lakebase에 접속하는 방법은 두 가지입니다. **OAuth 토큰** 을 Postgres 비밀번호로 쓰는 방식과, Postgres **네이티브 비밀번호 역할** 을 쓰는 방식입니다. 이 페이지는 두 방식의 차이, 토큰 만료와 연결 수명, 역할과 권한, 커넥션 풀링을 다룹니다.

## 1. 왜 이 구조가 필요한가

애플리케이션이 Postgres에 접속할 때 보통 정적 비밀번호를 설정 파일이나 환경 변수에 둡니다. 이 방식에는 다음 문제가 있습니다.

- 비밀번호가 유출되면 권한 회수 전까지 계속 쓰일 수 있습니다.
- 사용자 퇴사나 권한 변경이 Postgres 역할에 바로 반영되지 않습니다.
- 감사 로그에서 실제 사람이나 서비스 주체를 식별하기 어렵습니다.

Lakebase는 Databricks 아이디(사용자, 서비스 프린시펄, 그룹)를 Postgres 역할과 연결하고, 짧은 수명의 OAuth 토큰을 비밀번호처럼 쓰게 합니다. 이렇게 하면 Databricks의 아이디 관리와 Postgres 권한이 같은 주체를 중심으로 묶입니다.

## 2. 두 가지 인증 방식

| 항목 | OAuth 토큰 | 네이티브 Postgres 비밀번호 |
|---|---|---|
| 주체 | Databricks 아이디(사용자, SP, 그룹) | Postgres 역할 이름 |
| 비밀번호 값 | 토큰 발급 API가 돌려준 `token` 값 | 역할에 설정한 비밀번호 |
| 만료 | 1시간 (로그인 시점에만 검사) | 자동 만료 없음 (수동 교체 필요) |
| 커넥션 풀러(PgBouncer) | 사용 불가 | 사용 가능 |
| 적합한 경우 | 사람·앱이 토큰을 주기적으로 갱신할 수 있을 때 | 토큰 갱신이 어렵거나 장기 실행 프로세스, 토큰 갱신을 지원하지 않는 도구 |
| 권장 SSL | `sslmode=require` | 문서 예시 모두 `sslmode=require` 사용 |

문서는 제3자 도구(예: pgAdmin, DBeaver)에는 네이티브 Postgres 비밀번호를 권장한다고 설명합니다. 이 도구들은 토큰 갱신을 지원하지 않을 수 있기 때문입니다.

> **참고** 네이티브 비밀번호 연결은 새 프로젝트에서 기본으로 비활성화되어 있다고 문서가 설명합니다. 활성화 방법은 문서의 "Manage password connections" 항목을 따릅니다.

## 3. OAuth 토큰을 비밀번호로 쓰는 방식

### 동작 원리

1. 클라이언트가 Databricks 아이디로 토큰을 발급받습니다. 토큰은 엔드포인트 경로 단위로 발급되며, 워크스페이스 범위입니다. 토큰은 프로젝트를 소유한 워크스페이스에서 나와야 합니다.
2. 클라이언트는 토큰 값을 Postgres 비밀번호 자리에 넣고 SSL로 접속합니다.
3. Postgres는 토큰이 유효한지 로그인 시점에 확인하고, 역할이 있는지 확인합니다.

발급된 토큰 응답에는 `token`과 `expire_time`이 들어 있습니다.

UI에서는 Lakebase 앱에서 **Connect** 를 열고, Role 드롭다운의 OAuth 역할을 고른 뒤, psql이 비밀번호를 물으면 **Copy OAuth token** 버튼으로 복사한 값을 붙여 넣습니다. 이 버튼은 **현재 로그인한 아이덴티티** 의 토큰만 만들며, 서비스 프린시펄이나 다른 사용자의 토큰은 만들지 않습니다. 그런 경우에는 CLI나 SDK를 씁니다.

### 토큰 발급 (CLI)

엔드포인트 경로 형식은 `projects/{project-id}/branches/{branch-id}/endpoints/{endpoint-id}`입니다.

```bash
databricks postgres generate-database-credential \
  projects/my-project/branches/production/endpoints/my-compute \
  --output json
```

응답에서 `token` 값을 꺼내 `PGPASSWORD`에 넣어 psql로 접속할 수 있습니다. 문서의 그룹 역할 예시가 이 방식을 씁니다.

```bash
export PGPASSWORD='<토큰 값>'
psql -h ep-abc-123.databricks.com -p 5432 -d databricks_postgres -U <역할 이름>
```

> **주의** 위 예시의 `ep-abc-123.databricks.com`과 `<토큰 값>`은 자리 표시자입니다. 토큰 값을 명령 기록이나 소스 코드에 남기지 마십시오.

### 토큰 발급 (Python SDK)

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
cred = w.postgres.generate_database_credential(
    endpoint="projects/my-project/branches/production/endpoints/my-compute"
)
print(cred.token)       # Postgres 비밀번호로 사용
print(cred.expire_time) # 만료 시각
```

문서는 Java SDK에도 같은 기능(`generateDatabaseCredential`, `GenerateDatabaseCredentialRequest`)이 있다고 설명합니다.

### 머신 투 머신(M2M) 인증

서비스 프린시펄(Service Principal)을 쓰면 장기 자격 증명으로 토큰을 발급받을 수 있습니다. 문서는 Python 예시에서 `WorkspaceClient`에 `host`, `client_id`, `client_secret`을 넘기는 방식을 보여 줍니다. 이 값들은 시크릿 저장소에 두어야 합니다.

## 4. 토큰 만료와 연결 수명

문서가 명시하는 시간 제한은 다음과 같습니다. 모든 인증 방식에 공통으로 적용됩니다.

| 제한 | 값 | 동작 |
|---|---|---|
| 토큰 만료 | 1시간 | 만료는 **로그인 시점에만** 강제됩니다. 이미 열린 연결은 토큰이 만료되어도 유지됩니다. |
| 유휴 시간 제한 | 24시간 | 활동이 없는 연결은 자동으로 닫힙니다. |
| 최대 연결 수명 | 3일 | 활동과 무관하게 3일을 넘긴 연결은 닫힐 수 있습니다. |

문서는 이 제한을 고려해 **재연결 로직을 구현하라고 권장합니다**.

### 토큰 재발급 패턴

문서는 두 가지 방법을 제시합니다.

- 사용할 때마다 토큰의 만료 시각을 확인하고, 임박하면 새로 발급합니다.
- 백그라운드 스레드에서 주기적으로 토큰을 갱신합니다.

다음은 새 연결을 열 때마다 토큰을 새로 발급하는 가장 단순한 형태입니다. 토큰 만료 시각을 계산하지 않아도 되므로 만료 처리 오류를 줄입니다.

```python
import psycopg
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
ENDPOINT = "projects/my-project/branches/production/endpoints/my-compute"
HOST = "ep-abc-123.databricks.com"
USER = "user@example.com"  # 본인 Databricks 아이디에 해당하는 Postgres 역할

def connect():
    token = w.postgres.generate_database_credential(endpoint=ENDPOINT).token
    return psycopg.connect(
        host=HOST,
        port=5432,
        dbname="databricks_postgres",
        user=USER,
        password=token,
        sslmode="require",
    )

with connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT now()")
        print(cur.fetchone())
```

> **참고** 위 코드는 새 연결을 열 때마다 토큰을 발급합니다. 연결 풀을 쓰면 풀이 새 연결을 만들 때 이 함수가 호출되도록 연결 생성 단계에 넣어야 합니다. 문서의 psycopg3 예시는 `ConnectionPool`과 커스텀 연결 클래스를 쓰며, 토큰을 연결마다 발급하는 구조입니다.

> **주의** 문서의 SQLAlchemy 토큰 갱신 예시는 만료 시각을 `credential.expire_time.seconds`로 계산합니다. 이 값이 항상 의도한 만료 시각을 주는지 확인하지 않은 채 복사하지 마십시오. 위 예시처럼 새 연결마다 발급하면 이 계산이 필요 없습니다.

## 5. 역할과 권한

### 기본 역할

프로젝트를 만들면 다음 역할이 자동으로 생깁니다.

- 프로젝트를 만든 사용자의 Databricks 아이디에 대한 역할. 기본 데이터베이스 `databricks_postgres`의 소유자입니다.
- `databricks_superuser` 관리 역할. 문서는 `pg_read_all_data`, `pg_write_all_data`, `pg_monitor`를 상속하는 광범위한 권한이라고 설명합니다.

Azure 문서는 Lakebase UI에서 만든 모든 역할이 `databricks_superuser` 권한으로 생성된다고 설명합니다. 권한 최소화를 원하면 UI에서 만든 역할의 권한을 AWS 문서의 역할 관리 절차대로 점검하십시오.

### OAuth 역할 만들기

OAuth 역할은 Databricks 아이디(사용자, 서비스 프린시펄, 그룹)마다 만듭니다. 문서의 SQL 예시는 다음과 같습니다. 확장(`databricks_auth`)은 각 데이터베이스에 따로 설치합니다.

```sql
CREATE EXTENSION IF NOT EXISTS databricks_auth;

-- 사용자
SELECT databricks_create_role('user@example.com', 'USER');

-- 서비스 프린시펄 (애플리케이션 ID, UUID)
SELECT databricks_create_role('8c01cfb1-62c9-4a09-88a8-e195f4b01b08', 'SERVICE_PRINCIPAL');

-- 그룹 (워크스페이스 그룹 이름, 대소문자 구분)
SELECT databricks_create_role('My Group Name', 'GROUP');
```

같은 작업을 CLI로 할 때의 예시는 다음과 같습니다.

```bash
databricks postgres create-role projects/my-project/branches/production \
  --role-id my-user-role \
  --json '{"spec": {"identity_type": "USER", "postgres_role": "user@example.com"}}'
```

> **주의** 역할은 `LOGIN` 권한만 가진 상태로 만들어집니다. 테이블 권한은 따로 GRANT해야 합니다. OAuth 역할을 만들려면 `CREATE`와 `CREATE ROLE` 권한, 그리고 OAuth 세션이 필요합니다. 네이티브 Postgres 세션으로는 만들 수 없습니다.

### 그룹 역할

그룹용 역할을 만들면 그룹의 직접·간접 구성원(사용자, 서비스 프린시펄)이 각자의 OAuth 토큰으로 그룹 역할에 접속할 수 있습니다. 그룹 역할에 준 GRANT는 현재 구성원과 앞으로의 구성원에게 자동 적용됩니다. 구성원 여부는 인증 시점에만 확인하므로, 이미 열린 연결은 그룹에서 빠져도 유지됩니다. 워크스페이스에 할당된 그룹만 지원됩니다.

### 네이티브 비밀번호 역할

```sql
CREATE ROLE role_name WITH LOGIN PASSWORD 'your_secure_password';
```

```bash
databricks postgres create-role projects/my-project/branches/production \
  --role-id my-app-role \
  --json '{"spec": {"postgres_role": "my-app-role"}}'
```

- 비밀번호는 최소 12자이며 소문자, 대문자, 숫자, 기호를 포함해야 합니다. 사용자가 정한 비밀번호는 60비트 이상의 엔트로피 검사를 받습니다.
- SDK, CLI, API는 생성된 비밀번호를 돌려주지 않습니다. SQL로 설정하거나 UI의 **Reset password** 흐름을 사용합니다.
- Postgres에는 평문이 아니라 SCRAM-SHA-256 검증자가 저장됩니다.

### 권한 부여와 역할 정리

| 작업 | 방법 |
|---|---|
| 권한 부여 | 역할을 만든 뒤 GRANT를 별도로 실행 (역할은 LOGIN만 가짐) |
| 관리자 역할 부여 | `databricks postgres update-role`로 `spec.membership_roles`에 `DATABRICKS_SUPERUSER` 지정. 빈 배열이면 제거 |
| 역할 삭제 | `DROP ROLE` 또는 `databricks postgres delete-role`. 객체를 소유한 역할은 소유권을 먼저 넘겨야 함 |
| 사용자·그룹 이름 변경 | 인증이 깨지므로 역할을 삭제하고 다시 만든 뒤 권한과 연결 문자열을 갱신 |

> **주의** 역할 이름은 63자를 넘을 수 없으며, 일부 이름은 허용되지 않습니다. SDK, REST API, Terraform으로 만든 역할은 내부 컨트롤 플레인 역할이 소유하므로, 고객이 SQL로 비밀번호를 바꿀 수 없습니다(Postgres 16에서는 `ADMIN` 옵션 필요). 이 경우 UI의 **Reset password** 흐름을 사용하십시오.

> **주의** 역할 삭제는 되돌릴 수 없습니다. 삭제된 아이디는 새 역할을 만들기 전까지 OAuth로 인증할 수 없습니다.

## 6. 클라이언트 도구

문서는 표준 Postgres 클라이언트를 쓸 수 있다고 설명하며, psql, pgAdmin, DBeaver, PgHero를 예로 듭니다. 연결 정보는 Lakebase 앱의 **Connect** 대화 상자에서 얻습니다.

| 항목 | 값 |
|---|---|
| 호스트 | 컴퓨트 엔드포인트 호스트 이름 |
| 포트 | 5432 |
| 데이터베이스 | 예: `databricks_postgres` |
| 사용자 | Postgres 역할 이름 |
| 비밀번호 | 네이티브 역할 비밀번호, 또는 OAuth 토큰 |

클라이언트 쪽 방화벽을 쓰면 Lakebase IP 주소를 허용 목록에 넣어야 한다고 문서가 안내합니다. IP 주소와 도메인은 "IP addresses and domains for Databricks services" 문서를 확인하십시오.

Django 예시(문서 원문):

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'databricks_postgres',
        'USER': 'role_name',
        'PASSWORD': 'password',
        'HOST': 'ep-abc-123.databricks.com',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

## 7. 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| OAuth 토큰 | 비밀번호 저장 불필요, 아이디 기반 감사, 역할 회수 쉬움 | 토큰 갱신 코드 필요, 풀러 사용 불가 |
| 네이티브 비밀번호 | 풀러 사용, 도구 호환성 높음 | 비밀번호 수동 교체, 시크릿 관리 필요 |

## 8. 주의사항

- **토큰을 로그나 코드에 남기지 않습니다.** 토큰은 비밀번호와 같습니다.
- **재연결 로직을 넣습니다.** 유휴 24시간, 최대 3일 제한과 컴퓨트 재시작으로 연결은 끊깁니다. 지수 백오프 재시도를 권장합니다.
- **풀링 방식을 먼저 정합니다.** OAuth와 풀러가 배타적이므로, 설계 초기에 인증 방식과 풀링 방식을 함께 정하십시오.
- **권한을 역할 단위로 분리합니다.** 서비스 프린시펄마다 역할을 만들고 필요한 권한만 GRANT하십시오. UI로 만든 역할은 기본적으로 관리자 권한을 가진다는 Azure 문서 설명을 확인하십시오.
- **SSL을 강제합니다.** 문서 예시는 모두 `sslmode=require`를 씁니다.

## 참고 문서

- [Authentication (AWS)](https://docs.databricks.com/aws/en/oltp/projects/authentication)
- [Connection quickstart (AWS)](https://docs.databricks.com/aws/en/oltp/projects/connect-overview)
- [Connection pooling (AWS)](https://docs.databricks.com/aws/en/oltp/projects/connection-pooling)
- [Postgres roles (AWS)](https://docs.databricks.com/aws/en/oltp/projects/postgres-roles)
- [Postgres clients (AWS)](https://docs.databricks.com/aws/en/oltp/projects/postgres-clients)
- [Connect to your project (AWS)](https://docs.databricks.com/aws/en/oltp/projects/connect)
- [Manage projects (Azure) — 역할 설명](https://learn.microsoft.com/en-us/azure/databricks/oltp/projects/manage-projects)
