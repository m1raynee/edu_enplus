import paho.mqtt.client as mqtt
from _ip import server_ip
import time

client = mqtt.Client(userdata="pc")
client.connect(server_ip, 1883)

time.sleep(7)
client.publish("topic/steer-n-speed", "40 0")
time.sleep(0.2)
client.publish("topic/steer-n-speed", "-40 0")
time.sleep(0.2)
client.publish("topic/steer-n-speed", "0 -20")
time.sleep(0.5)
client.publish("topic/steer-n-speed", "0 0")
time.sleep(0.5)
client.publish("topic/grabber", "catch")
time.sleep(3)
client.publish("topic/steer-n-speed", "40 0")
time.sleep(0.2)
client.publish("topic/steer-n-speed", "-40 0")
time.sleep(0.2)
client.publish("topic/steer-n-speed", "0 -20")
time.sleep(0.5)
client.publish("topic/grabber", "catch")
time.sleep(3)
client.publish("topic/steer-n-speed", "0 0")
