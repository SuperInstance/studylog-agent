# studylog-agent

**PLATO Study Partner Agent** — Research Study Partner for studylog.ai

Tracks student/researcher learning progression. Every lesson is logged to PLATO as a tile. Later agents can "don the shell" and continue from prior sessions seamlessly. Self-improving curriculum via agent learning from past sessions.

## Overview

The studylog-agent is an agent that:
- **Logs every study session** to PLATO as a tile (like git commits)
- **Presents material** through PLATO rooms, tracking progress
- **Don the Shell**: later agents load past session context to continue curriculum
- **Self-improving**: curriculum knowledge accumulates in the PLATO vessel

## Architecture

- **PLATO room**: `studylog-ai`
- **Each study session** → PLATO tile with:
  - Topic studied
  - Concepts covered
  - Questions asked
  - Understanding level (novice → apprentice → journeyman → master)
  - Session notes
  - Next steps
  - Resources used
- **Vessel**: curriculum knowledge accumulates over time

## Quick Start

```bash
# Log a study session
python3 studylog_agent.py

# Don the shell — resume where you left off
python3 studylog_agent.py --resume

# Show study history
python3 studylog_agent.py --history

# Suggest next lesson
python3 studylog_agent.py --suggest

# Show concept mastery stats
python3 studylog_agent.py --stats
```

## Tile Schema

Each PLATO tile captures a complete study session:

| Field | Type | Description |
|-------|------|-------------|
| topic | string | What was studied |
| concepts_covered | list[string] | Concepts learned this session |
| questions_asked | list[string] | Student questions during session |
| understanding_level | string | novice/apprentice/journeyman/master |
| session_notes | string | Agent observations |
| next_steps | list[string] | Recommended follow-up topics |
| resources_used | list[string] | Books, papers, tools referenced |

## Don the Shell

When a student returns, the agent:
1. Reads prior lesson tiles from `studylog-ai` room
2. Identifies where they left off (last topic, concepts, questions)
3. Resumes curriculum from that exact point

This is analogous to a sailor checking the ship's log before taking the helm.

## PLATO API

The agent communicates with the PLATO Room Server at `http://localhost:8847`:

```python
from studylog_agent import StudyLogAgent

agent = StudyLogAgent(student_id="alice")

# Log a session
agent.submit_session(
    topic="Constraint Theory",
    concepts=["hard constraints", "soft constraints", "penalty methods"],
    questions=["How do I express an OR relation as a constraint?", "What's the complexity of CSP?"],
    understanding="apprentice",
    notes="Struggled with penalty method formulation but got it after examples.",
    next_steps=["Lagrange multipliers", "Dual decomposition"],
    resources=["Dechter - Constraint Processing", "tscrump YouTube"],
)

# Resume
ctx = agent.don_the_shell()
print(ctx["next_suggestion"])
```

## Files

```
studylog-agent/
├── studylog_agent.py     # Main agent
├── README.md             # This file
└── LICENSE               # MIT
```

## License

MIT

## Fleet Context

This agent is part of the **Cocapn Fleet** — a system of domain-specific PLATO agents that track, learn, and persist knowledge across sessions. Each agent writes to its own PLATO room, creating a distributed knowledge graph that grows over time.

## Links

- Live site: https://studylog.ai
- Fleet: https://cocapn.com
- PLATO: https://github.com/SuperInstance/plato

## Related

- [studylog.ai](https://studylog.ai) — Live site
- [studylog-ai-pages](https://github.com/SuperInstance/studylog-ai-pages) — GitHub Pages source
