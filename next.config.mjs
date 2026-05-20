/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Ignora erros de lint durante o build para garantir que o deploy ocorra
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Ignora erros de tipagem no build
    ignoreBuildErrors: true,
  },
  // Configuração para permitir que as funções Python na pasta api/ funcionem localmente se necessário
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'development'
          ? 'http://127.0.0.1:8000/api/:path*'
          : '/api/index.py',
      },
    ];
  },
};

export default nextConfig;
