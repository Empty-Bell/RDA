"""G2a exact-SKU population adapter; source flags are never audit conclusions."""
import hashlib
import json
from urllib.parse import urljoin
from source_contract import pf_population
from regaudit.population import canonicalize_products


def observation(value=None):
    return {'state':'NOT_OBSERVED' if value is None else 'VALUE','value':value,'error':None}


def population_records(pages, run_id, plp_url):
    parsed=pf_population([json.loads(raw) for raw in pages])
    records=[]
    for raw in pages:
        page=json.loads(raw);digest=hashlib.sha256(raw).hexdigest()
        for group in page['searchResults']:
            for variant in group['groupedProductList']:
                records.append({'run_id':run_id,'exact_sku':variant['modelCode'],'listings':[{
                    'product_group':'refrigerator','source_family_id':group['group_id'],
                    'representative_sku':group['modelCode'],
                    'sku_role':'REPRESENTATIVE' if variant['modelCode']==group['modelCode'] else 'VARIANT',
                    'plp_url':plp_url,'pdp_url':urljoin('https://www.samsung.com',variant['pdpURL']),
                    'source_pf_search_hash':digest,'source_family_code':observation(),
                    'commerce_status':observation(variant.get('ecomFlag')),
                    'stock_flag':observation(variant.get('stockFlag')),
                    'ecom_flag':observation(variant.get('ecomFlag')),
                    'variant_attributes':observation(),
                }]})
    products=canonicalize_products(records)
    if len(products)!=parsed['unique_exact_skus']:raise ValueError('Population adapter lost SKU identities')
    return products,parsed
