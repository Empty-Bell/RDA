"use strict";

// Presentation-only translations. Model identities, source URLs, raw field
// paths/values, grade codes and exported evidence remain unchanged.
(() => {
  const preferenceKey = "rda-dashboard-language";
  const familyNames = {
    "냉장고": "Refrigerators", "식기세척기": "Dishwashers", "세탁기": "Washers",
    "레인지": "Ranges", "쿡탑": "Cooktops", "의류건조기": "Dryers",
    "후드": "Hoods", "모니터": "Monitors", "컴퓨터": "Computers",
    "태블릿": "Tablets"
  };
  const koreanToEnglish = {
    "미국": "United States", "홈": "Home", "Audit 홈": "Audit home",
    "페이지 내 이동": "Page navigation", "제품군별 문제 위치": "Issues by product family",
    "현재 상태": "Current status", "판정 분포": "Grade distribution",
    "전체 제품군": "All product families", "전체 심각도": "All severities",
    "전체 판정": "All grades", "전체 모델": "All models",
    "통과율": "Pass rate", "우선 조치": "Priority action",
    "확인 필요": "Review needed", "공개 보완": "Disclosure update",
    "조치 대상 보기": "View action queue", "통합 스냅샷 빌드": "Unified snapshot",
    "모델별 근거 로딩 중": "Loading model evidence",
    "11개 제품군의 최신 단일 감사 실행에서 공개 정보와 판정 근거를 확인합니다.": "Review disclosures and evidence from the latest unified audit of 11 product families.",
    "판정 이력": "Finding history",
    "문제가 사라진 첫 실행은 재확인 중으로 기록하고, 다른 원본 수집 실행에서 다시 확인되면 해결 확정으로 표시합니다.": "A finding absent in one run remains pending. It is resolved only after another independent source run confirms its absence.",
    "모델 단위 판정. PASS, HIGH, MEDIUM, LOW는 중복 없이 집계됩니다.": "One mutually exclusive PASS, HIGH, MEDIUM or LOW grade per model.",
    "숫자를 선택하면 해당 모델 목록으로 이동합니다.": "Select a count to open the matching models.",
    "이슈를 열어 잘못된 값과 조치 방향을 확인하세요.": "Open an issue to see the conflicting evidence and next action.",
    "전체 모델을 빠르게 찾고, 필요한 건만 상세 확인합니다.": "Find any model and open its evidence when needed.",
    "모델별 수집값, 판정 코드와 비교 설명을 한 행에서 확인합니다. 값이 없으면 원본에서 수집되지 않은 항목입니다.": "Review collected values, finding codes and comparisons in each model row. A blank means the source did not provide that value.",
    "근거·조치 보기": "View evidence and action", "VALUE · kWh 추출됨": "VALUE · kWh extracted",
    "EnergyGuide 연간 kWh 값 추출됨. 다른 출처와의 일치 판정은 아닙니다.": "An annual kWh value was extracted from EnergyGuide. This does not mean it matches another source.",
    "—는 해당 실행의 근거에서 확인되지 않은 값입니다.": "— means the value was not available in this run's evidence.",
    "제품군별 원본 실행과 판정 기준을 확인합니다.": "Review source runs and grading rules by product family.",
    "이슈 유형별 빠른 필터": "Quick filters by issue type",
    "모델 또는 이슈 검색": "Search model or issue", "조치 목록 검색": "Search action queue",
    "모델 검색": "Search models", "전체 모델 검색": "Search all models",
    "조건에 해당하는 조치 건이 없습니다.": "No actions match these filters.",
    "조건에 해당하는 모델이 없습니다.": "No models match these filters.",
    "현재 목록 CSV ↓": "Filtered CSV ↓", "전체 원본 CSV ↓": "All raw CSV ↓",
    "전체 모델의 판정 등급 구성": "Grade distribution across all models",
    "제품군": "Product family", "모델": "Model", "판정 포인트": "Finding",
    "심각도": "Severity", "로고": "logo",
    "판정": "Grade", "라벨": "Label", "상세": "Details",
    "이전 페이지": "Previous page", "다음 페이지": "Next page",
    "맨 위로": "Back to top", "출처와 기준": "Sources and rules",
    "출처 및 판정 방법 보기": "View sources and methods",
    "집계 범위: 태블릿은 PF에서 수집된 50개 SKU 중 실제 PLP 카드에 표시된 11개만 판정합니다. PLP 카드에 없는 39개 옵션 SKU는 별도 제품으로 더하지 않습니다. TV는 정의된 MNA 모델 2개를 원본 167개에서 제외한 165개를 판정합니다.": "Scope: Tablets include the 11 SKUs shown on PLP cards, from 50 PF-collected SKUs; the other 39 options are not counted as separate products. TV includes 165 of 167 source models after excluding two defined MNA models.",
    "판정 범위": "Assessment scope", "판정 기준": "Grading rules", "링크 기준": "Link rules",
    "원본 제품군 run은 이전 스냅샷과 같습니다.": "The source family run is unchanged from the previous snapshot.",
    "이전 run 대비": "Compared with previous run", "기준 스냅샷": "baseline snapshot",
    "이번에 처음 발견": "First seen in this run", "재확인 중": "Pending confirmation",
    "현재 PASS지만 독립적인 다음 수집에서 확인 필요": "Currently PASS; awaiting another independent collection",
    "해결 확정": "Confirmed resolved", "다른 원본 수집에서도 finding이 없음": "Absent in another independent source run",
    "해결 확정 뒤 다시 발견": "Found again after resolution", "재발": "Recurred",
    "신규": "New", "판정 변경": "Grade changed", "변경 모델": "Changed models",
    "집계 범위 변경": "Population change", "추가": "Added", "제외": "Removed",
    "범위 변경은 신규/해결 확정에 포함하지 않습니다.": "Population changes are excluded from new and resolved counts.",
    "모델별 판정 스냅샷 비교.": "Comparison of model-grade snapshots.",
    "판정/이슈 변경": "Grade/issue changes",
    "현재 PASS 전환은 다음 독립 수집 전까지 재확인 중으로 표시합니다.": "A transition to PASS stays pending until the next independent collection.",
    "비교할 이전 스냅샷이 없어 변화 건수는 표시하지 않습니다.": "No previous snapshot is available for a change count.",
    "전체": "All", "조치 항목 없음": "No action needed",
    "합계": "Total", "통과율": "Pass rate", "수집/비교/판정": "Collection/comparison/assessment",
    "모델별 이력을 저장합니다.": "Model history is recorded.",
    "전체 원본": "All raw", "개 필드는 모델 상세의": " fields are available in model details under",
    "또는 CSV·Excel에서 확인할 수 있습니다.": "or in CSV and Excel exports.",
    "판정 이유": "Reason for grade", "확인할 점": "What to check",
    "핵심 공개 정보": "Key disclosure evidence",
    "모델명 대조": "Model comparison", "PDP 모델": "PDP model",
    "EnergyGuide 모델 패턴": "EnergyGuide model patterns", "EPA 모델 패턴": "EPA model pattern",
    "라벨 후보 중 하나 이상이 PDP 모델과 일치합니다.": "At least one label model matches the PDP model.",
    "빨간 글씨만 가장 가까운 패턴과의 문자 차이입니다.": "Red characters show the difference from the closest pattern.",
    "*는 한 자리 모델 문자 후보입니다.": "* represents one model character.",
    "일치": "Match", "연간 에너지 사용량": "Annual energy use",
    "PDP·EnergyGuide 용량 불일치": "PDP–EnergyGuide capacity mismatch",
    "PDP와 EnergyGuide의 용량을 대조해 잘못된 공개값을 확인하세요.": "Compare PDP and EnergyGuide capacity and identify the incorrect disclosure.",
    "용량 비교 (cu.ft)": "Capacity comparison (cu.ft)",
    "PDP 용량이 라벨·EPA 값과 다릅니다.": "PDP capacity differs from the label and EPA values.",
    "복수 후보값 · 원본 확인": "Multiple candidates · check source",
    "PDP 누락 판정과 수집값이 다릅니다.": "The missing-PDP finding conflicts with a collected value.",
    "해당 모델의 PDP 에너지 항목을 재확인하세요.": "Recheck the PDP energy field for this model.",
    "출처 값이 서로 다릅니다.": "Source values differ.",
    "합의된 기준값이 없어 오답을 특정하지 않았습니다.": "No consensus value is available, so no single source is marked wrong.",
    "두 출처가 같은 값을 냅니다.": "Two sources agree.",
    "다른 수치만 강조했습니다.": "Only the differing value is highlighted.",
    "수집값 없음": "No collected value", "확인 자료 없음": "No evidence",
    "미수집": "Not collected", "미추출": "Not extracted", "미확인": "Unverified",
    "EnergyGuide 수치": "EnergyGuide value",
    "EPA 등록": "EPA registration", "ENERGY STAR 표기": "ENERGY STAR claim",
    "ENERGY STAR 표시 ↔ EPA 등록": "ENERGY STAR claim ↔ EPA registration",
    "ENERGY STAR 표기 비교": "ENERGY STAR claim comparison",
    "표기 여부가 서로 다릅니다.": "The claims differ across surfaces.",
    "세 화면의 ENERGY STAR 표시를 같은 상태로 맞추세요.": "Align the ENERGY STAR claim across the three surfaces.",
    "EnergyGuide 확인": "EnergyGuide availability", "EnergyGuide 문서": "EnergyGuide document",
    "문서 연결 없음": "No document link", "연결됐으나 PDF 내용 판독 불가": "Linked PDF could not be read",
    "문서 내용 확인됨": "Document content verified", "연결됨 · 수치 미추출": "Linked · value not extracted",
    "라벨 모델": "Label model", "라벨 연간 사용량": "Label annual energy",
    "이 모델의 현재 판정은 PASS입니다. 원본은 아래에서 확인할 수 있습니다.": "This model is currently PASS. The source evidence is available below.",
    "PDP에서 연간 kWh 표기가 수집됐습니다. EnergyGuide 인용값과 구분해 규제 공개 항목에 해당하는지 재검토하세요.": "An annual kWh value was collected on the PDP. Check whether it is the applicable disclosure field rather than an EnergyGuide citation.",
    "관련 공개 정보를 원본과 대조하세요.": "Compare the disclosure with its source evidence.",
    "ENERGY STAR 표시의 EPA 등록 근거를 확인하세요.": "Check the EPA registration supporting the ENERGY STAR claim.",
    "PDP·PLP·Specs의 ENERGY STAR 표시를 일치시키세요.": "Align ENERGY STAR claims across PDP, PLP and Specs.",
    "PDP 모델과 라벨의 모델 표기를 대조하고 라벨 연결을 확인하세요.": "Compare PDP and label models, then check the label link.",
    "EPA 등록 여부와 ENERGY STAR 표시 근거를 함께 확인하세요.": "Check EPA registration and the basis for the ENERGY STAR claim together.",
    "PDP의 연간 에너지 수치를 확인해 공개값을 보완하세요.": "Verify and complete the PDP annual energy disclosure.",
    "PDP·PLP·Specs의 로고와 인증 표기를 일치시키세요.": "Align logos and certification claims across PDP, PLP and Specs.",
    "PDP·라벨·EPA의 연간 에너지 수치를 대조해 잘못된 값을 수정하세요.": "Compare annual energy values on PDP, label and EPA, then correct the differing value.",
    "라벨 링크가 열리는지 확인하고 접근 가능한 파일로 교체하세요.": "Check the label link and replace it with an accessible file.",
    "해당 모델의 EnergyGuide 문서와 연결 위치를 확인하세요.": "Check the EnergyGuide document and its link for this model.",
    "PLP 옵션의 PDP 이동 불일치": "PLP option opens a different PDP",
    "옵션 재고와 PDP 이동 경로를 확인하고 해당 SKU의 페이지로 연결하세요.": "Check option availability and restore navigation to the exact-SKU PDP.",
    "PLP 재고 표시": "PLP stock flag",
    "PLP → PDP 모델 연결": "PLP → PDP model navigation",
    "PLP 옵션 SKU": "PLP option SKU",
    "이동한 PDP 모델": "Opened PDP model",
    "실제 이동 주소": "Actual destination",
    "ENERGY STAR 표시와 EPA 등록 불일치": "ENERGY STAR claim and EPA registration conflict",
    "ENERGY STAR 공개 불일치": "ENERGY STAR disclosure conflict",
    "모델명 불일치": "Model mismatch", "EPA 현행 등록 정보 없음": "No current EPA registration",
    "PDP 연간 에너지 누락": "PDP annual energy missing",
    "ENERGY STAR 표기 불일치": "ENERGY STAR claim conflict",
    "연간 에너지 불일치": "Annual energy mismatch",
    "라벨 파일 열람 불가": "Label file inaccessible", "라벨 문서 누락": "Label document missing",
    "PDP 에너지 판정 재검토": "Review PDP energy finding",
    "현재 EPA 일치 행 없음": "No matching current EPA row",
    "EPA 모델 후보 행 있음": "EPA model candidates found",
    "해당 없음": "Not applicable", "관찰되지 않음": "Not observed",
    "값 확인": "Value found", "있음": "Present", "없음": "Absent",
    "원본 전체 보기": "View all raw evidence", "불러오는 중…": "Loading…",
    "전체 원본 필드": "All raw fields", "모든 출처": "All sources",
    "원본 출처 필터": "Filter raw sources", "필드나 값 검색": "Search field or value",
    "원본 필드 검색": "Search raw fields", "일치하는 필드가 없습니다.": "No matching fields.",
    "원본 정보를 읽지 못했습니다": "Could not load raw evidence",
    "더 보기": "Show more", "보기": "View",
    "상세 닫기": "Close details", "닫기": "Close",
    "PDP 열기": "Open PDP", "EnergyGuide 열기": "Open EnergyGuide",
    "조치 없음": "No action", "판정 상세": "grade details", "상세 보기": "view details",
    "대시보드 데이터를 불러오지 못했습니다": "Could not load dashboard data",
    "PDP는": "PDP links are available for", "개 모델 모두 연결했습니다.": "models.",
    "EnergyGuide는 수집된 URL에 정확한 모델 토큰이 있는 경우에만 연결합니다.": "EnergyGuide links are shown only when the collected URL contains the exact model token."
  };
  Object.assign(koreanToEnglish, familyNames);

  const englishToKorean = {
    "US Samsung.com": "미국 Samsung.com",
    "Regulatory Disclosure Audit": "규제정보 공개 감사",
    "Regulatory Audit": "규제정보 감사",
    "SAMSUNG US / REGULATORY DISCLOSURE": "SAMSUNG US / 규제정보 공개",
    "Reviewed family snapshot": "검토된 제품군 스냅샷",
    "Samsung US disclosure evidence · Reviewed snapshot": "Samsung US 공개 근거 · 검토된 스냅샷",
    "Summary": "요약", "Action queue": "조치 목록", "Report data": "보고서 데이터",
    "Loading…": "불러오는 중…", "Label": "라벨",
    "01 / STATUS": "01 / 현황", "02 / SCOPE": "02 / 범위",
    "03 / RESOLVE": "03 / 조치", "04 / INVENTORY": "04 / 전체 모델",
    "05 / AUDIT TRAIL": "05 / 감사 근거", "RUN CHANGE": "실행별 변화",
    "FAMILIES": "제품군", "MODELS": "모델", "PASS": "PASS",
    "AM": "오전", "PM": "오후"
  };
  const koRules = Object.entries(englishToKorean).sort((a, b) => b[0].length - a[0].length);
  const enRules = Object.entries(koreanToEnglish).sort((a, b) => b[0].length - a[0].length);
  const koreanPolicy = "PASS/HIGH/MEDIUM/LOW는 모델마다 하나만 적용됩니다. 완전한 PDP Specs 목록에 ENERGY STAR 인증 필드 자체가 없으면 해당 없음으로 처리하며 LOW로 보지 않습니다. LOW는 존재하는 인증 필드가 명시적으로 No이거나 적용 대상 공개 항목이 확인된 상태로 누락된 경우입니다. 냉장고·TV·태블릿은 완전한 원본 목록으로 상세 판정을 다시 계산했습니다. 세탁기 LOW는 연간 에너지 이슈이고, 레인지·모니터·컴퓨터 LOW는 로고 누락입니다. 냉장고 NO_FINDING은 PASS에 포함합니다. TV 연간 에너지 비교는 범위 밖입니다. 태블릿 EPA 모델은 명시된 모델번호 또는 추가 모델정보 토큰과 완전 일치로 비교하며 접두어·유사 매칭은 사용하지 않습니다. EnergyGuide 인쇄 모델과 PDP 모델은 고정 접두어가 같으면 별표 수와 남은 글자 수가 달라도 일치로 인정합니다. EPA 현행 등록은 별도 규칙으로 비교합니다.";
  let language;
  try { language = localStorage.getItem(preferenceKey) === "en" ? "en" : "ko"; }
  catch { language = "ko"; }
  const textOrigins = new WeakMap();
  const attrOrigins = new WeakMap();

  function translate(source, target = language) {
    if (target === "ko" && source.startsWith("All 11 families were freshly collected")) {
      return source.replace(/All 11 families were freshly collected and assessed from unified GitHub Actions run (\d+)\..*/, "11개 제품군 모두 통합 GitHub Actions 실행 $1에서 새로 수집·판정했습니다. 각 정확한 SKU에는 PASS/HIGH/MEDIUM/LOW 중 하나의 등급이 있으며, 제품 전체의 법적 적합성은 판정하지 않았습니다.");
    }
    if (target === "ko" && source.startsWith("PASS/HIGH/MEDIUM/LOW are mutually exclusive")) return koreanPolicy;
    if (target === "en" && source.startsWith("PDP는 ")) {
      return source.replace(/PDP는 (\d[\d,]*)개 모델 모두 연결했습니다\. EnergyGuide는 수집된 URL에 정확한 모델 토큰이 있는 경우에만 연결합니다\./,
        "PDP links are available for all $1 models. EnergyGuide links appear only when the collected URL contains the exact model token.");
    }
    if (target === "en" && Object.hasOwn(koreanToEnglish, source)) return koreanToEnglish[source];
    const rules = target === "en" ? enRules : koRules;
    let result = source;
    if (target === "en") {
      result = result.replace(/변경 모델 (\d[\d,]*)개 보기/g, "View $1 changed models")
        .replace(/후보 (\d[\d,]*)건/g, "$1 candidates")
        .replace(/(\d[\d,]*)개 제품군/g, "$1 product families")
        .replace(/(\d[\d,]*)개 모델/g, "$1 models")
        .replace(/(\d[\d,]*)개 필드/g, "$1 fields")
        .replace(/(\d[\d,]*)건 표시/g, "$1 cases shown")
        .replace(/(\d[\d,]*)건/g, "$1 cases");
    }
    for (const [from, to] of rules) result = result.replaceAll(from, to);
    if (target === "en") {
      result = result.replace(/(\d[\d,]*)개/g, "$1");
    }
    return result;
  }

  function updateText(node) {
    if (!node.nodeValue.trim() || node.parentElement?.closest(".language-toggle, .field-list, script, style")) return;
    if (!textOrigins.has(node)) textOrigins.set(node, node.nodeValue);
    const translated = translate(textOrigins.get(node));
    if (node.nodeValue !== translated) node.nodeValue = translated;
  }

  function updateElement(element) {
    if (element.closest(".language-toggle, .field-list")) return;
    let originals = attrOrigins.get(element);
    if (!originals) { originals = new Map(); attrOrigins.set(element, originals); }
    for (const name of ["aria-label", "placeholder", "title"]) {
      if (!element.hasAttribute(name)) continue;
      if (!originals.has(name)) originals.set(name, element.getAttribute(name));
      const translated = translate(originals.get(name));
      if (element.getAttribute(name) !== translated) element.setAttribute(name, translated);
    }
  }

  function updateTree(root) {
    if (root.nodeType === Node.TEXT_NODE) { updateText(root); return; }
    if (root.nodeType !== Node.ELEMENT_NODE || root.matches("script, style") || root.closest(".field-list")) return;
    updateElement(root);
    for (const child of root.childNodes) updateTree(child);
  }

  function updateToggle() {
    const toggle = document.getElementById("language-toggle");
    document.documentElement.lang = language;
    document.documentElement.dataset.language = language;
    document.title = language === "en" ? "US Samsung.com Regulatory Disclosure Audit" : "미국 Samsung.com 규제정보 공개 감사";
    toggle.setAttribute("aria-checked", String(language === "en"));
    toggle.setAttribute("aria-label", language === "en" ? "Switch to Korean" : "영어로 전환");
    toggle.title = language === "en" ? "Switch to Korean" : "영어로 전환";
  }

  function setLanguage(next) {
    if (next === language) return;
    language = next;
    try { localStorage.setItem(preferenceKey, language); } catch { /* Storage may be disabled. */ }
    updateToggle();
    updateTree(document.body);
    document.dispatchEvent(new CustomEvent("rda-language-change", {detail: {language}}));
  }

  window.RDALang = {
    current: () => language,
    searchText: value => `${value} ${translate(value, "en")}`
  };
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === "characterData") updateText(record.target);
      else if (record.type === "attributes") updateElement(record.target);
      else for (const node of record.addedNodes) updateTree(node);
    }
  });
  updateToggle();
  updateTree(document.body);
  observer.observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true,
    attributeFilter: ["aria-label", "placeholder", "title"]});
  document.getElementById("language-toggle").addEventListener("click", () => setLanguage(language === "ko" ? "en" : "ko"));
})();
