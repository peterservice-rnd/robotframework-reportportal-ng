# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional, Type

from robot.api import ResultVisitor
from robot.result.model import TestCase, TestSuite

from .service import RobotService


class RobotFrameworkReportModifier(ResultVisitor):
    """Class for modifying Robot Framework report."""

    def __init__(self, robot_service: Type[RobotService]) -> None:  # noqa: E951
        """Init Result Visitor.

        Args:
            robot_service: instance RobotService.
        """
        self._robot_service = robot_service
        self._uri_parts: Optional[Dict[str, str]] = None

    @property
    def uri_parts(self) -> Dict[str, str]:
        """Sets value to _uri_parts attribute if it is not specified.

        Returns:
            Value of _uri_parts attribute.
        """
        if self._uri_parts is None:
            self._uri_parts = self._get_rp_uri_parts()
        return self._uri_parts

    def start_suite(self, suite: TestSuite) -> None:
        """Visits top level suite in result and adds Report Portal link in metadata.

        Args:
            suite: visited suite.
        """
        if not suite.parent:
            suite.metadata["Report Portal"] = self.get_link_to_rp_report()

    def start_test(self, test: TestCase) -> None:
        """Visits each test in result and adds Report Portal link in documentation.

        Args:
            test: visited test.
        """
        link = self.get_link_to_rp_report(test=test)
        message = f'[{link} | Report Portal]'
        test.doc = '\n\n'.join([test.doc, message]) if test.doc else message

    def _get_rp_uri_parts(self) -> Dict[str, str]:
        """Gets uri parts, for item name.

        Returns:
            Dictionary with item longname as key and uri part as value.
        """
        tests = self._get_rp_tests_info()
        parts = {}

        for test in tests:
            if len(test["path_names"]) > 1:
                continue

            suite_id = test.get("parent")
            if suite_id:
                suite_longname = test["path_names"][suite_id]
                test_longname = f"{suite_longname}.{test['name']}"
                parts[test_longname] = "/" + test["id"] if test["has_childs"] else "?log.item=" + test["id"]
                parts[suite_longname] = "/" + suite_id

        return parts

    def _get_rp_tests_info(self) -> List[Dict[str, Any]]:
        """Gets information about tests items from Report Portal.

        Returns:
            Information about tests.
        """
        params = {"page.size": 300, "filter.eq.type": "STEP"}
        response = self._robot_service.get_items_info(**params)
        page_num, page_count, tests = 2, response["page"]["totalPages"], response["content"]

        while page_num <= page_count:
            params["page.page"] = page_num
            response = self._robot_service.get_items_info(**params)
            tests.extend(response["content"])
            page_num += 1

        return tests

    def get_link_to_rp_report(self, test: TestCase = None) -> str:
        """Gets link to report in Report Portal.

        Args:
            test: test object from Robot Framework.
        Returns:
            Link to report.
        """
        if self._robot_service.rp is None:
            raise RuntimeError("RobotFrameworkService is not initialized.")

        link = f"{self._robot_service.rp.endpoint}/ui/#{self._robot_service.rp.project}" \
            f"/launches/all/{self._robot_service.rp.launch_id}"
        if test:
            suite_uri = self.uri_parts.get(test.parent.longname)
            test_uri = self.uri_parts.get(test.longname)
            if suite_uri:
                link += suite_uri
                if test_uri:
                    link += test_uri

        return link
