from cv2 import VideoCapture, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT

__all__ = ("r_cap", "rich_capture")

rich_capture = VideoCapture(2)  # подключение камеры
rich_capture.set(CAP_PROP_FRAME_WIDTH, 1920)
rich_capture.set(CAP_PROP_FRAME_HEIGHT, 1080)

r_cap = rich_capture

capture = VideoCapture(1)  # подключение камеры
