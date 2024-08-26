import time

import cv2 as cv
import paho.mqtt.client as mqtt
from _ip import server_ip

from video_source import r_cap
from toolbox import ImageToolbox

it = ImageToolbox()
it.load()
# it.default_chain = it.chain.add(partial(it.resize, factor = 4))

client = mqtt.Client(userdata="pc")
client.connect(server_ip, 1883)

### sadness
cv.namedWindow("settings")
cv.namedWindow("image")
cv.namedWindow("transformed")

settings_bars = {
}


def create_callback(key):
    def callback(value):
        it.settings[key] = value

    return callback


for key, borders in settings_bars.items():
    cv.createTrackbar(
        key,
        "settings",
        *borders,
        create_callback(key),
    )
    cv.setTrackbarPos(key, "settings", it.settings[key])


def mouse_callback(event, x, y, *args):
    if event != 7:
        return
    ret, img = r_cap.read()
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


cv.namedWindow("transformed")
cv.setMouseCallback("image", mouse_callback)
cv.setMouseCallback("transformed", mouse_callback)
### end of sadness
last_command = ("", "")
kick_timer = 0
def main():
    while it.tick("q"):
        global last_command, kick_timer
        with it.entry_loop(r_cap) as img:
            if list(img.centers["red"]) == [0, 0]:
                command = ("topic/speed", 0)
            else:
                d_x = img.centers["yellow"][0] - img.centers["red"][0]
                k = 2.5
                diff = it.min_max(d_x*k, -100, 100)

                d_y = img.centers["yellow"][1] - img.centers["red"][1]
                if d_y < 50 and time.time() - kick_timer > 1:
                    client.publish("topic/movements", 90)
                    kick_timer = time.time()


                command = ("topic/speed", str(int(diff)))

            if command != last_command:
                    last_command = command
                    client.publish(*last_command)




if __name__ == "__main__":
    main()
    client.publish("topic/speed", "Q")
    cv.waitKey(1000)