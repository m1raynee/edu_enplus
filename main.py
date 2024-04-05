import numpy as np
import cv2 as cv
import imutils as iu
from toolbox import ImageToolbox
import paho.mqtt.client as mqtt
from _ip import server_ip
import time


it = ImageToolbox()
it.load()

it.settings["H"] = 212
it.settings["h_r"] = 16
it.settings["h_c"] = 14

vid = cv.VideoCapture(0)  # подключение камеры


class video:
    def read(self):
        return True, cv.imread("saved.png")


# vid = video()
client = mqtt.Client(userdata="pc")
client.connect(server_ip, 1883)

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
### end of sadness

yg_tr = {"y": "yellow", "g": "green"}

robot = ("red", "purple")
cans = ("green", "yellow")
scan_colors = (*robot, "blue", *cans)
line_colors = robot
cans_colors = (*robot, *cans)
center_point = lambda im: np.array(im.shape[:2][::-1]) // 2

DIST_MULT = 1.2

last_angle = -1


def seek(goal, to_purple=False):
    dist = 100
    while dist > 18 and it.tick("z"):
        with it.entry_loop(vid, bin_kwargs={"colors": robot}) as l:
            if l.robot_vect is None:
                continue
            if to_purple:
                can_vect = goal - l.centers["purple"]
            else:
                can_vect = goal - l.centers["red"]
            dist = np.linalg.norm(can_vect)

            angle = it.signed_angle(l.robot_vect, can_vect) * 20

            align_angle = int(angle)
            if abs(align_angle) > 3:
                client.publish("topic/steer-n-speed", f"{align_angle} 0")
            else:
                client.publish("topic/steer-n-speed", f"{align_angle*10} 20")
    client.publish("topic/steer-n-speed", "0 0")

def release(back=True):
    client.publish("topic/steer-n-speed", "0 20")
    cv.waitKey(500)
    client.publish("topic/steer-n-speed", "0 0")
    client.publish("topic/grabber", "0")
    cv.waitKey(600)
    if back:
        client.publish("topic/steer-n-speed", "0 -20")
        cv.waitKey(850)
        client.publish("topic/steer-n-speed", "0 0")

def do_strategy(strategy, color_name):
    for can_index in strategy:
        # для каждого цилиндра пересчитываем центр 
        with it.entry_loop(vid, bin_kwargs={"colors": cans}, skip_centers=cans) as l:
            cnts, h = cv.findContours(
                l.bins[color_name], cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
            )
            dists = []
            centers = []
            for c in cnts:
                center = it.centers({color_name: c}, draw=False)[color_name]
                dists.append(np.linalg.norm(center - it.settings["cans"][can_index]))
                centers.append(center)
            
            print(dists)
            print(centers)

            goal = centers[dists.index(min(dists))]
            print(goal)

        # ищем и ловим цилиндр
        seek(goal, True)
        client.publish("topic/grabber", "catch")
        cv.waitKey(3000)

def main():
    # ожидание начала первоначального сканирования
    while it.tick("s"):
        with it.entry_loop(vid, bin_kwargs={"colors": scan_colors}):
            pass

    # определение цветов цилиндров и запись карты синего (линии)
    with it.entry_loop(vid, bin_kwargs={"colors": scan_colors}, skip_centers=True) as l:
        blue_map = l.bins["blue"]
        cans_types = []
        for i, can_center in enumerate(it.settings["cans"]):
            if cv.moments(it.square(l.bins["green"], can_center, 10))["m00"] != 0.0:
                cans_types.append("g")
            elif cv.moments(it.square(l.bins["yellow"], can_center, 10))["m00"] != 0.0:
                cans_types.append("y")
            else:
                raise Exception(f"Unable to find a can at {i} place")

    print(cans_types)

    while it.tick("x"):
        ...

    # определение зоны старта
    with it.entry_loop(vid, bin_kwargs={"colors": ("red",)}) as l:
        red = l.bins["red"]

        if (
            cv.moments(
                it.square(red, it.settings["left_start"], it.settings["r_start"])
            )["m00"]
            != 0.0
        ):
            start = "left_start"
            finish = "right_start"
        elif (
            cv.moments(
                it.square(red, it.settings["right_start"], it.settings["r_start"])
            )["m00"]
            != 0.0
        ):
            start = "right_start"
            finish = "left_start"
        else:
            raise Exception("Unable to calc starting zone")

    print(f"{start=}")

    # определение доминантных цилиндров и расчёт стратегии перемещения
    with it.entry_loop(vid, bin_kwargs={"colors": cans_colors}) as l:
        dom_factor = cans_types[1::2].count("y")
        dominant = "y" if dom_factor > 1 else "g"
        dom_name = yg_tr[dominant]
        rec_name = yg_tr["y" if dominant == "g" else "g"]

        if dom_factor == 3 or dom_factor == 0:
            strategy = [1, 3, 5]
        else:
            can0 = (n := cans_types[1::2]).index(dominant)
            can1 = n.index(dominant, can0 + 1) * 2 + 1
            can0 = can0 * 2 + 1
            outer_can = cans_types[::2].index(dominant) * 2
            if (dist0 := abs(can0 - outer_can)) == (dist1 := abs(can1 - outer_can)):
                # случай, когда цилиндры стоят подряд
                strategy = [can0, outer_can, can1]
            else:
                # определение крайнего внутреннего цилиндра
                first, middle = (can0, can1) if dist0 > dist1 else (can1, can0)
                strategy = [first, middle, outer_can]
        if strategy == [5, 3, 0]:
            strategy = [3, 5, 0]

    print(f"{strategy=}")

    # движение по линии, пока красный не будет рядом с финишем
    while (
        cv.moments(
            it.square(
                red,
                it.settings[finish],
                int(it.settings["r_start"] * 1.5),
            )
        )["m00"]
        == 0.0
    ) and it.tick(
        "l"
    ):
        # движение по линии
        with it.entry_loop(vid, bin_kwargs={"colors": line_colors}) as l:
            red = l.bins["red"]
            if l.robot_vect is None:
                client.publish("topic/steer-n-speed", "0 -10")

            angle = it.signed_angle(l.robot_vect, (0, -1))
            tr = iu.translate(
                blue_map,
                *it.as_int(center_point(blue_map) - l.centers["red"]),
            )
            rot = iu.rotate(tr, -angle * 180)

            r = int(np.linalg.norm(l.robot_vect * 4 / 3))

            area_center = center_point(rot) - [0, int(r * DIST_MULT)]
            b = 5
            a = r #int(r*1.2)
            zero_point = area_center - [a, b]
            one_point = area_center + [a, b]
            area = rot[
                zero_point[1] : one_point[1],
                zero_point[0] : one_point[0],
            ]
            M = cv.moments(area)
            rot = cv.rectangle(rot, zero_point, one_point, (255, 0, 0))
            if M["m00"] != 0.0:
                # линия зафиксирована, рисуем момент и отклонение
                line = it.M_point(M)
                actual_line = line + zero_point
                rot = cv.circle(rot, actual_line, 4, (255, 255, 0))
                diff = line[0] - a
                cv.putText(
                    rot, str(diff), actual_line, cv.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0)
                )
                angle = it.min_max(int(diff * 2), -100, 100)
                last_angle = np.sign(angle)
                print(angle)
                client.publish("topic/steer-n-speed", f"{angle} 20")
            else:
                # доворот в сторону, где была линия
                client.publish("topic/steer-n-speed", f"{10*last_angle} 0")

            cv.imshow("rot", rot)

    # небольшой проезд до финиша  
    client.publish("topic/steer-n-speed", "0 20")
    cv.waitKey(1000)
    client.publish("topic/steer-n-speed", "0 0")

    seek(it.settings["align_center"])
    do_strategy(strategy, dom_name)
    seek(it.settings["align_center"])

    # отвоз цилиндров в зону
    seek(it.settings[start if dominant == "g" else finish], True)
    release()

    # перерасчёт стратегии, сбор цилиндров в сторону нужной зоны
    strategy = sorted(list(set(range(0, 6)) - set(strategy)))
    if (start == "right_start" or dominant == "y") or (start == "left_start" and dominant == "g"):
        strategy = strategy[::-1]

    do_strategy(strategy, rec_name)
    
    seek(it.settings[finish if dominant == "g" else start], True)
    release(dominant == "y")

    if dominant == "y":
        seek(it.settings[finish], True)
        cv.waitKey(100)

class Init:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        client.publish("topic/steer-n-speed", "0 0")

if __name__ == "__main__":
    with Init() as init:
        it.load()
        main()
        it.dump()
    # init_
    # maid = init_robot_mind()
    # main
    # destroy
    # destroy(maid)


# init


# destroy
