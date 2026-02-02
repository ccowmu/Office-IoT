# Deployment Guide

## Deploying to newyakko.cs.wmich.edu

### Prerequisites

- SSH access to newyakko.cs.wmich.edu
- Docker and docker-compose installed (already present)
- Sudo permissions for port binding

### Step 1: Clone Repository

```bash
ssh sysadmin@141.218.143.78
cd ~
git clone https://github.com/ccowmu/Office-IoT.git
cd Office-IoT
```

### Step 2: Configure Environment

```bash
cp .env.example .env
nano .env  # Edit if needed (defaults should work)
```

### Step 3: Build and Start

```bash
# Build Docker image
docker-compose build

# Start server
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Step 4: Verify Server

```bash
# Test control endpoint
curl -X POST http://localhost:8878/control \
  -H "Content-Type: application/json" \
  -d '{"status": {"red": 255, "green": 0, "blue": 0}}'

# Test status endpoint
curl http://localhost:8877/status

# Check health
curl http://localhost:8878/health
```

Server should now be accessible at:
- Control: `http://newyakko.cs.wmich.edu:8878/control`
- Status: `http://newyakko.cs.wmich.edu:8877/status`

### Step 5: Set Up Auto-Start (Optional)

The Docker container is set to `restart: always`, so it will automatically start on system boot.

---

## Update Doorbot

### Raspberry Pi Configuration

SSH into the Raspberry Pi doorbot:

```bash
ssh Janus@<doorbot-ip>
```

Edit the doorbot client:

```bash
nano ~/doorbot/doorbot_client.py
```

Update the server URL:

```python
# Change from:
SERVER_URL = "http://dot.cs.wmich.edu:8877"

# To:
SERVER_URL = "http://newyakko.cs.wmich.edu:8877/status"
```

Restart the doorbot service:

```bash
sudo systemctl restart doorbot-client
sudo systemctl status doorbot-client
```

Verify it's polling:

```bash
sudo journalctl -u doorbot-client -f
```

---

## Update Chatbot Commands

### Update ccawmunity Repository

On newyakko, edit the chatbot commands:

```bash
cd ~/ccawmunity/chatbot/commandcenter/commands
```

#### Update led.py

```bash
nano led.py
```

Change:
```python
requests.post("http://dot.cs.wmich.edu:8878", data=json.dumps(data))
```

To:
```python
requests.post("http://newyakko.cs.wmich.edu:8878/control", 
              data=json.dumps(data),
              headers={"Content-Type": "application/json"})
```

#### Update letmein.py

```bash
nano letmein.py
```

Change both POST requests from:
```python
requests.post("http://dot.cs.wmich.edu:8878", data=json.dumps(data))
```

To:
```python
requests.post("http://newyakko.cs.wmich.edu:8878/control",
              data=json.dumps(data),
              headers={"Content-Type": "application/json"})
```

#### Update door.py

```bash
nano door.py
```

Change:
```python
r = requests.get("http://dot.cs.wmich.edu:8877").text
```

To:
```python
response = requests.get("http://newyakko.cs.wmich.edu:8877/status")
data = response.json()
r = f"Door: {'UNLOCKED 🔓' if data['letmein'] else 'LOCKED 🔒'}"
```

### Restart Chatbot

```bash
cd ~/ccawmunity
docker-compose restart
```

---

## Testing End-to-End

### Test from Matrix Chat

In your Matrix chat room:

```
$door
```
Should return: `Door: LOCKED 🔒`

```
$led #ff0000 color
```
Should return: `Set color to: #ff0000 (color)`

```
$letmein
```
Should return: `Door unlocked and now locked again.`

### Monitor on Server

Watch the Office-IoT server logs:

```bash
cd ~/Office-IoT
docker-compose logs -f
```

You should see:
- POST requests from chatbot commands
- GET requests from doorbot polling (every 1 second)

---

## Troubleshooting

### Server Not Starting

```bash
# Check if ports are already in use
sudo netstat -tlnp | grep -E "8877|8878"

# Check Docker logs
docker-compose logs

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Doorbot Not Connecting

```bash
# On doorbot, check if it can reach server
curl http://newyakko.cs.wmich.edu:8877/status

# Check doorbot logs
sudo journalctl -u doorbot-client -f

# Test network connectivity
ping newyakko.cs.wmich.edu
```

### Chatbot Commands Not Working

```bash
# Test endpoint directly from newyakko
curl -X POST http://localhost:8878/control \
  -H "Content-Type: application/json" \
  -d '{"status": {"letmein": true}}'

# Check chatbot logs
cd ~/ccawmunity
docker-compose logs -f bot
```

### Firewall Issues

```bash
# Check if INPUT allows connections
sudo iptables -L INPUT -n -v

# If blocked, add rule (usually not needed on newyakko)
sudo iptables -I INPUT -p tcp --dport 8878 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8877 -j ACCEPT
```

---

## Monitoring

### View Live Logs

```bash
cd ~/Office-IoT
docker-compose logs -f
```

### Check Server Status

```bash
curl http://newyakko.cs.wmich.edu:8878/health
```

### Monitor Resource Usage

```bash
docker stats office-iot-server
```

---

## Updating

```bash
cd ~/Office-IoT
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Rollback to Old Server (Emergency)

If you need to switch back to dot.cs.wmich.edu:

1. Ensure dot server is running
2. Revert chatbot commands to use `dot.cs.wmich.edu:8878`
3. Revert doorbot to use `dot.cs.wmich.edu:8877`
4. Restart services
5. Stop Office-IoT server: `docker-compose down`

---

## Production Checklist

- [ ] Server deployed and running on newyakko
- [ ] Health check returns 200 OK
- [ ] Doorbot updated and polling new server
- [ ] Doorbot logs show successful polling
- [ ] Chatbot commands updated (led.py, letmein.py, door.py)
- [ ] Chatbot restarted
- [ ] `$door` command works
- [ ] `$led` command works
- [ ] `$letmein` command works
- [ ] Door physically unlocks when triggered
- [ ] LED lights respond to commands
- [ ] Auto-restart configured (docker-compose restart: always)

---

## Contact

For issues or questions:
- GitHub: https://github.com/ccowmu/Office-IoT/issues
- Computer Club Discord/Matrix
