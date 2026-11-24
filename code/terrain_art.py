"""Illustrated terrain skins; all physical platforms remain owned by the level."""
import math
import pico2d
from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT


class TerrainArt:
    SIZE = 64

    def __init__(self):
        folder = IMAGE_ROOT / 'background/tutorial_tiles'
        names = [f'{kind}_{i}' for kind in ('dirt', 'grass', 'stone') for i in range(8)]
        names += [f'{kind}_{i}' for kind in ('water', 'fall') for i in range(3)]
        names += ['water_gray', 'fall_gray', 'rock', 'rocks', 'sprout', 'flowers', 'ledge', 'vine_cap', 'lamp', 'lamp_on']
        self.images = {name: pico2d.load_image(str(folder / f'{name}.png')) for name in names}

    def terrain(self, platform, camera_x, camera_y):
        p = platform
        if p.right < camera_x or p.left > camera_x + SCREEN_WIDTH:
            return
        if p.top - p.bottom <= 16:
            self.ledge(p, camera_x, camera_y)
            return
        first = max(0, int((camera_x - p.left) // self.SIZE))
        last = min(math.ceil((p.right - p.left) / self.SIZE),
                   math.ceil((camera_x + SCREEN_WIDTH - p.left) / self.SIZE))
        for row in range(math.ceil((p.top - p.bottom) / self.SIZE)):
            top = p.top - row * self.SIZE
            bottom = max(p.bottom, top - self.SIZE)
            if top < camera_y or bottom > camera_y + SCREEN_HEIGHT:
                continue
            for column in range(first, last):
                left = p.left + column * self.SIZE
                width = min(self.SIZE, p.right - left)
                height = top - bottom
                variant = (int(p.left // 32) + column * 3 + row * 5) % 8
                rocky = p.top >= 304
                name = f'stone_{(2, 5, 6)[variant % 3]}' if rocky else f'dirt_{variant}'
                self.cell(self.images[name], left, top, width, height, camera_x, camera_y)
                if row == 0 and p.top < 1008:
                    self.cell(self.images[f'grass_{variant}'], left, top, width, height, camera_x, camera_y)

    def cell(self, image, left, top, width, height, camera_x, camera_y):
        image.clip_draw(0, image.h - height, width, height,
                        left + width / 2 - camera_x, top - height / 2 - camera_y, width, height)

    def ledge(self, p, camera_x, camera_y):
        if p.top < camera_y or p.bottom > camera_y + SCREEN_HEIGHT:
            return
        for x in range(int(p.left), int(p.right), 64):
            width = min(64, p.right - x)
            if x + width >= camera_x and x <= camera_x + SCREEN_WIDTH:
                image = self.images['ledge']
                image.clip_draw(0, 0, max(1, round(image.w * width / 64)), image.h,
                                x + width / 2 - camera_x, p.top - 8 - camera_y, width, 16)

    def vine_leaf(self, p, camera_x, camera_y):
        for x in range(int(p.left), int(p.right), 64):
            width = min(64, p.right - x)
            if x + width >= camera_x and x <= camera_x + SCREEN_WIDTH:
                image = self.images['vine_cap']
                image.clip_draw(0, 0, width, image.h, x + width / 2 - camera_x,
                                p.top - 6 - camera_y, width, 12)

    def water(self, item, camera_x, camera_y, time, vertical=False):
        if item.right < camera_x or item.left > camera_x + SCREEN_WIDTH:
            return
        if item.top < camera_y or item.bottom > camera_y + SCREEN_HEIGHT:
            return
        blue = item.has_blue
        kind = 'fall' if vertical else 'water'
        name = f'{kind}_{int(time / .22) % 3}' if blue else f'{kind}_gray'
        image = self.images[name]
        image.opacify(.86 if blue else 1)
        if vertical:
            image.draw((item.left + item.right) / 2 - camera_x,
                       (item.bottom + item.top) / 2 - camera_y,
                       item.right - item.left, item.top - item.bottom)
            return
        for x in range(int(item.left), int(item.right), 64):
            width = min(64, item.right - x)
            if x + width < camera_x or x > camera_x + SCREEN_WIDTH:
                continue
            for top in range(int(item.top), int(item.bottom), -48):
                height = min(48, top - item.bottom)
                if top == item.top:
                    self.cell(image, x, top, width, height, camera_x, camera_y)
                else:
                    image.clip_draw(0, 0, width, 18, x + width / 2 - camera_x,
                                    top - height / 2 - camera_y, width, height)

    def lamp(self, item, camera_x, camera_y):
        name = 'lamp_on' if item.active else 'lamp'
        self.images[name].draw((item.left + item.right) / 2 - camera_x,
                               (item.top + item.bottom) / 2 - camera_y,
                               item.right - item.left, item.top - item.bottom)

    def decorations(self, camera_x, camera_y):
        for name, x, floor, width, height in (
                ('rock', 236, 96, 54, 34), ('sprout', 46, 96, 36, 20),
                ('flowers', 720, 96, 40, 24), ('rocks', 1080, 480, 68, 38),
                ('sprout', 1420, 224, 34, 20), ('rock', 1942, 304, 42, 27),
                ('rocks', 2800, 96, 58, 34), ('sprout', 3860, 96, 40, 24)):
            if camera_x - width < x < camera_x + SCREEN_WIDTH + width:
                self.images[name].draw(x - camera_x, floor + height / 2 - camera_y, width, height)
