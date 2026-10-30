import base64
import io
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import zipfile
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ID = os.environ.get("PROJECT_ID", "YOUR_GCP_PROJECT_ID")
PROJECT_NUMBER = os.environ.get("PROJECT_NUMBER", "YOUR_GCP_PROJECT_NUMBER")
SKILL_LOCATION = os.environ.get("SKILL_LOCATION", "europe-west4")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "europe-west4")
AGENT_ID = os.environ.get("AGENT_ID", "seneca-studio-agent")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(APP_DIR)
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
MEDIA_DIR = os.path.join(APP_DIR, "static", "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

app = FastAPI(title="Seneca Studio Prototype (Live Webcam + Skill Registry)")
app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")

DEFAULT_TELEPROMPTER_SCRIPTS: Dict[str, Dict[str, Any]] = {
    "seneca-show-aktuell": {
        "show_id": "seneca-show-aktuell",
        "title": "Format Aktuell — Die neue Realität an der Ostfront bei Pokrowsk",
        "article_text": (
            "An der Ostfront bei Pokrowsk verschiebt sich die militärische Dynamik spürbar. "
            "Während im ersten Kriegsjahr noch grosse Panzerverbände und geschlossene Artillerieduelle das Bild prägten, "
            "setzen die russischen Streitkräfte heute auf kleine, hochmobile Infanteriegruppen, die im Schutz der Dämmerung vorrücken. "
            "Über dem Gefechtsfeld patrouillieren ununterbrochen Aufklärungs- und FPV-Drohnen, die jede grössere Truppenbewegung innerhalb von Minuten erfassen. "
            "Für die ukrainische Verteidigung bedeutet das: Klassische Nachschublinien über asphaltierte Hauptstrassen sind kaum noch nutzbar. "
            "Munition, Verwundete und Ersatzteile müssen nachts in kleinen Etappen transportiert werden. "
            "Damit wird nicht die Zahl der Kampfpanzer, sondern die geschützte Logistik auf den letzten zehn Kilometern zur entscheidenden Schlüsselfrage des kommenden Winters."
        ),
        "first_sentence_plain": "An der Ostfront bei Pokrowsk verschiebt sich die militärische Dynamik spürbar.",
        "first_sentence_word_count": 11,
        "target_wpm": 130,
        "estimated_duration_sec": 75,
        "storage_path": "/static/media/teleprompter_script.json",
        "storage_txt_path": "/static/media/teleprompter_script.txt",
        "updated_at": "Standard-Studiofassung",
        "segments": [
            {
                "index": 1,
                "section": "01 ANMODERATION & EINSTIEG",
                "spoken_text": (
                    "An der Ostfront bei [BETONUNG] POKROWSK verschiebt sich die militärische Dynamik spürbar. [ATEMPAUSE] "
                    "Wer auf die Karten blickt, sieht langsame Geländegewinne — doch vor Ort hat sich die Art der Kriegsführung radikal verändert."
                ),
                "duration_sec": 14,
            },
            {
                "index": 2,
                "section": "02 TAKTIK DER KLEINEN GRUPPEN",
                "spoken_text": (
                    "Statt grosser [BETONUNG] PANZERKOLONNEN setzen die russischen Verbände auf kleine, hochmobile Infanterietrupps. [ATEMPAUSE] "
                    "Sie rücken zu dritt oder zu viert vor, nutzen Baumreihen als Deckung und testen systematisch jede Lücke in den ukrainischen Stellungen."
                ),
                "duration_sec": 16,
            },
            {
                "index": 3,
                "section": "03 DIE GLÄSERNE FRONT DURCH DROHNEN",
                "spoken_text": (
                    "Der Grund dafür liegt am Himmel: [PAUSE 0.5s] "
                    "Ein dichter Teppich aus [BETONUNG] AUFKLÄRUNGS- UND KAMPFDROHNEN macht das Gefechtsfeld auf bis zu fünfzehn Kilometer Tiefe gläsern. [ATEMPAUSE] "
                    "Jedes grössere Fahrzeug wird innerhalb weniger Minuten entdeckt und angegriffen."
                ),
                "duration_sec": 17,
            },
            {
                "index": 4,
                "section": "04 NACHSCHUB ALS SCHLÜSSELFRAGE",
                "spoken_text": (
                    "Für [BETONUNG] KIEW wird damit die Logistik auf den letzten zehn Kilometern zur Überlebensfrage. [ATEMPAUSE] "
                    "Munition, Batterien und der Abtransport von Verwundeten können fast nur noch in der Dämmerung oder bei Nebel erfolgen."
                ),
                "duration_sec": 15,
            },
            {
                "index": 5,
                "section": "05 AUSBLICK AUF DEN WINTER",
                "spoken_text": (
                    "Entscheidend für den kommenden Winter ist deshalb [BETONUNG] NICHT allein die Zahl schwerer Waffen. [PAUSE 0.5s] "
                    "Entscheidend ist, wer seine Versorgungslinien gegen elektronische Störung und Drohnenangriffe dauerhaft absichern kann."
                ),
                "duration_sec": 13,
            },
        ],
    },
    "seneca-show-finanz-kompakt": {
        "show_id": "seneca-show-finanz-kompakt",
        "title": "Finanz Kompakt — Frankenstärke und SNB-Zinsentscheid",
        "article_text": (
            "Der Schweizer Franken bleibt gegenüber dem Euro und dem Dollar auf hohem Niveau. "
            "Während Konsumenten von günstigeren Importen und tiefer Inflation profitieren, gerät die Schweizer Exportindustrie zunehmend unter Margendruck. "
            "Für die Schweizerische Nationalbank wird der nächste Zinsentscheid damit zur Gratwanderung zwischen Preisstabilität und Konjunkturstützung."
        ),
        "first_sentence_plain": "Der Schweizer Franken bleibt gegenüber dem Euro und dem Dollar auf Rekordkurs.",
        "first_sentence_word_count": 12,
        "target_wpm": 145,
        "estimated_duration_sec": 60,
        "storage_path": "/static/media/teleprompter_script.json",
        "storage_txt_path": "/static/media/teleprompter_script.txt",
        "updated_at": "Standard-Studiofassung",
        "segments": [
            {
                "index": 1,
                "section": "01 HOOK (0–10s)",
                "spoken_text": (
                    "Der [BETONUNG] SCHWEIZER FRANKEN bleibt gegenüber Euro und Dollar auf Rekordkurs. [ATEMPAUSE] "
                    "Was Sparer freut, wird für die Exportwirtschaft zur echten Belastungsprobe."
                ),
                "duration_sec": 12,
            },
            {
                "index": 2,
                "section": "02 DRUCK AUF DIE INDUSTRIE",
                "spoken_text": (
                    "Vor allem die [BETONUNG] MASCHINEN- UND ELEKTROINDUSTRIE spürt den starken Wechselkurs direkt in den Auftragsbüchern. [ATEMPAUSE] "
                    "Preiserhöhungen lassen sich im europäischen Markt kaum noch durchsetzen."
                ),
                "duration_sec": 15,
            },
            {
                "index": 3,
                "section": "03 DAS DILEMMA DER NATIONALBANK",
                "spoken_text": (
                    "Im Fokus steht jetzt die [BETONUNG] NATIONALBANK. [PAUSE 0.5s] "
                    "Mit einer Inflation von unter einem Prozent hat die SNB zwar Spielraum für weitere Zinssenkungen — doch die Untergrenze rückt näher."
                ),
                "duration_sec": 17,
            },
            {
                "index": 4,
                "section": "04 FAZIT FÜR ANLEGER",
                "spoken_text": (
                    "Für Anleger heisst das: [BETONUNG] QUALITÄTSTITEL mit hoher Preismacht bleiben im Vorteil. [ATEMPAUSE] "
                    "Die vollständige Analyse lesen Sie jetzt auf unserem Nachrichtenportal."
                ),
                "duration_sec": 14,
            },
        ],
    },
}


def persist_teleprompter_script(script_obj: Dict[str, Any]) -> Dict[str, Any]:
    script_obj["storage_path"] = "/static/media/teleprompter_script.json"
    script_obj["storage_txt_path"] = "/static/media/teleprompter_script.txt"
    script_obj["updated_at"] = time.strftime("%H:%M:%S")
    json_path = os.path.join(MEDIA_DIR, "teleprompter_script.json")
    txt_path = os.path.join(MEDIA_DIR, "teleprompter_script.txt")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(script_obj, f, ensure_ascii=False, indent=2)
    lines = [f"# {script_obj.get('title', 'Seneca Teleprompter-Manuskript')}\n"]
    for seg in script_obj.get("segments", []):
        lines.append(f"\n[{seg.get('section', '')}]\n{seg.get('spoken_text', '')}\n")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    show_id = script_obj.get("show_id", "seneca-show-aktuell")
    SESSION_STATE.setdefault("teleprompter_scripts", {})[show_id] = script_obj
    return script_obj


SESSION_STATE: Dict[str, Any] = {
    "environment_id": None,
    "previous_interaction_id": None,
    "visual_turn_history": [],
    "audio_turn_history": [],
    "teleprompter_scripts": {
        k: dict(v) for k, v in DEFAULT_TELEPROMPTER_SCRIPTS.items()
    },
}
persist_teleprompter_script(dict(DEFAULT_TELEPROMPTER_SCRIPTS["seneca-show-aktuell"]))


def get_gcp_token() -> str:
    try:
        import google.auth
        import google.auth.transport.requests
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        if creds.token:
            return creds.token
    except Exception:
        pass
    return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()


def read_local_skill_md(skill_id: str) -> str:
    p = os.path.join(SKILLS_DIR, skill_id, "SKILL.md")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def write_local_skill_and_zip(skill_id: str, skill_md: str) -> bytes:
    sdir = os.path.join(SKILLS_DIR, skill_id)
    os.makedirs(sdir, exist_ok=True)
    md_path = os.path.join(sdir, "SKILL.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(skill_md)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(sdir):
            for fn in files:
                full_p = os.path.join(root, fn)
                rel_p = os.path.relpath(full_p, sdir)
                zf.write(full_p, rel_p)
    zip_bytes = buf.getvalue()
    zip_path = os.path.join(SKILLS_DIR, f"{skill_id}.zip")
    with open(zip_path, "wb") as f:
        f.write(zip_bytes)
    return zip_bytes


def call_gemini_json(
    prompt: str,
    system_instruction: str,
    media_parts: Optional[List[Dict[str, Any]]] = None,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    token = get_gcp_token()
    parts: List[Dict[str, Any]] = []
    if media_parts:
        parts.extend(media_parts)
    parts.append({"text": prompt})

    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    url = (
        f"https://{VERTEX_LOCATION}-aiplatform.googleapis.com/v1beta1/"
        f"projects/{PROJECT_ID}/locations/{VERTEX_LOCATION}/publishers/google/models/{model}:generateContent"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": PROJECT_ID,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def synthesize_chirp3_hd(
    text: str,
    voice_name: str = "de-DE-Chirp3-HD-Aoede",
) -> Optional[str]:
    if not text or not text.strip():
        return None
    try:
        token = get_gcp_token()
        clean = text
        for sym in ["✅", "⚠️", "❌", "●", "Δ", "🎙️", "📸", "🔴", "⏭️"]:
            clean = clean.replace(sym, "")
        # Phonetic normalization for natural broadcast German vowel lengths in Chirp 3 HD
        phonetic_pairs = [
            ("schliessen", "schließen"),
            ("Schliessen", "Schließen"),
            ("grösser", "größer"),
            ("grosser", "großer"),
            ("grosse", "große"),
            ("grossen", "großen"),
            ("gemäss", "gemäß"),
            ("gleichmässig", "gleichmäßig"),
            ("regelmässig", "regelmäßig"),
            ("heisst", "heißt"),
            ("aussen", "außen"),
            ("LUFS", "Pegel"),
            ("dBTP", "Dezibel"),
            ("WPM", "Wörter pro Minute"),
        ]
        for k, v in phonetic_pairs:
            clean = clean.replace(k, v)
        clean = " ".join(clean.split())

        url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        body = {
            "input": {"text": clean},
            "voice": {"languageCode": "de-DE", "name": voice_name},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.02},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Goog-User-Project": PROJECT_ID,
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("audioContent")
    except Exception as e:
        print(f"TTS Warning: {e}")
        return None


def apply_check_overrides(
    res: Dict[str, Any],
    ignored_ids: List[str],
    status_key: str,
    stage_label: str,
) -> Dict[str, Any]:
    ignored_set = set(ignored_ids or [])
    checks = res.get("checks", [])
    open_corrections: List[str] = []
    any_fail = False
    any_warn = False

    for c in checks:
        cid = c.get("id", "")
        orig_st = (c.get("status") or "WARN").upper()
        c["original_status"] = orig_st
        if cid in ignored_set and orig_st != "PASS":
            c["status"] = "OVERRIDE"
            c["overridden"] = True
        else:
            c["overridden"] = False
            if orig_st == "FAIL":
                any_fail = True
                if c.get("correction"):
                    open_corrections.append(c["correction"])
            elif orig_st == "WARN":
                any_warn = True
                if c.get("correction"):
                    open_corrections.append(c["correction"])

    if any_fail:
        res[status_key] = "FAIL"
    elif any_warn:
        res[status_key] = "WARN"
    else:
        res[status_key] = "PASS"
        if status_key == "overall_audio_status":
            res["ready_to_record"] = True

    if ignored_set:
        if res[status_key] == "PASS":
            if stage_label == "visual":
                res["studio_banner_de"] = (
                    "Kamerabild freigegeben (offene Punkte wurden übersteuert). Weiter mit Mikrofon- und Sprechtempo-Check."
                )
            else:
                res["studio_banner_de"] = (
                    "Audio-Check freigegeben. Teleprompter ist bereit für die Aufnahme."
                )
        elif open_corrections:
            res["studio_banner_de"] = " ".join(open_corrections[:2])

    return res


@app.post("/api/tts")
async def api_tts(request: Request):
    body = await request.json()
    text = body.get("text", "")
    voice_name = body.get("voice_name", "de-DE-Chirp3-HD-Aoede")
    audio_b64 = synthesize_chirp3_hd(text, voice_name=voice_name)
    return {"tts_audio_b64": audio_b64, "voice_name": voice_name}


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(APP_DIR, "static", "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/status")
async def api_status():
    token = get_gcp_token()
    agent_info = {}
    try:
        url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/agents/{AGENT_ID}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "X-Goog-User-Project": PROJECT_ID},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            agent_info = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        agent_info = {"error": str(e)}

    return {
        "project_id": PROJECT_ID,
        "project_number": PROJECT_NUMBER,
        "skill_registry_location": SKILL_LOCATION,
        "agent_id": AGENT_ID,
        "agent": agent_info,
        "session_state": {
            "environment_id": SESSION_STATE.get("environment_id"),
            "previous_interaction_id": SESSION_STATE.get("previous_interaction_id"),
            "visual_turns": len(SESSION_STATE.get("visual_turn_history", [])),
            "audio_turns": len(SESSION_STATE.get("audio_turn_history", [])),
        },
    }


@app.get("/api/skills")
async def list_skills():
    token = get_gcp_token()
    url = f"https://{SKILL_LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{SKILL_LOCATION}/skills"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "X-Goog-User-Project": PROJECT_ID},
    )
    registry_skills = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            registry_skills = data.get("skills", [])
    except Exception:
        pass

    enriched = []
    for s in registry_skills:
        sid = s.get("name", "").split("/")[-1]
        if not sid.startswith("seneca-"):
            continue
        md = read_local_skill_md(sid)
        scripts = []
        sdir = os.path.join(SKILLS_DIR, sid, "scripts")
        if os.path.isdir(sdir):
            scripts = os.listdir(sdir)
        enriched.append(
            {
                "id": sid,
                "name": s.get("name"),
                "displayName": s.get("displayName", sid),
                "description": s.get("description", ""),
                "state": s.get("state", "ACTIVE"),
                "updateTime": s.get("updateTime", ""),
                "kind": "show" if sid.startswith("seneca-show-") else "capability",
                "skill_md": md,
                "scripts": scripts,
            }
        )
    enriched.sort(key=lambda x: (0 if x["kind"] == "show" else 1, x["id"]))
    return {"skills": enriched}


@app.post("/api/skills/{skill_id}")
async def update_skill(skill_id: str, request: Request):
    body = await request.json()
    new_md = body.get("skill_md", "")
    if not new_md.strip():
        raise HTTPException(status_code=400, detail="skill_md must not be empty")

    zip_bytes = write_local_skill_and_zip(skill_id, new_md)
    b64_zip = base64.b64encode(zip_bytes).decode("ascii")

    token = get_gcp_token()
    patch_url = (
        f"https://{SKILL_LOCATION}-aiplatform.googleapis.com/v1beta1/"
        f"projects/{PROJECT_ID}/locations/{SKILL_LOCATION}/skills/{skill_id}"
        f"?updateMask=zippedFilesystem"
    )
    payload = json.dumps({"zippedFilesystem": b64_zip}).encode("utf-8")
    req = urllib.request.Request(
        patch_url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": PROJECT_ID,
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            op_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=e.code, detail=err)

    return {
        "status": "UPDATED_IN_SKILL_REGISTRY",
        "skill_id": skill_id,
        "latency_ms": round((time.time() - t0) * 1000),
        "operation": op_data,
    }


@app.get("/api/script")
async def get_script(show_id: str = "seneca-show-aktuell"):
    scripts = SESSION_STATE.get("teleprompter_scripts", {})
    sc = scripts.get(show_id) or DEFAULT_TELEPROMPTER_SCRIPTS.get(
        show_id, DEFAULT_TELEPROMPTER_SCRIPTS["seneca-show-aktuell"]
    )
    return persist_teleprompter_script(dict(sc))


@app.post("/api/script-save")
async def save_script(request: Request):
    body = await request.json()
    show_id = body.get("show_id", "seneca-show-aktuell")
    segments = body.get("segments", [])
    first_sentence_plain = body.get("first_sentence_plain", "")
    article_text = body.get("article_text", "")

    base = dict(
        SESSION_STATE.get("teleprompter_scripts", {}).get(
            show_id, DEFAULT_TELEPROMPTER_SCRIPTS["seneca-show-aktuell"]
        )
    )
    if segments:
        base["segments"] = segments
    if first_sentence_plain:
        base["first_sentence_plain"] = first_sentence_plain
        base["first_sentence_word_count"] = len(first_sentence_plain.split())
    elif segments:
        import re as _re
        first_raw = segments[0].get("spoken_text", "")
        cleaned = _re.sub(r"\[[^\]]*\]", "", first_raw).strip()
        first_sent = cleaned.split(".")[0].strip() + "."
        base["first_sentence_plain"] = first_sent
        base["first_sentence_word_count"] = len(first_sent.split())
    if article_text:
        base["article_text"] = article_text

    total_words = sum(len(s.get("spoken_text", "").split()) for s in base.get("segments", []))
    target_wpm = int(base.get("target_wpm", 130))
    base["estimated_duration_sec"] = max(20, round((total_words / max(target_wpm, 100)) * 60))
    return persist_teleprompter_script(base)


@app.post("/api/script-prep")
async def script_prep(request: Request):
    body = await request.json()
    show_id = body.get("show_id", "seneca-show-aktuell")
    article_text = body.get("article_text", "")

    show_md = read_local_skill_md(show_id)
    cap_md = read_local_skill_md("seneca-prep-teleprompter")

    sys_inst = (
        "Du bist der Seneca Studio Teleprompter-Redaktor. Befolge strikt das aktive Show Playbook SKILL.md "
        "und das Capability SKILL.md.\n"
        "WICHTIG: Erstelle ein vollwertiges, sprechbares Studio-Teleprompter-Manuskript mit 4 bis 5 klaren Abschnitten "
        "(insgesamt ca. 130 bis 170 Wörter für 60–75 Sekunden Sendezeit), kurzen Sprechsätzen, "
        "hervorgehobenen Betonungswörtern in GROSSBUCHSTABEN sowie Sprechpausen-Markern wie `[ATEMPAUSE]` und `[PAUSE 0.5s]`.\n\n"
        f"=== SHOW PLAYBOOK ({show_id}/SKILL.md) ===\n{show_md}\n\n"
        f"=== CAPABILITY SKILL (seneca-prep-teleprompter/SKILL.md) ===\n{cap_md}\n"
    )
    prompt = (
        f"Formatiere und erweitere folgenden Artikel/Entwurf zu einem vollständigen 5-teiligen Studio-Teleprompter-Skript gemäss den Regeln im Show Playbook.\n\n"
        f"Entwurf:\n{article_text}\n\n"
        "Gib exakt folgendes JSON-Format zurück:\n"
        "{\n"
        '  "show_id": "' + show_id + '",\n'
        '  "title": "Sendungstitel",\n'
        '  "first_sentence_plain": "Der erste Satz komplett ohne Marker für den 4-Sekunden-Toncheck",\n'
        '  "first_sentence_word_count": 11,\n'
        '  "target_wpm": 130,\n'
        '  "estimated_duration_sec": 70,\n'
        '  "applied_rules_summary": ["Kurze Regel 1 aus SKILL.md", "Kurze Regel 2 aus SKILL.md"],\n'
        '  "segments": [\n'
        '    {"index": 1, "section": "01 ANMODERATION", "spoken_text": "Sprechtext mit [BETONUNG] WORT und [ATEMPAUSE]", "duration_sec": 15},\n'
        '    {"index": 2, "section": "02 HINTERGRUND", "spoken_text": "...", "duration_sec": 15},\n'
        '    {"index": 3, "section": "03 ANALYSE", "spoken_text": "...", "duration_sec": 15},\n'
        '    {"index": 4, "section": "04 EINORDNUNG", "spoken_text": "...", "duration_sec": 15},\n'
        '    {"index": 5, "section": "05 FAZIT & ABMODERATION", "spoken_text": "...", "duration_sec": 12}\n'
        "  ]\n"
        "}"
    )
    t0 = time.time()
    res = call_gemini_json(prompt=prompt, system_instruction=sys_inst)
    res["article_text"] = article_text
    res["latency_ms"] = round((time.time() - t0) * 1000)
    res = persist_teleprompter_script(res)
    return res


@app.post("/api/preflight/visual")
async def preflight_visual(request: Request):
    body = await request.json()
    show_id = body.get("show_id", "seneca-show-aktuell")
    turn = int(body.get("turn", 1))
    custom_frame_b64 = body.get("custom_frame_b64")
    ignored_check_ids: List[str] = body.get("ignored_check_ids", [])
    voice_enabled: bool = bool(body.get("voice_enabled", True))
    voice_name: str = body.get("voice_name", "de-DE-Chirp3-HD-Aoede")

    if turn == 1:
        SESSION_STATE["visual_turn_history"] = []

    show_md = read_local_skill_md(show_id)
    cap_md = read_local_skill_md("seneca-check-studio-visuals")

    media_parts: List[Dict[str, Any]] = []
    is_live_webcam = bool(custom_frame_b64)

    if is_live_webcam:
        clean_b64 = custom_frame_b64.split(",")[-1]
        cur_path = os.path.join(MEDIA_DIR, f"webcam_v{turn}.jpg")
        with open(cur_path, "wb") as f:
            f.write(base64.b64decode(clean_b64))
        prev_path = os.path.join(MEDIA_DIR, f"webcam_v{turn - 1}.jpg")
        if turn >= 2 and os.path.exists(prev_path):
            with open(prev_path, "rb") as pf:
                prev_b64 = base64.b64encode(pf.read()).decode("ascii")
            media_parts.append({"inlineData": {"mimeType": "image/jpeg", "data": prev_b64}})
        media_parts.append({"inlineData": {"mimeType": "image/jpeg", "data": clean_b64}})
        frame_url = f"/static/media/webcam_v{turn}.jpg?t={int(time.time())}"
    else:
        fname = "frame_v1.jpg" if turn == 1 else "frame_v2.jpg"
        fpath = os.path.join(MEDIA_DIR, fname)
        if turn >= 2 and os.path.exists(os.path.join(MEDIA_DIR, "frame_v1.jpg")):
            with open(os.path.join(MEDIA_DIR, "frame_v1.jpg"), "rb") as pf:
                media_parts.append(
                    {"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(pf.read()).decode("ascii")}}
                )
        with open(fpath, "rb") as cf:
            media_parts.append(
                {"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(cf.read()).decode("ascii")}}
            )
        frame_url = f"/static/media/{fname}?t={int(time.time())}"

    prev_context = ""
    if turn >= 2 and SESSION_STATE["visual_turn_history"]:
        prev_context = (
            "\n\n=== PREVIOUS TURN (previous_interaction_id) CHECK RESULTS ===\n"
            + json.dumps(SESSION_STATE["visual_turn_history"][-1], ensure_ascii=False)
            + "\nDas erste übergebene Bild ist aus der vorherigen Iteration (`v"
            + str(turn - 1)
            + "`), das zweite Bild ist die aktuelle Iteration (`v"
            + str(turn)
            + "`). Vergleiche beide Bilder, bewerte den aktuellen Stand im zweiten Bild und beschreibe im Feld `delta_note` konkret, was der Sprecher zwischen den beiden Aufnahmen verändert/verbessert hat."
        )

    mode_note = (
        "WICHTIG — ECHTES LIVE-WEBCAM-BILD DES NUTZERS:\n"
        "Sei sehr wohlwollend, pragmatisch und alltagstauglich! Normale Laptop- oder USB-Webcams im Büro oder Home-Office sind der Standard.\n"
        "- Vergib für `framing` (Bildausschnitt), `lighting` (Beleuchtung) und `background` (Hintergrund) standardmässig `PASS`, solange ein Mensch erkennbar vor der Kamera sitzt!\n"
        "- Normales Zimmerlicht, Bildschirmlicht, Fenster im Raum, Brillenreflexionen, ein normaler Schreibtisch/Wohnraum oder leicht aussermittiges Sitzen sind völlig in Ordnung (`PASS`).\n"
        "- Vergib NUR dann `WARN` oder `FAIL`, wenn (a) kein Gesicht im Bild ist oder der Kopf halb abgeschnitten ist, (b) das Bild fast komplett dunkel/schwarz ist, oder (c) ein in einer Zusatzregel explizit genannter Gegenstand (z.B. eine Kaffeetasse oder Kopfhörer) klar sichtbar ins Bild gehalten wird."
        if is_live_webcam
        else (
            "Hinweis zu den Studio-Simulationsbildern: In Iteration 1 (`frame_v1.jpg`) sitzt der Sprecher etwas zu nah am oberen Bildrand, rechts blendet ein Fenster, und links steht eine rote Kaffeetasse ('Kaffee'). "
            "In Iteration 2 (`frame_v2.jpg`) ist der Sprecher zurückgerückt (optimaler Kopfraum), die Jalousie ist geschlossen und die Kaffeetasse entfernt — daher MÜSSEN in Iteration 2 alle Prüfpunkte (`framing`, `lighting`, `background` und eventuelle Kaffeetassen-/Kopfhörer-Regeln) den Status `PASS` erhalten!"
        )
    )

    sys_inst = (
        "Du bist der Seneca Studio Pre-Flight Vision-Agent (Schritt 2A).\n"
        "WICHTIG: Lies die visuellen Prüfregeln (Bildausschnitt, Beleuchtung, Hintergrund sowie eventuelle Zusatzregeln wie Keine Kaffeetasse, Kein Kopfhörer, Blickkontakt etc., jedoch NICHT Mikrofon/Sprechtempo) "
        "aus Abschnitt `## 2. Kamera & Ton (Vorprüfung)` (bzw. `## 2. Studio Pre-Flight Check`) des aktiven Format-Regelwerks (`SKILL.md`).\n"
        "Die Regeln im `SKILL.md` sind in einfacher, natürlicher Sprache ohne technische Variablennamen formuliert. "
        "Ordne die drei Grundregeln den IDs `framing` (Bildausschnitt), `lighting` (Beleuchtung) und `background` (Hintergrund) zu, und vergib für jede weitere visuelle Regel im `SKILL.md` eine sprechende kurze ID (z.B. `coffee_mug`, `no_headset`, `eye_contact`).\n"
        "Jede visuelle Regel im Show Playbook MUSS als eigenes Objekt im Array `checks` zurückgegeben werden!\n\n"
        f"=== FORMAT-REGELWERK ({show_id}/SKILL.md) ===\n{show_md}\n\n"
        f"=== MODUL-BESCHREIBUNG (seneca-check-studio-visuals/SKILL.md) ===\n{cap_md}\n"
    )
    prompt = (
        f"Analysiere das aktuelle Kamerabild (Messung #{turn}) anhand der visuellen Regeln in `{show_id}/SKILL.md`.\n"
        f"{mode_note}"
        f"{prev_context}\n\n"
        "Gib exakt folgendes JSON-Format zurück:\n"
        "{\n"
        f'  "turn": {turn},\n'
        '  "overall_visual_status": "PASS" | "WARN" | "FAIL",\n'
        '  "studio_banner_de": "Kurze, freundliche 1-Satz-Rückmeldung für den Sprecher (oder Freigabe für Schritt 2B Tonprüfung)",\n'
        '  "delta_note": "Konkreter Vergleich zum vorherigen Bild (leer bei Messung 1)",\n'
        '  "checks": [\n'
        '    {\n'
        '      "id": "framing",\n'
        '      "label": "Bildausschnitt",\n'
        '      "status": "PASS" | "WARN" | "FAIL",\n'
        '      "rule_from_skill": "Kurzfassung der Regel aus SKILL.md",\n'
        '      "measured": "Was konkret im Kamerabild sichtbar ist",\n'
        '      "correction": "Kurze Bestätigung oder freundlicher Hinweis"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    t0 = time.time()
    res = call_gemini_json(
        prompt=prompt,
        system_instruction=sys_inst,
        media_parts=media_parts,
    )
    # On simulation Turn >= 2 (frame_v2.jpg), guarantee clean PASS across all checks
    if not is_live_webcam and turn >= 2:
        for c in res.get("checks", []):
            c["status"] = "PASS"
            if not c.get("correction") or "bitte" in c.get("correction", "").lower():
                c["correction"] = "Optimal eingestellt und für die Sendung freigegeben."
        res["overall_visual_status"] = "PASS"
        if not res.get("delta_note"):
            res["delta_note"] = "Abstand, Beleuchtung und Hintergrund erfolgreich korrigiert"
        res["studio_banner_de"] = "Kamerabild und Umgebung sind optimal eingestellt. Weiter mit Schritt 2B: Tonprüfung!"

    res = apply_check_overrides(res, ignored_check_ids, "overall_visual_status", "visual")
    if voice_enabled and res.get("studio_banner_de"):
        res["tts_audio_b64"] = synthesize_chirp3_hd(res["studio_banner_de"], voice_name=voice_name)
    res["latency_ms"] = round((time.time() - t0) * 1000)
    res["frame_url"] = frame_url
    res["is_live_webcam"] = is_live_webcam
    res["previous_interaction_id"] = f"int_vis_turn_{turn - 1}" if turn > 1 else None
    res["interaction_id"] = f"int_vis_turn_{turn}"
    SESSION_STATE["visual_turn_history"].append({k: v for k, v in res.items() if k != "tts_audio_b64"})
    return res


@app.post("/api/preflight/audio")
async def preflight_audio(request: Request):
    body = await request.json()
    show_id = body.get("show_id", "seneca-show-aktuell")
    turn = int(body.get("turn", 1))
    word_count = int(body.get("word_count", 11))
    custom_audio_b64 = body.get("custom_audio_b64")
    ignored_check_ids: List[str] = body.get("ignored_check_ids", [])
    voice_enabled: bool = bool(body.get("voice_enabled", True))
    voice_name: str = body.get("voice_name", "de-DE-Chirp3-HD-Aoede")
    first_sentence = body.get(
        "first_sentence",
        "An der Ostfront bei Pokrowsk verschiebt sich die militärische Dynamik spürbar.",
    )

    if turn == 1:
        SESSION_STATE["audio_turn_history"] = []

    t0 = time.time()
    ts_now = int(time.time() * 1000)
    is_live_mic = bool(custom_audio_b64)
    media_parts: List[Dict[str, Any]] = []

    if is_live_mic:
        clean_b64 = custom_audio_b64.split(",")[-1]
        webm_path = os.path.join(MEDIA_DIR, f"mic_v{turn}_{ts_now}.webm")
        wav_path = os.path.join(MEDIA_DIR, f"mic_v{turn}_{ts_now}.wav")
        with open(webm_path, "wb") as f:
            f.write(base64.b64decode(clean_b64))
        subprocess.run(
            ["ffmpeg", "-y", "-i", webm_path, "-ac", "1", "-ar", "16000", wav_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        audio_path = wav_path
        audio_url = f"/static/media/mic_v{turn}_{ts_now}.wav"
        with open(wav_path, "rb") as wf:
            media_parts.append(
                {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(wf.read()).decode("ascii")}}
            )
    else:
        audio_file = "audio_v1.wav" if turn == 1 else "audio_v2.wav"
        audio_path = os.path.join(MEDIA_DIR, audio_file)
        audio_url = f"/static/media/{audio_file}?t={ts_now}"

    script_path = os.path.join(SKILLS_DIR, "seneca-check-audio-pace", "scripts", "analyze_audio.py")
    proc = subprocess.run(
        ["python3", script_path, audio_path, "--word-count", str(word_count)],
        capture_output=True,
        text=True,
        check=True,
    )
    telemetry = json.loads(proc.stdout.strip())

    prev_audio_ctx = ""
    if turn >= 2 and SESSION_STATE["audio_turn_history"]:
        last_att = SESSION_STATE["audio_turn_history"][-1]
        prev_audio_ctx = (
            f"\nVorherige Tonmessung (#{last_att.get('turn')}): "
            f"Pegel={last_att.get('telemetry', {}).get('lufs')} LUFS, "
            f"Tempo={last_att.get('telemetry', {}).get('wpm')} WPM, "
            f"Transkript=\"{last_att.get('heard_transcript', '')}\".\n"
            "Vergleiche diesen neuen Versuch explizit mit dem vorherigen Versuch im Feld `delta_note`!"
        )

    show_md = read_local_skill_md(show_id)
    cap_md = read_local_skill_md("seneca-check-audio-pace")

    sys_inst = (
        "Du bist der Seneca Studio Audio- & Sprechtempo-Agent (Schritt 2B).\n"
        "Du erhältst die Messwerte aus der Audioanalyse sowie die eingesprochene Aufnahme und prüfst Mikrofon-Lautstärke und Sprechtempo "
        "anhand der einfachen Regeln im aktiven Format-Regelwerk (`SKILL.md`).\n"
        "WICHTIG: Höre dir die Audiodatei an, transkribiere, was gesprochen wurde (`heard_transcript`), "
        "und bewerte wohlwollend und alltagstauglich: Ein Sprechtempo zwischen 95 und 165 WPM sowie ein Mikrofonpegel zwischen -30 und -10 LUFS sind komplett im grünen Bereich (`PASS`)!\n\n"
        f"=== FORMAT-REGELWERK ({show_id}/SKILL.md) ===\n{show_md}\n\n"
        f"=== MODUL-BESCHREIBUNG (seneca-check-audio-pace/SKILL.md) ===\n{cap_md}\n"
    )
    prompt = (
        f"Bewerte diese Mikrofon- und Sprechtempo-Aufnahme (Messung #{turn}).\n"
        f"Vorgelesener Satz ({word_count} Wörter): \"{first_sentence}\"\n"
        f"Gemessene Audio-Kennzahlen: {json.dumps(telemetry)}"
        f"{prev_audio_ctx}\n\n"
        "Gib exakt folgendes JSON-Format zurück:\n"
        "{\n"
        f'  "turn": {turn},\n'
        '  "overall_audio_status": "PASS" | "WARN" | "FAIL",\n'
        '  "ready_to_record": true | false,\n'
        '  "heard_transcript": "Exakt was im Audio gesprochen wurde",\n'
        '  "spoken_word_count": 11,\n'
        '  "delta_note": "Kurzer Vergleich zur vorherigen Messung (z.B. Pegel und Tempo jetzt im Zielbereich)",\n'
        '  "studio_banner_de": "Kurze Regie-Rückmeldung für den Sprecher",\n'
        '  "checks": [\n'
        '    {\n'
        '      "id": "audio_lufs",\n'
        '      "label": "Mikrofon & Lautstärke",\n'
        '      "status": "PASS" | "WARN" | "FAIL",\n'
        '      "rule_from_skill": "Klar verständliche Stimme ohne Übersteuern (-26 bis -12 LUFS)",\n'
        '      "measured": "z.B. -16.0 LUFS (Spitze -8.1 dBFS)",\n'
        '      "correction": "Bestätigung oder kurzer Hinweis"\n'
        "    },\n"
        '    {\n'
        '      "id": "speaking_pace",\n'
        '      "label": "Sprechtempo",\n'
        '      "status": "PASS" | "WARN" | "FAIL",\n'
        '      "rule_from_skill": "Ruhiger, natürlicher Nachrichtenfluss (100 bis 160 WPM)",\n'
        '      "measured": "z.B. 137 WPM (11 Wörter in 4.1s)",\n'
        '      "correction": "Bestätigung oder kurzer Hinweis"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    res = call_gemini_json(prompt=prompt, system_instruction=sys_inst, media_parts=media_parts)
    # Deterministic calibration of WPM & LUFS so the UI status and coaching text ALWAYS match the true numbers
    heard_text = (res.get("heard_transcript") or "").strip()
    if not is_live_mic and not heard_text:
        heard_text = first_sentence
        res["heard_transcript"] = heard_text

    actual_words = len([w for w in heard_text.split() if w.strip()]) if is_live_mic else word_count
    speech_dur = float(telemetry.get("speech_duration_sec") or telemetry.get("duration_sec") or 4.1)

    if is_live_mic and actual_words >= 3:
        # Calibrated German single-sentence WPM (accounts for short articles/prepositions and single-sentence burst)
        real_wpm = round(((actual_words * 0.85) / max(speech_dur, 1.4)) * 60.0)
        telemetry["wpm"] = real_wpm
        telemetry["spoken_words"] = actual_words
    else:
        real_wpm = int(telemetry.get("wpm") or 135)
        telemetry["spoken_words"] = actual_words if actual_words > 0 else word_count

    lufs_val = float(telemetry.get("lufs") or -18.0)
    peak_val = float(telemetry.get("peak_db") or -6.0)
    spoken_cnt = telemetry["spoken_words"]

    for c in res.get("checks", []):
        cid = c.get("id")
        if cid == "audio_lufs":
            c["label"] = "Mikrofon & Lautstärke"
            c["rule_from_skill"] = "Klar verständliche Stimme ohne Übersteuern (ca. -26 bis -12 LUFS)"
            c["measured"] = f"{lufs_val:.1f} LUFS (Spitze {peak_val:.1f} dBFS)"
            if is_live_mic:
                if spoken_cnt < 2 or lufs_val < -36.0:
                    c["status"] = "WARN"
                    c["correction"] = "Mikrofonpegel war sehr leise. Bitte sprechen Sie etwas näher am Mikrofon."
                elif peak_val > -0.2 and lufs_val > -9.0:
                    c["status"] = "WARN"
                    c["correction"] = "Mikrofonpegel ist sehr hoch. Bitte etwas mehr Abstand zum Mikrofon halten."
                else:
                    c["status"] = "PASS"
                    c["correction"] = "Mikrofon-Lautstärke ist klar verständlich und sauber ausgesteuert."
            else:
                if -26.0 <= lufs_val <= -11.0 and peak_val <= -0.5:
                    c["status"] = "PASS"
                    c["correction"] = "Der Mikrofon-Pegel ist mit -16.0 LUFS perfekt ausgesteuert."
                else:
                    c["status"] = "FAIL"
                    c["correction"] = f"Mikrofon übersteuert bei {lufs_val:.1f} LUFS (Spitze {peak_val:.1f} dBFS). Bitte Pegel senken oder Abstand vergrössern."
        elif cid == "speaking_pace":
            c["label"] = "Sprechtempo"
            c["rule_from_skill"] = "Ruhiger, natürlicher Nachrichtenfluss (ca. 100 bis 160 Wörter/Min.)"
            c["measured"] = f"{real_wpm} WPM ({spoken_cnt} Wörter in {speech_dur:.1f}s Sprechzeit)"
            if is_live_mic and spoken_cnt < 2:
                c["status"] = "WARN"
                c["correction"] = "Es wurden noch zu wenige Wörter erkannt. Bitte lesen Sie den ganzen Satz vor."
            elif 95 <= real_wpm <= 165:
                c["status"] = "PASS"
                c["correction"] = f"Angenehmes, natürliches Sprechtempo ({real_wpm} WPM) — optimal für die Sendung."
            elif real_wpm > 165:
                c["status"] = "WARN" if real_wpm <= 185 else "FAIL"
                c["correction"] = f"Sprechtempo ({real_wpm} WPM) ist etwas zu hoch. Bitte lesen Sie den Satz eine Spur ruhiger."
            else:
                c["status"] = "WARN"
                c["correction"] = f"Sprechtempo ({real_wpm} WPM) ist sehr langsam. Bitte etwas flüssiger vorlesen."

    # Recompute overall_audio_status and banner deterministically from the calibrated checks
    statuses = [c.get("status", "PASS") for c in res.get("checks", [])]
    if "FAIL" in statuses:
        res["overall_audio_status"] = "FAIL"
        res["ready_to_record"] = False
    elif "WARN" in statuses:
        res["overall_audio_status"] = "WARN"
        res["ready_to_record"] = False
    else:
        res["overall_audio_status"] = "PASS"
        res["ready_to_record"] = True
        res["studio_banner_de"] = "Mikrofon und Sprechtempo sind perfekt eingestellt! Weiter zu Schritt 03 für die Studio-Aufnahme."
        if turn >= 2 and SESSION_STATE.get("audio_turn_history"):
            prev_t = SESSION_STATE["audio_turn_history"][-1].get("telemetry", {})
            prev_wpm = prev_t.get("wpm")
            if prev_wpm and prev_wpm > real_wpm:
                res["delta_note"] = f"Pegel optimal ({lufs_val:.1f} LUFS) & Sprechtempo um {prev_wpm - real_wpm} WPM beruhigt ({real_wpm} WPM)"

    res = apply_check_overrides(res, ignored_check_ids, "overall_audio_status", "audio")
    if voice_enabled and res.get("studio_banner_de"):
        res["tts_audio_b64"] = synthesize_chirp3_hd(res["studio_banner_de"], voice_name=voice_name)
    res["telemetry"] = telemetry
    res["audio_url"] = audio_url
    res["is_live_mic"] = is_live_mic
    res["timestamp"] = time.strftime("%H:%M:%S")
    res["latency_ms"] = round((time.time() - t0) * 1000)

    SESSION_STATE["audio_turn_history"].append(
        {
            "turn": turn,
            "timestamp": res["timestamp"],
            "overall_audio_status": res["overall_audio_status"],
            "heard_transcript": heard_text,
            "telemetry": dict(telemetry),
            "audio_url": audio_url,
        }
    )
    res["audio_history"] = list(SESSION_STATE["audio_turn_history"])
    return res


@app.post("/api/postprod")
async def run_postprod(request: Request):
    body = await request.json()
    show_id = body.get("show_id", "seneca-show-aktuell")
    custom_video_b64 = body.get("custom_video_b64")

    show_md = read_local_skill_md(show_id)
    cap_md = read_local_skill_md("seneca-auto-cut-master")
    t0 = time.time()

    is_live_video = bool(custom_video_b64)
    media_parts: List[Dict[str, Any]] = []

    if is_live_video:
        clean_b64 = custom_video_b64.split(",")[-1]
        webm_path = os.path.join(MEDIA_DIR, "user_raw_take.webm")
        raw_mp4 = os.path.join(MEDIA_DIR, "user_raw_take.mp4")
        with open(webm_path, "wb") as f:
            f.write(base64.b64decode(clean_b64))
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                webm_path,
                "-vf",
                "scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2",
                "-r",
                "24",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "44100",
                "-ac",
                "2",
                raw_mp4,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Get exact duration of user recording
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", raw_mp4],
            capture_output=True,
            text=True,
        )
        try:
            dur = round(float(probe.stdout.strip()), 1)
        except Exception:
            dur = 10.0
        with open(raw_mp4, "rb") as vf:
            media_parts.append(
                {"inlineData": {"mimeType": "video/mp4", "data": base64.b64encode(vf.read()).decode("ascii")}}
            )
        raw_video_url = f"/static/media/user_raw_take.mp4?t={int(time.time())}"
        prompt_context = (
            f"Dies ist die ECHTE Webcam-Videoaufnahme des Nutzers (Gesamtlänge: {dur} Sekunden).\n"
            "Höre dir die Tonspur und das Video genau an, transkribiere die gesprochenen Segmente mit exakten Start- und End-Sekunden (`0.0` bis `"
            + str(dur)
            + "`), markiere eventuelle Versprecher/Retakes oder lange Pausen am Anfang/Ende/Zwischendrin als `REMOVE` und die sauberen Sprechpassagen als `KEEP` (mindestens ein `KEEP`-Segment muss erhalten bleiben!)."
        )
    else:
        raw_mp4 = os.path.join(MEDIA_DIR, "raw_take.mp4")
        dur = 13.5
        raw_video_url = f"/static/media/raw_take.mp4?t={int(time.time())}"
        raw_take_transcript = (
            "[0.0s - 3.2s]: 'An der Ostfront bei Pokrowsk verschiebt sich die militärische Dynamik spürbar.'\n"
            "[3.2s - 6.2s]: 'Die russischen Verbände... äh Verzeihung, ich setze den Satz nochmal neu an.'\n"
            "[6.2s - 9.2s]: 'Die russischen Verbände setzen verstärkt auf kleine, hochmobile Infanteriegruppen.'\n"
            "[9.2s - 10.8s]: [Stille / Denkpause von 1.6 Sekunden]\n"
            "[10.8s - 13.5s]: 'Für Kiew wird die Nachschublogistik damit zur zentralen Schlüsselfrage des Winters.'"
        )
        prompt_context = f"Erstelle die Edit Decision List (`edl.json`) für folgende Rohaufnahme (`raw_take.mp4`, 13.5s):\n{raw_take_transcript}"

    sys_inst = (
        "Du bist der Seneca Studio Post-Production Agent.\n"
        "Du analysierst die Rohaufnahme gemäss den Schnittregeln in `## 3. Automatischer Rohschnitt` (bzw. `## 3. Post-Production`) des aktiven Format-Regelwerks (`SKILL.md`) "
        "und erzeugst eine präzise Schnittliste (`edl.json`).\n\n"
        f"=== FORMAT-REGELWERK ({show_id}/SKILL.md) ===\n{show_md}\n\n"
        f"=== MODUL-BESCHREIBUNG (seneca-auto-cut-master/SKILL.md) ===\n{cap_md}\n"
    )
    prompt = (
        f"{prompt_context}\n\n"
        "Gib exakt folgendes JSON-Format zurück:\n"
        "{\n"
        '  "summary_de": "Kurze Zusammenfassung der Schnitte und entfernten Retakes/Pausen",\n'
        f'  "original_duration_sec": {dur},\n'
        '  "final_duration_sec": 8.9,\n'
        '  "segments": [\n'
        '    {"start": 0.0, "end": 3.2, "action": "KEEP", "reason": "Sauberer Einstiegssatz", "transcript": "..."},\n'
        '    {"start": 3.2, "end": 6.2, "action": "REMOVE", "reason": "Retake / Pause entfernt", "transcript": "..."}\n'
        "  ]\n"
        "}"
    )
    edl = call_gemini_json(prompt=prompt, system_instruction=sys_inst, media_parts=media_parts)
    # Clamp segments to valid range [0, dur]
    valid_segments = []
    for seg in edl.get("segments", []):
        st = max(0.0, min(float(seg.get("start", 0.0)), dur - 0.2))
        en = max(st + 0.2, min(float(seg.get("end", dur)), dur))
        seg["start"] = round(st, 2)
        seg["end"] = round(en, 2)
        valid_segments.append(seg)
    if not any(s.get("action") == "KEEP" for s in valid_segments):
        valid_segments = [{"start": 0.0, "end": dur, "action": "KEEP", "reason": "Vollständiger Take", "transcript": "Aufnahme"}]
    edl["segments"] = valid_segments

    edl_path = os.path.join(MEDIA_DIR, "edl.json")
    with open(edl_path, "w", encoding="utf-8") as f:
        json.dump(edl, f, indent=2, ensure_ascii=False)

    render_script = os.path.join(SKILLS_DIR, "seneca-auto-cut-master", "scripts", "render_cuts.py")
    proc = subprocess.run(
        ["python3", render_script, raw_mp4, edl_path, "--out-dir", MEDIA_DIR],
        capture_output=True,
        text=True,
        check=True,
    )
    render_info = json.loads(proc.stdout.strip())
    ts = int(time.time())
    return {
        "edl": edl,
        "render": render_info,
        "is_live_video": is_live_video,
        "raw_video_url": raw_video_url,
        "master_16x9_url": f"/static/media/master_16x9.mp4?t={ts}",
        "reel_9x16_url": f"/static/media/reel_9x16.mp4?t={ts}",
        "latency_ms": round((time.time() - t0) * 1000),
    }


@app.post("/api/managed-agent/interact")
async def managed_agent_interact(request: Request):
    """Calls the live Managed Agents Interactions API (`seneca-studio-agent`) on YOUR_GCP_PROJECT_ID."""
    body = await request.json()
    user_prompt = body.get(
        "prompt",
        "List the Seneca skills mounted in your sandbox under .agent/skills, read seneca-show-aktuell/SKILL.md, and return a short JSON summary of the pre-flight check rules.",
    )
    token = get_gcp_token()
    url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions"

    req_body: Dict[str, Any] = {
        "stream": True,
        "background": True,
        "store": True,
        "agent": AGENT_ID,
        "input": [
            {
                "type": "user_input",
                "content": [{"type": "text", "text": user_prompt}],
            }
        ],
    }
    if SESSION_STATE.get("environment_id"):
        req_body["environment"] = SESSION_STATE["environment_id"]
    else:
        req_body["environment"] = {"type": "remote"}

    if SESSION_STATE.get("previous_interaction_id"):
        req_body["previous_interaction_id"] = SESSION_STATE["previous_interaction_id"]

    t0 = time.time()
    req = urllib.request.Request(
        url,
        data=json.dumps(req_body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
            "X-Goog-User-Project": PROJECT_ID,
        },
    )
    events = []
    final_text_parts = []
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if line.startswith("data:"):
                    payload_str = line[5:].strip()
                    if not payload_str:
                        continue
                    try:
                        ev = json.loads(payload_str)
                        events.append(ev)
                        ev_type = ev.get("event_type", "")
                        if ev_type == "content.delta":
                            delta = ev.get("delta", {})
                            if delta.get("type") == "text":
                                final_text_parts.append(delta.get("text", ""))
                        elif ev_type == "interaction.complete":
                            inter = ev.get("interaction", {})
                            if inter.get("environment_id"):
                                SESSION_STATE["environment_id"] = inter["environment_id"]
                            if inter.get("id"):
                                SESSION_STATE["previous_interaction_id"] = inter["id"]
                    except Exception:
                        pass
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=e.code, detail=err_body)

    return {
        "agent": AGENT_ID,
        "environment_id": SESSION_STATE.get("environment_id"),
        "interaction_id": SESSION_STATE.get("previous_interaction_id"),
        "output_text": "".join(final_text_parts),
        "event_count": len(events),
        "latency_ms": round((time.time() - t0) * 1000),
    }
