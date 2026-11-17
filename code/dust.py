"""Short, world-anchored smoke puffs behind a running character."""
from dataclasses import dataclass

import pico2d

from .settings import IMAGE_ROOT


@dataclass
class Puff:
    x: float
    ground: float
    facing: int
    age: float = 0.0


class RunDust:
    FRAME_SIZE = 64
    FRAME_COUNT = 6
    FPS = 18
    INTERVAL = 0.12
    DRAW_SIZE = 64

    def __init__(self):
        self.image = pico2d.load_image(str(
            IMAGE_ROOT / "character" / "effefct" / "Smoke FX Lite Zip 5.25.23" /
            "SmokeFX Lite SpriteSheet 2A-2.png"))
        self.puffs = []
        self.timer = 0.0

    def clear(self):
        self.puffs.clear()
        self.timer = 0.0

    def update(self, dt, player, old_x):
        for puff in self.puffs:
            puff.age += dt
        self.puffs = [p for p in self.puffs if p.age < self.FRAME_COUNT / self.FPS]
        if not player.grounded or player.in_water or abs(player.x - old_x) < 0.01:
            self.timer = 0.0
            return
        self.timer -= dt
        if self.timer <= 0:
            self.puffs.append(Puff(player.x - player.facing * 22,
                                   player.y - player.DRAW_SIZE / 2, player.facing))
            self.timer = self.INTERVAL

    def draw(self, camera_x):
        for puff in self.puffs:
            frame = min(int(puff.age * self.FPS), self.FRAME_COUNT - 1)
            # This sheet drifts left. Flip for a character running to the left.
            # The opaque pixels' lower edge is near row 49 (from the top).
            self.image.clip_composite_draw(
                frame * self.FRAME_SIZE, 0, self.FRAME_SIZE, self.FRAME_SIZE,
                0, "h" if puff.facing < 0 else "",
                round(puff.x - camera_x), round(puff.ground + 17),
                self.DRAW_SIZE, self.DRAW_SIZE)
