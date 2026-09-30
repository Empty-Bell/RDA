# HIGH EPA 등록 판정 독립 재확인 (2026-09-30)

대상: 통합 대시보드 Run #30의 HIGH 23건 중 EPA/ENERGY STAR 관련 22건. 나머지 1건은 TV EnergyGuide 문서 누락이다. 이 문서는 기존 판정과 별도로 ENERGY STAR 공식 웹사이트의 제품군별 CSV 다운로드 파일을 확인한 결과다. **공식 제품군 행이 있다는 사실과 특정 Samsung 판매 SKU가 그 행에 포함된다는 사실은 구분한다.**

## 공식 원본 및 재현 경로

| 용도 | 웹 페이지 | 웹 페이지의 CSV 다운로드 | 직접 조회 API |
| --- | --- | --- | --- |
| 현행 Model Index | [8wj2-sec8](https://data.energystar.gov/d/8wj2-sec8) | [CSV](https://data.energystar.gov/api/views/8wj2-sec8/rows.csv?accessType=DOWNLOAD) | [Samsung 행 JSON](https://data.energystar.gov/resource/8wj2-sec8.json?%24where=upper%28brand_name%29%20%3D%20%27SAMSUNG%27&%24limit=5000) |
| 냉장고 | [p5st-her9](https://data.energystar.gov/d/p5st-her9) | [CSV](https://data.energystar.gov/api/views/p5st-her9/rows.csv?accessType=DOWNLOAD) | [JSON](https://data.energystar.gov/resource/p5st-her9.json) |
| 냉동고 | [8t9c-g3tn](https://data.energystar.gov/d/8t9c-g3tn) | [CSV](https://data.energystar.gov/api/views/8t9c-g3tn/rows.csv?accessType=DOWNLOAD) | [JSON](https://data.energystar.gov/resource/8t9c-g3tn.json) |
| 식기세척기 | [q8py-6w3f](https://data.energystar.gov/d/q8py-6w3f) | [CSV](https://data.energystar.gov/api/views/q8py-6w3f/rows.csv?accessType=DOWNLOAD) | [JSON](https://data.energystar.gov/resource/q8py-6w3f.json) |
| TV | [pd96-rr3d](https://data.energystar.gov/d/pd96-rr3d) | [CSV](https://data.energystar.gov/api/views/pd96-rr3d/rows.csv?accessType=DOWNLOAD) | [JSON](https://data.energystar.gov/resource/pd96-rr3d.json) |

제품군 CSV는 `https://data.energystar.gov/api/views/<ID>/rows.csv?accessType=DOWNLOAD`에서 받았다. URL에 `api/views`가 들어가지만 공식 데이터 웹 페이지의 **Download → CSV** 원본 경로이며, 판정 파이프라인의 `/resource/<ID>.json` 질의와는 별도로 내려받아 비교했다. 파일은 로컬 `runtime/epa-independent-recheck/`에 보관한다. SHA-256: 냉장고 `1D28F7F66207D52AEBC9B288C34602B77011CE4972F799EDBDABDE5D26414AF3`, 냉동고 `C4E121173E2509469CE783AE086203A4F1D552E4792974EC3E0B3007F0E0E551`, 식기세척기 `E48AF66A19B7150EF395DAFE5E51CBBFEBC5CFDF78826C2BA73006A87E0B336E`, TV `208BC47C07D773F0AFCAF7A45581C8D9C8F5DEFC78DAA1F8906CDB14AB97A452`. Model Index의 Samsung 한정 API JSON SHA-256은 `74F2CA34F316A553B2040DE5CED5DBC1BC5EC9F1A66703CBFACC9D06AD169D6A`이다.

기존 Run #30의 등록 판정은 Model Index `8wj2-sec8`에 의존했다. 공식 제품군 CSV에는 **14개 냉장고·냉동고의 미국 시장 인증 행**, 그리고 **7개 식기세척기의 관련 모델군 행**이 있다. TV 1개도 대표 `Model Number` 검색만으로는 빠지지만, 공식 TV 인증 행의 `Additional Model Information`에 정확한 모델이 명시돼 있다. 따라서 22건 모두를 “EPA 미등록”으로 표시한 이전 결과는 오검출이다.

## 22개 HIGH의 행별 대조

`정규화 SKU 일치`는 Samsung 판매 SKU 끝의 `AA`를 제거한 뒤 EPA 패턴의 `*`를 한 글자로 해석한 결과다. 이것은 원본에 적힌 판매 SKU의 독립적인 명시 여부와 다르다. `Index 행`은 Samsung 범위의 현행 Model Index에 동일 EPA 모델 패턴 행이 있는지 뜻한다.

| Samsung SKU | 공식 제품군 CSV의 EPA 모델 | ENERGY STAR Unique ID | 정규화 SKU 일치 | Index 행 |
| --- | --- | ---: | :---: | :---: |
| RF25C5A01SRAA | RF25C5A01** | 4529239 | 예 | 없음 |
| RF27CG5B30SRAA | RF27CG5B30** | 4520751 | 예 | 없음 |
| RF32CG5B30SRAA | RF32CG5B30** | 4520750 | 예 | 없음 |
| RF32CG5D00SRAA | RF32CG5D00** | 4529142 | 예 | 없음 |
| RF70H25GERAA | RF70H25GE* | 4529040 | 예 | 없음 |
| RF70H25HERAA | RF70H25HE* | 4529041 | 예 | 없음 |
| RF70H25KERAA | RF70H25KE* | 4529042 | 예 | 없음 |
| RF70H30GEEAA | RF70H30GE* | 4528617 | 예 | 없음 |
| RF70H30GERAA | RF70H30GE* | 4528617 | 예 | 없음 |
| RF70H30HERAA | RF70H30HE* | 4528618 | 예 | 없음 |
| RF70H30KEEAA | RF70H30KE* | 4528619 | 예 | 없음 |
| RF70H30KERAA | RF70H30KE* | 4528619 | 예 | 없음 |
| RF80H30CERAA | RF80H30CE* | 4586373 | 예 | 없음 |
| RZ40H11PETAA | RZ40H11PE* | 4586375 | 예 | 없음 |
| DW80BB707012AA | DW80BB7070**** | 2409709 | 아니요 | 있음 |
| DW80CB545012AA | DW80CB545***** | 2453102 | 아니요 | 있음 |
| DW80CG5420SRAA | DW80CG542***** | 2453104 | 아니요 | 있음 |
| DW80CG5450MTAA | DW80CG545***** | 2453103 | 아니요 | 있음 |
| DW80CG5450SRAA | DW80CG545***** | 2453103 | 아니요 | 있음 |
| DW80CG5451MTAA | DW80CG545***** | 2453103 | 아니요 | 있음 |
| DW80CG5451SRAA | DW80CG545***** | 2453103 | 아니요 | 있음 |
| QN77S84FAEXZA | 대표 QN77S85FAE 행의 추가 모델 QN77S84FAE | 3994365 | 명시적 추가 모델 | 직접 모델행 없음 |

식기세척기 7건의 고정 접두어는 최소 9글자이고 제품군 CSV의 연간 에너지 239 kWh/년은 7건 모두의 PDP·EnergyGuide 수집값 239와 일치한다. 따라서 **한두 글자만 같아 통과한 결과는 아니다.** 냉장고·냉동고 14건의 공식 인증 행은 모두 `Markets`에 `United States`가 있으며 인증일은 2024–2026년이다. TV 행은 [ENERGY STAR 공식 제품 상세 PDF](https://www.energystar.gov/productfinder/product/certified-televisions/details/3994365/export/pdf/download)에도 `QN77S84FAE`가 추가 모델로 명시돼 있다.

## 승인된 보완 규칙

사용자는 이 22개 모델의 등록 모델군 포함을 확인하고 오검출 방지를 승인했다. 냉장고·냉동고는 현행 공식 제품군 행과 자리별 모델 패턴의 일치, 식기세척기는 긴 고정 접두어·미국 시장·독립적인 239 kWh 일치, TV는 인증 행에 명시된 추가 모델명과 Samsung 판매 접미어 `XZA`의 정확한 결합을 요구한다. 짧은 접두어, 중간 고정 문자 충돌, 다른 연간 사용량, 비미국 행, 인증일 누락 또는 여러 상충하는 후보는 자동 PASS하지 않는다. 보완 규칙은 [통합 Run #31](https://github.com/Empty-Bell/RDA/actions/runs/36693683213)의 공개 스냅샷에 반영됐으며, 22개 모두 `PASS` 및 `EPA PRESENT`로 확인됐다. 이 실행의 전체 HIGH 1건은 EPA 등록 문제가 아닌 TV EnergyGuide 문서 누락 건이다.
