"""Antialias the supplied GIF into a padded, high-resolution title atlas."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FRAME_SIZE = (2304, 1296)
COLUMNS = 3
PADDING = 4


def main():
    source = ROOT / 'image/ui/작은 잎사귀의 산들바람 애니메이션.gif'
    gif = Image.open(source)
    source_width, source_height = gif.size
    width, height = FRAME_SIZE
    stride_x, stride_y = width + 2 * PADDING, height + 2 * PADDING
    rows = (gif.n_frames + COLUMNS - 1) // COLUMNS
    sheet = Image.new('RGBA', (stride_x * COLUMNS, stride_y * rows))
    durations = []
    for index in range(gif.n_frames):
        gif.seek(index)
        # Pillow resamples RGBA in premultiplied-alpha space, avoiding colored
        # fringes at transparent leaf edges. Keep the original shapes and timing.
        frame = gif.convert('RGBA').resize(FRAME_SIZE, Image.Resampling.LANCZOS)
        column, row = index % COLUMNS, index // COLUMNS
        sheet.paste(frame, (column * stride_x + PADDING, row * stride_y + PADDING))
        durations.append(gif.info.get('duration', 160) / 1000)
    folder = ROOT / 'image/background/leaves'
    folder.mkdir(exist_ok=True)
    sheet.save(folder / 'leaves.png')
    (folder / 'leaves.json').write_text(json.dumps(
        {'width': width, 'height': height, 'columns': COLUMNS, 'padding': PADDING,
         'source_width': source_width, 'source_height': source_height,
         'durations': durations}), encoding='utf-8')


if __name__ == '__main__':
    main()
