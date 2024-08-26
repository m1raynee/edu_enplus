from __future__ import annotations
from collections.abc import Callable
import json
import typing as t
import cv2 as cv
import numpy as np
from functools import cached_property, partial
import imutils as imu


Chainable = t.Callable[[np.matrix], np.matrix]
Mat = np.ndarray


class NumpyEncoder(json.JSONEncoder):
    """Special json encoder for numpy types."""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class NumpyDecoder(json.JSONDecoder):
    """Special json decoder for lists to be represented as Numpy arrays."""

    def default(self, obj):
        obj = json.JSONEncoder.default(self, obj)
        if isinstance(obj, list):
            obj = np.asarray(obj)
        return obj


class ChainException(Exception):
    """Base exception class for exceptions occurring
    during image processing using function chains."""

    def __init__(self, base_exception: Exception, n: int, func: Callable) -> None:
        self.base_exception = base_exception
        self.n = n
        self.func = func
        message = f"Caught {base_exception.__class__} during image processing in chain link No.{n} ({func.__repr__()})"
        super().__init__(message)


class Chain:
    def __init__(self, im_class: ImageToolbox) -> None:
        self._im_class = im_class
        self._chain: list[Chainable] = []

    def add(self, func: Chainable) -> t.Self:
        """Adds `func` to the chain of image processing functions."""
        self._chain.append(func)
        return self

    def call(self, im: Mat) -> Mat:
        """Applies the chain to `im`.
        Re-raises exceptions as `ChainException`, if occurred.
        """
        for n, func in enumerate(self._chain):
            try:
                im = func(im)
            except Exception as e:
                raise ChainException(e, n, func) from e
        return im

class IterationImage:
    def __init__(self, img, defaulted, bins, centers) -> None:
        self.img: Mat = img
        self.defaulted: Mat = defaulted
        self.bins: dict[str, Mat] = bins
        self.centers: dict[str, Mat] = centers

    @property
    def robot_vect(self) -> np.ndarray | None:
        if not (self.centers["red"].all() and self.centers["purple"].all()):
            print("unable to calc robot vect")
            return

        return self.centers["purple"] - self.centers["red"]


class Loop:
    def __init__(
        self,
        toolbox: ImageToolbox,
        video_source: cv.VideoCapture,
        bin_kwargs: dict = None,
        skip_centers: bool | list = False,
    ) -> None:
        self.toolbox = toolbox
        self.video_source = video_source
        self.bin_kwargs = bin_kwargs or {}
        self.skip_centers = skip_centers

    def __enter__(self) -> IterationImage:
        ret, img = self.video_source.read()
        defaulted = self.toolbox.default_chain.call(img)
        bins = self.toolbox.bins(defaulted, **self.bin_kwargs)
        if self.skip_centers:
            if isinstance(self.skip_centers, t.Iterable):
                centers = self.toolbox.centers(
                    {
                        k: bin_
                        for k, bin_ in bins.items()
                        if k not in self.skip_centers
                    }
                )
        else:
            centers = self.toolbox.centers(bins)

        self.image = IterationImage(img, defaulted, bins, centers)
        return self.image

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        cv.imshow("image", self.image.img)
        transformed = self.toolbox.draw_bounds(self.image.defaulted)
        cv.imshow("transformed", transformed)


class ImageToolbox:
    def __init__(self, **kwargs) -> None:
        """Class that provides tools for image processing."""
        self.settings = {
            "x1": 0,
            "y1": 0,
        }
        self.can_type = "green"
        self.settings.update(kwargs)

        self._default_chain = (
            self.chain.add(self.resize)
            .add(partial(cv.cvtColor, code=cv.COLOR_BGR2HSV))
        )

    def bins(
        self,
        defaulted,
        *,
        colors=("red", "yellow",),
        to_dilate=("red",),
    ):
        return {
            k: (
                (
                    self.chain.add(self.bin(name=k)).add(
                        partial(
                            cv.erode,
                            kernel=cv.getStructuringElement(cv.MORPH_RECT, (7, 7)),
                        )
                    )
                    if k == "purple"
                    else self.chain.add(self.bin(name=k))
                ).add(
                    partial(
                        cv.dilate,
                        kernel=cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)),
                    )
                )
                if k in to_dilate
                else self.chain.add(self.bin(name=k))
            ).call(defaulted)
            for k in colors
        }

    def zero_point(self):
        return np.asarray((self.settings["xc"], self.settings["yc"]))

    def as_int_array(self, array):
        return np.array([int(i) for i in array])

    def centers(self, bins, *, perspective_correction=True, zero_point=None, draw=True):
        centers: dict[str, np.ndarray] = {}
        for name, bin_ in bins.items():
            M = cv.moments(bin_)
            if M["m00"] != 0.0:
                cnt = self.M_point(M)
                centers[name] = cnt
                if draw:
                    img_ = cv.cvtColor(bin_, cv.COLOR_GRAY2BGR)
                    bin_ = cv.circle(img_, cnt, 10, (0, 0, 255))

                if perspective_correction:
                    if zero_point is None:
                        zero_point = np.array(
                            [self.settings["x1"], self.settings["y1"]]
                        )
                    C = self.as_int_array(bin_.shape[:2][::-1])//2 - zero_point
                    A = centers[name]
                    k = None
                    if name in ("yellow",):
                        k = self.settings["h_r"] / self.settings["H"]
                    if name in ("red",):
                        k = self.settings["h_c"] / self.settings["H"]
                    if k:
                        centers[name] = self.as_int_array(A + k * (C - A))
                        if draw:
                            bin_ = cv.circle(img_, centers[name], 10, (0, 255, 0))
            else:
                centers[name] = np.asarray((0, 0))
            if draw:
                cv.imshow(f"{name}_bin", bin_)
        return centers

    @staticmethod
    def M_point(M: t.Mapping) -> Mat[int, int]:
        """Calculates mass center of a raw moments `M`."""
        cnt_x = int(M["m10"] / M["m00"])
        cnt_y = int(M["m01"] / M["m00"])
        return np.asarray((cnt_x, cnt_y))

    @staticmethod
    def unit_vector(vector: np.matrix) -> np.matrix:
        """Returns the unit vector of the vector."""
        return vector / np.linalg.norm(vector)

    @staticmethod
    def angle_between(v1: np.matrix, v2: np.matrix) -> float:
        """
        #NOT IN USE.
        Look for `ImageToolbox.signed_angle`.

        Returns the angle in radians between vectors 'v1' and 'v2'::

        >>> angle_between((1, 0, 0), (0, 1, 0))
        1.5707963267948966
        >>> angle_between((1, 0, 0), (1, 0, 0))
        0.0
        >>> angle_between((1, 0, 0), (-1, 0, 0))
        3.141592653589793
        """
        v1_u = ImageToolbox.unit_vector(v1)
        v2_u = ImageToolbox.unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

    @staticmethod
    def signed_angle(v1: np.matrix, v2: np.matrix):
        """Returns the CCW angle in radians / pi (i.e. [-1, 1])
        between 2-dimensional vectors from 'v1' to 'v2'::

        >>> signed_angle((1, 0), (0, 1))
        1.5707963267948966
        >>> signed_angle((1, 0), (-1, 0))
        3.141592653589793
        >>> signed_angle((-3, 1), (5, 2))
        -2.439335722080786
        """
        return np.arctan2(np.linalg.det([v1, v2]), np.dot(v1, v2)) / np.pi

    def draw_bounds(self, img: Mat) -> Mat:
        cv.rectangle(img, (self.settings["l_brd"], 0), (self.settings["l_brd"], img.shape[1]), (255, 255, 0), 2)
        cv.rectangle(img, (self.settings["r_brd"], 0), (self.settings["r_brd"], img.shape[1]), (255, 255, 0), 2)

        return img

    min_max = lambda self, v, mn, mx: min(max(v, mn), mx)

    def set_hsv(self, color: list, name: str, dh: int, ds: int, dv: int) -> None:
        """Sets into inner `settings` presets hsv `color`
        masks by new `name` replacing elder records.

        Masks are created using deltas representing a step
        in each direction for each spectrum.
        """
        min_max = self.min_max

        hsv = [
            np.asarray(
                (
                    min_max(int(color[0]) - dh, 0, 180),
                    min_max(int(color[1]) - ds, 0, 255),
                    min_max(int(color[2]) - dv, 0, 255),
                )
            ),
            np.asarray(
                (
                    min_max(int(color[0]) + dh, 0, 180),
                    min_max(int(color[1]) + ds, 0, 255),
                    min_max(int(color[2]) + dv, 0, 255),
                )
            ),
        ]
        self.settings["hsv"][name] = hsv

    def load(self) -> None:
        """Loads last `settings` from local file `last_settings.json`."""
        with open("last_settings.json", "r") as f:
            obj = json.load(f, cls=NumpyDecoder)
            self.settings.update(obj)

    def dump(self) -> None:
        """Saves current `settings` into local file `last_settings.json`."""
        with open("last_settings.json", "w+") as f:
            json.dump(self.settings, f, cls=NumpyEncoder)

    def square(self, im, center, r):
        return im[
            center[1] - r : center[1] + r,
            center[0] - r : center[0] + r,
        ]

    def resize(self, im: Mat, factor: int = 4) -> Mat:
        """Scale down the image `im` by a `factor`. Chainable."""
        return cv.resize(im, (im.shape[1] // factor, im.shape[0] // factor))

    def to_binary(
        self, im: Mat, name: str | None = None, masks: list[tuple] | None = None
    ) -> Mat:
        """Converts `im` to binary image by hsv `masks`.

        Uses inner `settings` presets if color `name` were passed.

        You can't chain this function.
        See `ImageToolbox.bin` for a wrapper.
        """
        if name is None and masks is None:
            raise TypeError("unable to define bounds")
        masks = masks or self.settings["hsv"][name]
        masks = [np.array(mask, np.uint8) for mask in masks]
        return cv.inRange(im, *masks)

    def bin(self, name: str | None = None, masks: list[tuple] | None = None):
        """Wraps `ImageToolbox.to_binary` to make it chainable."""
        return partial(self.to_binary, name=name, masks=masks)

    

    @property
    def default_chain(self) -> Chain:
        return self._default_chain
    
    @default_chain.setter
    def default_chain(self, chain):
        self._default_chain = chain

    @property
    def chain(self) -> Chain:
        """Returns `Chain` object with current `settings` presets."""
        return Chain(self)

    def tick(self, exit_char: str, time:int = 30) -> bool:
        return (cv.waitKey(time) & 0xFF) != ord(exit_char)

    def entry_loop(
        self,
        vid: cv.VideoCapture | int,
        *,
        bin_kwargs: dict | None = None,
        skip_centers: bool | list = False,
    ) -> Loop:
        if isinstance(vid, int):
            vid = cv.VideoCapture(vid)
        return Loop(self, vid, bin_kwargs, skip_centers)
