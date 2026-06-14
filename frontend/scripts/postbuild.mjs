// After `vite build`, TanStack Start's SPA mode emits the app shell as `_shell.html`.
// Static hosts (Cloudflare Pages) serve `index.html` for `/` and `404.html` for unmatched
// paths, so copy the shell to both. The client router then handles every route.
import { copyFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const dir = resolve("dist/client");
const shell = resolve(dir, "_shell.html");

if (!existsSync(shell)) {
  console.error("postbuild: dist/client/_shell.html not found — is SPA mode enabled in vite.config.ts?");
  process.exit(1);
}

for (const name of ["index.html", "404.html"]) {
  copyFileSync(shell, resolve(dir, name));
  console.log(`postbuild: wrote dist/client/${name}`);
}
