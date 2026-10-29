# 노트북 기초

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 한눈에 보기

노트북(notebook)은 코드, 실행 결과, 설명 문서를 한 파일에 담는 대화형 작업 단위입니다. Databricks 노트북은 **셀(cell)** 단위로 코드를 실행하며, 한 노트북 안에서 여러 언어를 섞어 쓸 수 있습니다. 이 페이지는 처음 노트북을 열었을 때 알아야 할 것만 다룹니다. 세부 기능(디버깅, 테스트, 버전 관리)은 공식 노트북 문서의 하위 페이지에 있습니다.

| 개념 | 설명 |
|---|---|
| 셀(cell) | 코드 또는 텍스트를 담는 단위입니다. 셀 단위로 실행합니다. |
| 기본 언어(default language) | 노트북을 만들 때 정한 언어입니다. 셀마다 바꿀 수 있습니다. |
| 매직 명령(magic command) | `%`로 시작하는 명령으로, 셀의 언어를 바꾸거나 부가 기능을 호출합니다. |
| 위젯(widget) | 노트북에 입력 값을 받는 입력란이나 드롭다운을 붙이는 기능입니다. |
| 결과(output) | 셀을 실행한 결과입니다. 표, 그래프, 텍스트로 나타납니다. |

## 1. 왜 노트북을 쓰는가

데이터 작업은 탐색 → 가공 → 검증 → 공유의 반복입니다. 스크립트 파일 하나만으로는 중간 결과를 보면서 한 줄씩 확인하기 어렵고, 결과를 팀과 공유하기도 불편합니다. 노트북은 다음 문제를 줄입니다.

- 셀 단위로 실행해 중간 결과를 바로 확인합니다.
- 코드, 결과, 설명을 한 문서에 묶어 재현 가능한 작업 기록을 남깁니다.
- 여러 언어(Python, SQL 등)를 같은 작업 흐름에 섞습니다.
- 같은 노트북을 잡(job)으로 예약 실행하는 전환이 쉽습니다. 잡 구성은 04장에서 다룹니다.

## 2. 지원 언어

공식 문서는 노트북에서 **Python, SQL, Scala, R** 을 지원한다고 설명합니다. 셀의 언어는 두 가지 방법으로 정합니다.

| 방법 | 예 |
|---|---|
| 셀의 언어 드롭다운에서 선택 | 셀 오른쪽 위의 언어 선택 메뉴 |
| 셀 첫 줄에 언어 매직 명령 작성 | `%python`, `%sql`, `%r`, `%scala` |

> **주의** 언어마다 실행 환경(REPL)이 분리됩니다. 공식 문서는 "Variables and state are isolated between different language REPLs."라고 명시합니다. Python에서 만든 변수를 SQL 셀에서 바로 쓸 수 없습니다. 언어 사이에서 값을 넘길 때는 임시 뷰(temporary view)나 테이블 같은 외부 자원을 거쳐야 합니다.

## 3. 셀 실행 기초

### 실행 단축키와 메뉴

| 동작 | 방법 |
|---|---|
| 한 셀 실행 | Shift+Enter |
| 모든 셀 실행 | Run All |
| 현재 셀 위의 셀 실행 | Run All Above |
| 현재 셀 아래의 셀 실행 | Run All Below (현재 셀 포함) |
| 실행 중지 | 툴바의 Interrupt 버튼, Run > Interrupt execution, 또는 `I I` |

> **참고** 공식 문서는 Run All이 공유 노트북에서 경쟁 상태(race condition)를 일으킬 수 있다고 설명합니다. 예를 들어 마운트와 언마운트를 같은 노트북에서 할 때는 Run All을 쓰지 말라고 권장합니다.

### 실행 방식의 차이

공식 문서는 런타임과 컴퓨트에 따라 셀 실행 방식이 다르다고 설명합니다.

| 조건 | 실행 방식 | 오류 처리 |
|---|---|---|
| Databricks Runtime 13.3 LTS 이하 | 셀을 개별로 실행 | 오류가 나도 뒤의 셀이 계속 실행됩니다. |
| Databricks Runtime 14.0 이상, 또는 SQL 웨어하우스 | 셀을 배치(batch)로 실행 | 오류가 나면 실행이 멈춥니다. 개별 셀은 취소할 수 없습니다. |

> **주의** 노트북을 처음 열면 런타임 버전과 컴퓨트 종류(서버리스인지 클래식인지)를 먼저 확인하십시오. 같은 노트북도 런타임에 따라 오류가 멈추는 방식이 달라집니다.

## 4. 매직 명령

공식 문서의 노트북 코드 페이지가 설명하는 주요 매직 명령은 다음과 같습니다.

| 명령 | 역할 | 예 |
|---|---|---|
| `%python`, `%r`, `%scala` | 셀 언어를 바꿉니다. | `%python` 다음 줄에 코드 |
| `%sql` | SQL 셀로 바꿉니다. 결과는 이후 Python·SQL 셀에서 `_sqldf`로 참조할 수 있습니다. | `SELECT * FROM sales_dev.orders.daily_orders LIMIT 10` |
| `%md` | 마크다운으로 텍스트, 이미지, 수식을 씁니다. | 설명 문장 |
| `%pip` | 노트북 범위의 Python 패키지를 설치합니다. | `%pip install pandas` |
| `%run` | 다른 노트북을 현재 노트북 안으로 불러옵니다. | `%run /path/to/notebook` |
| `%fs` | `dbutils.fs` 명령의 단축 표기입니다. | `%fs ls /path` |
| `%sh` | 셸 명령을 실행합니다. 드라이버에서만 실행됩니다. | `%sh ls -la` |

> **참고** 공식 문서는 IPython 자동 매직(automagic)이 켜져 있어서 `pip install pandas`처럼 `%` 없이도 쓸 수 있다고 설명합니다. 다만 노트북에서는 `%pip`를 쓰는 것이 명확합니다.

### `%sql`로 결과 이어 쓰기

```python
# 1) SQL 셀의 결과를 Python에서 이어 쓰는 예
# 먼저 SQL 셀에서 아래 쿼리를 실행합니다.
#   %sql
#   SELECT order_date, SUM(amount) AS total FROM sales_dev.orders.daily_orders GROUP BY order_date
# 이후 Python 셀에서 _sqldf를 참조합니다.
df = _sqldf.toPandas()
print(df.head())
```

> **주의** `_sqldf`는 직전 `%sql` 셀의 결과를 가리킵니다. 셀 실행 순서를 바꾸면 다른 결과를 가리킬 수 있으므로, 결과를 변수로 옮길 때는 셀 순서를 확인하십시오.

## 5. `%run`: 다른 노트북 불러오기

`%run`은 다른 노트북을 현재 노트북 안에서 실행하고, 그 노트북의 함수와 변수를 현재 노트북에서 쓸 수 있게 합니다. 공식 문서는 다음 규칙을 명시합니다.

- `%run`은 **셀 안에 단독으로** 있어야 합니다. 공식 문서는 "must be in a cell by itself, because it runs the entire notebook inline."이라고 설명합니다.
- 범위(scope)는 노트북 전체입니다. 불러온 노트북의 함수와 변수가 현재 노트북으로 들어옵니다.
- 위젯 값을 넘길 수 있습니다. 공식 위젯 문서 예시는 다음과 같습니다.

```python
# 위젯 기본값으로 실행하는 경우
%run /path/to/notebook

# 값을 넘겨 실행하는 경우 (클러스터에 연결된 노트북 기준)
%run /path/to/notebook $X="10" $Y="1"
```

> **주의** 공식 위젯 문서는 값을 넘기는 `%run` 형식이 SQL 웨어하우스가 아니라 클러스터에 연결된 노트북에서 동작한다고 설명합니다. 웨어하우스에서 쓰려면 같은 값을 다른 방식으로 전달해야 합니다. 노트북을 어떤 컴퓨트에 붙였는지 먼저 확인하십시오.

> **참고** 여러 노트북을 공통 함수로 묶는 방식은 `%run`만 있는 것이 아닙니다. 노트북 호출(notebook workflows)이나 Python 모듈로 나누는 방식도 공식 문서에 있으며, 이 페이지는 `%run`만 다룹니다.

## 6. 위젯(Widgets)

위젯은 노트북 상단에 입력란을 띄워 값을 바꾸며 실행할 수 있게 합니다. 공식 위젯 문서는 "Add interactive input parameters to your notebooks and dashboards using widgets."라고 설명합니다.

### 위젯 종류

| 종류 | 설명 |
|---|---|
| `text` | 값을 직접 입력하는 텍스트 박스입니다. |
| `dropdown` | 미리 준비한 목록에서 고릅니다. |
| `combobox` | 목록에서 고르거나 직접 입력할 수 있습니다. |
| `multiselect` | 목록에서 여러 값을 고릅니다. |

> **주의** 위젯은 **문자열(string) 값만** 받습니다. 숫자를 기대하면 `int()`나 `float()`로 변환하십시오.

### 위젯 API

공식 문서가 설명하는 `dbutils.widgets` 함수는 다음과 같습니다.

| 함수 | 역할 |
|---|---|
| `dbutils.widgets.text(name, defaultValue, label)` | 텍스트 위젯을 만듭니다. `choices` 인자가 없습니다. |
| `dbutils.widgets.dropdown(name, defaultValue, choices, label)` | 드롭다운 위젯을 만듭니다. |
| `dbutils.widgets.get(name)` | 위젯 값을 읽습니다. |
| `dbutils.widgets.getAll()` | 모든 위젯 값을 읽습니다. |
| `dbutils.widgets.remove(name)` | 위젯 하나를 제거합니다. |
| `dbutils.widgets.removeAll()` | 모든 위젯을 제거합니다. |
| `dbutils.widgets.help()` | 도움말을 보여 줍니다. |

공식 문서 예시는 다음과 같습니다.

```python
# 드롭다운 위젯 만들기: 이름, 기본값, 선택지, 라벨
dbutils.widgets.dropdown("state", "CA", ["CA", "IL", "MI", "NY", "OR", "VA"])

# 텍스트 위젯 만들기
dbutils.widgets.text("table", "")

# 값 읽기
state = dbutils.widgets.get("state")
```

> **참고** 공식 문서는 `combobox`와 `multiselect`의 정확한 호출 형식을 이 페이지 예시로 보여 주지 않습니다. 해당 위젯을 쓸 때는 `dbutils.widgets.help()` 또는 공식 위젯 문서의 최신 형식을 확인하십시오.

> **주의** 위젯을 제거한 뒤에는 **같은 셀에서 다시 만들 수 없습니다.** 공식 문서는 다른 셀에서 만들라고 안내합니다.

### SQL에서 위젯 값 쓰기

SQL 셀에서는 위젯 값을 이름 있는 파라미터 마커(parameter marker)로 참조합니다. 공식 문서는 `SELECT :state`처럼 쓰며, 파라미터 마커는 **Databricks Runtime 15.2 이상** 에서 쓸 수 있다고 명시합니다.

객체 이름(테이블 이름 등)을 위젯 값으로 넘길 때는 `IDENTIFIER()`로 감쌉니다.

```sql
-- 위젯 값으로 테이블 이름과 필터 값을 받는 예 (DBR 15.2 이상)
SELECT *
FROM IDENTIFIER(:database || '.' || :table)
WHERE col = :filter_value
LIMIT 100;
```

> **주의** 파라미터 마커에 값을 넣는 것과 객체 이름을 넣는 것은 다릅니다. 테이블 이름을 `:table`로 직접 쓰면 값으로 처리되어 실패합니다. 객체 이름은 반드시 `IDENTIFIER()`로 감싸십시오.

> **참고** 공식 문서 예시의 `WHERE` 절은 `==`를 씁니다. 이 페이지에서는 SQL의 표준 비교 연산자인 `=`로 바꿔 적었습니다.

## 7. 노트북 공유와 결과

| 항목 | 공식 문서 기준 |
|---|---|
| 노트북 가져오기·내보내기 | Import and export notebooks 페이지에서 다룹니다. |
| 협업 | Collaborate using notebooks 페이지에서 다룹니다. |
| 결과 관리 | Notebook outputs and results 페이지에서 다룹니다. |
| 노트북 대시보드 | Dashboards in notebooks 페이지에서 다룹니다. |
| 노트북 디버깅 | Debug notebooks 페이지에서 다룹니다. |

이 페이지는 위 기능의 세부 절차를 다루지 않습니다. 노트북을 잡으로 예약하는 방법은 04장에서 다룹니다.

## 8. 트레이드오프와 주의사항

| 상황 | 권장 |
|---|---|
| 탐색과 실험 | 노트북으로 셀 단위 실행을 씁니다. |
| 재사용할 공통 로직 | `%run` 대신 모듈로 나누는 방식을 함께 검토합니다. 노트북 범위 공유는 편하지만 의존 관계가 숨겨지기 쉽습니다. |
| 반복 실행과 예약 | 노트북을 그대로 쓰기보다 잡으로 등록하는 것을 검토합니다. |
| 언어 섞기 | 셀 단위 전환은 편하지만 변수 공유가 되지 않습니다. 중간 결과는 테이블이나 뷰로 넘기십시오. |

> **주의** 노트북 안에 자격 증명(토큰, 비밀번호)을 직접 쓰지 마십시오. 이 교육 자료의 예시도 자격 증명 없이 작성했습니다. 비밀 값은 Secret 같은 별도 저장소를 쓰는 방식을 공식 문서에서 확인하십시오.

> **참고** 이 페이지의 `%run`, 위젯, 실행 방식은 공식 노트북 문서 원문 기준입니다. 런타임 버전에 따라 차이가 있으니 실습 전에 노트북 상단의 런타임과 컴퓨트를 확인하십시오.

## 다음으로 읽을 페이지

노트북을 실행하면 비용이 발생할 수 있습니다. 실행 단위가 어떻게 과금되는지는 [과금 모델 기초](billing-basics.md)에서 이어집니다.

## 참고 문서

- [Databricks notebooks](https://docs.databricks.com/aws/en/notebooks/)
- [Develop code in notebooks](https://docs.databricks.com/aws/en/notebooks/notebooks-code)
- [Run notebooks](https://docs.databricks.com/aws/en/notebooks/run-notebook)
- [Databricks widgets](https://docs.databricks.com/aws/en/notebooks/widgets)
- [Notebook outputs and results](https://docs.databricks.com/aws/en/notebooks/notebook-outputs)
