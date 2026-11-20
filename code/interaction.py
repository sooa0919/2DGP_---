"""One-shot color transfer poses and the extraction swirl behind the player."""
import pico2d

from .settings import IMAGE_ROOT


class InteractionAnimation:
    COLORS = ('blue', 'green', 'yellow')
    FRAMES = 8
    FPS = 10
    DURATION = FRAMES / FPS
    DRAW_SIZE = 92
    EFFECT_SIZE = 116
    EFFECT_FRAMES = 14

    def __init__(self):
        folder = IMAGE_ROOT / 'character/interaction'
        self.poses = {color: pico2d.load_image(str(folder / f'mouse_{color}.webp'))
                      for color in self.COLORS}
        self.effect = pico2d.load_image(str(folder / 'extraction_effects.png'))
        self.reset()

    def reset(self):
        self.color = None
        self.extracting = False
        self.time = 0.0

    @property
    def active(self):
        return self.color is not None

    def start(self, color, extracting):
        if color not in self.COLORS:
            raise ValueError(f'Unknown interaction color: {color}')
        self.color = color
        self.extracting = extracting
        self.time = 0.0

    def update(self, dt):
        if self.active:
            self.time += dt
            if self.time + 1e-9 >= self.DURATION:
                self.reset()

    def draw(self, x, bottom, facing=1):
        if not self.active:
            return
        size = self.DRAW_SIZE
        # Source feet are roughly 91% down each cell; match the standing floor.
        y = bottom + size * (0.91 - 0.5)
        if self.extracting:
            frame = min(self.EFFECT_FRAMES - 1,
                        int(self.time / self.DURATION * self.EFFECT_FRAMES))
            row = self.COLORS.index(self.color)
            self.effect.clip_draw(frame * 64, self.effect.h - (row + 1) * 64,
                                  64, 64, round(x), round(bottom + 34),
                                  self.EFFECT_SIZE, self.EFFECT_SIZE)
        image = self.poses[self.color]
        frame = min(self.FRAMES - 1, int(self.time * self.FPS))
        row, column = divmod(frame + (0 if self.extracting else 8), 4)
        # 1254px sheets have fractional cell boundaries: round both edges.
        left, right = round(column * image.w / 4), round((column + 1) * image.w / 4)
        top, end = round(row * image.h / 4), round((row + 1) * image.h / 4)
        # Like idle poses, the supplied interaction sprites face left.
        image.clip_composite_draw(left, image.h - end, right - left, end - top,
                                  0, 'h' if facing > 0 else '',
                                  round(x), round(y), size, size)
