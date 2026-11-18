"""Tile-only temple blockout following the annotated tutorial reference."""
from .level import Level, Platform


class TutorialLevel(Level):
    is_tutorial = True
    gimmicks_enabled = False

    def __init__(self):
        self.name = "무너진 사원"
        self.width = 4096
        self.spawn = (160.0, 128.0)
        self.end_x = 3968
        self.objects = []
        # Revised reference, rounded to the existing 32px tile grid.
        self.platforms = [Platform(*bounds) for bounds in (
            (0, 0, 640, 128),
            (1152, 0, 1472, 224), (1472, 0, 1760, 384),
            (1760, 0, 2976, 64),
            (2304, 160, 2464, 256), (2464, 224, 2976, 256),
            (2976, 0, 3008, 352), (3104, 0, 3136, 352),
            (3168, 96, 3584, 128),
            (3648, 0, 4096, 384),
            (0, 576, 4096, 672),
        )]
        self.water = []
        self.thin_platforms = [
            Platform(640, 116, 1632, 128, one_way=True),
            Platform(1168, 372, 1472, 384, one_way=True),
            Platform(2304, 340, 3104, 352, one_way=True),
        ]

    def collision_platforms(self):
        return self.platforms + self.thin_platforms
