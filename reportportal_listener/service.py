# -*- coding: utf-8 -*-

from datetime import datetime
from time import time
from typing import Any, Callable, Dict, List, Optional, Union

from reportportal_client.errors import ResponseError as ReportPortalResponseError
from reportportal_client.service import ReportPortalService, uri_join
from requests.exceptions import ConnectionError
from robot.libraries.BuiltIn import BuiltIn
from urllib3.exceptions import ResponseError

from .report import Report
from .model import Keyword, Suite, Test


def timestamp(rf_time: str = None) -> str:
    """Get a timestamp to use when sending logs to Report Portal.

    Args:
        rf_time: Time in the format used in RobotFramework.
    Returns:
        Time stamp for use in the log.
    """
    if rf_time:
        _timestamp = datetime.strptime(rf_time, "%Y%m%d %H:%M:%S.%f").timestamp()
    else:
        _timestamp = time()

    return str(int(_timestamp * 1000))


def ignore_broken_pipe_error(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for ignore BrokenPipeError.

    Args:
        func: function to decorate.
    Returns:
        Decorated function.
    """

    def d(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ConnectionError as e:
            message = str(e)
            if 'BrokenPipeError' not in message:
                raise ConnectionError(message)

            RobotService.builtin_lib().log(message=message, level="WARN")

    return d


class RobotService(object):
    """The class for working with the Report Portal service."""
    rp: Optional[ReportPortalService] = None
    builtin: Optional[BuiltIn] = None
    report: Optional[Report] = None

    status_mapping = {"PASS": "PASSED", "FAIL": "FAILED", "SKIP": "SKIPPED"}

    log_level_mapping = {
        "INFO": "INFO",
        "FAIL": "ERROR",
        "TRACE": "TRACE",
        "DEBUG": "DEBUG",
        "WARN": "WARN",
        "ERROR": "ERROR"
    }

    @staticmethod
    def builtin_lib() -> BuiltIn:
        """Return the BuiltIn library instance.

        Returns:
            BuiltIn: instance of the BuiltIn library.
        """
        if not RobotService.builtin:
            RobotService.builtin = BuiltIn()
        return RobotService.builtin

    @staticmethod
    def rf_report() -> Report:
        """Return the instance of Report class.

        Returns:
            Report: instance of the Report class.
        """
        if not RobotService.report:
            RobotService.report = Report()
        return RobotService.report

    @staticmethod
    def init_service(endpoint: str, project: str, uuid: str) -> None:
        """Initialization of the service for working with the Report Portal.

        Args:
            endpoint: Report Portal endpoint.
            project: Report Portal project name.
            uuid: Report Portal uuid.
        """
        if RobotService.rp is None:
            RobotService.rp = ReportPortalService(endpoint=endpoint, project=project, token=uuid)
        else:
            raise Exception("RobotFrameworkService is already initialized.")

    @staticmethod
    def terminate_service() -> None:
        """Terminate the service."""
        if RobotService.rp is not None:
            RobotService.rp.terminate()

    @staticmethod
    def start_launch(launch_name: str, launch_tags: List[str], launch: Suite, mode: str = None) -> str:
        """Register a new launch in Report Portal.

        Args:
            launch_name: launch name.
            launch_tags: launch tags.
            launch: model.Suite instance.
            mode: data storage mode.

        Returns:
            Launch id.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        sl_pt = {
            "name": launch_name,
            "start_time": timestamp(),
            "description": launch.doc,
            "mode": mode,
            "tags": launch_tags
        }
        return RobotService.rp.start_launch(**sl_pt)

    @staticmethod
    def finish_launch(launch: Suite) -> None:
        """Finishes the launch in the Report Portal.

        Args:
            launch: model.Suite instance.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        fl_rq = {"end_time": timestamp(), "status": RobotService.status_mapping[launch.status]}
        RobotService.rp.finish_launch(**fl_rq)

    @staticmethod
    def start_suite(suite: Suite) -> None:
        """Register the start of a new suite.

        Args:
            suite: model.Suite instance.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        start_rq = {
            "name": suite.longname,
            "description": suite.doc,
            "tags": [],
            "start_time": timestamp(rf_time=suite.start_time),
            "item_type": suite.rp_item_type
        }
        RobotService.rp.start_test_item(**start_rq)

    @staticmethod
    def finish_suite(suite: Suite, issue: str = None) -> None:
        """Finishes the suite in the Report Portal.

        Args:
            suite: model.Suite instance.
            issue: issue number is automatically attached to log object.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        fta_rq = {
            "end_time": timestamp(rf_time=suite.end_time),
            "status": RobotService.status_mapping[suite.status],
            "issue": issue
        }
        RobotService.rp.finish_test_item(**fta_rq)

    @staticmethod
    def start_test(test: Test) -> None:
        """Register the start of a new test.

        Args:
            test: model.Test instance.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        description = test.doc.strip()
        report_link = RobotService.rf_report().get_url_to_report_by_case_id(test=test)
        if report_link:
            description += f"\n\n[Link to Report]({report_link})"

        start_rq = {
            "name": test.name,
            "description": description,
            "tags": test.tags,
            "start_time": timestamp(rf_time=test.start_time),
            "item_type": test.rp_item_type
        }
        RobotService.rp.start_test_item(**start_rq)

    @staticmethod
    def finish_test(test: Test, issue: str = None) -> None:
        """Finishes the test in the Report Portal.

        Args:
            test: model.Test instance.
            issue: issue number is automatically attached to log object.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        fta_rq = {
            "end_time": timestamp(rf_time=test.end_time),
            "status": RobotService.status_mapping[test.status],
            "issue": issue
        }
        RobotService.rp.finish_test_item(**fta_rq)

    @staticmethod
    def start_keyword(keyword: Keyword) -> None:
        """Register the start of a new keyword.

        Args:
            keyword: model.Keyword instance.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        start_rq = {
            "name": keyword.get_name(),
            "description": keyword.doc,
            "tags": keyword.tags,
            "start_time": timestamp(rf_time=keyword.start_time),
            "item_type": keyword.rp_item_type
        }
        RobotService.rp.start_test_item(**start_rq)

    @staticmethod
    def finish_keyword(keyword: Keyword, issue: str = None) -> None:
        """Finishes the keyword in the Report Portal.

        Args:
            keyword: model.Keyword instance.
            issue: issue number is automatically attached to log object.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        fta_rq = {
            "end_time": timestamp(rf_time=keyword.end_time),
            "status": RobotService.status_mapping[keyword.status],
            "issue": issue
        }
        RobotService.rp.finish_test_item(**fta_rq)

    @staticmethod
    @ignore_broken_pipe_error
    def log(log_data: Union[list, dict]) -> None:
        """Send a message in the Report Portal log.

        Args:
            log_data: message, or a list of messages prepared for logging in ReportPortal.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        try:
            if isinstance(log_data, dict):
                RobotService.rp.log(**log_data)
            elif isinstance(log_data, list):
                RobotService.rp.log_batch(log_data)
        except (ResponseError, ReportPortalResponseError) as e:
            error = str(e)
            message: Union[str, Dict[str, Any]] = f"RobotService.rp.log failed with ResponseError. " \
                f"See logs of a certain test.\n{error}"
            RobotService.builtin_lib().log_to_console(message=message)
            if "Maximum upload size" in error:
                message = {"message": message, "level": "INFO", "time": timestamp()}
                RobotService.rp.log(**message)

    @staticmethod
    def get_items_info(**params: Any) -> Dict[str, Any]:
        """Gets information about items from current launch.

        Args:
            params: request parameters.
        Returns:
            Items information.
        """
        if RobotService.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        params["filter.eq.launch"] = RobotService.rp.launch_id
        url = uri_join(RobotService.rp.base_url, "item")
        response = RobotService.rp.session.get(url=url, params=params)
        return response.json()
