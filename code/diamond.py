"""Color source with a square placeholder independent of removed object assets."""
from dataclasses import dataclass

import pico2d

from .settings import SCREEN_WIDTH


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
    def draw(self, sources, camera_x, camera_y=0):
        for source in sources:
            if source.right >= camera_x and source.left <= camera_x + SCREEN_WIDTH:
                color = (48, 164, 231) if source.has_blue else (150, 156, 162)
                half = source.WIDTH / 2
                x, y = source.x - camera_x, source.y - camera_y
                bounds = (round(x - half), round(y - half), round(x + half), round(y + half))
                pico2d.draw_rectangle(*bounds, *color, filled=True)
                pico2d.draw_rectangle(*bounds, 217, 225, 232)
