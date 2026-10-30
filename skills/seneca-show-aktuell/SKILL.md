---
name: seneca-show-aktuell
description: Declarative production playbook for Studio Analyse (Ukraine & Geopolitics video commentary, 3-5 min).
---

# Show Playbook: Studio Analyse (Geopolitik-Briefing)

## 1. Script Preparation (`phase: script`)
Use `seneca-prep-teleprompter` with these format rules:
- **Tonfall**: Analytisch, ruhig, präzise Seneca-Sprache; kurze Hauptsätze für freies Sprechen.
- **Ziel-Sprechtempo**: 130 Wörter pro Minute (max. 140 WPM).
- **Marker**: Setze `[BETONUNG]` bei Schlüsselbegriffen und `[PAUSE 0.5s]` bei Themenwechseln.

## 2. Studio Pre-Flight Check (`phase: preflight`)
Run `seneca-check-studio-visuals` (Loop A) and `seneca-check-audio-pace` (Loop B) against these show thresholds:
- **framing (Kameradistanz & Bildausschnitt)**: Sprecher mittig zentriert, Augenlinie im oberen Drittel (ca. 30% vom oberen Rand), Schultern vollständig sichtbar, mind. 10% Kopfraum.
- **lighting (Beleuchtung & Kontrast)**: Gleichmässige Gesichtsausleuchtung von vorn; kein hartes Gegenlicht durch Fenster im Hintergrund; keine starken Reflexionen in der Brille.
- **background (Hintergrund & Studio-Ordnung)**: Aufgeräumter Redaktions- oder Karten-Hintergrund; keine störenden Gegenstände im Bild.
- **audio_lufs (Mikrofon-Pegel & Raumklang)**: Zielwert -16.0 LUFS (Toleranz -18.0 bis -14.0 LUFS), Spitzenpegel unter -1.5 dBTP, kein Übersteuern (Clipping).
- **speaking_pace (Sprechgeschwindigkeit)**: Zielkorridor 115 bis 140 Wörter pro Minute (WPM) beim Vorlesen des ersten Skriptsatzes.

## 3. Post-Production (`phase: postprod`)
Run `seneca-auto-cut-master`:
- **Retake-Erkennung**: Wenn der Sprecher sich verspricht oder einen Satz neu ansetzt, behalte ausschliesslich den letzten sauberen Take.
- **Pausen-Glättung**: Kürze Sprechpausen über 0.8 Sekunden automatisch auf natürliche 0.25 Sekunden.
- **Ausgabeformate**: Rendere `master_16x9.mp4` (Seneca Web Player) und `reel_9x16.mp4` (Social Vertical mit Seneca Bauchbinde).
