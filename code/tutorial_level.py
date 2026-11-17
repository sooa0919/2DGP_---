"""Tile-only temple blockout following the annotated tutorial reference."""
from .level import Level, Platform, Water, ConnectedWater


class TutorialLevel(Level):
    is_tutorial = True

    def __init__(self):
        self.name = "무너진 사원"
        self.width = 4096
        self.spawn = (160.0, 160.0)
        self.end_x = 3968
        self.objects = []
        # The plant and light puzzle rooms retain their space for later objects.
        self.platforms = [Platform(*bounds) for bounds in (
            (0, 0, 672, 160), (672, 0, 960, 96), (960, 0, 1216, 160),
            (1216, 0, 1504, 96), (1504, 0, 1728, 160),
            (1728, 0, 2304, 64),
            (2304, 0, 2400, 128), (2400, 0, 2496, 224),
            (2496, 0, 2720, 320),
            (2496, 192, 2976, 224),
            (2880, 224, 2976, 288),
            (2720, 0, 3072, 64),
            (2976, 320, 3072, 352),
            (3072, 0, 3168, 128), (3168, 0, 3296, 224),
            (3360, 0, 3488, 224), (3488, 0, 3584, 320),
            (3584, 0, 3680, 416), (3680, 0, 4096, 448),
        )]
        fall = Water(736, 160, 864, 648, is_waterfall=True)
        self.water = [fall, Water(1216, 96, 1504, 160),
                      ConnectedWater(672, 96, 960, 160, fall)]
        self.zones = ((0, "이동과 점프"), (600, "파랑 · 물의 상태"),
                      (1728, "초록 · 생장"), (3072, "노랑 · 빛"), (3680, "출구"))

    def collision_platforms(self):
        # A frozen waterfall is a wall. Its flowing state opens the passage.
        return super().collision_platforms()
