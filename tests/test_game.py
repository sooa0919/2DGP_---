import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d

from code.camera import Camera
from code.player import Player
from code.level import Level, Platform
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
        floor = GROUND_HEIGHT + Player.DRAW_SIZE / 2
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
        self.assertEqual(self.player.y, GROUND_HEIGHT + Player.DRAW_SIZE / 2)

    def test_opposing_keys_and_map_limits(self):
        self.key(pico2d.SDLK_a)
        self.key(pico2d.SDLK_d)
        self.player.update(0.1)
        self.assertEqual(self.player.x, 200)
        self.key(pico2d.SDLK_a, False)
        half = Player.DRAW_SIZE / 2
        self.player.x = WORLD_WIDTH - half - 1
        self.player.update(0.1)
        self.assertEqual(self.player.x, WORLD_WIDTH - half)
        self.player.x = half + 1
        self.key(pico2d.SDLK_d, False)
        self.key(pico2d.SDLK_a)
        self.player.update(0.1)
        self.assertEqual(self.player.x, half)

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

    def test_both_routes_are_traversable_with_actual_jump_physics(self):
        for index in (0, 1):
            level = Level(index)
            self.player.enter_level(level)
            self.key(pico2d.SDLK_d)
            for _ in range(2400):
                p = self.player
                foot = p.y - p.DRAW_SIZE / 2
                if p.grounded:
                    half = p.DRAW_SIZE / 2
                    ahead = any(s.left > p.x and s.left - (p.x + half) < 40
                                and s.top > foot + 1 and s.bottom < p.y + half
                                for s in level.platforms)
                    support = next((s for s in level.platforms
                                    if abs(s.top - foot) < 1 and s.left <= p.x < s.right), None)
                    gap = (support is not None and support.right - p.x < 36
                           and not any(s.left == support.right and s.bottom == 0
                                       for s in level.platforms))
                    if ahead or gap:
                        self.key(pico2d.SDLK_w)
                self.player.update(1 / 60)
                self.key(pico2d.SDLK_w, False)
                if level.can_exit(self.player):
                    break
            self.assertTrue(level.can_exit(self.player),
                            (index, self.player.x, self.player.y))

    def test_wall_ceiling_walk_off_and_respawn(self):
        level = Level()
        level.platforms = [Platform(0, 0, 320, 96), Platform(320, 0, 480, 160)]
        self.player.enter_level(level)
        self.key(pico2d.SDLK_d)
        self.player.update(1)
        self.assertEqual(self.player.x, 320 - Player.DRAW_SIZE / 2)
        self.key(pico2d.SDLK_w)
        self.player.update(0.7)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.y, 160 + Player.DRAW_SIZE / 2)
        self.player.update(0.6)
        self.assertFalse(self.player.grounded)
        self.key(pico2d.SDLK_d, False)
        self.player.update(2)
        self.assertEqual(self.player.x, level.spawn[0])
        self.assertTrue(self.player.grounded)
        level.platforms.append(Platform(128, 208, 288, 240))
        self.key(pico2d.SDLK_w, False)
        self.key(pico2d.SDLK_w)
        self.player.update(0.1)
        self.assertLessEqual(self.player.y + Player.DRAW_SIZE / 2, 208)
        self.assertLessEqual(self.player.velocity_y, 0)

    def test_exit_requires_nearby_grounded_player_and_level_resets_motion(self):
        level = Level()
        self.player.enter_level(level)
        self.assertFalse(level.can_exit(self.player))
        self.player.x = level.exit_x
        self.assertTrue(level.can_exit(self.player))
        self.player.grounded = False
        self.assertFalse(level.can_exit(self.player))
        self.key(pico2d.SDLK_d)
        self.player.velocity_y = -500
        self.player.enter_level(Level(1))
        self.assertFalse(self.player.keys)
        self.assertEqual(self.player.velocity_y, 0)
        self.assertTrue(self.player.grounded)

    def test_main_switches_maps_only_on_fresh_e_at_exit(self):
        import main as game
        active = self.player
        scenes = []

        def background(level):
            scenes.append(level.index)
            return SimpleNamespace(draw=lambda x: None, draw_overlay=lambda x, p: None)

        def events():
            frame = events.frame
            events.frame += 1
            if frame in (2, 3, 5):
                active.x = active.level.exit_x
                active.y = active.level.exit_y + active.DRAW_SIZE / 2
            if frame == 6:
                return [SimpleNamespace(type=pico2d.SDL_QUIT)]
            return [SimpleNamespace(type=pico2d.SDL_KEYUP if frame in (1, 4) else pico2d.SDL_KEYDOWN,
                                    key=pico2d.SDLK_e)]

        events.frame = 0
        with patch.object(game, "Background", side_effect=background), \
             patch.object(game, "Player", return_value=active), \
             patch.object(game, "configure_fullscreen"), \
             patch.object(game, "clear_canvas"), \
             patch.object(active, "draw"), \
             patch.multiple(pico2d, open_canvas=lambda *a: None, close_canvas=lambda: None,
                            get_events=events, update_canvas=lambda: None, delay=lambda t: None):
            game.main()
        self.assertEqual(scenes, [0, 1, 0])

    def test_connected_soil_uses_plain_tile_and_exposed_walls_keep_edges(self):
        level = Level()
        level.platforms = [Platform(0, 0, 64, 96), Platform(64, 0, 128, 160)]
        tiles = level.terrain_tiles()
        self.assertEqual(tiles[1, 1], 12)
        self.assertEqual(tiles[2, 1], 12)
        self.assertEqual(tiles[2, 3], 11)
        self.assertEqual(tiles[0, 1], 11)
        self.assertEqual(tiles[3, 1], 13)

    def test_water_is_enterable_has_a_floor_and_allows_jumping_out(self):
        for index in (0, 1):
            level = Level(index)
            for pool in level.water:
                self.player.enter_level(level)
                self.player.x = (pool.left + pool.right) / 2
                self.player.y = pool.top + 40
                self.player.grounded = False
                self.player.update(0.8)
                self.assertEqual(self.player.y, pool.bottom + 40)
                self.assertTrue(self.player.grounded)
                self.assertTrue(self.player.in_water)
                self.key(pico2d.SDLK_w)
                self.player.update(0.17)
                self.assertGreater(self.player.y - 40, pool.top)
                self.assertFalse(self.player.in_water)


if __name__ == "__main__":
    unittest.main()
