from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOT = ROOT / "image"
FONT_PATH = ROOT / "fonts" / "KkakdugiDrafting-v1.003" / "KkakdugiDrafting-Regular.ttf"
FONT_BOLD_PATH = FONT_PATH.with_name("KkakdugiDrafting-Bold.ttf")
SCREEN_WIDTH = 1152
SCREEN_HEIGHT = 648
WORLD_WIDTH = SCREEN_WIDTH * 10
TILE_SOURCE_SIZE = 16
TILE_SIZE = 32
GROUND_HEIGHT = TILE_SIZE * 3
