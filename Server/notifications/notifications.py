#!/usr/bin/env python3
"""
Notification Backend - Abstract Interface
==========================================
Platform-independent notification interface.
Implementations: Windows Toast, Linux notify-send, disabled.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NotificationBackend(ABC):
    """Abstract notification backend"""

    @abstractmethod
    def show_notification(
        self,
        title: str,
        message: str,
        image_path: Optional[Path] = None,
        url: Optional[str] = None
    ) -> bool:
        """
        Show notification

        Args:
            title: Notification title
            message: Notification message
            image_path: Optional image to display
            url: Optional URL to open on click

        Returns:
            True if notification was shown successfully
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if notification backend is available"""
        pass


class DisabledBackend(NotificationBackend):
    """Disabled notification backend (headless servers)"""

    def show_notification(self, title, message, image_path=None, url=None):
        logger.debug(f"Notifications disabled: {title} - {message}")
        return True

    def is_available(self):
        return True


def get_notification_backend(backend_type: str, config: dict) -> NotificationBackend:
    """
    Factory: Get notification backend by type

    Args:
        backend_type: 'windows_toast', 'linux_notify', 'disabled'
        config: Configuration dict

    Returns:
        NotificationBackend instance
    """
    if backend_type == 'disabled':
        return DisabledBackend()

    elif backend_type == 'windows_toast':
        try:
            from .windows_toast import WindowsToastBackend
            return WindowsToastBackend(config)
        except ImportError as e:
            logger.warning(f"Windows Toast backend not available: {e}")
            logger.warning("Falling back to disabled notifications")
            return DisabledBackend()

    elif backend_type == 'linux_notify':
        try:
            from .linux_notify import LinuxNotifyBackend
            return LinuxNotifyBackend(config)
        except ImportError as e:
            logger.warning(f"Linux Notify backend not available: {e}")
            logger.warning("Falling back to disabled notifications")
            return DisabledBackend()

    else:
        logger.error(f"Unknown notification backend: {backend_type}")
        return DisabledBackend()
