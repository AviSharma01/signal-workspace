"""#33 acceptance through the retained-outcome deterministic application seam."""
import unittest
from copy import deepcopy
import random
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch

from analysis import canonical
from cohort_analysis import (
    CohortAnalysisApplication, V1_METHOD_VERSION, episode_interval, observations, report, summarize,
)
from tests import test_analysis as outcomes_fixture


def retained_run(specs):
    """Compact, isolated #32 output contract; no prices or return engine."""
    events, outcomes, filings = [], [], []
    for index, spec in enumerate(specs):
        member, value = spec[:2]
        day = spec[2] if len(spec) > 2 else '2025-07-03'
        security = spec[3] if len(spec) > 3 else 'security:ABC'
        direction = spec[4] if len(spec) > 4 else 'purchase'
        event_id, filing_id, version = f'event:{index:04}', f'filing:{index:04}', f'version:{index:04}'
        open_at = int(datetime.fromisoformat(day + 'T09:30:00').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)
        anchor = {'session_date': day, 'open_at': open_at, 'close_at': open_at + 23400000}
        fields = {'transactionDirection': direction, 'assetClass': 'individual_public_equity'}
        events.append({'id': event_id, 'status': 'event', 'chamber': 'house',
            'intrinsicBoundary': 0, 'anchor': anchor, 'occurrenceIds': [f'row:{index}'],
            'intrinsicState': {'fields': fields, 'identities': {
                'member': {'status': 'resolved', 'identity': {'identity_id': member}},
                'security': {'status': 'resolved', 'identity': {'identity_id': security}}}},
            'eligibility': {'primary_analysis': {'eligible': True, 'reasons': []}},
            'provenance': {'normalization': {'rowOccurrenceId': f'row:{index}'}, 'rows': [{
                'occurrenceId': f'row:{index}', 'artifactVersionId': version,
                'sourceAuthority': 'official', 'sourceFiling': {'id': filing_id},
                'rawFields': {'ticker': 'ABC'}}]}})
        filings.append({'artifactVersionId': version, 'sourceFiling': {'id': filing_id},
            'sourceRole': 'official', 'reportedRowOccurrences': 1,
            'interpretableEquityOccurrences': 1, 'resolvedSecurities': 1,
            'unresolvedSecurityOccurrences': 0, 'literalSourceTickerStrings': 1,
            'literalTickerMinimum': 1, 'literalTickerCompleteness': 'complete',
            'completeness': 'complete'})
        for horizon in (1, 5, 20, 60):
            outcomes.append({'event_id': event_id, 'horizon_sessions': horizon,
                'direction': direction, 'anchor': anchor, 'event_boundary': 0, 'outcome_boundary': 2,
                'metrics': {'direction_aligned_log': {'value': value,
                    'availability': 'available' if value is not None else 'unavailable',
                    'reasons': [] if value is not None else ['missing_bar', 'currency_unresolved']}},
                'security_snapshots': [{'id': 'snapshot:security', 'revision': '1'}],
                'benchmark_snapshots': [{'id': 'snapshot:SPY', 'revision': '1'}]})
    return {'id': 'retained-32', 'population': 'test', 'production_ready': False,
        'readiness_scope': 'toy', 'readiness': {'availability': 'available'},
        'method_version': 'event-outcomes@1', 'market_contract_version': 'contract@1',
        'calculated_at': 10, 'as_of': 5, 'perspective': 'public_information',
        'market_input_id': 'retained-snapshots', 'event_view_id': 'view:one',
        'event_input': {'methodVersion': 'event-pit@1', 'mode': 'original', 'events': events,
            'coverage': {'retainedOccurrences': len(events), 'filings': filings, 'reasonCounts': {},
                'readiness': {'house': {'availability': 'available'}, 'senate': {'availability': 'unavailable'}},
                'panelComplete': False}}, 'outcomes': outcomes}


def primary(report, cohort='combined', horizon=20):
    return next(item for item in report['results'] if item['cohort'] == cohort and item['horizon_sessions'] == horizon)


def sparse_episode_run():
    # Twelve observed months paired into six actual New York calendar weeks.
    # All dates are weekdays; each member/security supplies its own episode.
    days = ['2018-01-31', '2018-02-01', '2019-02-28', '2019-03-01',
            '2020-03-31', '2020-04-01', '2021-06-30', '2021-07-01',
            '2022-08-31', '2022-09-01', '2023-11-30', '2023-12-01']
    return retained_run([(f'm{i:02}', 1., days[i % 12], f's{i:02}', 'purchase') for i in range(30)])


class CohortTest(unittest.TestCase):
    def test_empty_draws_continue_to_10000_valid_episode_estimates(self):
        source = sparse_episode_run()
        result = primary(summarize(source))
        self.assertEqual(result['sample']['members'], 30)
        self.assertEqual(result['sample']['episodes'], 30)
        self.assertEqual(result['sample']['anchor_months'], 12)
        self.assertEqual(result['episode']['interval'], [1., 1.])
        attempts = result['bootstrap']['episode_resampling']
        self.assertEqual(attempts['requested_valid_replicates'], 10000)
        self.assertEqual(attempts['valid_replicates'], 10000)
        self.assertGreater(attempts['empty_draws'], 0)
        self.assertEqual(attempts['total_draw_attempts'], 10000 + attempts['empty_draws'])
        self.assertEqual(attempts['status'], 'complete')
        reordered = deepcopy(source)
        reordered['outcomes'].reverse()
        reordered['event_input']['events'].reverse()
        reordered['event_input']['coverage']['filings'].reverse()
        reversed_result = report(observations(reordered, 20), 'combined', 20)
        self.assertEqual(reversed_result['bootstrap'], result['bootstrap'])
        self.assertEqual(reversed_result['episode'], result['episode'])

    def test_original_86_empty_audit_draws_continue_same_stream_without_zero_estimators(self):
        source = sparse_episode_run()
        original = report(observations(source, 20), 'combined', 20, method_version=V1_METHOD_VERSION)
        self.assertEqual(original['bootstrap']['empty_episode_replicates'], 86)
        self.assertEqual(original['bootstrap']['seed'], '3282888945663694336')
        # Independent reference: six occupied weeks over 305 calendar weeks.
        weeks = [[] for _ in range(305)]
        for day in ('2018-01-31', '2019-02-28', '2020-03-31', '2021-06-30', '2022-08-31', '2023-11-30'):
            value = date.fromisoformat(day)
            monday = value - timedelta(days=value.weekday())
            weeks[(monday - date(2018, 1, 29)).days // 7] = [1.]
        bounds, attempts = episode_interval(weeks, original['bootstrap']['seed'])
        self.assertEqual(bounds, [1., 1.])
        self.assertEqual(attempts['requested_valid_replicates'], 10000)
        self.assertEqual(attempts['valid_replicates'], 10000)
        self.assertEqual(attempts['total_draw_attempts'], 10088)
        self.assertEqual(attempts['empty_draws'], 88)
        self.assertEqual(sum(i <= 10000 for i in attempts['empty_draw_indices']), 86)
        self.assertEqual(attempts['empty_draw_indices'][:5], [49, 52, 257, 414, 596])
        self.assertEqual(attempts['empty_draw_indices'][-5:], [9792, 9808, 9951, 10019, 10068])
        self.assertEqual(episode_interval(weeks, original['bootstrap']['seed']), (bounds, attempts))

    def test_numerically_zero_estimates_are_valid_but_empty_draws_have_no_value(self):
        # Many all-empty resamples: inserting zero for them would move the lower
        # percentile of the +1 fixture to zero. Legitimate zero outcomes remain valid.
        positive = [[] for _ in range(12)]
        positive[0] = [1.]
        bounds, attempts = episode_interval(positive, '17')
        self.assertEqual(bounds, [1., 1.])
        self.assertGreater(attempts['empty_draws'], 2500)
        self.assertEqual(attempts['valid_replicates'], 10000)
        zeros = [[] for _ in range(12)]
        zeros[0] = [0.]
        zero_bounds, zero_attempts = episode_interval(zeros, '17')
        self.assertEqual(zero_bounds, [0., 0.])
        self.assertEqual(zero_attempts, attempts)

    def test_draw_attempt_safeguard_withholds_interval_and_retains_supported_points(self):
        source = sparse_episode_run()
        result = primary(summarize(source, episode_draw_limit=7))
        self.assertIsNone(result['episode']['interval'])
        self.assertEqual(result['episode']['value'], 1.)
        self.assertEqual(result['episode']['interval_reasons'], ['episode_bootstrap_draw_attempt_limit_reached'])
        counts = result['bootstrap']['episode_resampling']
        self.assertEqual(counts['max_draw_attempts'], 7)
        self.assertEqual(counts['total_draw_attempts'], 7)
        self.assertLess(counts['valid_replicates'], 10000)
        self.assertEqual(counts['valid_replicates'] + counts['empty_draws'], 7)
        self.assertEqual(counts['status'], 'attempt_limit_reached')
        self.assertEqual(primary(summarize(source, episode_draw_limit=7)), result)

    def test_event_weighting_member_balance_and_episode_estimates_remain_descriptive(self):
        result = primary(summarize(retained_run([('a', .1), ('a', .1), ('a', .1), ('b', -.2)])))
        self.assertAlmostEqual(result['event_weighted']['value'], .025)
        self.assertAlmostEqual(result['member_balanced']['value'], -.05)
        self.assertAlmostEqual(result['episode']['value'], .025)
        self.assertTrue(result['sign_disagreement'])
        self.assertIsNone(result['event_weighted']['interval'])
        self.assertEqual(result['sample']['members'], 2)
        self.assertEqual(result['sample']['episodes'], 1)

    def test_cluster_bootstrap_repeats_complete_members_and_shares_balanced_resamples(self):
        # One member reports 10 values of +1; 29 report one value of -1 each.
        run = retained_run([('a', 1.)] * 10 + [(f'm{i:02}', -1.) for i in range(29)])
        result = primary(summarize(run))
        self.assertAlmostEqual(result['event_weighted']['value'], -19 / 39)
        self.assertAlmostEqual(result['member_balanced']['value'], -28 / 30)
        seed = result['bootstrap']['seed']
        self.assertEqual(result['bootstrap']['replicates'], 10000)
        rng = random.Random(int(seed))
        weighted, balanced = [], []
        for _ in range(10000):
            prolific = [rng.randrange(30) for _ in range(30)].count(0)
            weighted.append((11 * prolific - 30) / (9 * prolific + 30))
            balanced.append((2 * prolific - 30) / 30)
        def bounds(values):
            values.sort()
            # Explicit independently worked positions for N=10,000, linear percentiles.
            return [values[249] * .025 + values[250] * .975,
                    values[9749] * .975 + values[9750] * .025]
        for actual, expected in zip(result['event_weighted']['interval'], bounds(weighted)):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(result['member_balanced']['interval'], bounds(balanced)):
            self.assertAlmostEqual(actual, expected)
        self.assertIsNone(result['episode']['interval'])
        self.assertIn('fewer_than_12_anchor_months', result['episode']['interval_reasons'])

    def test_episodes_separate_security_direction_session_and_block_weeks_include_gaps(self):
        specs = []
        # 30 members, 48 episodes across 12 months; unequal episodes per week.
        for month in range(1, 13):
            for j in range(4):
                specs.append((f'm{(month * 4 + j) % 30:02}', float(month),
                              f'2025-{month:02}-' + ('12' if month == 12 else '06'), f'security:{j}', 'purchase'))
        specs += [('extra', 100., '2025-01-06', 'security:0', 'purchase')]
        result = primary(summarize(retained_run(specs)))
        self.assertEqual(result['sample']['episodes'], 48)
        # Jan's first episode is (1+100)/2=50.5, the other 47 retain their values.
        self.assertAlmostEqual(result['episode']['value'], 361.5 / 48)
        manifest = result['bootstrap']['week_range']
        self.assertEqual(manifest['start'], '2025-01-06')
        self.assertEqual(manifest['end'], '2025-12-08')
        self.assertEqual(manifest['weeks'], 49)
        rng = random.Random(int(result['bootstrap']['seed']))
        weeks = [[] for _ in range(49)]
        for month in range(1, 13):
            day = date(2025, month, 12 if month == 12 else 6)
            week = day - timedelta(days=day.weekday())
            index = (week - date(2025, 1, 6)).days // 7
            weeks[index] = [50.5, 1., 1., 1.] if month == 1 else [float(month)] * 4
        replicates = []
        for _ in range(10000):
            indices = []
            while len(indices) < 49:
                start = rng.randrange(46)
                indices.extend(range(start, start + 4))
            values = [v for index in indices[:49] for v in weeks[index]]
            replicates.append(sum(values) / len(values))
        replicates.sort()
        expected = [replicates[249] * .025 + replicates[250] * .975,
                    replicates[9749] * .975 + replicates[9750] * .025]
        for actual, value in zip(result['episode']['interval'], expected):
            self.assertAlmostEqual(actual, value)
        separated = primary(summarize(retained_run([
            ('a', 1., '2025-01-06', 's', 'purchase'),
            ('b', 3., '2025-01-06', 's', 'purchase'),
            ('c', -4., '2025-01-06', 's', 'sale'),
            ('d', 8., '2025-01-07', 's', 'purchase'),
            ('e', 10., '2025-01-06', 'other', 'purchase')])))
        self.assertEqual(separated['sample']['episodes'], 4)
        self.assertEqual(separated['episode']['value'], 4.)

    def test_fixed_cohorts_filing_size_missingness_dimensions_and_neutral_language(self):
        run = retained_run([('a', 0.), ('b', -.1), ('c', None), ('d', .2, '2024-01-08', 's', 'sale')])
        run['event_input']['coverage']['filings'][1].update(literalSourceTickerStrings=15, literalTickerMinimum=15)
        run['event_input']['coverage']['filings'][2]['completeness'] = 'partial'
        result = summarize(run)
        combined = primary(result)
        self.assertEqual(combined['sample']['events'], 4)
        self.assertEqual(combined['sample']['outcome_available'], 3)
        self.assertEqual(combined['sample']['missing'], 1)
        self.assertEqual(combined['missingness']['reason_counts'], {'currency_unresolved': 1, 'missing_bar': 1})
        self.assertEqual(combined['sample']['source_filings'], 3)
        self.assertEqual(combined['sample']['securities'], 2)
        self.assertEqual(combined['sample']['anchor_sessions'], 2)
        self.assertEqual(combined['sample']['anchor_months'], 2)
        self.assertEqual(combined['missingness']['field_missingness']['reason_counts'],
                         {'amount_range_unresolved': 4, 'transaction_date_missing': 4})
        for group in ('purchase', 'sale', 'house', 'year:2024', 'year:2025',
                      'filing_size:lt15', 'filing_size:ge15', 'filing_size:indeterminate',
                      'outcome:available', 'outcome:missing'):
            self.assertIsNotNone(primary(result, group))
        self.assertEqual(primary(result, 'filing_size:ge15')['sample']['events'], 1)
        self.assertEqual(primary(result, 'filing_size:indeterminate')['sample']['events'], 1)
        self.assertEqual(primary(result, 'outcome:missing')['event_weighted']['availability'], 'unavailable')
        self.assertIn('descriptive', combined['interpretation'])
        self.assertEqual(result['coverage']['chamber_label'], 'House-only readiness')
        self.assertTrue(result['coverage']['exploratory'])
        self.assertEqual(result['consensus']['availability'], 'unavailable')
        self.assertEqual(result['flow']['windows'][2]['final_denominator'], 3)
        for dimension in combined['coverage_dimensions'].values():
            self.assertEqual(sum(v['events'] for v in dimension.values()), 4)
            self.assertEqual(sum(v['available'] for v in dimension.values()), 3)
        zero = primary(summarize(retained_run([('a', 0.)])))
        self.assertFalse(zero['sign_disagreement'])
        self.assertIn('zero', zero['interpretation'].lower())

    def test_thresholds_apply_to_each_cohort_and_outcome_available_members(self):
        report = summarize(retained_run([(f'p{i}', 0., '2025-07-03', 's', 'purchase') for i in range(29)]
                                       + [(f's{i}', 0., '2025-07-03', 's', 'sale') for i in range(29)]))
        self.assertEqual(primary(report)['event_weighted']['interval'], [0., 0.])
        self.assertIn('null/inconclusive', primary(report)['interpretation'])
        self.assertIsNone(primary(report, 'purchase')['event_weighted']['interval'])
        missing = primary(summarize(retained_run([(f'm{i}', 1.) for i in range(29)] + [('missing', None)])))
        self.assertEqual(missing['population_dimensions']['members'], 30)
        self.assertEqual(missing['sample']['members'], 29)
        self.assertIsNone(missing['member_balanced']['interval'])

    def test_row_order_invariance_retained_seed_and_no_mutation(self):
        run = retained_run([(f'm{i}', float(i % 3 - 1)) for i in range(30)])
        original = deepcopy(run)
        first = summarize(run)
        reordered = deepcopy(run)
        reordered['outcomes'].reverse()
        reordered['event_input']['events'].reverse()
        reordered['event_input']['coverage']['filings'].reverse()
        second = summarize(reordered)
        self.assertEqual(first, second)
        self.assertEqual(run, original)
        changed = deepcopy(run)
        changed['outcomes'][2]['metrics']['direction_aligned_log']['value'] = 7.
        self.assertNotEqual(primary(first)['bootstrap']['seed'], primary(summarize(changed))['bootstrap']['seed'])

    def test_sign_disagreement_has_no_magnitude_cutoff_and_zero_has_no_sign(self):
        result = primary(summarize(retained_run([('a', 1e-20)] * 3 + [('b', -2e-20)])))
        self.assertTrue(result['sign_disagreement'])
        self.assertFalse(primary(summarize(retained_run([('a', 0.), ('b', 1e-20)])))['sign_disagreement'])

    def test_incomplete_and_conflicting_filings_do_not_exclude_primary_events(self):
        run = retained_run([('a', .1), ('b', .2), ('c', .3)])
        run['event_input']['coverage']['filings'][0].update(completeness='partial', literalSourceTickerStrings=20)
        run['event_input']['coverage']['filings'][1].update(literalTickerCompleteness='indeterminate', literalSourceTickerStrings=None)
        report = summarize(run)
        self.assertEqual(primary(report)['sample']['outcome_available'], 3)
        self.assertEqual(primary(report, 'filing_size:indeterminate')['sample']['events'], 2)
        self.assertAlmostEqual(primary(report)['event_weighted']['value'], .2)

    def test_duplicate_or_incomplete_upstream_outputs_are_rejected_without_repair(self):
        for mutate in (lambda r: r['outcomes'].append(deepcopy(r['outcomes'][0])),
                       lambda r: r['outcomes'].pop(),
                       lambda r: r['outcomes'][0].update(direction='sale')):
            run = retained_run([('a', 0.)])
            mutate(run)
            with self.assertRaises(ValueError):
                summarize(run)

    def test_anchor_failure_retains_supported_publication_year_and_missingness(self):
        run = retained_run([('a', None)])
        event = run['event_input']['events'][0]
        event['anchor'] = None
        event['publication'] = {'selectedEvidenceId': 'publication:one',
            'evidence': [{'id': 'publication:one', 'raw_value': '2024-12-31T23:00:00-05:00'}]}
        for outcome in run['outcomes']:
            outcome['anchor'] = None
        result = summarize(run)
        self.assertEqual(primary(result, 'year:2024')['sample']['events'], 1)
        self.assertEqual(primary(result, 'year:2024')['sample']['missing'], 1)
        self.assertEqual(primary(result)['coverage_dimensions']['year']['2024']['events'], 1)

    def test_house_only_readiness_blocks_senate_estimation_without_losing_retained_flow(self):
        run = retained_run([('house', 1.), ('senate', -10.)])
        run['event_input']['events'][1]['chamber'] = 'senate'
        report = summarize(run)
        result = primary(report)
        self.assertEqual(result['event_weighted']['value'], 1.)
        self.assertEqual(result['sample']['events'], 2)
        self.assertEqual(result['sample']['outcome_available'], 1)
        self.assertEqual(result['sample']['retained_outcome_available'], 2)
        self.assertEqual(result['missingness']['reason_counts'], {'disclosure_chamber_not_ready:senate': 1})
        self.assertEqual(result['coverage_dimensions']['chamber']['senate'], {'events': 1, 'available': 0, 'missing': 1})
        window = report['flow']['windows'][2]
        self.assertEqual(window['completed_windows'], 2)
        self.assertEqual(window['readiness_blocked'], 1)
        self.assertEqual(window['final_denominator'], 1)
        run['event_input']['coverage']['readiness']['senate']['availability'] = 'available'
        both = summarize(run)
        self.assertEqual(primary(both)['event_weighted']['value'], -4.5)
        self.assertEqual(primary(both, 'senate')['event_weighted']['value'], -10.)

    def test_episode_thresholds_at_30_members_30_episodes_and_12_months(self):
        specs = [(f'm{i:02}', 1., f'2025-{i % 12 + 1:02}-06', f's{i}', 'purchase') for i in range(30)]
        at_threshold = primary(summarize(retained_run(specs)))
        self.assertEqual(at_threshold['sample']['members'], 30)
        self.assertEqual(at_threshold['sample']['episodes'], 30)
        self.assertEqual(at_threshold['sample']['anchor_months'], 12)
        self.assertEqual(at_threshold['episode']['interval'], [1., 1.])
        eleven_months = [(m, v, '2025-11-06' if day == '2025-12-06' else day, s, d) for m, v, day, s, d in specs]
        below_months = primary(summarize(retained_run(eleven_months)))
        self.assertIsNone(below_months['episode']['interval'])
        self.assertEqual(below_months['episode']['value'], 1.)
        self.assertEqual(below_months['episode']['interval_reasons'], ['fewer_than_12_anchor_months'])
        twenty_nine_episodes = specs[:-1] + [('m29', 1., specs[0][2], specs[0][3], 'purchase')]
        below_episodes = primary(summarize(retained_run(twenty_nine_episodes)))
        self.assertEqual(below_episodes['sample']['members'], 30)
        self.assertEqual(below_episodes['sample']['episodes'], 29)
        self.assertIsNone(below_episodes['episode']['interval'])
        self.assertEqual(below_episodes['episode']['interval_reasons'], ['fewer_than_30_episodes'])

    def test_independent_distribution_golden_and_empty_run(self):
        result = primary(summarize(retained_run([('a', -3.), ('b', -1.), ('c', 1.), ('d', 5.)])))
        self.assertEqual(result['distribution'], {'median': 0., 'q1': -1.5, 'q3': 2., 'iqr': 3.5})
        empty = primary(summarize(retained_run([])))
        for key in ('event_weighted', 'member_balanced', 'episode'):
            self.assertIsNone(empty[key]['value'])
            self.assertIsNone(empty[key]['interval'])
        self.assertEqual(empty['sample']['events'], 0)
        self.assertIn('unavailable', empty['interpretation'])


class CohortApplicationTest(unittest.TestCase):
    def setUp(self):
        self.fixture = outcomes_fixture.AnalysisTest()
        self.fixture.setUp()
        self.application = CohortAnalysisApplication(self.fixture.fixture.connection, lambda: self.fixture.fixture.now)

    def tearDown(self):
        self.fixture.tearDown()

    def test_retained_empty_draw_provenance_and_both_method_versions_reproduce(self):
        # Retained-output contract fixture in an isolated test DB; no price inputs.
        source = sparse_episode_run()
        source['readiness']['evidence_class'] = 'synthetic'
        with self.fixture.fixture.connection() as conn:
            conn.execute('INSERT INTO analysis_market_inputs VALUES (?, ?, ?, ?)',
                         (source['market_input_id'], 'test', 'synthetic', '{}'))
            conn.execute('INSERT INTO analysis_runs VALUES (?, ?, ?, ?, ?, ?)',
                         (source['id'], 'test', source['readiness_scope'], source['market_input_id'],
                          source['calculated_at'], canonical(source)))
        with patch.dict('analysis.METHODS', {'event-outcomes@1': lambda *args: self.fail('market recalculation')}):
            with patch('cohort_analysis.METHOD_VERSION', V1_METHOD_VERSION):
                old = self.application.execute(population='test', source_run_id=source['id'])['runs'][0]
            current = self.application.execute(population='test', source_run_id=source['id'])['runs'][0]
            self.assertEqual(old['method_version'], 'cohort-analysis@1')
            self.assertIsNone(primary(old['report'])['episode']['interval'])
            self.assertEqual(primary(old['report'])['bootstrap']['empty_episode_replicates'], 86)
            self.assertEqual(current['method_version'], 'cohort-analysis@2')
            self.assertEqual(current['report']['method_contract']['episode_max_draw_attempts'], 50000)
            result = primary(current['report'])
            self.assertEqual(result['episode']['interval'], [1., 1.])
            counts = result['bootstrap']['episode_resampling']
            self.assertEqual(counts['valid_replicates'], 10000)
            self.assertEqual(counts['total_draw_attempts'], 10094)
            self.assertEqual(counts['empty_draws'], 94)
            self.assertEqual(len(counts['empty_draw_indices']), 94)
            self.assertEqual(self.application.get_run(current['id'], population='test'), current)
            with patch('cohort_analysis.METHOD_VERSION', 'future-default@3'):
                for recorded in (old, current):
                    reproduced = self.application.reproduce(recorded['id'], population='test')['output']
                    self.assertEqual(reproduced, recorded)
            self.assertEqual(self.fixture.analysis.get_run(source['id'], population='test'), source)

    def test_retained_execution_safeguard_reproduces_failure_counts(self):
        source = sparse_episode_run()
        source['readiness']['evidence_class'] = 'synthetic'
        with self.fixture.fixture.connection() as conn:
            conn.execute('INSERT INTO analysis_market_inputs VALUES (?, ?, ?, ?)',
                         (source['market_input_id'], 'test', 'synthetic', '{}'))
            conn.execute('INSERT INTO analysis_runs VALUES (?, ?, ?, ?, ?, ?)',
                         (source['id'], 'test', source['readiness_scope'], source['market_input_id'],
                          source['calculated_at'], canonical(source)))
        # Inject the smaller statistical-seam test limit; HTTP has no override.
        with patch.dict('cohort_analysis.METHODS', {
                'cohort-analysis@2': lambda source: summarize(source, episode_draw_limit=7)}):
            recorded = self.application.execute(population='test', source_run_id=source['id'])['runs'][0]
        result = primary(recorded['report'])
        self.assertIsNone(result['episode']['interval'])
        self.assertEqual(result['bootstrap']['episode_resampling']['total_draw_attempts'], 7)
        self.assertEqual(recorded['report']['method_contract']['episode_max_draw_attempts'], 7)
        # Reproduction uses the recorded limit rather than today's 50,000 default.
        self.assertEqual(self.application.reproduce(recorded['id'], population='test')['output'], recorded)

    def test_immutable_versioned_runs_reproduce_retained_outputs_without_market_recalculation(self):
        view, scope, evidence = self.fixture.prepare()
        upstream = self.fixture.run_outcomes(view, scope, evidence)
        # A guard against crossing the expressly forbidden #32 calculation boundary.
        with patch.dict('analysis.METHODS', {'event-outcomes@1': lambda *args: self.fail('market recalculation')}):
            first = self.application.execute(population='test', source_run_id=upstream['id'])['runs'][0]
            second = self.application.execute(population='test', source_run_id=upstream['id'])['runs'][0]
            self.assertNotEqual(first['id'], second['id'])
            self.assertEqual(first['report'], second['report'])
            self.assertEqual(first['input_digest'], second['input_digest'])
            self.assertEqual(self.application.reproduce(first['id'], population='test')['output'], first)
        self.assertFalse(first['production_ready'])
        self.assertEqual(first['source_input'], upstream)
        self.assertEqual(len(self.application.query(population='test')['runs']), 2)
        self.assertEqual(self.application.query(population='real')['runs'], [])
        with patch('cohort_analysis.production_market_readiness', return_value={
                'availability': 'available', 'evaluation_scope': 'production'}):
            with self.assertRaises(KeyError):
                self.application.execute(population='real', source_run_id=upstream['id'])
        with self.assertRaises(KeyError):
            self.application.get_run(first['id'], population='real')
        self.assertEqual(self.fixture.analysis.get_run(upstream['id'], population='test'), upstream)
        with patch('cohort_analysis.METHOD_VERSION', 'future-default@2'):
            self.assertEqual(self.application.reproduce(first['id'], population='test')['output'], first)
        with patch.dict('cohort_analysis.METHODS', {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'method version unavailable'):
                self.application.reproduce(first['id'], population='test')

    def test_production_refuses_without_readiness_and_cannot_select_test_inputs(self):
        response = self.application.execute(population='real', source_run_id='missing')
        self.assertEqual(response['capability']['availability'], 'unavailable')
        self.assertEqual(response['result']['state'], 'error')
        self.assertEqual(response['runs'], [])


if __name__ == '__main__':
    unittest.main()
