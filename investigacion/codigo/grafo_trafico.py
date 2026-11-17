"""
TrafficLive - Grafo Pesado dirigido implementado desde cero.

  V = intersecciones (nodos con coordenadas x, y en metros)
  E = tramos de calle (aristas dirigidas, para modelar calles de un solo sentido)
  peso(u, v) = tiempo estimado de viaje en minutos = tiempo_base * factor_congestion
"""
import heapq
from collections import deque
from math import hypot, inf

# Incremento de tiempo (minutos) por tipo de incidente reportado
PENALIZACION = {
    "atasco_leve": 2,
    "atasco_moderado": 5,
    "atasco_severo": 10,
    "accidente": 15,
    "bloqueo": inf,
}

VELOCIDAD_MAXIMA_KMH = 60   # usada por la heurística de A* (debe ser admisible)


class GrafoTrafico:
    def __init__(self):
        self.ady = {}        # u -> {v: peso_actual}
        self.base = {}       # (u, v) -> tiempo_base
        self.coord = {}      # u -> (x, y)

    def agregar_interseccion(self, id_nodo, x, y):
        self.coord[id_nodo] = (x, y)
        self.ady.setdefault(id_nodo, {})

    def agregar_calle(self, origen, destino, tiempo_base, doble_sentido=True):
        self.ady[origen][destino] = tiempo_base
        self.base[(origen, destino)] = tiempo_base
        if doble_sentido:
            self.ady[destino][origen] = tiempo_base
            self.base[(destino, origen)] = tiempo_base

    # ------------------------------------------------------------ pesos dinámicos
    def aplicar_reporte(self, origen, destino, tipo, factor_confianza=1.0, bidireccional=False):
        """Incrementa el peso de la arista dirigida origen -> destino según el tipo de incidente.
        factor_confianza: 0 (reporte falso), 1 (normal), 1.5 (validado por la comunidad).
        bidireccional: True si el incidente afecta a ambos sentidos de circulación (p. ej., calle bloqueada
        de lado a lado); por defecto solo se penaliza el carril reportado, respetando el grafo dirigido."""
        incremento = PENALIZACION[tipo] * factor_confianza if factor_confianza else 0
        sentidos = ((origen, destino), (destino, origen)) if bidireccional else ((origen, destino),)
        for u, v in sentidos:
            if v in self.ady.get(u, {}):
                self.ady[u][v] = self.ady[u][v] + incremento

    def restaurar(self, origen, destino):
        for u, v in ((origen, destino), (destino, origen)):
            if (u, v) in self.base:
                self.ady[u][v] = self.base[(u, v)]

    # ------------------------------------------------------------ caminos mínimos
    def dijkstra(self, origen, destino):
        """Cola de prioridad (montículo binario): O((V + E) log V)."""
        dist = {origen: 0.0}
        previo = {}
        visitado = set()
        heap = [(0.0, origen)]
        expandidos = 0
        while heap:
            d, u = heapq.heappop(heap)
            if u in visitado:
                continue
            visitado.add(u)
            expandidos += 1
            if u == destino:
                break
            for v, w in self.ady[u].items():
                nd = d + w
                if nd < dist.get(v, inf):
                    dist[v] = nd
                    previo[v] = u
                    heapq.heappush(heap, (nd, v))
        return self._reconstruir(previo, origen, destino), dist.get(destino, inf), expandidos

    def heuristica(self, u, destino):
        """Distancia en línea recta / velocidad máxima -> minutos. Nunca sobreestima (admisible)."""
        (x1, y1), (x2, y2) = self.coord[u], self.coord[destino]
        metros = hypot(x1 - x2, y1 - y2)
        return metros / (VELOCIDAD_MAXIMA_KMH * 1000 / 60)

    def a_estrella(self, origen, destino):
        """A*: f(n) = g(n) + h(n). Mismo resultado que Dijkstra, explorando menos nodos."""
        g = {origen: 0.0}
        previo = {}
        cerrado = set()
        heap = [(self.heuristica(origen, destino), 0.0, origen)]
        expandidos = 0
        while heap:
            _, gu, u = heapq.heappop(heap)
            if u in cerrado:
                continue
            cerrado.add(u)
            expandidos += 1
            if u == destino:
                break
            for v, w in self.ady[u].items():
                ng = gu + w
                if ng < g.get(v, inf):
                    g[v] = ng
                    previo[v] = u
                    heapq.heappush(heap, (ng + self.heuristica(v, destino), ng, v))
        return self._reconstruir(previo, origen, destino), g.get(destino, inf), expandidos

    @staticmethod
    def _reconstruir(previo, origen, destino):
        if destino != origen and destino not in previo:
            return []
        camino = [destino]
        while camino[-1] != origen:
            camino.append(previo[camino[-1]])
        return camino[::-1]

    # ------------------------------------------------------------ mapa de calor
    def propagar_congestion(self, nodo_reportado, intensidad=1.0, niveles=2, decaimiento=0.5):
        """BFS por niveles: el nodo reportado recibe 'intensidad', sus vecinos
        intensidad*decaimiento, los vecinos de éstos intensidad*decaimiento^2, ...  O(V + E)."""
        calor = {nodo_reportado: intensidad}
        cola = deque([(nodo_reportado, 0)])
        while cola:
            u, nivel = cola.popleft()
            if nivel == niveles:
                continue
            for v in self.ady[u]:
                if v not in calor:
                    calor[v] = intensidad * decaimiento ** (nivel + 1)
                    cola.append((v, nivel + 1))
        return calor
