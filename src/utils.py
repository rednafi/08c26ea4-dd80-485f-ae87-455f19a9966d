"""Test utility functions."""

import base64


def get_basic_auth_header(username: str, password: str) -> str:
    """Convert username and password to a base64-encoded header.

    This will be passed as the Authorization header in the request.
    """
    credentials: str = f"{username}:{password}"
    base64_credentials: str = base64.b64encode(credentials.encode("utf-8")).decode(
        "utf-8"
    )
    return f"Basic {base64_credentials}"
