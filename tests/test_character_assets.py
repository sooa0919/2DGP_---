import unittest
from unittest.mock import Mock, patch

from PIL import Image, ImageOps

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

    def test_gray_run_matches_new_blue_sheet_and_preserves_alpha(self):
        with Image.open(IMAGE_ROOT / "character/run/run_blue.png") as source, \
             Image.open(IMAGE_ROOT / "background/grayscale/character/run.png") as gray:
            source = source.convert("RGBA")
            self.assertEqual(gray.size, (640, 64))
            self.assertEqual(gray.getchannel("A").tobytes(), source.getchannel("A").tobytes())
            luminance = ImageOps.grayscale(source).tobytes()
            for channel in ("R", "G", "B"):
                self.assertEqual(gray.getchannel(channel).tobytes(), luminance)
