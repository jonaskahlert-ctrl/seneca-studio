# Seneca Studio — Skill-Driven Editorial Video Studio Prototype

A live, browser-webcam-enabled editorial studio application built on **Google Cloud Run**, **Gemini Enterprise Agent Platform (Skill Registry & Managed Agent API)**, **Vertex AI Gemini 2.5 Flash**, **Google Cloud Text-to-Speech (`Chirp 3: HD`)**, and **FFmpeg (`ebur128` + `loudnorm`)**.

---

## Core Capabilities

1. **Integrated 5-Section Studio Teleprompter (`01 Teleprompter-Manuskript` & `03 Studio-Aufnahme`)**
   - Pre-loaded and directly editable 5-section broadcast teleprompter script (`/static/media/teleprompter_script.txt` & `.json`) with `[BETONUNG]` emphasis markers and `[ATEMPAUSE]` / `[PAUSE 0.5s]` cues.
   - Positioned in the upper third of the 16:9 broadcast monitor along the camera eye-line (`▶ ... ◀`) with adjustable auto-scroll speed (WPM).

2. **Hands-Free Pre-Flight Loop with Visual Reward & Per-Check Override (`02 Kamera- & Ton-Vorprüfung`)**
   - **2A Visual Check**: Captures live webcam frames (`getUserMedia`) and evaluates framing, headroom, 9:16 crop safety, lighting, and custom studio rules defined in `SKILL.md`.
   - **2B Audio & Speaking Pace Check**: Records a 4.2-second live microphone take of the first sentence, strips leading/trailing silence (`analyze_audio.py`), measures true **LUFS**, **Peak dBFS**, and **WPM** from spoken words, and compares consecutive attempts with playable audio history.
   - **Visual Reward**: Resolved checks turn emerald green (`✓ GELÖST` / `✓ NEU GELÖST`) with a live progress bar (`X / Y gelöst`) and a green studio banner readable from 2 meters away.
   - **Chirp 3 HD Studio Regie Voice**: Speaks concise German studio directions via `de-DE-Chirp3-HD-Aoede` (`Charon`, `Leda`), automatically pausing before microphone recording starts.
   - **Per-Check & Global Override**: Every individual check or stage can be overridden (`Übersteuern`) at any time.

3. **Prominent `SKILL.md` Governance (`SKILL.md · Format-Regeln verwalten`)**
   - Editorial and technical rules are decoupled from application code and stored in modular `SKILL.md` files synced with the **GCP Agent Platform Skill Registry (`europe-west4`)**.
   - Includes 1-click live rule injection (`+ Keine Kaffeetasse`, `+ Kein Headset/AirPods`, `+ Blickkontakt`) to test zero-code rule changes immediately against the live webcam.

4. **Automated Rough-Cut & Dual-Format Mastering (`03 Studio-Aufnahme & Rohschnitt`)**
   - Records the presenter reading from the integrated teleprompter, generates an Edit Decision List (`edl.json`) removing retakes/slips and pauses (`>0.8s`), and renders both a **16:9 Broadcast Master** and a **9:16 Vertical Reel** normalized to **-16.0 LUFS** (`ffmpeg loudnorm`).

---

## Repository Structure

```text
.
├── app/
│   ├── main.py                  # FastAPI backend (Skill Registry sync, Gemini multimodal checks, Chirp 3 HD TTS, FFmpeg mastering)
│   └── static/
│       └── index.html           # Seneca Swiss Editorial Studio UI (Newsreader + Inter + JetBrains Mono)
├── skills/                      # Modular Agent Skills (mounted & synced to GCP Skill Registry)
│   ├── seneca-show-aktuell/ # Format Playbook: Studio Analyse (16:9 + 9:16)
│   ├── seneca-seneca-show-finanz-kompakt/ # Format Playbook: Finanz Kompakt (9:16)
│   ├── seneca-check-studio-visuals/# Capability Skill: Framing & Lighting QA
│   ├── seneca-check-audio-pace/    # Capability Skill: FFmpeg EBUR128 + WPM QA (with scripts/analyze_audio.py)
│   ├── seneca-prep-teleprompter/   # Capability Skill: Article -> 5-Section Teleprompter Script
│   └── seneca-auto-cut-master/     # Capability Skill: EDL Cut + Dual 16:9 / 9:16 FFmpeg Mastering
├── docs/
│   └── ARCHITECTURE.md          # Clean-Slate Architecture & Nov 5 Hackathon Blueprint
├── Dockerfile                   # Python 3.12 + FFmpeg container image
├── requirements.txt             # FastAPI, Uvicorn, Google Auth, Requests, Pillow
└── deploy.sh                    # One-command Cloud Run deployment script
```

---

## Local Development

```bash
pip install -r requirements.txt
cd app
uvicorn main:app --host 0.0.0.0 --port 8095 --reload
```

---

## Deploying to Google Cloud Run

```bash
chmod +x deploy.sh
./deploy.sh
```

### Granting External User Access via Cloud Run IAP

```bash
gcloud iap web add-iam-policy-binding \
  --resource-type=cloud-run \
  --region=europe-west1 \
  --service=seneca-studio \
  --member="user:user@example-domain.invalid" \
  --role="roles/iap.httpsResourceAccessor" \
  --project=your-gcp-project-id
```
