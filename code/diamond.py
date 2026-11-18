"""Animated blue color source using the supplied five diamond frames."""
from dataclasses import dataclass

import pico2d

from .settings import IMAGE_ROOT, SCREEN_WIDTH


@dataclass
class Diamond:
    x: float
    y: float
    has_blue: bool = True
    animation_time: float = 0.0

    WIDTH = 32
    HEIGHT = 36
    FRAMES = 5
    FPS = 8

    @property
    def left(self):
        return self.x - self.WIDTH / 2

    @property
    def right(self):
        return self.x + self.WIDTH / 2

    @property
    def bottom(self):
        return self.y - self.HEIGHT / 2

    @property
    def top(self):
        return self.y + self.HEIGHT / 2

    @property
    def frame(self):
        return int(self.animation_time * self.FPS) % self.FRAMES

    def update(self, dt):
        self.animation_time = (self.animation_time + dt) % (self.FRAMES / self.FPS)

    def reset(self):
        self.has_blue = True
        self.animation_time = 0.0


class DiamondRenderer:
    def __init__(self):
        folder = IMAGE_ROOT / 'object/diamond'
        self.blue = [pico2d.load_image(str(folder / f'blue-{i:02}.png'))
                     for i in range(1, 6)]
        self.gray = [pico2d.load_image(str(folder / f'gray-{i:02}.png'))
                     for i in range(1, 6)]

    def draw(self, sources, camera_x, camera_y=0):
        for source in sources:
            if source.right >= camera_x and source.left <= camera_x + SCREEN_WIDTH:
                frames = self.blue if source.has_blue else self.gray
                frames[source.frame].draw(round(source.x - camera_x),
                                          round(source.y - camera_y),
                                          source.WIDTH, source.HEIGHT)
