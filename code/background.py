import math

import pico2d

from .level import Level
from .settings import IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE


class Background:
    def __init__(self, level=None):
        self.level = level or Level()
        scenery = IMAGE_ROOT / "background" / "grayscale"
        if self.level.index == 0:
            paths = [scenery / "background3_jungle2" / f"plx-{i}.png" for i in range(1, 6)]
        else:
            paths = [scenery / "temple" / name for name in
                     ("background.png", "background2.png", "background3.png", "background4.png")]
        self.layers = [pico2d.load_image(str(p)) for p in paths]
        self.scroll_rates = (0.0, 0.15, 0.3, 0.5, 0.75)
        self.tiles = {i: pico2d.load_image(str(scenery / "tiles" / f"Tile_{i:02}.png"))
                      for i in (1, 2, 3, 11, 12, 13, 24, 57, 58)}
        self.objects = {name: pico2d.load_image(str(scenery / "objects" / f"{name}.png"))
                        for name, *_ in self.level.objects}
        self.prompt = pico2d.load_image(str(scenery / "press_e.png"))
        self.title = pico2d.load_image(str(scenery / ("grove.png" if self.level.index == 0 else "temple.png")))
        self.controls = pico2d.load_image(str(scenery / "controls.png"))

    def draw(self, camera_x):
        for layer, rate in zip(self.layers, self.scroll_rates):
            offset = round(camera_x * rate) % SCREEN_WIDTH
            for start in (-offset, SCREEN_WIDTH - offset):
                layer.draw(start + SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                           SCREEN_WIDTH, SCREEN_HEIGHT)
        for platform in self.level.platforms:
            first = max(platform.left // TILE_SIZE, math.floor(camera_x / TILE_SIZE))
            last = min(platform.right // TILE_SIZE, math.ceil((camera_x + SCREEN_WIDTH) / TILE_SIZE))
            for col in range(first, last):
                edge = 0 if col * TILE_SIZE == platform.left else (2 if (col + 1) * TILE_SIZE == platform.right else 1)
                for y in range(platform.bottom, platform.top, TILE_SIZE):
                    if y == platform.top - TILE_SIZE:
                        tile = (1, 2, 3)[edge]
                    elif edge != 1:
                        tile = (11, 12, 13)[edge]
                    else:
                        tile = (12, 24, 57, 58)[(col * 7 + y // TILE_SIZE) % 4]
                    self.tiles[tile].draw(col * TILE_SIZE + 16 - round(camera_x), y + 16, 32, 32)
        for name, x, y, scale in self.level.objects:
            obj = self.objects[name]
            w, h = obj.w * scale, obj.h * scale
            if -w < x - camera_x < SCREEN_WIDTH + w:
                obj.draw(round(x - camera_x), y + h / 2, w, h)

    def draw_overlay(self, camera_x, player):
        self.title.draw(24 + self.title.w / 2, SCREEN_HEIGHT - 36)
        self.controls.draw(24 + self.controls.w / 2, SCREEN_HEIGHT - 88)
        if self.level.can_exit(player):
            self.prompt.draw(round(self.level.exit_x - camera_x), self.level.exit_y + 190)
