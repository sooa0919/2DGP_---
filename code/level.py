"""Forest terrain and water that regains its liquid nature with blue."""
from dataclasses import dataclass

from .settings import TILE_SIZE
from .scenery import PROP_BOUNDS


@dataclass(frozen=True)
class Platform:
    left: int
    bottom: int
    right: int
    top: int
    one_way: bool = False


@dataclass
class Water:
    left: int
    bottom: int
    right: int
    top: int
    has_blue: bool = False
    animation_time: float = 0.0
    is_waterfall: bool = False

    @property
    def solid(self):
        return not self.has_blue

    @property
    def color_owner(self):
        return self


class ConnectedWater(Water):
    """Another shape of the same water body, sharing one color and clock."""
    def __init__(self, left, bottom, right, top, source):
        self.left, self.bottom, self.right, self.top = left, bottom, right, top
        self.source = source
        self.is_waterfall = False

    @property
    def color_owner(self):
        return self.source.color_owner

    @property
    def has_blue(self):
        return self.source.has_blue

    @has_blue.setter
    def has_blue(self, value):
        self.source.has_blue = value

    @property
    def animation_time(self):
        return self.source.animation_time

    @animation_time.setter
    def animation_time(self, value):
        self.source.animation_time = value


class Level:
    starting_blue = True

    def __init__(self):
        self.name = "SILENT GROVE"
        # Broad lowlands, smaller rises, a wooded ridge, then an open river.
        route = [(0, 10, 3), (10, 18, 2), (18, 24, 3), (24, 30, 4),
                 (30, 36, 5), (36, 43, 6), (43, 49, 5), (49, 55, 4),
                 (55, 60, 3), (60, 66, 4), (66, 70, 5), (70, 76, 7),
                 (76, 90, 3), (90, 96, 4), (96, 102, 5), (102, 108, 4),
                 (108, 114, 3), (114, 126, 2), (126, 132, 3),
                 (132, 138, 4), (138, 145, 3), (145, 160, 3)]
        self.water = [Water(76 * 32, 2 * 32, 89 * 32, 3 * 32),
                      Water(115 * 32, 32, 123 * 32, 2 * 32)]
        self.platforms = []
        for a, b, h in route:
            cuts = {a * 32, b * 32}
            for pool in self.water:
                if a * 32 < pool.left < b * 32:
                    cuts.add(pool.left)
                if a * 32 < pool.right < b * 32:
                    cuts.add(pool.right)
            edges = sorted(cuts)
            for left, right in zip(edges, edges[1:]):
                pool = next((w for w in self.water if w.left <= left and right <= w.right), None)
                self.platforms.append(Platform(left, 0, right, pool.bottom if pool else h * 32))
        self.width = 160 * TILE_SIZE
        self.spawn = (200.0, 96.0)
        self.end_x = self.width - 160
        self.objects = []
        kinds = ("Willows/1", "Trees/1", "Rock/moss", "Trees/2",
                 "Ridges/1", "Willows/2", "Rock/low", "Trees/3")
        # Keep the restored upper cliff clear and preserve existing prop groups.
        dry = [p for p in self.platforms if p.right - p.left >= 96 and p.left != 70 * 32
               and not any(w.left <= p.left and p.right <= w.right for w in self.water)]
        for i, platform in enumerate(dry):
            # Main silhouettes are clustered with shrubs, grass and small rocks.
            kind = kinds[i % len(kinds)]
            self._place(kind, platform, 0.47 if i % 2 else 0.57,
                        2.0 if "Rock" not in kind else 1.7)
            if platform.right - platform.left >= 160:
                self._place("Bushes/3" if i % 2 else "Rock/low", platform, 0.14, 1.4)
                self._place("Grass/3", platform, 0.86, 1.8)
        self._place("Willows/1", dry[-1], 0.74, 2.3)

    def _place(self, kind, platform, fraction, preferred_scale):
        left, _, right, _ = PROP_BOUNDS[kind]
        scale = min(preferred_scale, (platform.right - platform.left - 24) / (right - left))
        half = (right - left) * scale / 2
        x = max(platform.left + half + 12,
                min(platform.left + (platform.right - platform.left) * fraction,
                    platform.right - half - 12))
        self.objects.append((kind, x, platform.top, scale))

    def at_end(self, player):
        return player.grounded and player.x >= self.end_x

    def collision_platforms(self):
        return self.platforms + [Platform(w.left, w.bottom, w.right, w.top)
                                 for w in self.water if w.solid]

    def reset_water(self):
        for pool in self.water:
            pool.has_blue = False
            pool.animation_time = 0.0

    def reset(self):
        self.reset_water()
        for source in getattr(self, 'color_sources', []):
            source.reset()

    def terrain_tiles(self):
        size = getattr(self, 'tile_size', TILE_SIZE)
        cells = {(x, y) for p in self.platforms
                 for x in range(p.left // size, p.right // size)
                 for y in range(p.bottom // size, p.top // size)}
        tiles = {}
        for x, y in cells:
            left, right = (x - 1, y) in cells, (x + 1, y) in cells
            if (x, y + 1) not in cells:
                tile = 1 if not left else (3 if not right else 2)
            else:
                tile = 11 if not left else (13 if not right else 12)
            tiles[x, y] = tile
        return tiles
