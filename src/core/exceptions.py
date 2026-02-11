class SaveLinksError(Exception):
    """Base exception for SaveLinks application."""
    pass

class SecurityError(SaveLinksError):
    """Raised when a security operation fails."""
    pass

class DatabaseError(SaveLinksError):
    """Raised when a database operation fails."""
    pass

class ValidationError(SaveLinksError):
    """Raised when input validation fails."""
    pass
