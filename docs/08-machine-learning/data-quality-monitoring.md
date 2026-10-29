# 데이터 품질 모니터링

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

데이터 품질 모니터링(Data quality monitoring)은 Unity Catalog의 데이터 자산 품질을 감시하는 기능입니다. 두 가지 기능으로 구성됩니다. **이상 탐지(Anomaly detection)** 는 테이블의 신선도(freshness)와 완전성(completeness)을 과거 패턴과 비교합니다. **데이터 프로파일링(Data profiling)** 은 요약 통계를 계산하고, 시간에 따른 분포 변화(드리프트)를 비교합니다. 프로파일링은 추론 테이블(inference table)을 감시해 ML 모델과 모델 서빙 엔드포인트도 추적합니다.

> **참고** 문서는 데이터 프로파일링이 구 명칭 **Lakehouse Monitoring** 의 후속이라고 명시합니다. 검색 시에는 현재 명칭 "Data quality monitoring"을 쓰십시오.

## 왜 필요한가

| 이전 방식의 한계 | 품질 모니터링이 다루는 것 |
|---|---|
| 적재가 늦거나 행이 빠져도 보고서를 보고서야 안다 | 이상 탐지가 커밋 이력으로 신선도를 예측하고, 늦으면 stale로 표시 |
| 적재 행 수가 줄어도 알 수 없다 | 최근 24시간 커밋 행 수를 예측 범위와 비교 |
| 모델 입력 분포가 바뀌어도 알 수 없다 | 프로파일 메트릭과 드리프트 메트릭을 시간과 기준선에 대해 계산 |
| 품질 검사를 테이블마다 따로 짠다 | 스키마 단위로 한 번에 켬 |

## 두 기능 비교

| 항목 | 이상 탐지 (Anomaly detection) | 데이터 프로파일링 (Data profiling) |
|---|---|---|
| 감시 내용 | 신선도, 완전성 (Beta: null 비율, 슬라이스별 완전성) | 요약 통계, 시간 구간별 메트릭, 기준선 대비 드리프트 |
| 설정 단위 | 스키마 (카탈로그 단위도 가능) | 테이블 또는 추론 테이블 |
| 결과 | 시스템 테이블, 상태 표시, 인시던트 목록 | Delta 메트릭 테이블 2개와 프로파일별 대시보드 |
| ML과의 관계 | 직접 관계는 문서에 명시 없음 | 추론 테이블로 모델 입력, 예측, 성능을 추적 |
| 상태 라벨 | 문서에 명시 없음 (아래 상태 값은 기능 내부 표시) | 문서에 명시 없음 |

## 이상 탐지 (Anomaly detection)

### 동작 원리

| 검사 | 방식 (문서 원문) |
|---|---|
| 신선도 (Freshness) | 커밋 이력을 분석해 다음 커밋 시점을 예측. 커밋이 비정상적으로 늦으면 테이블을 stale로 표시 |
| 완전성 (Completeness) | 최근 24시간에 커밋된 행 수를 예측 범위와 비교. 하한보다 적으면 incomplete |
| Percent null (Beta) | 최근 24시간 컬럼별 null 비율을 추적. 예측 상한을 넘으면 incomplete |
| 완전성 슬라이싱 (Beta) | 최대 3개 슬라이스 컬럼의 고유 값별로 완전성 평가. 고유 값이 50개 이하인 컬럼에만 적용. 하나라도 incomplete이면 테이블은 unhealthy |
| 스캔 | 중요도가 높은 테이블을 우선 스캔하고, 덜 중요한 테이블은 빈도를 낮춤. 켜면 테이블이 갱신되는 주기와 같은 빈도로 스캔 |
| 지연 | 스마트 스캔은 초기 스캔에서 건너뛴 테이블의 상태 표시를 최대 2주까지 지연할 수 있음 |

> **참고** 백그라운드 잡이 테이블을 감시하며, 감시 대상 테이블을 수정하지 않고 테이블을 채우는 잡에 오버헤드를 더하지 않는다고 문서가 설명합니다.

### 스키마에서 켜기

1. Catalog Explorer에서 스키마를 열고 **Details** 탭을 클릭합니다.
2. **Data Quality Monitoring** 항목에서 **Enable** 을 클릭합니다.
3. **Anomaly detection** 이 켜져 있는지 확인하고 **Save** 를 클릭합니다.

- 필요 권한: 스키마 또는 상위 카탈로그의 `MANAGE`.
- 카탈로그 단위로 켜려면 카탈로그의 **Details** 탭을 씁니다. 한 번에 최대 50개 스키마까지 켤 수 있습니다.
- 특정 테이블을 제외하려면 Create 또는 Update Monitor API의 `excluded_table_full_names` 파라미터를 씁니다. 파라미터 이름은 원문 그대로입니다.
- 끄면 이상 탐지 잡과 관련 테이블, 정보가 모두 삭제되며 되돌릴 수 없습니다.

### 결과가 보이는 곳

| 위치 | 내용 |
|---|---|
| 시스템 테이블 `system.data_quality_monitoring.table_results` | 결과 저장. 컬럼 목록은 문서에 없음 |
| Catalog Explorer의 스키마·테이블 페이지, 계보 그래프의 테이블 노드 | 상태 표시(health indicator) |
| Data Quality Monitoring UI (**View results**) | 상태, First Detected, Last Scanned, Reason, Root Cause, Impact, Scan Frequency, Results, Error State, Details 열 |
| Recently Resolved Incidents | Resolution 열: Auto-resolved 또는 Not an issue |
| 레거시 대시보드 | `/Shared/Databricks Quality Monitoring/Data Quality Monitoring` |

상태 표시 값은 Healthy, Unhealthy, Training, Error, Excluded, Not enabled입니다. "Assign to me"와 "Not an issue" 조치는 7일 동안 유지됩니다.

### 권한과 제약

- 상태 표시를 보려면 테이블에 `SELECT` 또는 상위 카탈로그에 `BROWSE`가 필요합니다. 품질 세부 정보를 보려면 테이블에 `SELECT`가 필요합니다.
- 뷰와 외부 테이블(foreign table)은 지원되지 않습니다.
- 완전성 검사는 null, 0, NaN 비율을 고려하지 않습니다.
- 이벤트 신선도(Event freshness)는 현재 버전에서 지원되지 않습니다.

### 비용 성격

서버리스 컴퓨트에서 돌며, 청구 제품은 `DATA_QUALITY_MONITORING`으로 표시된 서버리스 DBU입니다. 비용은 감시 대상 테이블 수와 크기에 비례합니다. 시스템 테이블에 쌓이는 스캔 결과 저장은 과금되지 않는다고 문서가 설명합니다.

## 데이터 프로파일링 (Data profiling)

### 프로파일의 종류

| 종류 | 대상 | 계산 방식 |
|---|---|---|
| Time series | 타임스탬프 컬럼이 있는 테이블 | 시간 구간별로 메트릭 계산 |
| Inference | 타임스탬프, 입력, 예측, 선택적 정답 레이블이 있는 모델 요청 로그 | 시간 구간별로 모델 성능과 데이터 품질을 비교 |
| Snapshot | 그 밖의 모든 테이블 | 전체 데이터를 계산하며, 갱신할 때마다 전체를 다시 처리. 최대 4TB |

- 기준선 테이블(baseline)은 선택 사항이며, 드리프트를 재는 기준으로 씁니다. 추론 프로파일의 기준선은 주 테이블의 InferenceLog와 같은 피처 컬럼과 `model_id_col`을 가진 학습 또는 검증 데이터를 쓰라고 문서가 안내합니다.
- 메트릭은 테이블 전체와, 지정한 시간 구간과 슬라이스별로 계산됩니다.
- 시계열과 추론 프로파일은 최근 30일을 계산합니다. 이를 바꾸려면 Databricks 계정 팀에 문의해야 한다고 문서가 설명합니다.
- 지원 형식: Delta Lake 테이블(관리형, 외부, 뷰, 구체화된 뷰, 스트리밍 테이블)과 Unity Catalog 관리형 Iceberg 테이블.

### 결과 테이블

프로파일을 만들면 지정한 Unity Catalog 스키마에 Delta 메트릭 테이블 두 개가 생깁니다.

| 테이블 | 내용 |
|---|---|
| 프로파일 메트릭 테이블 (profile metrics) | 요약 통계 |
| 드리프트 메트릭 테이블 (drift metrics) | 시간에 따른 드리프트, 기준선이 있으면 기준선 대비 드리프트 |

물리 테이블 이름과 컬럼 목록은 문서의 "Data profiling metric tables" 페이지에 있습니다. 이 장은 컬럼 이름을 추정하지 않았습니다. 프로파일마다 대시보드가 자동으로 만들어집니다.

### 설정 절차

설정 세부는 두 가이드에 나뉩니다. UI는 "Create a profile using the Databricks UI", API는 "Create a data profile using the API"입니다. 예제 노트북도 제공됩니다. 이 페이지는 UI 단계와 SDK 코드를 싣지 않았습니다.

- 필요 권한: 상위 카탈로그와 스키마에 `USE CATALOG`, `USE SCHEMA`, 테이블에 `SELECT`, 카탈로그·스키마·테이블 중 하나에 `MANAGE`.
- 워크스페이스가 Unity Catalog에 연결되어 있고 Databricks SQL에 접근할 수 있어야 합니다.
- 추론 프로파일은 요청 로그 테이블을 씁니다. 모델 쪽 로그 설정은 [Foundation Model APIs](foundation-model-apis.md)와 [Unity Gateway](unity-gateway.md)의 페이로드 로깅 항목을 참고하십시오.
- 구체화된 뷰에 대한 프로파일은 증분 처리를 지원하지 않는다고 문서가 명시합니다.

### 비용 성격

데이터 프로파일링은 잡에서 서버리스 컴퓨트를 씁니다. 계정에서 서버리스 컴퓨트를 따로 켜 둘 필요는 없다고 문서가 설명합니다. 비용 추적은 "View data quality monitoring expenses" 페이지에서 확인하며, 단가는 이 장에서 다루지 않습니다.

## 트레이드오프

| 선택지 | 장점 | 단점 |
|---|---|---|
| 이상 탐지 (스키마 단위) | 한 번의 설정으로 많은 테이블을 감시한다 | 뷰와 외부 테이블은 대상이 아니고, 완전성 검사의 범위가 제한된다 |
| 데이터 프로파일링 | 요약 통계와 드리프트를 시간에 따라 본다 | 스냅샷 프로파일은 갱신마다 전체를 다시 계산해 비용이 커질 수 있다 |
| 직접 짠 품질 검사 잡 | 검사 로직을 완전히 통제한다 | 검사 코드와 실행 스케줄을 직접 유지해야 한다 |

## 주의사항

- **켜기 전에 대상 테이블을 고르십시오.** 감시 대상이 많을수록 서버리스 DBU가 늘어납니다. 중요도 높은 스키마부터 켜고, 제외 파라미터로 나머지를 조절하십시오.
- **스냅샷 프로파일의 크기를 확인하십시오.** 최대 4TB이며 갱신 때마다 전체를 처리합니다.
- **추론 프로파일의 기준선을 맞추십시오.** 피처 컬럼과 `model_id_col`이 다르면 드리프트 결과가 의미 없습니다.
- **상태 표시 권한을 확인하십시오.** 테이블 `SELECT` 또는 카탈로그 `BROWSE`가 없으면 상태가 보이지 않습니다.
- **끄기는 되돌릴 수 없습니다.** 이상 탐지를 끄면 관련 결과 테이블까지 삭제됩니다.

## 참고 문서

- [Data quality monitoring (개요)](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/)
- [Anomaly detection](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/anomaly-detection/)
- [Data profiling](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/)
- [Machine learning on Databricks](https://docs.databricks.com/aws/en/machine-learning/)
