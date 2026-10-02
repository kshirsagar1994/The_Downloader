import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
      {
        protocol: "http",
        hostname: "**",
      },
    ],
  },
  async rewrites() {
    const internalApi = process.env.INTERNAL_API_URL;
    const apiUrl = internalApi
      ? (internalApi.startsWith("http://") || internalApi.startsWith("https://")
          ? internalApi
          : `https://${internalApi}`)
      : "http://127.0.0.1:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
