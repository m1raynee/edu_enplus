import cv2 as cv
import numpy as np
import imutils as iu

transitions = {"angle": 0, "p1": None, "p2": None}


def crop_im(i: np.matrix, p1=None, p2=None):
    p1 = p1 or transitions["p1"]
    p2 = p2 or transitions["p2"]
    return i[p1[1] : p2[1] + 1, p1[0] : p2[0] + 1]


def resize_im(i: np.matrix, d: int = 2):
    return cv.resize(i, (i.shape[1] // d, i.shape[0] // d))


def rotate_im(i: np.matrix, angle=None):
    return iu.rotate(i, angle or transitions["angle"])


video = cv.VideoCapture(1)


class video_faker:
    def read(self):
        # return True, cv.imread("./saved.png")
        return True, cv.imread("./angle_test.png")


# video = video_faker()

while not video.read()[0]:
    cv.waitKey(10)

# cv.namedWindow("rotate image")
# cv.namedWindow("rotation")


# def rotate_callback(angle):
#     transitions["angle"] = angle
    


# cv.createTrackbar("angle/10", "rotation", 0, 360, rotate_callback)
# rotate_callback(0)

# while True:
#     key = cv.waitKey(10) & 0xFF
#     if key == ord("r"):
#         break
#     elif key == ord("p"):
#         transitions["angle"] += 1
#         cv.setTrackbarPos("angle/10", "rotation", transitions["angle"])

#     ret, img = video.read()
#     if not ret: continue
#     rotated = iu.rotate(img, transitions["angle"])
#     cv.imshow("rotate image", rotated)

# cv.destroyWindow("rotate image")
# cv.destroyWindow("rotation")


# cv.namedWindow("crop image")


# def crop_callback(event, x, y, *_):
#     if event != 7:
#         return

#     if transitions["p1"] is None:
#         transitions["p1"] = (x, y)
#         print(f"setted {transitions['p1']=}")
#     else:
#         transitions["p2"] = (x, y)
#         print(f"setted {transitions['p2']=}")


# cv.setMouseCallback("crop image", crop_callback)

# while True:
#     if cv.waitKey(10) & 0xFF == ord("q"):
#         break

#     ret, img = video.read()
#     img = rotate_im(img)
#     cv.imshow("crop image", img)

# cv.destroyWindow("crop image")

# if transitions["p1"] is None or transitions["p2"] is None:
#     raise TypeError("Boundaries weren't provided")


def mask_im(i):
    h_min = np.array((hsv_values["h1"], hsv_values["s1"], hsv_values["v1"]), np.uint8)
    h_max = np.array((hsv_values["h2"], hsv_values["s2"], hsv_values["v2"]), np.uint8)
    mask = cv.inRange(i, h_min, h_max)
    return mask


windows = [
    "hsv params",
    "cropped",
    "resized",
    "hsv",
    "binary",
    "eroded",
]

for wind in windows:
    cv.namedWindow(wind)


hsv_values = {
    "h1": 0,
    "s1": 0,
    "v1": 0,
    "h2": 180,
    "s2": 255,
    "v2": 255,
}


def trackbar_cb(key):
    def callback(value):
        hsv_values[key] = value

    return callback


for k, v in hsv_values.items():
    cv.createTrackbar(
        k,
        "hsv params",
        v,
        180 if k[0] == "h" else 255,
        trackbar_cb(k),
    )

while cv.waitKey(10) & 0xFF != ord("w"):
    ret, img = video.read()
    rotated = rotate_im(img)
    # cropped = crop_im(rotated)
    cropped = img
    resized = resize_im(cropped)
    hsv = cv.cvtColor(resized, cv.COLOR_BGR2HSV)
    ranged = mask_im(hsv)
    eroded = cv.erode(ranged, cv.getStructuringElement(cv.MORPH_RECT, (3, 3)))

    moments = cv.moments(ranged)
    if moments["m00"] != 0.0:
        cnt_x = int(moments["m10"] / moments["m00"])
        cnt_y = int(moments["m01"] / moments["m00"])
        moment = cv.circle(
            cv.cvtColor(ranged.copy(), cv.COLOR_GRAY2BGR),
            (cnt_x, cnt_y),
            10,
            (0, 255, 0),
            1,
        )
        cv.imshow("moments", moment)

    cv.imshow("cropped", cropped)
    cv.imshow("resized", resized)
    cv.imshow("hsv", hsv)
    cv.imshow("binary", ranged)
    cv.imshow("eroded", eroded)

print(repr(hsv_values))