"""Extract color rows of Part 1/16.png, with a matching golden-yellow variant."""
from pathlib import Path

from PIL import Image, ImageOps


def main():
    character = Path(__file__).resolve().parent.parent / 'image/character'
    source = character / 'effefct/Effect and FX Pixel All Free (1)/Free/Part 1/16.png'
    with Image.open(source) as image:
        image = image.convert('RGBA')
        sheet = Image.new('RGBA', (image.width, 64 * 3))
        for target, row in enumerate((2, 3)):
            sheet.paste(image.crop((0, row * 64, image.width, (row + 1) * 64)),
                        (0, target * 64))
        neutral = image.crop((0, 5 * 64, image.width, 6 * 64))
        yellow = ImageOps.colorize(neutral.convert('L'),
                                  black=(75, 41, 8), white=(255, 255, 218),
                                  mid=(255, 210, 65), midpoint=160).convert('RGBA')
        yellow.putalpha(neutral.getchannel('A'))
        sheet.paste(yellow, (0, 128))
        sheet.save(character / 'interaction/extraction_effects.png')


if __name__ == '__main__':
    main()
