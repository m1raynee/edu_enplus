import cv2
import serial
import time
from random import randint


le = 50
wide = 30

yr = 0
xr = 0
last = 0
e = ""

arduino = serial.Serial("COM6", 9600)
time.sleep(2)
print("connected")

cap = cv2.VideoCapture(2)  # подключение камеры
print("camera open")

for i in range(4):
    task = randint(1, 3)

    print("Вывод случайного целого числа ", task)
    # time.sleep(5)
    game = 0

    e = str(task)

    i = e.encode()
    arduino.write(i)
    time.sleep(20)

    while game != 1:
        if cv2.waitKey(10) == 27:  # ESC
            break

        # захват изображения из видеопотока ret - Данные об ошибке
        ret, img = cap.read()

        v = int(img.shape[0] * 0.5)  # y лучше умножать
        d = int(img.shape[1] * 0.5)  # x
        img = cv2.resize(img, (d, v))  # изменение размера
        # time.sleep(1)

        y = (115 * 2 + le) // 2

        # вывод значения rgb для одного конкретного пиктеля
        b3, g3, r3 = img[y][(75 * 2 + wide) // 2]
        cv2.circle(img, ((75 * 2 + wide) // 2, y), 3, (0, 255, 255), -1)
        print(r3, g3, b3)

        # вывод значения rgb для одного конкретного пиктеля
        b2, g2, r2 = img[y][(135 * 2 + wide) // 2]
        cv2.circle(img, ((135 * 2 + wide) // 2, y), 3, (0, 255, 255), -1)
        print(r2, g2, b2)

        # вывод значения rgb для одного конкретного пиктеля
        b1, g1, r1 = img[y][(200 * 2 + wide) // 2]
        cv2.circle(img, ((200 * 2 + wide) // 2, y), 3, (0, 255, 255), -1)
        print(r1, g1, b1)

        cv2.rectangle(img, (75, 115), (75 + wide, 115 + le), (0, 255, 255), 2)
        cv2.rectangle(img, (135, 115), (135 + wide, 115 + le), (0, 255, 255), 2)
        cv2.rectangle(img, (200, 115), (200 + wide, 115 + le), (0, 255, 255), 2)

        # вывод цветного изображения на экран
        cv2.imshow("Color picture 2", img)

        # определение выигрышной ситуации
        e = "f"
        if task == 1:
            if (
                (g1 > 150 and r1 > 150)
                and (b2 < 20 and g2 > 50 and g2 < 150 and r2 > 200)
                and (b3 > 150 and g3 > 50 and r3 < 20)
            ):
                e = "w"
        elif task == 2:
            if (
                (b1 < 20 and g1 > 50 and g1 < 150 and r1 > 200)
                and (b2 > 150 and g2 > 50 and r2 < 20)
                and (g3 > 150 and r3 > 150)
            ):
                e = "w"
        elif task == 3:
            if (
                (b1 > 150 and g1 > 50 and r1 < 20)
                and (g2 > 150 and r2 > 150)
                and (b3 < 20 and g3 > 50 and g3 < 150 and r3 > 200)
            ):
                e = "w"
        elif task == 4:
            if (
                (b1 > 150 and g1 > 50 and r1 < 20)
                and (b2 < 20 and g2 > 50 and g2 < 150 and r2 > 200)
                and (g3 > 150 and r3 > 150)
            ):
                e = "w"
        print(e)
        i = e.encode()
        arduino.write(i)

        # задержки для синхронизации
        time.sleep(2)
        if e == "f":
            time.sleep(5)

        game = 1

# cv2.waitKey(0) #ожидание нажатия на клавишу
cv2.destroyAllWindows()
print("close")
