"""Test the entrypoint module."""

from unittest import mock

import pytest
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials
from fastapi.testclient import TestClient
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from src.main import init_app, verify_credentials

# Initialize the FastAPI app and TestClient
app = init_app()
client = TestClient(app)


# Create a temporary protected route for testing
@app.get("/protected-route", dependencies=[Depends(verify_credentials)])
def protected_route() -> dict[str, str]:
    return {"message": "You have access"}


def test_verify_credentials_correct() -> None:
    """Test verify_credentials with correct username and password."""
    mock_credentials = mock.Mock(spec=HTTPBasicCredentials)
    mock_credentials.username = "correct_username"
    mock_credentials.password = "correct_password"

    with (
        mock.patch("src.main.settings.username", "correct_username"),
        mock.patch("src.main.settings.password", "correct_password"),
        mock.patch("secrets.compare_digest", return_value=True),
    ):
        # Ensure that no HTTPException is raised when credentials are correct
        try:
            verify_credentials(mock_credentials)
        except HTTPException:
            pytest.fail("verify_credentials raised HTTPException unexpectedly")


def test_verify_credentials_incorrect() -> None:
    """Test verify_credentials with incorrect username and/or password."""
    mock_credentials = mock.Mock(spec=HTTPBasicCredentials)
    mock_credentials.username = "wrong_username"
    mock_credentials.password = "wrong_password"

    with (
        mock.patch("src.main.settings.username", "correct_username"),
        mock.patch("src.main.settings.password", "correct_password"),
        mock.patch("secrets.compare_digest", side_effect=[False, False]),
    ):
        # Assert that HTTPException is raised for incorrect credentials
        with pytest.raises(HTTPException) as exc_info:
            verify_credentials(mock_credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Incorrect username or password"


def test_app_init() -> None:
    """Test if the FastAPI app initializes correctly with CORS middleware."""
    assert app is not None
    assert len(app.user_middleware) > 0  # Ensure middleware is present

    # Check that CORS middleware is added to the app
    assert any(
        isinstance(middleware, Middleware) and middleware.cls == CORSMiddleware
        for middleware in app.user_middleware
    )


def test_access_with_correct_credentials() -> None:
    """Test access to a protected route with correct credentials."""
    with (
        mock.patch("src.main.settings.username", "correct_username"),
        mock.patch("src.main.settings.password", "correct_password"),
        mock.patch("secrets.compare_digest", return_value=True),
    ):
        response = client.get(
            "/protected-route", auth=("correct_username", "correct_password")
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "You have access"}


def test_access_with_incorrect_credentials() -> None:
    """Test access to a protected route with incorrect credentials."""
    response = client.get("/protected-route", auth=("wrong_username", "wrong_password"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect username or password"}
