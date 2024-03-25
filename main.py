import numpy as np
import cv2 as cv
import imutils as iu
from toolbox import ImageToolbox
import paho.mqtt.client as mqtt
from _ip import server_ip


it = ImageToolbox()
it.load()

it.settings["H"] = 212
it.settings["h_r"] = 16
it.settings["h_c"] = 13

vid = cv.VideoCapture(0)  # подключение камеры
client = mqtt.Client(userdata="pc")
client.connect(server_ip, 1883)

def detect_cans():
    colors = ("green",)
    with it.entry_loop(vid, bin_kwargs={"colors": colors}, skip_centers=True) as l:
        cans_types = []
        for can_center in it.settings["cans"]:
            area = it.square(l.bins[colors[0]], can_center, 10)
            if cv.moments(area)["m00"] != 0.0:
                cans_types.append(1)
            else:
                cans_types.append(0)
        return cans_types


### sadness
cv.namedWindow("settings")
cv.namedWindow("image")
cv.namedWindow("transformed")

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
        case ["c", i]:
            it.settings["cans"][int(i)] = x, y
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
        case ["set", key]:
            it.settings[key] = x, y
            return
        case _:
            print("unknown command")


cv.namedWindow("transformed")
cv.setMouseCallback("image", mouse_callback)
cv.setMouseCallback("transformed", mouse_callback)
### sadness end

colors = ("red", "purple", "green", "yellow", "blue")
center_point = lambda im: np.array(im.shape[:2][::-1]) // 2

DIST_MULT = 1.2

last_angle = -1


def main():
    while it.tick("q"):  # simple loop
        ret, img = vid.read()  # захват изображения из видеопотока
        if ret:
            cv.imshow("image", img)  # вывод цветного изображения
        else:
            continue

        with it.entry_loop(vid, bin_kwargs={"colors": colors}) as l:
            if l.robot_vect is None:
                continue
            angle = it.signed_angle(l.robot_vect, (0, -1))
            tr = iu.translate(
                l.defaulted,
                *it.as_int(center_point(l.defaulted) - l.centers["red"]),
            )
            rot = iu.rotate(tr, -angle * 180)
            blue = it.to_binary(rot, "blue")

            r = int(np.linalg.norm(l.robot_vect * 4 / 3))

            area_center = center_point(rot) - [0, int(r * DIST_MULT)]
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
                line = it.M_point(M)
                actual_line = line + zero_point
                rot = cv.circle(rot, actual_line, 4, (255, 255, 0))
                diff = line[0] - a
                cv.putText(
                    rot, str(diff), actual_line, cv.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0)
                )
                angle = it.min_max(int(diff * 2), -100, 100)
                last_angle = np.sign(angle)
                client.publish("topic/steer-n-speed", f"{angle} 10")
            else:
                client.publish("topic/steer-n-speed", f"{5*last_angle} 0")

            cv.imshow("rot", rot)

    cv.imwrite("saved.png", img)

    vid.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    it.load()
    main()
    it.dump()
