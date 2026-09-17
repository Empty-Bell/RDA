import copy
import json
from pathlib import Path
import tempfile
import unittest
from regaudit.cli import main
from regaudit.contracts import ContractError, validate_bundle
from regaudit.population import canonicalize_products
from regaudit.report import summarize_bundle

FIXTURES=Path(__file__).resolve().parents[2]/'fixtures/g1'


class PopulationReport(unittest.TestCase):
    def setUp(self):self.bundle=json.loads((FIXTURES/'two-findings.json').read_bytes())
    def test_one_row_two_findings_one_affected_sku(self):
        before=copy.deepcopy(self.bundle)
        report=summarize_bundle(self.bundle,synthetic_assessments=True)
        self.assertEqual(report['counts'],{'product_count':1,'finding_count':2,'affected_sku_count':1})
        self.assertEqual(len(report['rows']),1)
        self.assertEqual([a['severity'] for a in report['rows'][0]['assessments']],['HIGH','MEDIUM'])
        self.assertEqual(self.bundle,before)
    def test_group_subtotals_overlap_global_identity(self):
        evidence=copy.deepcopy(self.bundle['evidence'][0]);evidence.update(evidence_id='dryer-evidence',product_group='dryer')
        self.bundle['evidence'].append(evidence)
        self.bundle['assessments'][1].update(product_group='dryer',evidence_ids=['dryer-evidence'])
        r=summarize_bundle(self.bundle,synthetic_assessments=True)
        self.assertEqual(r['counts']['affected_sku_count'],1)
        self.assertEqual(sum(g['affected_sku_count'] for g in r['by_group'].values()),2)
        self.assertTrue(r['group_subtotals_overlap'])
    def test_unassessed_zero_findings_not_evaluated(self):
        b=json.loads((FIXTURES/'bundle.json').read_bytes());r=summarize_bundle(b)
        self.assertEqual(r['counts']['finding_count'],0)
        self.assertFalse(r['assessment_enabled'])
        self.assertEqual(r['rows'][0]['assessments'],[])
    def test_findings_not_enabled_by_default(self):
        with self.assertRaises(ContractError):summarize_bundle(self.bundle)
    def test_duplicate_products_merge_listing_provenance(self):
        product=self.bundle['products'][0]
        records=[dict(product,listings=[product['listings'][i]]) for i in (0,1)]
        before=copy.deepcopy(records);merged=canonicalize_products(records)
        self.assertEqual(len(merged),1);self.assertEqual(len(merged[0]['listings']),2)
        self.assertEqual(records,before)
    def test_identical_source_record_dedup(self):
        p=self.bundle['products'][0];self.assertEqual(canonicalize_products([p,p]),[p])
    def test_conflicting_source_values_retained(self):
        p=self.bundle['products'][0];q=copy.deepcopy(p)
        q['listings'][0]['stock_flag']={'state':'VALUE','value':'N','error':None}
        merged=canonicalize_products([p,q])
        self.assertEqual(len(merged),1);self.assertEqual(len(merged[0]['listings']),3)
    def test_different_variant_sku_not_merged(self):
        p=self.bundle['products'][0];q=copy.deepcopy(p);q['exact_sku']+='-COLOR'
        self.assertEqual(len(canonicalize_products([p,q])),2)
    def test_case_and_wildcard_not_normalized(self):
        p=self.bundle['products'][0];q=copy.deepcopy(p);q['exact_sku']=q['exact_sku'].lower()
        w=copy.deepcopy(p);w['exact_sku']='SYNTHETIC-*'
        self.assertEqual(len(canonicalize_products([p,q,w])),3)
    def test_cross_run_merge_rejected(self):
        p=self.bundle['products'][0];q=copy.deepcopy(p);q['run_id']='different'
        with self.assertRaises(ContractError):canonicalize_products([p,q])
    def test_invalid_variant_attributes(self):
        self.bundle['products'][0]['listings'][0]['variant_attributes']={'state':'VALUE','value':'bad','error':None}
        with self.assertRaises(ContractError):canonicalize_products(self.bundle['products'])
    def test_listing_error_not_success(self):
        self.bundle['products'][0]['listings'][0]['commerce_status']={'state':'ERROR','value':None,'error':'parser failed'}
        with self.assertRaises(ContractError):validate_bundle(self.bundle,synthetic_assessments=True)
    def test_cli_summary_preserves_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'summary.json'
            args=['summarize',str(FIXTURES/'bundle.json'),'--evidence-root',str(FIXTURES),'--output',str(output)]
            self.assertEqual(main(args),0);before=output.read_bytes()
            self.assertEqual(main(args),1);self.assertEqual(output.read_bytes(),before)
    def test_summary_refuses_corrupt_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'summary.json'
            self.assertEqual(main(['summarize',str(FIXTURES/'bundle.json'),'--evidence-root',temp,'--output',str(output)]),1)
            self.assertFalse(output.exists())
