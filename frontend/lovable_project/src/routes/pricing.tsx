import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/pricing")({
  head: () => ({
    meta: [
      { title: "Pricing — Ortograph" },
      { name: "description", content: "Simple pricing for Ortograph. Free for 3 generations a day, €29.90 for unlimited and API access, or custom for parallel processing." },
      { property: "og:title", content: "Pricing — Ortograph" },
      { property: "og:description", content: "Three tiers. No surprises." },
    ],
  }),
  component: Pricing,
});

function Pricing() {
  return (
    <main className="wrap" style={{ paddingTop: 56, paddingBottom: 40 }}>
      <div className="eyebrow">Pricing · simple by design</div>
      <h1 style={{ marginTop: 14 }}>Pick a tier.<br />Start building.</h1>
      <p className="lead" style={{ marginTop: 14 }}>
        Three plans. No per-seat math, no hidden export fees. Upgrade when you outgrow it.
      </p>

      <div className="tiers">
        <div className="tier">
          <div className="name">Free</div>
          <div className="price">€0<small>/ month</small></div>
          <div className="desc">For tinkerers and one-off jobs.</div>
          <ul>
            <li>3 generations per day</li>
            <li>STEP export</li>
            <li>3D preview &amp; dimension report</li>
            <li>Community support</li>
          </ul>
          <Link to="/demo" className="btn ghost">Start free</Link>
        </div>

        <div className="tier featured">
          <div className="name">Pro</div>
          <div className="price">€29.90<small>/ month</small></div>
          <div className="desc">For engineers who ship parts.</div>
          <ul>
            <li>Unlimited generations</li>
            <li>API access</li>
            <li>Priority processing queue</li>
            <li>Refine loop &amp; tolerance tuning</li>
            <li>Email support</li>
          </ul>
          <Link to="/demo" className="btn primary">Go Pro</Link>
        </div>

        <div className="tier">
          <div className="name">Custom</div>
          <div className="price">Talk to us<small></small></div>
          <div className="desc">For teams and production lines.</div>
          <ul>
            <li>Dedicated integration</li>
            <li>Parallel batch processing</li>
            <li>On-prem / VPC deployment</li>
            <li>SLA &amp; named engineer</li>
            <li>Custom rulebooks</li>
          </ul>
          <a href="mailto:hello@ortograph.io" className="btn ghost">Contact sales</a>
        </div>
      </div>
    </main>
  );
}
