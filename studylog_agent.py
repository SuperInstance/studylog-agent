#!/usr/bin/env python3
"""
studylog_agent.py — PLATO Study Partner Agent for studylog.ai
============================================================
Logs study sessions to PLATO as tiles. Uses fleet_agent base class.
"""

import argparse
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from fleet_agent import BaseAgent

PLATO_URL = "http://localhost:8847"
ROOM = "studylog-ai"


class StudyLogAgent(BaseAgent):
    """PLATO Study Partner Agent.
    
    Tracks student/researcher learning progression. Every lesson is logged
    to PLATO as a tile. Later agents can "don the shell" and continue.
    """

    STUDYLOG_ROOM = "studylog-ai"
    
    def __init__(self, student_id: str = "default", verbose: bool = True):
        super().__init__(agent_name=f"study-{student_id}")
        self.student_id = student_id
        self.verbose = verbose
        self.room = self.STUDYLOG_ROOM
        self.session_tiles = []

    # === PLATO Operations (override base class methods) ===

    def get_all_sessions(self) -> list[dict]:
        """Fetch all study sessions from PLATO."""
        try:
            response = self.get_tiles(limit=500)
            return response.get("tiles", [])
        except Exception:
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
            "domain": self.room,
            "agent": self.agent_name,
            "type": "study_session",
            "question": f"What was covered studying '{topic}'?",
            "answer": f"Topic: {topic} | Concepts: {', '.join(concepts)} | Questions: {', '.join(questions)} | Level: {understanding} | Notes: {notes} | Next: {', '.join(next_steps)} | Resources: {', '.join(resources)}",
            "content": {
                "topic": topic,
                "concepts": concepts,
                "questions": questions,
                "understanding": understanding,
                "notes": notes,
                "next_steps": next_steps,
                "resources": resources,
            }
        }
        return self.post_tile(tile)

    def don_the_shell(self) -> dict:
        """Don the shell — resume from previous sessions."""
        sessions = self.get_all_sessions()
        if not sessions:
            return {"status": "no_history"}
        last_session = sessions[-1]
        last_topic = self._extract_topic(last_session)
        return {
            "status": "resumed",
            "last_topic": last_topic,
            "sessions_count": len(sessions)
        }

    def show_history(self, limit: int = 20) -> list:
        """Show study history."""
        sessions = self.get_all_sessions()[:limit]
        history = []
        for tile in sessions:
            history.append({
                "topic": self._extract_topic(tile),
                "question": tile.get("question", ""),
                "answer": tile.get("answer", ""),
                "timestamp": tile.get("provenance", {}).get("timestamp", 0),
            })
        return history

    def show_stats(self) -> dict:
        """Show concept mastery statistics."""
        sessions = self.get_all_sessions()
        concept_map = self._build_concept_map(sessions)
        total_sessions = len(sessions)
        unique_concepts = len(concept_map)
        mastery_levels = {}
        for tile in sessions:
            ans = tile.get("answer", "")
            if "Level:" in ans:
                start = ans.index("Level:") + len("Level:")
                end = ans.index("Notes:") if "Notes:" in ans else len(ans)
                level = ans[start:end].strip().split("|")[0].strip()
                mastery_levels[level] = mastery_levels.get(level, 0) + 1
        return {
            "total_sessions": total_sessions,
            "unique_concepts": unique_concepts,
            "concept_mastery": concept_map,
            "understanding_distribution": mastery_levels,
        }

    def _extract_topic(self, tile: dict) -> str:
        """Extract topic from tile."""
        ans = tile.get("answer", "")
        if "Topic:" in ans:
            start = ans.index("Topic:") + len("Topic:")
            end = ans.index("Concepts:") if "Concepts:" in ans else len(ans)
            return ans[start:end].strip().split("|")[0].strip()
        return "unknown"

    def _build_concept_map(self, sessions: list) -> dict:
        """Build concept frequency map."""
        concept_map = {}
        for tile in sessions:
            ans = tile.get("answer", "")
            if "Concepts:" in ans:
                start = ans.index("Concepts:") + len("Concepts:")
                end = ans.index("Questions:") if "Questions:" in ans else len(ans)
                concepts_str = ans[start:end].strip().split("|")[0].strip()
                for concept in concepts_str.split(","):
                    concept = concept.strip()
                    if concept:
                        concept_map[concept] = concept_map.get(concept, 0) + 1
        return concept_map

    def _suggest_next(self, concept_map: dict) -> str:
        """Suggest next topic based on weak areas."""
        if not concept_map:
            return "Start with fundamentals."
        weakest = min(concept_map.items(), key=lambda x: x[1])
        return f"Weakest concept: {weakest[0]} ({weakest[1]} mentions). Focus here next."


# === CLI ===

def interactive_session(agent: StudyLogAgent) -> None:
    print("=== PLATO Study Partner ===")
    print(f"Room: {ROOM}")
    print()
    topic = input("Topic: ").strip()
    concepts_raw = input("Concepts (comma-sep): ").strip()
    concepts = [c.strip() for c in concepts_raw.split(",") if c.strip()]
    questions_raw = input("Questions (comma-sep): ").strip()
    questions = [q.strip() for q in questions_raw.split(",") if q.strip()]
    print("Understanding (novice/apprentice/journeyman/master): ", end="")
    understanding = input().strip() or "novice"
    notes = input("Notes: ").strip()
    next_steps_raw = input("Next steps (comma-sep): ").strip()
    next_steps = [n.strip() for n in next_steps_raw.split(",") if n.strip()]
    resources_raw = input("Resources (comma-sep): ").strip()
    resources = [r.strip() for r in resources_raw.split(",") if r.strip()]
    print()
    result = agent.submit_session(topic, concepts, questions, understanding, notes, next_steps, resources)
    print(f"Logged: {result.get('tile_hash', '?')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PLATO Study Partner Agent")
    parser.add_argument("--student", default="default")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--suggest", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    agent = StudyLogAgent(student_id=args.student, verbose=args.verbose)

    if args.resume:
        print(json.dumps(agent.don_the_shell(), indent=2, default=str))
    elif args.history:
        for i, h in enumerate(agent.show_history()):
            ts = datetime.fromtimestamp(h["timestamp"], tz=timezone.utc).isoformat()
            print(f"[{i+1}] {ts} — {h['topic']}")
    elif args.suggest:
        sessions = agent.get_all_sessions()
        print(agent._suggest_next(agent._build_concept_map(sessions)))
    elif args.stats:
        print(json.dumps(agent.show_stats(), indent=2, default=str))
    else:
        interactive_session(agent)


if __name__ == "__main__":
    main()
