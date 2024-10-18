"""Test utility functions."""

import base64


def get_basic_auth_header(username: str, password: str) -> str:
    credentials: str = f"{username}:{password}"
    base64_credentials: str = base64.b64encode(credentials.encode("utf-8")).decode(
        "utf-8"
    )
    return f"Basic {base64_credentials}"
