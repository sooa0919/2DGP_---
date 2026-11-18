from .settings import SCREEN_HEIGHT


class Camera:
    def __init__(self, screen_width, world_width, world_height=SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.world_width = world_width
        self.x = 0.0
        self.world_height = world_height
        self.y = 0.0

    def follow(self, target_x, target_y=None):
        self.x = max(
            0.0,
            min(target_x - self.screen_width / 2,
                self.world_width - self.screen_width),
        )
        if target_y is not None:
            self.y = max(0.0, min(target_y - SCREEN_HEIGHT / 2,
                                  self.world_height - SCREEN_HEIGHT))
