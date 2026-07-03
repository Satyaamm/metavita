/** @type {import('next').NextConfig} */
const apiUrl = process.env.METAVITA_API_URL || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  // Emit a self-contained server bundle for small production Docker images.
  output: "standalone",
  // @lobehub/icons ships ESM that Next needs to transpile for the brand logos.
  transpilePackages: ["@lobehub/icons"],
  // Tree-shake the Fluent barrels so pages don't pull the entire icon set.
  experimental: {
    optimizePackageImports: ["@fluentui/react-icons", "@fluentui/react-components"],
  },
  async rewrites() {
    // Proxy API calls to the FastAPI gateway so the browser uses same-origin /api.
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
};

export default nextConfig;
