"""Leaderboard service tests."""

import leaderboard_pb2
import pytest


class TestLeaderboardService:
    """Test cases for leaderboard service."""

    def test_import_proto(self):
        """Test that proto messages can be imported."""
        req = leaderboard_pb2.RecordScoreRequest(player_name="Test Player", score=100)
        assert req.player_name == "Test Player"
        assert req.score == 100

    def test_score_entry_creation(self):
        """Test ScoreEntry message creation."""
        entry = leaderboard_pb2.ScoreEntry(
            player_name="Alice",
            score=250,
            timestamp=1234567890,
        )
        assert entry.player_name == "Alice"
        assert entry.score == 250
        assert entry.timestamp == 1234567890

    @pytest.mark.unit
    def test_get_top_scores_response(self):
        """Test GetTopScoresResponse message creation."""
        entry1 = leaderboard_pb2.ScoreEntry(
            player_name="Alice",
            score=300,
            timestamp=1234567890,
        )
        entry2 = leaderboard_pb2.ScoreEntry(
            player_name="Bob",
            score=250,
            timestamp=1234567891,
        )
        resp = leaderboard_pb2.GetTopScoresResponse(scores=[entry1, entry2])
        assert len(resp.scores) == 2
        assert resp.scores[0].player_name == "Alice"
