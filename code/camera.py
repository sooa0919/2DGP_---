import math

from .settings import SCREEN_HEIGHT


class Camera:
    RESPONSE = 9.0
    def __init__(self, screen_width, world_width, world_height=SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.world_width = world_width
        self.x = 0.0
        self.world_height = world_height
        self.y = 0.0

    def target(self, target_x, target_y=None):
        x = max(0.0, min(target_x - self.screen_width / 2,
                         self.world_width - self.screen_width))
        y = self.y
        if target_y is not None:
            y = max(0.0, min(target_y - SCREEN_HEIGHT / 2,
                             self.world_height - SCREEN_HEIGHT))
        return x, y

    def snap_to(self, target_x, target_y=None):
        self.x, self.y = self.target(target_x, target_y)

    def follow(self, target_x, target_y=None, dt=1 / 60):
        x, y = self.target(target_x, target_y)
        if abs(x - self.x) > self.screen_width or abs(y - self.y) > SCREEN_HEIGHT:
            self.x, self.y = x, y
            return
        # Catch up gently, with the same response at different frame rates.
        alpha = -math.expm1(-self.RESPONSE * max(0.0, dt))
        self.x += (x - self.x) * alpha
        self.y += (y - self.y) * alpha
