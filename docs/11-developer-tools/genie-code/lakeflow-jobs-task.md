# Lakeflow Jobs의 Genie Code 태스크

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 왜 필요한가

데이터 파이프라인은 대부분 결정적(deterministic)입니다. 같은 입력이면 같은 결과가 나와야 하고, 실패하면 재시도로 복구합니다. 그런데 운영에는 판단이 필요한 단계도 있습니다. 예를 들어 수집된 로그에서 이상 원인을 요약하거나, 새로 들어온 문서의 분류 근거를 설명하거나, 여러 지표를 보고 다음 조치를 고르는 일입니다.

이런 단계를 노트북에 규칙으로 하드코딩하면 규칙이 금방 낡습니다. 예약 작업으로 따로 돌리면 Job의 실행 순서와 의존 관계에서 떨어져 나옵니다. **Genie Code 태스크** 는 Job의 한 태스크로 자율 에이전트를 실행해, 판단 단계를 같은 Job 흐름 안에 둡니다.

문서는 이 태스크를 "Use the Genie Code task to run an autonomous agent as part of a job."이라고 소개합니다.

## 어떻게 동작하는가

### 실행 흐름

| 단계 | 동작 |
|------|------|
| 1 | Job이 실행되면 Genie Code 태스크가 프롬프트로 **새 Genie Code 채팅** 을 시작합니다. |
| 2 | 에이전트는 사용자 입력 없이 작업을 끝까지 수행합니다. 도구 호출은 자동 승인됩니다. |
| 3 | 결과 응답이 태스크 출력으로 남습니다. 대화 전체는 채팅에 남습니다. |
| 4 | 다음 태스크가 `{{tasks.<task_name>.output.response}}`로 응답을 참조하거나, 상위 태스크 값으로 조건을 만듭니다. |

실행 후에는 채팅을 열어 결과를 검토하거나, 그 채팅에서 이어서 작업할 수 있습니다.

### 실행 출력 화면

| 항목 | 설명 |
|------|------|
| Run output | 대화 링크, 프롬프트, 응답 |
| Final response | 성공한 실행의 최종 메시지 |
| Open conversation | 대화를 열어 검토하거나 이어 작업 |

문서는 긴 응답이 Run output에서 잘린다고 설명합니다. 대화에는 전체 텍스트가 남습니다.

## 어떻게 쓰는가

### 태스크 추가

1. Job 화면의 **Tasks** 탭으로 이동합니다.
2. **Add task** 를 누릅니다.
3. **Task name** 에 이름을 입력합니다.
4. **Type** 드롭다운에서 `Genie Code`를 고릅니다.
5. **Prompt** 필드에 프롬프트를 입력합니다.
6. 필요하면 **Advanced** 설정에서 재시도, 실행 시간 또는 스트리밍 백로그 임계값, 알림을 정합니다.
7. **Save task** 를 누릅니다.

### 프롬프트 파라미터 문법

| 문법 | 의미 |
|------|------|
| `{{name}}` | Job 파라미터 `name`의 값. **Job details** 사이드바의 **Edit parameters** 에서 정의합니다. |
| `{{job.id}}` | Job ID |
| `{{job.start_time.iso_date}}` | 실행 시작 날짜 (ISO 형식) |
| `{{tasks.<task_name>.values.<key>}}` | 상위 태스크의 값 `<key>` |
| `{{input}}` | For each 태스크 안에서 입력 항목 |
| `{{tasks.<task_name>.output.response}}` | 상위 태스크 Genie Code 실행의 최종 응답 (성공한 실행만) |

동작 규칙은 다음과 같습니다.

- 대응하는 Job 파라미터가 없는 `{{name}}`은 **그대로 남습니다.**
- 태스크가 쓸 수 없는 참조는 경고가 뜨고 입력한 그대로 남습니다.
- 실행 시점에 동적 값을 풀 수 없으면 **태스크가 시작되기 전에 실패합니다.**

### 예시 프롬프트

```text
다음 데이터는 수집 단계의 결과입니다. 행 수는 {{tasks.collect_orders.values.row_count}}건입니다.
기준일은 {{job.start_time.iso_date}}입니다.

1. sales.orders 테이블에서 기준일 전날 데이터의 행 수를 확인하세요.
2. 행 수가 수집 단계의 값과 다르면 차이 원인을 요약하세요.
3. 마지막 줄에 OK 또는 CHECK 중 하나만 적으세요.
```

이 예시에서 `collect_orders`는 상위 태스크 이름이고 `row_count`는 상위 태스크가 설정한 값의 키입니다. 값을 설정하는 방식은 Lakeflow Jobs의 태스크 값 기능을 따릅니다. 이 페이지는 그 설정 코드를 제시하지 않습니다.

### 다음 태스크에서 응답 쓰기

- 다른 Genie Code 태스크의 프롬프트에 `{{tasks.<task_name>.output.response}}`를 넣습니다.
- 조건 분기(If/else)의 조건에 응답 값을 씁니다.
- 일반 태스크의 파라미터로 넘깁니다.

## 설계 패턴

문서가 직접 정한 패턴은 아니며, 기능의 성격에 따른 설계 권고입니다.

| 패턴 | 설명 |
|------|------|
| 결정적 수집은 코드 태스크로 | 데이터 적재, 행 수 집계, 스키마 검사는 노트북이나 SQL 태스크로 둡니다. 결과를 태스크 값으로 남깁니다. |
| 판단은 Genie Code 태스크로 | 요약, 원인 추정, 분류 근거처럼 판단이 필요한 단계만 Genie Code 태스크로 둡니다. |
| 쓰기 권한 최소화 | 자동 승인을 끌 수 없으므로, 에이전트가 쓸 수 있는 범위를 Unity Catalog 권한으로 좁힙니다. 실행 주체 설정은 문서에 없으므로 권한 범위는 직접 확인합니다. |
| 응답 형식을 고정 | 조건 분기에 쓰는 값은 마지막 줄 같은 짧은 토큰으로 요구합니다. 긴 응답 전체를 조건에 쓰면 해석이 흔들릴 수 있습니다. |
| 중요한 값은 태스크 값으로 | Final response는 Run output에서 잘릴 수 있으므로, 후속 처리에 필요한 값은 가능하면 상위 태스크 값으로 남깁니다. |

## 예약 작업과의 차이

| 항목 | 예약 작업 (Scheduled tasks) | Lakeflow Jobs의 Genie Code 태스크 |
|------|------------------------------|-----------------------------------|
| 실행 단위 | 반복 일정에 따른 하나의 Genie Code 세션 | Job 실행 안의 한 태스크 |
| 입력 | Title, Prompt, Schedule, Timezone | Prompt와 Job 파라미터, 상위 태스크 값 |
| 실행 결과 | 실행마다 새 채팅 | Run output의 대화 링크와 응답, 다음 태스크가 참조하는 출력 |
| 다음 단계 연결 | 문서상 없음 | `{{tasks.<t>.output.response}}`, 조건 분기, 다른 태스크 파라미터 |
| 자동 승인 | 항상 켜짐, 끌 수 없음 | 항상 켜짐, 끌 수 없음 |
| 설정 상속 | 문서에 명시 없음 | Genie Code 설정과 사용자 정의 MCP 연결을 상속 |
| 재시도·알림 | 문서에 명시 없음 | Advanced 설정에서 재시도, 임계값, 알림 설정 |
| 실행 주체 | 작업 생성자 권한 (Unity Catalog 권한 적용) | 문서에 run-as 명시 없음 |
| 공유 | 작업 공유 불가. 실행 채팅은 공유 가능 | 문서에 명시 없음 |
| 과금 | Genie 사용량에 포함 | 문서에 명시 없음 |
| 상태 | 릴리즈 노트 2026-09-01 GA. 페이지 라벨 없음 | 릴리즈 노트 2026-10-21 GA. 2026-08-27에는 Beta. 페이지 라벨 없음. compliance security profile 워크스페이스는 2026년 11월부터 기본 제공 (What's coming) |

## 트레이드오프

| 항목 | 내용 |
|------|------|
| 장점 | 판단 단계를 Job의 실행 순서, 재시도, 알림 체계 안에 둘 수 있습니다. |
| 비결정성 | 같은 프롬프트라도 응답이 달라질 수 있습니다. 조건 분기에는 짧고 고정된 답을 쓰는 설계가 필요합니다. |
| 자동 승인 | 끌 수 없어, 실행 전 검토 단계가 없습니다. |
| 과금 | 문서에 명시가 없습니다. 비용 계획은 실제 실행으로 확인합니다. |
| 실행 주체 | 문서에 명시가 없어, 권한 범위를 설계 시점에 확인해야 합니다. |

## 주의사항

> **주의** 자동 승인은 항상 켜져 있으며, 문서는 "you cannot disable it for a job task"라고 명시합니다. 에이전트가 할 수 있는 일의 상한은 Unity Catalog 권한과 프롬프트 설계로 정해야 합니다.

- **프롬프트 파라미터 실패는 실행 전에 드러납니다.** 해석되지 않는 동적 값은 태스크를 시작하기 전에 실패하게 합니다. 파라미터 이름을 Job 설정과 맞춰 둡니다.
- **`{{name}}`에 대응하는 파라미터가 없으면 문자 그대로 남습니다.** 오타가 있어도 오류가 나지 않을 수 있으므로, 실행 결과의 Prompt 항목을 확인합니다.
- **Final response는 잘릴 수 있습니다.** 전체 응답은 대화에 있습니다.
- **Genie Code 설정과 MCP 연결을 상속합니다.** 태스크를 설계할 때 연결된 MCP 서버가 무엇인지 확인합니다. MCP 설정은 [MCP 서버 연결](mcp.md)을 참고하십시오.
- **상태 확인**: 릴리즈 노트 2026-10-21에 GA로 표기되어 있습니다. 같은 기능이 2026-08-27 릴리즈 노트에서는 Beta였습니다. 페이지 자체에는 라벨이 없습니다. compliance security profile이 켜진 워크스페이스에서는 2026년 11월부터 기본 제공된다고 What's coming에 나옵니다.
- **사전 요건**: 워크스페이스가 Genie Code의 에이전트 기능에 접근할 수 있어야 하고, 프롬프트가 Genie Code 사용 정책을 따라야 한다고 문서가 명시합니다. 에이전트 기능을 켜는 방법은 [거버넌스와 비용](governance-and-cost.md)을 참고하십시오.
- **문서에 없는 것**: 컴퓨트·서버리스 요구사항, run-as 신원, 필요한 권한, 과금, 클라우드별 차이.

## 참고 문서

- [Genie Code task for Lakeflow Jobs](https://docs.databricks.com/aws/en/jobs/tasks/genie-code)
- [Scheduled tasks](https://docs.databricks.com/aws/en/genie-code/scheduled-tasks)
- [Genie Code 릴리즈 노트 (2026년 8월)](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
- [Genie Code 릴리즈 노트 (2026년 10월)](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
- [What's coming — Genie Code tasks in Lakeflow Jobs (compliance security profile)](https://docs.databricks.com/aws/en/release-notes/whats-coming#genie-code-tasks-in-lakeflow-jobs-are-available-by-default-for-workspaces-with-the-compliance-security-profile-enabled-starting-in-november-2026)
