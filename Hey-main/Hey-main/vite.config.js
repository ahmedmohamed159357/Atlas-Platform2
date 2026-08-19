import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
            '@components': path.resolve(__dirname, './src/components'),
            '@features': path.resolve(__dirname, './src/features'),
            '@store': path.resolve(__dirname, './src/store'),
            '@types': path.resolve(__dirname, './src/types'),
            '@services': path.resolve(__dirname, './src/services'),
            '@utils': path.resolve(__dirname, './src/utils'),
            '@hooks': path.resolve(__dirname, './src/hooks'),
            '@config': path.resolve(__dirname, './src/config'),
            '@plugins-core': path.resolve(__dirname, './src/plugins-core'),
            '@constants': path.resolve(__dirname, './src/constants'),
        },
    },
    server: {
        port: 5000,
        host: '0.0.0.0',
        allowedHosts: true,
        open: false,
        proxy: {
            '/api': {
                target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:9001',
                changeOrigin: true,
                secure: false,
            },
            '/hive': {
                target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:9001',
                changeOrigin: true,
                secure: false,
                ws: true,
            },
        },
    },
});
