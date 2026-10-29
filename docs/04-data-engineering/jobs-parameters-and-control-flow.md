# 파라미터·태스크 값·조건 분기

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

잡의 태스크가 서로 정보를 주고받고 결과에 따라 다른 경로로 가려면 세 가지 장치가 필요합니다. **잡 파라미터** 는 실행 시점에 값을 바꿔 넣는 입력이고, ** 태스크 값** 은 앞 태스크가 만든 작은 결과를 뒤 태스크에 넘기는 통로이며, **Run if·If/else·For each** 는 실행 여부와 반복을 제어하는 흐름 제어 장치입니다. 이 페이지는 세 장치를 함께 다룹니다.

## 왜 필요한가

- **하드코딩 방지**: 날짜, 대상 카탈로그, 환경 이름을 노트북 안에 박아 두면 환경마다 코드를 복제해야 합니다.
- **결과 전달**: 앞 태스크가 처리한 레코드 수, 생성한 파일 목록을 뒤 태스크가 알아야 할 때가 많습니다. 이를 임시 테이블로 쓰면 정리 작업이 생깁니다.
- **분기와 반복**: 실패했을 때만 정리 태스크를 돌리거나, 나열된 테이블 수만큼 같은 작업을 반복해야 할 때가 있습니다.

## 어떻게 동작하는가

### 잡 파라미터

- 잡 파라미터는 기본값을 가진 **키-값 쌍** 입니다. 정적 값이나 동적 값 참조를 담을 수 있습니다.
- 키에는 밑줄, 하이픈, 마침표, 영숫자만 쓸 수 있습니다.
- 값은 문자열, 동적 값 참조, 또는 배열을 포함한 임의의 JSON일 수 있습니다.
- UI에서는 **Job details** 사이드바의 **Edit parameters** 에서 추가하고 편집한 뒤 **Save** 를 누릅니다.
- 실행할 때 값을 바꾸거나 새 파라미터를 추가할 수 있으며, **Repair run** 에서도 바꿀 수 있습니다.

**우선순위**: 키-값 파라미터를 받는 태스크에는 잡 파라미터가 자동으로 넘어갑니다. 잡 파라미터와 태스크 파라미터의 키가 같으면 ** 잡 파라미터가 우선** 합니다. JSON 배열 파라미터를 받는 태스크는 잡 파라미터를 자동으로 받지 않으므로 `{{job.parameters.<name>}}`로 명시해야 합니다.

### 태스크 값

태스크 값은 앞 태스크가 설정하고 뒤 태스크가 읽는 작은 값입니다. 문서의 `dbutils` 서브유틸리티 설명을 따릅니다.

- 키는 문자열이며 노트북 안에서 유일해야 합니다.
- 값은 유효한 JSON으로 표현할 수 있어야 합니다.
- JSON 표현은 **48 KiB** 를 넘을 수 없습니다.
- `dbutils.jobs.taskValues.set()`과 `get()`은 **Python 함수** 입니다. Python을 선택한 노트북에서만 쓸 수 있습니다. 동적 값 참조는 이 제한이 없습니다.

설정과 조회 예시는 다음과 같습니다. 문서 예제 그대로입니다.

```python
# 앞 태스크(노트북)에서 설정
dbutils.jobs.taskValues.set(key = "fave_food", value = "beans")
```

```python
# 뒤 태스크(노트북)에서 조회: taskKey는 앞 태스크 이름
booking_status = dbutils.jobs.taskValues.get(
    taskKey = "booking_lookup",
    key = "booking_status",
    debugValue = "confirmed"
)
```

> **참고** `get()`에는 `default`도 줄 수 있지만, 문서는 기본값을 두면 키 누락이나 태스크 이름 오타가 숨겨질 수 있다고 권장하지 않습니다. `debugValue`는 대화형 개발 중 쓰는 정적 값입니다.

문서는 태스크 값을 **태스크 파라미터로 설정하는 방식** 을 권장합니다. 참조 형식은 다음과 같습니다.

```
{{tasks.<task_name>.values.<value_name>}}
```

예: `destination_lookup` 태스크의 `dest_list` 키를 참조하려면 `{{tasks.destination_lookup.values.dest_list}}`.

### 동적 값 참조

동적 값 참조(dynamic value reference)는 실행 시점에 치환되는 `{{...}}` 문법입니다. 자주 쓰는 항목은 다음과 같습니다. 전체 목록은 참고 문서를 확인하십시오.

| 참조 | 의미 |
|---|---|
| `{{job.id}}` | 잡 고유 ID |
| `{{job.name}}` | 실행 시점의 잡 이름 |
| `{{job.run_id}}` | 잡 실행 ID |
| `{{job.repair_count}}` | 현재 실행의 복구(repair) 시도 횟수 |
| `{{job.start_time.<argument>}}` | 실행 시작 시각(UTC). 인수로 형식 지정 (예: `iso_date`) |
| `{{job.parameters.<name>}}` | 잡 파라미터 값 |
| `{{job.trigger.type}}` | 트리거 종류. 반환값: `periodic`, `one_time`, `run_job_task`, `file_arrival`, `continuous`, `table`, `model` |
| `{{job.trigger.file_arrival.location}}` | 파일 도착 트리거의 저장 위치 |
| `{{job.trigger.table_update.updated_tables}}` | 마지막 실행 이후 업데이트된 테이블의 JSON 목록 |
| `{{task.name}}` | 현재 태스크 이름 |
| `{{task.execution_count}}` | 재시도와 복구를 포함한 현재 태스크 실행 횟수 |
| `{{tasks.<task_name>.result_state}}` | 해당 태스크의 결과 상태. 예: `success`, `failed`, `excluded`, `canceled`, `timedout`, `upstream_failed` |
| `{{tasks.<task_name>.values.<value_name>}}` | 해당 태스크가 설정한 태스크 값. For each 안에서는 반복 순서대로 정렬된 JSON 배열 |
| `{{tasks.<task_name>.output.first_row.<column_alias>}}` | 앞 SQL 태스크 결과의 첫 행 특정 컬럼 값 |
| `{{input}}`, `{{input.<key>}}` | For each의 현재 반복 값 (아래 For each 절 참고) |

문서는 `{{job_id}}`, `{{run_id}}`, `{{start_date}}`, `{{start_time}}`, `{{task_retry_count}}`, `{{parent_run_id}}`, `{{task_key}}`를 **사용 중단(deprecated)** 으로 표기하고 대체 참조를 안내합니다.

## 조건 분기와 반복

### Run if (실행 조건)

뒤 태스크가 앞 태스크들의 결과에 따라 실행될지를 정합니다. 문서의 옵션과 의미입니다. 라벨은 UI 표기 그대로입니다.

| 옵션 | 실행 조건 | 조건을 만족하지 않을 때 |
|---|---|---|
| All succeeded (기본값) | 모든 의존 태스크가 실행되어 성공 | 태스크가 **Upstream failed** |
| At least one succeeded | 의존 태스크 중 하나 이상 성공 | **Upstream failed** |
| None failed | 실패한 의존 태스크가 없고, 하나 이상 실행됨 | **Upstream failed** |
| All done | 결과와 관계없이 모든 의존 태스크가 끝나면 실행 | (조건 없음) 정리 태스크에 적합 |
| At least one failed | 의존 태스크 중 하나 이상 실패 | **Excluded** |
| All failed | 모든 의존 태스크가 실패 | **Excluded** |

추가 규칙입니다.

- **Excluded** 상태의 상위 태스크는 조건 평가에서 ** 성공으로 간주** 됩니다. 반면 **Upstream failed** 나 **Upstream canceled** 는 실패로 간주됩니다.
- Excluded 태스크는 건너뜁니다. 모든 의존 태스크가 Excluded면 그 태스크도 Excluded가 됩니다.
- 제외는 체인을 따라 아래로 전파됩니다. A → B → C에서 A가 Excluded면 B와 C는 실행되지 않습니다.
- 태스크를 취소하면 그 취소가 아래로 전파되지만, 정리용 태스크(예: cleanup)는 여전히 실행됩니다.
- 상위 태스크가 비활성화(disabled)되면 하위 태스크는 Run if 조건으로 평가되며, 비활성화될 수도 있습니다. 비활성 태스크 동작의 전체 목록은 별도 문서 "Downstream task behavior"를 참고합니다.

### If/else 조건 태스크

If/else 태스크는 불리언 조건을 평가합니다. 결과는 참(true) 또는 거짓(false)입니다.

- **First Condition**: 평가할 피연산자. `{{job.parameters.<name>}}`, 태스크 파라미터, 또는 `{{tasks.<task_name>.values.<value_name>}}`.
- **Boolean operator**: 드롭다운에서 선택. 연산자는 `==`, `!=`, `>`, `>=`, `<`, `<=`.
- **Second Condition**: 비교 대상 값.

`==`와 `!=`는 **문자열로 비교** 합니다. 문서 예시는 `12.0 == 12`가 **false** 라고 설명합니다. `>`, `>=`, `<`, `<=`는 ** 숫자로 비교** 합니다.

하위 태스크는 두 결과 중 하나에 붙습니다. 기본 Depends on 값은 `<task-name> (true)`이며, 거짓일 때 실행하려면 `<task-name> (false)`를 고릅니다.

문서 예시는 다음 조건으로 나쁜 레코드가 있을 때만 분기하는 패턴입니다.

```
{{tasks.process_records.values.bad_records}} > 0
```

> **주의** If/else 태스크는 조건 값을 공급하는 상위 태스크가 비활성화되어 있으면 실패합니다.

### For each (반복)

For each 태스크는 **중첩된 태스크 하나** 를 입력 배열의 각 항목마다 다른 파라미터로 반복 실행합니다.

**입력(Inputs)** 은 세 가지 형태 중 하나입니다.

```json
[{"table": "sales"}, {"table": "orders"}]
```

- 리터럴 JSON 배열: 항목은 키-값 쌍, 문자열, 숫자, 불리언, 임의의 JSON 객체 가능
- 태스크 값 참조: `{{tasks.generate_countries_list.values.countries}}`
- 잡 파라미터: `{{job.parameters.countries}}`

**중첩 태스크에서 현재 값 참조**: 중첩 태스크의 **Parameters** 에 다음을 설정합니다.

- `{{input}}`: 현재 반복의 배열 값
- `{{input.<key>}}`: 객체 목록을 반복할 때 개별 필드 (예: `{{input.table}}`)

**동시 실행**: 설정 이름은 **Concurrency** 이며 기본값은 1입니다. 서로 의존하지 않는 중첩 태스크도 동시에 실행될 수 있습니다.

**결과 집계**: 하위 태스크는 중첩 태스크에 직접 의존하지 않고 For each 태스크에 의존합니다. 중첩 태스크가 각 반복에서 설정한 태스크 값은 반복 인덱스 순서의 하나의 리스트로 모입니다.

**제한**

- Inputs 입력란: 최대 5,000자.
- 태스크 값 참조가 가리키는 값: 최대 48 KB. 참조 문자열 자체는 5,000자 제한입니다.
- 잡 파라미터 값: 최대 10,000자.
- 큰 배열은 설정 파일로 넘기는 방식을 문서가 제안합니다.
- 입력을 제공하는 상위 태스크가 비활성화되면 For each는 실패합니다.
- 최대 반복 수는 문서에 명시되지 않았습니다.
- 중첩 태스크는 표준 태스크 유형이어야 하며 다른 For each 태스크일 수 없습니다.

**집계 값 읽기(Beta)**: For each 결과를 집계해 읽는 기능은 **Beta** 이며 기본으로 켜져 있다고 문서가 설명합니다. classic 컴퓨트에서는 Databricks Runtime 15.4 LTS 이상이 필요하고, 서버리스 컴퓨트에서 `get`은 환경 버전 5 이상이 필요합니다. 이전 환경 버전은 첫 반복의 값만 돌려주고 `TypeError`를 낼 수 있습니다. 집계 값을 읽을 때는 For each 태스크의 키가 아니라 ** 중첩 태스크의 키** 를 씁니다. 키를 설정하지 않은 반복은 `None`(JSON `null`)으로 나타납니다.

## 트레이드오프

| 방식 | 장점 | 주의 |
|---|---|---|
| 잡 파라미터 | 환경별 값을 실행 때 바꿈 | 값에 비밀 정보를 넣으면 안 됨 (일반 원칙) |
| 태스크 값 | 작은 결과를 메모리 없이 전달 | 48 KiB 한도. 큰 데이터는 테이블로 |
| 동적 값 참조 | 설정 파일 없이 연결 | 미리 존재하지 않는 키는 실패로 드러나야 함 |
| If/else | 명시적 분기 | 조건 값이 없으면 실패 |
| For each | 같은 태스크를 여러 입력에 반복 | Concurrency를 올리면 원천 부하 증가 |

## 주의사항

- **기본값 남용 금지**: 태스크 값에 `default`를 주면 키가 빠진 사고가 조용히 넘어갑니다. 누락을 드러내도록 두십시오.
- **Run if 설계**: 실패 정리는 `All done`, 실패 알림 분기는 `At least one failed`를 씁니다. 정리 태스크가 상위 실패에 의해 건너뛰어지지 않게 확인하십시오.
- **문자열 비교**: `==`는 문자열 비교입니다. 숫자 비교가 필요하면 `>`, `<` 등 숫자 연산자를 쓰거나 타입을 맞추십시오.
- **For each 집계와 버전**: 서버리스에서 집계 값을 읽는다면 환경 버전 5 이상을 확인하십시오.
- **Python 전용 함수**: 노트북이 Python이 아니면 `dbutils.jobs.taskValues`를 쓸 수 없습니다. 동적 값 참조를 쓰십시오.

## 참고 문서

- [Job parameters](https://docs.databricks.com/aws/en/jobs/job-parameters)
- [Task values](https://docs.databricks.com/aws/en/jobs/task-values)
- [Dynamic value references](https://docs.databricks.com/aws/en/jobs/dynamic-value-references)
- [Run if dependencies](https://docs.databricks.com/aws/en/jobs/run-if)
- [Control flow in jobs](https://docs.databricks.com/aws/en/jobs/control-flow)
- [If/else condition task](https://docs.databricks.com/aws/en/jobs/tasks/if-else)
- [For each task](https://docs.databricks.com/aws/en/jobs/tasks/for-each)
- [Disabled tasks](https://docs.databricks.com/aws/en/jobs/disabled-tasks)
