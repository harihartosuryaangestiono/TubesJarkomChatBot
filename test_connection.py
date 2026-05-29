#!/usr/bin/env python3
"""Quick test script to verify server connection."""

import socket
import json
import sys

def test_server(host="127.0.0.1", port=5001):
    print(f"Testing connection to {host}:{port}...")
    
    try:
        # Connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print("✅ Connected to server")
        
        # Send login
        login_packet = {
            "type": "login",
            "username": "test_user",
            "timestamp": "2024-01-20T10:00:00"
        }
        sock.send(json.dumps(login_packet).encode())
        print("📤 Sent login packet")
        
        # Receive response
        data = sock.recv(4096)
        if data:
            response = json.loads(data.decode())
            print(f"📥 Received: {response}")
            
            if response.get("success"):
                print("✅ Login successful!")
            else:
                print(f"❌ Login failed: {response.get('message')}")
        
        sock.close()
        print("✅ Test complete - Connection working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    test_server(port=port)
