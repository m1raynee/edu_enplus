import cv2
import numpy as np

# vid = cv2.VideoCapture(1)  # подключение камеры
# ret, img = vid.read()

ret, img = None, cv2.imread("./saved.png")
print(img.shape)
cv2.imshow("initial image", img)

pt1 = None
pt2 = None


def crop_mouse_callback(event, x, y, *args):
    global pt1, pt2
    if event == 7:
        if pt1 is None:
            pt1 = (x, y)
            print(f"setted {pt1=}")
        pt2 = (x, y)
        print(f"setted {pt2=}")


cv2.setMouseCallback("initial image", crop_mouse_callback)

while cv2.waitKey(10) & 0xFF != ord("q"):
    pass

if pt1 is None or pt2 is None:
    raise TypeError("Boundaries weren't provided")
img = img[pt1[1] : pt2[1], pt1[0] + 1 : pt2[0] + 1]
cv2.imshow("initial image", img)

img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
cv2.imshow("resized + hsv (in bgr spectrum)", hsv)
# print(img.shape)

# cv2.putText(
#     img,
#     str(img.shape),
#     (0, img.shape[0]),
#     cv2.FONT_HERSHEY_PLAIN,
#     1,
#     (0, 255, 255),
# )


def mouse_callback(event, x, y, *args):
    if event == 7:
        print(hsv[y][x])


cv2.namedWindow("hsv boundaries")
cv2.namedWindow("mask")

cv2.setMouseCallback("resized + hsv (in bgr spectrum)", mouse_callback)
cv2.setMouseCallback("mask", mouse_callback)

# cv2.imshow("resized", img)

values = {
    "h1": 0,
    "s1": 0,
    "v1": 0,
    "h2": 180,
    "s2": 255,
    "v2": 255,
}


def img_mask(hsv):
    h_min = np.array((values["h1"], values["s1"], values["v1"]), np.uint8)
    h_max = np.array((values["h2"], values["s2"], values["v2"]), np.uint8)
    mask = cv2.inRange(hsv, h_min, h_max)
    return mask


def cb(key, hsv):
    def callback(value):
        values[key] = value
        cv2.imshow("mask", img_mask(hsv))

    return callback


cb("h1", hsv)(0)

for k, v in values.items():
    cv2.createTrackbar(
        k,
        "hsv boundaries",
        v,
        180 if k[0] == "h" else 255,
        cb(k, hsv),
    )


while cv2.waitKey(10) & 0xFF != ord("q"):
    mask = img_mask(hsv)
    moments = cv2.moments(mask)

    if moments["m00"] != 0.0:
        cnt_x = int(moments["m10"] / moments["m00"])
        cnt_y = int(moments["m01"] / moments["m00"])
        moment = cv2.circle(img.copy(), (cnt_x, cnt_y), 10, (0, 255, 0), 1)
        cv2.imshow("moments", moment)


cv2.destroyAllWindows()
