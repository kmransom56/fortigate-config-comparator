import pytest
from app import app, get_db_connection
import sqlite3
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"FortiManager Query App" in response.data

def test_test_endpoint(client):
    response = client.get('/test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Test endpoint working'

def test_get_ips(client, mocker):
    # Mock the database connection and cursor
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock the fetchall method to return some test data
    mock_cursor.fetchall.return_value = [
        {'device_name': 'device1', 'ip_address': '192.168.1.1'},
        {'device_name': 'device2', 'ip_address': '192.168.1.2'}
    ]
    
    # Patch the get_db_connection function to return our mock connection
    mocker.patch('app.get_db_connection', return_value=mock_conn)
    
    response = client.get('/get_ips')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['device_name'] == 'device1'
    assert data[0]['ip_address'] == '192.168.1.1'
    assert data[1]['device_name'] == 'device2'
    assert data[1]['ip_address'] == '192.168.1.2'

def test_404_error(client):
    response = client.get('/nonexistent_route')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Not found'
    assert 'message' in data

# Add more tests as needed for other routes and edge cases