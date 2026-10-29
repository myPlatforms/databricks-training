# 트레이싱·평가·피드백

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 왜 필요한가

에이전트는 같은 질문에도 실행 경로가 달라질 수 있습니다. 어떤 도구를 몇 번 불렀는지, 어떤 검색 결과를 받았는지, 최종 답이 맞았는지를 사람이 매번 확인할 수는 없습니다. 에이전트를 배포하고 나서 "품질이 떨어졌는지"조차 알기 어렵습니다.

이 문제를 세 가지로 나눠 풉니다.

- **트레이싱(Tracing)**: 에이전트 한 번의 실행을 단계별 기록(모델 호출, 도구 호출, 검색)으로 남깁니다. 문제가 생긴 지점을 찾는 데 씁니다.
- **평가(Evaluation)**: 기록된 응답에 스코어러(채점기)를 적용해 품질을 수치로 봅니다. 앱 버전을 비교하는 데 씁니다.
- **피드백(Feedback)**: 사람이 응답을 판정하고 정답을 달아 평가 기준과 데이터셋을 만듭니다.

Databricks에서 이 기능은 MLflow 3의 GenAI 기능으로 제공됩니다. 공식 문서 페이지 이름은 "What is agent observability and quality?"입니다.

## 어떻게 동작하는가

흐름은 다음과 같습니다.

| 단계 | 하는 일 | 결과물 |
|---|---|---|
| 계측 | 에이전트에 트레이싱을 켬 (자동 계측 또는 수동 스팬) | 트레이스가 MLflow 실험에 기록 |
| 관찰 | Traces 탭에서 실행을 열어 단계별로 확인, 트레이스 클러스터링으로 반복 실패 패턴 확인 | 문제 사례 목록 |
| 피드백 | 전문가가 Assess로 평가하고 기대 응답(Expectation)을 추가 | 피드백과 정답이 트레이스에 저장 |
| 데이터셋 | 트레이스를 평가 데이터셋에 추가 (골든 데이터셋) | 평가용 질의-정답 세트 |
| 평가 | 내장 또는 커스텀 스코어러를 실행 | 트레이스마다 피드백(채점 결과) 부착 |
| 모니터링 | 운영 트래픽의 일부에 같은 스코어러를 자동 실행 | 품질 추세 |

피드백과 기대 응답은 서로 다릅니다. **피드백** 은 실제 출력이 좋은지 판정하는 것이고, **기대 응답(Expectation)** 은 정답으로 생각하는 출력을 기록하는 것입니다. 둘 다 트레이스에 저장됩니다.

## 어떻게 쓰는가

### 1. 트레이싱 켜기

LangGraph 에이전트는 LangChain 자동 계측을 씁니다. 문서 예시는 다음과 같습니다.

```python
import mlflow
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
mlflow.langchain.autolog()  # LangGraph uses LangChain's autolog
mlflow.set_tracking_uri("databricks")
mlflow.set_experiment("/Shared/my-first-trace")
```

설치는 다음 명령으로 합니다.

```python
%pip install --upgrade "mlflow[databricks]>=3.1.0" "langgraph" "langchain-openai"
```

문서는 "one line"으로 30개 이상 프레임워크를 계측할 수 있다고 설명하지만, 이 페이지에서 확인한 자동 계측 함수는 `mlflow.langchain.autolog()`뿐입니다. 자동 계측이 닿지 않는 코드는 수동 커스텀 트레이싱 페이지를 참고하십시오.

> **참고** 위 예시의 `ChatOpenAI`는 `OPENAI_API_KEY`가 필요합니다. 문서는 Databricks Foundation Model APIs를 대신 쓸 수 있다고 명시합니다.

### 2. 트레이스 저장 위치

트레이스는 MLflow 실험(Experiment)에 연결되어 저장됩니다. UI에서는 **Experiments** 에서 실험을 찾고 **Traces** 탭을 엽니다.

문서는 저장소 옵션으로 Unity Catalog를 설명합니다. 트레이스를 Unity Catalog의 Delta 테이블로 저장하며, 스키마와 테이블 단위의 접근 제어가 적용되고 SQL로 직접 조회할 수 있다고 적혀 있습니다. 문서는 이것이 기본값인지는 명시하지 않습니다. Unity Catalog 저장소에는 실험당 제한이 없다고 설명합니다.

Agent Bricks CLI로 만든 프로젝트는 `agentbricks tracing bind --experiment-id <experiment-id>` 명령으로 트레이싱 실험을 연결합니다 ([Agent Bricks CLI로 에이전트 개발하기](build-agent-with-cli.md)).

### 3. UI에서 평가 실행

코드 없이 기존 트레이스를 평가할 수 있습니다.

1. Traces 탭에서 평가할 트레이스를 체크박스로 고릅니다.
2. **Actions** 에서 **Evaluate** 를 선택합니다.
3. **Run scorer** 대화상자에서 스코어러를 고릅니다. 사전 정의된 LLM-as-a-judge 스코어러, 등록된 스코어러(Registered scorer), 새 스코어러(**Create scorer**) 중에서 고를 수 있습니다.
4. **Run scorer** 를 누르면 결과가 트레이스에 피드백으로 붙고, **Evaluation runs** 탭에 실행 기록이 남습니다.

문서는 UI 결과가 프로그래밍 방식 평가와 같은 채점을 쓴다고 설명합니다.

사전 정의된 LLM-as-a-judge 스코어러는 문서에 세 가지로 적혀 있습니다. **Correctness**, **Completeness**, **Fluency** 입니다. 전체 목록은 스코어러와 LLM 판정기 페이지에 있습니다.

### 4. 코드로 평가하기

문서는 `mlflow.genai.evaluate()`로 평가 데이터셋을 돌려 앱 버전을 점수 매기고 비교하는 튜토리얼을 연결합니다. 이 페이지에서는 함수 이름만 확인했고, 인자 구조는 튜토리얼 페이지([Evaluate and improve an agent](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/evaluate-app))에서 직접 확인해 옮기십시오.

커스텀 스코어러는 데코레이터 `@scorer`로 만듭니다. 원문 주의사항은 주의사항 절에 옮겼습니다.

### 5. 사람 피드백과 리뷰 앱

| 기능 | 문서 표기 | 상태 | 용도 |
|---|---|---|---|
| 피드백과 기대 응답 | Assess, Add expectation | 문서에 명시 없음 | 트레이스 판정과 정답 기록 |
| 데이터셋 추가 | Add to dataset | 문서에 명시 없음 | 판정한 트레이스를 평가 데이터셋으로 이동 |
| 리뷰 앱 | Review App | 문서에 명시 없음 | 도메인 전문가가 좋은 응답의 기준을 정하고 LLM 판정기를 맞춤 |
| 리뷰 큐 | Review queues | Beta | 트레이스와 데이터셋 레코드를 리뷰어에게 한 건씩 배정 |

리뷰 앱은 두 방식으로 씁니다. Chat UI로 에이전트를 테스트하는 방식과, 전문가가 기존 트레이스에 라벨을 붙이는 방식입니다. 문서는 신규 사람 검토 워크플로에는 리뷰 큐를 권장합니다.

사용자별 역할은 문서에 다음처럼 나옵니다. 개발자는 개발 중에 트레이스에 품질 메모를 달고 회귀 테스트 예시를 표시합니다. 도메인 전문가는 리뷰 앱에서 라벨을 답니다. 배포된 앱의 최종 사용자도 피드백을 줄 수 있으며, 이는 문제 질의를 찾고 성공한 상호작용을 보존하는 데 쓰입니다.

### 6. 프로덕션 모니터링 (Beta)

운영 트래픽에 스코어러를 백그라운드로 돌리는 기능입니다. 상태는 Beta입니다. 문서 예시는 다음과 같습니다.

```python
from mlflow.genai.scorers import Safety, ScorerSamplingConfig

# Register and start a built-in judge
safety_judge = Safety().register(name="safety")
safety_judge = safety_judge.start(sampling_config=ScorerSamplingConfig(sample_rate=0.7))
```

필터로 평가 대상 트레이스를 좁힐 수 있습니다. 필터 문법은 `mlflow.search_traces()`와 같습니다.

```python
safety_judge = safety_judge.start(
    sampling_config=ScorerSamplingConfig(
        sample_rate=1.0,
        filter_string="attributes.status = 'OK'"
    ),
)
```

Unity Catalog 트레이스를 쓰는 실험에는 모니터링용 SQL 웨어하우스 ID를 설정해야 합니다. 설정하지 않으면 모니터링 작업이 실패한다고 문서가 설명합니다.

```python
from mlflow.tracing import set_databricks_monitoring_sql_warehouse_id

# Set the SQL warehouse ID for monitoring
set_databricks_monitoring_sql_warehouse_id(
    sql_warehouse_id="<SQL_WAREHOUSE_ID>",
    experiment_id="<EXPERIMENT_ID>"  # Optional, uses active experiment if not specified
)
```

결과는 스케줄 후 15~20분 뒤 실험의 Traces 탭에 평가 결과(assessment)로 나타나고, 품질 추세는 모니터링 대시보드에서 봅니다.

## 트레이드오프

| 선택 | 장점 | 제약 |
|---|---|---|
| 사전 정의 LLM 판정기 | 설정 없이 바로 씀 | 도메인 기준을 반영하지 못할 수 있음 |
| 커스텀 스코어러 | 업무 기준을 직접 정의 | 직렬화 제약 (아래 주의사항) |
| 프로덕션 샘플링 | 비용을 샘플 비율로 조절 | 샘플링에서 빠진 실패는 보지 못함 |
| 리뷰 큐 | 사람 검토를 체계적으로 배분 | Beta 상태 |

샘플 비율의 권장값은 문서에 나옵니다. 중요한 안전과 보안 검사는 `1.0`, 비용이 큰 LLM 판정기는 약 `0.05`~`0.2`, 개발 중에는 `0.3`~`0.5`입니다. 비율이 높을수록 비용이 올라갑니다.

## 주의사항

- **실험당 스코어러 한도**: 한 실험에 동시에 연결할 수 있는 스코어러는 최대 20개입니다.
- **커스텀 스코어러 작성 규칙**: 스코어러는 원격 실행을 위해 직렬화되므로 독립적이어야 합니다. Databricks 노트북에서 정의하고, import는 함수 본문 안에 두고, `@scorer` 데코레이터를 씁니다. 클래스 기반 `Scorer` 하위 클래스는 지원되지 않으며, import가 필요한 타입 힌트는 실패를 일으킬 수 있다고 문서가 설명합니다.
- **SQL 웨어하우스 설정 누락**: Unity Catalog 트레이스의 모니터링 작업은 웨어하우스 ID가 없으면 실패합니다. 실험 설정이 빠졌는지 먼저 확인하십시오.
- **결과 지연**: 모니터링 결과는 15~20분 뒤에 보입니다. 설정 직후 결과가 없다고 실패로 판단하지 마십시오.
- **스코어 해석**: LLM 판정기 점수는 판정기 모델과 기준에 따라 달라집니다. 점수 추세를 보되, 기준 변경이 있으면 기준선을 다시 잡으십시오.
- **상태 확인**: 프로덕션 모니터링과 리뷰 큐는 Beta입니다. 운영 SLA에 넣기 전에 확인하십시오.
- **민감 정보**: 트레이스에는 프롬프트와 응답 원문이 들어갑니다. 저장 위치와 접근 권한을 먼저 정하십시오. 보존과 감사는 [가드레일·거버넌스·모니터링](guardrails-governance-monitoring.md)에서 다룹니다.

## 참고 문서

- [What is agent observability and quality?](https://docs.databricks.com/aws/en/mlflow3/genai/agent-observability-and-quality)
- [Instrument your agent (MLflow Tracing)](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/overview)
- [Collect feedback and build datasets](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/)
- [Evaluate and improve](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/)
- [Set up production monitoring](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring)
