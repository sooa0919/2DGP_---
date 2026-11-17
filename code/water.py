"""Animated surface, falling stream and foam from the supplied water sheets."""
import pico2d

from .settings import IMAGE_ROOT, SCREEN_WIDTH


class AnimatedWater:
    SURFACE_FRAMES = 3
    FALL_FRAMES = 20

    def __init__(self):
        folder = IMAGE_ROOT / "background" / "grayscale" / "water"
        self.surface = pico2d.load_image(str(folder / "surface.png"))
        self.falls = pico2d.load_image(str(folder / "falls.png"))
        self.surface.opacify(0.72)
        self.falls.opacify(0.8)
        self.time = 0.0

    def update(self, dt):
        self.time = (self.time + dt) % 6.0

    @property
    def surface_frame(self):
        return int(self.time * 6 + 1e-9) % self.SURFACE_FRAMES

    @property
    def fall_frame(self):
        return int(self.time * 10 + 1e-9) % self.FALL_FRAMES

    @staticmethod
    def _clip(image, sx, top, sw, sh, x, y, w, h):
        image.clip_draw(sx, image.h - top - sh, sw, sh, round(x), round(y), w, h)

    def draw_falls(self, waterfalls, camera_x):
        sx = self.fall_frame * 32
        for fall in waterfalls:
            x = fall.left - camera_x + fall.width / 2
            if not -64 < x < SCREEN_WIDTH + 64:
                continue
            self._clip(self.falls, sx, 104, 32, 24,
                       x, fall.top - 12, fall.width, 24)
            top = fall.top - 24
            while top > fall.bottom:
                height = min(32, top - fall.bottom)
                self._clip(self.falls, sx, 144, 32, height,
                           x, top - height / 2, fall.width, height)
                top -= height

    def draw_surface(self, pools, waterfalls, camera_x):
        for pool in pools:
            start = pool.left
            while start < pool.right:
                width = min(160, pool.right - start)
                if start + width >= camera_x and start <= camera_x + SCREEN_WIDTH:
                    self._clip(self.surface, 0, self.surface_frame * 64, width, 32,
                               start + width / 2 - camera_x, pool.bottom + 16, width, 32)
                start += width
        for fall in waterfalls:
            x = fall.left - camera_x + fall.width / 2
            if -64 < x < SCREEN_WIDTH + 64:
                self._clip(self.falls, self.fall_frame * 32, 192, 32, 32,
                           x, fall.bottom + 4, 64, 32)
