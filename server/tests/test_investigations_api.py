import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import investigations, findings
from routers.capabilities import get_capability_application
from tests import test_investigations


class InvestigationApiTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_investigations.InvestigationApplicationTest()
        self.fixture.setUp()
        api = FastAPI()
        api.include_router(investigations.router)
        api.include_router(findings.router)
        api.dependency_overrides[investigations.get_investigation_application] = lambda: self.fixture.app
        api.dependency_overrides[get_capability_application] = lambda: self.fixture.capabilities
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        self.fixture.tearDown()

    def test_real_event_run_api_exposes_frozen_provenance_and_validated_findings(self):
        self.fixture.fixture.population = 'real'
        _, _, event_id = self.fixture.event()
        command = self.fixture.command(event_id)
        created = self.client.post('/api/investigations', json=command)
        self.assertEqual(created.status_code, 201, created.text)
        run_id = created.json()['run']['id']
        output = self.client.post(f'/api/investigations/{run_id}/execute')
        self.assertEqual(output.status_code, 200, output.text)
        payload = output.json()
        self.assertEqual(payload['capability']['availability'], 'available')
        self.assertEqual(payload['result']['state'], 'successful')
        run = payload['run']
        self.assertEqual(run['finding']['outcome'], 'unexplained')
        citation = run['finding']['claims'][0]['citations'][0]
        self.assertTrue(citation['reference']['citations'][0]['contentSha256'])
        self.assertEqual(citation['reference']['eligibility']['asOf'], command['boundary']['as_of'])
        retained = self.client.get(f'/api/investigations/{run_id}').json()['run']
        self.assertEqual(retained, run)
        listing = self.client.get('/api/investigations', params={'eventId': event_id}).json()
        self.assertEqual(listing['runs'][0]['id'], run_id)
        finding_listing = self.client.get('/api/findings').json()
        self.assertEqual(finding_listing['findings'][0], run['finding'])
        # Official asset text is not a verified ticker join. Never infer one for navigation.
        self.assertEqual(self.client.get('/api/findings', params={'ticker': 'ABC'}).json()['findings'], [])
        reproduction = self.client.get(f'/api/investigations/{run_id}/reproduction')
        self.assertEqual(reproduction.status_code, 200, reproduction.text)
        self.assertEqual(reproduction.json()['finding'], run['finding'])

    def test_market_trigger_widening_and_fixture_reads_are_rejected(self):
        _, _, event_id = self.fixture.event()
        test_run = self.fixture.app.create(self.fixture.command(event_id), population='test')
        self.assertEqual(self.client.get(f"/api/investigations/{test_run['id']}").status_code, 404)
        self.assertEqual(self.client.post(f"/api/investigations/{test_run['id']}/execute").status_code, 404)
        self.assertEqual(self.client.get('/api/investigations').json()['runs'], [])
        self.assertEqual(self.client.get('/api/findings').json()['findings'], [])
        for trigger in [{'kind': 'market', 'id': 'ABC'}, {'kind': 'event', 'id': event_id, 'version': 'caller-invented'}]:
            command = self.fixture.command(event_id, trigger=trigger)
            response = self.client.post('/api/investigations', json=command)
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.patch(f"/api/investigations/{test_run['id']}", json={'asOf': 999999}).status_code, 405)

    def test_unknown_run_and_unvalidated_proposals_have_no_api_persistence_route(self):
        self.assertEqual(self.client.get('/api/investigations/unknown').status_code, 404)
        self.assertEqual(self.client.post('/api/findings', json={'summary': 'Buy ABC'}).status_code, 405)
        self.assertEqual(self.client.post('/api/investigations/unknown/findings', json={'summary': 'Buy ABC'}).status_code, 404)

    def test_budget_result_and_current_capability_are_distinct_api_axes(self):
        self.fixture.fixture.population = 'real'
        _, _, event_id = self.fixture.event()
        response = self.client.post('/api/investigations', json=self.fixture.command(event_id, budgets={'steps': 0, 'elapsed_ms': 10000}))
        run_id = response.json()['run']['id']
        completed = self.client.post(f'/api/investigations/{run_id}/execute').json()
        self.assertEqual(completed['capability']['availability'], 'available')
        self.assertEqual(completed['result']['state'], 'partial')
        self.assertEqual(completed['run']['finding']['outcome'], 'budget_exhausted')
