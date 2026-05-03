"""CLI entry point for studylog-agent."""
import argparse
import json
import sys
from datetime import datetime, timezone

from studylog_agent import StudyLogAgent


def interactive_session(agent: StudyLogAgent) -> None:
    print("=== PLATO Study Partner ===")
    print(f"Room: studylog-ai")
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