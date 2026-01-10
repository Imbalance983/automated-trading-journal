# API Documentation

## Overview

The Automated Trading Journal provides a comprehensive RESTful API for managing trading data, integrating with Bybit exchange, and performing advanced analytics.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently uses session-based authentication. Future versions will support JWT tokens.

## Endpoints

### Trade Management

#### Get All Trades
```http
GET /api/trades
```

**Query Parameters:**
- `asset` (optional): Filter by asset symbol
- `bias` (optional): Filter by market bias
- `side` (optional): Filter by trade side (long/short)
- `limit` (optional): Number of results to return

**Response:**
```json
{
  "trades": [
    {
      "id": 1,
      "asset": "BTCUSDT",
      "side": "long",
      "entry_price": 45000,
      "exit_price": 46000,
      "pnl": 100,
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

#### Create Trade
```http
POST /api/trades
```

**Body:**
```json
{
  "asset": "BTCUSDT",
  "side": "long",
  "entry_price": 45000,
  "exit_price": 46000,
  "quantity": 0.1,
  "stop_loss": 44000,
  "take_profit": 47000,
  "bias": "bullish",
  "model": "trend_following",
  "confirmations": 3,
  "notes": "Strong breakout pattern"
}
```

#### Update Trade
```http
PUT /api/trades/{id}
```

#### Delete Trade
```http
DELETE /api/trades/{id}
```

### Bybit Integration

#### Save API Credentials
```http
POST /api/save_bybit_credentials
```

**Body:**
```json
{
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "network": "mainnet",
  "remember_me": true
}
```

#### Sync Trades
```http
POST /api/sync_bybit_trades
```

**Response:**
```json
{
  "status": "success",
  "imported": 5,
  "duplicates": 2,
  "errors": []
}
```

#### Get Account Balance
```http
GET /api/bybit/balance
```

**Response:**
```json
{
  "usdt_equity": 1250.50,
  "total_balance": 1300.75,
  "available_balance": 1200.25
}
```

#### Extended Data Sync
```http
POST /api/sync_extended_data
```

Syncs positions, orders, and balance history.

### Analytics

#### Calendar Data
```http
GET /api/calendar_data
```

**Response:**
```json
{
  "events": [
    {
      "title": "P&L: +$100",
      "start": "2024-01-10",
      "color": "green"
    }
  ]
}
```

#### Risk Metrics
```http
GET /api/risk_metrics
```

**Response:**
```json
{
  "total_trades": 50,
  "win_rate": 0.65,
  "profit_factor": 1.8,
  "max_drawdown": -15.2,
  "sharpe_ratio": 1.2
}
```

#### Time Analytics
```http
GET /api/time_analytics
```

**Response:**
```json
{
  "hourly_performance": {
    "09:00": 0.05,
    "10:00": 0.12,
    "11:00": -0.02
  },
  "daily_performance": {
    "Monday": 0.08,
    "Tuesday": 0.15,
    "Wednesday": -0.03
  }
}
```

### User Management

#### Get Users
```http
GET /api/users
```

#### Create User
```http
POST /api/users
```

**Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

#### Switch User
```http
POST /api/switch_user/{id}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "status_code": 400
}
```

### Common Error Codes

- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

Currently no rate limiting is implemented. Future versions will include:
- 100 requests per minute per IP
- 1000 requests per hour per user

## WebSocket Support

Future versions will support WebSocket connections for real-time data:
- Live price updates
- Real-time trade notifications
- Account balance changes

## SDK Examples

### Python
```python
import requests

# Get trades
response = requests.get('http://localhost:5000/api/trades')
trades = response.json()['trades']

# Create trade
trade_data = {
    'asset': 'BTCUSDT',
    'side': 'long',
    'entry_price': 45000,
    'exit_price': 46000
}
response = requests.post('http://localhost:5000/api/trades', json=trade_data)
```

### JavaScript
```javascript
// Get trades
const response = await fetch('/api/trades');
const { trades } = await response.json();

// Create trade
const tradeData = {
  asset: 'BTCUSDT',
  side: 'long',
  entry_price: 45000,
  exit_price: 46000
};
const response = await fetch('/api/trades', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(tradeData)
});
```

## Testing

Use the built-in test endpoints:
- `GET /api/test/health` - Health check
- `GET /api/test/database` - Database connectivity
- `GET /api/test/bybit` - Bybit API connectivity

## Changelog

### v1.0.0 (2024-01-10)
- Initial API release
- Full CRUD operations for trades
- Bybit integration
- Analytics endpoints
- User management
