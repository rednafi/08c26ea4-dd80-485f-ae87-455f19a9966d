import base64

from src.utils import get_basic_auth_header


def test_get_basic_auth_header() -> None:
    username = "test_user"
    password = "test_password"
    expected_credentials = f"{username}:{password}"
    expected_base64 = base64.b64encode(expected_credentials.encode("utf-8")).decode(
        "utf-8"
    )
    expected_header = f"Basic {expected_base64}"

    result = get_basic_auth_header(username, password)

    assert result == expected_header
