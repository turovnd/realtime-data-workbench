class ConflictError(ValueError):
    pass


class AuthenticationError(ValueError):
    pass


class RateLimitError(ValueError):
    pass


class CursorError(ValueError):
    pass


class CursorExpired(CursorError):
    pass


class RetryableProviderError(ConnectionError):
    pass


class TerminalProviderError(ValueError):
    pass
