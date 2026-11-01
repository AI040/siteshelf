"""Application errors. Each carries the HTTP status the API should return."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message: str | None = None):
        self.message = message or "Something went wrong."
        super().__init__(self.message)


class FileParseError(AppError):
    """The uploaded file could not be read or is not in the expected shape."""

    status_code = 400


class MissingColumnsError(FileParseError):
    """Required columns are absent from the uploaded file."""


class FileTooLargeError(AppError):
    status_code = 413


class DatabaseError(AppError):
    """A database failure. Details are logged, not shown to the user."""

    status_code = 500

    def __init__(self, message: str | None = None):
        super().__init__(message or "A database error occurred. Please try again.")
