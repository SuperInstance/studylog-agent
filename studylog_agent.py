#!/usr/bin/env python3
"""
studylog_agent.py — PLATO Study Partner Agent

Tracks student/researcher learning progression. Every lesson is logged to PLATO
as a tile. Later agents can "don the shell" and continue from prior sessions.
Self-improving curriculum via agent learning from past sessions.

Usage:
    python3 studylog_agent.py                    # Interactive study session
    python3 studylog_agent.py --resume          # Don the shell, resume last session
    python3 studylog_agent.py --history         # Show study history
    python3 studylog_agent.py --suggest         # Suggest next lesson
    python3 studylog_agent.py --stats           # Show concept mastery stats
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.parse
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
        """Log a study session to PLATO."""
        tile = {
            "domain": ROOM,
            "question": f"What was covered studying '{topic}'?",
            "answer": self._build_answer(topic, concepts, questions, understanding, notes, next_steps, resources),
            "agent": f"studylog-agent:{self.student_id}",
        }
        # Extended metadata stored in answer field for now
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

        # Get last session
        last = sessions[-1]
        # Get concepts from all sessions
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
        # Find least-covered concepts as suggestions
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


# === CLI ===

def interactive_session(agent: StudyLogAgent) -> None:
    print("=== PLATO Study Partner ===")
    print(f"Room: {ROOM}")
    print()

    topic = input("Topic: ").strip()
    concepts_raw = input("Concepts covered (comma-separated): ").strip()
    concepts = [c.strip() for c in concepts_raw.split(",") if c.strip()]

    questions_raw = input("Questions asked (comma-separated): ").strip()
    questions = [q.strip() for q in questions_raw.split(",") if q.strip()]

    print("Understanding level (novice/apprentice/journeyman/master): ", end="")
    understanding = input().strip() or "novice"

    notes = input("Session notes: ").strip()

    next_steps_raw = input("Next steps (comma-separated): ").strip()
    next_steps = [n.strip() for n in next_steps_raw.split(",") if n.strip()]

    resources_raw = input("Resources used (comma-separated): ").strip()
    resources = [r.strip() for r in resources_raw.split(",") if r.strip()]

    print()
    result = agent.submit_session(topic, concepts, questions, understanding, notes, next_steps, resources)
    print(f"Logged. Tile: {result.get('tile_hash', '?')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PLATO Study Partner Agent")
    parser.add_argument("--student", default="default", help="Student ID")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--resume", action="store_true", help="Don the shell — resume last session")
    parser.add_argument("--history", action="store_true", help="Show study history")
    parser.add_argument("--suggest", action="store_true", help="Suggest next lesson")
    parser.add_argument("--stats", action="store_true", help="Show concept mastery stats")
    args = parser.parse_args()

    agent = StudyLogAgent(student_id=args.student, verbose=args.verbose)

    if args.resume:
        result = agent.don_the_shell()
        print(json.dumps(result, indent=2, default=str))
    elif args.history:
        history = agent.show_history()
        for i, h in enumerate(history):
            ts = datetime.fromtimestamp(h["timestamp"], tz=timezone.utc).isoformat()
            print(f"[{i+1}] {ts} — {h['topic']}")
    elif args.suggest:
        sessions = agent.get_all_sessions()
        concept_map = agent._build_concept_map(sessions)
        suggestion = agent._suggest_next(concept_map)
        print(suggestion)
    elif args.stats:
        stats = agent.show_stats()
        print(json.dumps(stats, indent=2, default=str))
    else:
        interactive_session(agent)


if __name__ == "__main__":
    main()
