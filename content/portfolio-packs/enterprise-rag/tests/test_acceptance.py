from fastapi.testclient import TestClient
import pytest
from app import create_app

@pytest.fixture
def client():
    # Implement a separately provisioned synthetic test fixture; production must not trust these tokens.
    with TestClient(create_app()) as client:
        yield client

import json
from pathlib import Path

def test_seed_retrieval_and_current_citations(client):
    fixture=json.loads(Path('fixtures.json').read_text())
    for q in fixture['queries']:
        response=client.post('/ask', json={"query":q['query'],"language":q['language'],"k":3},headers={"Authorization":"Bearer alpha-token"})
        assert response.status_code == 200
        body=response.json()
        assert body['status'] == 'supported'
        assert set(q['relevant']) <= {c['source_id'] for c in body['citations']}
        assert all(c['version'] == '1' and 'offset' in c for c in body['citations'])
        assert 'private fixture marker' not in str(body)

def test_no_support_is_explicit(client):
    r=client.post('/ask',json={"query":"What is the alpha office alarm password?","language":"en","k":3},headers={"Authorization":"Bearer alpha-token"})
    assert r.status_code == 200 and r.json()['status'] == 'no-support' and r.json()['citations'] == []

def test_unauthenticated(client):
    assert client.post('/ask',json={"query":"office","language":"en","k":3}).status_code == 401
