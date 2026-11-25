"""A subtle title layer using all frames of the supplied leaf animation."""
import json
from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT
from .display import load_smooth_image


class TitleLeaves:
    def __init__(self):
        folder = IMAGE_ROOT / 'background/leaves'
        self.sheet = load_smooth_image(str(folder / 'leaves.png'))
        self.frames = json.loads((folder / 'leaves.json').read_text(encoding='utf-8'))
        self.time = 0.0

    def update(self, dt):
        self.time = (self.time + dt) % sum(self.frames['durations'])

    @property
    def frame(self):
        remaining = self.time
        for index, duration in enumerate(self.frames['durations']):
            if remaining < duration - 1e-9:
                return index
            remaining -= duration
        return 0

    def draw(self):
        self.sheet.opacify(.65)
        width, height = self.frames['width'], self.frames['height']
        padding = self.frames['padding']
        column, row = self.frame % self.frames['columns'], self.frame // self.frames['columns']
        x = column * (width + 2 * padding) + padding
        y = self.sheet.h - row * (height + 2 * padding) - padding - height
        self.sheet.clip_draw(x, y, width, height,
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
