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

현재 파이프라인의 등록 판정 출처는 Model Index `8wj2-sec8`이다. 제품군 CSV를 대조하니 **14개 냉장고·냉동고는 미국 시장의 인증 행과 모델 패턴이 일치하지만 Index에는 그 행이 없다.** 따라서 이 14개를 단정적으로 “EPA 미등록”이라고 표시하는 것은 공식 출처끼리의 충돌을 숨기는 것이다. **7개 식기세척기는 Index와 제품군 목록 모두에 관련 모델군이 있지만 현재 EPA 패턴 규칙에서는 판매 SKU와 자리수까지 일치하지 않는다.** 이들 역시 “EPA 등록/후보 모델 수집값 없음”이라고 설명하면 부정확하다. TV 1개는 두 출처 모두에서 대응 행을 찾지 못했다.

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
| QN77S84FAEXZA | 대응 행 없음 | — | — | 없음 |

식기세척기 7건의 고정 접두어는 10–11글자이고 제품군 CSV의 연간 에너지 239 kWh/년은 7건 모두의 PDP·EnergyGuide 수집값 239와 일치한다. 따라서 **한두 글자만 같아 통과한 결과는 아니다.** 다만 현행 EPA 규칙의 별표 자리수 차이 때문에 이 7개 판매 SKU의 등록 범위는 추가 판정 기준이 필요하다. 냉장고·냉동고 14건의 공식 인증 행은 모두 `Markets`에 `United States`가 있으며 인증일은 2024–2026년이다.

## 판정상 남은 결정

2026-09-30 현재 Run #30의 HIGH 22건을 전부 실제 “미등록”으로 해석해서는 안 된다. 제품군 목록을 EPA 판정 근거로 포함할지, 별표 자리수가 다른 식기세척기 모델군의 고정 접두어를 판매 SKU 등록 범위로 인정할지 결정해야 한다. 그 기준을 확정하면 집계와 Action queue 문구를 함께 갱신한다. 원본 CSV의 모델군 존재만으로 SKU 인증 범위를 과도하게 확정하지 않는다.
