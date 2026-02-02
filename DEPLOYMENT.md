# Deployment Guide

## Deploy on newyakko

```bash
ssh sysadmin@141.218.143.78
cd ~
git clone https://github.com/ccowmu/Office-IoT.git
cd Office-IoT
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8878
```

## Update Chatbot

Edit commands in `~/ccawmunity/chatbot/commandcenter/commands/`:

**led.py**:
```python
# Line ~41, change:
requests.post("http://dot.cs.wmich.edu:8878", data=json.dumps(data))
# To:
requests.post("http://newyakko.cs.wmich.edu:8878", data=json.dumps(data))
```

**letmein.py**:
```python
# Line ~27, change:
response = requests.post("http://dot.cs.wmich.edu:8878", data=json.dumps(data))
# To:
response = requests.post("http://newyakko.cs.wmich.edu:8878", data=json.dumps(data))

# Line ~35, change:
reset_response = requests.post("http://dot.cs.wmich.edu:8878", data=json.dumps(data_reset))
# To:
reset_response = requests.post("http://newyakko.cs.wmich.edu:8878", data=json.dumps(data_reset))
```

Restart chatbot:
```bash
cd ~/ccawmunity
docker-compose restart bot
```

## Update Doorbot

SSH to the Raspberry Pi:
```bash
ssh Janus@<doorbot-ip>
```

Edit `/home/Janus/doorbot/doorbot_client.py`:
```python
# Change:
SERVER_URL = "http://dot.cs.wmich.edu:8878"
# To:
SERVER_URL = "http://newyakko.cs.wmich.edu:8878"
```

Restart service:
```bash
sudo systemctl restart doorbot-client
sudo journalctl -u doorbot-client -f
```

## Test

In Matrix chat:
```
$led #00ff00 color
$letmein
```

Watch logs:
```bash
cd ~/Office-IoT
docker-compose logs -f
```

## Troubleshooting

Server not responding:
```bash
docker-compose logs
docker-compose restart
```

Chatbot not connecting:
```bash
cd ~/ccawmunity
docker-compose logs bot
```

Doorbot not polling:
```bash
# On the Pi:
sudo systemctl status doorbot-client
sudo journalctl -u doorbot-client -n 50
```
