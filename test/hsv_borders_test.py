import cv2
from ..toolbox import ImageToolbox

it = ImageToolbox()

vid = cv2.VideoCapture(1)  # подключение камеры

def main():
    while cv2.waitKey(10) != 27:  # simple loop
        ret, img = vid.read()  # захват изображения из видеопотока
        if ret: cv2.imshow("Color picture 2", img)  # вывод цветного изображения
        else: continue

    cv2.imwrite("saved.png", img)

    vid.release()
    cv2.destroyAllWindows()