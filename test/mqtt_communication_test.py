#!/usr/bin/env python3
import functools
import paho.mqtt.client as mqtt

# This is the Subscriber

client = mqtt.Client(userdata="robot")
client.connect("127.0.0.1", 1883, 60)


def on_connect(client: mqtt.Client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    print("Client " + str(type(client)) + " = " + str(client))
    print("userdata " + str(type(userdata)) + " = " + str(userdata))
    print("flags " + str(type(flags)) + " = " + str(flags))
    client.subscribe("topic/test")
client.on_connect = on_connect


def on_message(client, userdata, msg: mqtt.MQTTMessage):
    if userdata == client.userdata: pass
    if msg.payload.decode() == "Hello world!":
        print("Yes!")
        client.disconnect()
client.on_message = on_message


client.loop_forever()
