"""Product-only public claim observations; no claim truth or compliance rules."""
import re

ENERGY_STAR = re.compile(r'energy[\s_-]*star', re.I)


def project_nested_claim_fields(payload):
    """Bounded schema/flag projection, excluding private and unrelated payload values."""
    fields = []
    visited = 0
    truncated = False
    private = re.compile(r'chat|analytics|license|account|auth|token|session|cookie|customer|email', re.I)
    identifiers = ('modelCode', 'modelcode', 'model_code', 'sku')
    def visit(node, path, identity, depth):
        nonlocal visited, truncated
        visited += 1
        if visited > 20000 or depth > 16 or len(fields) >= 100:
            truncated = True
            return
        if isinstance(node, list):
            for index, child in enumerate(node):
                if visited > 20000: break
                visit(child, f'{path}[{index}]', identity, depth + 1)
        elif isinstance(node, dict):
            local = [node[key] for key in identifiers if isinstance(node.get(key), str) and node[key]]
            current = local or identity
            for key, value in node.items():
                if private.search(key): continue
                child_path = f'{path}.{key}'
                if ENERGY_STAR.search(key) and (value is None or isinstance(value, (str, bool, int, float))):
                    fields.append({'path': child_path, 'identifiers_raw': current,
                                   'identity_basis': 'nearest explicit product identifier; unbound is not target',
                                   'name': key, 'value': value})
                if isinstance(value, (dict, list)):
                    child_identity = [] if re.search(r'related|recommend|accessor|variant|bundle|alternative', key, re.I) else current
                    visit(value, child_path, child_identity, depth + 1)
    visit(payload, '$', [], 0)
    return {'fields': fields, 'truncated': truncated,
            'root_sections': [key for key in payload if not private.search(key)] if isinstance(payload, dict) else ['ARRAY' if isinstance(payload, list) else 'SCALAR']}


def project_inline_product_claims(payload):
    """Observed NEXT_DATA product array only; never traverse unrelated page props."""
    try:
        products = payload['props']['pageProps']['productData']['products']
    except (KeyError, TypeError):
        raise ValueError('Observed inline product array path drifted')
    if not isinstance(products, list) or not products:
        raise ValueError('Inline product array unavailable/empty')
    fields = []
    records = []
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            raise ValueError('Inline product record drifted')
        identity = {key: product[key] for key in ('modelCode','modelcode','model_code','sku')
                    if isinstance(product.get(key), str) and product[key]}
        if not identity:
            raise ValueError('Inline product identity missing')
        record = {'identifiers': identity, 'energy_star_field_present': 'energyStarFlag' in product}
        if 'energyStarFlag' in product:
            value = product['energyStarFlag']
            if value is not None and not isinstance(value, (str, bool, int, float)):
                raise ValueError('Inline energyStarFlag scalar drifted')
            record['energyStarFlag'] = value
            fields.append({'path': f'$.props.pageProps.productData.products[{index}].energyStarFlag',
                           'identifiers_raw': list(identity.values()),
                           'identity_basis': 'explicit identifiers on observed inline product record',
                           'name': 'energyStarFlag', 'value': value})
        records.append(record)
    return {'fields': fields, 'truncated': False,
            'root_sections': ['props.pageProps.productData.products'],
            'product_claim_records': records}


def badge_attribution(snapshot, exact_jsonld, target):
    attributed = []
    snapshot_target = snapshot.get('target_sku')
    if snapshot_target is not None and snapshot_target != target:
        return attributed
    if snapshot_target is None and len(exact_jsonld) != 1:
        return attributed
    identified_products = [record for record in snapshot.get('product_jsonld', [])
                           if record.get('sku') or record.get('mpn')]
    if identified_products and (len(exact_jsonld) != 1 or len(identified_products) != 1):
        return attributed
    for candidate in snapshot.get('energy_candidates', []):
        if candidate.get('tag') != 'IMG':
            continue
        if candidate.get('product_surface') not in ('CURRENT_GALLERY', 'BUY_CONFIGURATOR_RELATION') or candidate.get('surface_count') != 1:
            continue
        ancestors = candidate.get('ancestors', [])
        in_energy_star_container = any(
            isinstance(item, dict) and re.search(r'Gallery_energyStarContainer|EnergyStar_energyStar', str(item.get('cls') or ''), re.I)
            for item in ancestors
        )
        official_legacy_asset = re.search(
            r'/us/b2c_pf/badge/energy-star-logo-pdp-', str(candidate.get('src') or ''), re.I
        )
        if (not in_energy_star_container
                and candidate.get('selector_contract') != 'PDP_ENERGY_STAR_GALLERY_CONTAINER_IMAGE_V2'
                and not official_legacy_asset):
            continue
        attributed.append({'exact_sku': target, 'src': candidate['src'],
                           'product_surface': candidate['product_surface'],
                           'identity_basis': 'verified exact-SKU PDP; unique observed ENERGY STAR gallery/configurator surface'})
    return attributed


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
    def exact_identifiers(record):
        identifiers = [record.get(key) for key in ('sku', 'mpn') if record.get(key)]
        return bool(identifiers) and all(isinstance(value, str) and value.upper() == target.upper() for value in identifiers)
    exact_jsonld = [r for r in snapshot['product_jsonld'] if exact_identifiers(r)]
    records = [r for r in snapshot['structured_records'] if r.get('modelCode') == target]
    direct = [f for r in records for f in r['energy_star_fields_raw']]
    properties = [p for r in exact_jsonld for p in r.get('additionalProperty', [])
                  if ENERGY_STAR.search(p.get('name') or '')]
    result = {'exact_sku': target,
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
    if 'structured_probes' in snapshot:
        for probe in snapshot['structured_probes']:
            if 'product_claim_records' in probe:
                matching = [record for record in probe['product_claim_records']
                            if record['identifiers'] and all(value.upper() == target.upper() for value in record['identifiers'].values())]
                if len(matching) != 1:
                    raise ValueError('Inline target SKU missing, conflicting or duplicated')
        nested = [field for probe in snapshot['structured_probes'] for field in probe['fields']
                  if field['identifiers_raw'] and all(value.upper() == target.upper() for value in field['identifiers_raw'])]
        result['pdp_nested_energy_star_fields_raw'] = nested
        result['structured_probe_status'] = 'BOUNDED_PROJECTION_TRUNCATED' if any(p['truncated'] for p in snapshot['structured_probes']) else 'BOUNDED_PROJECTION_COMPLETE'
        if nested: result['pdp_structured_claim_status'] = 'OBSERVED_RAW_FIELDS'
        result['rendered_attributed_badges_raw'] = badge_attribution(snapshot, exact_jsonld, target)
        result['rendered_claim_attribution'] = 'OBSERVED_CURRENT_PRODUCT_SURFACE' if result['rendered_attributed_badges_raw'] else 'NOT_EVALUATED'
    return result


DOM_SNAPSHOT = r"""() => {
  const visible = e => !!e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
  const energy = /energy[\s_-]*star/i;
  // Samsung PDPs use two published logo surfaces: a gallery badge and an
  // ENERGY STAR image in the product-detail configurator (common on Galaxy Books).
  const galleryLogoSelector = '#leftColumnInMainContent [class*="Gallery_energyStarContainer"] img';
  const configuratorLogoSelector = '.pdp-page .q6b6RelationContainer img[class*="EnergyStar_energyStar__"], ' +
    '.pdp-page .q6b6RelationContainer img[src*="/b2c_pf/badge/energy-star-logo-pdp-"]';
  const pdpLogoSelector = galleryLogoSelector + ', ' + configuratorLogoSelector;
  const galleryCount = document.querySelectorAll('[class*="Gallery_outerContainer__"]').length;
  const relationCount = document.querySelectorAll('.pdp-page .q6b6RelationContainer').length;
  const relationLogoCount = document.querySelectorAll(configuratorLogoSelector).length;
  const candidates = Array.from(document.querySelectorAll(pdpLogoSelector))
    .filter(visible).map(e => {
      const inGallery = !!(e.closest('[class*="Gallery_energyStarContainer__"]') &&
        e.closest('[class*="Gallery_outerContainer__"]'));
      const inConfigurator = !inGallery && !!e.closest('.pdp-page .q6b6RelationContainer');
      return {tag:e.tagName, text:(e.children.length ? '' : e.textContent || '').trim(),
        alt:e.getAttribute('alt'), label:e.getAttribute('aria-label'),
        ancestors:Array.from((function*(){let p=e;for(let i=0;p && i<5;i++,p=p.parentElement) yield {tag:p.tagName,cls:p.className};})()),
        selector_contract:inGallery ? 'PDP_ENERGY_STAR_GALLERY_CONTAINER_IMAGE_V2' : 'PDP_ENERGY_STAR_PRODUCT_DETAILS_IMAGE_V1',
        selector:pdpLogoSelector,
        product_surface:inGallery ? 'CURRENT_GALLERY' : inConfigurator ? 'BUY_CONFIGURATOR_RELATION' : null,
        surface_count:inGallery ? galleryCount : inConfigurator ? relationLogoCount : 0,
        src:e.tagName === 'IMG' ? e.getAttribute('src') : null};
    }).map(x => ({...x,text:x.text.slice(0,400)})).slice(0,40);
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
  const specRoot = document.querySelector('#specs');
  const specRows = specRoot ? Array.from(specRoot.querySelectorAll('[class*="Specs_subSpecItem__"]'))
    .filter(visible).map(e => ({tag:e.tagName, text:(e.innerText || '').trim().replace(/\s+/g,' ').slice(0,800),
      cells:Array.from(e.children).filter(visible).map(x => (x.innerText || '').trim().replace(/\s+/g,' ').slice(0,300)).filter(Boolean)}))
    .filter(x => energy.test(x.text)).slice(0,40) : [];
  const identifiedProductCount = products.filter(p => p.sku || p.mpn).length;
  // On configurator PDPs, a unique product identity plus a mounted details surface
  // is the supported primary surface even when the gallery component is absent.
  const configuratorSurfaceComplete = galleryCount === 0 && relationCount > 0 &&
    document.querySelector('.pdp-page') && identifiedProductCount === 1;
  const primaryLogoInspection = galleryCount === 1 || configuratorSurfaceComplete
    ? 'SUPPORTED_PRIMARY_SURFACE_COMPLETE' : 'UNSUPPORTED_OR_AMBIGUOUS_PRIMARY_SURFACE';
  return {headings:Array.from(document.querySelectorAll('h1')).filter(visible).map(e => e.textContent.trim().slice(0,300)),
    product_jsonld:products, jsonld_parse_errors:errors, energy_candidates:candidates,
    pdp_logo_selector_contract:'PDP_ENERGY_STAR_GALLERY_CONTAINER_IMAGE_V2', pdp_logo_selector:pdpLogoSelector,
    primary_logo_inspection:primaryLogoInspection, visible_spec_energy_star_rows:specRows,
    spec_surface_inspection:specRoot && specRows.length ? 'SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE' : 'SPEC_TABLE_NOT_MOUNTED_OR_SCHEMA_UNSUPPORTED',
    observation_scope:'current mounted DOM; visible page candidates are not attributed to target SKU'};
}"""

PLP_SNAPSHOT = r"""() => Array.from(document.querySelectorAll('.pd21-product-card__name')).map(e => {
  // `.pd21-product-card` is the page-wide product finder, rather than one SKU
  // card. The accepted boundary is its list's immediate child containing this
  // model-code anchor; this stops one card borrowing another card's badge.
  const list = e.closest('.pd21-product-card__list');
  let item = e;
  while (item && list && item.parentElement !== list) item = item.parentElement;
  if (!list || !item || item.parentElement !== list) item = null;
  const sku = e.getAttribute('data-modelcode');
  const itemModelCodeOccurrences = item ? Array.from(item.querySelectorAll('[data-modelcode]'))
    .map(x => x.getAttribute('data-modelcode')).filter(Boolean) : [];
  const itemModelCodes = [...new Set(itemModelCodeOccurrences)];
  const exactScope = !!item && typeof sku === 'string' && sku.length > 0 &&
    itemModelCodes.length === 1 && itemModelCodes[0] === sku;
  const rendered = x => {
    if (!x.getClientRects().length) return false;
    for (let node = x; node && node.nodeType === 1; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse' || style.opacity === '0') return false;
    }
    return true;
  };
  const plpLogoSelector = ':scope > [class*="energy-star-label-wrap"] img[src*="energy-star-logo"]';
  return {sku, title:e.textContent.trim().slice(0,300),
    card_scope_contract:'PLP_EXACT_LIST_ITEM_V2',
    exact_sku_anchor_count:itemModelCodes.length, exact_sku_anchor_values:itemModelCodes,
    exact_sku_anchor_occurrences:itemModelCodeOccurrences.length,
    logo_inspection:exactScope ? 'SUPPORTED_EXACT_CARD_COMPLETE' : 'UNSUPPORTED_EXACT_CARD_SCOPE',
    plp_logo_selector_contract:'PLP_EXACT_LIST_ITEM_IMAGE_V2', plp_logo_selector:plpLogoSelector,
    energy_candidates:exactScope ? Array.from(item.querySelectorAll(plpLogoSelector))
      .filter(rendered).map(x => ({tag:x.tagName, text:(x.children.length ? '' : x.textContent || '').trim().slice(0,400),
        alt:x.getAttribute('alt'),label:x.getAttribute('aria-label'),src:x.getAttribute('src'),
        selector_contract:'PLP_EXACT_LIST_ITEM_IMAGE_V2',selector:plpLogoSelector})).slice(0,10) : []};
})"""
