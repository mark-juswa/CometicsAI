import type { NextConfig } from 'next';

const config: NextConfig = {
  experimental: {
    // Windows dev sessions were repeatedly failing to persist/compact the disk cache.
    // Keep development compilation in memory; production builds retain their defaults.
    turbopackFileSystemCacheForDev: false,
  },
};

export default config;
