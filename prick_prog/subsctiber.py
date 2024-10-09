#!/usr/bin/env python3
from time import sleep
from paho.mqtt.client import Client, MQTTMessage
from ev3dev2.motor import (
    OUTPUT_A,
    OUTPUT_B,
    OUTPUT_C,
    OUTPUT_D,
    MediumMotor,
    LargeMotor,
    SpeedPercent,
    MoveSteering,
)


# Init of Steering motors (B - left, C - right medium motors).
msteer = MoveSteering(OUTPUT_B, OUTPUT_C, motor_class=LargeMotor)
mA = MediumMotor(OUTPUT_A)
mD = MediumMotor(OUTPUT_D)
mA.reset()
# Init of MQTT client, brick is our broker so 172.0.0.1 is the way.
client = Client("brick")
client.connect("127.0.0.1", 1883, 10)


ang = 0
def on_connect(*args):
    global ang
    print("Connected!")
    client.subscribe("topic/speed")
    client.subscribe("topic/movements")


client.on_connect = on_connect

def on_message(client: Client, userdata: str, message: MQTTMessage):
    speed = 0
    global ang

    text = message.payload.decode()
    topic = message.topic

    print(topic, text, mA.degrees)

    if text == "Q":
        msteer.off()
        client.disconnect()
        return

    if topic == "topic/speed":
        speed = int(text)

    if topic == "topic/movements":
        ang = 80

        msteer.on(100, SpeedPercent(0))

        while mA.degrees < 50:
            diff = max(max((ang - mA.degrees)//2, 100), -100) # было max(min)
            mA.on(SpeedPercent(diff))
            mD.on(SpeedPercent(-diff))

        ang = -15

        while mA.degrees > -5:
            diff = max(min((ang - mA.degrees)//2, 100), -100)
            mA.on(SpeedPercent(diff))
            mD.on(SpeedPercent(-diff))

        mA.on(SpeedPercent(0))
        mD.on(SpeedPercent(0))

    msteer.on(100, SpeedPercent(speed))

client.on_message = on_message

msteer.run_direct()
client.loop_forever()
