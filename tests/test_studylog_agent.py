"""Tests for studylog_agent."""
import json
import pytest
from unittest.mock import patch, MagicMock

from studylog_agent import StudyLogAgent, PLATO_URL, ROOM


class TestStudyLogAgent:
    """Tests for StudyLogAgent class."""

    @pytest.fixture
    def agent(self):
        return StudyLogAgent(student_id="test-student", verbose=False)

    # === _build_answer ===

    def test_build_answer_basic(self, agent):
        ans = agent._build_answer(
            "Python Basics",
            ["variables", "loops"],
            ["what is a variable?"],
            "novice",
            "Learned about variables",
            ["practice exercises"],
            ["docs.python.org"],
        )
        assert "Topic: Python Basics" in ans
        assert "Concepts covered: variables, loops" in ans
        assert "Understanding level: novice" in ans
        assert "Session notes: Learned about variables" in ans
        assert "Next steps: practice exercises" in ans
        assert "Resources used: docs.python.org" in ans

    def test_build_answer_empty_lists(self, agent):
        ans = agent._build_answer("", [], [], "", "", [], [])
        assert "Topic:" in ans
        assert "Concepts covered:" in ans
        assert " | " in ans  # pipe-separated

    # === _extract_topic ===

    def test_extract_topic_valid(self, agent):
        tile = {"question": "What was covered studying 'Python Basics'?"}
        assert agent._extract_topic(tile) == "Python Basics"

    def test_extract_topic_missing(self, agent):
        tile = {"question": "What is this about?"}
        assert agent._extract_topic(tile) == "unknown"

    def test_extract_topic_no_quotes(self, agent):
        tile = {"question": "studying something else"}
        assert agent._extract_topic(tile) == "unknown"

    # === _build_concept_map ===

    def test_build_concept_map_single(self, agent):
        tiles = [
            {
                "answer": "Topic: Python | Concepts covered: variables, loops | "
                         "Questions asked: what is a variable? | Understanding level: novice | "
                         "Session notes: ok | Next steps: practice | Resources used: docs"
            }
        ]
        cmap = agent._build_concept_map(tiles)
        assert cmap.get("variables") == 1
        assert cmap.get("loops") == 1

    def test_build_concept_map_multiple_sessions(self, agent):
        tiles = [
            {"answer": "Concepts covered: variables | Questions asked:"},
            {"answer": "Concepts covered: variables, loops | Questions asked:"},
            {"answer": "Concepts covered: loops | Questions asked:"},
        ]
        cmap = agent._build_concept_map(tiles)
        assert cmap.get("variables") == 2
        assert cmap.get("loops") == 2

    def test_build_concept_map_empty(self, agent):
        cmap = agent._build_concept_map([])
        assert cmap == {}

    # === _suggest_next ===

    def test_suggest_next_empty(self, agent):
        suggestion = agent._suggest_next({})
        assert "curriculum is yours" in suggestion.lower()

    def test_suggest_next_gives_undercovered(self, agent):
        cmap = {"variables": 5, "loops": 1, "functions": 1}
        suggestion = agent._suggest_next(cmap)
        assert "loops" in suggestion or "functions" in suggestion

    # === submit_session ===

    @patch.object(StudyLogAgent, "_post")
    def test_submit_session_calls_post(self, mock_post, agent):
        mock_post.return_value = {"status": "ok", "tile_hash": "abc123"}
        result = agent.submit_session(
            topic="Python",
            concepts=["variables"],
            questions=["what?"],
            understanding="novice",
            notes="test",
            next_steps=["more"],
            resources=["docs"],
        )
        assert result["status"] == "ok"
        mock_post.assert_called_once()
        tile = mock_post.call_args[0][1]
        assert tile["domain"] == ROOM
        assert "Python" in tile["question"]

    # === don_the_shell ===

    @patch.object(StudyLogAgent, "_get")
    def test_don_the_shell_no_history(self, mock_get, agent):
        mock_get.return_value = {"tiles": []}
        result = agent.don_the_shell()
        assert result["status"] == "no_history"

    @patch.object(StudyLogAgent, "_get")
    def test_don_the_shell_with_history(self, mock_get, agent):
        mock_get.return_value = {
            "tiles": [
                {"question": "What was covered studying 'Python'?", "answer": "Topic: Python | Concepts covered: variables | Questions asked: | Understanding level: novice | Session notes: | Next steps: | Resources used:"}
            ]
        }
        result = agent.don_the_shell()
        assert result["status"] == "resumed"
        assert result["last_topic"] == "Python"
        assert result["session_count"] == 1
        assert "concept_mastery" in result

    # === show_stats ===

    @patch.object(StudyLogAgent, "_get")
    def test_show_stats_empty(self, mock_get, agent):
        mock_get.return_value = {"tiles": []}
        stats = agent.show_stats()
        assert stats["total_sessions"] == 0
        assert stats["unique_concepts"] == 0

    @patch.object(StudyLogAgent, "_get")
    def test_show_stats_with_data(self, mock_get, agent):
        mock_get.return_value = {
            "tiles": [
                {"answer": "Topic: Python | Concepts covered: variables, loops | Questions asked: | Understanding level: novice | Session notes: | Next steps: | Resources used:"}
            ]
        }
        stats = agent.show_stats()
        assert stats["total_sessions"] == 1
        assert stats["unique_concepts"] == 2
        assert stats["understanding_distribution"]["novice"] == 1


class TestCLI:
    """Tests for CLI module."""

    def test_cli_module_exists(self):
        from studylog_agent import cli
        assert hasattr(cli, "main")