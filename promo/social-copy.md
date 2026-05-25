# Social Copy

Use the repo link:

`https://github.com/KrystalUnity/sana-video-local-ui`

## Short Post

Got SANA-Video 2B running locally and built a small Windows-friendly React + FastAPI workbench around it.

It has text-to-video, image starts, chained segments for longer clips, low-VRAM mode, model profiles, progress tracking, and an output gallery.

Update: SANA-WM is now also verified locally through WSL2 as a CLI probe. Native Windows hit Linux CUDA/Triton dependency walls, but WSL2 worked on a 12 GB laptop GPU with the stage-1/no-refiner path.

Repo:
https://github.com/KrystalUnity/sana-video-local-ui

## X / Threads

Built a local UI for SANA-Video 2B.

React + FastAPI, Windows-friendly, tested around a 12 GB laptop GPU.

Features:
- text-to-video + image starts
- chained segments for longer clips
- low-VRAM mode
- model profiles for future swaps
- progress + output gallery
- experimental SANA-WM WSL2 probe

https://github.com/KrystalUnity/sana-video-local-ui

## X / Threads - SANA-WM Update

SANA-WM is real now, and we got it running locally on a Windows laptop through WSL2.

Native Windows hit the expected Triton/Linux CUDA wall. WSL2 Ubuntu saw the RTX 5070 Ti Laptop GPU, installed the Linux stack, and generated a 1280x704 stage-1/no-refiner probe.

Repo + notes:
https://github.com/KrystalUnity/sana-video-local-ui

## LinkedIn

I put together a local workbench for experimenting with SANA-Video 2B on consumer hardware.

The goal is practical testing, not hype: a React + FastAPI UI with text-to-video, image start frames, chained segment generation for longer clips, low-VRAM controls, model profiles, job progress, and an output gallery.

It does not include model weights. Since the SANA-WM release landed, I also added an experimental WSL2 CLI probe using the official NVLabs script. That path is verified locally, but it is not yet integrated into the React UI.

Repo:
https://github.com/KrystalUnity/sana-video-local-ui

## Facebook / Friend Network

Small local AI build: I got SANA-Video 2B running on my laptop and wrapped it in a UI so it is easier to test.

It supports prompt-to-video, start images, chained clips, low-VRAM mode, model profiles, and a little output gallery.

Repo is public now:
https://github.com/KrystalUnity/sana-video-local-ui

PRs and hardware notes welcome.

SANA-WM note: WSL2 is now the practical Windows path for the official script because the dependency stack expects Linux CUDA/Triton packages.

## Reddit / Community Post

Title:
Windows-friendly local UI for SANA-Video 2B with low-VRAM mode and chained segments

Body:
I built a small React + FastAPI workbench for running the available SANA-Video 2B diffusers model locally.

It is aimed at practical local testing on consumer GPUs, especially Windows laptops where VRAM pressure matters.

Features:
- text-to-video and image-to-video start frames
- chained segment generation for longer clips
- low-VRAM and balanced modes
- model profiles for swapping local model folders
- job progress, peak VRAM reporting, and output gallery

It does not include model weights. SANA-WM has now been tested through WSL2 with the official NVLabs script. The UI still targets SANA-Video; SANA-WM currently lives as an experimental CLI probe.

Repo:
https://github.com/KrystalUnity/sana-video-local-ui

## Hugging Face / Model Discussion

I put together a small local UI around the SANA-Video 2B diffusers workflow for easier Windows testing:

https://github.com/KrystalUnity/sana-video-local-ui

It includes image start frames, chained segment generation, low-VRAM mode, model profiles, progress tracking, and an output gallery. The repo does not ship weights; it expects users to download the model separately and point the backend at the local folder.

I would welcome notes from anyone testing different GPUs or adapting newer SANA releases.

## DM To Builders

Hey, I made the repo public:

https://github.com/KrystalUnity/sana-video-local-ui

It is a local React + FastAPI UI for SANA-Video 2B with start images, chained segments, low-VRAM controls, and model profiles. Would love a sanity check on setup docs or hardware notes if you have a minute.

We also got SANA-WM running via WSL2 as a separate CLI probe, so the repo now has notes for that path too.

## Reply To Jeff

Repo is live:

https://github.com/KrystalUnity/sana-video-local-ui

It is still early, but the UI has the useful bits now: image starts, chained segments, low-VRAM mode, model profiles, progress, and an output gallery. PRs absolutely welcome.

## Hashtags

`#LocalAI #GenerativeAI #TextToVideo #SANA #SanaWM #Diffusers #OpenSource #ReactJS #FastAPI #NVIDIA #WSL2`
