# API Documentation

## Overview

The Office-IoT server provides two HTTP endpoints for controlling office devices.

## Endpoints

### Control Endpoint (Port 8878)

**POST /control**

Controls LED lights and triggers door unlock.

#### Request

```http
POST /control HTTP/1.1
Content-Type: application/json

{
  "status": {
    "red": 128,
    "green": 255,
    "blue": 0,
    "type": "color",
    "letmein": true
  }
}
```

#### Parameters

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `red` | int | 0-255 | Red LED intensity |
| `green` | int | 0-255 | Green LED intensity |
| `blue` | int | 0-255 | Blue LED intensity |
| `type` | string | see below | LED animation mode |
| `letmein` | boolean | true/false | Trigger door unlock |

**LED Types:**
- `color` - Solid color
- `chase` - Chase animation
- `rainbow` - Rainbow cycle
- `random` - Random colors

#### Response

```json
{
  "success": true,
  "message": "Status updated",
  "state": {
    "red": 128,
    "green": 255,
    "blue": 0,
    "type": "color",
    "letmein": true,
    "timestamp": 1738463755,
    "unlock_expires": 1738463765
  }
}
```

#### Error Response

```json
{
  "success": false,
  "error": "Missing 'status' field"
}
```

---

### Status Endpoint (Port 8877)

**GET /status**

Returns current device state. Used by doorbot for polling.

#### Request

```http
GET /status HTTP/1.1
```

#### Response

```json
{
  "letmein": false,
  "red": 128,
  "green": 255,
  "blue": 0,
  "type": "color",
  "timestamp": 1738463755,
  "unlock_expires": 0
}
```

## Examples

### Python (requests)

```python
import requests
import json

# Control LED lights
response = requests.post(
    "http://newyakko.cs.wmich.edu:8878/control",
    data=json.dumps({
        "status": {
            "red": 255,
            "green": 0,
            "blue": 0,
            "type": "color"
        }
    })
)
print(response.json())

# Trigger door unlock
response = requests.post(
    "http://newyakko.cs.wmich.edu:8878/control",
    data=json.dumps({
        "status": {
            "letmein": True
        }
    })
)
print(response.json())

# Check status
response = requests.get("http://newyakko.cs.wmich.edu:8877/status")
print(response.json())
```

### cURL

```bash
# Set LED to green
curl -X POST http://newyakko.cs.wmich.edu:8878/control \
  -H "Content-Type: application/json" \
  -d '{"status": {"red": 0, "green": 255, "blue": 0, "type": "color"}}'

# Unlock door
curl -X POST http://newyakko.cs.wmich.edu:8878/control \
  -H "Content-Type: application/json" \
  -d '{"status": {"letmein": true}}'

# Check status
curl http://newyakko.cs.wmich.edu:8877/status
```

### JavaScript (fetch)

```javascript
// Control LED
fetch('http://newyakko.cs.wmich.edu:8878/control', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    status: {
      red: 255,
      green: 165,
      blue: 0,
      type: 'rainbow'
    }
  })
})
  .then(response => response.json())
  .then(data => console.log(data));

// Check status
fetch('http://newyakko.cs.wmich.edu:8877/status')
  .then(response => response.json())
  .then(data => console.log(data));
```

## State Management

### Door Unlock Behavior

When `letmein: true` is sent:
1. Server sets `letmein` flag to `true`
2. Server sets `unlock_expires` timestamp (current time + `UNLOCK_DURATION`)
3. Doorbot polls and detects `letmein: true`
4. Doorbot actuates lock mechanism
5. After `UNLOCK_DURATION` seconds (default: 10), server automatically resets `letmein` to `false`

### LED State Persistence

LED color and type persist until explicitly changed. The server maintains the last set values.

## Integration

### Doorbot (Raspberry Pi)

Update `doorbot_client.py`:

```python
SERVER_URL = "http://newyakko.cs.wmich.edu:8877/status"
POLL_INTERVAL = 1  # seconds

while True:
    response = requests.get(SERVER_URL)
    data = response.json()
    
    if data.get('letmein'):
        unlock_door()
    
    time.sleep(POLL_INTERVAL)
```

### Chatbot Commands

Update ccawmunity commands:

**led.py:**
```python
response = requests.post(
    "http://newyakko.cs.wmich.edu:8878/control",
    data=json.dumps({
        "status": {
            "red": red,
            "green": green,
            "blue": blue,
            "type": typ
        }
    })
)
```

**letmein.py:**
```python
response = requests.post(
    "http://newyakko.cs.wmich.edu:8878/control",
    data=json.dumps({
        "status": {
            "letmein": True
        }
    })
)
```

**door.py:**
```python
response = requests.get("http://newyakko.cs.wmich.edu:8877/status")
data = response.json()
return f"Door: {'UNLOCKED' if data['letmein'] else 'LOCKED'}"
```

## Health Check

**GET /health**

Returns server health status.

```bash
curl http://newyakko.cs.wmich.edu:8878/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": 1738463755
}
```
