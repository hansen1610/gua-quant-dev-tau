/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,
    swcMinify: true,
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://core-engine:8000/api/:path*',
            },
            {
                source: '/ws/:path*',
                destination: 'http://core-engine:8000/ws/:path*',
            },
        ];
    },
};

export default nextConfig;
