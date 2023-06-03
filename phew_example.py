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
        pass

    def connect_to_network(self, ssid:str, password:st=None):
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
            return render_template("index.html")
        if request.method == 'POST':
            text = request.form.get("text", None)
            logging.debug(f"Posted message: {text}")
            return render_template("index.html", text=text)

    def wrong_host_redirect(self, request):
        # Captive portal redirects any other host request to self.DOMAIN
        body = "<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL='http://"+self.DOMAIN+"'/ /></head>"
        logging.debug("Redirecting to https://"+self.DOMAIN+"/")
        return body

    def hotspot(self, request):
        """ Redirect to Index Page """
        return render_template("index.html")

    def catch_all(self, request):
        """ Catch all requests and redirect if necessary """
        if request.headers.get("host") != self.DOMAIN:
            return redirect("http://"+self.DOMAIN+"/wrong-host-redirect")

""" A Global Singleton of the class """
wifi = Wifi()

""" Use decorators to bind the wifi methods to the requests """

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

