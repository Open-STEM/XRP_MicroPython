from XRPLib.webserver import Webserver
from XRPLib.defaults import *
import time

print("start")
webserver.registerForwardButton(lambda: drivetrain.set_effort(0.5, 0.5))
webserver.registerLeftButton(lambda: drivetrain.set_effort(-0.5, 0.5))
webserver.registerRightButton(lambda: drivetrain.set_effort(0.5, -0.5))
webserver.registerBackwardButton(lambda: drivetrain.set_effort(-0.5, -0.5))
webserver.registerStopButton(lambda: drivetrain.set_effort(0, 0))
webserver.log_data("test", "test")
webserver.log_data("Int", 123)
webserver.log_data("Float", 123.456)
webserver.log_data("Bool", True)
webserver.log_data("None", None)
webserver.log_data("List", [1,2,3])
webserver.log_data("Dict", {"a":1,"b":2,"c":3})
webserver.log_data("Tuple", (1,2,3))
print(webserver.display_arrows)
webserver.start_server(1)
