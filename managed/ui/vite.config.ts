import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Base '/ui/' matches the edge path split (design §3/§11): the ui image is
// served under /ui by the front proxy in every environment, including e2e.
export default defineConfig({
  base: "/ui/",
  plugins: [react()],
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
