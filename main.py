import time

import cv2 as cv
import numpy as np
import paho.mqtt.client as mqtt
from config import mqtt_server_ip

from video_sources import get_rich_video_capture
from toolbox import ImageToolbox

rich_capture = get_rich_video_capture(1)
it = ImageToolbox()
it.load()
# it.default_chain = it.chain.add(partial(it.resize, factor = 4))

### sadness
def mouse_callback(event, x, y, *args):
    if event != 7:
        return
    ret, img = rich_capture.read()
    if not ret:
        return
    img = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    command = input(f"command ({img[y][x]}): ")
    match command.split():
        case ["col", name]:
            it.set_hsv(img[y][x], name, 10, 40, 40)
            return
        case ["load"]:
            it.load()
            return
        case ["dump"]:
            it.dump()
            return
        case ["set", key]:
            it.settings[key] = x, y
            return
        case _:
            print("unknown command")


cv.namedWindow("image")
cv.namedWindow("transformed")
cv.setMouseCallback("image", mouse_callback)
cv.setMouseCallback("transformed", mouse_callback)
### end of sadness

def main():
    print("Connecting to a server")
    client = mqtt.Client(userdata="pc")
    client.connect(mqtt_server_ip, 1883)
    print("Connected")

    last_command = ("", "")
    kick_timer = 0
    pole_movement_k = 2.5
    memory = []

    while it.tick("q"):
        with it.entry_loop(rich_capture) as img:
            if list(img.centers["red"]) == [0, 0]:
                command = ("topic/speed", 0)
            else:
                d_x = img.centers["yellow"][0] - img.centers["red"][0]
                
                diff = d_x * pole_movement_k
                diff = np.sign(diff) * min(abs(diff), 100)

                d_y = img.centers["yellow"][1] - img.centers["red"][1]
                if d_y < 50 and time.time() - kick_timer > 1:
                    client.publish("topic/movements", 90)
                    kick_timer = time.time()


                command = ("topic/speed", str(int(diff)))

            if command != last_command:
                    last_command = command
                    client.publish(*last_command)
    
    client.publish("topic/speed", "Q")




if __name__ == "__main__":
    main()
    cv.waitKey(1000)
    cv.destroyAllWindows()