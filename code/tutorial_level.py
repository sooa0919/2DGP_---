"""Tile-only temple blockout following the annotated tutorial reference."""
from .level import Level, Platform


class TutorialLevel(Level):
    is_tutorial = True
    gimmicks_enabled = False

    def __init__(self):
        self.name = "무너진 사원"
        self.tile_size = 16
        self.width = 1792
        self.height = 672
        self.spawn = (96.0, 64.0)
        self.end_x = 1728
        self.end_y = 448
        self.objects = []
        # Reference scaled to 7/16 and snapped to 16px tiles. The starting
        # room has 144px of headroom for the player's 63px body.
        self.platforms = [Platform(*bounds) for bounds in (
            (0, 0, 336, 64), (512, 0, 1408, 64),
            (1408, 0, 1792, 448),
            (0, 64, 64, 624),
            (0, 208, 288, 288),
            (528, 176, 688, 288),
            (0, 288, 688, 400),
            (272, 400, 512, 512),
            (592, 512, 1136, 608),
            (592, 608, 1792, 624),
            (0, 624, 1792, 672),
        )]
        self.water = []
        self.thin_platforms = [
            Platform(512, 504, 592, 512, one_way=True),
        ]

    def collision_platforms(self):
        return self.platforms + self.thin_platforms

    def at_end(self, player):
        return (player.grounded and player.x >= self.end_x
                and abs(player.bottom - self.end_y) < 1)
