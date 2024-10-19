"""Entrypoint for the FastAPI application."""

import logging
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.cors import CORSMiddleware

from src.config import settings
from src.logger import configure_logger
from src.routes import router

security = HTTPBasic()
logger = logging.getLogger("pipeline")


def verify_credentials(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    """Verify the provided credentials."""
    # Compare the provided username with the correct ones
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = settings.username.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )

    # Compare the provided password with the correct one
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = settings.password.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )

    # Raise an HTTPException if the credentials are incorrect
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


def init_app() -> FastAPI:
    """Initialize the FastAPI application."""
    # Configure the logger
    configure_logger()

    # Initialize the FastAPI application instance
    app = FastAPI()

    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add welcome message to the index route. This doesn't need authentication and won't
    # be included in the docs. The route is used to run health check before running integration
    # tests.
    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    async def _() -> dict[str, str]:
        return {
            "message": "Welcome to the pipeline API. Visit /docs for the documentation."
        }

    # Include the router with basic auth applied to every route
    app.include_router(router, dependencies=[Depends(verify_credentials)])

    return app


app = init_app()
