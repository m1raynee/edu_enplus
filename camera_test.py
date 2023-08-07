import cv2

vid = cv2.VideoCapture(1)  # подключение камеры
ret, img = vid.read()  # захват изображения из видеопотока

cv2.imshow("Color picture 2", img)  # вывод цветного изображения

cv2.waitKey(0)  # ожидание нажатия на клавишу
cv2.destroyAllWindows()