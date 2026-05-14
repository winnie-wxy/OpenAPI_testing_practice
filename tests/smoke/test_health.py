import pytest


@pytest.mark.smoke
class TestHealthCheck:
    def test_ping_returns_201(self, unauth_client):
        """API is alive and responding."""
        response = unauth_client.health_check()
        assert response.status_code == 201
