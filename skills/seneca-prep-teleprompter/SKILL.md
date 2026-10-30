---
name: seneca-prep-teleprompter
description: Converts an Seneca article draft into spoken-word teleprompter segments according to the active Show Playbook.
---

# Capability Skill: Teleprompter Script Formatter

1. Read `## 1. Script Preparation` from the active Show Playbook (`SKILL.md`).
2. Transform the input article/notes into 3-4 concise spoken teleprompter blocks (`segments[]`).
3. Mark key stressed words in uppercase or `[BETONUNG]` and insert `[PAUSE 0.5s]` cues between thoughts.
4. Return JSON with `first_sentence_plain` (used for the Loop B spoken audio pre-flight check), `total_words`, `estimated_duration_sec`, and `segments[]`.
