from paho.mqtt.client import Client
try:
    from .._ip import server_ip
except:
    server_ip = "192.168.65.177"


client = Client()
client.connect(server_ip)

while True:
    msg = input()
    client.publish(*msg.split(maxsplit=1))