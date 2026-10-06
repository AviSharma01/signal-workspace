"""Offline synthetic evidence only. Never imported by production application code."""
from copy import deepcopy
import json
from pathlib import Path

from market_conformance import CandidateEvidence, ConformanceScope, MarketDataSnapshot
from dataclasses import replace
from decimal import Decimal


# Independently worked toy cases: no event outcome engine or provider data.
EXPECTED = {
    'bounded_revision_refresh': {'policy_version': 'toy-bounded-policy@1', 'session_scope': ['2026-03-06'], 'requests': 1, 'earlier_preserved': True},
    'five_complete_years_plus_current': {'start': '2021-01-01', 'end': '2026-10-06', 'gaps': []},
    'retained_inputs_permitted': {'permission': 'fixture-only'},
    'required_access_and_retention': {'cost': 0, 'currency': 'USD'},
    'ordinary_session': {'open_ms': 1772807400000, 'close_ms': 1772830800000, 'ohlcv': [100, 110, 90, 105, 1000]},
    'extended_hours_excluded': {'regular_session_only': True},
    'feed_venue_definitions': {'prices': 'toy consolidated', 'volume': 'toy consolidated shares'},
    'holiday': {'date': '2026-07-03', 'session': None},
    'early_close': {'date': '2026-11-27', 'close_utc': '18:00'},
    'dst_timezone': {'before_utc': '14:30', 'after_utc': '13:30', 'timezone': 'America/New_York'},
    'ticker_rename': {'old_symbol': 'OLD', 'new_symbol': 'NEW', 'security': 'toy-A'},
    'ticker_reuse': {'old_security': 'toy-A', 'new_security': 'toy-B', 'joined': False},
    'listing_change': {'old_listing': 'toy-X', 'new_listing': 'toy-Y', 'continuation': 'unavailable'},
    'ambiguous_identity': {'measurement': 'unavailable', 'reason': 'ambiguous_security'},
    'split': {'ratio': '2:1', 'raw_before': 100, 'raw_after': 50, 'economic_factor': 1},
    'cash_distribution': {'ex_date': '2026-03-09', 'amount': 2, 'currency': 'USD'},
    'non_cash_action': {'type': 'non_cash', 'measurement': 'unavailable'},
    'merger': {'type': 'merger', 'measurement': 'unavailable'},
    'spin_off': {'type': 'spin_off', 'measurement': 'unavailable'},
    'delisting': {'type': 'delisting', 'measurement': 'unavailable', 'terminal_return': None},
    'currency_and_price_volume_units': {'currency': 'USD', 'price': 'USD/share', 'volume': 'shares'},
    'missing_daily_bar': {'date': '2026-03-10', 'measurement': 'unavailable', 'filled': False},
    'gap_backfill': {'expected': 3, 'observed': 2, 'gaps': ['2026-03-10'], 'filled': False},
    'daily_acquisition': {'attempts': 1, 'last_success_ms': 1772830800000, 'latest_session': '2026-03-06', 'finality': 'unknown'},
    'downtime_catch_up': {'missed_sessions': ['2026-03-09'], 'recovered_sessions': ['2026-03-09'], 'failures': []},
    'later_revision': {'earlier_close': 105, 'later_close': 106, 'earlier_preserved': True},
    'unchanged_retrieval': {'observations': 2, 'versions': 1, 'bars': 1},
    'changed_retrieval': {'observations': 2, 'versions': 2, 'earlier_preserved': True},
    'event_session_join': {'date': '2026-03-06', 'exact_open_boundary_next_session': '2026-03-09'},
    'historical_security_join': {'security': 'toy-A', 'listing': 'toy-X', 'symbol': 'OLD'},
    'representative_calculation': {'raw_open': 100, 'raw_close': 105, 'close_open_factor': '1.05'},
    'provider_disagreement': {'source_a_close': 105, 'source_b_close': 106, 'measurement': 'unavailable', 'averaged': False},
    'later_identity_excluded': {'earlier_identity': 'unresolved', 'later_identity': 'toy-A', 'earlier_preserved': True},
    'later_correction_excluded': {'original_predictor': 1, 'replayed_predictor': 1, 'later_corrected_view': 2},
    'retained_provenance': {'inputs_retained': True},
    'reproduction': {'first': '1.05', 'replayed': '1.05'},
    'requests': {'count': 3},
    'elapsed': {'milliseconds': 12},
    'peak_memory': {'bytes': 4096},
    'retained_storage': {'bytes': 1024},
    'backfill_workload': {'sessions': 3, 'requests': 1},
    'acquisition_workload': {'sessions': 1, 'requests': 1},
    'catch_up_workload': {'sessions': 1, 'requests': 1},
    'revision_workload': {'sessions': 1, 'requests': 1},
    'join_workload': {'events': 2, 'security_joins': 2, 'session_joins': 2},
    'calculation_workload': {'calculations': 1, 'method': 'toy-close-open@1'},
}


def fixture():
    scope = ConformanceScope(
        scope_id='toy-2026', evidence_class='synthetic', evaluated_at_ms=1791244800000,
        coverage_start='2021-01-01', coverage_end='2026-10-06',
        securities=('toy-A', 'toy-B'), calendar_version='toy-calendar@1',
        expectation_source='independent-worked-toy-cases@1', expectations=deepcopy(EXPECTED),
    )
    snapshot = MarketDataSnapshot(
        evidence_class='synthetic',
        source='toy-provider', retrieval_observation='toy-retrieval-1', retrieved_at_ms=1772830800000,
        revision='toy-revision-1', raw_response=b'{"close":105,"symbol":"OLD"}',
        request={'security': 'toy-A', 'date': '2026-03-06'},
        normalization_version='toy-normalization@1',
        semantics={
            'security_identity': 'toy-A', 'symbol_observed': 'OLD', 'listing_identity': 'toy-X',
            'identity_evidence': {'source': 'toy-identity', 'revision': '1', 'valid_from': '2021-01-01', 'valid_to': '2026-03-06'},
            'exchange': 'toy-exchange', 'session_date': '2026-03-06', 'calendar_version': 'toy-calendar@1',
            'timezone': 'America/New_York', 'currency': 'USD',
            'price_unit': 'USD/share', 'volume_unit': 'shares', 'session_type': 'regular',
            'interval': 'daily', 'feed_venue': 'toy consolidated',
            'ohlcv_definitions': {'open': 'first regular trade', 'high': 'max', 'low': 'min', 'close': 'last regular trade', 'volume': 'regular shares'},
            'adjustment': 'raw', 'provider_adjusted': False, 'application_adjustments': [],
            'ohlcv': {'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000},
            'corporate_actions': [
                {'type': 'split', 'securities': ['toy-A'], 'listings': ['toy-X'], 'dates': {'effective': '2026-03-09'}, 'terms': {'ratio': '2:1'}, 'units': 'shares', 'source': 'toy-actions', 'revision': '1', 'availability': {'observed_at_ms': 1772830800000}},
                {'type': 'cash_distribution', 'securities': ['toy-A'], 'listings': ['toy-X'], 'dates': {'ex': '2026-03-09'}, 'terms': {'amount': 2}, 'units': 'USD/share', 'source': 'toy-actions', 'revision': '1', 'availability': {'observed_at_ms': 1772830800000}},
                {'type': 'non_cash', 'securities': ['toy-A'], 'listings': ['toy-X'], 'dates': {'effective': '2026-03-10'}, 'terms': {'description': 'toy distribution'}, 'units': 'rights', 'source': 'toy-actions', 'revision': '1', 'availability': {'observed_at_ms': 1772830800000}},
            ],
            'missingness': {'state': 'present', 'gaps': []}, 'finality': 'unknown',
        },
    )
    for action_type in ('merger', 'spin_off', 'delisting'):
        snapshot.semantics['corporate_actions'].append({
            'type': action_type, 'securities': ['toy-A'], 'listings': ['toy-X'],
            'dates': {'effective': '2026-03-10'}, 'terms': {'description': 'unresolved toy terminal action'},
            'units': 'shares', 'source': 'toy-actions', 'revision': '1',
            'availability': {'observed_at_ms': 1772830800000},
        })
    source_observations = json.loads((Path(__file__).parent / 'fixtures/market_conformance/candidate.json').read_text())
    snapshot = replace(snapshot, raw_response=json.dumps({'semantics': snapshot.semantics, 'observations': source_observations}, sort_keys=True).encode())
    # The reused symbol refers to two separately supported, disjoint histories.
    reused_semantics = deepcopy(snapshot.semantics)
    reused_semantics.update(security_identity='toy-B', listing_identity='toy-Z', session_date='2026-03-09', corporate_actions=[])
    reused_semantics['identity_evidence'].update(valid_from='2026-03-09', valid_to='2026-10-06')
    reused_snapshot = replace(
        snapshot, retrieval_observation='toy-retrieval-2', revision='toy-revision-B-1',
        retrieved_at_ms=1773086400000,
        request={'security': 'toy-B', 'date': '2026-03-09'}, semantics=reused_semantics,
        raw_response=json.dumps({'semantics': reused_semantics, 'observations': source_observations}, sort_keys=True).encode(),
    )
    case_refs = {case: (0,) for case in EXPECTED}
    case_refs['ticker_reuse'] = (0, 1)
    evidence = CandidateEvidence(
        candidate='toy-provider', evidence_class='synthetic', snapshots=(snapshot, reused_snapshot),
        observations=json.loads((Path(__file__).parent / 'fixtures/market_conformance/candidate.json').read_text()),
        case_snapshot_refs=case_refs,
        unsupported={}, workload_provenance={'method_version': 'toy-workloads@1', 'environment': 'offline toy fixture', 'input_refs': [0]},
    )
    return scope, evidence


class SyntheticAdapter:
    """Test-only source decoder. Rebuilds observations without expected answers."""

    def conformance_evidence(self, scope):
        return fixture()[1]

    def replay(self, scope, evidence):
        records = [json.loads(snapshot.raw_response) for snapshot in evidence.snapshots]
        observations = dict(records[0]['observations'])
        bar = records[0]['semantics']['ohlcv']
        observations['ordinary_session'] = dict(observations['ordinary_session'], ohlcv=[bar[key] for key in ('open', 'high', 'low', 'close', 'volume')])
        observations['representative_calculation'] = {
            'raw_open': bar['open'], 'raw_close': bar['close'],
            'close_open_factor': str(Decimal(str(bar['close'])) / Decimal(str(bar['open']))),
        }
        snapshots = tuple(replace(snapshot, semantics=record['semantics']) for snapshot, record in zip(evidence.snapshots, records))
        return replace(evidence, snapshots=snapshots, observations=observations)


def with_observations(evidence, observations):
    """Represent an incomplete/incorrect *source* response, not a cached result."""
    records = [json.loads(snapshot.raw_response) for snapshot in evidence.snapshots]
    for record in records:
        record['observations'] = observations
    return replace(evidence, observations=observations, snapshots=tuple(
        replace(snapshot, raw_response=json.dumps(record, sort_keys=True).encode())
        for snapshot, record in zip(evidence.snapshots, records)
    ))
