const CACHE_NAME = "starbucks-hub-v7";
const CORE_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./data/cms.json",
  "./assets/icons/starbucks_hub.png",
  "./assets/about/Kike_pbt.jpeg",
  "./assets/about/George_pbt.jpeg",
  "./assets/duty-roster/lunes_food.png",
  "./assets/duty-roster/lunes_showcase.png",
  "./assets/duty-roster/martes_lobby.png",
  "./assets/duty-roster/martes_pic.png",
  "./assets/duty-roster/miercoles_boh.png",
  "./assets/duty-roster/jueves_espresso.png",
  "./assets/duty-roster/jueves_lobby.png",
  "./assets/duty-roster/viernes_cafe_filtrado.png",
  "./assets/duty-roster/sabado_cbs.png",
  "./assets/duty-roster/domingo_drive_thru.png",
  "./assets/duty-roster/domingo_lobby.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(CORE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const requestUrl = new URL(event.request.url);
  if (requestUrl.origin !== self.location.origin) return;

  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          return response;
        })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  if (requestUrl.pathname.endsWith("/data/cms.json")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (!response.ok) return response;
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          return response;
        })
        .catch(() => caches.match(event.request).then((cached) => cached || caches.match("./data/cms.json")))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
      }
      return response;
    }))
  );
});
