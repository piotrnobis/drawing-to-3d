import { defineConfig } from "vite";
import tsConfigPaths from "vite-tsconfig-paths";
import tailwindcss from "@tailwindcss/vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";

// GitHub Pages serves from a project subpath (piotrnobis.github.io/drawing-to-3d/), so the
// build needs that base. CI sets PAGES_BASE; local dev/build stays at the root "/".
// Deployed to Cloudflare Pages, which serves at a root URL — so the default base "/" is correct
// and no asset-path juggling is needed. (PAGES_BASE stays available if a subpath host is ever used.)
const BASE = process.env.PAGES_BASE ?? "/";

export default defineConfig({
  base: BASE,
  server: { port: 8080 },
  resolve: { dedupe: ["react", "react-dom"] },
  plugins: [
    tsConfigPaths(),
    tailwindcss(),
    tanstackStart({
      // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
      server: { entry: "server" },
      // Static SPA build for Pages: prerender one shell; the client router handles every route
      // (routing base is derived from vite `base`). The deploy workflow copies the shell to
      // 404.html so deep links fall back to it.
      spa: { enabled: true },
    }),
    viteReact(),
  ],
});
