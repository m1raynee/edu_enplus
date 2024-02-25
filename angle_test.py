import cv2 as cv
import numpy as np
from config import red, violet

settings = {"rotation": 0}
trackbars = {"rotation": (0, 360)}

class video_faker:
    def __init__(self, im) -> None:
        self.im = im
    def read(self):
        return True, cv.imread(self.im)

# vid = video_faker("./angle_test.png")
vid = cv.VideoCapture(1)

cv.namedWindow("settings")
cv.namedWindow("image")

def create_cb(key):
    def callback(value):
        settings[key] = value
    return callback

def img_mask(im: np.matrix, mask: dict):
    h_min = np.array((mask["h1"], mask["s1"], mask["v1"]), np.uint8)
    h_max = np.array((mask["h2"], mask["s2"], mask["v2"]), np.uint8)
    mask = cv.inRange(im, h_min, h_max)
    return mask

for k, v in settings.items():
    cv.createTrackbar(
        k,
        "settings",
        *trackbars[k],
        create_cb(k),
    )

def m_normalize(moments):
    cnt_x = int(moments["m10"] / moments["m00"])
    cnt_y = int(moments["m01"] / moments["m00"])
    return (cnt_x, cnt_y)

while True:
    if cv.waitKey(10) & 0xFF == ord("q"): break

    ret, img = vid.read()
    binary_red = img_mask(img, red)
    binary_violet = img_mask(img, violet)
    M_red = cv.moments(binary_red)
    M_violet = cv.moments(binary_violet)

    if M_red["m00"] == 0.0 or M_violet["m00"] == 0.0:
        print("moments were not found")
        print(f"{M_red['m00'] =}")
        print(f"{M_violet['m00'] =}")
        break

    c_red = m_normalize(M_red)
    c_violet = m_normalize(M_violet)

    def f(x, pt1, pt2):
        x1, x2 = pt1[0], pt2[1]
        y1, y2 = pt1[1], pt2[1]
        return ((y1-y2)*x+(x1*y2-x2*y1))//(x2-x1)
    
    cv.circle(img, c_red, 7, (0, 0, 0))
    cv.circle(img, c_violet, 7, (0, 0, 0))

    for x in range(img.shape[1]):
        if 0 <= f(x, c_red, c_violet) < img.shape[0]:
            cv.circle(img, (x, f(x)), 3, (0, 0, 200))

    cv.imshow("image", img)


