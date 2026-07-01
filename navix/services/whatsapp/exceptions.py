class WhatsAppError(Exception):
    """Base exception for WhatsApp related errors."""
    pass

class WhatsAppNotAuthenticatedError(WhatsAppError):
    """Raised when WhatsApp Web is not authenticated."""
    pass

class ChatNotFoundError(WhatsAppError):
    """Raised when a specific chat cannot be found."""
    pass

class MessageSendError(WhatsAppError):
    """Raised when a message fails to send."""
    pass

class BrowserError(WhatsAppError):
    """Raised when there is an issue with the Playwright browser."""
    pass
