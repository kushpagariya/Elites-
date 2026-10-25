import type { NextConfig } from "next";
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
require('./scripts/map-assets.cjs').prepareMapAssets();
const apiOrigin = (process.env.STORESCOUT_API_ORIGIN ?? 'http://127.0.0.1:8000').trim().replace(/\/+$/, '');
if (process.env.VERCEL && (!process.env.STORESCOUT_API_ORIGIN || !apiOrigin.startsWith('https://') || /https:\/\/(localhost|127\.0\.0\.1)([:/]|$)/.test(apiOrigin))) {
  throw new Error('Set STORESCOUT_API_ORIGIN to the Render HTTPS origin before building on Vercel.');
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [{ source: '/api/v1/:path*', destination: `${apiOrigin}/api/v1/:path*` }];
  },
  async headers() {
    return [{source: '/vendor/maplibre/:path*', headers: [
      {key: 'Content-Type', value: 'text/javascript; charset=utf-8'},
      {key: 'Cache-Control', value: 'public, max-age=0, must-revalidate'},
    ]}];
  },
};

export default nextConfig;
