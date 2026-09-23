# Manga HQ Acervo Raro

Este repositório contém PDFs separados por história e um `catalogo.json` consumido pelo Manga HQ Hub.

## Adicionar uma edição

1. Coloque o PDF na pasta da história correspondente.
2. Execute `python3 -m pip install pymupdf pillow` e `python3 tools/build-catalog.py`.
3. Confira a capa WebP e o novo item em `catalogo.json`; publique os arquivos juntos.

O catálogo usa caminhos relativos para que o site e o leitor encontrem PDFs e capas no mesmo endereço do acervo.
