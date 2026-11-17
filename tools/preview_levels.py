"""Render the actual scene draw calls to PNGs without opening a game window."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageOps
import pico2d

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from code.background import Background
from code.level import Level
from code.color_system import ColorSystem
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
        level = Level()
        background = Background(level)
        player = Player(level)
        colors = ColorSystem()

        def render(camera):
            global canvas
            canvas = Image.new("RGB", (1152, 648))
            background.draw(camera)
            player.draw(camera)
            background.draw_overlay(camera, player)
            return canvas.copy()

        for label, camera in (("start", 0), ("middle", 900), ("water", 3400),
                              ("end", level.width - 1152), ("run_right", 0), ("run_left", 0)):
            player.enter_level(level)
            if label == "end":
                player.x, player.y = level.end_x, 96 + player.DRAW_SIZE / 2
            elif label == "water":
                pool = level.water[1]
                player.x = (pool.left + pool.right) / 2
                player.y = pool.top + player.DRAW_SIZE / 2
            elif label.startswith("run_"):
                if label == "run_left":
                    player.x = 300
                player.keys.add(pico2d.SDLK_d if label == "run_right" else pico2d.SDLK_a)
                for _ in range(24):
                    player.update(1 / 60)
            render(camera).save(output / f"map1_{label}.png")

        for color in ("blue", "grey"):
            for phase, steps in (("rise", 8), ("fall", 28)):
                player.enter_level(level)
                player.has_blue = color == "blue"
                player.grounded = False
                player.velocity_y = player.JUMP_SPEED
                for _ in range(steps):
                    player.update(1 / 60)
                render(0).save(output / f"jump_{color}_{phase}.png")

        player.enter_level(level)
        pool = level.water[0]
        player.x, player.y = pool.left + 160, pool.top + player.DRAW_SIZE / 2
        render(1900).save(output / "blue_01_solid.png")
        colors.interact_at(player.x, pool.top - 8, level, player)
        player.update(0.4)
        background.update(0.2)
        render(1900).save(output / "blue_02_liquid.png")
        colors.interact_at(player.x, pool.top - 8, level, player)
        render(1900).save(output / "blue_03_reclaimed.png")

        player.enter_level(level)
        player.x, player.y = pool.left + 160, pool.top + player.DRAW_SIZE / 2
        frames = []
        for step in range(30):
            if step in (5, 22):
                colors.interact_at(player.x, pool.top - 8, level, player)
            player.update(0.1)
            background.update(0.1)
            frames.append(render(1900))
        frames[0].save(output / "blue_transfer.gif", save_all=True,
                       append_images=frames[1:], duration=100, loop=0)

        player.enter_level(level)
        overview = Image.new("RGB", (level.width, 648))
        for left in range(0, level.width, 1152):
            camera = min(left, level.width - 1152)
            shot = render(camera)
            width = min(1152, level.width - left)
            overview.paste(shot.crop((left - camera, 0, left - camera + width, 648)), (left, 0))
        overview.resize((2560, 324), Image.Resampling.NEAREST).save(output / "forest_overview.png")


if __name__ == "__main__":
    main()
