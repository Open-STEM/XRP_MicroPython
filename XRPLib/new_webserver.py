import network
import socket
import machine


led = machine.Pin(2, machine.Pin.OUT)
led.off()

with open("lib/XRPLib/dist/index.html") as fd:
    html_template = fd.read()


def connect():
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        print("connecting to network...")
        sta.active(True)
        # sta.connect('your wifi ssid', 'your wifi password')
        sta.connect("Look, Pa! The Internet!", "mustang07")
        while not sta.isconnected():
            pass
    esp_ip = sta.ifconfig()[0]
    print("IP :", esp_ip)


def web_page(request_str):
    if request_str.find("GET /assets/") != -1:
        asset_path = request_str.split()[1]
        asset_path = asset_path[1:]
    
        with open("lib/XRPLib/dist/" + asset_path, "rb") as fd:
            asset = fd.read()

        return asset
    return html_template


def main():
    connect()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 80))
    s.listen(5)  # max of 5 socket connections

    while True:
        client_socket, client_address = s.accept()
        print("Got connection from %s" % str(client_address))

        request = client_socket.recv(1024)
        print("")
        request_str = request.decode("utf-8")
        print("Content:", request_str)
        
        response = web_page(request_str)
        client_socket.send("HTTP/1.1 200 OK\n")
        client_socket.send("Content-Type: text/html\n")
        client_socket.send("Connection: close\n\n")
        if response is not None:
            client_socket.sendall(response)
        client_socket.close()


main()