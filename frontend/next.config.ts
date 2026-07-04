import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: 'out',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

export default nextConfig;
