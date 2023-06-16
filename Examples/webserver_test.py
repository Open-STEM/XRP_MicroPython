from XRPLib.defaults import *
import time
from machine import Timer

# Binding functions to the arrow buttons
webserver.registerForwardButton(lambda: drivetrain.set_effort(0.5, 0.5))
webserver.registerLeftButton(lambda: drivetrain.set_effort(-0.5, 0.5))
webserver.registerRightButton(lambda: drivetrain.set_effort(0.5, -0.5))
webserver.registerBackwardButton(lambda: drivetrain.set_effort(-0.5, -0.5))
webserver.registerStopButton(lambda: drivetrain.set_effort(0, 0))

# Binding functions to custom buttons
webserver.add_button("test", lambda: print("test"))
webserver.add_button("blink", lambda: print(led.blink(2)))
webserver.add_button("LED_Off", lambda: led.off())

# Logging static data to the webserver
webserver.log_data("test", "test")
webserver.log_data("List", [1,2,3])
webserver.log_data("Dict", {"a":1,"b":2,"c":3})
webserver.log_data("Tuple", (1,2,3))

def log_time_and_range():
    # This function is called every second to update the data on the webserver
    webserver.log_data("Time", time.time())
    webserver.log_data("Range", rangefinder.distance())
    webserver.log_data("Left Motor", left_motor.get_position())
    webserver.log_data("Right Motor", right_motor.get_position())
    webserver.log_data("Button State", button.is_pressed())

timer = Timer(-1)
timer.init(freq=1, mode=Timer.PERIODIC, callback=lambda t: log_time_and_range())

webserver.start_server(1)
