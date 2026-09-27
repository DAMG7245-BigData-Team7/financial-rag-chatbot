import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: `npm run build` writes plain HTML/JS to out/, served by Caddy.
  output: "export",
};

export default nextConfig;
