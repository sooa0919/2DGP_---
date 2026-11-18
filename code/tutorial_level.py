"""Tile-only temple blockout following the annotated tutorial reference."""
from .level import Level, Platform


class TutorialLevel(Level):
    is_tutorial = True
    gimmicks_enabled = False

    def __init__(self):
        self.name = "무너진 사원"
        self.width = 4096
        self.height = 1536
        self.spawn = (192.0, 128.0)
        self.end_x = 3968
        self.end_y = 1024
        self.objects = []
        # Revised reference, rounded to the existing 32px tile grid.
        self.platforms = [Platform(*bounds) for bounds in (
            (0, 0, 768, 128), (1184, 0, 3232, 128),
            (3232, 0, 4096, 1024),
            (0, 128, 128, 1440),
            (0, 480, 672, 672),
            (1216, 416, 1568, 672),
            (0, 672, 1568, 928),
            (608, 928, 1152, 1152),
            (1344, 1184, 2592, 1408),
            (1344, 1408, 4096, 1440),
            (0, 1440, 4096, 1536),
        )]
        self.water = []
        self.thin_platforms = [
            Platform(1152, 1156, 1344, 1168, one_way=True),
        ]

    def collision_platforms(self):
        return self.platforms + self.thin_platforms

    def at_end(self, player):
        return (player.grounded and player.x >= self.end_x
                and abs(player.bottom - self.end_y) < 1)
