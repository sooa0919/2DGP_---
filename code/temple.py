"""Ruined masonry only: no decorative props or future puzzle objects."""
import math
import pico2d
from .background import Background
from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT
from .water import AnimatedWater


class TempleBackground(Background):
    def __init__(self, level):
        self.level = level
        self.sheet = pico2d.load_image(str(IMAGE_ROOT / 'background/tile/Tilesetv3.png'))
        self.terrain = level.terrain_tiles()
        self.water = AnimatedWater()

    def tile(self, sx, sy, x, y, size=32):
        self.sheet.clip_draw(sx, self.sheet.h - sy - 16, 16, 16, x, y, size, size)

    def draw(self, camera_x):
        pico2d.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 21, 20, 29, filled=True)
        # Recessed masonry and broken wall piers recede behind the playable tiles.
        offset = int(camera_x * .24)
        for col in range(-1, 39):
            x = col * 32 - offset % 32 + 16
            for row in range(21):
                self.sheet.opacify(.22)
                self.tile(160 + (col % 3) * 16, 224 + (row % 3) * 16, x, row * 32 + 16)
        self.sheet.opacify(.48)
        for world_x in range(96, self.level.width, 448):
            x = world_x - camera_x * .55
            if -64 < x < SCREEN_WIDTH + 64:
                for y in range(192, 576 - (world_x // 448 % 3) * 64, 32):
                    self.tile(80, 192 + (y // 32 % 2) * 16, x, y)
        self.sheet.opacify(1)
        first = math.floor(camera_x / 32)
        last = math.ceil((camera_x + SCREEN_WIDTH) / 32)
        for (col, row), tile in self.terrain.items():
            if first <= col < last:
                # Worn stone lips above plain temple brick; no forest moss.
                sx, sy = ((80 + (col % 3) * 16, 144) if tile in (1, 2, 3)
                          else (80 + (col % 3) * 16, 192 + row % 2 * 16))
                self.tile(sx, sy, col * 32 + 16 - round(camera_x), row * 32 + 16)

    def draw_overlay(self, camera_x, player):
        self.water.draw_surface(self.level.water, camera_x)
