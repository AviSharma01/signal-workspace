"""Application-owned #34 orchestration, validation and atomic lifecycle persistence."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
import unicodedata
import uuid
from contextlib import contextmanager
from typing import Callable

from capabilities import CapabilityApplication
from disclosures import ConnectionFactory
from events import EventApplication, POPULATIONS
from investigation_contract import Finding, METHOD_VERSION, RunCommand, VALIDATOR_VERSION
from investigation_runtime import BudgetExhausted, EvidenceTools, ReplayBudget, RunBudget, evidence_reference
from watch_events import WatchApplication


SUMMARIES = {
    'unexplained': 'Eligible disclosure evidence was inspected; an explanation is not established.',
    'insufficient_eligible_evidence': 'The frozen eligible evidence is insufficient for an investigation conclusion.',
    'capability_unavailable': 'A requested investigation capability is unavailable.',
    'budget_exhausted': 'A predeclared investigation budget was exhausted; the investigation is incomplete.',
}
CLAIM_TEXT = 'The retained disclosure row is available within the declared evidence boundary.'
QUESTION = 'What eligible evidence, if any, could establish an explanation?'
CONFIDENCE_BASIS = 'Low confidence reflects unresolved explanation; confidence is not evidence.'
LIMITATIONS = ['Disclosure evidence alone does not establish causality or investment intent.',
               'No market outcomes or external source retrieval were used.']
ADVICE_PATTERN = re.compile(
    r'\b(buy|sell|hold|short|long|invest|trade|recommend|recommendation|allocate|allocation|'
    r'portfolio|position|profit|alpha|outperform|underperform|overweight|underweight|'
    r'price\s*target|target\s*price|entry|exit|stop\s*loss|take\s*profit)\b', re.I)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _capability_limits(manifest):
    return [copy.deepcopy(item) for item in manifest['capability_snapshot']['capabilities']
            if item['availability'] != 'available' and
            (item['id'].startswith('investigation.') or item['id'] in {'market.outcomes', 'disclosure.house', 'disclosure.senate'})]


def draft_finding(run: dict, execution: dict) -> dict:
    """Canned application prose only; never interpolate raw source/model text."""
    manifest = run['manifest']
    inspected = set(execution['inspected_evidence_ids'])
    claims = [{'text': CLAIM_TEXT, 'citations': [{'evidence_id': item['id'], 'reference': evidence_reference(item)}]}
              for item in manifest['evidence'] if item['id'] in inspected and item['kind'] == 'reported_row']
    return {'run_id': run['id'], 'trigger': copy.deepcopy(manifest['trigger']),
            'boundary': copy.deepcopy(manifest['boundary']), 'outcome': execution['outcome'],
            'summary': SUMMARIES[execution['outcome']], 'hypotheses_considered': [],
            'claims': claims, 'counterevidence': [], 'unresolved_questions': [QUESTION],
            'confidence': 'low', 'confidence_basis': CONFIDENCE_BASIS,
            'limitations': [*LIMITATIONS, 'No explanatory hypothesis was supported; counterevidence assessment is incomplete.'],
            'missingness': execution['reasons'], 'capability_limitations': _capability_limits(manifest),
            'method_version': METHOD_VERSION, 'model_version': None,
            'review_status': 'needs_human_review', 'no_advice_status': 'validated', 'advice': None,
            'created_at': execution['finished_at']}


def validate_finding(candidate: dict, run: dict, execution: dict) -> dict:
    """Fail closed on structure/citations, then require the controlled text contract.

    Lexical checks catch explicit advice. Arbitrary prose, including paraphrased
    advice that escapes those checks, is withheld for review, never accepted on
    a keyword-filter assertion. #34 does not implement a human approval bypass.
    """
    try:
        finding = Finding.model_validate(candidate).model_dump(mode='json')
    except ValueError as exc:
        raise ValueError('invalid_finding_structure_or_outcome') from exc
    manifest = run['manifest']
    if finding['run_id'] != run['id'] or finding['trigger'] != manifest['trigger']:
        raise ValueError('finding_trigger_or_run_mismatch')
    if finding['boundary'] != manifest['boundary']:
        raise ValueError('finding_boundary_mismatch')
    if finding['method_version'] != manifest['method_version'] or finding['model_version'] is not None:
        raise ValueError('unsupported_finding_method_or_model')
    if finding['outcome'] != execution['outcome'] or finding['created_at'] != execution['finished_at']:
        raise ValueError('finding_execution_mismatch')
    if finding['capability_limitations'] != _capability_limits(manifest):
        raise ValueError('finding_capability_snapshot_mismatch')
    evidence = {item['id']: item for item in manifest['evidence']}
    for claim in [*finding['claims'], *finding['counterevidence']]:
        for citation in claim['citations']:
            item = evidence.get(citation['evidence_id'])
            if item is None or citation['evidence_id'] not in execution['inspected_evidence_ids']:
                raise ValueError('invalid_evidence_citation')
            reference = evidence_reference(item)
            if citation['reference'] != reference:
                raise ValueError('citation_provenance_or_timing_mismatch')
            boundary = manifest['boundary']
            eligibility = reference['eligibility']
            if (not eligibility['eligible'] or eligibility['as_of'] != boundary['as_of']
                    or eligibility['perspective'] != boundary['perspective']
                    or eligibility['available_by'] > boundary['as_of']):
                raise ValueError('ineligible_evidence_citation')
            timing_key = 'observed_at' if boundary['perspective'] == 'system_observation' else 'public_available_by'
            if reference[timing_key] is None or reference[timing_key] > boundary['as_of']:
                raise ValueError('future_evidence_citation')
            for source in reference['citations']:
                source_key = 'observed_at' if boundary['perspective'] == 'system_observation' else 'public_available_by'
                if source[source_key] > boundary['as_of'] or not source['content_sha256'] or not source['locator']:
                    raise ValueError('invalid_source_provenance_or_timing')
    text_fields = [finding['summary'], finding['confidence_basis'], *finding['hypotheses_considered'],
                   *finding['unresolved_questions'], *finding['limitations'], *finding['missingness'],
                   *(claim['text'] for claim in [*finding['claims'], *finding['counterevidence']])]
    for text in text_fields:
        normalized = unicodedata.normalize('NFKC', text)
        normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Cf')
        if ADVICE_PATTERN.search(normalized):
            raise ValueError('advice_bearing_free_text')
    if finding != draft_finding(run, execution):
        raise ValueError('unapproved_narrative_requires_review')
    return finding


class InvestigationApplication:
    def __init__(self, connection_factory: ConnectionFactory, capabilities: CapabilityApplication,
                 clock: Callable[[], int] | None = None, monotonic: Callable[[], float] = time.monotonic):
        self._connection_factory = connection_factory
        self._capabilities = capabilities
        self._clock = clock or (lambda: int(time.time() * 1000))
        self._monotonic = monotonic

    @contextmanager
    def _transaction(self, *, write):
        with self._connection_factory() as conn:
            conn.execute('BEGIN IMMEDIATE' if write else 'BEGIN')

            @contextmanager
            def bound_connection():
                yield conn

            yield conn, bound_connection

    @staticmethod
    def _population(population):
        if population not in POPULATIONS:
            raise ValueError('unknown_population')

    def create(self, command: dict, *, population: str) -> dict:
        self._population(population)
        request = RunCommand.model_validate(command)
        started = self._monotonic()
        with self._transaction(write=True) as (conn, bound):
            now = self._clock()
            if request.boundary.as_of > now:
                raise ValueError('future_investigation_boundary')
            authorization = None
            event_id = request.trigger.id
            trigger_record = None
            if request.trigger.kind == 'watch_event':
                if request.boundary.perspective != 'system_observation':
                    raise ValueError('watch_trigger_requires_system_observation')
                watch = WatchApplication(bound, lambda: now)
                detail = watch.get(request.trigger.id, population=population)
                trigger_record = detail['watchEvent']
                if trigger_record['admittedAt'] > request.boundary.as_of:
                    raise ValueError('watch_trigger_not_known_at_boundary')
                event_id = trigger_record['eventId']
                if request.trigger.active_only:
                    authorization = watch.authorize_active_action(request.trigger.id, population=population)
                    if not authorization['authorized']:
                        raise ValueError('watch_active_authorization_withheld')
            elif request.trigger.active_only:
                raise ValueError('active_only_requires_watch_trigger')
            snapshot = EventApplication(bound, lambda: now).investigation_snapshot(
                event_id, population=population, **request.boundary.model_dump(),
                original_occurrence_id=trigger_record['originalOccurrenceId'] if trigger_record else None)
            event_id = snapshot['event_id']
            capabilities = copy.deepcopy(self._capabilities.query())
            trigger = {**request.trigger.model_dump(), 'event_id': event_id,
                       'version': digest({'snapshot': snapshot, 'watch_record': trigger_record}),
                       'event_method_version': snapshot['event_method_version'],
                       'watch_record': trigger_record, 'authorization': authorization}
            manifest = {'trigger': trigger, 'boundary': request.boundary.model_dump(),
                        'evidence': snapshot['evidence'], 'occurrence_ids': snapshot['occurrence_ids'],
                        'navigation_tickers': snapshot['navigation_tickers'],
                        'capability_snapshot': capabilities, 'budgets': request.budgets.model_dump(),
                        'mode': request.mode, 'method_version': METHOD_VERSION,
                        'validator_version': VALIDATOR_VERSION, 'created_at': now,
                        'freeze_elapsed_ms': max(0, int((self._monotonic() - started) * 1000))}
            manifest['digest'] = digest(manifest)
            run_id = str(uuid.uuid4())
            conn.execute('INSERT INTO investigation_runs (id, population, created_at, manifest_json, status) '
                         "VALUES (?, ?, ?, ?, 'ready')", (run_id, population, now, json.dumps(manifest, sort_keys=True)))
            return self._load(conn, run_id, population)

    @staticmethod
    def _load(conn, run_id, population):
        row = conn.execute('SELECT * FROM investigation_runs WHERE id = ? AND population = ?',
                           (run_id, population)).fetchone()
        if row is None:
            raise KeyError(run_id)
        manifest = json.loads(row['manifest_json'])
        if digest({key: value for key, value in manifest.items() if key != 'digest'}) != manifest['digest']:
            raise ValueError('retained_manifest_integrity_failure')
        return {'id': run_id, 'population': population, 'created_at': row['created_at'],
                'manifest': manifest, 'status': row['status'],
                'execution': json.loads(row['execution_json']) if row['execution_json'] else None,
                'finding': json.loads(row['finding_json']) if row['finding_json'] else None}

    def get(self, run_id: str, *, population: str) -> dict:
        self._population(population)
        with self._transaction(write=False) as (conn, _):
            run = self._load(conn, run_id, population)
            if run['finding']:
                run['finding'] = validate_finding(run['finding'], run, run['execution'])
            return run

    def list(self, *, population: str, event_id: str | None = None, ticker: str | None = None,
             limit: int = 50) -> list[dict]:
        self._population(population)
        if limit < 1:
            raise ValueError('invalid_run_limit')
        with self._transaction(write=False) as (conn, _):
            runs = []
            for row in conn.execute('SELECT id FROM investigation_runs WHERE population = ? ORDER BY created_at DESC, id', (population,)):
                run = self._load(conn, row['id'], population)
                if event_id and run['manifest']['trigger']['event_id'] != event_id:
                    continue
                # A literal source ticker is only a navigation filter, never security identity.
                if ticker and ticker not in run['manifest']['navigation_tickers']:
                    continue
                if run['finding']:
                    run['finding'] = validate_finding(run['finding'], run, run['execution'])
                runs.append(run)
                if len(runs) >= limit:
                    break
            return runs

    def _execute(self, run, watch_authorizer=None, replay_budget=None, finished_at=None):
        manifest = run['manifest']
        budget = replay_budget or RunBudget(manifest['budgets'], elapsed_ms=max(
            manifest['freeze_elapsed_ms'], self._clock() - manifest['created_at']), monotonic=self._monotonic)
        inspected, reasons = [], []
        outcome = 'unexplained'
        authorization = None
        try:
            budget.step()
            if watch_authorizer is not None:
                authorization = watch_authorizer()
                budget.check_time()
            runtime = next(item for item in manifest['capability_snapshot']['capabilities'] if item['id'] == 'investigation.runtime')
            if authorization is not None and not authorization['authorized']:
                outcome, reasons = 'capability_unavailable', ['watch_active_authorization_withheld']
            elif runtime['availability'] != 'available':
                outcome, reasons = 'capability_unavailable', ['investigation_runtime_unavailable']
            elif manifest['mode'] == 'optional_model':
                if manifest['budgets']['model_spend_usd'] == 0:
                    raise BudgetExhausted('model_spend_budget_exhausted')
                outcome, reasons = 'capability_unavailable', ['optional_model_unavailable']
            else:
                tools = EvidenceTools(manifest, budget)
                evidence = tools.call('list_evidence')
                for item in evidence:
                    tools.call('read_evidence', {'evidence_id': item['id']})
                    inspected.append(item['id'])
                if not any(item['kind'] == 'reported_row' for item in evidence):
                    outcome, reasons = 'insufficient_eligible_evidence', ['eligible_disclosure_row_missing']
                budget.check_time()
        except BudgetExhausted as exc:
            outcome, reasons = 'budget_exhausted', [str(exc)]
        return {'outcome': outcome, 'reasons': reasons, 'inspected_evidence_ids': inspected,
                'usage': budget.usage(), 'finished_at': finished_at if finished_at is not None else self._clock(), 'method_version': METHOD_VERSION,
                'model_version': None, 'validator_version': VALIDATOR_VERSION,
                'execution_authorization': authorization}, budget

    def execute(self, run_id: str, *, population: str) -> dict:
        self._population(population)
        with self._transaction(write=True) as (conn, bound):
            run = self._load(conn, run_id, population)
            if run['status'] != 'ready':
                if run['finding']:
                    validate_finding(run['finding'], run, run['execution'])
                return run
            trigger = run['manifest']['trigger']
            authorizer = (lambda: WatchApplication(bound, self._clock).authorize_active_action(trigger['id'], population=population)) if trigger['active_only'] else None
            execution, budget = self._execute(run, authorizer)
            finding = self._validated_completion(run, execution, budget)
            status = {'unexplained': 'completed', 'insufficient_eligible_evidence': 'incomplete',
                      'capability_unavailable': 'unavailable', 'budget_exhausted': 'incomplete'}[execution['outcome']]
            conn.execute('UPDATE investigation_runs SET status = ?, execution_json = ?, finding_json = ? WHERE id = ?',
                         (status, json.dumps(execution, sort_keys=True), json.dumps(finding, sort_keys=True), run_id))
            return self._load(conn, run_id, population)

    @staticmethod
    def _validated_completion(run, execution, budget):
        finding = validate_finding(draft_finding(run, execution), run, execution)
        # Include the last successful validation pass in the budget. The only
        # work permitted after exhaustion is validating/persisting that outcome.
        try:
            budget.check_time()
            finding = validate_finding(draft_finding(run, execution), run, execution)
            budget.check_time()
        except BudgetExhausted as exc:
            execution.update(outcome='budget_exhausted', reasons=[str(exc)])
            finding = validate_finding(draft_finding(run, execution), run, execution)
        execution.update(usage=budget.usage(), time_checks=budget.time_checks)
        return finding

    def validate_proposal(self, run_id: str, candidate: dict, *, population: str) -> dict:
        """Explicit review seam; raw rejected prose is neither persisted nor displayed."""
        run = self.get(run_id, population=population)
        if run['execution'] is None:
            raise ValueError('execute_run_before_submitting_a_proposal')
        try:
            validate_finding(candidate, run, run['execution'])
        except ValueError as exc:
            return {'status': 'review_required', 'reason_codes': [str(exc)], 'run_id': run_id,
                    'proposal_digest': digest(candidate), 'finding': None}
        return {'status': 'validated', 'run_id': run_id, 'finding': run['finding']}

    def reproduce(self, run_id: str, *, population: str) -> dict:
        run = self.get(run_id, population=population)
        if run['execution'] is None or run['manifest']['method_version'] != METHOD_VERSION:
            raise ValueError('run_not_reproducible')
        if run['manifest']['validator_version'] != VALIDATOR_VERSION:
            raise ValueError('validator_version_not_reproducible')
        budget = ReplayBudget(run['manifest']['budgets'], run['execution'])
        trigger = run['manifest']['trigger']
        authorizer = (lambda: copy.deepcopy(run['execution']['execution_authorization'])) if trigger['active_only'] else None
        execution, _ = self._execute(run, authorizer, replay_budget=budget, finished_at=run['execution']['finished_at'])
        reproduced = self._validated_completion(run, execution, budget)
        budget.assert_complete()
        if execution != run['execution']:
            raise ValueError('execution_reproduction_failed')
        if reproduced != run['finding']:
            raise ValueError('retained_finding_reproduction_failed')
        return {'record_type': 'deterministic_reproduction', 'run_id': run_id,
                'manifest_digest': run['manifest']['digest'], 'finding': reproduced,
                'execution': run['execution']}
