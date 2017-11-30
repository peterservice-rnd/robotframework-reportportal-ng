# -*- coding: utf-8 -*-

from robot.libraries.BuiltIn import BuiltIn


def get_variable(name, default=None):
    """Get variable from the context of Robot Framework.

    Args:
        name: variable name.
        default: default value.

    Returns:
        Variable from the context of RF.
    """
    return BuiltIn().get_variable_value("${" + name + "}", default=default)


class Variables(object):
    """Container for listener settings."""

    uuid = None
    endpoint = None
    launch_name = None
    project = None
    launch_doc = None
    launch_tags = None

    @staticmethod
    def check_variables():
        """Check input variables for listener.

        Example: pybot --listener reportportal_listener --variable RP_UUID:unique-id

        Parameters list:

        RP_UUID - unique id of user in Report Portal profile..
        RP_ENDPOINT - <protocol><hostname>:<port> for connection with Report Portal.
                      Example: http://reportportal.local:8080/
        RP_LAUNCH - name of launch to be used in Report Portal.
        RP_PROJECT - project name for new launches.
        RP_LAUNCH_DOC - documentation of new launch.
        RP_LAUNCH_TAGS - additional tags to mark new launch.
        """
        Variables.uuid = get_variable("RP_UUID", default=None)
        if Variables.uuid is None:
            raise AssertionError(
                "Missing parameter RP_UUID for robot run\n"
                "You should pass -v RP_UUID:<uuid_value>")
        Variables.endpoint = get_variable("RP_ENDPOINT", default=None)
        if Variables.endpoint is None:
            raise AssertionError(
                "Missing parameter RP_ENDPOINT for robot run\n"
                "You should pass -v RP_RP_ENDPOINT:<endpoint_value>")
        Variables.launch_name = get_variable("RP_LAUNCH", default=None)
        if Variables.launch_name is None:
            raise AssertionError(
                "Missing parameter RP_LAUNCH for robot run\n"
                "You should pass -v RP_LAUNCH:<launch_name_value>")
        Variables.project = get_variable("RP_PROJECT", default=None)
        if Variables.project is None:
            raise AssertionError(
                "Missing parameter RP_PROJECT for robot run\n"
                "You should pass -v RP_PROJECT:<project_name_value>")
        Variables.launch_doc = get_variable("RP_LAUNCH_DOC", default=None)
        Variables.launch_tags = get_variable("RP_LAUNCH_TAGS", default="").split(",")
