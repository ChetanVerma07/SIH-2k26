import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cesium from 'vite-plugin-cesium';
export default defineConfig({
    plugins: [react(), cesium()],
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './tests/setup.ts',
    },
});
