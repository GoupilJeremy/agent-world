"""Minimal JWT authentication for identity-constrained file shares."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt

from ..models.base import db
from ..models.user import User


class AuthenticationError(RuntimeError):
    """An authentication request cannot establish an active user identity."""

    status_code = 401
    error_code = "authentication_required"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidCredentialsError(AuthenticationError):
    """The supplied login credentials are invalid."""

    error_code = "invalid_credentials"


class AuthenticationValidationError(AuthenticationError):
    """The authentication request payload is malformed."""

    status_code = 400
    error_code = "invalid_request"


class InvalidAccessTokenError(AuthenticationError):
    """A bearer token is malformed, expired, or no longer maps to a user."""

    error_code = "invalid_access_token"


class AuthService:
    """Issue and verify short-lived access tokens for existing users."""

    ALGORITHM = "HS256"

    def __init__(
        self,
        secret_key: str,
        access_token_ttl_seconds: int = 3600,
        issuer: str = "agent-world",
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(secret_key, str) or not secret_key:
            raise ValueError("A non-empty authentication secret is required")
        if (
            isinstance(access_token_ttl_seconds, bool)
            or not isinstance(access_token_ttl_seconds, int)
            or access_token_ttl_seconds < 1
        ):
            raise ValueError("Access token lifetime must be a positive integer")
        if not isinstance(issuer, str) or not issuer:
            raise ValueError("A non-empty token issuer is required")

        self.secret_key = secret_key
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.issuer = issuer
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def authenticate_credentials(self, identifier: str, password: str) -> User:
        """Authenticate an active user by username or email."""

        if not isinstance(identifier, str) or not identifier.strip():
            raise InvalidCredentialsError("Invalid username/email or password")
        if not isinstance(password, str) or not password:
            raise InvalidCredentialsError("Invalid username/email or password")

        normalized = identifier.strip()
        user = User.query.filter(
            (User.username == normalized) | (User.email == normalized)
        ).first()
        if user is None or not user.is_active or not user.check_password(password):
            raise InvalidCredentialsError("Invalid username/email or password")
        return user

    def issue_access_token(self, user: User) -> str:
        """Issue a signed access token for an active, persisted user."""

        if user.id is None or not user.is_active:
            raise InvalidCredentialsError("An active persisted user is required")
        now = self._utc_now()
        payload = {
            "sub": str(user.id),
            "type": "access",
            "iss": self.issuer,
            "iat": now,
            "exp": now + timedelta(seconds=self.access_token_ttl_seconds),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)

    def login(self, identifier: str, password: str) -> tuple[User, str]:
        """Authenticate credentials and return the user with a new token."""

        user = self.authenticate_credentials(identifier, password)
        return user, self.issue_access_token(user)

    def authenticate_authorization_header(
        self, header: str | None, *, required: bool = True
    ) -> User | None:
        """Resolve an HTTP ``Authorization: Bearer`` header to an active user."""

        if header is None or not header.strip():
            if required:
                raise AuthenticationError("A bearer access token is required")
            return None

        scheme, separator, raw_token = header.strip().partition(" ")
        if (
            not separator
            or scheme.casefold() != "bearer"
            or not raw_token
            or any(character.isspace() for character in raw_token)
        ):
            raise InvalidAccessTokenError("The bearer access token is invalid")

        try:
            payload = jwt.decode(
                raw_token,
                self.secret_key,
                algorithms=[self.ALGORITHM],
                issuer=self.issuer,
                options={"require": ["exp", "iat", "iss", "sub", "type"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidAccessTokenError(
                "The bearer access token is invalid or expired"
            ) from exc

        subject = payload.get("sub")
        if payload.get("type") != "access" or not isinstance(subject, str):
            raise InvalidAccessTokenError("The bearer access token is invalid")
        try:
            user_id = int(subject)
        except ValueError as exc:
            raise InvalidAccessTokenError("The bearer access token is invalid") from exc
        if user_id < 1 or str(user_id) != subject:
            raise InvalidAccessTokenError("The bearer access token is invalid")

        user = db.session.get(User, user_id)
        if user is None or not user.is_active:
            raise InvalidAccessTokenError(
                "The bearer access token no longer identifies an active user"
            )
        return user

    def _utc_now(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime):
            raise ValueError("Authentication clock must return a datetime")
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
