from phew import server, template, logging, access_point, dns
from phew.template import render_template
from phew.server import redirect
import gc
import network
import time

class Wifi:

    def __init__(self, network_timeout:int=10):
        gc.threshold(50000) # garbage collection
        self.DOMAIN = "remote.xrp"
        self.timeout = network_timeout
        self.logged_data = {}
        self.buttons = {}
        pass

    def connect_to_network(self, ssid:str, password:str=None):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(ssid, password)
        start_time = time.time()
        while not self.wlan.isconnected():
            print("Connecting to network, may take a second")
            if time.time() > start_time+self.timeout:
                print("Failed to connect to network, please try again")
                self.wlan.disconnect()
                return
            sleep(0.25)
        print("Successfully connected to network")

    def start_server(self, robot_number:int):
        self.access_point = access_point(f"XRP_{robot_number}")
        self.ip = network.WLAN(network.STA_IF).ifconfig()[0]
        logging.info(f"Starting DNS Server at {self.ip}")
        dns.run_catchall(self.ip)
        server.run()
        logging.info("Webserver Started")

    def index_page(self, request):
        """ Render index page and respond to form requests """
        if request.method == 'GET':
            logging.debug("Get request")
            return self._generateHTML()
        if request.method == 'POST':
            text = request.form.get("text", None)
            logging.debug(f"Posted message: {text}")
            self._handleUserFunctionRequest(text)
            return self._generateHTML()

    def wrong_host_redirect(self, request):
        # Captive portal redirects any other host request to self.DOMAIN
        body = "<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL='http://"+self.DOMAIN+"'/ /></head>"
        logging.debug("Redirecting to https://"+self.DOMAIN+"/")
        return body

    def hotspot(self, request):
        """ Redirect to Index Page """
        return self._generateHTML()

    def catch_all(self, request):
        """ Catch all requests and redirect if necessary """
        if request.headers.get("host") != self.DOMAIN:
            return redirect("http://"+self.DOMAIN+"/wrong-host-redirect")
        
    def _handleUserFunctionRequest(self, text) -> bool:
        user_function = self.buttons[text]
        if user_function is None:
            print("User function "+text+" not found")
            return False
        try:
            user_function()
            return True
        except:
            print("User function "+text+" caused an exception")
            return False

    def _generateHTML(self):

        string = _HTML1 + _HTML_ARROWS

        string += f'<h3>Custom Function Bindings:</h3><p>'
        # add each button's href to html
        for button in self.buttons:
            buttonID = self.FUNCTION_PREFIX + button.name + self.FUNCTION_SUFFIX
            string += f'<p><a href=\"{buttonID}"> <span><font size="30px">{button.name}</font></span></a></p>'
            string += "\n"
        string += '<\p>'

        string += f'<h3>Logged Data:</h3><p>'
        # add logged data to the html
        for data_entry in self.logged_data:
            string += f'{data_entry.key}: {data_entry.value}'
            string += "\n"
        string += '<\p>'

        string += _HTML2

        return string

""" Use decorators to bind the wifi methods to the requests """
wifi = Wifi()

@server.route("/", methods=['GET','POST'])
def index(request):
    return wifi.index_page(request)

@server.route("/wrong-host-redirect", methods=['GET'])
def wrong_host_redirect(request):
    return wifi.wrong_host_redirect(request)

@server.route("/hotspot-detect.html", methods=["GET"])
def hotspot(request):
    return wifi.hotspot(request)

@server.catchall()
def catch_all(request):
    return wifi.catch_all(request)

_HTML1 = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">

            <style>
                a { text-decoration: none; }

                html {
                    font-family: Arial;
                    display: inline-block;
                    margin: 0px auto;
                    text-align: center;
                }

            </style>
        </head>

        <body>
            <h2>XRP control page</h2>

            <p>
"""

_HTML_ARROWS = """
        <a href=\"forwardbutton"> <span><font size="30px">&#8593;</font></span></a>
        <p></p>
        <a href=\"leftbutton"> <span><font size="30px">&#8592;</font></span></a>
        &nbsp;&nbsp;
        <a href=\"stopbutton"> <span><font size="30px">&#9744;</font></span></a>
        &nbsp;&nbsp;
        <a href=\"rightbutton"> <span><font size="30px">&#8594;</font></span></a>
        <p></p>
        <a href=\"backbutton"> <span><font size="30px">&#8595;</font></span></a>
"""

_HTML2 = """
            </p>

        </body>

        </html>
"""
