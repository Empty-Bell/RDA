# 남은 마일스톤 — 2026-09-17

현재 **Phase 0 / G0 PASS**, **Phase 1 / G1 진행 중**, Phase 2–7 미착수다.
종료 기록: G0_ACCEPTANCE_RECORD.md, 통합 hosted checkpoint 35169843199.
11개 제품군 PLP 조사와 대표 PDP/라벨/EPA 샘플, 런타임 고정·cold/recovery,
소스 쿼리·claim·라벨 품질의 제한된 검증은 완료했다. 전체 모델별 PDP·라벨·EPA
연결 수집과 규제 판정은 아직 구현하지 않았다. 조사 성공을 전체 수집 성공으로
표시하지 않는다. 이번 공식 근거 수집은 hosted run 35169376748에서 계약 테스트
12개와 함께 통과했고, 독립 fixture 검증 run 35169376791은 참조 99개를 확인했다.
11군 근거표는 APPLICABILITY_EVIDENCE.md에 기록했다. 개별 SKU 적용성은 미판정이다.

| 순서 / 상태 | 할 일과 중간산출물 | 종료 검증 |
|---|---|---|
| **G0 종료 — PASS** | source matrix·계약/fixture coverage 대조와 후속 의미 결정의 시점 고정 완료 | 214개 테스트 중 213 성공·선택적 CV 1개 skip(기존 cold에서 실행), fixture 참조 99개 검증. 개별 적용성·판정 정책은 후속 gate까지 보류 |
| **G1 골격 — 진행 중** | typed schema, config, canonical SKU/provenance, run/evidence manifest, CLI, fixture CI; Python 3.11 호환성 | null/unknown/오류/다중 finding/중복 SKU/서로 다른 run 참조를 hosted CI에서 검증. D04/D08/D11/D12 관련 계약 확정 |
| **G2 냉장고 관통 — 미착수** | 먼저 소규모 PLP→PDP→PDF/OCR→EPA→판정→증거→대시보드, 이후 냉장고 전체 모집단 | 실제 전체 수집 coverage, OCR golden suite, 허용오차·보강증거·current/US/wildcard 판정표, 양 도메인 분리 검증. D01–D04/D07/D09/D10 선결 |
| **G3 FTC 3군 확장 — 미착수** | Dishwasher→Clothes Washer→Television adapter 및 제품군별 측정량·라벨 구조 | 네 FTC군 전체 모집단·정답/오류 fixture 검증, 냉장고 회귀 유지 |
| **G4 EPA 7군 확장 — 미착수** | Range/Cooktop→Dryer/Hood→Monitor/Computer/Tablet. 콤보·스택형·구성별 적용성과 인증 연결 | 11군 전체 수집 상태 설명. 무claim/비적용/미확인/조회 실패를 구분하고 제품군별 hosted 검증 |
| **G5 이력 — 미착수** | previous/current snapshots, 변화·모집단 이탈 기록 | NEW→OPEN→RESOLVED→REOPENED 재생. 이탈·실패가 해소로 바뀌지 않음; D05/D12 |
| **G6 운영 안정화 — 미착수** | full Actions orchestration, raw 증거 장기 보존·복원, 자원/재시도 예산, RUNBOOK, 수동 full run | cold full 실행·장애 주입·재실행 ID·게시 차단·복구 통과 후 schedule 활성화 |
| **G7 Pages — 미착수** | 검증된 동일 run artifact 배포, 링크/필터/mobile QA, 복구 절차 | run/hash 일치와 완전성 gate. 실패 bundle 게시 차단; D06 결정 |

사용자의 다음 단계 요청으로 AGENTS.md 범위를 G1까지 확장했다.
초안 계약·CLI·fixture CI부터 구현하며, 실제 판정과 공개 배포는 후속 단계다.
G1 미완료 항목과 승인 제안은 DATA_CONTRACTS.md / G1_DECISION_PROPOSAL.md를 참조한다.
각 종료 기록은 PASS/FAIL/BLOCKED와 실제 hosted Actions run/commit/attempt/
artifact를 갖는다. 위 표는 제품의 법적 적합 판정이나 완료 예정일 보장이 아니다.

## 결정해야 할 사항의 시점

- **G0 종료 검토:** 관측된 소스와 미지원/미확인 경로 구분, D08의 source grain 및
  D09의 조사 사실 정리. wildcard/UPC/US market/current 판정 정책은 임의 승인 금지.
- **G1:** SKU 및 증거/run 연결, 집계 단위, 저장/재실행 식별자 계약.
- **G2:** 비교 측정량·허용오차, 독립 OCR 보강조건, claim/인증/오류 판정, UI 완료 상태.
- **G5–7:** 이탈/해소 정책, 장기 보존·복원, 부분 실패 run의 게시 여부.

DECISIONS.md의 D01–D12는 전부 OPEN이다. 관측 사실은 이미 수집할 수 있으므로
매 단계 조사 전에 반복 확인을 요청하지 않는다. 필요한 판정 구현 직전에 근거를
갖춘 구체적인 결정표를 검토 대상으로 제시한다.

## 토큰·실행 비용

조사 workflow는 표준 라이브러리와 제한된 공개 API 응답을 우선 사용하고, 기존
성공한 cold/runtime 증거를 재사용한다. 소스 계약이 바뀐 경로만 추가 검증하되,
공통 런타임·parser 변경은 필요한 전체 회귀를 수행한다. 기존 모델 운용안을
재사용하며 새 추천/가격 추정은 하지 않는다. 모든 감사/수집 Actions는 **LLM 0회**다.

현재 근거: PHASE_STATUS.md, SOURCE_COVERAGE.md, G0_REVIEW.md,
APPLICABILITY_EVIDENCE.md와 docs/evidence의 hosted 기록.
