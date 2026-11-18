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
            (640, 0, 1152, 128),
            (1152, 0, 1472, 224), (1472, 0, 1760, 384),
            (1760, 0, 2976, 64),
            (2304, 160, 2464, 224), (2304, 224, 3104, 352),
            (2976, 0, 3104, 224),
            (3648, 0, 4096, 384),
            (0, 576, 4096, 672),
        )]
        self.water = []
        self.thin_platforms = [
            Platform(640, 116, 1632, 128, one_way=True),
            Platform(1264, 292, 1472, 304, one_way=True),
            Platform(3168, 116, 3584, 128, one_way=True),
        ]

    def collision_platforms(self):
        return self.platforms + self.thin_platforms
