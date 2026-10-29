# Model Serving 커스텀 모델

> 기준일: 2026-10-28 · 근거: 공식 문서

Model Serving은 등록된 모델을 REST 엔드포인트로 노출하는 관리형 서빙 기능입니다. 이 페이지는 **커스텀 모델**(MLflow 형식의 Python 모델)의 엔드포인트를 다룹니다. Foundation Model APIs와 외부 모델은 [Foundation Model APIs](foundation-model-apis.md)에서, 게이트웨이 거버넌스는 [Unity Gateway](unity-gateway.md)에서 다룹니다.

## 왜 필요한가

| 이전 방식의 한계 | Model Serving이 해결하는 것 |
|---|---|
| 모델을 웹 서버에 직접 올려 운영한다 | 등록된 모델 버전을 선택해 관리형 엔드포인트로 배포한다 |
| 트래픽 증가에 맞춰 서버를 수동으로 늘린다 | 워크로드 크기와 동시성 설정에 따라 스케일링한다 |
| 모델 교체마다 클라이언트 코드를 바꾼다 | 엔드포인트 이름은 그대로 두고 서빙 구성(served entity)을 바꾼다 |

## 핵심 개념

| 용어 | 의미 |
|---|---|
| 서빙 엔드포인트(Serving endpoint) | 클라이언트가 호출하는 REST 주소. 이름으로 식별한다 |
| 서빙 엔티티(Served entity) | 엔드포인트가 실제로 서빙하는 모델 버전. `served_entities` 설정 항목이다 |
| 트래픽 설정(traffic config) | 여러 서빙 엔티티에 트래픽 비율을 나누는 설정 |
| 워크로드 크기(workload size) | 컴퓨트 규모. UI에서는 Small, Medium, Large 등 scale-out 단위로 고른다 |
| 스케일 투 제로(Scale to zero) | 요청이 없을 때 리소스를 0으로 줄이는 설정 |

> **참고** 문서는 엔드포인트 이름에 `databricks-` 접두사를 쓸 수 없다고 명시합니다. 예약 이유는 문서에 설명되어 있지 않습니다.

## 어떻게 동작하는가

### 생성 흐름

1. **Serving** 을 열고 **Create serving endpoint** 를 클릭합니다.
2. 엔드포인트 이름을 입력합니다.
3. 서빙 엔티티에서 **My models - Unity Catalog**(권장) 또는 **My models - Model Registry** 를 고르고, 모델과 버전을 지정합니다.
4. 트래픽 비율, 컴퓨트 유형과 크기, scale-out, 스케일 투 제로 여부를 설정합니다.
5. 필요하면 고급 구성에서 서빙 엔티티를 더 추가합니다.
6. **Create** 를 클릭합니다. 생성 직후 상태는 **Not Ready** 입니다.

### 상태 값

문서가 정의한 상태 값은 다음과 같습니다.

| 대상 | 필드·표시 | 의미 (문서 설명) |
|---|---|---|
| 엔드포인트 | UI "Not Ready" | 생성 또는 업데이트 중이거나 준비가 안 된 상태 |
| 엔드포인트 | `state.ready` = `READY` | 요청을 받을 수 있는 상태 |
| 엔드포인트 | `state.update_state` = `NOT_UPDATING` | 진행 중인 업데이트가 없는 상태 |
| 서빙 엔티티 | `state.deployment` = `DEPLOYMENT_READY` | 엔티티 배포가 준비된 상태 |
| 엔드포인트 | "Ready (Update failed)", "Not ready (Stopped)" 등 | 업데이트 실패나 중지 상태 |

> **주의** 업데이트가 실패하면 기존 구성이 계속 활성 상태로 남는다고 문서가 설명합니다. 실패 원인은 `deployment_state_message`에서 확인하십시오.

## 어떻게 쓰는가

### REST API로 생성

엔드포인트 생성 호출의 형태는 다음과 같습니다. `name`과 `config.served_entities`가 필수 구성입니다.

```bash
databricks api post /api/2.0/serving-endpoints --json '{
  "name": "churn-endpoint",
  "config": {
    "served_entities": [
      {
        "name": "churn-v2",
        "entity_name": "prod.ml_team.churn_model",
        "entity_version": "2",
        "workload_size": "Small",
        "scale_to_zero_enabled": false
      }
    ],
    "traffic_config": {
      "routes": [
        { "served_model_name": "churn-v2", "traffic_percentage": 100 }
      ]
    }
  }
}'
```

`entity_name`은 Unity Catalog의 `catalog.schema.model` 형식이고, `entity_version`은 등록된 버전 번호입니다.

### 구성 업데이트

업데이트는 `PUT /api/2.0/serving-endpoints/{name}/config`로 보냅니다. 서빙 엔티티와 트래픽 설정을 함께 넘깁니다.

```bash
databricks api put /api/2.0/serving-endpoints/churn-endpoint/config --json '{
  "served_entities": [
    {
      "name": "churn-v3",
      "entity_name": "prod.ml_team.churn_model",
      "entity_version": "3",
      "workload_size": "Small",
      "scale_to_zero_enabled": false
    }
  ],
  "traffic_config": {
    "routes": [
      { "served_model_name": "churn-v3", "traffic_percentage": 100 }
    ]
  }
}'
```

> **참고** 업데이트는 10~25분이 걸릴 수 있다고 문서가 설명합니다. 업데이트 중에는 상태가 "Not ready (Updating)"로 보입니다.

### 상태 조회, 중지, 시작, 삭제

| 작업 | REST 호출 (문서 명시) | 비고 |
|---|---|---|
| 상태 조회 | `GET /api/2.0/serving-endpoints/{name}` | `state` 필드 확인 |
| 중지 | `POST /api/2.0/serving-endpoints/{name}/config:stop` | 커스텀 모델 엔드포인트에서만, 진행 중 업데이트가 없을 때 가능 |
| 시작 | `POST /api/2.0/serving-endpoints/{name}/config:start` | 중지 전과 같은 속성의 새 구성 버전이 생성된다 |
| 삭제 | `DELETE /api/2.0/serving-endpoints/{name}` | 되돌릴 수 없다 |

중지된 엔드포인트에 요청을 보내면 400 오류가 반환됩니다.

### 권한

엔드포인트 권한은 `CAN MANAGE` 권한이 있어야 바꿀 수 있습니다. CLI에서는 다음 형태를 씁니다.

```bash
databricks permissions get serving-endpoints <endpoint-id>
```

`permissions update`는 `access_control_list`에 `user_name`과 `permission_level`을 넣어 호출합니다. 사용자 이메일은 `user@example.com` 같은 자리 표시자로 바꿔 쓰십시오.

## 스케일링

| 설정 | 문서 원문의 설명 |
|---|---|
| `workload_size` | 워크로드 크기. 예시 응답에 등장하며 UI에서는 Small, Medium, Large로 고른다 |
| 동시성 | 최소·최대 provisioned concurrency가 있으며 값은 4의 배수여야 한다 |
| GPU 워크로드 유형 | `GPU_SMALL`, `GPU_MEDIUM`, `MULTIGPU_MEDIUM`, `GPU_MEDIUM_8` |
| CPU 워크로드 유형 | `CPU_MEDIUM`, `CPU_LARGE`. 메모리가 큰 CPU 모델용 |
| 스케일 투 제로 | `scale_to_zero_enabled`로 켠다. 문서는 운영 엔드포인트에 권장하지 않는다고 설명 |

> **주의** 스케일 투 제로를 켜면 요청이 다시 들어올 때 콜드 스타트(cold start) 지연이 생깁니다. 지연에 민감한 운영 엔드포인트에서는 끄는 것이 문서 권장입니다.

## 트레이드오프

| 선택지 | 장점 | 단점 |
|---|---|---|
| 커스텀 모델 엔드포인트 | 직접 학습한 모델을 그대로 서빙한다 | 컴퓨트 크기와 동시성을 직접 맞춰야 한다 |
| Foundation Model APIs | 모델 호스팅을 Databricks가 맡는다 | 제공되는 모델 목록 안에서만 쓴다 |
| 외부 모델 | 외부 제공자의 모델을 같은 엔드포인트 형태로 쓴다 | 외부 제공자의 가용성과 정책에 의존한다 |

## 주의사항

- **엔드포인트 이름과 모델 버전을 분리하십시오.** 클라이언트는 엔드포인트 이름만 알고, 교체는 서빙 엔티티 업데이트로 하는 구성이 유지보수에 좋습니다.
- **Unity Catalog 모델을 우선 쓰십시오.** 문서가 "My models - Unity Catalog"를 권장합니다.
- **생성자 계정 상태를 확인하십시오.** 문서는 엔드포인트를 만든 사람이 워크스페이스 멤버에서 빠지면 업데이트가 `PERMISSION_DENIED`로 실패한다고 설명합니다. 생성자 계정에 의존하지 않도록 서비스 프린시펄로 엔드포인트를 관리하는 구성은 설계 제안이며, 문서의 강제 규정은 아닙니다.
- **운영 엔드포인트는 스케일 투 제로를 끄십시오.**
- **삭제 전에 호출하는 클라이언트를 확인하십시오.** 삭제는 되돌릴 수 없습니다.

## 참고 문서

- [Deploy models using Model Serving](https://docs.databricks.com/aws/en/machine-learning/model-serving/)
- [Create and manage serving endpoints](https://docs.databricks.com/aws/en/machine-learning/model-serving/create-manage-serving-endpoints/)
- [Manage serving endpoints](https://docs.databricks.com/aws/en/machine-learning/model-serving/manage-serving-endpoints/)
- [Unity Catalog의 모델 (권한 요건)](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/)
