import pytest
import json
import tempfile
import os
from app import app, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = tempfile.mktemp(suffix='.db')
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

@pytest.fixture
def sample_trade():
    return {
        'asset': 'BTCUSDT',
        'side': 'long',
        'entry_price': 45000,
        'exit_price': 46000,
        'quantity': 0.1,
        'stop_loss': 44000,
        'take_profit': 47000,
        'bias': 'bullish',
        'model': 'trend_following',
        'confirmations': 3,
        'notes': 'Test trade'
    }

class TestAPI:
    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_get_trades_empty(self, client):
        response = client.get('/api/trades')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['trades'] == []

    def test_create_trade(self, client, sample_trade):
        response = client.post('/api/trades', 
                              data=json.dumps(sample_trade),
                              content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Trade created successfully'

    def test_get_trades_with_data(self, client, sample_trade):
        # Create a trade first
        client.post('/api/trades', 
                   data=json.dumps(sample_trade),
                   content_type='application/json')
        
        # Get trades
        response = client.get('/api/trades')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['trades']) == 1
        assert data['trades'][0]['asset'] == 'BTCUSDT'

    def test_update_trade(self, client, sample_trade):
        # Create trade
        create_response = client.post('/api/trades', 
                                     data=json.dumps(sample_trade),
                                     content_type='application/json')
        trade_id = json.loads(create_response.data)['id']
        
        # Update trade
        update_data = {'exit_price': 47000}
        response = client.put(f'/api/trades/{trade_id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        assert response.status_code == 200

    def test_delete_trade(self, client, sample_trade):
        # Create trade
        create_response = client.post('/api/trades', 
                                     data=json.dumps(sample_trade),
                                     content_type='application/json')
        trade_id = json.loads(create_response.data)['id']
        
        # Delete trade
        response = client.delete(f'/api/trades/{trade_id}')
        assert response.status_code == 200

class TestDatabase:
    def test_database_initialization(self, client):
        # Test that database tables are created
        response = client.get('/api/trades')
        assert response.status_code == 200

class TestValidation:
    def test_create_trade_missing_required_fields(self, client):
        incomplete_trade = {'asset': 'BTCUSDT'}
        response = client.post('/api/trades',
                              data=json.dumps(incomplete_trade),
                              content_type='application/json')
        assert response.status_code == 400

    def test_create_trade_invalid_data(self, client):
        invalid_trade = {
            'asset': 'BTCUSDT',
            'side': 'invalid_side',
            'entry_price': 'not_a_number'
        }
        response = client.post('/api/trades',
                              data=json.dumps(invalid_trade),
                              content_type='application/json')
        assert response.status_code == 400

class TestSecurity:
    def test_sql_injection_protection(self, client):
        malicious_input = "'; DROP TABLE trades; --"
        response = client.get(f'/api/trades?asset={malicious_input}')
        # Should not crash the server
        assert response.status_code in [200, 400]

    def test_xss_protection(self, client, sample_trade):
        xss_payload = '<script>alert("xss")</script>'
        sample_trade['notes'] = xss_payload
        response = client.post('/api/trades',
                              data=json.dumps(sample_trade),
                              content_type='application/json')
        assert response.status_code == 201

if __name__ == '__main__':
    pytest.main([__file__])
