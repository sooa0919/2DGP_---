"""Color-controlled illustrated platforms and their moving elevator."""
from dataclasses import dataclass

from .level import Platform, Water
from .stage_geometry import collision_rectangles


@dataclass
class StageDevice:
    left: float
    bottom: float
    right: float
    top: float
    name: str
    required_color: str = 'yellow'
    active: bool = False
    unlock_stage: int = 0

    @property
    def stored_color(self):
        return self.required_color if self.active else None

    def reset(self):
        self.active = False


class LeafPlatform(StageDevice):
    def platform(self):
        # The walking edge is the top of the horizontal vine, below a few
        # decorative shoots at the sprite's top.
        return Platform(self.left + 8, self.top - 24, self.right - 8,
                        self.top - 16, one_way=True)


class StageColorSource(StageDevice):
    def __init__(self, left, bottom, right, top, name, sprite_name, color):
        super().__init__(left, bottom, right, top, name, required_color=color, active=True)
        self.sprite_name = sprite_name
        self.animation_time = 0.0

    def reset(self):
        self.active = True
        self.animation_time = 0.0

    def update(self, dt):
        self.animation_time += dt


class ShapedWater(Water):
    def __init__(self, polygon, is_waterfall=False):
        super().__init__(min(x for x, y in polygon), min(y for x, y in polygon),
                         max(x for x, y in polygon), max(y for x, y in polygon),
                         is_waterfall=is_waterfall)
        self.polygon = polygon
        self.frozen_platforms = collision_rectangles(polygons=(polygon,))

    def contains_point(self, x, y):
        inside = False
        for (x1, y1), (x2, y2) in zip(self.polygon, self.polygon[1:] + self.polygon[:1]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        return inside

    def overlaps(self, left, bottom, right, top):
        return any(p.right > left and p.left < right and p.top > bottom and p.bottom < top
                   for p in self.frozen_platforms)


class RisingDoor:
    PAN_DURATION = .55
    OPEN_DURATION = 1.7
    HOLD_DURATION = .25
    RETURN_DURATION = .6
    CLOSE_DURATION = 1.1

    def __init__(self):
        self.reset()

    def reset(self):
        self.offset = 0.0
        self.was_active = False
        self.sequence_age = None
        self.start_offset = 0.0

    @staticmethod
    def ease(value):
        value = max(0, min(1, value))
        return value * value * (3 - 2 * value)

    @property
    def opening_started(self):
        return self.sequence_age is not None and self.sequence_age >= self.PAN_DURATION

    @property
    def camera_weight(self):
        if self.sequence_age is None:
            return 0.0
        if self.sequence_age < self.PAN_DURATION:
            return self.ease(self.sequence_age / self.PAN_DURATION)
        return_start = self.PAN_DURATION + self.OPEN_DURATION + self.HOLD_DURATION
        return 1 - self.ease((self.sequence_age - return_start) / self.RETURN_DURATION)

    def update(self, dt, door, active, player=None):
        dt = max(0, dt)
        travel = door.top - door.bottom + 24
        if active:
            if not self.was_active:
                self.sequence_age = 0.0
                self.start_offset = self.offset
            self.sequence_age += dt
            progress = self.ease((self.sequence_age - self.PAN_DURATION) / self.OPEN_DURATION)
            self.offset = self.start_offset + (travel - self.start_offset) * progress
        else:
            self.sequence_age = None
            offset = max(0, self.offset - travel * dt / self.CLOSE_DURATION)
            # Stop a descending gate above a character standing in the opening.
            if (player is not None and player.right > door.left and player.left < door.right
                    and player.bottom < door.top and player.top > door.bottom + offset):
                offset = min(self.offset, max(offset, player.top - door.bottom + .5))
            self.offset = offset
        self.was_active = active

    def platform(self, door):
        bottom = door.bottom + self.offset
        if bottom >= door.top:
            return None
        return Platform(door.left, bottom, door.right, door.top)


class Elevator:
    SPEED = 130.0

    def __init__(self, switch):
        self.switch = switch
        self.left, self.right = 3414, 3642
        self.low, self.high = 172.0, 827.0
        self.reset()

    def reset(self):
        self.top = self.low

    @property
    def offset(self):
        return self.top - self.low

    def platform(self):
        return Platform(self.left, self.top - 12, self.right, self.top, one_way=True)

    def update(self, dt, player, solids):
        target = self.high if self.switch.active else self.low
        movement = max(-self.SPEED * dt, min(self.SPEED * dt, target - self.top))
        if not movement:
            return
        old = self.platform()
        overlaps = player.x + player.FOOT_HALF_WIDTH > self.left and player.x - player.FOOT_HALF_WIDTH < self.right
        ignored = old in player.ignored_platforms
        rider = overlaps and not ignored and player.grounded and abs(player.bottom - self.top) <= 2
        pickup = (overlaps and not ignored and movement > 0 and
                  self.top <= player.bottom <= self.top + movement and player.velocity_y <= 0)
        if rider or pickup:
            # Keep an edge-standing rider inside the shaft before passing the
            # underside of the destination ledge.
            player.x = max(self.left + player.HALF_WIDTH,
                           min(player.x, self.right - player.HALF_WIDTH))
            # Do not force a rider through an overhanging cliff.
            if movement > 0:
                for p in solids:
                    if (not p.one_way and p.right > player.left and p.left < player.right
                            and p.bottom >= player.top - .01):
                        movement = min(movement, max(0, p.bottom - player.top))
            self.top += movement
            player.y = self.top + player.FOOT_OFFSET
            player.velocity_y = 0.0
            player.grounded = True
        else:
            self.top += movement
