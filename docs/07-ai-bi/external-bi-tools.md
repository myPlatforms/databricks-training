# 외부 BI 도구와 병행

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 300

## 한눈에 보기

AI/BI 대시보드와 Genie는 Databricks 안의 소비 계층입니다. 조직에 이미 Power BI나 Tableau 자산이 있다면, 둘을 **병행** 하는 것이 현실적입니다. 공식 AI/BI 도구 문서는 Partner Connect로 연결할 수 있는 BI 도구로 Hex, Power BI, Preset, Qlik Sense, Sigma, Tableau, ThoughtSpot을 나열합니다. 그 밖의 도구는 ODBC나 JDBC로 연결합니다.

병행의 핵심은 **지표 정의를 한 곳에 두고**, 두 소비 계층이 같은 정의를 읽게 하는 것입니다. 이 목적에 맞는 장치가 메트릭 뷰(Metric view)입니다.

| 연결 방식 | 무엇을 연결하는가 | 대표 대상 |
|---|---|---|
| Partner Connect | 워크스페이스의 SQL 웨어하우스와 BI 도구 | 파트너 BI 도구 전반 |
| ODBC·JDBC | 드라이버를 쓰는 임의의 도구 | 드라이버 지원 도구 |
| 메트릭 뷰 `MEASURE()` 쿼리 | 도구가 보내는 사용자 정의 SQL | Tableau, Sigma, Power BI(Native query) |
| 래퍼 뷰(Wrapper view) | 메트릭 뷰 위의 일반 뷰를 테이블처럼 노출 | 일반 테이블 연결만 되는 도구 |
| `/importBI` 가져오기 | Power BI·Tableau 파일을 메트릭 뷰와 대시보드로 변환 | 기존 보고서 이전 |

## 1. 왜 필요한가

### 이전 방식의 한계

- Power BI 보고서 안에 지표 계산식이 DAX로 들어 있으면, 같은 지표를 AI/BI 대시보드나 Genie Agent가 다르게 계산합니다.
- 기존 보고서를 한꺼번에 다시 만들면 시간이 많이 듭니다.
- 외부 도구마다 연결 방식이 달라 권한과 캐시를 따로 관리해야 합니다.

메트릭 뷰로 계산식을 한 번 정의하고 여러 도구가 쓰게 하면, 지표의 불일치를 줄이고 정의를 바꿀 때도 한 곳만 고치면 됩니다. 기존 보고서는 `/importBI`로 옮길 수 있습니다.

## 2. 어떻게 동작하는가

### 메트릭 뷰를 외부 도구에 연결하는 다섯 가지 패턴

공식 "Use metric views with external BI tools" 문서는 다섯 가지 패턴을 설명합니다.

| 패턴 | 방식 | 전제 |
|---|---|---|
| Genie Code로 가져오기 | `/importBI` 스킬로 Tableau·Power BI 파일을 메트릭 뷰로 변환 | 파일이 있어야 함 |
| 사용자 정의 SQL과 `MEASURE()` | 도구가 내장 쿼리 또는 사용자 정의 SQL 옵션으로 SQL을 보냄 | 대부분의 BI 도구가 지원 |
| 래퍼 뷰 | 메트릭 뷰 위에 일반 뷰를 만들고, 도구는 그 뷰를 테이블처럼 씀 | 차원 조합마다 뷰를 만들어야 함 |
| BI 호환 모드 | 도구가 `SUM`과 `COUNT`를 생성하면 Databricks가 올바른 측정값 계산으로 바꿔 줌 | 도구가 사용자 정의 SQL을 보낼 수 없을 때 |
| 내장 파트너 연동 | 도구에서 측정값과 차원이 SQL 없이 바로 보임 | 파트너가 지원해야 함 |

문서는 일부 파트너가 메트릭 뷰 지원을 내장하고 있으며, 그 연동은 Partner Connect 문서에 추가된다고 설명합니다. 특정 파트너 이름은 명시하지 않습니다.

### 도구별 연결 방식

| 도구 | 연결 방식 | 주의 |
|---|---|---|
| Power BI | Databricks Power BI 커넥터의 **Native query** 에서 `MEASURE()` 패턴을 DirectQuery 모드로 사용 | 메트릭 뷰 BI 호환 모드는 커넥터에서 제거됨 |
| Tableau | 사용자 정의 SQL의 `MEASURE()` 패턴, 또는 연결 대화 상자의 **Initial SQL** 필드에서 BI 호환 모드 설정 | 세부 설정은 Tableau 연결 문서 참고 |
| Sigma | `MEASURE()` 패턴을 쓰는 사용자 정의 SQL 기반 데이터셋 | 측정값 접근은 SQL로만 |
| 기타 JDBC·ODBC 도구 | 드라이버의 pass-through SQL 옵션으로 `MEASURE()` 패턴 사용 | 메타데이터는 JDBC 드라이버 문서 참고 |

> **주의** Power BI 메트릭 뷰 연동은 공식 문서 기준으로 바뀌었습니다. 공식 Power BI 문서는 Microsoft가 Databricks 커넥터에서 **Metric View BI Compatibility Mode** 옵션을 제거했으며, 그 옵션을 쓰던 보고서는 더 이상 동작하지 않는다고 명시합니다. 대체 방법으로는 커넥터의 Native query 옵션과 `MEASURE()`를 DirectQuery 모드에서 쓰는 방법을 안내합니다. 기존에 BI 호환 모드를 전제로 만든 Power BI 보고서가 있다면 이 변경을 먼저 확인하십시오.

## 3. 어떻게 쓰는가

### 3-1. Partner Connect로 연결하기

AI/BI 도구 문서는 각 파트너마다 "Connect to [도구] using Partner Connect" 링크를 제공합니다. Tableau의 경우 링크 문구는 "Connect Databricks to Tableau Desktop using Partner Connect"입니다. 절차는 해당 파트너 문서를 따르십시오.

Power BI 연결에 대한 공식 Power BI 문서의 설정 옵션은 다음과 같습니다.

| 항목 | 내용 |
|---|---|
| 인증 | 서비스 프린시펄을 쓰는 머신 간 OAuth |
| 드라이버 | ODBC 대신 **ADBC** 드라이버 사용 가능. Lakehouse Real-Time 웨어하우스에는 ADBC가 필요하다고 문서에 나옴 |
| SSO | Microsoft Entra ID를 SSO 공급자로 사용 |
| 메트릭 뷰 | BI 호환 모드는 제거되었음(위 주의 참고) |
| 역할 기반 연결 | `Assume` 권한이 있는 사용자가 역할로 OAuth 연결을 승인하면, Power BI는 그 역할로 쿼리를 실행 |

> **참고** Power BI 서비스에 Databricks 데이터를 게시하는 기능과 Power BI 작업(task)으로 의미 모델(semantic model)을 조율하는 기능도 문서에 나옵니다. 작업 기능은 먼저 UC에 Power BI 연결이 있어야 합니다. 두 기능의 세부 요건은 이 장에서 확인하지 않았습니다.

### 3-2. 메트릭 뷰를 `MEASURE()`로 연결하기

Tableau나 Sigma처럼 사용자 정의 SQL을 보낼 수 있는 도구는 메트릭 뷰를 `MEASURE()`로 쿼리합니다. 공식 문서의 쿼리 규칙은 다음과 같습니다.

- 모든 측정값은 `MEASURE` 집계 함수로 감싸야 합니다. Runtime 18.1 이상에서는 `AGG`도 됩니다.
- `SELECT *`는 쓸 수 없습니다. 모든 열을 명시해야 합니다.

```sql
SELECT
  `Order Status`,
  MEASURE(`Order Count`)
FROM catalog.schema.orders_metrics
GROUP BY ALL
```

위 쿼리는 도구가 보낼 사용자 정의 SQL의 형태를 보여 주는 예시입니다. 카탈로그와 객체 이름은 가상의 이름입니다. 쿼리 규칙의 자세한 설명은 [7페이지](metric-views-in-ai-bi.md)에 있습니다.

### 3-3. 래퍼 뷰로 연결하기

래퍼 뷰는 메트릭 뷰 위에 일반 뷰를 만들어, 테이블만 받는 도구도 쓸 수 있게 하는 방법입니다. 문서는 보고서가 필요로 하는 차원 조합마다 래퍼 뷰를 따로 만들라고 설명합니다.

> **주의** 래퍼 뷰는 차원 조합이 고정됩니다. 사용자가 자유롭게 차원을 고르는 메트릭 뷰의 장점이 줄어듭니다. 조합이 많으면 뷰 수가 늘어나므로, 사용자 정의 SQL을 보낼 수 있는 도구라면 래퍼 뷰보다 `MEASURE()` 연결을 먼저 검토하십시오.

### 3-4. `/importBI`로 기존 파일 가져오기

Genie Code의 `/importBI` 기능은 Tableau나 Power BI 파일을 메트릭 뷰로 가져옵니다. 절차는 다음과 같습니다.

1. 카탈로그 탐색기에서 스키마 이름을 누릅니다.
2. **Create** > **Metric view** 를 누르고 이름을 입력한 뒤 **Create** 를 누릅니다.
3. Genie Code를 열고 **New chat** 을 누릅니다.
4. **Import from a BI tool** 을 고르거나 `/importBI`를 입력합니다.
5. Tableau 또는 Power BI 파일을 첨부합니다.

받을 수 있는 파일 형식은 `.twb`, `.twbx`, `.tds`, `.tdsx`, `.pbit`, `.tmdl`입니다. UC 볼륨에 있는 파일을 경로로 참조할 수도 있습니다.

보고서 전체를 AI/BI 대시보드로 옮기려면 문서가 안내하는 별도 가이드 "Import BI files using Genie Code"를 따르십시오.

### 3-5. 가져오기 기능의 변화

| 날짜 | 항목 | 상태 |
|---|---|---|
| 2026-08-20 | `/importBI`로 Power BI·Tableau 가져오기 | GA |
| 2026-09-03 | `/importBI`에서 순위 테이블 계산 포함 | 라벨 없음 |
| 2026-09-10 | `/importBI`에서 매개변수가 있는 Tableau 계산 지원 확대 | 라벨 없음 |
| 2026-10-15 | `.tmdl` 파일로 Power BI 데이터 모델 가져오기 | 라벨 없음 |
| 2026-10-22 | Power BI·Tableau 파일 최대 100개 일괄 가져오기(Genie Code) | 라벨 없음 |

## 4. 트레이드오프

- **병행은 점진적 이전을 쉽게 하지만, 두 계층의 지표가 여전히 갈릴 수 있습니다.** 외부 도구의 DAX나 계산 필드가 메트릭 뷰와 같은 식을 쓰는지 검증하십시오.
- **`MEASURE()` 연결은 정확하지만 SQL을 보낼 수 있는 도구에 한정됩니다.** 사용자 정의 SQL이 없는 도구는 BI 호환 모드나 래퍼 뷰가 필요합니다.
- **BI 호환 모드는 도구가 집계를 생성하는 방식이라 사용할 수 있는 경우가 제한적입니다.** Power BI 커넥터에서는 제거되었습니다. Tableau에서는 Initial SQL 필드에서 설정합니다.
- **`/importBI`는 빠르지만 변환 결과를 검토해야 합니다.** 가져온 정의가 원본 보고서의 계산과 같은지 확인하는 단계가 필요합니다.

### 언제 쓰지 않는가

- 외부 도구의 보고서가 메트릭 뷰로 표현할 수 없는 복잡한 계산에 의존하는 경우
- 외부 도구 사용자에게 Databricks 쿼리 권한을 주기 어려운 경우. 서비스 프린시펄을 쓰더라도 권한 설계가 먼저입니다.

## 5. 주의사항

- **Power BI 보고서의 BI 호환 모드 의존성을 먼저 찾습니다.** 옵션이 제거되었으므로, 기존 보고서가 이 옵션을 쓰는지 점검하십시오.
- **모든 측정값을 `MEASURE()`로 감쌉니다.** 하나라도 빠지면 쿼리가 실패합니다.
- **`SELECT *`를 쓰지 않습니다.** 열을 명시해야 합니다.
- **서비스 프린시펄과 권한을 설계합니다.** 외부 도구의 연결 주체가 누구인지에 따라 UC 권한 검사 결과가 달라집니다. 06장 권한 모델을 기준으로 설계하십시오.
- **ADBC와 ODBC를 구분합니다.** Lakehouse Real-Time 웨어하우스에는 ADBC가 필요하다고 문서에 나옵니다.
- **Consumer access 사용자에게 외부 BI용 웨어하우스를 열 때 주의합니다.** Consumer access 문서는 사용자가 서드파티 BI 도구용으로 SQL 웨어하우스 접근을 받을 수 있다고 설명합니다. 웨어하우스 접근 범위를 점검하십시오.
- **`Publish to Power BI` 같은 게시 기능의 요건은 이 장에서 확인하지 않았습니다.** 요건을 추측하지 말고 Power BI 연결 문서에서 확인하십시오.
- **상태 라벨을 확인합니다.** 파트너 도구 페이지에는 라벨이 없습니다. 가져오기 기능의 GA와 라벨 없음은 위 표를 기준으로 하십시오.

## 참고 문서

- [AI/BI 도구(BI tools)](https://docs.databricks.com/aws/en/ai-bi/tools)
- [외부 BI 도구와 메트릭 뷰(Use metric views with external BI tools)](https://docs.databricks.com/aws/en/uc-semantics/metric-views/bi-tools)
- [Power BI와 Databricks(Power BI with Databricks)](https://docs.databricks.com/aws/en/partners/bi/power-bi)
- [메트릭 뷰 쿼리(Query metric views)](https://docs.databricks.com/aws/en/uc-semantics/metric-views/query)
- [Consumer access](https://docs.databricks.com/aws/en/ai-bi/consumers/)
- [AI/BI 릴리즈 노트 (2026)](https://docs.databricks.com/aws/en/ai-bi/release-notes/2026)
