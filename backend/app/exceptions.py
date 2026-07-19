from typing import Any, Dict, Optional


class LibraryError(Exception):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFoundError(LibraryError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("not_found", message, details)


class ConflictError(LibraryError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("conflict", message, details)


class ValidationError(LibraryError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("invalid_data", message, details)
