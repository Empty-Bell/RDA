import copy
import unittest
from scripts.claim_recon import project_nested_claim_fields, claim_facts

class ClaimAttributionContract(unittest.TestCase):
    def setUp(self):
        self.snapshot={'target_sku':'SKU','product_jsonld':[{'sku':'SKU','additionalProperty':[]}],
                       'structured_records':[],'structured_probes':[],
                       'energy_candidates':[{'tag':'IMG','src':'//image-us.samsung.com/us/b2c_pf/badge/energy-star-logo-pdp-m@2x.png',
                                             'product_surface':'CURRENT_GALLERY','surface_count':1}]}
        self.listing={'modelCode':'SKU'}
        self.specs={'exact_sku':'SKU','energy_star_spec_claim_raw':[]}
    def facts(self):return claim_facts(self.snapshot,'SKU',self.listing,self.specs)

    def test_unique_product_surface_and_exact_identity_attribute_logo(self):
        result=self.facts()
        self.assertEqual(result['rendered_claim_attribution'],'OBSERVED_CURRENT_PRODUCT_SURFACE')
        self.assertEqual(result['rendered_attributed_badges_raw'][0]['exact_sku'],'SKU')
        self.assertEqual(result['certification_matching'],'NOT_EVALUATED')

    def test_related_product_or_duplicate_gallery_prevents_attribution(self):
        self.snapshot['product_jsonld'].append({'sku':'OTHER'})
        self.assertEqual(self.facts()['rendered_attributed_badges_raw'],[])
        self.snapshot['product_jsonld'].pop()
        self.snapshot['energy_candidates'][0]['surface_count']=2
        self.assertEqual(self.facts()['rendered_attributed_badges_raw'],[])

    def test_footer_and_marketing_image_are_not_product_badges(self):
        self.snapshot['energy_candidates'][0]['product_surface']=None
        self.assertEqual(self.facts()['rendered_attributed_badges_raw'],[])
        self.snapshot['energy_candidates'][0]['product_surface']='CURRENT_GALLERY'
        self.snapshot['energy_candidates'][0]['src']='/marketing/energy-star-promotion.jpg'
        self.assertEqual(self.facts()['rendered_attributed_badges_raw'],[])

    def test_no_logo_observation_stays_unknown(self):
        self.snapshot['energy_candidates']=[]
        self.assertEqual(self.facts()['rendered_claim_attribution'],'NOT_EVALUATED')

    def test_nested_raw_flag_keeps_sku_path_and_value(self):
        probe=project_nested_claim_fields({'data':{'modelCode':'SKU','features':{'energyStarFlg':'N'}}})
        self.snapshot['structured_probes']=[probe]
        result=self.facts()
        self.assertEqual(result['pdp_nested_energy_star_fields_raw'][0]['value'],'N')
        self.assertEqual(result['pdp_nested_energy_star_fields_raw'][0]['path'],'$.data.features.energyStarFlg')
        self.assertEqual(result['claim_consistency'],'NOT_EVALUATED')

    def test_nearest_child_identifier_overrides_parent(self):
        probe=project_nested_claim_fields({'modelCode':'SKU','related':{'sku':'OTHER','energyStarFlg':'Y'}})
        self.snapshot['structured_probes']=[probe]
        self.assertEqual(self.facts()['pdp_nested_energy_star_fields_raw'],[])

    def test_unbound_or_conflicting_identifiers_cannot_supply_current_flag(self):
        probe=project_nested_claim_fields({'energyStarFlg':'Y','data':{'sku':'OTHER','modelCode':'SKU','energyStarFlg':'Y'}})
        self.snapshot['structured_probes']=[probe]
        self.assertEqual(len(probe['fields']),2)
        self.assertEqual(self.facts()['pdp_nested_energy_star_fields_raw'],[])

    def test_private_branches_and_unrelated_values_are_not_retained(self):
        probe=project_nested_claim_fields({'modelCode':'SKU','chat':{'energyStarFlg':'secret'},
                                           'account':{'email':'private'},'features':{'description':'private text','energyStarFlg':True}})
        self.assertEqual(len(probe['fields']),1)
        self.assertEqual(probe['fields'][0]['value'],True)
        self.assertNotIn('private',str(probe))
        self.assertNotIn('chat',probe['root_sections'])

    def test_bounded_projection_reports_truncation(self):
        probe=project_nested_claim_fields([{'sku':'SKU','energyStarFlg':'Y'} for _ in range(110)])
        self.assertTrue(probe['truncated'])
        self.snapshot['structured_probes']=[probe]
        self.assertEqual(self.facts()['structured_probe_status'],'BOUNDED_PROJECTION_TRUNCATED')
