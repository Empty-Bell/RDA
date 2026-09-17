"""Strict disabled-phase configuration, using JSON as a YAML 1.2 subset."""
import hashlib
import json
from pathlib import Path
import re
from .contracts import GROUPS, require, text


FIELDS = {
    'families': {'schema_version','routes','individual_applicability'},
    'sources': {'schema_version','contract_version','provenance','epa_catalog_url','source_routes_are_eligibility_rules'},
    'controls': {'schema_version','assessment_enabled','rule_version','rules','open_decisions'},
    'presentation': {'schema_version','enabled','summary_policy','aggregation_policy'},
    'runtime': {'schema_version','hosted_runner','architecture','audit_python','compatibility_python','llm_enabled','external_collection_enabled'},
}


def load_configuration(root):
    content = {name: json.loads((Path(root)/'configs'/(name+'.yaml')).read_bytes()) for name in FIELDS}
    for name, expected in FIELDS.items():
        require(isinstance(content[name],dict) and set(content[name]) == expected, 'Unknown/missing config fields: '+name)
        require(content[name]['schema_version']=='draft-1', 'Unsupported config schema')
    f = content['families']
    require(f['individual_applicability']=='NOT_EVALUATED' and isinstance(f['routes'],list) and f['routes'], 'Invalid family draft scope')
    legs=set(); groups=set()
    for route in f['routes']:
        require(isinstance(route,dict) and set(route)=={'source_leg','product_group','plp_url','epa_dataset_id'}, 'Invalid source route')
        leg=route['source_leg'];group=route['product_group']
        require(text(leg) and leg not in legs and group in GROUPS, 'Duplicate/invalid source leg or product group')
        require(text(route['plp_url']) and route['plp_url'].startswith('https://'), 'Invalid PLP URL')
        require(isinstance(route['epa_dataset_id'],str) and re.fullmatch('[a-z0-9]{4}-[a-z0-9]{4}',route['epa_dataset_id']), 'Invalid dataset identifier')
        legs.add(leg);groups.add(group)
    require(groups == GROUPS, 'Missing configured product groups')
    s=content['sources']
    require(text(s['contract_version']) and text(s['provenance']) and text(s['epa_catalog_url']) and s['epa_catalog_url'].startswith('https://'), 'Invalid source metadata')
    require(s['source_routes_are_eligibility_rules'] is False, 'Source routes cannot enable applicability rules')
    c=content['controls']
    require(c['assessment_enabled'] is False and c['rule_version'] is None and c['rules']==[], 'Unapproved assessment config')
    require(isinstance(c['open_decisions'],list) and len(c['open_decisions'])==len(set(c['open_decisions'])) and set(c['open_decisions'])=={'D%02d'%i for i in range(1,13)}, 'Draft must retain all open decisions')
    p=content['presentation']
    require(p['enabled'] is False and p['summary_policy'] is None and p['aggregation_policy'] is None, 'Unapproved presentation policy')
    r=content['runtime']
    require(r['hosted_runner']=='ubuntu-24.04' and r['architecture']=='x64', 'Unsupported hosted runner')
    require(r['audit_python']==(Path(root)/'.python-version').read_text(encoding='utf-8').strip() and r['compatibility_python']=='3.11', 'Runtime version mismatch')
    require(r['llm_enabled'] is False and r['external_collection_enabled'] is False, 'Draft is offline and has no LLM runtime')
    canonical=json.dumps(content,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return content, hashlib.sha256(canonical).hexdigest()
