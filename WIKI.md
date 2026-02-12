# Office-IoT WIKI

The **Office-IoT** server is the central hub for the Computer Club's office automation. It handles communication between the Matrix chatbot and the hardware clients (Doorbot and LEDBox).

---

## 🏛️ Architecture

```
┌──────────────┐      POST /      ┌──────────────────┐      GET /       ┌─────────────┐
│ Matrix Chat  │ ───────────────▶ │  Office-IoT      │ ◀──────────────  │  Hardware   │
│ (Chatbot)    │                  │  (yakko:8878)    │ ──────────────▶  │  Clients    │
└──────────────┘                  └──────────────────┘                  └─────────────┘
```

The server runs as a **Flask** application inside a **Docker** container on `yakko.cs.wmich.edu`. It maintains a global state in memory and provides a simple REST API for control and status polling.

---

## 🚀 API Reference

All requests must include the `Authorization: Bearer <API_KEY>` header.

### `POST /` (Control)
Used by the Matrix chatbot to update device state.

**Payload:**
```json
{
  "status": {
    "red": 0-255,
    "green": 0-255,
    "blue": 0-255,
    "type": "color|chase|rainbow|random",
    "letmein": true|false
  }
}
```

- **LEDs:** Updates color and animation mode.
- **Door:** Setting `letmein: true` triggers a 10-second unlock window.

### `GET /` (Status)
Used by hardware clients (`doorbot_client.py` and `updatecolors.py`) to poll for the current state.

**Response:**
```json
{
  "blue": 0,
  "green": 0,
  "letmein": false,
  "red": 0,
  "timestamp": 1707700000,
  "type": "color",
  "unlock_expires": 1707700010
}
```

### `GET /health`
Returns server health status (no authentication required).

---

## 🛠️ Deployment & Maintenance

The server is deployed using Docker Compose on `yakko`.

```bash
# Location on yakko
cd ~/Office-IoT

# View logs
sudo docker compose logs -f office-iot-server

# Restart service
sudo docker compose restart office-iot-server

# Update from GitHub
git pull
sudo docker compose up -d --build
```

### Environment Variables
The following variables are required in the `.env` file:
- `API_KEY`: Secret token for authentication.
- `PORT`: Port to listen on (default: 8878).
- `UNLOCK_DURATION`: Seconds to hold the door open (default: 10).

---

## 🔒 Security
- **Authentication:** All control and status endpoints are protected by a Bearer token.
- **Network:** The server is typically accessible within the WMU network or via the Tailscale jump host.

---

## 📂 Source Code
- **Repository:** [ccowmu/Office-IoT](https://github.com/ccowmu/Office-IoT)
- **Primary Files:**
  - `server.py`: The main Flask application.
  - `Dockerfile` / `docker-compose.yml`: Container orchestration.

---

## 🔗 See Also

### Door Bot (Office Lock)
- **Wiki:** [Door Bot WIKI](https://github.com/ccowmu/doorbot/blob/main/WIKI.md)
- **GitHub:** [ccowmu/doorbot](https://github.com/ccowmu/doorbot)

### LEDBox (Office Lighting)
- **Wiki:** [LEDBox WIKI](https://github.com/ccowmu/LEDBox/blob/main/WIKI.md)
- **GitHub:** [ccowmu/LEDBox](https://github.com/ccowmu/LEDBox)
