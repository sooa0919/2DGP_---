import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d

from code.color_system import ColorSystem
from code.level import Level
from code.player import Player
from code.settings import SCREEN_HEIGHT


class BlueColorTests(unittest.TestCase):
    def setUp(self):
        with patch("pico2d.load_image", return_value=SimpleNamespace(w=192, h=64)):
            self.player = Player()
        self.level = Level()
        self.player.enter_level(self.level)
        self.colors = ColorSystem()
        self.pool = self.level.water[0]
        self.player.x = self.pool.left + 80
        self.player.y = self.pool.top + self.player.DRAW_SIZE / 2

    def click(self, pool=None):
        pool = pool or self.pool
        return self.colors.interact_at(self.player.x, pool.top - 8, self.level, self.player)

    def assert_conserved(self):
        self.assertEqual(int(self.player.has_blue) + sum(p.has_blue for p in self.level.water), 1)

    def test_transfer_and_reclaim_preserve_one_blue_and_switch_sprites(self):
        self.assertTrue(self.pool.solid)
        self.assertIs(self.player.current_images, self.player.images)
        self.assertTrue(self.click())
        self.assertFalse(self.pool.solid)
        self.assertFalse(self.player.has_blue)
        self.assertIs(self.player.current_images, self.player.gray_images)
        self.assert_conserved()
        self.pool.animation_time = 0.4
        self.assertTrue(self.click())
        self.assertTrue(self.pool.solid)
        self.assertEqual(self.pool.animation_time, 0)
        self.assertTrue(self.player.has_blue)
        self.assert_conserved()

    def test_solid_surface_supports_character_then_liquid_allows_sinking(self):
        self.player.update(0.4)
        self.assertEqual(self.player.y, self.pool.top + Player.DRAW_SIZE / 2)
        self.assertFalse(self.player.in_water)
        self.assertTrue(self.click())
        self.player.update(0.4)
        self.assertEqual(self.player.y, self.pool.bottom + Player.DRAW_SIZE / 2)
        self.assertTrue(self.player.in_water)
        self.assertTrue(self.click())
        self.assertEqual(self.player.y, self.pool.top + Player.DRAW_SIZE / 2)
        self.assertTrue(self.player.grounded)
        self.assertFalse(self.player.in_water)

    def test_empty_character_cannot_activate_another_pool(self):
        self.assertTrue(self.click())
        other = self.level.water[1]
        self.player.x = other.left + 80
        self.player.y = other.top + Player.DRAW_SIZE / 2
        self.assertFalse(self.click(other))
        self.assertTrue(other.solid)
        self.assert_conserved()

    def test_click_requires_target_hit_and_nearby_player(self):
        self.assertFalse(self.colors.interact_at(self.pool.left - 1, self.pool.top - 8,
                                                self.level, self.player))
        self.assertFalse(self.colors.interact_at(self.player.x, self.pool.top + 1,
                                                self.level, self.player))
        self.player.x = self.pool.left - 300
        self.assertFalse(self.colors.interact_at(self.pool.left + 1, self.pool.top - 8,
                                                self.level, self.player))
        self.assert_conserved()

    def test_screen_click_uses_camera_and_only_fresh_left_button(self):
        camera_x = 1900
        down = SimpleNamespace(type=pico2d.SDL_MOUSEBUTTONDOWN, button=pico2d.SDL_BUTTON_LEFT,
                               x=self.player.x - camera_x, y=SCREEN_HEIGHT - self.pool.top + 8)
        self.colors.handle_event(down, self.level, self.player, camera_x)
        self.assertTrue(self.pool.has_blue)
        self.colors.handle_event(down, self.level, self.player, camera_x)
        self.assertTrue(self.pool.has_blue)
        self.colors.handle_event(SimpleNamespace(type=pico2d.SDL_MOUSEBUTTONUP,
                                                button=pico2d.SDL_BUTTON_LEFT),
                                 self.level, self.player, camera_x)
        self.colors.handle_event(down, self.level, self.player, camera_x)
        self.assertFalse(self.pool.has_blue)
        down.button = pico2d.SDL_BUTTON_RIGHT
        self.colors.handle_event(down, self.level, self.player, camera_x)
        self.assertFalse(self.pool.has_blue)

    def test_reset_and_respawn_return_blue_and_gray_water(self):
        self.assertTrue(self.click())
        self.colors.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_r),
                                 self.level, self.player, 1900)
        self.assertTrue(self.player.has_blue)
        self.assertTrue(all(p.solid for p in self.level.water))
        self.assert_conserved()

    def test_actual_draw_uses_existing_gray_character_sheet(self):
        self.player.images["idle"] = Mock(w=512, h=128)
        self.player.gray_images["idle"] = Mock(w=512, h=128)
        self.click()
        self.player.draw(1900)
        self.player.gray_images["idle"].clip_composite_draw.assert_called_once()
        self.player.images["idle"].clip_composite_draw.assert_not_called()

    def test_main_routes_left_click_to_the_color_system(self):
        import main as game
        frame = 0

        def events():
            nonlocal frame
            frame += 1
            if frame == 1:
                return [SimpleNamespace(type=pico2d.SDL_MOUSEBUTTONDOWN)]
            if frame == 2:
                self.player.x = self.pool.left + 80
                self.player.y = self.pool.top + Player.DRAW_SIZE / 2
                return [SimpleNamespace(type=pico2d.SDL_MOUSEBUTTONDOWN,
                                        button=pico2d.SDL_BUTTON_LEFT,
                                        x=self.player.x - 1900,
                                        y=SCREEN_HEIGHT - self.pool.top + 8)]
            return [SimpleNamespace(type=pico2d.SDL_QUIT)]

        with patch.object(game, "Level", return_value=self.level), \
             patch.object(game, "MusicManager"), \
             patch.object(game, "LoadingScreen", return_value=Mock(needs_level=True, phase='done', done=True)), \
             patch.object(game, "TitleScreen", return_value=Mock(handle_event=Mock(return_value='new'))), \
             patch.object(game, "Player", return_value=self.player), \
             patch.object(game, "Background", return_value=Mock()), \
             patch.object(game, "Camera", return_value=SimpleNamespace(x=1900, y=0, follow=lambda x, y, dt: None)), \
             patch.object(game, "configure_fullscreen"), patch.object(game, "clear_canvas"), \
             patch.object(self.player, "draw"), \
             patch.multiple(pico2d, open_canvas=lambda *a: None, close_canvas=lambda: None,
                            get_events=events, update_canvas=lambda: None, delay=lambda t: None):
            game.main()
        self.assertTrue(self.pool.has_blue)
        self.assertFalse(self.player.has_blue)
        self.assert_conserved()
