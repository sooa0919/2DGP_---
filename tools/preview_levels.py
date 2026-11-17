"""Render the actual scene draw calls to PNGs without opening a game window."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageOps
import pico2d

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from code.background import Background
from code.level import Level
from code.player import Player

canvas = None


class Sprite:
    def __init__(self, path):
        self.image = Image.open(path).convert("RGBA")
        self.w, self.h = self.image.size
        self.opacity = 1.0

    def opacify(self, opacity):
        self.opacity = opacity

    def draw(self, x, y, w=None, h=None):
        w, h = round(w or self.w), round(h or self.h)
        bitmap = self.image.resize((w, h), Image.Resampling.NEAREST)
        if self.opacity != 1.0:
            bitmap.putalpha(bitmap.getchannel("A").point(lambda v: round(v * self.opacity)))
        canvas.paste(bitmap, (round(x - w / 2), round(648 - y - h / 2)), bitmap)

    def clip_composite_draw(self, x, y, w, h, angle, flip, cx, cy, dw, dh):
        original = self.image
        self.image = original.crop((x, self.h - y - h, x + w, self.h - y))
        if flip == "h":
            self.image = ImageOps.mirror(self.image)
        self.draw(cx, cy, dw, dh)
        self.image = original

    def clip_draw(self, x, y, w, h, cx, cy, dw, dh):
        self.clip_composite_draw(x, y, w, h, 0, "", cx, cy, dw, dh)


def main():
    global canvas
    output = Path(__file__).resolve().parent.parent / "previews"
    output.mkdir(exist_ok=True)
    with patch("pico2d.load_image", side_effect=Sprite):
        for index in (0,):
            level = Level()
            background = Background(level)
            player = Player(level)
            player.enter_level(level)
            for label, camera in (("start", 0), ("middle", 900), ("water", 3400),
                                  ("waterfall", 1900), ("end", level.width - 1152),
                                  ("run_right", 0), ("run_left", 0)):
                canvas = Image.new("RGB", (1152, 648))
                player.enter_level(level)
                if label == "end":
                    player.x, player.y = level.end_x, 96 + player.DRAW_SIZE / 2
                elif label == "water":
                    pool = level.water[2]
                    player.x = (pool.left + pool.right) / 2
                    player.y = pool.bottom + player.DRAW_SIZE / 2
                elif label == "waterfall":
                    pool = level.water[1]
                    player.x, player.y = pool.left + 160, pool.bottom + player.DRAW_SIZE / 2
                elif label.startswith("run_"):
                    player.enter_level(level)
                    if label == "run_left":
                        player.x = 420
                    player.keys.add(pico2d.SDLK_d if label == "run_right" else pico2d.SDLK_a)
                    for _ in range(24):
                        player.update(1 / 60)
                background.draw(camera)
                player.draw(camera)
                background.draw_overlay(camera, player)
                canvas.save(output / f"map{index + 1}_{label}.png")
            # A moving preview uses the same draw calls and frame clock as the game.
            frames = []
            for step in range(20):
                canvas = Image.new("RGB", (1152, 648))
                background.water.time = step / 10
                background.draw(1900)
                background.draw_overlay(1900, player)
                frames.append(canvas.copy())
            frames[0].save(output / "forest_waterfall.gif", save_all=True,
                           append_images=frames[1:], duration=100, loop=0)
            overview = Image.new("RGB", (level.width, 648))
            for left in range(0, level.width, 1152):
                camera = min(left, level.width - 1152)
                canvas = Image.new("RGB", (1152, 648))
                background.draw(camera)
                background.draw_overlay(camera, player)
                width = min(1152, level.width - left)
                overview.paste(canvas.crop((left - camera, 0, left - camera + width, 648)), (left, 0))
            overview.resize((2560, 324), Image.Resampling.NEAREST).save(output / "forest_overview.png")


if __name__ == "__main__":
    main()
