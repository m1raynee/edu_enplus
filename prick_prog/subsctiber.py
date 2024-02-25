#!/usr/bin/env python3
from time import sleep
from paho.mqtt.client import Client, MQTTMessage
from ev3dev2.motor import (
    OUTPUT_A,
    OUTPUT_B,
    OUTPUT_C,
    MediumMotor,
    SpeedPercent,
    MoveSteering,
)

grabber = MediumMotor(OUTPUT_A)  # init of Grabber's motor

# Init of Steering motors (B - left, C - right medium motors).
# We'd like to inverse left motor polarity 'cause it's facing different direction.
msteer = MoveSteering(OUTPUT_B, OUTPUT_C, motor_class=MediumMotor)
msteer.set_polarity(MediumMotor.POLARITY_INVERSED, (msteer.left_motor,))


# Init of MQTT client, brick is our broker so 172.0.0.1 is the way.
client = Client("brick")
client.connect("127.0.0.1", 1883, 10)


def on_connect(*args):
    print("Connected!")
    client.subscribe("topic/steer-n-speed")
    client.subscribe("topic/grabber")
    client.subscribe("topic/movements")


client.on_connect = on_connect


def on_message(client: Client, userdata: str, message: MQTTMessage):
    text = message.payload.decode()
    topic = message.topic

    print(topic, text)

    if text == "Q":
        msteer.off()
        client.disconnect()
        return

    if topic == "topic/steer-n-speed":
        steer, speed = text.split()
        if speed == "0":
            msteer.left_motor.on(SpeedPercent(int(steer)))
            msteer.right_motor.on(SpeedPercent(-int(steer)))
            return
        msteer.on(int(steer), SpeedPercent(int(speed)))
    if topic == "topic/grabber":
        if text == "catch":  # grab
            grabber.on_for_seconds(20, 0.5)
            sleep(1)
            msteer.on_for_degrees(0, SpeedPercent(10), 200)
            sleep(1)
            grabber.on_for_seconds(-20, 0.5)
        elif text == "0":  # release
            grabber.on_for_seconds(20, 0.5, brake=False)

client.on_message = on_message

msteer.run_direct()
client.loop_forever()
