# -*- coding: utf-8 -*-

import logging
import re
import os

from mimetypes import guess_type

from robot.libraries.BuiltIn import BuiltIn

from .model import Keyword, Test, Suite
from .service import RobotService
from .variables import Variables

# First suite key name in html robot framework html log
FIRST_SUITE_ID = "s1"
# Key for usage of identifier of Report Portal launch between different pabotlib threads

# Turning off unnecessary logging
logging.getLogger(name='reportportal_client').setLevel(logging.WARNING)
logging.getLogger(name='urllib3').setLevel(logging.WARNING)


# noinspection PyPep8Naming
class reportportal_listener(object):  # noqa
    """Listener for Report Portal."""

    ROBOT_LISTENER_API_VERSION = 2

    builtin_lib = BuiltIn()  # type: BuiltIn()
    robot_service = RobotService()
    robot_variables = Variables()

    def __init__(self, launch_id=None):
        """Init Report Portal listener.

        Args:
            launch_id: id of launch created to log test results in Report Portal.
        """
        self.top_level_kw_name = None
        self.current_scope = []
        self._launch_id = launch_id
        self._pabot_used = None
        self._suite_setup_failed = False

    @property
    def pabot_used(self):
        """Get status of using pabot for test execution.

        Returns:
            Cached value of Pabotlib URI.
        """
        if not self._pabot_used:
            self._pabot_used = self.builtin_lib.get_variable_value(name='${PABOTLIBURI}')
        return self._pabot_used

    def log_message(self, message):
        """Log message of current executing keyword.

        This method sends each test log message to Report Portal.

        Args:
            message: current message passed from test by test executor.
        """
        attachment = None
        if (message['html'] == 'yes'):
            screenshot = re.search('[a-z]+-[a-z]+-[0-9]+.png', message['message'])
            if screenshot:
                kwname = '{}'.format(screenshot.group(0))
                kwname = os.path.join(BuiltIn().get_variable_value('${OUTPUT_DIR}'), kwname)
                with open(kwname, "rb") as fh:
                    attachment = {
                                "name": os.path.basename(kwname),
                                "data": fh.read(),
                                "mime": guess_type(kwname)[0] or "application/octet-stream"
                            }

        RobotService.log(message, attachment)

    def _init_service(self):
        """Init report portal service."""
        self.robot_variables.check_variables()
        # setting launch id for report portal service
        self.robot_service.init_service(endpoint=self.robot_variables.endpoint,
                                        project=self.robot_variables.project,
                                        uuid=self.robot_variables.uuid)

    def start_suite(self, name, attributes):
        """Do additional actions before suite start.

        Create new launch in report portal if it is not created yet, or create new suite with tests.
        Depends on stage of test execution.

        Args:
            name: suite name.
            attributes: suite attributes dictionary.
        """
        suite = Suite(attributes=attributes)
        self.current_scope = "SUITE"
        if attributes["id"] == FIRST_SUITE_ID:
            self._init_service()
            # in case running tests using pybot we can create launch automatically
            if self.pabot_used:
                if self._launch_id is None:
                    raise Exception("launch_id is not provided. "
                                    "Please, correctly initialize listener with launch_id argument.")
                self.robot_service.rp.launch_id = self._launch_id
            else:
                # fill launch description with contents of corresponding variable value
                suite.doc = self.robot_variables.launch_doc
                # automatically creating new report portal launch
                launch_id = self.robot_service.start_launch(launch_name=self.robot_variables.launch_name,
                                                            launch=suite)
                self._launch_id = launch_id
                # save launch id for service
                self.robot_service.rp.launch_id = launch_id
                # initialize report portal service to use in test run
        if attributes['tests']:
            self.robot_service.start_suite(name=attributes['longname'], suite=suite)

    def end_suite(self, name, attributes):
        """Do additional actions after suite run.

        Close report portal launch or finish current suite with corresponding status.

        Args:
            name: suite name.
            attributes: suite attributes.
        """
        suite = Suite(attributes=attributes)
        self.current_scope = "SUITE"

        if attributes["id"] == FIRST_SUITE_ID:
            self.robot_service.terminate_service()
            # in case running tests using pybot we can finish launch automatically
            if not self.pabot_used:
                # automatically close report portal launch
                self.robot_service.finish_launch(launch=suite)
            # terminating service
            self.robot_service.terminate_service()

        if attributes['tests']:
            self.robot_service.finish_suite(suite=suite)

    def start_test(self, name, attributes):
        """Do additional actions before test run.

        This method creates new test section in Report Portal launch.

        Args:
            name: test name.
            attributes: test attributes.
        """
        test = Test(name=name, attributes=attributes)
        self.current_scope = "TEST"
        self.robot_service.start_test(test=test)

    def end_test(self, name, attributes):
        """Do additional actions after test run.

        This method closes test section in Report Portal launch.

        Args:
            name: test name.
            attributes: test attributes.
        """
        test = Test(name=name, attributes=attributes)
        self.current_scope = "SUITE"
        if self._suite_setup_failed:
            # If test failed because of failing suite setup, output log message with error severity.
            message = {
                "message": u"[ERROR] Suite Setup failed!",
                "level": "FAIL"
            }
            self.log_message(message=message)
        self.robot_service.finish_test(test=test)

    def start_keyword(self, name, attributes):
        """Do additional actions before keyword starts.

        This method creates new step section in Report Portal launch.

        Args:
            name: keyword name.
            attributes: keyword attributes.
        """
        if attributes['type'] in ['Setup', 'Teardown'] and self.current_scope == 'SUITE':
            # resetting suite setup status
            self._suite_setup_failed = False
            kw = Keyword(name=name, parent_type=self.current_scope, attributes=attributes)
            self.robot_service.start_keyword(keyword=kw)
        else:
            if self.top_level_kw_name is None:
                self.top_level_kw_name = name
                message = {
                    "message": u"[Test Keyword Start] {name}".format(name=name),
                    "level": "INFO"
                }
                RobotService.log(message=message)
            else:
                message = {
                    "message": u"[Keyword Start] {name}".format(name=name),
                    "level": "DEBUG"
                }
                RobotService.log(message=message)

    def end_keyword(self, name, attributes):
        """Do additional actions after keyword ends.

        This method close step section of a test in Report Portal launch.

        Args:
            name: keyword name.
            attributes: keyword attributes.
        """
        if attributes['type'] in ['Setup', 'Teardown'] and self.current_scope == 'SUITE':
            kw = Keyword(name=name, parent_type=self.current_scope, attributes=attributes)
            # We can add additional information to test if suite setup failed
            # to help analyzer mark those with proper type.
            if kw.status == 'FAIL':
                self._suite_setup_failed = True
            self.robot_service.finish_keyword(keyword=kw)
        else:
            if self.top_level_kw_name == name:
                self.top_level_kw_name = None
                message = {
                    "message": u"[Test Keyword End] {name}".format(name=name),
                    "level": "INFO"
                }
                RobotService.log(message=message)
            else:
                message = {
                    "message": u"[Keyword End] {name}".format(name=name),
                    "level": "DEBUG"
                }
                RobotService.log(message=message)
