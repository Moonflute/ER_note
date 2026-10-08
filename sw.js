"use strict";

const CACHE_NAME = "er-note-v27";
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css?v=24",
  "./app.js?v=39",
  "./data/chief-complaints.json?v=24",
  "./data/cc-concepts.json?v=5",
  "./manifest.webmanifest",
  "./assets/icons/er-icon-32.png",
  "./assets/icons/er-icon-180.png",
  "./assets/icons/er-icon-192.png",
  "./assets/icons/er-icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(names.filter((name) => name.startsWith("er-note-") && name !== CACHE_NAME).map((name) => caches.delete(name))))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, fallbackUrl) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response.ok) {
      await cache.put(request, response.clone());
      return response;
    }
    return (await cache.match(request)) || (fallbackUrl ? await cache.match(fallbackUrl) : undefined) || response;
  } catch {
    return (await cache.match(request)) || (fallbackUrl ? await cache.match(fallbackUrl) : undefined) || Response.error();
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) await cache.put(request, response.clone());
  return response;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request, "./index.html"));
    return;
  }
  if (url.pathname.endsWith("/data/chief-complaints.json") || url.pathname.endsWith("/data/cc-concepts.json")) {
    event.respondWith(networkFirst(request));
    return;
  }
  event.respondWith(cacheFirst(request));
});
