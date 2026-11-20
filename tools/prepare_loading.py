"""Pack every supplied GIF frame into a PNG for pico2d (Pillow required)."""
import json
from pathlib import Path

from PIL import Image


def main():
    ui = Path(__file__).resolve().parent.parent / 'image/ui'
    with Image.open(ui / 'loading.gif') as source:
        width, height = source.size
        sheet = Image.new('RGBA', (width * source.n_frames, height))
        durations = []
        for index in range(source.n_frames):
            source.seek(index)
            sheet.paste(source.convert('RGBA'), (index * width, 0))
            durations.append(source.info.get('duration', 120) / 1000)
        sheet.save(ui / 'loading_frames.png')
    (ui / 'loading_frames.json').write_text(
        json.dumps(dict(width=width, height=height, durations=durations)), encoding='utf-8')
    Image.new('RGBA', (1, 1), (0, 0, 0, 255)).save(ui / 'fade_black.png')


if __name__ == '__main__':
    main()
