"""
TrafficLive - Árbol B+ implementado desde cero (sin bibliotecas externas).

Se usa para indexar los reportes de tráfico:
  - índice primario:   clave = id del reporte
  - índice temporal:   clave = (timestamp, id)  -> permite búsquedas por rango de tiempo

Orden M = número máximo de hijos por nodo (por defecto M = 5).
  - Máximo de claves por nodo:            M - 1
  - Mínimo de claves (nodo no raíz):      ceil(M / 2) - 1
"""
from bisect import bisect_left, bisect_right
from math import ceil


class NodoBPlus:
    def __init__(self, es_hoja=False):
        self.claves = []
        self.hijos = []        # en hojas: valores asociados a cada clave; en internos: nodos hijos
        self.es_hoja = es_hoja
        self.siguiente = None  # enlace a la siguiente hoja (lista enlazada de hojas)


class ArbolBPlus:
    def __init__(self, orden=5):
        if orden < 3:
            raise ValueError("El orden mínimo de un Árbol B+ es 3")
        self.orden = orden
        self.max_claves = orden - 1
        self.min_claves = ceil(orden / 2) - 1
        self.raiz = NodoBPlus(es_hoja=True)
        self.tamano = 0

    # ------------------------------------------------------------------ búsqueda
    def _buscar_hoja(self, clave):
        nodo = self.raiz
        while not nodo.es_hoja:
            nodo = nodo.hijos[bisect_right(nodo.claves, clave)]
        return nodo

    def buscar(self, clave):
        """Búsqueda exacta: O(log n)."""
        hoja = self._buscar_hoja(clave)
        i = bisect_left(hoja.claves, clave)
        if i < len(hoja.claves) and hoja.claves[i] == clave:
            return hoja.hijos[i]
        return None

    def buscar_rango(self, inicio, fin):
        """Devuelve los valores con inicio <= clave <= fin: O(log n + k).
        Baja una sola vez hasta la hoja de 'inicio' y luego recorre las hojas enlazadas."""
        resultado = []
        hoja = self._buscar_hoja(inicio)
        i = bisect_left(hoja.claves, inicio)
        while hoja is not None:
            while i < len(hoja.claves):
                if hoja.claves[i] > fin:
                    return resultado
                resultado.append(hoja.hijos[i])
                i += 1
            hoja, i = hoja.siguiente, 0
        return resultado

    # ------------------------------------------------------------------ inserción
    def insertar(self, clave, valor):
        """Inserción con división (split) de nodos: O(log n)."""
        camino = []
        nodo = self.raiz
        while not nodo.es_hoja:
            i = bisect_right(nodo.claves, clave)
            camino.append((nodo, i))
            nodo = nodo.hijos[i]

        i = bisect_left(nodo.claves, clave)
        if i < len(nodo.claves) and nodo.claves[i] == clave:
            nodo.hijos[i] = valor          # clave existente: se actualiza el valor
            return
        nodo.claves.insert(i, clave)
        nodo.hijos.insert(i, valor)
        self.tamano += 1
        if len(nodo.claves) <= self.max_claves:
            return

        # split de hoja: la primera clave de la nueva hoja sube al padre (copia)
        medio = len(nodo.claves) // 2
        nueva = NodoBPlus(es_hoja=True)
        nueva.claves, nodo.claves = nodo.claves[medio:], nodo.claves[:medio]
        nueva.hijos, nodo.hijos = nodo.hijos[medio:], nodo.hijos[:medio]
        nueva.siguiente, nodo.siguiente = nodo.siguiente, nueva
        clave_sube, derecho = nueva.claves[0], nueva

        # propagar hacia arriba
        while camino:
            padre, i = camino.pop()
            padre.claves.insert(i, clave_sube)
            padre.hijos.insert(i + 1, derecho)
            if len(padre.claves) <= self.max_claves:
                return
            # split de nodo interno: la clave del medio sube (se mueve, no se copia)
            medio = len(padre.claves) // 2
            nuevo = NodoBPlus(es_hoja=False)
            clave_sube = padre.claves[medio]
            nuevo.claves, padre.claves = padre.claves[medio + 1:], padre.claves[:medio]
            nuevo.hijos, padre.hijos = padre.hijos[medio + 1:], padre.hijos[:medio + 1]
            derecho = nuevo

        # la raíz se dividió: el árbol crece un nivel
        nueva_raiz = NodoBPlus(es_hoja=False)
        nueva_raiz.claves = [clave_sube]
        nueva_raiz.hijos = [self.raiz, derecho]
        self.raiz = nueva_raiz

    # ------------------------------------------------------------------ eliminación
    def eliminar(self, clave):
        """Eliminación con redistribución (préstamo) o fusión de nodos: O(log n)."""
        if self._eliminar(self.raiz, clave):
            self.tamano -= 1
            if not self.raiz.es_hoja and len(self.raiz.claves) == 0:
                self.raiz = self.raiz.hijos[0]   # el árbol baja un nivel
            return True
        return False

    def _eliminar(self, nodo, clave):
        if nodo.es_hoja:
            i = bisect_left(nodo.claves, clave)
            if i < len(nodo.claves) and nodo.claves[i] == clave:
                del nodo.claves[i]
                del nodo.hijos[i]
                return True
            return False
        i = bisect_right(nodo.claves, clave)
        hijo = nodo.hijos[i]
        if not self._eliminar(hijo, clave):
            return False
        if len(hijo.claves) < self.min_claves:
            self._reparar(nodo, i)
        return True

    def _reparar(self, padre, i):
        hijo = padre.hijos[i]
        izq = padre.hijos[i - 1] if i > 0 else None
        der = padre.hijos[i + 1] if i + 1 < len(padre.hijos) else None

        if izq is not None and len(izq.claves) > self.min_claves:      # préstamo izquierdo
            if hijo.es_hoja:
                hijo.claves.insert(0, izq.claves.pop())
                hijo.hijos.insert(0, izq.hijos.pop())
                padre.claves[i - 1] = hijo.claves[0]
            else:
                hijo.claves.insert(0, padre.claves[i - 1])
                hijo.hijos.insert(0, izq.hijos.pop())
                padre.claves[i - 1] = izq.claves.pop()
        elif der is not None and len(der.claves) > self.min_claves:    # préstamo derecho
            if hijo.es_hoja:
                hijo.claves.append(der.claves.pop(0))
                hijo.hijos.append(der.hijos.pop(0))
                padre.claves[i] = der.claves[0]
            else:
                hijo.claves.append(padre.claves[i])
                hijo.hijos.append(der.hijos.pop(0))
                padre.claves[i] = der.claves.pop(0)
        else:                                                          # fusión
            j = i - 1 if izq is not None else i      # se fusionan hijos[j] y hijos[j+1]
            a, b = padre.hijos[j], padre.hijos[j + 1]
            if a.es_hoja:
                a.claves += b.claves
                a.hijos += b.hijos
                a.siguiente = b.siguiente
            else:
                a.claves += [padre.claves[j]] + b.claves
                a.hijos += b.hijos
            del padre.claves[j]
            del padre.hijos[j + 1]

    # ------------------------------------------------------------------ utilidades
    def altura(self):
        h, nodo = 1, self.raiz
        while not nodo.es_hoja:
            nodo, h = nodo.hijos[0], h + 1
        return h

    def recorrer(self):
        """Recorrido secuencial completo por las hojas enlazadas: O(n)."""
        nodo = self.raiz
        while not nodo.es_hoja:
            nodo = nodo.hijos[0]
        while nodo is not None:
            yield from zip(nodo.claves, nodo.hijos)
            nodo = nodo.siguiente


class ListaEnlazada:
    """Estructura de referencia (línea base) para comparar contra el Árbol B+."""

    class _Nodo:
        __slots__ = ("clave", "valor", "siguiente")

        def __init__(self, clave, valor, siguiente):
            self.clave, self.valor, self.siguiente = clave, valor, siguiente

    def __init__(self):
        self.cabeza = None
        self.tamano = 0

    def insertar(self, clave, valor):          # O(1): inserción al inicio
        self.cabeza = self._Nodo(clave, valor, self.cabeza)
        self.tamano += 1

    def buscar(self, clave):                   # O(n)
        nodo = self.cabeza
        while nodo is not None:
            if nodo.clave == clave:
                return nodo.valor
            nodo = nodo.siguiente
        return None

    def buscar_rango(self, inicio, fin):       # O(n): debe revisar todos los nodos
        resultado = []
        nodo = self.cabeza
        while nodo is not None:
            if inicio <= nodo.clave <= fin:
                resultado.append(nodo.valor)
            nodo = nodo.siguiente
        return resultado
