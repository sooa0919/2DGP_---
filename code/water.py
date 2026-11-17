"""Static gray solid water and animated original-color liquid water."""
import pico2d

from .settings import IMAGE_ROOT, SCREEN_WIDTH


class AnimatedWater:
    SURFACE_FRAMES = 3

    def __init__(self):
        self.gray_surface = pico2d.load_image(str(
            IMAGE_ROOT / "background" / "grayscale" / "water" / "surface.png"))
        self.blue_surface = pico2d.load_image(str(
            IMAGE_ROOT / "background" / "tile" / "GandalfHardcore Water Tiles sheet.png"))
        self.gray_surface.opacify(0.9)
        self.blue_surface.opacify(0.72)
        path = IMAGE_ROOT / 'background' / 'tile' / 'GandalfHardcore Animated Water Tiles.png'
        self.falls = pico2d.load_image(str(path))
        self.gray_falls = pico2d.load_image(str(
            IMAGE_ROOT / 'background/grayscale/water/falls.png'))

    def update(self, dt, pools):
        for pool in pools:
            if pool.has_blue:
                pool.animation_time = (pool.animation_time + dt) % 6.0

    @classmethod
    def frame_for(cls, pool):
        return int(pool.animation_time * 6 + 1e-9) % cls.SURFACE_FRAMES if pool.has_blue else 0

    def draw_surface(self, pools, camera_x):
        for pool in pools:
            if getattr(pool, 'is_waterfall', False):
                self.draw_fall(pool, camera_x)
                continue
            image = self.blue_surface if pool.has_blue else self.gray_surface
            frame = self.frame_for(pool)
            for start in range(pool.left, pool.right, 160):
                width = min(160, pool.right - start)
                if start + width >= camera_x and start <= camera_x + SCREEN_WIDTH:
                    # Skip four transparent pixels above the crest: solid water's
                    # visible top now matches the collision surface.
                    image.clip_draw(0, image.h - frame * 64 - 32, width, 28,
                                    round(start + width / 2 - camera_x), pool.bottom + 16, width, 32)

    def draw_fall(self, pool, camera_x):
        if pool.right < camera_x or pool.left > camera_x + SCREEN_WIDTH:
            return
        image = self.falls if pool.has_blue else self.gray_falls
        frame = int(pool.animation_time * 10) % 20 if pool.has_blue else 0
        # The reference sheet contains twenty 32px waterfall columns. Scroll
        # repeated middle sections downward, clipping them at both pool edges.
        offset = pool.animation_time * 180 % 128 if pool.has_blue else 0
        for x in range(pool.left, pool.right, 32):
            y = pool.bottom - offset
            while y < pool.top:
                bottom, top = max(y, pool.bottom), min(y + 128, pool.top)
                if top > bottom:
                    source_y = image.h - 192 + int((bottom - y) / 2)
                    source_h = max(1, int((top - bottom) / 2))
                    image.clip_draw(frame * 32 + 16, source_y, 16, source_h,
                                    x + 16 - camera_x, (bottom + top) / 2, 32, top - bottom)
                y += 128
        # Foam at the foot shares the falling animation and remains still gray.
        image.clip_draw(frame * 32, image.h - 224, 32, 16,
                        (pool.left + pool.right) / 2 - camera_x, pool.bottom + 8,
                        pool.right - pool.left + 32, 32)
