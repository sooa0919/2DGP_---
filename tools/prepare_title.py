"""Pack title.gif into bounded PNG atlases for animated pico2d playback."""
import json
from pathlib import Path

from PIL import Image


def main():
    ui = Path(__file__).resolve().parent.parent / 'image/ui'
    output = ui / 'title_frames'
    output.mkdir(exist_ok=True)
    width, height = 1152, 648
    columns, per_sheet = 3, 12
    durations, paths = [], []
    with Image.open(ui / 'title.gif') as source:
        for start in range(0, source.n_frames, per_sheet):
            count = min(per_sheet, source.n_frames - start)
            rows = (count + columns - 1) // columns
            atlas = Image.new('RGB', (width * columns, height * rows))
            for local in range(count):
                source.seek(start + local)
                frame = source.convert('RGBA')
                background = Image.new('RGBA', source.size, (0, 0, 0, 255))
                background.alpha_composite(frame)
                frame = background.convert('RGB').resize((width, height), Image.Resampling.NEAREST)
                row, column = divmod(local, columns)
                atlas.paste(frame, (column * width, row * height))
                durations.append(max(10, source.info.get('duration', 100)) / 1000)
            filename = f'title_frames/atlas_{len(paths):02}.png'
            atlas.save(ui / filename)
            paths.append(filename)
    metadata = dict(width=width, height=height, columns=columns,
                    per_sheet=per_sheet, paths=paths, durations=durations)
    (ui / 'title_frames.json').write_text(json.dumps(metadata), encoding='utf-8')


if __name__ == '__main__':
    main()
