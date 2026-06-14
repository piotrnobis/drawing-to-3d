// Demo data layer — typed model of a bundled previous run, replayed client-side.
// No backend: every URL points at a static file under public/demo/<run>/.

export type GateStatus = "pass" | "fail" | "unmeasured";

export interface GateRow {
  label: string;
  kind: string;
  target: number;
  tol: number;
  measured: number | null;
  status: GateStatus;
}

export interface DemoStage {
  index: number;
  label: string;
  /** Preview image shown while this stage is "active" (public/demo/<run>/...). */
  iso: string;
}

export interface DemoRun {
  id: "bracket" | "manifold";
  title: string;
  subtitle: string;
  sourceDrawing: string;
  summary: string;
  guess: string;
  /** "staged" = real feature-by-feature build; "iter" = one-shot analyze→verify. */
  mode: "staged" | "iter";
  stages: DemoStage[];
  views: { front: string; top: string; side: string; iso: string };
  stepUrl: string;
  stlUrl: string;
  gate: { rows: GateRow[]; nPass: number; nMeasured: number; verdict: string };
}
