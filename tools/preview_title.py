"""Render the title menu's actual draw calls without opening a window."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.preview_levels as renderer
from code.title import TitleScreen


def main():
    output = Path(__file__).resolve().parent.parent / 'previews'
    with patch('pico2d.load_image', side_effect=renderer.Sprite):
        title = TitleScreen()
        for filename, menu, hover in (
                ('title_main.png', 'main', None),
                ('title_hover.png', 'main', 'start'),
                ('title_new_game.png', 'start', 'new')):
            title.menu = menu
            title.mouse = None
            if hover:
                left, bottom, right, top = title.bounds(hover)
                title.mouse = ((left + right) / 2, (bottom + top) / 2)
            renderer.canvas = Image.new('RGB', (1152, 648))
            title.draw()
            renderer.canvas.save(output / filename)
        title.menu, title.mouse = 'main', None
        frames = []
        for duration in title.leaves.frames['durations']:
            renderer.canvas = Image.new('RGB', (1152, 648))
            title.draw()
            frames.append(renderer.canvas.copy())
            title.update(duration)
        frames[0].save(output / 'title_leaves.gif', save_all=True,
                       append_images=frames[1:],
                       duration=[round(d * 1000) for d in title.leaves.frames['durations']], loop=0)


if __name__ == '__main__':
    main()
