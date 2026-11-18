"""Ruined masonry only: no decorative props or future puzzle objects."""
import math
import pico2d
from .background import Background
from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT
from .water import AnimatedWater


class TempleBackground(Background):
    def __init__(self, level):
        self.level = level
        self.sheet = pico2d.load_image(str(IMAGE_ROOT / 'background/grayscale/temple.png'))
        self.terrain = level.terrain_tiles()
        self.water = AnimatedWater()

    def tile(self, sx, sy, x, y, size=32):
        self.sheet.clip_draw(sx, self.sheet.h - sy - 16, 16, 16, x, y, size, size)

    def draw(self, camera_x, camera_y=0):
        pico2d.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 23, 23, 23, filled=True)
        # Recessed masonry and broken wall piers recede behind the playable tiles.
        offset = int(camera_x * .24)
        offset_y = int(camera_y * .24)
        for col in range(-1, 39):
            x = col * 32 - offset % 32 + 16
            for row in range(-1, 22):
                self.sheet.opacify(.22)
                self.tile(176, 256 + (row % 2) * 16, x,
                          row * 32 + 16 - offset_y % 32)
        self.sheet.opacify(.48)
        for world_x in range(96, self.level.width, 448):
            x = world_x - camera_x * .55
            if -64 < x < SCREEN_WIDTH + 64:
                for y in range(192, getattr(self.level, 'height', 648) - 72
                               - (world_x // 448 % 3) * 64, 32):
                    self.tile(96, 272 + (y // 32 % 2) * 16, x, y - camera_y * .55)
        self.sheet.opacify(1)
        first = math.floor(camera_x / 32)
        last = math.ceil((camera_x + SCREEN_WIDTH) / 32)
        for (col, row), tile in self.terrain.items():
            if first <= col < last and camera_y - 32 < row * 32 < camera_y + SCREEN_HEIGHT:
                x, y = col * 32 + 16 - round(camera_x), row * 32 + 16 - round(camera_y)
                # The stone lip has transparent padding. Keep masonry behind
                # it so that the padding cannot expose the background.
                self.tile(96, 240 + row % 2 * 16, x, y)
                if tile in (1, 2, 3):
                    self.tile(144 + (col % 3) * 16, 144, x, y)
        for platform in getattr(self.level, 'thin_platforms', []):
            for start in range(platform.left, platform.right, 32):
                if camera_x - 32 <= start <= camera_x + SCREEN_WIDTH:
                    width = min(32, platform.right - start)
                    self.sheet.clip_draw(160, self.sheet.h - 148, 16, 4,
                                         start + width / 2 - camera_x,
                                         (platform.bottom + platform.top) / 2 - round(camera_y),
                                         width, platform.top - platform.bottom)

    def draw_overlay(self, camera_x, player, camera_y=0):
        self.water.draw_surface(self.level.water, camera_x)
