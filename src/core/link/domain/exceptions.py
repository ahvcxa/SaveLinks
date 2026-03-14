"""
Domain-specific exceptions for SaveLinks.

Each exception maps to a specific HTTP status code in the API layer.
Domain code raises these; the API error handler translates them.
"""


class SaveLinksError(Exception):
    """Base exception for the SaveLinks domain."""
    pass


class LinkAlreadyExistsError(SaveLinksError):
    """Raised when a user tries to save a duplicate URL. → HTTP 409"""
    pass


class LinkNotFoundError(SaveLinksError):
    """Raised when a link cannot be found. → HTTP 404"""
    pass


class InvalidURLError(SaveLinksError):
    """Raised when a URL fails validation. → HTTP 422"""
    pass


class UserNotFoundError(SaveLinksError):
    """Raised when a user cannot be found. → HTTP 404"""
    pass


class UserAlreadyExistsError(SaveLinksError):
    """Raised when a username is already taken. → HTTP 409"""
    pass


class AuthenticationError(SaveLinksError):
    """Raised when authentication fails (bad password, invalid token). → HTTP 401"""
    pass


class RateLimitExceededError(SaveLinksError):
    """Raised when a user exceeds their rate limit. → HTTP 429"""
    pass
