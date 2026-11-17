// Árbol B+ (misma lógica que informe/codigo/arbol_bplus.py), con registro del camino recorrido
// para poder animarlo en el visualizador.

function bisectLeft(a, x, cmp) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (cmp(a[m], x) < 0) lo = m + 1; else hi = m; }
  return lo;
}
function bisectRight(a, x, cmp) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (cmp(x, a[m]) < 0) hi = m; else lo = m + 1; }
  return lo;
}
const cmpDefault = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

let nextNodeId = 1;
class NodoBPlus {
  constructor(esHoja) {
    this.id = nextNodeId++;
    this.claves = [];
    this.hijos = [];       // hojas: valores; internos: nodos
    this.esHoja = esHoja;
    this.siguiente = null;
  }
}

class ArbolBPlus {
  constructor(orden = 5, cmp = cmpDefault) {
    this.orden = orden;
    this.maxClaves = orden - 1;
    this.cmp = cmp;
    this.raiz = new NodoBPlus(true);
    this.tamano = 0;
  }

  _buscarHoja(clave, camino) {
    let nodo = this.raiz;
    while (!nodo.esHoja) {
      if (camino) camino.push(nodo.id);
      nodo = nodo.hijos[bisectRight(nodo.claves, clave, this.cmp)];
    }
    if (camino) camino.push(nodo.id);
    return nodo;
  }

  buscar(clave) {
    const hoja = this._buscarHoja(clave);
    const i = bisectLeft(hoja.claves, clave, this.cmp);
    return i < hoja.claves.length && this.cmp(hoja.claves[i], clave) === 0 ? hoja.hijos[i] : undefined;
  }

  // Devuelve { valores, camino (nodos bajados), hojas (hojas recorridas) }
  buscarRango(inicio, fin) {
    const camino = [], hojas = [], valores = [];
    let hoja = this._buscarHoja(inicio, camino);
    let i = bisectLeft(hoja.claves, inicio, this.cmp);
    while (hoja) {
      hojas.push(hoja.id);
      for (; i < hoja.claves.length; i++) {
        if (this.cmp(hoja.claves[i], fin) > 0) return { valores, camino, hojas };
        valores.push(hoja.hijos[i]);
      }
      hoja = hoja.siguiente; i = 0;
    }
    return { valores, camino, hojas };
  }

  insertar(clave, valor) {
    const camino = [];
    let nodo = this.raiz;
    while (!nodo.esHoja) {
      const i = bisectRight(nodo.claves, clave, this.cmp);
      camino.push([nodo, i]);
      nodo = nodo.hijos[i];
    }
    let i = bisectLeft(nodo.claves, clave, this.cmp);
    if (i < nodo.claves.length && this.cmp(nodo.claves[i], clave) === 0) { nodo.hijos[i] = valor; return nodo.id; }
    nodo.claves.splice(i, 0, clave);
    nodo.hijos.splice(i, 0, valor);
    this.tamano++;
    const hojaInsertada = nodo.id;
    if (nodo.claves.length <= this.maxClaves) return hojaInsertada;

    let medio = nodo.claves.length >> 1;
    const nueva = new NodoBPlus(true);
    nueva.claves = nodo.claves.splice(medio);
    nueva.hijos = nodo.hijos.splice(medio);
    nueva.siguiente = nodo.siguiente; nodo.siguiente = nueva;
    let claveSube = nueva.claves[0], derecho = nueva;

    while (camino.length) {
      const [padre, j] = camino.pop();
      padre.claves.splice(j, 0, claveSube);
      padre.hijos.splice(j + 1, 0, derecho);
      if (padre.claves.length <= this.maxClaves) return hojaInsertada;
      medio = padre.claves.length >> 1;
      const nuevo = new NodoBPlus(false);
      claveSube = padre.claves[medio];
      nuevo.claves = padre.claves.splice(medio + 1);
      padre.claves.splice(medio);
      nuevo.hijos = padre.hijos.splice(medio + 1);
      derecho = nuevo;
    }
    const r = new NodoBPlus(false);
    r.claves = [claveSube];
    r.hijos = [this.raiz, derecho];
    this.raiz = r;
    return hojaInsertada;
  }

  altura() {
    let h = 1, n = this.raiz;
    while (!n.esHoja) { n = n.hijos[0]; h++; }
    return h;
  }

  niveles() {
    const out = [];
    let nivel = [this.raiz];
    while (nivel.length) {
      out.push(nivel);
      nivel = nivel[0].esHoja ? [] : nivel.flatMap((n) => n.hijos);
    }
    return out;
  }
}

window.ArbolBPlus = ArbolBPlus;
