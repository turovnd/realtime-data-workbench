/* Cache public application files only. API responses and mutations are never cached. */
const CACHE = "feedback-desk-shell-__BUILD_HASH__";
const ASSETS = ["__BUILD_ASSETS__"];

self.addEventListener("install", event => {
  event.waitUntil(
    (async () => {
      const response = await fetch("/", {
        cache: "reload",
        credentials: "omit",
      });
      if (
        !response.ok ||
        !response.headers.get("content-type")?.includes("text/html")
      ) {
        throw new Error("The public application shell could not be loaded.");
      }

      if (!ASSETS.length) {
        throw new Error("The public application shell has no static assets.");
      }

      const cache = await caches.open(CACHE);
      await cache.addAll(
        ASSETS.map(
          url => new Request(url, { cache: "reload", credentials: "omit" })
        )
      );
      await cache.put("/", response);
      await self.skipWaiting();
    })()
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter(
            key =>
              (key.startsWith("signal-desk-shell-") ||
                key.startsWith("feedback-desk-shell-")) &&
              key !== CACHE
          )
          .map(key => caches.delete(key))
      );
      await self.clients.claim();
    })()
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (
    request.method !== "GET" ||
    url.origin !== self.location.origin ||
    url.pathname === "/api" ||
    url.pathname.startsWith("/api/")
  ) {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(async () => {
        const cache = await caches.open(CACHE);
        return (await cache.match("/")) || Response.error();
      })
    );
    return;
  }

  if (!url.pathname.startsWith("/assets/")) return;

  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE);
      // Public content-hashed assets are identical across Origin header variants.
      const cached = await cache.match(request, { ignoreVary: true });
      if (cached) return cached;

      const response = await fetch(request);
      if (response.ok) await cache.put(request, response.clone());

      return response;
    })()
  );
});
