import pytest
import main

@pytest.fixture()
def app():
    app = main.app
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()