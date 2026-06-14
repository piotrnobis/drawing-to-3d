// Two bundled demo runs (baked from real pipeline runs via scripts/bake_gate.py).
// Gate rows are pre-computed by backend.agent.gate.evaluate — they match what the
// pipeline actually produced, so the demo table is honest, not mocked.

import type { DemoRun, GateRow } from "./types";

const B = "/demo/bracket";
const M = "/demo/manifold";

const bracketGate: GateRow[] = [
  { label: "base width", kind: "bbox_x", target: 72, tol: 0.5, measured: 72.007, status: "pass" },
  { label: "base depth", kind: "bbox_y", target: 35, tol: 0.5, measured: 35.008, status: "pass" },
  { label: "base thickness", kind: "thickness", target: 10, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "pillar height to hole center", kind: "spacing", target: 60, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "pillar width", kind: "spacing", target: 30, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "pillar top radius", kind: "other", target: 15, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "pillar base fillet radius", kind: "other", target: 15, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "rib width", kind: "thickness", target: 10, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "base hole pitch", kind: "hole_pitch", target: 48, tol: 0.5, measured: 48, status: "pass" },
  { label: "base hole distance from back", kind: "spacing", target: 23, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "base hole diameter", kind: "hole_diameter", target: 12, tol: 0.5, measured: 12, status: "pass" },
  { label: "base hole count", kind: "hole_count", target: 2, tol: 0.5, measured: 2, status: "pass" },
  { label: "boss thickness", kind: "thickness", target: 13, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "upper hole diameter", kind: "hole_diameter", target: 12, tol: 0.5, measured: 12, status: "pass" },
  { label: "boss diameter", kind: "hole_diameter", target: 30, tol: 0.5, measured: 30, status: "pass" },
  { label: "wall step offset", kind: "spacing", target: 5, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "bottom step height", kind: "spacing", target: 6, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "rib angle", kind: "other", target: 60, tol: 0.5, measured: null, status: "unmeasured" },
];

const manifoldGate: GateRow[] = [
  { label: "overall length (X)", kind: "bbox_x", target: 111.25, tol: 0.5, measured: 111.262, status: "pass" },
  { label: "overall depth (Y)", kind: "bbox_y", target: 57.5, tol: 0.5, measured: 57.518, status: "pass" },
  { label: "overall height (Z)", kind: "bbox_z", target: 78.75, tol: 0.5, measured: 78.757, status: "pass" },
  { label: "circular flange outer diameter", kind: "other", target: 57.5, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "circular flange bolt circle", kind: "bolt_circle", target: 47.5, tol: 0.5, measured: 47.5, status: "pass" },
  { label: "circular flange hole diameter", kind: "hole_diameter", target: 5, tol: 0.5, measured: 5, status: "pass" },
  { label: "circular flange hole count", kind: "hole_count", target: 4, tol: 0.5, measured: 4, status: "pass" },
  { label: "circular flange thickness", kind: "thickness", target: 5, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "main pipe inner diameter", kind: "hole_diameter", target: 20, tol: 0.5, measured: 20, status: "pass" },
  { label: "circular→oval flange spacing", kind: "spacing", target: 23.75, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "oval→square flange spacing", kind: "spacing", target: 51.25, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "square flange→outlet spacing", kind: "spacing", target: 36.25, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "oval flange hole pitch", kind: "hole_pitch", target: 35, tol: 0.5, measured: 35, status: "pass" },
  { label: "oval flange central radius", kind: "other", target: 12.5, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "oval flange lobe radius", kind: "other", target: 5, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "oval flange hole diameter", kind: "hole_diameter", target: 5, tol: 0.5, measured: 5, status: "pass" },
  { label: "oval flange hole count", kind: "hole_count", target: 2, tol: 0.5, measured: 2, status: "pass" },
  { label: "square flange width", kind: "other", target: 50, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "square flange hole pitch", kind: "hole_pitch", target: 40, tol: 0.5, measured: 40, status: "pass" },
  { label: "square flange corner fillet", kind: "other", target: 5, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "square flange hole diameter", kind: "hole_diameter", target: 5, tol: 0.5, measured: 5, status: "pass" },
  { label: "square flange hole count", kind: "hole_count", target: 4, tol: 0.5, measured: 4, status: "pass" },
  { label: "oval flange top height", kind: "spacing", target: 28.75, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "square flange top height", kind: "spacing", target: 50, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "main pipe bend radius", kind: "other", target: 18.75, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "right outlet offset from top", kind: "spacing", target: 17.5, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "right outlet outer diameter", kind: "other", target: 20, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "right outlet inner diameter", kind: "hole_diameter", target: 15, tol: 0.5, measured: 15, status: "pass" },
  { label: "oval neck outer diameter", kind: "other", target: 20, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "oval neck inner diameter", kind: "hole_diameter", target: 15, tol: 0.5, measured: 15, status: "pass" },
  { label: "main pipe vertical OD", kind: "other", target: 25, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "oval flange thickness", kind: "thickness", target: 3.75, tol: 0.5, measured: null, status: "unmeasured" },
  { label: "square flange thickness", kind: "thickness", target: 5, tol: 0.5, measured: null, status: "unmeasured" },
];

const BRACKET_FEATURES = [
  "base plate",
  "+ back lip",
  "+ corner fillets",
  "+ pillar",
  "+ pillar top",
  "+ right fillet",
  "+ left fillet",
  "+ boss",
  "+ rib",
  "+ base holes",
  "+ upper bore",
];

export const bracketRun: DemoRun = {
  id: "bracket",
  title: "Mounting bracket",
  subtitle: "staged build · 11 locked features",
  sourceDrawing: `${B}/source.png`,
  summary:
    "A vertical mounting bracket: a flat base plate with two bolt holes and a filleted upright pillar with a rounded, bored top boss, reinforced by a 60° triangular rib.",
  guess: "Shaft / pivot support bracket — holds a pin in the upper bore, bolted down through the base.",
  mode: "staged",
  stages: BRACKET_FEATURES.map((label, index) => ({ index, label, iso: `${B}/stage${index}.iso.png` })),
  views: { front: `${B}/final.front.png`, top: `${B}/final.top.png`, side: `${B}/final.side.png`, iso: `${B}/final.iso.png` },
  stepUrl: `${B}/final.step`,
  stlUrl: `${B}/final.stl`,
  gate: { rows: bracketGate, nPass: 7, nMeasured: 7, verdict: "PASS · 7/18 verified, 11 unmeasured" },
};

export const manifoldRun: DemoRun = {
  id: "manifold",
  title: "Multi-flange manifold",
  subtitle: "one-shot · verified first try",
  sourceDrawing: `${M}/source.png`,
  summary:
    "A multi-port pipe elbow with a 90° bend and three flanges — a round 4-bolt inlet, a 2-bolt oval branch, and a square 4-bolt outlet — plus a horizontal branch outlet.",
  guess: "Manifold / distribution elbow fitting — branches a main fluid line to auxiliary ports.",
  mode: "iter",
  stages: [
    { index: 0, label: "Analyze drawing", iso: `${M}/source.png` },
    { index: 1, label: "Generate CadQuery", iso: `${M}/final.front.png` },
    { index: 2, label: "Render + measure", iso: `${M}/final.top.png` },
    { index: 3, label: "Verify (3 signals)", iso: `${M}/final.iso.png` },
  ],
  views: { front: `${M}/final.front.png`, top: `${M}/final.top.png`, side: `${M}/final.side.png`, iso: `${M}/final.iso.png` },
  stepUrl: `${M}/final.step`,
  stlUrl: `${M}/final.stl`,
  gate: { rows: manifoldGate, nPass: 15, nMeasured: 15, verdict: "PASS · 15/33 verified, 18 unmeasured" },
};

export const demoRuns: DemoRun[] = [bracketRun, manifoldRun];
