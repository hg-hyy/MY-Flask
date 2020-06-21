import os
import tempfile
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username="admin", password="12!@QWqw"):
        return self._client.post(
            "/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
