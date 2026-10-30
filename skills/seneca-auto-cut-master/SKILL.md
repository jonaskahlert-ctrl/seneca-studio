---
name: seneca-auto-cut-master
description: Uses Gemini Multimodal to identify retakes and long pauses into edl.json, then runs scripts/render_cuts.py (FFmpeg) for zero-token video cutting and 16:9 / 9:16 mastering.
---

# Capability Skill: Smart Cut EDL & Deterministic Mastering

1. Analyze the raw recording (`raw_take.mp4`) using Gemini Multimodal to identify:
   - **Retakes / Stumbles**: Spoken false starts or repeated sentences (mark `action: "REMOVE"`, `reason: "Retake / Versprecher"`).
   - **Long Pauses**: Dead air exceeding the show's threshold (mark `action: "REMOVE"`, `reason: "Sprechpause > 0.8s"`).
   - **Clean Segments**: Segments to keep (`action: "KEEP"`).
2. Save the resulting timestamp array to `edl.json`.
3. Execute `python3 scripts/render_cuts.py raw_take.mp4 edl.json --out-dir <dir>` to deterministically splice the keep-segments, normalize audio to -16 LUFS, and render both `master_16x9.mp4` and `reel_9x16.mp4`.
