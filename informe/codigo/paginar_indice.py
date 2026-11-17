"""Segunda pasada del índice: busca en el PDF la página de cada título (en orden) y guarda un JSON.
Uso: python paginar_indice.py informe.pdf informe_titulos.json salida_paginas.json"""
import json
import re
import sys

from pypdf import PdfReader

norm = lambda s: re.sub(r"\s+", "", s).lower()
paginas = [norm(p.extract_text() or "") for p in PdfReader(sys.argv[1]).pages]
titulos = json.load(open(sys.argv[2], encoding="utf-8"))

# el índice ocupa las páginas donde aparece "ÍNDICE" como título; se empieza a buscar después
inicio = next(i for i, t in enumerate(paginas) if t.startswith("índice") or "índice" in t[:40]) + 1
while inicio < len(paginas) and norm("INTRODUCCIÓN") not in paginas[inicio][:60]:
    inicio += 1

resultado, pagina = {}, 1
for t in titulos:
    clave = norm(t)[:40]
    if t in ("Identificadores ORCID de los autores", "Agradecimiento", "Resumen", "Abstract"):
        busca = range(1, len(paginas))
    else:
        busca = range(max(pagina, inicio), len(paginas))
    hallada = next((i for i in busca if clave in paginas[i]), None)
    if hallada is None:
        print("no encontrado:", t, file=sys.stderr)
        continue
    resultado[t] = hallada + 1                 # la carátula es la página 1
    if t not in ("Identificadores ORCID de los autores", "Agradecimiento", "Resumen", "Abstract"):
        pagina = hallada
json.dump(resultado, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(resultado), "de", len(titulos), "títulos paginados; total de páginas:", len(paginas))
