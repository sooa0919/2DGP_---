import math

import pico2d

from .settings import (
    GROUND_HEIGHT, IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH,
    TILE_SIZE, TILE_SOURCE_SIZE, WORLD_WIDTH,
)


class Background:
    def __init__(self):
        folder = IMAGE_ROOT / "background" / "background_layer" / "background3_jungle2"
        self.layers = [
            pico2d.load_image(str(folder / f"plx-{i}.png"))
            for i in range(1, 6)
        ]
        self.scroll_rates = (0.0, 0.15, 0.3, 0.5, 0.75)
        self.tiles = pico2d.load_image(
            str(IMAGE_ROOT / "background" / "tile" / "Tileset.png")
        )

    def draw(self, camera_x):
        for layer, rate in zip(self.layers, self.scroll_rates):
            offset = round(camera_x * rate) % SCREEN_WIDTH
            for start in (-offset, SCREEN_WIDTH - offset):
                layer.draw(start + SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                           SCREEN_WIDTH, SCREEN_HEIGHT)

        # Atlas coordinates use rows from the top: moss surface, then solid soil.
        first_column = max(0, math.floor(camera_x / TILE_SIZE))
        last_column = min(math.ceil(WORLD_WIDTH / TILE_SIZE),
                          math.ceil((camera_x + SCREEN_WIDTH) / TILE_SIZE))
        for column in range(first_column, last_column):
            x = column * TILE_SIZE + TILE_SIZE // 2 - round(camera_x)
            for row in range(GROUND_HEIGHT // TILE_SIZE):
                atlas_row = 0 if row == GROUND_HEIGHT // TILE_SIZE - 1 else 2
                self.tiles.clip_draw(
                    2 * TILE_SOURCE_SIZE,
                    self.tiles.h - (atlas_row + 1) * TILE_SOURCE_SIZE,
                    TILE_SOURCE_SIZE, TILE_SOURCE_SIZE,
                    x, row * TILE_SIZE + TILE_SIZE // 2, TILE_SIZE, TILE_SIZE,
                )
