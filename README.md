# Office-IoT

HTTP API server for Computer Club office IoT devices.

Replacement for the old `dot.cs.wmich.edu:8878` server that controls LED lights and the smart door lock.

## What It Does

- **LED Control**: Set colors and animations via Matrix chatbot (`$led` command)
- **Door Control**: Unlock office door remotely (`$letmein` command)
- **State Management**: Maintains device state and auto-resets door unlock after 10 seconds

## API

**Port 8878** handles both control and status:

- **POST /**: Control commands from chatbot
  ```json
  {"status": {"red": 255, "green": 0, "blue": 0, "type": "color", "letmein": true}}
  ```
  Returns: `200 OK`

- **GET /**: Status for doorbot polling
  ```json
  {"letmein": false, "red": 255, "green": 0, "blue": 0, "type": "color", ...}
  ```

## Quick Start

```bash
git clone https://github.com/ccowmu/Office-IoT.git
cd Office-IoT
./start.sh
```

Server runs on `http://localhost:8878`

## Configuration

Edit `.env`:
```bash
HOST=0.0.0.0
PORT=8878
UNLOCK_DURATION=10
DEBUG=false
```

## Deployment

On newyakko.cs.wmich.edu:
```bash
cd ~
git clone https://github.com/ccowmu/Office-IoT.git
cd Office-IoT
docker-compose up -d
```

Update chatbot commands (`led.py`, `letmein.py`):
```python
# Change from:
requests.post("http://dot.cs.wmich.edu:8878", ...)
# To:
requests.post("http://newyakko.cs.wmich.edu:8878", ...)
```

Update doorbot (`/home/Janus/doorbot/doorbot_client.py`):
```python
# Change from:
SERVER_URL = "http://dot.cs.wmich.edu:8878"
# To:
SERVER_URL = "http://newyakko.cs.wmich.edu:8878"
```

## Development

```bash
pip3 install -r requirements.txt
python3 server.py
```

Test:
```bash
# Trigger unlock
curl -X POST http://localhost:8878 -H "Content-Type: application/json" \
  -d '{"status": {"letmein": true}}'

# Check status
curl http://localhost:8878
```

## License

GPL-3.0
