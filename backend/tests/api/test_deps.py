from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from jwt.exceptions import InvalidTokenError

from app.api.deps import get_current_user
from app.models import User


def test_get_current_user_valid():
    mock_session = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.is_active = True
    mock_session.get.return_value = mock_user

    token = "valid.token.here"
    payload = {"sub": "1"}

    with patch("jwt.decode", return_value=payload):
        user = get_current_user(session=mock_session, token=token)

    assert user == mock_user
    mock_session.get.assert_called_once_with(User, "1")


def test_get_current_user_invalid_token():
    mock_session = MagicMock()
    token = "invalid.token"

    with patch("jwt.decode", side_effect=InvalidTokenError()):
        with pytest.raises(HTTPException) as exc:
            get_current_user(session=mock_session, token=token)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Could not validate credentials"


def test_get_current_user_not_found():
    mock_session = MagicMock()
    mock_session.get.return_value = None

    token = "valid.token"
    payload = {"sub": "1"}

    with patch("jwt.decode", return_value=payload):
        with pytest.raises(HTTPException) as exc:
            get_current_user(session=mock_session, token=token)

    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found"


def test_get_current_user_inactive():
    mock_session = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.is_active = False
    mock_session.get.return_value = mock_user

    token = "valid.token"
    payload = {"sub": "1"}

    with patch("jwt.decode", return_value=payload):
        with pytest.raises(HTTPException) as exc:
            get_current_user(session=mock_session, token=token)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Inactive user"
