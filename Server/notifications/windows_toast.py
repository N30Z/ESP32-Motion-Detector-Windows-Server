#!/usr/bin/env python3
"""
Windows Toast Notification Backend
===================================
Uses winotify for Windows 10/11 toast notifications.
"""

from pathlib import Path
from typing import Optional
import logging

try:
    from winotify import Notification, audio
    WINOTIFY_AVAILABLE = True
except ImportError:
    WINOTIFY_AVAILABLE = False

from .notifications import NotificationBackend

logger = logging.getLogger(__name__)


class WindowsToastBackend(NotificationBackend):
    """Windows Toast notification backend"""

    def __init__(self, config: dict):
        self.config = config
        self.sound_enabled = config.get('notifications', {}).get('sound', True)

        if not WINOTIFY_AVAILABLE:
            logger.error("winotify not installed! Install with: pip install winotify")

    def show_notification(
        self,
        title: str,
        message: str,
        image_path: Optional[Path] = None,
        url: Optional[str] = None
    ) -> bool:
        """Show Windows Toast notification"""
        if not WINOTIFY_AVAILABLE:
            return False

        try:
            toast = Notification(
                app_id="ESP32 Motion Detector",
                title=title,
                msg=message,
                icon=str(image_path.absolute()) if image_path and image_path.exists() else None
            )

            if self.sound_enabled:
                toast.set_audio(audio.Default, loop=False)

            if url:
                toast.add_actions(label="Details anzeigen", launch=url)

            toast.show()
            logger.info(f"Windows Toast shown: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to show Windows Toast: {e}")
            return False

    def is_available(self) -> bool:
        """Check if Windows Toast is available"""
        return WINOTIFY_AVAILABLE
