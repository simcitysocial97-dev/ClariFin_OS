import type { NextConfig } from "next";
import { ROUTE_REDIRECTS } from "./lib/config/navigation";

const nextConfig: NextConfig = {
  // Server mode for all environments (C24): static export removed so the
  // production Next.js server (`next start`) is the single frontend runtime
  // model for local, CI, and production. No CI-specific output fork.
  distDir: "dist",
  images: {
    unoptimized: true,
  },
  // Canonical no-slash URLs so native redirects() answer the alias request
  // directly (single-hop) instead of Next's trailing-slash 308 preceding it.
  trailingSlash: false,
  // Native redirect ownership (C24): derived from the single source of truth
  // in lib/config/navigation.ts. No second hard-coded alias table here.
  async redirects() {
    return Object.entries(ROUTE_REDIRECTS).map(([source, destination]) => ({
      source,
      destination,
      permanent: false,
    }));
  },
};

export default nextConfig;
