class Camera:
    def __init__(self, screen_width, world_width):
        self.screen_width = screen_width
        self.world_width = world_width
        self.x = 0.0

    def follow(self, target_x):
        self.x = max(
            0.0,
            min(target_x - self.screen_width / 2,
                self.world_width - self.screen_width),
        )
