"""API Gateway - gRPC router and orchestrator."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import grpc

# In the monorepo, the generated stubs live in the sibling service directories.
for _service in ("game-service", "leaderboard-service"):
    _stubs_dir = Path(__file__).resolve().parent.parent / _service
    if _stubs_dir.is_dir():
        sys.path.append(str(_stubs_dir))

# Import game service
from game_pb2 import BetRequest, CashOutRequest, GetBalanceRequest  # noqa: E402
from game_pb2_grpc import GameServiceStub  # noqa: E402

# Import leaderboard service
from leaderboard_pb2 import GetTopScoresRequest, RecordScoreRequest  # noqa: E402
from leaderboard_pb2_grpc import LeaderboardServiceStub  # noqa: E402


class GatewayClient:
    """Gateway client for managing connections to microservices."""

    def __init__(self, game_host="localhost:50051", leaderboard_host="localhost:50052"):
        self.game_channel = grpc.insecure_channel(game_host)
        self.game_stub = GameServiceStub(self.game_channel)

        self.leaderboard_channel = grpc.insecure_channel(leaderboard_host)
        self.leaderboard_stub = LeaderboardServiceStub(self.leaderboard_channel)

    def play_round(self, bet_amount: int) -> dict:
        """Place a bet and return the outcome with the new balance."""
        try:
            bet_response = self.game_stub.PlaceBet(BetRequest(amount=bet_amount))
            balance_response = self.game_stub.GetBalance(GetBalanceRequest())

            return {
                "success": True,
                "win": bet_response.win,
                "payout": bet_response.payout,
                "balance": balance_response.balance,
                "message": bet_response.message,
                "roll": bet_response.roll,
            }
        except grpc.RpcError as e:
            return {"success": False, "error": e.details() or str(e)}

    def cash_out(self, player_name: str) -> dict:
        """End the game: record the final balance on the leaderboard and restart."""
        try:
            cash = self.game_stub.CashOut(CashOutRequest())
            self.leaderboard_stub.RecordScore(
                RecordScoreRequest(player_name=player_name, score=cash.final_balance)
            )
            return {
                "success": True,
                "score": cash.final_balance,
                "balance": cash.new_balance,
            }
        except grpc.RpcError as e:
            return {"success": False, "error": e.details() or str(e)}

    def get_balance(self) -> dict:
        """Get the player's current balance."""
        try:
            response = self.game_stub.GetBalance(GetBalanceRequest())
            return {"success": True, "balance": response.balance}
        except grpc.RpcError as e:
            return {"success": False, "error": e.details() or str(e)}

    def get_leaderboard(self, limit: int = 10) -> dict:
        """Get top scores from leaderboard."""
        try:
            response = self.leaderboard_stub.GetTopScores(GetTopScoresRequest(limit=limit))
            scores = [
                {
                    "player_name": score.player_name,
                    "score": score.score,
                    "timestamp": score.timestamp,
                }
                for score in response.scores
            ]
            return {"success": True, "scores": scores}
        except grpc.RpcError as e:
            return {"success": False, "error": e.details() or str(e)}

    def close(self):
        """Close all connections."""
        self.game_channel.close()
        self.leaderboard_channel.close()


def make_handler(gateway: GatewayClient):
    """Build the HTTP handler exposing the gateway to the web frontend."""

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/api/balance":
                result = gateway.get_balance()
            elif self.path == "/api/leaderboard":
                result = gateway.get_leaderboard()
            else:
                return self._send(404, {"success": False, "error": "not found"})
            self._send(200 if result["success"] else 502, result)

        def do_POST(self):
            if self.path not in ("/api/bet", "/api/cashout"):
                return self._send(404, {"success": False, "error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length) or b"{}")
                player = str(data.get("player_name") or "Anonymous")[:32]
                amount = int(data["amount"]) if self.path == "/api/bet" else 0
            except (ValueError, KeyError, TypeError):
                return self._send(400, {"success": False, "error": "invalid request"})
            if self.path == "/api/bet":
                result = gateway.play_round(amount)
            else:
                result = gateway.cash_out(player)
            self._send(200 if result["success"] else 400, result)

        def log_message(self, format, *args):
            print(f"[gateway] {self.address_string()} {format % args}")

    return Handler


def main():
    """Serve the gateway HTTP API."""
    gateway = GatewayClient(
        game_host=os.environ.get("GAME_HOST", "localhost:50051"),
        leaderboard_host=os.environ.get("LEADERBOARD_HOST", "localhost:50052"),
    )
    port = int(os.environ.get("GATEWAY_PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), make_handler(gateway))
    print(f"API Gateway listening on port {port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        gateway.close()


if __name__ == "__main__":
    main()
