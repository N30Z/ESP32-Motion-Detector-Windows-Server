#!/usr/bin/env python3
"""
Linux Desktop Notification Backend
===================================
Uses notify-send (libnotify) for Linux desktop notifications.
Works on: Ubuntu, Debian, Fedora, Arch with Desktop Environment.
"""

from pathlib import Path
from typing import Optional
import subprocess
import shutil
import logging

from .notifications import NotificationBackend

logger = logging.getLogger(__name__)


class LinuxNotifyBackend(NotificationBackend):
    """Linux notify-send backend"""

    def __init__(self, config: dict):
        self.config = config
        self._notify_send_path = shutil.which('notify-send')

        if not self._notify_send_path:
            logger.warning("notify-send not found! Install with: sudo apt install libnotify-bin")

    def show_notification(
        self,
        title: str,
        message: str,
        image_path: Optional[Path] = None,
        url: Optional[str] = None
    ) -> bool:
        """
        Show Linux desktop notification via notify-send

        Args:
            title: Notification title
            message: Notification message
            image_path: Optional image (displayed as icon)
            url: URL info (shown in message, not clickable in basic notify-send)
        """
        if not self._notify_send_path:
            return False

        try:
            # Build notify-send command
            cmd = [self._notify_send_path]

            # Urgency (normal for motion events)
            cmd.extend(['--urgency=normal'])

            # App name
            cmd.extend(['--app-name=ESP32 Motion Detector'])

            # Icon (image path if available)
            if image_path and image_path.exists():
                cmd.extend(['--icon', str(image_path.absolute())])
            else:
                cmd.extend(['--icon=camera-video'])  # Fallback icon

            # Timeout (10 seconds)
            cmd.extend(['--expire-time=10000'])

            # Category
            cmd.extend(['--category=transfer.complete'])

            # Add URL to message if provided
            if url:
                message = f"{message}\n\n{url}"

            # Title and message
            cmd.append(title)
            cmd.append(message)

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"Linux notification shown: {title}")
                return True
            else:
                logger.error(f"notify-send failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("notify-send timeout")
            return False
        except Exception as e:
            logger.error(f"Failed to show Linux notification: {e}")
            return False

    def is_available(self) -> bool:
        """Check if notify-send is available"""
        return self._notify_send_path is not None


class LinuxNotifyHeadlessBackend(NotificationBackend):
    """
    Headless Linux backend

    For servers without GUI, notifications are logged only.
    Alternative: Could implement web push notifications as future feature.
    """

    def show_notification(self, title, message, image_path=None, url=None):
        logger.info(f"NOTIFICATION (headless): {title} - {message}")
        return True

    def is_available(self):
        return True
