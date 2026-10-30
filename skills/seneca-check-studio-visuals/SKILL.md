---
name: seneca-check-studio-visuals
description: Evaluates a studio snapshot frame (frame_vN.jpg) against the visual rules in the active Show Playbook skill.
---

# Capability Skill: Studio Visuals & Framing QA (Loop A)

1. Read every visual check bullet under `## 2. Studio Pre-Flight Check` of the active Show Playbook (`SKILL.md`).
2. Inspect the current camera snapshot (`frame_vN.jpg`). If a previous snapshot (`frame_vN-1.jpg`) or previous check result is provided in context, explicitly note the improvement delta (e.g., "Abstand verbessert (+15 cm)").
3. Return a JSON object with `overall_visual_status` (`PASS` | `WARN` | `FAIL`) and a `checks` array where each item has:
   - `id`: rule identifier (e.g., `framing`, `lighting`, `background`, plus any custom rule added to the Show Playbook)
   - `label`: short German badge title
   - `status`: `PASS`, `WARN`, or `FAIL`
   - `measured`: concise observation (e.g., "Augenlinie bei 31%, Kopfraum 12%")
   - `correction`: actionable 1-sentence German instruction for the presenter sitting 2m from the camera.
