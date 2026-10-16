from fastapi.testclient import TestClient
import pytest
from app import create_app

@pytest.fixture
def client():
    # Implement a separately provisioned synthetic test fixture; production must not trust these tokens.
    with TestClient(create_app()) as client:
        yield client

def test_order_replay_and_conflict(client):
    headers = {"Authorization": "Bearer alpha-token"}
    first = client.post('/orders', json={"key":"one", "sku":"book", "qty":1}, headers=headers)
    assert first.status_code == 201
    replay = client.post('/orders', json={"key":"one", "sku":"book", "qty":1}, headers=headers)
    assert replay.status_code == 200 and replay.json() == first.json()
    assert client.post('/orders', json={"key":"one", "sku":"book", "qty":2}, headers=headers).status_code == 409
    assert client.post('/orders', json={"key":"two", "sku":"book", "qty":1}, headers=headers).status_code == 409
    assert client.get('/orders/' + str(first.json()['id']), headers={"Authorization":"Bearer beta-token"}).status_code == 404

@pytest.mark.parametrize('qty', [True, 0, -1, '1', 1.5])
def test_strict_quantity(client, qty):
    assert client.post('/orders', json={"key":"bad", "sku":"book", "qty":qty}, headers={"Authorization":"Bearer alpha-token"}).status_code == 422

def test_unauthenticated(client):
    assert client.get('/orders').status_code == 401
