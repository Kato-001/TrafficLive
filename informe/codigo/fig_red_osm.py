"""Figura de la red vial real de Santa Cruz (OpenStreetMap) usada como grafo dirigido.
Uso: python fig_red_osm.py ../../pagina-web/data/red_santa_cruz.json ../figuras/fig_red_osm.png"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

red = json.load(open(sys.argv[1], encoding="utf-8"))
nodos = red["nodos"]
uno, doble = [], []
for u, v, km, mi, nom, unico, geom in red["tramos"]:
    pts = [nodos[u]] + [geom[i:i + 2] for i in range(0, len(geom), 2)] + [nodos[v]]
    (uno if unico else doble).append([(lon, lat) for lat, lon in pts])

fig, ax = plt.subplots(figsize=(7.5, 7.5))
ax.add_collection(LineCollection(doble, colors="#e07a1f", linewidths=1.1, label="Doble sentido (2 aristas dirigidas)"))
ax.add_collection(LineCollection(uno, colors="#1f5fa8", linewidths=0.7, label="Un solo sentido (1 arista dirigida)"))
ax.scatter([lon for lat, lon in nodos], [lat for lat, lon in nodos], s=1.2, color="#1d2430", zorder=3, label="Intersecciones")
ax.plot(-63.18213, -17.78363, marker="*", color="#d9534f", ms=14, zorder=4, label="Plaza 24 de Septiembre")
ax.autoscale(); ax.set_aspect(1 / 0.9525)            # corrección por latitud (cos 17,8°)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values():
    s.set_color("#c9ced6")
ax.legend(loc="lower left", fontsize=8.5, frameon=True)
ax.set_title(f"Red vial principal de Santa Cruz de la Sierra: {len(nodos):,} intersecciones".replace(",", "."),
             loc="left", fontweight="bold", fontsize=11)
fig.text(0.01, 0.005, "Datos: © colaboradores de OpenStreetMap (ODbL)", fontsize=7.5, color="#6b7280")
fig.savefig(sys.argv[2], dpi=200, bbox_inches="tight", facecolor="white")
print("ok", sys.argv[2])
