import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
  // Silence the turbopack "multiple lockfiles" warning
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;