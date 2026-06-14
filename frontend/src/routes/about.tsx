import { createFileRoute } from "@tanstack/react-router";
import pnPic from "@/assets/pn.jpg";
import cdPic from "@/assets/cd.jpg";
import dchenPic from "@/assets/dchen.jpg";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — Ortograph team" },
      { name: "description", content: "Meet the team behind Ortograph: computer vision, machine learning, and research engineers turning drawings into editable CAD." },
      { property: "og:title", content: "About — Ortograph team" },
      { property: "og:description", content: "The people building Ortograph." },
    ],
  }),
  component: About,
});

const team = [
  { name: "Piotr Nobis", role: "Computer Vision · Marketing", img: pnPic },
  { name: "Carlos Barbera Domingo", role: "ML Engineer · Business", img: cdPic },
  { name: "Danqing Chen", role: "Researcher", img: dchenPic },
];

function About() {
  return (
    <main className="wrap" style={{ paddingTop: 56, paddingBottom: 40 }}>
      <div className="eyebrow">About · the team</div>
      <h1 style={{ marginTop: 14 }}>Engineers who got tired of redrawing parts.</h1>
      <p className="lead" style={{ marginTop: 14 }}>
        Ortograph is a small team obsessed with one problem: turning the world's mountain of legacy 2D drawings into models you can actually work with.
      </p>

      <div className="team-grid">
        {team.map((m) => (
          <div key={m.name} className="member">
            <div className="pic"><img src={m.img} alt={m.name} /></div>
            <div className="meta">
              <div className="nm">{m.name}</div>
              <div className="rl">{m.role}</div>
            </div>
          </div>
        ))}
        <div className="member mystery">
          <div className="pic">?</div>
          <div className="meta">
            <div className="nm">Open seat</div>
            <div className="rl">Business strategist · join us</div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 40, borderLeft: "2px solid var(--accent)", paddingLeft: 18, color: "var(--ink-soft)" }}>
        <p style={{ margin: 0 }}>
          <b style={{ color: "var(--ink)" }}>We're hiring.</b> If you live somewhere between a CAD kernel and a vision model and want to ship something engineers actually use — reach out at{" "}
          <a href="mailto:hello@ortograph.io" style={{ color: "var(--accent)" }}>hello@ortograph.io</a>.
        </p>
      </div>
    </main>
  );
}
