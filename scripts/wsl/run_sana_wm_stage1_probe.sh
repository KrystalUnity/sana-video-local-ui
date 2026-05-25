#!/usr/bin/env bash
set -euo pipefail

LAB="${SANA_WM_LAB:-$HOME/sana-wm-lab}"

cd "$LAB/Sana"
source "$LAB/.venv311/bin/activate"
export PYTHONPATH="$LAB/Sana:${PYTHONPATH:-}"
mkdir -p "$LAB/outputs"

python inference_video_scripts/inference_sana_wm.py \
  --config "$LAB/configs/sana_wm_stage1_local.yaml" \
  --model_path "$LAB/models/SANA-WM_bidirectional_stage1/dit/sana_wm_1600m_720p.safetensors" \
  --image asset/sana_wm/demo_0.png \
  --prompt asset/sana_wm/demo_0.txt \
  --output_dir "$LAB/outputs" \
  --name stage1_probe_demo_0 \
  --camera asset/sana_wm/demo_0_pose.npy \
  --intrinsics asset/sana_wm/demo_0_intrinsics.npy \
  --num_frames 17 \
  --fps 8 \
  --step 12 \
  --cfg_scale 4.0 \
  --seed 42 \
  --no_refiner \
  --offload_vae

echo ""
echo "Saved:"
echo "  $LAB/outputs/stage1_probe_demo_0_generated.mp4"
