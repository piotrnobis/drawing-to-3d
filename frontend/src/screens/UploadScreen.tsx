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
      <div className="mb-10 text-center">
        <p className="mb-3 text-xs font-medium uppercase tracking-[0.25em] text-zinc-500">
          Drawing → editable solid
        </p>
        <h1 className="font-[family-name:var(--font-display)] text-5xl font-normal leading-[1.1] tracking-tight text-white md:text-6xl">
          Turn a drawing into a part
          <br />
          <em className="text-zinc-400">you&apos;ll actually edit</em>
        </h1>
        <p className="mx-auto mt-5 max-w-md text-sm leading-relaxed text-zinc-500">
          Upload an orthographic engineering drawing, describe the part, and DATUM rebuilds it as
          parametric CAD — verified dimension by dimension.
        </p>
      </div>

      <GlassCard className="animate-float space-y-5">
        <label className="block text-xs font-medium uppercase tracking-wider text-zinc-500">
          Describe the part
        </label>
        <textarea
          value={session.prompt}
          onChange={(e) => onUpdate({ prompt: e.target.value })}
          placeholder="L-bracket, 60×60 mm, wall thickness 18, bore Ø12, European projection…"
          rows={3}
          className="w-full resize-none rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:border-white/20"
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
          className={`relative flex min-h-[180px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed transition ${
            dragging
              ? "border-[#c5341f]/60 bg-[#c5341f]/5"
              : "border-white/10 bg-black/20 hover:border-white/20"
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
              className="max-h-40 rounded-lg object-contain"
            />
          ) : (
            <>
              <span className="text-3xl text-zinc-600">↑</span>
              <p className="mt-2 text-sm text-zinc-400">Drop PNG drawing here</p>
              <p className="text-xs text-zinc-600">or click to browse</p>
            </>
          )}
        </div>

        <PrimaryButton onClick={onNext} disabled={!session.imageFile}>
          Read drawing →
        </PrimaryButton>
      </GlassCard>
    </div>
  );
}
