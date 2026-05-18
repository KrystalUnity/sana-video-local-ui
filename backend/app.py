from __future__ import annotations

import gc
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Any

import torch
from diffusers import SanaImageToVideoPipeline, SanaVideoPipeline
from diffusers.utils import export_to_video
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image


APP_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = APP_ROOT / "outputs"
LOCAL_PROFILES_FILE = APP_ROOT / "model-profiles.local.json"
DEFAULT_MODEL_ID = "sana-video-2b-480p"
DEFAULT_MODEL_NAME = "SANA-Video_2B_480p_diffusers"
DEFAULT_MODEL_LABEL = "SANA-Video 2B 480p"
SUPPORTED_PIPELINE_FAMILIES = {"sana-video-diffusers"}
DEFAULT_NEGATIVE = (
    "jitter, flicker, warped geometry, deformed anatomy, broken limbs, sudden cuts, "
    "heavy blur, ghosting, low quality, text artifacts, watermark"
)

OUTPUTS.mkdir(parents=True, exist_ok=True)


def resolve_model_dir() -> Path:
    explicit = os.environ.get("SANA_MODEL_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()

    candidates = [
        APP_ROOT / "models" / DEFAULT_MODEL_NAME,
        APP_ROOT.parent / "sana-video-prep" / "models" / DEFAULT_MODEL_NAME,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return candidates[0].resolve()


@dataclass(frozen=True)
class ModelProfile:
    id: str
    label: str
    path: Path
    pipeline_family: str = "sana-video-diffusers"
    description: str = "Current SANA-Video diffusers pipeline."

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "path": str(self.path),
            "pipelineFamily": self.pipeline_family,
            "description": self.description,
            "exists": self.path.exists(),
            "supported": self.pipeline_family in SUPPORTED_PIPELINE_FAMILIES,
        }


def normalize_profile_id(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-") or DEFAULT_MODEL_ID


def coerce_profile(raw: dict[str, Any], index: int) -> ModelProfile:
    label = str(raw.get("label") or raw.get("name") or f"Model profile {index + 1}")
    profile_id = normalize_profile_id(str(raw.get("id") or label))
    raw_path = raw.get("path") or raw.get("modelDir") or raw.get("model_dir")
    if not raw_path:
        raise ValueError(f"Model profile '{profile_id}' is missing a path.")

    pipeline_family = str(
        raw.get("pipelineFamily") or raw.get("pipeline_family") or "sana-video-diffusers"
    )
    description = str(raw.get("description") or "Local model profile.")
    return ModelProfile(
        id=profile_id,
        label=label,
        path=Path(str(raw_path)).expanduser().resolve(),
        pipeline_family=pipeline_family,
        description=description,
    )


def load_model_profiles() -> list[ModelProfile]:
    raw_config = os.environ.get("SANA_MODEL_PROFILES_JSON")
    if raw_config:
        raw_profiles = json.loads(raw_config)
    elif LOCAL_PROFILES_FILE.exists():
        raw_profiles = json.loads(LOCAL_PROFILES_FILE.read_text(encoding="utf-8"))
    else:
        raw_profiles = None

    if raw_profiles:
        if not isinstance(raw_profiles, list):
            raise ValueError("Model profile config must be a JSON array.")
        return [coerce_profile(raw, index) for index, raw in enumerate(raw_profiles)]

    return [
        ModelProfile(
            id=DEFAULT_MODEL_ID,
            label=DEFAULT_MODEL_LABEL,
            path=resolve_model_dir(),
            description="Default SANA-Video 2B 480p diffusers model.",
        )
    ]


def model_profiles_by_id() -> dict[str, ModelProfile]:
    return {profile.id: profile for profile in load_model_profiles()}


def get_model_profile(profile_id: str) -> ModelProfile:
    profiles = model_profiles_by_id()
    profile = profiles.get(profile_id) or profiles.get(DEFAULT_MODEL_ID)
    if not profile and profiles and profile_id in {"", DEFAULT_MODEL_ID}:
        profile = next(iter(profiles.values()))
    if not profile:
        raise RuntimeError(f"Unknown model profile: {profile_id}")
    return profile


@dataclass
class Job:
    id: str
    status: str
    prompt: str
    model_profile: str
    mode: str
    memory_mode: str
    total_steps: int
    frames: int
    segments: int
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    step: int = 0
    progress: float = 0.0
    message: str = "Queued"
    output_url: str | None = None
    output_name: str | None = None
    error: str | None = None
    peak_allocated_gb: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "prompt": self.prompt,
            "modelProfile": self.model_profile,
            "mode": self.mode,
            "memoryMode": self.memory_mode,
            "totalSteps": self.total_steps,
            "frames": self.frames,
            "segments": self.segments,
            "createdAt": self.created_at,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "step": self.step,
            "progress": self.progress,
            "message": self.message,
            "outputUrl": self.output_url,
            "outputName": self.output_name,
            "error": self.error,
            "peakAllocatedGb": self.peak_allocated_gb,
        }


jobs: dict[str, Job] = {}
jobs_lock = Lock()
pipeline_lock = Lock()
executor = ThreadPoolExecutor(max_workers=1)
pipeline: SanaImageToVideoPipeline | SanaVideoPipeline | None = None
pipeline_profile_key: str | None = None
pipeline_mode: str | None = None
pipeline_memory_mode: str | None = None


def set_job(job_id: str, **updates: Any) -> None:
    with jobs_lock:
        job = jobs[job_id]
        for key, value in updates.items():
            setattr(job, key, value)


def get_pipeline(mode: str, memory_mode: str, model_profile_id: str) -> SanaImageToVideoPipeline | SanaVideoPipeline:
    global pipeline, pipeline_profile_key, pipeline_mode, pipeline_memory_mode

    profile = get_model_profile(model_profile_id)
    profile_key = f"{profile.id}:{profile.path}"

    with pipeline_lock:
        if (
            pipeline is not None
            and pipeline_profile_key == profile_key
            and pipeline_mode == mode
            and pipeline_memory_mode == memory_mode
        ):
            return pipeline

        unload_pipeline_locked()

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available.")
        if profile.pipeline_family not in SUPPORTED_PIPELINE_FAMILIES:
            raise RuntimeError(
                f"Model profile '{profile.label}' uses unsupported pipeline family "
                f"'{profile.pipeline_family}'. Add a backend adapter before running it."
            )
        if not profile.path.exists():
            raise RuntimeError(f"Model folder not found: {profile.path}")

        cls = SanaImageToVideoPipeline if mode == "image-to-video" else SanaVideoPipeline
        pipeline = cls.from_pretrained(str(profile.path), torch_dtype=torch.bfloat16, local_files_only=True)
        pipeline.vae.to(torch.float32)
        pipeline.text_encoder.to(torch.bfloat16)

        if memory_mode == "low":
            if hasattr(pipeline, "enable_attention_slicing"):
                pipeline.enable_attention_slicing("max")
            pipeline.enable_sequential_cpu_offload()
        else:
            pipeline.enable_model_cpu_offload()

        pipeline_profile_key = profile_key
        pipeline_mode = mode
        pipeline_memory_mode = memory_mode
        return pipeline


def unload_pipeline_locked() -> None:
    global pipeline, pipeline_profile_key, pipeline_mode, pipeline_memory_mode

    pipeline = None
    pipeline_profile_key = None
    pipeline_mode = None
    pipeline_memory_mode = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def unload_pipeline() -> None:
    with pipeline_lock:
        unload_pipeline_locked()


def run_generation(job_id: str, params: dict[str, Any], image_path: Path | None) -> None:
    steps = int(params["steps"])
    frames = int(params["frames"])
    segments = int(params["segments"])
    memory_mode = str(params["memory_mode"])
    model_profile_id = str(params["model_profile"])
    profile = get_model_profile(model_profile_id)

    set_job(
        job_id,
        status="running",
        started_at=time.time(),
        progress=0.04,
        message=f"Loading {profile.label}",
    )

    try:
        seed = int(params["seed"])
        if seed < 0:
            seed = int(torch.seed() % (2**31))

        prompt = str(params["prompt"]).strip()
        if "motion score:" not in prompt.lower():
            prompt = f"{prompt} motion score: {int(params['motion_score'])}."

        output_mode = "chain" if segments > 1 else "i2v" if image_path else "t2v"
        out_name = f"sana_{profile.id}_{output_mode}_{int(time.time())}_seed{seed}.mp4"
        out_path = OUTPUTS / out_name

        combined_frames: list[Any] = []
        current_image: Image.Image | None = None
        if image_path:
            current_image = Image.open(image_path).convert("RGB")

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

        peak_gb = 0.0
        for segment_index in range(segments):
            segment_mode = "image-to-video" if current_image else "text-to-video"
            pipe = get_pipeline(segment_mode, memory_mode, model_profile_id)
            segment_seed = seed + segment_index
            kwargs: dict[str, Any] = {
                "prompt": prompt,
                "negative_prompt": str(params["negative_prompt"]).strip(),
                "height": 480,
                "width": 832,
                "frames": frames,
                "guidance_scale": float(params["guidance"]),
                "num_inference_steps": steps,
                "generator": torch.Generator(device="cuda").manual_seed(segment_seed),
                "callback_on_step_end": make_step_callback(job_id, steps, segment_index, segments),
            }
            if current_image:
                kwargs["image"] = current_image

            set_job(
                job_id,
                progress=0.08 + (segment_index / max(segments, 1)) * 0.82,
                message=f"Generating segment {segment_index + 1}/{segments}",
            )
            result = list(pipe(**kwargs).frames[0])
            if not result:
                raise RuntimeError(f"Segment {segment_index + 1} returned no frames.")

            frames_to_add = result
            if segment_index > 0 and len(result) > 1:
                frames_to_add = result[1:]
            combined_frames.extend(frames_to_add)
            current_image = result[-1].convert("RGB")

            if torch.cuda.is_available():
                peak_gb = max(peak_gb, torch.cuda.max_memory_allocated() / (1024**3))
                torch.cuda.empty_cache()

            if params["unload_after"] and segment_index < segments - 1:
                unload_pipeline()

        if params["unload_after"]:
            unload_pipeline()

        set_job(job_id, progress=0.94, message="Encoding MP4", peak_allocated_gb=round(peak_gb, 2))
        export_to_video(combined_frames, str(out_path), fps=int(params["fps"]))

        set_job(
            job_id,
            status="completed",
            progress=1.0,
            message="Completed",
            output_url=f"/outputs/{out_name}",
            output_name=out_name,
            finished_at=time.time(),
            peak_allocated_gb=round(peak_gb, 2),
        )
    except Exception as exc:
        set_job(
            job_id,
            status="failed",
            message="Failed",
            error=str(exc),
            finished_at=time.time(),
        )
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def make_step_callback(job_id: str, steps: int, segment_index: int, segments: int):
    def callback(_pipe, step: int, _timestep, callback_kwargs: dict[str, Any]) -> dict[str, Any]:
        current = step + 1
        total_step = segment_index * steps + current
        total_steps = max(steps * segments, 1)
        progress = 0.08 + (total_step / total_steps) * 0.82
        set_job(
            job_id,
            step=total_step,
            progress=min(progress, 0.9),
            message=f"Segment {segment_index + 1}/{segments} step {current}/{steps}",
        )
        return callback_kwargs

    return callback


app = FastAPI(title="SANA Video Local UI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS)), name="outputs")


@app.get("/api/health")
def health() -> dict[str, Any]:
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    profiles = load_model_profiles()
    default_profile = profiles[0]
    return {
        "ok": True,
        "cudaAvailable": torch.cuda.is_available(),
        "gpuName": gpu_name,
        "modelDir": str(default_profile.path),
        "modelExists": default_profile.path.exists(),
        "defaultModelProfile": default_profile.id,
    }


@app.get("/api/model-profiles")
def model_profiles() -> list[dict[str, Any]]:
    return [profile.to_dict() for profile in load_model_profiles()]


@app.post("/api/jobs")
async def create_job(
    prompt: str = Form(...),
    negative_prompt: str = Form(DEFAULT_NEGATIVE),
    motion_score: int = Form(20),
    steps: int = Form(8),
    guidance: float = Form(6.0),
    frames: int = Form(17),
    segments: int = Form(1),
    seed: int = Form(42),
    fps: int = Form(16),
    model_profile: str = Form(DEFAULT_MODEL_ID),
    memory_mode: str = Form("low"),
    unload_after: bool = Form(True),
    start_image: UploadFile | None = File(None),
) -> dict[str, Any]:
    if memory_mode not in {"low", "balanced"}:
        raise HTTPException(status_code=400, detail="memory_mode must be low or balanced")
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")
    if steps < 1 or frames < 1:
        raise HTTPException(status_code=400, detail="steps and frames must be positive")
    if segments < 1 or segments > 8:
        raise HTTPException(status_code=400, detail="segments must be between 1 and 8")
    try:
        profile = get_model_profile(model_profile)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if profile.pipeline_family not in SUPPORTED_PIPELINE_FAMILIES:
        raise HTTPException(
            status_code=400,
            detail=f"Model profile '{profile.label}' uses unsupported pipeline family '{profile.pipeline_family}'",
        )

    job_id = uuid.uuid4().hex[:12]
    image_path: Path | None = None

    if start_image and start_image.filename:
        raw = await start_image.read()
        image = Image.open(BytesIO(raw)).convert("RGB")
        image_path = OUTPUTS / f"{job_id}_start.png"
        image.save(image_path)

    mode = "chain" if segments > 1 else "image-to-video" if image_path else "text-to-video"
    output_frames = frames + max(segments - 1, 0) * max(frames - 1, 1)
    job = Job(
        id=job_id,
        status="queued",
        prompt=prompt,
        model_profile=profile.id,
        mode=mode,
        memory_mode=memory_mode,
        total_steps=steps * segments,
        frames=output_frames,
        segments=segments,
    )
    with jobs_lock:
        jobs[job_id] = job

    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "motion_score": motion_score,
        "steps": steps,
        "guidance": guidance,
        "frames": frames,
        "segments": segments,
        "seed": seed,
        "fps": fps,
        "model_profile": profile.id,
        "memory_mode": memory_mode,
        "unload_after": unload_after,
    }
    executor.submit(run_generation, job_id, params, image_path)
    return job.to_dict()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return job.to_dict()


@app.post("/api/unload")
def unload() -> dict[str, str]:
    unload_pipeline()
    return {"message": "Model unloaded"}


@app.get("/api/outputs")
def list_outputs() -> list[dict[str, Any]]:
    files = sorted(OUTPUTS.glob("*.mp4"), key=lambda path: path.stat().st_mtime, reverse=True)
    return [
        {
            "name": file.name,
            "url": f"/outputs/{file.name}",
            "size": file.stat().st_size,
            "modifiedAt": file.stat().st_mtime,
        }
        for file in files[:30]
    ]
