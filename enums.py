from enum import Enum


class Color(tuple, Enum):
    BLACK = (0,0,0)
    GRAY25 = (70,70,70)
    GRAY50 = (128,128,128)
    GRAYISH = (108, 118, 155)
    WHITE = (255,255,255)
    RED = (255,0,0)
    GREEN = (0,255,0)
    MOSAIC = (80, 80, 80)
    SIGN = (150, 100, 50)