import unittest

from market_conformance import MarketConformanceApplication, production_market_readiness


class MarketConformanceTest(unittest.TestCase):
    def test_production_has_exact_unmet_gates_and_no_fixture_activation_path(self):
        readiness = production_market_readiness(evaluated_at=100)
        self.assertEqual(readiness['availability'], 'unavailable')
        codes = {item['code'] for item in readiness['unmet_prerequisites']}
        self.assertIn('historical_coverage', codes)
        self.assertIn('explicit_provider_approval', codes)
        self.assertIn('reproducibility', codes)
        self.assertEqual(readiness['evaluation_scope'], 'production')

class SyntheticConformanceTest(unittest.TestCase):
    def test_complete_synthetic_evidence_is_available_only_in_its_scope_and_reproducible(self):
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        app = MarketConformanceApplication()
        report = app.evaluate(scope, evidence, adapter=SyntheticAdapter())
        self.assertEqual(report['readiness']['availability'], 'available')
        self.assertEqual(report['readiness']['evaluation_scope'], 'toy-2026')
        self.assertEqual(report['readiness']['evidence_class'], 'synthetic')
        self.assertEqual(report['readiness']['unmet_prerequisites'], [])
        self.assertEqual(app.reproduce(report, adapter=SyntheticAdapter()), report)
        self.assertEqual(production_market_readiness(evaluated_at=100)['availability'], 'unavailable')

    def test_each_required_case_can_block_its_gate_and_never_implies_production(self):
        from copy import deepcopy
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        from market_conformance import GATE_CASES
        app = MarketConformanceApplication()
        for gate, cases in GATE_CASES.items():
            for case in cases:
                with self.subTest(gate=gate, case=case):
                    scope, evidence = fixture()
                    changed = deepcopy(evidence.observations)
                    changed[case] = {'incorrect': True}
                    report = app.evaluate(scope, with_observations(evidence, changed), adapter=SyntheticAdapter())
                    decision = next(item for item in report['gates'] if item['code'] == gate)
                    self.assertEqual(decision['status'], 'fail')
                    self.assertNotEqual(report['readiness']['availability'], 'available')
                    self.assertEqual(production_market_readiness(evaluated_at=100)['availability'], 'unavailable')

    def test_missing_and_unsupported_evidence_are_distinct_from_failed_evidence(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        observations = dict(evidence.observations)
        del observations['split']
        report = MarketConformanceApplication().evaluate(scope, with_observations(evidence, observations), adapter=SyntheticAdapter())
        self.assertEqual(report['readiness']['availability'], 'conditional')
        self.assertEqual(report['readiness']['unmet_prerequisites'], [{'code': 'split_handling', 'status': 'unsupported', 'detail': 'split: missing independent expectation or candidate observation'}])
        del observations['cash_distribution']
        observations['non_cash_action'] = {'measurement': 'fabricated'}
        report = MarketConformanceApplication().evaluate(scope, replace(with_observations(evidence, observations), unsupported={'merger': 'adapter cannot supply merger evidence'}), adapter=SyntheticAdapter())
        self.assertEqual({item['code']: item['status'] for item in report['readiness']['unmet_prerequisites']}, {
            'split_handling': 'unsupported', 'cash_distribution_handling': 'unsupported', 'non_cash_actions': 'fail', 'terminal_events': 'unsupported',
        })

    def test_provider_adjusted_only_history_does_not_pass(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        snapshot = evidence.snapshots[0]
        semantics = dict(snapshot.semantics, adjustment='provider_adjusted', provider_adjusted=True)
        report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(replace(snapshot, semantics=semantics),)))
        self.assertIn('regular_session_daily_ohlcv', {item['code'] for item in report['readiness']['unmet_prerequisites']})
        self.assertEqual(next(item for item in report['gates'] if item['code'] == 'regular_session_daily_ohlcv')['status'], 'fail')

    def test_report_retains_raw_source_separately_and_detects_tampering(self):
        import base64
        import json
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        app = MarketConformanceApplication()
        report = json.loads(json.dumps(app.evaluate(scope, evidence, adapter=SyntheticAdapter())))
        snapshot = report['retained']['evidence']['snapshots'][0]
        self.assertEqual(json.loads(base64.b64decode(snapshot['raw_response']))['semantics']['ohlcv']['close'], 105)
        self.assertEqual(snapshot['semantics']['symbol_observed'], 'OLD')
        self.assertEqual(len(snapshot['semantics']['corporate_actions']), 6)
        self.assertEqual(app.reproduce(report, adapter=SyntheticAdapter()), report)
        report['retained']['evidence']['snapshots'][0]['revision'] = 'rewritten'
        with self.assertRaisesRegex(ValueError, 'digest'):
            app.reproduce(report, adapter=SyntheticAdapter())

    def test_evaluation_scope_cannot_be_production_even_with_complete_evidence(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        with self.assertRaisesRegex(ValueError, 'isolated'):
            MarketConformanceApplication().evaluate(replace(scope, scope_id='production'), evidence)
        with self.assertRaisesRegex(ValueError, 'class'):
            MarketConformanceApplication().evaluate(replace(scope, evidence_class='real_candidate'), evidence)

    def test_missing_provenance_identity_calendar_and_workload_are_not_inferred(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        snapshot = evidence.snapshots[0]
        for field, gate in [('identity_evidence', 'historical_security_identity'), ('timezone', 'session_calendar'), ('currency', 'currency_units'), ('corporate_actions', 'provenance_completeness')]:
            with self.subTest(field=field):
                semantics = dict(snapshot.semantics)
                del semantics[field]
                report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(replace(snapshot, semantics=semantics),)))
                self.assertIn(gate, {item['code'] for item in report['readiness']['unmet_prerequisites']})
        report = MarketConformanceApplication().evaluate(scope, replace(evidence, workload_provenance={}))
        self.assertIn('workload', {item['code'] for item in report['readiness']['unmet_prerequisites']})

    def test_v1_price_rows_are_not_conformance_evidence(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        v1 = {'company_id': 'OLD', 'timestamp': 1772830800000, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000}
        snapshot = replace(evidence.snapshots[0], semantics=v1, source='yfinance')
        report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(snapshot,)))
        self.assertEqual(report['readiness']['availability'], 'unavailable')
        self.assertTrue(all(item['status'] != 'pass' for item in report['gates']))

    def test_no_evidence_does_not_pass_and_metrics_cannot_be_missing_or_negative(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        app = MarketConformanceApplication()
        report = app.evaluate(scope, replace(evidence, snapshots=(), observations={}, case_snapshot_refs={}, workload_provenance={}))
        self.assertEqual(report['readiness']['availability'], 'unavailable')
        self.assertEqual(len(report['readiness']['unmet_prerequisites']), 28)
        for case, unit in [('requests', 'count'), ('elapsed', 'milliseconds'), ('peak_memory', 'bytes'), ('retained_storage', 'bytes')]:
            observations = dict(evidence.observations)
            observations[case] = {unit: -1}
            report = app.evaluate(scope, replace(evidence, observations=observations))
            self.assertNotEqual(report['readiness']['availability'], 'available')

    def test_action_claims_without_separate_source_evidence_cannot_pass(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        snapshot = evidence.snapshots[0]
        semantics = dict(snapshot.semantics, corporate_actions=[])
        report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(replace(snapshot, semantics=semantics),)))
        unmet = {item['code'] for item in report['readiness']['unmet_prerequisites']}
        self.assertTrue({'split_handling', 'cash_distribution_handling', 'non_cash_actions', 'terminal_events'}.issubset(unmet))

    def test_join_claims_with_incompatible_snapshot_scope_cannot_pass(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        snapshot = evidence.snapshots[0]
        semantics = dict(snapshot.semantics, security_identity='unrelated', calendar_version='other-calendar')
        report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(replace(snapshot, semantics=semantics),)))
        self.assertIn('identity_calendar_joins', {item['code'] for item in report['readiness']['unmet_prerequisites']})

    def test_retained_input_replay_is_required_and_rejects_unrelated_raw_or_cached_values(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter
        scope, evidence = fixture()
        app = MarketConformanceApplication()
        self.assertNotEqual(app.evaluate(scope, evidence)['readiness']['availability'], 'available')
        for snapshot in (
            replace(evidence.snapshots[0], raw_response=b'unrelated'),
            replace(evidence.snapshots[0], semantics=dict(evidence.snapshots[0].semantics, ohlcv={'open': 1, 'high': 3, 'low': 1, 'close': 2, 'volume': 1000})),
        ):
            report = app.evaluate(scope, replace(evidence, snapshots=(snapshot,)), adapter=SyntheticAdapter())
            self.assertNotEqual(report['readiness']['availability'], 'available')
            self.assertIn('reproducibility', {item['code'] for item in report['readiness']['unmet_prerequisites']})

    def test_matching_arbitrary_claims_cannot_replace_required_case_evidence(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        cases = ('holiday', 'early_close', 'dst_timezone', 'ticker_rename', 'ticker_reuse', 'listing_change', 'later_revision', 'representative_calculation', 'reproduction')
        expectations, observations = dict(scope.expectations), dict(evidence.observations)
        for case in cases:
            expectations[case] = observations[case] = {'nothing': True}
        report = MarketConformanceApplication().evaluate(replace(scope, expectations=expectations), with_observations(evidence, observations), adapter=SyntheticAdapter())
        self.assertNotEqual(report['readiness']['availability'], 'available')
        self.assertTrue({'session_calendar', 'historical_security_identity', 'revision_correction', 'deterministic_calculations', 'reproducibility'}.issubset({item['code'] for item in report['readiness']['unmet_prerequisites']}))

    def test_historical_identity_and_action_provenance_cannot_be_reversed_or_unrelated(self):
        from copy import deepcopy
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter
        scope, evidence = fixture()
        for corruption in ('interval', 'action_identity', 'action_terms', 'future_availability'):
            semantics = deepcopy(evidence.snapshots[0].semantics)
            if corruption == 'interval':
                semantics['identity_evidence'].update(valid_from='2099-01-01', valid_to='1900-01-01')
            elif corruption == 'action_identity':
                for action in semantics['corporate_actions']:
                    action.update(securities=['unrelated'], listings=['unrelated'])
            elif corruption == 'action_terms':
                semantics['corporate_actions'][0]['terms']['ratio'] = '9:1'
            else:
                semantics['corporate_actions'][0]['availability']['observed_at_ms'] = scope.evaluated_at_ms + 1
            with self.subTest(corruption=corruption):
                report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(replace(evidence.snapshots[0], semantics=semantics),)), adapter=SyntheticAdapter())
                self.assertNotEqual(report['readiness']['availability'], 'available')

    def test_null_nested_evidence_yields_unmet_gates(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter
        scope, evidence = fixture()
        for field in ('identity_evidence', 'missingness', 'ohlcv', 'ohlcv_definitions', 'corporate_actions'):
            with self.subTest(field=field):
                snapshot = replace(evidence.snapshots[0], semantics=dict(evidence.snapshots[0].semantics, **{field: None}))
                report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(snapshot,)), adapter=SyntheticAdapter())
                self.assertNotEqual(report['readiness']['availability'], 'available')

    def test_provider_neutral_adapter_seam_replays_without_expected_answers(self):
        from market_fixture import fixture, SyntheticAdapter
        scope, _ = fixture()
        report = MarketConformanceApplication().evaluate_adapter(scope, SyntheticAdapter())
        self.assertEqual(report['readiness']['availability'], 'available')

    def test_relabeling_fixture_report_cannot_supply_real_candidate_evidence(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter
        scope, evidence = fixture()
        report = MarketConformanceApplication().evaluate(
            replace(scope, evidence_class='real_candidate'),
            replace(evidence, evidence_class='real_candidate'), adapter=SyntheticAdapter(),
        )
        self.assertEqual(report['readiness']['availability'], 'unavailable')
        self.assertEqual(report['retained']['evidence']['snapshots'][0]['evidence_class'], 'synthetic')
        self.assertEqual(production_market_readiness(evaluated_at=100)['availability'], 'unavailable')

    def test_empty_or_mistyped_required_fields_are_not_evidence(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        for case, field in [('ticker_rename', 'new_symbol'), ('early_close', 'close_utc'), ('dst_timezone', 'before_utc'), ('calculation_workload', 'method')]:
            for empty in ('', None, 0):
                with self.subTest(case=case, field=field, value=empty):
                    observations, expectations = dict(evidence.observations), dict(scope.expectations)
                    observations[case] = expectations[case] = dict(observations[case], **{field: empty})
                    report = MarketConformanceApplication().evaluate(replace(scope, expectations=expectations), with_observations(evidence, observations), adapter=SyntheticAdapter())
                    self.assertNotEqual(report['readiness']['availability'], 'available')

    def test_malformed_action_identities_are_failed_evidence(self):
        from dataclasses import replace
        from copy import deepcopy
        from market_fixture import fixture, SyntheticAdapter
        scope, evidence = fixture()
        for field in ('securities', 'listings'):
            semantics = deepcopy(evidence.snapshots[0].semantics)
            semantics['corporate_actions'][0][field] = 1
            report = MarketConformanceApplication().evaluate(scope, replace(evidence, snapshots=(replace(evidence.snapshots[0], semantics=semantics),)), adapter=SyntheticAdapter())
            self.assertNotEqual(report['readiness']['availability'], 'available')

    def test_environment_flags_cannot_activate_production_readiness(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'MARKET_DATA_READY': 'true', 'SIGNAL_MARKET_PROVIDER': 'yfinance', 'SIGNAL_EVALUATION_SCOPE': 'synthetic'}):
            readiness = production_market_readiness(evaluated_at=100)
        self.assertEqual(readiness['availability'], 'unavailable')
        self.assertEqual(readiness['evaluation_scope'], 'production')

    def test_matching_counterexamples_cannot_override_mandatory_contract_outcomes(self):
        from copy import deepcopy
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        for case, field, value, gate in (
            ('ticker_reuse', 'joined', True, 'historical_security_identity'),
            ('later_revision', 'earlier_preserved', False, 'revision_correction'),
            ('bounded_revision_refresh', 'session_scope', [], 'revision_refresh_validation'),
        ):
            with self.subTest(case=case):
                scope, evidence = fixture()
                observations, expectations = deepcopy(evidence.observations), deepcopy(scope.expectations)
                observations[case][field] = expectations[case][field] = value
                report = MarketConformanceApplication().evaluate(
                    replace(scope, expectations=expectations),
                    with_observations(evidence, observations), adapter=SyntheticAdapter(),
                )
                self.assertNotEqual(report['readiness']['availability'], 'available')
                decision = next(item for item in report['gates'] if item['code'] == gate)
                self.assertEqual(decision['status'], 'fail')
                self.assertNotIn('candidate observation disagrees with independent expectation',
                                 [detail for check in decision['cases'] for detail in check['details']])

    def test_ticker_reuse_requires_distinct_supported_security_identities(self):
        from copy import deepcopy
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        for new_identity, expected_status in (('toy-A', 'fail'), ('unresolved', 'unsupported')):
            with self.subTest(identity=new_identity):
                scope, evidence = fixture()
                observations, expectations = deepcopy(evidence.observations), deepcopy(scope.expectations)
                observations['ticker_reuse']['new_security'] = expectations['ticker_reuse']['new_security'] = new_identity
                report = MarketConformanceApplication().evaluate(
                    replace(scope, expectations=expectations),
                    with_observations(evidence, observations), adapter=SyntheticAdapter(),
                )
                self.assertNotEqual(report['readiness']['availability'], 'available')
                check = next(check for gate in report['gates'] for check in gate['cases'] if check['case'] == 'ticker_reuse')
                self.assertEqual(check['status'], expected_status)

    def test_bounded_refresh_scope_entries_must_be_explicit_sessions(self):
        from copy import deepcopy
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        for session_scope in ([''], ['   '], [None], [{}]):
            with self.subTest(session_scope=session_scope):
                scope, evidence = fixture()
                observations, expectations = deepcopy(evidence.observations), deepcopy(scope.expectations)
                observations['bounded_revision_refresh']['session_scope'] = expectations['bounded_revision_refresh']['session_scope'] = session_scope
                report = MarketConformanceApplication().evaluate(
                    replace(scope, expectations=expectations),
                    with_observations(evidence, observations), adapter=SyntheticAdapter(),
                )
                self.assertNotEqual(report['readiness']['availability'], 'available')
                self.assertEqual(next(gate for gate in report['gates'] if gate['code'] == 'revision_refresh_validation')['status'], 'fail')

    def test_valid_reuse_preservation_and_explicit_scope_still_pass(self):
        from market_fixture import fixture, SyntheticAdapter
        scope, evidence = fixture()
        report = MarketConformanceApplication().evaluate(scope, evidence, adapter=SyntheticAdapter())
        gates = {gate['code']: gate for gate in report['gates']}
        for gate in ('historical_security_identity', 'revision_correction', 'revision_refresh_validation'):
            with self.subTest(gate=gate):
                self.assertEqual(gates[gate]['status'], 'pass')
        self.assertEqual(report['readiness']['availability'], 'available')
        self.assertEqual(report['readiness']['evidence_class'], 'synthetic')
        self.assertEqual(production_market_readiness(evaluated_at=scope.evaluated_at_ms)['availability'], 'unavailable')

    def test_ticker_reuse_cannot_pass_without_both_retained_identity_mappings(self):
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter
        scope, evidence = fixture()
        refs = dict(evidence.case_snapshot_refs, ticker_reuse=(0,))
        report = MarketConformanceApplication().evaluate(scope, replace(evidence, case_snapshot_refs=refs), adapter=SyntheticAdapter())
        check = next(check for gate in report['gates'] for check in gate['cases'] if check['case'] == 'ticker_reuse')
        self.assertEqual(check['status'], 'unsupported')
        self.assertNotEqual(report['readiness']['availability'], 'available')

    def test_missing_refresh_scope_is_failed_without_inventing_a_default(self):
        from copy import deepcopy
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        observations, expectations = deepcopy(evidence.observations), deepcopy(scope.expectations)
        del observations['bounded_revision_refresh']['session_scope']
        del expectations['bounded_revision_refresh']['session_scope']
        report = MarketConformanceApplication().evaluate(replace(scope, expectations=expectations), with_observations(evidence, observations), adapter=SyntheticAdapter())
        self.assertEqual(next(gate for gate in report['gates'] if gate['code'] == 'revision_refresh_validation')['status'], 'fail')
        self.assertNotEqual(report['readiness']['availability'], 'available')
        self.assertNotIn('session_scope', report['retained']['evidence']['observations']['bounded_revision_refresh'])

    def test_later_revision_is_separately_attributable_and_does_not_change_earlier_replay(self):
        import json
        from copy import deepcopy
        from dataclasses import replace
        from market_fixture import fixture, SyntheticAdapter, with_observations
        scope, evidence = fixture()
        app = MarketConformanceApplication()
        earlier = app.evaluate(scope, evidence, adapter=SyntheticAdapter())
        saved_earlier = deepcopy(earlier)
        observations = deepcopy(evidence.observations)
        observations['ordinary_session']['ohlcv'][3] = 106
        observations['representative_calculation'].update(raw_close=106, close_open_factor='1.06')
        revised = with_observations(evidence, observations)
        semantics = deepcopy(revised.snapshots[0].semantics)
        semantics['ohlcv']['close'] = 106
        raw = json.loads(revised.snapshots[0].raw_response)
        raw['semantics'] = semantics
        revised_snapshot = replace(revised.snapshots[0], semantics=semantics,
                                   raw_response=json.dumps(raw, sort_keys=True).encode(),
                                   revision='toy-revision-2', retrieval_observation='toy-correction-retrieval',
                                   retrieved_at_ms=1773172800000)
        revised = replace(revised, snapshots=(revised_snapshot, revised.snapshots[1]))
        later = app.evaluate(replace(scope, scope_id='toy-later-revision', expectations=deepcopy(observations)), revised, adapter=SyntheticAdapter())
        self.assertEqual(later['readiness']['availability'], 'available')
        self.assertNotEqual(later['evaluation_id'], earlier['evaluation_id'])
        self.assertEqual(later['retained']['evidence']['snapshots'][0]['revision'], 'toy-revision-2')
        self.assertEqual(earlier, saved_earlier)
        self.assertEqual(app.reproduce(earlier, adapter=SyntheticAdapter()), saved_earlier)
        self.assertEqual(earlier['retained']['evidence']['snapshots'][0]['semantics']['ohlcv']['close'], 105)


if __name__ == '__main__':
    unittest.main()
