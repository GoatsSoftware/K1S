"""API Gateway tests."""

import pytest


class TestGateway:
    """Test cases for API gateway."""

    @pytest.mark.unit
    def test_imports(self):
        """Test that gateway can be imported."""
        from gateway import GatewayClient

        assert GatewayClient is not None

    def test_gateway_initialization(self):
        """Test gateway client initialization."""
        from gateway import GatewayClient

        gateway = GatewayClient()
        assert gateway.game_channel is not None
        assert gateway.leaderboard_channel is not None
        gateway.close()
