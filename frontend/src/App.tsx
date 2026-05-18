import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Gauge,
  Image as ImageIcon,
  Layers,
  Loader2,
  Play,
  RotateCcw,
  Server,
  Sparkles,
  Video,
  Zap,
} from "lucide-react";
import { ChangeEvent, FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8008";

type Health = {
  ok: boolean;
  cudaAvailable: boolean;
  gpuName: string | null;
  modelDir: string;
  modelExists: boolean;
  defaultModelProfile: string;
};

type Job = {
  id: string;
  status: "queued" | "running" | "completed" | "failed";
  prompt: string;
  modelProfile: string;
  mode: string;
  memoryMode: string;
  totalSteps: number;
  frames: number;
  segments: number;
  createdAt: number;
  startedAt: number | null;
  finishedAt: number | null;
  step: number;
  progress: number;
  message: string;
  outputUrl: string | null;
  outputName: string | null;
  error: string | null;
  peakAllocatedGb: number | null;
};

type OutputFile = {
  name: string;
  url: string;
  size: number;
  modifiedAt: number;
};

type ModelProfile = {
  id: string;
  label: string;
  path: string;
  pipelineFamily: string;
  description: string;
  exists: boolean;
  supported: boolean;
};

type FormState = {
  prompt: string;
  negativePrompt: string;
  motionScore: number;
  steps: number;
  frames: number;
  segments: number;
  guidance: number;
  seed: number;
  fps: number;
  modelProfile: string;
  memoryMode: "low" | "balanced";
  unloadAfter: boolean;
};

const defaultForm: FormState = {
  prompt:
    "A slow cinematic shot of a small robot exploring a quiet neon-lit workshop, soft reflections on metal surfaces, gentle camera movement, clean details.",
  negativePrompt:
    "jitter, flicker, warped geometry, deformed anatomy, broken limbs, sudden cuts, heavy blur, ghosting, low quality, text artifacts, watermark",
  motionScore: 20,
  steps: 8,
  frames: 17,
  segments: 1,
  guidance: 6,
  seed: 42,
  fps: 16,
  modelProfile: "sana-video-2b-480p",
  memoryMode: "low",
  unloadAfter: true,
};

function toAssetUrl(url: string | null) {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${API_URL}${url}`;
}

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatClock(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rem = Math.floor(seconds % 60);
  if (minutes === 0) return `${rem}s`;
  return `${minutes}m ${rem.toString().padStart(2, "0")}s`;
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(defaultForm);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [modelProfiles, setModelProfiles] = useState<ModelProfile[]>([]);
  const [outputs, setOutputs] = useState<OutputFile[]>([]);
  const [logs, setLogs] = useState<string[]>(["Workbench ready."]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedOutput, setSelectedOutput] = useState<string | null>(null);

  const selectedModel = useMemo(
    () => modelProfiles.find((profile) => profile.id === form.modelProfile) ?? modelProfiles[0] ?? null,
    [form.modelProfile, modelProfiles],
  );
  const selectedModelReady = !selectedModel || (selectedModel.exists && selectedModel.supported);
  const canGenerate = Boolean(form.prompt.trim()) && selectedModelReady && !isSubmitting && job?.status !== "running" && job?.status !== "queued";
  const activeOutputUrl = selectedOutput ?? toAssetUrl(job?.outputUrl ?? null) ?? toAssetUrl(outputs[0]?.url ?? null);
  const modelStatusLabel = selectedModel
    ? selectedModel.exists && selectedModel.supported
      ? "Model ready"
      : selectedModel.supported
        ? "Model missing"
        : "Adapter needed"
    : health?.modelExists
      ? "Model found"
      : "Model missing";
  const modelStatusGood = selectedModel ? selectedModel.exists && selectedModel.supported : Boolean(health?.modelExists);
  const projectedFrames = form.frames + Math.max(form.segments - 1, 0) * Math.max(form.frames - 1, 1);

  const runProfile = useMemo(() => {
    const seconds = projectedFrames / form.fps;
    const mode = form.segments > 1 ? (imageFile ? "Image chain" : "Text chain") : imageFile ? "Image seed" : "Text seed";
    const model = selectedModel?.label ?? "Default model";
    return `${model} / ${mode} / ${seconds.toFixed(2)}s / ${form.segments} segment${form.segments === 1 ? "" : "s"}`;
  }, [form.fps, form.segments, imageFile, projectedFrames, selectedModel]);

  useEffect(() => {
    refreshHealth();
    refreshModelProfiles();
    refreshOutputs();
  }, []);

  useEffect(() => {
    if (!imageFile) {
      setImagePreview(null);
      return;
    }
    const url = URL.createObjectURL(imageFile);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [imageFile]);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;
    const timeout = window.setTimeout(async () => {
      const next = await fetchJson<Job>(`/api/jobs/${job.id}`);
      setJob(next);
      setLogs((prev) => appendLog(prev, `${next.message} (${Math.round(next.progress * 100)}%)`));
      if (next.status === "completed") {
        setSelectedOutput(toAssetUrl(next.outputUrl));
        refreshOutputs();
      }
    }, 1000);
    return () => window.clearTimeout(timeout);
  }, [job]);

  async function refreshHealth() {
    try {
      setHealth(await fetchJson<Health>("/api/health"));
      setHealthError(null);
    } catch (error) {
      setHealthError(error instanceof Error ? error.message : String(error));
    }
  }

  async function refreshModelProfiles() {
    try {
      const profiles = await fetchJson<ModelProfile[]>("/api/model-profiles");
      setModelProfiles(profiles);
      setForm((prev) => {
        if (profiles.length === 0 || profiles.some((profile) => profile.id === prev.modelProfile)) {
          return prev;
        }
        return { ...prev, modelProfile: profiles[0].id };
      });
    } catch {
      setModelProfiles([]);
    }
  }

  async function refreshOutputs() {
    try {
      setOutputs(await fetchJson<OutputFile[]>("/api/outputs"));
    } catch {
      setOutputs([]);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);
    setLogs((prev) => appendLog(prev, `Submitting ${runProfile}`));

    const data = new FormData();
    data.set("prompt", form.prompt);
    data.set("negative_prompt", form.negativePrompt);
    data.set("motion_score", String(form.motionScore));
    data.set("steps", String(form.steps));
    data.set("guidance", String(form.guidance));
    data.set("frames", String(form.frames));
    data.set("segments", String(form.segments));
    data.set("seed", String(form.seed));
    data.set("fps", String(form.fps));
    data.set("model_profile", form.modelProfile);
    data.set("memory_mode", form.memoryMode);
    data.set("unload_after", String(form.unloadAfter));
    if (imageFile) data.set("start_image", imageFile);

    try {
      const response = await fetch(`${API_URL}/api/jobs`, { method: "POST", body: data });
      if (!response.ok) throw new Error(await response.text());
      const created = (await response.json()) as Job;
      setJob(created);
      setLogs((prev) => appendLog(prev, `Queued job ${created.id}`));
    } catch (error) {
      setLogs((prev) => appendLog(prev, `Submit failed: ${error instanceof Error ? error.message : String(error)}`));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function unload() {
    await fetch(`${API_URL}/api/unload`, { method: "POST" });
    setLogs((prev) => appendLog(prev, "Unload requested."));
  }

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function pickImage(event: ChangeEvent<HTMLInputElement>) {
    setImageFile(event.target.files?.[0] ?? null);
  }

  return (
    <main className="app-shell">
      <section className="top-strip">
        <div>
          <p className="eyebrow">Local video lab</p>
          <h1>SANA Video Workbench</h1>
        </div>
        <div className="status-cluster">
          <SystemPill icon={<Cpu size={16} />} label={health?.gpuName ?? "GPU unknown"} tone={health?.cudaAvailable ? "good" : "bad"} />
          <SystemPill icon={<Server size={16} />} label={modelStatusLabel} tone={modelStatusGood ? "good" : "bad"} />
        </div>
      </section>

      {healthError && (
        <div className="banner">
          <AlertTriangle size={18} />
          Backend offline: {healthError}
        </div>
      )}

      <section className="workspace-grid">
        <form className="panel compose-panel" onSubmit={submit}>
          <div className="panel-title">
            <Sparkles size={18} />
            Prompt
          </div>
          <textarea
            value={form.prompt}
            onChange={(event) => update("prompt", event.target.value)}
            spellCheck={false}
          />

          <label className="drop-zone">
            <input type="file" accept="image/*" onChange={pickImage} />
            {imagePreview ? (
              <img src={imagePreview} alt="Start frame preview" />
            ) : (
              <span>
                <ImageIcon size={22} />
                Optional start image
              </span>
            )}
          </label>

          <textarea
            className="negative"
            value={form.negativePrompt}
            onChange={(event) => update("negativePrompt", event.target.value)}
            spellCheck={false}
          />

          <div className="action-row">
            <button className="primary-button" disabled={!canGenerate} type="submit">
              {isSubmitting || job?.status === "running" || job?.status === "queued" ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
              Generate
            </button>
            <button className="secondary-button" type="button" onClick={unload}>
              <RotateCcw size={17} />
              Unload
            </button>
          </div>
        </form>

        <aside className="panel controls-panel">
          <div className="panel-title">
            <Gauge size={18} />
            Controls
          </div>
          <Control label="Motion" value={form.motionScore} min={1} max={100} step={1} onChange={(value) => update("motionScore", value)} />
          <Control label="Steps" value={form.steps} min={4} max={30} step={1} onChange={(value) => update("steps", value)} />
          <Control label="Frames" value={form.frames} min={9} max={49} step={8} onChange={(value) => update("frames", value)} />
          <Control label="Segments" value={form.segments} min={1} max={8} step={1} onChange={(value) => update("segments", value)} />
          <Control label="Guidance" value={form.guidance} min={1} max={10} step={0.25} onChange={(value) => update("guidance", value)} />
          <Control label="FPS" value={form.fps} min={8} max={24} step={1} onChange={(value) => update("fps", value)} />

          <label className="field-label">
            Seed
            <input
              type="number"
              value={form.seed}
              onChange={(event) => update("seed", Number(event.target.value))}
            />
          </label>

          <label className="field-label">
            Model
            <select value={form.modelProfile} onChange={(event) => update("modelProfile", event.target.value)}>
              {modelProfiles.length === 0 && <option value={form.modelProfile}>Default model</option>}
              {modelProfiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.label}
                </option>
              ))}
            </select>
          </label>

          {selectedModel && (
            <div className={`model-note ${selectedModelReady ? "ready" : "blocked"}`}>
              <span>
                <Layers size={14} />
                {selectedModel.supported ? selectedModel.pipelineFamily : "adapter required"}
              </span>
              <small>{selectedModel.description}</small>
              <code>{selectedModel.path}</code>
            </div>
          )}

          <label className="field-label">
            Memory mode
            <select value={form.memoryMode} onChange={(event) => update("memoryMode", event.target.value as FormState["memoryMode"])}>
              <option value="low">Low VRAM</option>
              <option value="balanced">Balanced</option>
            </select>
          </label>

          <label className="check-row">
            <input
              type="checkbox"
              checked={form.unloadAfter}
              onChange={(event) => update("unloadAfter", event.target.checked)}
            />
            Unload after generation
          </label>

          <div className="run-profile">
            <Zap size={16} />
            {runProfile}
          </div>
        </aside>

        <section className="panel output-panel">
          <div className="panel-title">
            <Video size={18} />
            Output
          </div>
          {activeOutputUrl ? (
            <video src={activeOutputUrl} controls loop />
          ) : (
            <div className="empty-output">Generated videos appear here.</div>
          )}
        </section>

        <section className="panel progress-panel">
          <div className="panel-title">
            <Activity size={18} />
            Run Status
          </div>
          <div className="progress-head">
            <span>{job?.message ?? "Idle"}</span>
            <strong>{job ? `${Math.round(job.progress * 100)}%` : "0%"}</strong>
          </div>
          <div className="progress-track">
            <div style={{ width: `${Math.round((job?.progress ?? 0) * 100)}%` }} />
          </div>
          <div className="metric-grid">
            <Metric label="Step" value={job ? `${job.step}/${job.totalSteps}` : "-"} />
            <Metric label="Frames" value={job ? String(job.frames) : String(projectedFrames)} />
            <Metric label="Segments" value={job ? String(job.segments) : String(form.segments)} />
            <Metric label="Peak VRAM" value={job?.peakAllocatedGb ? `${job.peakAllocatedGb} GB` : "-"} />
            <Metric label="Elapsed" value={job?.startedAt ? formatClock((job.finishedAt ?? Date.now() / 1000) - job.startedAt) : "-"} />
          </div>
          {job?.status === "completed" && <div className="success-line"><CheckCircle2 size={16} /> {job.outputName}</div>}
          {job?.status === "failed" && <div className="error-line"><AlertTriangle size={16} /> {job.error}</div>}
          <div className="log-box">
            {logs.slice(-8).map((entry, index) => (
              <div key={`${entry}-${index}`}>{entry}</div>
            ))}
          </div>
        </section>

        <section className="panel gallery-panel">
          <div className="panel-title">Recent Outputs</div>
          <div className="gallery-list">
            {outputs.map((output) => (
              <button key={output.name} type="button" onClick={() => setSelectedOutput(toAssetUrl(output.url))}>
                <span>{output.name}</span>
                <small>{formatBytes(output.size)}</small>
              </button>
            ))}
            {outputs.length === 0 && <div className="empty-output compact">No videos yet.</div>}
          </div>
        </section>
      </section>
    </main>
  );
}

function Control(props: { label: string; value: number; min: number; max: number; step: number; onChange: (value: number) => void }) {
  return (
    <label className="control">
      <span>
        {props.label}
        <strong>{props.value}</strong>
      </span>
      <input
        type="range"
        min={props.min}
        max={props.max}
        step={props.step}
        value={props.value}
        onChange={(event) => props.onChange(Number(event.target.value))}
      />
    </label>
  );
}

function Metric(props: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{props.label}</span>
      <strong>{props.value}</strong>
    </div>
  );
}

function SystemPill(props: { icon: ReactNode; label: string; tone: "good" | "bad" }) {
  return (
    <div className={`system-pill ${props.tone}`}>
      {props.icon}
      <span>{props.label}</span>
    </div>
  );
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

function appendLog(lines: string[], entry: string) {
  if (lines[lines.length - 1] === entry) return lines;
  return [...lines, entry].slice(-20);
}
