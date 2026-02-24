import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Use server mode for Playwright tests (static export breaks next start)
  output: process.env.CI ? 'export' : undefined,
  distDir: 'dist',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

export default nextConfig;
