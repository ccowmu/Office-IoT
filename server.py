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

# Global state storage
state_lock = Lock()
device_state = {
    'letmein': False,
    'red': 0,
    'green': 0,
    'blue': 0,
    'type': 'color',
    'timestamp': int(time.time()),
    'unlock_expires': 0
}


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
    def set_unlock(duration: int) -> None:
        """Set door unlock for specified duration."""
        with state_lock:
            device_state['letmein'] = True
            device_state['unlock_expires'] = int(time.time()) + duration
            device_state['timestamp'] = int(time.time())
            logger.info(f"Door unlock set for {duration} seconds")
    
    @staticmethod
    def check_unlock_expiry() -> None:
        """Check if unlock duration has expired and reset."""
        with state_lock:
            if device_state['letmein'] and time.time() >= device_state['unlock_expires']:
                device_state['letmein'] = False
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
            "type": "color|chase|rainbow|random",
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
            if led_type in ['color', 'chase', 'rainbow', 'random']:
                updates['type'] = led_type
        
        # Update LED state if any LED params provided
        if updates:
            StateManager.update_state(updates)
        
        # Handle door unlock
        if 'letmein' in status_data and status_data['letmein']:
            StateManager.set_unlock(UNLOCK_DURATION)
        
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


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time())
    })


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Office IoT Control Server")
    logger.info("=" * 60)
    logger.info(f"Listening on: http://{HOST}:{PORT}")
    logger.info(f"  POST / - Control (chatbot commands)")
    logger.info(f"  GET  / - Status (doorbot polling)")
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
