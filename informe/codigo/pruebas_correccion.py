"""Pruebas de corrección: el Árbol B+ y A* se comparan contra resultados de referencia."""
import random
from arbol_bplus import ArbolBPlus
from grafo_trafico import GrafoTrafico
from benchmark import construir_grafo_ciudad


def probar_bplus(orden, n_ops=20000, semilla=1):
    rnd = random.Random(semilla)
    arbol, ref = ArbolBPlus(orden), {}
    for _ in range(n_ops):
        k = rnd.randint(0, 3000)
        if rnd.random() < 0.65:
            arbol.insertar(k, k * 10); ref[k] = k * 10
        else:
            assert arbol.eliminar(k) == (k in ref); ref.pop(k, None)
    assert arbol.tamano == len(ref)
    assert [c for c, _ in arbol.recorrer()] == sorted(ref)
    for k in range(0, 3001, 7):
        assert arbol.buscar(k) == ref.get(k)
    a, b = 500, 1500
    assert arbol.buscar_rango(a, b) == [ref[k] * 1 for k in sorted(ref) if a <= k <= b]


def probar_grafo():
    g = construir_grafo_ciudad(900, semilla=3)
    rnd = random.Random(5)
    nodos = list(g.ady)
    for _ in range(100):
        o, d = rnd.sample(nodos, 2)
        _, c1, _ = g.dijkstra(o, d)
        _, c2, _ = g.a_estrella(o, d)
        assert abs(c1 - c2) < 1e-9, (c1, c2)
    # un bloqueo en la ruta obliga a recalcular por otro camino
    camino, costo, _ = g.a_estrella(0, 899)
    u, v = camino[len(camino) // 2], camino[len(camino) // 2 + 1]
    g.aplicar_reporte(u, v, "bloqueo")
    nuevo, costo2, _ = g.a_estrella(0, 899)
    assert (u, v) not in zip(nuevo, nuevo[1:]) and costo2 >= costo
    # el reporte es dirigido: solo penaliza u -> v, salvo que se indique bidireccional=True
    g.restaurar(u, v)
    base_vu = g.ady[v][u]
    g.aplicar_reporte(u, v, "atasco_severo")
    assert g.ady[v][u] == base_vu and g.ady[u][v] > g.base[(u, v)]
    g.restaurar(u, v)
    g.aplicar_reporte(u, v, "atasco_severo", bidireccional=True)
    assert g.ady[v][u] > base_vu
    # un reporte marcado como falso (confianza 0) no altera el peso
    g.restaurar(u, v)
    antes = g.ady[u][v]
    g.aplicar_reporte(u, v, "accidente", factor_confianza=0)
    assert g.ady[u][v] == antes


if __name__ == "__main__":
    for orden in (3, 4, 5, 8, 32):
        probar_bplus(orden)
    probar_grafo()
    print("Todas las pruebas de corrección pasaron.")
