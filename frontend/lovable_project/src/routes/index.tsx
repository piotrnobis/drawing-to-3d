import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect } from "react";
import { bracketRun } from "@/demo/runs";
import heroDrawing from "@/assets/hero-drawing.png";
import heroSolid from "@/assets/hero-solid.png";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Ortograph — from technical drawing to a verified, editable solid" },
      { name: "description", content: "Ortograph reads an orthographic engineering drawing and rebuilds it as a real parametric STEP model — then proves it right three ways: a vision critique, an independent judge, and every dimension measured." },
      { property: "og:title", content: "Ortograph — drawing to verified editable CAD" },
      { property: "og:description", content: "A drawing in. A solid you can trust, and edit, out." },
    ],
  }),
  component: Home,
});

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      els.forEach((e) => e.classList.add("in"));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add("in");
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, []);
}

function Home() {
  useReveal();
  return (
    <>
      <header className="hero">
        <div className="wrap">
          <div className="eyebrow">drawing → verified, editable CAD — what we built</div>
          <h1>A drawing in. A solid you can trust, and&nbsp;<span className="accentword">edit</span>, out.</h1>
          <p className="lead">Ortograph reads an orthographic engineering drawing and rebuilds it as a real parametric STEP model — then <b>proves it is right</b> three ways: a vision critique looks at it, an independent judge double-checks, and the geometry is measured against every callout. One conversation runs the whole loop.</p>

          <div className="io">
            <span><span className="k">Input</span><b>Drawing image</b><span>multi-view orthographic PNG / PDF</span></span>
            <span><span className="k">Output</span><b>STEP / STL model</b><span>editable B-rep, dimension-checked</span></span>
            <span><span className="k">Engine</span><b>One vision-LLM loop</b><span>analyze · generate · verify · refine</span></span>
          </div>

          <div style={{ marginTop: 26, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Link to="/demo" className="btn primary">Try the demo →</Link>
            <Link to="/pricing" className="btn ghost">See pricing</Link>
          </div>

          <div className="hero-fig reveal">
            <div className="col">
              <div className="frame"><img src={heroDrawing} alt="Orthographic engineering drawing of a multi-flange manifold" /></div>
              <div className="figcap">input · orthographic drawing</div>
            </div>
            <div className="mid">RECONSTRUCT<span className="sub">parametric · verified</span></div>
            <div className="col">
              <div className="frame"><img src={heroSolid} alt="Reconstructed parametric 3D solid (real run)" /></div>
              <div className="figcap">output · editable solid</div>
            </div>
          </div>
          <p className="figcap">FIG.01 — drawing in, solid out · reconstructed and verified end-to-end</p>
        </div>
      </header>

      <main className="wrap">

        <div className="dim-divider"><span className="tag"><span className="num">01</span> / the problem</span><span className="rule"></span></div>
        <section>
          <div className="sec-head reveal">
            <h2>A drawing is not a model.</h2>
            <p>Industry runs on millions of legacy 2D drawings with no 3D counterpart. To remake a part, an engineer rebuilds it by hand in CAD — slow, and exactly the structured visual reasoning a model should do. But two things make it hard.</p>
          </div>
          <div className="twocol">
            <div className="note reveal">
              <div className="k">It must be editable</div>
              <p>The output has to be a <b>parametric STEP B-rep</b>, not a mesh. A triangle soup looks fine and is useless — you cannot change a wall thickness or re-fit a bore on it.</p>
            </div>
            <div className="note reveal">
              <div className="k">Looking right isn't enough</div>
              <p>Inferring one solid consistent across three views is genuine spatial reasoning, and vision models are <b>weak at it</b>. A part that looks right but <b>measures wrong</b> is worthless. So checking is the product, not an afterthought.</p>
            </div>
          </div>
        </section>

        <div className="dim-divider"><span className="tag"><span className="num">02</span> / overview</span><span className="rule"></span></div>
        <section>
          <div className="sec-head reveal">
            <h2>One loop: understand → build → prove → fix.</h2>
            <p>Everything happens inside a single conversation, so each step carries the full context of the ones before it. The agent reasons about the drawing, writes CadQuery code (for complex parts, one feature at a time), runs it in a sandbox, then verifies the result with <b>three</b> independent signals and refines until they agree.</p>
          </div>
          <div className="loop reveal">
            <svg viewBox="0 0 880 250" role="img" aria-label="Ortograph agent loop">
              <defs>
                <marker id="lar" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--ink-soft)"/></marker>
                <marker id="rar" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--accent)"/></marker>
              </defs>
              <g fontFamily="'IBM Plex Mono',monospace" fontSize="12.5" textAnchor="middle">
                <g><rect x="14" y="34" width="120" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/><text x="74" y="56">analyze</text><text x="74" y="72" fontSize="10" fill="var(--ink-soft)">dimension table</text></g>
                <g><rect x="190" y="34" width="120" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/><text x="250" y="56">generate</text><text x="250" y="72" fontSize="10" fill="var(--ink-soft)">CadQuery code</text></g>
                <g><rect x="366" y="34" width="120" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/><text x="426" y="56">run + repair</text><text x="426" y="72" fontSize="10" fill="var(--ink-soft)">sandboxed</text></g>
                <g><rect x="542" y="34" width="130" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/><text x="607" y="56">render + measure</text><text x="607" y="72" fontSize="10" fill="var(--ink-soft)">views + B-rep</text></g>
                <g><rect x="728" y="34" width="130" height="50" rx="2" fill="var(--paper)" stroke="var(--pass)" strokeWidth="1.6"/><text x="793" y="56" fill="var(--pass)">verify</text><text x="793" y="72" fontSize="10" fill="var(--ink-soft)">eye · judge · ruler</text></g>
                <g stroke="var(--ink-soft)" strokeWidth="1.4" fill="none">
                  <line x1="134" y1="59" x2="186" y2="59" markerEnd="url(#lar)"/>
                  <line x1="310" y1="59" x2="362" y2="59" markerEnd="url(#lar)"/>
                  <line x1="486" y1="59" x2="538" y2="59" markerEnd="url(#lar)"/>
                  <line x1="672" y1="59" x2="724" y2="59" markerEnd="url(#lar)"/>
                </g>
                <path d="M404,84 C384,116 468,116 448,86" fill="none" stroke="var(--ink-soft)" strokeWidth="1.2" strokeDasharray="4 3" markerEnd="url(#lar)"/>
                <text x="426" y="126" fontSize="10" fill="var(--ink-soft)">code error → fix</text>
                <text x="793" y="108" fill="var(--pass)" fontSize="11">pass → export STEP ✓</text>
                <path d="M793,84 C793,200 250,210 250,90" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeDasharray="6 4" markerEnd="url(#rar)"/>
                <text x="470" y="206" fill="var(--accent)" fontSize="11" letterSpacing="1">refine: shape critique + failing dimensions → regenerate (keep the best)</text>
              </g>
            </svg>
            <div className="guards">
              <span className="guard"><b>one conversation</b> · full context</span>
              <span className="guard"><b>sandboxed</b> code execution</span>
              <span className="guard"><b>3 verifiers</b> · eye + judge + ruler</span>
              <span className="guard"><b>staged build</b> · complex parts</span>
              <span className="guard"><b>keep-best</b> · never ship a regression</span>
            </div>
          </div>
        </section>

        <div className="dim-divider"><span className="tag"><span className="num">03</span> / the pipeline</span><span className="rule"></span></div>
        <section>
          <div className="sec-head reveal">
            <h2>Six steps, end-to-end.</h2>
            <p>Each step maps to a module: the LLM layer, the sandboxed CAD runner, and the agent that orchestrates the loop.</p>
          </div>
          <div className="steps">
            <div className="step reveal">
              <div className="pk">Step 01 · read</div>
              <h3>Analyze</h3>
              <p>The model studies the drawing first — what the part is, a per-view breakdown, and a structured <b>dimension table</b> with every callout, value, tolerance and kind. This table is the ground truth the size check uses later.</p>
              <span className="mod">agent/analysis</span>
            </div>
            <div className="step reveal">
              <div className="pk">Step 02 · build</div>
              <h3>Generate</h3>
              <p>Grounded by its analysis, an embedded <b>CadQuery manual</b>, and a few <b>examples fetched live</b> (Tavily), the model writes a parametric script — Z-up, real CAD operations, one solid. Complex parts are built feature-by-feature.</p>
              <span className="mod">agent/prompts · retrieval</span>
            </div>
            <div className="step reveal">
              <div className="pk">Step 03 · run</div>
              <h3>Execute &amp; repair</h3>
              <p>The untrusted script runs in a <b>sandboxed subprocess</b> (scrubbed env, time-limited). If it errors, the traceback goes back into the same conversation and the model fixes it — cheaply, before any verification.</p>
              <span className="mod">cad/render</span>
            </div>
            <div className="step reveal">
              <div className="pk">Step 04 · observe</div>
              <h3>Render &amp; measure</h3>
              <p>From the solid we export STEP/STL and render <b>four views</b> (front/top/side/iso). We also measure the B-rep: bounding box, hole patterns (count, pitch, bolt-circle), and connectivity.</p>
              <span className="mod">cad/harness</span>
            </div>
            <div className="step reveal">
              <div className="pk">Step 05 · prove</div>
              <h3>Verify (3 signals)</h3>
              <p><b>Shape:</b> the vision model compares renders to the drawing. <b>Judge:</b> an independent Pro model double-checks any claimed pass. <b>Size:</b> a numeric gate measures the geometry. Verified only if all three agree.</p>
              <span className="mod">agent/gate</span>
            </div>
            <div className="step reveal">
              <div className="pk">Step 06 · fix</div>
              <h3>Refine (keep best)</h3>
              <p>If a check fails, the critique and failing numbers are fed back and the model edits the <b>best working script</b> — a minimal change, not a rewrite. Bounded iterations with <b>elitism</b>: we always return the best candidate, never a regression.</p>
              <span className="mod">agent/loop</span>
            </div>
          </div>
        </section>

        <div className="dim-divider"><span className="tag"><span className="num">04</span> / the idea that wins</span><span className="rule"></span></div>
        <section>
          <div className="sec-head reveal">
            <h2>We don't just generate. We verify — three ways.</h2>
            <p>The eye, an <i>independent</i> second opinion, and the ruler catch different errors, so we use all three and divide the labour cleanly: a vision critique and a separate judge model judge <i>shape</i>; the geometry kernel judges <i>size</i>. None is asked to do another's job.</p>
          </div>
          <div className="verify">
            <div className="signal reveal">
              <div className="k">Signal 1 · shape (the eye)</div>
              <h3>Does it look like the part?</h3>
              <p>In-conversation, the vision model compares the four rendered views to the drawing and flags only <b>obvious, structural</b> differences — a missing or extra feature, a bore that should be open but is solid, a major feature on the wrong face. Small details are ignored so a good model isn't nitpicked into a worse one.</p>
              <p>A deterministic <b>connectivity check</b> backs it up: more than one solid means the part fell apart — caught instantly, no LLM needed.</p>
            </div>
            <div className="signal reveal">
              <div className="k">Signal 2 · second opinion (the judge)</div>
              <h3>Would a fresh reviewer agree?</h3>
              <p>The self-critique shares the generator's context and tends to rationalize its own intent. So before we trust a pass, an <b>independent judge</b> weighs in — a stronger model with <b>no system prompt and no history</b>, shown only the drawing and the renders. It runs only to confirm a claimed pass, applies a high bar, and vetoes false positives the in-context critic waves through.</p>
            </div>
          </div>
          <div className="signal reveal" style={{ marginTop: 22 }}>
            <div className="k">Signal 3 · size (the ruler)</div>
            <h3>Does it measure right?</h3>
            <p>We query the actual solid and check each callout within tolerance. Beyond overall size and bore diameters, the gate verifies <b>hole patterns precisely</b> — count, hole-to-hole pitch, and bolt-circle diameter — per flange, catching mis-placed screws the eye cannot judge. Every verdict reports its <b>coverage</b> so a thin check never masquerades as a strong one.</p>
            <table className="dim">
              <thead><tr><th>Dimension</th><th>kind</th><th className="r">spec</th><th className="r">built</th><th>status</th></tr></thead>
              <tbody>
                <tr><td>Overall length (X)</td><td>bbox_x</td><td className="r">111.25</td><td className="r">111.26</td><td><span className="pill pass">PASS</span></td></tr>
                <tr><td>Circular flange bolt circle</td><td>bolt_circle</td><td className="r">47.5</td><td className="r">47.5</td><td><span className="pill pass">PASS</span></td></tr>
                <tr><td>Square flange hole pitch</td><td>hole_pitch</td><td className="r">40</td><td className="r">40</td><td><span className="pill pass">PASS</span></td></tr>
                <tr><td>Circular flange hole count</td><td>hole_count</td><td className="r">4</td><td className="r">4</td><td><span className="pill pass">PASS</span></td></tr>
                <tr><td>Main pipe inner diameter</td><td>hole_diameter</td><td className="r">20</td><td className="r">20</td><td><span className="pill pass">PASS</span></td></tr>
                <tr><td>Square flange thickness</td><td>thickness</td><td className="r">5</td><td className="r">—</td><td><span className="pill na">N/A</span></td></tr>
              </tbody>
            </table>
            <p className="caption"><b>Real run</b> (multi-flange manifold) — <b>15 / 15</b> measurable dims passed; 18 are kinds we don't measure yet (<span className="pill na">N/A</span>, honest — never a false pass).</p>
          </div>
          <div className="callout reveal">
            <p><b>The gate has teeth.</b> Inject a fault — build a 30&nbsp;mm bolt pattern where the drawing calls 40 — and the gate fails it deterministically: <span className="mono">"hole pitch: expected 40 ±0.5 mm but measured 30 mm"</span>. The eye would wave that through; the ruler does not.</p>
          </div>
        </section>

        <div className="dim-divider"><span className="tag"><span className="num">05</span> / under the hood</span><span className="rule"></span></div>
        <section>
          <div className="sec-head reveal">
            <h2>Two mechanisms worth a closer look.</h2>
            <p>The <b>independent judge</b> stops the model grading its own homework. The <b>staged build</b> stops a complex part collapsing under one giant script. Here is how each works.</p>
          </div>

          <h3 style={{ margin: "0 0 8px" }}>The independent judge — fresh eyes on every claimed pass</h3>
          <p style={{ color: "var(--ink-soft)", maxWidth: "70ch", margin: "0 0 18px" }}>The self-critique runs <i>inside</i> the generation conversation, so it has seen the model's intent and is lenient on its own work. The judge shares none of that: a stronger model, called with no system prompt and no history, handed only the drawing and the renders. It fires only when the cheap critique already claims a pass, applies a high bar, and vetoes false positives.</p>
          <div className="loop reveal">
            <svg viewBox="0 0 880 206" role="img" aria-label="Independent-judge verification gate">
              <defs>
                <marker id="ja" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--ink-soft)"/></marker>
                <marker id="jg" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--pass)"/></marker>
                <marker id="jr" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--accent)"/></marker>
              </defs>
              <g fontFamily="'IBM Plex Mono',monospace" fontSize="12" textAnchor="middle">
                <rect x="8" y="28" width="116" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/>
                <text x="66" y="50">render</text><text x="66" y="66" fontSize="9.5" fill="var(--ink-soft)">4 views + B-rep</text>
                <rect x="168" y="28" width="140" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/>
                <text x="238" y="50">self-critique</text><text x="238" y="66" fontSize="9.5" fill="var(--ink-soft)">in conversation</text>
                <text x="238" y="98" fontSize="9.5" fill="var(--ink-soft)">shares the model's context</text>
                <rect x="356" y="28" width="116" height="50" rx="2" fill="var(--paper)" stroke="var(--ink-soft)" strokeWidth="1.3" strokeDasharray="3 3"/>
                <text x="414" y="50">claims a</text><text x="414" y="66">match?</text>
                <rect x="520" y="28" width="158" height="50" rx="2" fill="var(--paper)" stroke="var(--accent)" strokeWidth="1.7"/>
                <text x="599" y="48" fill="var(--accent)">independent judge</text><text x="599" y="64" fontSize="9.5" fill="var(--ink-soft)">3.1-pro · no context</text>
                <text x="599" y="98" fontSize="9.5" fill="var(--ink-soft)">only the drawing + renders</text>
                <rect x="726" y="28" width="146" height="50" rx="2" fill="var(--paper)" stroke="var(--pass)" strokeWidth="1.7"/>
                <text x="799" y="50" fill="var(--pass)">verified ✓</text><text x="799" y="66" fontSize="9.5" fill="var(--ink-soft)">+ gate passes</text>
                <g stroke="var(--ink-soft)" strokeWidth="1.4" fill="none">
                  <line x1="124" y1="53" x2="164" y2="53" markerEnd="url(#ja)"/>
                  <line x1="308" y1="53" x2="352" y2="53" markerEnd="url(#ja)"/>
                  <line x1="472" y1="53" x2="516" y2="53" markerEnd="url(#ja)"/>
                </g>
                <text x="494" y="42" fontSize="9" fill="var(--pass)">yes</text>
                <line x1="678" y1="53" x2="722" y2="53" stroke="var(--pass)" strokeWidth="1.7" fill="none" markerEnd="url(#jg)"/>
                <text x="700" y="42" fontSize="9" fill="var(--pass)">agrees</text>
                <path d="M414,78 L414,156" stroke="var(--accent)" strokeWidth="1.3" strokeDasharray="5 3" fill="none"/>
                <text x="414" y="94" fontSize="9" fill="var(--accent)">no</text>
                <path d="M599,78 L599,156" stroke="var(--accent)" strokeWidth="1.3" strokeDasharray="5 3" fill="none"/>
                <text x="599" y="94" fontSize="9" fill="var(--accent)">vetoes</text>
                <path d="M599,156 L66,156 L66,80" stroke="var(--accent)" strokeWidth="1.4" strokeDasharray="6 4" fill="none" markerEnd="url(#jr)"/>
                <text x="300" y="174" fill="var(--accent)" fontSize="10.5">no match, or the judge vetoes a false positive → refine &amp; retry</text>
              </g>
            </svg>
          </div>

          <h3 style={{ margin: "34px 0 8px" }}>The staged build — one verified feature at a time</h3>
          <p style={{ color: "var(--ink-soft)", maxWidth: "70ch", margin: "0 0 18px" }}>A single 200-line script for a complex part is brittle: fix one feature and the model rewrites the whole thing, breaking three others. So it plans the part as an ordered list of features — solids first, then cuts — and builds them one at a time, each stage extending the last script that rendered, locked before the next is added.</p>
          <div className="loop reveal">
            <svg viewBox="0 0 880 188" role="img" aria-label="Staged feature-by-feature build">
              <defs>
                <marker id="sa" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--ink-soft)"/></marker>
                <marker id="sg" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--pass)"/></marker>
              </defs>
              <g fontFamily="'IBM Plex Mono',monospace" fontSize="11" textAnchor="middle">
                <text x="440" y="16" fontSize="10" fill="var(--ink-soft)">each step extends the previous working script — adds exactly one feature, then re-checks</text>
                <rect x="6" y="36" width="100" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/>
                <text x="56" y="58">plan</text><text x="56" y="74" fontSize="9" fill="var(--ink-soft)">solids → cuts</text>
                <rect x="124" y="36" width="84" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/><text x="166" y="60">base</text>
                <rect x="232" y="36" width="84" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/><text x="274" y="60">+ column</text>
                <rect x="340" y="36" width="84" height="50" rx="2" fill="var(--paper)" stroke="var(--ink)" strokeWidth="1.4"/><text x="382" y="60">+ pillars</text>
                <rect x="448" y="36" width="84" height="50" rx="2" fill="var(--paper)" stroke="var(--accent)" strokeWidth="1.5"/><text x="490" y="60" fill="var(--accent)">+ arch</text>
                <rect x="556" y="36" width="84" height="50" rx="2" fill="var(--paper)" stroke="var(--accent)" strokeWidth="1.5"/><text x="598" y="60" fill="var(--accent)">+ window</text>
                <rect x="664" y="36" width="84" height="50" rx="2" fill="var(--paper)" stroke="var(--accent)" strokeWidth="1.5"/><text x="706" y="60" fill="var(--accent)">+ U-cuts</text>
                <rect x="772" y="36" width="102" height="50" rx="2" fill="var(--paper)" stroke="var(--pass)" strokeWidth="1.6"/>
                <text x="823" y="56" fill="var(--pass)">base model</text><text x="823" y="72" fontSize="9" fill="var(--ink-soft)">→ refine loop</text>
                <g stroke="var(--ink-soft)" strokeWidth="1.3" fill="none">
                  <line x1="106" y1="61" x2="122" y2="61" markerEnd="url(#sa)"/>
                  <line x1="208" y1="61" x2="230" y2="61" markerEnd="url(#sa)"/>
                  <line x1="316" y1="61" x2="338" y2="61" markerEnd="url(#sa)"/>
                  <line x1="424" y1="61" x2="446" y2="61" markerEnd="url(#sa)"/>
                  <line x1="532" y1="61" x2="554" y2="61" markerEnd="url(#sa)"/>
                  <line x1="640" y1="61" x2="662" y2="61" markerEnd="url(#sa)"/>
                </g>
                <line x1="748" y1="61" x2="770" y2="61" stroke="var(--pass)" strokeWidth="1.5" fill="none" markerEnd="url(#sg)"/>
                <g fontSize="9" fill="var(--pass)">
                  <text x="166" y="104">✓ lock</text><text x="274" y="104">✓ lock</text><text x="382" y="104">✓ lock</text>
                  <text x="490" y="104">✓ lock</text><text x="598" y="104">✓ lock</text><text x="706" y="104">✓ lock</text>
                </g>
                <text x="440" y="138" fontSize="9.5" fill="var(--ink-soft)">rendered &amp; connectivity-checked every stage · a stage that won't render is skipped, the rest continue</text>
              </g>
            </svg>
          </div>

          <h3 style={{ margin: "34px 0 8px" }}>Watch it build — 11 locked stages, one real run</h3>
          <p style={{ color: "var(--ink-soft)", maxWidth: "70ch", margin: "0 0 16px" }}>A mounting bracket, reconstructed feature-by-feature. Every frame is a real render straight from that run — the drawing in, the verified solid out.</p>
          <div className="hero-fig reveal" style={{ marginTop: 0 }}>
            <div className="col"><div className="frame"><img src={bracketRun.sourceDrawing} alt="bracket drawing" /></div><div className="figcap">the drawing — input</div></div>
            <div className="mid">11 stages<span className="sub">solids → cuts</span></div>
            <div className="col"><div className="frame"><img src={bracketRun.views.iso} alt="final bracket solid" /></div><div className="figcap">verified solid — output</div></div>
          </div>
          <div className="stages-grid reveal">
            {bracketRun.stages.slice(0, 10).map((s, i) => (
              <figure className="shot" key={s.index}>
                <img src={s.iso} alt={`stage ${i + 1}`} loading="lazy" />
                <figcaption><span className="n">{String(i + 1).padStart(2, "0")}</span>{s.label}</figcaption>
              </figure>
            ))}
          </div>
          <p className="caption" style={{ marginTop: 12 }}>Stages 01–10, each rendered, connectivity-checked and <b>locked</b> before the next. Stage 11 (the through-bore) yields the finished solid above — which then enters the three-signal verify loop.</p>
        </section>

        <div className="dim-divider"><span className="tag"><span className="num">06</span> / engineering &amp; guards</span><span className="rule"></span></div>
        <section>
          <div className="split">
            <div>
              <h3 style={{ marginBottom: 14 }}>How it stays robust</h3>
              <ul className="clean">
                <li><span className="t">CTX</span><b>One conversation, many turns.</b> Analyze, generate, repair, critique and refine are turns in the same chat — the model fixes its own prior code with full context.</li>
                <li><span className="t">JDG</span><b>Independent judge.</b> A separate Pro model with no context double-checks every claimed pass — the generator can't rubber-stamp its own work.</li>
                <li><span className="t">STG</span><b>Staged build.</b> Complex parts are assembled one verified feature at a time, so a new feature only stacks on a solid that already renders.</li>
                <li><span className="t">SEC</span><b>Sandboxed execution.</b> Model-written CadQuery never runs in our process — only in a subprocess with a scrubbed environment and a hard timeout.</li>
                <li><span className="t">DOC</span><b>Manual + live examples.</b> An embedded CadQuery guide plus a few examples retrieved at generation time (Tavily) lift first-try quality.</li>
              </ul>
            </div>
            <div>
              <h3 style={{ marginBottom: 14 }}>Loop guards</h3>
              <div className="guards" style={{ justifyContent: "flex-start" }}>
                <span className="guard"><b>repair</b> code errors first</span>
                <span className="guard"><b>anchored</b> refine · minimal edit</span>
                <span className="guard"><b>keep-best</b> elitism</span>
                <span className="guard"><b>connectivity</b> must be 1 solid</span>
                <span className="guard"><b>Z-up</b> · centered on origin</span>
                <span className="guard"><b>traces</b> for every run</span>
              </div>
              <h3 style={{ margin: "22px 0 14px" }}>Stack</h3>
              <ul className="clean">
                <li><span className="t">LLM</span><b>Gemini</b> — a vision model for the loop; a Pro tier as the independent judge.</li>
                <li><span className="t">CAD</span><b>CadQuery / OpenCASCADE</b> — true B-rep, STEP/STL export, B-rep measurement.</li>
                <li><span className="t">RNDR</span><b>VTK (headless)</b> — clay-gray views with feature edges, so cuts read clearly.</li>
                <li><span className="t">RAG</span><b>Tavily</b> — live CadQuery-example retrieval, best-effort and optional.</li>
              </ul>
            </div>
          </div>
          <div className="scope reveal">
            <p><b>Honest scope.</b> We win by nailing a few real part classes end-to-end with a passing dimension table — not by gesturing at every possible part. The substance is a backend that demonstrably reconstructs and verifies real drawings; the UI is the wrapper.</p>
          </div>
          <div style={{ marginTop: 30, display: "flex", gap: 14, flexWrap: "wrap" }}>
            <Link to="/demo" className="btn primary">Run the demo</Link>
            <Link to="/about" className="btn ghost">Meet the team</Link>
          </div>
        </section>
      </main>
    </>
  );
}
