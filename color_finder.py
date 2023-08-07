import cv2

vid = cv2.VideoCapture(1)

while True:
    if cv2.waitKey(10) == 27:
        break
    
    ret, img = vid.read()  # захват изображения из видеопотока

    v, d, _ = map(lambda z: int(z * 0.5), img.shape)

    img = cv2.resize(img, (d, v))
    center = tuple(map(lambda z: int(z * 0.5), (v,d)))

    count = 0
    for x in range(center[0]-20, center[0]+20):
        for y in range(center[1]-20, center[1]+20):
            b,g,r = img[y][x]

            if b > 70 and g > 70 and r < 50:
                img[y, x] = (255, 0, 255)
                count += 1
    if count > 500:
        color = (0,0,255)
    else:
        color = (255, 0, 0)
    cv2.rectangle(
        img, 
        (center[0]-20, center[1]-20), 
        (center[0]+20, center[1]+20), 
        color, 
        1
    )
    cv2.putText(img, str(count), (182,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 200, 0), 3)

    cv2.imshow("Color picture 2", img)  # вывод цветного изображения

cv2.destroyAllWindows()