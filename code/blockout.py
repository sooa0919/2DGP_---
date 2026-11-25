"""Forest backdrop and the supplied, fully assembled stage illustration."""
import pico2d
from .display import load_pixel_image

from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT
from .diamond import DiamondRenderer
from .stage_art import StageArt


class ForestBlockout:
    def __init__(self, level):
        self.level = level
        folder = IMAGE_ROOT / 'background/grayscale/background3_jungle2'
        self.layers = [load_pixel_image(str(folder / f'plx-{i}.png')) for i in range(1, 6)]
        self.diamonds = DiamondRenderer()
        self.stage = StageArt(level)
        self.time = 0.0
        self.scroll_rates = (0, .12, .24, .4, .6)

    def update(self, dt):
        self.time += dt

    def draw(self, camera_x, camera_y=0):
        height = max(SCREEN_HEIGHT, self.level.height)
        width = round(height * SCREEN_WIDTH / SCREEN_HEIGHT)
        for layer, rate in zip(self.layers, self.scroll_rates):
            offset = round(camera_x * rate) % width
            for start in (-offset, width - offset):
                layer.draw(start + width / 2, height / 2 - camera_y, width, height)
        self.stage.draw(camera_x, camera_y)

    def draw_overlay(self, camera_x, player, camera_y=0):
        self.stage.draw_water(camera_x, camera_y)
        self.diamonds.draw(self.level.color_sources, camera_x, camera_y)
