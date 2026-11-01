#!/usr/bin/env python3
"""Read-only manuscript/asset checks. No literary score or automatic edits."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

FIGURE = re.compile(r'\[\[FIGURE:([^|\]\n]+)\|([^\]\n]+)\]\]')


def audit(root):
    root = Path(root).resolve()
    issues, assets = [], []
    def issue(code, message, line=None, severity='warning'):
        issues.append(dict(code=code, severity=severity, line=line, message=message))
    source = root / 'manuscript/source.md'
    if not source.is_file():
        issue('missing_source', 'Нет manuscript/source.md', severity='error')
        return dict(schema_version=1, issues=issues, assets=[], stats={})
    raw = source.read_bytes()
    text = raw.decode('utf-8')
    for n, line in enumerate(text.splitlines(), 1):
        for char, code in [('ё', 'yo'), ('Ё', 'yo'), ('—', 'em_dash')]:
            if char in line:
                issue(code, f'Символ {char!r}: {line.count(char)}. Проверить правило автора.', n)
        if re.search(r'\b(TODO|TBD|FIXME)\b|\[уточнить\]', line, re.I):
            issue('placeholder', 'Осталось поле для уточнения.', n)
        if '[[FIGURE:' in line and not FIGURE.fullmatch(line.strip()):
            issue('malformed_figure', 'Некорректный маркер иллюстрации.', n, 'error')
        # Exclude URLs: URL paths can legitimately repeat words.
        prose = re.sub(r'https?://\S+', '', line)
        if re.search(r'\b([А-Яа-яЁёA-Za-z]+)\s+\1\b', prose, re.I):
            issue('repeated_word', 'Возможен случайный повтор соседних слов.', n)
    paras = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 70 and not p.startswith('[[')]
    for paragraph, count in Counter(paras).items():
        if count > 1:
            issue('duplicate_paragraph', f'Абзац повторяется {count} раза: {paragraph[:75]}')
    try:
        manifest = json.loads((root / 'assets/figures/manifest.json').read_text())
        if not isinstance(manifest, list):
            raise ValueError('Expected list')
    except (OSError, ValueError):
        manifest = []
        issue('manifest', 'Нет корректного списка manifest.json.', severity='error')
    by_name = {}
    for item in manifest:
        name = item.get('path')
        if not isinstance(name, str):
            issue('manifest_path', 'Нет имени изображения.', severity='error')
            continue
        if name in by_name:
            issue('duplicate_manifest', f'Повтор в manifest: {name}', severity='error')
        by_name[name] = item
    rights_file = root / 'assets/rights.csv'
    rights = {}
    if rights_file.exists():
        with rights_file.open(newline='') as f:
            rights = {r['asset_id']: r for r in csv.DictReader(f)}
    else:
        issue('rights_registry', 'Нет реестра прав assets/rights.csv.')
    try:
        from PIL import Image
    except ImportError:
        Image = None
        issue('image_check_skipped', 'Pillow недоступен: размеры файлов не проверены.')
    seen = set()
    base = (root / 'assets/figures').resolve()
    for match in FIGURE.finditer(text):
        name, caption = match.groups()
        line = text.count('\n', 0, match.start()) + 1
        if name in seen:
            issue('reused_figure', f'Повторное использование {name}: проверить намерение.', line)
        seen.add(name)
        path = (base / name).resolve()
        if not path.is_relative_to(base):
            issue('unsafe_path', 'Изображение находится вне assets/figures.', line, 'error')
            continue
        item = by_name.get(name)
        if item is None:
            issue('unlisted_figure', f'Нет записи manifest: {name}', line, 'error')
        elif not item.get('alt', '').strip():
            issue('missing_alt', f'Нет alt: {name}', line)
        if not caption.strip():
            issue('missing_caption', f'Нет подписи: {name}', line)
        asset = dict(path=name)
        if not path.is_file():
            issue('missing_figure', f'Нет файла: {name}', line, 'error')
        elif Image:
            try:
                with Image.open(path) as im:
                    width, height = im.size
                    im.verify()
                asset.update(width=width, height=height, width_mm_at_300ppi=round(width / 300 * 25.4, 2))
                if item and (item.get('width'), item.get('height')) != (width, height):
                    issue('dimension_mismatch', f'Размер отличается от manifest: {name}', line, 'error')
            except (OSError, ValueError) as error:
                issue('invalid_image', f'Не удалось прочитать {name}: {error}', line, 'error')
        rights_row = rights.get(name, {})
        if rights_row.get('status') not in ('cleared', 'author_confirmed'):
            issue('rights_unverified', f'Права требуют записи/подтверждения: {name}', line)
        assets.append(asset)
    for name in by_name.keys() - seen:
        issue('unused_asset', f'Не используется в рукописи: {name}')
    prose = FIGURE.sub('', text)
    prose = re.sub(r'^#{1,6}\s+', '', prose, flags=re.M)
    stats = dict(characters_with_spaces=len(text),
                 words_excluding_figure_markers=len(prose.split()),
                 yo_count=text.count('ё') + text.count('Ё'),
                 em_dash_count=text.count('—'), figure_count=len(assets),
                 errors=sum(i['severity'] == 'error' for i in issues),
                 warnings=sum(i['severity'] == 'warning' for i in issues))
    return dict(schema_version=1, source='manuscript/source.md',
                source_sha256=hashlib.sha256(raw).hexdigest(),
                word_count_method='Whitespace tokens; heading markers and full FIGURE markers excluded; title/author included.',
                stats=stats, assets=assets, issues=issues)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, help='Optional JSON report path; source never modified')
    args = parser.parse_args()
    result = audit(args.root)
    content = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content)
    print(json.dumps(result.get('stats', {}), ensure_ascii=False))
    for entry in result['issues']:
        print(f"{entry['severity']} {entry['code']} line={entry['line']}: {entry['message']}")
    return int(any(i['severity'] == 'error' for i in result['issues']))


if __name__ == '__main__':
    raise SystemExit(main())
