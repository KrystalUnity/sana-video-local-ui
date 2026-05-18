# Demo Script

Goal: make a 30 to 45 second screen recording that proves the app is real, local, and practical.

## Shot List

1. Show the repo README for 2 seconds.
2. Switch to the running UI at `http://127.0.0.1:5173`.
3. Hover one or two tooltips: `Segments` and `Memory mode`.
4. Show the safe settings:
   - Memory mode: `Low VRAM`
   - Frames: `17` or `25`
   - Segments: `1` or `2`
   - Steps: `8`
   - Unload after generation: enabled
5. Upload or show a start image if using image-to-video.
6. Click `Generate`.
7. Show the progress panel and peak VRAM field.
8. Cut to the completed output playing in the UI.
9. End on the repo link.

## Voiceover

I wanted a practical local UI for testing SANA-Video 2B on consumer hardware, especially Windows laptops where VRAM pressure gets real fast.

This is a React + FastAPI workbench with text-to-video, optional start images, chained segments for longer clips, low-VRAM mode, model profiles, progress tracking, and a replay gallery.

It does not include model weights, but it points at a local model folder and is structured so future SANA releases can be swapped in through profiles or backend adapters.

Repo is public on GitHub.

## Caption

Local SANA-Video 2B testing on a consumer GPU. React + FastAPI UI, image starts, chained segments, low-VRAM mode, model profiles, progress tracking, and gallery replay.

Repo: https://github.com/KrystalUnity/sana-video-local-ui

## Suggested Recording Sizes

- X / LinkedIn / YouTube: 1920 x 1080.
- Vertical social: 1080 x 1920 with the UI zoomed in on controls and output.
- GitHub README GIF: short loop under 10 seconds if possible.
