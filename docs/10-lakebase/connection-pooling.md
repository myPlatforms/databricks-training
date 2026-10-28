# 커넥션 풀링 (PgBouncer)

> 기준일: 2026-10-28 · 근거: 공식 문서

Lakebase에는 내장 PgBouncer 풀러가 있습니다. 여러 클라이언트 연결을 더 적은 서버 연결로 공유합니다. 풀러 사용은 선택 사항입니다.

| 항목 | 내용 |
|---|---|
| 풀 모드 | 트랜잭션 모드. 서버 연결은 트랜잭션 하나 동안만 점유 |
| 인증 요건 | **네이티브 Postgres 비밀번호 역할** 이어야 함. OAuth 역할은 사용 불가 |
| 풀러 호스트 | `<endpoint-id>-pooler.<region>.<cloud>.databricks.com` (읽기 전용 컴퓨트는 `<endpoint-id>-ro-pooler...`) |
| 포트 | 5432 |
| 최대 클라이언트 연결 (`max_client_conn`) | 10,000 |
| 풀 크기 (`default_pool_size`) | `max_connections`의 약 90% |
| 대기 시간 (`query_wait_timeout`) | 120초. 서버 연결이 2분 안에 비지 않으면 타임아웃 오류 |
| 직접 연결 수 (`max_connections`) | 컴퓨트 크기에 따라 다름 (문서 예: 8 CU 1,678개, 16 CU 3,357개) |

위 PgBouncer 설정값은 Lakebase가 고정하며 고객이 바꿀 수 없습니다. 트랜잭션 풀 모드, `max_prepared_statements=1000`도 같습니다.

### 트랜잭션 모드의 제약

문서가 적은 트랜잭션 모드의 제약은 다음과 같습니다.

- SQL 수준의 `PREPARE`와 `DEALLOCATE`는 지원되지 않습니다. 드라이버 수준의 프리페어드 문장은 PgBouncer 프로토콜 지원으로 동작합니다. JDBC에서 프리페어드 문장 오류가 나면 문서는 `prepareThreshold=0`을 제안합니다.
- `SET` 명령은 트랜잭션을 넘어 유지되지 않습니다. 설정을 지속시키려면 `ALTER ROLE ... SET`을 씁니다.
- 세션에 묶인 임시 테이블은 트랜잭션 사이에서 쓸 수 없습니다.
- `WITH HOLD` 커서, 어드바이저리 락(advisory lock)은 지원되지 않습니다.
- `LISTEN`/`NOTIFY`는 지원되지 않습니다. 발행·구독이 필요하면 직접 연결을 씁니다.
- `pg_dump`와 스키마 마이그레이션은 직접 연결을 씁니다.

```sql
-- 트랜잭션 안에서만 유효하므로 풀러에서는 기대대로 동작하지 않음
BEGIN;
SET search_path TO myschema;
SELECT * FROM mytable;
COMMIT;

-- 역할 단위로 지속 설정
ALTER ROLE myrole SET search_path TO myschema, public;
```

### 풀러를 쓸지 정하는 기준

| 상황 | 권장 연결 |
|---|---|
| 많은 짧은 쿼리를 많은 클라이언트가 보냄 | 풀러 + 네이티브 비밀번호 역할 |
| OAuth 토큰으로 인증해야 함 | 직접 연결 + 앱 쪽 연결 수 관리 |
| `LISTEN`/`NOTIFY`, `WITH HOLD` 커서, 세션 임시 테이블을 씀 | 직접 연결 |
| 마이그레이션, `pg_dump` | 직접 연결 |

> **주의** 풀러와 OAuth는 배타적입니다. OAuth 토큰을 쓰는 서비스에서 풀러를 기대하면 연결 방식부터 바꿔야 합니다. 이 점은 설계 단계에서 확정하십시오.

## 참고 문서

- [Connection pooling (AWS)](https://docs.databricks.com/aws/en/oltp/projects/connection-pooling)
- [Authentication (AWS)](https://docs.databricks.com/aws/en/oltp/projects/authentication)
- [연결과 인증 (이 장)](connect-and-auth.md)
