# SANA Video Local UI

A local React + FastAPI workbench for running the available SANA-Video 2B diffusers model on consumer GPUs.

This repository contains only the UI and backend wrapper. It does not include model weights.

## Features

- Text-to-video and image-to-video generation.
- Low VRAM mode using sequential CPU offload.
- Balanced mode for faster runs when your GPU has enough headroom.
- Job queue with progress, current step, elapsed time, and output gallery.
- Windows-friendly defaults tested around a 12 GB laptop GPU.

## Model

Download the model separately from Hugging Face:

`Efficient-Large-Model/SANA-Video_2B_480p_diffusers`

Set `SANA_MODEL_DIR` to the downloaded model folder, or place the model at:

`models/SANA-Video_2B_480p_diffusers`

Model weights and generated outputs are ignored by git.

## Backend

Create a Python environment and install PyTorch for your CUDA setup first. On the tested Windows machine, CUDA 12.8 wheels worked:

```powershell
python -m pip install --index-url https://download.pytorch.org/whl/cu128 torch torchvision torchaudio
python -m pip install -r backend\requirements.txt
```

Run the backend:

```powershell
$env:SANA_MODEL_DIR="C:\path\to\SANA-Video_2B_480p_diffusers"
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8008
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open:

`http://127.0.0.1:5173`

## One-Command Dev Run

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_dev.ps1
```

## Safe Starting Settings

For 12 GB laptop GPUs, start with:

- Memory mode: `low`
- Frames: `17` or `25`
- Steps: `8` or `12`
- Unload after generation: enabled

Scale up after a successful run.

## License Notes

The app code in this repository is MIT licensed. SANA model weights, upstream model code, PyTorch, diffusers, and other dependencies remain governed by their own licenses and terms.

This public UI intentionally avoids paid React Bits Pro source code or private registry components.
