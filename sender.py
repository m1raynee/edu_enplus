from paho.mqtt.client import Client
try:
    from .config import mqtt_server_ip
except:
    mqtt_server_ip = "192.168.65.177"


client = Client()
client.connect(mqtt_server_ip)

while True:
    msg = input()
    client.publish(*msg.split(maxsplit=1))