"""Play the complete reference route with actual movement and click rules."""
import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.color_system import ColorSystem
from code.player import Player
from code.tutorial_level import TutorialLevel


class TutorialRouteTests(unittest.TestCase):
    def setUp(self):
        self.level = TutorialLevel()
        with patch('pico2d.load_image', return_value=Mock(w=512, h=128)):
            self.player = Player(self.level)
        self.player.enter_level(self.level)
        self.colors = ColorSystem()

    def tick(self):
        self.player.update(1 / 120)
        self.level.update(1 / 120, self.player)

    def key(self, key, down=True):
        self.player.handle_event(Event(type=pico2d.SDL_KEYDOWN if down else pico2d.SDL_KEYUP, key=key))

    def direction(self, target):
        self.player.keys.discard(pico2d.SDLK_a)
        self.player.keys.discard(pico2d.SDLK_d)
        if abs(self.player.x - target) > 1.5:
            self.player.keys.add(pico2d.SDLK_d if target > self.player.x else pico2d.SDLK_a)

    def go(self, target, jump_banks=False):
        for _ in range(3000):
            self.direction(target)
            if abs(self.player.x - target) <= 1.5 and self.player.grounded:
                return
            if jump_banks and self.player.grounded and any(
                    not p.one_way and 0 <= p.left - self.player.right < 38
                    and p.top > self.player.bottom + 1 for p in self.level.collision_platforms()):
                self.key(pico2d.SDLK_SPACE, False)
                self.key(pico2d.SDLK_SPACE)
            self.tick()
        self.fail(('walk stuck', target, self.player.x, self.player.bottom))

    def jump(self, target, floor):
        self.assertTrue(self.player.grounded)
        self.direction(target)
        self.key(pico2d.SDLK_SPACE, False)
        self.key(pico2d.SDLK_SPACE)
        for _ in range(600):
            self.direction(target)
            self.tick()
            if self.player.grounded:
                break
        self.key(pico2d.SDLK_SPACE, False)
        self.assertAlmostEqual(self.player.bottom, floor, delta=1,
                               msg=str(('jump', target, self.player.x, self.player.bottom)))
        self.go(target)

    def climb(self, top):
        while self.player.bottom < top - 1:
            next_top = min(top, self.player.bottom + 80)
            self.jump(self.player.x, next_top)

    def click(self, target):
        x = max(target.left + 1, min(self.player.x, target.right - 1))
        y = max(target.bottom + 1, min(self.player.y, target.top - 1))
        self.assertTrue(self.colors.interact_at(x, y, self.level, self.player),
                        (self.level.progress, self.player.color, target, self.player.x, self.player.y))

    def convert(self, key):
        self.colors.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=key), self.level, self.player, 0)

    def test_full_blue_green_falling_water_yellow_exit_route(self):
        p, level = self.player, self.level
        self.assertIsNone(p.color)
        self.click(level.color_sources[0])
        self.go(288)
        self.click(level.water[0])
        self.go(684, jump_banks=True)
        self.assertEqual(level.progress, 1)
        self.click(level.water[1])
        self.convert(pico2d.SDLK_2)
        self.go(808)
        self.click(level.vines[0])
        self.climb(480)
        self.jump(962, 480)
        self.assertEqual(level.progress, 2)
        self.click(level.vines[0])
        self.go(1174)
        self.jump(1354, 224)
        self.go(1454)
        self.jump(1594, 224)
        self.go(1694)
        self.jump(1834, 304)
        self.go(2120)
        self.assertEqual(p.bottom, 224)
        self.key(pico2d.SDLK_s)
        self.go(2190)
        self.key(pico2d.SDLK_s, False)
        self.assertEqual(level.progress, 3)
        self.go(2288)
        self.click(level.vines[1])
        self.climb(224)
        self.jump(2376, 224)
        self.assertEqual(level.progress, 4)
        self.click(level.vines[1])
        self.go(2520)
        self.click(level.vines[2])
        self.jump(2624, 304)
        self.jump(2728, 304)
        self.assertEqual(level.progress, 5)
        self.click(level.vines[2])
        self.go(2872)
        self.click(level.vines[3])
        self.jump(3000, 336)
        self.climb(480)
        self.jump(3096, 480)
        self.assertEqual(level.progress, 6)
        self.assertIsNone(p.color)
        self.go(3240)
        for _ in range(1200):
            drop = next((d for d in level.droplets if d.has_blue and 552 <= d.top <= 568), None)
            if drop:
                break
            self.tick()
        self.assertIsNotNone(drop)
        self.click(drop)
        self.assertTrue(drop.solid)
        frozen_top = drop.top
        self.jump(3336, frozen_top)
        self.assertEqual(level.progress, 7)
        self.go(3544)
        self.jump(3624, 600)
        self.convert(pico2d.SDLK_3)
        self.go(3696)
        self.click(level.lamp)
        self.assertTrue(level.lamp.active)
        self.go(4040)
        self.assertTrue(level.at_end(p))
        self.assertTrue(level.complete)
