# US Samsung Regulatory Audit — 단계별 착수·검증·모델 운용 가이드

작성일: 2026-09-16 · GitHub-hosted runner 우선 설계 반영  
기준: `US_SAMSUNG_REGULATORY_AUDIT_MASTER_PLAN_v2.md` §0–33  
상태: 실행 준비안. 원본 계획의 규칙을 대체하거나 미정 의미를 승인한 문서가 아니다.

2026-09-17 현재 G0는 소스 조사·hosted 실행 기반 범위에서 PASS다.
G0_ACCEPTANCE_RECORD.md와 PHASE_STATUS.md가 현재 종료 상태의 근거다.
아래 초기 폴더/구현 미확인 설명은 작성 당시의 준비 상태 기록이며,
현재는 Phase 1 골격 구현·검증 중이다. 제품 식별/집계/실행 ID의 G1 기준은
2026-09-17 사용자 승인으로 확정했다(G1_DECISION_PROPOSAL.md). 그 밖의
미확정 판정·게시·보존 정책은 계속 OPEN이다.

## 1. 검토 결론과 현재 상태

원본의 소스 분리, exact SKU 기준, PyMuPDF 우선, 오류의 PASS 전환 금지, 단일 run 기반 게시 구조는 유지한다. Phase 0 조사부터 착수할 수 있다. 다만 아래 의미 결정이 끝나기 전 해당 판정·집계·이력 로직을 확정하면 안 된다.

현재 작업 폴더에는 마스터 플랜만 확인되었다. 구현 코드·AGENTS.md·테스트·실측 fixture·GitHub 설정은 확인되지 않았다. 이번 작업은 문서 검토와 착수 준비이며, Samsung/EPA 실측, 법규 적용성 검증, CI 실행 또는 배포를 완료한 것이 아니다. 문서에 등장하는 산출물과 테스트는 이후 구현할 항목이다.

권장 순서: **Phase 0 → Phase 1 → Phase 2의 소규모 냉장고 관통 검증 → 냉장고 전체 모집단 검증 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7**.

**GitHub Actions의 표준 GitHub-hosted `ubuntu-24.04` x64 러너가 처음부터 기준 실행환경이다.** Phase 0 첫 작업에 bootstrap/probe workflow를 만들고, Phase 1부터 CI, Phase 2부터 live smoke를 실행한다. Phase 6은 Actions 도입 단계가 아니라 이미 가동 중인 전체 감사의 운영 안정화 단계다. 로컬 PC는 편집·디버깅 보조 환경이며, 로컬 성공만으로 어떤 단계도 PASS 처리하지 않는다. Phase 2에서 fixture 기반 대시보드까지 연결하되 공개 배포는 Phase 7에서 한다.

## 2. 착수 전 결정 목록

아래는 문서 간 공백/충돌에 대한 제안이다. `OPEN` 항목은 담당자가 근거와 결정을 DECISIONS.md/ADR에 기록해야 하며, 모델이 임의로 확정하지 않는다. 조사·스키마 초안 등 독립 작업은 계속 진행한다.

| ID | 원본 근거 / 문제 | 권장 정리 | 확정 시점 |
|---|---|---|---|
| D01 | §10·12: kWh 비교는 요구하지만 차이의 허용오차·단위·이슈 코드가 없음 | 제품군별 측정량·단위·기간·시험기준의 비교 가능성을 먼저 정의. 차이 기록과 finding 발행을 분리. 신규 코드/심각도는 명시적 승인 대상 | Phase 2 규칙 전 |
| D02 | §12·13: 우선순위와 양 도메인 동시 finding의 관계 불명확 | 모든 control 평가를 보존하고 도메인별 대표 이슈/정렬을 별도 정의하는 안 검토. 전역 첫 이슈에서 반환하여 EPA를 누락시키지 않음 | Phase 1–2 |
| D03 | §16·20.4: Hero의 LOW-only, 미평가, coverage=0 처리 미정 | 평가 완결성 → finding 상태 순으로 판정표 작성. 미평가·오류를 PASS로 표시하지 않음. LOW-only 표시와 HIGH+오류 동시 표시 결정 | Phase 2 UI 전 |
| D04 | §20.5: finding 수와 SKU 수 혼합 가능 | finding 수, 영향받은 고유 SKU 수, 배타적 모델 요약 상태를 분리. coverage 분모와 양 도메인 완료 조건 명시 | Phase 1 |
| D05 | §18: 모집단 이탈/수집 실패가 RESOLVED로 오인될 위험 | 동일 SKU/control의 유효한 재평가로만 해소 판정하는 안 검토. 이탈·미평가는 별도 관측 메타데이터, 기존 history 상태를 임의 추가하지 않음 | Phase 5 |
| D06 | §3·27: 부분 가족 게시와 모든 가족 게시 gate 관계 | V1 production은 전 가족 gate 통과 시만 교체하는 안 권장. 실패 run은 진단 artifact에 보관하고 기존 validated site 유지 | Phase 6–7 |
| D07 | §8: OCR 독립 보강증거의 최소 충족 조건 없음 | 제품군별 필수/선택 보강증거와 모순 시 우선조건을 표로 고정. URL 일치만으로 독립 검증으로 취급하지 않음 | Phase 2 OCR 전 |
| D08 | §3: family는 제품군과 tile group 양쪽 의미로 사용 | product_group과 source family_id의 의미를 계약에 구분. 페이지 count가 tile/SKU 중 무엇인지 실측하여 동일 grain끼리 대조 | Phase 0 |
| D09 | §11: current EPA, 미국 시장, 중복 인증, wildcard 의미 미정 | dataset별 갱신/상태/시장/모델 패턴 계약 작성. 불완전 조회를 no-candidate로 바꾸지 않음. 지원하지 않는 제품군은 미확인/비적용 근거를 구분 | Phase 0–2 |
| D10 | §12·25: 읽기 불가 HIGH와 403/429 pipeline 장애의 경계 | 실제 개별 문서 문제와 수집환경/광역 장애 구분표 작성. timeout만으로 문서 부재를 확정하지 않음 | Phase 2 |
| D11 | §15·17·20: fact provenance/run_id와 다중 finding 표현 보강 필요 | fact와 evidence의 run 연결·버전·hash를 보장. report는 SKU당 1행 + 다중 issue 표현을 명세하여 finding 유실 방지 | Phase 1 |
| D12 | §17·18: raw artifact 만료, 역사 저장소, 재실행 ID 충돌 | 보존기간·복구·history 입력 저장 위치·재시도 식별자 결정. 같은 초/commit 재실행 충돌 검증 | Phase 1, 5–6 |

적용 대상·인증 프로그램 범위 등 법규 의미는 원본의 가정을 그대로 검증 완료로 취급하지 않는다. Phase 0에서 FTC/EPA 공식 출처, 확인일, 해당 문구 위치를 근거표로 남긴다. DOE를 데이터 입력으로 추가하지 않는다.

## 3. 단계별 작업 카드

모델 표기: Luna=`gpt-5.6-luna`, Terra=`gpt-5.6-terra`, Sol=`gpt-5.6-sol`, Astra=`gpt-6-astra`. 모델은 개발 작업에 사용한다. 정기 감사 실행은 Python/Playwright/PyMuPDF/RapidOCR와 버전 고정 규칙으로 처리하여 **LLM 호출 0회**를 기본 설계로 한다.

| 단계 | 진입 조건 / 작업 단위 | 중간산출물 | 종료 검증 | 권장 모델·추론 |
|---|---|---|---|---|
| 0 조사 | 원본 이해. 0A Actions bootstrap/probe → 0B 러너에서 Samsung → 0C 러너에서 EPA → 0D cold-start 재검증 | runner contract, probe workflow, source contracts 2종, 11군 source matrix, 비식별 fixture+hash, Actions log/artifact | G0. headless browser·PDF/OCR 설치부터 소스 파싱까지 hosted Ubuntu에서 재현 | Sol medium 주도; 문서 정리는 Luna low; 복잡한 계약 충돌만 Astra high |
| 1 스키마·골격 | G0. 미확정 의미는 명시적으로 비활성 | typed models, 5개 config, run/evidence manifest, CLI, DATA_CONTRACTS, TEST_STRATEGY, AGENTS | G1. null/unknown/오류/다중 issue/중복 SKU/참조 무결성·직렬화 검증 | Terra medium; 스키마 경계 검토 Sol high |
| 2 냉장고 관통 | G1 + D01–04·07·10 결정 | population→PDP→PDF/OCR→EPA→assessment→evidence→site 전 경로, golden cases | G2a–G2e 전부 통과. 소규모 성공 뒤 냉장고 전체 모집단 gate. 이전 실패 미해결 시 다른 군 확장 금지 | 핵심 parser/OCR/rules Sol high; 수집 연결·UI Terra medium; 최종 경계 검토 Astra high 1회 |
| 3 FTC+EPA 확장 | G2e. Dishwasher → Clothes Washer → Television, 군별 독립 작업 | 3개 adapter, field/unit mapping, 군별 fixture/회귀표 | G3. 4군 전체 모집단 검증, 군별 정답·오류 fixture, 냉장고 회귀 유지 | Terra medium; 신규 문서 구조·측정량 차이 Sol high |
| 4 EPA 중심 확장 | G3. Range/Cooktop → Dryer/Hood → Monitor/Computer/Tablet 묶음 | 7군 adapter, applicability/claim matrix, 미국시장·current 인증 근거 | G4. 11군 모두 상태 설명. FTC N/A, claim 없음, EPA 조회 실패를 각각 구분 | Terra medium; 매칭 모호성 Sol high |
| 5 이력 | G4 + D05·12 결정 | history snapshot, delta, population-change metadata, 이력 replay fixture | G5. NEW→OPEN→RESOLVED→REOPENED 및 모집단 이탈·실패 run을 포함한 재생 | Terra medium; 상태전이 검토 Sol high |
| 6 Actions 운영 안정화 | G5 + Phase 0부터 가동 중인 workflows | full workflow 안정화, history 복원, artifact manifest, RUNBOOK, 수동 full log | G6. cold-start full, 자원 예산, 실패 주입·재시도·게시 차단. 안정성 확인 후 schedule | Terra medium; 환경/권한/재시도 장애 Sol medium 또는 high |
| 7 Pages | G6 + D06 결정 + 검증된 site bundle | pages workflow, 게시 manifest, 공개 URL, 복구 절차 | G7. 동일 artifact 배포, run/hash 일치, 링크·필터·mobile 확인. 실패 bundle 배포 차단 | Terra medium; 외형·문서 정리 Luna low; 게시 gate 검토 Sol high |

모든 단계의 종료는 PASS/FAIL/BLOCKED와 증거 경로를 남긴다. PASS에는 실제 hosted Actions run URL·commit·run attempt·로그·artifact가 필수다. 실행 전에는 NOT_STARTED로 관리하고 통과 표시를 미리 채우지 않는다. 외부 접근/결정 미확정은 BLOCKED, 테스트 불일치는 FAIL이다. 단계 PASS는 제품의 규제 적합 판정이 아니다.

## 4. 주요 거점별 중간산출물 검증

### G0 — 소스 계약 동결

- 11개 제품군마다 PLP URL, 발견된 endpoint/method/params, count grain, pagination 종료조건, representative/variant 구조, PDP identity, EPA dataset/status를 기록한다.
- 정상·빈 결과·다음 페이지·누락 필드·중복 variant·오류 응답을 fixture로 준비한다. 실제 수집본과 합성 장애 fixture를 표시로 구분한다.
- 각 fixture는 수집 URL/시간, hash, 비식별 처리 내역, 예상 필드를 갖는다. Cookie/Authorization/개인정보는 제거하되 파서 동작에 필요한 구조는 보존한다.
- endpoint 존재 확인만으로 통과하지 않는다. 첫 페이지부터 마지막까지 재생하고 필수 필드 제거 시 계약 테스트가 실패하는지 확인한다.
- GitHub-hosted Ubuntu에서 실제 source probe를 수행한다. 로컬 결과는 차이 분석에만 사용한다. cache 없는 신규 러너에서 설치·Chromium 실행·embedded PDF·image-only OCR·소스 접근·artifact 업로드를 검증해야 G0 PASS다. 필수 러너 검사 미검증이면 Phase 1 진입을 보류한다.
- source matrix의 11군 행이 완결되고 활성 소스는 실제 응답+파싱 근거가 있어야 한다. 소스 미확인·프로그램 비적용 여부가 미정인 행은 관련 gate를 BLOCKED로 남긴다.

### G1 — 데이터 계약

- 내부 join key와 중복 제거 기준을 고정한다. 같은 SKU가 여러 PLP에 있으면 provenance를 보존하고 제품 수를 중복 증가시키지 않는다. 제품군 간 SKU 충돌도 묵살하지 않는다.
- `0`, `null`, 미관측, 해당 없음, 수집 실패를 별도 fixture로 확인한다. ENERGY STAR claim은 true/false/unknown과 관측 출처를 보존한다.
- 모든 assessment의 SKU·evidence 참조가 유효해야 한다. 서로 다른 run을 결합하면 검증이 실패해야 한다.
- 1 SKU에 FTC HIGH와 EPA MEDIUM이 있는 fixture에서 report 1행, finding 2건, affected SKU 1개가 유지되는지 검증한다. 구체적인 대표 상태는 D02/D04 결정표를 따른다.

### G2a — 모집단과 PDP

- 최종 렌더된 대표 tile 수 = 페이지 N Results = API의 같은 grain 총수. lazy load 전체 완료가 확인되지 않으면 불완전으로 남긴다.
- exact SKU 집합은 대표 SKU와 모든 variant의 합집합에서 결정된 key로 중복을 제거한 집합과 일치해야 한다. 대표 tile 수와 exact SKU 수를 같다고 가정하지 않는다.
- 필수 fixture: 두 페이지 경계 중복, variant 누락, 총수 변동, 0건, redirect, 다른 SKU 응답, 선택한 variant와 구조화 model 불일치.
- 모집단 hash/수집시점/파싱 근거를 보관한다. 라이브 중 count가 변하면 제한된 재수집 후에도 불일치할 때 FAIL, 무한 retry 금지.

### G2b — PDF/OCR

- golden fixture별 label model/kWh/단위/이미지 위치를 사람이 확인한 expected file로 고정한다. 구현 결과에서 정답을 역생성하지 않는다.
- 원본 §26의 13개 범주 전부 포함: embedded text, image-only, 저해상도, B↔8, O↔0, I/l↔1, S↔5, wildcard, 반복 wildcard, 보정 성공, 진짜 wrong model, kWh 누락, malformed PDF.
- HTTP 200 HTML과 빈 PDF도 추가한다. PDF hash·signature·engine·fallback reason·raw/normalized 값·최종 상태를 assertion한다.
- PyMuPDF 우선, RapidOCR 재사용, threads 1/1, 2× 기본, 필요한 경우만 3× ROI+Otsu가 실행되는지 spy/log로 확인한다.
- 동일 숫자 필드가 우연히 맞는 다른 모델을 넣어 과도한 OCR 보정을 막는다. 보정 성공 케이스와 진짜 불일치 control을 함께 통과해야 한다.
- golden suite 내 false mismatch/false correction 0건을 목표 gate로 사용한다. 이 수치를 실제 모든 제품에 대한 정확도 보장으로 표현하지 않는다.

### G2c — EPA 및 규칙

- exact pattern, exact UPC, 중복 UPC, prefix+kWh, no-candidate 각각을 독립 fixture로 검증한다. 미국시장 필터·인증 상태·dataset snapshot/갱신 메타데이터도 확인한다.
- API timeout/부분 pagination/필드 drift는 no-candidate가 되지 않아야 한다.
- claim 없음+no-candidate → 그 사실만으로 finding 없음. claim 있음+정상 조회+no-candidate → 원본 eligibility 후보 규칙. EPA 실패 → 관련 평가 미완료. 이 세 경로를 분리한다.
- 각 원본 issue code의 양성/음성/경계 사례와 동시 trigger를 테스트한다. OCR 보정 informational은 actionable finding 집계에서 제외한다.
- EnergyGuide 실패가 EPA 결과를 오염시키지 않고 EPA 부재가 FTC 실패를 만들지 않는지 양방향 테스트한다.
- 수집 장애, missing document, wrong document의 분류는 D10 판정표를 따라 검증한다.

### G2d — 증거와 대시보드

- `assessment → evidence_id → manifest → 원본 hash/위치`를 역추적한다. 공개 compact 증거와 raw artifact의 대응도 확인한다.
- 현재 데이터 패키지의 run_id 단일성, population/report SKU 집합 동등성, family 합계, finding 집계, control mapping, CSV 행 수를 기계 검증한다.
- history 안의 과거 run_id는 허용된 과거 레코드다. 현재 패키지 envelope와 Hero가 이전 run을 가리키는 혼합을 차단한다.
- fixture site를 동일 입력·고정 clock·정렬·버전으로 두 번 빌드하여 파일 hash를 비교한다. 휘발성 메타데이터가 있다면 제외 필드와 이유를 명시한다.
- 원본 §20.20의 UI acceptance를 전부 자동화한다. 모든 queue/report 필터, heatmap 연결, CSV, evidence 링크를 확인하고 JS가 판정/심각도를 다시 계산하지 않는지 코드 검토한다.
- mutation 검증: run_id 하나 변경, report에서 SKU 삭제, evidence 파일 누락, severity 합계 변조 각각에 대해 build가 실패해야 한다.

### G2e / G3 / G4 — 확장 허용

- G2e는 냉장고 전체 모집단 실행과 golden suite가 모두 통과해야 한다. 소규모 smoke만으로 다른 군 확장을 허용하지 않는다.
- G3/G4는 새 제품군마다 G0 계약 및 G2a–d 해당 항목을 다시 적용한다. 소스 구조가 같아 보인다는 이유로 fixture를 생략하지 않는다.
- 수작업 spot check는 새 군에서 대표/variant, claim true/false/unknown, PDF 직접추출/OCR, EPA exact/ambiguous를 우선 선정한다. 해당 사례가 라이브에 없으면 합성 fixture로 보완하고 구분한다.
- 파일럿의 모든 HIGH·OCR 보정·EPA 모호 사례를 검토하고, 정상 사례도 경로별 최소 1개 원본과 대조한다. 전수 기계 검증과 표본 육안 검증을 서로 대체하지 않는다.

### G5 — 이력 재생

- 최소 4회 고정 run으로 `NEW → OPEN → RESOLVED → REOPENED`를 재생한다.
- 중간에 source 실패, SKU 이탈, 신규 SKU 유입, rule_version 변경, 동일 run 재처리를 끼워 넣는다. 미관측을 해소로 바꾸거나 같은 finding을 중복 생성하면 실패한다.
- 이전 validated history를 입력으로 쓰는 규칙과 rule 변경 시 비교 가능성 처리법을 명시한다. FIRST/latest/resolved 시간도 assertion한다.

### G6 / G7 — 운영·게시

- 제안 안정성 기준: 서로 다른 수집시점의 수동 full 3회 연속 gate 통과 후 schedule 활성화. 이는 실측된 안정성 수치가 아닌 초기 운영 정책 제안이다.
- 한 제품군 429, OCR crash, EPA timeout, 산출물 누락, artifact 업로드 실패를 주입한다. 실패는 실행 상태에 남고 production 게시가 차단되어야 한다.
- build 이후 deploy 전에 재수집하지 않는다. 검증한 site artifact의 run_id·git_sha·hash를 배포 manifest와 비교한다.
- 늦게 끝난 과거 run이 최신 run을 덮어쓰지 않도록 게시 순서/동시실행 제어를 검증한다.
- Pages 프로젝트 경로에서 CSS/JS/JSON/evidence URL을 확인한다. desktop/mobile smoke와 console 오류 검사를 수행한다.
- 실패 시 직전 validated bundle로 복구하는 rehearsal과 artifact 보존기간 만료 시 설명 가능한 상태를 점검한다.

## 5. 모델별 역할과 비용 판단

아래 역할 배분은 이 프로젝트에 대한 추천이며 실측 벤치마크 결과가 아니다. 현재 세션에 노출된 Codex 모델 목록에는 Luna/Terra/Sol/Astra가 있다. 앱에서 지원되는 추론 수준에 맞춰 low/medium/high부터 사용한다.

| 모델 | 맡길 일 | 피할 일 |
|---|---|---|
| Luna low | 확정 명세의 문서/매핑 정리, 반복적인 작은 파일 변경, 로그 요약 | 규제 의미 결정, OCR 보정 안전성, EPA 패턴 설계, 전체 아키텍처 |
| Terra medium | 기본 구현, 확정 계약 기반 adapter 반복 확장, UI, CLI, workflow | 불명확한 규칙을 추측하며 구현 |
| Sol medium/high | 탐색적 소스 조사, 복잡한 parser, OCR/매칭/규칙, integration failure 분석 | 단순 rename/복사/집계를 매번 장문으로 처리 |
| Astra high | 다중 계약 충돌, 시스템 경계, false PASS 위험 검토, Sol로 해결되지 않는 복합 장애 | 모든 반복 작업에 일괄 사용 |

공식 문서는 Terra를 지능/비용 균형, Luna를 비용 민감 대량 작업, Sol을 복잡한 전문 작업용으로 설명한다. API 표준 텍스트 가격은 확인 시점 기준 100만 input/output tokens당 Luna $0.20/$1.20, Terra $2/$12, Sol $4/$20이다. 이 가격을 Codex 구독 한도 차감률로 환산하지 않는다. 긴 입력·캐시·도구 등 별도 조건도 존재한다. [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol).

작은 모델이 항상 총 토큰을 적게 쓰는 것은 아니다. Astra 공식 가이드도 일부 평가에서 더 적은 출력 토큰과 낮은 과업당 추정 비용을 보고한다. 따라서 재작업까지 포함하여 선택한다. [공식 모델 가이드](https://developers.openai.com/api/docs/guides/latest-model).

동일 범위에서 실패 원인을 특정하지 못한 수정이 2회 반복되면 전체 과정을 재시작하지 말고, 실패 테스트·관련 계약·최소 fixture·변경 diff를 묶어 한 단계 상향한다. 의미 미정은 모델 상향으로 승인된 규칙이 되지 않는다. 네트워크 차단도 추론 수준을 올려 해결할 문제가 아니다.

## 6. 토큰 최소화 실행 규약

1. **개발 시에만 LLM 사용.** 제품 수만큼 모델을 호출하는 구조를 만들지 않는다. OCR과 감사 규칙은 코드로 수행한다.
2. **작업 단위는 한 계약/한 adapter/한 gate.** Phase 2 전체를 한 번에 맡기지 않고 G2a→G2b→G2c→G2d로 나눈다.
3. **첫 세션에서 전체 원본 숙지, 이후 관련 계약과 변경분만.** 각 작업 카드는 관련 원본 절 번호, 허용 파일, fixture ID, 선행 gate를 명시한다. 핵심 불변조건은 짧게 유지한다.
4. **큰 원본은 파일에 보관.** HTML/PDF/JSON 전체를 대화에 반복 출력하지 않고 `rg`, JSON 필드 추출, 필요한 페이지/ROI로 좁힌다. 출처/원본 hash는 잃지 않는다.
5. **offline fixture 우선.** 코드 변경마다 live full crawl 하지 않는다. 단위·계약 테스트 후 관련 live smoke, 단계 종료 때 full 검증한다.
6. **출력은 변경점·검증·잔여 위험·다음 입력.** 코드 전체를 답변으로 재출력하지 않는다. 테스트 로그는 실패 핵심과 원본 로그 경로만 전달한다.
7. **단계 경계에서 인계 파일 작성.** 긴 대화 재독 대신 1쪽 이내 상태+계약 경로+재현 명령을 사용한다. 계약이 변하면 인계도 갱신한다.
8. **high/max를 상시 사용하지 않는다.** 일반 작업은 medium, 기계적 변경은 low. high는 규칙/OCR/경계 검토에 집중하고 xhigh/max는 구체적인 미해결 문제에서만 평가한다.
9. **모델 검토보다 기계 gate 우선.** 행 수·hash·run_id·참조 무결성은 스크립트가 검증한다. 모델은 실패 원인과 의미 충돌을 검토한다.
10. **첫 3개 작업 카드로 보정.** 실제 입력/출력/추론 토큰(관측 가능할 때), 경과시간, 재시도, 재열림 여부를 기록한다. 구독 환경에서 확인 불가능한 토큰은 추정값으로 꾸미지 않는다.

권장 지표: `성공한 작업 카드당 총 토큰/시간`, `첫 검증 통과율`, `후속 회귀 발생률`. 최소 단가나 한 번의 응답 길이만 최적화하지 않는다. 컨텍스트 절약 때문에 필요한 원본 증거·반례 테스트를 삭제하지 않는다.

## 7. GitHub-hosted runner 실행환경 계약

아래는 구현 시 적용할 초기 설계다. 아직 workflow 실행이나 자원 실측을 완료한 것은 아니다.

| 항목 | 초기 설계 / 검증 |
|---|---|
| 러너 | `runs-on: ubuntu-24.04`, 표준 x64 VM. OS label과 별개로 runner image version 기록 |
| 런타임 | Python 3.12 audit, 3.11/3.12 fixture CI. Node 22는 사용하는 작업에서 설치 |
| 의존성 | Python lock/제약 파일, Node lockfile, 검증된 Action commit SHA 고정. 공통 bootstrap 재사용 |
| 브라우저 | Playwright 버전 고정 후 `python -m playwright install --with-deps chromium`. headless 신규 context, 개인 profile/cookie 불필요 |
| OCR | PyMuPDF→RapidOCR, CPU ONNX. 모델 파일/version/hash 명시, cache miss 설치 검증. 초기 worker 1개, engine 재사용, threads 1/1 |
| 경로 | pathlib·workspace 상대 경로, 임시 파일은 runner temp. Windows 드라이브·개인 절대 경로 금지 |
| 시간/식별 | UTC 및 `GITHUB_RUN_ID`/`GITHUB_RUN_ATTEMPT`를 manifest에 기록하여 재실행 구분 |
| 네트워크 | concurrency 2 시작, 3은 측정 후. timeout 30초·retry 3·backoff+jitter. browser 별도 timeout |
| 상태/cache | job 간 디스크 공유 가정 금지. history 명시적 복원. cache는 dependency/OCR binary 최적화에만 사용 |
| orchestration | 초기 acquisition→assessment→build는 한 job. stage 증분 기록, canonical population/run 일치 |
| artifact | compact validated bundle/raw diagnostics 분리. 이름에 run/attempt 포함. 일반 step 실패 시에도 가용 로그 업로드하고 실패 exit 유지 |
| 권한 | CI/collection은 `contents: read`. Pages job에만 필요한 `pages: write`, `id-token: write`. history 쓰기는 저장방식에 맞춰 별도 최소 권한 |

공개 저장소의 표준 Ubuntu x64 VM은 확인 시점에 4 CPU/16 GB RAM/14 GB SSD 사양이다. 이 수치는 감사 성공의 실측 근거가 아니다. 신규 VM·이미지 변경·소스의 러너 IP 접근성을 고려한다. [GitHub runner 문서](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). 브라우저/시스템 의존성 명시 설치는 [Playwright CI 문서](https://playwright.dev/python/docs/ci)를 따른다.

### 초기 자원·시간 예산

아래는 프로젝트 정책 초안이며 Phase 0/2/4 측정으로 조정한다. GitHub 서비스 최대 제한과는 별개다.

- probe job timeout 20분, fixture CI 30분, live smoke 30분, full audit 120분으로 시작한다. 설치/수집/OCR/빌드 시간을 각각 기록한다.
- full 내부 실행 예산은 job timeout보다 최소 10분 짧게 설정하여 정리·업로드 여유를 둔다. 초과 시 불완전 상태로 종료하고 게시를 차단한다.
- 감사 프로세스 peak RSS 8 GB 이내, 자체 작업파일 8 GB 이내, 여유 디스크 3 GB 이상을 초기 목표로 측정한다. bootstrap 이후 공간 부족 시 시작하지 않는다.
- PDF 스트리밍 저장, 필요한 OCR page/ROI만 렌더, 종료된 browser context 정리로 사용량을 제한한다. 필요한 raw 증거를 용량 확보를 위해 몰래 삭제하지 않는다.
- stage manifest를 증분 기록한다. 일반 실패에서는 업로드를 시도하지만 hard cancellation/VM 유실에서는 마지막 업로드가 보장되지 않음을 운영 상태에 반영한다.
- Phase 2의 냉장고 전체, Phase 4의 11군 전체에서 시간·메모리·디스크·artifact 크기를 측정한다. 초과 시 중복 이미지 제거와 bounded processing부터 개선한다.
- sharding은 측정 후 ADR로 도입한다. source snapshot/config/rule/run을 통일하고 shard 누락·중복·merge 집합 검증을 추가한다. job concurrency 합이 소스 요청 예산을 초과하지 않게 한다.

### 단계별 Actions 발전 경로

```text
Phase 0  runner-probe.yml + bootstrap + cold-start 계약
Phase 1  ci.yml: lint/type/unit/contract/schema (live crawl 없음)
Phase 2  smoke-audit.yml + 수동 refrigerator full + fixture dashboard
Phase 3–4 동일 full 진입점에 검증된 family adapter 추가
Phase 5  이전 validated history 명시적 복원/재생
Phase 6  11군 full 안정화·자원 측정·복구·schedule
Phase 7  검증된 immutable site artifact만 Pages 배포
```

full 실행 실패와 finding 발생을 구분한다. 정상 감사가 HIGH 후보를 발견한 것은 수집 실패가 아니다. 실행/데이터 gate 실패는 게시 불가이며, HIGH finding 자체를 이유로 검증된 dashboard를 숨기지 않는다.

표준 hosted 러너에서 소스가 지속 차단되면 해당 경로는 BLOCKED다. 개인 PC 성공이나 self-hosted 결과를 hosted 목표 통과로 간주하지 않는다. 응답·시점·재시도 근거를 남기고 hosted 환경에서 허용되는 공식 소스 접근 경로를 검토한다.

## 8. 다음 세션의 착수 패킷

첫 작업은 **P0-A: GitHub Actions bootstrap/probe와 문서 골격**이다. Sol medium으로 시작한다. 생성할 파일은 원본 §21·29에 맞추되 빈 문서를 검증 완료로 표시하지 않는다.

- AGENTS.md: 원본 §22의 14개 규칙 반영.
- docs/MASTER_PLAN.md: 원본을 기준 문서로 복사하고 원본 경로·hash를 기록, 중복본 간 수정 정책 명시.
- docs/DECISIONS.md: D01–D12를 OPEN으로 등록.
- docs/SAMSUNG_SOURCE_CONTRACTS.md, EPA_SOURCE_CONTRACTS.md: 조사 항목 template, UNKNOWN 표시.
- docs/TEST_STRATEGY.md: G0–G7와 테스트/fixture 연결표.
- docs/PHASE_STATUS.md: NOT_STARTED/RUNNING 및 종료 PASS/FAIL/BLOCKED, 증거 경로.
- docs/GITHUB_HOSTED_RUNNER_CONTRACT.md: 아래 실행환경·자원·artifact·권한 계약.
- .github/workflows/runner-probe.yml: 수동 hosted Ubuntu probe.
- scripts/bootstrap.sh 및 scripts/runner_probe.py: 명시적 설치와 체크별 상태/로그. 실제 endpoint 미관측 부분은 미검증으로 보고.
- configs/families.yaml: 원본 11군과 도메인 범위. 아직 관측하지 않은 endpoint는 추측해 채우지 않음.

P0-A에서 설치·browser·PDF/OCR probe를 먼저 돌린 뒤 P0-B/C의 소스 실측을 같은 hosted 러너에서 수행한다. P0-D는 cold-cache 재실행 및 fixture 업로드 검증이다. 리포지토리/권한 미확정이면 workflow와 조사 초안은 준비하되 G0는 BLOCKED로 남기고 이후 구현 단계로 넘어가지 않는다.

재사용 가능한 작업 프롬프트:

```text
이번 범위: [P0-B 또는 G2b 등 한 작업 카드].
AGENTS.md, 해당 source/data/rule 계약, EXECUTION_GUIDE의 관련 gate를 읽어라.
첫 착수 세션에는 MASTER_PLAN 전체를 읽어라. 후속 세션은 관련 절과 변경분을 확인하라.
선행 gate: [상태/근거 파일]. 허용 변경: [파일/모듈 목록].
입력 fixture: [ID/경로]. 요구 산출물: [목록].
판정 의미·issue code는 추측하지 말고 미정 부분을 결정 목록에 기록하라.
정상·반례·source 실패를 검증하고 오류를 PASS로 바꾸지 마라.
대형 원본은 파일로 보존하고 필요한 필드만 출력하라.
해당 gate를 통과하면 중지하고 다음 단계로 범위를 넓히지 마라.
최종 보고: 변경 파일, 실행 명령/실제 결과, PASS/FAIL/BLOCKED,
증거 경로, 미해결 결정, 다음 세션 입력. 미실행 검사를 PASS로 쓰지 마라.
```

단계 검증 기록 양식:

```yaml
phase: "2"
gate: G2b
status: NOT_STARTED
git_sha: null
run_id: null
contract_versions: {}
fixture_ids: []
checks: [] # command, exit_code, log_path, expected, observed
evidence_paths: []
open_decisions: []
model: null
reasoning_effort: null
reviewer: null
next_action: null
```

자동 검증 결과가 gate 통과의 근거다. 모델의 “문제없음” 서술이나 화면이 그럴듯하게 보이는 것만으로 다음 단계에 진입하지 않는다.
