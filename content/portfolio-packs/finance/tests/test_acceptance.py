from fastapi.testclient import TestClient
import pytest
from app import create_app

@pytest.fixture
def client():
    # Implement a separately provisioned synthetic test fixture; production must not trust these tokens.
    with TestClient(create_app()) as client:
        yield client

def test_exact_expense_replay_and_owner_scope(client):
    headers={"Authorization":"Bearer alpha-token"}
    payload={"key":"one","cents":1250,"currency":"USD","category":"food","date":"2026-10-01"}
    first=client.post('/expenses',json=payload,headers=headers)
    assert first.status_code == 201
    replay=client.post('/expenses',json=payload,headers=headers)
    assert replay.status_code == 200 and replay.json() == first.json()
    assert client.post('/expenses',json={**payload,"cents":1300},headers=headers).status_code == 409
    report=client.get('/reports/monthly?month=2026-10&currency=USD',headers=headers)
    assert report.status_code == 200 and report.json()['expense_cents'] == 1250
    foreign=client.get('/reports/monthly?month=2026-10&currency=USD',headers={"Authorization":"Bearer beta-token"})
    assert foreign.status_code == 200 and foreign.json()['expense_cents'] == 0

@pytest.mark.parametrize('cents',[True,0,-1,12.5,'1250'])
def test_exact_money(client,cents):
    assert client.post('/expenses',json={"key":"bad","cents":cents,"currency":"USD","category":"food","date":"2026-10-01"},headers={"Authorization":"Bearer alpha-token"}).status_code == 422

def test_unauthenticated(client):
    assert client.get('/reports/monthly?month=2026-10&currency=USD').status_code == 401
