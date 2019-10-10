# -*- coding: utf-8 -*-

import os
import re
from typing import Any, Dict, Union

from html import unescape
from mimetypes import guess_type
from robot.libraries.BuiltIn import BuiltIn

# Patterns for editing HTML messages.
HTML_MESSAGE_PATTERN = re.compile(r"<details><summary>(?P<summary>.*)</summary><p>(?P<message>.*)</p></details>", re.S)
SCREENSHOT_PATH_PATTERN = re.compile(r'<img src="(?P<path>[_/.\-\w]*)"', re.S)


class MessageFormatter(object):
    """Class for formatting log messages in ReportPortal."""

    @staticmethod
    def format_message(message: Dict[str, Any], keyword_name: str) -> Dict[str, Any]:
        """Method for formatting message.
        Truncate message and cut any html attribute:
        tags: details, summary, p; quote symbols: &gt and other.
        Adds attachment to message if it exists.
        And prepare message to correctly display in Report Portal.

        Args:
            message: message of the step of keyword.
            keyword_name: current keyword name.
        Returns:
            Dictionary with message information, that is correctly displayed in Report Portal.
        """
        path_to_screen = SCREENSHOT_PATH_PATTERN.search(message["message"])
        if path_to_screen:
            message["attachment"] = MessageFormatter._get_attachment(attachment_path=path_to_screen.group("path"))
            message["message"] = f'Screen shot in the keyword "{keyword_name}"'
        else:
            message["message"] = MessageFormatter._strip_html_tags(message=message["message"])
            message["message"] = MessageFormatter._truncate_message(message=message["message"])

        message = {
            "time": message.get("timestamp"),
            "message": message["message"],
            "level": message["level"],
            "attachment": message.get("attachment"),
        }
        return message

    @staticmethod
    def _get_attachment(attachment_path: str, is_absolute_path: bool = False) -> Dict[str, str]:
        """Gets attachment information to use in Report Portal.

        Args:
            attachment_path: path to attachment.
            is_absolute_path: flag indicating path to attachment is absolute or not.
        Returns:
            Information by attachment for log message.
        """
        if not is_absolute_path:
            output_dir = BuiltIn().get_variable_value("${OUTPUT_DIR}")
            attachment_path = os.path.join(output_dir, attachment_path)
        with open(attachment_path, "rb") as attachment:
            attachment_info = {
                "name": os.path.basename(attachment_path),
                "data": str(attachment.read()),
                "mime": guess_type(attachment_path)[0] or "application/octet-stream"
            }
        return attachment_info

    @staticmethod
    def _strip_html_tags(message: str) -> str:
        """Method for unquote message and removing html tags: details, summary, p.

        Args:
            message: message of the step of keyword.
        Returns:
            String, where all quotes and html tags are removing.
        """
        match = HTML_MESSAGE_PATTERN.fullmatch(message)
        if match:
            summary, message = match.group("summary", "message")
            if not message.startswith(summary):
                message = "\n".join([summary, message])
            message = unescape(message)
        return message

    @staticmethod
    def _truncate_message(message: Union[str, dict], max_length: int = 8388608) -> Union[str, Dict[str, Any]]:
        """Truncate message to the maximum length.

        Args:
            message: message of the step of keyword. It may be string or dictionary.
            max_length: max length of the message.
        Returns:
            String or dictionary, that is truncated.
        """
        if isinstance(message, dict):
            message["message"] = message["message"][:max_length] + (message["message"][max_length:] and "..")
        else:
            message = message[:max_length] + (message[max_length:] and "..")
        return message
