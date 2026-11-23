"""Forest backdrop with simple rectangular terrain and color devices."""
import pico2d

from .settings import FONT_PATH, IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT
from .diamond import DiamondRenderer


COLORS = {'blue': (48, 164, 231), 'green': (68, 190, 104), 'yellow': (249, 211, 80)}


class ForestBlockout:
    def __init__(self, level):
        self.level = level
        folder = IMAGE_ROOT / 'background/grayscale/background3_jungle2'
        self.layers = [pico2d.load_image(str(folder / f'plx-{i}.png')) for i in range(1, 6)]
        self.diamonds = DiamondRenderer()
        self.font = pico2d.load_font(str(FONT_PATH), 16)
        self.time = 0.0
        self.scroll_rates = (0, .12, .24, .4, .6)

    def update(self, dt):
        self.time += dt

    def box(self, item, camera_x, camera_y, color, filled=True, alpha=255):
        left, right = item.left - camera_x, item.right - camera_x
        bottom, top = item.bottom - camera_y, item.top - camera_y
        if right < 0 or left > SCREEN_WIDTH or top < 0 or bottom > SCREEN_HEIGHT:
            return
        pico2d.draw_rectangle(round(left), round(bottom), round(right), round(top),
                              *color, alpha, filled=filled)

    def draw(self, camera_x, camera_y=0):
        height = max(SCREEN_HEIGHT, self.level.height)
        width = round(height * SCREEN_WIDTH / SCREEN_HEIGHT)
        for layer, rate in zip(self.layers, self.scroll_rates):
            offset = round(camera_x * rate) % width
            for start in (-offset, width - offset):
                layer.draw(start + width / 2, height / 2 - camera_y, width, height)
        for p in self.level.platforms:
            self.box(p, camera_x, camera_y, (32, 35, 38))
            self.box(p, camera_x, camera_y, (178, 182, 184), False)
        for p in self.level.thin_platforms:
            self.box(p, camera_x, camera_y, (154, 158, 161))
        for vine in self.level.vines:
            color = COLORS['green'] if vine.active else (157, 166, 159)
            center = (vine.left + vine.stem_right) / 2 - camera_x
            height = vine.top if vine.active else vine.bottom + 28
            if -128 < center < SCREEN_WIDTH + 128:
                pico2d.draw_rectangle(round(center - 5), round(vine.bottom - camera_y),
                                      round(center + 5), round(height - camera_y), *color, filled=True)
            for leaf in vine.leaves():
                if vine.active:
                    self.box(leaf, camera_x, camera_y, color)
                else:
                    for x in range(int(leaf.left), int(leaf.right), 20):
                        if camera_x - 12 < x < camera_x + SCREEN_WIDTH:
                            pico2d.draw_rectangle(round(x - camera_x), round(leaf.top - camera_y - 2),
                                                  round(min(x + 12, leaf.right) - camera_x),
                                                  round(leaf.top - camera_y), *color, filled=True)
            if -128 < center < SCREEN_WIDTH + 128:
                self.font.draw(center - 30, vine.bottom + 18 - camera_y, vine.name, color)
        for water in self.level.water:
            color = COLORS['blue'] if water.has_blue else (128, 137, 146)
            self.box(water, camera_x, camera_y, color, alpha=155 if water.has_blue else 255)
            self.box(water, camera_x, camera_y, (205, 213, 220), False)
        for drop in self.level.droplets:
            self.box(drop, camera_x, camera_y, COLORS['blue'] if drop.has_blue else (186, 195, 205),
                     alpha=165 if drop.has_blue else 255)
            self.box(drop, camera_x, camera_y, (214, 222, 230), False)
        self.box(self.level.lamp, camera_x, camera_y,
                 COLORS['yellow'] if self.level.lamp.active else (126, 124, 108))
        self.box(self.level.door, camera_x, camera_y,
                 COLORS['yellow'] if self.level.lamp.active else (70, 72, 75),
                 not self.level.lamp.active)
        self.box(self.level.door, camera_x, camera_y, (213, 213, 195), False)
        if camera_x + SCREEN_WIDTH > self.level.lamp.left:
            self.font.draw(self.level.lamp.left - camera_x - 5,
                           self.level.lamp.top + 18 - camera_y, '노랑 등불', (243, 228, 163))
            self.font.draw(self.level.door.right - camera_x + 12,
                           self.level.door.bottom + 36 - camera_y, '출구', (243, 228, 163))

    def draw_overlay(self, camera_x, player, camera_y=0):
        self.diamonds.draw(self.level.color_sources, camera_x, camera_y)
