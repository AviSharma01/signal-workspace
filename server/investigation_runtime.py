"""Deterministic, in-memory evidence tools. No DB, network, provider or persistence access."""
from __future__ import annotations

import copy
import time
from collections.abc import Callable


class BudgetExhausted(ValueError):
    pass


class RunBudget:
    def __init__(self, limits: dict, *, elapsed_ms: int = 0,
                 monotonic: Callable[[], float] = time.monotonic):
        self.limits = copy.deepcopy(limits)
        self.steps = 0
        self.spend_usd = 0.0
        self.time_checks = []
        self._elapsed_ms = elapsed_ms
        self._monotonic = monotonic
        self._started = monotonic()

    def elapsed_ms(self):
        return self._elapsed_ms + max(0, int((self._monotonic() - self._started) * 1000))

    def check_time(self):
        elapsed = self.elapsed_ms()
        self.time_checks.append({'elapsed_ms': elapsed, 'steps': self.steps, 'model_spend_usd': self.spend_usd})
        if elapsed >= self.limits['elapsed_ms']:
            raise BudgetExhausted('elapsed_time_budget_exhausted')

    def step(self):
        self.check_time()
        if self.steps >= self.limits['steps']:
            raise BudgetExhausted('step_budget_exhausted')
        self.steps += 1

    def reserve_model_spend(self, maximum_usd: float):
        """Reserve a declared worst-case call cost before any optional API call.

        No provider is enabled in #34. An adapter may never call first and check
        cost later, or rely on the legacy global V1 spend guard.
        """
        import math
        self.check_time()
        limit = self.limits['model_spend_usd']
        if not math.isfinite(maximum_usd) or maximum_usd < 0:
            raise ValueError('invalid_model_cost_reservation')
        if limit is None or maximum_usd > limit - self.spend_usd:
            raise BudgetExhausted('model_spend_budget_exhausted')
        self.spend_usd += maximum_usd

    def usage(self):
        return {'steps': self.steps, 'elapsed_ms': self.elapsed_ms(), 'model_spend_usd': self.spend_usd}


class ReplayBudget(RunBudget):
    """Replay actual recorded deadline observations, never invent faster execution."""
    def __init__(self, limits: dict, execution: dict):
        super().__init__(limits, monotonic=lambda: 0)
        self._recorded_checks = copy.deepcopy(execution['time_checks'])
        self._recorded_elapsed = execution['usage']['elapsed_ms']

    def check_time(self):
        index = len(self.time_checks)
        if index >= len(self._recorded_checks):
            raise ValueError('execution_reproduction_checkpoint_missing')
        checkpoint = self._recorded_checks[index]
        if (checkpoint['steps'] != self.steps or checkpoint['model_spend_usd'] != self.spend_usd
                or checkpoint['elapsed_ms'] < (self.time_checks[-1]['elapsed_ms'] if self.time_checks else 0)
                or checkpoint['elapsed_ms'] > self._recorded_elapsed):
            raise ValueError('execution_reproduction_checkpoint_mismatch')
        self.time_checks.append(checkpoint)
        if checkpoint['elapsed_ms'] >= self.limits['elapsed_ms']:
            raise BudgetExhausted('elapsed_time_budget_exhausted')

    def elapsed_ms(self):
        return self._recorded_elapsed

    def assert_complete(self):
        if self.time_checks != self._recorded_checks:
            raise ValueError('execution_reproduction_checkpoint_mismatch')


def evidence_reference(item: dict) -> dict:
    return {key: copy.deepcopy(item[key]) for key in
            ('kind', 'citations', 'observed_at', 'public_available_by', 'derived_at', 'method_version', 'eligibility')}


class EvidenceTools:
    """Only list/read within one frozen run. Caller mutations affect only copies."""
    def __init__(self, manifest: dict, budget: RunBudget):
        self._boundary = copy.deepcopy(manifest['boundary'])
        self._evidence = {item['id']: copy.deepcopy(item) for item in manifest['evidence']}
        self._budget = budget

    def call(self, name: str, arguments: dict | None = None):
        self._budget.step()
        arguments = arguments or {}
        if name == 'list_evidence' and not arguments:
            result = [{'id': item['id'], **evidence_reference(item)} for item in self._evidence.values()]
        elif name == 'read_evidence' and set(arguments) == {'evidence_id'}:
            item = self._evidence.get(arguments['evidence_id'])
            if item is None or not item['eligibility']['eligible'] or item['eligibility']['available_by'] > self._boundary['as_of']:
                raise ValueError('evidence_not_in_frozen_eligible_set')
            result = copy.deepcopy(item)
        else:
            raise ValueError('unsupported_evidence_tool_or_arguments')
        self._budget.check_time()
        return result
