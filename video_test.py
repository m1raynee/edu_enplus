import cv2

vid = cv2.VideoCapture(1)

while True:
    if cv2.waitKey(10) == 27:
        break
    
    ret, img = vid.read()  # захват изображения из видеопотока
    cv2.imshow("Color picture 2", img)  # вывод цветного изображения

cv2.destroyAllWindows()