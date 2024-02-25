import cv2 as cv
import numpy as np
from functools import partial
import paho.mqtt.client as mqtt

from toolbox import ImageToolbox, Mat

vid = cv.VideoCapture(1)

# This is the Publisher

server_ip = "192.168.1.38"

client = mqtt.Client(userdata="pc")
# client.connect(server_ip, 1883)


class client_faker:
    def publish(*_, **__):
        pass


client = client_faker()


class video_faker:
    def read(self):
        return True, cv.imread("./saved.png")
        # return True, cv.imread("./angle_test.png")


cv.namedWindow("settings")
cv.namedWindow("image")
cv.namedWindow("transformed")

it = ImageToolbox()
it.load()

settings_bars = {
    "x1": (0, 640),
    "y1": (0, 480),
    "x2": (0, 640),
    "y2": (0, 480),
    "xc": (0, 640),
    "yc": (0, 480),
    "angle": (0, 360),
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


def detect_cans():
    ret, img = vid.read()

    defaulted = default_chain.call(img)
    bins = it.bins(defaulted, ("green", "yellow"))
    area_center = it.settings["ctr"]

    for col in ("green", "yellow"):
        area = it.square(bins[col], area_center, 5)
        M = cv.moments(area)
        if M["m00"] != 0.0:
            it.can_type = col

    cans_types = []
    for can_center in it.settings["cans"]:
        area = it.square(bins[it.can_type], can_center, 10)
        if cv.moments(area)["m00"] != 0.0:
            cans_types.append(1)
        else:
            cans_types.append(0)
    return cans_types


def mouse_callback(event, x, y, *args):
    if event != 7:
        return
    ret, img = vid.read()
    if not ret:
        return
    img = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    command = input(f"command ({img[y][x]}): ")
    match command.split():
        case ["cp"]:
            it.settings["cp"] = np.asarray((y, x))
            return
        case ["c"]:
            it.settings["yc"], it.settings["xc"] = y, x
            it.compute_circles()
            return
        case ["r"]:
            it.settings["r"] = it.settings["yc"] - y
            it.compute_circles()
            return
        case ["ctr"]:
            it.settings["ctr"] = y, x
            return
        case ["col", name]:
            it.set_hsv(img[y][x], name, 10, 40, 40)
            return
        case ["load"]:
            it.load()
            return
        case ["dump"]:
            it.dump()
            return
        case ["calc"]:
            print(detect_cans())
            return
        case _:
            print("unknown command")


cv.namedWindow("transformed")
cv.setMouseCallback("image", mouse_callback)
cv.setMouseCallback("transformed", mouse_callback)

default_chain = (
    it.chain.add(it.resize)
    .add(it.rotate)
    .add(it.crop)
    .add(partial(cv.cvtColor, code=cv.COLOR_BGR2HSV))
)

while (key := cv.waitKey(10) & 0xFF) != ord("q"):
    if key == ord("r"):
        cv.setTrackbarPos("angle", "settings", it.settings["angle"] + 1)

    ret, img = vid.read()
    transformed = default_chain.call(img)

    ### REFACTORED
    bins = it.bins(transformed, ("red", "purple", "green", "yellow"))
    centers = it.centers(bins)
    ### REFACTORED

    post_img = it.rotate(img)
    transformed = it.draw_bounds(transformed)

    cv.imshow("image", post_img)
    cv.imshow("transformed", transformed)


grabbed = 0

def can(can_i):
    if grabbed > 1:
        raise NotImplementedError
    
    can_center = it.settings["cans"][can_i]

    catched = False
    while not catched:  # ~30 between red center and can center
        ret, img = vid.read()

        defaulted = default_chain.call(img)
        centers = it.centers(it.bins(defaulted))

        if centers["red"] == (0,0) or centers["purple"] == (0,0):
            print("can: unable to calc robot vect")
            continue

        r_vect = centers["purple"] - centers["red"]
        can_vect = can_center - centers["red"]

        dist = np.linalg.norm(can_vect)
        print(dist)
        angle = it.signed_angle(r_vect, can_vect) * 100
        if dist > 32:
            if not -5 <= angle <= 5:
                client.publish("topic/steer-n-speed", f"{int(angle)} 0")
            else:
                client.publish("topic/steer-n-speed", f"{int(angle)} {int(dist-35)}")
        else:
            client.publish("topic/steer-n-speed", "0 0")
            client.publish("topic/grabber", "catch")
            catched = True
            grabbed += 1
            





            


it.dump()
client.publish("topic/steer-n-speed", "0 0")
client.publish("topic/grabber", "0")
# client.disconnect()
