// TrafficLive - demo interactiva sobre la red vial REAL de Santa Cruz de la Sierra
// (vías principales de OpenStreetMap convertidas en un grafo pesado dirigido por informe/codigo/red_osm.py).

const PLAZA = [-17.78363, -63.18213];
const VMAX = 60;   // km/h: velocidad máxima del grafo -> heurística admisible de A*
const TIPOS = {
  atasco_leve: { nombre: "Atasco leve", min: 2, color: "#e9b949", intensidad: 0.35 },
  atasco_moderado: { nombre: "Atasco moderado", min: 5, color: "#e48a2a", intensidad: 0.55 },
  atasco_severo: { nombre: "Atasco severo", min: 10, color: "#d9534f", intensidad: 0.8 },
  accidente: { nombre: "Accidente", min: 15, color: "#c0392b", intensidad: 0.95 },
  bloqueo: { nombre: "Calle bloqueada", min: Infinity, color: "#5b2333", intensidad: 1 },
};
const $ = (id) => document.getElementById(id);

// ------------------------------------------------------------------ geometría
const KM_LAT = 110.574, KM_LNG = 111.32 * Math.cos((PLAZA[0] * Math.PI) / 180);
const toKm = ([lat, lng]) => [(lng - PLAZA[1]) * KM_LNG, (lat - PLAZA[0]) * KM_LAT];
const distKm = (a, b) => { const [x1, y1] = toKm(a), [x2, y2] = toKm(b); return Math.hypot(x1 - x2, y1 - y2); };

// ------------------------------------------------------------------ montículo binario
class Heap {
  constructor() { this.a = []; }
  get size() { return this.a.length; }
  push(x) { const a = this.a; a.push(x); let i = a.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (a[p][0] <= a[i][0]) break; [a[p], a[i]] = [a[i], a[p]]; i = p; } }
  pop() { const a = this.a, top = a[0], last = a.pop();
    if (a.length) { a[0] = last; let i = 0;
      for (;;) { const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < a.length && a[l][0] < a[m][0]) m = l;
        if (r < a.length && a[r][0] < a[m][0]) m = r;
        if (m === i) break; [a[m], a[i]] = [a[i], a[m]]; i = m; } }
    return top; }
}

// ------------------------------------------------------------------ estado
let nodos = [];      // [lat, lng]
let tramos = [];     // {id, u, v, km, base, nombre, unico, puntos}
let aristas = [];    // aristas dirigidas {id, tramo, u, v, base, peso}
let ady = [];        // ady[u] = [arista]
let porTramo = [];   // porTramo[t] = [arista u->v, arista v->u?]

function cargarRed(red) {
  nodos = red.nodos;
  X = new Float64Array(nodos.length); Y = new Float64Array(nodos.length);
  nodos.forEach((p, i) => { [X[i], Y[i]] = toKm(p); });
  ady = nodos.map(() => []);
  red.tramos.forEach(([u, v, km, min, iNombre, unico, geom], id) => {
    const puntos = [nodos[u]];
    for (let i = 0; i < geom.length; i += 2) puntos.push([geom[i], geom[i + 1]]);
    puntos.push(nodos[v]);
    const t = { id, u, v, km, base: min, nombre: red.nombres[iNombre], unico: !!unico, puntos };
    tramos.push(t);
    const dirs = [[u, v]];
    if (!unico) dirs.push([v, u]);
    porTramo[id] = dirs.map(([a, b]) => {
      const e = { id: aristas.length, tramo: id, u: a, v: b, base: min, peso: min };
      aristas.push(e); ady[a].push(e);
      return e;
    });
  });
}

// coordenadas en km precalculadas: la heurística se evalúa miles de veces por búsqueda
let X, Y;
const heuristica = (u, d) => (Math.hypot(X[u] - X[d], Y[u] - Y[d]) / VMAX) * 60;

// usarHeuristica=false -> Dijkstra; true -> A*
function caminoMinimo(origen, destino, usarHeuristica) {
  const n = nodos.length, g = new Float64Array(n).fill(Infinity), previo = new Int32Array(n).fill(-1);
  const cerrado = new Uint8Array(n);
  const h = usarHeuristica ? (u) => heuristica(u, destino) : () => 0;
  const heap = new Heap();
  g[origen] = 0; heap.push([h(origen), origen]);
  let expandidos = 0;
  while (heap.size) {
    const [, u] = heap.pop();
    if (cerrado[u]) continue;
    cerrado[u] = 1; expandidos++;
    if (u === destino) break;
    for (const e of ady[u]) {
      const ng = g[u] + e.peso;
      if (ng < g[e.v]) { g[e.v] = ng; previo[e.v] = e.id; heap.push([ng + h(e.v), e.v]); }
    }
  }
  if (g[destino] === Infinity) return { costo: Infinity, aristas: [], expandidos };
  const ruta = [];
  for (let x = destino; x !== origen; x = aristas[previo[x]].u) ruta.push(aristas[previo[x]]);
  return { costo: g[destino], aristas: ruta.reverse(), expandidos };
}

// BFS por niveles sobre el grafo (sin importar el sentido): la congestión se desborda a las calles vecinas
function propagarCongestion(nodo, intensidad, niveles = 2, decaimiento = 0.5) {
  const calor = new Map([[nodo, intensidad]]);
  const cola = [[nodo, 0]];
  while (cola.length) {
    const [u, nivel] = cola.shift();
    if (nivel === niveles) continue;
    for (const e of ady[u]) if (!calor.has(e.v)) {
      calor.set(e.v, intensidad * decaimiento ** (nivel + 1));
      cola.push([e.v, nivel + 1]);
    }
  }
  return calor;
}

// ------------------------------------------------------------------ reportes (Árbol B+ con doble indexación)
const indicePorTiempo = new ArbolBPlus(5, (a, b) => a[0] - b[0] || a[1] - b[1]);   // clave = (minuto del día, id)
const indicePorId = new ArbolBPlus(5);                                             // clave = id
const reportes = [];   // reportes activos
let siguienteId = 1;

function cargarHistorial() {     // historial simulado del día para las consultas por rango
  let s = 7;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const tipos = Object.keys(TIPOS).filter((t) => t !== "bloqueo");
  for (let i = 0; i < 400; i++) {
    const pico = [7.5, 13, 19][Math.floor(rnd() * 3)];
    const hora = rnd() < 0.7 ? pico + (rnd() - 0.5) * 2.4 : 6 + rnd() * 16;
    const t = tramos[Math.floor(rnd() * tramos.length)];
    const r = { id: siguienteId++, minuto: Math.round(hora * 60), tipo: tipos[Math.floor(rnd() * tipos.length)], calle: t.nombre };
    indicePorTiempo.insertar([r.minuto, r.id], r);
    indicePorId.insertar(r.id, r);
  }
}

function factorConfianza(r) {
  const total = r.up + r.down;
  if (total >= 3 && r.down / total > 0.7) return 0;
  if (total >= 3 && r.up / total > 0.7) return 1.5;
  return 1;
}

function recalcularPesos() {
  for (const e of aristas) e.peso = e.base;
  for (const r of reportes) {
    const f = factorConfianza(r);
    if (f === 0) continue;
    for (const e of r.aristas) {
      const ar = aristas[e];
      ar.peso = TIPOS[r.tipo].min === Infinity ? Infinity : ar.peso + TIPOS[r.tipo].min * f;
    }
  }
}

// ------------------------------------------------------------------ mapa
const mapa = L.map("mapa", { preferCanvas: true, scrollWheelZoom: false, zoomSnap: 0.5 }).setView(PLAZA, 13);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19, className: "tiles-suaves",
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">colaboradores de OpenStreetMap</a>',
}).addTo(mapa);
const lienzo = L.canvas({ padding: 0.3 });
const capaCalles = L.layerGroup().addTo(mapa);
const capaRuta = L.layerGroup().addTo(mapa);
const capaMarcas = L.layerGroup().addTo(mapa);
let capaCalor = null;
let lineas = [];

function colorTramo(t) {
  const es = porTramo[t.id];
  const r = Math.max(...es.map((e) => e.peso / e.base));
  if (!isFinite(r)) return ["#5b2333", 5, 0.95];
  return r < 1.15 ? ["#8794a8", 2, 0.45] : r < 2 ? ["#e9a23b", 4.5, 0.95] : ["#d9534f", 5, 0.95];
}
function pintarCalles() {
  tramos.forEach((t, i) => { const [c, w, o] = colorTramo(t); lineas[i].setStyle({ color: c, weight: w, opacity: o }); });
}
function pintarCalor() {
  if (capaCalor) mapa.removeLayer(capaCalor);
  const calor = new Map();
  for (const r of reportes) {
    const f = factorConfianza(r);
    if (!f) continue;
    const t = tramos[r.tramo];
    for (const extremo of [t.u, t.v])
      for (const [n, c] of propagarCongestion(extremo, TIPOS[r.tipo].intensidad * Math.min(f, 1.2), 3))
        calor.set(n, Math.min(1, (calor.get(n) || 0) + c));
  }
  capaCalor = L.heatLayer([...calor].map(([n, c]) => [...nodos[n], c]), {
    radius: 28, blur: 22, maxZoom: 15, minOpacity: 0.25,
    gradient: { 0.2: "#f4d35e", 0.5: "#e9a23b", 0.8: "#d9534f", 1: "#7a1f2b" },
  }).addTo(mapa);
}

// ------------------------------------------------------------------ ruta
let origen, destino, rutaAnterior = null;
const iconoPin = (txt, color) => L.divIcon({ className: "pin", html: `<span style="background:${color}">${txt}</span>`, iconSize: [28, 28], iconAnchor: [14, 14] });
const nodoCercano = (ll) => { let m = 0, dm = Infinity; nodos.forEach((p, i) => { const d = distKm(p, ll); if (d < dm) { dm = d; m = i; } }); return m; };

function dibujarRuta(guardarAnterior) {
  capaRuta.clearLayers();
  const t0 = performance.now();
  const a = caminoMinimo(origen, destino, true);
  const tA = performance.now() - t0;
  const d = caminoMinimo(origen, destino, false);
  if (guardarAnterior && rutaAnterior)
    rutaAnterior.forEach((e) => L.polyline(puntosArista(e), { color: "#1d2430", weight: 4, opacity: 0.5, dashArray: "4 8", renderer: lienzo }).addTo(capaRuta));
  a.aristas.forEach((e) => L.polyline(puntosArista(e), { color: "#1f5fa8", weight: 7, opacity: 0.92, renderer: lienzo }).addTo(capaRuta));
  capaMarcas.clearLayers();
  L.marker(nodos[origen], { icon: iconoPin("A", "#1f8a4c") }).addTo(capaMarcas);
  L.marker(nodos[destino], { icon: iconoPin("B", "#1f5fa8") }).addTo(capaMarcas);
  rutaAnterior = a.aristas;
  a.ms = tA;
  const km = a.aristas.reduce((s, e) => s + tramos[e.tramo].km, 0);
  $("st-costo").textContent = isFinite(a.costo) ? a.costo.toFixed(1) + " min" : "sin ruta";
  $("st-km").textContent = km.toFixed(1) + " km";
  $("st-astar").textContent = a.expandidos.toLocaleString("es-BO");
  $("st-dijkstra").textContent = d.expandidos.toLocaleString("es-BO");
  $("st-ms").textContent = `${tA.toFixed(1)} ms`;
  const calles = [];
  a.aristas.forEach((e) => { const n = tramos[e.tramo].nombre; if (calles[calles.length - 1] !== n) calles.push(n); });
  $("st-calles").textContent = calles.filter((c) => c !== "Vía sin nombre").join(" → ") || "—";
  return a;
}
function puntosArista(e) { const t = tramos[e.tramo]; return e.u === t.u ? t.puntos : [...t.puntos].reverse(); }

// ------------------------------------------------------------------ interacción
let modo = "ruta", paso = 0, fotoPendiente = null;
function distPuntoSegmento(p, a, b) {
  const [px, py] = toKm(p), [ax, ay] = toKm(a), [bx, by] = toKm(b);
  const dx = bx - ax, dy = by - ay, t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}
function tramoCercano(ll) {
  let mejor = null, dmin = Infinity;
  for (const t of tramos) for (let i = 1; i < t.puntos.length; i++) {
    const d = distPuntoSegmento(ll, t.puntos[i - 1], t.puntos[i]);
    if (d < dmin) { dmin = d; mejor = t; }
  }
  return dmin < 0.15 ? mejor : null;
}
const minutoActual = () => { const d = new Date(); return d.getHours() * 60 + d.getMinutes(); };
const hhmm = (m) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

// Sentido afectado: si el tramo está en la ruta actual, el de la ruta; si no, el primero. "Ambos" = bidireccional.
function aristasAfectadas(t, bidireccional) {
  const es = porTramo[t.id];
  if (bidireccional || es.length === 1) return es.map((e) => e.id);
  const enRuta = (rutaAnterior || []).find((e) => e.tramo === t.id);
  return [(enRuta || es[0]).id];
}

function crearReporte(t, tipo, foto, bidireccional) {
  const r = { id: siguienteId++, minuto: minutoActual(), tipo, tramo: t.id, calle: t.nombre, up: 0, down: 0, foto,
              aristas: aristasAfectadas(t, bidireccional) };
  const t0 = performance.now();
  indicePorTiempo.insertar([r.minuto, r.id], r);
  indicePorId.insertar(r.id, r);
  const tIns = performance.now() - t0;
  reportes.push(r);
  recalcularPesos(); pintarCalles(); pintarCalor();
  const tRuta = dibujarRuta(true).ms;     // solo el tiempo de A*, sin contar el dibujo
  const sentido = t.unico ? "vía de un solo sentido" : r.aristas.length === 2 ? "ambos sentidos" : "solo un sentido";
  log(`<b>${TIPOS[tipo].nombre}</b> en ${t.nombre} (${sentido}). Árbol B+: ${tIns < 0.01 ? "< 0,01" : tIns.toFixed(3)} ms
      en los dos índices (${indicePorId.tamano} reportes, altura ${indicePorId.altura()}). Peso: ${t.base.toFixed(2)} →
      ${TIPOS[tipo].min === Infinity ? "∞" : (t.base + TIPOS[tipo].min).toFixed(2)} min. Ruta recalculada con A* en ${tRuta.toFixed(1)} ms.`);
  renderReportes();
  $("st-arbol").textContent = `${indicePorId.tamano} · h ${indicePorId.altura()}`;
}

function setModo(m) {
  modo = m;
  document.querySelectorAll("[data-modo]").forEach((b) => b.classList.toggle("activo", b.dataset.modo === m));
  $("panel-reporte").hidden = m !== "reporte";
  setAyuda(m === "ruta" ? "Haz clic en el mapa para elegir el <b>origen</b> y luego el <b>destino</b>."
    : "Elige el tipo de incidente y haz clic sobre una calle del mapa.");
}
const setAyuda = (h) => ($("ayuda").innerHTML = h);
function log(html) {
  const li = document.createElement("li");
  li.innerHTML = html;
  $("log").prepend(li);
  while ($("log").children.length > 5) $("log").lastChild.remove();
}

function renderReportes() {
  const ul = $("lista-reportes");
  ul.innerHTML = reportes.length ? "" : '<li class="vacio">Aún no hay reportes activos.</li>';
  for (const r of [...reportes].reverse()) {
    const f = factorConfianza(r);
    const estado = f === 0 ? '<span class="tag gris">no verificado</span>' : f > 1 ? '<span class="tag verde">validado ×1,5</span>' : "";
    const li = document.createElement("li");
    li.innerHTML = `${r.foto ? `<img src="${r.foto}" alt="">` : `<span class="dot" style="background:${TIPOS[r.tipo].color}"></span>`}
      <div><b>${TIPOS[r.tipo].nombre}</b> · ${r.calle}<br><small>${hhmm(r.minuto)} · #${r.id} ${estado}</small></div>
      <div class="votos"><button data-v="up" aria-label="Confirmar">▲ ${r.up}</button><button data-v="down" aria-label="Desmentir">▼ ${r.down}</button></div>`;
    li.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      r[b.dataset.v]++; recalcularPesos(); pintarCalles(); pintarCalor(); dibujarRuta(true); renderReportes();
    }));
    ul.appendChild(li);
  }
}

function iniciarInteraccion() {
  mapa.on("click", (ev) => {
    const ll = [ev.latlng.lat, ev.latlng.lng];
    if (modo === "ruta") {
      if (paso === 0) { origen = nodoCercano(ll); paso = 1; capaMarcas.clearLayers();
        L.marker(nodos[origen], { icon: iconoPin("A", "#1f8a4c") }).addTo(capaMarcas);
        setAyuda("Ahora haz clic en el <b>destino</b>."); return; }
      destino = nodoCercano(ll); paso = 0; rutaAnterior = null; dibujarRuta(false);
      setAyuda("Ruta calculada. Haz clic de nuevo para elegir otro origen.");
    } else {
      const t = tramoCercano(ll);
      if (!t) { setAyuda("Haz clic más cerca de una avenida."); return; }
      crearReporte(t, $("tipo").value, fotoPendiente, $("bidireccional").checked);
      fotoPendiente = null; $("foto-info").textContent = ""; $("foto").value = "";
    }
  });
  document.querySelectorAll("[data-modo]").forEach((b) => b.addEventListener("click", () => setModo(b.dataset.modo)));
  $("btn-bloquear").addEventListener("click", () => {
    if (!rutaAnterior || !rutaAnterior.length) return;
    const e = rutaAnterior[Math.floor(rutaAnterior.length / 2)];
    crearReporte(tramos[e.tramo], "bloqueo", null, false);
  });
  $("btn-limpiar").addEventListener("click", () => {
    reportes.length = 0; recalcularPesos(); pintarCalles(); pintarCalor(); rutaAnterior = null; dibujarRuta(false);
    renderReportes(); log("Se limpiaron los reportes activos. Los pesos volvieron a su valor base.");
  });
  $("foto").addEventListener("change", (ev) => {        // compresión en el cliente (Canvas API)
    const archivo = ev.target.files[0];
    if (!archivo) return;
    const img = new Image();
    img.onload = () => {
      const escala = Math.min(1, 800 / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * escala); c.height = Math.round(img.height * escala);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      fotoPendiente = c.toDataURL("image/jpeg", 0.7);
      const kb = Math.round((fotoPendiente.length * 3) / 4 / 1024);
      $("foto-info").textContent = `Comprimida: ${(archivo.size / 1024).toFixed(0)} KB → ${kb} KB ` +
        `(−${(100 * (1 - kb * 1024 / archivo.size)).toFixed(1)} %). Haz clic en una calle para reportar.`;
      URL.revokeObjectURL(img.src);
    };
    img.src = URL.createObjectURL(archivo);
  });
  $("btn-rango").addEventListener("click", () => {
    const [h1, m1] = $("desde").value.split(":").map(Number), [h2, m2] = $("hasta").value.split(":").map(Number);
    const ini = h1 * 60 + m1, fin = h2 * 60 + m2;
    const t0 = performance.now();
    const { valores, camino, hojas } = indicePorTiempo.buscarRango([ini, -1], [fin, Infinity]);
    const t = performance.now() - t0;
    const cuenta = {};
    valores.forEach((r) => (cuenta[r.tipo] = (cuenta[r.tipo] || 0) + 1));
    $("rango-res").innerHTML =
      `<p><b>${valores.length}</b> reportes entre ${hhmm(ini)} y ${hhmm(fin)} · ${t.toFixed(3)} ms ·
       bajó ${camino.length} niveles y recorrió ${hojas.length} hojas enlazadas.</p>
       <ul class="barras">${Object.entries(cuenta).sort((a, b) => b[1] - a[1]).map(([k, v]) =>
         `<li><span>${TIPOS[k].nombre}</span><i style="width:${(100 * v) / Math.max(1, valores.length)}%;background:${TIPOS[k].color}"></i><b>${v}</b></li>`).join("")}</ul>`;
  });
}

// ------------------------------------------------------------------ arranque
fetch("data/red_santa_cruz.json").then((r) => r.json()).then((red) => {
  cargarRed(red);
  lineas = tramos.map((t) => L.polyline(t.puntos, { color: "#8794a8", weight: 2, opacity: 0.45, renderer: lienzo })
    .bindTooltip(() => {
      const es = porTramo[t.id];
      const pesos = es.map((e) => (isFinite(e.peso) ? e.peso.toFixed(2) + " min" : "bloqueada")).join(" / ");
      return `<b>${t.nombre}</b><br>${t.unico ? "Un sentido" : "Doble sentido"} · ${(t.km * 1000).toFixed(0)} m · ${pesos}`;
    }, { sticky: true }).addTo(capaCalles));
  cargarHistorial();
  origen = nodoCercano([-17.8105, -63.2040]);
  destino = nodoCercano([-17.7600, -63.1625]);
  for (let i = 0; i < 3; i++) { caminoMinimo(origen, destino, true); caminoMinimo(origen, destino, false); }   // calentamiento del JIT
  $("st-red").textContent = `${nodos.length.toLocaleString("es-BO")} intersecciones · ${aristas.length.toLocaleString("es-BO")} aristas dirigidas`;
  $("st-arbol").textContent = `${indicePorId.tamano} · h ${indicePorId.altura()}`;
  iniciarInteraccion();
  pintarCalles();
  dibujarRuta(false);
  renderReportes();
  setModo("ruta");
  if (new URLSearchParams(location.search).has("simular")) { $("btn-bloquear").click(); $("btn-rango").click(); }
  document.body.dataset.listo = "1";
});
