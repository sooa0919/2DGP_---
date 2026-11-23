"""Forest blockout following previews/ex.png's left-to-right puzzle route."""
from .level import Level, Platform, Water, ConnectedWater
from .diamond import Diamond
from .gimmicks import Vine, Lamp, FallingWater, FallingWaterGroup


class TutorialLevel(Level):
    is_tutorial = True
    gimmicks_enabled = True
    show_color_messages = False
    starting_blue = False

    def __init__(self):
        self.name = '색의 숲'
        self.width, self.height = 4096, 1008
        self.spawn = (80.0, 96.0)
        self.end_x, self.end_y = 4032, 96
        self.objects = []
        # The diagram's black masses. The first roof prevents bypassing the gate.
        self.platforms = [Platform(*p) for p in (
            (0, 0, 320, 96), (320, 0, 656, 64), (656, 0, 4096, 96),
            (0, 816, 320, 1008),
            (960, 96, 1184, 480), (1344, 96, 1464, 224),
            (1584, 96, 1704, 224), (1824, 96, 2008, 304),
            (3616, 592, 3808, 600),
        )]
        self.thin_platforms = [Platform(2008, 216, 2176, 224, one_way=True)]
        gate = Water(320, 96, 384, 816, is_waterfall=True)
        self.water = [gate, ConnectedWater(384, 64, 656, 96, gate)]
        self.color_sources = [Diamond(164, 132)]
        self.vines = [Vine(752, 96, 864, 480, 1, '첫 덩굴'),
                      Vine(2240, 96, 2336, 224, 3, '덩굴 1'),
                      Vine(2576, 96, 2672, 304, 4, '덩굴 2'),
                      Vine(2944, 96, 3056, 480, 5, '덩굴 3')]
        for vine, right in zip(self.vines[1:], (2528, 2880, 3248)):
            vine.cap_right = right
        group = FallingWaterGroup()
        self.droplets = [FallingWater(3328, top - 80, 3552, top, top, group)
                         for top in (932, 712, 492, 272)]
        self.lamp = Lamp(3712, 600, 3760, 672)
        self.door = Platform(3936, 96, 3984, 704)
        self.reset()

    @property
    def devices(self):
        return self.vines + self.droplets + [self.lamp]

    def collision_platforms(self):
        result = super().collision_platforms() + self.thin_platforms
        for vine in self.vines:
            if vine.active:
                result += vine.leaves()
        result += [drop.platform() for drop in self.droplets if drop.solid]
        if not self.lamp.active:
            result.append(self.door)
        return result

    def reset(self):
        super().reset()
        for item in self.devices:
            item.reset()
        self.progress = 0
        self.gate_opened = False
        self.complete = False
        self.vine_attempt_started = False

    def update(self, dt, player):
        for source in self.color_sources:
            source.update(dt)
        for drop in self.droplets:
            drop.update(dt)
        self.gate_opened |= self.water[0].has_blue
        if self.progress == 0 and self.gate_opened and player.x >= 680:
            self.progress = 1
        milestones = ((1, 960, 1184, 480, 2),
                      (3, 2240, 2528, 224, 4),
                      (4, 2576, 2880, 304, 5),
                      (5, 2944, 3248, 480, 6))
        for stage, left, right, floor, next_stage in milestones:
            if (self.progress == stage and player.grounded and left <= player.x <= right
                    and abs(player.bottom - floor) < 1):
                self.progress = next_stage
        if self.progress == 2 and player.x >= 2176 and player.bottom < 128:
            self.progress = 3
        if self.progress == 6 and any(
                d.solid and d.left <= player.x <= d.right and player.grounded
                and abs(player.bottom - d.top) < 1 for d in self.droplets):
            self.progress = 7
        if 3 <= self.progress <= 6 and 2200 <= player.x < 3616:
            self.vine_attempt_started |= player.bottom > 144
            if self.vine_attempt_started and player.grounded and player.bottom <= 97:
                player.enter_level(self)
                return
        self.complete = self.complete or self.at_end(player)

    def at_end(self, player):
        return (self.lamp.active and self.progress >= 7 and player.grounded
                and player.x >= self.end_x and abs(player.bottom - self.end_y) < 1)
