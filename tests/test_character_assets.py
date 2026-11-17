import unittest
from unittest.mock import Mock, patch

from PIL import Image

from code.player import Player
from code.settings import IMAGE_ROOT


class CharacterAssetTests(unittest.TestCase):
    def setUp(self):
        def load(path):
            with Image.open(path) as image:
                return Mock(w=image.width, h=image.height)
        with patch("pico2d.load_image", side_effect=load):
            self.player = Player()

    def test_updated_sheets_use_all_frames_in_both_color_states(self):
        for has_blue in (True, False):
            self.player.has_blue = has_blue
            for state, count in (("idle", 16), ("run", 10)):
                with self.subTest(has_blue=has_blue, state=state):
                    self.player.state, self.player.frame = state, count - 1
                    self.player.draw(0)
                    image = self.player.current_images[state]
                    args = image.clip_composite_draw.call_args.args
                    self.assertEqual(args[:4], (448, 0, 64, 64) if state == "idle"
                                     else (576, 0, 64, 64))
                    self.player._animate(1 / self.player.ANIMATION_FPS[state],
                                         1 if state == "run" else 0)
                    self.assertAlmostEqual(self.player.frame, 0)

    def test_run_faces_movement_direction_with_and_without_blue(self):
        for has_blue in (True, False):
            self.player.has_blue = has_blue
            self.player.state = "run"
            for facing, flip in ((1, ""), (-1, "h")):
                self.player.facing = facing
                self.player.draw(0)
                self.assertEqual(self.player.current_images["run"].clip_composite_draw.call_args.args[5], flip)

    def test_supplied_grey_sheets_are_loaded_directly(self):
        with patch("pico2d.load_image", return_value=Mock(w=640, h=64)) as load:
            Player()
        paths = [call.args[0] for call in load.call_args_list]
        self.assertIn(str(IMAGE_ROOT / "character/run/run_grey.png"), paths)
        self.assertIn(str(IMAGE_ROOT / "character/jump/jump_grey.png"), paths)
        self.assertNotIn(str(IMAGE_ROOT / "background/grayscale/character/run.png"), paths)

    def test_jump_rises_with_first_two_frames_and_falls_with_last_two(self):
        for has_blue in (True, False):
            self.player.has_blue = has_blue
            self.player.grounded = False
            for velocity, state, valid in ((100, "jump", (0, 1)), (-100, "fall", (2, 3))):
                self.player.velocity_y = velocity
                for _ in range(12):
                    self.player._animate(0.1, 0)
                    self.assertEqual(self.player.state, state)
                    self.assertIn(int(self.player.frame), valid)
                    self.player.draw(0)
                    args = self.player.current_images[state].clip_composite_draw.call_args.args
                    self.assertIn(args[0], [frame * 64 for frame in valid])
            self.player.grounded = True
            self.player._animate(0.1, 0)
            self.assertEqual(self.player.state, "idle")
            self.player._animate(0.1, 1)
            self.assertEqual(self.player.state, "run")

    def test_run_size_and_foot_alignment_match_visible_pixels_in_every_frame(self):
        for has_blue, color in ((True, "blue"), (False, "grey")):
            self.player.has_blue = has_blue
            self.player.state = "run"
            with Image.open(IMAGE_ROOT / f"character/run/run_{color}.png") as sheet:
                for frame in range(10):
                    self.player.frame = frame
                    self.player.draw(0)
                    args = self.player.current_images["run"].clip_composite_draw.call_args.args
                    self.assertEqual(args[-2:], (80, 80))
                    bottom_row = sheet.crop((frame * 64, 0, (frame + 1) * 64, 64)).getbbox()[3]
                    visible_bottom = args[7] - 40 + (64 - bottom_row) * 80 / 64
                    self.assertAlmostEqual(visible_bottom, self.player.bottom, delta=0.5)
