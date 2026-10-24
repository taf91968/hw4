import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The FastAPI backend runs on port 8000. Proxying /api and /media means the
// frontend can use relative URLs (the same ones the backend returns) with no CORS setup.
const backend = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": backend,
      "/media": backend,
    },
  },
});
