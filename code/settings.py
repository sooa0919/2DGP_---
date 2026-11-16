from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOT = ROOT / "image"
SCREEN_WIDTH = 1152
SCREEN_HEIGHT = 648
WORLD_WIDTH = SCREEN_WIDTH * 10
TILE_SOURCE_SIZE = 16
TILE_SIZE = 32
GROUND_HEIGHT = TILE_SIZE * 3
