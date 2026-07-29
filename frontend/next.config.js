/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://api:8000/:path*',
      },
      {
        source: '/ws',
        destination: 'ws://websocket:8765',
      },
    ];
  },
};

export default nextConfig;
