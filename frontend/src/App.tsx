import { useCallback, useState } from "react";
import { Background } from "./components/Background";
import { Header } from "./components/Header";
import { BuildScreen } from "./screens/BuildScreen";
import { ExportScreen } from "./screens/ExportScreen";
import { PreviewScreen } from "./screens/PreviewScreen";
import { ReadScreen } from "./screens/ReadScreen";
import { UploadScreen } from "./screens/UploadScreen";
import { VerifyScreen } from "./screens/VerifyScreen";
import { initialSession, type SessionState, type Stage } from "./types";

export default function App() {
  const [stage, setStage] = useState<Stage>("upload");
  const [session, setSession] = useState<SessionState>(initialSession);

  const update = useCallback((patch: Partial<SessionState>) => {
    setSession((s) => ({ ...s, ...patch }));
  }, []);

  const restart = () => {
    setSession(initialSession());
    setStage("upload");
  };

  return (
    <div className="relative min-h-screen">
      <Background />
      <Header stage={stage} onStageClick={setStage} />

      <main className="relative z-10 px-6 pb-24 pt-8">
        {stage === "upload" && (
          <UploadScreen session={session} onUpdate={update} onNext={() => setStage("read")} />
        )}
        {stage === "read" && (
          <ReadScreen
            session={session}
            onUpdate={update}
            onNext={() => setStage("build")}
            onRefine={() => {}}
          />
        )}
        {stage === "build" && <BuildScreen onDone={() => setStage("verify")} />}
        {stage === "verify" && (
          <VerifyScreen
            session={session}
            onUpdate={update}
            onNext={() => setStage("preview")}
            onRefine={() => {}}
          />
        )}
        {stage === "preview" && <PreviewScreen onNext={() => setStage("export")} />}
        {stage === "export" && <ExportScreen onRestart={restart} />}
      </main>

      <footer className="relative z-10 border-t border-white/5 py-6 text-center text-[11px] uppercase tracking-wider text-zinc-600">
        DATUM · drawing → editable solid · Munich AI Hackathon
      </footer>
    </div>
  );
}
