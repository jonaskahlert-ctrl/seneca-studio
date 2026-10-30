#!/usr/bin/env python3
import argparse, json, os, subprocess

def render(input_mp4, edl_path, out_dir):
    with open(edl_path) as f:
        edl = json.load(f)
    keep = [s for s in edl.get("segments", []) if s.get("action") == "KEEP"]
    if not keep:
        keep = [{"start": 0.0, "end": 10.0}]
    os.makedirs(out_dir, exist_ok=True)
    master_out = os.path.join(out_dir, "master_16x9.mp4")
    reel_out = os.path.join(out_dir, "reel_9x16.mp4")
    v_parts, a_parts = [], []
    for idx, seg in enumerate(keep):
        st, en = float(seg["start"]), float(seg["end"])
        v_parts.append(f"[0:v]trim=start={st}:end={en},setpts=PTS-STARTPTS[v{idx}];")
        a_parts.append(f"[0:a]atrim=start={st}:end={en},asetpts=PTS-STARTPTS[a{idx}];")
    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(keep)))
    fc = "".join(v_parts + a_parts) + f"{concat_inputs}concat=n={len(keep)}:v=1:a=1[vout][aout];[aout]loudnorm=I=-16:TP=-1.5:LRA=11[anorm]"
    subprocess.run([
        "ffmpeg", "-y", "-i", input_mp4, "-filter_complex", fc,
        "-map", "[vout]", "-map", "[anorm]", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", master_out
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Render 9:16 vertical crop from master
    subprocess.run([
        "ffmpeg", "-y", "-i", master_out,
        "-vf", "crop=ih*9/16:ih:(iw-ow)/2:0,scale=540:960",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "copy", reel_out
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"master_16x9": master_out, "reel_9x16": reel_out, "kept_segments": len(keep)}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input_mp4")
    p.add_argument("edl_json")
    p.add_argument("--out-dir", default=".")
    args = p.parse_args()
    print(json.dumps(render(args.input_mp4, args.edl_json, args.out_dir)))
