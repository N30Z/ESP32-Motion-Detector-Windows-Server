"""Platform-specific backends for notifications"""

from .notifications import NotificationBackend, get_notification_backend

__all__ = ['NotificationBackend', 'get_notification_backend']
