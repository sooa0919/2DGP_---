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

    def update(self, dt, pools):
        for pool in pools:
            if pool.has_blue:
                pool.animation_time = (pool.animation_time + dt) % 6.0

    @classmethod
    def frame_for(cls, pool):
        return int(pool.animation_time * 6 + 1e-9) % cls.SURFACE_FRAMES if pool.has_blue else 0

    def draw_surface(self, pools, camera_x):
        for pool in pools:
            image = self.blue_surface if pool.has_blue else self.gray_surface
            frame = self.frame_for(pool)
            for start in range(pool.left, pool.right, 160):
                width = min(160, pool.right - start)
                if start + width >= camera_x and start <= camera_x + SCREEN_WIDTH:
                    # Skip four transparent pixels above the crest: solid water's
                    # visible top now matches the collision surface.
                    image.clip_draw(0, image.h - frame * 64 - 32, width, 28,
                                    round(start + width / 2 - camera_x), pool.bottom + 16, width, 32)
