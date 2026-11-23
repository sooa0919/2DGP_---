"""Prepare the supplied 12-frame WebP strip for pico2d (Pillow required)."""
import json
from pathlib import Path

from PIL import Image, ImageChops


def main():
    ui = Path(__file__).resolve().parent.parent / 'image/ui'
    count = 12
    with Image.open(ui / 'loading.webp') as source:
        source = source.convert('RGB')
        if source.width % count:
            raise ValueError('Loading sheet must contain 12 equal-width frames')
        width = height = source.width // count
        brightness = ImageChops.lighter(ImageChops.lighter(
            source.getchannel('R'), source.getchannel('G')), source.getchannel('B'))
        bounds = brightness.point(lambda value: 255 if value > 16 else 0).getbbox()
        if bounds is None:
            raise ValueError('Loading sheet contains no visible lights')
        center_y = (bounds[1] + bounds[3]) // 2
        top = max(0, min(source.height - height, center_y - height // 2))
        sheet = Image.new('RGBA', (width * count, height))
        for index in range(count):
            sheet.paste(source.crop((index * width, top, (index + 1) * width, top + height)),
                        (index * width, 0))
        durations = [0.12] * count
        sheet.save(ui / 'loading_frames.png')
    (ui / 'loading_frames.json').write_text(
        json.dumps(dict(width=width, height=height, durations=durations)), encoding='utf-8')
    Image.new('RGBA', (1, 1), (0, 0, 0, 255)).save(ui / 'fade_black.png')


if __name__ == '__main__':
    main()
