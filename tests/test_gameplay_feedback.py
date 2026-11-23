import unittest
from types import SimpleNamespace as Event
from unittest.mock import Mock, patch

import pico2d

from code.player import Player
from code.tutorial_level import TutorialLevel
from code.color_system import ColorSystem
from code.leaves import ForestLeaves


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.level = TutorialLevel()
        self.sound = Mock()
        with patch('pico2d.load_image', return_value=Mock(w=512, h=128)):
            self.player = Player(self.level, on_sound=self.sound)
        self.player.enter_level(self.level)

    def test_steps_require_distance_and_stop_at_wall_jump_only_once_and_land_once(self):
        p = self.player
        p.keys.add(pico2d.SDLK_d)
        for _ in range(120):
            p.update(1 / 120)
        self.assertIn('step', [c.args[0] for c in self.sound.call_args_list])
        self.sound.reset_mock()
        for _ in range(60):
            p.update(1 / 120)
        self.sound.assert_not_called()
        p.keys.clear()
        event = Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE)
        p.handle_event(event)
        p.handle_event(event)
        for _ in range(120):
            p.update(1 / 120)
        self.assertEqual([c.args[0] for c in self.sound.call_args_list], ['jump', 'land'])

    def test_interaction_sound_only_on_success_and_conversion_only_for_new_color(self):
        colors = ColorSystem(on_sound=self.sound)
        gem = self.level.color_sources[0]
        self.assertFalse(colors.interact_at(0, 0, self.level, self.player))
        self.sound.assert_not_called()
        colors.interact_at(gem.x, gem.y, self.level, self.player)
        self.sound.assert_called_once_with('extract')
        colors.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_1), self.level, self.player, 0)
        self.assertEqual(self.sound.call_count, 1)
        colors.handle_event(Event(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_2), self.level, self.player, 0)
        self.sound.assert_called_with('convert')
        self.player.color = 'blue'
        self.player.x = 288
        colors.interact_at(321, 132, self.level, self.player)
        self.sound.assert_called_with('water')

    def test_leaves_use_every_supplied_frame_and_repeat_independent_of_frame_rate(self):
        with patch('pico2d.load_image', return_value=Mock()):
            leaves = ForestLeaves()
            frames = []
            for duration in leaves.frames['durations']:
                frames.append(leaves.frame)
                leaves.update(duration)
            self.assertEqual(frames, list(range(9)))
            self.assertEqual(leaves.frame, 0)
            end = []
            for fps in (30, 60, 120):
                leaves.time = 0
                for _ in range(fps):
                    leaves.update(1 / fps)
                end.append(leaves.frame)
            self.assertEqual(end, [6, 6, 6])
