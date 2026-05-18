# Krystal Unity Website Landing Page Draft

Recommended URL:

`/projects/sana-video-local-ui`

## Page Goal

Use the Krystal Unity site as the polished public doorway. Keep installs, issues, releases, and contributor workflow on GitHub.

## Hero

Headline:

SANA Video Local UI

Subheadline:

A Windows-friendly local workbench for testing SANA-Video 2B on consumer GPUs, with image starts, chained clips, low-VRAM controls, and model profiles.

Primary button:

View on GitHub

Secondary button:

Watch demo

## Short Body Copy

SANA Video Local UI is a practical React + FastAPI workbench for local video generation experiments. It wraps the available SANA-Video 2B diffusers workflow in a focused UI for prompts, optional start images, chained segment generation, memory mode selection, progress tracking, and output replay.

The project is designed for real local testing, not announcement hype. It does not include model weights, and future SANA-WM / VM support will be added only when downloadable weights and APIs are available to test.

## Feature Bullets

- Text-to-video and image-to-video start frames.
- Chained segments for longer clips without one huge generation pass.
- Low-VRAM mode for 12 GB class laptop GPUs.
- Model profiles for local model folder swaps.
- Progress, elapsed time, peak VRAM, and output gallery.
- Open-source React + FastAPI app.

## Proof Block

Tested locally on:

- Windows laptop
- NVIDIA GeForce RTX 5070 Ti Laptop GPU
- 12 GB dedicated VRAM
- SANA-Video 2B 480p diffusers model

Suggested caption:

Built as a practical local lab for video generation experiments on consumer hardware.

## Website CTAs

- GitHub repo: `https://github.com/KrystalUnity/sana-video-local-ui`
- Share kit: link to GitHub `promo/`
- Issues: `https://github.com/KrystalUnity/sana-video-local-ui/issues`

## Page Sections

1. Hero with screenshot or short demo clip.
2. What it does.
3. Why it exists.
4. Hardware-tested note.
5. Honest limitations.
6. GitHub CTA.
7. Share kit / press assets.

## Honest Limitations Copy

This project does not ship model weights. Users download compatible SANA-Video weights separately and point the backend at their local model folder. SANA-WM / VM support is not claimed until the relevant weights and APIs are publicly available and tested.

## Metadata

Title:

SANA Video Local UI | Krystal Unity

Description:

A Windows-friendly React + FastAPI workbench for testing SANA-Video 2B locally with image starts, chained clips, low-VRAM controls, and model profiles.

Open Graph image:

Use `promo/assets/social-card.svg` or export it to PNG for broader social compatibility.
