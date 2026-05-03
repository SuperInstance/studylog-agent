"""
studylog_agent — PLATO Study Partner Agent

Tracks student/researcher learning progression. Every lesson is logged to PLATO
as a tile. Later agents can "don the shell" and continue from prior sessions.
Self-improving curriculum via agent learning from past sessions.

Usage:
    python -m studylog_agent                    # Interactive study session
    python -m studylog_agent --resume           # Don the shell, resume last session
    python -m studylog_agent --history          # Show study history
    python -m studylog_agent --suggest          # Suggest next lesson
    python -m studylog_agent --stats            # Show concept mastery stats

Install:
    pip install studylog-agent
    studylog --help
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

PLATO_URL = "http://localhost:8847"
ROOM = "studylog-ai"


class StudyLogAgent:
    """PLATO Study Partner Agent."""

    def __init__(self, student_id: str = "default", verbose: bool = True):
        self.student_id = student_id
        self.verbose = verbose
        self.session_tiles = []

    # === PLATO Communication ===

    def _get(self, path: str) -> dict:
        req = urllib.request.Request(f"{PLATO_URL}{path}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def _post(self, path: str, data: dict) -> dict:
        body = json.dumps(data, default=str).encode()
        req = urllib.request.Request(f"{PLATO_URL}{path}", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def log(self, msg: str) -> None:
        if self.verbose:
            print(f"[studylog] {msg}")

    # === PLATO Operations ===

    def get_all_sessions(self) -> list[dict]:
        """Fetch all study sessions from PLATO."""
        try:
            room = self._get(f"/rooms/{ROOM}")
            return room.get("tiles", [])
        except Exception as e:
            self.log(f"Could not fetch sessions: {e}")
            return []

    def submit_session(
        self,
        topic: str,
        concepts: list[str],
        questions: list[str],
        understanding: str,
        notes: str,
        next_steps: list[str],
        resources: list[str],
    ) -> dict:
        """Log a study session to PLATO as a tile."""
        tile = {
            "domain": ROOM,
            "question": f"What was covered studying '{topic}'?",
            "answer": self._build_answer(topic, concepts, questions, understanding, notes, next_steps, resources),
            "agent": f"studylog-agent:{self.student_id}",
        }
        result = self._post("/submit", tile)
        self.log(f"Session logged: {result.get('status')}")
        return result

    def _build_answer(
        self, topic, concepts, questions, understanding, notes, next_steps, resources
    ) -> str:
        parts = [
            f"Topic: {topic}",
            f"Concepts covered: {', '.join(concepts)}",
            f"Questions asked: {', '.join(questions)}",
            f"Understanding level: {understanding}",
            f"Session notes: {notes}",
            f"Next steps: {', '.join(next_steps)}",
            f"Resources used: {', '.join(resources)}",
        ]
        return " | ".join(parts)

    # === Shell / Resume ===

    def don_the_shell(self) -> dict:
        """Load past session context to continue curriculum."""
        sessions = self.get_all_sessions()
        if not sessions:
            return {"status": "no_history", "message": "No prior sessions found."}

        last = sessions[-1]
        concept_map = self._build_concept_map(sessions)

        return {
            "status": "resumed",
            "last_topic": self._extract_topic(last),
            "last_session": last,
            "concept_mastery": concept_map,
            "session_count": len(sessions),
            "next_suggestion": self._suggest_next(concept_map),
        }

    def _extract_topic(self, tile: dict) -> str:
        q = tile.get("question", "")
        if "studying '" in q:
            return q.split("studying '")[1].split("'")[0]
        return "unknown"

    def _build_concept_map(self, sessions: list[dict]) -> dict[str, int]:
        """Parse all sessions to build concept mastery counts."""
        mastery = {}
        for tile in sessions:
            ans = tile.get("answer", "")
            if "Concepts covered:" in ans:
                start = ans.index("Concepts covered:") + len("Concepts covered:")
                end = ans.index("Questions asked:") if "Questions asked:" in ans else len(ans)
                concepts_str = ans[start:end].strip().rstrip("|").strip()
                for c in concepts_str.split(","):
                    c = c.strip()
                    if c:
                        mastery[c] = mastery.get(c, 0) + 1
        return mastery

    def _suggest_next(self, concept_map: dict[str, int]) -> str:
        """Suggest next topic based on concept coverage."""
        if not concept_map:
            return "Start with any topic. The curriculum is yours to define."
        sorted_concepts = sorted(concept_map.items(), key=lambda x: x[1])
        suggestions = [c for c, _ in sorted_concepts[:3]]
        return f"Consider exploring: {', '.join(suggestions)}"

    # === History ===

    def show_history(self) -> list[dict]:
        """Show all prior study sessions."""
        sessions = self.get_all_sessions()
        history = []
        for tile in sessions:
            history.append({
                "topic": self._extract_topic(tile),
                "question": tile.get("question", ""),
                "answer": tile.get("answer", ""),
                "timestamp": tile.get("provenance", {}).get("timestamp", 0),
            })
        return history

    # === Stats ===

    def show_stats(self) -> dict:
        """Show concept mastery statistics."""
        sessions = self.get_all_sessions()
        concept_map = self._build_concept_map(sessions)
        total_sessions = len(sessions)
        unique_concepts = len(concept_map)
        total_concepts = sum(concept_map.values())
        mastery_levels = {}
        for tile in sessions:
            ans = tile.get("answer", "")
            if "Understanding level:" in ans:
                start = ans.index("Understanding level:") + len("Understanding level:")
                end = ans.index("Session notes:") if "Session notes:" in ans else len(ans)
                level = ans[start:end].strip().rstrip("|").strip()
                mastery_levels[level] = mastery_levels.get(level, 0) + 1
        return {
            "total_sessions": total_sessions,
            "unique_concepts": unique_concepts,
            "total_concept_mentions": total_concepts,
            "concept_mastery": concept_map,
            "understanding_distribution": mastery_levels,
        }