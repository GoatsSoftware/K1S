"""Leaderboard service implementation."""

import time
from concurrent import futures

import grpc
import leaderboard_pb2
import leaderboard_pb2_grpc


class LeaderboardServicer(leaderboard_pb2_grpc.LeaderboardServiceServicer):
    """Leaderboard service implementation."""

    def __init__(self):
        self.scores = []

    def RecordScore(self, request, context):
        """Record a player's score."""
        if not request.player_name or request.score < 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid player name or score")

        # Keep only top 10 scores
        self.scores.append(
            {
                "player_name": request.player_name,
                "score": request.score,
                "timestamp": int(time.time() * 1000),
            }
        )
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]

        return leaderboard_pb2.RecordScoreResponse(
            success=True, message=f"Score recorded for {request.player_name}"
        )

    def GetTopScores(self, request, context):
        """Get top scores from leaderboard."""
        limit = request.limit if request.limit > 0 else 10
        top_scores = self.scores[:limit]

        entries = [
            leaderboard_pb2.ScoreEntry(
                player_name=score["player_name"],
                score=score["score"],
                timestamp=score["timestamp"],
            )
            for score in top_scores
        ]

        return leaderboard_pb2.GetTopScoresResponse(scores=entries)


def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    leaderboard_pb2_grpc.add_LeaderboardServiceServicer_to_server(LeaderboardServicer(), server)
    server.add_insecure_port("[::]:50052")
    print("Leaderboard Service listening on port 50052...")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
