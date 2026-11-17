"""Genera las figuras del informe a partir de resultados.json."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AZUL, NARANJA, GRIS, TINTA = "#1f5fa8", "#e07a1f", "#8a8f98", "#1d2430"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#c9ced6",
    "axes.labelcolor": TINTA, "xtick.color": TINTA, "ytick.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e6e9ee", "grid.linewidth": 0.8, "savefig.dpi": 200,
})

res = json.load(open(sys.argv[1], encoding="utf-8"))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
R, G = res["reportes"], res["grafo"]


def linea(ax, x, y, color, etiqueta, marcador="o"):
    ax.plot(x, y, color=color, marker=marcador, lw=2, ms=5)
    ax.annotate(etiqueta, (x[-1], y[-1]), xytext=(6, 0), textcoords="offset points",
                color=color, fontweight="bold", va="center")


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(os.path.join(out, nombre), bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- Figura: búsqueda por ID y por rango
for clave_b, clave_l, nombre, titulo in (
    ("busqueda_id_bplus_ms", "busqueda_id_lista_ms", "fig_busqueda_id.png", "Búsqueda de un reporte por ID"),
    ("rango_bplus_ms", "rango_lista_ms", "fig_busqueda_rango.png", "Búsqueda por rango de tiempo (1 hora)"),
):
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = [r["n"] for r in R]
    linea(ax, x, [r[clave_l] for r in R], NARANJA, "Lista enlazada  O(n)", "s")
    linea(ax, x, [r[clave_b] for r in R], AZUL, "Árbol B+")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Número de reportes almacenados (escala log)")
    ax.set_ylabel("Tiempo por consulta en ms (escala log)")
    ax.set_title(titulo, loc="left", fontweight="bold", color=TINTA)
    ax.set_xlim(right=x[-1] * 6)
    guardar(fig, nombre)

# ---------------------------------------------------------------- Figura: Dijkstra vs A*
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
x = [g["nodos"] for g in G]
linea(a1, x, [g["dijkstra_ms"] for g in G], NARANJA, "Dijkstra", "s")
linea(a1, x, [g["a_estrella_ms"] for g in G], AZUL, "A*")
a1.set_xlabel("Intersecciones (nodos) del grafo"); a1.set_ylabel("Tiempo por ruta (ms)")
a1.set_title("Tiempo de cálculo de ruta", loc="left", fontweight="bold", color=TINTA)
a1.set_xlim(right=x[-1] * 1.25)
linea(a2, x, [g["expandidos_dijkstra"] for g in G], NARANJA, "Dijkstra", "s")
linea(a2, x, [g["expandidos_a_estrella"] for g in G], AZUL, "A*")
a2.set_xlabel("Intersecciones (nodos) del grafo"); a2.set_ylabel("Nodos expandidos (promedio)")
a2.set_title("Trabajo realizado por búsqueda", loc="left", fontweight="bold", color=TINTA)
a2.set_xlim(right=x[-1] * 1.25)
guardar(fig, "fig_dijkstra_vs_aestrella.png")

# ---------------------------------------------------------------- Figura: recálculo
fig, ax = plt.subplots(figsize=(6.4, 3.4))
linea(ax, x, [g["recalculo_max_ms"] for g in G], GRIS, "peor caso", "^")
linea(ax, x, [g["recalculo_ms"] for g in G], AZUL, "promedio")
ax.axhline(100, color="#c0392b", ls="--", lw=1.2)
ax.text(x[0], 104, "umbral de respuesta inmediata: 100 ms", color="#c0392b", fontsize=9)
ax.set_ylim(0, 120); ax.set_xlim(right=x[-1] * 1.25)
ax.set_xlabel("Intersecciones (nodos) del grafo"); ax.set_ylabel("ms")
ax.set_title("Recálculo de ruta tras un reporte de accidente (A*)", loc="left", fontweight="bold", color=TINTA)
guardar(fig, "fig_recalculo.png")


# ---------------------------------------------------------------- Diagrama: Árbol B+ con hojas enlazadas
def caja(ax, x, y, claves, ancho_celda=0.98, alto=0.5, color=AZUL, relleno="#eaf1fb"):
    w = ancho_celda * len(claves)
    ax.add_patch(FancyBboxPatch((x - w / 2, y - alto / 2), w, alto, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc=relleno, ec=color, lw=1.6))
    for i, k in enumerate(claves):
        cx = x - w / 2 + ancho_celda * (i + 0.5)
        ax.text(cx, y, k, ha="center", va="center", fontsize=8.5, color=TINTA, fontweight="bold")
        if i:
            ax.plot([x - w / 2 + ancho_celda * i] * 2, [y - alto / 2, y + alto / 2], color=color, lw=1)
    return x - w / 2, x + w / 2


fig, ax = plt.subplots(figsize=(11, 4.6))
ax.set_xlim(0, 19.6); ax.set_ylim(0, 6.4); ax.axis("off"); ax.grid(False)
caja(ax, 9.5, 5.6, ["07:30"], color=TINTA, relleno="#f1f3f6")
ax.text(10.3, 5.6, "raíz (solo claves guía)", va="center", fontsize=9, color=GRIS)
internos = [(4.3, ["07:05", "07:15"]), (14.7, ["07:45", "08:05"])]
for xi, ks in internos:
    caja(ax, xi, 4.0, ks, color=TINTA, relleno="#f1f3f6")
    ax.annotate("", (xi, 4.27), (9.5, 5.33), arrowprops=dict(arrowstyle="-|>", color=GRIS, lw=1.2))
hojas = [(1.4, ["06:50", "07:00"]), (4.3, ["07:05", "07:10"]), (7.6, ["07:15", "07:20", "07:25"]),
         (11.4, ["07:30", "07:40"]), (14.7, ["07:45", "07:55", "08:00"]), (18.0, ["08:05", "08:20"])]
bordes = []
for j, (xh, ks) in enumerate(hojas):
    bordes.append(caja(ax, xh, 1.9, ks, color=AZUL))
    padre = internos[0][0] if j < 3 else internos[1][0]
    ax.annotate("", (xh, 2.17), (padre + (j % 3 - 1) * 0.9, 3.73),
                arrowprops=dict(arrowstyle="-|>", color=GRIS, lw=1.1))
    ax.text(xh, 1.35, "reportes R" + "".join(str(j * 3 + i + 1) + "," for i in range(len(ks)))[:-1],
            ha="center", fontsize=7.5, color=GRIS)
for (a, b), (c, d) in zip(bordes, bordes[1:]):
    ax.annotate("", (c - 0.02, 1.9), (b + 0.02, 1.9),
                arrowprops=dict(arrowstyle="-|>", color=NARANJA, lw=2))
# consulta por rango 07:10 - 07:45
ax.annotate("", (4.3, 2.65), (4.3, 3.6), arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=2.2, ls="--"))
ax.text(0.2, 0.55, "Consulta \"reportes entre 07:10 y 07:45\": 1) bajar de la raíz a la hoja de 07:10 → O(log n);  "
        "2) avanzar por los enlaces de hojas (naranja) hasta pasar 07:45 → O(k).",
        fontsize=8.5, color=TINTA)
ax.text(9.8, 6.25, "Árbol B+ de orden M = 5 indexado por hora del reporte", ha="center",
        fontsize=11, fontweight="bold", color=TINTA)
guardar(fig, "fig_bplus_hojas.png")

# ---------------------------------------------------------------- Diagrama: arquitectura
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.set_xlim(0, 20); ax.set_ylim(0, 10.4); ax.axis("off"); ax.grid(False)


def bloque(x, y, w, h, titulo, sub, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc="white", ec=color, lw=1.8))
    ax.text(x + w / 2, y + h - 0.42, titulo, ha="center", va="center", fontweight="bold", color=color, fontsize=10)
    ax.text(x + w / 2, y + h / 2 - 0.25, sub, ha="center", va="center", fontsize=8.3, color=TINTA, linespacing=1.4)


def flecha(a, b, texto=""):
    ax.annotate("", b, a, arrowprops=dict(arrowstyle="-|>", color=GRIS, lw=1.5))
    if texto:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.3, texto, ha="center", fontsize=8, color=GRIS)


bloque(0.4, 7.4, 5.6, 2.4, "Cliente web / móvil", "Leaflet + OpenStreetMap\nformulario de reporte con foto\ncompresión de imagen (Canvas)", TINTA)
bloque(7.2, 7.4, 5.6, 2.4, "Servidor (API REST)", "Python / Flask\nrecibe reportes y votos\nexpone rutas y mapa de calor", AZUL)
bloque(14.0, 7.4, 5.6, 2.4, "Fuentes externas", "Waze for Cities (convenio GAMSCS)\ncapa visual Google Traffic\n(contexto, no datos crudos)", GRIS)
bloque(0.4, 2.2, 4.4, 3.6, "Árbol B+ (propio)", "índice por id\níndice por (timestamp, id)\nM = 5\nconsultas por rango", AZUL)
bloque(5.3, 2.2, 4.4, 3.6, "Grafo pesado (propio)", "V = intersecciones\nE = tramos de calle\nDijkstra · A* · BFS\npesos dinámicos", AZUL)
bloque(10.2, 2.2, 4.4, 3.6, "Base de datos", "SQLite / PostgreSQL\npersistencia de reportes\ny usuarios", GRIS)
bloque(15.1, 2.2, 4.5, 3.6, "Almacenamiento\nde imágenes", "Firebase Storage / S3\nsolo la URL se guarda\nen el Árbol B+", GRIS)
flecha((6.0, 8.6), (7.2, 8.6), "HTTPS")
flecha((14.0, 8.6), (12.8, 8.6))
for xc in (2.6, 7.5, 12.4, 17.35):
    flecha((10.0, 7.4), (xc, 5.8))
ax.text(10, 1.2, "Flujo: reporte → se indexa en el Árbol B+ → se ubica la arista más cercana → sube su peso en el grafo → "
        "A* recalcula la ruta → BFS actualiza el mapa de calor", ha="center", fontsize=8.8, color=TINTA, style="italic")
ax.text(10, 10.15, "Arquitectura de TrafficLive", ha="center", fontsize=11.5, fontweight="bold", color=TINTA)
guardar(fig, "fig_arquitectura.png")
print("Figuras generadas en", out)
