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
                      for i in (1, 2, 3, 10, 11, 12, 13, 20, 30)}
        self.terrain = self.level.terrain_tiles()
        for i in (10, 20, 30):
            self.tiles[i].opacify(0.55)
        self.objects = {name: pico2d.load_image(str(scenery / "objects" / f"{name}.png"))
                        for name, *_ in self.level.objects}
        self.prompt = pico2d.load_image(str(scenery / "press_e.png"))

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
        for name, x, y, scale in self.level.objects:
            obj = self.objects[name]
            w, h = obj.w * scale, obj.h * scale
            if -w < x - camera_x < SCREEN_WIDTH + w:
                obj.draw(round(x - camera_x), y + h / 2, w, h)

    def draw_overlay(self, camera_x, player):
        # Water is drawn over the player; its surface is never solid terrain.
        for pool in self.level.water:
            for x in range(pool.left, pool.right, 32):
                if -32 <= x - camera_x <= SCREEN_WIDTH:
                    for y in range(pool.bottom, pool.top, 32):
                        self.tiles[10 if y == pool.top - 32 else 20].draw(
                            x + 16 - round(camera_x), y + 16, 32, 32)
        if self.level.can_exit(player):
            self.prompt.draw(round(self.level.exit_x - camera_x), self.level.exit_y + 190)
