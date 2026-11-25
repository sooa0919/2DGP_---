"""Compatibility command and shared helpers for headless game previews."""
import sys
from pathlib import Path
from PIL import ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.preview_levels as renderer


class Font:
    def __init__(self, path, size):
        self.font = ImageFont.truetype(path, size)

    def draw(self, x, y, text, color):
        ImageDraw.Draw(renderer.canvas).text((round(x), round(648-y)), text,
                                             font=self.font, fill=color, anchor='lm')


def rectangle(x1, y1, x2, y2, r=255, g=0, b=0, a=255, filled=False):
    ImageDraw.Draw(renderer.canvas).rectangle(
        (int(x1), int(648-y2), int(x2), int(648-y1)),
        fill=(r,g,b) if filled else None, outline=(r,g,b))


def main():
    from tools.preview_stage import main as preview_stage
    preview_stage()


if __name__ == '__main__':
    main()
