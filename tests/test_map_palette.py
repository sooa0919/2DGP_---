import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.blockout import ForestBlockout
from code.illustrated_level import IllustratedLevel


class MapPaletteTests(unittest.TestCase):
    def setUp(self):
        self.level = IllustratedLevel()
        with patch('pico2d.load_image', side_effect=lambda path: Mock(w=1024, h=1008)):
            self.background = ForestBlockout(self.level)

    def test_v_toggles_once_per_press_and_releases_during_menus(self):
        bg = self.background
        down = Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_v)
        up = Event(type=pico2d.SDL_KEYUP, key=pico2d.SDLK_v)
        self.assertFalse(bg.colored)
        bg.handle_event(down)
        bg.handle_event(down)
        self.assertTrue(bg.colored)
        bg.handle_event(up, enabled=False)
        bg.handle_event(down)
        self.assertFalse(bg.colored)
        bg.handle_event(up)
        bg.handle_event(down, enabled=False)
        self.assertFalse(bg.colored)
        bg.handle_event(Event(type=pico2d.SDL_WINDOWEVENT, event=pico2d.SDL_WINDOWEVENT_FOCUS_LOST))
        bg.handle_event(down)
        self.assertTrue(bg.colored)

    def test_color_mode_uses_color_layers_without_activating_devices(self):
        bg = self.background
        platforms = self.level.collision_platforms()
        bg.colored = True
        with patch('pico2d.draw_rectangle'):
            bg.draw(0, 0)
        self.assertTrue(bg.stage.colored)
        self.assertTrue(all(layer.draw.called for layer in bg.color_layers))
        self.assertTrue(all(not layer.draw.called for layer in bg.layers))
        self.assertTrue(all(not water.has_blue for water in self.level.water))
        self.assertFalse(self.level.elevator_switch.active)
        self.assertEqual(self.level.collision_platforms(), platforms)

    def test_extracted_ceiling_source_stays_gray_in_colored_map(self):
        art = self.background.stage
        source = next(s for s in self.level.color_sources if getattr(s, 'sprite_name', None) == 'source_ceiling')
        art.colored = True
        with patch.object(art, 'draw_chunks') as draw:
            art.draw_terrain(2944)
            self.assertIs(draw.call_args.args[0][3], art.color_chunks[3])
            source.active = False
            art.draw_terrain(2944)
            self.assertIs(draw.call_args.args[0][3], art.empty_source_chunk)
            art.colored = False
            source.active = True
            art.draw_terrain(2944)
            self.assertIs(draw.call_args.args[0][3], art.source_chunk)
