#!/usr/bin/env python3
"""
Office IoT Control Server

HTTP API server for Computer Club office IoT devices.
Provides endpoints for LED control and door lock management.

Port 8878:
  - POST: Control commands from chatbot ($led, $letmein)
  - GET: Status polling from doorbot (checks letmein flag)

Author: Computer Club @ WMU
License: GPL-3.0
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any
from threading import Thread, Lock

import hmac
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8878))
UNLOCK_DURATION = int(os.getenv('UNLOCK_DURATION', 10))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
API_KEY = os.getenv('API_KEY', '')

# Logging setup
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('office-iot')

# Valid LED animation types
VALID_LED_TYPES = [
    'color', 'chase', 'rainbow', 'random',
    'solid', 'breathe', 'strobe', 'fire', 'meteor', 'scanner',
    'sparkle', 'police', 'gradient', 'wave', 'candy', 'off'
]

# Global state storage
state_lock = Lock()
device_state = {
    'letmein': False,
    'sound': '',
    'sounds': [],
    'red': 0,
    'green': 0,
    'blue': 0,
    'type': 'color',
    'hold_time': 0,
    'timestamp': int(time.time()),
    'unlock_expires': 0
}

# Persistent user log directory
USER_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Doorbot', 'user-logs')
USER_LOG_FILE = os.path.join(USER_LOG_DIR, 'unlock_log.json')

# Doorbot unlock log (last 100 events, backed by disk)
unlock_log_lock = Lock()
unlock_log = []

# Doorbot health state
doorbot_health_lock = Lock()
doorbot_health = {}


def _ensure_log_dir():
    """Create the user-logs directory if it doesn't exist."""
    os.makedirs(USER_LOG_DIR, exist_ok=True)


def _load_log_from_disk():
    """Load existing unlock log from disk on startup."""
    global unlock_log
    try:
        if os.path.isfile(USER_LOG_FILE):
            with open(USER_LOG_FILE, 'r') as f:
                unlock_log = json.load(f)
            logger.info(f"Loaded {len(unlock_log)} log entries from {USER_LOG_FILE}")
    except Exception as e:
        logger.error(f"Failed to load log from disk: {e}")
        unlock_log = []


def _save_log_to_disk():
    """Write the current unlock log to disk. Must be called with unlock_log_lock held."""
    try:
        _ensure_log_dir()
        with open(USER_LOG_FILE, 'w') as f:
            json.dump(unlock_log, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save log to disk: {e}")


def log_unlock_event(event: Dict[str, Any]) -> None:
    """Append an unlock event to the log and persist to disk."""
    with unlock_log_lock:
        unlock_log.append(event)
        # Keep last 500 events on disk
        if len(unlock_log) > 500:
            del unlock_log[:-500]
        _save_log_to_disk()
    logger.info(f"Unlock event logged: {event}")


class StateManager:
    """Manages device state with thread-safe operations."""

    @staticmethod
    def get_state() -> Dict[str, Any]:
        """Get current device state."""
        with state_lock:
            return device_state.copy()

    @staticmethod
    def update_state(updates: Dict[str, Any]) -> None:
        """Update device state with new values."""
        with state_lock:
            device_state.update(updates)
            device_state['timestamp'] = int(time.time())
            logger.info(f"State updated: {updates}")

    @staticmethod
    def set_unlock(duration: int, sound: str = '', hold_time: int = 0, sender: str = '') -> None:
        """Set door unlock for specified duration."""
        with state_lock:
            device_state['letmein'] = True
            device_state['sound'] = sound
            device_state['hold_time'] = hold_time
            device_state['unlock_expires'] = int(time.time()) + duration
            device_state['timestamp'] = int(time.time())
            logger.info(f"Door unlock set for {duration} seconds, sound: {sound or 'random'}, sender: {sender or 'unknown'}")

    @staticmethod
    def check_unlock_expiry() -> None:
        """Check if unlock duration has expired and reset."""
        with state_lock:
            if device_state['letmein'] and time.time() >= device_state['unlock_expires']:
                device_state['letmein'] = False
                device_state['sound'] = ''
                device_state['hold_time'] = 0
                device_state['timestamp'] = int(time.time())
                logger.info("Door unlock expired, reset to locked")


def unlock_monitor():
    """Background thread to monitor and reset unlock state."""
    while True:
        StateManager.check_unlock_expiry()
        time.sleep(1)


# Create Flask app
app = Flask('office-iot')
CORS(app)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth_header[len('Bearer '):]
        if not hmac.compare_digest(token, API_KEY):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/', methods=['POST'])
@require_auth
def control():
    """
    Control endpoint for LED and door lock - EXACT match for old dot server.

    POST / (port 8878)
    Body: {
        "status": {
            "red": 0-255,
            "green": 0-255,
            "blue": 0-255,
            "type": "color|chase|rainbow|random|solid|breathe|strobe|fire|meteor|scanner|sparkle|police|gradient|wave|candy|off",
            "letmein": true|false
        }
    }

    Returns: 200 OK (same as original)
    """
    try:
        data = request.get_json()

        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing "status" field'
            }), 400

        status_data = data['status']
        updates = {}

        # Handle LED color updates
        if 'red' in status_data:
            updates['red'] = max(0, min(255, int(status_data['red'])))
        if 'green' in status_data:
            updates['green'] = max(0, min(255, int(status_data['green'])))
        if 'blue' in status_data:
            updates['blue'] = max(0, min(255, int(status_data['blue'])))

        # Handle LED type
        if 'type' in status_data:
            led_type = status_data['type']
            if led_type in VALID_LED_TYPES:
                updates['type'] = led_type

        # Update LED state if any LED params provided
        if updates:
            StateManager.update_state(updates)

        # Handle door unlock
        if 'letmein' in status_data and status_data['letmein']:
            sound = status_data.get('sound', '')
            hold_time = int(status_data.get('hold_time', 0))
            sender = status_data.get('sender', '')
            StateManager.set_unlock(UNLOCK_DURATION, sound, hold_time, sender)

            # Log the unlock event immediately (persistent to disk)
            log_unlock_event({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'epoch': int(time.time()),
                'sender': sender or 'unknown',
                'sound': sound or 'random',
                'source': 'chatbot',
            })

        # Return simple 200 OK (like original server)
        return '', 200

    except Exception as e:
        logger.error(f"Error in control endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/', methods=['GET'])
@require_auth
def status():
    """
    Status endpoint for doorbot polling.

    GET / (port 8878)
    Returns: {"letmein": true/false, ...}
    """
    try:
        return jsonify(StateManager.get_state())

    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/sounds', methods=['POST'])
@require_auth
def update_sounds():
    """Update available sound list (pushed by doorbot Pi)."""
    try:
        data = request.get_json()
        if not data or 'sounds' not in data:
            return jsonify({'error': 'Missing "sounds" field'}), 400
        StateManager.update_state({'sounds': data['sounds']})
        return '', 200
    except Exception as e:
        logger.error(f"Error in sounds endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/log', methods=['POST'])
@require_auth
def post_log():
    """Receive unlock event log from doorbot."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing JSON body'}), 400
        data['source'] = 'doorbot'
        log_unlock_event(data)
        return '', 200
    except Exception as e:
        logger.error(f"Error in log POST endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/log', methods=['GET'])
@require_auth
def get_log():
    """Return recent unlock history."""
    try:
        with unlock_log_lock:
            return jsonify(list(unlock_log))
    except Exception as e:
        logger.error(f"Error in log GET endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health/doorbot', methods=['GET'])
@require_auth
def get_doorbot_health():
    """Return last heartbeat from doorbot."""
    try:
        with doorbot_health_lock:
            if not doorbot_health:
                return jsonify({'error': 'No heartbeat received yet'}), 404
            return jsonify(doorbot_health.copy())
    except Exception as e:
        logger.error(f"Error in doorbot health endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health/doorbot', methods=['POST'])
@require_auth
def post_doorbot_health():
    """Receive heartbeat from doorbot."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing JSON body'}), 400
        with doorbot_health_lock:
            doorbot_health.clear()
            doorbot_health.update(data)
            doorbot_health['server_received'] = int(time.time())
        logger.debug(f"Doorbot heartbeat: {data}")
        return '', 200
    except Exception as e:
        logger.error(f"Error in doorbot health POST endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time())
    })


def main():
    """Main entry point."""
    # Load persistent logs from disk
    _ensure_log_dir()
    _load_log_from_disk()

    logger.info("=" * 60)
    logger.info("Office IoT Control Server")
    logger.info("=" * 60)
    logger.info(f"Listening on: http://{HOST}:{PORT}")
    logger.info(f"  POST / - Control (chatbot commands)")
    logger.info(f"  GET  / - Status (doorbot polling)")
    logger.info(f"  POST /log - Doorbot unlock event log")
    logger.info(f"  GET  /log - Recent unlock history")
    logger.info(f"  POST /health/doorbot - Doorbot heartbeat")
    logger.info(f"  GET  /health/doorbot - Doorbot health status")
    logger.info(f"  User logs: {USER_LOG_DIR}")
    logger.info(f"Unlock duration: {UNLOCK_DURATION} seconds")
    logger.info("=" * 60)

    # Start unlock monitor thread
    monitor_thread = Thread(target=unlock_monitor, daemon=True)
    monitor_thread.start()
    logger.info("Unlock monitor thread started")

    if not API_KEY:
        logger.warning("WARNING: API_KEY is not set. All requests will be rejected.")

    # Run server
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )


if __name__ == '__main__':
    main()
