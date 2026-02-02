# Office-IoT

HTTP API server for Computer Club office IoT devices (LED lights and door lock control).

## Overview

This server provides REST API endpoints to control:
- **LED Strip Lights** - Color, animations (chase, rainbow, random)
- **Smart Door Lock** - Remote unlock via Raspberry Pi actuator

The server maintains state and is polled by:
- Raspberry Pi "doorbot" (polls every 1 second for unlock commands)
- Matrix chatbot commands (`$led`, `$letmein`, `$door`)

## Architecture

```
Matrix Chatbot ──POST──> Office-IoT Server ──GET (poll)──> Raspberry Pi Doorbot
     ($led)                 (port 8878)                      (actuates lock)
  ($letmein)
   ($door)
```

## API Endpoints

### POST /control (Port 8878)
Control LED lights and door lock.

**Request Body:**
```json
{
  "status": {
    "red": 127,
    "green": 255,
    "blue": 0,
    "type": "color",
    "letmein": true
  }
}
```

**Parameters:**
- `red`, `green`, `blue` (0-255): LED color values
- `type`: `"color"`, `"chase"`, `"rainbow"`, or `"random"`
- `letmein` (boolean): Trigger door unlock

**Response:**
```json
{
  "success": true,
  "message": "Status updated"
}
```

### GET /status (Port 8877)
Query current device status (for doorbot polling).

**Response:**
```json
{
  "letmein": false,
  "red": 127,
  "green": 255,
  "blue": 0,
  "type": "color",
  "timestamp": 1738463755
}
```

## Quick Start

### Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/ccowmu/Office-IoT.git
cd Office-IoT

# Configure environment
cp .env.example .env
nano .env  # Edit settings

# Start server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop server
docker-compose down
```

### Manual Setup

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run server
python3 server.py
```

Server will listen on:
- Port 8878 - Control endpoint
- Port 8877 - Status endpoint

## Configuration

Edit `.env` file:

```env
HOST=0.0.0.0
CONTROL_PORT=8878
STATUS_PORT=8877
UNLOCK_DURATION=10
DEBUG=false
```

## Integration

### Update Doorbot

Edit doorbot's `doorbot_client.py`:

```python
SERVER_URL = "http://newyakko.cs.wmich.edu:8877/status"
```

### Update Chatbot Commands

Edit ccawmunity commands to point to:
```python
requests.post("http://newyakko.cs.wmich.edu:8878/control", ...)
```

## Development

```bash
# Run in debug mode
DEBUG=true python3 server.py

# Run tests
python3 -m pytest tests/

# Simulate doorbot polling
curl http://localhost:8877/status

# Trigger door unlock
curl -X POST http://localhost:8878/control \
  -H "Content-Type: application/json" \
  -d '{"status": {"letmein": true}}'
```

## Security

⚠️ **Important:** This server has no authentication by design (legacy compatibility).
- Should only be accessible on trusted campus network
- Consider adding API key authentication for production
- Use firewall rules to restrict access

## License

GPL-3.0 License - See LICENSE file

## Authors

- Computer Club @ Western Michigan University
- Original dot.cs.wmich.edu server (legacy)
- Redesigned 2026 for newyakko.cs.wmich.edu deployment
