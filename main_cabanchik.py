import cv2
import numpy as np
import time
import os

#  Импорт библиотеки нужной для того, чтобы подавать напряжение на пины платы и тем самым контролировать всего кабанчика
import wiringpi # type: ignore

# обозначение левого мотора, как выход
wiringpi.pinMode(9, 1)

# Обозначение правого мотора, как выход
wiringpi.pinMode(10, 1)

# Обозначение динамика, как выход
wiringpi.pinMode(13, 1)

# Создать объект VideoCapture для считывания кадров с камеры
cap = cv2.VideoCapture(1)

# Установить разрешение камеры
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    # Считать кадр с камеры
    ret, frame = cap.read()

    # Если кадр успешно считан
    if ret:

        os.system("gpio write 9 1")
        os.system("gpio write 10 1")

        # Преобразовать кадр в формат HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Выделить область коричневого цвета в HSV
        mask = cv2.inRange(hsv, (20, 100, 100), (30, 255, 255))

        # Подсчитать количество пикселей коричневого цвета
        brown_pixels = np.count_nonzero(mask)

        # Вывести количество пикселей коричневого цвета
        print(f"Количество пикселей коричневого цвета: {brown_pixels}")

        # Отобразить маску в отдельном окне
        cv2.imshow("Маска", mask)

        # Отобразить исходную картинку
        cv2.imshow("Исходное изображение", frame)

        # Ожидать нажатия клавиши
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if brown_pixels > 30000:
            wiringpi.digitalWrite(9, 0)
            wiringpi.digitalWrite(10, 0)
            wiringpi.digitalWrite(13, 1)
            time.sleep(4000)
            wiringpi.digitalWrite(13, 0)
            wiringpi.digitalWrite(9, 1)
            wiringpi.digitalWrite(10, 0)
            time.sleep(1000)
            wiringpi.digitalWrite(9, 1)
            wiringpi.digitalWrite(10, 1)
            time.sleep(2000)
            wiringpi.digitalWrite(9, 0)
            wiringpi.digitalWrite(10, 1)
            time.sleep(1000)
            wiringpi.digitalWrite(9, 1)
            wiringpi.digitalWrite(10, 1)
            time.sleep(2000)
            wiringpi.digitalWrite(9, 0)
            wiringpi.digitalWrite(10, 1)
            time.sleep(1000)
            wiringpi.digitalWrite(9, 1)
            wiringpi.digitalWrite(10, 1)
            time.sleep(2000)
            wiringpi.digitalWrite(9, 1)
            wiringpi.digitalWrite(10, 0)
            time.sleep(1000)

# Закрыть все окна и освободить ресурсы
cv2.destroyAllWindows()
cap.release()