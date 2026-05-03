#!/usr/bin/env python3
"""studylog-agent — PLATO Study Partner. Tracks learning progression, logs sessions as tiles."""
import json, time
from typing import List, Dict

class StudyLogAgent:
    def __init__(self, plato_url="http://147.224.38.131:8847"):
        self.plato_url = plato_url
        self.sessions: List[Dict] = []
        self.topics: Dict[str, int] = {}
    
    def log_session(self, topic: str, duration_min: int, understanding: int, notes: str=""):
        sess = {"topic": topic, "duration": duration_min, "understanding": understanding, "notes": notes, "time": time.time()}
        self.sessions.append(sess)
        self.topics[topic] = self.topics.get(topic, 0) + duration_min
        self._submit(f"Studied {topic} for {duration_min}min", f"Understanding: {understanding}/10. {notes}")
        return sess
    
    def get_progress(self) -> Dict:
        if not self.sessions: return {"error": "No study sessions"}
        total_time = sum(s["duration"] for s in self.sessions)
        avg_understanding = sum(s["understanding"] for s in self.sessions) / len(self.sessions)
        return {"total_sessions": len(self.sessions), "total_hours": round(total_time/60, 1), "topics": self.topics, "avg_understanding": round(avg_understanding, 1)}
    
    def _submit(self, q: str, a: str):
        try:
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(f"{self.plato_url}/submit", data=json.dumps({"question": q, "answer": a, "agent": "studylog-agent", "room": "studylog"}).encode(), headers={"Content-Type": "application/json"}), timeout=5)
        except: pass

def demo():
    a = StudyLogAgent()
    a.log_session("Rust", 90, 7, "Learned ownership and borrowing")
    a.log_session("PLATO", 60, 8, "Built first tile submission agent")
    a.log_session("Rust", 120, 9, "Completed async chapter")
    print(a.get_progress())

if __name__ == "__main__": demo()
