"""Convert the supplied transparent leaf GIF to a grayscale runtime sprite sheet."""
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent


def main():
    source = ROOT / 'image/ui/작은 잎사귀의 산들바람 애니메이션.gif'
    gif = Image.open(source)
    width, height = gif.size
    sheet = Image.new('RGBA', (width * gif.n_frames, height))
    durations = []
    for index in range(gif.n_frames):
        gif.seek(index)
        frame = gif.convert('RGBA')
        gray = ImageOps.grayscale(frame).convert('RGBA')
        gray.putalpha(frame.getchannel('A'))
        sheet.paste(gray, (index * width, 0))
        durations.append(gif.info.get('duration', 160) / 1000)
    folder = ROOT / 'image/background/leaves'
    folder.mkdir(exist_ok=True)
    sheet.save(folder / 'leaves.png')
    (folder / 'leaves.json').write_text(json.dumps(
        {'width': width, 'height': height, 'durations': durations}), encoding='utf-8')


if __name__ == '__main__':
    main()
