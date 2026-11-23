"""Preview the actual orb animation and typing effect without a game window."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.preview_levels as renderer
from tools.preview_tutorial import Font
from code.loading import LoadingScreen
from code.settings import ROOT


def main():
    frames = []
    with patch('pico2d.load_image', side_effect=renderer.Sprite), \
         patch('pico2d.load_font', side_effect=Font):
        loading = LoadingScreen()
        loading.phase = 'loading'
        for index in range(24):
            loading.time = index * 0.12
            renderer.canvas = Image.new('RGB', (1152, 648))
            loading.draw()
            frames.append(renderer.canvas.copy())
    frames[10].save(ROOT / 'previews/loading.png')
    frames[0].save(ROOT / 'previews/loading.gif', save_all=True,
                   append_images=frames[1:], duration=120, loop=0)


if __name__ == '__main__':
    main()
