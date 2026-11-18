"""Game service implementation."""

import random
from concurrent import futures

import game_pb2
import game_pb2_grpc
import grpc

START_BALANCE = 10  # blades of grass


class GameServicer(game_pb2_grpc.GameServiceServicer):
    """Game service implementation."""

    def __init__(self):
        self.player_balance = START_BALANCE

    def PlaceBet(self, request, context):
        """Process a bet from the player."""
        if request.amount <= 0 or request.amount > self.player_balance // 2:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid bet amount")

        # Roll the dice (1-6)
        roll = random.randint(1, 6)

        if roll <= 3:
            # Lose: 3/6 chance
            self.player_balance -= request.amount
            return game_pb2.BetResponse(
                win=False,
                payout=0,
                message=f"You lost! Balance: {self.player_balance}",
                roll=roll,
            )

        # Win with multipliers
        if roll == 4:
            payout = int(request.amount * 1.25)
        elif roll == 5:
            payout = int(request.amount * 1.5)
        else:  # roll == 6
            payout = request.amount * 2

        self.player_balance += payout
        return game_pb2.BetResponse(
            win=True,
            payout=payout,
            message=f"You won {payout}! Balance: {self.player_balance}",
            roll=roll,
        )

    def GetBalance(self, request, context):
        """Get current player balance."""
        return game_pb2.GetBalanceResponse(balance=self.player_balance)

    def CashOut(self, request, context):
        """End the game: return the final balance and start a fresh game."""
        final_balance = self.player_balance
        self.player_balance = START_BALANCE
        return game_pb2.CashOutResponse(
            final_balance=final_balance, new_balance=self.player_balance
        )


def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    game_pb2_grpc.add_GameServiceServicer_to_server(GameServicer(), server)
    server.add_insecure_port("[::]:50051")
    print("Game Service listening on port 50051...")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
