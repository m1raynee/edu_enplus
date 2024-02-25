import cv2

# import serial
import time
# from random import randint


le = 50
wide = 30

yr = 0
xr = 0
last = 0
e = ""

cap = cv2.VideoCapture(2)  # подключение камеры

while True:
    ret, img = cap.read()  # захват изображения из видеопотока ret - Данные об ошибке

    v = int(img.shape[0] * 0.5)  # y лучше умножать
    d = int(img.shape[1] * 0.5)  # x
    img = cv2.resize(img, (d, v))  # изменение размера
    # time.sleep(1)

    y = (115 * 2 + le) // 2

    b3, g3, r3 = img[y][
        (75 * 2 + wide) // 2
    ]  # вывод значения rgb для одного конкретного пиктеля
    cv2.circle(img, ((75 * 2 + wide) // 2, y), 3, (0, 255, 255), -1)
    print(r3, g3, b3)

    b2, g2, r2 = img[y][
        (135 * 2 + wide) // 2
    ]  # вывод значения rgb для одного конкретного пиктеля
    cv2.circle(img, ((135 * 2 + wide) // 2, y), 3, (0, 255, 255), -1)
    print(r2, g2, b2)

    b1, g1, r1 = img[y][
        (200 * 2 + wide) // 2
    ]  # вывод значения rgb для одного конкретного пиктеля
    cv2.circle(img, ((200 * 2 + wide) // 2, y), 3, (0, 255, 255), -1)
    print(r1, g1, b1)

    cv2.rectangle(img, (75, 115), (75 + wide, 115 + le), (0, 255, 255), 2)
    cv2.rectangle(img, (135, 115), (135 + wide, 115 + le), (0, 255, 255), 2)
    cv2.rectangle(img, (200, 115), (200 + wide, 115 + le), (0, 255, 255), 2)

    cv2.imshow("Color picture 2", img)
    print()
    time.sleep(2)
