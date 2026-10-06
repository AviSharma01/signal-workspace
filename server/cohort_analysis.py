"""Deterministic #33 reporting over immutable #32 outputs, never market prices."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
from functools import partial
from math import fsum, isfinite
import random
import json
import time
import uuid
from zoneinfo import ZoneInfo

from analysis import AnalysisApplication, HORIZONS, canonical, digest, disclosure_flow
from capabilities import result_state
from market_conformance import production_market_readiness

V1_METHOD_VERSION = 'cohort-analysis@1'
V2_METHOD_VERSION = 'cohort-analysis@2'
METHOD_VERSION = V2_METHOD_VERSION
REPLICATES = 10000
MAX_EPISODE_DRAW_ATTEMPTS = 50000
MIN_MEMBERS = 30
MIN_EPISODES = 30
MIN_MONTHS = 12
V1_METHOD_CONTRACT = {
    'version': V1_METHOD_VERSION, 'primary_horizon_sessions': 20,
    'supporting_horizons_sessions': [1, 5, 60], 'replicates': REPLICATES,
    'minimum_reporting_members': MIN_MEMBERS, 'minimum_episodes': MIN_EPISODES,
    'minimum_anchor_months': MIN_MONTHS, 'block_calendar_weeks': 4,
    'week_timezone': 'America/New_York', 'week_definition': 'Monday_through_Sunday',
    'primary_weighting': 'one_equal_weight_per_available_eligible_Event',
    'member_weighting': 'within_member_Event_mean_then_equal_member_mean',
    'episode_weighting': 'within_security_source_direction_anchor_session_mean_then_equal_episode_mean',
    'cohort_definitions': {
        'combined': 'all_retained_primary_disclosure_eligible_Events_from_ready_chambers_without_filing_size_exclusion',
        'purchase_sale': 'frozen_source_direction_separate_not_netted',
        'chamber': 'retained_chamber_strata_when_each_chamber_ready',
        'year': 'anchor_session_or_supported_source_local_publication_year',
        'outcome': 'descriptive_available_missing_strata_by_retained_aligned_metric',
        'filing_size': 'original_official_artifact_distinct_literal_tickers_lt15_ge15_indeterminate_sensitivity_only'},
    'sign_disagreement': 'strict_positive_and_strict_negative_across_supported_estimates_zero_has_no_direction',
    'supporting_intervals': 'descriptive_unadjusted_for_multiple_comparisons',
}
METHOD_CONTRACT = {**deepcopy(V1_METHOD_CONTRACT), 'version': V2_METHOD_VERSION,
    'episode_empty_draw_policy': 'undefined_estimator_record_invalid_draw_continue_same_stream_until_requested_valid_count',
    'episode_requested_valid_replicates': REPLICATES,
    'episode_max_draw_attempts': MAX_EPISODE_DRAW_ATTEMPTS,
    'episode_attempt_limit_reason': 'episode_bootstrap_draw_attempt_limit_reached',
    'approval': 'docs/specs/cohort-empty-bootstrap-33.md'}


def mean(values):
    return fsum(values) / len(values) if values else None


def estimate(value, reasons=()):
    return {'value': value, 'availability': 'available' if value is not None else 'unavailable',
            'interval': None, 'interval_reasons': list(reasons)}


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    index = int(position)
    weight = position - index
    return ordered[index] * (1 - weight) + ordered[min(index + 1, len(ordered) - 1)] * weight


def interval(values):
    return [percentile(values, .025), percentile(values, .975)]


def bootstrap_manifest(rows, cohort, horizon, method_version):
    inputs = {'method_version': method_version, 'cohort': cohort, 'horizon_sessions': horizon,
              'ordered_inputs': [[r['event_id'], r['member'], r['security'], r['direction'], r['day'],
                                  r['outcome']['anchor']['open_at'], r['value']]
                                 for r in rows]}
    return {'seed': str(int(digest(inputs)[:16], 16)), 'seed_encoding': 'unsigned_64_bit_decimal_string', 'derivation_inputs': inputs,
            'derivation': 'sha256_canonical_json_first_64_bits', 'replicates': REPLICATES,
            'generator': 'python_random_MT19937_integer_seed_randrange@1',
            'percentile': 'linear_interpolation_(n-1)p', 'confidence': .95,
            'member_method': 'complete_reporting_member_clusters_with_replacement',
            'episode_method': 'overlapping_four_calendar_week_blocks_with_replacement',
            'member_replicates_executed': 0, 'episode_replicates_executed': 0}


def member_intervals(members, seed):
    clusters = [members[key] for key in sorted(members)]
    totals = [fsum(values) for values in clusters]
    sizes = [len(values) for values in clusters]
    means = [mean(values) for values in clusters]
    rng = random.Random(int(seed))
    weighted, balanced = [], []
    for _ in range(REPLICATES):
        indices = [rng.randrange(len(clusters)) for _ in clusters]
        weighted.append(fsum(totals[i] for i in indices) / sum(sizes[i] for i in indices))
        balanced.append(mean([means[i] for i in indices]))
    return interval(weighted), interval(balanced)


def anchor_week(open_at):
    value = datetime.fromtimestamp(open_at / 1000, ZoneInfo('America/New_York')).date()
    return value - timedelta(days=value.weekday())


def episode_weeks(episodes, anchors):
    grouped = defaultdict(list)
    for key in sorted(episodes):
        grouped[anchor_week(anchors[key])].append(mean(episodes[key]))
    if not grouped:
        return [], {'start': None, 'end': None, 'weeks': 0, 'timezone': 'America/New_York'}
    start, end = min(grouped), max(grouped)
    count = (end - start).days // 7 + 1
    return [grouped[start + timedelta(weeks=i)] for i in range(count)], {
        'start': start.isoformat(), 'end': end.isoformat(), 'weeks': count,
        'timezone': 'America/New_York', 'empty_weeks': count - len(grouped),
        'overlapping_blocks': max(0, count - 3)}


def episode_interval_v1(weeks, seed):
    """Archived unapproved suppression behavior, solely for retained v1 reproduction."""
    rng = random.Random(int(seed))
    totals = [fsum(values) for values in weeks]
    sizes = [len(values) for values in weeks]
    replicates, empty = [], 0
    for _ in range(REPLICATES):
        indices = []
        while len(indices) < len(weeks):
            start = rng.randrange(len(weeks) - 3)
            indices.extend(range(start, start + 4))
        indices = indices[:len(weeks)]
        count = sum(sizes[i] for i in indices)
        if count:
            replicates.append(fsum(totals[i] for i in indices) / count)
        else:
            empty += 1
    # Never turn an empty resample into zero or silently redraw/select replicates.
    return (interval(replicates) if not empty else None), empty


def episode_interval(weeks, seed, *, max_draw_attempts=MAX_EPISODE_DRAW_ATTEMPTS):
    """Approved valid-estimate bootstrap; cap attempts without changing the stream."""
    if type(max_draw_attempts) is not int or not 1 <= max_draw_attempts <= MAX_EPISODE_DRAW_ATTEMPTS:
        raise ValueError('Episode draw safeguard must be between 1 and 50000 attempts')
    rng = random.Random(int(seed))
    totals = [fsum(values) for values in weeks]
    sizes = [len(values) for values in weeks]
    replicates, empty_indices, attempts = [], [], 0
    while len(replicates) < REPLICATES and attempts < max_draw_attempts:
        attempts += 1
        indices = []
        while len(indices) < len(weeks):
            start = rng.randrange(len(weeks) - 3)
            indices.extend(range(start, start + 4))
        indices = indices[:len(weeks)]
        count = sum(sizes[i] for i in indices)
        if count:
            replicates.append(fsum(totals[i] for i in indices) / count)
        else:
            empty_indices.append(attempts)
    complete = len(replicates) == REPLICATES
    return (interval(replicates) if complete else None), {
        'requested_valid_replicates': REPLICATES, 'max_draw_attempts': max_draw_attempts,
        'total_draw_attempts': attempts, 'valid_replicates': len(replicates),
        'empty_draws': len(empty_indices), 'empty_draw_indices': empty_indices,
        'empty_draw_index_basis': 'one_based_draw_attempt',
        'status': 'complete' if complete else 'attempt_limit_reached'}


def observations(run, horizon):
    events = {event['id']: event for event in run['event_input']['events']}
    if len(events) != len(run['event_input']['events']):
        raise ValueError('Duplicate retained Event identity')
    outcomes = run['outcomes']
    keys = [(o['event_id'], o['horizon_sessions']) for o in outcomes]
    if len(set(keys)) != len(keys) or set(keys) != {(key, h) for key in events for h in HORIZONS}:
        raise ValueError('Retained outcomes must contain exactly one row per Event and horizon')
    filings = {item['artifactVersionId']: item for item in run['event_input']['coverage']['filings']}
    rows = []
    for outcome in sorted(run['outcomes'], key=lambda item: (item['event_id'], item['horizon_sessions'])):
        if outcome['horizon_sessions'] != horizon:
            continue
        event = events[outcome['event_id']]
        intrinsic = event['intrinsicState']
        member = intrinsic['identities']['member']['identity']
        security = intrinsic['identities']['security']['identity']
        metric = outcome['metrics']['direction_aligned_log']
        supported = event['eligibility']['primary_analysis']['eligible'] and metric['availability'] == 'available'
        value = metric['value'] if supported else None
        if supported and (not isinstance(value, (int, float)) or not isfinite(value)):
            raise ValueError('Available retained outcome must be finite')
        if value is not None and (not member or not security or not outcome['anchor']):
            raise ValueError('Supported retained outcome requires member, security and anchor')
        if outcome['direction'] != intrinsic['fields'].get('transactionDirection') or outcome['anchor'] != event['anchor']:
            raise ValueError('Retained outcome metadata conflicts with frozen Event')
        chamber_ready = run['event_input']['coverage']['readiness'].get(event['chamber'], {}).get('availability') == 'available'
        retained_available = value is not None
        if not chamber_ready:
            value = None
        day = outcome['anchor']['session_date'] if outcome['anchor'] else None
        publication = event.get('publication', {})
        publication_year = next((claim['raw_value'][:4] for claim in publication.get('evidence', [])
                                 if claim['id'] == publication.get('selectedEvidenceId')), 'unknown')
        provenance = event['provenance']
        base_id = (provenance.get('normalization') or {}).get('rowOccurrenceId')
        original = [r for r in provenance['rows'] if r['occurrenceId'] == base_id and r['sourceAuthority'] == 'official']
        if not original:
            original = [r for r in provenance['rows'] if r['sourceAuthority'] == 'official']
        versions = {r['artifactVersionId'] for r in original}
        filing = filings.get(next(iter(versions))) if len(versions) == 1 else None
        size = 'indeterminate'
        if (filing and filing['completeness'] == 'complete'
                and filing['literalTickerCompleteness'] == 'complete'
                and filing['literalSourceTickerStrings'] is not None):
            size = 'lt15' if filing['literalSourceTickerStrings'] < 15 else 'ge15'
        source_filings = sorted({r['sourceFiling']['id'] for r in original if r.get('sourceFiling')})
        reasons = sorted(set(metric['reasons'] + event['eligibility']['primary_analysis']['reasons'])) if value is None else []
        if not chamber_ready:
            reasons.append('disclosure_chamber_not_ready:' + event['chamber'])
        if value is None and not reasons:
            reasons = ['retained_aligned_outcome_unavailable']
        rows.append({'event_id': event['id'], 'member': member['identity_id'] if member else None,
            'security': security['identity_id'] if security else None,
            'direction': intrinsic['fields'].get('transactionDirection', 'unknown'),
            'day': day, 'chamber': event['chamber'], 'value': value,
            'year': day[:4] if day else publication_year, 'filing_size': size,
            'source_role': 'official' if event['status'] == 'event' else 'supporting',
            'source_filings': source_filings, 'missing_reasons': reasons,
            'retained_outcome_available': retained_available,
            'readiness_blocked': retained_available and not chamber_ready,
            'filing_size_evidence': filing,
            'outcome': outcome, 'event': event})
    return rows


def dimensions(rows):
    output = {}
    for dimension in ('chamber', 'year', 'source_role', 'direction', 'filing_size'):
        counts = {}
        for row in rows:
            count = counts.setdefault(row[dimension], {'events': 0, 'available': 0, 'missing': 0})
            count['events'] += 1
            count['available' if row['value'] is not None else 'missing'] += 1
        output[dimension] = dict(sorted(counts.items()))
    return output


def sample(rows):
    days = sorted({row['day'] for row in rows if row['day']})
    return {'events': len(rows), 'members': len({r['member'] for r in rows if r['member']}),
            'securities': len({r['security'] for r in rows if r['security']}),
            'source_filings': len({f for r in rows for f in r['source_filings']}),
            'anchor_sessions': len(days),
            'episodes': len({(r['security'], r['direction'], r['day']) for r in rows
                             if r['security'] and r['day'] and r['direction'] in ('purchase', 'sale')}),
            'anchor_months': len({day[:7] for day in days}),
            'covered_time_range': {'start': days[0] if days else None, 'end': days[-1] if days else None},
            'chambers': dict(sorted(Counter(r['chamber'] for r in rows).items()))}


def concentration(rows):
    result = {}
    for dimension in ('member', 'security', 'day', 'year'):
        result[dimension] = dict(sorted(Counter(str(r[dimension]) for r in rows).items()))
    result['source_filing'] = dict(sorted(Counter(f for r in rows for f in r['source_filings']).items()))
    return {'counting_unit': 'outcome_available_events', 'counts': result}


def field_missingness(rows):
    counts = Counter()
    for row in rows:
        fields = row['event']['intrinsicState']['fields']
        if fields.get('transactionDate') is None:
            counts['transaction_date_missing'] += 1
        if fields.get('amountLower') is None or fields.get('amountUpper') is None:
            counts['amount_range_unresolved'] += 1
    return {'reason_counts': dict(sorted(counts.items())), 'reasons_non_exclusive': True,
            'denominator': len(rows), 'scope': 'frozen_intrinsic_fields; only_dependent_uses_blocked'}


def interpretation(point, bounds, is_primary):
    if point is None:
        return 'Outcome unavailable; no supported point estimate.'
    direction = 'positive' if point > 0 else 'negative' if point < 0 else 'zero'
    if bounds is None:
        return f'{direction.capitalize()} descriptive estimate; inferential interval unavailable. Small-sample limitations are explicit.'
    if not is_primary:
        return f'{direction.capitalize()} supporting estimate; descriptive interval unadjusted for multiple comparisons.'
    if bounds[0] > 0 or bounds[1] < 0:
        return f'{direction.capitalize()} primary estimate; pre-specified 95% interval excludes zero (statistically distinguishable from zero).'
    return f'{direction.capitalize()} primary estimate; valid null/inconclusive result. Interval includes zero; this does not establish exact zero or no information.'


def report(rows, cohort, horizon, *, method_version=V2_METHOD_VERSION,
           episode_draw_limit=MAX_EPISODE_DRAW_ATTEMPTS):
    available = [row for row in rows if row['value'] is not None]
    members, episodes, anchors = defaultdict(list), defaultdict(list), {}
    for row in available:
        members[row['member']].append(row['value'])
        key = (row['security'], row['direction'], row['day'])
        open_at = row['outcome']['anchor']['open_at']
        if key in anchors and anchors[key] != open_at:
            raise ValueError('Retained episode anchor instants conflict')
        anchors[key] = open_at
        episodes[key].append(row['value'])
    values = [row['value'] for row in available]
    points = [mean(values), mean([mean(v) for v in members.values()]), mean([mean(v) for v in episodes.values()])]
    member_reasons = ['fewer_than_30_reporting_members'] if len(members) < MIN_MEMBERS else []
    months = len({row['day'][:7] for row in available})
    episode_reasons = [*member_reasons,
        *(['fewer_than_30_episodes'] if len(episodes) < MIN_EPISODES else []),
        *(['fewer_than_12_anchor_months'] if months < MIN_MONTHS else [])]
    bootstrap = bootstrap_manifest(available, cohort, horizon, method_version)
    weeks, bootstrap['week_range'] = episode_weeks(episodes, anchors)
    bootstrap['empty_episode_replicates'] = 0
    if method_version == V2_METHOD_VERSION:
        bootstrap['episode_resampling'] = {
            'requested_valid_replicates': REPLICATES, 'max_draw_attempts': episode_draw_limit,
            'total_draw_attempts': 0, 'valid_replicates': 0, 'empty_draws': 0,
            'empty_draw_indices': [], 'empty_draw_index_basis': 'one_based_draw_attempt',
            'status': 'not_run_inferential_thresholds'}
    event_estimate, member_estimate = estimate(points[0], member_reasons), estimate(points[1], member_reasons)
    if not member_reasons:
        event_estimate['interval'], member_estimate['interval'] = member_intervals(members, bootstrap['seed'])
        bootstrap['member_replicates_executed'] = REPLICATES
    episode_estimate = estimate(points[2], episode_reasons)
    if not episode_reasons:
        if method_version == V1_METHOD_VERSION:
            episode_estimate['interval'], bootstrap['empty_episode_replicates'] = episode_interval_v1(weeks, bootstrap['seed'])
            bootstrap['episode_replicates_executed'] = REPLICATES
            if bootstrap['empty_episode_replicates']:
                episode_estimate['interval_reasons'].append('empty_four_week_block_replicates')
        else:
            episode_estimate['interval'], attempts = episode_interval(weeks, bootstrap['seed'], max_draw_attempts=episode_draw_limit)
            bootstrap['episode_resampling'] = attempts
            bootstrap['empty_episode_replicates'] = attempts['empty_draws']
            bootstrap['episode_replicates_executed'] = attempts['valid_replicates']
            if attempts['status'] != 'complete':
                episode_estimate['interval_reasons'].append('episode_bootstrap_draw_attempt_limit_reached')
    return {'cohort': cohort, 'horizon_sessions': horizon, 'primary': cohort == 'combined' and horizon == 20,
            'event_weighted': event_estimate, 'member_balanced': member_estimate,
            'episode': episode_estimate, 'bootstrap': bootstrap,
            'sign_disagreement': any(v is not None and v > 0 for v in points) and any(v is not None and v < 0 for v in points),
            'interpretation': interpretation(points[0], event_estimate['interval'], cohort == 'combined' and horizon == 20),
            'supporting_intervals': 'descriptive_unadjusted_for_multiple_comparisons',
            'sample': {**sample(available), 'events': len(rows), 'outcome_available': len(available), 'missing': len(rows) - len(available),
                       'retained_outcome_available': sum(r['retained_outcome_available'] for r in rows),
                       'readiness_blocked': sum(r['readiness_blocked'] for r in rows)},
            'population_dimensions': sample(rows), 'coverage_dimensions': dimensions(rows),
            'concentration': concentration(available),
            'distribution': {'median': percentile(values, .5), 'q1': percentile(values, .25), 'q3': percentile(values, .75),
                             'iqr': percentile(values, .75) - percentile(values, .25) if values else None},
            'missingness': {'reason_counts': dict(sorted(Counter(reason for r in rows for reason in r['missing_reasons']).items())),
                           'reasons_non_exclusive': True, 'final_denominator': len(available),
                           'field_missingness': field_missingness(rows)},
            'event_ids': [r['event_id'] for r in rows]}


def summarize(run, *, method_version=V2_METHOD_VERSION, episode_draw_limit=MAX_EPISODE_DRAW_ATTEMPTS):
    if method_version not in (V1_METHOD_VERSION, V2_METHOD_VERSION):
        raise ValueError('Retained cohort method version unavailable')
    if method_version == V2_METHOD_VERSION and (type(episode_draw_limit) is not int or not 1 <= episode_draw_limit <= MAX_EPISODE_DRAW_ATTEMPTS):
        raise ValueError('Episode draw safeguard must be between 1 and 50000 attempts')
    if run['perspective'] != 'public_information' or run['event_input']['mode'] == 'corrected_retrospective':
        raise ValueError('Cohorts require retained primary public-information outcomes')
    results = []
    readiness = run['event_input']['coverage']['readiness']
    for horizon in HORIZONS:
        rows = observations(run, horizon)
        groups = {'combined': rows, 'purchase': [r for r in rows if r['direction'] == 'purchase'],
                  'sale': [r for r in rows if r['direction'] == 'sale']}
        for chamber in ('house', 'senate'):
            if readiness[chamber]['availability'] == 'available':
                groups[chamber] = [r for r in rows if r['chamber'] == chamber]
        for year in sorted({r['year'] for r in rows}):
            groups['year:' + year] = [r for r in rows if r['year'] == year]
        for size in ('lt15', 'ge15', 'indeterminate'):
            groups['filing_size:' + size] = [r for r in rows if r['filing_size'] == size]
        groups['outcome:available'] = [r for r in rows if r['value'] is not None]
        groups['outcome:missing'] = [r for r in rows if r['value'] is None]
        for cohort, subset in groups.items():
            item = report(subset, cohort, horizon, method_version=method_version, episode_draw_limit=episode_draw_limit)
            item['provenance'] = {
                'method_version': method_version, 'outcome_method_version': run['method_version'],
                'event_method_version': run['event_input']['methodVersion'],
                'market_contract_version': run['market_contract_version'],
                'source_run_id': run['id'], 'as_of': run['as_of'], 'perspective': run['perspective'],
                'as_of_definition': 'public_information; Event-intrinsic evidence frozen at supported publication boundary',
                'event_view_id': run['event_view_id'], 'market_input_id': run['market_input_id'],
                'outcome_boundaries': sorted({r['outcome']['outcome_boundary'] for r in subset if r['outcome']['outcome_boundary'] is not None}),
                'event_boundaries': sorted({r['event']['intrinsicBoundary'] for r in subset if r['event']['intrinsicBoundary'] is not None}),
                'snapshot_ids': sorted({s['id'] for r in subset for key in ('security_snapshots', 'benchmark_snapshots') for s in r['outcome'][key]}),
                'readiness_scope': run['readiness_scope']}
            results.append(item)
    primary_rows = observations(run, 20)
    flow = disclosure_flow(run['event_input'])
    flow['windows'] = [{'horizon_sessions': h,
        'events': len(run['event_input']['events']),
        'market_outcome_eligible': primary_result['sample']['retained_outcome_available'],
        'completed_windows': primary_result['sample']['retained_outcome_available'],
        'market_missing': primary_result['sample']['events'] - primary_result['sample']['retained_outcome_available'],
        'readiness_blocked': primary_result['sample']['readiness_blocked'],
        'missing': primary_result['sample']['missing'],
        'final_denominator': primary_result['sample']['outcome_available'],
        'reason_counts': primary_result['missingness']['reason_counts'], 'reasons_non_exclusive': True}
        for h in HORIZONS for primary_result in results if primary_result['cohort'] == 'combined' and primary_result['horizon_sessions'] == h]
    ready = [c for c in ('house', 'senate') if readiness[c]['availability'] == 'available']
    study_year = datetime.fromtimestamp(run['calculated_at'] / 1000, ZoneInfo('America/New_York')).year
    contract = deepcopy(V1_METHOD_CONTRACT if method_version == V1_METHOD_VERSION else METHOD_CONTRACT)
    if method_version == V2_METHOD_VERSION:
        contract['episode_max_draw_attempts'] = episode_draw_limit
    return {'method_version': method_version, 'method_contract': contract,
            'primary_estimand': '20_session_event_weighted_direction_aligned_benchmark_adjusted_log_mean',
            'results': results, 'flow': flow,
            'coverage': {'chamber_label': 'House-only readiness' if ready == ['house'] else 'Senate-only readiness' if ready == ['senate'] else 'House and Senate readiness' if len(ready) == 2 else 'Chamber readiness unavailable',
                'readiness': readiness, 'panel_complete': False, 'exploratory': True,
                'period_status': 'reliable_common_period_not_certified_by_retained_inputs',
                'required_period': {'start': f'{study_year - 5}-01-01', 'current_year': study_year},
                'observed_time_range': sample(primary_rows)['covered_time_range'],
                'calendar_year_basis': 'anchor_session_or_supported_source_local_publication',
                'dimensions': dimensions(primary_rows)},
            'filing_size': {'sensitivity_only': True, 'exclusion_applied': False,
                'definition': 'distinct_literal_source_ticker_strings; lt15/ge15/indeterminate; no behavioral label',
                'retained_counts': sorted(run['event_input']['coverage']['filings'], key=lambda f: f['artifactVersionId']),
                'event_classifications': [{'event_id': r['event_id'], 'group': r['filing_size'],
                                           'evidence': r['filing_size_evidence']} for r in primary_rows]},
            'consensus': {'availability': 'unavailable', 'reasons': ['historical_consensus_deferred'],
                          'raw': None, 'expected': None, 'excess': None}}


METHODS = {V1_METHOD_VERSION: partial(summarize, method_version=V1_METHOD_VERSION),
           V2_METHOD_VERSION: summarize}


class CohortAnalysisApplication:
    """Explicit application commands append results; reads never invoke #32 execution."""
    def __init__(self, connection_factory, clock=None):
        self._connection_factory = connection_factory
        self._clock = clock or (lambda: int(time.time() * 1000))
        self._outcomes = AnalysisApplication(connection_factory, self._clock)

    def execute(self, *, population, source_run_id):
        AnalysisApplication._population(population)
        now = self._clock()
        readiness = production_market_readiness(evaluated_at=now)
        if population == 'real' and (readiness['availability'] != 'available' or readiness['evaluation_scope'] != 'production'):
            return {'capability': readiness, 'runs': [],
                    'result': result_state('error', 'Cohort execution refused: production market readiness unavailable.', evaluated_at=now)}
        source = self._outcomes.get_run(source_run_id, population=population)
        if source['population'] != population or source['calculated_at'] > now:
            raise ValueError('Source run population or calculation boundary incompatible')
        if source['method_version'] != 'event-outcomes@1':
            raise ValueError('Retained outcome contract version unavailable')
        if source['readiness']['availability'] != 'available':
            raise ValueError('Source run lacks retained readiness')
        if population == 'real':
            if not source['production_ready'] or source['readiness_scope'] != 'production':
                raise ValueError('Isolated outcomes cannot enter production cohorts')
        else:
            if source['production_ready'] or source['readiness_scope'] == 'production' or source['readiness']['evidence_class'] != 'synthetic':
                raise ValueError('Evaluation cohorts require isolated synthetic outputs')
            readiness = source['readiness']
        report = METHODS[METHOD_VERSION](source)
        missing = any(r['sample']['missing'] for r in report['results'] if r['cohort'] == 'combined')
        empty = not source['outcomes']
        result = result_state('empty' if empty else 'partial' if missing else 'successful',
            'Retained cohort Analysis; supported estimates are valid regardless of sign or interval availability. Historical Consensus unavailable.', evaluated_at=now)
        run = {'id': str(uuid.uuid4()), 'method_version': METHOD_VERSION, 'calculated_at': now,
            'population': population, 'production_ready': population == 'real',
            'readiness_scope': source['readiness_scope'], 'readiness': readiness,
            'source_run_id': source_run_id, 'source_input': source, 'input_digest': digest(source),
            'report': report, 'result': result}
        with self._connection_factory() as conn:
            conn.execute('INSERT INTO analysis_cohort_runs VALUES (?, ?, ?, ?, ?, ?)',
                (run['id'], population, source_run_id, METHOD_VERSION, now, canonical(run)))
        return {'capability': readiness, 'result': result, 'runs': [run]}

    def query(self, *, population):
        AnalysisApplication._population(population)
        now = self._clock()
        with self._connection_factory() as conn:
            rows = conn.execute('SELECT run_json FROM analysis_cohort_runs WHERE population = ? ORDER BY calculated_at, id', (population,)).fetchall()
        runs = [json.loads(row['run_json']) for row in rows]
        readiness = production_market_readiness(evaluated_at=now)
        if population != 'real' and runs:
            readiness = runs[-1]['readiness']
        return {'capability': readiness, 'runs': runs,
                'result': result_state('error' if readiness['availability'] != 'available' else 'successful' if runs else 'empty',
                    'Market readiness unavailable.' if readiness['availability'] != 'available' else 'Retained cohort Analysis runs.', evaluated_at=now)}

    def get_run(self, run_id, *, population):
        AnalysisApplication._population(population)
        with self._connection_factory() as conn:
            row = conn.execute('SELECT run_json FROM analysis_cohort_runs WHERE id = ? AND population = ?', (run_id, population)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row['run_json'])

    def reproduce(self, run_id, *, population):
        run = self.get_run(run_id, population=population)
        if run['method_version'] not in METHODS:
            raise ValueError('Retained cohort method version unavailable')
        source = self._outcomes.get_run(run['source_run_id'], population=population)
        if source != run['source_input'] or digest(source) != run['input_digest']:
            raise ValueError('Retained outcome input mismatch')
        options = {'episode_draw_limit': run['report']['method_contract']['episode_max_draw_attempts']} if run['method_version'] == V2_METHOD_VERSION else {}
        report = METHODS[run['method_version']](source, **options)
        if report != run['report']:
            raise ValueError('Retained outputs do not reproduce cohort Analysis')
        return {'record_type': 'deterministic_reproduction', 'recorded_run_id': run_id,
                'reproduced_at': self._clock(), 'output': run}
