import unittest
from unittest.mock import Mock, patch

from code.loading import LoadingScreen


class LoadingTests(unittest.TestCase):
    def setUp(self):
        with patch('pico2d.load_image', return_value=Mock()), \
             patch('pico2d.load_font', return_value=Mock()):
            self.loading = LoadingScreen()

    def test_black_loading_frame_is_presented_before_level_is_requested(self):
        self.assertFalse(self.loading.needs_level)
        self.loading.update(self.loading.FADE_OUT)
        self.assertEqual(self.loading.phase, 'loading')
        self.assertFalse(self.loading.needs_level)
        self.loading.draw()
        self.assertTrue(self.loading.needs_level)
        self.loading.ready = True
        self.assertFalse(self.loading.needs_level)

    def test_two_typing_loops_then_fade_in(self):
        self.loading.update(self.loading.FADE_OUT)
        self.loading.ready = True
        for _ in range(2):
            self.assertEqual(self.loading.text, 'l')
            self.loading.update(self.loading.LETTER_TIME * 8 + 0.01)
            self.assertEqual(self.loading.text, 'loading..')
            self.loading.update(self.loading.CYCLE - self.loading.LETTER_TIME * 8 - 0.01 + 1e-8)
        self.assertEqual(self.loading.phase, 'in')
        self.loading.draw()
        self.loading.black.opacify.assert_called_with(1.0)
        self.loading.update(self.loading.FADE_IN / 2)
        self.loading.draw()
        self.loading.black.opacify.assert_called_with(0.5)
        self.loading.update(self.loading.FADE_IN / 2)
        self.assertTrue(self.loading.done)

    def test_loading_waits_for_assets_even_after_animation_duration(self):
        self.loading.update(self.loading.FADE_OUT)
        self.loading.update(20)
        self.assertEqual(self.loading.phase, 'loading')
        self.loading.ready = True
        self.loading.update(0)
        self.assertEqual(self.loading.phase, 'in')
