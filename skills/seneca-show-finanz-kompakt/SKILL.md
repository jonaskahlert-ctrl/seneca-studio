---
name: seneca-seneca-show-finanz-kompakt
description: Declarative production playbook for Seneca Finanz Kompakt (60s 9:16 vertical social briefing).
---

# Show Playbook: Seneca Finanz Kompakt (60s Social Reel)

## 1. Script Preparation (`phase: script`)
- **Tonfall**: Dynamisch, auf den Punkt, max. 130 Wörter Gesamtlänge (60 Sekunden).
- **Hook**: Erster Satz muss die wichtigste Marktbewegung in unter 4 Sekunden nennen.

## 2. Studio Pre-Flight Check (`phase: preflight`)
- **framing (Vertikaler 9:16 Safe-Zone Check)**: Sprecher strikt im mittleren 9:16-Korridor zentriert (mind. 25% Platz links/rechts für Hochformat-Beschnitt).
- **lighting (Studio-Licht)**: Helle, kontrastreiche Ausleuchtung ohne Schattenwurf.
- **background (Börsen-/Newsroom-Hintergrund)**: Ruhiger Newsroom-Hintergrund ohne lesbare fremde Bildschirme.
- **audio_lufs (Mikrofon-Pegel)**: Zielwert -14.0 LUFS (lauter gemastert für Mobile Feeds, Toleranz -16.0 bis -12.5 LUFS).
- **speaking_pace (Sprechgeschwindigkeit)**: Dynamischer Korridor 135 bis 155 WPM.

## 3. Post-Production (`phase: postprod`)
- **Schnittrhythmus**: Alle Pausen über 0.4 Sekunden entfernen (Jump-Cut-Stil für Mobile).
- **Ausgabeformate**: Primär `reel_9x16.mp4` mit eingebrannten Untertiteln.
