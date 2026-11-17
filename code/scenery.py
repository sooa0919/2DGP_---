"""Top-left atlas regions, sampled directly without changing the Swamp assets."""
from .settings import IMAGE_ROOT


SWAMP_ATLAS = (IMAGE_ROOT / "background" / "tile" /
               "forest-nature-fantasy-tileset-free" / "Fantasy Swamp Forest" /
               "Free" / "Terrain_and_Props.png")

SWAMP_PROPS = {
    "Swamp/pillar": (0, 288, 32, 64),
    "Swamp/broken_pillar": (32, 288, 32, 64),
    "Swamp/monolith": (96, 256, 176, 96),
    "Swamp/rubble": (0, 352, 48, 32),
}
