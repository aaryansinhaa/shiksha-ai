import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/startConversation': 'http://localhost:5000',
      '/reply': 'http://localhost:5000',
      '/resetConversation': 'http://localhost:5000',
      '/conversation': 'http://localhost:5000',
      '/dashboard': 'http://localhost:5000',
      '/log': 'http://localhost:5000',
      '/protocols': 'http://localhost:5000',
      '/survey': 'http://localhost:5000',
      '/student': 'http://localhost:5000'
    }
  }
});
