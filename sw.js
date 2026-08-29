const CACHE_NAME = "starbucks-hub-v12";
const CORE_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./data/cms.json",
  "./assets/icons/starbucks_hub.png"
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
    Promise.all([
      caches.keys().then((names) => Promise.all(
        names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
      )),
      self.registration.navigationPreload?.enable(),
    ]).then(() => self.clients.claim())
  );
});

async function storeResponse(request, response) {
  if (response?.ok) {
    const cache = await caches.open(CACHE_NAME);
    await cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request, fallback, preloadResponse) {
  try {
    const response = await preloadResponse || await fetch(request);
    return await storeResponse(request, response);
  } catch {
    return (await caches.match(request)) || caches.match(fallback);
  }
}

function staleWhileRevalidate(request, event) {
  const update = fetch(request)
    .then((response) => storeResponse(request, response))
    .catch(() => undefined);
  event.waitUntil(update);
  return caches.match(request).then((cached) => cached || update);
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET" || event.request.headers.has("range")) return;
  const requestUrl = new URL(event.request.url);
  if (requestUrl.origin !== self.location.origin) return;

  if (event.request.mode === "navigate") {
    event.respondWith(networkFirst(event.request, "./index.html", event.preloadResponse));
    return;
  }

  if (requestUrl.pathname.endsWith("/data/cms.json")) {
    event.respondWith(networkFirst(event.request, "./data/cms.json"));
    return;
  }

  event.respondWith(staleWhileRevalidate(event.request, event));
});
