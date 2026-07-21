import type { NextConfig } from "next";
// `output: "standalone"` est requis pour l'image Docker (frontend/Dockerfile),
// mais casse le routage sur Vercel (404 NOT_FOUND). Vercel définit VERCEL=1
// pendant le build : on désactive donc standalone uniquement dans ce cas.
const nextConfig: NextConfig = process.env.VERCEL ? {} : { output: "standalone" };
export default nextConfig;

