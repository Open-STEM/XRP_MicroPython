import machine
from XRPLib import webserver
from Examples.xrp_demo_test import xrp
import time


def forward():
    # go forward simulate
    print("forward")
    xrp.drivetrain.set_effort(0.8, 0.8)

def stop():
    print("stop")
    xrp.drivetrain.stop()

def left():
    print("left")
    xrp.drivetrain.set_effort(-0.8, 0.8)

def right():
    print("right")
    xrp.drivetrain.set_effort(0.8, -0.8)

def back():
    print("back")
    xrp.drivetrain.set_effort(-0.8, -0.8)

def square():
    print("square")
    for i in range(4):
        xrp.drivetrain.straight(12, 0.8)
        xrp.drivetrain.turn(90, 0.8)

print("start")
server = webserver.WebServer()
server.addButton(square)
server.registerForwardButton(forward)
server.registerBackButton(back)
server.registerLeftButton(left)
server.registerRightButton(right)
server.registerStopButton(stop)

while True:
    server.run()
