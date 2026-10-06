import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import analysis as analysis_router
from tests import test_cohort_analysis as cohort_fixture


class CohortApiTest(unittest.TestCase):
    def setUp(self):
        self.fixture = cohort_fixture.CohortApplicationTest()
        self.fixture.setUp()
        api = FastAPI()
        api.include_router(analysis_router.router)
        api.dependency_overrides[analysis_router.get_cohort_application] = lambda: self.fixture.application
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        self.fixture.tearDown()

    def test_blocked_execution_and_empty_read_are_explicit(self):
        read = self.client.get('/api/analysis/cohorts')
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.json()['result']['state'], 'error')
        denied = self.client.post('/api/analysis/cohorts', json={'sourceRunId': 'missing'})
        self.assertEqual(denied.status_code, 409)
        self.assertEqual(denied.json()['runs'], [])

    def test_http_normalization_preserves_retained_source_and_dynamic_reason_keys(self):
        value = {'source_input': {'event_input': {'provenance': {'extraction': {
            'representation': {'raw_source_key': 'unchanged'},
            'rawFields': {'source_ticker': 'ABC'}}, 'coverage': {'reasonCounts': {'missing_security': 1}}}}},
            'report': {'results': [{'horizon_sessions': 20,
                'missingness': {'reason_counts': {'missing_bar:2025-07-03': 1}},
                'concentration': {'counts': {'member': {'member:raw_id': 2}}}}]}}
        result = analysis_router.cohort_json(value)
        self.assertEqual(result['sourceInput']['eventInput']['provenance']['extraction']['representation'], {'raw_source_key': 'unchanged'})
        self.assertEqual(result['sourceInput']['eventInput']['provenance']['coverage']['reasonCounts'], {'missing_security': 1})
        self.assertEqual(result['report']['results'][0]['missingness']['reasonCounts'], {'missing_bar:2025-07-03': 1})
        self.assertEqual(result['report']['results'][0]['concentration']['counts']['member'], {'member:raw_id': 2})

    def test_population_overrides_and_isolated_results_never_cross_http_boundary(self):
        upstream_fixture = self.fixture.fixture
        view, scope, evidence = upstream_fixture.prepare()
        source = upstream_fixture.run_outcomes(view, scope, evidence)
        run = self.fixture.application.execute(population='test', source_run_id=source['id'])['runs'][0]
        self.assertEqual(self.client.get('/api/analysis/cohorts').json()['runs'], [])
        for path in ('/api/analysis/cohorts', '/api/analysis/cohorts/' + run['id'],
                     '/api/analysis/cohorts/' + run['id'] + '/reproduction'):
            self.assertEqual(self.client.get(path, params={'population': 'test'}).status_code, 422)
        self.assertEqual(self.client.get('/api/analysis/cohorts/' + run['id']).status_code, 404)
        self.assertEqual(self.client.get('/api/analysis/cohorts/' + run['id'] + '/reproduction').status_code, 404)
        for extra in ({'population': 'test'}, {'seed': 1}, {'horizonSessions': 5}, {'threshold': 1}):
            self.assertEqual(self.client.post('/api/analysis/cohorts', json={'sourceRunId': source['id'], **extra}).status_code, 422)
