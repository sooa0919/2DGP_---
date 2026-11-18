"""Grayscale dungeon masonry and timber from the main_lev_build atlas."""
import math
import pico2d
from .background import Background
from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT
from .water import AnimatedWater
from .diamond import DiamondRenderer


class TempleBackground(Background):
    def __init__(self, level):
        self.level = level
        self.size = getattr(level, 'tile_size', 32)
        self.sheet = pico2d.load_image(str(
            IMAGE_ROOT / 'background/grayscale/main_lev_build.png'))
        self.terrain = level.terrain_tiles()
        self.water = AnimatedWater()
        self.diamonds = DiamondRenderer() if getattr(level, 'color_sources', []) else None
        self.supports = []
        # Place background timber inside actual gaps between floors and ceilings.
        for x in range(192, level.width, 320):
            spans = sorted((p.bottom, p.top) for p in level.platforms
                           if p.left <= x < p.right)
            merged = []
            for bottom, top in spans:
                if merged and bottom <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], top))
                else:
                    merged.append((bottom, top))
            for lower, upper in zip(merged, merged[1:]):
                if upper[0] - lower[1] >= 128:
                    self.supports.append((x, lower[1], upper[0]))

    def update(self, dt):
        self.water.update(dt, self.level.water)
        for source in getattr(self.level, 'color_sources', []):
            source.update(dt)

    def patch(self, sx, sy, sw, sh, x, y, width, height, angle=0):
        self.sheet.clip_composite_draw(sx, self.sheet.h - sy - sh, sw, sh,
                                       angle, '', round(x), round(y), width, height)

    def draw(self, camera_x, camera_y=0):
        pico2d.draw_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 12, 12, 12, filled=True)
        # Continuous room walls use the atlas' complete brick panel.
        background_size = 32
        first_x = math.floor(camera_x / background_size)
        first_y = math.floor(camera_y / background_size)
        self.sheet.opacify(.85)
        for col in range(first_x, math.ceil((camera_x + SCREEN_WIDTH) / background_size)):
            for row in range(first_y, math.ceil((camera_y + SCREEN_HEIGHT) / background_size)):
                self.patch(1152 + col % 9 * 16, 464 + row % 7 * 16, 16, 16,
                           col * background_size + background_size / 2 - camera_x,
                           row * background_size + background_size / 2 - camera_y,
                           background_size, background_size)
        self.sheet.opacify(.72)
        for x, floor, ceiling in self.supports:
            if camera_x - 144 <= x <= camera_x + SCREEN_WIDTH + 144:
                self.patch(1872, 176, 144, 32, x - camera_x,
                           ceiling - 32 - camera_y, 288, 64)
                self.patch(1936, 208, 16, 80, x - camera_x,
                           (floor + ceiling - 64) / 2 - camera_y,
                           32, ceiling - floor - 64)
        size = self.size
        for col, row in self.terrain:
            if not (camera_x - size < col * size < camera_x + SCREEN_WIDTH
                    and camera_y - size < row * size < camera_y + SCREEN_HEIGHT):
                continue
            x = col * size + size / 2 - camera_x
            y = row * size + size / 2 - camera_y
            # Fill beneath each trim, including its transparent corner pixels.
            pico2d.draw_rectangle(round(x - size / 2), round(y - size / 2),
                                  round(x + size / 2), round(y + size / 2),
                                  7, 7, 7, filled=True)
            self.sheet.opacify(.4)
            self.patch(1152 + col % 9 * 16, 464 + row % 7 * 16,
                       16, 16, x, y, size, size)
            self.sheet.opacify(1)
            # Rotate the same bright stone trim toward every exposed face.
            for dx, dy, angle in ((-1, 0, math.pi / 2), (1, 0, -math.pi / 2),
                                  (0, -1, math.pi), (0, 1, 0)):
                if (col + dx, row + dy) not in self.terrain:
                    self.patch(240 + (col + row) % 3 * 16, 720, 16, 16,
                               x, y, size, size, angle)
        self.sheet.opacify(1)
        for platform in getattr(self.level, 'thin_platforms', []):
            for start in range(platform.left, platform.right, size):
                width = min(size, platform.right - start)
                self.patch(1872, 48, 16, 8, start + width / 2 - camera_x,
                           (platform.bottom + platform.top) / 2 - camera_y,
                           width, platform.top - platform.bottom)

    def draw_overlay(self, camera_x, player, camera_y=0):
        self.water.draw_surface(self.level.water, camera_x, camera_y)
        if self.diamonds:
            self.diamonds.draw(self.level.color_sources, camera_x, camera_y)
