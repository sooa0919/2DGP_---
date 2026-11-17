import math

import pico2d

from .level import Level
from .scenery import PROP_BOUNDS
from .water import AnimatedWater
from .settings import IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE


class Background:
    def __init__(self, level=None):
        self.level = level or Level()
        scenery = IMAGE_ROOT / "background" / "grayscale"
        paths = [scenery / "background3_jungle2" / f"plx-{i}.png" for i in range(1, 6)]
        self.layers = [pico2d.load_image(str(p)) for p in paths]
        self.scroll_rates = (0.0, 0.15, 0.3, 0.5, 0.75)
        self.tiles = {i: pico2d.load_image(str(scenery / "tiles" / f"Tile_{i:02}.png"))
                      for i in (1, 2, 3, 11, 12, 13)}
        self.terrain = self.level.terrain_tiles()
        self.objects = {name: pico2d.load_image(str(scenery / "objects" / f"{name}.png"))
                        for name, *_ in self.level.objects}
        self.water = AnimatedWater()

    def update(self, dt):
        self.water.update(dt)

    def draw(self, camera_x):
        for layer, rate in zip(self.layers, self.scroll_rates):
            offset = round(camera_x * rate) % SCREEN_WIDTH
            for start in (-offset, SCREEN_WIDTH - offset):
                layer.draw(start + SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                           SCREEN_WIDTH, SCREEN_HEIGHT)
        first = math.floor(camera_x / TILE_SIZE)
        last = math.ceil((camera_x + SCREEN_WIDTH) / TILE_SIZE)
        for (col, row), tile in self.terrain.items():
            if first <= col < last:
                self.tiles[tile].draw(col * 32 + 16 - round(camera_x), row * 32 + 16, 32, 32)
        self.water.draw_falls(self.level.waterfalls, camera_x)
        for name, x, y, scale in self.level.objects:
            obj = self.objects[name]
            left, top, right, bottom = PROP_BOUNDS[name]
            w, h = (right - left) * scale, (bottom - top) * scale
            if -w < x - camera_x < SCREEN_WIDTH + w:
                obj.clip_draw(left, obj.h - bottom, right - left, bottom - top,
                              round(x - camera_x), y - 2 + h / 2, w, h)

    def draw_overlay(self, camera_x, player):
        # Water is drawn over the player; its surface is never solid terrain.
        self.water.draw_surface(self.level.water, self.level.waterfalls, camera_x)
