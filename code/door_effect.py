"""A short door-opening impact: decaying shake, stone chips, and dust."""
from dataclasses import dataclass
import math
import random

import pico2d

from .settings import IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT


@dataclass(frozen=True)
class Debris:
    x: float
    y: float
    vx: float
    vy: float
    lifetime: float
    size: float
    dust: bool
    spin: float

    def position(self, age):
        gravity = 35 if self.dust else 650
        return self.x + self.vx * age, self.y + self.vy * age - gravity * age * age / 2


class DoorOpeningEffect:
    SHAKE_DURATION = .38
    SHAKE_STRENGTH = 7.0

    def __init__(self):
        self.reset()

    def reset(self):
        self.was_open = False
        self.age = 0.0
        self.particles = []
        self.openings = 0

    def update(self, dt, door, is_open):
        if is_open and not self.was_open:
            self._burst(door)
        self.was_open = is_open
        self.age += max(0, dt)
        self.particles = [p for p in self.particles if self.age < p.lifetime]

    def _burst(self, door):
        self.openings += 1
        rng = random.Random(715 + self.openings)
        self.age = 0.0
        self.particles = []
        for dust, count in ((False, 30), (True, 18)):
            for i in range(count):
                side = -1 if i % 2 else 1
                x = door.left if side < 0 else door.right
                y = rng.uniform(door.bottom + 8, door.top - 6)
                self.particles.append(Debris(
                    x, y, side * rng.uniform(25, 90 if dust else 155),
                    rng.uniform(12, 48) if dust else rng.uniform(30, 180),
                    rng.uniform(.65, 1.15) if dust else rng.uniform(.45, .85),
                    rng.uniform(22, 42) if dust else rng.uniform(4, 9),
                    dust, rng.uniform(-9, 9)))

    @property
    def shake_offset(self):
        if not self.openings or self.age >= self.SHAKE_DURATION:
            return 0.0, 0.0
        strength = self.SHAKE_STRENGTH * (1 - self.age / self.SHAKE_DURATION) ** 2
        return (strength * math.sin(self.age * 91 + .4),
                strength * .65 * math.sin(self.age * 123 + 1.2))


class DoorEffectRenderer:
    def __init__(self):
        folder = IMAGE_ROOT / 'effects'
        self.dust = pico2d.load_image(str(folder / 'door_dust.png'))
        self.chip = pico2d.load_image(str(folder / 'door_chip.png'))

    def draw(self, effect, camera_x, camera_y):
        # Soft puffs behind the sharper, rotating rock fragments.
        for dust in (True, False):
            image = self.dust if dust else self.chip
            for p in effect.particles:
                if p.dust != dust:
                    continue
                progress = effect.age / p.lifetime
                x, y = p.position(effect.age)
                x, y = x - camera_x, y - camera_y
                size = p.size * (1 + progress * 1.8) if dust else p.size
                if not (-size < x < SCREEN_WIDTH + size and -size < y < SCREEN_HEIGHT + size):
                    continue
                image.opacify(.38 * (1 - progress) ** 1.5 if dust else min(1, (1 - progress) * 4))
                if dust:
                    image.draw(x, y, size * 1.25, size)
                else:
                    image.clip_composite_draw(0, 0, image.w, image.h, p.spin * effect.age,
                                              '', x, y, size, size * .8)
            image.opacify(1)
