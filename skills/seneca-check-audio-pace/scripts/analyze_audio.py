#!/usr/bin/env python3
import argparse
import json
import math
import re
import struct
import subprocess
import wave


def measure_wav_speech_window(wav_path: str) -> dict:
    """Measures active speech duration (excluding leading/trailing silence), RMS dBFS, and Peak dBFS directly from PCM samples."""
    try:
        with wave.open(wav_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

        if sampwidth != 2 or n_frames == 0:
            return {}

        total_samples = len(raw_bytes) // 2
        samples = struct.unpack(f"<{total_samples}h", raw_bytes)
        if n_channels > 1:
            samples = samples[0::n_channels]

        total_dur = len(samples) / float(framerate)
        window_size = max(1, int(framerate * 0.05))  # 50ms windows
        window_rms_db = []
        peak_abs = 1

        for i in range(0, len(samples), window_size):
            chunk = samples[i : i + window_size]
            if not chunk:
                continue
            local_max = max(abs(x) for x in chunk)
            if local_max > peak_abs:
                peak_abs = local_max
            mean_sq = sum(float(x) * float(x) for x in chunk) / len(chunk)
            rms = math.sqrt(mean_sq)
            db = 20.0 * math.log10(max(rms, 1.0) / 32768.0)
            window_rms_db.append(db)

        if not window_rms_db:
            return {}

        peak_db = 20.0 * math.log10(max(peak_abs, 1.0) / 32768.0)
        max_win_db = max(window_rms_db)
        # Adaptive voice activity threshold: 18 dB below peak window, or at least -48 dBFS
        vad_threshold = max(-48.0, min(-28.0, max_win_db - 18.0))
        active_indices = [idx for idx, db in enumerate(window_rms_db) if db >= vad_threshold]

        if active_indices:
            first_idx = active_indices[0]
            last_idx = active_indices[-1]
            speech_span_sec = max(0.6, (last_idx - first_idx + 1) * 0.05)
            active_dbs = [window_rms_db[i] for i in active_indices]
            # Convert active RMS dBFS to approximate LUFS (speech RMS dBFS is roughly LUFS)
            mean_active_rms_db = sum(active_dbs) / len(active_dbs)
        else:
            speech_span_sec = total_dur
            mean_active_rms_db = sum(window_rms_db) / len(window_rms_db)

        return {
            "total_duration_sec": round(total_dur, 2),
            "speech_duration_sec": round(speech_span_sec, 2),
            "rms_lufs_approx": round(mean_active_rms_db, 1),
            "pcm_peak_db": round(peak_db, 1),
            "active_windows": len(active_indices),
        }
    except Exception:
        return {}


def analyze(path: str, word_count: int = 10) -> dict:
    cmd = ["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    stderr = proc.stderr

    dur_m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
    duration = 4.0
    if dur_m:
        duration = int(dur_m.group(1)) * 3600 + int(dur_m.group(2)) * 60 + float(dur_m.group(3))

    i_matches = re.findall(r"I:\s*(-?\d+\.\d+)\s*LUFS", stderr)
    tp_matches = re.findall(r"Peak:\s*(-?\d+\.\d+)\s*dBFS", stderr)

    pcm_stats = measure_wav_speech_window(path)
    speech_dur = pcm_stats.get("speech_duration_sec") or duration

    ebur_lufs = float(i_matches[-1]) if i_matches else None
    # If ebur128 gated out (-70.0 LUFS on a short clip), use active speech RMS dBFS
    if ebur_lufs is None or ebur_lufs <= -55.0:
        lufs = pcm_stats.get("rms_lufs_approx", -24.0)
    else:
        lufs = ebur_lufs

    peak = float(tp_matches[-1]) if tp_matches else pcm_stats.get("pcm_peak_db", -6.0)
    wpm = round((word_count / max(speech_dur, 0.8)) * 60.0)

    return {
        "duration_sec": round(duration, 2),
        "speech_duration_sec": round(speech_dur, 2),
        "lufs": round(lufs, 1),
        "peak_db": round(peak, 1),
        "wpm": wpm,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--word-count", type=int, default=10)
    args = p.parse_args()
    print(json.dumps(analyze(args.path, args.word_count)))
