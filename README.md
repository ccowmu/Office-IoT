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

## Deployment

```bash
git clone https://github.com/ccowmu/Office-IoT.git
cd Office-IoT
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

## License

GPL-3.0
