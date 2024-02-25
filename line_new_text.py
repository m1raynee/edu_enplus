import cv2 as cv
import numpy as np
import time
import paho.mqtt.client as mqtt
import imutils as iu

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
        case ["exit"]:
            it.settings["exit"] = np.asarray((y, x))
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

center_point = lambda im: np.array(im.shape[:2][::-1]) // 2
# 9 cm - 23 cm
print("here")
second_can = 5
cv.waitKey(1000)
client.publish("topic/grabber", "0")
cv.waitKey(1000)
client.publish("topic/steer-n-speed", "0 -10")
cv.waitKey(2500)
last_angle = -1 if second_can in [3, 4, 5, 6] else 1
client.publish("topic/steer-n-speed", f"{10*last_angle} 0")
cv.waitKey(1500)

first_moment = None
first_lap = True

while it.tick("a"):
    with it.entry_loop(vid) as l:
        if l.robot_vect is not None:
            if first_lap:
                if first_moment is not None and time.time() - timer > 5:
                    area = it.square(l.bins["red"], first_moment, 13)
                    l.defaulted = cv.rectangle(
                        l.defaulted,
                        first_moment - [10, 10],
                        first_moment + [10, 10],
                        (0, 255, 0),
                    )

                    if cv.moments(area)["m00"] != 0.0:
                        first_lap = False
            else:
                area = it.square(l.bins["red"], it.settings["exit"], 2)
                if cv.moments(area)["m00"] != 0.0:
                    client.publish("topic/steer-n-speed", "0 10")
                    cv.waitKey(1500)
                    client.publish("topic/steer-n-speed", "0 0")
                    break

            angle = it.signed_angle(l.robot_vect, (0, -1))
            tr = iu.translate(
                l.defaulted,
                *[int(i) for i in (center_point(l.defaulted) - l.centers["red"])],
            )
            rot = iu.rotate(tr, -angle * 180)
            blue = it.to_binary(rot, "blue")

            r = int(np.linalg.norm(l.robot_vect * 4 / 3))

            area_center = center_point(rot) - [0, int(r * 1.3)]
            b = 5
            a = r
            zero_point = area_center - [a, b]
            one_point = area_center + [a, b]
            area = blue[
                zero_point[1] : one_point[1],
                zero_point[0] : one_point[0],
            ]
            rot = cv.rectangle(rot, zero_point, one_point, (255, 0, 0))
            M = cv.moments(area)
            if M["m00"] != 0.0:
                if first_moment is None:
                    first_moment = l.centers["red"]
                    print(f"{first_moment = }")
                    timer = time.time()
                line = it.M_point(M)
                actual_line = line + zero_point
                rot = cv.circle(rot, actual_line, 4, (255, 255, 0))
                diff = line[0] - a
                cv.putText(
                    rot, str(diff), actual_line, cv.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255)
                )
                angle = it.min_max(int(diff * 2), -100, 100)
                last_angle = np.sign(angle)
                client.publish("topic/steer-n-speed", f"{angle} 10")
            else:
                if last_angle != 0:
                    client.publish("topic/steer-n-speed", f"{5*last_angle} 0")
                else:
                    client.publish("topic/steer-n-speed", f"{0} 10")

            cv.imshow("rot", rot)
        else:
            client.publish("topic/steer-n-speed", "0 0")


caught = False
while not caught and it.tick("a"):
    with it.entry_loop(vid) as l:
        dest = it.settings["cans"][6]
        can_vect = dest - l.centers["red"]
        dist = np.linalg.norm(dest - l.centers["purple"])
        if l.robot_vect is None:
            continue
        angle = it.signed_angle(l.robot_vect, can_vect) * 100
        if dist > 10 or dist < 4:
            align_angle = it.min_max(int(angle), -30, 30)
            # align_angle = it.min_max(int(angle), -MAX_STEER, MAX_STEER)
            if abs(align_angle) > 3:
                client.publish("topic/steer-n-speed", f"{align_angle} 0")
            else:
                speed = it.min_max(int((dist - 6) // 2), -20, 20)
                client.publish("topic/steer-n-speed", f"{align_angle} {speed}")
        else:
            client.publish("topic/steer-n-speed", "0 0")
            cv.waitKey(500)
            caught = True

caught = False
while not caught and it.tick("a"):
    with it.entry_loop(vid) as l:
        dest = it.settings["cp"]
        can_vect = dest - l.centers["red"]
        dist = np.linalg.norm(dest - l.centers["purple"])
        if l.robot_vect is None:
            continue
        angle = it.signed_angle(l.robot_vect, can_vect) * 100
        if dist > 10 or dist < 4:
            align_angle = it.min_max(int(angle), -30, 30)
            # align_angle = it.min_max(int(angle), -MAX_STEER, MAX_STEER)
            if abs(align_angle) > 3:
                client.publish("topic/steer-n-speed", f"{align_angle} 0")
            else:
                speed = it.min_max(int((dist - 6) // 2), -20, 20)
                client.publish("topic/steer-n-speed", f"{align_angle} {speed}")
        else:
            client.publish("topic/steer-n-speed", "0 0")
            cv.waitKey(500)
            caught = True

client.publish("topic/steer-n-speed", "0 0")
client.publish("topic/grabber", "0")
it.dump()
cv.waitKey(100)
# client.disconnect()
