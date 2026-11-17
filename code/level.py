"""Map geometry shared by drawing, collisions and exits (world coordinates)."""
from dataclasses import dataclass

from .settings import TILE_SIZE
from .scenery import PROP_BOUNDS


@dataclass(frozen=True)
class Platform:
    left: int
    bottom: int
    right: int
    top: int


@dataclass(frozen=True)
class Water:
    left: int
    bottom: int
    right: int
    top: int


class Level:
    def __init__(self, index=0):
        self.index = index % 2
        self.name = ("SILENT GROVE", "FORGOTTEN TEMPLE")[self.index]
        # Column ranges, surface height in tiles. Missing columns are jump gaps.
        routes = (
            [(0, 16, 3), (16, 23, 5), (23, 30, 7), (30, 38, 5),
             (41, 50, 4), (50, 57, 6), (57, 64, 8), (64, 72, 6),
             (75, 84, 4), (84, 91, 6), (91, 99, 5), (99, 120, 3)],
            [(0, 14, 3), (14, 21, 5), (21, 28, 7), (28, 36, 9),
             (39, 47, 8), (47, 54, 6), (54, 62, 4), (65, 73, 4),
             (73, 80, 6), (80, 87, 8), (87, 95, 6), (95, 120, 3)],
        )
        self.platforms = []
        self.water = []
        for i, (a, b, h) in enumerate(routes[self.index]):
            if i in (4, 8, 11):
                left, right = (a + 2) * 32, min(b - 2, a + 9) * 32
                self.platforms += [Platform(a * 32, 0, left, h * 32),
                                   Platform(left, 0, right, (h - 1) * 32),
                                   Platform(right, 0, b * 32, h * 32)]
                self.water.append(Water(left, (h - 1) * 32, right, h * 32))
            else:
                self.platforms.append(Platform(a * 32, 0, b * 32, h * 32))
        self.width = 120 * TILE_SIZE
        self.spawn = (200.0, 96.0)
        self.exit_x = self.width - 160
        self.exit_y = 96
        # Decorations are anchored to the actual surface, away from jump lips.
        self.objects = []
        if self.index == 0:
            kinds = ("Willows/1", "Rock/low", "Trees/2", "Ridges/1",
                     "Rock/moss", "Willows/2", "Rock/low", "Trees/3")
        else:
            kinds = ("Stones/2", "Rock/moss", "Ruins/statue",
                     "Stones/3", "Ridges/1", "Stones/1")
        # Keep the whole visible sprite above one continuous, dry surface.
        dry = [p for p in self.platforms if p.right - p.left >= 96
               and not any(w.left <= p.left and p.right <= w.right for w in self.water)]
        for i, platform in enumerate(dry):
            kind = kinds[i % len(kinds)]
            left, _, right, _ = PROP_BOUNDS[kind]
            scale = min(2.0 if self.index == 0 else 2.3,
                        (platform.right - platform.left - 32) / (right - left))
            self.objects.append((kind, (platform.left + platform.right) / 2,
                                 platform.top, scale))
        self.objects += [("Pointers/1", self.exit_x - 120, 96, 2.5)]

    def can_exit(self, player):
        return (player.grounded and abs(player.x - self.exit_x) <= 80
                and abs(player.y - player.DRAW_SIZE / 2 - self.exit_y) < 3)

    def terrain_tiles(self):
        cells = {(x, y) for p in self.platforms
                 for x in range(p.left // 32, p.right // 32)
                 for y in range(p.bottom // 32, p.top // 32)}
        tiles = {}
        for x, y in cells:
            left, right = (x - 1, y) in cells, (x + 1, y) in cells
            if (x, y + 1) not in cells:
                tile = 1 if not left else (3 if not right else 2)
            else:
                tile = 11 if not left else (13 if not right else 12)
            tiles[x, y] = tile
        return tiles
