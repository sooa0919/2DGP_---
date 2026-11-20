import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d

from code.camera import Camera
from code.color_system import ColorSystem
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
        self.key(pico2d.SDLK_SPACE)
        self.player.update(0.1)
        self.assertGreater(self.player.y, floor)
        self.assertFalse(self.player.grounded)
        velocity = self.player.velocity_y
        self.key(pico2d.SDLK_SPACE, False)
        self.key(pico2d.SDLK_SPACE)
        self.assertEqual(self.player.velocity_y, velocity)
        for _ in range(120):
            self.player.update(1 / 60)
        self.assertEqual(self.player.y, floor)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.state, "idle")

    def test_holding_jump_does_not_repeat_on_landing(self):
        self.key(pico2d.SDLK_SPACE)
        for _ in range(120):
            self.player.update(1 / 60)
            self.key(pico2d.SDLK_SPACE)
        self.assertTrue(self.player.grounded)

    def test_w_no_longer_jumps_and_space_does(self):
        self.key(pico2d.SDLK_w)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.velocity_y, 0)
        self.key(pico2d.SDLK_SPACE)
        self.assertFalse(self.player.grounded)
        self.assertEqual(self.player.velocity_y, Player.JUMP_SPEED)

    def test_s_in_air_preserves_normal_gravity_and_ground_collision(self):
        self.key(pico2d.SDLK_SPACE)
        self.player.update(0.1)
        velocity = self.player.velocity_y
        self.key(pico2d.SDLK_s)
        self.player.update(0.1)
        self.assertAlmostEqual(self.player.velocity_y, velocity - Player.GRAVITY * 0.1)
        for _ in range(60):
            self.player.update(1 / 60)
        self.assertEqual(self.player.y, GROUND_HEIGHT + Player.DRAW_SIZE / 2)

    def test_opposing_keys_and_map_limits(self):
        self.key(pico2d.SDLK_a)
        self.key(pico2d.SDLK_d)
        self.player.update(0.1)
        self.assertEqual(self.player.x, 200)
        self.key(pico2d.SDLK_a, False)
        half = Player.HALF_WIDTH
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

    def test_forest_route_is_traversable_with_actual_jump_physics(self):
        for index in (0,):
            level = Level()
            self.player.enter_level(level)
            self.key(pico2d.SDLK_d)
            for _ in range(2400):
                p = self.player
                foot = p.y - p.DRAW_SIZE / 2
                if p.grounded:
                    half = p.HALF_WIDTH
                    ahead = any(s.left > p.x and s.left - (p.x + half) < 40
                                and s.top > foot + 1 and s.bottom < p.y + half
                                for s in level.platforms)
                    support = next((s for s in level.platforms
                                    if abs(s.top - foot) < 1 and s.left <= p.x < s.right), None)
                    gap = (support is not None and support.right - p.x < 36
                           and not any(s.left == support.right and s.bottom == 0
                                       for s in level.platforms))
                    if ahead or gap:
                        self.key(pico2d.SDLK_SPACE)
                self.player.update(1 / 60)
                self.key(pico2d.SDLK_SPACE, False)
                if level.at_end(self.player):
                    break
            self.assertTrue(level.at_end(self.player),
                            (index, self.player.x, self.player.y))

    def test_wall_ceiling_walk_off_and_respawn(self):
        level = Level()
        level.platforms = [Platform(0, 0, 320, 96), Platform(320, 0, 480, 160)]
        self.player.enter_level(level)
        self.key(pico2d.SDLK_d)
        self.player.update(1)
        self.assertEqual(self.player.x, 320 - Player.HALF_WIDTH)
        self.key(pico2d.SDLK_SPACE)
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
        self.key(pico2d.SDLK_SPACE, False)
        self.key(pico2d.SDLK_SPACE)
        self.player.update(0.12)
        self.assertLessEqual(self.player.top, 208)
        self.assertLessEqual(self.player.velocity_y, 0)

    def test_respawn_resets_motion(self):
        self.player.enter_level(Level())
        self.key(pico2d.SDLK_d)
        self.player.update(0.1)
        self.player.velocity_y = -500
        self.player.enter_level(Level())
        self.assertFalse(self.player.keys)
        self.assertEqual(self.player.velocity_y, 0)
        self.assertTrue(self.player.grounded)

    def test_holding_movement_at_either_wall_keeps_run_animation(self):
        for direction, key in ((1, pico2d.SDLK_d), (-1, pico2d.SDLK_a)):
            level = Level()
            level.platforms = [Platform(0, 0, 320, 96 if direction == 1 else 160),
                               Platform(320, 0, 640, 160 if direction == 1 else 96)]
            self.player.enter_level(level)
            self.player.x = 200 if direction == 1 else 440
            self.key(key)
            self.player.update(1)
            contact_x = 320 - direction * Player.HALF_WIDTH
            self.assertEqual(self.player.x, contact_x)
            self.assertEqual((self.player.state, self.player.facing), ("run", direction))
            frame = self.player.frame
            self.player.update(0.05)
            self.assertEqual(self.player.x, contact_x)
            self.assertNotEqual(self.player.frame, frame)
            self.key(key, False)
            self.player.update(0.05)
            self.assertEqual(self.player.state, "idle")

    def test_body_can_approach_wall_past_transparent_frame_margin(self):
        level = Level()
        level.platforms = [Platform(0, 0, 320, 96), Platform(320, 0, 640, 160)]
        self.player.enter_level(level)
        self.player.x = 320 - Player.DRAW_SIZE / 2
        self.key(pico2d.SDLK_d)
        self.player.update(0.02)
        self.assertGreater(self.player.x, 320 - Player.DRAW_SIZE / 2)
        self.assertLess(self.player.right, 320)
        self.player.update(0.5)
        self.assertEqual(self.player.right, 320)

    def test_ledge_support_uses_feet_and_not_the_cloak(self):
        level = Level()
        level.platforms = [Platform(0, 0, 320, 96)]
        self.player.enter_level(level)
        self.player.x = 319
        self.player.update(0.05)
        self.assertEqual(self.player.bottom, 96)
        self.player.x = 320 + Player.FOOT_HALF_WIDTH + 1
        self.assertLess(self.player.left, 320)
        self.player.update(0.05)
        self.assertFalse(self.player.grounded)
        self.assertLess(self.player.bottom, 96)

    def test_head_collision_uses_body_height_in_a_low_passage(self):
        level = Level()
        level.platforms = [Platform(0, 0, 640, 96), Platform(256, 160, 448, 192)]
        self.player.enter_level(level)
        self.key(pico2d.SDLK_d)
        self.player.update(0.5)
        self.assertAlmostEqual(self.player.x, 320)
        self.assertEqual(self.player.bottom, 96)
        self.assertLessEqual(self.player.top, 160)
        self.key(pico2d.SDLK_d, False)
        self.key(pico2d.SDLK_SPACE)
        self.player.update(0.05)
        self.assertLessEqual(self.player.top, 160)
        self.assertLessEqual(self.player.velocity_y, 0)

    def test_tutorial_ignores_e_and_updates_water_animation(self):
        import main as game
        scene = Mock()
        events = iter([[SimpleNamespace(type=pico2d.SDL_MOUSEBUTTONDOWN)],
                       [SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_e)],
                       [SimpleNamespace(type=pico2d.SDL_QUIT)]])
        with patch.object(game, "Background", return_value=scene) as factory, \
             patch.object(game, "TitleScreen", return_value=Mock(handle_event=Mock(return_value='new'))), \
             patch.object(game, "Tutorial", return_value=Mock(paused=False)), \
             patch.object(game, "Player", return_value=self.player), \
             patch.object(game, "configure_fullscreen"), \
             patch.object(game, "clear_canvas"), \
             patch.object(self.player, "draw"), \
             patch.multiple(pico2d, open_canvas=lambda *a: None, close_canvas=lambda: None,
                            get_events=lambda: next(events), update_canvas=lambda: None,
                            delay=lambda t: None):
            game.main()
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(scene.update.call_count, 2)

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
        for index in (0,):
            level = Level()
            for pool in level.water:
                self.player.enter_level(level)
                self.player.x = (pool.left + pool.right) / 2
                self.player.y = pool.top + Player.DRAW_SIZE / 2
                self.assertTrue(ColorSystem().interact_at(self.player.x, pool.top - 8, level, self.player))
                self.player.grounded = False
                self.player.update(0.8)
                self.assertEqual(self.player.y, pool.bottom + Player.DRAW_SIZE / 2)
                self.assertTrue(self.player.grounded)
                self.assertTrue(self.player.in_water)
                self.key(pico2d.SDLK_SPACE)
                self.player.update(0.17)
                self.assertGreater(self.player.y - Player.DRAW_SIZE / 2, pool.top)
                self.assertFalse(self.player.in_water)


if __name__ == "__main__":
    unittest.main()
