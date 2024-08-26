from cv2 import VideoCapture, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT

__all__ = ("get_rcap", "get_rich_video_capture")

def get_rich_video_capture(index):
    rich_capture = VideoCapture(index)  # подключение камеры
    rich_capture.set(CAP_PROP_FRAME_WIDTH, 1920)
    rich_capture.set(CAP_PROP_FRAME_HEIGHT, 1080)
    return rich_capture

get_rcap = get_rich_video_capture
