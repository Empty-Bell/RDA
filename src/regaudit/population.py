"""Approved exact-SKU identity with lossless listing provenance."""
import copy
import json
from .contracts import ListingProvenance, ProductPopulationRecord, record, require, text


def canonicalize_products(records):
    require(isinstance(records,list), 'Products must be an array')
    runs=set(); products={}; provenance={}
    for raw in records:
        product=record(ProductPopulationRecord,raw)
        require(text(product.run_id) and text(product.exact_sku), 'Run/SKU missing')
        runs.add(product.run_id);require(len(runs)<=1, 'Cannot merge different runs')
        require(isinstance(product.listings,list) and product.listings, 'Listing provenance missing')
        key=product.exact_sku
        if key not in products:
            products[key]={'run_id':product.run_id,'exact_sku':key,'listings':[]};provenance[key]=set()
        for listing in product.listings:
            record(ListingProvenance,listing)
            identity=json.dumps(listing,sort_keys=True,separators=(',',':'),allow_nan=False)
            if identity not in provenance[key]:
                products[key]['listings'].append(copy.deepcopy(listing));provenance[key].add(identity)
    return [products[key] for key in sorted(products)]
