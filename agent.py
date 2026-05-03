#!/usr/bin/env python3
"""studylog-agent — PLATO Study Partner. Tracks learning progression, logs sessions as tiles.
Now uses domain-agent-base for PLATO integration, health checks, and reporting.
"""
import json, time
from typing import List, Dict

try:
    from domain_agent_base import DomainAgent
except ImportError:
    class DomainAgent:
        domain = "base"
        plato_url = "http://147.224.38.131:8847"
        def __init__(self):
            self.tiles_submitted = []
            self.errors = []
            self.start_time = time.time()
        def submit_tile(self, question, answer, room=None):
            self.tiles_submitted.append({"q": question, "a": answer})
            return True
        def get_stats(self):
            return {"domain": self.domain, "tiles": len(self.tiles_submitted)}
        def run(self):
            raise NotImplementedError

class StudyLogAgent(DomainAgent):
    domain = "study"
    version = "0.2.0"
    
    def __init__(self):
        super().__init__()
        self.sessions: List[Dict] = []
        self.topics: Dict[str, int] = {}
    
    def log_session(self, topic: str, duration_min: int, understanding: int, notes: str=""):
        sess = {"topic": topic, "duration": duration_min, "understanding": understanding, "notes": notes, "time": time.time()}
        self.sessions.append(sess)
        self.topics[topic] = self.topics.get(topic, 0) + duration_min
        self.submit_tile(f"Studied {topic} for {duration_min}min", f"Understanding: {understanding}/10. {notes}")
        return sess
    
    def get_progress(self) -> Dict:
        if not self.sessions: return {"error": "No study sessions"}
        total_time = sum(s["duration"] for s in self.sessions)
        avg_understanding = sum(s["understanding"] for s in self.sessions) / len(self.sessions)
        return {"total_sessions": len(self.sessions), "total_hours": round(total_time/60, 1), "topics": self.topics, "avg_understanding": round(avg_understanding, 1)}
    
    def run(self):
        print(f"StudyLogAgent v{self.version} starting...")
        self.log_session("Python", 60, 8, "Finished async chapter")
        self.log_session("Rust", 45, 6, "Memory ownership is tricky")
        self.log_session("Python", 30, 9, "Built a web scraper")
        progress = self.get_progress()
        self.submit_tile("What is my study progress?", json.dumps(progress, indent=2))
        print(f"Run complete. {len(self.sessions)} sessions, {len(self.tiles_submitted)} tiles")

def main():
    agent = StudyLogAgent()
    agent.run()
    print(f"\nStats: {json.dumps(agent.get_stats(), indent=2)}")
    print(f"\nHealth: {json.dumps(agent.health_check(), indent=2)}")

if __name__ == "__main__":
    main()
