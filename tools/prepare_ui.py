"""Extract the supplied UI sheet's colored components without altering the source."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def main():
    sheet = Image.open(ROOT / 'image/ui/ui.png').convert('RGBA')
    output = ROOT / 'image/ui/current'
    output.mkdir(exist_ok=True)
    regions = {
        'menu': (145, 1800, 860, 2860),
        'frame': (1000, 1820, 2440, 2910),
        'button': (315, 1435, 595, 1545),
        'back': (320, 1550, 435, 1675),
        'reset': (470, 1550, 585, 1675),
        'track': (750, 1455, 1325, 1520),
        'fill': (760, 1540, 1320, 1585),
        'knob': (745, 1610, 820, 1695),
    }
    for name, bounds in regions.items():
        crop = sheet.crop(bounds)
        crop = crop.crop(crop.getchannel('A').getbbox())
        crop.save(output / f'{name}.png')
        print(name, crop.size)


if __name__ == '__main__':
    main()
