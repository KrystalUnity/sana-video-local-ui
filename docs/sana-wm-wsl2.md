# Experimental SANA-WM on WSL2

SANA-WM is not wired into the React workbench UI yet. It uses the official
NVLabs SANA-WM script, which has Linux/CUDA dependencies that are awkward on
native Windows. WSL2 is the clean path for Windows machines.

This repo includes a small, reproducible WSL2 probe for the public
`Efficient-Large-Model/SANA-WM_bidirectional` release. It runs the stage-1
model plus VAE with the refiner disabled, which keeps the first test smaller
and more realistic for consumer GPUs.

## What Was Verified

On a Windows laptop with an RTX 5070 Ti Laptop GPU, WSL2 Ubuntu could see CUDA
via `nvidia-smi`, and the stage-1 SANA-WM probe generated a short MP4:

- `1280x704`
- `17` frames
- `8` FPS
- `12` sampling steps
- `--no_refiner`
- `--offload_vae`

That run produced a 2.125 second demo from the official SANA-WM demo assets.

## Requirements

- Windows 11 with WSL2 enabled.
- A recent NVIDIA driver with WSL CUDA support.
- Ubuntu installed in WSL.
- At least 12 GB VRAM for the tiny no-refiner probe. More is better.
- Plenty of disk space. The first setup downloads Python, CUDA PyTorch wheels,
  NVLabs/Sana source, and the SANA-WM stage-1/VAE subset.

The script intentionally does not download the full refiner stack.

## Enable WSL2

Run PowerShell as Administrator:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\wsl\enable_wsl2_windows.ps1
```

If Windows asks for a reboot, reboot and then install Ubuntu:

```powershell
wsl.exe --install -d Ubuntu
```

Check that the GPU is visible inside WSL:

```powershell
wsl.exe -d Ubuntu -- nvidia-smi
```

## Setup SANA-WM In WSL

From the repo root in PowerShell, replace the path with your repo path:

```powershell
wsl.exe -d Ubuntu -- bash -lc "bash /mnt/c/path/to/sana-video-local-ui/scripts/wsl/setup_sana_wm_wsl2.sh"
```

The setup creates:

```text
~/sana-wm-lab/
  Sana/
  .venv311/
  models/SANA-WM_bidirectional_stage1/
  configs/sana_wm_stage1_local.yaml
  outputs/
```

## Run The Tiny Probe

```powershell
wsl.exe -d Ubuntu -- bash -lc "bash /mnt/c/path/to/sana-video-local-ui/scripts/wsl/run_sana_wm_stage1_probe.sh"
```

The output is written to:

```text
~/sana-wm-lab/outputs/stage1_probe_demo_0_generated.mp4
```

From Windows Explorer, WSL files are usually visible under:

```text
\\wsl.localhost\Ubuntu\root\sana-wm-lab\outputs
```

## Current Limitations

- This is CLI-only. The React UI still targets the SANA-Video Diffusers adapter.
- The SANA-WM full refiner is not part of the tiny probe.
- Native Windows is not the recommended path because the official script relies
  on Linux-friendly Triton and attention packages.
- The prompt argument is a file path in the official script, not raw prompt text.

## Next Adapter Work

A proper UI adapter should expose SANA-WM-specific inputs:

- start image
- prompt file or text-to-temp-file wrapper
- camera path or action string
- intrinsics path
- frame count
- steps
- guidance
- no-refiner/refiner mode
- VAE/refiner offload controls

Until then, treat the WSL2 script as the tested probe lane and the main UI as
the SANA-Video workbench.
