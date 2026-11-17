// Visualizador didáctico del Árbol B+ y gráficos de resultados del benchmark.

(function visualizador() {
  const svg = document.getElementById("bp-svg");
  const info = document.getElementById("bp-info");
  let arbol, resaltado = { camino: new Set(), hojas: new Set(), claves: new Set(), nuevo: null };

  function reiniciar() {
    arbol = new ArbolBPlus(Number(document.getElementById("bp-orden").value));
    [5, 12, 18, 25, 31, 7, 40, 3, 22, 15, 28, 35].forEach((k) => arbol.insertar(k, k));
    resaltado = { camino: new Set(), hojas: new Set(), claves: new Set(), nuevo: null };
    dibujar(`Árbol de orden M = ${arbol.orden}: cada nodo tiene como máximo ${arbol.orden - 1} claves.`);
  }

  function dibujar(mensaje) {
    const niveles = arbol.niveles();
    const CW = 30, H = 30, GAP = 16, VGAP = 70;
    const ancho = (n) => n.claves.length * CW;
    const hojas = niveles[niveles.length - 1];
    const pos = new Map();
    let x = 10;
    hojas.forEach((h) => { pos.set(h.id, { x, w: ancho(h) }); x += ancho(h) + GAP; });
    const W = Math.max(x, 300);
    for (let l = niveles.length - 2; l >= 0; l--)
      niveles[l].forEach((n) => {
        const a = pos.get(n.hijos[0].id), b = pos.get(n.hijos[n.hijos.length - 1].id);
        const c = (a.x + b.x + b.w) / 2, w = ancho(n);
        pos.set(n.id, { x: c - w / 2, w });
      });
    const Ht = niveles.length * (H + VGAP) - VGAP + 40;
    svg.setAttribute("viewBox", `0 0 ${W} ${Ht}`);
    let s = "";
    niveles.forEach((nivel, l) => {
      const y = 10 + l * (H + VGAP);
      nivel.forEach((n) => {
        const p = pos.get(n.id);
        if (!n.esHoja) n.hijos.forEach((h, i) => {
          const q = pos.get(h.id);
          const activo = resaltado.camino.has(n.id) && (resaltado.camino.has(h.id) || resaltado.hojas.has(h.id));
          s += `<line x1="${p.x + i * CW}" y1="${y + H}" x2="${q.x + q.w / 2}" y2="${y + H + VGAP}" class="${activo ? "arista activa" : "arista"}"/>`;
        });
        if (n.esHoja && n.siguiente) {
          const q = pos.get(n.siguiente.id);
          const activo = resaltado.hojas.has(n.id) && resaltado.hojas.has(n.siguiente.id);
          s += `<line x1="${p.x + p.w + 2}" y1="${y + H / 2}" x2="${q.x - 4}" y2="${y + H / 2}" class="${activo ? "enlace activo" : "enlace"}" marker-end="url(#flecha)"/>`;
        }
        const cls = ["nodo", n.esHoja ? "hoja" : "interno", resaltado.camino.has(n.id) ? "en-camino" : "",
          resaltado.hojas.has(n.id) ? "recorrida" : "", resaltado.nuevo === n.id ? "nuevo" : ""].join(" ");
        s += `<rect x="${p.x}" y="${y}" width="${p.w}" height="${H}" rx="5" class="${cls}"/>`;
        n.claves.forEach((k, i) => {
          if (i) s += `<line x1="${p.x + i * CW}" y1="${y}" x2="${p.x + i * CW}" y2="${y + H}" class="sep"/>`;
          const hit = n.esHoja && resaltado.claves.has(k);
          s += `<text x="${p.x + i * CW + CW / 2}" y="${y + H / 2 + 4}" class="${hit ? "clave hit" : "clave"}">${k}</text>`;
        });
      });
    });
    svg.innerHTML = `<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="punta"/></marker></defs>${s}`;
    info.innerHTML = `${mensaje}<br><small>${arbol.tamano} claves · altura ${arbol.altura()} · las hojas (azul) están enlazadas en orden.</small>`;
  }

  function insertar(k) {
    if (!Number.isFinite(k)) return;
    const altura = arbol.altura();
    const hoja = arbol.insertar(k, k);
    resaltado = { camino: new Set(), hojas: new Set(), claves: new Set([k]), nuevo: hoja };
    dibujar(arbol.altura() > altura ? `Se insertó ${k}: la raíz se dividió y el árbol creció un nivel (sigue balanceado).`
      : `Se insertó ${k}. Si una hoja supera ${arbol.orden - 1} claves se divide (split) y la clave del medio sube al padre.`);
  }

  document.getElementById("bp-orden").addEventListener("change", reiniciar);
  document.getElementById("bp-reiniciar").addEventListener("click", reiniciar);
  document.getElementById("bp-insertar").addEventListener("click", () => {
    const inp = document.getElementById("bp-valor");
    insertar(parseInt(inp.value, 10)); inp.value = "";
  });
  document.getElementById("bp-valor").addEventListener("keydown", (e) => { if (e.key === "Enter") document.getElementById("bp-insertar").click(); });
  document.getElementById("bp-aleatorio").addEventListener("click", () => {
    let k; do { k = 1 + Math.floor(Math.random() * 99); } while (arbol.buscar(k) !== undefined && arbol.tamano < 99);
    insertar(k);
  });
  document.getElementById("bp-rango").addEventListener("click", () => {
    const a = parseInt(document.getElementById("bp-a").value, 10), b = parseInt(document.getElementById("bp-b").value, 10);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return;
    const r = arbol.buscarRango(Math.min(a, b), Math.max(a, b));
    resaltado = { camino: new Set(r.camino), hojas: new Set(r.hojas), claves: new Set(r.valores), nuevo: null };
    dibujar(`Rango [${Math.min(a, b)}, ${Math.max(a, b)}]: bajó ${r.camino.length} niveles (rojo) y luego recorrió
      ${r.hojas.length} hojas enlazadas (naranja) → ${r.valores.length} resultados: ${r.valores.join(", ") || "ninguno"}.`);
  });
  reiniciar();
})();

(function graficos() {
  if (!window.Chart || !window.RESULTADOS) return;
  const css = getComputedStyle(document.documentElement);
  const tinta = css.getPropertyValue("--tinta-2").trim(), grid = css.getPropertyValue("--linea").trim();
  const AZUL = "#1f5fa8", NAR = "#e07a1f";
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.color = tinta;
  const R = RESULTADOS.reportes, G = RESULTADOS.grafo;
  const serie = (label, data, color) => ({ label, data, borderColor: color, backgroundColor: color, tension: 0.25, pointRadius: 4, borderWidth: 2.5 });
  // en ejes logarítmicos solo se rotulan las potencias de 10
  const ticksLog = { autoSkip: false, maxRotation: 0,
    callback: (v) => (Math.abs(Math.log10(v) % 1) < 1e-9 ? Number(v).toLocaleString("es-BO") : "") };
  const ejes = (xt, yt, log) => ({
    x: { type: log ? "logarithmic" : "linear", title: { display: true, text: xt }, grid: { color: grid }, ticks: log ? ticksLog : {} },
    y: { type: log ? "logarithmic" : "linear", title: { display: true, text: yt }, grid: { color: grid }, ticks: log ? ticksLog : {} },
  });
  const opts = (xt, yt, log) => ({ responsive: true, maintainAspectRatio: false, parsing: false,
    plugins: { legend: { position: "bottom" }, tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${c.parsed.y.toPrecision(3)}` } } },
    scales: ejes(xt, yt, log) });
  const pts = (arr, kx, ky) => arr.map((r) => ({ x: r[kx], y: r[ky] }));

  new Chart(document.getElementById("ch-id"), { type: "line", options: opts("Reportes almacenados", "ms por consulta (log)", true),
    data: { datasets: [serie("Lista enlazada", pts(R, "n", "busqueda_id_lista_ms"), NAR), serie("Árbol B+", pts(R, "n", "busqueda_id_bplus_ms"), AZUL)] } });
  new Chart(document.getElementById("ch-rango"), { type: "line", options: opts("Reportes almacenados", "ms por consulta (log)", true),
    data: { datasets: [serie("Lista enlazada", pts(R, "n", "rango_lista_ms"), NAR), serie("Árbol B+", pts(R, "n", "rango_bplus_ms"), AZUL)] } });
  new Chart(document.getElementById("ch-ruta"), { type: "line", options: opts("Intersecciones del grafo", "ms por ruta", false),
    data: { datasets: [serie("Dijkstra", pts(G, "nodos", "dijkstra_ms"), NAR), serie("A*", pts(G, "nodos", "a_estrella_ms"), AZUL)] } });
  new Chart(document.getElementById("ch-exp"), { type: "line", options: opts("Intersecciones del grafo", "nodos expandidos", false),
    data: { datasets: [serie("Dijkstra", pts(G, "nodos", "expandidos_dijkstra"), NAR), serie("A*", pts(G, "nodos", "expandidos_a_estrella"), AZUL)] } });
})();

(function tablas() {
  const es = (x, d = 1) => Number(x).toLocaleString("es-BO", { minimumFractionDigits: d, maximumFractionDigits: d });
  const O = window.RESULTADOS_OSM, G = window.RESULTADOS && RESULTADOS.grafo[RESULTADOS.grafo.length - 1];
  if (O && G) {
    const red = (a, b) => es(100 * (1 - a / b), 1) + " %";
    document.getElementById("tb-osm").innerHTML = `
      <thead><tr><th></th><th>Cuadrícula</th><th>Red real</th></tr></thead><tbody>
      <tr><td>Intersecciones</td><td>${es(G.nodos, 0)}</td><td>${es(O.nodos, 0)}</td></tr>
      <tr><td>Aristas dirigidas</td><td>${es(G.aristas, 0)}</td><td>${es(O.aristas_dirigidas, 0)}</td></tr>
      <tr><td>Nodos A* / Dijkstra</td><td>${es(G.expandidos_a_estrella, 0)} / ${es(G.expandidos_dijkstra, 0)}</td><td>${es(O.expandidos_a_estrella, 0)} / ${es(O.expandidos_dijkstra, 0)}</td></tr>
      <tr><td>Reducción de nodos</td><td>${red(G.expandidos_a_estrella, G.expandidos_dijkstra)}</td><td>${red(O.expandidos_a_estrella, O.expandidos_dijkstra)}</td></tr>
      <tr><td>Reducción de tiempo</td><td>${red(G.a_estrella_ms, G.dijkstra_ms)}</td><td>${red(O.a_estrella_ms, O.dijkstra_ms)}</td></tr>
      <tr><td>Recálculo máximo</td><td>${es(G.recalculo_max_ms)} ms</td><td>${es(O.recalculo_max_ms)} ms</td></tr></tbody>`;
  }
  const C = window.COMPRESION;
  if (C) {
    const prom = (k) => C.reduce((s, r) => s + r[k], 0) / C.length;
    document.getElementById("tb-fotos").innerHTML = `
      <thead><tr><th>Foto</th><th>Original</th><th>Comprimida</th><th>Reducción</th></tr></thead><tbody>
      ${C.map((r, i) => `<tr><td>${i + 1} · ${r.original_px}</td><td>${es(r.original_kb, 0)} KB</td><td>${es(r.comprimida_kb, 1)} KB</td><td>${es(r.reduccion_pct)} %</td></tr>`).join("")}
      <tr class="total"><td>Promedio</td><td>${es(prom("original_kb"), 0)} KB</td><td>${es(prom("comprimida_kb"), 1)} KB</td><td>${es(prom("reduccion_pct"))} %</td></tr></tbody>`;
  }
})();

(function equipo() {
  const EQUIPO = [   // nombres, apellidos, carrera, ORCID
    ["Sergio", "Estaca Paco", "Ingeniería Informática", "0009-0006-5377-8272"],
    ["Annett Alejandra", "Cruz Rojas", "Ingeniería Informática", ""],
    ["Wendy Nicol", "Perez Sandoval", "Ingeniería Informática", "0009-0004-3923-5445"],
    ["Paola Andrea", "Murguia Duran", "Ingeniería en Sistemas", ""],
    ["Adria Fernando", "Roca Camacho", "Ingeniería en Sistemas", ""],
  ];
  const cont = document.getElementById("equipo-lista");
  if (!cont) return;
  cont.innerHTML = EQUIPO.map(([n, a, c, o]) => `
    <article class="miembro">
      <div class="avatar" aria-hidden="true">${n[0]}${a[0]}</div>
      <b>${n}</b><span class="ap">${a}</span>
      <span class="carrera ${c.includes("Sistemas") ? "sistemas" : ""}">${c}</span>
      ${o ? `<a class="orcid" href="https://orcid.org/${o}" target="_blank" rel="noopener">ORCID ${o}</a>` : '<span class="orcid pend">ORCID en trámite</span>'}
    </article>`).join("");
})();
