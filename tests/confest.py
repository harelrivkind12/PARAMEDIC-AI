import pytest
from fastapi.testclient import TestClient

# importing the main application
from main import app

# importing example payloads for testing
from app.core.examples import (
    TRAUMA_INPUT_EXAMPLE,
    PEDIATRIC_SHOCK_INPUT_EXAMPLE,
    ANAPHYLAXIS_INPUT_EXAMPLE,
    TACTICAL_IV_FAILURE_INPUT_EXAMPLE
)

@pytest.fixture
def client():
    """
    Creates a FastAPI TestClient instance.
    This allows us to send simulated HTTP requests to our endpoints 
    without actually starting the uvicorn server.
    """
    return TestClient(app)

@pytest.fixture
def trauma_payload():
    """Returns the adult massive hemorrhage scenario dictionary."""
    return TRAUMA_INPUT_EXAMPLE

@pytest.fixture
def pediatric_payload():
    """Returns the pediatric shock scenario dictionary."""
    return PEDIATRIC_SHOCK_INPUT_EXAMPLE

@pytest.fixture
def anaphylaxis_payload():
    """Returns the severe anaphylaxis scenario dictionary."""
    return ANAPHYLAXIS_INPUT_EXAMPLE

@pytest.fixture
def tactical_iv_payload():
    """Returns the tactical IV failure scenario dictionary."""
    return TACTICAL_IV_FAILURE_INPUT_EXAMPLE