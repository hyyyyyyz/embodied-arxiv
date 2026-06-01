import type { NextConfig } from "next";

// Static export for GitHub Pages.
//  - `output: 'export'` → `next build` produces a fully static `out/` dir.
//  - `basePath` / `assetPrefix` route the site under
//    hyyyyyyz.github.io/embodied-arxiv/
//  - `images.unoptimized` is required for export (no server image optimizer).
//  - `trailingSlash` keeps directory-index URLs working cleanly on GH Pages
//    (so /papers/ resolves to /papers/index.html).
const isProd = process.env.NODE_ENV === "production";
const BASE_PATH = isProd ? "/embodied-arxiv" : "";

const nextConfig: NextConfig = {
  output: "export",
  basePath: BASE_PATH,
  assetPrefix: BASE_PATH || undefined,
  trailingSlash: true,
  images: { unoptimized: true },
  env: {
    NEXT_PUBLIC_BASE_PATH: BASE_PATH,
  },
};

export default nextConfig;
