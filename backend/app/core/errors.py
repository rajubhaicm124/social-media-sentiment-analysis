"""Application error types with user-safe messages.

Raw exception details are logged server-side; users only ever receive the
friendly ``message`` defined here. Python stack traces are never returned.
"""

from __future__ import annotations

from typing import Any


class SocialScopeError(Exception):
    """Base class for expected, user-facing failures."""

    status_code = 400
    code = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.detail = detail or {}

    def to_payload(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "detail": self.detail}}


class InvalidURLError(SocialScopeError):
    status_code = 422
    code = "invalid_url"

    def __init__(
        self, message: str = "Please enter a valid YouTube, Facebook or Instagram URL."
    ) -> None:
        super().__init__(message)


class UnsupportedPlatformError(SocialScopeError):
    status_code = 422
    code = "unsupported_platform"

    def __init__(
        self,
        message: str = (
            "Unsupported social-media URL. SocialScope AI currently supports YouTube, "
            "Facebook and Instagram."
        ),
    ) -> None:
        super().__init__(message)


class MissingCredentialsError(SocialScopeError):
    status_code = 503
    code = "missing_credentials"

    def __init__(self, platform: str, env_var: str) -> None:
        super().__init__(
            f"The {platform} API is not configured. Set {env_var} in backend/.env to analyse "
            f"live {platform} content, or run a clearly labelled demo analysis instead.",
            detail={"platform": platform, "environment_variable": env_var},
        )


class PlatformAPIError(SocialScopeError):
    status_code = 502
    code = "platform_api_error"

    def __init__(self, platform: str, reason: str | None = None) -> None:
        message = f"The {platform} API is currently unavailable. Please try again later."
        if reason:
            message = f"{message} ({reason})"
        super().__init__(message, detail={"platform": platform, "reason": reason})


class RateLimitError(SocialScopeError):
    status_code = 429
    code = "rate_limited"

    def __init__(
        self, message: str = "API request limit reached. Please wait and try again."
    ) -> None:
        super().__init__(message)


class NotFoundError(SocialScopeError):
    status_code = 404
    code = "not_found"

    def __init__(self, message: str = "The requested analysis could not be found.") -> None:
        super().__init__(message)


class NoDataError(SocialScopeError):
    status_code = 422
    code = "no_data"

    def __init__(
        self, message: str = "No public comments were available for this content."
    ) -> None:
        super().__init__(message)


class DataUnavailableError(SocialScopeError):
    code = "data_unavailable"

    def __init__(
        self,
        message: str = "The requested metric is not available through the current platform API.",
    ) -> None:
        super().__init__(message)


class AnalysisFailedError(SocialScopeError):
    status_code = 500
    code = "analysis_failed"

    def __init__(
        self, message: str = "The analysis could not be completed. Please try again."
    ) -> None:
        super().__init__(message)
