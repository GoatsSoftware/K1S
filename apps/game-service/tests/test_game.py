"""Game service tests."""

import game_pb2
import pytest


class TestGameService:
    """Test cases for game service."""

    def test_import_proto(self):
        """Test that proto messages can be imported."""
        # This is a simple test to ensure proto compilation worked
        req = game_pb2.BetRequest(amount=5)
        assert req.amount == 5

    def test_get_balance_response(self):
        """Test GetBalanceResponse message creation."""
        resp = game_pb2.GetBalanceResponse(balance=10)
        assert resp.balance == 10

    @pytest.mark.unit
    def test_bet_response_creation(self):
        """Test BetResponse message creation."""
        resp = game_pb2.BetResponse(win=True, payout=25, message="You won!")
        assert resp.win is True
        assert resp.payout == 25
        assert resp.message == "You won!"

    def test_cash_out_returns_balance_and_resets(self):
        """CashOut returns the final balance and starts a fresh game."""
        import main

        servicer = main.GameServicer()
        servicer.player_balance = 42
        resp = servicer.CashOut(game_pb2.CashOutRequest(), None)
        assert resp.final_balance == 42
        assert resp.new_balance == main.START_BALANCE
        assert servicer.player_balance == main.START_BALANCE
