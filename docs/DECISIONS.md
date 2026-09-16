# Open semantic decisions

All decisions below are OPEN; no rule approval is implied.

Dryer reconnaissance: combo WD90F53AVBUS belongs to both washer and dryer listings.
Future canonical SKU population must retain both listing provenances without creating
two exact identities (D08/D11). Its 103 kWh label is Clothes Washer energy, not dryer
or combined wash/dry energy (D01). Gas dryer EPA kWh and CEF test-basis semantics,
combo/stacked certification routing and heat-pump/vented applicability remain OPEN (D09).

Range reconnaissance: Samsung sales population includes gas/electric variants but
EPA m6gi-ng33 is residential electric cooking and includes both Cooktop and Range
product types (D09). Gas/dual-fuel applicability must not be inferred from dataset
nonmembership. Total annual energy and oven/cooking-top low-power component energy
are distinct measurements (D01). Oven Capacity 6.3 cu. ft. is a PDP source fact,
not an independent appliance-label identity gate in this EPA-only reconnaissance.

TV reconnaissance: Typical/Max/Stand-by power W and annual label/EPA energy kWh
must remain distinct (D01). Sample label assumes 5 hours/day and 16 cents/kWh;
PDP Typical 208 W cannot be treated as label 390 yearly kWh. OCR reading order puts
cost range $155 before product $62; coordinates/semantic regions are required (D07).
Label MRN75R95HAF versus PDP MRN75R95HAFXZA needs an approved suffix identity
contract; do not normalize away XZA to force a match. Claim absence is UNKNOWN.

Washer reconnaissance: the listing includes standalone, stacked and all-in-one PDPs.
Combo WD90F53AVBUS has a Clothes Washer EnergyGuide, not a combined wash/dry metric.
Catalog routing to bghd-e2wd versus separate combo dataset 9jai-gs6t remains OPEN
(D09); do not force listing membership into certification type. Its label explicitly
requires same-test-procedure yellow-number comparisons (D01). Preserve label/test
basis before numerical findings; no new issue code is implied.

Dishwasher reconnaissance: mixed US EnergyGuide + Canadian EnerGuide in one PDF
requires US-region selection with OCR coordinates (D07); whole-page text order is
insufficient. PDP 16 place settings and label Standard capacity category are distinct
quantities. No numeric discrepancy or wildcard identity conclusion is inferred.
EPA date_certified replaces refrigerator date_qualified but neither alone establishes
current certification (D09). These are source gaps, not new audit issue codes.

Refrigerator reconnaissance note (2026-09-16): D08's count grain is empirically
resolved for this product group: 41 API groups = 41 rendered cards, 75 exact SKUs.
PLP grouping ID and PDP bridge request group_id are different namespaces.
D07 remains OPEN: PDP capacity 29 cu.ft. vs label 28.6 cu.ft. needs an approved
measurement/rounding contract before capacity can corroborate OCR identity.
D09 remains OPEN: dataset schema is verified but current/withdrawn status and
wildcard/UPC matching semantics are not inferred from availability or date_qualified.

| ID | Gap | Proposed direction | Due |
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
