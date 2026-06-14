import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
// @ts-expect-error - no types
import occtimportjs from "occt-import-js";
import occtWasmUrl from "occt-import-js/dist/occt-import-js.wasm?url";


type Props = { stepUrl: string };

export function StepViewer({ stepUrl }: Props) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;
    let renderer: THREE.WebGLRenderer | null = null;
    let frame = 0;
    let resizeObs: ResizeObserver | null = null;

    async function run() {
      try {
        const mount = mountRef.current;
        if (!mount) return;

        const [occt, stepBuf] = await Promise.all([
          occtimportjs({ locateFile: () => occtWasmUrl }),
          fetch(stepUrl).then((r) => r.arrayBuffer()),
        ]);
        if (disposed) return;

        const result = occt.ReadStepFile(new Uint8Array(stepBuf), null);
        if (!result?.success) throw new Error("Failed to parse STEP file");

        const scene = new THREE.Scene();
        scene.background = new THREE.Color("#ffffff");

        const group = new THREE.Group();
        const inner = new THREE.Group();
        group.add(inner);
        const material = new THREE.MeshStandardMaterial({
          color: 0xc8ccc2,
          metalness: 0.15,
          roughness: 0.55,
          flatShading: false,
        });
        const edgeMat = new THREE.LineBasicMaterial({ color: 0x191b19 });

        for (const mesh of result.meshes) {
          const geom = new THREE.BufferGeometry();
          geom.setAttribute(
            "position",
            new THREE.Float32BufferAttribute(mesh.attributes.position.array, 3),
          );
          if (mesh.attributes.normal) {
            geom.setAttribute(
              "normal",
              new THREE.Float32BufferAttribute(mesh.attributes.normal.array, 3),
            );
          }
          if (mesh.index) {
            geom.setIndex(Array.from(mesh.index.array));
          }
          if (!mesh.attributes.normal) geom.computeVertexNormals();

          const m = new THREE.Mesh(geom, material);
          inner.add(m);

          const edges = new THREE.EdgesGeometry(geom, 25);
          const lines = new THREE.LineSegments(edges, edgeMat);
          inner.add(lines);
        }

        // Center the object inside inner so the outer group rotates around its centroid
        const box = new THREE.Box3().setFromObject(inner);
        const size = new THREE.Vector3();
        const center = new THREE.Vector3();
        box.getSize(size);
        box.getCenter(center);
        inner.position.sub(center);
        scene.add(group);

        const maxDim = Math.max(size.x, size.y, size.z) || 1;

        const w = mount.clientWidth;
        const h = mount.clientHeight;
        const camera = new THREE.PerspectiveCamera(40, w / h, maxDim * 0.01, maxDim * 100);
        const dist = maxDim * 1.2;
        camera.position.set(dist, dist * 0.8, dist);
        camera.lookAt(0, 0, 0);

        scene.add(new THREE.AmbientLight(0xffffff, 0.55));
        const dir1 = new THREE.DirectionalLight(0xffffff, 0.85);
        dir1.position.set(1, 1.2, 0.8);
        scene.add(dir1);
        const dir2 = new THREE.DirectionalLight(0xffffff, 0.35);
        dir2.position.set(-1, -0.4, -0.6);
        scene.add(dir2);

        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(w, h);
        mount.appendChild(renderer.domElement);

        // Pointer-drag rotation
        let rotX = 0.2;
        let rotY = 0.4;
        let dragging: { x: number; y: number; rx: number; ry: number } | null = null;
        const el = renderer.domElement;
        el.style.cursor = "grab";
        el.addEventListener("pointerdown", (e) => {
          dragging = { x: e.clientX, y: e.clientY, rx: rotX, ry: rotY };
          el.setPointerCapture(e.pointerId);
          el.style.cursor = "grabbing";
        });
        el.addEventListener("pointermove", (e) => {
          if (!dragging) return;
          rotY = dragging.ry + (e.clientX - dragging.x) * 0.008;
          rotX = dragging.rx + (e.clientY - dragging.y) * 0.008;
        });
        const endDrag = () => {
          dragging = null;
          el.style.cursor = "grab";
        };
        el.addEventListener("pointerup", endDrag);
        el.addEventListener("pointercancel", endDrag);

        let zoom = 1;
        el.addEventListener("wheel", (e) => {
          e.preventDefault();
          zoom *= e.deltaY > 0 ? 1.1 : 0.9;
          zoom = Math.max(0.3, Math.min(zoom, 4));
        }, { passive: false });

        resizeObs = new ResizeObserver(() => {
          if (!renderer || !mount) return;
          const nw = mount.clientWidth;
          const nh = mount.clientHeight;
          renderer.setSize(nw, nh);
          camera.aspect = nw / nh;
          camera.updateProjectionMatrix();
        });
        resizeObs.observe(mount);

        const baseDist = dist;
        const animate = () => {
          if (disposed || !renderer) return;
          group.rotation.x = rotX;
          group.rotation.y = rotY;
          const d = baseDist * zoom;
          camera.position.set(d, d * 0.8, d);
          camera.lookAt(0, 0, 0);
          renderer.render(scene, camera);
          frame = requestAnimationFrame(animate);
        };
        animate();
        setLoading(false);
      } catch (e) {
        console.error(e);
        setError((e as Error).message);
        setLoading(false);
      }
    }
    run();

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      resizeObs?.disconnect();
      if (renderer) {
        renderer.dispose();
        renderer.domElement.remove();
      }
    };
  }, [stepUrl]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div ref={mountRef} style={{ width: "100%", height: "100%" }} />
      {loading && (
        <div style={{
          position: "absolute", inset: 0, display: "flex",
          alignItems: "center", justifyContent: "center",
          fontFamily: "IBM Plex Mono, monospace", fontSize: 12,
          letterSpacing: ".18em", textTransform: "uppercase",
          color: "var(--ink-soft)", background: "var(--paper-2)",
        }}>
          Loading 3D model…
        </div>
      )}
      {error && (
        <div style={{
          position: "absolute", inset: 0, display: "flex",
          alignItems: "center", justifyContent: "center",
          color: "var(--accent)", fontSize: 13,
        }}>
          {error}
        </div>
      )}
    </div>
  );
}
