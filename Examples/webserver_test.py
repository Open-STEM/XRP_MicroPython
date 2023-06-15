from XRPLib import webserver
import time
from XRPLib.defaults import *
def square():
    # use a loop
    print("Making a square")
    for i in range(4):
        print("forward")
        drivetrain.straight(30, 0.5)
        print("turn right")
        drivetrain.turn(90, 0.5)

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
server.add_button(square)
server.add_button(keepaway)
server.add_button(imufun)
server.registerForwardButton(forward)
server.registerLeftButton(lambda: led.on())
server.registerRightButton(lambda: led.off())
server.registerStopButton(lambda: led.blink(2))
server.log_data("test", "test")
server.log_data("Int", 123)
server.log_data("Float", 123.456)
server.log_data("Bool", True)
server.log_data("None", None)
server.log_data("List", [1,2,3])
server.log_data("Dict", {"a":1,"b":2,"c":3})
server.log_data("Tuple", (1,2,3))
server.start_server(1)
