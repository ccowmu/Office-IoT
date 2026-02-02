#!/usr/bin/env python3
"""
Test script for Office-IoT server

Tests all API endpoints and behaviors.
"""

import requests
import json
import time
import sys

BASE_URL_CONTROL = "http://localhost:8878"
BASE_URL_STATUS = "http://localhost:8877"


def test_health():
    """Test health check endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL_CONTROL}/health")
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'
        print("✓ Health check passed")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_led_control():
    """Test LED control."""
    print("\nTesting LED control...")
    try:
        # Set LED to red
        response = requests.post(
            f"{BASE_URL_CONTROL}/control",
            json={
                "status": {
                    "red": 255,
                    "green": 0,
                    "blue": 0,
                    "type": "color"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert data['state']['red'] == 255
        print("✓ LED color control passed")
        
        # Set LED to rainbow
        response = requests.post(
            f"{BASE_URL_CONTROL}/control",
            json={
                "status": {
                    "type": "rainbow"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['state']['type'] == 'rainbow'
        print("✓ LED type control passed")
        
        return True
    except Exception as e:
        print(f"✗ LED control failed: {e}")
        return False


def test_status_endpoint():
    """Test status polling endpoint."""
    print("\nTesting status endpoint...")
    try:
        response = requests.get(f"{BASE_URL_STATUS}/status")
        assert response.status_code == 200
        data = response.json()
        assert 'letmein' in data
        assert 'red' in data
        assert 'green' in data
        assert 'blue' in data
        assert 'type' in data
        assert 'timestamp' in data
        print("✓ Status endpoint passed")
        return True
    except Exception as e:
        print(f"✗ Status endpoint failed: {e}")
        return False


def test_door_unlock():
    """Test door unlock functionality."""
    print("\nTesting door unlock...")
    try:
        # Trigger unlock
        response = requests.post(
            f"{BASE_URL_CONTROL}/control",
            json={
                "status": {
                    "letmein": True
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['state']['letmein'] == True
        print("✓ Door unlock trigger passed")
        
        # Check status reflects unlock
        response = requests.get(f"{BASE_URL_STATUS}/status")
        data = response.json()
        assert data['letmein'] == True
        print("✓ Unlock state visible in status")
        
        # Wait for auto-reset (should be ~10 seconds)
        print("  Waiting for auto-reset (10 seconds)...")
        time.sleep(11)
        
        response = requests.get(f"{BASE_URL_STATUS}/status")
        data = response.json()
        assert data['letmein'] == False
        print("✓ Auto-reset after timeout passed")
        
        return True
    except Exception as e:
        print(f"✗ Door unlock failed: {e}")
        return False


def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    try:
        # Missing status field
        response = requests.post(
            f"{BASE_URL_CONTROL}/control",
            json={}
        )
        assert response.status_code == 400
        print("✓ Missing field error handling passed")
        
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Office-IoT Server Test Suite")
    print("=" * 60)
    
    tests = [
        test_health,
        test_status_endpoint,
        test_led_control,
        test_error_handling,
        test_door_unlock,  # Last because it takes time
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
