const state = {
  data: null,
  route: "inicio",
  selectedOpsDay: null,
  sidebarCollapsed: false,
  imageModalTrigger: null,
};

const DAY_NAMES = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
const WEEK_ORDER = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const HOME_TOOL_NAMES = [
  "Ranking",
  "Tasa de Éxito DT",
  "Calculadora de Ritmo",
  "Transferencias",
  "Partner Hub",
  "Layout",
  "Code Brew",
  "RSA 2.0",
];
const HOME_TOOL_DESCRIPTIONS = {
  "Ranking": "Consulta indicadores, ranking y desempeño operativo del distrito.",
  "Tasa de Éxito DT": "Registra observaciones de Drive Thru, Tasa de Éxito & Goo See.",
  "Calculadora de Ritmo": "Mide el ritmo de producción de bebidas durante observaciones en tienda.",
  "Transferencias": "Audita transferencias entre tiendas con foco operativo y conciliación rápida.",
  "Partner Hub": "Consulta aniversarios, cumpleaños e información de Partners.",
  "Layout": "Diseña, ajusta y valida layouts operativos de tienda.",
  "Code Brew": "Busca artículos, códigos y mercancía de forma rápida.",
  "RSA 2.0": "Realiza auditorías RSA, seguimiento de hallazgos y control mediante semáforo operativo.",
};
const DUTY_IMAGES_BY_DAY = {
  "Lunes": ["lunes_food.png", "lunes_showcase.png"],
  "Martes": ["martes_lobby.png", "martes_pic.png"],
  "Miércoles": ["miercoles_boh.png"],
  "Jueves": ["jueves_espresso.png", "jueves_lobby.png"],
  "Viernes": ["viernes_cafe_filtrado.png"],
  "Sábado": ["sabado_cbs.png"],
  "Domingo": ["domingo_drive_thru.png", "domingo_lobby.png"],
};
const DUTY_IMAGE_LABELS = {
  "lunes_food.png": "Lunes · Food",
  "lunes_showcase.png": "Lunes · Show Case",
  "martes_lobby.png": "Martes · Lobby",
  "martes_pic.png": "Martes · PIC",
  "miercoles_boh.png": "Miércoles · BOH",
  "jueves_espresso.png": "Jueves · Espresso",
  "jueves_lobby.png": "Jueves · Lobby",
  "viernes_cafe_filtrado.png": "Viernes · Café Filtrado",
  "sabado_cbs.png": "Sábado · CBS",
  "domingo_drive_thru.png": "Domingo · Drive Thru",
  "domingo_lobby.png": "Domingo · Lobby",
};
const ICONS = {
  home: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V20h13v-9.5"/><path d="M9.5 20v-6h5v6"/>',
  chart: '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18"/>',
  pulse: '<path d="M3 12h4l2.2-5 4.2 10 2.1-5H21"/>',
  users: '<path d="M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 20v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  week: '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M8 2v4M16 2v4M3 9h18M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.6 2.6L16.5 9"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="m15 9-2 6-4 2 2-6 4-2Z"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1"/><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.1-1.1"/>',
  message: '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z"/><path d="M8 9h8M8 13h5"/>',
  about: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.6 2.6 0 1 1 4.4 1.9c-1 .8-1.9 1.2-1.9 2.6M12 17h.01"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  arrow: '<path d="M5 12h14M14 7l5 5-5 5"/>',
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);

function icon(name) {
  return `<svg class="icon" aria-hidden="true" viewBox="0 0 24 24">${ICONS[name] || ICONS.info}</svg>`;
}

function normalizeBool(value) {
  return value === true || ["true", "si", "sí", "1"].includes(String(value ?? "").trim().toLowerCase());
}

function parseDate(value) {
  if (!value) return null;
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]), 12);
}

function startOfDay(date = new Date()) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate(), 12);
}

function formatDate(value, options = { day: "numeric", month: "short" }) {
  const date = value instanceof Date ? value : parseDate(value);
  return date ? new Intl.DateTimeFormat("es-MX", options).format(date) : "";
}

function formatLongDate(date = new Date()) {
  return new Intl.DateTimeFormat("es-MX", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  }).format(date);
}

function mondayOf(date) {
  const base = startOfDay(date);
  const day = base.getDay() || 7;
  base.setDate(base.getDate() - day + 1);
  return base;
}

function sundayOf(date) {
  const result = mondayOf(date);
  result.setDate(result.getDate() + 6);
  return result;
}

function dateRangeLabel(start, end) {
  return `${formatDate(start, { day: "numeric", month: "short" })} – ${formatDate(end, { day: "numeric", month: "short", year: "numeric" })}`;
}

function getSheets() {
  return state.data?.sheets || {};
}

function sheet(name) {
  return getSheets()[name] || [];
}

function visibleRecords(name) {
  return sheet(name).filter((record) => !("Visible" in record) || normalizeBool(record.Visible));
}

function publishedEvents() {
  return sheet("Eventos")
    .filter((record) => normalizeBool(record.Publicar))
    .map((record) => ({
      ...record,
      start: parseDate(record["Fecha Inicio"]),
      end: parseDate(record["Fecha Fin"]) || parseDate(record["Fecha Inicio"]),
    }))
    .filter((record) => record.start && record.end)
    .sort((a, b) => a.start - b.start);
}

function externalUrl(value) {
  const text = String(value ?? "").trim();
  return /^https?:\/\//i.test(text) && !text.includes("...") ? text : null;
}

function localAsset(value) {
  const name = String(value ?? "").trim().split(/[\\/]/).pop();
  return name ? `./assets/content/${encodeURIComponent(name)}` : null;
}

function isImageUrl(value) {
  return /\.(?:avif|gif|jpe?g|png|webp)(?:[?#].*)?$/i.test(String(value || ""));
}

function linkMarkup(value, label = "Abrir recurso", imageAlt = label) {
  if (!value) return "";
  const external = externalUrl(value);
  const text = String(value).trim();
  if (/^https?:\/\//i.test(text) && !external) return "";
  const href = external || localAsset(text);
  if (!href) return "";
  if (!external || isImageUrl(href)) {
    const imageLabel = label === "Abrir recurso" ? "Ver imagen" : label;
    return `<button class="external-link image-link" type="button" data-image-src="${esc(href)}" data-image-alt="${esc(imageAlt)}">${esc(imageLabel)} ${icon("arrow")}</button>`;
  }
  return `<a class="external-link" href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(label)} ${icon("arrow")}</a>`;
}

function emptyState(message) {
  return `<div class="empty-state">${esc(message)}</div>`;
}

function installIcons() {
  $$("[data-icon]").forEach((element) => {
    const label = element.querySelector("span");
    const accessibleLabel = element.textContent.trim();
    if (accessibleLabel) {
      element.dataset.tooltip = accessibleLabel;
      if (!element.getAttribute("aria-label")) element.setAttribute("aria-label", accessibleLabel);
    }
    element.insertAdjacentHTML("afterbegin", icon(element.dataset.icon));
    if (label && element.tagName === "A") label.setAttribute("aria-hidden", "false");
  });
}

function setGreeting() {
  const hour = new Date().getHours();
  const rows = sheet("Identidad");
  const desired = hour < 12
    ? "hero.greeting.morning"
    : hour < 19
      ? "hero.greeting.afternoon"
      : "hero.greeting.evening";
  const greeting = rows.find((record) => record.Identificador === desired)?.Valor;
  $("#greeting").textContent = greeting || (hour < 12 ? "Buenos días" : hour < 19 ? "Buenas tardes" : "Buenas noches");
  const campaign = rows.find((record) => record.Identificador === "hero.campaign.display")?.Valor;
  $("#campaign-display").textContent = campaign || "JUNTÉMONOS MÁS";
}

function routeTo(route, focus = true) {
  const target = $(`[data-view="${route}"]`) ? route : "inicio";
  state.route = target;
  $$(".view").forEach((view) => {
    view.hidden = view.dataset.view !== target;
  });
  $$("[data-route-link]").forEach((link) => {
    const active = link.dataset.routeLink === target;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  closeMenu();
  if (focus) {
    window.scrollTo({ top: 0, behavior: "smooth" });
    $("#main").focus({ preventScroll: true });
  }
}

function isCompactViewport() {
  return window.matchMedia("(max-width: 820px)").matches;
}

function applySidebarState() {
  const collapsed = state.sidebarCollapsed && !isCompactViewport();
  document.body.classList.toggle("sidebar-collapsed", collapsed);
  const button = $("#sidebar-collapse");
  button.setAttribute("aria-expanded", String(!collapsed));
  button.setAttribute("aria-label", collapsed ? "Expandir navegación" : "Contraer navegación");
  button.querySelector("span").textContent = collapsed ? "›" : "‹";
}

function toggleSidebar() {
  state.sidebarCollapsed = !state.sidebarCollapsed;
  localStorage.setItem("starbucksHubSidebarCollapsed", String(state.sidebarCollapsed));
  applySidebarState();
}

function openMenu() {
  if (!isCompactViewport()) {
    state.sidebarCollapsed = false;
    localStorage.setItem("starbucksHubSidebarCollapsed", "false");
    applySidebarState();
    return;
  }
  $("#sidebar").classList.add("is-open");
  $("#scrim").hidden = false;
  $("#menu-toggle").setAttribute("aria-expanded", "true");
  document.body.classList.add("menu-open");
}

function closeMenu() {
  $("#sidebar").classList.remove("is-open");
  $("#scrim").hidden = true;
  $("#menu-toggle").setAttribute("aria-expanded", "false");
  document.body.classList.remove("menu-open");
}

function currentDayName() {
  return DAY_NAMES[new Date().getDay()];
}

function renderHome() {
  const linksByName = new Map(sheet("Links").map((record) => [record.Nombre, record]));
  $("#home-tools-grid").innerHTML = HOME_TOOL_NAMES.map((name) => {
    const record = linksByName.get(name);
    const title = esc(name);
    const iconText = esc(record?.Icono || "•");
    const description = esc(HOME_TOOL_DESCRIPTIONS[name]);
    if (!record || !externalUrl(record.URL)) {
      return `<article class="home-tool-card is-disabled" aria-disabled="true">
        <span class="home-tool-icon" aria-hidden="true">${iconText}</span>
        <div><h3>${title}</h3><p>${description}</p></div>
        <span class="home-tool-state">No disponible</span>
      </article>`;
    }
    return `<a class="home-tool-card" href="${esc(record.URL)}" target="_blank" rel="noopener noreferrer" aria-label="${title}: abrir herramienta">
      <span class="home-tool-icon" aria-hidden="true">${iconText}</span>
      <div><h3>${title}</h3><p>${description}</p></div>
      <span class="home-tool-arrow" aria-hidden="true">${icon("arrow")}</span>
    </a>`;
  }).join("");
}

function eventInMonth(event, date = new Date()) {
  const start = new Date(date.getFullYear(), date.getMonth(), 1, 12);
  const end = new Date(date.getFullYear(), date.getMonth() + 1, 0, 12);
  return event.start <= end && event.end >= start;
}

function renderEvents() {
  const today = startOfDay();
  const mode = $("#event-period").value;
  const events = publishedEvents().filter((event) => {
    if (mode === "upcoming") return event.end >= today;
    if (mode === "month") return eventInMonth(event, today);
    return true;
  });
  const label = mode === "upcoming"
    ? `Desde ${formatDate(today, { day: "numeric", month: "long" })}`
    : mode === "month"
      ? formatDate(today, { month: "long", year: "numeric" })
      : "Todos los eventos publicados";
  $("#event-period-label").textContent = label;
  $("#events-timeline").innerHTML = events.length ? events.map((event) => {
    const status = event.end < today ? "Finalizado" : event.start <= today ? "Actual" : "Próximo";
    return `<article class="timeline-item">
      <time class="timeline-date" datetime="${esc(event["Fecha Inicio"])}"><strong>${event.start.getDate()}</strong><span>${esc(formatDate(event.start, { month: "short" }))}</span></time>
      <div class="timeline-copy">
        <h2>${esc(event["Nombre Evento"])}</h2>
        <p>${esc(event.Descripción)}</p>
        <div class="timeline-meta">
          <span class="badge ${status === "Actual" ? "" : "neutral"}">${status}</span>
          ${event.end > event.start ? `<span class="badge neutral">${esc(dateRangeLabel(event.start, event.end))}</span>` : ""}
          ${linkMarkup(event["Link/Imagen"], "Abrir", event["Nombre Evento"])}
        </div>
      </div>
    </article>`;
  }).join("") : emptyState("No hay eventos publicados para el periodo seleccionado.");
}

function getWeeklyForDay(day) {
  return sheet("Actividades_Semanales").filter((record) => record.Día === day);
}

function dateForWeekDay(day) {
  const date = mondayOf(new Date());
  date.setDate(date.getDate() + Math.max(0, WEEK_ORDER.indexOf(day)));
  return date;
}

function opsItem(record, type) {
  const isDaily = type === "daily";
  const link = isDaily ? record["Link / Imagen"] : type === "info" ? record["Link /Imagen"] : record.Link;
  const meta = isDaily
    ? record.Categoría || "Operación"
    : type === "info"
      ? record.Frecuencia || record.Categoría || "Vigente"
      : record["Hora / Corte"] || "";
  const priority = record.Prioridad ? `<span class="badge ${Number(record.Prioridad) === 1 ? "amber" : "neutral"}">Prioridad ${esc(record.Prioridad)}</span>` : "";
  return `<article class="ops-item">
    <span class="ops-item-icon" aria-hidden="true">${esc(record.Icono || (isDaily ? "✓" : "•"))}</span>
    <div class="ops-item-copy">
      <h3>${esc(record.Actividad)}</h3>
      <p>${esc(record.Descripción)}</p>
      <div class="ops-item-meta">${priority}${meta ? `<span class="badge neutral">${esc(meta)}</span>` : ""}${linkMarkup(link, "Abrir recurso", record.Actividad)}</div>
    </div>
  </article>`;
}

function opsSection(id, title, description, content) {
  return `<section class="ops-section" aria-labelledby="${id}-title">
    <div class="ops-section-heading">
      <div><p class="eyebrow">${esc(description)}</p><h2 id="${id}-title">${esc(title)}</h2></div>
    </div>
    <div class="ops-section-body">${content}</div>
  </section>`;
}

function renderDutyForDay(day) {
  const records = [...sheet("Duty_Roster")].sort((a, b) => Number(a.Orden || 99) - Number(b.Orden || 99));
  const record = records.find((item) => item.Día === day);
  if (!record) return emptyState("No hay información de Duty Roster para este día.");
  const stations = String(record.Estaciones || "").split(",").map((item) => item.trim()).filter(Boolean);
  const dutyImages = DUTY_IMAGES_BY_DAY[record.Día] || [];
  return `<div class="duty-card">
    <div class="duty-copy"><p class="eyebrow">${esc(record.Día)} · Foco operativo</p><h2>${esc(record.Estaciones)}</h2><p>${esc(record.Enfoque)}</p><div class="duty-stations">${stations.map((station) => `<span class="badge">${esc(station)}</span>`).join("")}</div></div>
    <div class="duty-gallery">${dutyImages.map((fileName) => {
      const label = DUTY_IMAGE_LABELS[fileName] || fileName;
      const src = `./assets/duty-roster/${encodeURIComponent(fileName)}`;
      return `<figure class="duty-thumbnail">
        <button type="button" data-image-src="${esc(src)}" data-image-alt="${esc(label)}" aria-label="Abrir ${esc(label)} en el visor">
          <img src="${esc(src)}" alt="${esc(label)}" loading="lazy" decoding="async">
          <span>${esc(label)}</span>
        </button>
      </figure>`;
    }).join("")}</div>
  </div>`;
}

function renderOps() {
  const todayName = currentDayName();
  state.selectedOpsDay = WEEK_ORDER.includes(state.selectedOpsDay) ? state.selectedOpsDay : todayName;
  const selectedDate = dateForWeekDay(state.selectedOpsDay);
  const isToday = state.selectedOpsDay === todayName;
  $("#ops-date").textContent = formatLongDate(selectedDate);
  $("#ops-day-badge").textContent = isToday ? "Hoy" : "Semana actual";
  $("#ops-day-tabs").innerHTML = WEEK_ORDER.map((day) => `
    <button type="button" role="tab" aria-selected="${day === state.selectedOpsDay}" data-ops-day="${esc(day)}" class="${day === todayName ? "is-today" : ""}">
      ${esc(day)}${day === todayName ? "<small>Hoy</small>" : ""}
    </button>`).join("");
  $$("[data-ops-day]").forEach((button) => button.addEventListener("click", () => {
    state.selectedOpsDay = button.dataset.opsDay;
    renderOps();
  }));

  const weekly = getWeeklyForDay(state.selectedOpsDay);
  const wfm = weekly.filter((record) => /^WFM\b/i.test(String(record.Actividad || "")));
  const nonWfmWeekly = weekly.filter((record) => !/^WFM\b/i.test(String(record.Actividad || "")));
  const daily = visibleRecords("Actividades_Diaria")
    .sort((a, b) => Number(a.Prioridad || 99) - Number(b.Prioridad || 99));
  const info = visibleRecords("Informativo")
    .sort((a, b) => Number(a.Prioridad || 99) - Number(b.Prioridad || 99));
  const planningDate = new Date(selectedDate);
  planningDate.setDate(planningDate.getDate() + 15);
  const planningLabel = dateRangeLabel(mondayOf(planningDate), sundayOf(planningDate));
  const wfmContent = `<div class="ops-planning">
      <span>Semana en planeación</span><strong>${esc(planningLabel)}</strong>
      <small>Referencia calculada 15 días adelante</small>
    </div>
    <div class="ops-list">${wfm.length ? wfm.map((record) => opsItem(record, "weekly")).join("") : emptyState("No hay una acción WFM programada para este día.")}</div>`;

  const focusLabel = isToday ? "Hoy" : state.selectedOpsDay;
  $("#ops-content").innerHTML = `
    <section class="ops-focus" aria-label="Resumen del día seleccionado">
      <span>${esc(focusLabel)}</span>
      <strong>${esc(state.selectedOpsDay)}</strong>
      <p>Consulta en orden las acciones y apoyos disponibles para la operación.</p>
    </section>
    ${opsSection("ops-wfm", "WFM", "Planeación inteligente", wfmContent)}
    ${opsSection("ops-daily", "Actividad del día", "Consistencia diaria", `<div class="ops-list">${daily.length ? daily.map((record) => opsItem(record, "daily")).join("") : emptyState("No hay actividades diarias visibles.")}</div>`)}
    ${opsSection("ops-weekly", "Actividad semanal", "Acciones para el día", `<div class="ops-list">${nonWfmWeekly.length ? nonWfmWeekly.map((record) => opsItem(record, "weekly")).join("") : emptyState("No hay una actividad semanal adicional para este día.")}</div>`)}
    ${opsSection("ops-duty", "Duty Roster", "Cobertura operativa", renderDutyForDay(state.selectedOpsDay))}
    ${opsSection("ops-info", "Informativo", "Comunicados vigentes", `<div class="ops-list">${info.length ? info.map((record) => opsItem(record, "info")).join("") : emptyState("No hay comunicaciones vigentes.")}</div>`)}
  `;
}

function renderLinks() {
  const records = [...sheet("Links")].sort((a, b) => Number(a.Orden || 99) - Number(b.Orden || 99));
  const favorites = records.filter((record) => normalizeBool(record.Favorito));
  $("#favorite-links").innerHTML = favorites.length ? favorites.slice(0, 8).map((record) => `
    <a class="favorite-link" href="${esc(record.URL)}" target="_blank" rel="noopener noreferrer">
      <span class="link-icon">${esc(record.Icono || "↗")}</span><strong>${esc(record.Nombre)}</strong><small>${esc(record.Notas || record.Grupo || "")}</small>
    </a>`).join("") : "";
  $("#links-list").innerHTML = records.length ? records.map((record) => `
    <a class="link-row" href="${esc(record.URL)}" target="_blank" rel="noopener noreferrer">
      <span>${esc(record.Icono || "↗")}</span><strong>${esc(record.Nombre)}</strong><p>${esc(record.Notas || "")}</p><span class="external">Abrir ↗</span>
    </a>`).join("") : emptyState("No hay herramientas disponibles en el CMS.");
}

function renderAll() {
  setGreeting();
  renderHome();
  renderEvents();
  renderOps();
  renderLinks();
}

function openImageModal(src, alt, trigger) {
  state.imageModalTrigger = trigger || document.activeElement;
  $("#image-modal-content").src = src;
  $("#image-modal-content").alt = alt || "Imagen ampliada";
  $("#image-modal-title").textContent = alt || "Vista de imagen";
  $("#image-modal").hidden = false;
  document.body.classList.add("modal-open");
  $("#image-modal-close").focus();
}

function closeImageModal() {
  if ($("#image-modal").hidden) return;
  $("#image-modal").hidden = true;
  $("#image-modal-content").src = "";
  document.body.classList.remove("modal-open");
  state.imageModalTrigger?.focus?.();
  state.imageModalTrigger = null;
}

function bindEvents() {
  window.addEventListener("hashchange", () => routeTo(location.hash.slice(1) || "inicio"));
  $$("[data-route-link]").forEach((link) => link.addEventListener("click", closeMenu));
  $("#menu-toggle").addEventListener("click", () => $("#sidebar").classList.contains("is-open") ? closeMenu() : openMenu());
  $("#sidebar-collapse").addEventListener("click", toggleSidebar);
  $("#sidebar-close").addEventListener("click", closeMenu);
  $("#scrim").addEventListener("click", closeMenu);
  $("#image-modal-close").addEventListener("click", closeImageModal);
  $("#image-modal").addEventListener("click", (event) => {
    if (event.target === $("#image-modal")) closeImageModal();
  });
  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-image-src]");
    if (!trigger) return;
    openImageModal(trigger.dataset.imageSrc, trigger.dataset.imageAlt, trigger);
  });
  $("#event-period").addEventListener("change", renderEvents);
  window.addEventListener("online", updateConnectionStatus);
  window.addEventListener("offline", updateConnectionStatus);
  window.addEventListener("resize", () => {
    closeMenu();
    applySidebarState();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !$("#image-modal").hidden) {
      closeImageModal();
      return;
    }
    if (event.key === "Escape") closeMenu();
    if (event.key === "Tab" && !$("#image-modal").hidden) {
      event.preventDefault();
      $("#image-modal-close").focus();
    }
  });
}

function updateConnectionStatus() {
  $("#offline-banner").hidden = navigator.onLine;
}

async function loadData() {
  const response = await fetch("./data/cms.json", { cache: "no-cache" });
  if (!response.ok) throw new Error(`No fue posible cargar el CMS (${response.status}).`);
  const payload = await response.json();
  if (!payload.sheets) throw new Error("El archivo de datos no contiene las hojas esperadas.");
  return payload;
}

async function init() {
  state.sidebarCollapsed = localStorage.getItem("starbucksHubSidebarCollapsed") === "true";
  applySidebarState();
  installIcons();
  bindEvents();
  updateConnectionStatus();
  try {
    state.data = await loadData();
    renderAll();
    routeTo(location.hash.slice(1) || "inicio", false);
  } catch (error) {
    $("#error-banner").textContent = `${error.message} Actualiza los datos desde Starbucks_Hub_CMS.xlsx.`;
    $("#error-banner").hidden = false;
    routeTo("inicio", false);
  }
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  }
}

init();
