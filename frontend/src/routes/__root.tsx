import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { type ReactNode } from "react";

import appCss from "../styles.css?url";

function NotFoundComponent() {
  return (
    <div className="wrap" style={{ padding: "120px 28px", textAlign: "center" }}>
      <div className="eyebrow">404</div>
      <h1 style={{ marginTop: 16 }}>Page not found</h1>
      <p className="lead" style={{ margin: "16px auto" }}>The page you're looking for doesn't exist.</p>
      <Link to="/" className="btn primary" style={{ display: "inline-block", marginTop: 12 }}>Go home</Link>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();

  return (
    <div className="wrap" style={{ padding: "120px 28px", textAlign: "center" }}>
      <h1>Something went wrong</h1>
      <p className="lead" style={{ margin: "16px auto" }}>Try again or head home.</p>
      <div style={{ display: "flex", gap: 10, justifyContent: "center", marginTop: 18 }}>
        <button className="btn primary" onClick={() => { router.invalidate(); reset(); }}>Try again</button>
        <a className="btn ghost" href="/">Go home</a>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Ortograph — drawings into verified, editable 3D models" },
      { name: "description", content: "Ortograph turns 2D technical drawings into parametric, editable 3D CAD models — and proves them right." },
      { property: "og:title", content: "Ortograph — drawings into verified, editable 3D models" },
      { property: "og:description", content: "Turn any orthographic drawing into a verified STEP-ready parametric solid." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
    links: [{ rel: "stylesheet", href: appCss }],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function TopBar() {
  return (
    <div className="topbar">
      <div className="wrap">
        <Link to="/" className="brand"><b>△</b> ORTOGRAPH</Link>
        <nav className="topnav">
          <Link to="/" activeOptions={{ exact: true }}>Home</Link>
          <Link to="/demo">Demo</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/about">About</Link>
        </nav>
        <div className="topmeta">drawing → parametric CAD</div>
      </div>
    </div>
  );
}

function SiteFooter() {
  return (
    <footer>
      <div className="wrap">
        <span><b>ORTOGRAPH</b> · drawing → verified editable solid</span>
        <span>Kyrall track · Munich AI Hackathon</span>
        <span>v0.3 · © 2026</span>
      </div>
    </footer>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      <TopBar />
      <Outlet />
      <SiteFooter />
    </QueryClientProvider>
  );
}
