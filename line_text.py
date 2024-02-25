import cv2 as cv
import numpy as np
import time
import paho.mqtt.client as mqtt

from toolbox import ImageToolbox
from _ip import server_ip

MAX_STEER = 30
MAX_SPEED = 30


class client_faker:
    def publish(*_, **__):
        pass

    def connect(*_, **__):
        pass

    def disconnect(*_, **__):
        pass


class video_faker:
    def read(self):
        return True, cv.imread("./saved.png")
        # return True, cv.imread("./angle_test.png")


vid = cv.VideoCapture(1)

# This is the Publisher

# client = client_faker()
client = mqtt.Client(userdata="pc")
client.connect(server_ip, 1883)

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
    colors = ("green", "yellow")
    with it.entry_loop(vid, bin_kwargs={"colors": colors}, skip_centers=True) as l:
        area_center = it.settings["ctr"]

        for col in colors:
            area = it.square(l.bins[col], area_center, 5)
            M = cv.moments(area)
            if M["m00"] != 0.0:
                it.can_type = col

        cans_types = []
        for can_center in it.settings["cans"]:
            area = it.square(l.bins[it.can_type], can_center, 10)
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


while (key := cv.waitKey(10) & 0xFF) != ord("q"):
    if key == ord("r"):
        cv.setTrackbarPos("angle", "settings", it.settings["angle"] + 1)

    with it.entry_loop(vid, bin_kwargs={"colors": it.settings["hsv"].keys()}) as l:
        pass

# 9 cm - 23 cm
print("here")
colors = ("red", "purple", "blue")



while it.tick("a"):
    with it.entry_loop(vid, bin_kwargs={"colors": colors}, skip_centers=("blue",)) as l:
        if l.robot_vect is None:
            continue
        r = l.robot_vect * 4 / 3
        area_center = l.centers["red"] + 1.35 * r
        area_center = [int(i) for i in area_center]
        d = int(np.linalg.norm(r * 0.35))

        pt1 = np.array((area_center[0] - d, area_center[1] - d))
        pt2 = np.array((area_center[0] + d, area_center[1] + d))
        zero_point = np.asarray(
            (
                it.min_max(pt1[0], 0, 640),
                it.min_max(pt1[1], 0, 480),
            )
        )
        one_point = np.asarray(
            (
                it.min_max(pt2[0], 0, 640),
                it.min_max(pt2[1], 0, 480),
            )
        )

        area = l.bins["blue"][
            zero_point[1] : one_point[1], zero_point[0] : one_point[0]
        ]

        M = cv.moments(area)
        if M["m00"] != 0.0:
            point = it.M_point(cv.moments(area))
            point += zero_point

            if l.robot_vect is not None:
                dest = point - l.centers["red"]
                angle = it.signed_angle(l.robot_vect, dest) * 100 * 0.3
                speed = np.linalg.norm(dest) * 0 + 10
                client.publish(
                    "topic/steer-n-speed",
                    f"{0} {int(speed)}",  # int(it.min_max(angle, -100, 100))
                )

            l.defaulted = cv.circle(l.defaulted, point, 5, (255, 255, 0))
        else:
            try:
                angle
            except Exception:
                pass
            finally:
                if angle > 0:
                    angle = 10
                else:
                    angle = -10
                client.publish("topic/steer-n-speed", f"{int(angle)} 0")

        l.defaulted = cv.rectangle(l.defaulted, zero_point, one_point, (0, 255, 255))

client.publish("topic/steer-n-speed", "0 0")
client.publish("topic/grabber", "0")
it.dump()
cv.waitKey(100)
# client.disconnect()
