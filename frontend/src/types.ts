export type Stage = "upload" | "read" | "build" | "verify" | "preview" | "export";

export interface DimensionRow {
  name: string;
  spec: number;
  built: number;
  status: "PASS" | "FLAG";
}

export interface SessionState {
  prompt: string;
  imageFile: File | null;
  imagePreview: string | null;
  reconstructedPreview: string | null;
  svgPreview: string | null;
  dimensions: DimensionRow[];
  overlayPreview: string | null;
  iou: number | null;
  iteration: number;
  gltfUrl: string | null;
  stepUrl: string | null;
}

export const STAGES: { id: Stage; label: string; num: string }[] = [
  { id: "upload", label: "Upload", num: "01" },
  { id: "read", label: "Read", num: "02" },
  { id: "build", label: "Build", num: "03" },
  { id: "verify", label: "Verify", num: "04" },
  { id: "preview", label: "3D", num: "05" },
  { id: "export", label: "Export", num: "06" },
];

export const initialSession = (): SessionState => ({
  prompt: "",
  imageFile: null,
  imagePreview: null,
  reconstructedPreview: null,
  svgPreview: null,
  dimensions: [],
  overlayPreview: null,
  iou: null,
  iteration: 0,
  gltfUrl: null,
  stepUrl: null,
});
