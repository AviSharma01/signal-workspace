import unittest
from dataclasses import replace
from unittest.mock import patch

from tests import test_events
from analysis import AnalysisApplication
from tests.analysis_fixture import GOLDEN, action, outcome_evidence, report, update_bar
from tests.market_fixture import SyntheticAdapter
from tests.test_events import ms


class AnalysisTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_events.EventApplicationTest()
        self.fixture.setUp()
        self.analysis = AnalysisApplication(self.fixture.connection, lambda: self.fixture.now)

    def tearDown(self):
        self.fixture.tearDown()

    def test_production_execution_requires_readiness_even_without_inputs(self):
        response = self.analysis.execute(population='real', event_view_id='missing', market_input_id='missing')
        self.assertEqual(response['capability']['availability'], 'unavailable')
        self.assertEqual(response['result']['state'], 'error')
        self.assertEqual(response['runs'], [])
        self.assertEqual(self.analysis.query(population='real')['runs'], [])

    def prepare(self, *, resolve_identity=True, direction='purchase', publication='2025-07-03T09:00:00-04:00', population='test'):
        self.fixture.population = population
        version, rows = self.fixture.official(publication)
        if resolve_identity:
            self.fixture.identities(version, rows[0]['id'], ms('2025-07-03T09:00:00-04:00'))
        if direction != 'purchase':
            self.fixture.assertion('interpretation', version, ms('2025-07-03T09:00:00-04:00'),
                occurrence_id=rows[0]['id'], fields={'transaction_direction': direction})
        self.fixture.calendar(version, ms('2025-07-03T09:00:00-04:00'))
        view = self.fixture.events.record_view(population=population, perspective='public_information', as_of=self.fixture.now)
        self.fixture.now = ms('2026-10-06T12:00:00+00:00')
        scope, evidence = outcome_evidence()
        return view, scope, evidence

    def run_outcomes(self, view, scope, evidence, *, population='test'):
        retained = self.analysis.retain_evaluation(report(scope, evidence), population=population, adapter=SyntheticAdapter())
        response = self.analysis.execute(population=population, event_view_id=view['id'], market_input_id=retained['id'])
        self.assertEqual(response['capability']['availability'], 'available', response)
        return response['runs'][0]

    def test_all_four_golden_horizons_include_anchor_and_align_spy(self):
        view, scope, evidence = self.prepare()
        run = self.run_outcomes(view, scope, evidence)
        self.assertEqual(run['readiness_scope'], 'toy-2026')
        self.assertFalse(run['production_ready'])
        for outcome in run['outcomes']:
            expected = GOLDEN[outcome['horizon_sessions']]
            for key, value in zip(('security_gross', 'benchmark_gross', 'benchmark_relative_log', 'compounded_relative'), expected):
                self.assertAlmostEqual(outcome['metrics'][key]['value'], value, places=13)
            self.assertAlmostEqual(outcome['metrics']['direction_aligned_log']['value'], expected[2], places=13)
            self.assertEqual(len(outcome['session_dates']), outcome['horizon_sessions'])
        self.assertEqual(run['outcomes'][0]['outcome_boundary'], ms('2025-07-03T13:00:00-04:00'))
        self.assertEqual(run['outcomes'][1]['session_dates'], ['2025-07-03', '2025-07-07', '2025-07-08', '2025-07-09', '2025-07-10'])

    def test_split_evidence_retained_before_effective_session_changes_basis_only(self):
        view, scope, evidence = self.prepare()
        split = action('split', '2025-07-07', {'ratio': '2:1'})
        # Evidence is retained in the anchor record, not repeated on effective day.
        evidence = update_bar(evidence, 'security:ABC', 0, corporate_actions=[split])
        for index in range(1, 60):
            evidence = update_bar(evidence, 'security:ABC', index, ohlcv={
                'open': (100 + index) / 2, 'high': (101 + index) / 2,
                'low': (100 + index) / 2, 'close': (101 + index) / 2, 'volume': 2000})
        run = self.run_outcomes(view, scope, evidence)
        self.assertAlmostEqual(run['outcomes'][1]['metrics']['security_gross']['value'], 1.05)
        self.assertEqual(run['outcomes'][1]['application_adjustments']['security'][0]['share_ratio'], '2')

    def test_ex_date_reinvestment_compounds_and_anchor_distribution_is_excluded(self):
        view, scope, evidence = self.prepare()
        distributions = [action('cash_distribution', day, {'amount': amount}, units='USD/share')
                         for day, amount in [('2025-07-03', 50), ('2025-07-07', 2), ('2025-07-08', 2)]]
        for index in range(60):
            evidence = update_bar(evidence, 'security:ABC', index,
                ohlcv={'open': 100, 'high': 100, 'low': 100, 'close': 100, 'volume': 1000},
                corporate_actions=distributions)
        run = self.run_outcomes(view, scope, evidence)
        self.assertEqual(run['outcomes'][0]['metrics']['security_gross']['value'], 1)
        self.assertAlmostEqual(run['outcomes'][1]['metrics']['security_gross']['value'], 1.0404)
        self.assertEqual(len(run['outcomes'][1]['application_adjustments']['security']), 2)

    def test_sale_negates_log_outcome_without_changing_relative_compounding(self):
        view, scope, evidence = self.prepare(direction='sale')
        run = self.run_outcomes(view, scope, evidence)
        for outcome in run['outcomes']:
            expected = GOLDEN[outcome['horizon_sessions']]
            self.assertAlmostEqual(outcome['metrics']['direction_aligned_log']['value'], -expected[2])
            self.assertAlmostEqual(outcome['metrics']['compounded_relative']['value'], expected[3])

    def test_missing_intermediate_and_terminal_bars_only_block_dependent_windows(self):
        for index, valid_horizons in [(2, [1]), (59, [1, 5, 20])]:
            with self.subTest(index=index):
                view, scope, evidence = self.prepare()
                selected = [s for s in evidence.snapshots if s.semantics['security_identity'] == 'security:ABC'][index]
                evidence = replace(evidence, snapshots=tuple(s for s in evidence.snapshots if s != selected))
                run = self.run_outcomes(view, scope, evidence)
                for outcome in run['outcomes']:
                    horizon = outcome['horizon_sessions']
                    self.assertEqual(outcome['metrics']['security_gross']['availability'], 'available' if horizon in valid_horizons else 'unavailable')
                    self.assertEqual(outcome['metrics']['benchmark_gross']['availability'], 'available')
                    if horizon not in valid_horizons:
                        self.assertIsNone(outcome['metrics']['security_gross']['value'])
                        self.assertIn('missing_bar:' + selected.semantics['session_date'], outcome['reasons'])
                        self.assertEqual(len(outcome['session_dates']), horizon)
                        self.assertIsNotNone(outcome['outcome_boundary'])

    def test_unresolved_semantics_block_only_dependent_windows_and_metrics(self):
        cases = [
            ({'currency': 'EUR'}, 'currency_or_units_unresolved'),
            ({'price_unit': 'unknown'}, 'currency_or_units_unresolved'),
            ({'open_at': 1}, 'sessions_incompatible:2025-07-07'),
            ({'provider_adjusted': True, 'adjustment': 'provider_adjusted'}, 'snapshot_semantics:regular_session_daily_ohlcv:2025-07-07'),
            ({'identity_evidence': {'source': 'later mapping', 'revision': '2', 'valid_from': '2020-01-01',
              'valid_to': '2026-12-31', 'public_at_ms': ms('2025-07-08T12:00:00+00:00'), 'listing_country': 'US'}}, 'identity_evidence_after_event_boundary_or_unknown'),
            ({'listing_identity': 'listing:different'}, 'listing_identity_incompatible'),
            ({'ohlcv': {'open': 101, 'high': 102, 'low': 101, 'close': None, 'volume': 1000}}, 'price_unavailable:2025-07-07'),
            ({'missingness': {'state': 'missing', 'gaps': []}}, 'missing_bar:2025-07-07'),
        ]
        for changes, reason in cases:
            with self.subTest(changes=changes):
                view, scope, evidence = self.prepare()
                run = self.run_outcomes(view, scope, update_bar(evidence, 'security:ABC', 1, **changes))
                self.assertEqual(run['outcomes'][0]['availability'], 'available')
                for outcome in run['outcomes'][1:]:
                    self.assertIn(reason, outcome['reasons'])
                    self.assertIsNone(outcome['metrics']['security_gross']['value'])
                    self.assertEqual(outcome['metrics']['benchmark_gross']['availability'], 'available')
                    self.assertIsNone(outcome['metrics']['benchmark_relative_log']['value'])

    def test_unresolved_event_security_cannot_be_repaired_by_market_mapping(self):
        view, scope, evidence = self.prepare(resolve_identity=False)
        run = self.run_outcomes(view, scope, evidence)
        self.assertTrue(all('security_identity_unresolved' in o['reasons'] for o in run['outcomes']))
        self.assertTrue(all(o['metrics']['security_gross']['value'] is None for o in run['outcomes']))
        self.assertEqual(self.fixture.events.get_recorded_view(view['id'], population='test'), view)

    def test_benchmark_missing_or_incompatible_cannot_substitute_security_return(self):
        view, scope, evidence = self.prepare()
        for changes in ({'close_at': 1}, {'currency': 'unknown'}, {'instrument_name': 'another fund'}):
            with self.subTest(changes=changes):
                index = 0 if 'instrument_name' in changes else 1
                run = self.run_outcomes(view, scope, update_bar(evidence, 'security:SPY', index, **changes))
                outcome = run['outcomes'][1]
                self.assertEqual(outcome['metrics']['security_gross']['availability'], 'available')
                self.assertIsNone(outcome['metrics']['benchmark_gross']['value'])
                self.assertIsNone(outcome['metrics']['compounded_relative']['value'])

    def test_unresolved_non_cash_and_terminal_actions_never_invent_continuation(self):
        for kind in ('non_cash', 'merger', 'spin_off', 'delisting', 'terminal_event', 'listing_change', 'ambiguous'):
            with self.subTest(kind=kind):
                view, scope, evidence = self.prepare()
                evidence = update_bar(evidence, 'security:ABC', 0,
                    corporate_actions=[action(kind, '2025-07-07', {'description': 'unresolved'})])
                run = self.run_outcomes(view, scope, evidence)
                self.assertEqual(run['outcomes'][0]['availability'], 'available')
                for outcome in run['outcomes'][1:]:
                    self.assertIn('action_unresolved:' + kind + ':2025-07-07', outcome['reasons'])
                    self.assertIsNone(outcome['metrics']['security_total_return']['value'])
                    self.assertEqual(outcome['metrics']['benchmark_gross']['availability'], 'available')

    def test_repeated_execution_and_revised_snapshot_keep_old_runs_reproducible(self):
        view, scope, evidence = self.prepare()
        first = self.run_outcomes(view, scope, evidence)
        self.fixture.now += 1000
        second = self.run_outcomes(view, scope, evidence)
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(first['outcomes'], second['outcomes'])
        revised = update_bar(evidence, 'security:ABC', 19,
            ohlcv={'open': 119, 'high': 130, 'low': 119, 'close': 130, 'volume': 1000})
        self.fixture.now = ms('2026-10-06T14:00:00+00:00')
        revised = replace(revised, snapshots=tuple(
            replace(s, retrieved_at_ms=ms('2026-10-06T13:00:00+00:00'), retrieval_observation=s.retrieval_observation + ':later')
            if s.revision.endswith(':changed') else s for s in revised.snapshots))
        scope = replace(scope, evaluated_at_ms=self.fixture.now)
        third = self.run_outcomes(view, scope, revised)
        self.assertNotEqual(third['market_input_id'], first['market_input_id'])
        self.assertEqual(third['outcomes'][0]['metrics'], first['outcomes'][0]['metrics'])
        self.assertNotEqual(third['outcomes'][2]['metrics'], first['outcomes'][2]['metrics'])
        self.assertEqual(self.analysis.get_run(first['id'], population='test'), first)
        with patch('analysis.METHOD_VERSION', 'event-outcomes@2'), patch('market_conformance.CONTRACT_VERSION', 'signal-v2-market-data-contract@2'):
            self.assertEqual(self.analysis.reproduce(first['id'], population='test')['output'], first)
        self.assertEqual(len(self.analysis.query(population='test')['runs']), 3)

    def test_outcome_revisions_and_future_correction_do_not_change_event_or_watch_state(self):
        from watch_events import WatchApplication
        view, scope, evidence = self.prepare()
        watch = WatchApplication(self.fixture.connection, lambda: self.fixture.now)
        before_events = self.fixture.events.derive(population='test', perspective='public_information', as_of=view['asOf'])
        admitted = watch.admit(view['events'][0]['id'], population='test')
        before_watch = watch.get(admitted['watchEvent']['id'], population='test')
        run = self.run_outcomes(view, scope, evidence)
        event = view['events'][0]
        self.fixture.assertion('correction', event['provenance']['rows'][0]['artifactVersionId'],
            ms('2026-10-06T10:00:00+00:00'), occurrence_id=event['occurrenceIds'][0],
            fields={'transaction_direction': 'sale'})
        later_events = self.fixture.events.derive(population='test', perspective='public_information', as_of=view['asOf'])
        # Computation time may advance; historical Events themselves cannot change.
        self.assertEqual(before_events['events'], later_events['events'])
        after_watch = watch.get(admitted['watchEvent']['id'], population='test')
        self.assertEqual(after_watch['lifecycleHistory'], before_watch['lifecycleHistory'])
        self.assertEqual(self.analysis.reproduce(run['id'], population='test')['output'], run)

    def test_synthetic_readiness_and_results_cannot_enter_production(self):
        view, scope, evidence = self.prepare()
        ready = report(scope, evidence)
        with self.assertRaisesRegex(ValueError, 'Synthetic'):
            self.analysis.retain_evaluation(ready, population='real', adapter=SyntheticAdapter())
        run = self.run_outcomes(view, scope, evidence)
        refused = self.analysis.execute(population='real', event_view_id=view['id'], market_input_id=run['market_input_id'])
        self.assertEqual(refused['capability']['availability'], 'unavailable')
        self.assertEqual(refused['runs'], [])
        self.assertEqual(self.analysis.query(population='real')['runs'], [])
        with self.assertRaises(KeyError):
            self.analysis.get_run(run['id'], population='real')
        with self.assertRaises(ValueError):
            self.analysis.execute(population='demo', event_view_id=view['id'], market_input_id=run['market_input_id'])

    def test_partial_or_forged_readiness_is_not_execution_authority(self):
        view, scope, evidence = self.prepare()
        ready = report(scope, evidence)
        ready['readiness']['evaluation_scope'] = 'production'
        with self.assertRaises(ValueError):
            self.analysis.retain_evaluation(ready, population='test', adapter=SyntheticAdapter())
        incomplete = replace(evidence, unsupported={'split': 'no action evidence'})
        with self.assertRaisesRegex(ValueError, 'Complete scoped'):
            self.analysis.retain_evaluation(report(scope, incomplete), population='test', adapter=SyntheticAdapter())

    def test_conflicting_action_revisions_are_unavailable_not_added_together(self):
        view, scope, evidence = self.prepare()
        first = action('cash_distribution', '2025-07-07', {'amount': 2}, units='USD/share')
        revised = {**first, 'revision': '2', 'terms': {'amount': 3}}
        evidence = update_bar(evidence, 'security:ABC', 0, corporate_actions=[first, revised])
        run = self.run_outcomes(view, scope, evidence)
        self.assertEqual(run['outcomes'][0]['availability'], 'available')
        self.assertIn('action_evidence_ambiguous', run['outcomes'][1]['reasons'])
        self.assertIsNone(run['outcomes'][1]['metrics']['security_gross']['value'])

    def test_same_action_identity_with_revised_date_is_not_applied_on_both_dates(self):
        view, scope, evidence = self.prepare()
        first = {**action('split', '2025-07-07', {'ratio': '2:1'}), 'action_id': 'split:one'}
        revised = {**first, 'revision': '2', 'dates': {'effective': '2025-07-08'}}
        evidence = update_bar(evidence, 'security:ABC', 0, corporate_actions=[first, revised])
        run = self.run_outcomes(view, scope, evidence)
        self.assertEqual(run['outcomes'][0]['availability'], 'available')
        for outcome in run['outcomes'][1:]:
            self.assertIn('action_evidence_ambiguous', outcome['reasons'])
            self.assertIsNone(outcome['metrics']['security_gross']['value'])

    def test_same_day_split_and_cash_use_new_share_basis_with_close_reinvestment(self):
        view, scope, evidence = self.prepare()
        actions = [action('split', '2025-07-07', {'ratio': '2:1'}),
                   action('cash_distribution', '2025-07-07', {'amount': 1}, units='USD/share')]
        evidence = update_bar(evidence, 'security:ABC', 0,
            ohlcv={'open': 100, 'high': 100, 'low': 100, 'close': 100, 'volume': 1000}, corporate_actions=actions)
        for index in range(1, 60):
            evidence = update_bar(evidence, 'security:ABC', index,
                ohlcv={'open': 50, 'high': 50, 'low': 50, 'close': 50, 'volume': 2000})
        run = self.run_outcomes(view, scope, evidence)
        # Two shares at $50 plus $1 per new share -> $102 / original $100.
        self.assertEqual(run['outcomes'][1]['metrics']['security_gross']['value'], 1.02)

    def test_incompatible_calendars_and_missing_calendar_terminal_do_not_shorten_windows(self):
        view, scope, evidence = self.prepare()
        anchor = [s for s in evidence.snapshots if s.semantics['security_identity'] == 'security:ABC'][0]
        calendar = {**anchor.semantics['calendar'], 'sessions': anchor.semantics['calendar']['sessions'][:20]}
        # Security has a shorter certified calendar; SPY retains all expected dates.
        run = self.run_outcomes(view, scope, update_bar(evidence, 'security:ABC', 0, calendar=calendar))
        self.assertTrue(all(o['availability'] == 'available' for o in run['outcomes'][:3]))
        self.assertIn('sessions_incompatible', run['outcomes'][3]['reasons'])
        self.assertEqual(len(run['outcomes'][3]['session_dates']), 60)
        spy = [s for s in evidence.snapshots if s.semantics['security_identity'] == 'security:SPY'][0]
        spy_calendar = {**spy.semantics['calendar'], 'sessions': spy.semantics['calendar']['sessions'][:20]}
        evidence = update_bar(evidence, 'security:ABC', 0, calendar=calendar)
        evidence = update_bar(evidence, 'security:SPY', 0, calendar=spy_calendar)
        run = self.run_outcomes(view, scope, evidence)
        self.assertTrue(all(o['availability'] == 'available' for o in run['outcomes'][:3]))
        self.assertIn('required_session_window_unavailable', run['outcomes'][3]['reasons'])
        self.assertIsNone(run['outcomes'][3]['outcome_boundary'])
        self.assertIsNone(run['outcomes'][3]['metrics']['security_gross']['value'])

    def test_missing_anchor_metadata_is_unavailable_and_never_raises(self):
        view, scope, evidence = self.prepare()
        for key in ('calendar_version', 'exchange', 'timezone', 'listing_identity'):
            with self.subTest(key=key):
                snapshots = list(evidence.snapshots)
                position = next(i for i, s in enumerate(snapshots) if s.semantics['security_identity'] == 'security:SPY')
                bar = snapshots[position]
                semantics = dict(bar.semantics)
                del semantics[key]
                import json
                snapshots[position] = replace(bar, semantics=semantics,
                    raw_response=json.dumps({'semantics': semantics, 'observations': evidence.observations}, sort_keys=True).encode())
                run = self.run_outcomes(view, scope, replace(evidence, snapshots=tuple(snapshots)))
                for outcome in run['outcomes']:
                    self.assertEqual(outcome['metrics']['security_gross']['availability'], 'available')
                    self.assertIsNone(outcome['metrics']['benchmark_gross']['value'])
                    self.assertIsNone(outcome['metrics']['benchmark_relative_log']['value'])

    def test_readiness_scope_does_not_authorize_unrelated_calendar_or_security(self):
        view, scope, evidence = self.prepare()
        for changed_scope in (replace(scope, securities=('toy-A', 'toy-B', 'security:SPY')),
                              replace(scope, coverage_start='2026-01-01')):
            with self.subTest(scope=changed_scope):
                # Conformance itself may reject scope; passing scopes still cannot
                # authorize out-of-scope security/window observations.
                ready = report(changed_scope, evidence)
                if ready['readiness']['availability'] != 'available':
                    with self.assertRaisesRegex(ValueError, 'Complete scoped'):
                        self.analysis.retain_evaluation(ready, population='test', adapter=SyntheticAdapter())
                    continue
                run = self.run_outcomes(view, changed_scope, evidence)
                self.assertIsNone(run['outcomes'][0]['metrics']['security_gross']['value'])
                self.assertIn('snapshot_outside_readiness_scope', run['outcomes'][0]['reasons'])
        changed = update_bar(evidence, 'security:ABC', 1, calendar_version='unapproved-calendar@2')
        run = self.run_outcomes(view, scope, changed)
        self.assertEqual(run['outcomes'][0]['availability'], 'available')
        self.assertIn('snapshot_outside_readiness_scope', run['outcomes'][1]['reasons'])

    def test_source_feed_changes_and_duplicate_bar_revisions_are_unavailable(self):
        view, scope, evidence = self.prepare()
        changed = update_bar(evidence, 'security:ABC', 1, feed_venue='another unvalidated venue')
        run = self.run_outcomes(view, scope, changed)
        self.assertIn('source_compatibility_unresolved', run['outcomes'][1]['reasons'])
        selected = [s for s in evidence.snapshots if s.semantics['security_identity'] == 'security:ABC'][1]
        changed = replace(evidence, snapshots=(*evidence.snapshots, replace(selected, revision='revision-two')))
        run = self.run_outcomes(view, scope, changed)
        self.assertIn('ambiguous_snapshot:2025-07-07', run['outcomes'][1]['reasons'])
        self.assertEqual(run['outcomes'][0]['availability'], 'available')

    def test_pre_close_retrieval_cannot_supply_a_completed_session_return(self):
        view, scope, evidence = self.prepare()
        snapshots = list(evidence.snapshots)
        position = next(i for i, s in enumerate(snapshots) if s.semantics['security_identity'] == 'security:ABC'
                        and s.semantics['session_date'] == '2025-07-07')
        snapshots[position] = replace(snapshots[position], retrieved_at_ms=ms('2025-07-07T12:00:00-04:00'))
        run = self.run_outcomes(view, scope, replace(evidence, snapshots=tuple(snapshots)))
        self.assertEqual(run['outcomes'][0]['availability'], 'available')
        self.assertIn('completed_session_observation_unavailable', run['outcomes'][1]['reasons'])

    def test_exact_at_open_anchor_uses_next_regular_session_and_excludes_its_distribution(self):
        view, scope, evidence = self.prepare(publication='2025-07-03T09:30:00-04:00')
        self.assertEqual(view['events'][0]['anchor']['session_date'], '2025-07-07')
        evidence = update_bar(evidence, 'security:ABC', 0, corporate_actions=[
            action('cash_distribution', '2025-07-07', {'amount': 30}, units='USD/share')])
        run = self.run_outcomes(view, scope, evidence)
        self.assertAlmostEqual(run['outcomes'][0]['metrics']['security_gross']['value'], 1.0099009900990099)
        self.assertAlmostEqual(run['outcomes'][1]['metrics']['security_gross']['value'], 1.0495049504950495)
        self.assertEqual(run['outcomes'][0]['session_dates'], ['2025-07-07'])
        self.assertEqual(run['outcomes'][2]['availability'], 'available')
        self.assertIsNone(run['outcomes'][3]['metrics']['security_gross']['value'])

    def test_named_evaluation_scope_is_available_only_in_isolated_evaluation_population(self):
        view, scope, evidence = self.prepare(population='evaluation')
        run = self.run_outcomes(view, scope, evidence, population='evaluation')
        self.assertFalse(run['production_ready'])
        self.assertEqual(self.analysis.query(population='evaluation')['runs'][0]['id'], run['id'])
        self.assertEqual(self.analysis.query(population='real')['runs'], [])
        with self.assertRaises(KeyError):
            self.analysis.get_run(run['id'], population='test')
        self.assertEqual(self.analysis.reproduce(run['id'], population='evaluation')['output'], run)

    def test_off_window_action_and_calendar_evidence_must_predate_readiness_evaluation(self):
        view, scope, evidence = self.prepare()
        changed = update_bar(evidence, 'security:ABC', 59, corporate_actions=[
            action('cash_distribution', '2025-07-07', {'amount': 20}, units='USD/share')])
        changed = replace(changed, snapshots=tuple(
            replace(s, retrieved_at_ms=scope.evaluated_at_ms + 1) if s.revision.endswith(':changed') else s
            for s in changed.snapshots))
        run = self.run_outcomes(view, scope, changed)
        self.assertEqual(run['outcomes'][0]['availability'], 'available')
        self.assertIn('action_evidence_unavailable', run['outcomes'][1]['reasons'])
        self.assertIsNone(run['outcomes'][1]['metrics']['security_gross']['value'])
        anchor = next(s for s in evidence.snapshots if s.semantics['security_identity'] == 'security:ABC')
        changed = update_bar(evidence, 'security:ABC', 0, calendar=None)
        changed = update_bar(changed, 'security:ABC', 59, calendar=anchor.semantics['calendar'])
        changed = replace(changed, snapshots=tuple(
            replace(s, retrieved_at_ms=scope.evaluated_at_ms + 1) if s.semantics.get('calendar') and s.semantics['security_identity'] == 'security:ABC' else s
            for s in changed.snapshots))
        run = self.run_outcomes(view, scope, changed)
        self.assertIn('calendar_outside_readiness_scope', run['outcomes'][0]['reasons'])
        self.assertIsNone(run['outcomes'][0]['metrics']['security_gross']['value'])

    def test_later_calendar_proof_cannot_change_an_earlier_supported_window(self):
        view, scope, evidence = self.prepare()
        anchor = next(s for s in evidence.snapshots if s.semantics['security_identity'] == 'security:ABC')
        later_calendar = {**anchor.semantics['calendar'], 'public_at_ms': ms('2025-07-08T10:00:00-04:00')}
        changed = update_bar(evidence, 'security:ABC', 59, calendar=later_calendar)
        run = self.run_outcomes(view, scope, changed)
        for outcome in run['outcomes']:
            self.assertAlmostEqual(outcome['metrics']['security_gross']['value'], GOLDEN[outcome['horizon_sessions']][0])

    def test_extra_security_session_cannot_be_silently_skipped_to_match_spy(self):
        view, scope, evidence = self.prepare()
        anchor = next(s for s in evidence.snapshots if s.semantics['security_identity'] == 'security:ABC')
        original = anchor.semantics['calendar']
        extra = {'session_date': '2025-07-04', 'open_at': ms('2025-07-04T09:30:00-04:00'),
                 'close_at': ms('2025-07-04T16:00:00-04:00')}
        calendar = {**original, 'sessions': [original['sessions'][0], extra, *original['sessions'][1:]]}
        run = self.run_outcomes(view, scope, update_bar(evidence, 'security:ABC', 0, calendar=calendar))
        self.assertEqual(run['outcomes'][0]['availability'], 'available')
        for outcome in run['outcomes'][1:]:
            self.assertIn('sessions_incompatible', outcome['reasons'])
            self.assertIsNone(outcome['metrics']['security_gross']['value'])
            self.assertIsNone(outcome['metrics']['benchmark_relative_log']['value'])
            self.assertEqual(outcome['metrics']['benchmark_gross']['availability'], 'available')

    def test_actions_between_regular_sessions_cannot_be_silently_ignored(self):
        view, scope, evidence = self.prepare()
        for kind in ('split', 'cash_distribution', 'non_cash', 'merger', 'spin_off', 'delisting', 'listing_change', 'terminal_event'):
            with self.subTest(kind=kind):
                terms = {'ratio': '2:1'} if kind == 'split' else {'amount': 2} if kind == 'cash_distribution' else {'description': 'unresolved'}
                units = 'USD/share' if kind == 'cash_distribution' else 'shares'
                changed = update_bar(evidence, 'security:ABC', 0,
                    corporate_actions=[action(kind, '2025-07-04', terms, units=units)])
                run = self.run_outcomes(view, scope, changed)
                self.assertEqual(run['outcomes'][0]['availability'], 'available')
                for outcome in run['outcomes'][1:]:
                    self.assertIn('action_session_unresolved:' + kind + ':2025-07-04', outcome['reasons'])
                    self.assertIsNone(outcome['metrics']['security_gross']['value'])
                    self.assertEqual(outcome['metrics']['benchmark_gross']['availability'], 'available')


if __name__ == '__main__':
    unittest.main()
