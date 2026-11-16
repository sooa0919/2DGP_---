import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d

from code.camera import Camera
from code.player import Player
from code.settings import GROUND_HEIGHT, SCREEN_WIDTH, WORLD_WIDTH


class PlatformerTests(unittest.TestCase):
    def setUp(self):
        def image(path):
            return SimpleNamespace(w=512, h=128) if "idle" in path else SimpleNamespace(w=192, h=64)
        with patch("pico2d.load_image", side_effect=image):
            self.player = Player()

    def key(self, key, down=True):
        self.player.handle_event(SimpleNamespace(
            type=pico2d.SDL_KEYDOWN if down else pico2d.SDL_KEYUP, key=key,
        ))

    def test_run_release_and_facing(self):
        self.key(pico2d.SDLK_a)
        self.player.update(0.1)
        self.assertEqual(self.player.x, 176)
        self.assertEqual((self.player.state, self.player.facing), ("run", -1))
        self.key(pico2d.SDLK_a, False)
        self.player.update(0.1)
        self.assertEqual(self.player.state, "idle")

    def test_jump_no_double_jump_and_landing(self):
        floor = GROUND_HEIGHT + 32
        self.key(pico2d.SDLK_w)
        self.player.update(0.1)
        self.assertGreater(self.player.y, floor)
        self.assertFalse(self.player.grounded)
        velocity = self.player.velocity_y
        self.key(pico2d.SDLK_w, False)
        self.key(pico2d.SDLK_w)
        self.assertEqual(self.player.velocity_y, velocity)
        for _ in range(120):
            self.player.update(1 / 60)
        self.assertEqual(self.player.y, floor)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.state, "idle")

    def test_holding_jump_does_not_repeat_on_landing(self):
        self.key(pico2d.SDLK_w)
        for _ in range(120):
            self.player.update(1 / 60)
            self.key(pico2d.SDLK_w)
        self.assertTrue(self.player.grounded)

    def test_fast_fall_and_ground_collision(self):
        self.key(pico2d.SDLK_w)
        self.player.update(0.1)
        velocity = self.player.velocity_y
        self.key(pico2d.SDLK_s)
        self.player.update(0.1)
        self.assertAlmostEqual(self.player.velocity_y, velocity - Player.FAST_FALL_GRAVITY * 0.1)
        for _ in range(60):
            self.player.update(1 / 60)
        self.assertEqual(self.player.y, GROUND_HEIGHT + 32)

    def test_opposing_keys_and_map_limits(self):
        self.key(pico2d.SDLK_a)
        self.key(pico2d.SDLK_d)
        self.player.update(0.1)
        self.assertEqual(self.player.x, 200)
        self.key(pico2d.SDLK_a, False)
        self.player.x = WORLD_WIDTH - 33
        self.player.update(0.1)
        self.assertEqual(self.player.x, WORLD_WIDTH - 32)
        self.player.x = 33
        self.key(pico2d.SDLK_d, False)
        self.key(pico2d.SDLK_a)
        self.player.update(0.1)
        self.assertEqual(self.player.x, 32)

    def test_focus_loss_clears_keys(self):
        self.key(pico2d.SDLK_d)
        self.player.handle_event(SimpleNamespace(
            type=pico2d.SDL_WINDOWEVENT, event=pico2d.SDL_WINDOWEVENT_FOCUS_LOST,
        ))
        self.assertFalse(self.player.keys)

    def test_camera_tracks_and_stops_at_world_edges(self):
        camera = Camera(SCREEN_WIDTH, WORLD_WIDTH)
        for target, expected in ((32, 0), (2000, 2000 - SCREEN_WIDTH / 2),
                                 (WORLD_WIDTH - 32, WORLD_WIDTH - SCREEN_WIDTH)):
            camera.follow(target)
            self.assertEqual(camera.x, expected)


if __name__ == "__main__":
    unittest.main()
