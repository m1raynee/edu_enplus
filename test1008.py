# import socket
import numpy as np

# import csv
import time
import cv2

camera = cv2.VideoCapture(1)
time.sleep(3)

import socket


mac = "17:B9:01:05:61:E4"
ret, img = camera.read()
print("программа запустилась")

xr = 0
yr = 0
while True:
    if cv2.waitKey(10) == 27:
        break
    ret, img = camera.read()
    hsvg_min = np.array((151, 97, 175), np.uint8)  # HSV фильтр для желтых объектов min
    hsvg_max = np.array((255, 196, 255), np.uint8)  # HSV фильтр для желтых объектов max
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    thresh = cv2.inRange(
        hsv, hsvg_min, hsvg_max
    )  # применяем фильтр для желтых объектов
    # нахождение самого большого пятна желтого цвета на поле
    moments = cv2.moments(thresh, 1)
    dM01 = moments["m01"]
    dM10 = moments["m10"]
    dArea = moments["m00"]
    # будем реагировать только на те моменты,
    # которые содержать больше 300 пикселей

    if dArea > 200:
        # print ('dArea')
        xr = int(dM10 / dArea)
        yr = int(dM01 / dArea)
        # xr = xr + 40
        cv2.circle(img, (xr, yr), 10, (0, 255, 255), -1)
    cv2.imshow("камера (imgh)", img)  # вывод цветного изображения на экран
# остановка программы и выход из всех циклов
camera.release()
cv2.destroyAllWindows()
