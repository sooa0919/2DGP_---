"""Draw the supplied stage composition at its original relative coordinates."""
import pico2d
import json

from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT


class StageArt:
    WIDTH, HEIGHT = 4096, 1008
    CHUNK_WIDTH = 1024

    def __init__(self, level=None):
        self.level = level
        folder = IMAGE_ROOT / 'background/stage1'
        self.chunks = [pico2d.load_image(str(folder / f'stage_{i}.png'))
                       for i in range(4)]
        self.layout = json.loads((folder / 'layout.json').read_text(encoding='utf-8'))
        self.sprites = {name + suffix: pico2d.load_image(str(folder / f'{name}{suffix}.png'))
                        for name in self.layout for suffix in ('', '_gray')}

    def sprite(self, name, camera_x, camera_y, gray=False, offset=0, trim_bottom=None, opacity=1.0, trim_top=None):
        left, bottom, right, top = self.layout[name]
        bottom += offset
        top += offset
        visible_bottom = max(bottom, camera_y, trim_bottom if trim_bottom is not None else bottom)
        visible_top = min(top, camera_y + SCREEN_HEIGHT, trim_top if trim_top is not None else top)
        visible_left = max(left, camera_x)
        visible_right = min(right, camera_x + SCREEN_WIDTH)
        if visible_right <= visible_left or visible_top <= visible_bottom:
            return
        image = self.sprites[name + ('_gray' if gray else '')]
        image.opacify(opacity)
        image.clip_draw(round(visible_left - left), round(visible_bottom - bottom),
                        round(visible_right - visible_left), round(visible_top - visible_bottom),
                        (visible_left + visible_right) / 2 - camera_x,
                        (visible_bottom + visible_top) / 2 - camera_y,
                        visible_right - visible_left, visible_top - visible_bottom)
        image.opacify(1.0)

    def draw(self, camera_x, camera_y=0):
        # Share rounded edges between chunks to avoid seams on scroll.
        camera_x, camera_y = round(camera_x), round(camera_y)
        bottom = max(0, camera_y)
        top = min(self.HEIGHT, camera_y + SCREEN_HEIGHT)
        if top <= bottom:
            return
        for index, image in enumerate(self.chunks):
            origin = index * self.CHUNK_WIDTH
            left = max(origin, camera_x)
            right = min(origin + self.CHUNK_WIDTH, camera_x + SCREEN_WIDTH)
            if right > left:
                image.clip_draw(left - origin, bottom, right - left, top - bottom,
                                (left + right) / 2 - camera_x,
                                (bottom + top) / 2 - camera_y,
                                right - left, top - bottom)
        self.draw_devices(camera_x, camera_y, include_water=self.level is None)

    def draw_devices(self, camera_x, camera_y, include_water=True):
        level = self.level
        if level is None:
            for name in ('water1', 'pool', 'leaf_0', 'leaf_1', 'leaf_2', 'leaf_3',
                         'lamp_upper', 'door', 'lamp_door', 'ropes', 'elevator', 'lamp_elevator', 'source_ceiling'):
                self.sprite(name, camera_x, camera_y)
            return
        if include_water:
            self.draw_water(camera_x, camera_y)
        for i, leaf in enumerate(level.leaves):
            self.sprite(f'leaf_{i}', camera_x, camera_y, gray=True)
        self.draw_temporary_vines(camera_x, camera_y)
        for source in level.color_sources:
            if getattr(source, 'sprite_name', None):
                self.sprite(source.sprite_name, camera_x, camera_y, gray=not source.active)
        for name, switch in (('lamp_upper', level.upper_lamp),
                             ('lamp_elevator', level.elevator_switch)):
            self.sprite(name, camera_x, camera_y, gray=not switch.active)
        if level.door_motion.platform(level.door) is not None:
            self.sprite('door', camera_x, camera_y, gray=True, offset=level.door_motion.offset,
                        trim_top=level.door.top)
        self.sprite('ropes', camera_x, camera_y, gray=not level.elevator_switch.active,
                    offset=level.elevator.offset)
        self.sprite('elevator', camera_x, camera_y, gray=not level.elevator_switch.active,
                    offset=level.elevator.offset)

    def draw_water(self, camera_x, camera_y):
        fall, pool = self.level.water
        frame = int((fall.animation_time + 1e-9) / .22) % 3 + 1 if fall.has_blue else 1
        self.sprite(f'water{frame}', camera_x, camera_y, gray=not fall.has_blue,
                    opacity=.3 if fall.has_blue else 1.0)
        self.sprite('pool', camera_x, camera_y, gray=not pool.has_blue,
                    opacity=.3 if pool.has_blue else 1.0)

    def draw_temporary_vines(self, camera_x, camera_y):
        for vine in self.level.vines:
            if vine.stem_right < camera_x or vine.left > camera_x + SCREEN_WIDTH:
                continue
            color = (75, 165, 95) if vine.active else (145, 145, 145)
            x = (vine.left + vine.stem_right) / 2 - camera_x
            bottom = max(0, vine.bottom - camera_y)
            top = min(SCREEN_HEIGHT, vine.top - camera_y)
            if top < bottom:
                continue
            pico2d.draw_rectangle(round(x - 3), round(bottom), round(x + 3), round(top),
                                  *color, filled=True)
            for leaf in vine.leaves():
                if camera_y <= leaf.top <= camera_y + SCREEN_HEIGHT:
                    pico2d.draw_rectangle(round(leaf.left - camera_x), round(leaf.bottom - camera_y),
                                          round(leaf.right - camera_x), round(leaf.top - camera_y),
                                          *color, filled=vine.active)
