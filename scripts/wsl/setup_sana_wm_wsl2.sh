#!/usr/bin/env bash
set -euo pipefail

LAB="${SANA_WM_LAB:-$HOME/sana-wm-lab}"
SANA_REPO_URL="${SANA_REPO_URL:-https://github.com/NVlabs/Sana.git}"
HF_REPO="${SANA_WM_HF_REPO:-Efficient-Large-Model/SANA-WM_bidirectional}"
VENV="$LAB/.venv311"
UV="$HOME/.local/bin/uv"

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "== Checking NVIDIA GPU visibility =="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "nvidia-smi was not found in WSL. Update your Windows NVIDIA driver and WSL kernel."
fi

echo "== Installing Ubuntu packages =="
$SUDO apt-get update
$SUDO apt-get install -y \
  build-essential \
  curl \
  ffmpeg \
  git \
  git-lfs \
  libgl1 \
  libglib2.0-0 \
  ninja-build \
  python3-venv \
  rsync

mkdir -p "$LAB/models" "$LAB/configs" "$LAB/outputs"

if [ ! -x "$UV" ]; then
  echo "== Installing uv =="
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "== Installing Python 3.11 =="
"$UV" python install 3.11
"$UV" venv --clear --seed --python 3.11 "$VENV"

PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

echo "== Cloning or updating NVLabs/Sana =="
if [ -d "$LAB/Sana/.git" ]; then
  git -C "$LAB/Sana" pull --ff-only
else
  git clone --depth 1 "$SANA_REPO_URL" "$LAB/Sana"
fi

echo "== Installing CUDA PyTorch stack =="
"$PY" -m pip install -U pip wheel
"$PY" -m pip install setuptools==70.2.0
"$PY" -m pip install --upgrade --index-url https://download.pytorch.org/whl/cu128 \
  torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1
"$PY" -m pip install --upgrade --index-url https://download.pytorch.org/whl/cu128 \
  xformers==0.0.33.post2

echo "== Installing SANA-WM Python dependencies =="
"$PIP" install --no-build-isolation mmcv==1.7.2
"$PIP" install \
  "accelerate>=1.3" \
  "diffusers>=0.37.0" \
  einops \
  ftfy \
  huggingface-hub==0.36.0 \
  imageio \
  imageio-ffmpeg \
  omegaconf \
  opencv-python \
  patch_conv \
  pillow \
  pytz \
  qwen-vl-utils \
  pyrallis \
  safetensors \
  scipy \
  sentencepiece \
  termcolor \
  timm==0.6.13 \
  transformers==4.57.3
"$PIP" install "flash-linear-attention>=0.4.2"

echo "== Downloading SANA-WM stage-1/VAE subset =="
"$PY" - <<PY
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="$HF_REPO",
    local_dir="$LAB/models/SANA-WM_bidirectional_stage1",
    local_dir_use_symlinks=False,
    allow_patterns=[
        "README.md",
        "config.yaml",
        "dit/sana_wm_1600m_720p.safetensors",
        "vae/config.json",
        "vae/diffusion_pytorch_model.safetensors",
    ],
)
PY

echo "== Creating local no-refiner config =="
cp "$LAB/models/SANA-WM_bidirectional_stage1/config.yaml" "$LAB/configs/sana_wm_stage1_local.yaml"
"$PY" - <<PY
from pathlib import Path

path = Path("$LAB/configs/sana_wm_stage1_local.yaml")
text = path.read_text()
text = text.replace(
    "vae_pretrained: hf://Efficient-Large-Model/SANA-WM_bidirectional",
    "vae_pretrained: $LAB/models/SANA-WM_bidirectional_stage1",
)
path.write_text(text)
PY

echo "== Smoke-testing imports =="
cd "$LAB/Sana"
PYTHONPATH="$LAB/Sana:${PYTHONPATH:-}" "$PY" - <<'PY'
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
import triton
print("triton", triton.__version__)
import mmcv
print("mmcv", mmcv.__version__)
import fla
print("fla import ok")
PY

echo ""
echo "Ready. Run the probe:"
echo "  bash scripts/wsl/run_sana_wm_stage1_probe.sh"
