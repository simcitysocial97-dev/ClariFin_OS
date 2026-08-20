import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // C38.5 — Canonical runtime is Next.js server mode (`next start`) in EVERY
  // environment (local dev, Playwright, verification runtime, CI, production
  // build verification). The frontend is an SPA that also relies on
  // middleware.ts for legacy-route compatibility (ROUTE_REDIRECTS), and
  // middleware only executes under server mode. A static export cannot run
  // middleware and has no SPA fallback, which previously caused divergent
  // behaviour between local (`next start`) and CI (`output: 'export'` +
  // `python3 -m http.server`). We standardise on server mode so the same
  // architecture executes identically everywhere. The API is reached from the
  // browser via absolute CORS URLs (see lib/api/gateway.ts), so the Next.js
  // server never needs to proxy API traffic.
  distDir: 'dist',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

export default nextConfig;
