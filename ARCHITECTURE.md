# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Matrix Chat Room                         │
│                    (Computer Club Members)                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Chat Commands:
                       │ $led #ff0000 color
                       │ $letmein
                       │ $door
                       ▼
        ┌──────────────────────────────┐
        │   ccawmunity Chatbot         │
        │   (newyakko Docker)          │
        │                              │
        │   ├─ led.py                  │
        │   ├─ letmein.py              │
        │   └─ door.py                 │
        └──────────┬───────────────────┘
                   │ HTTP POST
                   │ JSON payloads
                   ▼
        ┌──────────────────────────────┐
        │   Office-IoT Server          │
        │   (newyakko Docker)          │
        │                              │
        │   Port 8878: /control ◄──────┤ POST from chatbot
        │   Port 8877: /status  ────►  │ GET polling (1/sec)
        │                              │
        │   State Manager:             │
        │   ├─ LED: {r,g,b,type}       │
        │   ├─ Door: {letmein}         │
        │   └─ Auto-reset timer        │
        └──────────┬───────────────────┘
                   │
                   │ HTTP GET (polling)
                   │ Every 1 second
                   ▼
        ┌──────────────────────────────┐
        │   Raspberry Pi "Doorbot"     │
        │   (morgana WiFi)             │
        │                              │
        │   doorbot_client.py          │
        │   ├─ Polls: /status          │
        │   ├─ Reads: letmein flag     │
        │   └─ GPIO Control            │
        └──────────┬───────────────────┘
                   │
                   │ Physical Control
                   ▼
        ┌──────────────────────────────┐
        │   Physical Hardware          │
        │                              │
        │   ├─ Stepper Motor           │
        │   ├─ Door Lock Mechanism     │
        │   ├─ Position Sensor         │
        │   └─ (Future: LED strips)    │
        └──────────────────────────────┘
```

## Data Flow

### Door Unlock Sequence

```
User types: $letmein
      ↓
Chatbot receives command
      ↓
POST /control {"status": {"letmein": true}}
      ↓
Office-IoT Server:
  - Sets letmein = true
  - Sets unlock_expires = now + 10s
      ↓
Doorbot polls /status (next 1-second cycle)
      ↓
Doorbot reads letmein = true
      ↓
Doorbot activates stepper motor
      ↓
Door unlocks for 10 seconds
      ↓
After 10 seconds:
  - Office-IoT auto-resets letmein = false
  - Doorbot returns lock to original position
```

### LED Control Sequence

```
User types: $led #00ff00 rainbow
      ↓
Chatbot parses color: {r:0, g:255, b:0}
      ↓
POST /control {"status": {"red": 0, "green": 255, "blue": 0, "type": "rainbow"}}
      ↓
Office-IoT Server:
  - Updates LED state
  - Stores: {red: 0, green: 255, blue: 0, type: "rainbow"}
      ↓
(Future) LED controller polls /status
      ↓
(Future) LED strip displays rainbow effect with base color green
```

## Component Details

### Office-IoT Server

**Technology Stack:**
- Python 3.11
- Flask 3.0
- Threading (for dual-port + monitor)
- Alpine Linux (Docker)

**Responsibilities:**
1. Accept control commands via POST
2. Maintain device state in memory
3. Serve state to pollers via GET
4. Auto-reset unlock after timeout
5. Provide health check endpoint

**Thread Architecture:**
```
Main Thread:        Control Server (port 8878)
Background Thread:  Status Server (port 8877)
Daemon Thread:      Unlock Monitor (1 Hz)
```

### Doorbot Client

**Technology Stack:**
- Python 3.12
- RPi.GPIO
- requests library
- systemd service

**Responsibilities:**
1. Poll Office-IoT server every 1 second
2. Check `letmein` flag
3. Control GPIO pins (relay, motor, sensor)
4. Execute physical door unlock sequence
5. Auto-return to locked state

### Chatbot Commands

**Technology Stack:**
- Python 3.11
- Matrix nio client
- requests library
- Docker

**Responsibilities:**
1. Parse user commands
2. Validate input (colors, parameters)
3. Translate to API calls
4. Return status messages to users

## Network Architecture

```
Internet/Campus Network (141.218.143.0/24)
    │
    ├─ newyakko.cs.wmich.edu (141.218.143.78)
    │     ├─ Port 22:   SSH
    │     ├─ Port 80:   HTTP (Caddy)
    │     ├─ Port 443:  HTTPS (Caddy)
    │     ├─ Port 8877: Office-IoT Status ◄── Doorbot
    │     ├─ Port 8878: Office-IoT Control ◄── Chatbot
    │     └─ Docker Networks (internal)
    │
    └─ Raspberry Pi Doorbot (morgana WiFi)
          └─ Polls: newyakko.cs.wmich.edu:8877
```

## State Machine

### Door Lock State

```
       ┌─────────┐
       │ LOCKED  │ ◄──────────────┐
       │ (init)  │                │
       └────┬────┘                │
            │                     │
            │ letmein=true        │ Timeout (10s)
            │ via POST            │ OR manual reset
            ▼                     │
       ┌─────────┐                │
       │UNLOCKING│                │
       │ (motor) │                │
       └────┬────┘                │
            │                     │
            │ Position            │
            │ sensor              │
            ▼                     │
       ┌─────────┐                │
       │UNLOCKED │                │
       │ (hold)  │                │
       └────┬────┘                │
            │                     │
            │ Timer expires       │
            │ (10 seconds)        │
            ▼                     │
       ┌─────────┐                │
       │ LOCKING │                │
       │ (motor) │────────────────┘
       └─────────┘
```

### LED State

```
       ┌─────────┐
       │   OFF   │
       │ (init)  │
       └────┬────┘
            │
            │ Color command
            │ via POST
            ▼
       ┌─────────┐
       │   ON    │
       │ {r,g,b} │
       │  {type} │ ◄──────┐
       └────┬────┘        │
            │             │
            │ New color   │
            │ command     │
            └─────────────┘
        
        (Persists until changed)
```

## Security Considerations

### Current (Legacy Compatible)

- ✗ No authentication
- ✗ No authorization
- ✗ HTTP (not HTTPS)
- ✓ Campus network only
- ✓ Firewall at network edge

### Recommendations for Future

1. **API Key Authentication**
   ```python
   API_KEY = os.getenv('API_KEY')
   if request.headers.get('X-API-Key') != API_KEY:
       return 401
   ```

2. **HTTPS with Reverse Proxy**
   ```
   User → Caddy (HTTPS) → Office-IoT (HTTP local)
   ```

3. **Rate Limiting**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app, default_limits=["100 per hour"])
   ```

4. **IP Allowlist**
   ```python
   ALLOWED_IPS = ['141.218.143.78', '192.168.x.x']
   if request.remote_addr not in ALLOWED_IPS:
       return 403
   ```

## Monitoring & Observability

### Metrics to Track

- Request rate (per minute)
- Error rate (4xx, 5xx responses)
- Door unlock frequency
- LED command frequency
- Doorbot poll success rate
- Average response time

### Logging

```python
# Current logging format:
2024-02-02 01:23:45 - office-iot - INFO - State updated: {'letmein': True}
2024-02-02 01:23:45 - office-iot - INFO - Door unlock set for 10 seconds
2024-02-02 01:23:55 - office-iot - INFO - Door unlock expired, reset to locked
```

### Health Checks

```bash
# Automated health monitoring
while true; do
    curl -sf http://newyakko.cs.wmich.edu:8878/health || \
        echo "ALERT: Office-IoT server down!" | mail -s "Alert" admin@example.com
    sleep 60
done
```

## Scalability

Current design is suitable for:
- ✓ 1 doorbot polling at 1 Hz
- ✓ 10-20 concurrent chatbot users
- ✓ <100 requests per minute

For higher loads, consider:
- Load balancer (multiple instances)
- Redis for shared state
- Message queue (RabbitMQ) for async processing
- Database for audit logging

## Future Enhancements

1. **Persistent State**: Redis/database backend
2. **LED Hardware**: Actual LED strip integration
3. **Web Dashboard**: Real-time status page
4. **Audit Log**: Track all door unlocks
5. **Metrics Dashboard**: Grafana + Prometheus
6. **Mobile App**: Direct control via smartphone
7. **Schedule**: Automatic unlock/lock times
8. **Access Control**: User-based permissions
