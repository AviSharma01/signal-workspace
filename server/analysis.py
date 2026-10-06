"""Application-owned immutable outcomes; no source writes, provider or cohort logic."""
from __future__ import annotations

import base64
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from decimal import Context, Decimal, localcontext, ROUND_HALF_EVEN
import hashlib
import json
import time
from typing import Callable
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from capabilities import result_state
from events import EventApplication
from market_conformance import (
    MarketConformanceApplication, MarketDataSnapshot,
    production_market_readiness, snapshot_problems,
)

METHOD_VERSION = 'event-outcomes@1'
HORIZONS = (1, 5, 20, 60)
SUPPORTED_MARKET_CONTRACTS = {'signal-v2-market-data-contract@1'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def snapshot_json(snapshot):
    value = asdict(snapshot)
    value['raw_response'] = base64.b64encode(snapshot.raw_response).decode()
    return value


def metric(value=None, reasons=()):
    reasons = sorted(set(reasons))
    return {'value': float(value) if value is not None and not reasons else None,
            'availability': 'unavailable' if value is None or reasons else 'available',
            'reasons': reasons}


def mapping(value):
    return value if isinstance(value, dict) else {}


def calendar_sessions(snapshot, boundary):
    if snapshot is None:
        return [], ['calendar_unavailable']
    semantics = snapshot.semantics
    calendar = mapping(semantics.get('calendar'))
    sessions = calendar.get('sessions', [])
    if (calendar.get('validation') != 'validated_complete_regular_sessions'
            or not calendar.get('source') or not semantics.get('calendar_version')
            or calendar.get('revision') != semantics.get('calendar_version')
            or not semantics.get('exchange') or calendar.get('calendar_id') != semantics.get('exchange')
            or not semantics.get('timezone') or calendar.get('timezone') != semantics.get('timezone')
            or type(calendar.get('public_at_ms')) is not int or boundary is None
            or calendar['public_at_ms'] > boundary or not sessions):
        return [], ['calendar_unavailable_or_future_evidence']
    try:
        if (any(type(session['open_at']) is not int or type(session['close_at']) is not int
                or not calendar['coverage_start'] <= session['open_at'] < session['close_at'] < calendar['coverage_end']
                or datetime.fromtimestamp(session['open_at'] / 1000, ZoneInfo(calendar['timezone'])).date().isoformat() != session['session_date']
                for session in sessions)
                or any(left['close_at'] >= right['open_at'] or left['session_date'] >= right['session_date']
                       for left, right in zip(sessions, sessions[1:]))):
            return [], ['calendar_incompatible']
    except (KeyError, TypeError, ValueError, OverflowError):
        return [], ['calendar_incompatible']
    return sessions, []


def retained_calendar(snapshots, security, boundary, market_scope):
    candidates = {}
    scope_reasons = []
    for snapshot in snapshots:
        if snapshot.semantics.get('security_identity') == security and snapshot.semantics.get('calendar'):
            calendar = mapping(snapshot.semantics['calendar'])
            if (boundary is None or type(calendar.get('public_at_ms')) is not int
                    or calendar['public_at_ms'] > boundary):
                scope_reasons.append('calendar_unavailable_or_future_evidence')
                continue
            if (snapshot.retrieved_at_ms > market_scope['evaluated_at_ms']
                    or snapshot.source != market_scope['source']
                    or snapshot.semantics.get('calendar_version') != market_scope['calendar_version']):
                scope_reasons.append('calendar_outside_readiness_scope')
                continue
            candidates[digest(calendar)] = snapshot
    if len(candidates) > 1:
        return [], ['calendar_evidence_ambiguous']
    sessions, reasons = calendar_sessions(next(iter(candidates.values()), None), boundary)
    return sessions, reasons if candidates else [*reasons, *scope_reasons]


def gross_factor(snapshots, sessions, *, security, listing, boundary, calculated_at, market_scope):
    """Raw anchor close/open; split basis and ex-date close reinvestment thereafter."""
    reasons, refs, adjustments = [], [], []
    by_date = {}
    actions = {}
    for snapshot in snapshots:
        if snapshot.semantics.get('security_identity') == security:
            by_date.setdefault(snapshot.semantics.get('session_date'), []).append(snapshot)
            retained_actions = snapshot.semantics.get('corporate_actions')
            for action in retained_actions if isinstance(retained_actions, list) else []:
                if not isinstance(action, dict):
                    continue
                actions[digest(action)] = (action, snapshot)
    action_identity_counts = Counter(action.get('action_id') for action, _ in actions.values() if action.get('action_id'))
    session_dates = {session['session_date'] for session in sessions}
    if sessions:
        for action, _ in actions.values():
            dates = mapping(action.get('dates'))
            action_day = dates.get('ex') if action.get('type') == 'cash_distribution' else dates.get('effective') or dates.get('termination')
            if (isinstance(action_day, str) and sessions[0]['session_date'] <= action_day <= sessions[-1]['session_date']
                    and action_day not in session_dates):
                reasons.append('action_session_unresolved:' + str(action.get('type')) + ':' + action_day)
    basis, factor, prior_close = Decimal(1), Decimal(1), None
    feed_semantics = None
    for index, session in enumerate(sessions):
        bars = by_date.get(session['session_date'], [])
        if not bars:
            reasons.append('missing_bar:' + session['session_date'])
            continue
        if len(bars) != 1:
            reasons.append('ambiguous_snapshot:' + session['session_date'])
            continue
        snapshot = bars[0]
        value = snapshot.semantics
        if (security not in market_scope['securities']
                or value.get('calendar_version') != market_scope['calendar_version']
                or snapshot.retrieved_at_ms > market_scope['evaluated_at_ms']
                or not market_scope['coverage_start'] <= session['session_date'] <= market_scope['coverage_end']):
            reasons.append('snapshot_outside_readiness_scope')
        current_feed = (snapshot.source, value.get('feed_venue'), canonical(value.get('ohlcv_definitions')))
        if feed_semantics is None:
            feed_semantics = current_feed
        if current_feed != feed_semantics or snapshot.source != market_scope['source']:
            reasons.append('source_compatibility_unresolved')
        refs.append({'id': digest(snapshot_json(snapshot)), 'source': snapshot.source,
                     'revision': snapshot.revision, 'normalization_version': snapshot.normalization_version,
                     'retrieval_observation': snapshot.retrieval_observation, 'retrieved_at': snapshot.retrieved_at_ms})
        problems = snapshot_problems(snapshot)
        for gate in problems:
            reasons.append('snapshot_semantics:' + gate + ':' + session['session_date'])
        if snapshot.retrieved_at_ms > calculated_at:
            reasons.append('snapshot_after_calculation')
        if snapshot.retrieved_at_ms < session['close_at'] or session['close_at'] > calculated_at:
            reasons.append('completed_session_observation_unavailable')
        identity = mapping(value.get('identity_evidence'))
        if not listing or value.get('listing_identity') != listing:
            reasons.append('listing_identity_incompatible')
        if (boundary is None or type(identity.get('public_at_ms')) is not int
                or identity['public_at_ms'] > boundary):
            reasons.append('identity_evidence_after_event_boundary_or_unknown')
        if identity.get('listing_country') != 'US':
            reasons.append('listing_scope_unresolved')
        if (value.get('currency') != 'USD' or value.get('price_unit') != 'USD/share'
                or value.get('volume_unit') != 'shares'):
            reasons.append('currency_or_units_unresolved')
        if value.get('open_at') != session['open_at'] or value.get('close_at') != session['close_at']:
            reasons.append('sessions_incompatible:' + session['session_date'])
        missingness = mapping(value.get('missingness'))
        if missingness.get('state') != 'present' or session['session_date'] in (missingness.get('gaps') or []):
            reasons.append('missing_bar:' + session['session_date'])
        cash = Decimal(0)
        applicable_actions = []
        for action, action_snapshot in actions.values():
            dates = mapping(action.get('dates'))
            action_day = dates.get('ex') if action.get('type') == 'cash_distribution' else dates.get('effective') or dates.get('termination')
            if action_day is None:
                reasons.append('action_date_unresolved')
                continue
            if action_day != session['session_date']:
                # A supported record about another session is not applied here.
                continue
            if action.get('action_id') and action_identity_counts[action['action_id']] > 1:
                reasons.append('action_evidence_ambiguous')
                continue
            action_issues = snapshot_problems(action_snapshot).get('provenance_completeness', [])
            if (action_issues or action_snapshot.retrieved_at_ms > calculated_at
                    or action_snapshot.retrieved_at_ms > market_scope['evaluated_at_ms']
                    or action_snapshot.source != market_scope['source']):
                reasons.append('action_evidence_unavailable')
                continue
            if security not in action.get('securities', []) or listing not in action.get('listings', []):
                reasons.append('action_identity_unresolved')
                continue
            applicable_actions.append((action, action_snapshot))
        action_keys = [canonical({'id': action.get('action_id'), 'type': action['type'], 'date': session['session_date'],
                                 'securities': sorted(action['securities']), 'listings': sorted(action['listings'])})
                       for action, _ in applicable_actions]
        if len(set(action_keys)) != len(action_keys):
            reasons.append('action_evidence_ambiguous')
            applicable_actions = []
        for action, action_snapshot in applicable_actions:
            action_day = session['session_date']
            action_ref = {'id': digest(snapshot_json(action_snapshot)), 'source': action_snapshot.source,
                         'revision': action_snapshot.revision, 'normalization_version': action_snapshot.normalization_version,
                         'retrieval_observation': action_snapshot.retrieval_observation, 'retrieved_at': action_snapshot.retrieved_at_ms}
            if action_ref not in refs:
                refs.append(action_ref)
            try:
                if action['type'] == 'split':
                    numerator, denominator = action['terms']['ratio'].split(':')
                    ratio = Decimal(numerator) / Decimal(denominator)
                    if not ratio.is_finite() or ratio <= 0 or action['units'] != 'shares':
                        raise ValueError('unsupported split')
                    if index > 0:
                        basis *= ratio
                        adjustments.append({'session_date': action_day, 'type': 'split', 'share_ratio': str(ratio),
                                            'source': action['source'], 'revision': action['revision'],
                                            'evidence_snapshot_id': digest(snapshot_json(action_snapshot))})
                elif action['type'] == 'cash_distribution':
                    amount = Decimal(str(action['terms']['amount']))
                    if not amount.is_finite() or amount < 0 or action['units'] != 'USD/share':
                        raise ValueError('unsupported distribution')
                    if index > 0:
                        cash += amount
                        adjustments.append({'session_date': action_day, 'type': 'cash_distribution', 'amount': str(amount),
                                            'source': action['source'], 'revision': action['revision'],
                                            'evidence_snapshot_id': digest(snapshot_json(action_snapshot))})
                else:
                    reasons.append('action_unresolved:' + action['type'] + ':' + action_day)
            except (KeyError, ValueError, ArithmeticError, TypeError):
                reasons.append('action_terms_unresolved')
        try:
            close = Decimal(str(value['ohlcv']['close'])) * basis
            opening = Decimal(str(value['ohlcv']['open'])) * basis
            if not close.is_finite() or not opening.is_finite() or close <= 0 or opening <= 0:
                raise ValueError('nonpositive price')
            if index == 0:
                factor = close / opening
            elif prior_close is not None:
                factor *= (close + cash * basis) / prior_close
            prior_close = close
        except (KeyError, ValueError, ArithmeticError, TypeError):
            reasons.append('price_unavailable:' + session['session_date'])
    return (None if reasons else factor), reasons, refs, adjustments


def calculate_v1(view, snapshots, calculated_at, market_scope):
    outcomes = []
    for event in view['events']:
        intrinsic = event['intrinsicState']
        identity = intrinsic['identities']['security']['identity']
        security = identity.get('identity_id') if identity else None
        listing = identity.get('listing_id') if identity else None
        boundary, anchor = event['intrinsicBoundary'], event['anchor']
        # SPY must have a retained historically scoped instrument identity, not a symbol-only match.
        spy_anchors = [item for item in snapshots if anchor and item.semantics.get('symbol_observed') == 'SPY'
                       and item.semantics.get('instrument_name') == 'SPDR S&P 500 ETF Trust'
                       and item.semantics.get('session_date') == anchor['session_date']]
        spy = spy_anchors[0] if len(spy_anchors) == 1 else None
        security_sessions, security_calendar_reasons = retained_calendar(snapshots, security, boundary, market_scope)
        benchmark_sessions, benchmark_calendar_reasons = retained_calendar(
            snapshots, spy.semantics.get('security_identity') if spy else None, boundary, market_scope)
        calendar = benchmark_sessions or security_sessions
        start = next((i for i, session in enumerate(calendar) if anchor and session['session_date'] == anchor['session_date']), None)
        security_start = next((i for i, session in enumerate(security_sessions) if anchor and session['session_date'] == anchor['session_date']), None)
        eligibility = list(event['eligibility']['primary_analysis']['reasons'])
        if intrinsic['identities']['security']['status'] != 'resolved':
            eligibility.append('security_identity_unresolved')
        if intrinsic['identities']['member']['status'] != 'resolved':
            eligibility.append('member_identity_unresolved')
        direction = {'purchase': 1, 'sale': -1}.get(intrinsic['fields'].get('transactionDirection'))
        if intrinsic['fields'].get('assetClass') != 'individual_public_equity':
            eligibility.append('individual_equity_unresolved_or_out_of_scope')
        for horizon in HORIZONS:
            sessions = calendar[start:start + horizon] if start is not None else []
            common = []
            if len(sessions) != horizon:
                common.append('required_session_window_unavailable')
            if not anchor or not sessions or any(sessions[0].get(key) != anchor.get(key) for key in ('session_date', 'open_at', 'close_at')):
                common.append('anchor_session_incompatible_or_unavailable')
            security_reasons = [*common, *eligibility, *security_calendar_reasons]
            benchmark_reasons = [*common, *benchmark_calendar_reasons]
            security_window = security_sessions[security_start:security_start + horizon] if security_start is not None else []
            if security_window != sessions:
                security_reasons.append('sessions_incompatible')
            if not spy:
                benchmark_reasons.append('benchmark_identity_unresolved')
            with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
                security_factor, factor_reasons, security_refs, security_adjustments = gross_factor(
                    snapshots, sessions, security=security, listing=listing, boundary=boundary,
                    calculated_at=calculated_at, market_scope=market_scope)
                benchmark_factor, benchmark_factor_reasons, benchmark_refs, benchmark_adjustments = gross_factor(
                    snapshots, sessions, security=spy.semantics.get('security_identity') if spy else None,
                    listing=spy.semantics.get('listing_identity') if spy else None,
                    boundary=boundary, calculated_at=calculated_at, market_scope=market_scope)
                security_reasons.extend(factor_reasons)
                benchmark_reasons.extend(benchmark_factor_reasons)
                relative_reasons = [*security_reasons, *benchmark_reasons]
                log_return = (security_factor / benchmark_factor).ln() if security_factor is not None and benchmark_factor is not None and not relative_reasons else None
                aligned_reasons = [*relative_reasons, *([] if direction else ['direction_unresolved'])]
                metrics = {
                    'security_gross': metric(security_factor, security_reasons),
                    'security_total_return': metric(security_factor - 1 if security_factor is not None else None, security_reasons),
                    'benchmark_gross': metric(benchmark_factor, benchmark_reasons),
                    'benchmark_total_return': metric(benchmark_factor - 1 if benchmark_factor is not None else None, benchmark_reasons),
                    'benchmark_relative_log': metric(log_return, relative_reasons),
                    'compounded_relative': metric(log_return.exp() - 1 if log_return is not None else None, relative_reasons),
                    'direction_aligned_log': metric(direction * log_return if direction and log_return is not None else None, aligned_reasons),
                }
            outcomes.append({'event_id': event['id'], 'event_boundary': boundary, 'as_of': view['asOf'],
                'horizon_sessions': horizon, 'primary_horizon': horizon == 20,
                'anchor': anchor, 'direction': intrinsic['fields'].get('transactionDirection'),
                'session_dates': [s['session_date'] for s in sessions],
                'outcome_boundary': sessions[-1]['close_at'] if len(sessions) == horizon else None,
                'metrics': metrics, 'security_snapshots': security_refs, 'benchmark_snapshots': benchmark_refs,
                'application_adjustments': {'security': security_adjustments, 'benchmark': benchmark_adjustments},
                'availability': 'available' if all(m['availability'] == 'available' for m in metrics.values()) else 'unavailable',
                'reasons': sorted({reason for m in metrics.values() for reason in m['reasons']})})
    return outcomes


# Retained methods remain addressable independently of the default for new runs.
METHODS = {'event-outcomes@1': calculate_v1}


def disclosure_flow(view):
    events = view['events']
    # Descriptive flow only. No cohort construction, estimate or inference.
    counts = {'retained_row_occurrences': view['coverage']['retainedOccurrences'],
              'events': len(events), 'officially_verified': sum(e['status'] == 'event' for e in events),
              'primary_disclosure_eligible': sum(e['eligibility']['primary_analysis']['eligible'] for e in events)}
    for name, supported in {
        'direction_resolved': lambda e: e['intrinsicState']['fields'].get('transactionDirection') in ('purchase', 'sale'),
        'individual_equity': lambda e: e['intrinsicState']['fields'].get('assetClass') == 'individual_public_equity',
        'member_resolved': lambda e: e['intrinsicState']['identities']['member']['status'] == 'resolved',
        'security_resolved': lambda e: e['intrinsicState']['identities']['security']['status'] == 'resolved',
        'publication_supported': lambda e: e['intrinsicBoundary'] is not None,
        'anchor_supported': lambda e: e['anchor'] is not None,
        'occurrence_unambiguous': lambda e: not any(r.startswith('occurrence_') for r in e['eligibility']['primary_analysis']['reasons']),
    }.items():
        counts[name] = sum(supported(event) for event in events)
    return {'counts': counts, 'counts_non_exclusive': True,
            'reason_counts': view['coverage']['reasonCounts'], 'final_denominator': counts['primary_disclosure_eligible']}


class AnalysisApplication:
    def __init__(self, connection_factory, clock: Callable[[], int] | None = None):
        self._connection_factory = connection_factory
        self._clock = clock or (lambda: int(time.time() * 1000))
        self._events = EventApplication(connection_factory, self._clock)

    @staticmethod
    def _population(population):
        if population not in ('real', 'test', 'evaluation'):
            raise ValueError('Analysis population must be real or isolated test/evaluation')

    def retain_evaluation(self, report, *, population, adapter):
        """Explicit retention command, never exposed as a production activation API."""
        self._population(population)
        reproduced = MarketConformanceApplication().reproduce(report, adapter=adapter)
        readiness = reproduced['readiness']
        if readiness['availability'] != 'available':
            raise ValueError('Complete scoped conformance readiness required')
        if population == 'real' and readiness['evidence_class'] == 'synthetic':
            raise ValueError('Synthetic evidence cannot enter production storage')
        if population != 'real' and readiness['evidence_class'] != 'synthetic':
            raise ValueError('Isolated execution requires synthetic readiness')
        if readiness['evaluated_at'] > self._clock():
            raise ValueError('Readiness evaluation cannot postdate retention')
        input_id = report['evaluation_id']
        with self._connection_factory() as conn:
            row = conn.execute('SELECT population, report_json FROM analysis_market_inputs WHERE id = ?', (input_id,)).fetchone()
            if row is not None:
                if row['population'] != population or json.loads(row['report_json']) != report:
                    raise ValueError('Retained input identity conflict')
            else:
                conn.execute('INSERT INTO analysis_market_inputs VALUES (?, ?, ?, ?)',
                             (input_id, population, readiness['evidence_class'], canonical(report)))
        return {'id': input_id, 'readiness': deepcopy(readiness)}

    def _inputs(self, input_id, population):
        with self._connection_factory() as conn:
            row = conn.execute('SELECT report_json FROM analysis_market_inputs WHERE id = ? AND population = ?', (input_id, population)).fetchone()
        if row is None:
            raise KeyError(input_id)
        report = json.loads(row['report_json'])
        if report['evaluation_id'] != digest(report['retained']) or report['contract_version'] not in SUPPORTED_MARKET_CONTRACTS:
            raise ValueError('Retained market input digest/version mismatch')
        snapshots = [MarketDataSnapshot(**{**value, 'raw_response': base64.b64decode(value['raw_response'], validate=True)})
                     for value in report['retained']['evidence']['snapshots']]
        return report, snapshots

    def execute(self, *, population: str, event_view_id: str, market_input_id: str) -> dict:
        self._population(population)
        now = self._clock()
        if population == 'real':
            readiness = production_market_readiness(evaluated_at=now)
            if readiness['availability'] != 'available' or readiness['evaluation_scope'] != 'production':
                return {'capability': readiness,
                        'result': result_state('error', 'Execution refused: production market readiness is unavailable.', evaluated_at=now), 'runs': []}
        report, snapshots = self._inputs(market_input_id, population)
        if population != 'real':
            readiness = report['readiness']
            if (readiness['availability'] != 'available' or readiness['evidence_class'] != 'synthetic'
                    or readiness['evaluation_scope'] == 'production'
                    or any(s.evidence_class != 'synthetic' for s in snapshots)):
                raise ValueError('Only isolated synthetic readiness authorizes evaluation outcomes')
        elif report['readiness']['evidence_class'] != 'real_candidate' or any(s.evidence_class != 'real_candidate' for s in snapshots):
            raise ValueError('Synthetic evidence cannot produce production outcomes')
        view = self._events.get_recorded_view(event_view_id, population=population)
        if view['perspective'] != 'public_information' or view['mode'] == 'corrected_retrospective':
            raise ValueError('Primary outcomes require a recorded public-information historical Event view')
        if view['computedAt'] > now:
            raise ValueError('Event view cannot postdate calculation')
        market_scope = {**report['retained']['scope'], 'source': report['retained']['evidence']['candidate']}
        outcomes = METHODS[METHOD_VERSION](view, snapshots, now, market_scope)
        reasons = Counter(reason for outcome in outcomes for reason in outcome['reasons'])
        available = sum(o['availability'] == 'available' for o in outcomes)
        run = {'id': str(uuid.uuid4()), 'method_version': METHOD_VERSION, 'calculated_at': now,
               'population': population, 'production_ready': population == 'real',
               'readiness_scope': readiness['evaluation_scope'], 'readiness': readiness,
               'event_view_id': view['id'], 'as_of': view['asOf'], 'perspective': view['perspective'],
               'market_input_id': market_input_id, 'market_contract_version': report['contract_version'],
               'event_input': view, 'input_digest': digest({'event_view': view, 'market_input_id': market_input_id}),
               'outcomes': outcomes,
               'coverage': {'disclosure': view['coverage'], 'disclosure_flow': disclosure_flow(view), 'event_count': len(view['events']),
                            'completed_windows': available, 'unavailable_windows': len(outcomes) - available,
                            'reason_counts': dict(sorted(reasons.items())), 'reasons_non_exclusive': True,
                            'windows': [{'horizon_sessions': h, 'available': sum(o['horizon_sessions'] == h and o['availability'] == 'available' for o in outcomes),
                                         'total': len(view['events'])} for h in HORIZONS]},
               'result': result_state('empty' if not outcomes else 'partial' if reasons else 'successful',
                   'Per-Event outcomes; 20 sessions is primary. No cohort estimates or inference.', evaluated_at=now)}
        with self._connection_factory() as conn:
            conn.execute('INSERT INTO analysis_runs VALUES (?, ?, ?, ?, ?, ?)',
                         (run['id'], population, run['readiness_scope'], market_input_id, now, canonical(run)))
        return {'capability': readiness, 'result': run['result'], 'runs': [run]}

    def query(self, *, population: str) -> dict:
        self._population(population)
        now = self._clock()
        with self._connection_factory() as conn:
            rows = conn.execute('SELECT run_json FROM analysis_runs WHERE population = ? ORDER BY calculated_at, id', (population,)).fetchall()
        readiness = production_market_readiness(evaluated_at=now)
        runs = [json.loads(row['run_json']) for row in rows]
        if population != 'real':
            readiness = runs[-1]['readiness'] if runs else {**readiness, 'evaluation_scope': population}
        return {'capability': readiness,
                'result': result_state('error' if readiness['availability'] != 'available' else 'successful' if runs else 'empty',
                    'Market readiness unavailable.' if readiness['availability'] != 'available' else 'Retained Analysis runs.', evaluated_at=now),
                'runs': runs}

    def get_run(self, run_id, *, population):
        self._population(population)
        with self._connection_factory() as conn:
            row = conn.execute('SELECT run_json FROM analysis_runs WHERE id = ? AND population = ?', (run_id, population)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row['run_json'])

    def reproduce(self, run_id, *, population):
        run = self.get_run(run_id, population=population)
        if run['method_version'] not in METHODS:
            raise ValueError('Retained method version unavailable')
        report, snapshots = self._inputs(run['market_input_id'], population)
        view = self._events.get_recorded_view(run['event_view_id'], population=population)
        if view != run['event_input'] or digest({'event_view': view, 'market_input_id': run['market_input_id']}) != run['input_digest']:
            raise ValueError('Retained Event input mismatch')
        market_scope = {**report['retained']['scope'], 'source': report['retained']['evidence']['candidate']}
        outcomes = METHODS[run['method_version']](view, snapshots, run['calculated_at'], market_scope)
        if outcomes != run['outcomes']:
            raise ValueError('Retained inputs do not reproduce outcomes')
        return {'record_type': 'deterministic_reproduction', 'recorded_run_id': run_id,
                'reproduced_at': self._clock(), 'output': run}
