import cv2

vid = cv2.VideoCapture(2)  # подключение камеры

while True:  # simple loop
    if cv2.waitKey(10) == 27:
        break  # ожидание нажатия на клавишу

    ret, img = vid.read()  # захват изображения из видеопотока
    if ret: cv2.imshow("Color picture 2", img)  # вывод цветного изображения

cv2.imwrite("saved.png", img)

vid.release()
cv2.destroyAllWindows()
