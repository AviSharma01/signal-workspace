"""Offline candidate conformance; this module has no production activation command."""
from __future__ import annotations

from typing import Any, Literal, Protocol
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
from copy import deepcopy
import base64
import hashlib
import json
import math
from zoneinfo import ZoneInfo
from decimal import Decimal

CONTRACT_VERSION = 'signal-v2-market-data-contract@1'
HARNESS_VERSION = 'market-conformance@1'

# Required independent cases, not provider claims of gate status.
GATE_CASES = {
    'historical_coverage': ('five_complete_years_plus_current',),
    'retention_rights': ('retained_inputs_permitted',),
    'zero_cost_feasibility': ('required_access_and_retention',),
    'regular_session_daily_ohlcv': ('ordinary_session', 'extended_hours_excluded', 'feed_venue_definitions'),
    'session_calendar': ('holiday', 'early_close', 'dst_timezone'),
    'historical_security_identity': ('ticker_rename', 'ticker_reuse', 'listing_change', 'ambiguous_identity'),
    'split_handling': ('split',),
    'cash_distribution_handling': ('cash_distribution',),
    'non_cash_actions': ('non_cash_action',),
    'terminal_events': ('merger', 'spin_off', 'delisting'),
    'currency_units': ('currency_and_price_volume_units',),
    'missing_bar_behavior': ('missing_daily_bar',),
    'gap_backfill_behavior': ('gap_backfill',),
    'acquisition_catch_up': ('daily_acquisition', 'downtime_catch_up'),
    'revision_correction': ('later_revision',),
    'revision_refresh_validation': ('bounded_revision_refresh',),
    'repeated_retrieval_versions': ('unchanged_retrieval', 'changed_retrieval'),
    'identity_calendar_joins': ('event_session_join', 'historical_security_join'),
    'deterministic_calculations': ('representative_calculation',),
    'source_disagreement': ('provider_disagreement',),
    'temporal_boundaries': ('later_identity_excluded', 'later_correction_excluded'),
    'provenance_completeness': ('retained_provenance',),
    'reproducibility': ('reproduction',),
    'request_counts': ('requests',),
    'elapsed_time': ('elapsed',),
    'memory': ('peak_memory',),
    'storage': ('retained_storage',),
    'workload': ('backfill_workload', 'acquisition_workload', 'catch_up_workload',
                 'revision_workload', 'join_workload', 'calculation_workload'),
}


# Required observable evidence fields for each acceptance scenario.
CASE_FIELDS = {
    'bounded_revision_refresh': {
        'policy_version': str, 'session_scope': list, 'requests': (int, float),
        'earlier_preserved': bool,
    },
    'five_complete_years_plus_current': {
        'start': str, 'end': str, 'gaps': list,
    },
    'retained_inputs_permitted': {
        'permission': str,
    },
    'required_access_and_retention': {
        'cost': (int, float), 'currency': str,
    },
    'ordinary_session': {
        'open_ms': (int, float), 'close_ms': (int, float), 'ohlcv': list,
    },
    'extended_hours_excluded': {
        'regular_session_only': bool,
    },
    'feed_venue_definitions': {
        'prices': str, 'volume': str,
    },
    'holiday': {
        'date': str, 'session': type(None),
    },
    'early_close': {
        'date': str, 'close_utc': str,
    },
    'dst_timezone': {
        'before_utc': str, 'after_utc': str, 'timezone': str,
    },
    'ticker_rename': {
        'old_symbol': str, 'new_symbol': str, 'security': str,
    },
    'ticker_reuse': {
        'old_security': str, 'new_security': str, 'joined': bool,
    },
    'listing_change': {
        'old_listing': str, 'new_listing': str, 'continuation': str,
    },
    'ambiguous_identity': {
        'measurement': str, 'reason': str,
    },
    'split': {
        'ratio': str, 'raw_before': (int, float), 'raw_after': (int, float), 'economic_factor': (int, float),
    },
    'cash_distribution': {
        'ex_date': str, 'amount': (int, float), 'currency': str,
    },
    'non_cash_action': {
        'type': str, 'measurement': str,
    },
    'merger': {
        'type': str, 'measurement': str,
    },
    'spin_off': {
        'type': str, 'measurement': str,
    },
    'delisting': {
        'type': str, 'measurement': str, 'terminal_return': type(None),
    },
    'currency_and_price_volume_units': {
        'currency': str, 'price': str, 'volume': str,
    },
    'missing_daily_bar': {
        'date': str, 'measurement': str, 'filled': bool,
    },
    'gap_backfill': {
        'expected': (int, float), 'observed': (int, float), 'gaps': list, 'filled': bool,
    },
    'daily_acquisition': {
        'attempts': (int, float), 'last_success_ms': (int, float), 'latest_session': str, 'finality': str,
    },
    'downtime_catch_up': {
        'missed_sessions': list, 'recovered_sessions': list, 'failures': list,
    },
    'later_revision': {
        'earlier_close': (int, float), 'later_close': (int, float), 'earlier_preserved': bool,
    },
    'unchanged_retrieval': {
        'observations': (int, float), 'versions': (int, float), 'bars': (int, float),
    },
    'changed_retrieval': {
        'observations': (int, float), 'versions': (int, float), 'earlier_preserved': bool,
    },
    'event_session_join': {
        'date': str, 'exact_open_boundary_next_session': str,
    },
    'historical_security_join': {
        'security': str, 'listing': str, 'symbol': str,
    },
    'representative_calculation': {
        'raw_open': (int, float), 'raw_close': (int, float), 'close_open_factor': str,
    },
    'provider_disagreement': {
        'source_a_close': (int, float), 'source_b_close': (int, float), 'measurement': str, 'averaged': bool,
    },
    'later_identity_excluded': {
        'earlier_identity': str, 'later_identity': str, 'earlier_preserved': bool,
    },
    'later_correction_excluded': {
        'original_predictor': (int, float), 'replayed_predictor': (int, float), 'later_corrected_view': (int, float),
    },
    'retained_provenance': {
        'inputs_retained': bool,
    },
    'reproduction': {
        'first': str, 'replayed': str,
    },
    'requests': {
        'count': (int, float),
    },
    'elapsed': {
        'milliseconds': (int, float),
    },
    'peak_memory': {
        'bytes': (int, float),
    },
    'retained_storage': {
        'bytes': (int, float),
    },
    'backfill_workload': {
        'sessions': (int, float), 'requests': (int, float),
    },
    'acquisition_workload': {
        'sessions': (int, float), 'requests': (int, float),
    },
    'catch_up_workload': {
        'sessions': (int, float), 'requests': (int, float),
    },
    'revision_workload': {
        'sessions': (int, float), 'requests': (int, float),
    },
    'join_workload': {
        'events': (int, float), 'security_joins': (int, float), 'session_joins': (int, float),
    },
    'calculation_workload': {
        'calculations': (int, float), 'method': str,
    },
}


def production_market_readiness(*, evaluated_at: int) -> dict[str, Any]:
    """No provider has been approved. Evaluation reports cannot change this state."""
    return {
        'id': 'market.data_readiness',
        'name': 'Production market-data readiness',
        'availability': 'unavailable',
        'reason_codes': ['market_data_contract_unsatisfied', 'provider_not_approved'],
        'detail': 'No real candidate evidence or explicit provider approval exists.',
        'evaluated_at': evaluated_at,
        'governing_version': CONTRACT_VERSION,
        'evaluation_scope': 'production',
        'unmet_prerequisites': [
            {'code': code, 'detail': 'Independent real-provider evidence required.', 'status': 'unsupported'}
            for code in (*GATE_CASES, 'explicit_provider_approval')
        ],
    }


EvidenceClass = Literal['synthetic', 'real_candidate']


@dataclass(frozen=True)
class MarketDataSnapshot:
    evidence_class: EvidenceClass
    source: str
    retrieval_observation: str
    retrieved_at_ms: int
    revision: str
    raw_response: bytes
    request: dict[str, Any]
    normalization_version: str
    semantics: dict[str, Any]


@dataclass(frozen=True)
class ConformanceScope:
    scope_id: str
    evidence_class: EvidenceClass
    evaluated_at_ms: int
    coverage_start: str
    coverage_end: str
    securities: tuple[str, ...]
    calendar_version: str
    expectation_source: str
    expectations: dict[str, Any]


@dataclass(frozen=True)
class CandidateEvidence:
    candidate: str
    evidence_class: EvidenceClass
    snapshots: tuple[MarketDataSnapshot, ...]
    observations: dict[str, Any]
    case_snapshot_refs: dict[str, tuple[int, ...]]
    unsupported: dict[str, str]
    workload_provenance: dict[str, Any]


class CandidateMarketAdapter(Protocol):
    """An adapter returns retained evidence, never a claim that a gate passed.

    Acquisition is intentionally not invoked by production or by the harness.
    A future approved candidate trial can implement this offline evaluation seam.
    """

    def conformance_evidence(self, scope: ConformanceScope) -> CandidateEvidence: ...

    def replay(self, scope: ConformanceScope, evidence: CandidateEvidence) -> CandidateEvidence:
        """Rebuild normalized semantics/observations from retained source inputs only.

        Must not fetch data, use cached observed results, or access expectations.
        The evaluator supplies a scope with expectations removed.
        """
        ...


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _present(value: Any) -> bool:
    return value is not None and value != '' and value != b'' and value != {} and value != [] and value != ()


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _case_field_valid(value: Any, required_type: Any) -> bool:
    if required_type == (int, float):
        return _number(value)
    if required_type is str:
        return isinstance(value, str) and bool(value.strip())
    return type(value) is required_type


def _snapshot_problems(snapshot: MarketDataSnapshot) -> dict[str, list[str]]:
    """Validate only approved fields; unknown semantics are never invented."""
    problems: dict[str, list[str]] = {}

    def require(gate: str, condition: bool, detail: str) -> None:
        if not condition:
            problems.setdefault(gate, []).append(detail)

    for field in ('source', 'retrieval_observation', 'revision', 'raw_response', 'request', 'normalization_version'):
        require('provenance_completeness', _present(getattr(snapshot, field)), f'missing {field}')
    require(
        'provenance_completeness',
        type(snapshot.retrieved_at_ms) is int and snapshot.retrieved_at_ms > 0,
        'missing retrieval instant',
    )
    semantics = _mapping(snapshot.semantics)
    fields = {
        'historical_security_identity': ('security_identity', 'symbol_observed', 'listing_identity', 'identity_evidence'),
        'session_calendar': ('exchange', 'session_date', 'calendar_version', 'timezone'),
        'currency_units': ('currency', 'price_unit', 'volume_unit'),
        'regular_session_daily_ohlcv': ('feed_venue', 'ohlcv_definitions', 'ohlcv'),
        'missing_bar_behavior': ('missingness',),
        'revision_correction': ('finality',),
    }
    for gate, names in fields.items():
        for name in names:
            require(gate, _present(semantics.get(name)), f'missing {name}')
    require(
        'regular_session_daily_ohlcv',
        semantics.get('session_type') == 'regular' and semantics.get('interval') == 'daily',
        'daily regular-session semantics required',
    )
    require(
        'regular_session_daily_ohlcv',
        semantics.get('adjustment') == 'raw' and semantics.get('provider_adjusted') is False and (semantics.get('application_adjustments') == []),
        'unadjusted source OHLCV required; adjusted history alone is insufficient',
    )
    ohlcv = semantics.get('ohlcv')
    ohlcv = ohlcv if isinstance(ohlcv, dict) else {}
    require(
        'regular_session_daily_ohlcv',
        all((_number(ohlcv.get(field)) for field in ('open', 'high', 'low', 'close', 'volume'))),
        'all raw OHLCV fields required',
    )
    definitions = semantics.get('ohlcv_definitions')
    definitions = definitions if isinstance(definitions, dict) else {}
    require(
        'regular_session_daily_ohlcv',
        all((_present(definitions.get(field)) for field in ('open', 'high', 'low', 'close', 'volume'))),
        'each OHLCV definition required',
    )
    if all(_number(ohlcv.get(field)) for field in ('open', 'high', 'low', 'close')):
        require(
            'regular_session_daily_ohlcv',
            ohlcv['low'] <= min(ohlcv['open'], ohlcv['close']) <= max(ohlcv['open'], ohlcv['close']) <= ohlcv['high'],
            'inconsistent OHLC prices',
        )
    try:
        ZoneInfo(semantics.get('timezone', ''))
        date.fromisoformat(semantics.get('session_date', ''))
    except (KeyError, ValueError, TypeError):
        require('session_calendar', False, 'invalid session date or timezone')
    require(
        'revision_correction',
        semantics.get('finality') in ('unknown', 'provisional', 'final'),
        'explicit finality state required',
    )
    missingness = semantics.get('missingness')
    missingness = missingness if isinstance(missingness, dict) else {}
    require(
        'missing_bar_behavior',
        missingness.get('state') in ('present', 'missing', 'gap', 'unsupported') and isinstance(missingness.get('gaps'), list),
        'explicit missingness and gap state required',
    )
    identity = semantics.get('identity_evidence')
    identity = identity if isinstance(identity, dict) else {}
    require(
        'historical_security_identity',
        all((_present(identity.get(field)) for field in ('source', 'revision', 'valid_from', 'valid_to'))),
        'historically scoped identity provenance required',
    )
    try:
        start, end = date.fromisoformat(identity.get('valid_from', '')), date.fromisoformat(identity.get('valid_to', ''))
        session = date.fromisoformat(semantics.get('session_date', ''))
        require(
            'historical_security_identity',
            start <= session <= end,
            'identity interval must contain snapshot session',
        )
    except (TypeError, ValueError):
        require('historical_security_identity', False, 'invalid historical identity interval')
    actions = semantics.get('corporate_actions')
    require(
        'provenance_completeness',
        isinstance(actions, list),
        'separate corporate-action evidence required (empty means explicitly no actions)',
    )
    if isinstance(actions, list):
        for action in actions:
            require(
                'provenance_completeness',
                isinstance(action, dict) and all((_present(action.get(field)) for field in ('type', 'securities', 'listings', 'dates', 'terms', 'units', 'source', 'revision', 'availability'))),
                'incomplete corporate-action provenance',
            )
            action = _mapping(action)
            require(
                'provenance_completeness',
                bool(_list(action.get('securities'))) and bool(_list(action.get('listings'))),
                'action security/listing lists required',
            )
            dates = _mapping(action.get('dates'))
            try:
                require('provenance_completeness', bool(dates), 'action date meanings required')
                for value in dates.values():
                    date.fromisoformat(value)
            except (ValueError, TypeError):
                require('provenance_completeness', False, 'invalid action date evidence')
            observed_at = _mapping(action.get('availability')).get('observed_at_ms')
            require(
                'provenance_completeness',
                type(observed_at) is int and type(snapshot.retrieved_at_ms) is int and (0 < observed_at <= snapshot.retrieved_at_ms),
                'action observation must not postdate retrieval',
            )
    return problems


class MarketConformanceApplication:
    """Pure offline evaluation. Reports are retained/exportable JSON, not DB writes.

    Independent expectations are trial inputs, not values inferred from the adapter.
    Their authority requires human review before any later production adoption.
    """

    def evaluate_adapter(self, scope: ConformanceScope, adapter: CandidateMarketAdapter) -> dict[str, Any]:
        return self.evaluate(scope, adapter.conformance_evidence(replace(scope, expectations={})), adapter=adapter)

    def evaluate(self, scope: ConformanceScope, evidence: CandidateEvidence, *, adapter: CandidateMarketAdapter | None = None) -> dict[str, Any]:
        if scope.scope_id == 'production' or not scope.scope_id.strip():
            raise ValueError('Conformance requires an isolated named evaluation scope')
        if scope.evidence_class not in ('synthetic', 'real_candidate') or evidence.evidence_class != scope.evidence_class:
            raise ValueError('Evidence class must match the evaluation scope')
        if not scope.expectation_source or not evidence.candidate or scope.expectation_source == evidence.candidate:
            raise ValueError('Independently attributed expectations and candidate identity required')
        if type(scope.evaluated_at_ms) is not int or scope.evaluated_at_ms <= 0:
            raise ValueError('Evaluation instant required')
        # Canonicalization rejects non-finite values and makes equality type-sensitive.
        retained = {'scope': asdict(scope), 'evidence': asdict(evidence)}
        for snapshot in retained['evidence']['snapshots']:
            snapshot['raw_response'] = base64.b64encode(snapshot['raw_response']).decode()
        retained = json.loads(_canonical(retained))
        replay_status = 'unsupported'
        replay_detail = 'No retained-input adapter replay supplied.'
        if adapter is not None:
            try:
                # Neither independently expected answers nor cached normalized results
                # are supplied to replay. Only retained source snapshots and references.
                replay_input = replace(evidence, observations={}, snapshots=tuple(replace(snapshot, semantics={}) for snapshot in evidence.snapshots))
                replayed = adapter.replay(replace(scope, expectations={}), replay_input)
                replay_status = 'pass' if asdict(replayed) == asdict(evidence) else 'fail'
                replay_detail = 'Adapter replay differs from submitted retained evidence.'
            except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError):
                replay_status, replay_detail = 'fail', 'Retained-input adapter replay failed.'
        decisions = []
        for gate, cases in GATE_CASES.items():
            checks = []
            for case in cases:
                status = 'pass'
                details = []
                refs = evidence.case_snapshot_refs.get(case, ())
                if case in evidence.unsupported:
                    status, details = 'unsupported', [evidence.unsupported[case]]
                elif case not in scope.expectations or case not in evidence.observations:
                    status, details = 'unsupported', ['missing independent expectation or candidate observation']
                elif not refs or any(type(ref) is not int or ref < 0 or ref >= len(evidence.snapshots) for ref in refs):
                    status, details = 'unsupported', ['missing retained snapshot references']
                elif not isinstance(scope.expectations[case], dict) or not isinstance(evidence.observations[case], dict) or not _present(scope.expectations[case]) or not _present(evidence.observations[case]):
                    status, details = 'unsupported', ['empty case evidence']
                else:
                    if _canonical(scope.expectations[case]) != _canonical(evidence.observations[case]):
                        status, details = 'fail', ['candidate observation disagrees with independent expectation']
                    for ref in refs:
                        snapshot = evidence.snapshots[ref]
                        issues = _snapshot_problems(snapshot)
                        details.extend(issues.get(gate, []))
                        # Every passing case must retain complete source provenance.
                        details.extend(issues.get('provenance_completeness', []) if gate != 'provenance_completeness' else [])
                        if snapshot.evidence_class != scope.evidence_class:
                            details.append('snapshot evidence class differs from evaluation scope')
                        if snapshot.source != evidence.candidate:
                            details.append('snapshot source differs from evaluated candidate')
                        if type(snapshot.retrieved_at_ms) is not int or snapshot.retrieved_at_ms > scope.evaluated_at_ms:
                            details.append('retrieval occurs after evaluation boundary')
                    if case == 'ordinary_session':
                        observation = evidence.observations[case]
                        raw_bar = _mapping(_mapping(evidence.snapshots[refs[0]].semantics).get('ohlcv'))
                        if observation.get('ohlcv') != [raw_bar.get(key) for key in ('open', 'high', 'low', 'close', 'volume')]:
                            details.append('ordinary-session observation differs from retained raw bar')
                    if case == 'representative_calculation':
                        observation = evidence.observations[case]
                        raw_bar = _mapping(_mapping(evidence.snapshots[refs[0]].semantics).get('ohlcv'))
                        try:
                            factor = Decimal(str(raw_bar['close'])) / Decimal(str(raw_bar['open']))
                            if observation.get('raw_open') != raw_bar['open'] or observation.get('raw_close') != raw_bar['close'] or Decimal(observation['close_open_factor']) != factor:
                                details.append('representative calculation does not match retained inputs')
                        except (KeyError, TypeError, ValueError, ArithmeticError):
                            details.append('representative calculation inputs unsupported')
                    action_type = {'split': 'split', 'cash_distribution': 'cash_distribution', 'non_cash_action': 'non_cash', 'merger': 'merger', 'spin_off': 'spin_off', 'delisting': 'delisting'}.get(case)
                    if action_type and not any(
                        action.get('type') == action_type
                        and _mapping(evidence.snapshots[ref].semantics).get('security_identity') in _list(action.get('securities'))
                        and _mapping(evidence.snapshots[ref].semantics).get('listing_identity') in _list(action.get('listings'))
                        and (case != 'split' or _mapping(action.get('terms')).get('ratio') == evidence.observations[case].get('ratio'))
                        and (case != 'cash_distribution' or (_mapping(action.get('terms')).get('amount') == evidence.observations[case].get('amount') and _mapping(action.get('dates')).get('ex') == evidence.observations[case].get('ex_date')))
                        for ref in refs
                        for action in _list(_mapping(evidence.snapshots[ref].semantics).get('corporate_actions'))
                        if isinstance(action, dict)
                    ):
                        details.append('separately attributed action evidence required')
                    if gate == 'identity_calendar_joins' and any(
                        _mapping(evidence.snapshots[ref].semantics).get('security_identity') not in scope.securities
                        or _mapping(evidence.snapshots[ref].semantics).get('calendar_version') != scope.calendar_version
                        for ref in refs
                    ):
                        details.append('snapshot security/calendar incompatible with declared scope')
                    required_fields = CASE_FIELDS[case]
                    if any(field not in evidence.observations[case] or field not in scope.expectations[case] or not _case_field_valid(evidence.observations[case].get(field), required_type) or not _case_field_valid(scope.expectations[case].get(field), required_type) for field, required_type in required_fields.items()):
                        details.append('required case evidence fields missing')
                    unsupported_details = []
                    # Approved outcomes cannot be weakened by a matching oracle.
                    if case == 'ticker_reuse':
                        reuse = evidence.observations[case]
                        if reuse.get('joined') is not False:
                            details.append('reused ticker histories must remain separated')
                        old_security, new_security = reuse.get('old_security'), reuse.get('new_security')
                        if old_security == new_security:
                            details.append('ticker reuse requires distinct historical security identities')
                        supported_identities = [
                            _mapping(evidence.snapshots[ref].semantics).get('security_identity')
                            for ref in refs
                            if not _snapshot_problems(evidence.snapshots[ref]).get('historical_security_identity')
                        ]
                        if any(identity not in scope.securities or identity not in supported_identities
                               for identity in (old_security, new_security)):
                            unsupported_details.append('ticker reuse lacks retained historical identity evidence for both securities')
                    if case == 'later_revision' and evidence.observations[case].get('earlier_preserved') is not True:
                        details.append('later revisions must preserve earlier retained evidence')
                    if case == 'bounded_revision_refresh':
                        session_scope = evidence.observations[case].get('session_scope')
                        if not isinstance(session_scope, list) or not session_scope or any(
                            not isinstance(session, str) or not session.strip() for session in session_scope
                        ):
                            details.append('bounded revision-refresh session scope must be non-empty and explicit')
                    if details:
                        status = 'fail'
                        details.extend(unsupported_details)
                    elif unsupported_details:
                        status, details = 'unsupported', unsupported_details
                checks.append({'case': case, 'status': status, 'details': details, 'snapshot_refs': list(refs)})
            if gate == 'reproducibility' and replay_status != 'pass':
                checks.append({'case': 'retained_input_replay', 'status': replay_status, 'details': [replay_detail], 'snapshot_refs': []})
            extra = self._gate_requirements(gate, scope, evidence)
            status = 'fail' if extra or any(item['status'] == 'fail' for item in checks) else 'unsupported' if any(item['status'] == 'unsupported' for item in checks) else 'pass'
            decisions.append({'code': gate, 'status': status, 'cases': checks, 'details': extra})
        unmet = [
            {
                'code': item['code'], 'status': item['status'],
                'detail': '; '.join([
                    *item['details'],
                    *[f"{case['case']}: {'; '.join(case['details'])}" for case in item['cases'] if case['status'] != 'pass'],
                ]),
            }
            for item in decisions if item['status'] != 'pass'
        ]
        availability = 'available' if not unmet else 'conditional' if any(item['status'] == 'pass' for item in decisions) else 'unavailable'
        readiness = {
            'id': 'market.conformance', 'name': 'Candidate market-data conformance',
            'availability': availability, 'reason_codes': [f"market_gate_{item['status']}:{item['code']}" for item in unmet],
            'detail': 'Scoped conformance evidence only; this decision cannot authorize production use.',
            'evaluated_at': scope.evaluated_at_ms, 'governing_version': CONTRACT_VERSION,
            'evaluation_scope': scope.scope_id, 'evidence_class': scope.evidence_class,
            'unmet_prerequisites': unmet,
        }
        return {
            'harness_version': HARNESS_VERSION, 'contract_version': CONTRACT_VERSION,
            'evaluation_id': _digest(retained), 'retained': retained,
            'gates': decisions, 'readiness': readiness,
        }

    @staticmethod
    def _gate_requirements(gate: str, scope: ConformanceScope, evidence: CandidateEvidence) -> list[str]:
        problems = []
        if gate == 'historical_coverage':
            try:
                start, end = date.fromisoformat(scope.coverage_start), date.fromisoformat(scope.coverage_end)
                evaluation_date = datetime.fromtimestamp(scope.evaluated_at_ms / 1000, timezone.utc).date()
                if start > date(evaluation_date.year - 5, 1, 1) or end < evaluation_date or end > evaluation_date:
                    problems.append('five complete calendar years plus current-year coverage through evaluation required')
                observation = evidence.observations.get('five_complete_years_plus_current', {})
                if observation.get('start') != scope.coverage_start or observation.get('end') != scope.coverage_end or observation.get('gaps') != []:
                    problems.append('coverage limits or gaps do not satisfy declared scope')
            except (ValueError, TypeError, AttributeError):
                problems.append('invalid coverage evidence')
        if gate == 'zero_cost_feasibility':
            access = _mapping(evidence.observations.get('required_access_and_retention'))
            if access.get('cost') != 0 or not _present(access.get('currency')):
                problems.append('required access and retention must satisfy approved zero-cost constraints')
        if gate == 'retention_rights':
            permission = _mapping(evidence.observations.get('retained_inputs_permitted')).get('permission')
            if not isinstance(permission, str) or not permission.strip() or (scope.evidence_class == 'real_candidate' and permission == 'fixture-only'):
                problems.append('independently supported retention permission for this evidence class required')
        if gate == 'identity_calendar_joins':
            if not scope.securities or not scope.calendar_version:
                problems.append('declared securities and validated calendar version required')
        metric_cases = {'request_counts': ('requests', 'count'), 'elapsed_time': ('elapsed', 'milliseconds'), 'memory': ('peak_memory', 'bytes'), 'storage': ('retained_storage', 'bytes')}
        if gate in (*metric_cases, 'workload', 'acquisition_catch_up', 'gap_backfill_behavior', 'revision_correction', 'revision_refresh_validation', 'reproducibility'):
            if not all(_present(evidence.workload_provenance.get(key)) for key in ('method_version', 'environment', 'input_refs')):
                problems.append('workload method, environment and retained input references required')
            refs = evidence.workload_provenance.get('input_refs', [])
            if not isinstance(refs, list) or any(type(ref) is not int or ref < 0 or ref >= len(evidence.snapshots) for ref in refs):
                problems.append('invalid workload input references')
        if gate in metric_cases:
            case, unit = metric_cases[gate]
            value = evidence.observations.get(case, {})
            if not isinstance(value, dict) or not _number(value.get(unit)):
                problems.append(f'nonnegative finite {unit} measurement required')
        return problems

    def reproduce(self, report: dict[str, Any], *, adapter: CandidateMarketAdapter | None = None) -> dict[str, Any]:
        if report.get('harness_version') != HARNESS_VERSION or report.get('contract_version') != CONTRACT_VERSION:
            raise ValueError('Unsupported conformance version')
        retained = deepcopy(report['retained'])
        if _digest(retained) != report['evaluation_id']:
            raise ValueError('Retained evidence digest mismatch')
        scope_data = retained['scope']
        scope_data['securities'] = tuple(scope_data['securities'])
        evidence_data = retained['evidence']
        snapshots = []
        for value in evidence_data['snapshots']:
            value['raw_response'] = base64.b64decode(value['raw_response'], validate=True)
            snapshots.append(MarketDataSnapshot(**value))
        evidence_data['snapshots'] = tuple(snapshots)
        evidence_data['case_snapshot_refs'] = {key: tuple(value) for key, value in evidence_data['case_snapshot_refs'].items()}
        reproduced = self.evaluate(ConformanceScope(**scope_data), CandidateEvidence(**evidence_data), adapter=adapter)
        if reproduced != report:
            raise ValueError('Recorded decision does not reproduce')
        return reproduced
