# 재시도·알림·Repair run

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

잡이 실패하는 것은 피할 수 없습니다. 이 페이지는 실패를 다루는 세 가지 장치를 설명합니다. **재시도(Retries)** 는 같은 태스크를 자동으로 다시 실행하고, **타임아웃과 지표 임계값** 은 너무 오래 걸리는 실행을 드러내며, **알림(Notifications)** 은 시작·성공·실패 같은 이벤트를 사람이나 시스템에 전달합니다. **Repair run** 은 실패한 실행에서 실패한 부분만 다시 돌리는 수동 복구 기능입니다.

## 왜 필요한가

- **일시적 장애**: 네트워크 오류, 원천 시스템 속도 제한처럼 잠깐 실패하는 경우가 많습니다. 사람이 다시 돌리기 전에 자동으로 재시도하면 운영 부담이 줄어듭니다.
- **끝나지 않는 실행**: 교착 상태나 데이터 폭증으로 실행이 끝나지 않으면 알아채기 어렵습니다. 임계값과 타임아웃이 이를 드러냅니다.
- **부분 실패 복구**: 열 개 태스크 중 마지막 하나만 실패했는데 전체를 다시 돌리면 시간과 비용이 낭비됩니다. Repair run은 실패한 태스크와 그에 의존하는 태스크만 다시 실행합니다.

## 어떻게 동작하는가

### 재시도

- 기본 설정에서는 **대부분의 구성에서 태스크 실패 시 재시도하지 않습니다.** 문서가 "For most configurations, the default setting does not retry any tasks on task failure"라고 명시합니다.
- **서버리스 잡** 은 재시도를 자동으로 최적화합니다. 재시도를 끄는 설정 항목도 있다고 문서가 설명합니다(세부 위치는 태스크 설정 페이지를 확인).
- **Continuous 잡** 은 지수 백오프(exponential backoff) 재시도 정책을 씁니다.
- 설정: 태스크의 고급 설정에서 **Retries** 옆 **Add** 아이콘을 누릅니다.
- 재시도 간격은 **실패한 실행의 시작부터 재시도 실행의 시작까지** 밀리초 단위로 계산됩니다.

### 타임아웃과 지표 임계값

- 태스크 설정에서 **Metric thresholds** 를 열고 지표 드롭다운에서 **Run duration** 을 고릅니다.
- **Warning**: 예상 완료 시간을 입력합니다. 초과하면 이벤트가 발생합니다(알림의 Duration warning과 연결).
- **Timeout**: 최대 실행 시간을 입력합니다. 이 시간 안에 끝나지 않으면 상태가 **Timed Out** 이 됩니다.
- **Timeout과 재시도를 함께 쓰면**: 타임아웃은 **재시도마다 각각** 적용됩니다.
- 파이프라인 태스크에는 **스트리밍 백로그 임계값이 지원되지 않습니다**.

### 알림

알림은 두 수준에서 설정합니다.

| 수준 | 설정 위치 | 용도 |
|---|---|---|
| 잡 수준 | Job details 패널의 **Job notifications** → **Edit notifications** | 잡 전체 실행 기준 알림 |
| 태스크 수준 | 태스크 설정 패널의 **Notifications** → **Add** | 실패한 태스크 시도마다 알림이 필요할 때. 문서는 "every failed task attempt"에 대해 태스크 알림을 권장 |

편집에는 잡에 대한 **CAN MANAGE** 또는 **IS OWNER** 권한이 필요합니다.

**이벤트 종류(UI 체크박스)**

- **Start**
- **Success**
- **Failure**
- **Duration warning** (잡에 예상 실행 시간 제한을 먼저 설정해야 함)
- **Streaming backlog**

문서 소개 부분은 연속 잡의 유지 관리 창(maintenance window)과 관련해 "Maintenance start", "Maintenance complete" 이벤트를 언급하지만, 설정 절차에 체크박스로 나오지는 않습니다. 이 페이지에서는 "Timeout" 이벤트 이름을 확인하지 못했습니다.

**알림 대상**

- 이메일 주소
- 시스템 대상(system destination): Slack, Microsoft Teams, PagerDuty, HTTP 웹훅. 워크스페이스 관리자가 관리자 설정에서 만들어야 합니다.
- Amazon SES, SNS는 이메일 경로로 받을 수 있다고 문서가 설명합니다.

**웹훅 이벤트 코드**

| 코드 | 대응 이벤트 |
|---|---|
| `jobs.on_start` | Start |
| `jobs.on_success` | Success |
| `jobs.on_failure` | Failure |
| `jobs.on_duration_warning_threshold_exceeded` | Duration warning |

### Repair run

실패한 실행을 복구하는 기능입니다. UI 절차는 다음과 같습니다.

1. 잡 실행 목록에서 실패한 실행의 **Start time** 링크를 누르거나, 매트릭스 보기에서 실패한 실행을 누릅니다. **Job run details** 페이지가 열립니다.
2. **Repair run** 을 누릅니다. **Repair job run** 대화상자에 실패한 태스크와 그에 의존하는 태스크가 표시됩니다.
3. 필요하면 파라미터를 추가하거나 고칩니다. 이 값은 기존 값을 덮어씁니다. 이후 복구에서 원래 값으로 되돌리려면 키와 값을 지우면 됩니다.
4. 대화상자에서 **Repair run** 을 누릅니다.
5. 복구가 끝나면 매트릭스 보기에 복구 실행 열이 추가됩니다. 이전에 빨간색이던 실패 태스크가 성공하면 초록색으로 바뀝니다.

**어떤 태스크가 다시 실행되는가**

- 실패하지 않은(성공한) 태스크와, 성공한 태스크에만 의존하는 태스크는 다시 실행되지 않습니다.
- **미성공(unsuccessful)** 태스크는 다시 실행됩니다. 실패, 취소, 또는 상위 의존성 실패로 건너뛴 태스크가 여기에 듭니다.
- 복구는 태스크의 **실행 상태** 를 기준으로 합니다. 비활성 상태는 기준이 아닙니다. 비활성 태스크를 강제로 돌리려면 복구 요청의 `rerun_tasks`에 포함해야 합니다.
- 미성공 태스크는 **현재의 잡과 태스크 설정** 으로 처음부터 다시 실행됩니다. 복구 전에 바꾼 설정이 반영됩니다.

**API**

복구 엔드포인트는 `POST /api/2.2/jobs/runs/repair`입니다. 요청 본문에서 `run_id`와 `rerun_tasks`를 쓰며, 문서는 `rerun_tasks`로 비활성 태스크를 지정할 수 있다고 설명합니다. 나머지 요청 필드는 이 페이지에서 확인하지 못했으므로 [Jobs API 레퍼런스의 repair 항목](https://docs.databricks.com/api/workspace/jobs/repairrun)에서 확인하십시오.

**기타 제약**

- 복구는 **태스크가 두 개 이상인 잡** 에만 쓸 수 있습니다. 태스크가 하나인 잡을 다시 돌리려면 **Run now** 를 씁니다.
- 태스크가 같은 잡 클러스터를 공유하면, 복구 시 `_v1` 접미사가 붙은 새 잡 클러스터가 만들어집니다(예: `my_job_cluster_v1`). 설정은 원래 클러스터의 현재 설정과 같습니다.
- **Runs** 탭의 **Duration** 은 최초 실행의 시작부터 마지막 복구 실행의 끝까지를 잽니다.
- 복구는 태스크를 **처음부터 다시** 실행합니다. 태스크가 멱등(idempotent)하지 않으면 실패 전에 쓴 부분 결과가 중복될 수 있다고 문서가 경고합니다. 중복이 문제되면 덮어쓰기(overwrite)나 병합(merge) 방식을 쓰십시오.

## 어떻게 쓰는가

### 재시도와 타임아웃을 함께 설정하는 예

설정은 UI 항목으로 진행합니다. 이 장에서는 REST나 CLI 필드 이름을 확인하지 못했으므로 코드 예시를 쓰지 않습니다.

1. 태스크를 열고 **Retries** 에서 **Add** 를 눌러 재시도 횟수와 간격을 설정합니다.
2. **Metric thresholds** → **Run duration** 에서 **Warning** 과 **Timeout** 을 입력합니다.
3. 잡 수준에서 **Failure** 와 **Duration warning** 알림을 추가합니다.

### 실패 정리 태스크 연결

실패 시에도 실행돼야 하는 정리 태스크는 [파라미터·태스크 값·조건 분기](jobs-parameters-and-control-flow.md)의 Run if 옵션 **All done** 을 씁니다. 결과와 관계없이 끝나면 실행됩니다.

## 트레이드오프

| 전략 | 장점 | 단점 |
|---|---|---|
| 재시도 없음 (기본) | 실패가 바로 보임, 중복 위험 없음 | 일시 장애에 사람이 개입해야 함 |
| 재시도 | 일시 장애 자동 흡수 | 멱등하지 않은 태스크는 중복 쓰기 위험 |
| Repair run | 실패 지점부터 복구, 비용 절약 | 수동 조치. 태스크 한 개 잡에는 쓸 수 없음 |
| 전체 재실행 (Run now) | 단순 | 성공한 부분까지 다시 계산 |

## 주의사항

- **멱등성 먼저**: 재시도와 Repair run은 태스크를 다시 실행합니다. 쓰기 로직이 멱등하지 않으면 중복 데이터가 생깁니다. Overwrite나 MERGE를 쓰십시오.
- **알림 범위 혼동**: 잡 수준 알림은 **실패한 태스크의 재시도 때는 발생하지 않습니다**. 태스크 시도마다 알림이 필요하면 태스크 수준에 설정하십시오.
- **"성공 but 실패 포함" 상태**: "Succeeded with failures" 상태는 문서상 성공으로 집계됩니다. 이 상태도 알리려면 **Success** 이벤트를 선택하십시오.
- **음소거 범위**: "Mute notifications for skipped runs", "Mute notifications for canceled runs", 태스크의 "Mute notifications until the last retry"는 설정한 수준에서만 적용됩니다. 잡을 음소거해도 태스크 알림은 그대로 옵니다.
- **시스템 대상 수 제한**: 이벤트 종류마다 잡 또는 태스크당 시스템 대상은 최대 3개입니다.
- **Slack·Teams 메시지 형식**: 메시지 내용은 바뀔 수 있으므로 파싱하지 마십시오. 스키마가 고정된 연동이 필요하면 사용자 정의 웹훅을 쓰십시오.
- **스트리밍 백로그 알림**: 10분 평균 백로그가 임계값을 넘으면 알림이 발생하고, 백로그가 높은 상태가 계속되면 30분 간격으로 다시 보냅니다. 파이프라인 태스크는 지원하지 않습니다. 잡에서 `awaitTermination()`을 호출하지 말라고 문서가 권장합니다.
- **Continuous 잡 백오프**: 지수 백오프 중에는 연속 실패 횟수, 성공 기간, 다음 재시도까지 시간이 표시됩니다. **Restart run** 은 진행 중인 실행을 취소하고 새 실행을 시작합니다.

## 참고 문서

- [Configure tasks](https://docs.databricks.com/aws/en/jobs/configure-task)
- [Job notifications](https://docs.databricks.com/aws/en/jobs/notifications)
- [Repair job failures](https://docs.databricks.com/aws/en/jobs/repair-job-failures)
- [Jobs API: Repair a job run](https://docs.databricks.com/api/workspace/jobs/repairrun)
- [Control flow in jobs](https://docs.databricks.com/aws/en/jobs/control-flow)
- [Disabled tasks](https://docs.databricks.com/aws/en/jobs/disabled-tasks)
