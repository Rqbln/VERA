/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Single-origin deployment (user-study tunnel): with NEXT_PUBLIC_API_URL=""
  // the client uses relative URLs and Next proxies them to the local API, so
  // one tunnel on :3000 exposes the whole stack. Deployments that set an
  // absolute NEXT_PUBLIC_API_URL never hit these rewrites.
  async rewrites() {
    const api = process.env.STUDY_API_ORIGIN || "http://127.0.0.1:8000";
    return [
      { source: "/api/v1/:path*", destination: `${api}/api/v1/:path*` },
      { source: "/admin/:path*", destination: `${api}/admin/:path*` },
    ];
  },
};

export default nextConfig;
