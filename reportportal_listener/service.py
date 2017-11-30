# -*- coding: utf-8 -*-

import codecs
import re
from time import time

from reportportal_client import ReportPortalService
from robot.utils import PY2

from .variables import Variables

# https://stackoverflow.com/a/24519338/720097
ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)


def _decode_escapes(unicode_escaped_string):
    """Python 2 hack to decode unicode-escaped strings.

    Method executes selective replace of symbolic codes of the unicode specification.
    codecs.decode('unicode-escape') cannot ignore non-ascii symbols by itself, so that cases should be manually processed.

    Args:
        unicode_escaped_string: string containing unicode symbolic codes.

    Returns:
        Unicode string which replaces symbolic codes of \\uxxx kind.
    """

    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape', 'replace')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, unicode_escaped_string)


def timestamp():
    """Get timestamp for logs in Report Portal.

    Returns:
        timestamp for logs.
    """
    return str(int(time() * 1000))


class RobotService(object):
    """Service class for work with Report Portal."""
    rp = None  # type: ReportPortalService

    status_mapping = {
        "PASS": "PASSED",
        "FAIL": "FAILED",
        "SKIP": "SKIPPED"
    }

    log_level_mapping = {
        "INFO": "INFO",
        "FAIL": "ERROR",
        "TRACE": "TRACE",
        "DEBUG": "DEBUG",
        "WARN": "WARN"
    }

    @staticmethod
    def init_service(endpoint, project, uuid):
        """Init service for Report Portal.

        Args:
            endpoint: ReportPortal API endpoint.
            project: project name in Report Portal.
            uuid: unique id of user in Report Portal profile.
        """
        if RobotService.rp is None:
            RobotService.rp = ReportPortalService(
                endpoint=endpoint,
                project=project,
                token=uuid)
        else:
            raise Exception("RobotFrameworkService is already initialized.")

    @staticmethod
    def terminate_service():
        """End service."""
        if RobotService.rp is not None:
            RobotService.rp.terminate()

    @staticmethod
    def start_launch(launch_name, mode=None, launch=None):
        """Register new launch in Report Portal.

        Args:
            launch_name: name of launch.
            mode: saving data mode.
            launch: launch model object.

        Returns:
            Launch id.
        """
        sl_pt = {
            "name": launch_name,
            "start_time": timestamp(),
            "description": launch.doc,
            "mode": mode,
            "tags": Variables.launch_tags
        }
        return RobotService.rp.start_launch(**sl_pt)

    @staticmethod
    def finish_launch(launch=None):
        """Finish launch.

        Args:
            launch: launch object model.
        """
        fl_rq = {
            "end_time": timestamp(),
            "status": RobotService.status_mapping[launch.status]
        }
        RobotService.rp.finish_launch(**fl_rq)

    @staticmethod
    def start_suite(name=None, suite=None):
        """Start new suite.

        Args:
            name: name of suite.
            suite: suite object model.
        """
        start_rq = {
            "name": name,
            "description": suite.doc,
            "tags": [],
            "start_time": timestamp(),
            "item_type": suite.get_type()
        }
        RobotService.rp.start_test_item(**start_rq)

    @staticmethod
    def finish_suite(issue=None, suite=None):
        """Close suite.

        Args:
            issue: issue number, automatically linked for suite.
            suite: suite object model.
        """
        fta_rq = {
            "end_time": timestamp(),
            "status": RobotService.status_mapping[suite.status],
            "issue": issue
        }
        RobotService.rp.finish_test_item(**fta_rq)

    @staticmethod
    def start_test(test=None):
        """Start test.

        Args:
            test: test object model.
        """
        start_rq = {
            "name": test.name,
            "description": test.doc,
            "tags": test.tags,
            "start_time": timestamp(),
            "item_type": "STEP"
        }
        RobotService.rp.start_test_item(**start_rq)

    @staticmethod
    def finish_test(issue=None, test=None):
        """Finish test.

        Args:
            issue: issue number, automatically linked for log.
            test: test object model.
        """
        fta_rq = {
            "end_time": timestamp(),
            "status": RobotService.status_mapping[test.status],
            "issue": issue
        }
        RobotService.rp.finish_test_item(**fta_rq)

    @staticmethod
    def start_keyword(keyword=None):
        """Start keyword.

        Args:
            keyword: keyword object model.
        """
        start_rq = {
            "name": keyword.get_name(),
            "description": keyword.doc,
            "tags": keyword.tags,
            "start_time": timestamp(),
            "item_type": keyword.get_type()
        }
        RobotService.rp.start_test_item(**start_rq)

    @staticmethod
    def finish_keyword(issue=None, keyword=None):
        """Finish keyword.

        Args:
            issue: issue number, automatically linked for log object.
            keyword: keyword object model.
        """
        fta_rq = {
            "end_time": timestamp(),
            "status": RobotService.status_mapping[keyword.status],
            "issue": issue
        }
        RobotService.rp.finish_test_item(**fta_rq)

    @staticmethod
    def log(message, attachment=None):
        """Log message in Report Portal.

        Args:
            message: message object model.
            attachment: attachment object. Example: file or screen shot.
        """
        if PY2:
            # hack to identify and decode unicode-escaped strings on python2
            message["message"] = _decode_escapes(message["message"])

        sl_rq = {
            "time": timestamp(),
            "message": message["message"],
            "level": RobotService.log_level_mapping[message["level"]],
            "attachment": attachment,
        }
        RobotService.rp.log(**sl_rq)
