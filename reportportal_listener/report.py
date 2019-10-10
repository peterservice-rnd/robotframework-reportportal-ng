# -*- coding: utf-8 -*-

import os
from typing import Dict, Optional

from robot.api import logger

from .model import Test


class Report(object):
    """Class which helps to build link to Robot Framework report."""
    def __init__(self) -> None:
        """Initialization."""
        self._report_link: Optional[str] = None

    @property
    def report_link(self) -> str:
        """Get link to Robot Framework report file.

        Returns:
            Cached value of link to report file.
        """
        if self._report_link is None:
            self._report_link = self._build_link_to_report_file()
        return self._report_link

    def get_url_to_report_by_case_id(self, test: Test) -> str:
        """Get url to Robot Framework report file by TestRail case id.

        Args:
            test: test object from the model.

        Returns:
            Report URL.
        """
        report_url = self.report_link
        if report_url:
            case_id = self._get_tag_with_testrailid(test=test)
            report_url = f'{report_url}#search?include={case_id}'
        return report_url

    @staticmethod
    def _get_tag_with_testrailid(test: Test) -> Optional[str]:
        """Get tag containing TestRail case id.

        Args:
            test: test object from the model.

        Returns:
            Tag with case id.
        """
        for tag in test.tags:
            if tag.startswith('testrailid='):
                return tag

        return None

    def _build_link_to_report_file(self) -> str:
        """"Build url to Robot Framework report file.

        Returns:
            URL to report file.
        """
        build_url = ''
        ci_vars = self._get_vars_for_report_link()

        if 'TEAMCITY_HOST_URL' in ci_vars:
            base_hostname = ci_vars.get('TEAMCITY_HOST_URL')
            buildtype_id = ci_vars.get('TEAMCITY_BUILDTYPE_ID')
            build_id = ci_vars.get('TEAMCITY_BUILD_ID')
            report_artifact_path = ci_vars.get('REPORT_ARTIFACT_PATH')
            build_url = (f'{base_hostname}/repository/download/{buildtype_id}'
                         f'/{build_id}:id/{report_artifact_path}')
        elif 'JENKINS_BUILD_URL' in ci_vars:
            build_url = ci_vars['JENKINS_BUILD_URL'] + 'robot/report'
        return f'{build_url}/report.html' if build_url else ''

    @staticmethod
    def _get_vars_for_report_link() -> Dict[str, str]:
        """"Getting values from environment variables for preparing link to report.

        If tests are running in CI, the environment variables should be defined
        in the CI configuration settings to get url to the test case report.
        The following variables are used:
            for Teamcity - TEAMCITY_HOST_URL, TEAMCITY_BUILDTYPE_ID, TEAMCITY_BUILD_ID, REPORT_ARTIFACT_PATH;
            for Jenkins  - JENKINS_BUILD_URL.
        If these variables are not found, the link to report will not be formed.

        == Example ==
        1. for Teamcity
        |    Changing build configuration settings
        |    REPORT_ARTIFACT_PATH     output
        |    TEAMCITY_BUILD_ID        %teamcity.build.id%
        |    TEAMCITY_BUILDTYPE_ID    %system.teamcity.buildType.id%
        |    TEAMCITY_HOST_URL        https://teamcity.billing.ru

        2. for Jenkins
        |    add to the shell the execution of the docker container parameter
        |    -e "JENKINS_BUILD_URL = ${BUILD_URL}"

        Returns:
            Dictionary with environment variables.
        """
        variables: Dict[str, str] = {}
        env_var = os.environ.copy() or {}
        if 'TEAMCITY_HOST_URL' in env_var:
            teamcity_vars = {'TEAMCITY_HOST_URL', 'TEAMCITY_BUILDTYPE_ID', 'TEAMCITY_BUILD_ID', 'REPORT_ARTIFACT_PATH'}
            try:
                variables = {var: env_var[var] for var in teamcity_vars}
            except KeyError:
                error_msg = "[reportportal-listener] There are no variables for getting a link to the report by tests."
                logger.error(error_msg)
        elif 'JENKINS_BUILD_URL' in env_var:
            variables = {'JENKINS_BUILD_URL': env_var['JENKINS_BUILD_URL']}
        return variables
