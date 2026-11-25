"""Stage one: collision and devices placed on the supplied illustration."""
from .level import Level, Platform
from .diamond import Diamond
from .stage_geometry import terrain_collision_rectangles
from .stage_devices import StageDevice, StageColorSource, LeafPlatform, ShapedWater, Elevator, RisingDoor
from .gimmicks import Vine
from .door_effect import DoorOpeningEffect


class IllustratedLevel(Level):
    is_tutorial = True
    gimmicks_enabled = True
    show_color_messages = False
    starting_blue = False
    jump_speed = 600.0
    step_height = 10

    def __init__(self):
        self.name = '색의 숲'
        self.width, self.height = 4096, 1008
        self.spawn = (80.0, 78.0)
        self.end_x, self.end_y = 4020, 827
        self.objects = []
        self.platforms = terrain_collision_rectangles()
        self.thin_platforms = []
        self.color_sources = [Diamond(164, 112),
            StageColorSource(3130, 315, 3220, 390, '천장 노랑 원천', 'lamp_door', 'yellow'),
            StageColorSource(3850, 398, 3935, 493, '천장 파랑 원천', 'source_ceiling', 'blue')]
        fall = ((160, 749), (190, 734), (225, 721), (267, 699), (302, 665),
                (325, 599), (341, 478), (359, 300), (381, 120), (408, 72),
                (470, 73), (538, 69), (523, 41), (475, 10), (405, 0),
                (350, 11), (319, 46), (326, 85), (329, 205), (319, 377),
                (306, 522), (291, 623), (273, 665), (232, 694), (192, 719))
        pool = ((2490, 66), (2535, 68), (2590, 66), (2665, 69),
                (2655, 47), (2615, 35), (2570, 34), (2520, 43))
        self.water = [ShapedWater(fall, True), ShapedWater(pool)]
        self.leaves = [LeafPlatform(*bounds, f'덩굴 발판 {i + 1}', required_color='green')
                       for i, bounds in enumerate(((1510, 143, 1705, 218),
                            (1830, 143, 2030, 218), (2135, 143, 2330, 218),
                            (2395, 553, 2590, 633)))]
        self.thin_platforms = [leaf.platform() for leaf in self.leaves]
        # Temporary green climbing devices bridge the tall sections while
        # retaining the original jump physics. Their art is deliberately simple.
        self.vines = [Vine(550, 75, 630, 438, 0, '임시 덩굴 1'),
                      Vine(2320, 73, 2410, 617, 0, '임시 덩굴 2')]
        self.droplets = []
        self.upper_lamp = StageDevice(3010, 598, 3120, 718, '윗가지 등불')
        self.door_switch = self.upper_lamp
        self.elevator_switch = StageDevice(3645, 63, 3735, 173, '엘리베이터 장치')
        self.lamp = self.elevator_switch
        self.door = Platform(2882, 75, 2928, 486)
        self.door_motion = RisingDoor()
        self.elevator = Elevator(self.elevator_switch)
        self.door_effect = DoorOpeningEffect()
        self._bins = {}
        for p in self.platforms:
            for col in range(int(p.left) // 128, int(p.right) // 128 + 1):
                self._bins.setdefault(col, []).append(p)
        self.reset()

    @property
    def devices(self):
        return self.vines + [self.upper_lamp, self.elevator_switch]

    def dynamic_platforms(self):
        result = [self.elevator.platform()]
        result += [leaf for vine in self.vines if vine.active for leaf in vine.leaves()]
        for water in self.water:
            if water.solid:
                result += water.frozen_platforms
        door = self.door_motion.platform(self.door)
        if door is not None:
            result.append(door)
        return result

    def collision_platforms(self):
        return self.platforms + self.thin_platforms + self.dynamic_platforms()

    def collision_platforms_near(self, left, right):
        result = {}
        for col in range(int(left) // 128, int(right) // 128 + 1):
            for p in self._bins.get(col, ()):
                result[p] = p
        return list(result.values()) + [p for p in self.thin_platforms + self.dynamic_platforms()
                                       if p.right >= left and p.left <= right]

    def reset(self):
        super().reset()
        for device in self.devices:
            device.reset()
        self.elevator.reset()
        self.door_motion.reset()
        self.door_effect.reset()
        self.progress = 99  # No invisible checkpoints from the former map.
        self.complete = False

    def update(self, dt, player):
        for source in self.color_sources:
            source.update(dt)
        for water in self.water:
            if water.has_blue:
                water.animation_time = (water.animation_time + dt) % .66
        self.elevator.update(dt, player, self.collision_platforms_near(player.left, player.right))
        self.door_motion.update(dt, self.door, self.door_switch.active, player)
        effect_dt = dt
        if self.door_motion.opening_started and not self.door_effect.was_open:
            effect_dt = min(dt, self.door_motion.sequence_age - self.door_motion.PAN_DURATION)
        self.door_effect.update(effect_dt, self.door, self.door_motion.opening_started)
        self.complete |= self.at_end(player)

    def at_end(self, player):
        return player.grounded and player.x >= self.end_x and player.bottom >= 815

    def camera_target(self, player):
        weight = self.door_motion.camera_weight
        x = (self.door.left + self.door.right) / 2
        y = (self.door.bottom + self.door.top) / 2
        return (player.x + (x - player.x) * weight,
                player.y + (y - player.y) * weight)
