/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/search', // The frontend will still call this simple name...
        destination: 'http://localhost:8000/api/v1/patron_search', // ...but we silently forward it here!
      },
    ]
  },
};

export default nextConfig;