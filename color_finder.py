import cv2
import serial
import time

serial_port = serial.Serial("COM6", 9600)
time.sleep(2)

vid = cv2.VideoCapture(1)

while True:
    if cv2.waitKey(10) == 27:
        break

    ret, img = vid.read()  # захват изображения из видеопотока

    v, d, _ = map(lambda z: int(z * 0.5), img.shape)

    img = cv2.resize(img, (d, v))
    center = tuple(map(lambda z: int(z * 0.5), (v, d)))

    count = [0, 0, 0]
    for x in range(center[0] - 20, center[0] + 20):
        for y in range(center[1] - 20, center[1] + 20):
            b, g, r = img[y][x]

            if 150 < b:
                count[2] += 1
            if 150 < g:
                count[1] += 1
            if 150 < r:
                count[0] += 1

    out_sum = sum(count) / 3
    count = list(map(lambda d: int(d > out_sum), count))
    to_write = str(count[0] + count[1] * 2 + count[2] * 4)

    cv2.rectangle(
        img,
        (center[0] - 20, center[1] - 20),
        (center[0] + 20, center[1] + 20),
        (255, 255, 255),
        1,
    )
    serial_port.write(to_write.encode())
    cv2.putText(
        img,
        str(count) + str(to_write),
        (0, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (50, 200, 0),
        3,
    )

    cv2.imshow("Color picture 2", img)  # вывод цветного изображения

cv2.destroyAllWindows()
