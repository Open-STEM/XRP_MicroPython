import machine
from XRPLib import webserver
import time

selection = 0

def blink():
    for i in range(4):
        print("LED ON")
        time.sleep(0.5)
        print("LED OFF")
        time.sleep(0.5)

def square():
    # simulating a square through printing and waiting
    # use a loop
    print("Making a square")
    for i in range(4):
        print("forward")
        time.sleep(1)
        print("right")
        time.sleep(1)

def keepaway():
    print("Keep away")

def imufun():
    print("IMU Fun")

def forward():
    # go forward simulate
    print("forward")
    time.sleep(1)
    print("stop")

print("start")
server = webserver.WebServer()
server.addButton(blink)
server.addButton(square)
server.addButton(keepaway)
server.addButton(imufun)
server.registerForwardButton(forward)

while True:
    server.run()

