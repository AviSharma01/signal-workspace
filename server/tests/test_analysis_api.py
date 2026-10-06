import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import analysis as analysis_router
from tests import test_analysis


class AnalysisApiTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_analysis.AnalysisTest()
        self.fixture.setUp()
        api = FastAPI()
        api.include_router(analysis_router.router)
        api.dependency_overrides[analysis_router.get_analysis_application] = lambda: self.fixture.analysis
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        self.fixture.tearDown()

    def test_unavailable_readiness_is_an_explicit_error_not_empty_success(self):
        response = self.client.get('/api/analysis')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['capability']['availability'], 'unavailable')
        self.assertEqual(response.json()['capability']['evaluationScope'], 'production')
        self.assertEqual(response.json()['result']['state'], 'error')
        self.assertEqual(response.json()['runs'], [])
        denied = self.client.post('/api/analysis/runs', json={'eventViewId': 'missing', 'marketInputId': 'missing'})
        self.assertEqual(denied.status_code, 409)
        self.assertEqual(denied.json()['result']['state'], 'error')

    def test_synthetic_results_and_population_switches_cannot_cross_http_boundary(self):
        view, scope, evidence = self.fixture.prepare()
        run = self.fixture.run_outcomes(view, scope, evidence)
        self.assertEqual(self.client.get('/api/analysis').json()['runs'], [])
        for url in ('/api/analysis', '/api/analysis/runs/' + run['id'], '/api/analysis/runs/' + run['id'] + '/reproduction'):
            self.assertEqual(self.client.get(url, params={'population': 'test'}).status_code, 422)
        self.assertEqual(self.client.get('/api/analysis/runs/' + run['id']).status_code, 404)
        self.assertEqual(self.client.get('/api/analysis/runs/' + run['id'] + '/reproduction').status_code, 404)
        self.assertEqual(self.client.post('/api/analysis/runs', json={
            'eventViewId': view['id'], 'marketInputId': run['market_input_id'], 'population': 'test'}).status_code, 422)
        self.assertEqual(self.client.post('/api/analysis/runs', json={
            'eventViewId': view['id'], 'marketInputId': run['market_input_id'], 'readinessScope': 'toy-2026'}).status_code, 422)
        self.assertEqual(self.client.post('/api/analysis/evaluations', json={}).status_code, 404)


if __name__ == '__main__':
    unittest.main()
