"""Product-only public claim observations; no claim truth or compliance rules."""
import re

ENERGY_STAR = re.compile(r'energy[\s_-]*star', re.I)


def project_claim_records(payload):
    """Only direct fields on explicitly SKU-identified public product records."""
    sections = payload if isinstance(payload, dict) else {'ROOT': payload}
    result = []
    for section, collection in sections.items():
        records = collection if isinstance(collection, list) else [collection]
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get('modelCode'), str):
                continue
            fields = [{'name': key, 'value': value} for key, value in record.items()
                      if ENERGY_STAR.search(key) and (value is None or isinstance(value, (str, bool, int, float)))]
            result.append({'section': section, 'modelCode': record['modelCode'],
                           'energy_star_fields_raw': fields})
    return result


def claim_facts(snapshot, target, listing, specs):
    if snapshot.get('target_sku') != target or listing.get('modelCode') != target or specs.get('exact_sku') != target:
        raise ValueError('Claim observation lacks exact SKU provenance')
    if not isinstance(snapshot.get('product_jsonld'), list) or not isinstance(snapshot.get('structured_records'), list):
        raise ValueError('Claim observation collections missing')
    exact_jsonld = [r for r in snapshot['product_jsonld']
                    if target.upper() in {(r.get('sku') or '').upper(), (r.get('mpn') or '').upper()}]
    records = [r for r in snapshot['structured_records'] if r.get('modelCode') == target]
    direct = [f for r in records for f in r['energy_star_fields_raw']]
    properties = [p for r in exact_jsonld for p in r.get('additionalProperty', [])
                  if ENERGY_STAR.search(p.get('name') or '')]
    return {'exact_sku': target,
            'listing_title_raw': listing.get('modelName'),
            'pdp_headings_raw': snapshot.get('headings', []),
            'pdp_exact_jsonld_raw': exact_jsonld,
            'listing_commerce_raw': {key: listing.get(key) for key in ('ecomFlag', 'stockFlag')},
            'plp_energy_star_flag_raw': listing.get('energyStarFlg'),
            'pdp_structured_energy_star_fields_raw': direct,
            'pdp_jsonld_energy_star_properties_raw': properties,
            'pdp_structured_claim_status': 'OBSERVED_RAW_FIELDS' if direct or properties else 'NOT_EVALUATED',
            'pdp_spec_energy_star_claim_raw': specs['energy_star_spec_claim_raw'],
            'rendered_page_candidates_raw': snapshot.get('energy_candidates', []),
            'rendered_claim_attribution': 'NOT_EVALUATED',
            'certification_matching': 'NOT_EVALUATED', 'claim_consistency': 'NOT_EVALUATED'}


DOM_SNAPSHOT = r"""() => {
  const visible = e => !!e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
  const energy = /energy[\s_-]*star/i;
  const candidates = Array.from(document.querySelectorAll('img,[aria-label],p,span,li'))
    .filter(visible).map(e => ({tag:e.tagName, text:(e.children.length ? '' : e.textContent || '').trim(),
      alt:e.getAttribute('alt'), label:e.getAttribute('aria-label'),
      src:e.tagName === 'IMG' ? e.getAttribute('src') : null}))
    .filter(x => energy.test([x.text,x.alt,x.label,x.src].join(' ')))
    .map(x => ({...x,text:x.text.slice(0,400)})).slice(0,40);
  const products = []; let errors = 0;
  const visit = (x, depth=0) => {
    if (!x || depth > 8) return;
    if (Array.isArray(x)) { x.forEach(y => visit(y,depth+1)); return; }
    if (typeof x !== 'object') return;
    const types = Array.isArray(x['@type']) ? x['@type'] : [x['@type']];
    if (types.includes('Product')) {
      const offers = Array.isArray(x.offers) ? x.offers : x.offers ? [x.offers] : [];
      const props = Array.isArray(x.additionalProperty) ? x.additionalProperty : x.additionalProperty ? [x.additionalProperty] : [];
      const scalar = y => ['string','number','boolean'].includes(typeof y) ? y : null;
      products.push({sku:scalar(x.sku),mpn:scalar(x.mpn),name:scalar(x.name),
        availability:offers.map(o => scalar(o.availability)),
        additionalProperty:props.filter(p => energy.test(p.name || '')).map(p => ({name:scalar(p.name),value:scalar(p.value)}))});
    }
    Object.values(x).forEach(y => visit(y,depth+1));
  };
  document.querySelectorAll('script[type="application/ld+json"]').forEach(e => {
    try { visit(JSON.parse(e.textContent)); } catch { errors++; }
  });
  return {headings:Array.from(document.querySelectorAll('h1')).filter(visible).map(e => e.textContent.trim().slice(0,300)),
    product_jsonld:products, jsonld_parse_errors:errors, energy_candidates:candidates,
    observation_scope:'current mounted DOM; visible page candidates are not attributed to target SKU'};
}"""

PLP_SNAPSHOT = r"""() => Array.from(document.querySelectorAll('.pd21-product-card__name')).map(e => {
  const card = e.closest('.pd21-product-card');
  const visible = x => !!x.getClientRects().length && getComputedStyle(x).visibility !== 'hidden';
  const energy = /energy[\s_-]*star/i;
  return {sku:e.getAttribute('data-modelcode'), title:e.textContent.trim().slice(0,300),
    card_scope_found:!!card, energy_candidates:card ? Array.from(card.querySelectorAll('img,[aria-label],span,p'))
      .filter(visible).map(x => ({tag:x.tagName, text:(x.children.length ? '' : x.textContent || '').trim().slice(0,400),
        alt:x.getAttribute('alt'),label:x.getAttribute('aria-label'),src:x.tagName === 'IMG' ? x.getAttribute('src') : null}))
      .filter(x => energy.test([x.text,x.alt,x.label,x.src].join(' '))).slice(0,10) : []};
})"""
