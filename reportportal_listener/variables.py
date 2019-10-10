# -*- coding: utf-8 -*-

from typing import Any, List, Optional

from robot.libraries.BuiltIn import BuiltIn


def get_variable(name: str, default: Any = None) -> Any:
    """Gets the Robot Framework variable.

    Args:
        name: variable name.
        default: default value.

    Returns:
        The value of the variable, otherwise, the default value.
    """
    return BuiltIn().get_variable_value("${" + name + "}", default=default)


class Variables(object):
    """Class for initializing and storing listener settings."""

    def __init__(self) -> None:
        """Class initialization."""
        self._uuid: Optional[str] = None
        self._endpoint: Optional[str] = None
        self._launch_name: Optional[str] = None
        self._project: Optional[str] = None
        self._launch_doc: Optional[str] = None
        self._launch_tags: Optional[List[str]] = None

    @property
    def uuid(self) -> str:
        """Gets the user uuid for accessing the ReportPortal.

        Raises:
            AssertionError if RP_UUID variable is empty or does not exist.

        Returns:
            User uuid
        """
        self._uuid = self._uuid or get_variable("RP_UUID")
        if self._uuid is None:
            raise AssertionError("Missing parameter RP_UUID for robot run\nYou should pass -v RP_UUID:<uuid_value>")

        return self._uuid

    @property
    def endpoint(self) -> str:
        """Gets the ReportPortal endpoint.

        Raises:
            AssertionError if RP_ENDPOINT variable is empty or does not exist.

        Returns:
            ReportPortal endpoint.
        """
        self._endpoint = self._endpoint or get_variable("RP_ENDPOINT")
        if self._endpoint is None:
            raise AssertionError("Missing parameter RP_ENDPOINT for robot run\n"
                                 "You should pass -v RP_RP_ENDPOINT:<endpoint_value>")

        return self._endpoint

    @property
    def launch_name(self) -> str:
        """Gets the ReportPortal launch name.

        Raises:
            AssertionError if RP_LAUNCH variable is empty or does not exist.

        Returns:
            ReportPortal launch name.
        """
        self._launch_name = self._launch_name or get_variable("RP_LAUNCH")
        if self._launch_name is None:
            raise AssertionError("Missing parameter RP_LAUNCH for robot run\n"
                                 "You should pass -v RP_LAUNCH:<launch_name_value>")

        return self._launch_name

    @property
    def project(self) -> str:
        """Gets the ReportPortal project name.

        Raises:
            AssertionError if RP_PROJECT variable is empty or does not exist.

        Returns:
            ReportPortal project name.
        """
        self._project = self._project or get_variable("RP_PROJECT")
        if self._project is None:
            raise AssertionError("Missing parameter RP_PROJECT for robot run\n"
                                 "You should pass -v RP_PROJECT:<project_name_value>")

        return self._project

    @property
    def launch_doc(self) -> str:
        """Gets the ReportPortal launch documentation.

        Returns:
            ReportPortal launch documentation.
        """
        if self._launch_doc is None:
            self._launch_doc = get_variable("RP_LAUNCH_DOC", "")

        return self._launch_doc

    @property
    def launch_tags(self) -> List[str]:
        """Gets the ReportPortal launch tags.

        Returns:
            ReportPortal launch tags.
        """
        if self._launch_tags is None:
            self._launch_tags = get_variable("RP_LAUNCH_TAGS", "").split(",")

        return self._launch_tags
