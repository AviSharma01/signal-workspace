"""Regression coverage for executable V1 Finding bypasses in the #26 audit."""
import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

from agent import finding, findings_store, loop, run_one
from agent.eval import run_eval
from agent.llm.base import LLMResponse
from jobs import scan_signals
from tests import test_investigations


ADVICE = {
    'ticker': 'AAPL', 'trigger': {}, 'hypothesis': 'Buy AAPL now for profit.',
    'primary_driver': 'news', 'evidence': [], 'confidence': 'high',
    'needs_human_review': False, 'advice': None,
}


class LegacyFindingClosureTest(unittest.TestCase):
    def test_legacy_constructor_and_validator_reject_advice_and_invalid_citations(self):
        for evidence in [[], [{'id': 'not-eligible'}]]:
            candidate = {**ADVICE, 'evidence': evidence}
            with self.subTest(evidence=evidence):
                with self.assertRaisesRegex(RuntimeError, 'Legacy V1'):
                    finding.validate_finding(json.dumps(candidate))
                with self.assertRaisesRegex(RuntimeError, 'Legacy V1'):
                    finding.Finding(**candidate)

    def test_loop_cannot_call_backend_or_force_a_finding_without_v2_inputs(self):
        backend = Mock()
        backend.complete.return_value = LLMResponse(text=json.dumps(ADVICE))
        for steps in [0, 8]:
            with self.subTest(steps=steps):
                with self.assertRaisesRegex(RuntimeError, 'Legacy V1'):
                    loop.run_agent('AAPL', {}, backend=backend, max_steps=steps)
        backend.complete.assert_not_called()

    def test_legacy_store_cannot_persist_or_expose_a_finding(self):
        unvalidated = SimpleNamespace(**ADVICE)
        with patch.object(findings_store, 'get_connection', create=True) as connection:
            with self.assertRaisesRegex(RuntimeError, 'Legacy V1'):
                findings_store.insert_finding(unvalidated)
            with self.assertRaisesRegex(RuntimeError, 'Legacy V1'):
                findings_store.list_findings()
            connection.assert_not_called()

    def test_run_one_fails_before_computation_or_display(self):
        output = io.StringIO()
        with patch.object(run_one, '_compute_trigger', create=True) as trigger, \
                patch.object(run_one, 'run_agent', create=True) as agent, \
                patch('sys.argv', ['agent.run_one', 'AAPL']), redirect_stdout(output):
            trigger.return_value = {}
            agent.return_value.to_dict.return_value = ADVICE
            with self.assertRaisesRegex(SystemExit, 'Legacy V1'):
                run_one.main()
            trigger.assert_not_called()
            agent.assert_not_called()
        self.assertNotIn(ADVICE['hypothesis'], output.getvalue())
        self.assertNotIn('Finding:', output.getvalue())

    def test_scan_fails_before_scanning_creating_or_persisting(self):
        with patch.object(scan_signals, 'scan_watchlist', create=True) as scan, \
                patch.object(scan_signals, 'run_agent', create=True) as agent, \
                patch.object(scan_signals, 'insert_finding', create=True) as persist:
            scan.return_value = [('AAPL', {})]
            agent.return_value = SimpleNamespace(**ADVICE)
            with self.assertRaisesRegex(RuntimeError, 'Legacy V1'):
                scan_signals.scan_signals()
            scan.assert_not_called()
            agent.assert_not_called()
            persist.assert_not_called()

    def test_eval_entrypoint_cannot_run_or_display_legacy_findings(self):
        with patch.object(run_eval, '_compute_trigger', create=True) as trigger, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, 'Legacy V1'):
                run_eval.main()
            trigger.assert_not_called()

    def test_v2_boundary_withholds_advice_and_empty_or_invalid_citations(self):
        fixture = test_investigations.InvestigationApplicationTest()
        fixture.setUp()
        try:
            run = fixture.completed()
            original = copy.deepcopy(run['finding'])
            candidates = [ADVICE]
            advice = copy.deepcopy(original)
            advice['summary'] = ADVICE['hypothesis']
            candidates.append(advice)
            for citations in [[], [{'evidence_id': 'legacy', 'reference': {}}]]:
                candidate = copy.deepcopy(original)
                candidate['claims'][0]['citations'] = citations
                candidates.append(candidate)
            for candidate in candidates:
                with self.subTest(candidate=candidate):
                    result = fixture.app.validate_proposal(run['id'], candidate, population='test')
                    self.assertEqual(result['status'], 'review_required')
                    self.assertIsNone(result['finding'])
                    self.assertNotIn(ADVICE['hypothesis'], str(result))
                    self.assertEqual(fixture.app.get(run['id'], population='test')['finding'], original)
            with fixture.fixture.connection() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM findings').fetchone()[0], 0)
        finally:
            fixture.tearDown()
