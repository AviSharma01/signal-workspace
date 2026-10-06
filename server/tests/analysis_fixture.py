"""Isolated source records and independent worked expectations for #32."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
import json

from market_conformance import MarketConformanceApplication
from tests.market_fixture import fixture, SyntheticAdapter
from tests.test_events import ms


# Pencil-and-paper endpoint fractions for a no-action price chain:
# security=(100+k)/100; SPY=(200+k)/200. Decimal logarithms were worked
# independently at 45-digit precision, never through the production engine.
GOLDEN = {
    1: (1.01, 1.005, 0.004962789342129014, 0.004975124378109453),
    5: (1.05, 1.025, 0.024097551579060524, 0.024390243902439025),
    20: (1.2, 1.1, 0.08701137698962977, 0.09090909090909091),
    60: (1.6, 1.3, 0.2076393647782445, 0.23076923076923078),
}


def outcome_evidence():
    scope, evidence = fixture()
    sessions = []
    day = date(2025, 7, 3)
    while len(sessions) < 60:
        if day.weekday() < 5 and day.isoformat() not in ('2025-07-04', '2025-09-01'):
            text = day.isoformat()
            sessions.append({'session_date': text, 'open_at': ms(f'{text}T09:30:00-04:00'),
                             'close_at': ms(f'{text}T' + ('13:00:00' if text == '2025-07-03' else '16:00:00') + '-04:00')})
        day += timedelta(days=1)
    snapshots = list(evidence.snapshots)
    for security, listing, symbol, initial in (
        ('security:ABC', 'listing:security:ABC', 'ABC', 100),
        ('security:SPY', 'listing:SPY', 'SPY', 200),
    ):
        for index, session in enumerate(sessions):
            semantics = deepcopy(evidence.snapshots[0].semantics)
            semantics.update(security_identity=security, listing_identity=listing, symbol_observed=symbol,
                exchange='XNYS', calendar_version='toy-calendar@1', session_date=session['session_date'],
                open_at=session['open_at'], close_at=session['close_at'], corporate_actions=[],
                instrument_name='SPDR S&P 500 ETF Trust' if symbol == 'SPY' else 'Example Corp',
                ohlcv={'open': initial + index, 'high': initial + index + 1,
                       'low': initial + index, 'close': initial + index + 1, 'volume': 1000})
            semantics['identity_evidence'] = {'source': 'retained listing evidence', 'revision': '1',
                'valid_from': '2020-01-01', 'valid_to': '2026-12-31', 'public_at_ms': ms('2025-07-03T08:00:00-04:00'),
                'listing_country': 'US'}
            if index == 0:
                semantics['calendar'] = {'source': 'independent toy calendar', 'revision': 'toy-calendar@1',
                    'calendar_id': 'XNYS', 'timezone': 'America/New_York',
                    'public_at_ms': ms('2025-07-03T08:00:00-04:00'),
                    'validation': 'validated_complete_regular_sessions', 'sessions': sessions,
                    'coverage_start': sessions[0]['open_at'], 'coverage_end': sessions[-1]['close_at'] + 1}
            snapshots.append(replace(evidence.snapshots[0], semantics=semantics,
                raw_response=json.dumps({'semantics': semantics, 'observations': evidence.observations}, sort_keys=True).encode(),
                revision=f'{security}:{session["session_date"]}:1', retrieval_observation=f'observation:{security}:{index}',
                retrieved_at_ms=ms('2026-10-06T00:00:00+00:00'),
                request={'security': security, 'date': session['session_date']}))
    scope = replace(scope, securities=(*scope.securities, 'security:ABC', 'security:SPY'))
    return scope, replace(evidence, snapshots=tuple(snapshots))


def update_bar(evidence, security, index, **changes):
    snapshots = list(evidence.snapshots)
    indices = [i for i, snapshot in enumerate(snapshots) if snapshot.semantics['security_identity'] == security]
    selected = indices[index]
    old = snapshots[selected]
    semantics = deepcopy(old.semantics)
    semantics.update(changes)
    snapshots[selected] = replace(old, semantics=semantics, revision=old.revision + ':changed',
        raw_response=json.dumps({'semantics': semantics, 'observations': evidence.observations}, sort_keys=True).encode())
    return replace(evidence, snapshots=tuple(snapshots))


def report(scope, evidence):
    return MarketConformanceApplication().evaluate(scope, evidence, adapter=SyntheticAdapter())


def action(kind, day, terms, *, units='shares'):
    return {'type': kind, 'securities': ['security:ABC'], 'listings': ['listing:security:ABC'],
            'dates': {'ex' if kind == 'cash_distribution' else 'effective': day},
            'terms': terms, 'units': units, 'source': 'retained action record', 'revision': '1',
            'availability': {'observed_at_ms': ms('2025-07-03T08:00:00-04:00')}}
