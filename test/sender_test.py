import paho.mqtt.client as mqtt

# This is the Publisher

server_ip = "192.168.1.38"

client = mqtt.Client(userdata="pc")
client.connect(server_ip, 1883)
client.publish("topic/steer-n-speed", "0 20")
client.disconnect()