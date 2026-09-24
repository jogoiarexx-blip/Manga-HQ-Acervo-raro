#!/usr/bin/env python3
"""Build the static catalog and small WebP covers from PDFs in story folders.

Usage: python3 tools/build-catalog.py
Requires: pip install pymupdf pillow
"""

import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
STORIES = [
    ('Batman - A Maldicao do Cavaleiro Branco', 'batman-maldicao-cavaleiro-branco',
     'Batman: A Maldição do Cavaleiro Branco', 'DC'),
    ('Batman - Cavaleiro Branco Apresenta Capuz Vermelho', 'batman-capuz-vermelho',
     'Batman: Cavaleiro Branco Apresenta Capuz Vermelho', 'DC'),
    ('Batman - Um Dia Ruim - Ras al Ghul', 'batman-um-dia-ruim-ras-al-ghul',
     "Batman: Um Dia Ruim - Ra's al Ghul", 'DC'),
    ('Hulk - Contra o Mundo', 'hulk-contra-o-mundo', 'Hulk: Contra o Mundo', 'Marvel'),
    ('O Batman que Ri', 'o-batman-que-ri', 'O Batman que Ri', 'DC'),
]


def url(path):
    return '/'.join(quote(part) for part in path.parts)


def number_and_title(folder, stem):
    if folder == 'Hulk - Contra o Mundo':
        match = re.search(r'Edicao\s+(\d+)$', stem, re.I)
        if not match:
            raise ValueError(f'Edição sem número: {stem}')
        issue = int(match.group(1))
        return issue, f'Hulk: Contra o Mundo #{issue}'
    if folder == 'O Batman que Ri' and 'Cavaleiro Sombrio' in stem:
        return None, 'O Batman que Ri: O Cavaleiro Sombrio #1'
    match = re.search(r'(?:#|\s)(\d+)(?:\s*\(\d{4}\))?$', stem)
    if not match:
        raise ValueError(f'Edição sem número: {stem}')
    issue = int(match.group(1))
    if folder == 'Batman - A Maldicao do Cavaleiro Branco':
        return issue, f'Batman: A Maldição do Cavaleiro Branco #{issue}'
    if folder == 'Batman - Um Dia Ruim - Ras al Ghul':
        return issue, "Batman: Um Dia Ruim - Ra's al Ghul"
    if folder == 'Batman - Cavaleiro Branco Apresenta Capuz Vermelho':
        return issue, f'Batman: Cavaleiro Branco Apresenta Capuz Vermelho #{issue}'
    return issue, f'O Batman que Ri #{issue}'


def cover_from_pdf(document, output):
    page = document[0]
    scale = min(1.0, 480 / page.rect.width)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    with Image.open(BytesIO(pix.tobytes('png'))) as image:
        image.save(output, 'WEBP', quality=80, method=6)


catalog = {
    'schemaVersion': 1,
    'name': 'Manga HQ Acervo Raro',
    'format': 'pdf',
    'supportedFormats': ['pdf'],
    'collections': [],
    'items': [],
}

for folder_name, collection_id, collection_title, publisher in STORIES:
    folder = ROOT / folder_name
    if not folder.is_dir():
        raise FileNotFoundError(folder)
    issues = []
    for pdf in sorted(folder.glob('*.pdf')):
        issue, title = number_and_title(folder_name, pdf.stem)
        cover = pdf.with_name(pdf.stem + '-cover.webp')
        with fitz.open(pdf) as document:
            if not document.page_count:
                raise ValueError(f'PDF vazio: {pdf}')
            if not cover.exists():
                cover_from_pdf(document, cover)
            pages = document.page_count
        unique = (str(issue) if issue is not None else 'especial-cavaleiro-sombrio')
        row = {
            'id': f'{collection_id}-{unique}',
            'title': title,
            'format': 'pdf',
            'file': url(pdf.relative_to(ROOT)),
            'cover': url(cover.relative_to(ROOT)),
            'size': pdf.stat().st_size,
            'pageCount': pages,
            'collectionId': collection_id,
            'collectionTitle': collection_title,
            'publisher': publisher,
        }
        if issue is not None:
            row['issue'] = issue
        issues.append(row)
    issues.sort(key=lambda item: (item.get('issue', 999), item['title']))
    catalog['collections'].append({
        'id': collection_id, 'title': collection_title,
        'publisher': publisher, 'issues': issues,
    })
    catalog['items'].extend(issues)

catalog['itemCount'] = len(catalog['items'])
(ROOT / 'catalogo.json').write_text(
    json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
)
print(f"Catálogo criado: {len(catalog['collections'])} histórias, {catalog['itemCount']} edições")
