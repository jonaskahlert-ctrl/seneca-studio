---
name: seneca-check-audio-pace
description: Measures exact LUFS loudness, peak dBTP, and speaking pace (WPM) on the spoken first-sentence clip using deterministic FFmpeg + Gemini speech check.
---

# Capability Skill: Audio Loudness & Speaking Pace QA (Loop B)

1. **Deterministic Audio Telemetry**: Always execute `python3 scripts/analyze_audio.py <clip_path> --word-count <N>` first to compute exact integrated loudness (`input_i` in LUFS), true peak (`input_tp` in dBTP), duration, and words per minute (WPM).
2. Compare the measured LUFS and WPM against the `audio_lufs` and `speaking_pace` thresholds in the active Show Playbook (`SKILL.md`).
3. Return `checks[]` items for `audio_lufs` and `speaking_pace` with `PASS`, `WARN`, or `FAIL` and a clear German coaching instruction.
