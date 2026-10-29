# 커넥션 풀링 (PgBouncer)

> 기준일: 2026-10-29 · 근거: 공식 문서

Lakebase에는 내장 PgBouncer 풀러(connection pooler)가 있습니다. 여러 클라이언트 연결을 더 적은 서버 연결로 공유합니다. 풀러 사용은 선택 사항이며, 같은 컴퓨트에 직접 연결하는 방식과 함께 쓸 수 있습니다. 이 페이지는 풀러의 동작, 쓸 수 없는 기능, 애플리케이션 측 풀과의 차이, 그리고 OAuth 인증과의 관계를 정리합니다.

> **참고** Connection pooling 문서 페이지에는 기능 상태 라벨(GA, Public Preview 등)이 표시되어 있지 않습니다. 사용 중인 워크스페이스에서 스위치가 보이는지 먼저 확인하십시오.

## 1. 왜 필요한가

Postgres 서버는 연결 하나마다 자원을 씁니다. 연결 수가 `max_connections`에 가까워지면 새 연결이 거절됩니다. 서버리스 함수, 짧은 요청을 많이 받는 웹 서비스처럼 클라이언트가 많고 쿼리가 짧은 워크로드에서 이 한계가 먼저 드러납니다.

직접 연결만 쓰면 다음 문제가 생깁니다.

| 문제 | 직접 연결만 쓸 때 |
|---|---|
| 연결 수 상한 | 컴퓨트 크기에 묶입니다. 문서 예시는 8 CU에서 직접 연결 1,678개, 16 CU에서 3,357개입니다. |
| 유휴 연결 비용 | 클라이언트가 트랜잭션 사이에 쉬어도 서버 연결은 점유됩니다. |
| 급격한 동시 접속 | 요청이 몰리면 연결 생성 자체가 병목이 됩니다. |

풀러는 클라이언트 연결(client connection)과 서버 연결(server connection)을 분리합니다. 클라이언트는 많이 붙고, 서버 쪽은 풀 크기만큼만 유지됩니다.

## 2. 어떻게 동작하는가

### 2.1 트랜잭션 모드

풀 모드는 **트랜잭션 모드(transaction mode)** 입니다. 서버 연결은 트랜잭션 하나가 진행되는 동안만 클라이언트에 묶입니다. 트랜잭션이 끝나면 서버 연결은 풀로 돌아가 다른 클라이언트가 씁니다. 그래서 클라이언트가 트랜잭션 사이에 대기해도 서버 연결을 낭비하지 않습니다.

이 방식의 대가는 **세션 상태가 트랜잭션을 넘어 이어지지 않는다는 점** 입니다. 같은 클라이언트가 다음 트랜잭션을 시작할 때 다른 서버 연결을 받을 수 있기 때문입니다. 아래 2.3절의 제약이 모두 여기서 나옵니다.

### 2.2 고정 설정값

다음 PgBouncer 설정은 Lakebase가 고정하며 고객이 바꿀 수 없습니다.

| 설정 | 값 (문서 기준) | 의미 |
|---|---|---|
| `pool_mode` | `transaction` | 트랜잭션 단위로 서버 연결 반환 |
| `max_client_conn` | `10000` | 풀러가 받는 최대 클라이언트 연결 |
| `default_pool_size` | `max_connections`의 약 90% | (사용자, 데이터베이스) 쌍마다의 서버 연결 수. 컴퓨트 크기에 따라 달라짐 |
| `max_prepared_statements` | `1000` | 클라이언트 연결당 프로토콜 수준 프리페어드 문장 추적 수 |
| `query_wait_timeout` | `120`초 | 서버 연결을 기다리는 최대 시간. 2분 안에 연결을 얻지 못하면 타임아웃 오류 |

풀 크기는 고정 숫자가 아니라 컴퓨트 크기에 따라 바뀝니다. 오토스케일링으로 CU가 바뀌면 직접 연결 상한과 풀 크기도 함께 바뀝니다.

### 2.3 연결 문자열과 호스트

풀러 연결과 직접 연결은 **호스트 이름이 다릅니다.** 읽기-쓰기와 읽기 전용 컴퓨트에 따라 아래처럼 나뉩니다.

| 연결 방식 | 호스트 형식 | 포트 |
|---|---|---|
| 풀러, 읽기-쓰기 | `<endpoint-id>-pooler.<region>.<cloud>.databricks.com` | 5432 |
| 풀러, 읽기 전용 컴퓨트 | `<endpoint-id>-ro-pooler.<region>.<cloud>.databricks.com` | 5432 |
| 직접 연결 | Connect 대화상자에서 **Connection pooling** 스위치를 끈 상태의 연결 문자열 | 문서에 별도 명시 없음 |

문서는 직접 연결의 호스트 형식을 따로 적지 않습니다. 직접 연결 문자열은 Connect 대화상자에서 복사합니다.

> **주의** 풀러 스위치는 **네이티브 Postgres 비밀번호 역할** 을 선택했을 때만 나타납니다. OAuth 역할을 고르면 스위치 자체가 보이지 않습니다.

### 2.4 인증 요건

풀러는 **네이티브 Postgres 비밀번호 역할** 만 받습니다. OAuth 토큰으로 인증하는 역할은 풀러를 쓸 수 없습니다. 인증 문서는 두 방식을 다음과 같이 비교합니다.

| 항목 | OAuth 토큰 | Postgres 비밀번호 |
|---|---|---|
| 자격 증명 수명 | 1시간 | 자동 만료 없음 |
| 갱신 | 앱이 토큰을 갱신해야 함 | 수동 교체와 배포 |
| 내장 풀러 | 지원하지 않음 | 지원 |
| 적합한 용도 | 대화형 세션, 토큰 갱신이 가능한 앱 | 1시간마다 갱신할 수 없는 앱, 장기 실행 프로세스 |

비밀번호 연결은 새 프로젝트에서 기본으로 꺼져 있습니다. 활성화 방법은 인증 문서의 **Manage password connections** 절을 따릅니다.

## 3. 어떻게 쓰는가

### 3.1 풀러 연결 예시 (Python)

풀러 호스트와 네이티브 비밀번호 역할로 연결하는 최소 예시입니다. 호스트와 역할 이름은 Connect 대화상자의 값으로 바꿉니다. 비밀번호는 코드에 넣지 않고 환경 변수에서 읽습니다.

```python
import os
import psycopg

# 풀러 호스트: Connect 대화상자에서 Connection pooling을 켠 값
conn = psycopg.connect(
    host="<endpoint-id>-pooler.<region>.<cloud>.databricks.com",
    port=5432,
    dbname="databricks_postgres",
    user="<네이티브 비밀번호 역할 이름>",
    password=os.environ["LAKEBASE_PASSWORD"],
    sslmode="require",
)

with conn.cursor() as cur:
    cur.execute("SELECT now()")
    print(cur.fetchone())
conn.close()
```

> **참고** 위 예시는 문서의 호스트 형식과 인증 문서의 연결 예시(`sslmode=require`)를 조합한 것입니다. 풀러 연결 전용 코드 예시는 문서에 없습니다.

### 3.2 JDBC에서 프리페어드 문장 오류 해결

JDBC 드라이버가 서버 측 프리페어드 문장을 캐시하면 트랜잭션 모드에서 오류가 날 수 있습니다. 문서는 이때 `prepareThreshold=0`을 제안합니다. 이 값은 이름 붙은 서버 측 프리페어드 문장 캐시를 끕니다.

```text
jdbc:postgresql://<endpoint-id>-pooler.<region>.<cloud>.databricks.com:5432/databricks_postgres?sslmode=require&prepareThreshold=0
```

### 3.3 세션 설정을 유지하는 방법

`SET`으로 바꾼 설정은 트랜잭션이 끝나면 사라집니다. 문서의 예시는 다음과 같습니다.

```sql
-- 트랜잭션 안에서만 유효하므로 풀러에서는 기대대로 동작하지 않음
BEGIN;
SET search_path TO myschema;
SELECT * FROM mytable;   -- COMMIT 뒤의 다른 트랜잭션에서는 mytable을 찾지 못할 수 있음
COMMIT;

-- 역할 단위로 지속 설정
ALTER ROLE myrole SET search_path TO myschema, public;
```

문서의 예시 출력은 `COMMIT` 뒤에 `SELECT * FROM mytable;`이 `ERROR: relation "mytable" does not exist`로 실패하는 경우를 보여 줍니다. 역할 단위 설정은 연결이 바뀌어도 유지됩니다.

### 3.4 연결 방식을 고르는 기준

| 상황 | 권장 연결 | 근거 |
|---|---|---|
| 많은 짧은 쿼리를 많은 클라이언트가 보냄 | 풀러 + 네이티브 비밀번호 역할 | 트랜잭션 모드의 목적에 맞음 |
| OAuth 토큰으로 인증해야 함 | 직접 연결 + 앱 쪽 연결 수 관리 | 풀러는 OAuth를 받지 않음 |
| `LISTEN`/`NOTIFY`를 씀 | 직접 연결 | 풀러에서 지원하지 않음 |
| `WITH HOLD` 커서, 세션 임시 테이블, 어드바이저리 락을 씀 | 직접 연결 | 풀러에서 지원하지 않음 |
| 마이그레이션, `pg_dump` | 직접 연결 | 문서가 직접 연결을 지정 |

## 4. 트레이드오프

Lakebase 풀러, 직접 연결, 애플리케이션 측 풀은 서로 대체재가 아니라 역할이 다릅니다. 문서가 다루는 범위는 풀러와 직접 연결입니다. 애플리케이션 측 풀은 문서 본문이 다루지 않으므로 아래 표의 해당 칸은 일반적인 드라이버 사용 방식을 기준으로 합니다.

| 항목 | 내장 풀러 (트랜잭션 모드) | 직접 연결 | 애플리케이션 측 풀 (예: psycopg_pool) |
|---|---|---|---|
| 서버 연결 수 제어 | 풀러가 관리, 고정 설정 | 클라이언트 수만큼 점유 | 앱 프로세스 단위로 제한 |
| 인증 | 네이티브 비밀번호 역할만 | 비밀번호 또는 OAuth | 직접 연결 방식을 따름 |
| 세션 상태 (SET, 임시 테이블, LISTEN) | 트랜잭션 사이 유지 안 됨 | 유지됨 | 직접 연결 방식을 따름 |
| 설정 위치 | 고정(고객 변경 불가) | 해당 없음 | 앱 코드 |
| 문서 근거 | 있음 | 있음 | 없음 (Lakebase 문서 범위 밖) |

> **참고** 애플리케이션 측 풀을 Lakebase 직접 연결 앞에 두면 풀러의 이점은 없고 연결 관리만 남습니다. 연결 수 상한이 문제이면 풀러를 먼저 검토하고, OAuth 토큰 갱신이 필요하면 앱 측 풀을 쓰는 것이 문서의 패턴과 맞습니다.

### 4.1 OAuth와 앱 측 풀

OAuth를 써야 하면 풀러는 쓸 수 없고, 앱 측 풀을 직접 연결 앞에 둡니다. 인증 문서는 `psycopg_pool`의 `ConnectionPool`을 상속한 연결 클래스에서 연결을 만들 때마다 새 OAuth 토큰을 발급하는 패턴을 보여 줍니다. 문서는 이 방식이 "each connection from the pool always has a valid, current token"을 보장한다고 설명합니다. SQLAlchemy 예시는 `do_connect` 이벤트에서 토큰 만료 2분 전부터 새 토큰을 받습니다.

토큰과 연결의 수명은 다음과 같습니다.

| 항목 | 문서 기준 |
|---|---|
| OAuth 토큰 수명 | 1시간 |
| 만료 검사 시점 | 로그인할 때만 검사. 열린 연결은 토큰이 만료돼도 유지됨 |
| 유휴 연결 | 24시간 활동이 없으면 자동 종료 |
| 최대 수명 | 3일이 지나면 활동과 무관하게 종료될 수 있음 |

## 5. 주의사항

- **풀러와 OAuth는 배타적입니다.** OAuth 토큰을 쓰는 서비스에 풀러를 붙일 계획이면 설계 단계에서 인증 방식을 먼저 정하십시오.
- **`query_wait_timeout`은 120초입니다.** 풀이 가득 찬 상태에서 2분 넘게 기다리면 타임아웃 오류가 납니다. 쿼리를 길게 잡는 워크로드는 풀러 대신 직접 연결을 검토하십시오.
- **`SET`은 연결 설정이 아닙니다.** 트랜잭션 밖에서 설정했다고 다음 요청에 남아 있지 않습니다. 설정이 필요하면 `ALTER ROLE ... SET`을 씁니다.
- **프리페어드 문장 오류는 드라이버 설정으로 먼저 해결합니다.** JDBC는 `prepareThreshold=0`을 확인하십시오.
- **스케일 투 제로 이후 재활성화 시 풀이 초기화됩니다.** 문서는 재활성화 때 커넥션 풀을 포함한 세션 상태가 초기화된다고 설명합니다. 풀이 오래된 연결을 들고 있으면 첫 요청이 실패할 수 있으므로 재시도와 연결 검증을 넣으십시오. 자세한 내용은 [컴퓨트와 스케일링](compute-and-scaling.md)을 보십시오.
- **읽기 전용 컴퓨트는 `-ro-pooler` 호스트를 씁니다.** 호스트 형식은 위 2.3절 표를 따릅니다. 읽기 전용 컴퓨트 설정은 [컴퓨트와 스케일링](compute-and-scaling.md)을 참고하십시오.
- **마이그레이션과 백업은 직접 연결로 합니다.** `pg_dump`와 스키마 변경이 풀러를 거치면 트랜잭션 모드 제약에 걸릴 수 있습니다.
- **풀 크기는 컴퓨트 크기에 따릅니다.** 오토스케일링 범위를 넓히면 풀 크기도 커지지만, 문서가 제시한 숫자는 예시일 뿐 고정 보장이 아닙니다. 실제 값은 Connect 대화상자와 컴퓨트 설정에서 확인하십시오.

## 참고 문서

- [Connection pooling (AWS)](https://docs.databricks.com/aws/en/oltp/projects/connection-pooling)
- [Authentication (AWS)](https://docs.databricks.com/aws/en/oltp/projects/authentication)
- [Lakebase Postgres 프로젝트 개요 (AWS)](https://docs.databricks.com/aws/en/oltp/projects/)
- [Scale to zero (AWS)](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)
- [연결과 인증 (이 장)](connect-and-auth.md)
- [컴퓨트와 스케일링 (이 장)](compute-and-scaling.md)
