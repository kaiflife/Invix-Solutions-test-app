import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Все запросы к /api/* отправляем на FastAPI бэкенд
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
      {
        // Все запросы к /minio/* проксируем в MinIO
        source: '/minio/:path*',
        destination: 'http://minio:9000/:path*',
      },
    ];
  },
};

export default nextConfig;