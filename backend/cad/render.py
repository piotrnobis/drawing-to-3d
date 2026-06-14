"""Render untrusted CadQuery scripts for debugging.

`render_file` / `render_code` run a CadQuery script in a sandboxed subprocess
(scrubbed environment, time-limited) and export the resulting model to STEP /
STL / SVG. Nothing is ever `exec`'d in this process — the actual execution
happens in `_harness.py` inside the child process.
"""

import base64
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

_HARNESS = Path(__file__).with_name("_harness.py")
DEFAULT_FORMATS = ("step", "stl", "svg")
DEFAULT_TIMEOUT = 60  # seconds; untrusted code may hang or loop

# The harness also renders these snapshot views (keys in `outputs`).
_VIEWS = ("front", "top", "side", "iso")

# Env var names matching any of these are dropped before handing the
# environment to the untrusted child, so the script can't read our secrets.
_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "GEMINI")


@dataclass
class RenderResult:
    ok: bool
    outputs: dict[str, Path] = field(default_factory=dict)
    measurements: dict = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""

    def __bool__(self) -> bool:
        return self.ok


# Self-contained three.js viewer. The STL is embedded as base64 so the file
# works by double-clicking (no server / no file:// CORS issues). three.js itself
# loads from a CDN, so a network connection is needed to view.
_VIEWER_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__TITLE__ — CadQuery debug viewer</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #15171c; }
  #hud { position: fixed; top: 10px; left: 12px; font: 12px/1.4 system-ui, sans-serif;
         color: #9aa4b2; user-select: none; }
  #hud b { color: #e6e9ef; }
</style>
<script type="importmap">
{ "imports": {
  "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
  "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
}}
</script>
</head>
<body>
<div id="hud"><b>__TITLE__</b> · drag to orbit · scroll to zoom</div>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

// CAD convention: Z is up (matches how the model is built and rendered).
THREE.Object3D.DEFAULT_UP.set(0, 0, 1);

const b64 = "__B64__";
const bin = atob(b64);
const bytes = new Uint8Array(bin.length);
for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x15171c);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100000);
camera.up.set(0, 0, 1);

const geometry = new STLLoader().parse(bytes.buffer);
geometry.computeVertexNormals();
geometry.computeBoundingBox();
const bb = geometry.boundingBox;
const center = new THREE.Vector3();
bb.getCenter(center);
geometry.translate(-center.x, -center.y, -center.z);
const size = new THREE.Vector3();
bb.getSize(size);
const radius = Math.max(size.x, size.y, size.z) || 1;

const mesh = new THREE.Mesh(
  geometry,
  new THREE.MeshStandardMaterial({ color: 0x4c8bf5, metalness: 0.1, roughness: 0.55 })
);
scene.add(mesh);

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const key = new THREE.DirectionalLight(0xffffff, 0.9);
key.position.set(1, 1, 1);
scene.add(key);
const fill = new THREE.DirectionalLight(0xffffff, 0.4);
fill.position.set(-1, -0.5, -1);
scene.add(fill);
const grid = new THREE.GridHelper(radius * 4, 20, 0x2a2f3a, 0x22262e);
grid.rotateX(Math.PI / 2);  // lay the grid in the XY plane (Z up)
scene.add(grid);

camera.position.set(radius * 2, -radius * 2, radius * 1.5);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 0, 0);

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

(function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
})();
</script>
</body>
</html>
"""


def _write_viewer(stl_path: Path) -> Path:
    """Write a self-contained three.js HTML viewer next to (and embedding) the STL."""
    b64 = base64.b64encode(stl_path.read_bytes()).decode("ascii")
    html = _VIEWER_TEMPLATE.replace("__TITLE__", stl_path.stem).replace("__B64__", b64)
    html_path = stl_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    return html_path


def _scrubbed_env() -> dict[str, str]:
    """Copy the current env minus anything that looks like a secret.

    Keeping the rest (PATH, SYSTEMROOT, conda dirs) is what lets the child
    actually start and load CadQuery's native libraries on Windows.
    """
    return {
        k: v
        for k, v in os.environ.items()
        if not any(marker in k.upper() for marker in _SECRET_MARKERS)
    }


def render_file(
    script_path: str | Path,
    out_dir: str | Path = "renders",
    name: str | None = None,
    formats: Sequence[str] = DEFAULT_FORMATS,
    timeout: float = DEFAULT_TIMEOUT,
    viewer: bool = True,
) -> RenderResult:
    """Run a CadQuery script file in the sandbox and export its model.

    The script must assign its model to a variable named `result` or call
    `show_object(model)`. Returns a `RenderResult` with the written file paths
    and captured stdout/stderr (truthy on success).

    If `viewer` is set and an STL was produced, also writes a self-contained
    `<name>.html` three.js viewer (added to `outputs` under "html").
    """
    script_path = Path(script_path)
    out_dir = Path(out_dir)
    name = name or script_path.stem

    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(_HARNESS),
                str(script_path),
                str(out_dir),
                name,
                ",".join(formats),
            ],
            env=_scrubbed_env(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        # A hanging script (e.g. a pathological sweep/hull) is just a failed
        # render — surface it as stderr so the refine loop can react to it.
        return RenderResult(
            ok=False,
            stdout=e.stdout or "",
            stderr=f"TimeoutError: render exceeded {timeout:g}s and was killed.\n{e.stderr or ''}",
        )

    # Scan for artifacts regardless of exit code. View rendering runs LAST in the
    # harness and can hard-crash the child on a headless/GPU-less box (VTK/OpenGL:
    # "GLEW could not be initialized") AFTER the geometry — STEP/STL + measurements —
    # was already exported. That geometry is valid; only the PNG snapshots are missing.
    # Each attempt writes a uniquely-named file, so a present file always belongs to
    # this run (no stale-file false positives).
    outputs: dict[str, Path] = {}
    measurements: dict = {}
    for fmt in formats:
        ext = fmt if fmt.startswith(".") else f".{fmt}"
        candidate = out_dir / f"{name}{ext}"
        if candidate.exists():
            outputs[fmt] = candidate

    if viewer and "stl" in outputs:
        outputs["html"] = _write_viewer(outputs["stl"])

    # Snapshot views + measurements emitted by the harness.
    for view in _VIEWS:
        png = out_dir / f"{name}.{view}.png"
        if png.exists():
            outputs[f"view_{view}"] = png
    meas_path = out_dir / f"{name}.measurements.json"
    if meas_path.exists():
        outputs["measurements"] = meas_path
        measurements = json.loads(meas_path.read_text(encoding="utf-8"))

    # A render is usable if the model was exported AND measured — even if the child
    # later crashed while rendering the PNG views. A real code error produces neither,
    # so it still fails (and the stderr drives the repair loop).
    geometry_ok = "measurements" in outputs and any(fmt in outputs for fmt in formats)
    return RenderResult(
        ok=(proc.returncode == 0 and bool(outputs)) or geometry_ok,
        outputs=outputs,
        measurements=measurements,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def render_code(
    code: str,
    out_dir: str | Path = "renders",
    name: str = "model",
    formats: Sequence[str] = DEFAULT_FORMATS,
    timeout: float = DEFAULT_TIMEOUT,
) -> RenderResult:
    """Like `render_file`, but takes the CadQuery source as a string."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", dir=out_dir, delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        script_path = Path(f.name)
    try:
        return render_file(
            script_path, out_dir=out_dir, name=name, formats=formats, timeout=timeout
        )
    finally:
        script_path.unlink(missing_ok=True)
