"""State-based vines, a light switch and independently falling water blocks."""
from dataclasses import dataclass

from .level import Platform


@dataclass
class Vine:
    left: float
    bottom: float
    right: float
    top: float
    unlock_stage: int
    name: str
    active: bool = False
    animation_time: float = 0.0
    required_color: str = 'green'

    @property
    def stored_color(self):
        return self.required_color if self.active else None

    def reset(self):
        self.active = False
        self.animation_time = 0.0

    def leaves(self):
        heights = list(range(int(self.bottom) + 80, int(self.top), 80)) + [int(self.top)]
        return [Platform(self.left, y - 8, self.right, y, one_way=True) for y in heights]


@dataclass
class Lamp:
    left: float
    bottom: float
    right: float
    top: float
    unlock_stage: int = 7
    name: str = '출구 등불'
    active: bool = False
    animation_time: float = 0.0
    required_color: str = 'yellow'

    @property
    def stored_color(self):
        return 'yellow' if self.active else None

    def reset(self):
        self.active = False
        self.animation_time = 0.0


@dataclass
class FallingWater:
    left: float
    bottom: float
    right: float
    top: float
    initial_top: float
    has_blue: bool = True
    animation_time: float = 0.0
    unlock_stage: int = 6
    required_color: str = 'blue'
    name: str = '떨어지는 물'
    speed: float = 100.0

    @property
    def stored_color(self):
        return 'blue' if self.has_blue else None

    @property
    def solid(self):
        return not self.has_blue

    def reset(self):
        self.has_blue = True
        self.animation_time = 0.0
        self.top = self.initial_top
        self.bottom = self.top - 80

    def update(self, dt):
        if not self.has_blue:
            return
        self.top = 96 + (self.top - 96 - self.speed * dt) % 880
        self.bottom = self.top - 80

    def platform(self):
        return Platform(self.left, self.bottom, self.right, self.top, one_way=True)
