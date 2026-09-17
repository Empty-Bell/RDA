"""Offline draft boundaries; synthetic findings test transport, not rules."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from regaudit.cli import configuration, main
from regaudit.contracts import ContractError, Observation, dumps, validate_bundle, verify_evidence_files

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'fixtures/g1'


class Contracts(unittest.TestCase):
    def setUp(self): self.bundle = json.loads((FIXTURES / 'bundle.json').read_bytes())

    def invalid(self, edit):
        edit(self.bundle)
        with self.assertRaises((ContractError, ValueError, TypeError)): validate_bundle(self.bundle)

    def test_round_trip(self):
        self.assertEqual(validate_bundle(json.loads(dumps(self.bundle))), self.bundle)
        verify_evidence_files(self.bundle, FIXTURES)

    def test_zero_and_false_remain_observed(self):
        for value in (0, False): self.assertIs(Observation('VALUE', value, None).value, value)

    def test_absent_states_are_distinct(self):
        states = [Observation(s, None, None).state for s in ('MISSING','NOT_OBSERVED','NOT_APPLICABLE')]
        self.assertEqual(len(set(states)), 3)

    def test_invalid_observation_combinations(self):
        for state, value, error in [('VALUE',None,None),('ERROR',None,None),('MISSING',0,None),('NOT_OBSERVED',False,None),('NOT_APPLICABLE',None,'error'),('VALUE',float('nan'),None)]:
            with self.subTest(state=state), self.assertRaises(ValueError): Observation(state,value,error)

    def test_unknown_fields(self): self.invalid(lambda b: b['manifest'].update(unapproved=True))
    def test_missing_fields(self): self.invalid(lambda b: b['manifest'].pop('git_sha'))
    def test_invalid_git_hash(self): self.invalid(lambda b: b['manifest'].update(git_sha='bad'))
    def test_timezone_required(self): self.invalid(lambda b: b['manifest'].update(started_at='2026-09-17'))
    def test_completed_before_started(self): self.invalid(lambda b: b['manifest'].update(completed_at='2020-01-01T00:00:00Z'))
    def test_engine_disabled(self): self.invalid(lambda b: b['manifest'].update(assessment_enabled=True))
    def test_duplicate_product(self): self.invalid(lambda b: b['products'].append(copy.deepcopy(b['products'][0])))
    def test_preserve_multiple_listing_groups(self):
        validate_bundle(self.bundle)
        self.assertEqual([p['product_group'] for p in self.bundle['products'][0]['listings']], ['washer','dryer'])
    def test_cross_run_evidence(self): self.invalid(lambda b: b['evidence'][0].update(run_id='different'))
    def test_cross_sku_evidence(self): self.invalid(lambda b: b['evidence'][0].update(sku='different'))
    def test_cross_group_reference(self): self.invalid(lambda b: b['facts'][0].update(product_group='dryer'))
    def test_missing_reference(self): self.invalid(lambda b: b['facts'][0].update(evidence_ids=['absent']))
    def test_duplicate_reference(self): self.invalid(lambda b: b['facts'][0].update(evidence_ids=['e1','e1']))
    def test_duplicate_evidence(self): self.invalid(lambda b: b['evidence'].append(copy.deepcopy(b['evidence'][0])))
    def test_source_error_not_success(self):
        self.invalid(lambda b: b['facts'][0]['observations'].update(plp_energy_star_claim={'state':'ERROR','value':None,'error':'HTTP 403'}))
    def test_source_error_partial_has_no_findings(self):
        self.bundle['manifest']['overall_execution_status'] = 'PARTIAL'
        self.bundle['facts'][0]['observations']['plp_energy_star_claim'] = {'state':'ERROR','value':None,'error':'HTTP 403'}
        validate_bundle(self.bundle)
        self.assertEqual(self.bundle['assessments'], [])
    def test_synthetic_findings_retained_without_running_rules(self):
        bundle = json.loads((FIXTURES / 'two-findings.json').read_bytes())
        with self.assertRaises(ContractError): validate_bundle(bundle)
        validate_bundle(bundle, synthetic_assessments=True)
        self.assertEqual(len(bundle['products']), 1)
        self.assertEqual(len(bundle['assessments']), 2)
        self.assertEqual({a['regulatory_domain'] for a in bundle['assessments']}, {'FTC','EPA'})
    def test_unknown_synthetic_issue_rejected(self):
        b = json.loads((FIXTURES / 'two-findings.json').read_bytes())
        b['assessments'][0]['issue_code']='INVENTED'
        with self.assertRaises(ContractError): validate_bundle(b, synthetic_assessments=True)
    def test_traversal_rejected(self):
        for path in ('../secret','/secret','C:/secret','raw\\secret'):
            with self.subTest(path=path):
                b=copy.deepcopy(self.bundle);b['evidence'][0]['relative_path']=path
                with self.assertRaises(ContractError): validate_bundle(b)
    def test_corrupt_and_missing_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'raw').mkdir();(root/'raw/source.json').write_bytes(b'corrupt')
            with self.assertRaises(ContractError): verify_evidence_files(self.bundle,root)
            (root/'raw/source.json').unlink()
            with self.assertRaises(FileNotFoundError): verify_evidence_files(self.bundle,root)
    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'evidence';(root/'raw').mkdir(parents=True);outside=Path(temp)/'outside.json';outside.write_bytes(b'outside')
            try: (root/'raw/source.json').symlink_to(outside)
            except OSError: self.skipTest('Local Windows lacks symlink permission; hosted Linux must execute')
            with self.assertRaises(ContractError): verify_evidence_files(self.bundle,root)
    def test_cli_validate_requires_raw(self):
        self.assertEqual(main(['validate',str(FIXTURES/'bundle.json'),'--evidence-root',str(FIXTURES)]),0)
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(main(['validate',str(FIXTURES/'bundle.json'),'--evidence-root',temp]),1)
    def test_cli_unique_run_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            paths=[Path(temp)/name for name in ('first.json','second.json')]
            for path in paths: self.assertEqual(main(['init-run','--git-sha','0'*40,'--project',str(ROOT),'--output',str(path)]),0)
            bundles=[json.loads(p.read_bytes()) for p in paths]
            self.assertNotEqual(bundles[0]['manifest']['run_id'],bundles[1]['manifest']['run_id'])
            self.assertTrue(all(b['manifest']['overall_execution_status']=='OUTPUT_MISSING' for b in bundles))
            before=paths[0].read_bytes()
            self.assertEqual(main(['init-run','--git-sha','0'*40,'--project',str(ROOT),'--output',str(paths[0])]),1)
            self.assertEqual(paths[0].read_bytes(),before)
    def test_unapproved_config_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'configs').mkdir()
            for path in (ROOT/'configs').glob('*.yaml'): (root/'configs'/path.name).write_bytes(path.read_bytes())
            controls=json.loads((root/'configs/controls.yaml').read_bytes());controls['assessment_enabled']=True
            (root/'configs/controls.yaml').write_text(json.dumps(controls),encoding='utf-8')
            with self.assertRaises(ContractError): configuration(root)


if __name__ == '__main__': unittest.main()
