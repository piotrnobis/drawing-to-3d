import { useCallback, useState } from "react";
import { GlassCard, PrimaryButton } from "../components/GlassCard";
import type { SessionState } from "../types";

interface Props {
  session: SessionState;
  onUpdate: (patch: Partial<SessionState>) => void;
  onNext: () => void;
}

export function UploadScreen({ session, onUpdate, onNext }: Props) {
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith("image/")) return;
      const url = URL.createObjectURL(file);
      onUpdate({ imageFile: file, imagePreview: url });
    },
    [onUpdate],
  );

  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="mb-16 text-center">
        <p className="label-spaced mb-6">Drawing to editable solid</p>
        <h1 className="font-[family-name:var(--font-display)] text-5xl font-normal leading-[1.1] tracking-tight text-[var(--color-ink)] md:text-6xl">
          Turn a drawing into a part
          <br />
          <em className="text-[var(--color-muted)]">you&apos;ll actually edit</em>
        </h1>
        <p className="mx-auto mt-6 max-w-md text-sm leading-relaxed text-[var(--color-muted)]">
          Upload an orthographic engineering drawing, describe the part, and Datum rebuilds it as
          parametric CAD — verified dimension by dimension.
        </p>
      </div>

      <GlassCard className="space-y-6">
        <label className="label-spaced block">Describe the part</label>
        <textarea
          value={session.prompt}
          onChange={(e) => onUpdate({ prompt: e.target.value })}
          placeholder="L-bracket, 60×60 mm, wall thickness 18, bore Ø12, European projection…"
          rows={3}
          className="w-full resize-none border border-[var(--color-border)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-muted)]/60 outline-none focus:border-[var(--color-border-strong)]"
        />

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const f = e.dataTransfer.files[0];
            if (f) handleFile(f);
          }}
          className={`relative flex min-h-[200px] cursor-pointer flex-col items-center justify-center border border-dashed transition ${
            dragging
              ? "border-[var(--color-warm)] bg-[var(--color-warm)]/5"
              : "border-[var(--color-border)] bg-white hover:border-[var(--color-border-strong)]"
          }`}
          onClick={() => document.getElementById("file-input")?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
          {session.imagePreview ? (
            <img
              src={session.imagePreview}
              alt="Uploaded drawing"
              className="max-h-44 object-contain p-4"
            />
          ) : (
            <>
              <p className="text-sm text-[var(--color-muted)]">Drop PNG drawing here</p>
              <p className="mt-1 text-xs text-[var(--color-border-strong)]">or click to browse</p>
            </>
          )}
        </div>

        <PrimaryButton onClick={onNext} disabled={!session.imageFile}>
          Read drawing
        </PrimaryButton>
      </GlassCard>
    </div>
  );
}
