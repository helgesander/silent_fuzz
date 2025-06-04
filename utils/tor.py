import time
import urllib3
from stem import Signal
from stem.control import Controller
from stem.process import launch_tor
import requests
import socks
import socket


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def launch_tor():
    tor_process = launch_tor()
    print("Tor process started")
    return tor_process


def set_tor_proxy():
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    socket.socket = socks.socksocket

def change_tor_ip(retries=3):
    for attempt in range(retries):
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                time.sleep(30)  
                return
        except Exception as e:
            print(f"Error with Tor: {e}")
            if attempt < retries - 1:
                print(f"Попытка {attempt + 1} смены IP не удалась. Повтор через {10} секунд...")

            else:
                print("Все попытки смены IP через Tor завершились неудачно.")
                raise
