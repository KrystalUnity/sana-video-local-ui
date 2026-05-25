# Release Checklist

## Before Sharing

- [ ] Add `assets/ui-screenshot.png` to the README if desired.
- [ ] Create a first GitHub release, for example `v0.1.0`.
- [ ] Add GitHub topics:
  - `sana-video`
  - `text-to-video`
  - `image-to-video`
  - `diffusers`
  - `local-ai`
  - `video-generation`
  - `react`
  - `fastapi`
  - `nvidia`
  - `windows`
- [ ] Pin one known-working settings block in the README.
- [ ] Confirm no local model paths, secrets, or paid component references are committed.
- [ ] Record one short demo clip from the local UI.
- [ ] Record or link one short WSL2 SANA-WM probe clip if mentioning SANA-WM.

## Good First Issues

- Add a hardware results table.
- Add a setup smoke test command.
- Add a ComfyUI handoff/export option.
- Add more model profile examples.
- Add a SANA-WM UI adapter around the official NVLabs script.
- Add README screenshots and a short demo GIF.

## First Outreach Targets

- Jeff and close AI builder friends.
- Hugging Face discussion thread for the relevant SANA-Video model.
- Local AI Discords.
- Reddit communities focused on local generative AI and video generation.
- LinkedIn post for builder credibility.
- X / Threads for quick discovery.

## What Not To Claim

- Do not say this includes NVIDIA weights.
- Do not say SANA-WM is integrated into the UI yet. It is currently an experimental WSL2 CLI probe.
- Do not promise long clips in a single model pass. The app uses chained short segments.
- Do not imply 12 GB VRAM is comfortable for all settings. Start low and scale.
