# -*- coding: utf-8 -*-

import logging

from os import environ
from typing import Any, Dict, List, Optional, Union

from robot.api import ExecutionResult
from robot.libraries.BuiltIn import BuiltIn
from robot.utils import get_error_message

from .model import Keyword, Test, Suite
from .service import RobotService
from .variables import Variables
from .message import MessageFormatter
from .service import timestamp
from .report_modifier import RobotFrameworkReportModifier

# The id of the first suite keyword in the Robot Framework html log.
FIRST_SUITE_ID = "s1"
# The key for using the Report Portal launch ID between the pabotlib threads.
PABOT_LIB_LAUNCH_ID = "PABOT_LIB_LAUNCH_ID"
# The key for blocking the initial initialization of the Report Portal launch.
PABOT_LIB_LAUNCH_LOCK = "PABOT_LIB_LAUNCH_LOCK"

# Disable redundant logging in the report portal client.
logging.getLogger(name="reportportal_client").setLevel(logging.WARNING)
logging.getLogger(name="urllib3").setLevel(logging.WARNING)


# noinspection PyPep8Naming
class reportportal_listener(object):  # noqa
    """Listener for working with Report Portal."""

    ROBOT_LISTENER_API_VERSION = 2

    builtin_lib: BuiltIn = BuiltIn()

    def __init__(self, launch_id: str = None) -> None:
        """Init Report Portal listener.

        Args:
            launch_id: id of launch created to log test results in Report Portal.
        """
        self._launch_id = launch_id
        self._service = RobotService
        self._pabot_used: Optional[str] = None
        self._suite: Optional[Suite] = None
        self._test: Optional[Test] = None
        self._keyword: Optional[Keyword] = None
        self._current_scope: Union[Suite, Test, Keyword, None] = None
        self._variables = Variables()

    @property
    def suite(self) -> Suite:
        """Gets current suite.

        Raises:
            RuntimeError if suite does not exists.
        Returns:
            model.Suite class instance.
        """
        if self._suite is None:
            raise RuntimeError("Suite not running.")

        return self._suite

    @property
    def test(self) -> Test:
        """Gets current test.

        Raises:
            RuntimeError if test does not exists.
        Returns:
            model.Test class instance.
        """
        if self._test is None:
            raise RuntimeError("Test not running")

        return self._test

    @property
    def keyword(self) -> Keyword:
        """Gets current keyword.

        Raises:
            RuntimeError if keyword is not exists.
        Returns:
            model.Keyword class instance.
        """
        if self._keyword is None:
            raise RuntimeError("Keyword not running.")

        return self._keyword

    @property
    def current_scope(self) -> Union[Suite, Test, Keyword]:
        """Gets current scope.

        Raises:
            RuntimeError if current scope is not set.
        Returns:
            model.Keyword, model.Test or model.Suite class instance.
        """
        if self._current_scope is None:
            raise RuntimeError("Current scope is not set.")

        return self._current_scope

    @property
    def pabot_used(self) -> Optional[str]:
        """Get status of using pabot for test execution.

        Returns:
            Cached value of Pabotlib URI.
        """
        if not self._pabot_used:
            self._pabot_used = self.builtin_lib.get_variable_value(name="${PABOTLIBURI}")
        return self._pabot_used

    def log_message(self, message: Dict[str, str]) -> None:
        """Log message of current executing keyword.

        Adds log message to current keyword.
        Message will be added if keyword is at top level or keyword type is setup/teardown,
         keyword is not WUKS and message level is not "FAIL".

        Args:
            message: current message passed from test by test executor.
        """
        if self.keyword.is_top_level or self.keyword.is_setup_or_teardown:
            if not self.keyword.is_wuks and message["level"] != "FAIL":
                message = self._prepare_message(message)
                self.keyword.messages.append(message)

    def _init_service(self) -> None:
        """Init report portal service."""
        # Setting launch id for report portal service.
        self._service.init_service(endpoint=self._variables.endpoint, project=self._variables.project,
                                   uuid=self._variables.uuid)

    def start_suite(self, name: str, attributes: Dict[str, Any]) -> None:
        """Do additional actions before suite start.

        Create new launch in report portal if it is not created yet, or create new suite with tests.
        Depends on stage of test execution.

        Args:
            name: suite name.
            attributes: suite attributes dictionary.
        """
        if self._service.rp is None:
            self._init_service()

        self._suite = self._current_scope = Suite(attributes=attributes)

        if attributes["id"] == FIRST_SUITE_ID and self._service.rp:
            # If launch id is specified - use it.
            # Otherwise, create launch automatically.
            if self._launch_id is not None:
                self._service.rp.launch_id = self._launch_id
            else:
                # In case running tests using robot we can create launch automatically.
                if self.pabot_used:
                    raise Exception("Pabot used but launch_id is not provided. "
                                    "Please, correctly initialize listener with launch_id argument.")
                # Fill launch description with contents of corresponding variable value.
                self.suite.doc = self._variables.launch_doc
                # Automatically create new report portal launch and save it into the service instance.
                self._service.rp.launch_id = self._service.start_launch(launch_name=self._variables.launch_name,
                                                                        launch_tags=self._variables.launch_tags,
                                                                        launch=self.suite)
        if attributes["tests"]:
            self._service.start_suite(suite=self.suite)

    def end_suite(self, name: str, attributes: Dict[str, Any]) -> None:
        """Do additional actions after suite run.

        Send tests logs of current suite to Report Portal.
        Close report portal launch or finish current suite with corresponding status.

        Args:
            name: suite name.
            attributes: suite attributes.
        """
        self.suite.update(attributes=attributes)
        if attributes["tests"]:
            if attributes["message"]:
                msg = {"message": attributes["message"], "level": "FAIL", "timestamp": self.suite.end_time}
                self.suite.message = self._prepare_message(msg)

            self._rp_log_tests()
            self._service.finish_suite(suite=self.suite)

        if attributes["id"] == FIRST_SUITE_ID:
            # If we create a launch from the outside of the script,
            # finishing launch should be made outside too.
            # Otherwise it is possible to finish a launch for several times.
            if self._launch_id is None:
                # If we run tests without pabot then we use robot,
                # thus we can finish a launch automatically.
                if not self.pabot_used:
                    self._service.finish_launch(launch=self.suite)

    def start_test(self, name: str, attributes: Dict[str, Union[str, List[str]]]) -> None:
        """Do additional actions before test run.

        Create Test model for current test.

        Args:
            name: test name.
            attributes: test attributes.
        """
        self._test = self._current_scope = Test(name=name, attributes=attributes)

    def end_test(self, name: str, attributes: Dict[str, Union[str, List[str]]]) -> None:
        """Do additional actions after test run.

        Update Test model and add to current suite.

        Args:
            name: test name.
            attributes: test attributes.
        """
        self.test.update(attributes=attributes)
        if attributes["message"]:
            msg = {"message": attributes["message"], "level": "FAIL", "timestamp": self.test.end_time}
            if "skipped" in self.test.tags:
                self.test.status = "SKIP"
                msg["level"] = "WARN"
            self.test.message = self._prepare_message(msg)

        self.suite.tests.append(self.test)
        self._current_scope = self.suite

    def start_keyword(self, name: str, attributes: Dict[str, Union[str, List[str]]]) -> None:
        """Do additional actions before keyword starts.

        Create Keyword model for current keyword, if it is at top level or a fixture.
        Add Keyword model to corresponding parent model.

        Args:
            name: keyword name.
            attributes: keyword attributes.
        """
        self._keyword = self._current_scope = Keyword(name=name, attributes=attributes, parent=self.current_scope)
        if self.keyword.is_setup_or_teardown and isinstance(self.keyword.parent, Test):
            self.keyword.tags = self.keyword.parent.tags

        if attributes["type"] == "Setup" and not isinstance(self.keyword.parent, Keyword):
            self.keyword.parent.setup = self.keyword
        elif attributes["type"] == "Teardown" and not isinstance(self.keyword.parent, Keyword):
            self.keyword.parent.teardown = self.keyword
        elif self._keyword.is_top_level and not isinstance(self.keyword.parent, Suite):
            self.keyword.parent.steps.append(self.keyword)

    def end_keyword(self, name: str, attributes: Dict[str, Union[str, List[str]]]) -> None:
        """Do additional actions after keyword ends.

        Update current Keyword model.
        For keywords with type "BEFORE_SUITE" and "AFTER_SUITE" send logs to Report Portal.

        Args:
            name: keyword name.
            attributes: keyword attributes.
        """
        self.keyword.update(attributes=attributes)

        if self.keyword.is_setup_or_teardown:
            error_message = get_error_message()
            message = {"message": error_message, "level": "FAIL", "timestamp": self.keyword.end_time}
            if self.keyword.status == "FAIL":
                message = self._prepare_message(message=message)
                self.keyword.messages.append(message)
            elif "Skip tests:" in error_message:
                self.keyword.status = "SKIP"
                message["level"] = "WARN"
                message = self._prepare_message(message=message)
                self.keyword.messages.append(message)

        if self.keyword.rp_item_type in ["BEFORE_SUITE", "AFTER_SUITE"]:
            self._rp_log_fixture_keyword(keyword=self.keyword)

        self._current_scope = self.keyword.parent
        if isinstance(self.current_scope, Keyword):
            self._keyword = self.current_scope

    def output_file(self, path: str) -> None:
        """Called when writing to an output file is ready.

        Adds Report Portal links to output file.

        Args:
            path: absolute path to output file.
        """
        result = ExecutionResult(path)
        result.visit(RobotFrameworkReportModifier(robot_service=RobotService))
        result.save()

    def close(self) -> None:
        """Called when the whole test execution ends.
        Terminating service.
        """
        self._service.terminate_service()

    def _rp_log_steps(self, steps: List[Keyword], additional_msgs: List[Dict[str, Any]] = None) -> None:
        """Send steps logs of test or keyword to Report Portal.

        Args:
            steps (list): test or keyword steps, contain Keyword models.
            additional_msgs (list): additional messages, they will be logged last.
        """
        messages = []
        for step in steps:
            msg = {"message": step.name, "level": "INFO", "timestamp": step.start_time}
            messages.append(self._prepare_message(msg))
            messages.extend(step.messages)

        if additional_msgs:
            messages.extend(additional_msgs)

        self._service.log(log_data=messages)

    def _rp_log_fixture_keyword(self, keyword: Optional[Keyword]) -> None:
        """Send fixture keyword logs to Report Portal.

        Args:
            keyword: logging keyword.

        """
        if keyword:
            self._service.start_keyword(keyword=keyword)

            if keyword.steps:
                error_messages = [msg for msg in keyword.messages if msg["level"] == "ERROR"]
                self._rp_log_steps(steps=keyword.steps, additional_msgs=error_messages)
            else:
                self._service.log(log_data=keyword.messages)

            self._service.finish_keyword(keyword=keyword)

    def _rp_log_tests(self) -> None:
        """Send tests logs of current suite to Report Portal."""
        for test in self.suite.tests:
            error_msg = self._get_test_error(test=test)
            if error_msg:
                if test.status != "SKIP":
                    test.status = "FAIL"
                if environ.get("STACK_TRACE_DESCRIPTION") == '1':
                    test.doc += f"\n```error\n{error_msg['message']}\n```"

            self._service.start_test(test=test)

            additional_msgs = [error_msg] if error_msg else None
            if test.setup or test.teardown:
                self._rp_log_fixture_keyword(keyword=test.setup)
                if test.setup:
                    test.start_time = test.setup.end_time

                self._service.start_test(test=test)
                self._rp_log_steps(steps=test.steps, additional_msgs=additional_msgs)
                self._service.finish_test(test=test)
                self._rp_log_fixture_keyword(keyword=test.teardown)
            else:
                self._rp_log_steps(steps=test.steps, additional_msgs=additional_msgs)

            self._service.finish_test(test=test)

    def _prepare_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare message for sending to Report Portal.

        Args:
            message (dict): message for preparing.
        Returns:
            Message dictionary, contains LEVEL, MESSAGE, TIME, ATTACHMENT.
        """
        message["timestamp"] = timestamp(rf_time=message["timestamp"])
        message["level"] = self._service.log_level_mapping[message["level"]]
        message = MessageFormatter.format_message(message=message, keyword_name=self.keyword.name)
        return message

    def _get_test_error(self, test: Test) -> Dict[str, Any]:
        """Gets test error considering Suite errors.

        Args:
            test: instance of Test model.
        Returns:
            Test error message.
        """
        if getattr(self.suite.setup, "status", None) == "FAIL":
            error_msg = self.suite.message
        elif getattr(self.suite.teardown, "status", None) == "FAIL":
            if test.message:
                error_msg = test.message
                error_msg["message"] = f"{test.message['message']}\n\n{self.suite.message['message']}"
            else:
                error_msg = self.suite.message
        else:
            error_msg = test.message

        return error_msg
