// The seam between the UI and "how a drawing gets reconstructed".
// Today: DemoRunner replays a bundled run with timers (no backend, no waiting).
// Later: an ApiRunner with the SAME interface POSTs to the Python FastAPI and
// streams real progress — swap the instance, the UI doesn't change.

import { demoRuns } from "./runs";
import type { DemoRun } from "./types";

export interface RunUpdate {
  stageIndex: number;
  label: string;
  isoUrl?: string;
}

export interface RunResult {
  run: DemoRun;
}

export interface RunOptions {
  runId: string;
  onStage: (u: RunUpdate) => void;
  stageMs?: number;
  signal?: AbortSignal;
}

export interface DrawingRunner {
  runDrawing(opts: RunOptions): Promise<RunResult>;
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(new DOMException("aborted", "AbortError"));
    const id = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(id);
        reject(new DOMException("aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

/** Replays a bundled run by stepping through its stages on a timer. */
export class DemoRunner implements DrawingRunner {
  async runDrawing({ runId, onStage, stageMs = 750, signal }: RunOptions): Promise<RunResult> {
    const run = demoRuns.find((r) => r.id === runId) ?? demoRuns[0];
    for (let i = 0; i < run.stages.length; i++) {
      const s = run.stages[i];
      onStage({ stageIndex: i, label: s.label, isoUrl: s.iso });
      await delay(stageMs, signal);
    }
    return { run };
  }
}

export const demoRunner = new DemoRunner();
