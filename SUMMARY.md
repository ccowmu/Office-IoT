# Office-IoT Project Summary

## What Was Created

A complete HTTP API server replacement for the offline `dot.cs.wmich.edu` server, designed to control Computer Club office IoT devices.

## Repository Structure

```
Office-IoT/
├── server.py              # Main Flask application (dual-port server)
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose orchestration
├── .env.example          # Environment configuration template
├── start.sh              # Quick-start script
├── test.py               # Automated test suite
├── README.md             # Project overview and quick start
├── API.md                # Complete API documentation
├── DEPLOYMENT.md         # Step-by-step deployment guide
└── LICENSE               # GPL-3.0 License

```

## Key Features

### Dual-Port Architecture
- **Port 8878**: Control endpoint (POST) - Accepts LED and door control commands
- **Port 8877**: Status endpoint (GET) - Polled by Raspberry Pi doorbot

### State Management
- Thread-safe state storage
- Automatic door unlock timeout (10 seconds default)
- LED color/animation persistence
- Timestamp tracking

### Docker-Ready
- Alpine-based Python image (lightweight)
- Auto-restart on failure
- Network isolation
- Easy deployment with docker-compose

## API Endpoints

### POST /control (8878)
Control LED lights and trigger door unlock.

Example:
```bash
curl -X POST http://newyakko.cs.wmich.edu:8878/control \
  -H "Content-Type: application/json" \
  -d '{"status": {"red": 255, "green": 0, "blue": 0, "letmein": true}}'
```

### GET /status (8877)
Get current device state (doorbot polling).

Example:
```bash
curl http://newyakko.cs.wmich.edu:8877/status
```

## Deployment Target

**Server**: newyakko.cs.wmich.edu (141.218.143.78)
- 48 CPU cores
- 62 GB RAM
- 4.4 TB storage
- Public campus IP
- Docker installed
- No firewall restrictions

## Integration Points

### 1. Raspberry Pi Doorbot
- **Current**: Polls `dot.cs.wmich.edu:8877` (offline)
- **New**: Polls `newyakko.cs.wmich.edu:8877/status`
- **Change**: Update `SERVER_URL` in `doorbot_client.py`

### 2. Matrix Chatbot Commands
- **Current**: POST to `dot.cs.wmich.edu:8878` (offline)
- **New**: POST to `newyakko.cs.wmich.edu:8878/control`
- **Files to update**:
  - `led.py` - LED light control
  - `letmein.py` - Door unlock
  - `door.py` - Door status check

## Advantages Over Original

1. **Documented**: Complete API docs and deployment guide
2. **Tested**: Automated test suite included
3. **Containerized**: Easy deployment with Docker
4. **Thread-Safe**: Proper locking for concurrent access
5. **Auto-Reset**: Door unlock automatically resets after timeout
6. **Health Check**: Monitoring endpoint for uptime checks
7. **Logging**: Structured logging for debugging
8. **Modern**: Python 3.11, Flask 3.0, Alpine Linux

## Migration Path

1. Deploy Office-IoT server on newyakko
2. Test endpoints manually
3. Update doorbot configuration
4. Update chatbot commands
5. Test end-to-end functionality
6. Monitor for 24 hours
7. Decommission dot.cs.wmich.edu (if appropriate)

## Repository

**GitHub**: https://github.com/ccowmu/Office-IoT

## Status

✅ Code written  
✅ Tested locally  
✅ Documentation complete  
✅ Repository created  
✅ Code pushed to GitHub  
⏳ Awaiting deployment to newyakko  
⏳ Awaiting doorbot update  
⏳ Awaiting chatbot update  

## Next Steps

1. Deploy to newyakko: `cd ~ && git clone https://github.com/ccowmu/Office-IoT.git && cd Office-IoT && ./start.sh`
2. Follow DEPLOYMENT.md for complete setup
3. Test with `test.py`
4. Update integration points
5. Monitor logs for issues

## Notes

- Server has no authentication (by design, for legacy compatibility)
- Should only be accessible on trusted campus network
- Doorbot is on "morgana" WiFi (should have campus network access)
- Original dot.cs.wmich.edu server code was not found
- This is a clean reimplementation based on observed behavior
