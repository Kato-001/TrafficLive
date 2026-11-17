"""
TrafficLive - Experimento de rendimiento (benchmark).

Variable independiente: estructura / algoritmo (Árbol B+ vs Lista enlazada; A* vs Dijkstra)
Variables dependientes: tiempo por operación (ms) y nodos expandidos.
Cada medición es el promedio de varias repeticiones con semilla fija (reproducible).
"""
import json
import random
import statistics
import sys
import time
from math import hypot

from arbol_bplus import ArbolBPlus, ListaEnlazada
from grafo_trafico import GrafoTrafico

SEMILLA = 2026
TAMANOS_REPORTES = [1_000, 5_000, 10_000, 50_000, 100_000]
TAMANOS_GRAFO = [100, 400, 1_000, 2_500, 5_000, 10_000]
CONSULTAS = 200
RUTAS = 40
INICIO_DIA = 1_767_225_600          # 01/01/2026 00:00 (timestamp Unix)
SEGUNDOS_30_DIAS = 30 * 24 * 3600
TIPOS = ["atasco_leve", "atasco_moderado", "atasco_severo", "accidente", "bache", "inundacion"]


def generar_reportes(n, rnd):
    reportes = []
    for i in range(n):
        reportes.append({
            "id": i,
            "lat": -17.78 + rnd.uniform(-0.06, 0.06),
            "lon": -63.18 + rnd.uniform(-0.06, 0.06),
            "timestamp": INICIO_DIA + rnd.randrange(SEGUNDOS_30_DIAS),
            "tipo": rnd.choice(TIPOS),
        })
    rnd.shuffle(reportes)
    return reportes


def medir(fn, repeticiones):
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        fn()
    return (time.perf_counter() - t0) * 1000 / repeticiones


def bench_reportes():
    filas = []
    for n in TAMANOS_REPORTES:
        rnd = random.Random(SEMILLA + n)
        reportes = generar_reportes(n, rnd)
        arbol_id, arbol_t, lista = ArbolBPlus(5), ArbolBPlus(5), ListaEnlazada()

        t0 = time.perf_counter()
        for r in reportes:
            arbol_id.insertar(r["id"], r)
            arbol_t.insertar((r["timestamp"], r["id"]), r)
        ins_bplus = (time.perf_counter() - t0) * 1000 / n

        t0 = time.perf_counter()
        for r in reportes:
            lista.insertar(r["id"], r)
        ins_lista = (time.perf_counter() - t0) * 1000 / n

        ids = [rnd.randrange(n) for _ in range(CONSULTAS)]
        # consulta por rango: 1 hora de reportes ("todos los reportes entre las 07:00 y 08:00")
        rangos = []
        for _ in range(CONSULTAS):
            ini = INICIO_DIA + rnd.randrange(SEGUNDOS_30_DIAS - 3600)
            rangos.append((ini, ini + 3600))

        it = iter(ids * 2)
        bus_bplus = medir(lambda: arbol_id.buscar(next(it)), CONSULTAS)
        rep_lista = CONSULTAS if n <= 10_000 else 40      # la lista es lenta: menos repeticiones
        it = iter(ids * 2)
        bus_lista = medir(lambda: lista.buscar(next(it)), rep_lista)

        it = iter(rangos * 2)
        k_prom = statistics.mean(len(arbol_t.buscar_rango((a, -1), (b, n))) for a, b in rangos[:50])
        ran_bplus = medir(lambda: (lambda a, b: arbol_t.buscar_rango((a, -1), (b, n)))(*next(it)), CONSULTAS)
        it = iter(rangos * 2)
        # en la lista se busca por timestamp recorriendo todos los nodos
        lista_t = ListaEnlazada()
        for r in reportes:
            lista_t.insertar(r["timestamp"], r)
        ran_lista = medir(lambda: (lambda a, b: lista_t.buscar_rango(a, b))(*next(it)), rep_lista)

        fila = {
            "n": n, "altura_bplus": arbol_id.altura(), "k_promedio": round(k_prom, 1),
            "insercion_bplus_ms": ins_bplus, "insercion_lista_ms": ins_lista,
            "busqueda_id_bplus_ms": bus_bplus, "busqueda_id_lista_ms": bus_lista,
            "rango_bplus_ms": ran_bplus, "rango_lista_ms": ran_lista,
        }
        filas.append(fila)
        print(json.dumps(fila), file=sys.stderr)
    return filas


def construir_grafo_ciudad(n_nodos, semilla=SEMILLA):
    """Cuadrícula que imita el damero del centro cruceño: cuadras de ~110 m,
    velocidades por tramo entre 15 y 50 km/h (avenidas cada 5 cuadras más rápidas)."""
    rnd = random.Random(semilla)
    lado = int(round(n_nodos ** 0.5))
    g = GrafoTrafico()
    cuadra = 110
    for f in range(lado):
        for c in range(lado):
            g.agregar_interseccion(f * lado + c, c * cuadra + rnd.uniform(-15, 15), f * cuadra + rnd.uniform(-15, 15))
    for f in range(lado):
        for c in range(lado):
            u = f * lado + c
            for v, avenida in ((u + 1, f % 5 == 0) if c + 1 < lado else (None, 0),
                               (u + lado, c % 5 == 0) if f + 1 < lado else (None, 0)):
                if v is None:
                    continue
                (x1, y1), (x2, y2) = g.coord[u], g.coord[v]
                kmh = rnd.uniform(35, 50) if avenida else rnd.uniform(15, 30)
                g.agregar_calle(u, v, hypot(x1 - x2, y1 - y2) / (kmh * 1000 / 60))
    return g


def bench_grafo():
    filas = []
    for n in TAMANOS_GRAFO:
        g = construir_grafo_ciudad(n)
        rnd = random.Random(SEMILLA + n)
        nodos = list(g.ady)
        pares = [tuple(rnd.sample(nodos, 2)) for _ in range(RUTAS)]
        td, ta, ed, ea = [], [], [], []
        for o, d in pares:
            t0 = time.perf_counter(); _, c1, e1 = g.dijkstra(o, d); td.append(time.perf_counter() - t0)
            t0 = time.perf_counter(); _, c2, e2 = g.a_estrella(o, d); ta.append(time.perf_counter() - t0)
            assert abs(c1 - c2) < 1e-9
            ed.append(e1); ea.append(e2)

        # recálculo ante un reporte: se bloquea un tramo de la ruta actual y se recalcula con A*
        trec = []
        for o, d in pares[:20]:
            camino, _, _ = g.a_estrella(o, d)
            if len(camino) < 3:
                continue
            u, v = camino[len(camino) // 2], camino[len(camino) // 2 + 1]
            t0 = time.perf_counter()
            g.aplicar_reporte(u, v, "accidente", bidireccional=True)   # así se midió en resultados.json
            g.a_estrella(o, d)
            trec.append(time.perf_counter() - t0)
            g.restaurar(u, v)

        tbfs = medir(lambda: g.propagar_congestion(rnd.choice(nodos), niveles=2), 200)
        fila = {
            "nodos": len(nodos), "aristas": sum(len(a) for a in g.ady.values()),
            "dijkstra_ms": statistics.mean(td) * 1000, "a_estrella_ms": statistics.mean(ta) * 1000,
            "expandidos_dijkstra": statistics.mean(ed), "expandidos_a_estrella": statistics.mean(ea),
            "recalculo_ms": statistics.mean(trec) * 1000, "recalculo_max_ms": max(trec) * 1000,
            "bfs_ms": tbfs,
        }
        filas.append(fila)
        print(json.dumps(fila), file=sys.stderr)
    return filas


if __name__ == "__main__":
    resultados = {
        "python": sys.version.split()[0],
        "reportes": bench_reportes(),
        "grafo": bench_grafo(),
    }
    with open(sys.argv[1] if len(sys.argv) > 1 else "resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2)
