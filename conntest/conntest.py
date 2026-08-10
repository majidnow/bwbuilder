import socket
import time

SERVER_HOST = "192.168.137.10"   # server address or IP
SERVER_PORT = 20000              # port number
N = 1                         # number of connections
DELAY = 0.01                     # seconds between connections

for i in range(N):
    try:
        print(f"[{i+1}/{N}] Connecting to {SERVER_HOST}:{SERVER_PORT}...")
        with socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=5):
            print("Connection successful ✅")
    except Exception as e:
        print(f"Connection failed ❌ ({e})")
    # time.sleep(DELAY)

# pause before exiting
input("\nPress Enter to exit...")