"""
TrafficLive - Grafo dirigido de la red vial REAL de Santa Cruz de la Sierra (datos de OpenStreetMap, licencia ODbL).

1) Convierte las vías principales descargadas con Overpass en un GrafoTrafico:
   - vértices = intersecciones (nodos OSM compartidos por dos o más vías) y extremos de vía
   - aristas  = tramos entre intersecciones; las vías con oneway=yes (o rotondas) generan una sola dirección
2) Mide Dijkstra frente a A* sobre la red real (misma metodología que benchmark.py).
3) Exporta una versión compacta del grafo para la página web.

Uso: python red_osm.py santa_cruz_vias.json resultados_osm.json red_santa_cruz.json
"""
import json
import random
import statistics
import sys
import time
from math import cos, radians

from grafo_trafico import GrafoTrafico

VELOCIDAD = {"motorway": 60, "trunk": 50, "primary": 40, "secondary": 35, "tertiary": 30}   # km/h
CENTRO = (-17.78363, -63.18213)                         # Plaza 24 de Septiembre
KM_LAT, KM_LON = 110.574, 111.320 * cos(radians(CENTRO[0]))


def a_metros(lat, lon):
    return (lon - CENTRO[1]) * KM_LON * 1000, (lat - CENTRO[0]) * KM_LAT * 1000


def construir(ruta_json):
    vias = [e for e in json.load(open(ruta_json, encoding="utf-8"))["elements"] if e["type"] == "way"]
    usos = {}
    for v in vias:
        for n in v["nodes"]:
            usos[n] = usos.get(n, 0) + 1

    tramos = []   # (u_osm, v_osm, geometria, km, minutos, nombre, sentido_unico)
    for v in vias:
        t = v.get("tags", {})
        clase = t["highway"].replace("_link", "")
        kmh = VELOCIDAD.get(clase, 30) if not t["highway"].endswith("_link") else 30
        ow = t.get("oneway", "no")
        unico = ow in ("yes", "1", "true", "-1") or t.get("junction") in ("roundabout", "circular")
        nodos, geom = v["nodes"], [(g["lat"], g["lon"]) for g in v["geometry"]]
        if ow == "-1":
            nodos, geom = nodos[::-1], geom[::-1]
        nombre = t.get("name") or t.get("ref") or "Vía sin nombre"
        inicio = 0
        for i in range(1, len(nodos)):
            if usos[nodos[i]] > 1 or i == len(nodos) - 1:
                seg = geom[inicio:i + 1]
                m = sum(((a_metros(*a)[0] - a_metros(*b)[0]) ** 2 + (a_metros(*a)[1] - a_metros(*b)[1]) ** 2) ** 0.5
                        for a, b in zip(seg, seg[1:]))
                if m > 0:
                    tramos.append((nodos[inicio], nodos[i], seg, m / 1000, (m / 1000) / kmh * 60, nombre, unico))
                inicio = i

    # componente fuertemente conexa más grande (para que toda ruta origen-destino exista)
    ady, inv = {}, {}
    for u, v, *_r, unico in tramos:
        for a, b in ((u, v),) + (() if unico else ((v, u),)):
            ady.setdefault(a, set()).add(b); inv.setdefault(b, set()).add(a)
            ady.setdefault(b, set()); inv.setdefault(a, set())
    orden, visto = [], set()
    for s in ady:                                   # Kosaraju iterativo
        if s in visto:
            continue
        pila = [(s, iter(ady[s]))]; visto.add(s)
        while pila:
            x, it = pila[-1]
            y = next(it, None)
            if y is None:
                orden.append(x); pila.pop()
            elif y not in visto:
                visto.add(y); pila.append((y, iter(ady[y])))
    comp, mejor = {}, []
    for s in reversed(orden):
        if s in comp:
            continue
        actual, pila = [s], [s]; comp[s] = s
        while pila:
            x = pila.pop()
            for y in inv[x]:
                if y not in comp:
                    comp[y] = s; actual.append(y); pila.append(y)
        if len(actual) > len(mejor):
            mejor = actual
    validos = set(mejor)

    g = GrafoTrafico()
    ids, coords = {}, []
    for u, v, seg, km, minutos, nombre, unico in tramos:
        if u not in validos or v not in validos:
            continue
        for osm, (lat, lon) in ((u, seg[0]), (v, seg[-1])):
            if osm not in ids:
                ids[osm] = len(ids); coords.append((lat, lon))
                g.agregar_interseccion(ids[osm], *a_metros(lat, lon))
        g.agregar_calle(ids[u], ids[v], minutos, doble_sentido=not unico)
    tramos_validos = [t for t in tramos if t[0] in validos and t[1] in validos]
    return g, ids, coords, tramos_validos


def medir(g, n_rutas=200, semilla=2026):
    rnd = random.Random(semilla)
    nodos = list(g.ady)
    td, ta, ed, ea, trec = [], [], [], [], []
    for _ in range(n_rutas):
        o, d = rnd.sample(nodos, 2)
        t0 = time.perf_counter(); camino, c1, e1 = g.dijkstra(o, d); td.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); _, c2, e2 = g.a_estrella(o, d); ta.append(time.perf_counter() - t0)
        assert abs(c1 - c2) < 1e-9
        ed.append(e1); ea.append(e2)
        if len(camino) > 2:                         # accidente en un tramo de la ruta (solo ese sentido) y recálculo
            u, v = camino[len(camino) // 2], camino[len(camino) // 2 + 1]
            t0 = time.perf_counter(); g.aplicar_reporte(u, v, "accidente"); g.a_estrella(o, d)
            trec.append(time.perf_counter() - t0); g.restaurar(u, v)
    return {
        "nodos": len(nodos), "aristas_dirigidas": sum(len(a) for a in g.ady.values()), "rutas": n_rutas,
        "dijkstra_ms": statistics.mean(td) * 1000, "a_estrella_ms": statistics.mean(ta) * 1000,
        "expandidos_dijkstra": statistics.mean(ed), "expandidos_a_estrella": statistics.mean(ea),
        "recalculo_ms": statistics.mean(trec) * 1000, "recalculo_max_ms": max(trec) * 1000,
    }


if __name__ == "__main__":
    g, ids, coords, tramos = construir(sys.argv[1])
    res = medir(g)
    res["tramos_sentido_unico"] = sum(1 for t in tramos if t[6])
    res["tramos"] = len(tramos)
    json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), indent=2)
    print(json.dumps(res, indent=1))

    # exportación compacta para la web
    nombres = sorted({t[5] for t in tramos})
    idx_nombre = {n: i for i, n in enumerate(nombres)}
    web = {
        "fuente": "© colaboradores de OpenStreetMap (ODbL)",
        "nodos": [[round(a, 5), round(b, 5)] for a, b in coords],
        "nombres": nombres,
        # u, v, km, minutos, nombre, sentido_unico, geometría intermedia [lat, lon, lat, lon, ...]
        "tramos": [[ids[u], ids[v], round(km, 4), round(mi, 4), idx_nombre[n], int(un),
                    [round(c, 5) for p in seg[1:-1] for c in p]] for u, v, seg, km, mi, n, un in tramos],
    }
    json.dump(web, open(sys.argv[3], "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print("web:", len(web["nodos"]), "nodos,", len(web["tramos"]), "tramos")
