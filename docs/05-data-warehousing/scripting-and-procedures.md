# SQL 스크립팅과 저장 프로시저

> 기준일: 2026-10-28 · 근거: 공식 문서

SQL 스크립팅(SQL scripting)은 여러 SQL 문장을 `BEGIN ... END` 블록으로 묶고, 변수·조건문·반복문·예외 처리를 SQL 안에서 쓰게 해주는 기능입니다. 저장 프로시저(Stored procedure)는 이 스크립트를 Unity Catalog 객체로 저장해 `CALL`로 재사용하는 방식입니다.

> **참고** 이 페이지의 상태 정보는 공식 문서 원문 기준입니다. 공식 문서 페이지에 상태 라벨(GA, Public Preview, Beta)은 표시되어 있지 않아, 상태 칸에는 "라벨 없음(원문 기준)"으로 적습니다.

## 왜 필요한가

분석 파이프라인에는 "전날 데이터가 있으면 처리하고, 없으면 종료", "여러 테이블을 순서대로 갱신하고 실패하면 롤백" 같은 절차가 있습니다. 이런 절차를 노트북이나 외부 오케스트레이션 코드로만 구현하면, 같은 로직을 다른 도구에서 다시 쓰기 어렵습니다. 스크립팅과 프로시저는 로직을 데이터 옆(SQL)에 두어 재사용과 권한 통제를 가능하게 합니다.

| 이전 방식의 한계 | 스크립팅·프로시저의 접근 |
|---|---|
| 절차 로직이 노트북마다 흩어짐 | `CREATE PROCEDURE`로 한 번 정의하고 `CALL`로 재사용 |
| 실행 권한과 데이터 권한이 얽힘 | `SQL SECURITY INVOKER`와 `DEFINER`로 실행 주체를 선택 |
| 조건 분기를 외부 코드로 처리 | `IF`, `CASE`, `WHILE`, `FOR` 같은 제어 문장 사용 |

## 어떻게 동작하는가

### 스크립트의 구조

스크립트의 기본 단위는 `BEGIN ... END` 복합 문장(compound statement)입니다. 공식 문서는 블록의 선언부에서 로컬 변수, 커서, 사용자 정의 조건, 조건 핸들러를 선언한다고 설명합니다.

공식 문서가 나열하는 제어 문장은 다음과 같습니다.

| 문장 | 역할 (문서 설명 기준) |
|---|---|
| `BEGIN ... END` | 복합 문장. 선언부와 본문을 묶음 |
| `SET` | 로컬 변수와 세션 변수에 값을 설정 |
| `IF THEN ELSE`, `CASE` | 조건 분기 |
| `WHILE`, `LOOP`, `REPEAT` | 반복. `LEAVE`로 빠져나오고 `ITERATE`로 다음 반복으로 넘어감 |
| `FOR` | 쿼리 결과의 행을 순회 |
| `SIGNAL`, `RESIGNAL` | 새 예외를 발생시키거나, 핸들러 안에서 원래 예외를 다시 발생 |
| `GET DIAGNOSTICS` | 진단 정보를 가져옴 (문서에 세부 문법 없음) |
| `OPEN`, `FETCH`, `CLOSE` | 커서 처리. Databricks Runtime 18.1 이상 |

공식 문서는 스크립트 안에서 DDL(`ALTER`, `CREATE`, `DROP`), DCL(`GRANT`, `REVOKE`), DML(`INSERT`, `UPDATE`, `DELETE`, `MERGE`), 결과 집합을 반환하는 쿼리도 쓸 수 있다고 설명합니다. `EXECUTE IMMEDIATE`도 지원 문장으로 나열됩니다.

### 저장 프로시저

공식 문서의 `CREATE PROCEDURE` 페이지가 명시하는 조건은 다음과 같습니다.

| 항목 | 문서 원문 기준 |
|---|---|
| 적용 대상 | Databricks SQL, Databricks Runtime 17.0 and above, Unity Catalog only |
| 상태 라벨 | 페이지에 표시 없음 (라벨 없음, 원문 기준) |
| 구문 | `CREATE [OR REPLACE] PROCEDURE [IF NOT EXISTS] procedure_name` |
| 필수 절 | `LANGUAGE SQL`, `SQL SECURITY` (INVOKER 또는 DEFINER) |
| 본문 | `BEGIN ... END` 복합 문장 |
| 선택 특성 | `COMMENT`, `NOT DETERMINISTIC`, `DEFAULT COLLATION`, `MODIFIES SQL DATA` |

**매개변수 모드**

| 모드 | 설명 (문서 기준) |
|---|---|
| `IN` (기본값) | 입력 전용 매개변수 |
| `INOUT` | 입출력 인자. 프로시저가 처리되지 않은 오류 없이 끝나면 최종 값을 출력으로 반환 |
| `OUT` | 출력 매개변수. NULL로 시작하며, 오류 없이 끝나면 최종 값을 반환 |

**실행 권한 모델**

| `SQL SECURITY` | 본문 실행 권한 |
|---|---|
| `INVOKER` | 호출한 사용자의 권한으로 실행. 호출자는 프로시저에 `EXECUTE` 권한만 있으면 됨 |
| `DEFINER` | 프로시저 소유자의 권한으로 실행 |

관련 명령은 `CALL`(실행), `SHOW PROCEDURES`, `DESCRIBE PROCEDURE`, `DROP PROCEDURE`입니다. 공식 문서의 관련 문서 목록에는 이 명령들이 나오지만, 각 명령의 세부 동작은 해당 레퍼런스 페이지를 따릅니다.

## 어떻게 쓰는가

### 예 1: 스크립트 블록으로 변수와 분기 쓰기

```sql
-- 임시 변수로 행 수를 확인하고, 0이면 다음 작업을 건너뛴다
BEGIN
  DECLARE row_cnt INT;

  SET row_cnt = (SELECT COUNT(*) FROM main.sales.orders WHERE order_date = DATE'2026-10-27');

  IF row_cnt = 0 THEN
    SELECT 'no data for 2026-10-27' AS message;
  ELSE
    SELECT 'data found' AS message, row_cnt;
  END IF;
END;
```

### 예 2: 저장 프로시저 정의와 호출

공식 문서의 구문 요소를 따른 예시입니다. 입력과 출력 매개변수를 보여줍니다.

```sql
CREATE OR REPLACE PROCEDURE main.sales.add_nums(IN a INT, IN b INT, OUT total INT)
  LANGUAGE SQL
  SQL SECURITY INVOKER
  AS BEGIN
    SET total = a + b;
  END;

-- 세션 변수는 DECLARE VARIABLE로 선언한다 (문서의 DDL 목록에 있는 문장)
DECLARE VARIABLE result INT;
CALL main.sales.add_nums(2, 3, result);
SELECT result;
```

> **주의** 위 예시는 문서의 구문 요소를 조합한 설명용 코드입니다. 세션 변수 선언 문법은 `DECLARE VARIABLE` 레퍼런스에서 한 번 더 확인하십시오. 이 페이지는 실행 결과를 검증하지 않았습니다. 실행 전 Databricks Runtime 17.0 이상과 Unity Catalog 환경을 확인하십시오. 프로시저를 만들 때 필요한 권한은 문서 원문에 명시되어 있지 않으므로, 워크스페이스 관리자와 확인합니다.

### 예 3: 실행 권한을 정하는 방법

- 데이터 접근을 호출자별로 제한하려면 `SQL SECURITY INVOKER`를 씁니다. 호출자는 프로시저의 `EXECUTE` 권한과 본문에서 쓰는 객체의 권한이 필요합니다.
- 호출자에게 원본 테이블 권한을 주지 않고 특정 집계만 제공하려면 `SQL SECURITY DEFINER`를 씁니다. 이때 프로시저 소유자가 가진 권한이 본문 실행에 쓰이므로, 본문에 허용할 작업만 넣습니다.

## 트레이드오프

| 선택지 | 장점 | 한계 |
|---|---|---|
| 스크립트 블록 | 설정 없이 바로 실행, 노트북 셀이나 SQL 에디터에서 사용 | 재사용 불가. 이름이 없어 권한 통제가 어려움 |
| 저장 프로시저 | 이름과 권한을 가진 재사용 단위. `CALL`로 호출 | 런타임 17.0 이상, Unity Catalog 필요 |
| 노트북·잡 로직 | 파이썬 등 다른 언어와 결합, 복잡한 제어 가능 | 로직이 SQL 밖으로 나가 거버넌스와 재사용이 약해짐 |
| 구체화 뷰·스트리밍 테이블 | 선언형으로 결과를 유지·갱신 | 절차형 분기·예외 처리 용도로는 맞지 않음 (7번 페이지) |

## 주의사항

- **런타임과 카탈로그를 먼저 확인합니다.** 저장 프로시저는 Databricks Runtime 17.0 이상과 Unity Catalog에서만 적용된다고 문서에 명시되어 있습니다.
- **`SQL SECURITY`를 명시적으로 고릅니다.** 두 모드의 권한 기준이 달라 같은 본문이라도 접근 결과가 달라집니다.
- **외부 입력을 문자열로 이어 붙여 SQL을 만들지 않습니다.** 값은 매개변수로 받고, 동적 SQL이 필요하면 파라미터 마커(4번 페이지)를 씁니다.
- **커서는 Databricks Runtime 18.1 이상에서만 쓸 수 있습니다.** 커서를 쓴 스크립트를 이전 런타임에 배포하면 실패합니다.
- **`DEFINER` 프로시저는 소유자 변경의 영향을 받습니다.** 소유자가 바뀌면 실행 권한도 바뀌므로, 소유자 관리 절차를 함께 정합니다.

## 참고 문서

- [SQL scripting](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-scripting)
- [CREATE PROCEDURE](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-procedure)
- [CALL](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-call)
- [BEGIN END compound statement](https://docs.databricks.com/aws/en/sql/language-manual/control-flow/compound-stmt)
- [SQL language reference](https://docs.databricks.com/aws/en/sql/language-manual/)
