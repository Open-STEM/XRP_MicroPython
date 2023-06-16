from XRPLib.webserver import Webserver
from XRPLib.defaults import *
import time

print("start")
server = Webserver.get_default_webserver()
server.registerForwardButton(lambda: drivetrain.set_effort(0.5, 0.5))
server.registerLeftButton(lambda: drivetrain.set_effort(-0.5, 0.5))
server.registerRightButton(lambda: drivetrain.set_effort(0.5, -0.5))
server.registerBackwardButton(lambda: drivetrain.set_effort(-0.5, -0.5))
server.registerStopButton(lambda: drivetrain.set_effort(0, 0))
server.log_data("test", "test")
server.log_data("Int", 123)
server.log_data("Float", 123.456)
server.log_data("Bool", True)
server.log_data("None", None)
server.log_data("List", [1,2,3])
server.log_data("Dict", {"a":1,"b":2,"c":3})
server.log_data("Tuple", (1,2,3))
print(server.display_arrows)
server.start_server(1)
