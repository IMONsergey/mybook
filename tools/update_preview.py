from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'manuscript/source.md').read_text(encoding='utf-8')
counter = 0

def figure(match):
    global counter
    counter += 1
    filename, caption = match.groups()
    return f'![{caption}](../assets/figures/{filename})\n\n*Рисунок {counter}. {caption}*'

preview = re.sub(r'\[\[FIGURE:([^|]+)\|(.+?)\]\]', figure, source)
preview = re.sub(r'(?m)^(#{1,4} [^\n]+)\n(?!\n)', r'\1\n\n', preview)
(ROOT / 'manuscript/README.md').write_text(preview, encoding='utf-8')
print(f'Preview updated: {counter} illustrations')
